# ADR-0029 A release is an annotated tag

## Status

`accepted`. Enforced in this repository.

## Decision

A release is an annotated `vX.Y.Z` tag on a green `master` commit.

## Why

The README states it under "Maintaining this repo". Tags `v0.2.0` to `v0.2.2` carry the message "provenance-telemetry X.Y.Z: <summary>".

## Consequences

`v0.1.0` is annotated with another message form. `v0.2.3` is a lightweight tag, so the written rule was not kept at the latest release. Nothing checks it.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The rule | `README.md:235-236` | — | `accepted` |
| The tags | `git cat-file -t` on each tag: `v0.1.0` to `v0.2.2` are tag objects, `v0.2.3` is a commit | — | `built` |
