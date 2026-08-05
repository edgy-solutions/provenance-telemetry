"""provenance-telemetry — project a provenance doctrine into an observability backend.

The public surface is small on purpose: a mapping loader (shape-validated), a
fail-soft trace emitter, two span carriers that share one shape, and a redactor.
No vocabulary lives here — it lives in the mapping config the caller supplies.
"""
from .mapping import Mapping, ScoreSpec, load_mapping, KNOWN_SLOTS, KNOWN_SCORE_ENCODINGS
from .emit import set_trace_standard, observed_trace, emit_misses
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
    "span_descriptor",
    "litellm_metadata",
    "observe_span",
    "traced",
    "redact",
]
