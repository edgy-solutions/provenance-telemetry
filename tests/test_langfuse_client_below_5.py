"""The langfuse client is capped below 5.

Client 4.x works against Langfuse servers from 3.63.0; client 5.x needs a server on
v4.59.0 or later, and v3 servers still receive patches until January 2027. So this package
declares ``langfuse<5``. Lift the cap only when the servers it is used against are v4.59+.

Set ``PT_FORWARD_LANGFUSE=1`` (the forward-looking CI job does) to skip the installed-version
check while a 5.x client is deliberately installed.
"""
import os
import re
from importlib import metadata
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

try:
    from packaging.specifiers import SpecifierSet
except ModuleNotFoundError:
    SpecifierSet = None

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
PROBES = ("5.0.0", "5.2.0", "5.99.0")


def _excludes_every_5x(spec: str) -> bool:
    """True when the specifier string admits none of the 5.x probe versions."""
    if SpecifierSet is not None:
        s = SpecifierSet(spec)
        return not any(s.contains(v) for v in PROBES)
    m = re.search(r"<\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\s*(?:,|$)", spec)
    return bool(m) and int(m.group(1)) <= 5


def _declared_langfuse_spec() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    if tomllib is not None:
        deps = tomllib.loads(text)["project"]["dependencies"]
    else:
        deps = re.findall(r'^\s*"([^"]+)",?\s*(?:#.*)?$', text, re.M)
    for dep in deps:
        m = re.match(r"\s*langfuse\s*([^;\s].*?)\s*(?:;.*)?$", dep)
        if m:
            return m.group(1)
    raise AssertionError("no langfuse requirement found in pyproject.toml")


def test_declared_requirement_excludes_every_5x():
    spec = _declared_langfuse_spec()
    assert _excludes_every_5x(spec), f"pyproject allows langfuse 5.x: {spec!r}"
    if SpecifierSet is not None:
        assert SpecifierSet(spec).contains("4.7.0"), f"floor 4.7.0 excluded: {spec!r}"


@pytest.mark.skipif(
    os.environ.get("PT_FORWARD_LANGFUSE") == "1",
    reason="forward-looking leg installs langfuse 5.x on purpose",
)
def test_installed_langfuse_is_below_5():
    major = int(metadata.version("langfuse").split(".")[0])
    assert major < 5, f"langfuse {metadata.version('langfuse')} installed; the cap is <5"


def test_detector_control():
    assert not _excludes_every_5x(">=4.7.0,<6")
    assert _excludes_every_5x(">=4.7.0,<5")
