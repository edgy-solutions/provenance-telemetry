# Changelog

Every release of `provenance-telemetry`, newest first. Each version is an annotated git tag
(`vX.Y.Z`), and that tag is what publishes to PyPI. Dates are tag dates.

## Unreleased

No package change, so nothing to publish.

- **CI runs Python 3.14.** The package has declared `<3.15` since 0.1.0, but the test matrix stopped at
  3.13, so the 3.14 claim had never been exercised.
- **This file**, and a README section on what to re-test when the Langfuse client is upgraded.
- **An ADR is cited with its repository.** The decisions behind this library are ADRs in another
  repository, so a bare ADR number names nothing a reader can follow. The two bare cites (a
  docstring in `mapping.py` and the example mapping's header) now name their repo, and a test
  refuses any new bare one.
- **`sessions/` is gitignored.** Session files are local working notes for the repo's
  maintainers. They are never committed.

## 0.2.2 — 2026-11-16

- **A seed that is already a W3C trace-id is the trace id.** `trace_id_for(seed)` returns a
  32-lowercase-hex, non-zero seed verbatim, and hashes any other seed with the SDK's
  `create_trace_id` as before. `observed_trace` and `mint_boundary_ids` both use it. A caller that
  received a `traceparent` now joins that trace rather than a hash of it.
- **W3C parsers.** `parse_traceparent`, `parse_tracestate` and `format_traceparent` are pure
  functions, with no SDK involved.
- **`traced` gains `capture_input` and `capture_output`** (keyword-only). They are forwarded to the
  SDK only when set, so leaving them out keeps the SDK's own default.
- **The public surface is 21 names.** CI checks the documented set against `__all__`.

## 0.2.1 — 2026-11-10

- **A joined entry with no known parent is a root.** Before, a seeded `observed_trace` let the
  SDK invent a remote parent span id that was never exported, so the entry pointed at a parent
  that did not exist.
- **New keyword-only `parent_span_id`** (16 hex) travels with the trace id. An ambient span of the
  same trace is used as the parent. An invalid parent, or a parent given with no seed, counts one
  miss and is ignored.
- **The root entry and the boundary take their environment and release from the client**
  (`LANGFUSE_TRACING_ENVIRONMENT`), as every SDK-built span does, so a parent and its children
  can no longer land in different environments.
- **Breaking: `DEPLOY_ENV` is no longer read.** A deployment that relied on it must set
  `LANGFUSE_TRACING_ENVIRONMENT`.

## 0.2.0 — 2026-11-10

Langfuse Cloud went v4-only and stopped accepting the legacy ingestion API, which the
consumer-side replay-safe boundary had used. **This release reverses 0.1.0's choice** to leave the
boundary to consumers.

- **The boundary moved into the library, rewritten over OTLP:** `mint_boundary_ids`,
  `boundary_parent` and `emit_boundary`.
  - The boundary span is built by hand on the SDK tracer's own resource, processor and scope.
  - OTLP does not upsert, so `emit_boundary` must be called exactly once, inside the journaled
    step. See `docs/durable-execution.md`.
- **`emit_misses()` counts spans lost from an export,** whether the export was refused or raised.
  It does this through an export witness: installed lazily, idempotently and under a lock, so a
  concurrent install cannot double-count.
- **Trace attributes propagate to child spans:** user, session, tags and metadata. Values must be
  ASCII and at most 200 characters. `trace_name` is not propagated.
- **`flush()`.**
- **Requires `langfuse>=4.7.0,<6`.** Older SDKs land data late on v4. The ceiling keeps a future
  major release from arriving unreviewed.

## 0.1.0 — 2026-08-07

The first release.

- **It projects a provenance doctrine into Langfuse.** The vocabulary is caller-supplied config;
  the library ships no field names of its own.
- **The public surface is 13 names:** `load_mapping`, `Mapping`, `ScoreSpec`, `KNOWN_SLOTS`,
  `KNOWN_SCORE_ENCODINGS`, `observed_trace`, `set_trace_standard`, `emit_misses`, `observe_span`,
  `litellm_metadata`, `span_descriptor`, `traced` and `redact`.
- **Langfuse v3/v4 (OpenTelemetry).** Cross-service joins are native: the same upstream id on two
  services lands in one trace.
- **Fail-soft and countable.** An outage never raises, and every soft failure increments
  `emit_misses()`.
- **Python `>=3.10,<3.15`, with four dependencies.** The floor was raised from a false `>=3.9`:
  two of the dependencies refuse anything below 3.10.
- **`docs/durable-execution.md`** explains that `observed_trace` is not replay-safe in a replaying
  runtime.
