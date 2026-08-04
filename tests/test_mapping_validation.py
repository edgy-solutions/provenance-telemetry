"""Seal: the leaf validates SHAPE at load — an unknown slot or encoding is refused."""
import pytest
from pydantic import ValidationError

from provenance_telemetry import load_mapping


def test_valid_mapping_loads():
    m = load_mapping(
        {
            "slots": {"trace_id": "request_key", "user_id": "authz_id"},
            "tags": ["engine", "verb"],
            "scores": {"needs_review": {"encoding": "fraction"}},
            "content_bearing": ["mpn"],
        }
    )
    assert m.slots["user_id"] == "authz_id"
    assert m.scores["needs_review"].encoding == "fraction"


def test_unknown_slot_refused():
    # `trace_idx` is not a known Langfuse slot -> refuse at load (shape gate).
    with pytest.raises(ValidationError):
        load_mapping({"slots": {"trace_idx": "request_key"}})


def test_unknown_score_encoding_refused():
    with pytest.raises(ValidationError):
        load_mapping({"scores": {"x": {"encoding": "bogus"}}})
