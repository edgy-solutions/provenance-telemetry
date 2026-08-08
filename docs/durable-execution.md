# Durable execution — instrumenting a replaying runtime

**Read this before instrumenting a Restate / Temporal / any-replaying handler. `observed_trace` is not replay-safe on its own, and the failure is invisible in a green test suite.**

This recipe is written from a production adoption across a ten-engine mesh on Restate. The library's own primitives are correct; what follows is what a *durable* caller must add around them.

---

## The failure

A durable runtime re-executes your handler from the top after a crash, a suspension, or a redeploy. It does not re-run the *effects* you wrapped in a journal call (`ctx.run` in Restate) — those return their recorded values. Everything **outside** a journal call runs again, for real, every time.

`observed_trace` is a context manager wrapped around your work. On replay it re-enters and **exports a second span for the same logical operation**:

```python
# ❌ WRONG in a durable handler — emits one boundary per replay
async def handler(ctx: Context, req: Request):
    with observed_trace(MAPPING, values, name="analyze"):
        result = await ctx.run("work", lambda: do_work(req))
    return result
```

Three replays produce **three** boundary spans on one trace, each with a different span id and overlapping timings. The trace stops being a record of what happened and becomes a record of how many times the runtime retried — and because every span is individually well-formed, nothing in Langfuse looks broken.

**Why tests do not catch it:** replays are rare, and a test that exercises the handler once cannot produce one. You must *manufacture* a replay (kill the process mid-handler, or fail after the work) to witness it at all.

## Why the obvious fixes do not work

- **Move the `with` inside `ctx.run`** — the span now covers only the journaled body, and everything else in the handler falls outside the trace.
- **Deduplicate afterwards** — the doubles are already exported; you are reconciling, not preventing.
- **Pass a fixed span id to the tracer** — the OTel API has no way to set a span's *own* id. It can set a **parent**, not itself. (The ingestion API can, which is what the emit step below uses.)

## The fix — three parts

**Journal the identity, make it a non-recording parent, and emit the boundary once from inside the journal.**

```python
import secrets, uuid, datetime
from contextlib import contextmanager

def mint_boundary_ids(trace_seed=None) -> dict:
    """Mint {"trace_id": 32-hex, "span_id": 16-hex}. CALL INSIDE ctx.run."""
    ids = {"trace_id": None, "span_id": secrets.token_hex(8)}
    try:
        from langfuse import get_client
        ids["trace_id"] = get_client().create_trace_id(
            seed=str(trace_seed) if trace_seed else None)
    except Exception:
        pass          # telemetry never breaks the work
    return ids

@contextmanager
def boundary_parent(ids: dict):
    """Make the journaled (trace_id, span_id) the AMBIENT parent — emitting NOTHING."""
    timing = {"started_at": datetime.datetime.now(datetime.timezone.utc), "ended_at": None}
    detach = None
    if ids.get("trace_id") and ids.get("span_id"):
        try:
            from opentelemetry import context as _octx, trace as _otr
            from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
            tok = _octx.attach(_otr.set_span_in_context(NonRecordingSpan(SpanContext(
                trace_id=int(ids["trace_id"], 16), span_id=int(ids["span_id"], 16),
                is_remote=True, trace_flags=TraceFlags(TraceFlags.SAMPLED)))))
            detach = lambda: _octx.detach(tok)
        except Exception:
            detach = None                 # untraced beats broken
    try:
        yield timing
    finally:
        timing["ended_at"] = datetime.datetime.now(datetime.timezone.utc)
        if detach: 
            try: detach()
            except Exception: pass
```

`emit_boundary(mapping, values, *, ids, name, timing)` then posts the boundary itself through the **ingestion API** (`trace-create` + `span-create`), which — unlike the OTel path — accepts an explicit observation `id`. Because the id comes from the journal, a re-emit **upserts** rather than duplicating.

### Wiring it

```python
async def handler(ctx: Context, req: Request):
    # 1. Identity is JOURNALED -> identical on every replay
    ids = await ctx.run("telemetry-ids", lambda: mint_boundary_ids(req.trace_id))

    # 2. Ambient NON-RECORDING parent: exports nothing itself, so replaying is free
    with boundary_parent(ids) as timing:
        result = await ctx.run("work", lambda: do_work(req))   # spans inside nest normally

    # 3. Emit the boundary ONCE, from inside the journal
    await ctx.run("telemetry-boundary",
                  lambda: emit_boundary(MAPPING, values, ids=ids,
                                        name="analyze", timing=timing))
    return result
```

### Why each part is load-bearing

| part | what it buys |
|---|---|
| ids minted **inside** `ctx.run` | the runtime hands back the *same* pair on every replay — one stable identity, not a new one per attempt |
| parent is **non-recording** | re-entering the block exports **nothing**. The double cannot occur *by construction*, not by later dedup |
| boundary emitted **inside** `ctx.run` | happens once; and the ingestion API upserts on observation id, so even a re-emit lands one observation |
| `trace_seed` passed through | the cross-service join still holds — durability does not cost you the trace |

**Leaf spans go inside; parenting boundaries go outside.** Existing `observe_span` / `traced` instrumentation inside the handler needs **no change** — it nests under the ambient parent through the ordinary OTel context.

### The failure mode this leaves

If the handler dies *between* the work and the emit, the boundary never lands and its children appear as roots on the correct trace. That is **a missing parent, never a phantom one** — chosen deliberately. An absent span reads as absent; a fabricated one reads as truth.

---

## Witnessing it

A fix to a replay defect that has not been observed under an actual replay is a belief, not a result. **Manufacture one.**

```python
# a seal that FAILS after the work, forcing a real replay
if os.getenv("SEAL_FAIL_AFTER_WORK") == "1":
    raise RuntimeError("manufactured replay")
```

**Fail, do not kill.** An early version killed the process instead, which *also* produced a replay — but killing cannot discriminate between "the boundary was emitted once" and "the boundary was never emitted at all", because both leave nothing behind at that instant. Raising after the work leaves the journal intact and the handler genuinely re-entering, so the two outcomes look different.

Then check the trace carries **exactly one** boundary span with the **same span id** across attempts. If your instrument cannot tell one-emission from zero-emissions, it is not a witness — fix the instrument before trusting the result.

> Note on where verification lives: an *inner* span created inside `ctx.run` is not evidence of replay-safety. The journal records the **return value** of the wrapped function, not the spans it exported as a side effect — so an inner span re-exports on replay exactly like any other un-journaled effect. Only the three-part shape above is replay-safe.

## Should this be in the library?

Not yet, deliberately. It needs no code from this package — it is a *composition* over `create_trace_id`, the OTel context API, and the ingestion API — and it is coupled to a specific runtime's journal semantics (`ctx.run`). Promoting it would put a Restate-shaped assumption into a package whose whole pitch is four dependencies and no domain. It is documented here so the next adopter inherits the finding instead of rediscovering it in production, which is the expensive way.
