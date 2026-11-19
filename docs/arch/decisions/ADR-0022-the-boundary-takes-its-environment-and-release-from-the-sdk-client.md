# ADR-0022 The boundary takes its environment and release from the SDK client

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

The boundary span's environment and release are the SDK client's, from `LANGFUSE_TRACING_ENVIRONMENT` and the SDK's release settings, as on every span the SDK builds. `DEPLOY_ENV` is no longer read.

## Why

A parent and its children must not report different environments (0.2.1, commit `29b1171`).

## Consequences

This was a breaking change for a deployment that set only `DEPLOY_ENV`. On the boundary the client's release wins over a mapped one; on an ordinary entry the mapped one wins ([CO-ENTRY](../components/trace-entry.md), finding 7).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| One source | `boundary.py:154-160`; `CHANGELOG.md:44-47` | `test_boundary_v4.py`: `test_boundary_and_child_report_the_same_environment_and_release` | `built` |
