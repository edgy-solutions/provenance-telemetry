# ADR-0004 Validation has two tiers: the library checks shape, the vocabulary owner checks truth

## Status

`built`. Enforced in this repository.

## Decision

On load, the library refuses a slot outside five trace fields (`trace_id`, `user_id`, `session_id`, `release`, `version`) and a score encoding outside four (`ordinal`, `fraction`, `binary_per_join`, `count_total`). Whether the mapped names are real fields is checked in the repository that owns them.

## Why

The library cannot know a caller's fields without holding its vocabulary ([ADR-0003](ADR-0003-the-library-ships-no-vocabulary-and-the-caller-s-mapping-supplies-it.md)). The README lists "does not verify your mapping is true" as a non-goal.

## Consequences

An unknown top-level key, such as a misspelled `content_bearing`, is ignored rather than refused ([mapping and redaction](../components/mapping-and-redaction.md), finding 3). The consumer read for these records checks slots, tags, metadata and scores against its code, and does not check `content_bearing`.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Two closed sets, refused at load | `mapping.py:18-34`, `:51-59` | `test_mapping_validation.py`: `test_unknown_slot_refused`, `test_unknown_score_encoding_refused` | `built` |
| Shape, not truth | `README.md:226-230` | — | `built` |
| The consumer's truth check | edgy-solutions/invincible-agent: `tests/test_telemetry.py:75-88` | `test_mesh_mapping_truth_check` | `built` |
