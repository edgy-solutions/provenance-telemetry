"""Redaction — hash, don't drop.

A content-bearing field (an identifier, a document snippet, a free-text reason)
is replaced by a stable hash rather than removed. The trace stays *joinable* for
debugging — two traces referencing the same value still collide on the hash —
without the trace carrying the content itself. Provenance without disclosure;
the same shape an audit trail already uses. Which fields are content-bearing is
the caller's mapping config, never named here.
"""
from __future__ import annotations

import hashlib
from typing import Any

_PREFIX = "sha1:"


def redact(value: Any) -> str:
    """Return a stable, non-reversible, join-preserving token for ``value``."""
    digest = hashlib.sha1(str(value).encode("utf-8")).hexdigest()
    return _PREFIX + digest[:16]


def is_redacted(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(_PREFIX)
