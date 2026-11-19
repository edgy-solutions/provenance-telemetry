# ADR-0011 A trace joins on a seed: a W3C id is used verbatim, any other seed is hashed

## Status

`built`. Enforced in this repository.

## Decision

`observed_trace` and `trace_id_for` turn the caller's seed into the trace id. A seed that is already a W3C trace id is used unchanged; any other non-empty seed is hashed by the SDK. `set_trace_standard` writes onto the current span and cannot set the trace id.

## Why

Two services given the same seed land on the same trace without passing a trace id between them (commit `d397970`). Since 0.2.2 an upstream W3C id is kept as it is, so a trace started outside the library keeps its id (commit `fa6bc68`). Passing an id to the SDK's trace update aborted all enrichment on an older SDK (commit `9ca43d4`).

## Consequences

Two docstrings still describe the seed as always hashed ([trace entry](../components/trace-entry.md), finding 10).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Seed to id | `emit.py:313-326` | `test_w3c_v022.py`: `test_w3c_seed_is_verbatim_and_needs_no_langfuse`, `test_non_w3c_seeds_are_hashed`, `test_empty_seed_is_none` | `built` |
| `set_trace_standard` cannot set the id | `emit.py:222-254` | `test_v4.py`: `test_set_trace_standard_noop_when_disabled` | `built` |
