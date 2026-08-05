"""set_trace_standard — project provenance values onto the current Langfuse trace.

Fail-soft-and-countable (the witness-channel axiom): a Langfuse outage, a missing
SDK, or an emit error is logged and counted (`emit_misses()`), never raised. The
telemetry channel must not stop the work it observes — a review starts even when
Langfuse is down.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

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


def _slot_kwarg(slot: str) -> str:
    # langfuse update_current_trace uses `id` for the trace identity.
    return "id" if slot == "trace_id" else slot


def _encode_score(value: Any, encoding: str) -> float:
    if encoding == "count_total" and isinstance(value, (list, tuple)) and len(value) == 2:
        num, den = value
        return float(num) / float(den) if den else 0.0
    return float(value)


def set_trace_standard(mapping: Mapping, values: Dict[str, Any]) -> None:
    """Project ``values`` onto the current Langfuse trace per ``mapping``.

    ``values`` is a flat dict of the caller's provenance fields; the mapping
    decides which land in which Langfuse slot, which become tags/metadata, which
    become scores, and which are content-bearing (hashed, not dropped). Never
    raises.
    """
    if not _enabled():
        return
    try:
        from langfuse.decorators import langfuse_context  # lazy: no import cost when disabled
    except Exception:  # noqa: BLE001 — SDK absent is a soft miss, not a crash
        _miss("langfuse SDK unavailable")
        return

    try:
        content_bearing = set(mapping.content_bearing)

        def project(field: str) -> Any:
            v = values.get(field)
            if v is None:
                return None
            return redact(v) if field in content_bearing else v

        trace_kwargs: Dict[str, Any] = {}
        for slot, field in mapping.slots.items():
            val = project(field)
            if val is None:
                continue
            if slot == "trace_id":
                # langfuse v2 decorators fix the trace id when @observe CREATES the trace
                # and cannot change it on a running trace; `update_current_trace` has no
                # `id` kwarg — passing one raises and aborts the ENTIRE enrichment (tags,
                # user, metadata all lost with it). Best-effort set the ROOT id instead:
                # it takes effect only when this runs BEFORE the trace starts, otherwise
                # the trace keeps its own id and we still enrich everything else. (Joining
                # a trace across the @observe boundary is the caller's job at the entry.)
                try:
                    langfuse_context._set_root_trace_id(str(val))
                except Exception:  # noqa: BLE001 — never let id-setting sink the enrichment
                    pass
                continue
            trace_kwargs[_slot_kwarg(slot)] = val

        tags = [str(project(f)) for f in mapping.tags if values.get(f) is not None]
        if tags:
            trace_kwargs["tags"] = tags

        md = {f: project(f) for f in mapping.metadata if values.get(f) is not None}
        if md:
            trace_kwargs["metadata"] = md

        if trace_kwargs:
            langfuse_context.update_current_trace(**trace_kwargs)

        for name, spec in mapping.scores.items():
            if values.get(name) is not None:
                try:
                    langfuse_context.score_current_trace(
                        name=name, value=_encode_score(values[name], spec.encoding)
                    )
                except Exception as exc:  # noqa: BLE001 — one bad score never sinks the trace
                    _miss(f"score {name!r} failed: {exc}")
    except Exception as exc:  # noqa: BLE001 — the whole emission is soft
        _miss(f"emit failed: {exc}")
