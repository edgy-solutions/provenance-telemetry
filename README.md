# provenance-telemetry

**Telemetry is your provenance doctrine projected into an observability backend:** trace identity from artifact keys (never LLM-derived), user/session from your identity key, span attributes and scores from the fields your system of record already uses — so a trace and a decision record tell the same story *in the same words*, and adopters inherit the **vocabulary, not just the plumbing**.

**The dependency list *is* the adoption pitch.** Four dependencies — `langfuse`, `opentelemetry-api`, `pydantic`, `pyyaml` — one doctrine, config-governed vocabulary. This library ships **no vocabulary of its own**: which of *your* provenance fields map onto which Langfuse slot is a small ratifiable mapping config *you* supply. That is what lets any team adopt it without importing anyone else's domain — and what keeps a security review's read of this `README` + `pyproject` short.

---

## Install

```toml
# pyproject.toml — from PyPI (preferred)
dependencies = ["provenance-telemetry>=0.1.0,<0.2"]
```

```toml
# pyproject.toml — direct from git, pinned to a TAG (pre-index form)
dependencies = [
  "provenance-telemetry @ git+https://github.com/edgy-solutions/provenance-telemetry.git@v0.1.0",
]
```

> **Never a floating ref.** A `git+https://…` with no `@ref` resolves to the default branch **at build time**, so a single upstream commit changes what every consuming service ships — with nobody deciding, and no diff in the consumer's repo to review. This is not hypothetical: a sibling package renamed its *distribution* on `master`, and every consumer floating on that branch broke on the next clean resolve, while machines holding a stale install kept working so the repo looked healthy. Pin to a tag, or to a version once it is on an index.

> **The distribution name is `provenance-telemetry`; the import name is `provenance_telemetry`.** These are different namespaces and they are allowed to diverge — which is exactly how the failure above happened, because a rename of one is invisible to code that only ever types the other. **The import name is the load-bearing one and will not change without a major version.** If the distribution is ever renamed, `import provenance_telemetry` keeps working and only your dependency *declaration* needs editing.

## Enabling it

Everything in this library is **inert unless both** of these are set:

```bash
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://langfuse.example.com   # read by the langfuse SDK itself
```

With either missing, every entry point becomes a pass-through: context managers yield, decorators return the undecorated function, emitters return without emitting. **No-credentials code carries no runtime dependency on Langfuse being reachable.**

> ⚠️ **`traced` gates at DECORATION time**, i.e. at module import. If you set the environment *after* importing the module that uses `@traced`, the decorator has already resolved to pass-through. This matches the deployment model (env set before the process starts) but bites in notebooks and tests. `observed_trace`, `observe_span` and `set_trace_standard` gate at **call** time and do not have this constraint.

---

## Quickstart — a traced service entry

The shape used across a real ten-engine mesh: join the caller's trace on an inbound header, enrich it from your provenance values, and let everything inside nest automatically.

```python
from fastapi import FastAPI, Request
from provenance_telemetry import load_mapping, observed_trace, observe_span

MAPPING = load_mapping("config/mesh-mapping.yaml")   # shape-validated at load
app = FastAPI()

@app.post("/analyze")
async def analyze(req: Request, body: dict):
    values = {
        "request_key": req.headers.get("X-Trace-Id"),  # -> trace_id slot: THE JOIN
        "authz_id":    req.headers.get("X-Authz-Id"),  # -> user_id slot
        "session_id":  body.get("session_id"),
        "engine":      "analyst",
        "verb":        "analyzeWithCodeAgent",
        "domain":      body.get("domain"),
    }
    with observed_trace(MAPPING, values, name="analyze"):
        with observe_span("plan", verb=values["verb"]):
            plan = build_plan(body)
        return run(plan)
```

**What makes this a join and not a new trace:** `observed_trace` reads the field your mapping puts in the `trace_id` slot (`request_key` above) and derives a deterministic Langfuse id from it via `create_trace_id(seed=...)`. Two services handed the **same** `X-Trace-Id` compute the **same** Langfuse trace id, so their spans land on **one** trace. The join is native, not a reconciliation step.

If the seed field is absent, `observed_trace` opens a fresh trace instead — which is correct, but means **a caller that forgets the header silently gets an orphan trace rather than an error.** If joins are load-bearing for you, assert the header's presence in your own code; this library will not refuse the work to protect the telemetry.

### Propagating the trace to the next hop

The join only holds if the id travels. Send it on every outbound call:

```python
headers = {"X-Trace-Id": values["request_key"], "X-Authz-Id": values["authz_id"]}
httpx.post(next_engine_url, json=payload, headers=headers)
```

---

## API

### `load_mapping(source) -> Mapping`

Accepts a path or a dict. **Shape-validated at load**: an unknown Langfuse slot or score encoding raises `pydantic.ValidationError` immediately.

Two-tier validation is deliberate. This library validates **shape** — `KNOWN_SLOTS` (`trace_id`, `user_id`, `session_id`, `release`, `version`) and `KNOWN_SCORE_ENCODINGS` (`ordinal`, `fraction`, `binary_per_join`, `count_total`) are closed sets. It does **not** validate that the provenance field names on the right-hand side exist — that is **truth**, and it belongs with whoever owns the vocabulary. Add a CI check in *your* repo asserting your mapping's field names exist in your contracts; that is the half this library cannot do for you, and skipping it is how a mapping quietly projects `None` forever.

### `observed_trace(mapping, values, *, name="operation", as_type="span")`

Context manager. **The entry primitive** — opens or *joins* a trace on the mapped `trace_id`, then enriches it. Everything opened inside nests under it via the ordinary OTel context.

### `set_trace_standard(mapping, values)`

Enrich the **current** trace in place: identity slots, tags, metadata as OTel attributes, plus scores. Use when something you learned *later* in the request belongs on the trace.

**It cannot set the trace id** — under Langfuse v4 a trace's id is fixed at creation. Choose the id at the entry with `observed_trace`. Calling this with a `trace_id` slot mapped is not an error; the slot is simply skipped.

### `observe_span(operation, **attributes)` / `litellm_metadata(operation, ...)`

Two carriers for **one** span shape (both derive from `span_descriptor`), so a direct-provider call and a LiteLLM-proxied call emit comparable spans:

```python
# direct provider — explicit span; a generation created inside nests automatically
with observe_span("classify", model="gpt-oss", domain=domain) as d:
    result = client.chat.completions.create(...)

# through a LiteLLM proxy — feed the callback metadata instead
import litellm
litellm.completion(model="gpt-4o-mini", messages=msgs,
                   metadata=litellm_metadata("classify", trace_id=tid, user_id=uid,
                                             session_id=sid, tags=["analyst"], domain=domain))
```

### `traced(name=None, as_type=None)`

Decorator that opens a span/trace around a function. For a top-level entry that must open on a **chosen** id, use `observed_trace` — `traced` wraps Langfuse's `observe`, which mints its own id and therefore **cannot join**. See the decoration-time gating warning above.

### `redact(value) -> str`

**Hash, don't drop.** Returns `sha1:<16 hex>`. A redacted trace stays *joinable* — two traces referencing the same value still collide on the hash — without carrying the content. Applied automatically to any field listed in `content_bearing`; call it directly for ad-hoc values.

`is_redacted(value)` also exists but is **not** exported at top level in this release — import it as `from provenance_telemetry.redact import is_redacted`.

### `emit_misses() -> int`

**Fail-soft is only honest if it is countable.** Every soft failure — SDK absent, Langfuse unreachable, a bad score, an enrichment error — increments this counter and logs a warning; nothing raises. Telemetry must not stop the work it observes, but *silent* telemetry loss is indistinguishable from a healthy quiet system. Export it:

```python
@app.get("/health")
def health():
    return {"status": "ok", "telemetry_misses": emit_misses()}
```

A rising count means you are flying blind and do not know it. Alert on the **derivative**, not the value.

---

## The mapping config (you supply this)

```yaml
version: 1
slots:                       # langfuse slot  ->  your provenance field
  trace_id:  request_key
  user_id:   authz_id
  session_id: session_id
tags:        [engine, verb, domain]
metadata:    [subject_class, resolved_via, chart_version]
scores:                      # honest-degradation signals, projected from your schema
  confidence_tier: {encoding: ordinal}
  needs_review:    {encoding: fraction}
  coherence:       {encoding: binary_per_join}
  crops_failed:    {encoding: count_total}
content_bearing: [mpn, notice_id, snippet, matched_text, override_reason]
```

The field *names* on the right are yours. This library never names them in its source (a deletion seal enforces it) — they live only in your mapping, checked for truth by you. See [`examples/mesh-mapping.example.yaml`](examples/mesh-mapping.example.yaml).

---

## Recipes

- **[Durable execution (Restate, Temporal, any replaying runtime)](docs/durable-execution.md)** — the entry primitive is **not** replay-safe on its own, and the failure is invisible in a green test suite. Read this before instrumenting a durable handler.

## Non-goals

- **It will not refuse your work.** Every failure path is soft. If a trace *must* exist for compliance, that is a check you own; this library is a witness channel, not a gate.
- **It does not own your vocabulary.** No provenance field name appears in this source, by design and by test.
- **It does not verify your mapping is true** — only that it is well-shaped. See the two-tier split above.
