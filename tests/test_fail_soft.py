"""Seal: emission fails soft-and-countable — a Langfuse outage never raises."""
import sys
import types

from provenance_telemetry import emit_misses, load_mapping, set_trace_standard

MAPPING = load_mapping({"slots": {"user_id": "authz_id"}, "tags": ["engine"]})
VALUES = {"authz_id": "svc:review-starter", "engine": "engine-a"}


def test_disabled_is_a_noop(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    before = emit_misses()
    set_trace_standard(MAPPING, VALUES)  # must not raise, must not count a miss
    assert emit_misses() == before


def test_langfuse_outage_is_soft_and_counted(monkeypatch):
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")

    def boom(**_kw):
        raise RuntimeError("langfuse down")

    fake_ctx = types.SimpleNamespace(update_current_trace=boom, score_current_trace=boom)
    dec = types.ModuleType("langfuse.decorators")
    dec.langfuse_context = fake_ctx
    monkeypatch.setitem(sys.modules, "langfuse", types.ModuleType("langfuse"))
    monkeypatch.setitem(sys.modules, "langfuse.decorators", dec)

    before = emit_misses()
    set_trace_standard(MAPPING, VALUES)  # the review must still be able to start
    assert emit_misses() == before + 1  # the miss is counted, not silent
