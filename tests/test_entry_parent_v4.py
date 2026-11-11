"""Seals for observed_trace's parent handling (0.2.1): a joined entry with no known parent
is a ROOT; a known parent travels with the trace id. Assertions read the EXPORTED spans.

No network: every client points at localhost:1 and exports to an in-memory exporter.
"""
import itertools

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from provenance_telemetry import (
    emit_misses, load_mapping, observe_span, observed_trace,
)

_n = itertools.count()
MAPPING = load_mapping({"slots": {"trace_id": "tid", "user_id": "uid"}})
VALUES = {"tid": "upstream-1", "uid": "svc:a"}
PARENT = "00f067aa0ba902b7"


@pytest.fixture(autouse=True)
def _isolate_sdk_singletons():
    from langfuse._client.resource_manager import LangfuseResourceManager
    LangfuseResourceManager.reset()
    yield
    LangfuseResourceManager.reset()


def make_client(monkeypatch, exporter):
    from langfuse import Langfuse
    pk = f"pk-test-ep-{next(_n)}"
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", pk)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("DEPLOY_ENV", raising=False)
    return Langfuse(public_key=pk, secret_key="sk-test", base_url="http://localhost:1",
                    span_exporter=exporter)


@pytest.fixture
def mem(monkeypatch):
    exp = InMemorySpanExporter()
    yield make_client(monkeypatch, exp), exp


def spans_of(client, exp):
    client.flush()
    return exp.get_finished_spans()


def by_name(spans, name):
    found = [s for s in spans if s.name == name]
    assert len(found) == 1, [s.name for s in spans]
    return found[0]


def test_case_d_seed_no_parent_is_root(mem):
    client, exp = mem
    tid = client.create_trace_id(seed="upstream-1")
    before = emit_misses()
    with observed_trace(MAPPING, VALUES, name="entry"):
        with observe_span("child"):
            pass
    spans = spans_of(client, exp)
    entry, child = by_name(spans, "entry"), by_name(spans, "child")
    assert entry.parent is None
    assert entry.context.trace_id == int(tid, 16)
    assert child.parent.span_id == entry.context.span_id
    assert child.context.trace_id == int(tid, 16)
    assert emit_misses() == before


def test_case_d_root_carries_the_environment_and_release_its_children_carry(monkeypatch):
    """The hand-built root must land in the same Langfuse environment as the SDK-built child."""
    monkeypatch.setenv("LANGFUSE_TRACING_ENVIRONMENT", "env-ep")
    monkeypatch.setenv("LANGFUSE_RELEASE", "rel-ep")
    exp = InMemorySpanExporter()
    client = make_client(monkeypatch, exp)
    with observed_trace(MAPPING, VALUES, name="entry"):
        with observe_span("child"):
            pass
    spans = spans_of(client, exp)
    entry, child = by_name(spans, "entry"), by_name(spans, "child")
    for key, want in (("langfuse.environment", "env-ep"), ("langfuse.release", "rel-ep")):
        assert child.attributes.get(key) == want, key  # control: the SDK stamps it
        assert entry.attributes.get(key) == want, key


def test_control_for_d_sdk_path_invents_a_parent(mem):
    """The detector can see a phantom parent: the OLD call shape exports one."""
    client, exp = mem
    tid = client.create_trace_id(seed="upstream-1")
    with client.start_as_current_observation(trace_context={"trace_id": tid},
                                             name="old", as_type="span"):
        pass
    old = by_name(spans_of(client, exp), "old")
    assert old.parent is not None


def test_case_a_no_seed_unchanged(mem):
    client, exp = mem
    before = emit_misses()
    with observed_trace(MAPPING, {"uid": "svc:a"}, name="entry"):
        pass
    entry = by_name(spans_of(client, exp), "entry")
    assert entry.parent is None
    assert emit_misses() == before


def test_case_b_valid_parent_travels_with_trace_id(mem):
    client, exp = mem
    tid = client.create_trace_id(seed="upstream-1")
    before = emit_misses()
    with observed_trace(MAPPING, VALUES, name="entry", parent_span_id=PARENT):
        pass
    entry = by_name(spans_of(client, exp), "entry")
    assert entry.parent.span_id == int(PARENT, 16)
    assert entry.context.trace_id == int(tid, 16)
    assert emit_misses() == before


def test_case_c_ambient_span_of_same_trace_is_the_parent(mem):
    client, exp = mem
    before = emit_misses()
    with observed_trace(MAPPING, VALUES, name="outer"):
        with observed_trace(MAPPING, VALUES, name="inner"):
            pass
    spans = spans_of(client, exp)
    outer, inner = by_name(spans, "outer"), by_name(spans, "inner")
    assert outer.parent is None
    assert inner.parent is not None
    assert inner.parent.span_id == outer.context.span_id
    assert inner.context.trace_id == outer.context.trace_id
    assert emit_misses() == before


@pytest.mark.parametrize("bad", ["xyz", "00f067aa0ba902b", "0" * 16, "g" * 16, ""])
def test_case_e_invalid_parent_counts_one_miss_then_root(mem, bad):
    client, exp = mem
    tid = client.create_trace_id(seed="upstream-1")
    before = emit_misses()
    with observed_trace(MAPPING, VALUES, name="entry", parent_span_id=bad):
        pass
    entry = by_name(spans_of(client, exp), "entry")
    assert emit_misses() == before + 1
    assert entry.parent is None
    assert entry.context.trace_id == int(tid, 16)


def test_case_f_parent_without_seed_counts_one_miss(mem):
    client, exp = mem
    before = emit_misses()
    with observed_trace(MAPPING, {"uid": "svc:a"}, name="entry", parent_span_id=PARENT):
        pass
    entry = by_name(spans_of(client, exp), "entry")
    assert emit_misses() == before + 1
    assert entry.parent is None


def test_body_exception_in_d_propagates_and_marks_error(mem):
    client, exp = mem
    before = emit_misses()
    with pytest.raises(ValueError, match="body"):
        with observed_trace(MAPPING, VALUES, name="entry"):
            raise ValueError("body")
    entry = by_name(spans_of(client, exp), "entry")
    assert entry.status.status_code == StatusCode.ERROR
    assert emit_misses() == before
