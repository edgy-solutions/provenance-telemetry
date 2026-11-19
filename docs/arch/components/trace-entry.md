# Trace entry and identity (CO-ENTRY)

The trace entry is where a service's unit of work enters a trace. It opens a new trace or joins one that started upstream, decides the entry span's parent, stamps the caller's mapped fields on the entry, and passes the person, session, tags and metadata to every span opened inside it. The trace id itself comes from a seed the caller supplies, usually the id an upstream service sent. The three W3C Trace Context helpers belong here, because they turn a received header into that seed and parent. For an entry inside a durable runtime that replays its handler, see [replay-safe boundary](replay-safe-boundary.md).

This record covers what the code provides by default, and what a caller may set. It describes no particular caller, except where a row says which consumer it read.

**This record describes; it proposes nothing.** Statuses are those of [the README](../README.md). Line numbers are at the leaf pin listed there (`e84fd29`). The record shape is provisional.

## Findings

1. **The entry is a context manager, `observed_trace`.** It takes a mapping, the caller's values, a name, an observation type and an optional parent span id. The body always runs. If setting up the trace fails, the failure is counted and the body runs untraced ([emission witness](emission-witness.md)). `built`
2. **The seed is the value of the mapping's `trace_id` slot.** With no such slot, or no value for it, there is no seed.
   - **No seed:** the SDK decides. The entry nests under whatever span is current, else it starts a new trace with an id the SDK mints.
   - **A seed and a parent:** the entry joins the seeded trace under that parent. The parent is the one passed in, or, when none is passed, a current span that belongs to the same trace.
   - **A seed and no parent:** the entry is the trace's root. The library builds it without a parent rather than let the SDK invent one.
   `built`
3. **A seed becomes a trace id in one of two ways.** A seed that is already a W3C trace id (32 lowercase hex characters, not all zeros) is used unchanged, and that needs no SDK. Any other non-empty seed is hashed by the SDK into a trace id, so the same seed on two services gives the same trace. An empty seed gives none. `built`
4. **A bad parent is counted and dropped.** A parent span id that is not 16 hex characters, or is all zeros, counts one miss and is ignored. So does a parent passed with no seed. `built`
5. **The root entry is built by hand on the SDK's private tracer.** The SDK's public call cannot start a root on a chosen trace id, so the library builds the span itself, on the SDK tracer's own processor and scope, and stamps it with the client's environment and release, as the SDK stamps its own spans. `built`
6. **The entry span gets the mapped fields; children get a subset.** On entry, the mapped person, session, release, version, tags and metadata are set on the entry span. The person, session, version, tags and metadata are then passed to every child span opened inside. Release and the trace name are never passed. A value that is not ASCII, or is over 200 characters, is left off the children and stays on the entry. `built`
7. **A mapped release and the client's release can disagree within one trace.** When the mapping fills the `release` slot, the entry span carries the mapping's value, written over the client's. Its children carry the client's, because release is not passed down. On a boundary span the order is the other way, and the client's release wins ([replay-safe boundary](replay-safe-boundary.md), finding 5). The tests for a shared environment and release use a mapping with no `release` slot. `built`
8. **`set_trace_standard` writes onto whatever span is current.** It sets the mapped fields on the active span and sends the mapping's scores to the current trace. It cannot set the trace id. With no active span, the attributes land on the empty placeholder span and are lost, and no miss is counted. `built`
9. **The W3C helpers are pure functions.** `parse_traceparent` returns the trace id, parent id and flags, or nothing for an invalid header or for two headers. `parse_tracestate` returns the normalised list or nothing, and trims it from the right past 512 characters. `format_traceparent` writes a version-00 header. The library reads and writes no HTTP headers itself; the caller carries the header and hands its parts to the entry. `built`
10. **Two docstrings still describe the seed as always hashed.** The module's opening docstring and `observed_trace`'s docstring say the trace id comes from the SDK's seeded hash. Since 0.2.2 a W3C seed is used unchanged (finding 3); the code and its tests say so, and the docstrings do not. `built`

## Settings and defaults

| Setting | Code default | What it does |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | unset: the entry yields and traces nothing | both must be set; read at each call |
| `name` | `"operation"` | the entry span's name |
| `as_type` | `"span"` | the entry's observation type |
| `parent_span_id` | none | the caller's own span id, sent with the trace id |
| `LANGFUSE_TRACING_ENVIRONMENT` (read by the SDK) | the SDK's default | the environment stamped on a root entry and on the SDK's own spans |
| `LANGFUSE_RELEASE` (read by the SDK) | the SDK's fallbacks | the release stamped the same way |

## Gaps

- **Entry and children can report different releases** when a mapping fills `release` (finding 7). Untested. `built`
- **`set_trace_standard` outside an entry is silent** (finding 8): nothing is emitted and nothing is counted. `built`
- **Two docstrings are stale** (finding 10). `built`

## Not established from code

- Whether every consumer sends the parent span id with the trace id. Where it does not, the entry is a root on the right trace and its link to the caller's span is lost. In the consumer read for these records, `edgy-solutions/invincible-agent`, three HTTP receivers drop the parent: the middlewares of engine-w and engine-f, and the analyst's `/analyze` proxy, which forwards the trace id and not the parent. The flow record traces each.
- Whether every consumer maps the person. In that consumer, four engine entries pass no person value, so their spans carry no user id. This is recorded in the flow record.

## Sources

All paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` unless the row names another repository. Library paths are under `provenance_telemetry/`.

| Claim | Source | Decision | Evidence | Status |
|---|---|---|---|---|
| A context manager; body always runs | `emit.py:329-394`, `:382-385` | not stated | `test_v4.py`: `test_observed_trace_passthrough_when_disabled`; `test_entry_parent_v4.py`: `test_body_exception_in_d_propagates_and_marks_error` | `built` |
| Seed, parent and root: three branches | `emit.py:353-381` | not stated | `test_entry_parent_v4.py`: `test_case_a_no_seed_unchanged`, `test_case_b_valid_parent_travels_with_trace_id`, `test_case_c_ambient_span_of_same_trace_is_the_parent`, `test_case_d_seed_no_parent_is_root`, `test_control_for_d_sdk_path_invents_a_parent` | `built` |
| W3C seed verbatim, else hashed, empty is none | `emit.py:313-326` | not stated | `test_w3c_v022.py`: `test_w3c_seed_is_verbatim_and_needs_no_langfuse`, `test_dashed_uuid_seed_control_equals_create_trace_id`, `test_non_w3c_seeds_are_hashed`, `test_empty_seed_is_none`, `test_observed_trace_opens_on_w3c_seed_and_parent`, `test_observed_trace_w3c_seed_no_parent_is_root_on_that_id` | `built` |
| Bad parent counted and dropped | `emit.py:257-264`, `:357-363` | not stated | `test_entry_parent_v4.py`: `test_case_e_invalid_parent_counts_one_miss_then_root`, `test_case_f_parent_without_seed_counts_one_miss` | `built` |
| Root built by hand; environment and release stamped | `emit.py:267-310` | not stated | `test_entry_parent_v4.py`: `test_case_d_root_carries_the_environment_and_release_its_children_carry` | `built` |
| Mapped fields on the entry; subset to children | `emit.py:150-178`, `:181-219`, `:387-394` | not stated | `test_boundary_v4.py`: `test_observed_trace_propagates_and_drops_bad_values`, `test_set_trace_standard_attributes_pinned` | `built` |
| Mapped release over the client's on the entry only | `emit.py:295-299` then `:389` → `:240-241`; release absent from `:193`; contrast `boundary.py:154-160` | not stated | no test: the release tests' mapping has no `release` slot (`test_boundary_v4.py:21-25`) | `built` |
| `set_trace_standard` writes onto the current span | `emit.py:222-254`, `:239-241` | not stated | `test_v4.py`: `test_set_trace_standard_noop_when_disabled`; `test_boundary_v4.py`: `test_set_trace_standard_attributes_pinned`; no test outside an entry | `built` |
| W3C helpers are pure | `w3c.py:1-92` | not stated | `test_w3c_v022.py`: `test_valid_00`, `test_invalid_traceparent`, `test_higher_version_with_suffix_accepted`, `test_two_traceparent_headers_rejected`, `test_format_traceparent_roundtrip`, the six `test_tracestate_*` tests | `built` |
| Stale docstrings | `emit.py:11-12`, `:334-336` | not stated | — | `built` |
| SDK settings for environment and release | langfuse 4.18.0, `_client/client.py:346-353` | — | — | `built` |
| Consumer: three receivers without a parent | edgy-solutions/invincible-agent at `6b3e8ef`: `agent_fleet/weaviate_expert/main.py:382-392`; `agent_fleet/presentation_agent/main.py:192-202`; `agent_fleet/restate_analyst/main.py:4350-4356` | edgy-solutions/invincible-agent ADR-0038 | — | `built` |
