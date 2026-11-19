# ADR-0026 A skip caused by a missing dependency fails CI

## Status

`built`. Enforced in this repository.

## Decision

After the suite, CI fails if any test was skipped for a missing import.

## Why

A skip looks like a pass in a summary line. The suite needs no credentials, so a missing-import skip means CI is under-installed.

## Consequences

Other skips still pass.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The guard | `.github/workflows/test.yml:66-78` | a CI step | `built` |
