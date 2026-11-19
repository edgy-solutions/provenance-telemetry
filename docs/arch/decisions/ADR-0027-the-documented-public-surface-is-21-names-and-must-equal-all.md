# ADR-0027 The documented public surface is 21 names and must equal __all__

## Status

`built`. Enforced in this repository.

## Decision

CI checks that each of 21 documented names exists and that `__all__` exports nothing else.

## Why

The public surface is the contract. An export that disappears breaks adopters; an export that is not documented is not supported. 0.2.2 documented its four new exports so the check passes (commit `577fb05`).

## Consequences

The list lives in the workflow, not in a test, so a local test run does not check it.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The check | `.github/workflows/test.yml:83-98`; `__init__.py:16-38` | a CI step | `built` |
