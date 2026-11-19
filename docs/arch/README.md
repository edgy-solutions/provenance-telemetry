# Architecture records: provenance-telemetry

These records **describe the library as it is**. They do not propose. Where a record names something that is not built, it gives that thing a status of `accepted` or `proposed` and says so. Nothing unbuilt is called built.

The records are written for [arch-kit](https://github.com/edgy-solutions/arch-kit), pinned at tag `v0.1.0` (`e0b9b3c40520440a09a4e0e6050ea5017de05848`). They follow the shape the mesh's own records use (`edgy-solutions/dag-tools`, `docs/arch/`): a title line, findings first, and a Sources table at the end. **That shape is provisional.** When the mesh settles a final shape, these records convert to it.

## Status vocabulary

Every claim carries exactly one status.

| Status | Means | Evidence it needs |
|---|---|---|
| `measured` | A recorded run against a running system showed it. | The record of the run. Having a test that could measure it is not enough. |
| `built` | Code at the pinned commit does it. | A file and line. A test that pins it, when one exists; when none does, the row says so. |
| `accepted` | A decision record accepts it, and no code does it yet. | The decision record. |
| `proposed` | It is written down as intent, but not accepted or built. | Where it is written. |

A gap is a claim a reader would expect and the library does not meet. Its status is the status of whatever partial thing exists. A gap with nothing built is written `not built`.

A CI run is a run of the tests, not of a running system. It shows that the tests passed at a commit, so it supports `built`, not `measured`.

## Pins

All evidence is read at these commits. A line number is valid only at its pin.

| Source | Pin | Read status |
|---|---|---|
| provenance-telemetry (this repo) | `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` (tag `v0.2.3`) | read directly |
| langfuse (the Python SDK) | `4.18.0`, the version that resolves under this repo's `langfuse>=4.7.0,<5` on the day of reading | read directly, for the SDK defaults cited |
| edgy-solutions/invincible-agent | `6b3e8efdd4a4d2a172fb394ca5338c23413e57bb` | read directly, file by file, for the consumer facts cited |

At the leaf pin, the Tests workflow passed on Python 3.10 to 3.14, and its forward job against langfuse 5.x passed too. The Build workflow passed on `master` and on the tag `v0.2.3`, and the package is on PyPI at 0.2.3.

## What the library is

`provenance-telemetry` is a small Python library. A caller hands it a *mapping* from the caller's own provenance field names to the trace backend's fields. The library then opens and joins traces, stamps those fields on them, and exports them through the Langfuse SDK as OpenTelemetry spans. It has 21 public names (`provenance_telemetry/__init__.py:16-38`). It runs in the caller's process. Nothing deploys it.

The records split it into five components:

| Component | What it provides | Public names |
|---|---|---|
| [Mapping and redaction](components/mapping-and-redaction.md) (CO-MAPPING) | the caller's mapping, its shape gate, and the hash that stands in for content | `Mapping`, `ScoreSpec`, `load_mapping`, `KNOWN_SLOTS`, `KNOWN_SCORE_ENCODINGS`, `redact` |
| [Trace entry and identity](components/trace-entry.md) (CO-ENTRY) | opening or joining a trace on a chosen id, its parent, and the fields its children carry | `observed_trace`, `set_trace_standard`, `trace_id_for`, `parse_traceparent`, `parse_tracestate`, `format_traceparent` |
| [Span carriers](components/span-carriers.md) (CO-SPANS) | the spans and model-call metadata opened inside an entry | `span_descriptor`, `observe_span`, `litellm_metadata`, `traced` |
| [Emission witness](components/emission-witness.md) (CO-WITNESS) | the enable gate, soft failure, and the count of what was lost | `emit_misses`, `flush` |
| [Replay-safe boundary](components/replay-safe-boundary.md) (CO-BOUNDARY) | an entry for a durable runtime that re-runs a handler on replay | `mint_boundary_ids`, `boundary_parent`, `emit_boundary` |

## Records

| Record | Kind | State |
|---|---|---|
| [components/mapping-and-redaction.md](components/mapping-and-redaction.md) | component | draft |
| [components/trace-entry.md](components/trace-entry.md) | component | draft |
| [components/span-carriers.md](components/span-carriers.md) | component | draft |
| [components/emission-witness.md](components/emission-witness.md) | component | draft |
| [components/replay-safe-boundary.md](components/replay-safe-boundary.md) | component | draft |
| [flows/agent-call-to-trace-store.md](flows/agent-call-to-trace-store.md) | flow | draft |
| [decisions/README.md](decisions/README.md) | decision index, 35 records | draft |
