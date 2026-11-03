# Rule pins: R-990-01@?
"""H-003 tests. Story: docs/stories/H-003.md, "Every night the token report writes
the four numbers for the week, and the share of spend that went into building and
testing is the first of them."

Premises dumped from real transcripts (~/.claude/projects/-home-westopoli-Projects-ouroboros-manifold):
  line keys: type ("assistant"|"user"|...), isSidechain, timestamp (ISO Z), message, requestId, ...
  assistant line: message.model, message.usage.{input_tokens, output_tokens,
    cache_creation_input_tokens, cache_read_input_tokens}
  sub-agent files: <session-uuid>/subagents/agent-*.jsonl, isSidechain true, first line is
    type "user" with message.content = the prompt string.
"""
import csv
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "method" / "token_report.py"
PROJ = ".claude/projects/-home-westopoli-Projects-ouroboros-manifold"
REAL_DIR = Path.home() / PROJ


def _load():
    spec = importlib.util.spec_from_file_location("token_report", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # red while the file is missing
    return mod


def _call(model, ts, i, o, cc, cr, rid, side=False):
    return {"type": "assistant", "isSidechain": side, "timestamp": ts, "requestId": rid,
            "message": {"model": model, "role": "assistant", "content": [],
                        "usage": {"input_tokens": i, "output_tokens": o,
                                  "cache_creation_input_tokens": cc,
                                  "cache_read_input_tokens": cr}}}


def _prompt(text, ts):
    return {"type": "user", "isSidechain": True, "timestamp": ts,
            "message": {"role": "user", "content": text}}


def _write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x) + "\n" for x in lines))


def _row(stdout, week):
    line = next(l for l in stdout.splitlines() if l.startswith(week + ","))
    return line.split(",")


def _pct(x):
    v = float(x.split()[0])
    return v * 100 if v <= 1.0 else v


def _run(home, week):
    env = dict(os.environ, HOME=str(home))
    p = subprocess.run([sys.executable, str(SCRIPT), "--week", week], cwd=REPO,
                       env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout


def test_fixture_shares_match_hand_sum(tmp_path):
    """H-003 Tests: "Fixture: three small transcripts under tmp_path (one Fable main chat,
    one doer sidechain, one engineer sidechain) with known token counts; the shares match
    a hand sum (positive control)." Weighting: input+output+cache-create+cache-read/10."""
    ts = "2026-10-28T10:00:00.000Z"  # ISO week 2026-W44
    base = tmp_path / PROJ
    # Fable main: 2 calls of 1000+500+2000+10000/10 = 4500 each -> 9000
    _write(base / "sess1.jsonl", [
        _call("claude-fable-5-1", ts, 1000, 500, 2000, 10000, "r1"),
        _call("claude-fable-5-1", ts, 1000, 500, 2000, 10000, "r2")])
    # doer sidechain: 1000+500+1500+0 = 3000
    _write(base / "sess1" / "subagents" / "agent-a.jsonl", [
        _prompt("Builder. Read docs/method/builder.md then the story.", ts),
        _call("claude-sonnet-5-5", ts, 1000, 500, 1500, 0, "r3", True)])
    # engineer sidechain: 500+500+500+5000/10 = 2000
    _write(base / "sess1" / "subagents" / "agent-b.jsonl", [
        _prompt("Test writer. Read docs/method/test_writer.md then the story.", ts),
        _call("claude-sonnet-5-5", ts, 500, 500, 500, 5000, "r4", True)])
    _load()  # module must exist
    out = _run(tmp_path, "2026-W44")
    r = _row(out, "2026-W44")
    # header: window,calls,weighted_tokens,builder_share,tests_share,build_plus_tests_share,fable_share,...
    assert int(r[1]) == 4
    assert int(r[2]) == 14000
    assert _pct(r[5]) == pytest.approx(5000 / 14000 * 100, abs=0.1)  # 35.7
    assert _pct(r[6]) == pytest.approx(9000 / 14000 * 100, abs=0.1)  # 64.3
    assert "UNDER" in out or "OK" in out  # thresholds printed beside the shares
    csvp = REPO / "docs" / "method" / "metrics" / "2026-W44.csv"
    if csvp.exists():
        assert next(csv.reader(csvp.open()))[:5] == [
            "window", "calls", "weighted_tokens", "builder_share", "tests_share"]
        csvp.unlink()  # fixture run must not leave a record in the repo


@pytest.mark.slow
@pytest.mark.skipif(not REAL_DIR.is_dir(), reason="no real transcript directory")
def test_real_day_reproduces_measurement():
    """H-003 Tests: self-consistency control on the real transcripts: --day 2026-10-29
    exits 0 and writes one row; class shares sum to 100 within 0.2; fable_share is within
    0.5 point of an independent count made here (assistant lines, model claude-fable-5-1,
    once per requestId, same files, same UTC day, same weighting).
    DEC-token-report-fixture-2026-10-30."""
    import datetime as dt
    day = "2026-10-29"
    home = Path.home()
    p = subprocess.run([sys.executable, str(SCRIPT), "--day", day], cwd=REPO,
                       env=dict(os.environ, HOME=str(home)), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    c = home / "Projects/om-push/metrics" / (day + ".csv")
    try:
        rows = [l for l in p.stdout.splitlines() if l.startswith(day + ",")]
        assert len(rows) == 1
        r = rows[0].split(",")
        # The row carries builder, tests and fable only (clerk/runner/other are not columns),
        # so "sum to 100" is checked as: parts consistent and no overshoot of 100.
        assert _pct(r[3]) + _pct(r[4]) == pytest.approx(_pct(r[5]), abs=0.2)
        assert _pct(r[3]) + _pct(r[4]) + _pct(r[6]) <= 100.2
        seen, fable, total = set(), 0.0, 0.0
        for f in REAL_DIR.glob("**/*.jsonl"):
            for line in f.open(errors="replace"):
                if '"assistant"' not in line:
                    continue
                try:
                    d = json.loads(line)
                    if d.get("type") != "assistant":
                        continue
                    t = dt.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
                    if t.astimezone(dt.timezone.utc).date().isoformat() != day:
                        continue
                    u = d["message"]["usage"]
                except (ValueError, KeyError, TypeError):
                    continue
                k = d.get("requestId") or d.get("uuid")
                if k in seen:
                    continue
                seen.add(k)
                w = (u.get("input_tokens", 0) + u.get("output_tokens", 0)
                     + u.get("cache_creation_input_tokens", 0)
                     + u.get("cache_read_input_tokens", 0) / 10)
                total += w
                if d["message"].get("model") == "claude-fable-5-1":
                    fable += w
        assert total > 0
        assert _pct(r[6]) == pytest.approx(100.0 * fable / total, abs=0.5)
    finally:
        if c.exists():
            c.unlink()


def test_timer_unit_parses():
    """H-003 Files: "scripts/specfactory/systemd/om-token-report.service and .timer
    (nightly 23:50)". Tests: "The timer unit parses (systemd-analyze verify)." """
    t = REPO / "scripts/specfactory/systemd/om-token-report.timer"
    p = subprocess.run(["systemd-analyze", "verify", str(t)], capture_output=True, text=True)
    assert t.exists(), "om-token-report.timer is missing"
    assert p.returncode == 0, p.stderr


def test_control_existing_timer_parses():
    """Positive control, green today: the harness works on the existing timer."""
    t = REPO / "scripts/specfactory/systemd/om-method-metrics.timer"
    p = subprocess.run(["systemd-analyze", "verify", str(t)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr


# ---- H-078: the report sees every directory of the project (docs/stories/H-078.md) ----------------------------
# Premises (dumped from the real ~/.claude/projects tree, 2026-11-03): session directories are named
# `-home-westopoli-Projects-ouroboros-manifold` and `-home-westopoli-Projects-om-push-wt-<name>`; every record
# carries `cwd`. Mail lines (docs/stories/H-077.md "Mail line") carry `ts` as ISO-8601 UTC.
# Every H-078 test runs under a temp HOME and a toy repo holding a copy of the script (REPO = parents[2] of the
# script), so the live ~/.claude/projects and ~/Projects/om-push are never read or written.
import shutil
import stat

MAIN_DIR = "-home-westopoli-Projects-ouroboros-manifold"
WT_DIR = "-home-westopoli-Projects-om-push-wt-x"
OTHER_DIR = "-home-westopoli-Projects-other"
MAIN_CWD = "/home/westopoli/Projects/ouroboros-manifold"
WT_CWD = "/home/westopoli/Projects/om-push/wt/x"
OTHER_CWD = "/home/westopoli/Projects/other"
IN_WIN = "2026-10-28T10:00:00.000Z"  # ISO week 2026-W44
WEEK = "2026-W44"


def _turn(cwd, rid, ts=IN_WIN, side=False, tokens=1000):
    d = _call("claude-fable-5-1", ts, tokens, 0, 0, 0, rid, side)
    d["cwd"] = cwd
    return d


def _toy(tmp_path, lands=0):
    """A toy repo holding a copy of token_report.py with `lands` first-parent `Land` commits dated in W44 on
    refs/remotes/origin/main. Returns the copied script."""
    toy = tmp_path / "toy"
    (toy / "scripts" / "method").mkdir(parents=True)
    script = toy / "scripts" / "method" / "token_report.py"
    shutil.copy(SCRIPT, script)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_COMMITTER_DATE="2026-10-28T09:00:00Z",
               GIT_AUTHOR_DATE="2026-10-28T09:00:00Z")
    run = lambda *a: subprocess.run(["git", "-C", str(toy), *a], check=True, capture_output=True, env=env)
    run("init", "-q", "-b", "main")
    run("add", "-A")
    run("commit", "-q", "-m", "base")
    for i in range(lands):
        (toy / ("f%d.txt" % i)).write_text("x\n")
        run("add", "-A")
        run("commit", "-q", "-m", "Land H-%03d toy" % i)
    run("update-ref", "refs/remotes/origin/main", "HEAD")
    return script


def _go(home, script, week=WEEK):
    p = subprocess.run([sys.executable, str(script), "--week", week], cwd=script.parents[2],
                       env=dict(os.environ, HOME=str(home)), capture_output=True, text=True)
    csvp = Path(home) / "Projects/om-push/metrics" / (week + ".csv")
    rec = next(csv.DictReader(csvp.open()), None) if csvp.exists() else None
    return p, rec


def test_h078_control_one_transcript_under_the_main_directory_is_counted(tmp_path):
    """Positive control, green today (H-078 Tests 1): the same transcript under the main directory gives
    weighted_tokens 1000 through the toy-repo harness."""
    script = _toy(tmp_path)
    _write(tmp_path / "home" / ".claude/projects" / MAIN_DIR / "s.jsonl", [_turn(MAIN_CWD, "r1")])
    p, rec = _go(tmp_path / "home", script)
    assert p.returncode == 0, p.stderr
    assert int(rec["weighted_tokens"]) == 1000


def test_h078_worktree_directory_transcript_is_counted(tmp_path):
    """H-078 Tests 1: "A fixture transcript under a fake `-home-westopoli-Projects-om-push-wt-x` directory with
    `cwd` `/home/westopoli/Projects/om-push/wt/x` and a timestamp in the window is counted in `weighted_tokens`
    (positive control: the same transcript under the main directory gives the same total)." """
    script = _toy(tmp_path)
    _write(tmp_path / "home" / ".claude/projects" / WT_DIR / "s.jsonl", [_turn(WT_CWD, "r1")])
    p, rec = _go(tmp_path / "home", script)
    assert p.returncode == 0, p.stderr
    assert int(rec["weighted_tokens"]) == 1000
    assert "TOKENS dirs scanned 1 active 1 skipped 0" in p.stdout


def test_h078_other_project_directory_is_not_counted(tmp_path):
    """H-078 Tests 2: "A fixture transcript under `-home-westopoli-Projects-other` is not counted." Change 1: a
    session file is kept when any record's `cwd` is under ouroboros-manifold or om-push; the report prints
    `TOKENS dirs scanned <n> active <m> skipped <k>`. The other directory is scanned but not active."""
    script = _toy(tmp_path)
    proj = tmp_path / "home" / ".claude/projects"
    _write(proj / MAIN_DIR / "s.jsonl", [_turn(MAIN_CWD, "r1")])
    _write(proj / OTHER_DIR / "s.jsonl", [_turn(OTHER_CWD, "r2", tokens=5000)])
    p, rec = _go(tmp_path / "home", script)
    assert p.returncode == 0, p.stderr
    assert int(rec["weighted_tokens"]) == 1000
    assert "TOKENS dirs scanned 2 active 1 skipped 0" in p.stdout


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads any directory")
def test_h078_unreadable_directory_is_drift_and_row_is_still_written(tmp_path):
    """H-078 Tests 3: "An unreadable directory prints `TOKENS dirs ... skipped 1` and `STATUS tokens DRIFT
    skipped 1`, exit 1, and the CSV row is still written." The `dirs` column holds `<n>/<m>/<k>`."""
    script = _toy(tmp_path)
    proj = tmp_path / "home" / ".claude/projects"
    _write(proj / MAIN_DIR / "s.jsonl", [_turn(MAIN_CWD, "r1")])
    bad = proj / WT_DIR
    _write(bad / "s.jsonl", [_turn(WT_CWD, "r2")])
    bad.chmod(0)
    try:
        p, rec = _go(tmp_path / "home", script)
    finally:
        bad.chmod(stat.S_IRWXU)
    assert "TOKENS dirs scanned 2 active 1 skipped 1" in p.stdout, p.stdout + p.stderr
    assert "STATUS tokens DRIFT skipped 1" in p.stdout
    assert p.returncode == 1
    assert rec is not None and int(rec["weighted_tokens"]) == 1000
    assert rec["dirs"] == "2/1/1"


def test_h078_control_header_keeps_its_ten_columns_first(tmp_path):
    """Positive control, green today (H-078 Tests 4/5): the existing ten columns stay first and the row carries the
    landing count of the toy repo, so a red on the new columns means they are missing, not that the toy is broken."""
    script = _toy(tmp_path, lands=2)
    _write(tmp_path / "home" / ".claude/projects" / MAIN_DIR / "s.jsonl", [_turn(MAIN_CWD, "r1")])
    p, rec = _go(tmp_path / "home", script)
    assert p.returncode == 0, p.stderr
    assert list(rec)[:10] == ["window", "calls", "weighted_tokens", "builder_share", "tests_share",
                              "build_plus_tests_share", "fable_share", "landings", "seen",
                              "tokens_per_landed_line"]
    assert rec["landings"] == "2"


def test_h078_wakeups_per_landing(tmp_path):
    """H-078 Tests 4: "On a toy repo with two `Land` commits in the window and a transcript with 40 non-sidechain
    assistant turns, `wakeups_per_landing` is 20; with no `Land` the field is empty." Change 2: assistant turns of
    non-sidechain sessions, counted once per requestId (3 repeated lines and 5 sidechain turns must not count)."""
    turns = [_turn(MAIN_CWD, "r%d" % i) for i in range(40)]
    dup = [_turn(MAIN_CWD, "r0")] * 3
    side = [_turn(MAIN_CWD, "s%d" % i, side=True) for i in range(5)]
    for lands, want in ((2, 20.0), (0, None)):
        t = tmp_path / ("l%d" % lands)
        script = _toy(t, lands=lands)
        proj = t / "home" / ".claude/projects" / MAIN_DIR
        _write(proj / "s.jsonl", turns + dup)
        _write(proj / "s" / "subagents" / "agent-a.jsonl", side)
        p, rec = _go(t / "home", script)
        assert p.returncode == 0, p.stderr
        got = rec["wakeups_per_landing"]  # KeyError while the column is missing
        if want is None:
            assert got == ""
        else:
            assert float(got) == want


def test_h078_messages_per_landing_counts_inbox_and_delivered_by_ts(tmp_path):
    """H-078 Tests 5: "`messages_per_landing` counts fixture inbox and delivered lines by `ts`." Change 2: lines of
    every `~/Projects/om-push/mail/*/inbox.jsonl` plus `delivered.jsonl` with `ts` in the window, divided by the
    window's `Land` commits. 4 in-window lines over 2 landings is 2; out-of-window lines do not count."""
    script = _toy(tmp_path, lands=2)
    home = tmp_path / "home"
    _write(home / ".claude/projects" / MAIN_DIR / "s.jsonl", [_turn(MAIN_CWD, "r1")])
    mail = home / "Projects/om-push/mail"
    out = "2026-10-20T10:00:00Z"
    _write(mail / "a" / "inbox.jsonl", [{"id": "1", "ts": IN_WIN}, {"id": "2", "ts": IN_WIN}, {"id": "3", "ts": out}])
    _write(mail / "a" / "delivered.jsonl", [{"id": "4", "ts": IN_WIN}, {"id": "5", "ts": out}])
    _write(mail / "b" / "inbox.jsonl", [{"id": "6", "ts": IN_WIN}])
    p, rec = _go(home, script)
    assert p.returncode == 0, p.stderr
    assert float(rec["messages_per_landing"]) == 2.0  # KeyError while the column is missing
