# ADR-0016 Trace attributes propagate to children, within limits

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-ENTRY](../components/trace-entry.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

Inside an entry, the mapped person, session, version, tags and metadata are passed to every child span. Values that are not ASCII or are over 200 characters stay on the entry only. Release and the trace name are not passed.

## Why

Queries by person or session find child spans too (0.2.0, commit `3f0eed8`). The test asserts the propagated value rather than one SDK's encoding of it (commit `e510d99`).

## Consequences

When a mapping fills `release`, the entry and its children can report different releases ([CO-ENTRY](../components/trace-entry.md), finding 7).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Propagation | `emit.py:181-219` | `test_boundary_v4.py`: `test_observed_trace_propagates_and_drops_bad_values` | `built` |
