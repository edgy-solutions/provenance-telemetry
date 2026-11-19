# ADR-0020 A step that dies leaves a missing parent, never a phantom one

## Status

`accepted`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

If a durable handler dies before the boundary is exported, its children appear as roots on the right trace. The library never exports a boundary it cannot vouch for.

## Why

The recipe calls this deliberate: an absent span reads as absent.

## Consequences

No test kills a step and reads the trace back from a store.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The failure mode | `docs/durable-execution.md:70` | no test | `accepted` |
