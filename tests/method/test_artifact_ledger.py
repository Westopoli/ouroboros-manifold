# Rule pins: R-990-01@?
"""Lint for the artifact ledger (Westley, 2026-11-24): docs/northstar/story_reviews/westley/artifacts.md."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "docs" / "northstar" / "story_reviews" / "westley" / "artifacts.md"
COLUMNS = ["id", "url and version", "date", "title", "shows", "why (his words quoted)",
           "code (sha or branch, record and render commands, hashes)", "his response (verbatim, dated, or 'none yet')",
           "done (commit, DEC id, report)", "status (current, superseded by A-00N, retired)"]


def _rows():
    lines = [l for l in LEDGER.read_text().splitlines() if l.startswith("|")]
    cells = [[c.strip() for c in l.strip().strip("|").split(" | ")] for l in lines]
    return cells[0], cells[2:]


def test_ledger_exists_and_has_the_ten_columns():
    assert LEDGER.is_file()
    header, rows = _rows()
    assert header == COLUMNS and rows


def test_every_row_is_complete():
    _, rows = _rows()
    for r in rows:
        assert len(r) == 10, r[0]
        assert all(c for c in r), r[0]


def test_ids_unique_sequential_and_urls_valid():
    _, rows = _rows()
    assert [r[0] for r in rows] == ["A-%03d" % (i + 1) for i in range(len(rows))]
    for r in rows:
        assert re.match(r"https://claude\.ai/artifact/\S+ v\d+$", r[1]), r[0]


def test_claude_md_points_at_the_ledger():
    assert "artifacts.md" in (REPO / "CLAUDE.md").read_text()
