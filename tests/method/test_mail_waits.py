# Rule pins: R-990-01@?
# spec: docs/stories/H-086.md (mailbox-reads-whole-and-waits-once), Finding 1 to 3, Change 1 to 8, Tests; docs/method/communication.md "Reading and waiting"
"""H-086 tests for scripts/method/mail.py, scripts/method/station.py and scripts/specfactory/status_check.py (mail check).
Written first, red on main. Rule quoted (communication.md "Reading and waiting"): "Only `read` consumes mail. `wait`
ends with the line `MAIL pending <n> <classes>` (no text) and never moves mail to `delivered.jsonl`", "A read lowers
the flag", "One wait per chat, no time limit", "A wait never orphans, and if one does it is a bug that shows", "The
undelivered watch".

Every test: a temp OM_PUSH_DIR, a temp registry (tests/method/mailfix.py REGISTRY plus the `station` table), nothing of
the real mailboxes, the real station or a real chat. Every `mail.py wait` and helper process a test starts runs in its
own session and is ended by the test's fixture (os.killpg on the pids it started), never by a shell kill. Waits are
started with a hard `--max` except where the test is about having none (it ends them within 10 s).
OM_MAIL_ANCHOR_PID is the pytest process for every wait and read, except in the orphan tests.

Controls (green on main): a short mail prints the same line as today; the station raises the flag for an `ask`; a single
wait takes the flag and returns; `--max N` ends with `MAIL idle Ns`; with its anchor alive a wait keeps waiting and takes
the flag; stale mail at 119 minutes, and stale mail for `architect`, sends nothing; a 31-minute `block` is the old DRIFT.
Runtime: about one minute (the waits are real processes).
"""
import fcntl
import json
import os
import re
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailfix import MAIL, REGISTRY, REPO, STATION, iso, lines, mail, make_env, put_mail, station_once  # noqa: E402

STATUS_CHECK = REPO / "scripts" / "specfactory" / "status_check.py"
REG = REGISTRY + '\n[station]\nrole = "none"\nrules = false\nsenders = []\n'  # H-086: the undelivered watch sends as `station`
ANCHOR = os.getpid()  # the chat process of the tests: alive for the whole run
MID = "01H086STALE000000000000001"  # a 26-character mail id for the planted stale mail


# ---------------------------------------------------------------- helpers
def env_for(tmp_path, anchor=ANCHOR, **extra):
    env, root = make_env(tmp_path, REG)
    env.pop("OM_MAIL_WAIT_MAX", None)  # H-086 Change 4: this variable does not exist; a stray one must not leak in
    if anchor is None:
        env.pop("OM_MAIL_ANCHOR_PID", None)
    else:
        env["OM_MAIL_ANCHOR_PID"] = str(anchor)
    env.update(extra)
    return env, root


def killpg(p):
    """End a process we started (it leads its own session and group) and everything it left in that group."""
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    for s in (p.stdout, p.stderr):
        if s:
            s.close()


@pytest.fixture
def procs():
    started = []
    yield started
    for p in started:
        killpg(p)


def spawn(procs, argv, env, text=True):
    p = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=text, start_new_session=True)
    procs.append(p)
    return p


def spawn_wait(procs, env, *args, agent="architect"):
    return spawn(procs, [sys.executable, str(MAIL), "wait", "--me", agent, *args], env)


def spawn_helper(procs):
    """A process that stands in for a chat: it just sleeps (at most 120 s, and the fixture ends it)."""
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    procs.append(p)
    return p


def ended(p, secs):
    try:
        p.wait(timeout=secs)
        return True
    except subprocess.TimeoutExpired:
        return False


def wait_for(cond, secs):
    end = time.monotonic() + secs
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.05)
    return bool(cond())


def eof_within(stream, secs):
    """(True, data) when the pipe reaches EOF within secs, else (False, data): EOF means every holder of it has exited."""
    fd, end, data = stream.fileno(), time.monotonic() + secs, b""
    while True:
        left = end - time.monotonic()
        if left <= 0:
            return False, data
        if select.select([fd], [], [], left)[0]:
            chunk = os.read(fd, 4096)
            if not chunk:
                return True, data
            data += chunk


def inbox(root, agent="architect"):
    return lines(root / agent / "inbox.jsonl")


def flag(root, agent="architect"):
    return root / agent / "flag"


def waits_dir(root, agent="architect"):
    return root / agent / "waits"


def log(root):
    p = root / "station.log"
    return p.read_text().splitlines() if p.exists() else []


def last_line(r):
    out = r.stdout.strip().splitlines()
    return out[-1] if out else ""


def ask(env, root, text="a ruling is needed", check=True):
    """An unread `ask` for the architect and the flag the station raises for it (an `ask` wakes a rules agent)."""
    put_mail(root, "architect", cls="ask", text=text, frm="runner-lab")
    assert station_once(env).returncode == 0
    if check:
        assert flag(root).exists(), "premise: the station raises the flag for an ask"


def put_stale(root, agent, minutes_ago, cls="info", frm="runner-lab", re_="H-063", text="a stale note", id_=MID):
    d = root / agent
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "inbox.jsonl", "a") as f:
        f.write(json.dumps({"id": id_, "ts": iso(minutes_ago), "from": frm, "to": agent, "class": cls, "re": re_,
                            "text": text, "attach": [], "read": None}) + "\n")


def text_of(n):
    """n characters, every five of them different from every other five: a cut anywhere shows."""
    return "".join(f"{i:04d}-" for i in range(n // 5 + 1))[:n]


# ---------------------------------------------------------------- Finding 1 / Change 1: the digest is whole
def _digest_case(tmp_path, n, attach):
    env, root = env_for(tmp_path)
    text = text_of(n)
    argv = ["send", "--me", "runner-lab", "--to", "architect", "--class", "ask", "--re", "H-086"]
    for a in attach:
        argv += ["--attach", a]
    sent = mail(env, *argv, text)
    assert sent.returncode == 0, (sent.stdout, sent.stderr)
    rec = inbox(root)[0]
    expected = f"MAIL ask runner-lab H-086 {rec['ts']}: {text}" + (f" [attach: {' '.join(attach)}]" if attach else "")
    r = mail(env, "read", "--me", "architect")
    assert r.returncode == 0, r.stderr
    digest = [x for x in r.stdout.splitlines() if x.startswith("MAIL ")]
    return digest, expected


def test_control_short_mail_prints_the_same_line_as_today(tmp_path):
    """H-086 Tests: "a short mail prints the same line as today (control)." Line: `MAIL <class> <from> <re> <ts>: <text>
    [attach: <paths>]`."""
    digest, expected = _digest_case(tmp_path, 40, ["/p/note.md"])
    assert digest == [expected], digest


@pytest.mark.parametrize("n,attach", [(201, []), (900, []), (1500, ["/p/one.md", "/p/two.md"])])
def test_f1_read_prints_a_long_mail_whole(tmp_path, n, attach):
    """H-086 Finding 1 / Change 1: "A 1,500-character mail prints in full by `read` (red on main)"; "Remove the `[:200]`.
    No other change to the line format." (201 is the first cut length, 900 the measured one, 1500 DRAFT-mail-max.)"""
    digest, expected = _digest_case(tmp_path, n, attach)
    assert len(digest) == 1 and digest[0] == expected, \
        f"digest line is {len(digest[0]) if digest else 0} characters, the whole mail line is {len(expected)}"


# ---------------------------------------------------------------- Change 2: only `read` consumes mail
def test_c2_wait_ends_with_the_pending_line_and_no_text(tmp_path, procs):
    """H-086 Tests: "`wait` returns with `MAIL pending 1 ask` and no text"; Change 2: "`cmd_wait` ends with `MAIL pending
    <n> <classes>` (counts and classes from the inbox, no text)"."""
    env, root = env_for(tmp_path)
    ask(env, root, "the-ruling-words-q9z")
    w = spawn_wait(procs, env, "--max", "10")
    assert ended(w, 5), "the wait did not return though the flag was up"
    out = w.stdout.read()
    assert w.returncode == 0, w.stderr.read()
    assert [x for x in out.splitlines() if x.startswith("MAIL ")] == ["MAIL pending 1 ask"], out
    assert "the-ruling-words-q9z" not in out, out


def test_c2_pending_line_counts_every_unread_mail_and_names_the_classes(tmp_path, procs):
    """H-086 Change 2: "`MAIL pending <n> <classes>` (counts and classes from the inbox, no text)". The separator and the
    order of the classes are not given, so only the count and the class words are asserted."""
    env, root = env_for(tmp_path)
    put_mail(root, "architect", cls="info", n=2, text="plain-note-x1")
    ask(env, root, "the-ruling-words-q9z")
    w = spawn_wait(procs, env, "--max", "10")
    assert ended(w, 5), "the wait did not return though the flag was up"
    out = w.stdout.read()
    pending = [x for x in out.splitlines() if x.startswith("MAIL pending")]
    assert len(pending) == 1 and pending[0].startswith("MAIL pending 3 "), out
    assert "ask" in pending[0] and "info" in pending[0], pending
    assert "plain-note-x1" not in out and "the-ruling-words-q9z" not in out, out


def test_c2_wait_leaves_the_mail_in_the_inbox_unmoved(tmp_path, procs):
    """H-086 Tests: "afterwards the mail is still in `inbox.jsonl` and not in `delivered.jsonl` (red on main: it reads and
    moves it)"; Change 2: "never writes `delivered.jsonl` or empties the inbox"."""
    env, root = env_for(tmp_path)
    ask(env, root, "the-ruling-words-q9z")
    before = (root / "architect" / "inbox.jsonl").read_bytes()
    w = spawn_wait(procs, env, "--max", "10")
    assert ended(w, 5), "the wait did not return though the flag was up"
    assert (root / "architect" / "inbox.jsonl").read_bytes() == before, "wait emptied or changed the inbox"
    assert not (root / "architect" / "delivered.jsonl").exists(), "wait wrote delivered.jsonl"


def test_c2_read_after_a_wait_prints_the_mail_and_marks_it_delivered(tmp_path, procs):
    """H-086 Tests: "a following `read` prints it and marks it delivered (control)"; communication.md: "the chat's next turn
    begins with `read`, which prints the mail and marks it delivered"."""
    env, root = env_for(tmp_path)
    ask(env, root, "the-ruling-words-q9z")
    w = spawn_wait(procs, env, "--max", "10")
    assert ended(w, 5), "the wait did not return though the flag was up"
    r = mail(env, "read", "--me", "architect")
    digest = [x for x in r.stdout.splitlines() if x.startswith("MAIL ")]
    assert len(digest) == 1 and digest[0].endswith(": the-ruling-words-q9z"), r.stdout
    done = lines(root / "architect" / "delivered.jsonl")
    assert len(done) == 1 and done[0]["read"], done
    assert inbox(root) == []


def test_control_read_prints_an_ask_and_marks_it_delivered(tmp_path):
    """H-086 Tests: control for the two tests above, without a wait: `read` alone prints the mail and delivers it."""
    env, root = env_for(tmp_path)
    ask(env, root, "the-ruling-words-q9z")
    r = mail(env, "read", "--me", "architect")
    assert [x for x in r.stdout.splitlines() if x.startswith("MAIL ask")][0].endswith(": the-ruling-words-q9z"), r.stdout
    assert len(lines(root / "architect" / "delivered.jsonl")) == 1 and inbox(root) == []


def test_c2_station_raises_the_flag_again_for_mail_a_wait_left_unread(tmp_path, procs):
    """H-086 Change 2: "The flag taken by a wait whose chat never reads is raised again by the station while mail stays
    unread." (Red on main: the wait read the mail, so there is nothing left to raise for.)"""
    env, root = env_for(tmp_path)
    ask(env, root, "the-ruling-words-q9z")
    w = spawn_wait(procs, env, "--max", "10")
    assert ended(w, 5), "the wait did not return though the flag was up"
    assert not flag(root).exists(), "premise: the wait took the flag"
    assert station_once(env).returncode == 0
    assert flag(root).exists(), "the mail is still unread but the station did not raise the flag again"
    assert len([x for x in log(root) if " flag architect " in x]) == 2, log(root)


# ---------------------------------------------------------------- Finding 2 / Change 3: a read lowers the flag
def test_control_station_raises_the_flag_for_an_ask(tmp_path):
    """H-086 Tests: "Station raises a flag for an `ask`" (control, green on main)."""
    env, root = env_for(tmp_path)
    ask(env, root)
    assert any(" flag architect class=ask unread=1" in x for x in log(root)), log(root)


def test_f2_read_lowers_the_flag(tmp_path):
    """H-086 Finding 2 / Change 3: "`cmd_read` removes `mail/<agent>/flag` after draining, under the agent lock"; Tests:
    "`read` leaves no flag" (red on main)."""
    env, root = env_for(tmp_path)
    ask(env, root)
    r = mail(env, "read", "--me", "architect")
    assert r.returncode == 0 and inbox(root) == [], (r.stdout, r.stderr)
    assert not flag(root).exists(), "read drained the mail and left the flag up"


def test_f2_wait_after_a_read_blocks_until_max(tmp_path, procs):
    """H-086 Finding 2: "the next `wait` returned in 0.1 s with `MAIL none`"; Tests: "`read` leaves no flag and then
    `wait --max 2` prints `MAIL idle 2s` and does not return at once (red)"."""
    env, root = env_for(tmp_path)
    ask(env, root)
    mail(env, "read", "--me", "architect")
    t0 = time.monotonic()
    w = spawn_wait(procs, env, "--max", "2")
    assert ended(w, 8), "wait --max 2 did not end"
    took = time.monotonic() - t0
    out = w.stdout.read()
    assert "MAIL idle 2s" in out and w.returncode == 0, (out, w.stderr.read())
    assert took >= 1.5, f"wait returned after {took:.2f} s on a flag that read should have lowered: {out!r}"


def test_f2_read_with_no_mail_still_removes_a_stray_flag(tmp_path):
    """H-086 Change 3: "`cmd_read` removes `mail/<agent>/flag` after draining ... whether or not there was mail"; Tests:
    "`read` with no mail still removes a stray flag"."""
    env, root = env_for(tmp_path)
    (root / "architect").mkdir(parents=True)
    flag(root).touch()
    r = mail(env, "read", "--me", "architect")
    assert r.returncode == 0 and r.stdout.startswith("MAIL none"), (r.stdout, r.stderr)
    assert not flag(root).exists(), "a stray flag outlived a read with no mail"


# ---------------------------------------------------------------- Change 3: the station takes the agent lock
def _station_under_held_lock(env, root, procs, drain):
    """The test holds mail/architect/.lock with an unread ask in the inbox, starts `station --once`, waits, then (drain)
    empties the inbox as a `read` would, releases the lock and lets the station finish. Returns (held, flag_up, log)."""
    put_mail(root, "architect", cls="ask", text="needs a ruling", frm="runner-lab")
    lock = open(root / "architect" / ".lock", "a")
    fcntl.flock(lock, fcntl.LOCK_EX)
    st = spawn(procs, [sys.executable, str(STATION), "--once"], env)
    try:
        time.sleep(1.2)
        held = st.poll() is None
        if drain:
            (root / "architect" / "inbox.jsonl").write_text("")
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    assert ended(st, 15), "station --once did not finish after the lock was released"
    return held, flag(root).exists(), log(root)


def test_c3_station_is_held_by_the_agent_lock(tmp_path, procs):
    """H-086 Change 3: "`station.py loop()` takes the agent lock (`mail.locked(name)`)"; Tests: "with the test holding
    `mail/<agent>/.lock`, a `station --once` started in the background is held" (red on main)."""
    env, root = env_for(tmp_path)
    held, _, _ = _station_under_held_lock(env, root, procs, drain=False)
    assert held, "station --once finished while the test held mail/architect/.lock"


def test_c3_mail_drained_under_the_lock_raises_no_flag_and_logs_nothing(tmp_path, procs):
    """H-086 Change 3: "re-reads the inbox under it and raises the flag only if mail is still unread"; Tests: "the test
    drains the inbox and releases; no flag and no log line (red on main)"."""
    env, root = env_for(tmp_path)
    _, flag_up, entries = _station_under_held_lock(env, root, procs, drain=True)
    assert not flag_up, "the station raised a flag for mail that was drained before it got the lock"
    assert entries == [], entries


def test_control_mail_left_unread_under_the_lock_still_raises_the_flag(tmp_path, procs):
    """H-086 Tests: "control: mail left unread, the flag is raised" (green on main)."""
    env, root = env_for(tmp_path)
    _, flag_up, entries = _station_under_held_lock(env, root, procs, drain=False)
    assert flag_up and any(" flag architect class=ask unread=1" in x for x in entries), (flag_up, entries)


# ---------------------------------------------------------------- Finding 3 / Change 4: a flag is taken once
def test_control_single_wait_takes_the_flag_and_returns(tmp_path, procs):
    """H-086 Tests control: one armed wait blocks without a flag and returns when the flag is raised (green on main)."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "10")
    time.sleep(1.0)
    assert w.poll() is None, "wait must block while there is no flag"
    ask(env, root, "wake up", check=False)
    assert ended(w, 3), "wait did not return after the flag was raised"
    assert w.returncode == 0 and w.stdout.read().startswith("MAIL "), w.stderr.read()
    assert not flag(root).exists()


def test_f3_three_waits_one_flag_exactly_one_returns(tmp_path, procs):
    """H-086 Finding 3 / Change 4: "a failed `os.remove(flag)` means another wait took it: keep waiting"; Tests: "Three
    waits armed, one flag: exactly one returns, the other two still block until `--max` (red on main: two return); a
    second flag then wakes exactly one more (control)." Five rounds, because on main the double return is a race that
    one round hits about half the time."""
    rounds = 5
    for rnd in range(rounds):
        env, root = env_for(tmp_path / f"round{rnd}")
        ws = [spawn_wait(procs, env, "--max", "6") for _ in range(3)]
        time.sleep(0.8)
        ask(env, root, f"first-{rnd}", check=False)
        time.sleep(1.0)
        done = [w for w in ws if w.poll() is not None]
        assert len(done) == 1, \
            f"round {rnd}: {len(done)} of 3 waits returned for one flag, outputs {[w.stdout.read() for w in done]}"
        put_mail(root, "architect", cls="ask", text=f"second-{rnd}", frm="runner-lab")
        assert station_once(env).returncode == 0  # the second flag
        time.sleep(1.0)
        done = [w for w in ws if w.poll() is not None]
        assert len(done) == 2, f"round {rnd}: {len(done)} of 3 waits had returned after a second flag, expected 2"
        rest = [w for w in ws if w.poll() is None]
        if rnd == rounds - 1:
            assert ended(rest[0], 8), "the last wait did not end at its --max"
            out = rest[0].stdout.read()
            assert "MAIL idle 6s" in out and rest[0].returncode == 0, out
        else:
            for w in ws:
                killpg(w)


# ---------------------------------------------------------------- Change 5: the registry and the WAIT line
def test_c5_read_prints_wait_none_when_no_wait_is_armed(tmp_path):
    """H-086 Tests: "`read` prints `WAIT none` with none armed" (red on main: no WAIT line); Change 5: "`read` ends with
    `WAIT none` or `WAIT armed <n>`"."""
    env, root = env_for(tmp_path)
    r = mail(env, "read", "--me", "architect")
    assert r.returncode == 0 and r.stdout.strip().splitlines() == ["MAIL none", "WAIT none"], r.stdout
    ask(env, root)
    r = mail(env, "read", "--me", "architect")
    assert last_line(r) == "WAIT none", r.stdout


@pytest.mark.parametrize("n", [1, 2])
def test_c5_read_counts_the_waits_of_this_chat(tmp_path, procs, n):
    """H-086 Tests: "`read` prints ... `WAIT armed 1` with one belonging to this chat (`OM_MAIL_ANCHOR_PID` equal)"."""
    env, root = env_for(tmp_path)
    for _ in range(n):
        spawn_wait(procs, env, "--max", "30")
    wait_for(lambda: len(list(waits_dir(root).glob("*"))) >= n, 3.0)
    r = mail(env, "read", "--me", "architect")
    assert last_line(r) == f"WAIT armed {n}", r.stdout


def test_c5_wait_writes_its_record(tmp_path, procs):
    """H-086 Change 5: "`wait` writes `mail/<agent>/waits/<pid>` (JSON: pid, `start` from `/proc/<pid>/stat`, `anchor`)".
    The format of `start` is not given, so only the keys, the pid and the anchor are asserted."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "30")
    rec = waits_dir(root) / str(w.pid)
    assert wait_for(rec.exists, 3.0), f"no record {rec}"
    data = json.loads(rec.read_text())
    assert {"pid", "start", "anchor"} <= set(data), data
    assert int(data["pid"]) == w.pid and int(data["anchor"]) == ANCHOR, data


def test_c5_a_wait_of_another_chat_is_not_counted(tmp_path, procs):
    """H-086 Tests: "a wait with another anchor ... is not counted". Whether its record is dropped is not asserted: Change 5
    deletes only records of dead processes, the Tests line says dropped (reported as a gap)."""
    env, root = env_for(tmp_path)
    other = spawn_helper(procs)
    spawn_wait(procs, {**env, "OM_MAIL_ANCHOR_PID": str(other.pid)}, "--max", "30")
    wait_for(lambda: len(list(waits_dir(root).glob("*"))) >= 1, 3.0)
    r = mail(env, "read", "--me", "architect")
    assert last_line(r) == "WAIT none", r.stdout


def test_c5_a_killed_wait_leaves_a_record_that_the_next_read_drops(tmp_path, procs):
    """H-086 Tests: "a wait killed with `SIGKILL` leaves a record that the next `read` drops and reports `WAIT none` (red
    on main: no WAIT line)"; Change 5: "records of dead processes are deleted"."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "30")
    rec = waits_dir(root) / str(w.pid)
    assert wait_for(rec.exists, 3.0), f"no record {rec} while the wait is armed"
    os.kill(w.pid, signal.SIGKILL)
    w.wait(timeout=5)
    assert rec.exists(), "a killed wait cannot have removed its own record"
    r = mail(env, "read", "--me", "architect")
    assert last_line(r) == "WAIT none", r.stdout
    assert not rec.exists(), "the dead wait's record was not dropped by read"


def test_c5_a_live_pid_with_another_start_time_is_not_counted(tmp_path, procs):
    """H-086 Change 5: "counting only records whose pid is alive with the same start time ... records of dead processes are
    deleted" (pid reuse). The record of a real wait is copied onto a live pid (this test process) so that only the start
    time differs; the anchor still equals the read's."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "30")
    rec = waits_dir(root) / str(w.pid)
    assert wait_for(rec.exists, 3.0), f"no record {rec} while the wait is armed"
    data = json.loads(rec.read_text())
    os.kill(w.pid, signal.SIGKILL)
    w.wait(timeout=5)
    rec.unlink()
    data["pid"] = os.getpid()
    reused = waits_dir(root) / str(os.getpid())
    reused.write_text(json.dumps(data))
    r = mail(env, "read", "--me", "architect")
    assert last_line(r) == "WAIT none", r.stdout


@pytest.mark.parametrize("how", ["flag", "idle"])
def test_c5_wait_removes_its_record_on_every_exit_it_controls(tmp_path, procs, how):
    """H-086 Change 5: "`wait` writes `mail/<agent>/waits/<pid>` ... and removes it on every exit it controls" (the flag
    taken, and `--max` reached)."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "3" if how == "idle" else "20")
    rec = waits_dir(root) / str(w.pid)
    assert wait_for(rec.exists, 2.5), f"no record {rec} while the wait is armed"
    if how == "flag":
        ask(env, root, "wake up", check=False)
    assert ended(w, 6), "the wait did not end"
    assert not rec.exists(), f"the wait left {rec} behind after ending by {how}"


# ---------------------------------------------------------------- Change 4: `--max` stays, no default limit
def test_control_explicit_max_ends_with_idle(tmp_path, procs):
    """H-086 Change 4: "the option [`--max`] stays for tests"; the story's own line `MAIL idle 2s` (control, green on main)."""
    env, root = env_for(tmp_path)
    w = spawn_wait(procs, env, "--max", "2")
    assert ended(w, 6), "wait --max 2 did not end"
    assert "MAIL idle 2s" in w.stdout.read() and w.returncode == 0


def test_control_no_default_limit_and_no_env_variable_limit(tmp_path, procs):
    """H-086 Tests: "No default limit: `wait` with no `--max` and no flag is still running after 5 s (control for "no
    expiry" ...)"; Change 4: "No default `--max` ... `OM_MAIL_WAIT_MAX` does not exist": the variable is set to 1 here. It
    then takes a flag, so the test ends it by itself (the fixture would otherwise)."""
    env, root = env_for(tmp_path, OM_MAIL_WAIT_MAX="1")
    w = spawn_wait(procs, env)
    assert not ended(w, 5), f"wait with no --max ended inside 5 s: {w.stdout.read()!r}"
    ask(env, root, "wake up", check=False)
    assert ended(w, 3), "the wait did not return when the flag was raised"


# ---------------------------------------------------------------- Change 6: orphans
def test_c6_a_wait_exits_silently_when_its_anchor_ends_and_logs_one_line(tmp_path, procs):
    """H-086 Tests: "a wait whose `OM_MAIL_ANCHOR_PID` helper is then ended exits within 4 s with empty output and exit
    0, a raised flag and an unread mail are untouched, and `station.log` gains one `orphan` line (red on main)"; Change 6:
    "removes its record, appends `<ts> orphan <agent> <pid>` to `station.log`, and exits 0 with no output"."""
    env, root = env_for(tmp_path)
    helper = spawn_helper(procs)
    w = spawn_wait(procs, {**env, "OM_MAIL_ANCHOR_PID": str(helper.pid)}, "--max", "30")
    rec = waits_dir(root) / str(w.pid)
    wait_for(rec.exists, 3.0)
    time.sleep(0.5)
    os.kill(helper.pid, signal.SIGKILL)
    helper.wait(timeout=5)  # reaped: a zombie would still look alive to a kill(pid, 0) check
    assert ended(w, 4.0), "the wait was still running 4 s after its anchor ended"
    assert w.returncode == 0 and w.stdout.read() == "", (w.returncode, w.stderr.read())
    assert not rec.exists(), "the orphan left its record behind"
    orphans = [x for x in log(root) if re.fullmatch(rf"\S+ orphan architect {w.pid}", x)]
    assert len(orphans) == 1, log(root)
    put_mail(root, "architect", cls="ask", text="nobody must take this", frm="runner-lab")
    assert station_once(env).returncode == 0
    time.sleep(1.0)
    assert flag(root).exists() and len(inbox(root)) == 1, "the flag or the unread mail was touched"
    assert not (root / "architect" / "delivered.jsonl").exists()


def test_control_a_wait_with_its_anchor_alive_keeps_waiting_and_takes_the_flag(tmp_path, procs):
    """H-086 Tests: "Control: with the helper alive the wait keeps waiting and takes the flag when it is raised." The 3.2 s
    cover more than one 2 s anchor check (green on main)."""
    env, root = env_for(tmp_path)
    helper = spawn_helper(procs)
    w = spawn_wait(procs, {**env, "OM_MAIL_ANCHOR_PID": str(helper.pid)}, "--max", "30")
    assert not ended(w, 3.2), f"the wait ended with its anchor alive: {w.stdout.read()!r}"
    ask(env, root, "wake up", check=False)
    assert ended(w, 3), "the wait did not take the flag"
    assert w.returncode == 0 and w.stdout.read().startswith("MAIL "), w.stderr.read()
    assert not flag(root).exists()


def test_c6_default_anchor_is_the_first_ancestor_that_is_not_a_shell_or_python(tmp_path, procs):
    """H-086 Change 6: "`anchor` is the chat process: `OM_MAIL_ANCHOR_PID` when set, else the first ancestor that is not a
    shell, `python*`, `setsid`, `timeout` or `env`". `xargs` stands in for the chat: wait <- xargs. Beyond the Tests list (the
    story leaves the real ancestor to the builder); the exit is seen as EOF on the pipe both hold."""
    env, root = env_for(tmp_path, anchor=None)
    x = spawn(procs, ["xargs", sys.executable, str(MAIL), "wait", "--me", "architect", "--max", "30"], env, text=False)
    eof, _ = eof_within(x.stdout, 3.2)
    assert not eof, "the wait ended with its anchor (xargs) alive"
    os.kill(x.pid, signal.SIGKILL)
    x.wait(timeout=5)
    eof, data = eof_within(x.stdout, 4.0)
    assert eof, "the wait was still running 4 s after its anchor (xargs) ended"
    assert data == b"", data


# ---------------------------------------------------------------- Change 7: the undelivered watch
def test_c7_stale_mail_makes_one_block_alert_to_the_architect(tmp_path):
    """H-086 Tests: "mail 121 min old to `runner-lab` makes exactly one `block` mail from `station` to `architect` whose
    text contains the recipient, class, sender, re, `waited=121m` and the mail text ... the mail itself stays unread in the
    inbox". Recipient `planner` here (same rules: nothing but `architect` is exempt)."""
    env, root = env_for(tmp_path)
    put_stale(root, "planner", 121, cls="info", frm="runner-lab", re_="H-063", text="pictures for Westley are ready")
    before = (root / "planner" / "inbox.jsonl").read_bytes()
    assert station_once(env).returncode == 0
    got = inbox(root)
    assert len(got) == 1, got
    a = got[0]
    assert (a["from"], a["to"], a["class"]) == ("station", "architect", "block"), a
    for needle in ("UNDELIVERED", "to=planner", "class=info", "from=runner-lab", "re=H-063", "waited=121m", MID,
                   "pictures for Westley are ready"):
        assert needle in a["text"], (needle, a["text"])
    assert (root / "planner" / "inbox.jsonl").read_bytes() == before, "the stale mail was moved or changed"


def test_c7_a_second_loop_sends_nothing_more_and_the_marker_exists(tmp_path):
    """H-086 Tests: "a second `--once` sends nothing more (marker)"; Change 7: "whose id is not in `mail/station-alerted/` ...
    writes the marker file and one `station.log` line" (the other log line is the linger flag for the same mail)."""
    env, root = env_for(tmp_path)
    put_stale(root, "planner", 121)
    assert station_once(env).returncode == 0
    assert (root / "station-alerted" / MID).exists(), "no marker mail/station-alerted/<id>"
    about_planner = [x for x in log(root) if " flag architect " not in x]  # the alert itself wakes the architect: not counted
    assert station_once(env).returncode == 0
    assert len(inbox(root)) == 1, inbox(root)
    assert [x for x in log(root) if " flag architect " not in x] == about_planner and len(about_planner) == 2, log(root)
    # two lines: the linger flag for the mail and the one line of the watch


def test_c7_mail_119_minutes_old_sends_nothing(tmp_path):
    """H-086 Tests: "mail 119 min old sends nothing" (control: DRAFT-mail-undelivered is 2 h; green on main)."""
    env, root = env_for(tmp_path)
    put_stale(root, "planner", 119)
    before = (root / "planner" / "inbox.jsonl").read_bytes()
    assert station_once(env).returncode == 0
    assert inbox(root) == [] and not (root / "station-alerted").exists()
    assert (root / "planner" / "inbox.jsonl").read_bytes() == before


def test_c7_a_1500_character_stale_mail_gives_an_alert_that_fits_and_names_the_id(tmp_path):
    """H-086 Tests: "a 1,500-character stale mail yields an alert under 1,500 characters naming the id"; Change 7: "the text
    cut so the whole stays under DRAFT-mail-max with the id named when cut". 1,500 is the limit `send` allows, so the
    bound asserted is <= 1500."""
    env, root = env_for(tmp_path)
    put_stale(root, "planner", 121, text=text_of(1500))
    before = (root / "planner" / "inbox.jsonl").read_bytes()
    assert station_once(env).returncode == 0
    got = inbox(root)
    assert len(got) == 1 and got[0]["from"] == "station", got
    assert len(got[0]["text"]) <= 1500 and MID in got[0]["text"] and "waited=121m" in got[0]["text"], got[0]["text"]
    assert (root / "planner" / "inbox.jsonl").read_bytes() == before


def test_c7_stale_mail_addressed_to_the_architect_sends_nothing(tmp_path):
    """H-086 Tests: "stale mail addressed to `architect` sends nothing; the mail itself stays unread" (green on main);
    Change 7: "For `architect` itself nothing is sent"."""
    env, root = env_for(tmp_path)
    put_stale(root, "architect", 121, frm="runner-lab")
    before = (root / "architect" / "inbox.jsonl").read_bytes()
    assert station_once(env).returncode == 0
    assert (root / "architect" / "inbox.jsonl").read_bytes() == before, "the station sent to or changed the architect's inbox"
    assert not (root / "station-alerted").exists()


# ---------------------------------------------------------------- Change 7: status_check.py
def _status(tmp_path, env):
    """status_check.py on a toy git repo (as tests/specfactory/test_status_check.py builds it), mail root and registry
    from env."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*a):
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                       capture_output=True, text=True, check=True)
    head = "# Harness\n\n| Id | Story | Status | Evidence |\n|---|---|---|---|\n"
    git("init", "-q", "-b", "main")
    (repo / "docs" / "method").mkdir(parents=True)
    (repo / "docs" / "method" / "README.md").write_text("method\n")
    (repo / "docs" / "method" / "harness.md").write_text(head + "| S-1 | x | Ready | none |\n")
    git("add", "-A")
    git("commit", "-q", "-m", "anchor")
    (repo / "docs" / "method" / "harness.md").write_text(head + "| S-1 | x | Ready | edited |\n")
    git("add", "-A")
    git("commit", "-q", "-m", "edit rows")
    res = subprocess.run([sys.executable, str(STATUS_CHECK), "--repo", str(repo), "--base", "main"], env=env,
                         capture_output=True, text=True, cwd=repo, timeout=60)
    return res, [x for x in res.stdout.splitlines() if x.startswith("STATUS mail ")]


@pytest.mark.parametrize("agent", ["runner-lab", "architect"])
def test_c7_status_check_flags_an_info_unread_past_two_hours(tmp_path, agent):
    """H-086 Tests: "`status_check.py` (toy registry): an `info` mail 121 min old prints `STATUS mail DRIFT <agent> info unread
    121m`"; Change 7: "for any class past 7200 s ... which also covers the Architect's own mail"."""
    env, root = env_for(tmp_path)
    put_mail(root, agent, cls="info", minutes_ago=121)
    res, hits = _status(tmp_path, env)
    assert hits == [f"STATUS mail DRIFT {agent} info unread 121m"], res.stdout
    assert res.returncode == 1, res.stdout


def test_c7_status_check_leaves_an_info_unread_119_minutes_alone(tmp_path):
    """H-086 Tests: "one 119 min old prints no DRIFT" (green on main)."""
    env, root = env_for(tmp_path)
    put_mail(root, "runner-lab", cls="info", minutes_ago=119)
    res, hits = _status(tmp_path, env)
    assert hits == ["STATUS mail OK 1 unread"], res.stdout


def test_control_status_check_still_flags_a_block_past_thirty_minutes(tmp_path):
    """H-086 Tests: "the existing 30-minute block/ask line is unchanged (control)"."""
    env, root = env_for(tmp_path)
    put_mail(root, "architect", cls="block", minutes_ago=31)
    res, hits = _status(tmp_path, env)
    assert hits == ["STATUS mail DRIFT architect block unread 31m"] and res.returncode == 1, res.stdout
