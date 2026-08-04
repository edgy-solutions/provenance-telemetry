"""Seal: the generic-at-birth deletion test.

No caller's provenance vocabulary appears in the leaf's *source*. The library is
an engine; the field names live only in the caller's mapping config (validated
for truth in the caller's own repo). If any of these tokens is hardcoded here,
the leaf has started to know a domain it should stay ignorant of.
"""
from pathlib import Path

import provenance_telemetry

# A representative set of provenance field names owned by consumers, NOT the
# leaf. (Langfuse slot names like session_id / user_id are the leaf's own
# concepts and are intentionally absent from this list.)
FOREIGN_VOCAB = [
    "resolved_via",
    "ruleset_ref",
    "admitted_by",
    "obtained_via",
    "authz_id",
    "request_key",
    "subject_class",
    "chart_version",
    "override_reason",
    "matched_text",
    "crops_failed",
    "confidence_tier",
    "needs_review",
    "coherence",
    "notice_id",
    "doc_ref",
    "mpn",
]


def test_no_foreign_vocabulary_in_leaf_source():
    pkg_dir = Path(provenance_telemetry.__file__).parent
    offenders = {}
    for py in pkg_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        hits = [tok for tok in FOREIGN_VOCAB if tok in text]
        if hits:
            offenders[str(py.relative_to(pkg_dir))] = hits
    assert not offenders, f"consumer vocabulary leaked into the leaf source: {offenders}"
