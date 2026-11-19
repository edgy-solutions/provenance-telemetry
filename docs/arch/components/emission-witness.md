# Emission witness (CO-WITNESS)

The emission witness is how the library fails, and how a failure can still be seen. Every entry point is off unless two keys are set. Once on, nothing the library does may raise into the caller's work: each failure is logged and added to a counter instead. A refused export happens in the SDK's own exporter thread, where the caller never sees it, so the library wraps the SDK's exporter to count those too. `flush` sends what is pending, for a process that is about to exit. The export itself, and where it goes, is the SDK's.

This record covers what the code provides by default, and what a caller may set. It describes no particular caller, except where a row says which consumer it read.

**This record describes; it proposes nothing.** Statuses are those of [the README](../README.md). Line numbers are at the leaf pin listed there (`e84fd29`). The record shape is provisional.

## Findings

1. **Off unless both keys are set.** Every entry point first checks that `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are both non-empty. If either is missing, context managers yield, emitters return, and the decorator returns the function unchanged; nothing is counted. The check is repeated in three modules. `built`
2. **The destination is the SDK's choice.** The library names no host. The SDK reads the host from its environment and, when it is unset, defaults to the vendor's cloud service. So a process with the two keys and no host exports there. The library's README names `LANGFUSE_HOST`; the SDK version read marks that name deprecated in favour of `LANGFUSE_BASE_URL`, and still reads it. `built`
3. **The SDK exports in batches, as OTLP over HTTP.** Spans go through the SDK's span processor, a batch processor, to an OTLP HTTP exporter. The path on the host defaults to `/api/public/otel/v1/traces`. The library adds no transport of its own. `built`
4. **Nothing the library does raises into the caller.** Each entry point catches its own errors, counts a miss, logs a warning and lets the work go on. The miss counter is a process-wide integer behind a lock, read through `emit_misses()`. Its unit is failed calls plus spans lost on export. `built`
5. **The export witness counts what the exporter thread loses.** On first use, the library finds the SDK's exporters behind its span processors and wraps each one once. A raised export, or a result other than success, adds the number of spans in that batch to the counter. The wrapper re-raises, so the SDK's own handling is unchanged. Installing twice, or from two threads at once, wraps each exporter once. `built`
6. **The witness is installed by four calls, not all six.** `observed_trace`, `observe_span`, `emit_boundary` and `flush` install it. `set_trace_standard` and `traced` do not. A process that traces only through `traced` never counts a refused export. `built`
7. **If the SDK's internals have moved, the witness switches itself off with one warning.** It reaches the SDK's private tracer and processor list. When that shape is absent, it logs one warning per process and counts nothing, so the counter stops seeing lost exports while every call still works. The README tells a maintainer to treat that warning in a test run as a failure. `built`
8. **A zero is not proof.** The counter's own docstring says so: a zero means no failure was seen, and a backend that accepts and then drops a span is not seen. Proof that spans land needs a known span read back from the store. The library ships no such check. `built`
9. **`flush` sends the pending batch now.** It does nothing when off. When on, it installs the witness and asks the SDK to flush; a failure counts one miss. `built`
10. **A caller cannot count its own miss through the public surface.** The counting function is private. The consumer read for these records imports it by its private name, so a consumer's soft failures can join the same counter. `built`
11. **The outage test reaches the missing-SDK branch, not an outage.** `test_langfuse_outage_is_soft_and_counted` replaces the SDK with a module shaped like a much older SDK. The current code then fails to import the client and counts that as "unavailable". A server that refuses is exercised instead by the witness tests, which give the real SDK an exporter that fails. `built`

## Connections

One row per connection. Ids are those of [the README](../README.md#element-ids). Direction is one of: calls, is called by, reads, writes. Evidence paths are at the leaf pin, under `provenance_telemetry/`, unless the row says otherwise. Every connection here is inside the caller's process: the component opens no socket and signs in to nothing. The one authenticated hop, the SDK's export to XE-STORE, is the SDK's and is drawn in [FL-TRACE](../flows/agent-call-to-trace-store.md), step 19. Status is one of the four in [the status vocabulary](../README.md#status-vocabulary); every row here is `built`, and its evidence is the file and line at the leaf pin.

| Other | Direction | Protocol | Authentication | What passes | Status | Evidence |
|---|---|---|---|---|---|---|
| XE-CALLER | is called by | in-process Python call | none: same process | `emit_misses()`, returned as the count; `flush()` | `built` | `__init__.py:10`; `emit.py:47-58`, `:118-133` |
| CO-ENTRY | is called by | in-process Python call | none: same process | the SDK client to wrap; a miss and its reason | `built` | `emit.py:352`, `:359`, `:362`, `:383`, `:391` |
| CO-SPANS | is called by | in-process Python call | none: same process | the SDK client to wrap; a miss and its reason | `built` | `spans.py:73-79`, `:87-88` |
| CO-BOUNDARY | is called by | in-process Python call | none: same process | the SDK client to wrap; a miss and its reason | `built` | `boundary.py:59`, `:104`, `:144`, `:177` |
| XE-SDK | calls | in-process Python call, through the SDK's private tracer and processor list | none at the call; the SDK holds the keys | each exporter's `export`, replaced once by a counting wrapper; a flush request | `built` | `emit.py:85-111`, `:129-131` |
| XE-SDK | is called by | in-process Python call, on the SDK's exporter thread | none: same process | each batch of spans, and the export's result or error | `built` | `emit.py:66-82` |
| XE-ENV | reads | environment variable | none: same process | whether both keys are set | `built` | `emit.py:114-115` |
| XE-LOG | writes | Python logging, logger `provenance_telemetry` | none: same process | one warning per miss, with its reason; one warning when the SDK's shape is absent | `built` | `emit.py:35`, `:63`, `:98-102`, `:111` |

## Settings and defaults

| Setting | Code default | What it does |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | unset: everything off | both must be set |
| `LANGFUSE_BASE_URL`, or the older `LANGFUSE_HOST` (read by the SDK) | the vendor's cloud service | where spans are exported |
| `LANGFUSE_OTEL_TRACES_EXPORT_PATH` (read by the SDK) | `/api/public/otel/v1/traces` | the export path on that host |
| logger `provenance_telemetry` | the host's logging setup | each miss is one warning on it |

## Gaps

- **The counter lives in the process and nothing publishes it** (findings 4, 8). A consumer must export it as a metric itself, and pair it with a read-back. `not built` in the library
- **Two entry points never install the witness** (finding 6). `built`
- **No public way to count a consumer's miss** (finding 10). `not built`
- **The outage test is mislabelled** (finding 11): its name says outage, its path is a missing SDK. `built`

## Not established from code

- How many spans the batch processor holds, and for how long, before export. Those are the SDK's and the OpenTelemetry SDK's defaults and settings; this record did not read them.
- Whether any consumer publishes `emit_misses()`. In the consumer read for these records, the shim counts its own misses into it; this record did not trace where, if anywhere, the count is exposed.

## Sources

All paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` unless the row names another repository. Library paths are under `provenance_telemetry/`.

| Claim | Source | Decision | Evidence | Status |
|---|---|---|---|---|
| Off unless both keys | `emit.py:114-115`; `spans.py:23-24`; `boundary.py:24-25`; `README.md`, section "Enabling it" | [ADR-0007](../decisions/ADR-0007-without-both-keys-the-library-does-nothing.md) | `test_fail_soft.py`: `test_disabled_is_a_noop`; `test_boundary_v4.py`: `test_disabled_is_noop`; `test_traced.py`: `test_disabled_is_passthrough` | `built` |
| Destination is the SDK's; default host; deprecated name | langfuse 4.18.0, `_client/environment_variables.py:38-52`; `README.md:34` | — | — | `built` |
| Batch processor, OTLP over HTTP, default path | langfuse 4.18.0, `_client/span_processor.py:23-25`, `:98`; `_client/environment_variables.py:55-62` | — | — | `built` |
| Never raises; counter and unit | `emit.py:37-63` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | `test_fail_soft.py`: `test_langfuse_outage_is_soft_and_counted` | `built` |
| Export witness wraps once | `emit.py:66-111` | [ADR-0009](../decisions/ADR-0009-the-export-witness-counts-spans-lost-on-export-and-a-zero-is-not-proof.md) | `test_boundary_v4.py`: `test_witness_counts_refused_export`, `test_witness_counts_raising_export`, `test_witness_success_is_flat`, `test_witness_install_twice_does_not_double_count`, `test_witness_concurrent_install_does_not_double_count`, `test_control_without_witness_counter_is_flat` | `built` |
| Installed by four calls | `emit.py:130`, `:352`; `spans.py:75`; `boundary.py:144`; absent from `emit.py:222-254` and `spans.py:92-122` | [ADR-0009](../decisions/ADR-0009-the-export-witness-counts-spans-lost-on-export-and-a-zero-is-not-proof.md) | no test | `built` |
| Switches off with one warning | `emit.py:93-102`; `README.md`, section "Upgrading the Langfuse client" | [ADR-0019](../decisions/ADR-0019-the-root-entry-and-the-boundary-use-the-sdk-s-private-tracer-behind-one-fail-soft-wall.md) | `test_boundary_v4.py`: `test_witness_absent_shape_warns_once_not_a_miss` | `built` |
| A zero is not proof | `emit.py:47-55` | [ADR-0009](../decisions/ADR-0009-the-export-witness-counts-spans-lost-on-export-and-a-zero-is-not-proof.md) | — | `built` |
| `flush` | `emit.py:118-133` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | `test_boundary_v4.py`: `test_flush_disabled_noop`, `test_flush_makes_spans_visible`, `test_flush_error_is_counted` | `built` |
| Counting is private; a consumer imports it | `emit.py:60`; `__init__.py:16-38`; edgy-solutions/invincible-agent at `6b3e8ef`: `baml_shared/telemetry.py:248-251` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | — | `built` |
| The outage test reaches the missing-SDK branch | `tests/test_fail_soft.py:19-34`; `emit.py:231-236` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | — | `built` |
