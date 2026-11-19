# Architecture records: provenance-telemetry

These records **describe the library as it is**. They do not propose. Where a record names something that is not built, it gives that thing a status of `accepted` or `proposed` and says so. Nothing unbuilt is called built.

The records are written for [arch-kit](https://github.com/edgy-solutions/arch-kit), pinned at tag `v0.1.0` (`e0b9b3c40520440a09a4e0e6050ea5017de05848`). They follow the shape the mesh's own records use (`edgy-solutions/dag-tools`, `docs/arch/`): a title line, findings first, and a Sources table at the end. **That shape is provisional.** When the mesh settles a final shape, these records convert to it.

Three tables are the structured fields that views and diagrams are drawn from: a component record's **Connections** table, a flow record's numbered **steps** table, and a decision record's **Governs** table. Every cell that names another element names it by id ([element ids](#element-ids)). The prose explains; the tables are what gets drawn. When the mesh publishes its field names, the tables convert column for column.

## Status vocabulary

Every claim carries exactly one status.

| Status | Means | Evidence it needs |
|---|---|---|
| `measured` | A recorded run showed it. A run measures only what it exercised. | The run's id or its result file; for a CI run, the words "in CI, in process". Having a test that could measure it is not enough. |
| `built` | Code at the pinned commit does it. | A file and line. A test that pins it, when one exists; when none does, the row says so. |
| `accepted` | A decision record accepts it, and no code does it yet. | The decision record. |
| `proposed` | It is written down as intent, but not accepted or built. | Where it is written. |

A gap is a claim a reader would expect and the library does not meet. Its status is the status of whatever partial thing exists. A gap with nothing built is written `not built`.

A CI run is in process. A claim about the code's behaviour that a CI run exercised may be `measured`, citing the run and saying "in CI, in process". A claim about a deployed service or a real backend is not measured by an in-process run, and stays `built`. These records cite tests, not runs, so their claims stay `built` until a row cites a run.

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

| Id | Component | What it provides | Public names |
|---|---|---|---|
| [CO-MAPPING](components/mapping-and-redaction.md) | Mapping and redaction | the caller's mapping, its shape gate, and the hash that stands in for content | `Mapping`, `ScoreSpec`, `load_mapping`, `KNOWN_SLOTS`, `KNOWN_SCORE_ENCODINGS`, `redact` |
| [CO-ENTRY](components/trace-entry.md) | Trace entry and identity | opening or joining a trace on a chosen id, its parent, and the fields its children carry | `observed_trace`, `set_trace_standard`, `trace_id_for`, `parse_traceparent`, `parse_tracestate`, `format_traceparent` |
| [CO-SPANS](components/span-carriers.md) | Span carriers | the spans and model-call metadata opened inside an entry | `span_descriptor`, `observe_span`, `litellm_metadata`, `traced` |
| [CO-WITNESS](components/emission-witness.md) | Emission witness | the enable gate, soft failure, and the count of what was lost | `emit_misses`, `flush` |
| [CO-BOUNDARY](components/replay-safe-boundary.md) | Replay-safe boundary | an entry for a durable runtime that re-runs a handler on replay | `mint_boundary_ids`, `boundary_parent`, `emit_boundary` |

## Records

| Id | Record | Kind | State |
|---|---|---|---|
| CO-MAPPING | [components/mapping-and-redaction.md](components/mapping-and-redaction.md) | component | draft |
| CO-ENTRY | [components/trace-entry.md](components/trace-entry.md) | component | draft |
| CO-SPANS | [components/span-carriers.md](components/span-carriers.md) | component | draft |
| CO-WITNESS | [components/emission-witness.md](components/emission-witness.md) | component | draft |
| CO-BOUNDARY | [components/replay-safe-boundary.md](components/replay-safe-boundary.md) | component | draft |
| FL-TRACE | [flows/agent-call-to-trace-store.md](flows/agent-call-to-trace-store.md) | flow | draft |
| — | [decisions/README.md](decisions/README.md) | decision index, 35 records | draft |

## Element ids

Records refer to one another, and to everything they connect to, by id. `CO-` and `FL-` ids are records in this directory, and `ADR-` ids are the decision records. Every other id names an element that has no record here, and is defined once, in this table.

- `XE-` ids are outside this library.
- `IA-` ids and the role are parts of the one consumer read for these records, `edgy-solutions/invincible-agent`. They are used only by the flow record and by consumer rows. When that consumer publishes records of its own, its ids replace these.

The prefixes are provisional until the mesh settles a naming rule.

| Id | Kind | What it is |
|---|---|---|
| XE-CALLER | external | the calling application's own code, in the same process |
| XE-MAPFILE | external | a caller's mapping file, in YAML |
| XE-ENV | external | the process environment |
| XE-SDK | external | the Langfuse Python SDK in the process, with the OpenTelemetry tracer provider, batch span processor and OTLP exporter it sets up |
| XE-OTEL | external | the OpenTelemetry API's current-span context in the process |
| XE-LOG | external | the Python logger `provenance_telemetry` |
| XE-STORE | external | the trace store that receives the SDK's OTLP export |
| XE-RUNTIME | external | a durable-execution runtime and its journal |
| RL-PERSON | role | the person asking a question |
| IA-BFF | consumer | the backend-for-frontend that receives the question |
| IA-ORCH | consumer | the orchestrator, which runs a plan as steps |
| IA-STEP | consumer | one orchestrator step, in its own process |
| IA-ANALYST-PROXY | consumer | the analyst agent's `/analyze` proxy |
| IA-ANALYST | consumer | the analyst agent's run, inside XE-RUNTIME |
| IA-TOOL | consumer | the analyst agent's tools |
| IA-MODEL | consumer | the model the analyst calls |
| IA-TELEMETRY | consumer | the consumer's telemetry module: its model-call wrapper, its decorator wrapper, and its re-export shim |
| IA-ENGINE-O | consumer | the ontology engine |
| IA-ENGINE-DOCS | consumer | the documentation engine |
| IA-ENGINE-W | consumer | the vector-search engine |
| IA-ENGINE-F | consumer | the presentation engine |
| IA-DATA | consumer | an engine's own store: graph, vector or ontology |
