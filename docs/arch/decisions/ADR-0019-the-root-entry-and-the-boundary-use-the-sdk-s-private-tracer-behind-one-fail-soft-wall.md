# ADR-0019 The root entry and the boundary use the SDK's private tracer, behind one fail-soft wall

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-ENTRY](../components/trace-entry.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

To build a root on a chosen trace id, and to export the boundary span, the library uses the SDK's private tracer, its processor and its instrumentation scope. The export witness reaches the processor list the same way.

## Why

The SDK's public calls cannot start a span on a chosen trace id with no parent. Keeping the private access in one library keeps it tested against the declared SDK range.

## Consequences

An SDK upgrade can move these internals. The README's upgrade section says what to re-run. If the witness finds the shape gone it warns once and stops counting; the README tells a maintainer to treat that warning as a failure.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Private access | `emit.py:94`, `:283`, `:306-307`; `boundary.py:145`, `:170-171` | `test_boundary_v4.py`: `test_witness_absent_shape_warns_once_not_a_miss` | `built` |
| Upgrade procedure | `README.md:172-187` | — | `built` |
