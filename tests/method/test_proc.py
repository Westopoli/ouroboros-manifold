# Rule pins: R-990-01@?
"""H-081 tests (proc.py register and reaper). Story: docs/stories/H-081.md, "Every process the harness starts is
written down with who started it and why, and a finished one is cleaned up by the evidence, not by asking me."

Rule quoted: "A process is killed by an agent only through `proc.py reap`, and `reap` kills only when all three hold:
(1) a record exists for the pid; (2) the pid's start time equals the record's (no pid reuse); (3) one of: the owner
has ended (...), the story has a `Land` commit on main after the record's start, or the record's TTL has passed."

Fixture premises (story Interfaces, no live path touched): OM_PUSH_DIR and HOME are temp dirs; records are
$OM_PUSH_DIR/procs/<pid>.json; sub-agent transcripts are $HOME/.claude/projects/<dir>/subagents/<id>.jsonl; the toy
repo is the cwd of the reap call (branch main). Children are `sleep`.
Parked (docs/stories/H-081.md is silent): how reap is pointed at the repo, the socket dir env name for the chat-owner
case (not tested, only the transcript owner is), and the transcript line key for the time (`timestamp`, ISO Z, as in
real transcripts, see tests/method/test_token_report.py).
"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "scripts" / "method" / "proc.py"


def _ticks(pid):
    return open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[19]  # field 22


def _alive(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


class Env:
    def __init__(self, tmp):
        self.push = tmp / "push"
        self.home = tmp / "home"
        self.repo = tmp / "repo"
        self.push.mkdir()
        self.home.mkdir()
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "OM_PUSH_DIR": str(self.push)}
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
        self.pids = []

    def git(self, *a, **kw):
        return subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True, text=True,
                              env={**os.environ, **kw.get("env", {})})

    def run(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(PROC), *args], capture_output=True, text=True, env=self.env,
                              cwd=str(cwd or self.repo), timeout=60)

    def start(self, owner, story="H-999", ttl=None):
        a = ["start", "--owner", owner, "--story", story, "--purpose", f"test {owner}", "--detach"]
        if ttl is not None:
            a += ["--ttl", str(ttl)]
        r = self.run(*a, "--", "sleep", "300")
        assert r.returncode == 0, r.stderr
        pid = int(r.stdout.split("PROC OK ")[1].split()[0])
        self.pids.append(pid)
        return pid

    def record(self, pid):
        return json.loads((self.push / "procs" / f"{pid}.json").read_text())

    def transcript(self, agent, ended, offset_s=120):
        d = self.home / ".claude" / "projects" / "-toy" / "sess" / "subagents"
        d.mkdir(parents=True, exist_ok=True)
        ts = (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        line = {"type": "assistant", "timestamp": ts,
                "message": {"role": "assistant", "stop_reason": "end_turn" if ended else "tool_use", "content": []}}
        (d / f"{agent}.jsonl").write_text(json.dumps(line) + "\n")

    def cleanup(self):
        for p in self.pids:
            try:
                os.killpg(p, signal.SIGKILL)
            except OSError:
                pass


@pytest.fixture
def E(tmp_path):
    e = Env(tmp_path)
    yield e
    e.cleanup()


def test_control_fixture_and_sleep_child(E):
    """Positive control (green today): the temp env is isolated, a sleep child runs and its /proc start parses."""
    p = subprocess.Popen(["sleep", "300"], start_new_session=True)
    E.pids.append(p.pid)
    assert _alive(p.pid) and _ticks(p.pid).isdigit()
    live = (Path.home() / "Projects" / "om-push").resolve()
    assert str(E.push).startswith(str(E.push.parent)) and E.push.resolve() != live
    assert not str(E.push.resolve()).startswith(str((live / "procs").resolve()))


def test_start_detach_writes_record(E):
    """S-H-081 test 1: record `start` equals the live /proc value and `pgid` is the child's."""
    pid = E.start("agent-a")  # red: scripts/method/proc.py does not exist
    rec = E.record(pid)
    assert rec["pid"] == pid and rec["start"] == _ticks(pid)
    assert rec["pgid"] == os.getpgid(pid) == pid
    assert rec["owner"] == "agent-a" and rec["story"] == "H-999" and rec["cmd"][0] == "sleep"


def test_reap_keeps_live_owner_and_ttl_left_and_unrecorded(E):
    """Rule (3): kept when owner alive and TTL left; (2) kept when start differs; no record: KEEP, not killed."""
    E.transcript("agent-live", ended=False)
    live = E.start("agent-live")
    mism = E.start("agent-live")
    rec = E.record(mism)
    rec["start"] = str(int(rec["start"]) + 1)
    (E.push / "procs" / f"{mism}.json").write_text(json.dumps(rec))
    out = E.run("reap").stdout
    assert f"PROC KEEP {live} alive owner" in out
    assert f"PROC KEEP {mism} start mismatch" in out
    assert _alive(live) and _alive(mism)
    stranger = subprocess.Popen(["sleep", "300"], start_new_session=True)
    E.pids.append(stranger.pid)
    out = E.run("reap", "--pid", str(stranger.pid)).stdout
    assert f"PROC KEEP {stranger.pid} no record" in out
    assert _alive(stranger.pid)  # positive control: still alive


def test_ttl_left_is_kept(E):
    """Rule (3): `ttl <n>s left` is a KEEP when nothing else ends the process."""
    E.transcript("agent-live", ended=False)
    pid = E.start("agent-live", ttl=3600)
    assert f"PROC KEEP {pid} ttl" in E.run("reap").stdout and _alive(pid)


def _killed_and_logged(E, pid, survivor, evidence_word):
    out = E.run("reap").stdout
    assert f"PROC KILL {pid} {evidence_word}" in out, out
    deadline = time.time() + 15
    while _alive(pid) and time.time() < deadline:
        time.sleep(0.1)
    assert not _alive(pid) and _alive(survivor)
    assert (E.push / "procs" / "reaped" / f"{pid}.json").exists()
    assert not (E.push / "procs" / f"{pid}.json").exists()
    line = (E.push / "procs" / "reaped.log").read_text().strip().splitlines()[-1].split()
    assert line[1] == str(pid) and evidence_word in " ".join(line) and line[-1] == "sleep"


def test_reap_kills_when_owner_ended(E):
    """S-H-081 test 3a: owner transcript ends after the record -> KILL `owner ended`, survivor lives."""
    E.transcript("agent-live", ended=False)
    survivor = E.start("agent-live")
    victim = E.start("agent-done")
    E.transcript("agent-done", ended=True)
    _killed_and_logged(E, victim, survivor, "owner ended")


def test_reap_kills_when_story_landed(E):
    """S-H-081 test 3b: a `Land <story>` commit on main after the record -> KILL `story landed`."""
    E.transcript("agent-live", ended=False)
    survivor = E.start("agent-live", story="H-998")
    victim = E.start("agent-live", story="H-999")
    later = (datetime.now(timezone.utc) + timedelta(seconds=120)).isoformat()
    E.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "Land H-999 toy",
          env={"GIT_COMMITTER_DATE": later, "GIT_AUTHOR_DATE": later})
    _killed_and_logged(E, victim, survivor, "story landed")


def test_reap_kills_when_ttl_passed(E):
    """S-H-081 test 3c: TTL passed -> KILL `ttl passed`, survivor lives."""
    E.transcript("agent-live", ended=False)
    survivor = E.start("agent-live", ttl=3600)
    victim = E.start("agent-live", ttl=1)
    time.sleep(2.5)
    _killed_and_logged(E, victim, survivor, "ttl passed")


def test_reap_dry_run_kills_nothing(E):
    """S-H-081 test 4: --dry-run prints the same KILL line and kills nothing."""
    E.transcript("agent-done", ended=True)
    victim = E.start("agent-done")
    dry = E.run("reap", "--dry-run").stdout
    assert f"PROC KILL {victim} owner ended" in dry
    assert _alive(victim) and (E.push / "procs" / f"{victim}.json").exists()
    assert not (E.push / "procs" / "reaped.log").exists()
