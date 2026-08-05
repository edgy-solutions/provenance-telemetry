"""Seals for the v4 (OpenTelemetry) surface: disabled = clean pass-through / no-op.

The enabled path (native trace-id join via create_trace_id + start_as_current_observation,
imperative enrich via OTel span attributes) is validated end-to-end against a live Langfuse
in the migration; here we pin the witness-channel axiom — telemetry never blocks the work.
"""
from provenance_telemetry import observed_trace, set_trace_standard, load_mapping


def _mapping():
    return load_mapping({
        "version": 1,
        "slots": {"trace_id": "tid", "user_id": "uid", "session_id": "sid", "release": "rel"},
        "tags": ["engine", "verb"],
        "metadata": ["subject_class"],
        "content_bearing": ["snippet"],
    })


def test_observed_trace_passthrough_when_disabled(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    ran = []
    with observed_trace(_mapping(), {"tid": "x", "uid": "svc:y", "engine": "a"}, name="op"):
        ran.append(1)
    assert ran == [1]  # the body runs, untraced — never blocked by telemetry


def test_set_trace_standard_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    # No current OTel span, no creds — must not raise.
    set_trace_standard(_mapping(), {"uid": "svc:y", "engine": "a", "subject_class": "pcn:Notice"})
