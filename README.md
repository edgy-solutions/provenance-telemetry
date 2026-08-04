# provenance-telemetry

**Telemetry is your provenance doctrine projected into an observability backend:** trace identity from artifact keys (never LLM-derived), user/session from your identity key, span attributes and scores from the fields your system of record already uses — so a trace and a decision record tell the same story *in the same words*, and adopters inherit the **vocabulary, not just the plumbing**.

**The dependency list *is* the adoption pitch.** Four dependencies — `langfuse`, `opentelemetry-api`, `pydantic`, `pyyaml` — one doctrine, config-governed vocabulary. This library ships **no vocabulary of its own**: which of *your* provenance fields map onto which Langfuse slot is a small ratifiable mapping config *you* supply. That is what lets any team adopt it without importing anyone else's domain — and what keeps a security review's read of this `README` + `pyproject` short.

## What it does

- **`load_mapping(path)`** — read a ratifiable mapping config and **validate its *shape* at load** (an unknown Langfuse slot or score encoding is refused). The library validates shape; *you* validate truth (a CI check in your own repo that the field names your mapping references actually exist in your contracts).
- **`set_trace_standard(mapping, values)`** — project your provenance `values` onto the current Langfuse trace (id / user_id / session_id / tags / metadata / scores) per the mapping. **Fail-soft:** a Langfuse outage or missing SDK is logged and *counted* (`emit_misses()`), never raised — telemetry emission must not stop the work it observes.
- **`observe_span(op, **attrs)` / `litellm_metadata(op, **attrs)`** — two carriers for one span shape: explicit spans for direct-provider calls, and a metadata dict that nests a LiteLLM generation under your trace. Both derive from the same `span_descriptor`, so the two environments emit the *same* shape and stay comparable.
- **`redact(value)`** — content-bearing fields are **hashed, not dropped** (`sha1:` prefix): a redacted trace stays *joinable* for debugging without exposing content.

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

The field *names* on the right are yours. This library never names them in its source (a deletion seal enforces it) — they live only in your mapping, checked for truth by you.
