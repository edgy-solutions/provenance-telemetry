# ADR-0030 Consumers pin an exact release

## Status

`built`. Enforced in the consumer, not this repository.

## Governs

| Kind | Ids |
|---|---|
| component | none |
| flow | none |

No component or flow of these records: it governs a consumer's dependency pin.

## Decision

A consumer pins the library with `==`, never a range or a floating git reference, so an upgrade arrives as a visible diff.

## Why

A range on a dependency that governs a fleet acts as a floating reference with a ceiling (edgy-solutions/invincible-agent `AGENTS.md:1682`).

## Consequences

Enforced in the consumer, not here. The library's README recommends a bounded range, `>=0.2.2,<0.3`, for an install from PyPI, which the consumer's rule does not allow; and its examples name 0.2.2, not the current 0.2.3.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The consumer's rule | edgy-solutions/invincible-agent: `AGENTS.md:1682` | — | `built` in the consumer |
| The README's advice | `README.md:9-23` | — | `built` |
