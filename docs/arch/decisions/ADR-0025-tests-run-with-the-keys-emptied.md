# ADR-0025 Tests run with the keys emptied

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | none |
| flow | none |

No component or flow of these records: it governs the repository's test practice.

## Decision

CI runs the suite with `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST` set empty.

## Why

A runner that carried real keys would take other code paths and send test spans to a real project.

## Consequences

Tests that need tracing on set the keys themselves and export to memory.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Emptied | `.github/workflows/test.yml:50-60` | a CI step | `built` |
