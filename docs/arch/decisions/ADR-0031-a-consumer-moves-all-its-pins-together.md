# ADR-0031 A consumer moves all its pins together

## Status

`built`. Enforced in the consumer, not this repository.

## Decision

The consumer read for these records pins the library in eight places, its root and seven services, and moves them together.

## Why

Two services on two releases of the library would trace differently within one request.

## Consequences

Enforced in the consumer by a test that names the release, so each upgrade renames that test. At the consumer pin it names 0.2.2.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The census test | edgy-solutions/invincible-agent: `tests/perf/test_trace_spans.py:318` | `test_every_pyproject_pins_provenance_telemetry_0_2_2` | `built` in the consumer |
