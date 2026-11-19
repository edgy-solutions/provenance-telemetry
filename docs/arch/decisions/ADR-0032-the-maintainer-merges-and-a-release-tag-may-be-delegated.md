# ADR-0032 The maintainer merges, and a release tag may be delegated

## Status

`accepted`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | none |
| flow | none |

No component or flow of these records: it governs the release process.

## Decision

The repository's maintainer merges pull requests. Tagging a release may be delegated by the maintainer.

## Why

Pull requests here are prepared by the owning team's coding agent and merged by the maintainer.

## Consequences

Nothing in the repository records this: there is no CODEOWNERS or CONTRIBUTING file, and the README's maintenance section names no roles.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| No written roles | `README.md:232-239`; no `CODEOWNERS`, no `CONTRIBUTING.md` | — | `accepted` |
