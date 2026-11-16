"""Seal: an ADR number without its repo is not a citation.

The decisions behind this library are recorded in another repository's ADRs. A
bare ``ADR-NNNN`` here names nothing a reader can follow, and an ADR number in
one repo can mean a different record in another. Every ADR number in a tracked
text file must be qualified by its repository: ``<owner>/<repo> ADR-NNNN``, or
sit inside a GitHub URL of that repository.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".cfg"}
SKIP_PARTS = {"build", "dist", "__pycache__", "sessions"}

ADR = re.compile(r"ADR-\d{4}")
QUALIFIED_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/\S*")
QUALIFIER = re.compile(r"[\w.-]+/[\w.-]+ $")


def bare_citations(text):
    """Return each bare ``ADR-NNNN`` in ``text``, with 40 characters of context."""
    text = QUALIFIED_URL.sub(lambda m: "u" * len(m.group(0)), text)
    found = []
    for m in ADR.finditer(text):
        if not QUALIFIER.search(text[max(0, m.start() - 80):m.start()]):
            found.append(text[max(0, m.start() - 40):m.end()])
    return found


def _files():
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(p.startswith(".") and p != ".github" or p in SKIP_PARTS for p in rel.parts):
            continue
        if path.is_file() and path.suffix in SUFFIXES and path.name != "uv.lock":
            yield path, rel


def test_every_adr_number_names_its_repo():
    offenders = {}
    for path, rel in _files():
        if rel.as_posix() == "tests/test_adr_citations.py":
            continue
        hits = bare_citations(path.read_text(encoding="utf-8"))
        if hits:
            offenders[rel.as_posix()] = hits
    assert not offenders, f"cite an ADR with its repo, e.g. 'owner/repo ADR-0001': {offenders}"


def test_the_detector_sees_a_bare_number_and_passes_a_qualified_one():
    assert bare_citations("by design (ADR-0038): shape only")
    assert bare_citations("see docs/adr/ADR-0038-x.md")
    assert not bare_citations("by design (edgy-solutions/invincible-agent ADR-0038): x")
    assert not bare_citations(
        "https://github.com/edgy-solutions/invincible-agent/blob/master/docs/adr/ADR-0038-x.md"
    )
