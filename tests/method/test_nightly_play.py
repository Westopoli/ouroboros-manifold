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


# ---- H-033: nightly-play-git-path (docs/stories/H-033.md) -------------------
# Story: "The nightly play files what it found as harness rows on a branch
# every night; a finding never dies in the timer's journal."
# Gap (no rule states it, so the shape is the test writer's): the service runs
# file_findings.py from the repository root with the doc as the relative path
# `docs/method/harness.md`; the red case uses that call shape.
H033_DATE = "2026-10-30"
H033_DOC = "docs/method/harness.md"
H033_BASE = ("| Story | Words | Status | Depth |\n|---|---|---|---|\n"
             '| H-001 | "first" | Ready | `docs/stories/H-001.md` |\n'
             '| H-002 | "second" | Ready | `docs/stories/H-002.md` |\n')


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a], check=True,
                          capture_output=True, text=True).stdout


def toy_repo(tmp_path):
    """Toy repository: docs/method/harness.md with two H- rows committed on
    main, a bare origin holding main, and a log with one FINDING line."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    _git(work, "config", "user.email", "toy@example.invalid")
    _git(work, "config", "user.name", "toy")
    (work / "docs/method").mkdir(parents=True)
    (work / H033_DOC).write_text(H033_BASE)
    _git(work, "add", H033_DOC)
    _git(work, "commit", "-q", "-m", "toy base")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "-q", "origin", "main")
    log = tmp_path / "nightly" / f"{H033_DATE}.log"
    log.parent.mkdir()
    log.write_text("boot ok\nFINDING the minimap is blank\nnoise\n")
    return origin, work, log


def run_push(work, log, doc):
    return subprocess.run(["python3", str(FILE_FINDINGS), str(log), str(doc), "--push"],
                          cwd=work, capture_output=True, text=True, timeout=60)


def test_h033_control_no_push_writes_row_and_touches_no_git(tmp_path):
    """H-033 positive control (green today): without --push the same call from
    the repo root writes one row into the fixture file, exits 0, and the origin
    gets no branch (the parsing half is right; only the git half is wrong)."""
    origin, work, log = toy_repo(tmp_path)
    r = subprocess.run(["python3", str(FILE_FINDINGS), str(log), H033_DOC],
                       cwd=work, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rows = parse_rows((work / H033_DOC).read_text())
    assert [x[0] for x in rows] == ["H-001", "H-002", "H-003"]
    assert "the minimap is blank" in rows[2][1]
    assert _git(origin, "branch", "--list").split() == ["*", "main"] or \
        _git(origin, "branch", "--list").split() == ["main"]


def test_h033_control_push_with_absolute_doc_path_works(tmp_path):
    """H-033 positive control (green today): the push machinery of the toy
    fixture works when the doc is given as an absolute path, so the red test
    below fails on the relative-path shape alone, not on the fixture."""
    origin, work, log = toy_repo(tmp_path)
    r = run_push(work, log, work / H033_DOC)
    assert r.returncode == 0, r.stderr
    assert f"s/H-nightly-{H033_DATE}" in _git(origin, "branch", "--list")


def test_h033_push_from_repo_root_files_one_row_on_origin_branch(tmp_path):
    """H-033: 'running file_findings.py <log> <doc> --push against a bare origin
    creates the branch s/H-nightly-<date> on that origin with one commit whose
    diff adds exactly one row to docs/method/harness.md'. The doc is given as
    docs/method/harness.md from the repo root (the service's call shape)."""
    origin, work, log = toy_repo(tmp_path)
    r = run_push(work, log, H033_DOC)
    assert r.returncode == 0, r.stderr
    branch = f"s/H-nightly-{H033_DATE}"
    assert _git(origin, "rev-parse", "--verify", f"refs/heads/{branch}").strip()
    assert _git(origin, "rev-list", "--count", f"main..{branch}").strip() == "1"
    stat = _git(origin, "diff", "--numstat", "main", branch).splitlines()
    assert stat == [f"1\t0\t{H033_DOC}"]
    patch = _git(origin, "diff", "-U0", "main", branch)
    added = [l for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
    assert len(added) == 1 and added[0].startswith("+| H-003 |")
    assert "the minimap is blank" in added[0]
