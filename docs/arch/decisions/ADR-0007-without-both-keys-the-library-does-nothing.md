# ADR-0007 Without both keys the library does nothing

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-ENTRY](../components/trace-entry.md), [CO-SPANS](../components/span-carriers.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

Every entry point does nothing unless `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are both set. `traced` reads them when it decorates; everything else reads them on each call.

## Why

A service can import and call the library with no trace store configured, and runs the same as without it.

## Consequences

A process that sets the keys after importing a module decorated with `traced` is not traced by it ([CO-SPANS](../components/span-carriers.md), finding 5).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The gate | `emit.py:114-115`; `spans.py:23-24`, `:104-106`; `boundary.py:24-25` | `test_fail_soft.py`: `test_disabled_is_a_noop`; `test_traced.py`: `test_disabled_is_passthrough`; `test_boundary_v4.py`: `test_disabled_is_noop` | `built` |
