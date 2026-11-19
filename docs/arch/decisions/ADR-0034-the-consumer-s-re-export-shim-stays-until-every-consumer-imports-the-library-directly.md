# ADR-0034 The consumer's re-export shim stays until every consumer imports the library directly

## Status

`built`. Enforced in the consumer, not this repository.

## Decision

The consumer read for these records keeps a shim that re-exports the library under its older names. It is removed once every consumer imports `provenance_telemetry` directly.

## Why

The move to this library is expand and contract (edgy-solutions/invincible-agent ADR-0038): old imports keep working while callers move.

## Consequences

Enforced in the consumer, by a removal marker in the shim. The library knows nothing of it.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The marker | edgy-solutions/invincible-agent: `baml_shared/telemetry.py:8-12` | — | `built` in the consumer |
