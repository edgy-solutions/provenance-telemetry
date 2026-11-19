# ADR-0001 Telemetry is the provenance record projected onto a trace, and the trace id never comes from a model

## Status

`accepted`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-MAPPING](../components/mapping-and-redaction.md), [CO-ENTRY](../components/trace-entry.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

A trace says what the caller's provenance record already says, in the caller's words. The trace id comes from an artifact key the caller supplies. It is never derived from model output.

## Why

The README opens with this rule. It means a trace and a decision record about the same work can be joined by key, and a model cannot open or join a trace by what it writes. The decision that set it is edgy-solutions/invincible-agent ADR-0038.

## Consequences

The library takes the seed from the caller's mapped `trace_id` field ([ADR-0011](ADR-0011-a-trace-joins-on-a-seed-a-w3c-id-is-used-verbatim-any-other-seed-is-hashed.md)). It cannot tell where the caller got that value, so the second half of the rule is the caller's to keep.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The rule | `README.md:3` | — | `accepted` |
| The seed is the mapped field | `emit.py:313-326`, `:353-381` | `test_w3c_v022.py`: `test_non_w3c_seeds_are_hashed` | `built` |
