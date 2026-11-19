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
| Off unless both keys | `emit.py:114-115`; `spans.py:23-24`; `boundary.py:24-25`; `README.md`, section "Enabling it" | not stated | `test_fail_soft.py`: `test_disabled_is_a_noop`; `test_boundary_v4.py`: `test_disabled_is_noop`; `test_traced.py`: `test_disabled_is_passthrough` | `built` |
| Destination is the SDK's; default host; deprecated name | langfuse 4.18.0, `_client/environment_variables.py:38-52`; `README.md:34` | — | — | `built` |
| Batch processor, OTLP over HTTP, default path | langfuse 4.18.0, `_client/span_processor.py:23-25`, `:98`; `_client/environment_variables.py:55-62` | — | — | `built` |
| Never raises; counter and unit | `emit.py:37-63` | not stated | `test_fail_soft.py`: `test_langfuse_outage_is_soft_and_counted` | `built` |
| Export witness wraps once | `emit.py:66-111` | not stated | `test_boundary_v4.py`: `test_witness_counts_refused_export`, `test_witness_counts_raising_export`, `test_witness_success_is_flat`, `test_witness_install_twice_does_not_double_count`, `test_witness_concurrent_install_does_not_double_count`, `test_control_without_witness_counter_is_flat` | `built` |
| Installed by four calls | `emit.py:130`, `:352`; `spans.py:75`; `boundary.py:144`; absent from `emit.py:222-254` and `spans.py:92-122` | not stated | no test | `built` |
| Switches off with one warning | `emit.py:93-102`; `README.md`, section "Upgrading the Langfuse client" | not stated | `test_boundary_v4.py`: `test_witness_absent_shape_warns_once_not_a_miss` | `built` |
| A zero is not proof | `emit.py:47-55` | not stated | — | `built` |
| `flush` | `emit.py:118-133` | not stated | `test_boundary_v4.py`: `test_flush_disabled_noop`, `test_flush_makes_spans_visible`, `test_flush_error_is_counted` | `built` |
| Counting is private; a consumer imports it | `emit.py:60`; `__init__.py:16-38`; edgy-solutions/invincible-agent at `6b3e8ef`: `baml_shared/telemetry.py:248-251` | not stated | — | `built` |
| The outage test reaches the missing-SDK branch | `tests/test_fail_soft.py:19-34`; `emit.py:231-236` | not stated | — | `built` |
