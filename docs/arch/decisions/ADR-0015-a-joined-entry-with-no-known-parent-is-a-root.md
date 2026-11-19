# ADR-0015 A joined entry with no known parent is a root

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-ENTRY](../components/trace-entry.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

An entry on a seeded trace with no parent passed, and no current span of that trace, has no parent: it is the trace's root. A parent span id must be 16 hex characters and not all zeros; anything else is counted and dropped.

## Why

Left to itself the SDK would invent a parent that was never exported (0.2.1, commit `423d54b`). A root that exists is better than a link to nothing.

## Consequences

A caller that sends the trace id without the parent loses the link to its own span; the entry is still on the right trace ([CO-ENTRY](../components/trace-entry.md), "Not established from code").

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Three branches | `emit.py:353-381` | `test_entry_parent_v4.py`: `test_case_d_seed_no_parent_is_root`, `test_control_for_d_sdk_path_invents_a_parent` | `built` |
| Bad parent | `emit.py:257-264` | `test_entry_parent_v4.py`: `test_case_e_invalid_parent_counts_one_miss_then_root`, `test_case_f_parent_without_seed_counts_one_miss` | `built` |
