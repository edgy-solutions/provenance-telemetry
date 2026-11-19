# ADR-0013 Two carriers share one span shape

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-SPANS](../components/span-carriers.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

A model call can be traced through an open span (`observe_span`) or through metadata for a LiteLLM proxy (`litellm_metadata`). Both build their name and attributes from one descriptor.

## Why

A trace reads the same whichever way the call was made.

## Consequences

Carrier attributes are not redacted and do not consult the mapping ([CO-SPANS](../components/span-carriers.md), findings 2 and 3).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| One descriptor | `spans.py:27-58` | `test_path_equivalence.py`: `test_carriers_share_one_shape` | `built` |
