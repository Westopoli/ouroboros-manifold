# spec: docs/stories/H-080.md (gate-queue; DEC-gate-queue-2026-11-03)
"""H-080: a landing hands its candidate to the gate queue and comes back for the verdict; the gate works its own
queue and a red main pauses it instead of failing everyone behind it.

Story quote: "A landing hands its candidate to the gate and comes back for the verdict; the gate works its own queue
and a red main pauses it instead of failing everyone behind it."

INTERFACES FIXED HERE (the story leaves them open; each is reported as a gap for the Architect to confirm)
- Paths: the worker reads and writes `$OM_PUSH_DIR` (queue/<channel>/, gate-<channel>.lock, mail/, wt/); default
  `$HOME/Projects/om-push`. Every test uses a temp OM_PUSH_DIR and HOME, never the live ~/Projects/om-push.
- Siblings: the worker finds pre_gate.sh, merge_gate.sh, wt.py next to its own (unresolved) script path and
  `../method/mail.py` (H-077) one directory over, so a fake root of symlinks drives it. The sweeps row is read from
  `<root>/docs/northstar/plans/push/sweeps.md` as merge_gate.sh does (REPO_ROOT = two levels up from the script).
- `gate_queue.py --once --channel <c>` drains the channel's queue (every ticket present, in `ts` order) and exits;
  while PAUSED it blocks until the sweeps row is green (or the ticket is exempt). Without --once it is the daemon.
- Lookahead trees come from `wt.py new q-<channel>-<n> --owner gate-queue ...` and end with `wt.py done <path> <sha>`;
  the tests substitute a stub wt.py that clones $TOY_ORIGIN into `$OM_PUSH_DIR/wt/<name>` and logs every call.
- A `PAUSED` file reads exactly `red-sweep <sha>`.

Stubs: pre_gate.sh always prints `PRE_GATE verdict OK`; merge_gate.sh is a stub (logs, optional sleep, rejects a
worktree holding a file FAIL) except in tests 2 and 5, which run the real one with MERGE_GATE_STOP_AFTER=base.

Red on the base tree: tests 1 to 8 (scripts/specfactory/gate_queue.py does not exist, `can't open file`; test 6 also
needs scripts/method/mail.py, H-077). Controls green today: test_control_*.
"""
import csv
import fcntl
import io
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import REPO, SPEC_DIR, fake_gate_root, gate_env  # noqa: E402

CHANNEL = "lab"
SHA_RED = "c4131ea5a0e1eb8098688c43c093c80892ae92ad"
SWEEPS_REL = "docs/northstar/plans/push/sweeps.md"
TIMEOUT = 120

PRE_GATE_STUB = "#!/usr/bin/env bash\necho 'PRE_GATE verdict OK'\nexit 0\n"
MERGE_GATE_STUB = r'''#!/usr/bin/env bash
wt="$1"; id="$3"
anc=0
if [[ -n "${STUB_J_SHA:-}" ]] && git -C "$wt" merge-base --is-ancestor "$STUB_J_SHA" HEAD 2>/dev/null; then anc=1; fi
echo "MG start $id wt=$wt anc_j=$anc queue_s=${MERGE_GATE_QUEUE_S:-unset}" >> "$STUB_LOG"
if [[ "$id" == "${STUB_SLOW_ID:-}" ]]; then
    sleep "${STUB_SLEEP:-3}"
    for d in "$OM_PUSH_DIR"/wt/q-*; do
        [[ -d "$d" ]] || continue
        c=0; git -C "$d" merge-base --is-ancestor "$STUB_J_SHA" HEAD 2>/dev/null && c=1
        echo "PREP $(basename "$d") contains_j=$c" >> "$STUB_LOG"
    done
fi
echo "MG end $id" >> "$STUB_LOG"
if [[ -e "$wt/FAIL" ]]; then echo "GATE base REJECT stub failing candidate"; exit 1; fi
echo "GATE base OK stub"
exit 0
'''
WT_STUB = r'''#!/usr/bin/env python3
import os, subprocess, sys
a = sys.argv[1:]
log = open(os.environ["STUB_WT_LOG"], "a")
log.write(" ".join(a) + "\n"); log.close()
if a[0] == "new":
    path = os.path.join(os.environ["OM_PUSH_DIR"], "wt", a[1])
    subprocess.run(["git", "clone", "-q", os.environ["TOY_ORIGIN"], path], check=True)
    print(f"WT OK {path} push/{a[1]} slots 1/20")
else:
    print("WT OK done " + " ".join(a[1:]))
'''
AGENTS_TOML = '''[runner-lab]
role = "runner.md"
rules = false

[architect]
role = "architect.md"
rules = true
senders = ["*"]

[gate-queue]
role = "none"
rules = false
senders = []
'''


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Env:
    """A fake gate root, a temp OM_PUSH_DIR and a toy origin; `stub` swaps merge_gate.sh and wt.py for stubs."""

    def __init__(self, tmp_path, stub=True):
        self.tmp = tmp_path
        self.push = tmp_path / "push"
        self.home = tmp_path / "home"
        (self.push / "queue" / CHANNEL).mkdir(parents=True)
        self.home.mkdir()
        self.stublog = tmp_path / "stub.log"
        self.wtlog = tmp_path / "wt.log"
        self.runs_csv = tmp_path / "runs.csv"
        self.mg = fake_gate_root(tmp_path)
        self.spec = self.mg.parent
        self.root = self.spec.parent.parent
        self.queue = self.spec / "gate_queue.py"
        self.sweeps = self.root / SWEEPS_REL
        self._replace(self.spec / "pre_gate.sh", PRE_GATE_STUB)
        if stub:
            self._replace(self.spec / "merge_gate.sh", MERGE_GATE_STUB)
            self._replace(self.spec / "wt.py", WT_STUB)
        method = self.root / "scripts" / "method"
        method.mkdir(parents=True)
        (method / "mail.py").symlink_to(REPO / "scripts" / "method" / "mail.py")  # dangling until H-077 lands
        dm = self.root / "docs" / "method"
        if dm.is_symlink():
            dm.unlink()
            dm.mkdir()
            for e in (REPO / "docs" / "method").iterdir():
                if e.name != "agents.toml":
                    (dm / e.name).symlink_to(e)
        (dm / "agents.toml").unlink(missing_ok=True)
        (dm / "agents.toml").write_text(AGENTS_TOML)
        self.origin = tmp_path / "origin.git"
        seed = tmp_path / "seed"
        git(tmp_path, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(tmp_path, "clone", "-q", str(self.origin), str(seed))
        git(seed, "checkout", "-q", "-B", "main")
        (seed / "m1.txt").write_text("m1\n")
        git(seed, "add", "m1.txt")
        git(seed, "commit", "-q", "-m", "m1")
        git(seed, "push", "-q", "origin", "main")
        pieces = tmp_path / "pieces.toml"
        pieces.write_text("")
        self.env = {**gate_env(tmp_path, pieces, MERGE_GATE_STOP_AFTER="base", MERGE_GATE_TOY="1",
                               PRE_GATE_PYTHON=sys.executable),
                    "HOME": str(self.home), "OM_PUSH_DIR": str(self.push), "TOY_ORIGIN": str(self.origin),
                    "STUB_LOG": str(self.stublog), "STUB_WT_LOG": str(self.wtlog)}
        self.env["MERGE_GATE_RUNS_CSV"] = str(self.runs_csv)

    @staticmethod
    def _replace(path, text):
        path.unlink(missing_ok=True)
        path.write_text(text)
        path.chmod(0o755)

    def candidate(self, id, fail=False, fixes=None):
        wt = self.tmp / "cands" / id
        git(self.tmp, "clone", "-q", str(self.origin), str(wt))
        git(wt, "checkout", "-q", "-b", f"s/{id}-toy")
        story = wt / "docs" / "stories" / f"{id}.md"
        story.parent.mkdir(parents=True)
        fx = f"Fixes-sweep: {fixes}\n" if fixes else ""
        story.write_text(f"# {id}: toy\n\n## Files\n\n## Machine lines\n\nFlag: harness\nTests: \n{fx}")
        (wt / f"{id}.txt").write_text(id + "\n")
        if fail:
            (wt / "FAIL").write_text("x\n")
        git(wt, "add", "-A")
        git(wt, "commit", "-q", "-m", id)
        git(wt, "push", "-q", "origin", f"s/{id}-toy")
        return {"id": id, "path": wt, "sha": git(wt, "rev-parse", "HEAD"), "branch": f"origin/s/{id}-toy"}

    def run(self, *args, timeout=TIMEOUT, **kw):
        return subprocess.run([sys.executable, str(self.queue), *args], capture_output=True, text=True,
                              env={**self.env, **kw.pop("env", {})}, timeout=timeout)

    def popen(self, *args, env=None):
        return subprocess.Popen([sys.executable, str(self.queue), *args], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, env={**self.env, **(env or {})})

    def submit(self, c, requester="runner-lab"):
        return self.run("submit", "--channel", CHANNEL, "--id", c["id"], "--branch", c["branch"], "--sha", c["sha"],
                        "--worktree", str(c["path"]), "--requester", requester)

    def ticket_path(self, id):
        return self.push / "queue" / CHANNEL / f"{id}.json"

    def result_path(self, id):
        return self.push / "queue" / CHANNEL / f"{id}.result"

    def write_sweeps(self, *rows):
        head = "| Date-time UTC | Main sha | Verdict | New | Red | Red ids |\n|---|---|---|---|---|---|\n"
        self.sweeps.unlink(missing_ok=True)
        self.sweeps.write_text(head + "".join(rows))

    def log(self, path=None):
        p = path or self.stublog
        return p.read_text() if p.exists() else ""


def sweep_row(verdict, sha):
    return f"| 2026-11-03 00:00 | {sha} | {verdict} | new: none | red: {3 if verdict == 'REJECT' else 0} | |\n"


def wait_for(cond, secs):
    end = time.time() + secs
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.2)
    return cond()


def gate_lines(text):
    out = []
    for ln in text.splitlines():
        if ln.startswith("GATE ") and not ln.startswith("GATE row "):
            ln = re.sub(r"\[\d+(\.\d+)?s\]", "[T]", ln)
            out.append(re.sub(r"(?<=\s)/\S+", "<path>", ln))
    return out


def toy_ticket(env, c, ts):
    d = {"id": c["id"], "branch": c["branch"], "sha": c["sha"], "worktree": str(c["path"]), "requester": "runner-lab",
         "tier": "", "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ")}
    p = env.ticket_path(c["id"])
    p.write_text(json.dumps(d))
    return d


# ---------------------------------------------------------------------------------------------------------- controls

def test_control_toy_gate_runs_through_the_flock_wrapper_and_honours_queue_s(tmp_path):
    """Positive control (green today): today's wrapper path (flock, then pre_gate and merge_gate on the toy repo) prints
    GATE lines, and merge_gate.sh writes MERGE_GATE_QUEUE_S as column 6 of its runs row (story: "`gate_row()` honours
    `MERGE_GATE_QUEUE_S`"). A red in tests 2 and 5 is then the missing queue, not a broken fixture."""
    e = Env(tmp_path, stub=False)
    c = e.candidate("H-901")
    r = subprocess.run(["flock", "-w", "5", str(e.push / "gate-lab.lock"), "bash", "-c",
                        f"cd {c['path']} && git fetch -q origin && git merge --no-edit -q origin/main && "
                        f"{e.spec}/pre_gate.sh {c['path']} origin/main H-901 && "
                        f"{e.spec}/merge_gate.sh {c['path']} origin/main H-901"],
                       capture_output=True, text=True, env={**e.env, "MERGE_GATE_QUEUE_S": "7"}, timeout=TIMEOUT)
    lines = gate_lines(r.stdout)
    assert any(ln.startswith("GATE tier") for ln in lines), r.stdout + r.stderr
    row = next(csv.reader(io.StringIO(e.runs_csv.read_text().splitlines()[-1])))
    assert row[5] == "7", row


# ------------------------------------------------------------------------------------------------------------ tests

def test_1_submit_writes_the_ticket_atomically_and_wait_max_times_out(tmp_path):
    """H-080 Tests 1: "`submit` writes the ticket atomically and prints the position; `wait --max 1` on a missing result
    exits 3." Ticket fields per the story: id, branch, sha, worktree, requester, tier, ts."""
    e = Env(tmp_path)
    c1, c2 = e.candidate("H-901"), e.candidate("H-902")
    r = e.submit(c1)
    assert r.returncode == 0 and r.stdout.strip() == "QUEUE lab H-901 position 1", r.stdout + r.stderr
    t = json.loads(e.ticket_path("H-901").read_text())
    assert {"id", "branch", "sha", "worktree", "requester", "tier", "ts"} <= set(t), t
    assert (t["id"], t["branch"], t["sha"], t["worktree"], t["requester"], t["tier"]) == (
        "H-901", c1["branch"], c1["sha"], str(c1["path"]), "runner-lab", "")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d.*", t["ts"]), t["ts"]
    assert sorted(p.name for p in (e.push / "queue" / CHANNEL).iterdir()) == ["H-901.json"], "no temp file left"
    r2 = e.submit(c2)
    assert r2.stdout.strip() == "QUEUE lab H-902 position 2", r2.stdout + r2.stderr
    w = e.run("wait", "--channel", CHANNEL, "--id", "H-909", "--max", "1")
    assert w.returncode == 3, (w.returncode, w.stdout, w.stderr)


def test_2_one_worker_loop_gate_lines_equal_the_flock_wrapper(tmp_path):
    """H-080 Tests 2: "One worker loop (`gate_queue.py --once --channel lab`) runs a ticket through pre_gate and
    merge_gate on the toy repo and writes a result whose GATE lines equal the lines the same candidate produces through
    today's `flock` wrapper (positive control, byte-equal except timings)." Result ends `QUEUE verdict OK|REJECT <id>
    queue <s>s stage <s>s`; `wait` prints it and exits 0 or 1."""
    e = Env(tmp_path, stub=False)
    c = e.candidate("H-901")
    w = subprocess.run(["flock", "-w", "5", str(e.push / "gate-lab.lock"), "bash", "-c",
                        f"cd {c['path']} && git fetch -q origin && git merge --no-edit -q origin/main && "
                        f"{e.spec}/pre_gate.sh {c['path']} origin/main H-901 && "
                        f"{e.spec}/merge_gate.sh {c['path']} origin/main H-901"],
                       capture_output=True, text=True, env=e.env, timeout=TIMEOUT)
    expect = gate_lines(w.stdout)
    assert expect, w.stdout + w.stderr
    assert e.submit(c).returncode == 0
    r = e.run("--once", "--channel", CHANNEL)
    assert r.returncode == 0, r.stdout + r.stderr
    res = e.result_path("H-901").read_text()
    assert gate_lines(res) == expect, (gate_lines(res), expect)
    assert re.search(r"^QUEUE verdict (OK|REJECT) H-901 queue \d+s stage \d+s$", res, re.M), res
    ok = "QUEUE verdict OK" in res
    wr = e.run("wait", "--channel", CHANNEL, "--id", "H-901", "--max", "5")
    assert wr.returncode == (0 if ok else 1) and "QUEUE verdict" in wr.stdout, (wr.returncode, wr.stdout)


def test_3_stacked_second_ticket_is_prepared_on_the_first_and_reprepared_without_it(tmp_path):
    """H-080 Tests 3: "Two tickets: the second's prepared tree contains the first's sha; when the first is rejected (a
    toy candidate that fails `base`), the second is re-prepared without it and passes." Also: the preparation trees come
    from `wt.py new q-<channel>-<n> --owner gate-queue` and each ends with `wt.py done`."""
    e = Env(tmp_path)
    j, k = e.candidate("H-901", fail=True), e.candidate("H-902")
    assert e.submit(j).returncode == 0
    time.sleep(1.1)
    assert e.submit(k).returncode == 0
    r = e.run("--once", "--channel", CHANNEL,
              env={"STUB_J_SHA": j["sha"], "STUB_SLOW_ID": "H-901", "STUB_SLEEP": "3"})
    assert r.returncode == 0, r.stdout + r.stderr
    log = e.log()
    assert re.search(r"^PREP q-lab-\d+ contains_j=1$", log, re.M), "no prepared tree held H-901 while it gated\n" + log
    starts = [ln for ln in log.splitlines() if ln.startswith("MG start H-902")]
    assert starts and starts[-1].split("wt=")[1].split()[1] == "anc_j=0", starts
    assert "QUEUE verdict REJECT H-901" in e.result_path("H-901").read_text()
    assert "QUEUE verdict OK H-902" in e.result_path("H-902").read_text()
    wt = e.log(e.wtlog).splitlines()
    news = [ln for ln in wt if ln.startswith("new q-lab-")]
    assert news and all("--owner gate-queue" in ln for ln in news), wt
    assert len([ln for ln in wt if ln.startswith("done ")]) == len(news), wt


def test_4_red_sweep_pauses_the_queue_and_fixes_sweep_runs_through(tmp_path):
    """H-080 Tests 4: "A `REJECT` sweeps row writes `PAUSED red-sweep <sha>` and the ticket is not rejected; a green row
    written afterwards resumes it; a ticket whose story file has `Fixes-sweep: <sha>` runs during the pause."""
    e = Env(tmp_path)
    e.write_sweeps(sweep_row("REJECT", SHA_RED))
    c = e.candidate("H-901")
    assert e.submit(c).returncode == 0
    p = e.popen("--once", "--channel", CHANNEL)
    try:
        paused = e.push / "queue" / CHANNEL / "PAUSED"
        assert wait_for(paused.exists, 20), "no PAUSED file on a REJECT sweeps row\n" + (p.poll() is not None and p.stdout.read() or "")
        assert paused.read_text().strip() == f"red-sweep {SHA_RED}"
        time.sleep(1)
        assert not e.result_path("H-901").exists() and p.poll() is None, "ticket must wait, not be rejected"
        e.write_sweeps(sweep_row("REJECT", SHA_RED), sweep_row("PASS", "1" * 40))
        assert wait_for(lambda: p.poll() is not None, 60), "worker did not resume on a green row"
    finally:
        if p.poll() is None:
            p.kill()
    assert "QUEUE verdict OK H-901" in e.result_path("H-901").read_text()
    assert not paused.exists()


def test_4b_ticket_fixing_the_red_sweep_runs_during_the_pause(tmp_path):
    """H-080 Tests 4, last clause: "a ticket whose story file has `Fixes-sweep: <sha>` runs during the pause."
    The row stays red throughout."""
    e = Env(tmp_path)
    e.write_sweeps(sweep_row("REJECT", SHA_RED))
    c = e.candidate("H-901", fixes=SHA_RED)
    assert e.submit(c).returncode == 0
    r = e.run("--once", "--channel", CHANNEL, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "QUEUE verdict OK H-901" in e.result_path("H-901").read_text()


def test_5_queue_s_in_the_runs_row_equals_the_tickets_wait(tmp_path):
    """H-080 Tests 5: "`queue_s` in the `gate_runs.csv` row equals the ticket's wait within 2 s." The ticket is written
    30 s in the past; the real merge_gate.sh (STOP_AFTER=base) writes the row."""
    e = Env(tmp_path, stub=False)
    c = e.candidate("H-901")
    ts = datetime.now(timezone.utc) - timedelta(seconds=30)
    toy_ticket(e, c, ts)
    started = datetime.now(timezone.utc)
    r = e.run("--once", "--channel", CHANNEL)
    assert r.returncode == 0, r.stdout + r.stderr
    row = next(csv.reader(io.StringIO(e.runs_csv.read_text().splitlines()[-1])))
    wait = (started - ts).total_seconds()
    assert abs(int(row[5]) - wait) <= 2, (row[5], wait)


def test_6_each_result_sends_one_info_mail_to_the_requester(tmp_path):
    """H-080 Tests 6: "Each result sends one `info` mail to the requester (fixture registry, H-077's `mail.py`)."
    Mail line (H-077): class info, from gate-queue, to the requester, re the story id."""
    e = Env(tmp_path)
    mail = e.root / "scripts" / "method" / "mail.py"
    reg = subprocess.run([sys.executable, str(mail), "register", "runner-lab"], capture_output=True, text=True, env=e.env)
    assert reg.returncode == 0, f"scripts/method/mail.py (H-077) missing or failing: {reg.stdout}{reg.stderr}"
    c = e.candidate("H-901")
    assert e.submit(c).returncode == 0
    r = e.run("--once", "--channel", CHANNEL)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = (e.push / "mail" / "runner-lab" / "inbox.jsonl").read_text().splitlines()
    assert len(lines) == 1, lines
    m = json.loads(lines[0])
    assert (m["from"], m["to"], m["class"], m["re"]) == ("gate-queue", "runner-lab", "info", "H-901"), m
    assert m["text"].startswith("gate H-901 OK") and str(e.result_path("H-901")) in m["text"], m["text"]


def test_7_worker_holds_the_channel_lock_while_running(tmp_path):
    """H-080 Tests 7: "The worker holds `gate-lab.lock` while running: a `flock -n` from the test fails during a run and
    succeeds after." (Change: each worker holds `~/Projects/om-push/gate-<channel>.lock` with `flock`.)"""
    e = Env(tmp_path)
    c = e.candidate("H-901")
    assert e.submit(c).returncode == 0
    p = e.popen("--once", "--channel", CHANNEL, env={"STUB_SLOW_ID": "H-901", "STUB_J_SHA": c["sha"], "STUB_SLEEP": "4"})
    lock = e.push / "gate-lab.lock"

    def try_lock():
        fd = os.open(lock, os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False
        finally:
            os.close(fd)

    try:
        assert wait_for(lambda: "MG start H-901" in e.log(), 30), p.poll() is not None and p.stdout.read()
        assert not try_lock(), "gate-lab.lock was free during a run"
        p.wait(timeout=60)
    finally:
        if p.poll() is None:
            p.kill()
    assert try_lock(), "gate-lab.lock still held after the worker exited"


def test_8_status_prints_running_waiting_and_paused(tmp_path):
    """H-080 Tests 8: "`status` prints the running id, the waiting count and `PAUSED` when paused." Line shape:
    `QUEUE <channel> <running id|idle> waiting <n> [PAUSED <why>]`, one line per channel (lab, beta)."""
    e = Env(tmp_path)
    idle = e.run("status")
    assert idle.returncode == 0 and "QUEUE lab idle waiting 0" in idle.stdout.splitlines(), idle.stdout + idle.stderr
    assert "QUEUE beta idle waiting 0" in idle.stdout.splitlines(), idle.stdout
    a, b = e.candidate("H-901"), e.candidate("H-902")
    assert e.submit(a).returncode == 0
    time.sleep(1.1)
    assert e.submit(b).returncode == 0
    p = e.popen("--once", "--channel", CHANNEL, env={"STUB_SLOW_ID": "H-901", "STUB_J_SHA": a["sha"], "STUB_SLEEP": "5"})
    try:
        assert wait_for(lambda: "MG start H-901" in e.log(), 30)
        st = e.run("status")
        assert "QUEUE lab H-901 waiting 1" in st.stdout.splitlines(), st.stdout + st.stderr
        p.wait(timeout=90)
    finally:
        if p.poll() is None:
            p.kill()
    (e.push / "queue" / CHANNEL / "PAUSED").write_text(f"red-sweep {SHA_RED}\n")
    e.result_path("H-901").unlink(), e.result_path("H-902").unlink(), e.ticket_path("H-901").unlink()
    e.ticket_path("H-902").write_text(json.dumps({"id": "H-902", "ts": "2026-11-03T00:00:00Z"}))
    st = e.run("status")
    assert f"QUEUE lab idle waiting 1 PAUSED red-sweep {SHA_RED}" in st.stdout.splitlines(), st.stdout + st.stderr
