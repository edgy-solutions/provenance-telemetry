"""Two carriers, one span shape.

An LLM call is traced two ways depending on the environment: **direct-provider**
(e.g. sandbox Ollama) needs an *explicit* span; **through a LiteLLM proxy** (e.g.
work) needs its callback fed *metadata* so the generation nests under our trace.
The failure mode is the two paths drifting until their traces stop being
comparable — which defeats "same story in the same words" at exactly the
environment boundary where comparison matters most.

So both carriers derive from one `span_descriptor`: same name, same attributes,
same nesting — differing only in transport. `observe_span` yields the descriptor
so callers (and the path-equivalence seal) can see the shape both paths share.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Optional

logger = logging.getLogger("provenance_telemetry")


def span_descriptor(operation: str, **attributes: Any) -> Dict[str, Any]:
    """The canonical span shape both carriers derive from. Pure and deterministic.

    ``operation`` is the human name ("extract table crop 3/5 for document X");
    ``attributes`` are the span's provenance attributes (None values dropped).
    """
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
    """Metadata dict to pass as ``metadata=`` on a LiteLLM completion so its
    Langfuse callback nests the generation under our trace (the WORK path).

    Shape is derived from ``span_descriptor`` — the ``name``/``attributes`` match
    what ``observe_span`` would emit; only the transport keys (``existing_trace_id``
    etc., which LiteLLM's callback reads) are added.
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
    """Explicit Langfuse span for a direct-provider call (the SANDBOX path).

    Yields the same ``span_descriptor`` the LiteLLM carrier uses, so the two paths
    stay shape-equivalent. Fail-soft: if the SDK is absent/errors, the block still
    runs — the operation is never blocked by its own telemetry.
    """
    d = span_descriptor(operation, **attributes)
    enabled = bool(os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"))
    if not enabled:
        yield d
        return
    try:
        from langfuse.decorators import langfuse_context

        langfuse_context.update_current_observation(name=d["name"], metadata=d["attributes"])
    except Exception as exc:  # noqa: BLE001 — telemetry never blocks the work
        logger.warning("provenance-telemetry observe_span miss (counted, not raised): %s", exc)
        from .emit import _miss

        _miss(f"observe_span failed: {exc}")
    yield d


def traced(name: Optional[str] = None, as_type: Optional[str] = None):
    """Decorator that OPENS a Langfuse trace around the wrapped function.

    The one primitive `set_trace_standard`/`observe_span` assume but can't provide:
    they enrich/nest the *current* trace; this creates it. Enrich the opened trace
    with `set_trace_standard` and nest LLM calls with `observe_span` inside.

    **Pass-through when Langfuse is disabled** — file-mode / no-creds code carries
    no runtime dependency and no import cost. (Generalizes the legacy `safe_observe`.)
    Gating is evaluated at decoration time, matching the deployment model where env
    is set before the process imports its modules.
    """
    def deco(fn):
        if not (os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")):
            return fn
        try:
            from langfuse.decorators import observe

            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            if as_type is not None:
                kwargs["as_type"] = as_type
            return observe(**kwargs)(fn)
        except Exception:  # noqa: BLE001 — SDK absent -> pass-through, never a crash
            return fn

    return deco
