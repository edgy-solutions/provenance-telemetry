# Span carriers (CO-SPANS)

The span carriers mark the work done inside an entry, above all a model call. A model call can be traced two ways. Called directly, it needs a span open around it, and the SDK nests the call's generation under that span. Called through a LiteLLM proxy, it needs metadata handed to the proxy's callback. Both ways derive their name and attributes from one descriptor, so a trace from either path reads the same. A decorator, `traced`, opens a span around a whole function. None of the carriers applies the caller's mapping.

This record covers what the code provides by default, and what a caller may set. It describes no particular caller, except where a row says which consumer it read.

**This record describes; it proposes nothing.** Statuses are those of [the README](../README.md). Line numbers are at the leaf pin listed there (`e84fd29`). The record shape is provisional.

## Findings

1. **One descriptor, two carriers.** `span_descriptor` returns a name and the attributes given, without those that are `None`. `observe_span` yields that descriptor; `litellm_metadata` builds from it. Given the same operation and attributes, both carry the same name and attributes, and differ only in the transport keys `litellm_metadata` adds. `built`
2. **`observe_span` opens a child of whatever is current, and writes its attributes as the observation's metadata.** It opens the span through the SDK's public call with no trace context, so the span nests under the current entry or span. Its attributes are written as given. They are not redacted, and the mapping is not consulted. `built`
3. **`litellm_metadata` returns a dict for the proxy's callback.** It carries `generation_name` and the attributes, and, when given, `existing_trace_id`, `trace_user_id`, `session_id` and `tags`. The library's docstring names them as metadata for callbacks that read the request rather than the current span. The library sends nothing itself: the caller passes the dict to the model call, and the proxy's callback decides what reaches the trace. The values are not redacted. `built`
4. **`traced` defers to the SDK on whether a function's input and output are captured.** It forwards `capture_input` and `capture_output` to the SDK's decorator only when the caller sets them. Left unset, the SDK's environment variable decides, and in the SDK version read that variable defaults to capturing. So by default, a function decorated with `traced` sends its arguments and return value to the trace, unredacted. `built`
5. **`traced` decides at decoration time.** The enable gate is read when the decorator is applied, normally at import. A process that sets the keys after importing a decorated module is not traced by that decorator. If the SDK cannot be imported or its decorator fails at that moment, `traced` returns the function unchanged and counts no miss. `built`
6. **`observe_span` is fail-soft and countable; `traced` is fail-soft only.** An error opening or updating an `observe_span` span counts one miss and the block still runs. `traced` never counts (finding 5). `observe_span` also installs the export witness; `traced` does not ([emission witness](emission-witness.md), finding 4). `built`

## Settings and defaults

| Setting | Code default | What it does |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | unset: every carrier is a pass-through | read at each call by `observe_span`; at decoration by `traced` |
| `traced(name=…)`, `traced(as_type=…)` | unset: the SDK's defaults | the span's name and observation type |
| `traced(capture_input=…)`, `traced(capture_output=…)` | unset: the next row decides | `False` keeps arguments or the return value out of the trace |
| `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED` (read by the SDK) | capture on, when unset (langfuse 4.18.0) | the default for both capture flags |

## Gaps

- **A decorated function's input and output go to the trace by default, unredacted** (finding 4). Keeping them out is the caller's setting. `built`
- **Carrier attributes bypass redaction** (findings 2, 3). A caller that passes a content-bearing value as an attribute sends it as written. `built`
- **A `traced` failure is invisible** (findings 5, 6): no miss is counted, and refused exports are counted only if another call installed the witness. `built`

## Not established from code

- What the LiteLLM proxy's callback does with each key of finding 3. That is the proxy's behaviour; no test here exercises a proxy.
- Which consumers turn I/O capture off. The consumer read for these records, `edgy-solutions/invincible-agent`, sets the SDK's capture variable to off in its telemetry shim before the SDK is imported, and its own decorator wrapper passes `capture_input=False` and `capture_output=False`.

## Sources

All paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` unless the row names another repository. Library paths are under `provenance_telemetry/`.

| Claim | Source | Decision | Evidence | Status |
|---|---|---|---|---|
| One descriptor, two carriers | `spans.py:27-32`, `:48-58`, `:67` | [ADR-0013](../decisions/ADR-0013-two-carriers-share-one-span-shape.md) | `test_path_equivalence.py`: `test_carriers_share_one_shape` | `built` |
| `observe_span` nests and writes unredacted metadata | `spans.py:61-89`, `:76`, `:85` | [ADR-0013](../decisions/ADR-0013-two-carriers-share-one-span-shape.md) | `test_boundary_v4.py`: `test_observed_trace_propagates_and_drops_bad_values` (nesting); no test reads the metadata | `built` |
| `litellm_metadata` keys | `spans.py:35-58` | [ADR-0013](../decisions/ADR-0013-two-carriers-share-one-span-shape.md) | `test_path_equivalence.py`: `test_carriers_share_one_shape` | `built` |
| `traced` forwards capture flags only when set | `spans.py:92-122`, `:114-117` | [ADR-0014](../decisions/ADR-0014-traced-opens-a-trace-but-cannot-join-one-and-forwards-capture-flags-only-when-set.md) | `test_w3c_v022.py`: `test_traced_default_passes_neither_capture_key`, `test_traced_capture_false_is_forwarded` | `built` |
| SDK default: capture on | langfuse 4.18.0, `_client/observe.py:119`, `:196-198` | — | — | `built` |
| Decoration-time gate; silent fallback | `spans.py:104-120`; `README.md`, section "Enabling it" | [ADR-0007](../decisions/ADR-0007-without-both-keys-the-library-does-nothing.md) | `test_traced.py`: `test_disabled_is_passthrough`, `test_enabled_still_runs_the_function` | `built` |
| `observe_span` counts; `traced` does not | `spans.py:73-88`; `spans.py:119-120` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | no test for either | `built` |
| Consumer turns capture off | edgy-solutions/invincible-agent at `6b3e8ef`: `baml_shared/telemetry.py:27-31`, `:196-205` | [ADR-0035](../decisions/ADR-0035-model-call-text-stays-out-of-spans-and-labelled-text-is-dropped-not-kept.md) | — | `built` |
