# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md section 5 (G4); preflight 7-story-plays.md section 6
"""G4: the story review queue format, the `Seen` status, the stories.md header."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "docs" / "northstar" / "story_reviews" / "README.md"
AGILE = REPO / "docs" / "northstar" / "agile.md"
STORIES = REPO / "docs" / "bible" / "stories.md"

COLUMNS = ["story", "lane", "run id", "screenshot path", "qa_state file",
           "reviewer", "reviewer verdict", "Westley verdict", "date"]


def _read(path: Path) -> str:
    assert path.exists(), f"missing {path.relative_to(REPO)}"
    return path.read_text()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _header_cells(text: str):
    """Return the cell list of the first markdown table header row that has `story` first."""
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip().strip("`").lower() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] == "story":
                return cells
    return None


def _columns_match(cells) -> bool:
    if cells is None or len(cells) != len(COLUMNS):
        return False
    return all(cells[i].startswith(COLUMNS[i].lower()) for i in range(len(COLUMNS)))


def test_control_column_checker_detects_defects():
    good = "| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date |"
    assert _columns_match(_header_cells(good))
    swapped = good.replace("| lane | run id |", "| run id | lane |")
    assert not _columns_match(_header_cells(swapped))
    assert not _columns_match(_header_cells(good.replace("| date |", "|")))
    assert not _columns_match(_header_cells("no table here"))


def test_readme_exists():
    assert _read(README).strip()


def test_readme_table_columns_in_order():
    cells = _header_cells(_read(README))
    assert _columns_match(cells), f"queue table header wrong or absent: {cells}"


def test_readme_file_per_lane():
    t = _flat(_read(README))
    assert "docs/northstar/story_reviews/<lane>.md" in t
    assert "one markdown table per lane" in t or "one table per lane" in t


def test_readme_screenshots_and_run_id():
    t = _flat(_read(README))
    assert "shots/<run id>/<story>.png" in t
    assert "timestamp" in t and "commit hash" in t
    assert "qa_state" in t and "beside the png" in t
    assert "never overwrites" in t or "never overwrite" in t


def test_readme_verdict_vocabularies():
    t = _flat(_read(README))
    for word in ("yes", "no", "unclear", "pending", "approved", "rejected"):
        assert re.search(rf"\b{word}\b", t), word


def test_readme_seen_rules():
    t = _flat(_read(README))
    assert "seen" in t
    assert "clerk" in t
    assert "status cell" in t
    assert "stories.md" in t
    assert "approved" in t
    assert "one commit" in t
    assert "reviewer agents never edit" in t or "reviewer agents never edit `stories.md`" in t
    assert "30b" in t
    assert "built" in t and "revised" in t  # rejected row sets the story back


def test_readme_compound_status_catch():
    t = _flat(_read(README))
    assert "blocked on" in t or "compound" in t
    assert "flag" in t


def test_agile_vocabulary_has_seen():
    t = _flat(_read(AGILE))
    assert "seen (built, and the player has been shown it and westley approved)" in t or \
        "seen (built, and the player has been shown it and westley approved" in t


def test_agile_vocabulary_keeps_old_statuses():
    text = _read(AGILE)
    line = next(l for l in text.splitlines() if l.startswith("Story status in"))
    for s in ("Spec'd", "Ready", "Tested", "Queued", "Building", "Built", "Revised", "Killed", "Seen"):
        assert s in line, s


def test_stories_header_lists_seen():
    text = _read(STORIES)
    line = next(l for l in text.splitlines() if l.startswith("One row per user-facing"))
    assert "Seen" in line
    for s in ("Spec'd", "Ready", "Built", "Revised", "Killed"):
        assert s in line, s
