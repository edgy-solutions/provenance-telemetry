# ADR-0021 The boundary is witnessed by a manufactured replay: fail, do not kill

## Status

`built`. Enforced in this repository.

## Decision

The boundary's test forces a replay by failing after the work, and asserts the span count.

## Why

Killing the process also causes a replay, but leaves nothing to tell "exported once" from "never exported" at that instant.

## Consequences

The test runs against an in-memory exporter, not a runtime or a store.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The method | `docs/durable-execution.md:75-89` | `test_boundary_v4.py`: `test_replay_shape` | `built` |
