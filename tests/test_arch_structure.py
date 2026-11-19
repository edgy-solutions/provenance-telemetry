"""The architecture records' structured fields: what diagrams are drawn from.

A component record carries a Connections table, the flow record a numbered steps table,
and every decision record a Governs table. Every element those tables name is an id that
is defined: a record's own id, or a row of the README's element-ids table.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "docs" / "arch"
COMPONENTS = sorted((ARCH / "components").glob("*.md"))
FLOWS = sorted((ARCH / "flows").glob("*.md"))
DECISIONS = sorted((ARCH / "decisions").glob("ADR-*.md"))

CONNECTIONS_HEADER = "| Other | Direction | Protocol | Authentication | What passes | Evidence |"
STEPS_HEADER = "| # | Actor | Action | Target | What passes | Check or decision | Status | Evidence |"
DIRECTIONS = {"calls", "is called by", "reads", "writes"}
STATUSES = {"`measured`", "`built`", "`accepted`", "`proposed`", "`not built`", "not established"}
LINKED_ID = re.compile(r"^\[([A-Z][A-Z0-9-]+)\]\([^)]+\)$")


def record_id(path: Path) -> str:
    m = re.search(r"\(((?:CO|FL)-[A-Z-]+)\)\s*$", path.read_text(encoding="utf-8").splitlines()[0])
    assert m, f"{path.name}: the title line carries no record id"
    return m.group(1)


def element_ids() -> set:
    text = (ARCH / "README.md").read_text(encoding="utf-8")
    section = text.split("## Element ids", 1)[1]
    ids = [r[0] for r in rows(section, "| Id | Kind | What it is |")]
    assert len(ids) == len(set(ids)), "an element id is defined twice"
    return set(ids)


def known_ids() -> set:
    return element_ids() | {record_id(p) for p in COMPONENTS + FLOWS}


def rows(text: str, header: str) -> list:
    """The cells of each row of the one table under `header`."""
    lines = text.splitlines()
    assert lines.count(header) == 1, f"expected one table headed {header!r}"
    i = lines.index(header) + 2  # skip the header and its rule
    out = []
    while i < len(lines) and lines[i].startswith("|"):
        out.append([c.strip() for c in lines[i].strip().strip("|").split(" | ")])
        i += 1
    return out


def ids_in(cell: str) -> list:
    """A cell names one id, or several separated by '; '; a linked id counts as its id."""
    out = []
    for part in cell.split("; "):
        m = LINKED_ID.match(part)
        out.append(m.group(1) if m else part)
    return out


def connection_errors(text: str, known: set) -> list:
    errs = []
    table = rows(text, CONNECTIONS_HEADER)
    if not table:
        errs.append("no connection rows")
    for r in table:
        if len(r) != 6 or any(not c for c in r):
            errs.append(f"row has an empty or missing cell: {r}")
            continue
        if r[0] not in known:
            errs.append(f"unknown id {r[0]!r}")
        if r[1] not in DIRECTIONS:
            errs.append(f"direction {r[1]!r} is not one of {sorted(DIRECTIONS)}")
    return errs


def step_errors(text: str, known: set) -> list:
    errs = []
    table = rows(text, STEPS_HEADER)
    if not table:
        errs.append("no steps")
    for n, r in enumerate(table, 1):
        if len(r) != 8 or any(not c for c in r):
            errs.append(f"step {n}: an empty or missing cell")
            continue
        if r[0] != str(n):
            errs.append(f"step {n} is numbered {r[0]!r}")
        for col, cell in (("actor", r[1]), ("target", r[3])):
            for i in ids_in(cell):
                if i not in known and not (col == "target" and i == "—"):
                    errs.append(f"step {n}: {col} {i!r} is not an id")
        if r[6] not in STATUSES:
            errs.append(f"step {n}: status {r[6]!r}")
    return errs


def governs_errors(text: str, known_records: set) -> list:
    errs = []
    if "## Governs" not in text:
        return ["no Governs section"]
    table = {r[0]: r[1] for r in rows(text, "| Kind | Ids |")}
    if set(table) != {"component", "flow"}:
        return [f"Governs rows are {sorted(table)}"]
    named = []
    for kind, prefix in (("component", "CO-"), ("flow", "FL-")):
        if table[kind] == "none":
            continue
        for i in ids_in(table[kind].replace(", ", "; ")):
            if not i.startswith(prefix) or i not in known_records:
                errs.append(f"{kind} {i!r} is not a {prefix} record")
            named.append(i)
    if not named and "No component or flow of these records" not in text:
        errs.append("governs nothing and does not say what it governs")
    return errs


@pytest.mark.parametrize("path", COMPONENTS, ids=lambda p: p.name)
def test_every_component_record_carries_its_connections(path):
    assert connection_errors(path.read_text(encoding="utf-8"), known_ids()) == []


@pytest.mark.parametrize("path", FLOWS, ids=lambda p: p.name)
def test_every_flow_record_carries_numbered_steps(path):
    assert step_errors(path.read_text(encoding="utf-8"), known_ids()) == []


@pytest.mark.parametrize("path", DECISIONS, ids=lambda p: p.name)
def test_every_decision_names_what_it_governs(path):
    records = {record_id(p) for p in COMPONENTS + FLOWS}
    assert governs_errors(path.read_text(encoding="utf-8"), records) == []


def test_the_records_exist():
    assert len(COMPONENTS) == 5 and len(FLOWS) == 1 and len(DECISIONS) == 35


def test_the_checks_can_fire():
    """Controls: each check refuses what it exists to refuse."""
    known = {"CO-A", "XE-B"}
    good = CONNECTIONS_HEADER + "\n|---|\n| XE-B | calls | p | a | w | e |\n"
    assert connection_errors(good, known) == []
    assert connection_errors(good.replace("| XE-B |", "| XE-Z |"), known)
    assert connection_errors(good.replace("| calls |", "| talks to |"), known)
    assert connection_errors(good.replace("| a |", "|  |"), known)

    step = STEPS_HEADER + "\n|---|\n| 1 | XE-B | acts | [CO-A](x.md) | w | c | `built` | e |\n"
    assert step_errors(step, known) == []
    assert step_errors(step.replace("| 1 |", "| 2 |"), known)
    assert step_errors(step.replace("| XE-B |", "| the caller |"), known)
    assert step_errors(step.replace("`built`", "`done`"), known)

    gov = "## Governs\n\n| Kind | Ids |\n|---|---|\n| component | [CO-A](x.md) |\n| flow | none |\n"
    assert governs_errors(gov, {"CO-A"}) == []
    assert governs_errors(gov.replace("[CO-A](x.md)", "[CO-Q](x.md)"), {"CO-A"})
    assert governs_errors(gov.replace("[CO-A](x.md)", "none"), {"CO-A"})
    assert governs_errors("## Decision\n", {"CO-A"})
