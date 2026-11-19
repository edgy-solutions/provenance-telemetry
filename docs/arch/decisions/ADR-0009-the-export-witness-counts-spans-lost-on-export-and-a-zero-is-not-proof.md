# ADR-0009 The export witness counts spans lost on export, and a zero is not proof

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-WITNESS](../components/emission-witness.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

The library wraps the SDK's exporters once, so a refused or raising export adds the number of spans in that batch to the miss counter. The counter's documentation says a zero means no loss was seen, not that spans arrived; that needs a known span read back from the store.

## Why

Export runs in the SDK's thread, where the caller cannot see a failure. Install was serialised after a concurrent install was found to double-count (commit `57092c1`).

## Consequences

Two entry points, `set_trace_standard` and `traced`, do not install the witness ([CO-WITNESS](../components/emission-witness.md), finding 6). The library ships no read-back check.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Witness | `emit.py:66-111` | `test_boundary_v4.py`: `test_witness_counts_refused_export`, `test_witness_counts_raising_export`, `test_witness_success_is_flat`, `test_witness_install_twice_does_not_double_count`, `test_witness_concurrent_install_does_not_double_count`, `test_control_without_witness_counter_is_flat` | `built` |
| A zero is not proof | `emit.py:47-55`; `README.md:153-155` | — | `built` |
