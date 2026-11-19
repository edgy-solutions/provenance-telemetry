# ADR-0006 The library's own dependencies carry a ceiling

## Status

`built`. Enforced in this repository.

## Decision

Each runtime dependency the library publishes has an upper bound where a major release is known to break it. `langfuse` is declared `>=4.7.0,<5`.

## Why

A range with no ceiling lets a new major reach every adopter on their next resolve. The consumer's charter states the rule for what a repository publishes (edgy-solutions/invincible-agent `AGENTS.md:1682`). The ceiling moved from `<6` to `<5` in 0.2.3, because client 5 needs a newer server (commit `1a3f05b`).

## Consequences

A non-blocking CI job runs the suite against `langfuse` 5.x, so a break shows before the ceiling is raised. `docs/durable-execution.md:93` still names `<6`.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The ceiling | `pyproject.toml:49-56` | `test_langfuse_client_below_5.py`: `test_declared_requirement_excludes_every_5x`, `test_detector_control` | `built` |
| The forward job | `.github/workflows/test.yml:110-142` | a CI job, allowed to fail | `built` |
| The stale range | `docs/durable-execution.md:93` | — | `built` |
