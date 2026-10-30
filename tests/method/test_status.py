"""H-002 status from git.

Story H-002: "One command prints what is in flight, what landed this week, what
waits on me and the four numbers, from git alone."
Schema (story_loop.md): "every `Land` commit has Story, Tests, Play, Played, Gate,
Flag; every story in Tested has a `Land` commit; every `Seen` has a Verdict."
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STATUS_SH = ROOT / "scripts" / "method" / "status.sh"
CHECK_PY = ROOT / "scripts" / "specfactory" / "status_check.py"
SECTIONS = ["IN FLIGHT", "LANDED", "WAITING ON WESTLEY", "TEST DEFECTS",
            "SWEEPS", "DECISIONS", "NUMBERS", "LAST PLAYED"]
WORDS_902 = "I see the second thing land"


def git(cwd, *args, env=None):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=e)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r.stdout.strip()


def commit(cwd, msg, files=None, allow_empty=False):
    for name, body in (files or {}).items():
        p = Path(cwd) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    git(cwd, "add", "-A")
    args = ["commit", "-q", "-m", msg] + (["--allow-empty"] if allow_empty else [])
    git(cwd, *args)
    return git(cwd, "rev-parse", "HEAD")


def land(cwd, sid, trailers):
    git(cwd, "checkout", "-q", "-b", f"s/{sid}-x")
    commit(cwd, f"{sid} build", {f"src/{sid}.txt": sid})
    git(cwd, "checkout", "-q", "main")
    body = f"Land {sid} thing\n\n" + "\n".join(f"{k}: {v}" for k, v in trailers)
    git(cwd, "merge", "-q", "--no-ff", f"s/{sid}-x", "-m", body)
    return git(cwd, "rev-parse", "HEAD")


def trailers(sid, played=True):
    t = [("Story", sid), ("Tests", "tests/x.py"), ("Play", f"scripts/play.sh --story {sid}")]
    if played:
        t.append(("Played", "2026-10-30 window 11s scene reached"))
    return t + [("Gate", "412s fast"), ("Flag", "harness")]


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    t = tmp_path_factory.mktemp("fx")
    repo = t / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    stories = (
        "# Story Catalog\n\n| Story | Epic | In the commander's words | Status | Depth |\n"
        "|---|---|---|---|---|\n"
        '| S-900 | E-01 | "I see the first thing land." | Tested | `docs/stories/S-900.md` |\n'
        f'| S-902 | E-01 | "{WORDS_902}." | Tested | `docs/stories/S-902.md` |\n')
    harness = (
        "# Harness stories\n\n| Story | In Westley's words | Status | Depth |\n|---|---|---|---|\n"
        '| H-001 | "I type one command and today\'s main opens, built, in front of me." | Spec\'d | `docs/stories/H-001.md` |\n'
        '| H-002 | "One command prints what is in flight, what landed this week." | Spec\'d | `docs/stories/H-002.md` |\n')
    commit(repo, "method lands", {
        "docs/bible/stories.md": stories, "docs/method/harness.md": harness,
        "docs/stories/S-900.md": "# S-900\n\n## Machine lines\n\nFlag: harness\nTests: tests/x.py\n"})
    c1 = land(repo, "S-900", trailers("S-900"))
    c2 = land(repo, "S-902", trailers("S-902", played=False))
    commit(repo, "Seen S-900\n\nVerdict: approve looks right to me", allow_empty=True)
    commit(repo, "fix a test\n\nTest-defect: asserts wrong count (ruler-1)", {"tests/x.py": "# fixed\n"})
    commit(repo, "Sweep 2026-10-30 pass", allow_empty=True)
    origin = t / "origin"
    subprocess.run(["git", "clone", "-q", "--bare", str(repo), str(origin)], check=True)
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "origin", "main")
    git(repo, "checkout", "-q", "-b", "s/S-901-x")
    commit(repo, "S-901 spec: unmerged", {"docs/stories/S-901.md": "# S-901\n"})
    git(repo, "push", "-q", "origin", "s/S-901-x")
    git(repo, "checkout", "-q", "main")
    git(repo, "fetch", "-q", "origin")
    home = t / "home"
    play = home / "Projects" / "om-push"
    play.mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(play / "main")], check=True)
    sha = git(play / "main", "rev-parse", "HEAD")
    return dict(repo=repo, c1=c1, c2=c2, home=home, playsha=sha)


def run_status(cwd, home=None):
    env = dict(os.environ)
    if home:
        env["HOME"] = str(home)
    return subprocess.run(["bash", str(STATUS_SH)], cwd=cwd, capture_output=True, text=True, env=env)


def sections(out):
    """Map section name -> text, splitting at lines that start with a section name."""
    cur, res = None, {}
    for line in out.splitlines():
        hit = next((s for s in SECTIONS if line.startswith(s)), None)
        if hit:
            cur = hit
            res[cur] = ""
        elif cur:
            res[cur] += line + "\n"
    return res


def test_control_trailer_machinery(fx):
    """Positive control: S-900 landing's Story trailer reads back through git."""
    out = git(fx["repo"], "log", "--format=%(trailers:key=Story,valueonly)", "-1", fx["c1"])
    assert out == "S-900"


def test_status_sh_sections_in_order(fx):
    """H-002: output order is IN FLIGHT, LANDED, WAITING ON WESTLEY, TEST DEFECTS,
    SWEEPS, DECISIONS, NUMBERS, LAST PLAYED."""
    r = run_status(fx["repo"], fx["home"])
    assert r.returncode == 0, r.stderr
    pos = [r.stdout.find(s) for s in SECTIONS]
    assert all(p >= 0 for p in pos), pos
    assert pos == sorted(pos)


def test_in_flight_lists_unmerged_branch(fx):
    """H-002: IN FLIGHT is every origin/s/* branch not yet merged into origin/main."""
    s = sections(run_status(fx["repo"], fx["home"]).stdout)
    assert "s/S-901-x" in s.get("IN FLIGHT", "")
    assert "S-901 spec: unmerged" in s["IN FLIGHT"]
    assert "s/S-900-x" not in s["IN FLIGHT"]


def test_landed_lists_trailers(fx):
    """H-002: LANDED lists first-parent Land commits with Story, Played and Gate trailers."""
    s = sections(run_status(fx["repo"], fx["home"]).stdout)["LANDED"]
    assert "Land S-900 thing" in s and "Land S-902 thing" in s
    assert "2026-10-30 window 11s scene reached" in s and "412s fast" in s


def test_waiting_on_westley(fx):
    """H-002: WAITING lists each Land with no later `Seen <id>`, with the Play run
    line and the story's words from stories.md."""
    s = sections(run_status(fx["repo"], fx["home"]).stdout)["WAITING ON WESTLEY"]
    assert "S-902" in s and "S-900" not in s
    assert "scripts/play.sh --story S-902" in s
    assert WORDS_902 in s


def test_test_defects(fx):
    """H-002: TEST DEFECTS lists commits with a Test-defect trailer, file and why."""
    s = sections(run_status(fx["repo"], fx["home"]).stdout)["TEST DEFECTS"]
    assert "tests/x.py" in s and "asserts wrong count" in s


def test_sweeps_numbers_last_played(fx):
    """H-002: SWEEPS shows the Sweep subject; NUMBERS says `no report yet` without a
    metrics csv; LAST PLAYED is the sha of ~/Projects/om-push/main."""
    s = sections(run_status(fx["repo"], fx["home"]).stdout)
    assert "Sweep 2026-10-30 pass" in s["SWEEPS"]
    assert "no report yet" in s["NUMBERS"]
    assert fx["playsha"] in s["LAST PLAYED"]


def test_status_check_one_drift(fx):
    """Schema: a Land commit missing any of Story, Tests, Play, Played, Gate, Flag is
    one DRIFT line naming it; the complete landing prints nothing."""
    r = subprocess.run([sys.executable, str(CHECK_PY), "--repo", str(fx["repo"])],
                       capture_output=True, text=True, cwd=fx["repo"])
    drift = [l for l in r.stdout.splitlines() if "DRIFT" in l]
    assert len(drift) == 1, (r.stdout[:600], r.stderr[-600:])
    assert "S-902" in drift[0] and "Played" in drift[0]
    assert "S-900" not in drift[0]
    assert r.returncode != 0


def test_real_repo_status():
    """H-002: on the real origin/main the script exits 0 and IN FLIGHT lists an
    origin/s/* branch that exists today (s/H-001-play)."""
    assert STATUS_SH.exists(), "scripts/method/status.sh missing"
    r = subprocess.run(["bash", str(STATUS_SH)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "s/H-001-play" in sections(r.stdout).get("IN FLIGHT", "")
