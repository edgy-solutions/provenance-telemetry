"""Seal: the two carriers emit ONE span shape.

Given the same logical operation, the sandbox explicit-span carrier and the work
LiteLLM-metadata carrier produce the same name + attributes — differing only in
transport. This is what keeps sandbox and work traces comparable at the exact
boundary where comparison matters most.
"""
from provenance_telemetry import litellm_metadata, observe_span, span_descriptor

OP = "extract table crop 3/5 for document X"
ATTRS = {"resolved_via": "exact", "engine": "doc-tools", "empty": None}


def test_carriers_share_one_shape(monkeypatch):
    # Disabled -> observe_span is a pure no-op that still yields the shared shape.
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)

    canonical = span_descriptor(OP, **ATTRS)

    # Carrier 1 — explicit span (sandbox / direct provider)
    with observe_span(OP, **ATTRS) as yielded:
        assert yielded == canonical

    # Carrier 2 — LiteLLM metadata (work / proxy). Same name + attributes;
    # only transport keys are added.
    md = litellm_metadata(
        OP, trace_id="t1", user_id="svc:x", session_id="s1", tags=["a"], **ATTRS
    )
    assert md["generation_name"] == canonical["name"]
    for key, value in canonical["attributes"].items():
        assert md[key] == value

    # None-valued attribute dropped by BOTH carriers (same shape, not a divergence).
    assert "empty" not in canonical["attributes"]
    assert "empty" not in md

    # Transport-only keys live on the LiteLLM carrier, not in the shared shape.
    assert md["existing_trace_id"] == "t1"
    assert "existing_trace_id" not in canonical["attributes"]
