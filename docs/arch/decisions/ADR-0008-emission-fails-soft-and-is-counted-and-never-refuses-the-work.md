# ADR-0008 Emission fails soft and is counted, and never refuses the work

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-ENTRY](../components/trace-entry.md), [CO-SPANS](../components/span-carriers.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

Nothing the library does raises into the caller's work. A failure is logged and counted, and the work goes on. A missing seed opens a fresh trace rather than raising.

## Why

The library is a witness channel, not a gate: the observing channel must never break the observed work. The README lists "it will not refuse your work" as a non-goal and tells a caller who needs a trace to exist to check that itself. edgy-solutions/invincible-agent ADR-0038 sets the rule.

## Consequences

A caller that forgets its seed gets an orphan trace and no error (`README.md:72`). The test named for an outage reaches the missing-SDK branch, not a refusing server ([CO-WITNESS](../components/emission-witness.md), finding 11). Counting a miss is a private function, which the consumer read for these records imports by name.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Never raises; counted | `emit.py:37-63` | `test_fail_soft.py`: `test_langfuse_outage_is_soft_and_counted` | `built` |
| Non-goal | `README.md:226-228` | — | `built` |
| A missing seed opens a fresh trace | `README.md:72`; `emit.py:364-366` | `test_entry_parent_v4.py`: `test_case_a_no_seed_unchanged` | `built` |
