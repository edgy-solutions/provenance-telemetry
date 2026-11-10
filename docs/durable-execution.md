# Durable execution — instrumenting a replaying runtime

**Read this before instrumenting a Restate / Temporal / any-replaying handler. `observed_trace` is not replay-safe on its own, and the failure is invisible in a green test suite.**

This recipe comes from a production adoption across a ten-engine mesh on Restate. Since 0.2.0 the library ships the primitives (`mint_boundary_ids`, `boundary_parent`, `emit_boundary`); this page says how to wire them.

---

## The failure

A durable runtime re-executes your handler from the top after a crash, a suspension, or a redeploy. It does not re-run the *effects* you wrapped in a journal call (`ctx.run` in Restate) — those return their recorded values. Everything **outside** a journal call runs again, for real, every time.

`observed_trace` is a context manager wrapped around your work. On replay it re-enters and **exports a second span for the same logical operation**:

```python
# WRONG in a durable handler — emits one boundary per replay
async def handler(ctx: Context, req: Request):
    with observed_trace(MAPPING, values, name="analyze"):
        result = await ctx.run("work", lambda: do_work(req))
    return result
```

Three replays produce **three** boundary spans on one trace, each with a different span id and overlapping timings. The trace becomes a record of how many times the runtime retried, and because every span is individually well-formed, nothing in Langfuse looks broken. Tests do not catch it: replays are rare, and a test that runs the handler once cannot produce one. You must *manufacture* a replay to witness it.

## Why the obvious fixes do not work

- **Move the `with` inside `ctx.run`** — the span covers only the journaled body; the rest of the handler falls outside the trace.
- **Deduplicate afterwards** — the doubles are already exported.
- **Pass a fixed span id to the tracer** — the OTel API cannot set a span's *own* id, only a parent. The library works around that by building the boundary span by hand with a chosen `SpanContext` (see below).

## The fix — three parts

**Journal the identity, make it a non-recording parent, and export the boundary once from inside the journal.**

```python
from provenance_telemetry import (
    mint_boundary_ids, boundary_parent, emit_boundary, observe_span, flush,
)

async def handler(ctx: Context, req: Request):
    # 1. Identity is JOURNALED -> identical on every replay
    ids = await ctx.run("telemetry-ids", lambda: mint_boundary_ids(req.trace_id))

    # 2. Ambient NON-RECORDING parent: exports nothing, so replaying is free.
    #    mapping/values also propagate user/session/tags/metadata to every child.
    with boundary_parent(ids, mapping=MAPPING, values=values) as timing:
        result = await ctx.run("work", lambda: do_work(req))  # observe_span etc. nest under it

    # 3. Export the boundary ONCE, from inside the journal
    await ctx.run("telemetry-boundary",
                  lambda: emit_boundary(MAPPING, values, ids=ids,
                                        name="analyze", timing=timing))
    return result
```

For a subprocess step or CLI job that exits right after the work, call `flush()` before exit; the batch is otherwise lost.

### What each primitive does

| primitive | behaviour |
|---|---|
| `mint_boundary_ids(trace_seed)` | `{"trace_id": 32-hex or None, "span_id": 16-hex}`. Inside `ctx.run` the runtime replays the same pair. `trace_seed` keeps the cross-service join. |
| `boundary_parent(ids, mapping=, values=)` | attaches a non-recording remote parent as the ambient span; exports nothing, so re-entry cannot double. Yields `timing`. With `mapping`/`values` it propagates the trace attributes (v4 filters on them per span). |
| `emit_boundary(mapping, values, *, ids, name, timing)` | builds the boundary span with the journaled ids as the trace root, over OTLP, reusing the SDK tracer's resource, processor and instrumentation scope (a span with another scope is dropped by the Langfuse processor). Returns the span id. |

**Leaf spans go inside; parenting boundaries go outside.** Existing `observe_span` / `traced` instrumentation inside the handler needs no change.

### The failure modes this leaves

* **Dies before `emit_boundary`:** the boundary never lands and its children appear as roots on the correct trace — a missing parent, never a phantom one. Chosen deliberately: an absent span reads as absent.
* **Export succeeded, the step's journal entry did not commit:** on replay `emit_boundary` runs again and, **on Langfuse v4, produces one DUPLICATE observation.** The OTLP path does not upsert a re-exported span id. (Before v4 the ingestion API upserted, and an earlier version of this recipe leaned on that as a safety net. v4 removed the ingestion leg, so only "called once, inside the journaled step" remains.) Never call `emit_boundary` outside a journaled step.

---

## Witnessing it

A fix to a replay defect that has not been observed under an actual replay is a belief, not a result. **Manufacture one.**

```python
# a seal that FAILS after the work, forcing a real replay
if os.getenv("SEAL_FAIL_AFTER_WORK") == "1":
    raise RuntimeError("manufactured replay")
```

**Fail, do not kill.** Killing the process also produces a replay, but cannot discriminate between "emitted once" and "never emitted", since both leave nothing behind at that instant. Raising after the work leaves the journal intact and the handler genuinely re-entering.

Then check the trace carries **exactly one** boundary span with the **same span id** across attempts. If your instrument cannot tell one-emission from zero-emissions, it is not a witness. Pair it with `emit_misses()`: a refused export (a rejected key) is counted there, and a zero is only meaningful with a positive control.

> An *inner* span created inside `ctx.run` is not evidence of replay-safety. The journal records the **return value**, not the spans exported as a side effect, so an inner span re-exports on replay like any other un-journaled effect.

## Why this is in the library (0.2.0 reverses 0.1.0)

Version 0.1.0 deliberately did **not** promote this: it was a composition over the public ingestion API and coupled to a runtime's journal semantics, and putting it in a four-dependency package seemed unjustified. That reasoning no longer holds. Langfuse v4 (cloud, 2026-11-16) removed the legacy ingestion leg the composition used, and its replacement needs the SDK's private tracer internals (`_otel_tracer`, its resource, processor and instrumentation scope). Those belong behind **one fail-soft wall in the library**, tested against the pinned SDK range (`langfuse>=4.7.0,<6`), not copied into every consumer where each copy drifts. The library stays runtime-neutral: nothing in it names a runtime's API; `ctx.run` appears only here, as the example.
