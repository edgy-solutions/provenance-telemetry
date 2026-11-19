# ADR-0017 A durable runtime gets a replay-safe boundary, exported once from a journaled step

## Status

`built`. Enforced in this repository.

## Decision

For a handler that a durable runtime replays, the library splits the entry in three: mint the ids inside a journaled step, make them a non-recording parent, and export the boundary span from another journaled step. Exporting it is the caller's job, exactly once.

## Why

An ordinary entry re-opens on each replay and shows one execution as several. On the SDK version read, a second export is a second observation, not an update.

## Consequences

The residual case is an export that succeeds before its journal entry commits; the replay then exports a duplicate. The library names it and cannot prevent it ([replay-safe boundary](../components/replay-safe-boundary.md), finding 6).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Three calls | `boundary.py:43-178`; `docs/durable-execution.md:31-66` | `test_boundary_v4.py`: `test_children_parent_to_boundary_and_boundary_exports_nothing`, `test_emit_boundary_exports_one_root_span`, `test_replay_shape` | `built` |
| The residual duplicate | `docs/durable-execution.md:71` | `test_replay_shape` | `built` |
