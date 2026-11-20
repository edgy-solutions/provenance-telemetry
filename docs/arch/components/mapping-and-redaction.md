# Mapping and redaction (CO-MAPPING)

The mapping is the caller's half of the library. A caller writes down, in its own vocabulary, which of its provenance fields fill which trace fields, and which of them carry content that must not leave the process as written. The library loads that mapping, checks its shape, and applies it wherever it projects the caller's values onto a trace. Redaction is the hash it puts in place of a content-bearing value. How the projection reaches a span is in [CO-ENTRY](trace-entry.md) and [CO-BOUNDARY](replay-safe-boundary.md); it is not repeated here.

This record covers what the code provides by default, and what a caller may set. It describes no particular caller, except where a row says which consumer it read.

**This record describes; it proposes nothing.** Statuses are those of [the README](../README.md). Line numbers are at the leaf pin listed there (`e84fd29`). The record shape is provisional.

## Findings

1. **The library holds no vocabulary; the mapping does.** A mapping's slot values, tags, metadata and `content_bearing` entries are the caller's field names, which the library treats as opaque strings. A test scans the package source for a list of field names that one consumer uses and fails if any appears. `built`
2. **The shape gate is two closed sets.** A slot must be one of five trace fields: `trace_id`, `user_id`, `session_id`, `release`, `version`. A score's encoding must be one of four: `ordinal`, `fraction`, `binary_per_join`, `count_total`. Anything else raises a validation error when the mapping is loaded, naming the known values. `built`
3. **An unknown top-level key is dropped without a word.** The model declares no rule for extra keys, so the validation library's default applies, and that default ignores them. A mapping that misspells `content_bearing` loads cleanly with an empty list, and every field it meant to protect is then projected as written. The gate refuses a bad slot name; it does not refuse a bad section name. No test pins either behaviour. `built`
4. **The gate checks shape, not truth.** Whether the names in a mapping are fields the caller actually produces is the caller's check, in the caller's repository. The README states this split as a non-goal of the library. `built`
5. **A mapping is a file or a dict.** A path is read as YAML with the safe loader; an empty file is an empty mapping. Every section defaults to empty, so an empty mapping is valid and projects nothing. The `version` field defaults to 1 and nothing in the library reads it. `built`
6. **Only projected fields are emitted.** The library emits a caller's value only where a slot, the tag list or the metadata list names it. `content_bearing` does not select fields to emit; it changes how a field that is already projected is written. A field listed only under `content_bearing` is never emitted. `built`
7. **Redaction is hash, don't drop.** A content-bearing value is replaced by `sha1:` and the first 16 hex characters of the SHA-1 of its string form. The same value always gives the same token, so two traces that mention it still join on the token. `built`
8. **No key or salt enters the hash.** The token is the same in every process and every deployment. A value drawn from a small or guessable set, such as an identifier with a known format, can be recovered by hashing candidates and comparing. The source calls the token "non-reversible"; that holds for free text, not for such identifiers. `built`
9. **Redaction applies to the projection and to nothing else.** It is applied, through one function, to slot values, tags and metadata wherever the mapping is projected: on an entry, on the active span, in the attributes propagated to children, and on a boundary span. It is not applied to a span carrier's attributes, to model-call metadata, or to a function's captured input and output ([CO-SPANS](span-carriers.md), findings 2 to 4). `built`
10. **Three of the four score encodings are the same arithmetic.** `count_total` turns a pair into a fraction, and 0.0 when the denominator is zero. `ordinal`, `fraction` and `binary_per_join` all send the value as a float, unchanged. The encoding names a meaning the library does not check. No test asserts a score's value. `built`

## Connections

One row per connection. Ids are those of [the README](../README.md#element-ids). Direction is one of: calls, is called by, reads, writes. Evidence paths are at the leaf pin, under `provenance_telemetry/`, unless the row says otherwise. Every connection here is inside the caller's process: the component opens no socket and signs in to nothing. The one authenticated hop, the SDK's export to XE-STORE, is the SDK's and is drawn in [FL-TRACE](../flows/agent-call-to-trace-store.md), step 19. Status is one of the four in [the status vocabulary](../README.md#status-vocabulary); every row here is `built`, and its evidence is the file and line at the leaf pin.

| Other | Direction | Protocol | Authentication | What passes | Status | Evidence |
|---|---|---|---|---|---|---|
| XE-CALLER | is called by | in-process Python call | none: same process | a path or dict, returned as a `Mapping`; a value to `redact`, returned as its token | `built` | `__init__.py:9`, `:13`; `mapping.py:62-69`; `redact.py:15-21` |
| XE-MAPFILE | reads | YAML file, safe loader | the process's file access | the mapping's sections | `built` | `mapping.py:68` |
| CO-ENTRY | is called by | in-process Python call | none: same process | a projected field's value, returned as itself or as its token; the `Mapping` it projects | `built` | `emit.py:32-33`, `:143-147` |

## Settings and defaults

These are the keys of a mapping. Nothing in this component reads the environment.

| Setting | Code default | What it does |
|---|---|---|
| `version` | `1` | declared; read by nothing |
| `slots` | empty | trace field → the caller's field; keys limited to the five of finding 2 |
| `tags` | empty | caller fields written as trace tags |
| `metadata` | empty | caller fields written as trace metadata, JSON-encoded on the entry span |
| `scores` | empty | score name → encoding; the score name is also the caller's field name |
| `content_bearing` | empty | caller fields whose projected value is replaced by the token of finding 7 |
| any other key | — | ignored (finding 3) |

## Gaps

- **A misspelled section is accepted** (finding 3). The likeliest misspelling to matter is `content_bearing`, whose loss sends content as written. `built`
- **The token is unkeyed** (finding 8). It protects free text; it does not protect an identifier drawn from a known format. `built`
- **Score encodings are names without behaviour** (finding 10), and no test reads a score's value. `built`, untested

## Not established from code

- Which consumers emit scores at all. The consumer read for these records, `edgy-solutions/invincible-agent`, declares no `scores` section in its mapping, so its traces carry none.
- Whether any consumer checks its `content_bearing` list against the fields it produces. That consumer's truth check compares slots, tags, metadata and scores with the fields its code produces; it does not read `content_bearing`. Its `content_bearing` names six fields, none of which its slots, tags or metadata project, so by finding 6 its mapping redacts nothing because it emits none of them.

## Sources

All paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6` unless the row names another repository. Library paths are under `provenance_telemetry/`.

| Claim | Source | Decision | Evidence | Status |
|---|---|---|---|---|
| No vocabulary in the library | `mapping.py:37-49`; `__init__.py:1-8` | [ADR-0003](../decisions/ADR-0003-the-library-ships-no-vocabulary-and-the-caller-s-mapping-supplies-it.md) | `test_no_mesh_vocab.py`: `test_no_foreign_vocabulary_in_leaf_source` | `built` |
| Two closed sets, refused at load | `mapping.py:18-34`, `:51-59` | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | `test_mapping_validation.py`: `test_valid_mapping_loads`, `test_unknown_slot_refused`, `test_unknown_score_encoding_refused` | `built` |
| Unknown top-level key ignored | `mapping.py:37-49` (no extra-key rule) | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | no test | `built` |
| Shape, not truth | `README.md`, section "Non-goals" | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | — | `built` |
| File or dict; empty is valid; `version` unread | `mapping.py:44`, `:62-69` | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | `test_mapping_validation.py`: `test_valid_mapping_loads` | `built` |
| Only projected fields are emitted | `emit.py:143-178`, `:185-208` | [ADR-0010](../decisions/ADR-0010-content-bearing-values-are-hashed-not-dropped.md) | `test_boundary_v4.py`: `test_set_trace_standard_attributes_pinned` | `built` |
| Hash, don't drop: `sha1:` and 16 hex | `redact.py:15-21` | [ADR-0010](../decisions/ADR-0010-content-bearing-values-are-hashed-not-dropped.md) | `test_boundary_v4.py`: `test_set_trace_standard_attributes_pinned` (asserts a redacted metadata value equals `redact` of it) | `built` |
| No key or salt | `redact.py:18-21` | [ADR-0010](../decisions/ADR-0010-content-bearing-values-are-hashed-not-dropped.md) | — | `built` |
| Applied to the projection only | `emit.py:143-147`, `:162`, `:169`, `:174`, `:195-203`; `boundary.py:154`; contrast `spans.py:27-32`, `:85` | [ADR-0010](../decisions/ADR-0010-content-bearing-values-are-hashed-not-dropped.md) | `test_boundary_v4.py`: `test_set_trace_standard_attributes_pinned` | `built` |
| Score encodings | `emit.py:136-140`, `:243-252` | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | no test reads a score value | `built` |
| Consumer: no scores; truth check skips `content_bearing` | edgy-solutions/invincible-agent at `6b3e8ef`: `baml_shared/telemetry-mapping.yaml:5-20`; `tests/test_telemetry.py:75-88` | [ADR-0004](../decisions/ADR-0004-validation-has-two-tiers-the-library-checks-shape-the-vocabulary-owner-checks-truth.md) | `tests/test_telemetry.py`: `test_mesh_mapping_truth_check` | `built` |
