"""Seals for 0.2.2: a W3C trace-id seed is the trace id; the pure W3C parsers; traced() IO flags.

No network: every client points at localhost:1 and exports to an in-memory exporter.
"""
import itertools

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from provenance_telemetry import (
    format_traceparent, load_mapping, mint_boundary_ids, observed_trace,
    parse_traceparent, parse_tracestate, trace_id_for, traced,
)

_n = itertools.count()
MAPPING = load_mapping({"slots": {"trace_id": "tid"}})
TID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT = "00f067aa0ba902b7"
TP = f"00-{TID}-{PARENT}-01"


@pytest.fixture(autouse=True)
def _isolate_sdk_singletons():
    from langfuse._client.resource_manager import LangfuseResourceManager
    LangfuseResourceManager.reset()
    yield
    LangfuseResourceManager.reset()


@pytest.fixture
def mem(monkeypatch):
    from langfuse import Langfuse
    exp = InMemorySpanExporter()
    pk = f"pk-test-w3c-{next(_n)}"
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", pk)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("DEPLOY_ENV", raising=False)
    client = Langfuse(public_key=pk, secret_key="sk-test", base_url="http://localhost:1",
                      span_exporter=exp)
    return client, exp


# ---- trace_id_for -------------------------------------------------------------------

def test_w3c_seed_is_verbatim_and_needs_no_langfuse(monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    assert trace_id_for(TID) == TID


def test_dashed_uuid_seed_control_equals_create_trace_id(mem):
    client, _ = mem
    seed = "123e4567-e89b-12d3-a456-426614174000"
    assert trace_id_for(seed) == client.create_trace_id(seed=seed)
    assert trace_id_for(seed) != seed.replace("-", "")


@pytest.mark.parametrize("seed", ["0" * 32, TID.upper(), TID[:-1], TID + "0", "g" * 32])
def test_non_w3c_seeds_are_hashed(mem, seed):
    client, _ = mem
    assert trace_id_for(seed) == client.create_trace_id(seed=seed)
    assert trace_id_for(seed) != seed


@pytest.mark.parametrize("seed", [None, ""])
def test_empty_seed_is_none(seed):
    assert trace_id_for(seed) is None


def test_observed_trace_opens_on_w3c_seed_and_parent(mem):
    client, exp = mem
    with observed_trace(MAPPING, {"tid": TID}, name="entry", parent_span_id=PARENT):
        pass
    client.flush()
    (span,) = [s for s in exp.get_finished_spans() if s.name == "entry"]
    assert span.context.trace_id == int(TID, 16)
    assert format(span.parent.span_id, "016x") == PARENT


def test_observed_trace_w3c_seed_no_parent_is_root_on_that_id(mem):
    client, exp = mem
    with observed_trace(MAPPING, {"tid": TID}, name="entry"):
        pass
    client.flush()
    (span,) = [s for s in exp.get_finished_spans() if s.name == "entry"]
    assert span.context.trace_id == int(TID, 16)
    assert span.parent is None


def test_mint_boundary_ids_returns_w3c_seed(mem):
    assert mint_boundary_ids(trace_seed=TID)["trace_id"] == TID


def test_mint_boundary_ids_dashed_seed_unchanged(mem):
    client, _ = mem
    seed = "123e4567-e89b-12d3-a456-426614174000"
    assert mint_boundary_ids(trace_seed=seed)["trace_id"] == client.create_trace_id(seed=seed)


# ---- traceparent ---------------------------------------------------------------------

def test_valid_00():
    assert parse_traceparent(TP) == (TID, PARENT, "01")
    assert parse_traceparent(f"  {TP} \t") == (TID, PARENT, "01")
    assert parse_traceparent([TP]) == (TID, PARENT, "01")


@pytest.mark.parametrize("bad", [
    f"00-{TID.upper()}-{PARENT}-01",
    f"00-{TID}-{PARENT.upper()}-01",
    f"00-{'0' * 32}-{PARENT}-01",
    f"00-{TID}-{'0' * 16}-01",
    f"ff-{TID}-{PARENT}-01",
    TP[:-1],
    TP + "0",
    f"00-{TID}-{PARENT}-01-extra",
    f"01-{TID}-{PARENT}-01x",
    f"00-{'g' * 32}-{PARENT}-01",
    f"00-{TID}-{PARENT}-zz",
    "", "garbage", None, 5,
])
def test_invalid_traceparent(bad):
    assert parse_traceparent(bad) is None


def test_higher_version_with_suffix_accepted():
    assert parse_traceparent(f"01-{TID}-{PARENT}-01-future") == (TID, PARENT, "01")
    assert parse_traceparent(f"01-{TID}-{PARENT}-01") == (TID, PARENT, "01")


def test_two_traceparent_headers_rejected():
    assert parse_traceparent([TP, TP]) is None
    assert parse_traceparent([]) is None


def test_format_traceparent_roundtrip():
    assert format_traceparent(TID, PARENT) == TP
    assert format_traceparent(TID, PARENT, "00") == f"00-{TID}-{PARENT}-00"
    assert parse_traceparent(format_traceparent(TID, PARENT)) == (TID, PARENT, "01")


# ---- tracestate ----------------------------------------------------------------------

def test_tracestate_valid_and_whitespace_and_empty_members():
    assert parse_tracestate("a=1, b=2 ,,c@t=3") == "a=1,b=2,c@t=3"
    assert parse_tracestate(["a=1", "b=2"]) == "a=1,b=2"


def test_tracestate_33_members_dropped_32_kept():
    assert parse_tracestate(",".join(f"k{i}=v" for i in range(33))) is None
    assert parse_tracestate(",".join(f"k{i}=v" for i in range(32))) is not None


@pytest.mark.parametrize("bad", [
    "a=1,a=2", "A=1", "1a=1", "a=b=c", "a=", "=1", "a", "a=\x7f",
    "a" * 257 + "=1", "a=" + "v" * 257, None, "", ",,",
])
def test_tracestate_malformed_dropped_whole(bad):
    assert parse_tracestate(bad) is None


def test_tracestate_multitenant_key():
    assert parse_tracestate("t1@vendor=x") == "t1@vendor=x"
    assert parse_tracestate("t1@" + "v" * 15 + "=x") is None


def test_tracestate_600_chars_truncated_from_the_right():
    members = [f"k{i:02d}=" + "v" * 56 for i in range(10)]  # 10 x 60 = 600 with commas
    out = parse_tracestate(",".join(members))
    assert len(out) <= 512
    assert out == ",".join(members[:len(out.split(","))])
    assert len(out.split(",")) == 8


def test_tracestate_with_invalid_traceparent_is_the_callers_drop():
    # Pure parsers: the caller pairs them. A bad traceparent is None, so tracestate is unused.
    assert parse_traceparent("bad") is None
    assert parse_tracestate("a=1") == "a=1"


# ---- traced(capture_*) ---------------------------------------------------------------

@pytest.fixture
def doubled_observe(monkeypatch):
    calls = []

    def observe(**kw):
        calls.append(kw)
        return lambda fn: fn

    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    import langfuse
    monkeypatch.setattr(langfuse, "observe", observe)
    return calls


def test_traced_default_passes_neither_capture_key(doubled_observe):
    traced(name="x")(lambda: 1)
    assert doubled_observe == [{"name": "x"}]


def test_traced_capture_false_is_forwarded(doubled_observe):
    traced(capture_input=False, capture_output=False)(lambda: 1)
    assert doubled_observe == [{"capture_input": False, "capture_output": False}]
