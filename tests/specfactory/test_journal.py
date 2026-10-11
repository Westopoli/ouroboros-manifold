"""HARNESS-journal: tests for scripts/journal.sh (method rev 2 item 6: journals
are printed from git, never hand-written).

Spec: scripts/journal.sh [<since ref>] [<until ref>] prints one line per
first-parent commit, oldest first, "- MM-DD HH:MM <sha7> <subject>", from
git log --first-parent --reverse --date=format:'%m-%d %H:%M'
--format='- %ad %h %s' <since>..<until> run in the script's own parent
directory. Defaults: since origin/main~40, until origin/main. "--help" / "-h"
prints a usage line and exits 0. A bad ref exits with git's status and message.

See also: docs/northstar/plans/workflows_2026-10-07/journal_2026-10-09.md (the
last hand-built journal).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "journal.sh"
LINE_RE = re.compile(r"^- \d{2}-\d{2} \d{2}:\d{2} [0-9a-f]{7,} .+$")


def _run_script(*args: str) -> subprocess.CompletedProcess:
    assert SCRIPT.is_file(), f"scripts/journal.sh is missing: {SCRIPT}"
    return subprocess.run(["bash", str(SCRIPT), *args], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=60)


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True,
                          text=True, check=True, timeout=60).stdout


# ------------------------------------------------------- positive controls --

def test_control_line_regex_matches_a_hand_written_line():
    assert LINE_RE.match("- 10-10 14:05 9876483 Method rev 2: the nine retro changes grafted")
    assert not LINE_RE.match("10-10 14:05 9876483 no leading dash")
    assert not LINE_RE.match("- 10-10 14:05 xyz1234 not a sha")


def test_control_repo_has_three_first_parent_commits_to_print():
    shas = _git("log", "--first-parent", "--reverse", "--format=%h", "HEAD~3..HEAD").split()
    assert len(shas) == 3


# ------------------------------------------------------------------- script --

def test_journal_prints_three_lines_oldest_first():
    r = _run_script("HEAD~3", "HEAD")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert len(lines) == 3, r.stdout
    for line in lines:
        assert LINE_RE.match(line), line
    want = _git("log", "--first-parent", "--reverse", "--format=%h", "HEAD~3..HEAD").split()
    got = [ln.split(" ")[3] for ln in lines]
    for g, w in zip(got, want):
        assert g.startswith(w) or w.startswith(g), (got, want)


def test_journal_help_exits_zero_with_usage():
    for flag in ("--help", "-h"):
        r = _run_script(flag)
        assert r.returncode == 0, (flag, r.stderr)
        assert "journal.sh" in r.stdout, (flag, r.stdout)


def test_journal_bad_ref_exits_nonzero():
    r = _run_script("no-such-ref-journal-test", "HEAD")
    assert r.returncode != 0
    assert r.stderr.strip(), "git's message should reach stderr"


def test_journal_header_comment_names_rev2_and_last_hand_built_journal():
    assert SCRIPT.is_file(), f"scripts/journal.sh is missing: {SCRIPT}"
    text = SCRIPT.read_text()
    assert text.startswith("#!"), "bash script needs a shebang"
    assert "method rev 2" in text.lower()
    assert "See also: docs/northstar/plans/workflows_2026-10-07/journal_2026-10-09.md" in text
