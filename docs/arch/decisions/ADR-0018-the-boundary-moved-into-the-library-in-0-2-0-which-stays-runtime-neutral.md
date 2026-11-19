# ADR-0018 The boundary moved into the library in 0.2.0, which stays runtime-neutral

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

Version 0.1.0 left the boundary to callers. Version 0.2.0 reverses that and ships it. Nothing in the library names a runtime.

## Why

0.1.0's composition used the trace store's public ingestion API, which the v4 SDK no longer offers. Its replacement needs the SDK's private internals, which belong behind one fail-soft wall here rather than in every consumer ([ADR-0019](ADR-0019-the-root-entry-and-the-boundary-use-the-sdk-s-private-tracer-behind-one-fail-soft-wall.md)).

## Consequences

The rationale's own text names the old range `<6` and gives 2026-11-16 as the date of the SDK change, in a line committed on 2026-11-10. The range is stale and the date cannot be right.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The reversal | `docs/durable-execution.md:91-93`; tag `v0.2.0` | — | `built` |
