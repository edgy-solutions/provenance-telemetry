# ADR-0012 W3C trace-context helpers are pure, and the caller carries the headers

## Status

`built`. Enforced in this repository.

## Decision

The library parses and formats `traceparent` and parses `tracestate`. It reads and writes no HTTP headers.

## Why

The caller owns its transport. Pure helpers let any caller hand a received header's parts to an entry (0.2.2, commit `fa6bc68`).

## Consequences

Whether a parent span id travels between services is each caller's choice. The consumer read for these records drops it at four receivers ([the flow record](../flows/agent-call-to-trace-store.md), finding 4).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The helpers | `w3c.py:1-92` | `test_w3c_v022.py`: `test_valid_00`, `test_invalid_traceparent`, `test_two_traceparent_headers_rejected`, `test_format_traceparent_roundtrip` | `built` |
