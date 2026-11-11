"""Replay-safe entry boundary for a journaled step of a durable-execution runtime.

A durable runtime (e.g. Restate's ``ctx.run``) re-runs a handler from the top on replay,
returning recorded values only for journaled steps. ``observed_trace`` re-enters on every
replay and mints a fresh span id each time, so one execution shows up as N boundary spans.
These three primitives fix that:

* ``mint_boundary_ids`` — mint the boundary's identity INSIDE a journaled step, so the
  runtime hands back the identical ids on every replay.
* ``boundary_parent`` — make those ids the ambient NON-RECORDING parent. It exports nothing,
  so a replay re-entering it cannot double; everything opened inside nests under it.
* ``emit_boundary`` — export the boundary span itself, once, from inside a journaled step.

See ``docs/durable-execution.md``. Everything is fail-soft and countable (``emit_misses``).
"""
from __future__ import annotations

import datetime
import logging
import secrets
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, Iterator, Optional

from .emit import (
    _enabled,
    _enter_propagation,
    _install_export_witness,
    _miss,
    _trace_attributes,
)

logger = logging.getLogger("provenance_telemetry")


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _ns(dt: datetime.datetime) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def mint_boundary_ids(trace_seed: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Mint the boundary's identity: ``{"trace_id": 32-hex | None, "span_id": 16-hex}``.

    **Call inside the journaled step** so the runtime replays the identical pair.
    ``trace_seed`` is the upstream id (X-Trace-Id) so the cross-service join still holds;
    with no seed a random trace id is minted once and then replayed from the journal.
    ``trace_id`` is None when telemetry is disabled or minting failed (counted).
    """
    ids: Dict[str, Optional[str]] = {"trace_id": None, "span_id": secrets.token_hex(8)}
    if _enabled():
        try:
            from langfuse import get_client
            ids["trace_id"] = get_client().create_trace_id(
                seed=str(trace_seed) if trace_seed else None
            )
        except Exception as exc:  # noqa: BLE001 — telemetry never breaks the work
            _miss(f"mint_boundary_ids failed: {exc}")
            ids["trace_id"] = None
    return ids


@contextmanager
def boundary_parent(ids: Dict[str, Any], *, mapping: Any = None,
                    values: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
    """Make the journaled ``(trace_id, span_id)`` the AMBIENT OTel parent, exporting
    NOTHING for the boundary itself.

    Everything opened inside nests under it through the ordinary OTel context, so existing
    ``observe_span`` / ``traced`` instrumentation needs no change. The parent is
    non-recording, so re-entering this block on a replay exports nothing.

    With ``mapping`` and ``values`` the mapped user/session/tags/metadata are also
    propagated onto every child opened inside (v4 filters on per-span attributes).

    Yields a timing dict ``{"started_at", "ended_at"}`` to hand to :func:`emit_boundary`;
    ``ended_at`` is set on exit. Fail-soft: a setup error is counted and the body runs
    untraced.
    """
    timing: Dict[str, Any] = {"started_at": _utcnow(), "ended_at": None}
    stack = ExitStack()
    if _enabled() and ids and ids.get("trace_id") and ids.get("span_id"):
        try:
            from opentelemetry import context as _octx, trace as _otr
            from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
            tok = _octx.attach(_otr.set_span_in_context(NonRecordingSpan(SpanContext(
                trace_id=int(ids["trace_id"], 16),
                span_id=int(ids["span_id"], 16),
                is_remote=True,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
            ))))

            def _detach() -> None:
                try:
                    _octx.detach(tok)
                except Exception:  # noqa: BLE001 — detach errors are swallowed
                    pass

            stack.callback(_detach)
            if mapping is not None and values is not None:
                _enter_propagation(stack, mapping, values)
        except Exception as exc:  # noqa: BLE001 — untraced beats broken
            _miss(f"boundary_parent setup failed: {exc}")
    try:
        yield timing
    finally:
        timing["ended_at"] = _utcnow()
        try:
            stack.close()
        except Exception:  # noqa: BLE001
            pass


def emit_boundary(mapping: Any, values: Dict[str, Any], *, ids: Dict[str, Any],
                  name: str, timing: Dict[str, Any]) -> Optional[str]:
    """Export the boundary span itself, keyed on the journaled span id, over OTLP.

    Returns the span id (so the journal entry carries something legible), or None when
    disabled / ids missing (no miss) or on any error (counted).

    **Call exactly once, inside the journaled step.** On Langfuse v4 the OTLP path does NOT
    upsert: a second call with the same id produces a DUPLICATE observation. The residual
    window is "export succeeded, the step's journal entry did not commit", which gives one
    duplicate on replay. If the handler dies before this call the parent is MISSING
    (children show as roots on the right trace), never a phantom one.

    The span is the trace's root (no parent) and carries the trace-level attributes from
    the mapping, since the ambient boundary parent is non-recording and cannot. Scores are
    not sent here. The span is built by hand on the SDK's own tracer scope (a span whose
    scope differs is dropped by the Langfuse processor); no id generator is swapped.
    """
    if not _enabled() or not ids or not ids.get("trace_id") or not ids.get("span_id"):
        return None
    try:
        from langfuse import LangfuseOtelSpanAttributes as A, get_client
        try:  # newer OTel SDKs made ``Span`` abstract; the concrete class is ``_Span``
            from opentelemetry.sdk.trace import _Span as Span
        except ImportError:
            from opentelemetry.sdk.trace import Span
        from opentelemetry.trace import SpanContext, TraceFlags

        client = get_client()
        _install_export_witness(client)
        tracer = client._otel_tracer

        ctx = SpanContext(
            trace_id=int(ids["trace_id"], 16),
            span_id=int(ids["span_id"], 16),
            is_remote=False,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )
        attrs: Dict[str, Any] = {A.OBSERVATION_TYPE: "span", A.TRACE_NAME: name}
        attrs.update(_trace_attributes(mapping, values))
        # One source with every SDK-built span (its children): the client's environment
        # (LANGFUSE_TRACING_ENVIRONMENT) and release, so boundary and children cannot differ.
        if getattr(client, "_environment", None):
            attrs[A.ENVIRONMENT] = client._environment
        if getattr(client, "_release", None):
            attrs[A.RELEASE] = client._release

        started = timing.get("started_at") or _utcnow()
        ended = timing.get("ended_at") or _utcnow()
        span = Span(
            name,
            ctx,
            parent=None,
            resource=tracer.resource,
            attributes=attrs,
            span_processor=tracer.span_processor,
            instrumentation_scope=tracer._instrumentation_scope,
        )
        span.start(start_time=_ns(started))
        span.end(end_time=_ns(ended))
        return ids["span_id"]
    except Exception as exc:  # noqa: BLE001 — the witness channel never breaks the work
        _miss(f"emit_boundary failed: {exc}")
        return None
