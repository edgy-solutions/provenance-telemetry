"""Enabled-path seals for the v4 boundary primitives, witness, propagation and flush.

No network: every client points at localhost:1 and exports to an in-memory or fake exporter.
Each test uses a unique public key because the SDK's resource manager is a singleton per key.
"""
import itertools
import sys
import types

import pytest
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import provenance_telemetry as pt
from provenance_telemetry import emit as emit_mod
from provenance_telemetry import (
    boundary_parent, emit_boundary, emit_misses, flush, load_mapping,
    mint_boundary_ids, observe_span, observed_trace, set_trace_standard,
)

_n = itertools.count()
MAPPING = load_mapping({
    "slots": {"trace_id": "tid", "user_id": "uid", "session_id": "sid"},
    "tags": ["engine"],
    "metadata": ["note"],
})
VALUES = {"tid": "upstream-1", "uid": "svc:a", "sid": "s-1", "engine": "eng", "note": "n"}

USER, SESSION, TAGS = "user.id", "session.id", "langfuse.trace.tags"


class FailingExporter(InMemorySpanExporter):
    def export(self, spans):
        super().export(spans)
        return SpanExportResult.FAILURE


class RaisingExporter(InMemorySpanExporter):
    def export(self, spans):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def _isolate_sdk_singletons():
    """The SDK keeps one resource manager per public key and get_client() refuses to guess
    when several exist; clear them around every test so each sees only its own client."""
    from langfuse._client.resource_manager import LangfuseResourceManager
    LangfuseResourceManager.reset()
    yield
    LangfuseResourceManager.reset()


def make_client(monkeypatch, exporter):
    from langfuse import Langfuse
    pk = f"pk-test-{next(_n)}"
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", pk)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("DEPLOY_ENV", raising=False)
    return Langfuse(public_key=pk, secret_key="sk-test", base_url="http://localhost:1",
                    span_exporter=exporter)


@pytest.fixture
def mem(monkeypatch):
    exp = InMemorySpanExporter()
    client = make_client(monkeypatch, exp)
    yield client, exp


def spans_of(client, exp):
    client.flush()
    return exp.get_finished_spans()


def hexid(n, width):
    return format(n, f"0{width}x")


# 1 ---------------------------------------------------------------- disabled
def test_disabled_is_noop(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    before = emit_misses()
    ids = mint_boundary_ids("seed")
    assert ids["trace_id"] is None and len(ids["span_id"]) == 16
    int(ids["span_id"], 16)
    ran = []
    with boundary_parent(ids, mapping=MAPPING, values=VALUES) as timing:
        ran.append(1)
    assert ran == [1] and timing["ended_at"] is not None
    assert emit_boundary(MAPPING, VALUES, ids=ids, name="x", timing=timing) is None
    flush()
    assert emit_misses() == before


# 2 ------------------------------------------------------- emit_boundary shape
def test_emit_boundary_exports_one_root_span(monkeypatch, mem):
    client, exp = mem
    ids = mint_boundary_ids("upstream-1")
    assert len(ids["trace_id"]) == 32
    with boundary_parent(ids, mapping=MAPPING, values=VALUES) as timing:
        pass
    got = emit_boundary(MAPPING, VALUES, ids=ids, name="analyze", timing=timing)
    assert got == ids["span_id"]
    spans = spans_of(client, exp)
    assert len(spans) == 1
    s = spans[0]
    assert hexid(s.context.trace_id, 32) == ids["trace_id"]
    assert hexid(s.context.span_id, 16) == ids["span_id"]
    assert s.parent is None
    assert s.name == "analyze"
    assert s.start_time == int(timing["started_at"].timestamp() * 1e9)
    assert s.end_time == int(timing["ended_at"].timestamp() * 1e9)
    a = s.attributes
    assert a["langfuse.observation.type"] == "span"
    assert a["langfuse.trace.name"] == "analyze"
    assert a[USER] == "svc:a" and a[SESSION] == "s-1"
    assert list(a[TAGS]) == ["eng"]


# 3 ----------------------------------------------- children under the boundary
def test_children_parent_to_boundary_and_boundary_exports_nothing(mem):
    client, exp = mem
    ids = mint_boundary_ids("upstream-1")
    with boundary_parent(ids, mapping=MAPPING, values=VALUES):
        with observe_span("leaf"):
            pass
    spans = spans_of(client, exp)
    assert [s.name for s in spans] == ["leaf"]  # no emit_boundary -> only the child
    c = spans[0]
    assert hexid(c.parent.span_id, 16) == ids["span_id"]
    assert hexid(c.context.trace_id, 32) == ids["trace_id"]
    assert c.attributes[USER] == "svc:a" and c.attributes[SESSION] == "s-1"


# 4 ------------------------------------------------------------ replay shape
def test_replay_shape(mem):
    client, exp = mem
    ids = mint_boundary_ids("upstream-1")
    for _ in range(2):
        with boundary_parent(ids):
            pass
    assert spans_of(client, exp) == ()
    t = {"started_at": None, "ended_at": None}
    emit_boundary(MAPPING, VALUES, ids=ids, name="b", timing=t)
    emit_boundary(MAPPING, VALUES, ids=ids, name="b", timing=t)
    spans = spans_of(client, exp)
    # v4 does not upsert: the documented residual is a duplicate, not a collapse.
    assert len(spans) == 2
    assert {s.context.span_id for s in spans} == {int(ids["span_id"], 16)}


# 5 ------------------------------------------------------------------ witness
def _emit_n(client, n):
    for i in range(n):
        with observe_span(f"s{i}"):
            pass
    flush()


def test_witness_counts_refused_export(monkeypatch):
    exp = FailingExporter()
    client = make_client(monkeypatch, exp)
    before = emit_misses()
    _emit_n(client, 3)
    assert emit_misses() == before + 3


def test_witness_counts_raising_export(monkeypatch):
    exp = RaisingExporter()
    client = make_client(monkeypatch, exp)
    before = emit_misses()
    _emit_n(client, 2)
    assert emit_misses() == before + 2


def test_witness_success_is_flat(mem):
    client, exp = mem
    before = emit_misses()
    _emit_n(client, 2)
    assert emit_misses() == before
    assert len(exp.get_finished_spans()) == 2


def test_witness_install_twice_does_not_double_count(monkeypatch):
    exp = FailingExporter()
    client = make_client(monkeypatch, exp)
    emit_mod._install_export_witness(client)
    emit_mod._install_export_witness(client)
    before = emit_misses()
    _emit_n(client, 2)
    assert emit_misses() == before + 2


def test_control_without_witness_counter_is_flat(monkeypatch):
    exp = FailingExporter()
    client = make_client(monkeypatch, exp)
    monkeypatch.setattr(emit_mod, "_install_export_witness", lambda c: None)
    before = emit_misses()
    with client.start_as_current_observation(name="raw", as_type="span"):
        pass
    client.flush()
    assert len(exp.get_finished_spans()) == 1  # the export really happened and "failed"
    assert emit_misses() == before  # nothing counted it: the movement above is the witness


def test_witness_absent_shape_warns_once_not_a_miss(caplog):
    emit_mod._warned_no_witness["done"] = False
    before = emit_misses()
    with caplog.at_level("WARNING", logger="provenance_telemetry"):
        emit_mod._install_export_witness(object())
        emit_mod._install_export_witness(object())
    assert emit_misses() == before
    assert sum("cannot locate" in r.message for r in caplog.records) == 1


# 6 ---------------------------------------------------- observed_trace propagation
def test_observed_trace_propagates_and_drops_bad_values(mem):
    client, exp = mem
    m = load_mapping({"slots": {"trace_id": "tid", "user_id": "uid", "session_id": "sid"},
                      "metadata": ["good", "long", "uni"]})
    vals = {"tid": "t", "uid": "u1", "sid": "s1", "good": "ok",
            "long": "x" * 201, "uni": "café"}
    before = emit_misses()
    with observed_trace(m, vals, name="entry"):
        with observe_span("child"):
            pass
    spans = {s.name: s for s in spans_of(client, exp)}
    child = spans["child"].attributes
    assert child[USER] == "u1" and child[SESSION] == "s1"
    assert child["langfuse.trace.metadata.good"] == "ok"
    assert "langfuse.trace.metadata.long" not in child
    assert "langfuse.trace.metadata.uni" not in child
    # still on the entry span via set_trace_standard
    assert "long" in spans["entry"].attributes["langfuse.trace.metadata"]
    assert emit_misses() == before


# 7 -------------------------------------------------------------------- flush
def test_flush_disabled_noop(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    before = emit_misses()
    flush()
    assert emit_misses() == before


def test_flush_makes_spans_visible(mem):
    client, exp = mem
    with observe_span("x"):
        pass
    assert exp.get_finished_spans() == ()  # batched, not yet exported
    flush()
    assert len(exp.get_finished_spans()) == 1


def test_flush_error_is_counted(monkeypatch, mem):
    client, _ = mem
    monkeypatch.setattr(type(client), "flush", lambda self: (_ for _ in ()).throw(RuntimeError("x")))
    before = emit_misses()
    flush()
    assert emit_misses() == before + 1


# 8 ------------------------------------------------------------ malformed ids
def test_emit_boundary_malformed_ids_one_miss(mem):
    before = emit_misses()
    ids = {"trace_id": "not-hex", "span_id": "zzzz"}
    t = {"started_at": None, "ended_at": None}
    assert emit_boundary(MAPPING, VALUES, ids=ids, name="b", timing=t) is None
    assert emit_misses() == before + 1


# 9 ------------------------------------------- set_trace_standard unchanged
def test_set_trace_standard_attributes_pinned(mem):
    client, exp = mem
    m = load_mapping({
        "slots": {"trace_id": "tid", "user_id": "uid", "session_id": "sid",
                  "release": "rel", "version": "ver"},
        "tags": ["engine", "secret"],
        "metadata": ["note", "secret"],
        "content_bearing": ["secret"],
    })
    vals = {"tid": "t", "uid": "u", "sid": "s", "rel": "r1", "ver": "v2",
            "engine": "e", "secret": "hide", "note": "n"}
    with client.start_as_current_observation(name="e", as_type="span"):
        set_trace_standard(m, vals)
    a = spans_of(client, exp)[0].attributes
    red = pt.redact("hide")
    assert a[USER] == "u" and a[SESSION] == "s"
    assert a["langfuse.release"] == "r1" and a["langfuse.version"] == "v2"
    assert list(a[TAGS]) == ["e", red]
    import json
    assert json.loads(a["langfuse.trace.metadata"]) == {"note": "n", "secret": red}
