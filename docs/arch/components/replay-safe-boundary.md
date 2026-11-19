# Replay-safe boundary (CO-BOUNDARY)

The replay-safe boundary is an entry for a handler run by a durable-execution runtime. Such a runtime re-runs a handler from the top on replay, and hands back recorded results only for the steps it journaled. An ordinary entry ([CO-ENTRY](trace-entry.md)) re-runs too, and mints a new span each time, so one execution shows as several entries. The boundary splits the entry into three calls. The first mints the boundary's ids inside a journaled step, so a replay gets the same ids. The second makes those ids the parent of everything inside without exporting anything, so a replay cannot add a span. The third exports the boundary span itself, once, from another journaled step. The library names no runtime; its one worked example is in `docs/durable-execution.md`.

This record covers what the code provides by default, and what a caller may set. It describes no particular caller, except where a row says which consumer it read.

**This record describes; it proposes nothing.** Statuses are those of [the README](../README.md). Line numbers are at the leaf pin listed there (`e84fd29`). The record shape is provisional.

## Findings

1. **`mint_boundary_ids` mints the pair to be journaled.** It always returns a fresh random 16-hex span id, even when tracing is off. The trace id is the seed's, by the rule of [CO-ENTRY](trace-entry.md), finding 3. With no seed it is a random id from the SDK. The trace id is none when tracing is off, or when minting fails, which counts one miss. The call is meant to run inside a journaled step; the library cannot check that it does. `built`
2. **`boundary_parent` makes the ids the parent of everything inside, and exports nothing.** It attaches a non-recording span with those ids, marked as remote, as the current span. Spans opened inside, by any carrier, nest under it through the ordinary context. Being non-recording, it exports nothing, so re-entering it on a replay adds nothing. Given a mapping and values, it also passes the mapped person, session, version, tags and metadata to the children. `built`
3. **`boundary_parent` yields the timing for the export.** It yields a start time and sets the end time on exit, from the wall clock. A setup error counts one miss and the body runs untraced. When tracing is off, or the ids lack a trace id, it only times. `built`
4. **`emit_boundary` exports the boundary span itself, as the trace's root.** It builds the span by hand, with the journaled ids, no parent, and the start and end times it is given (or now, for a missing time). It builds it on the SDK tracer's own processor and scope; the docstring says the SDK's processor drops a span from any other scope. The span carries the trace name and the mapped trace fields. It sends no scores. It returns the span id. `built`
5. **On the boundary span, the client's environment and release win.** The mapped fields are set first, then the client's environment and release are written over them. So the boundary and the SDK-built spans inside it report the same environment and release. A mapped `release` is overwritten here, and not on an ordinary entry ([CO-ENTRY](trace-entry.md), finding 7). `built`
6. **Exported twice, the boundary is two spans.** The export does not update a span with the same id; the backend records a second observation. Calling `emit_boundary` exactly once is the caller's job. The docstring names the residual case: the export succeeds, then the journal entry for that step does not commit, and the replay exports a duplicate. A test pins that a second export gives two spans with one span id. `built`
7. **Missing or malformed ids are handled two ways.** With tracing off, or ids that lack a trace id or span id, `emit_boundary` returns nothing and counts nothing. With ids that are present but not hex, it counts one miss and returns nothing. `built`
8. **The worked example's version range is stale.** `docs/durable-execution.md` gives the tested SDK range as `langfuse>=4.7.0,<6`. The package has declared `<5` since 0.2.3. `built`

## Connections

One row per connection. Ids are those of [the README](../README.md#element-ids). Direction is one of: calls, is called by, reads, writes. Evidence paths are at the leaf pin, under `provenance_telemetry/`, unless the row says otherwise. Every connection here is inside the caller's process: the component opens no socket and signs in to nothing. The one authenticated hop, the SDK's export to XE-STORE, is the SDK's and is drawn in [FL-TRACE](../flows/agent-call-to-trace-store.md), step 19. Status is one of the four in [the status vocabulary](../README.md#status-vocabulary); every row here is `built`, and its evidence is the file and line at the leaf pin.

| Other | Direction | Protocol | Authentication | What passes | Status | Evidence |
|---|---|---|---|---|---|---|
| XE-CALLER | is called by | in-process Python call | none: same process | a seed, returned as the ids to journal; ids, mapping and values; a name and the timing | `built` | `__init__.py:11`; `boundary.py:43-178` |
| CO-ENTRY | calls | in-process Python call | none: same process | the seed, for a trace id; mapping and values, for trace attributes and for propagation to children | `built` | `boundary.py:24-30`, `:56`, `:102`, `:154` |
| CO-WITNESS | calls | in-process Python call | none: same process | the SDK client, to install the export witness; a miss and its reason | `built` | `boundary.py:59`, `:104`, `:144`, `:177` |
| XE-ENV | reads | environment variable, through CO-ENTRY's gate | none: same process | whether both keys are set | `built` | `boundary.py:25`, `:52`, `:83`, `:133` |
| XE-OTEL | writes | OpenTelemetry context, in process | none: same process | a non-recording span with the journaled ids, attached as current and detached on exit | `built` | `boundary.py:85-97` |
| XE-SDK | calls | in-process Python call, through the SDK tracer's private processor and scope | none at the call; the SDK holds the keys | a request for a trace id; a hand-built span with the ids, times, name, mapped fields, and the client's environment and release | `built` | `boundary.py:54-57`, `:143-174` |

## Settings and defaults

| Setting | Code default | What it does |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | unset: ids carry no trace id; nothing is attached or exported | both must be set |
| `trace_seed` | none: a random trace id | the upstream id, so the boundary joins the caller's trace |
| `mapping`, `values` on `boundary_parent` | none: nothing passed to children | the fields children carry |
| `name` on `emit_boundary` | required | the boundary span's name and the trace name |
| `timing` | required; a missing time is now | the boundary span's start and end |

## Gaps

- **Exactly-once rests on the caller** (finding 6). The library can neither see the journal nor update an exported span. `built`
- **The worked example names the old SDK range** (finding 8). `built`

## Not established from code

- How a trace store shows children whose boundary span was never exported. The docstring says they appear as roots on the right trace. No test reads a trace back from a store.
- Whether the residual duplicate of finding 6 occurs in practice. It depends on the runtime's journal commit, which no test here runs.
- Which consumers use the boundary. The consumer read for these records, `edgy-solutions/invincible-agent`, uses all three calls in three engines (data_analyst, neo4j_expert and restate_analyst), each with the mint and the export inside the runtime's journaled step.

## Sources

All paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` unless the row names another repository. Library paths are under `provenance_telemetry/`.

| Claim | Source | Decision | Evidence | Status |
|---|---|---|---|---|
| `mint_boundary_ids` | `boundary.py:43-61` | [ADR-0017](../decisions/ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md) | `test_w3c_v022.py`: `test_mint_boundary_ids_returns_w3c_seed`, `test_mint_boundary_ids_dashed_seed_unchanged` | `built` |
| `boundary_parent` attaches a non-recording parent; children nest; replay adds nothing | `boundary.py:64-112`, `:87-92`, `:101-102` | [ADR-0017](../decisions/ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md) | `test_boundary_v4.py`: `test_children_parent_to_boundary_and_boundary_exports_nothing`, `test_replay_shape` | `built` |
| Timing; setup error counted | `boundary.py:81`, `:103-108` | [ADR-0017](../decisions/ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md) | no test of a setup error | `built` |
| `emit_boundary`: a root on the SDK's scope, no scores | `boundary.py:115-178`, `:147-153`, `:164-174` | [ADR-0017](../decisions/ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md); [ADR-0019](../decisions/ADR-0019-the-root-entry-and-the-boundary-use-the-sdk-s-private-tracer-behind-one-fail-soft-wall.md) | `test_boundary_v4.py`: `test_emit_boundary_exports_one_root_span` | `built` |
| Client's environment and release win | `boundary.py:154-160` | [ADR-0022](../decisions/ADR-0022-the-boundary-takes-its-environment-and-release-from-the-sdk-client.md) | `test_boundary_v4.py`: `test_boundary_and_child_report_the_same_environment_and_release` | `built` |
| Twice is two spans | `boundary.py:122-126` | [ADR-0017](../decisions/ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md) | `test_boundary_v4.py`: `test_replay_shape` | `built` |
| Missing ids: nothing; malformed: one miss | `boundary.py:133-134`, `:176-178` | [ADR-0008](../decisions/ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | `test_boundary_v4.py`: `test_disabled_is_noop`, `test_emit_boundary_malformed_ids_one_miss` | `built` |
| Stale range in the worked example | `docs/durable-execution.md:93`; `pyproject.toml:53` | [ADR-0018](../decisions/ADR-0018-the-boundary-moved-into-the-library-in-0-2-0-which-stays-runtime-neutral.md); [ADR-0006](../decisions/ADR-0006-the-library-s-own-dependencies-carry-a-ceiling.md) | `test_langfuse_client_below_5.py`: `test_declared_requirement_excludes_every_5x` | `built` |
| Consumer: three engines | edgy-solutions/invincible-agent at `6b3e8ef`: `agent_fleet/data_analyst/main.py:825-842`; `agent_fleet/neo4j_expert/service.py:972-986`; `agent_fleet/restate_analyst/main.py:1454-1475` | edgy-solutions/invincible-agent ADR-0038 | — | `built` |
