"""The ratifiable mapping config + its SHAPE validation.

Two-tier validation, by design (ADR-0038): this library validates *shape* — the
Langfuse slots and score encodings a mapping may target are a closed set, and an
unknown one is refused at load. It deliberately does NOT validate that the
provenance *field names* on the right-hand side exist — that is *truth*, and it
belongs with whoever owns the vocabulary (a CI check in their own repo). That
split is what lets a finance team map fields this library never heard of.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Union

import yaml
from pydantic import BaseModel, field_validator

# The closed set of Langfuse trace slots a mapping may target. Unknown -> refuse.
KNOWN_SLOTS = {"trace_id", "user_id", "session_id", "release", "version"}
# The closed set of score encodings. Unknown -> refuse.
KNOWN_SCORE_ENCODINGS = {"ordinal", "fraction", "binary_per_join", "count_total"}


class ScoreSpec(BaseModel):
    encoding: str

    @field_validator("encoding")
    @classmethod
    def _known_encoding(cls, v: str) -> str:
        if v not in KNOWN_SCORE_ENCODINGS:
            raise ValueError(
                f"unknown score encoding {v!r}; known: {sorted(KNOWN_SCORE_ENCODINGS)}"
            )
        return v


class Mapping(BaseModel):
    """A projection of a provenance vocabulary onto Langfuse primitives.

    `slots`/`tags`/`metadata`/`content_bearing` values are *provenance field
    names* — the caller's vocabulary, opaque to this library.
    """

    version: int = 1
    slots: Dict[str, str] = {}            # langfuse slot -> provenance field
    tags: List[str] = []                  # provenance fields projected to tags
    metadata: List[str] = []              # provenance fields projected to metadata
    scores: Dict[str, ScoreSpec] = {}     # score name -> spec
    content_bearing: List[str] = []       # provenance fields to redact (hash-don't-drop)

    @field_validator("slots")
    @classmethod
    def _known_slots(cls, v: Dict[str, str]) -> Dict[str, str]:
        unknown = set(v) - KNOWN_SLOTS
        if unknown:
            raise ValueError(
                f"unknown Langfuse slot(s) {sorted(unknown)}; known: {sorted(KNOWN_SLOTS)}"
            )
        return v


def load_mapping(source: Union[str, Path, dict]) -> Mapping:
    """Load + shape-validate a mapping. Raises pydantic ``ValidationError`` on an
    unknown slot or score encoding (the shape gate). Accepts a path or a dict."""
    if isinstance(source, dict):
        data = source
    else:
        data = yaml.safe_load(Path(source).read_text(encoding="utf-8")) or {}
    return Mapping(**data)
