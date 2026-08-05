"""Span carriers — langfuse v3/v4 (OpenTelemetry).

An LLM call is traced two ways: **direct-provider** needs an *explicit* span; **through a
LiteLLM proxy** needs its callback fed *metadata*. Both derive from one ``span_descriptor``
so the two paths stay shape-equivalent — "same story in the same words" at the environment
boundary where comparison matters most.

Under v4 the direct-provider path nests natively: a generation created while a langfuse
span is the current OTel context attaches to it automatically. ``observe_span`` opens that
span; ``traced`` opens/decorates one; ``litellm_metadata`` remains for callbacks that read
request metadata rather than the OTel context.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Optional

logger = logging.getLogger("provenance_telemetry")


def _enabled() -> bool:
    return bool(os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"))


def span_descriptor(operation: str, **attributes: Any) -> Dict[str, Any]:
    """The canonical span shape both carriers derive from. Pure and deterministic."""
    return {
        "name": operation,
        "attributes": {k: v for k, v in attributes.items() if v is not None},
    }


def litellm_metadata(
    operation: str,
    *,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    **attributes: Any,
) -> Dict[str, Any]:
    """Metadata dict to pass as ``metadata=`` on a LiteLLM completion for callbacks that
    read request metadata. Under v4 a completion made inside an active langfuse span nests
    via the OTel context without this; kept for callback-based nesting + generation naming.
    """
    d = span_descriptor(operation, **attributes)
    md: Dict[str, Any] = {"generation_name": d["name"], **d["attributes"]}
    if trace_id:
        md["existing_trace_id"] = trace_id
    if user_id:
        md["trace_user_id"] = user_id
    if session_id:
        md["session_id"] = session_id
    if tags:
        md["tags"] = list(tags)
    return md


@contextmanager
def observe_span(operation: str, **attributes: Any) -> Iterator[Dict[str, Any]]:
    """Explicit Langfuse span for a direct-provider call. Yields the same
    ``span_descriptor`` the LiteLLM carrier uses, so the two paths stay shape-equivalent.
    Fail-soft: if the SDK is absent/errors, the block still runs.
    """
    d = span_descriptor(operation, **attributes)
    if not _enabled():
        yield d
        return
    try:
        from langfuse import get_client
        cm = get_client().start_as_current_observation(name=operation, as_type="span")
    except Exception as exc:  # noqa: BLE001 — telemetry never blocks the work
        from .emit import _miss
        _miss(f"observe_span setup failed: {exc}")
        yield d
        return
    with cm as span:
        if d["attributes"]:
            try:
                span.update(metadata=d["attributes"])
            except Exception as exc:  # noqa: BLE001
                from .emit import _miss
                _miss(f"observe_span update failed: {exc}")
        yield d


def traced(name: Optional[str] = None, as_type: Optional[str] = None):
    """Decorator that OPENS a Langfuse span/trace around the wrapped function (v4 ``observe``).

    For a top-level entry that must open on a CHOSEN trace id (a join), prefer
    ``observed_trace`` — ``@observe`` mints its own id. **Pass-through when Langfuse is
    disabled**, so no-creds code carries no runtime dependency. Gating is at decoration
    time, matching the deploy model where env is set before modules import.
    """
    def deco(fn):
        if not _enabled():
            return fn
        try:
            from langfuse import observe
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            if as_type is not None:
                kwargs["as_type"] = as_type
            return observe(**kwargs)(fn)
        except Exception:  # noqa: BLE001 — SDK absent -> pass-through, never a crash
            return fn

    return deco
