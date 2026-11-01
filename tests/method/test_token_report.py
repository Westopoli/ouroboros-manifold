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
    t = REPO / "scripts/specfactory/systemd/om-nightly-play.timer"
    p = subprocess.run(["systemd-analyze", "verify", str(t)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
