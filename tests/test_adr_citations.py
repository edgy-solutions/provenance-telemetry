"""Seal: an ADR number this repository does not hold names its repo.

Most decisions behind this library were first recorded in another repository's
ADRs, and an ADR number in one repo can mean a different record in another.
This repository now holds its own records, in ``docs/arch/decisions/``. A bare
``ADR-NNNN`` passes only when that folder holds that number. Any other ADR
number in a tracked text file must be qualified by its repository:
``<owner>/<repo> ADR-NNNN``, or sit inside a GitHub URL of that repository.

Known limit: once this repository holds a number, a bare cite of the same
number meant for another repository passes too. Qualify every foreign cite.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECISIONS = ROOT / "docs" / "arch" / "decisions"
SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".cfg"}
SKIP_PARTS = {"build", "dist", "__pycache__", "sessions"}

ADR = re.compile(r"ADR-\d{4}")
QUALIFIED_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/\S*")
QUALIFIER = re.compile(r"[\w.-]+/[\w.-]+ $")


def held_numbers():
    """The ADR numbers this repository holds: one per ``ADR-NNNN-*.md`` record."""
    return frozenset(ADR.match(p.name).group(0) for p in DECISIONS.glob("ADR-*.md"))


def bare_citations(text, held=frozenset()):
    """Return each bare, unheld ``ADR-NNNN`` in ``text``, with 40 characters of context."""
    text = QUALIFIED_URL.sub(lambda m: "u" * len(m.group(0)), text)
    found = []
    for m in ADR.finditer(text):
        if m.group(0) in held:
            continue
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
    held = held_numbers()
    offenders = {}
    for path, rel in _files():
        if rel.as_posix() == "tests/test_adr_citations.py":
            continue
        hits = bare_citations(path.read_text(encoding="utf-8"), held)
        if hits:
            offenders[rel.as_posix()] = hits
    assert not offenders, f"cite an ADR this repo does not hold with its repo, e.g. 'owner/repo ADR-0038': {offenders}"


def test_the_detector_sees_a_bare_number_and_passes_a_qualified_one():
    assert bare_citations("by design (ADR-0038): shape only")
    assert bare_citations("see docs/adr/ADR-0038-x.md")
    assert not bare_citations("by design (edgy-solutions/invincible-agent ADR-0038): x")
    assert not bare_citations(
        "https://github.com/edgy-solutions/invincible-agent/blob/master/docs/adr/ADR-0038-x.md"
    )


def test_a_held_number_may_be_bare_and_an_unheld_one_may_not():
    held = held_numbers()
    first = min(held)
    assert not bare_citations(f"see [{first}]({first}-x.md)", held)
    # Control: the same detector, given the held set, still flags a number not held.
    assert "ADR-0038" not in held
    assert bare_citations("by design (ADR-0038): shape only", held)
    assert bare_citations(f"see [{first}]({first}-x.md)")


def test_the_held_set_is_read_from_the_records():
    held = held_numbers()
    assert held, f"no ADR-*.md records found under {DECISIONS}"
    assert all(ADR.fullmatch(n) for n in held)
