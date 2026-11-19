# ADR-0010 Content-bearing values are hashed, not dropped

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-MAPPING](../components/mapping-and-redaction.md), [CO-ENTRY](../components/trace-entry.md), [CO-BOUNDARY](../components/replay-safe-boundary.md) |
| flow | none |

## Decision

A field the caller lists under `content_bearing` is written as `sha1:` and the first 16 hex characters of its SHA-1, wherever the mapping projects it.

## Why

The same value gives the same token, so two traces that mention it still join, while the value itself does not leave the process. edgy-solutions/invincible-agent ADR-0038 sets the rule.

## Consequences

The hash is unkeyed, so an identifier from a known format can be recovered by hashing candidates ([CO-MAPPING](../components/mapping-and-redaction.md), finding 8). Redaction covers the projection only, not carrier attributes or captured input and output (finding 9 there).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The token | `redact.py:15-21` | `test_boundary_v4.py`: `test_set_trace_standard_attributes_pinned` | `built` |
| Applied to the projection | `emit.py:143-147` | the same test | `built` |
