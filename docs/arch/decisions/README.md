# Decision records

These records come from a census of the decisions behind this library, each checked against the code at the pins below. Statuses are those of [the architecture README](../README.md). The record shape is provisional.

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

"Enforced" says where a decision is kept. Four records describe decisions that a consumer keeps, not this repository; they are here because they govern how this library is used, and each says so in its status.

| Record | Decision | Status | Enforced |
|---|---|---|---|
| [ADR-0001](ADR-0001-telemetry-is-the-provenance-record-projected-onto-a-trace-and-the-trace-id-never-comes-from-a-model.md) | Telemetry is the provenance record projected onto a trace, and the trace id never comes from a model | `accepted` | here |
| [ADR-0002](ADR-0002-the-library-is-a-standalone-package-outside-its-consumers.md) | The library is a standalone package outside its consumers | `built` | here |
| [ADR-0003](ADR-0003-the-library-ships-no-vocabulary-and-the-caller-s-mapping-supplies-it.md) | The library ships no vocabulary, and the caller's mapping supplies it | `built` | here |
| [ADR-0004](ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | Validation has two tiers: the library checks shape, the vocabulary owner checks truth | `built` | here |
| [ADR-0005](ADR-0005-four-runtime-dependencies-and-no-fifth.md) | Four runtime dependencies, and no fifth | `built` | here |
| [ADR-0006](ADR-0006-the-library-s-own-dependencies-carry-a-ceiling.md) | The library's own dependencies carry a ceiling | `built` | here |
| [ADR-0007](ADR-0007-without-both-keys-the-library-does-nothing.md) | Without both keys the library does nothing | `built` | here |
| [ADR-0008](ADR-0008-emission-fails-soft-and-is-counted-and-never-refuses-the-work.md) | Emission fails soft and is counted, and never refuses the work | `built` | here |
| [ADR-0009](ADR-0009-the-export-witness-counts-spans-lost-on-export-and-a-zero-is-not-proof.md) | The export witness counts spans lost on export, and a zero is not proof | `built` | here |
| [ADR-0010](ADR-0010-content-bearing-values-are-hashed-not-dropped.md) | Content-bearing values are hashed, not dropped | `built` | here |
| [ADR-0011](ADR-0011-a-trace-joins-on-a-seed-a-w3c-id-is-used-verbatim-any-other-seed-is-hashed.md) | A trace joins on a seed: a W3C id is used verbatim, any other seed is hashed | `built` | here |
| [ADR-0012](ADR-0012-w3c-trace-context-helpers-are-pure-and-the-caller-carries-the-headers.md) | W3C trace-context helpers are pure, and the caller carries the headers | `built` | here |
| [ADR-0013](ADR-0013-two-carriers-share-one-span-shape.md) | Two carriers share one span shape | `built` | here |
| [ADR-0014](ADR-0014-traced-opens-a-trace-but-cannot-join-one-and-forwards-capture-flags-only-when-set.md) | Traced opens a trace but cannot join one, and forwards capture flags only when set | `built` | here |
| [ADR-0015](ADR-0015-a-joined-entry-with-no-known-parent-is-a-root.md) | A joined entry with no known parent is a root | `built` | here |
| [ADR-0016](ADR-0016-trace-attributes-propagate-to-children-within-limits.md) | Trace attributes propagate to children, within limits | `built` | here |
| [ADR-0017](ADR-0017-a-durable-runtime-gets-a-replay-safe-boundary-exported-once-from-a-journaled-step.md) | A durable runtime gets a replay-safe boundary, exported once from a journaled step | `built` | here |
| [ADR-0018](ADR-0018-the-boundary-moved-into-the-library-in-0-2-0-which-stays-runtime-neutral.md) | The boundary moved into the library in 0.2.0, which stays runtime-neutral | `built` | here |
| [ADR-0019](ADR-0019-the-root-entry-and-the-boundary-use-the-sdk-s-private-tracer-behind-one-fail-soft-wall.md) | The root entry and the boundary use the SDK's private tracer, behind one fail-soft wall | `built` | here |
| [ADR-0020](ADR-0020-a-step-that-dies-leaves-a-missing-parent-never-a-phantom-one.md) | A step that dies leaves a missing parent, never a phantom one | `accepted` | here |
| [ADR-0021](ADR-0021-the-boundary-is-witnessed-by-a-manufactured-replay-fail-do-not-kill.md) | The boundary is witnessed by a manufactured replay: fail, do not kill | `built` | here |
| [ADR-0022](ADR-0022-the-boundary-takes-its-environment-and-release-from-the-sdk-client.md) | The boundary takes its environment and release from the SDK client | `built` | here |
| [ADR-0023](ADR-0023-the-import-name-is-the-load-bearing-name-and-changes-only-with-a-major-version.md) | The import name is the load-bearing name and changes only with a major version | `accepted` | here |
| [ADR-0024](ADR-0024-python-3-10-to-3-14-and-ci-runs-every-version-in-the-range.md) | Python 3.10 to 3.14, and CI runs every version in the range | `built` | here |
| [ADR-0025](ADR-0025-tests-run-with-the-keys-emptied.md) | Tests run with the keys emptied | `built` | here |
| [ADR-0026](ADR-0026-a-skip-caused-by-a-missing-dependency-fails-ci.md) | A skip caused by a missing dependency fails CI | `built` | here |
| [ADR-0027](ADR-0027-the-documented-public-surface-is-21-names-and-must-equal-all.md) | The documented public surface is 21 names and must equal __all__ | `built` | here |
| [ADR-0028](ADR-0028-a-version-tag-publishes-to-pypi-by-trusted-publishing.md) | A version tag publishes to PyPI by Trusted Publishing | `built` | here |
| [ADR-0029](ADR-0029-a-release-is-an-annotated-tag.md) | A release is an annotated tag | `accepted` | here |
| [ADR-0030](ADR-0030-consumers-pin-an-exact-release.md) | Consumers pin an exact release | `built` | consumer |
| [ADR-0031](ADR-0031-a-consumer-moves-all-its-pins-together.md) | A consumer moves all its pins together | `built` | consumer |
| [ADR-0032](ADR-0032-the-maintainer-merges-and-a-release-tag-may-be-delegated.md) | The maintainer merges, and a release tag may be delegated | `accepted` | here |
| [ADR-0033](ADR-0033-session-files-are-placed-never-committed.md) | Session files are placed, never committed | `built` | here |
| [ADR-0034](ADR-0034-the-consumer-s-re-export-shim-stays-until-every-consumer-imports-the-library-directly.md) | The consumer's re-export shim stays until every consumer imports the library directly | `built` | consumer |
| [ADR-0035](ADR-0035-model-call-text-stays-out-of-spans-and-labelled-text-is-dropped-not-kept.md) | Model-call text stays out of spans, and labelled text is dropped, not kept | `built` | consumer |

## Census rows without a record

The census had 36 rows. Row 33, how the owner's workstation authenticates a push, is a local practice and not a decision of this repository, so it has no record. The other rows map in order: census rows 1 to 32 are ADR-0001 to ADR-0032, and rows 34 to 36 are ADR-0033 to ADR-0035.
