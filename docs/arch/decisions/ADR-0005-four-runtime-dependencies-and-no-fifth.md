# ADR-0005 Four runtime dependencies, and no fifth

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-MAPPING](../components/mapping-and-redaction.md), [CO-ENTRY](../components/trace-entry.md), [CO-SPANS](../components/span-carriers.md), [CO-WITNESS](../components/emission-witness.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

The package depends on `langfuse`, `opentelemetry-api`, `pydantic` and `pyyaml`, and on nothing else. `opentelemetry-sdk` is imported inside fail-soft blocks and arrives through `langfuse`; it is deliberately not declared.

## Why

The README says the dependency list is the adoption pitch: a security review reads it and the README and is done. The pyproject comment says not to add a fifth without a very good reason.

## Consequences

An adopter's resolver decides the `opentelemetry-sdk` version through `langfuse`. Nothing here pins it.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Four dependencies | `pyproject.toml:39-56` | — | `built` |
| The reason | `README.md:5` | — | `accepted` |
