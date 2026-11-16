"""W3C Trace Context Level 1 parsing — pure, no langfuse / OpenTelemetry import.

``parse_traceparent`` / ``parse_tracestate`` / ``format_traceparent`` follow the
Recommendation of 2021-11-23. A header may arrive as one string or, when the transport
carries repeated header lines, as a list of strings.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple, Union

HeaderValue = Union[str, List[str], None]

_VERSION = re.compile(r"[0-9a-f]{2}\Z")
_TRACE = re.compile(r"[0-9a-f]{32}\Z")
_PARENT = re.compile(r"[0-9a-f]{16}\Z")
_FLAGS = re.compile(r"[0-9a-f]{2}\Z")
_KEY = re.compile(
    r"(?:[a-z][a-z0-9_\-*/]{0,255}|[a-z0-9][a-z0-9_\-*/]{0,240}@[a-z][a-z0-9_\-*/]{0,13})\Z"
)
_VALUE = re.compile(r"[\x20-\x2b\x2d-\x3c\x3e-\x7e]{1,256}\Z")
_OWS = " \t"
_MAX_MEMBERS = 32
_MAX_LEN = 512


def _single(value: HeaderValue) -> Optional[str]:
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            return None
        value = value[0]
    return value if isinstance(value, str) else None


def parse_traceparent(value: HeaderValue) -> Optional[Tuple[str, str, str]]:
    """Return ``(trace_id, parent_id, flags)`` or None. More than one header -> None."""
    s = _single(value)
    if s is None:
        return None
    s = s.strip(_OWS)
    if len(s) < 55:
        return None
    version = s[:2]
    if not _VERSION.match(version) or version == "ff":
        return None
    if version == "00":
        if len(s) != 55:
            return None
    elif len(s) > 55 and s[55] != "-":
        return None
    if s[2] != "-" or s[35] != "-" or s[52] != "-":
        return None
    trace_id, parent_id, flags = s[3:35], s[36:52], s[53:55]
    if not (_TRACE.match(trace_id) and _PARENT.match(parent_id) and _FLAGS.match(flags)):
        return None
    if trace_id == "0" * 32 or parent_id == "0" * 16:
        return None
    return trace_id, parent_id, flags


def parse_tracestate(value: HeaderValue) -> Optional[str]:
    """Return the normalised tracestate or None (empty, invalid, duplicate key, >32 members).

    The caller must only use it alongside a valid traceparent (an invalid traceparent
    voids tracestate). Over 512 characters, members are dropped from the right.
    """
    if isinstance(value, (list, tuple)):
        if not all(isinstance(v, str) for v in value):
            return None
        value = ",".join(value)
    if not isinstance(value, str):
        return None
    members = [m.strip(_OWS) for m in value.split(",")]
    members = [m for m in members if m]
    if not members or len(members) > _MAX_MEMBERS:
        return None
    seen = set()
    for m in members:
        key, sep, val = m.partition("=")
        if not sep or not _KEY.match(key) or not _VALUE.match(val) or val.endswith(" "):
            return None
        if key in seen:
            return None
        seen.add(key)
    while members and len(",".join(members)) > _MAX_LEN:
        members.pop()
    return ",".join(members) or None


def format_traceparent(trace_id: str, span_id: str, flags: str = "01") -> str:
    """Format a version-00 traceparent."""
    return f"00-{trace_id}-{span_id}-{flags}"
