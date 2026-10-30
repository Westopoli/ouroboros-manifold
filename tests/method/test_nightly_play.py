"""H-004: the 30B plays main nightly (docs/stories/H-004.md).

Story: "Every night the 30B plays today's main through the same command I use
and what it finds shows up as harness stories, never as edits."
Gaps (no rule states them, so the shapes below are the test writer's):
  - FINDING line shape: `FINDING <words>`.
  - file_findings.py CLI: `file_findings.py <log> <harness.md>`, no git work
    when the harness file is outside a repo.
"""
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "docs/method/harness.md"
FILE_FINDINGS = REPO / "scripts/method/file_findings.py"
NIGHTLY = REPO / "scripts/method/nightly_play.sh"
UNITS = REPO / "scripts/specfactory/systemd"
ROW = re.compile(r"^\| (H-\d+) \| (.*) \| ([^|]+) \| (.*) \|$")


def parse_rows(text):
    return [m.groups() for m in map(ROW.match, text.splitlines()) if m]


def fixture(tmp_path, log_text):
    """Copy the real table header and its first two rows into tmp_path."""
    lines = HARNESS.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("| Story |"))
    doc = tmp_path / "harness.md"
    doc.write_text("\n".join(lines[: start + 4]) + "\n")
    log = tmp_path / "nightly" / "2026-10-30.log"
    log.parent.mkdir()
    log.write_text(log_text)
    return doc, log


def run_findings(doc, log, cwd):
    return subprocess.run(
        ["python3", str(FILE_FINDINGS), str(log), str(doc)],
        cwd=cwd, capture_output=True, text=True, timeout=60)


def test_control_parser_sees_every_h_row_in_real_file():
    """Positive control for H-004: the row parser used on the fixture counts
    every `| H-` line of the real harness.md (green today)."""
    text = HARNESS.read_text()
    assert len(parse_rows(text)) == len(
        [l for l in text.splitlines() if l.startswith("| H-")]) >= 6


def test_two_findings_append_two_rows(tmp_path):
    """H-004: 'appends one `H-` row per new finding to `docs/method/harness.md`
    (status `Spec'd`, words quoted from the log, depth `nightly/<date>.log`)'."""
    doc, log = fixture(tmp_path, "boot ok\nFINDING the minimap is blank\n"
                       "noise\nFINDING build menu never opens\n")
    before = parse_rows(doc.read_text())
    assert len(before) == 2
    r = run_findings(doc, log, tmp_path)
    assert r.returncode == 0, r.stderr
    after = parse_rows(doc.read_text())
    assert [a[0] for a in after[:2]] == [b[0] for b in before]
    new = after[2:]
    assert [n[0] for n in new] == ["H-003", "H-004"]
    assert all(n[2] == "Spec'd" for n in new)
    assert all(n[3].strip("`") == "nightly/2026-10-30.log" for n in new)
    assert "the minimap is blank" in new[0][1]
    assert "build menu never opens" in new[1][1]


def test_no_finding_no_diff(tmp_path):
    """H-004: a log with no FINDING line yields no diff."""
    doc, log = fixture(tmp_path, "boot ok\nall quiet\n")
    before = doc.read_text()
    r = run_findings(doc, log, tmp_path)
    assert r.returncode == 0, r.stderr
    assert doc.read_text() == before


def test_timer_units_verify(tmp_path):
    """H-004: 'om-nightly-play.service and .timer (23:00, before the sweep at
    23:30)' parse under systemd-analyze verify."""
    for n in ("service", "timer"):
        assert (UNITS / f"om-nightly-play.{n}").is_file()
    t = (UNITS / "om-nightly-play.timer").read_text()
    assert "23:00" in t
    r = subprocess.run(
        ["systemd-analyze", "verify",
         str(UNITS / "om-nightly-play.service"),
         str(UNITS / "om-nightly-play.timer")],
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr


def test_dry_run_prints_play_line(tmp_path):
    """H-004: '--dry-run prints the play line and the QA line without running
    them' (the QA runner for the 30B is not identifiable under scripts/qa/, so
    only the play line is asserted)."""
    assert NIGHTLY.is_file()
    r = subprocess.run(["bash", str(NIGHTLY), "--dry-run"], cwd=tmp_path,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert any("play.sh --check" in l for l in r.stdout.splitlines())
