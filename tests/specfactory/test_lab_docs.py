# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces row L7 (LAB-REV2-L7)
"""Doc tests for the skill lab rev 2 record: README output rule (ruling 12), the retired gap-table
rows (E3 fog and cross-layer fire land in the engine), register rows Q-008-03 / Q-008-07 (ruling 5)
and the Q-LAB-03 note, the ROADMAP section 1 row, and the LAB-REV2 owner rows."""
import re
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "docs" / "northstar" / "research" / "layer_dynamics" / "README.md"
REGISTER = REPO / "docs" / "northstar" / "ambiguity_register.md"
ROADMAP = REPO / "docs" / "northstar" / "ROADMAP.md"
PIECES = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"


def _section(text: str, number: int) -> str:
    """Body of '## <number>. ...' up to the next '## ' heading."""
    m = re.search(rf"^## {number}\. .*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"README has no '## {number}.' section"
    return m.group(1)


def _register_row(qid: str) -> list[str]:
    for line in REGISTER.read_text().splitlines():
        if line.startswith(f"| {qid} |"):
            return [c.strip() for c in line.strip().strip("|").split("|")]
    raise AssertionError(f"register has no row {qid}")


# Register columns: id, epic/story, question, candidates, status, answer
STATUS, ANSWER = 4, 5


def _lab_rev2_rows():
    pieces = tomllib.loads(PIECES.read_text())["piece"]
    return [p for p in pieces if p["id"].startswith("LAB-REV2")]


# --- positive controls (green today) ---

def test_control_readme_and_section5_exist():
    assert README.exists()
    assert "Small batches" in _section(README.read_text(), 5)


def test_control_register_rows_exist_with_status_column():
    for qid in ("Q-008-03", "Q-008-07", "Q-LAB-03"):
        assert _register_row(qid)[STATUS] in ("open", "closed"), qid
    assert _register_row("Q-008-04")[STATUS] == "closed"  # control: a row known closed parses as closed


# --- ruling 12: output rule in README section 5 ---

def test_ruling12_readme_section5_has_output_rule():
    body = _section(README.read_text(), 5).lower()
    phrases = [
        "csv", "json",                     # the lab's output is data (CSV, JSON, run metadata)
        "run metadata",
        "claude analyses",
        "top-down",
        "arrows",
        "where the lines cross",
        "a number without its diagram is not evidence",
    ]
    missing = [p for p in phrases if p not in body]
    assert not missing, f"README section 5 lacks the ruling 12 output rule phrases: {missing}"


# --- gap table rows retired (spec L7 row) ---

def test_readme_gap_table_rows_deleted():
    text = README.read_text().lower()
    hits = {s: [i + 1 for i, ln in enumerate(text.splitlines()) if s in ln]
            for s in ("same-layer fire only", "targeting ignores fog")}
    hits = {s: h for s, h in hits.items() if h}
    assert not hits, f"README still carries retired gap rows (phrase: lines): {hits}"


# --- register: Q-008-03 and Q-008-07 closed to (a) by ruling 5; Q-LAB-03 note ---

def test_ruling5_q_008_03_closed_to_a():
    row = _register_row("Q-008-03")
    assert row[STATUS] == "closed", f"Q-008-03 status is {row[STATUS]!r}"
    assert row[ANSWER].startswith("(a)"), f"Q-008-03 answer {row[ANSWER][:40]!r}"
    assert "ruling 5" in row[ANSWER].lower()


def test_ruling5_q_008_07_closed_to_a():
    row = _register_row("Q-008-07")
    assert row[STATUS] == "closed", f"Q-008-07 status is {row[STATUS]!r}"
    assert row[ANSWER].startswith("(a)"), f"Q-008-07 answer {row[ANSWER][:40]!r}"
    assert "ruling 5" in row[ANSWER].lower()


def test_q_lab_03_has_rev2_note():
    row = " | ".join(_register_row("Q-LAB-03")).lower()
    assert "skill-lab-rev2-spec" in row or "lab-rev2" in row, "Q-LAB-03 has no note naming the rev 2 spec"


# --- ROADMAP section 1 row ---

def test_roadmap_section1_has_lab_rev2_row():
    text = ROADMAP.read_text()
    m = re.search(r"^## 1\. .*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, "ROADMAP has no section 1"
    rows = [ln for ln in m.group(1).splitlines()
            if ln.startswith("|") and ("LAB-REV2" in ln or "skill-lab-rev2-spec" in ln)]
    assert rows, "ROADMAP section 1 has no LAB-REV2 row"
    assert any("2026-10-14-skill-lab-rev2-spec.md" in r for r in rows), "row does not point at the spec"


# --- pieces.toml invariants ---

def test_lab_rev2_rows_all_have_status_table():
    rows = _lab_rev2_rows()
    assert len(rows) >= 14, f"expected umbrella + L1..L7 + S + E0..E4, found {len(rows)}"
    for p in rows:
        st = p.get("status")
        assert isinstance(st, dict) and st.get("state"), f"{p['id']} has no status table"


def test_l7_depends_on_every_other_lab_rev2_row():
    rows = _lab_rev2_rows()
    l7 = next(p for p in rows if p["id"] == "LAB-REV2-L7")
    others = {p["id"] for p in rows if p["id"] not in ("LAB-REV2", "LAB-REV2-L7")}
    missing = sorted(others - set(l7["depends_on"]))
    assert not missing, f"LAB-REV2-L7 depends_on lacks {missing}"
