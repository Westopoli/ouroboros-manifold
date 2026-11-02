# spec: docs/stories/H-059.md (two-gate-channels), Tests 1 to 6
"""H-059 two-gate-channels. Tests are named t1 to t6 after the story's Tests list; c* are positive controls.

Everything runs in scratch: private HOME (so `~/Projects/om-push/<name>.lock` is under tmp_path), scratch gate roots
reusing test_gate_concurrent.py's helpers (_fake_root, _fixture_repo, _env; that file is not edited), scratch wt root
and repo, scratch bare remote. Nothing touches the real om-push locks, trees or remote.

Pinned from the story: lock names gate-lab.lock, gate-beta.lock, push.lock, play.lock; `Channel: lab|beta` Machine
line; `CHANNEL mismatch`; wt.py `--channel`; ten slots per channel (DRAFT-wt-slots-per-channel). Pinned by precedent
(gate.lock, records.lock live in ~/Projects/om-push): the new locks live there too. Open interfaces are listed in
the report and in gate_channels_park.py; no value is guessed.

Runtime: t1 about 30 s, t2 about 60 s (two serial gates, may pass 60 s), the rest a few seconds each.
"""
import csv
import fcntl
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(HERE))
import gate_channels_park as park  # noqa: E402
import test_gate_concurrent as gc  # noqa: E402  (helpers only)
from gate_toy_root import write_story  # noqa: E402

SLEEP = 2.5
SLEEPS = {s: SLEEP for s in gc.SUITES}
CSV_COLS = 14


def _lock(home, name):
    p = Path(home) / "Projects" / "om-push" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


class Gate:
    """One scratch candidate gated under `flock <lock> merge_gate.sh`; stamps first and last stdout line."""

    def __init__(self, base, idx, lock, csv_path, home, merge_root, stop_after=None, hold_csv=False):
        d = base / f"g{idx}"
        d.mkdir(parents=True)
        root, _ = gc._fake_root(d)
        repo = gc._fixture_repo(merge_root / f"wt-c{idx}")
        env = gc._env(d, SLEEPS, {})
        env.update(HOME=str(home), MERGE_GATE_RUNS_CSV=str(csv_path), TMPDIR=str(d))
        if stop_after:
            env["MERGE_GATE_STOP_AFTER"] = stop_after
        self.repo, self.lines, self.first, self.last = repo, [], None, None
        gate = root / "scripts" / "specfactory" / "merge_gate.sh"
        self.p = subprocess.Popen(["flock", str(lock), "bash", str(gate), "--tier", "full", str(repo), "HEAD", "B1"],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()

    def _read(self):
        for ln in self.p.stdout:
            now = time.time()
            self.first = self.first or now
            self.last = now
            self.lines.append(ln.rstrip("\n"))

    def finish(self, timeout=gc.GATE_TIMEOUT_S):
        try:
            self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.t.join(5)
        return self.p.returncode

    @property
    def out(self):
        return "\n".join(self.lines)

    @property
    def head(self):
        return gc._git(self.repo, "rev-parse", "HEAD")


def run_two(tmp_path, lock_a, lock_b):
    home = tmp_path / "home"
    csv_path = tmp_path / "gate_runs.csv"
    merge_root = tmp_path / "wt"
    merge_root.mkdir()
    a = Gate(tmp_path, 1, _lock(home, lock_a), csv_path, home, merge_root)
    b = Gate(tmp_path, 2, _lock(home, lock_b), csv_path, home, merge_root)
    a.finish(), b.finish()
    return a, b, csv_path


def rows_of(csv_path):
    return list(csv.reader(io.StringIO(Path(csv_path).read_text()))) if Path(csv_path).exists() else []


def overlap(a, b):
    return max(a.first, b.first) < min(a.last, b.last)


# ------------------------------------------------------------------ controls (green on main)


def test_c1_overlap_detector_reads_serial_and_overlap():
    """Control for t1 and t2: the interval test tells overlap from serial."""
    class G:
        def __init__(s, f, l): s.first, s.last = f, l
    assert overlap(G(0, 5), G(1, 6)) and not overlap(G(0, 5), G(5.5, 9))


def test_c2_one_gate_lands_alone_with_a_row(tmp_path):
    """Control for t1 and t2: the scratch gate harness runs one candidate to a csv row; so a red means the feature."""
    home = tmp_path / "home"
    csv_path = tmp_path / "gate_runs.csv"
    (tmp_path / "wt").mkdir()
    g = Gate(tmp_path, 1, _lock(home, "gate.lock"), csv_path, home, tmp_path / "wt")
    rc = g.finish()
    rows = rows_of(csv_path)
    assert len(rows) == 1 and len(rows[0]) == CSV_COLS, (rc, g.out[-2000:], rows)
    assert rows[0][1] == "B1" and rows[0][4] == g.head and not re.search(r"^GATE \S+ REJECT", g.out, re.M), g.out[-2000:]


# ------------------------------------------------------------------ t1, t2

def test_t1_two_candidates_gate_at_once_under_the_two_channel_locks(tmp_path):
    """H-059 test 1: "Two scratch candidates gate at the same time under the two locks ...; both land; gate_runs.csv
    holds both rows intact." gate-lab.lock and gate-beta.lock, one shared csv and one shared merge root."""
    a, b, csv_path = run_two(tmp_path, "gate-lab.lock", "gate-beta.lock")
    assert overlap(a, b), f"the gates ran one after the other: {a.first:.1f}-{a.last:.1f} / {b.first:.1f}-{b.last:.1f}"
    for g in (a, b):
        assert not re.search(r"^GATE \S+ REJECT", g.out, re.M), g.out[-2000:]
    rows = rows_of(csv_path)
    assert len(rows) == 2 and all(len(r) == CSV_COLS for r in rows), rows
    assert {r[4] for r in rows} == {a.head, b.head} and all(r[1] == "B1" for r in rows), rows


def test_t2_control_the_same_two_under_one_lock_name_serialise(tmp_path):
    """H-059 test 2 (positive control): the same two candidates under one lock name serialise; the second waits."""
    a, b, csv_path = run_two(tmp_path, "gate-lab.lock", "gate-lab.lock")
    assert not overlap(a, b), f"one lock name but the gates overlapped: {a.first:.1f}-{a.last:.1f} / {b.first:.1f}-{b.last:.1f}"
    assert len(rows_of(csv_path)) == 2


def test_t1b_runs_csv_row_is_appended_under_flock_on_the_csv(tmp_path):
    """H-059 Change: "`gate_runs.csv` rows appended under `flock` on the csv". A holder takes LOCK_EX on the csv; a
    gate that reaches its row waits for it and then writes it. Control half: with no holder the row lands at once."""
    home = tmp_path / "home"
    for held in (False, True):
        sub = tmp_path / ("held" if held else "free")
        sub.mkdir()
        csv_path = sub / "gate_runs.csv"
        csv_path.write_text("")
        (sub / "wt").mkdir()
        fd = open(csv_path, "a")
        if held:
            fcntl.flock(fd, fcntl.LOCK_EX)
        g = Gate(sub, 1, _lock(home, "gate-lab.lock"), csv_path, home, sub / "wt", stop_after="base")
        time.sleep(5)
        if held:
            assert g.p.poll() is None and csv_path.read_text() == "", \
                f"the gate wrote its row (rc {g.p.poll()}) while the csv was flock'd by another process"
            fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()
        assert g.finish(60) == 0, g.out
        assert len(rows_of(csv_path)) == 1, (held, g.out)


def test_t1c_cache_and_candidate_files_are_written_through_mktemp_and_renamed(tmp_path):
    """H-059 Change: "cache and candidate-result files written through `mktemp` in the same directory and renamed".
    Today the temp name is fixed (`<file>.tmp`); a directory squatting that name breaks the store. Control half: the
    store works when nothing squats and leaves one valid json."""
    sys.path.insert(0, str(SPEC_DIR))
    import merge_gate_support as mgs
    res = type("R", (), dict(passed=1, failed=0, failing_ids=[], returncode=0, first_assertion={}, skipped=0,
                             xfailed=0, scale_gated=[]))()
    for squat in (False, True):
        cache = tmp_path / ("s" if squat else "n") / "baseline_cache" / "abc123.json"
        cache.parent.mkdir(parents=True)
        if squat:
            (cache.parent / (cache.name + ".tmp")).mkdir()
        mgs._store_cached_baseline(cache, "h", "abc123", "csim", res)
        assert "csim" in json.loads(cache.read_text())["suites"], squat
        strays = [p.name for p in cache.parent.iterdir() if p.name not in (cache.name, cache.name + ".lock", cache.name + ".tmp")]
        assert not strays, strays


# ------------------------------------------------------------------ t3

PLAY_LAUNCH_S = 30


def _play_tree(tmp_path):
    t = tmp_path / "tree"
    (t / "scripts" / "specfactory").mkdir(parents=True)
    (t / "docs" / "stories").mkdir(parents=True)
    (t / "project.godot").write_text('run/main_scene="res://scenes/main.tscn"\n')
    build = t / "scripts" / "build_pipe_linux.sh"
    build.write_text("#!/bin/sh\nmkdir -p dist/linux && printf '#!/bin/sh\\n' > dist/linux/ouroboros_pipe\n")
    build.chmod(0o755)
    cap = t / "scripts" / "specfactory" / "screen_capture.sh"
    cap.write_text("#!/bin/sh\nexit 1\n")
    cap.chmod(0o755)
    gc._git(t, "init", "-q")
    gc._git(t, "add", "-A")
    gc._git(t, "commit", "-q", "-m", "x")
    return t


def _play(tmp_path, home, wait_s):
    """Run `play.sh --check --tree` with a recording fake godot; returns (proc, launch_seen). A launch is a godot
    call without --headless (the real-display run). Killed at the end; the fake godot exits by itself."""
    tree = _play_tree(tmp_path)
    log = tmp_path / "godot.log"
    gd = Path(home) / ".local" / "bin" / "godot.real"
    gd.parent.mkdir(parents=True, exist_ok=True)
    gd.write_text(f'#!/bin/sh\necho "$*" >> {log}\ncase "$*" in *--headless*) exit 0;; esac\nsleep 15\n')
    gd.chmod(0o755)
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "DISPLAY": ":99", "TMPDIR": str(tmp_path / "tmp")}
    (tmp_path / "tmp").mkdir(exist_ok=True)
    p = subprocess.Popen(["bash", str(REPO / "scripts" / "play.sh"), "--check", "--tree", str(tree)],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)

    def launched():
        return log.exists() and any("--headless" not in ln for ln in log.read_text().splitlines())

    end = time.time() + wait_s
    while time.time() < end and not launched():
        time.sleep(0.5)
    return p, launched


def _kill(p):
    try:
        os.killpg(p.pid, 9)
    except OSError:
        pass
    p.wait()


def test_c3_play_sh_check_launches_with_no_holder(tmp_path):
    """Control for t3: with nobody holding play.lock, play.sh --check reaches the real-display launch of the fake godot."""
    p, launched = _play(tmp_path, tmp_path / "home", PLAY_LAUNCH_S)
    try:
        assert launched(), "play.sh never launched the fake godot: harness broken"
    finally:
        _kill(p)


def test_t3_play_lock_blocks_a_second_play_check_until_released(tmp_path):
    """H-059 test 3: "`play.lock`: a second `play.sh --check` invocation blocks while a first holds the lock
    (simulated holder), and proceeds when released." Holder: flock on <HOME>/Projects/om-push/play.lock."""
    home = tmp_path / "home"
    fd = open(_lock(home, "play.lock"), "w")
    fcntl.flock(fd, fcntl.LOCK_EX)
    p, launched = _play(tmp_path, home, 12)
    try:
        assert not launched(), "play.sh launched on the display while another process held play.lock"
        fcntl.flock(fd, fcntl.LOCK_UN)
        end = time.time() + PLAY_LAUNCH_S
        while time.time() < end and not launched():
            time.sleep(0.5)
        assert launched(), "play.sh did not proceed after play.lock was released"
    finally:
        fd.close()
        _kill(p)


# ------------------------------------------------------------------ t4

def _scratch_remote(tmp_path):
    bare = tmp_path / "remote.git"
    gc._git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    for n in ("a", "b"):
        w = tmp_path / n
        gc._git(tmp_path, "clone", "-q", str(bare), str(w))
        gc._git(w, "checkout", "-q", "-B", "main")
    (tmp_path / "a" / "f").write_text("0\n")
    gc._git(tmp_path / "a", "add", "-A")
    gc._git(tmp_path / "a", "commit", "-q", "-m", "seed")
    gc._git(tmp_path / "a", "push", "-q", "origin", "main")
    return bare


def test_c4_two_pushes_under_one_flock_serialise_and_both_land_in_order(tmp_path):
    """Control for t4 (green on main): the shape the clerk's push step must have, fetch+merge+push under push.lock,
    serialises two pushers to a scratch remote and both commits land, the second on top of the first."""
    bare = _scratch_remote(tmp_path)
    lock = _lock(tmp_path / "home", "push.lock")
    for n in ("b", "a"):  # b fetches the seed too
        gc._git(tmp_path / n, "fetch", "-q", "origin")
    gc._git(tmp_path / "b", "merge", "-q", "--ff-only", "origin/main")
    procs = []
    for n in ("a", "b"):
        w = tmp_path / n
        (w / f"{n}.txt").write_text(n)
        gc._git(w, "add", "-A")
        gc._git(w, "commit", "-q", "-m", f"commit {n}")
        script = (f'cd {w} && git fetch -q origin && git -c user.name=t -c user.email=t@t merge -q --no-edit origin/main '
                  f'&& sleep 1 && git push -q origin HEAD:main')
        procs.append(subprocess.Popen(["flock", str(lock), "bash", "-c", script], stderr=subprocess.PIPE, text=True))
    assert [p.wait(30) for p in procs] == [0, 0]
    subj = gc._git(bare, "log", "--format=%s", "main")
    assert "commit a" in subj and "commit b" in subj


def test_t4_the_clerk_card_takes_push_lock_around_the_push():
    """H-059 test 4: "`push.lock`: two pushes ... serialise and both land in order." and Change: "`push.lock` (new,
    short) around fetch, merge, pre_gate re-check and `git push HEAD:main`". No script performs the push (Q-H059-2),
    so the carrier tested is the clerk card: the push step names push.lock and the retired gate.lock is gone."""
    text = (REPO / "docs" / "method" / "clerk.md").read_text()
    push_lines = [ln for ln in text.splitlines() if "HEAD:main" in ln]
    assert push_lines and any("push.lock" in ln for ln in push_lines), "clerk.md: no push line names push.lock"
    assert "gate.lock" not in re.sub(r"gate-(lab|beta)\.lock", "", text), "clerk.md still names the retired gate.lock"


# ------------------------------------------------------------------ t5

def _channel_repo(tmp_path, channel):
    r = tmp_path / "chrepo"
    (r / "docs" / "stories").mkdir(parents=True)
    lines = "Flag: harness\n" + (f"Channel: {channel}\n" if channel else "") + "Tests: tests/x.py\nScene: none (harness)\n"
    (r / "docs" / "stories" / "H-777.md").write_text("# H-777: x\n\n" + lines)
    gc._git(r, "init", "-q", "-b", "main")
    gc._git(r, "add", "-A")
    gc._git(r, "commit", "-q", "-m", "x")
    return r


def _status(repo, extra):
    return subprocess.run([sys.executable, str(SPEC_DIR / "status_check.py"), "--repo", str(repo), *extra],
                          capture_output=True, text=True)


def test_c5_status_check_runs_on_a_toy_repo_without_channel_complaints(tmp_path):
    """Control for t5: status_check.py runs on the toy repo (story with no Channel line, default lab) and says nothing
    about CHANNEL."""
    r = _status(_channel_repo(tmp_path, None), [])
    assert "STATUS" in r.stdout and "CHANNEL" not in r.stdout + r.stderr, r.stdout + r.stderr


def test_t5_beta_story_gated_under_the_lab_lock_is_refused(tmp_path):
    """H-059 test 5: "A story with `Channel: beta` gated under `gate-lab.lock` is refused by `status_check.py` with
    `CHANNEL mismatch`." Also Change: "a `Channel: lab|beta` Machine line (default `lab` when absent)"; so beta under
    gate-beta.lock and an absent line under gate-lab.lock are both accepted. How status_check.py learns the lock is
    Q-H059-1 (gate_channels_park.py)."""
    assert park.TAKEN_LOCK_ARGV is not None, "PARKED Q-H059-1: the interface by which status_check.py learns the lock taken"
    def run(channel, lock):
        return _status(_channel_repo(tmp_path / f"{channel}-{lock}", channel), park.TAKEN_LOCK_ARGV("H-777", lock))
    bad = run("beta", "gate-lab.lock")
    assert bad.returncode != 0 and "CHANNEL mismatch" in bad.stdout + bad.stderr, bad.stdout + bad.stderr
    for channel, lock in (("beta", "gate-beta.lock"), (None, "gate-lab.lock"), ("lab", "gate-lab.lock")):
        ok = run(channel, lock)
        assert "CHANNEL mismatch" not in ok.stdout + ok.stderr, (channel, lock, ok.stdout + ok.stderr)


# ------------------------------------------------------------------ t6

def _wt(tmp_path, *args):
    root, repo = tmp_path / "wt", tmp_path / "wtrepo"
    root.mkdir(exist_ok=True)
    if not repo.exists():
        repo.mkdir()
        gc._git(repo, "init", "-q", "-b", "main")
        (repo / "f").write_text("x")
        gc._git(repo, "add", "-A")
        gc._git(repo, "commit", "-q", "-m", "x")
    common = ["--root", str(root), "--repo", str(repo)]
    sub, rest = args[0], list(args[1:])
    extra = ["--free-floor-gb", "0", "--disk-cap-gb", "100000"]
    return subprocess.run([sys.executable, str(SPEC_DIR / "wt.py"), sub, *common, *extra, *rest],
                          capture_output=True, text=True, timeout=60)


def _new(tmp_path, name, channel):
    ch = ["--channel", channel] if channel else []
    return _wt(tmp_path, "new", name, *ch, "--owner", "t", "--purpose", "h059", "--base", "main")


def test_c6_wt_status_and_check_run_on_the_scratch_root(tmp_path):
    """Control for t6: wt.py status/check run against the scratch repo and root and exit 0."""
    assert _wt(tmp_path, "status").returncode == 0 and _wt(tmp_path, "check").returncode == 0


def test_t6a_wt_new_without_channel_refuses(tmp_path):
    """H-059 test 6: "`wt.py new` without `--channel` refuses" (`--channel lab|beta` is required on `new`)."""
    r = _new(tmp_path, "nochan", None)
    assert r.returncode != 0 and not (tmp_path / "wt" / "nochan").exists(), r.stdout + r.stderr


def test_t6b_status_prints_the_channel_of_each_tree(tmp_path):
    """H-059 test 6: "`status` prints the channel". Tested as: the tree's status row carries its channel word as a
    whitespace token and not the other's (column name and position are Q-H059-3)."""
    for name, ch in (("treeone", "lab"), ("treetwo", "beta")):
        r = _new(tmp_path, name, ch)
        assert r.returncode == 0, r.stdout + r.stderr
    rows = {ln.split()[0]: ln.split() for ln in _wt(tmp_path, "status").stdout.splitlines() if ln.split()[:1] in (["treeone"], ["treetwo"])}
    assert "lab" in rows["treeone"] and "beta" not in rows["treeone"], rows
    assert "beta" in rows["treetwo"] and "lab" not in rows["treetwo"], rows


def test_t6c_slot_cap_is_per_channel(tmp_path):
    """H-059 test 6: "the per-channel slot cap holds (the eleventh `lab` tree refused while `beta` has room)";
    DRAFT-wt-slots-per-channel 10. The default cap is used: no --slots override."""
    for i in range(10):
        r = _new(tmp_path, f"lab{i}", "lab")
        assert r.returncode == 0, (i, r.stdout + r.stderr)
    eleventh = _new(tmp_path, "lab10", "lab")
    assert eleventh.returncode == 3 and "WT REFUSED" in eleventh.stdout and not (tmp_path / "wt" / "lab10").exists(), \
        eleventh.stdout + eleventh.stderr
    beta = _new(tmp_path, "beta0", "beta")
    assert beta.returncode == 0, beta.stdout + beta.stderr
