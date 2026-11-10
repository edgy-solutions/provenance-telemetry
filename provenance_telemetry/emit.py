"""Project provenance onto the current Langfuse trace — langfuse v3/v4 (OpenTelemetry).

Entry points:

* ``set_trace_standard(mapping, values)`` — enrich the CURRENT trace in place. v4 has no
  imperative ``update_current_trace``; trace-level fields are OTel span attributes
  (``user.id``, ``session.id``, ``langfuse.trace.tags`` …), so we set them on the active
  span. The trace *id* cannot be changed once a trace is running — set it at the entry via
  ``observed_trace`` (below), never here.
* ``observed_trace(mapping, values, *, name)`` — the v4-native ENTRY: open (or JOIN) a trace
  keyed on the mapping's ``trace_id`` and enrich it. ``create_trace_id(seed=...)`` makes the
  langfuse id deterministic from an upstream id (X-Trace-Id / a doc's id), so the same id on
  two services lands ONE trace — the join is native, not a v2 private-API hack. The
  user/session/tags/metadata are also PROPAGATED to every child span opened inside.
* ``flush()`` — flush the batch now, for processes that exit right after the work.

Fail-soft-and-countable (the witness-channel axiom): a Langfuse outage, a missing SDK, or an
emit error is logged and counted (``emit_misses()``), never raised. A refused export (401,
5xx) happens in the OTel batch exporter thread; an export witness wraps the exporter so
those are counted too.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, Iterator

from .mapping import Mapping
from .redact import redact

logger = logging.getLogger("provenance_telemetry")

# Observable miss counter — a soft failure that nobody can see is a silent one.
# Guarded by a lock: the export witness increments it from the OTel exporter thread.
_misses = {"count": 0}
_misses_lock = threading.Lock()
_warned_no_witness = {"done": False}


def emit_misses() -> int:
    """How many emissions have failed soft since import (for a health metric).

    Units: **failed calls plus spans lost on export.** A setup/enrich/score error in the
    calling thread counts 1. A refused or raised export (a 401, a 5xx, a network error),
    seen in the OTel batch exporter thread by the export witness, counts one per span in
    the lost batch. A zero is NOT proof that emission works: pair it with a positive
    control (a known span that must appear in the backend).
    """
    with _misses_lock:
        return _misses["count"]


def _miss(reason: str, n: int = 1) -> None:
    with _misses_lock:
        _misses["count"] += n
    logger.warning("provenance-telemetry emit miss (counted, not raised): %s", reason)


def _wrap_exporter(exporter: Any) -> None:
    from opentelemetry.sdk.trace.export import SpanExportResult

    original = exporter.export

    def export(spans, *args, **kwargs):
        try:
            result = original(spans, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — count, then keep the SDK's own handling
            _miss(f"export raised: {exc!r}", n=len(spans))
            raise
        if result != SpanExportResult.SUCCESS:
            _miss(f"export refused: {getattr(result, 'name', result)}", n=len(spans))
        return result

    exporter.export = export
    exporter._pt_witness = True


def _install_export_witness(client: Any) -> None:
    """Wrap the exporter instance(s) behind ``client`` so a refused export is counted.

    The OTel BatchSpanProcessor exports in its own thread, so a 401/5xx there never
    reaches the calling thread. Idempotent (each exporter instance is marked) and lazy.
    If the SDK's internal shape is absent (a future SDK) nothing is installed and ONE
    warning is logged per process; that is not a miss.
    """
    try:
        procs = list(client._otel_tracer.span_processor._span_processors)
    except Exception:  # noqa: BLE001 — shape moved: say so once, carry on
        if not _warned_no_witness["done"]:
            _warned_no_witness["done"] = True
            logger.warning(
                "provenance-telemetry: cannot locate the SDK span processors; refused "
                "exports will NOT be counted by emit_misses()"
            )
        return
    for proc in procs:
        try:
            exporter = getattr(proc, "span_exporter", None)
            if exporter is None or getattr(exporter, "_pt_witness", False):
                continue
            _wrap_exporter(exporter)
        except Exception:  # noqa: BLE001
            logger.warning("provenance-telemetry: could not wrap an exporter", exc_info=True)


def _enabled() -> bool:
    return bool(os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"))


def flush() -> None:
    """Flush the Langfuse batch now.

    For processes that exit right after the work (subprocess steps, CLI jobs), whose
    pending batch is otherwise lost. No-op when disabled; a failing flush is counted,
    never raised.
    """
    if not _enabled():
        return
    try:
        from langfuse import get_client
        client = get_client()
        _install_export_witness(client)
        client.flush()
    except Exception as exc:  # noqa: BLE001
        _miss(f"flush failed: {exc}")


def _encode_score(value: Any, encoding: str) -> float:
    if encoding == "count_total" and isinstance(value, (list, tuple)) and len(value) == 2:
        num, den = value
        return float(num) / float(den) if den else 0.0
    return float(value)


def _project(mapping: Mapping, values: Dict[str, Any], field: str) -> Any:
    v = values.get(field)
    if v is None:
        return None
    return redact(v) if field in set(mapping.content_bearing) else v


def _trace_attributes(mapping: Mapping, values: Dict[str, Any]) -> Dict[str, Any]:
    """Project ``values`` onto trace-level OTel attribute keys per ``mapping`` (no trace_id).

    Shared by ``set_trace_standard`` (sets them on the active span) and ``emit_boundary``
    (sets them on the boundary span it builds). Raises ImportError if the SDK is absent.
    """
    from langfuse import LangfuseOtelSpanAttributes as A

    out: Dict[str, Any] = {}
    slot_attr = {"user_id": A.TRACE_USER_ID, "session_id": A.TRACE_SESSION_ID,
                 "release": A.RELEASE, "version": A.VERSION}
    for slot, field in mapping.slots.items():
        val = _project(mapping, values, field)
        if val is None or slot == "trace_id":
            continue
        attr = slot_attr.get(slot)
        if attr is not None:
            out[attr] = str(val)

    tags = [str(_project(mapping, values, f)) for f in mapping.tags
            if values.get(f) is not None]
    if tags:
        out[A.TRACE_TAGS] = tags

    md = {f: _project(mapping, values, f) for f in mapping.metadata
          if values.get(f) is not None}
    if md:
        out[A.TRACE_METADATA] = json.dumps(md, default=str)
    return out


def _propagable(v: Any) -> bool:
    return isinstance(v, str) and v.isascii() and len(v) <= 200


def _propagation_kwargs(mapping: Mapping, values: Dict[str, Any]) -> Dict[str, Any]:
    """Keyword arguments for ``langfuse.propagate_attributes`` built from the mapping.

    Same redaction as ``set_trace_standard``. Values are coerced to str; any that is
    non-ASCII or over 200 chars is dropped from the PROPAGATED set (it stays on the entry
    span). ``trace_name`` is deliberately never propagated.
    """
    kw: Dict[str, Any] = {}
    for slot in ("user_id", "session_id", "version"):
        field = mapping.slots.get(slot)
        val = _project(mapping, values, field) if field else None
        if val is not None and _propagable(str(val)):
            kw[slot] = str(val)
    tags = [str(_project(mapping, values, f)) for f in mapping.tags
            if values.get(f) is not None]
    tags = [t for t in tags if _propagable(t)]
    if tags:
        kw["tags"] = tags
    md = {f: str(_project(mapping, values, f)) for f in mapping.metadata
          if values.get(f) is not None}
    md = {k: v for k, v in md.items() if _propagable(v)}
    if md:
        kw["metadata"] = md
    return kw


def _enter_propagation(stack: ExitStack, mapping: Mapping, values: Dict[str, Any]) -> None:
    """Enter ``propagate_attributes`` on ``stack``; any failure is a miss, never a raise."""
    try:
        from langfuse import propagate_attributes
        kw = _propagation_kwargs(mapping, values)
        if kw:
            stack.enter_context(propagate_attributes(**kw))
    except Exception as exc:  # noqa: BLE001
        _miss(f"attribute propagation failed: {exc}")


def set_trace_standard(mapping: Mapping, values: Dict[str, Any]) -> None:
    """Project ``values`` onto the current Langfuse trace per ``mapping`` (langfuse v4).

    Sets the mapped identity/tags/metadata as OTel span attributes on the active span and
    emits scores. The ``trace_id`` slot is NOT applied here — v4 fixes a trace's id at
    creation; use ``observed_trace`` at the entry to open/join on a chosen id. Never raises.
    """
    if not _enabled():
        return
    try:
        from langfuse import get_client
        from opentelemetry import trace as _otel
    except Exception:  # noqa: BLE001 — SDK absent is a soft miss, not a crash
        _miss("langfuse v4 / opentelemetry unavailable")
        return

    try:
        span = _otel.get_current_span()
        for key, val in _trace_attributes(mapping, values).items():
            span.set_attribute(key, val)

        if mapping.scores:
            client = get_client()
            for name, spec in mapping.scores.items():
                if values.get(name) is not None:
                    try:
                        client.score_current_trace(
                            name=name, value=_encode_score(values[name], spec.encoding)
                        )
                    except Exception as exc:  # noqa: BLE001 — one bad score never sinks the trace
                        _miss(f"score {name!r} failed: {exc}")
    except Exception as exc:  # noqa: BLE001 — the whole emission is soft
        _miss(f"emit failed: {exc}")


@contextmanager
def observed_trace(mapping: Mapping, values: Dict[str, Any], *, name: str = "operation",
                   as_type: str = "span") -> Iterator[None]:
    """Open (or JOIN) a trace keyed on the mapping's ``trace_id`` and enrich it (langfuse v4).

    The v4-native entry primitive: derives a deterministic langfuse trace id from the
    mapped ``trace_id`` value via ``create_trace_id(seed=...)`` so the SAME upstream id
    (X-Trace-Id, a doc's id) on two services lands ONE trace — a real join. Everything the
    body opens (child spans, LLM generations under the active OTel context) nests under it
    and carries the propagated user/session/tags/metadata (v4 filters on them per span).
    Fail-soft: on any setup error the body still runs, untraced.

    Note: a joined entry (seed given, no parent) gets a random phantom remote parent span id
    from the SDK; a waterfall reader must treat "parent not in trace" as a root.
    """
    if not _enabled():
        yield
        return
    try:
        from langfuse import get_client
        client = get_client()
        _install_export_witness(client)
        seed = None
        tid_field = mapping.slots.get("trace_id")
        if tid_field is not None and values.get(tid_field) is not None:
            seed = str(values[tid_field])
        trace_context = {"trace_id": client.create_trace_id(seed=seed)} if seed else None
        cm = client.start_as_current_observation(
            trace_context=trace_context, name=name, as_type=as_type
        )
    except Exception as exc:  # noqa: BLE001 — never block the work on telemetry setup
        _miss(f"observed_trace setup failed: {exc}")
        yield
        return

    with cm:
        try:
            set_trace_standard(mapping, values)
        except Exception as exc:  # noqa: BLE001
            _miss(f"observed_trace enrich failed: {exc}")
        with ExitStack() as stack:
            _enter_propagation(stack, mapping, values)
            yield
