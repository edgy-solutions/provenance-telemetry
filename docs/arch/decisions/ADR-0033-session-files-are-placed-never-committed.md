# ADR-0033 Session files are placed, never committed

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | none |
| flow | none |

No component or flow of these records: it governs the repository's working practice.

## Decision

Maintainers' local working notes live in `sessions/`, which is ignored. They are placed in a recipient's local folder and never committed, pushed or force-added.

## Why

The notes carry internal detail that does not belong in a public repository. 0.2.3 landed the ignore rule (commit `d1dc86b`).

## Consequences

A force-add would still commit one; nothing refuses it.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Ignored | `.gitignore:9-10` | — | `built` |
| The rule | `README.md:237-239` | — | `built` |
