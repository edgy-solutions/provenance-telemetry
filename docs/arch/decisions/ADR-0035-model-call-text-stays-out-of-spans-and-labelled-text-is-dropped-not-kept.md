# ADR-0035 Model-call text stays out of spans, and labelled text is dropped, not kept

## Status

`built`. Enforced in the consumer, not this repository.

## Governs

| Kind | Ids |
|---|---|
| component | [CO-SPANS](../components/span-carriers.md) |
| flow | [FL-TRACE](../flows/agent-call-to-trace-store.md) |

## Decision

The consumer read for these records turns the SDK's input and output capture off before the SDK is imported, and its decorator wrapper forces both flags off. Its model-call wrapper records the model id and token counts, not text.

## Why

The text is dropped rather than kept under a label. The reason in the consumer's unpublished working notes is that the trace store grants access per project, so a label inside a project would not limit who reads the text. This record has no public source for that reason.

## Consequences

Enforced in the consumer, not here: the library's own default defers to the SDK, which captures ([ADR-0014](ADR-0014-traced-opens-a-trace-but-cannot-join-one-and-forwards-capture-flags-only-when-set.md)).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Capture off | edgy-solutions/invincible-agent: `baml_shared/telemetry.py:27-31`, `:197-205` | — | `built` in the consumer |
| No prompt text on model calls | edgy-solutions/invincible-agent: `baml_shared/telemetry.py:257-270` | — | `built` in the consumer |
| Landed | edgy-solutions/invincible-agent PR #415, merged | — | `built` in the consumer |
