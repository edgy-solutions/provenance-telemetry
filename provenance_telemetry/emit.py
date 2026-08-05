"""Project provenance onto the current Langfuse trace — langfuse v3/v4 (OpenTelemetry).

Two entry points:

* ``set_trace_standard(mapping, values)`` — enrich the CURRENT trace in place. v4 has no
  imperative ``update_current_trace``; trace-level fields are OTel span attributes
  (``user.id``, ``session.id``, ``langfuse.trace.tags`` …), so we set them on the active
  span. The trace *id* cannot be changed once a trace is running — set it at the entry via
  ``observed_trace`` (below), never here.
* ``observed_trace(mapping, values, *, name)`` — the v4-native ENTRY: open (or JOIN) a trace
  keyed on the mapping's ``trace_id`` and enrich it. ``create_trace_id(seed=...)`` makes the
  langfuse id deterministic from an upstream id (X-Trace-Id / a doc's id), so the same id on
  two services lands ONE trace — the join is native, not a v2 private-API hack.

Fail-soft-and-countable (the witness-channel axiom): a Langfuse outage, a missing SDK, or an
emit error is logged and counted (``emit_misses()``), never raised.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator

from .mapping import Mapping
from .redact import redact

logger = logging.getLogger("provenance_telemetry")

# Observable miss counter — a soft failure that nobody can see is a silent one.
_misses = {"count": 0}


def emit_misses() -> int:
    """How many emissions have failed soft since import (for a health metric)."""
    return _misses["count"]


def _miss(reason: str) -> None:
    _misses["count"] += 1
    logger.warning("provenance-telemetry emit miss (counted, not raised): %s", reason)


def _enabled() -> bool:
    return bool(os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"))


def _encode_score(value: Any, encoding: str) -> float:
    if encoding == "count_total" and isinstance(value, (list, tuple)) and len(value) == 2:
        num, den = value
        return float(num) / float(den) if den else 0.0
    return float(value)


def set_trace_standard(mapping: Mapping, values: Dict[str, Any]) -> None:
    """Project ``values`` onto the current Langfuse trace per ``mapping`` (langfuse v4).

    Sets the mapped identity/tags/metadata as OTel span attributes on the active span and
    emits scores. The ``trace_id`` slot is NOT applied here — v4 fixes a trace's id at
    creation; use ``observed_trace`` at the entry to open/join on a chosen id. Never raises.
    """
    if not _enabled():
        return
    try:
        from langfuse import LangfuseOtelSpanAttributes as A, get_client
        from opentelemetry import trace as _otel
    except Exception:  # noqa: BLE001 — SDK absent is a soft miss, not a crash
        _miss("langfuse v4 / opentelemetry unavailable")
        return

    try:
        content_bearing = set(mapping.content_bearing)

        def project(field: str) -> Any:
            v = values.get(field)
            if v is None:
                return None
            return redact(v) if field in content_bearing else v

        span = _otel.get_current_span()

        # slots -> trace-level OTel attributes. trace_id is set at the entry, not here.
        _slot_attr = {"user_id": A.TRACE_USER_ID, "session_id": A.TRACE_SESSION_ID,
                      "release": A.RELEASE, "version": A.VERSION}
        for slot, field in mapping.slots.items():
            val = project(field)
            if val is None or slot == "trace_id":
                continue
            attr = _slot_attr.get(slot)
            if attr is not None:
                span.set_attribute(attr, str(val))

        tags = [str(project(f)) for f in mapping.tags if values.get(f) is not None]
        if tags:
            span.set_attribute(A.TRACE_TAGS, tags)

        md = {f: project(f) for f in mapping.metadata if values.get(f) is not None}
        if md:
            span.set_attribute(A.TRACE_METADATA, json.dumps(md, default=str))

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
    body opens (child spans, LLM generations under the active OTel context) nests under it.
    Fail-soft: on any setup error the body still runs, untraced.
    """
    if not _enabled():
        yield
        return
    try:
        from langfuse import get_client
        client = get_client()
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
        yield
