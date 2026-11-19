# ADR-0023 The import name is the load-bearing name and changes only with a major version

## Status

`accepted`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-MAPPING](../components/mapping-and-redaction.md), [CO-ENTRY](../components/trace-entry.md), [CO-SPANS](../components/span-carriers.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

The distribution is `provenance-telemetry` and the import is `provenance_telemetry`. The two are kept aligned. The import name will not change without a major version.

## Why

A sibling package renamed its distribution on its default branch, and every consumer that floated on that branch broke on the next clean resolve.

## Consequences

The release job imports the built wheel by that name in a clean environment, so a wheel that does not import cannot publish. The promise about a major version is written, not enforced.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Aligned names | `pyproject.toml:1-8`; `README.md:25` | — | `accepted` |
| Import smoke test | `.github/workflows/build-package.yml:64-71` | a CI step | `built` |
