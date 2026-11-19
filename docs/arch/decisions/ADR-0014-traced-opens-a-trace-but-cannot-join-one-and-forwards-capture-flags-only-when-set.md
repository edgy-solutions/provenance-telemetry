# ADR-0014 Traced opens a trace but cannot join one, and forwards capture flags only when set

## Status

`built`. Enforced in this repository.

## Decision

`traced` wraps the SDK's decorator, which mints its own id, so it cannot open on a chosen trace id; an entry that must join uses `observed_trace`. It forwards `capture_input` and `capture_output` to the SDK only when the caller sets them.

## Why

It generalises an older consumer decorator into the library (commit `fc930a0`). Leaving the flags unset keeps the SDK's own setting in charge.

## Consequences

In the SDK version read, that setting defaults to capturing, so by default a decorated function's arguments and return value go to the trace ([span carriers](../components/span-carriers.md), finding 4).

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| Cannot join | `spans.py:92-122`; `README.md:119-121` | `test_traced.py`: `test_enabled_still_runs_the_function` | `built` |
| Capture flags | `spans.py:114-117` | `test_w3c_v022.py`: `test_traced_default_passes_neither_capture_key`, `test_traced_capture_false_is_forwarded` | `built` |
