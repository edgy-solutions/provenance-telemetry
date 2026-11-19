# ADR-0002 The library is a standalone package outside its consumers

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-MAPPING](../components/mapping-and-redaction.md), [CO-ENTRY](../components/trace-entry.md), [CO-SPANS](../components/span-carriers.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

The library is its own repository and distribution. It imports nothing from any consumer and is named for what it does.

## Why

edgy-solutions/invincible-agent ADR-0038 places it outside both the consumer that first needed it and that consumer's SDK, so other repositories can adopt it without taking either.

## Consequences

Each consumer pins a release of it ([ADR-0030](ADR-0030-consumers-pin-an-exact-release.md)). A change here reaches a consumer only through that pin.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Own distribution | `pyproject.toml:7-8` | — | `built` |
| No consumer vocabulary in the source | `tests/test_no_mesh_vocab.py` | `test_no_foreign_vocabulary_in_leaf_source` | `built` |
