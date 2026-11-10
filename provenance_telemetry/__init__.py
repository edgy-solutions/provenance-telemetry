"""provenance-telemetry — project a provenance doctrine into an observability backend.

The public surface is small on purpose: a mapping loader (shape-validated), a
fail-soft trace emitter (with a counted-miss witness over refused exports and a flush),
two span carriers that share one shape, a redactor, and three replay-safe boundary
primitives for journaled steps of a durable-execution runtime.
No vocabulary lives here — it lives in the mapping config the caller supplies.
"""
from .mapping import Mapping, ScoreSpec, load_mapping, KNOWN_SLOTS, KNOWN_SCORE_ENCODINGS
from .emit import set_trace_standard, observed_trace, emit_misses, flush
from .boundary import mint_boundary_ids, boundary_parent, emit_boundary
from .spans import span_descriptor, litellm_metadata, observe_span, traced
from .redact import redact

__all__ = [
    "Mapping",
    "ScoreSpec",
    "load_mapping",
    "KNOWN_SLOTS",
    "KNOWN_SCORE_ENCODINGS",
    "set_trace_standard",
    "observed_trace",
    "emit_misses",
    "flush",
    "mint_boundary_ids",
    "boundary_parent",
    "emit_boundary",
    "span_descriptor",
    "litellm_metadata",
    "observe_span",
    "traced",
    "redact",
]
