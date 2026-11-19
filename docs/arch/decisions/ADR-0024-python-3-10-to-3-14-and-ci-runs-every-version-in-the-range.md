# ADR-0024 Python 3.10 to 3.14, and CI runs every version in the range

## Status

`built`. Enforced in this repository.

## Decision

The package declares `>=3.10,<3.15`, and CI runs the suite on 3.10, 3.11, 3.12, 3.13 and 3.14.

## Why

The first floor, 3.9, was false: the dependencies refuse 3.9 (commit `ce5fb9d`). The pyproject says a support claim nothing exercises is a claim, not a measurement. 3.14 joined the matrix in 0.2.3 (commit `d1dc86b`).

## Consequences

The trove classifiers stop at 3.13.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The range | `pyproject.toml:11-17` | — | `built` |
| The matrix | `.github/workflows/test.yml:33` | a CI matrix | `built` |
| Classifiers | `pyproject.toml:29-32` | — | `built` |
