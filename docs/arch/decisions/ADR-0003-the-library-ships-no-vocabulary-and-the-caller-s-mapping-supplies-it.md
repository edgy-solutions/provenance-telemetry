# ADR-0003 The library ships no vocabulary, and the caller's mapping supplies it

## Status

`built`. Enforced in this repository.

## Decision

No provenance field name appears in the library's source. Which of the caller's fields fill which trace fields is a mapping the caller writes.

## Why

The README calls this what lets any team adopt the library without importing another team's domain. A test fails if any of a list of one consumer's field names appears in the package source.

## Consequences

Every name in a mapping is opaque to the library. Whether those names are fields the caller produces is checked by the caller ([ADR-0004](ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md)).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| No vocabulary | `README.md:5`; `mapping.py:37-49` | `test_no_mesh_vocab.py`: `test_no_foreign_vocabulary_in_leaf_source` | `built` |
