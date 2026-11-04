"""H-084 play-leaves-no-game-behind: tests for scripts/play.sh (docs/stories/H-084.md).

Story line: "A play never leaves a game running after it ends, however it ends, and a scene that needs a
file to show anything is never passed without one."

Nothing here opens a window, captures a screen or touches the portal, play.lock or ~/Pictures. Same
fakes as tests/method/test_play_proof.py (copied, not imported): a fake tree (a git repo with a stub
build script), a fake HOME whose `.local/bin/godot.real` is a stub Godot, stub `xdotool` / `xwininfo`
ahead of the real ones on PATH. The stub Godot here writes its own pid to a file and sleeps, so the
tests can ask "is the game still alive after play.sh ended". `scripts/screen_capture.sh` in the fake tree
is a stub that prints a `CAPTURE portal` line (the real one needs a portal).

Each test names the finding it proves (Finding 1..4 of H-084) and kills every stub it started in the
fixture teardown, by pid, from Python, only after checking /proc that the pid still runs this test's stub.

Out of scope, named here as the story's Change 1 asks: a SIGKILL of play.sh itself cannot be trapped, so
no test sends one.

Not tested, no rule states it (reported as gaps): what a play.sh WITHOUT --check does to the game when it
exits (today it leaves the game open for the human to play); how play.sh tells a Scene-env value that is
a path from one that is not; what the dry run prints for a story that has a Scene-env line; whether the
missing-input path is printed relative or resolved.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAY = ROOT / "scripts" / "play.sh"
SCENE = "res://scenes/stub/stub.tscn"
OTHER_SCENE = "res://scenes/other/other.tscn"
RES = "1919x1080"  # H-031 Piece two, DEC-display-fault-measured-2026-10-31
MARK = "h084-cleanup-"  # in every stub's command line (its path is under the test's base dir)
# H-084 Change 1: "then KILL after DRAFT-play-term-s 5 s if it is still there".
TERM_S = 5
# Test patience only, not a product tolerance: how long the harness waits before it calls a play.sh or a
# TERM-ignoring stub hung. The story gives no bound for the KILL step beyond "after DRAFT-play-term-s".
PATIENCE_S = 30

GODOT_STUB = '''#!/usr/bin/env python3
import json, os, signal, socket, sys, threading, time
argv = sys.argv[1:]
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps(argv) + "\\n")
if "--import" in argv:
    sys.exit(0)
if os.environ.get("STUB_IGNORE_TERM"):
    def on_term(sig, frm):
        with open(os.environ["STUB_TERM"], "a") as f:
            f.write(repr(time.time()) + "\\n")
    signal.signal(signal.SIGTERM, on_term)
with open(os.environ["STUB_PIDS"], "a") as f:
    f.write(str(os.getpid()) + "\\n")
fight = os.environ.get("OM_FIGHT", "")
with open(os.environ["STUB_ENV"], "w") as f:
    json.dump({"env": dict(os.environ), "OM_FIGHT_exists": bool(fight) and os.path.exists(fight)}, f)
scene = os.environ.get("STUB_QA_SCENE") or next((a for a in argv if a.startswith("res://")), "")
if "--qa-port" in argv:
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", int(argv[argv.index("--qa-port") + 1]))); srv.listen(4)
    def serve():
        while True:
            c, _ = srv.accept(); b = b""
            while not b.endswith(b"\\n"):
                d = c.recv(65536)
                if not d: break
                b += d
            c.sendall(json.dumps({"result": {"scene": scene}}).encode() + b"\\n"); c.close()
    threading.Thread(target=serve, daemon=True).start()
end = time.time() + 300  # a stub nobody kills ends by itself, long after any test
while time.time() < end:
    if "--print-fps" in argv:
        print("FPS: " + os.environ.get("STUB_FPS", "140"), flush=True)
    open(os.environ["STUB_READY"], "a").close()  # one loop turn done: the game is up and being watched
    time.sleep(1)
'''

CAPTURE_STUB = '#!/bin/sh\necho "CAPTURE portal $1"\n'


def proc_state(pid, marker):
    """The /proc state letter of pid when it is still this test's stub, else None."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return None
    if marker.encode() not in cmd:
        return None  # gone, or the pid was reused by something that is not this test's stub
    return stat.rsplit(")", 1)[1].split()[0]


def alive(pid, marker):
    st = proc_state(pid, marker)
    return st is not None and st != "Z"


def wait_gone(pid, marker, within):
    """Seconds until pid is no longer a running stub, polled at 50 ms; None if it outlives `within`."""
    t0 = time.time()
    while time.time() - t0 <= within:
        if not alive(pid, marker):
            return time.time() - t0
        time.sleep(0.05)
    return None if alive(pid, marker) else time.time() - t0


def wait_for(path, within):
    t0 = time.time()
    while time.time() - t0 <= within:
        if Path(path).exists():
            return True
        time.sleep(0.05)
    return Path(path).exists()


class Rig:
    """One test's world: base dir, fake tree, fake HOME, env. Teardown kills every stub it started."""

    def __init__(self, base):
        self.base = Path(base)
        self.pids_file = self.base / "stub-pids"
        self.procs = []  # Popen objects to reap

    def pids(self):
        return [int(x) for x in self.pids_file.read_text().split()] if self.pids_file.exists() else []

    def stub_pid(self):
        assert wait_for(self.pids_file, 20) and self.pids(), "the stub Godot was never launched"
        return self.pids()[-1]

    def gone(self, pid, within):
        return wait_gone(pid, str(self.base), within)

    def alive(self, pid):
        return alive(pid, str(self.base))

    def make(self, map_state="IsViewable", fps=140, wayland=False, x_window=True, stories=None, files=None,
             extra_env=None):
        base = self.base
        home = base / "home"; (home / ".local" / "bin").mkdir(parents=True)
        godot = home / ".local" / "bin" / "godot.real"
        godot.write_text(GODOT_STUB); godot.chmod(0o755)
        bindir = base / "bin"; bindir.mkdir()
        (bindir / "xdotool").write_text("#!/bin/sh\n" + ("echo 12345\nexit 0\n" if x_window else "exit 1\n"))
        (bindir / "xwininfo").write_text(
            "#!/bin/sh\necho 'xwininfo: Window id: 0x3a00007 \"Ouroboros (DEBUG)\"'\n"
            "echo '  Map State: %s'\nexit 0\n" % map_state)
        for p in bindir.iterdir():
            p.chmod(0o755)
        tree = base / "fake_tree"; (tree / "scripts" / "specfactory").mkdir(parents=True)
        (tree / "scripts" / "build_pipe_linux.sh").write_text(
            '#!/bin/sh\necho ran >> "$BUILD_MARK"\nmkdir -p dist/linux && echo stub > dist/linux/ouroboros_pipe\n')
        (tree / "scripts" / "build_pipe_linux.sh").chmod(0o755)
        (tree / "scripts" / "specfactory" / "screen_capture.sh").write_text(CAPTURE_STUB)
        (tree / "scripts" / "specfactory" / "screen_capture.sh").chmod(0o755)
        (tree / "project.godot").write_text('config_version=5\n[application]\nrun/main_scene="%s"\n' % SCENE)
        for sid, text in (stories or {}).items():
            (tree / "docs" / "stories").mkdir(parents=True, exist_ok=True)
            (tree / "docs" / "stories" / f"{sid}.md").write_text(text)
        for rel, text in (files or {}).items():
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            (tree / rel).write_text(text)
        g = ["git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g[:3] + ["init", "-q"], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "fake tree"], check=True)
        (base / "tmp").mkdir(); (base / "run").mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
        env.update(HOME=str(home), PATH=f"{bindir}:{env['PATH']}", TMPDIR=str(base / "tmp"), DISPLAY=":99",
                   STUB_LOG=str(base / "godot-argv.log"), STUB_PIDS=str(self.pids_file),
                   STUB_ENV=str(base / "stub-env.json"), STUB_TERM=str(base / "stub-term"),
                   STUB_READY=str(base / "stub-ready"), STUB_FPS=str(fps), BUILD_MARK=str(base / "build-mark"),
                   DBUS_SESSION_BUS_ADDRESS=f"unix:path={base}/no-bus", XDG_RUNTIME_DIR=str(base / "run"))
        if wayland:
            env["WAYLAND_DISPLAY"] = "wayland-99"
        env.update(extra_env or {})
        return env, tree

    def play(self, env, tree, *args, timeout=150):
        return subprocess.run(["bash", str(PLAY), "--tree", str(tree), *args], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=timeout)

    def play_bg(self, env, tree, *args):
        """play.sh in its own session and process group (what proc.py start gives it), output to a file.
        SIGINT is reset to its default so an inherited 'ignore' cannot hide the Ctrl-C case."""
        out = open(self.base / "play-out.txt", "w")
        p = subprocess.Popen(["bash", str(PLAY), "--tree", str(tree), *args], cwd=ROOT, env=env, stdout=out,
                             stderr=subprocess.STDOUT, start_new_session=True,
                             preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
        self.procs.append(p)
        return p

    def out(self):
        return (self.base / "play-out.txt").read_text()

    def teardown(self):
        for p in self.procs:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            p.wait()
        for pid in self.pids():
            if self.alive(pid):
                for kill in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
                    try:
                        kill()
                    except OSError:
                        pass


@pytest.fixture
def rig():
    base = Path(tempfile.mkdtemp(prefix=MARK))
    r = Rig(base)
    try:
        yield r
    finally:
        r.teardown()
        shutil.rmtree(base, ignore_errors=True)


def scratch_of(stdout):
    m = re.search(r"^scratch: (\S+)$", stdout, re.M)
    assert m, "play.sh printed no `scratch:` line: " + stdout
    return Path(m.group(1))


def spawn_stub_directly(rig, *, ignore_term):
    """The stub Godot started by the test itself (own session), not by play.sh. For the detector control."""
    env, _ = rig.make(extra_env={"STUB_IGNORE_TERM": "1"} if ignore_term else None)
    p = subprocess.Popen([str(rig.base / "home" / ".local" / "bin" / "godot.real"), "--path", "x"], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    rig.procs.append(p)
    assert wait_for(rig.base / "stub-ready", 20), "the directly started stub never came up"
    return p


# ---------------------------------------------------------------------------------------------
# Controls: green on main, stay green
# ---------------------------------------------------------------------------------------------

def test_control_detector_sees_a_term_ignoring_stub_survive_term_and_die_on_kill(rig):
    """H-084 Tests, positive control for the detector: "a stub that ignores `TERM` is still gone after the
    `KILL` step". Detector control (no play.sh involved, green today): the liveness check used by every test
    below reports a TERM-ignoring stub alive after a TERM it recorded, and gone after SIGKILL. So a red below
    means a leaked game, not a blind detector. (The same stub through play.sh is
    test_term_ignoring_game_is_killed_after_the_term_step, red on main.)"""
    p = spawn_stub_directly(rig, ignore_term=True)
    assert rig.alive(p.pid)
    os.kill(p.pid, signal.SIGTERM)
    assert wait_for(rig.base / "stub-term", 10), "the stub never recorded the TERM"
    assert rig.alive(p.pid), "the detector says a TERM-ignoring stub is gone after TERM"
    os.kill(p.pid, signal.SIGKILL)
    p.wait()
    assert rig.gone(p.pid, 1) is not None, "the detector still sees the stub after SIGKILL"


def test_control_detector_sees_a_term_handling_stub_die_on_term(rig):
    """H-084 Tests, positive control for the detector, the other polarity (green today): the liveness check
    reports a stub that has not been signalled alive, and gone after one TERM. The window-reject and signal
    tests below wait on exactly this stub for "gone within DRAFT-play-term-s"."""
    p = spawn_stub_directly(rig, ignore_term=False)
    assert rig.alive(p.pid), "the detector says a running stub is gone"
    os.kill(p.pid, signal.SIGTERM)
    p.wait()
    assert rig.gone(p.pid, 1) is not None, "the detector still sees a TERM-handling stub after TERM"


def test_control_scene_mismatch_path_leaves_no_game_and_removes_scratch(rig):
    """H-084 Tests: "Controls (already green, stay green): the scene-mismatch path ... leave[s] no stub
    alive" (Finding 1: `kill "$gpid"` on `PLAY REJECT scene`, exit 3). The stub reports another scene than
    play.sh wants; play.sh prints `PLAY REJECT scene` and exits 3; the stub is gone. Also H-084 Change 1:
    "the scratch removal trap is kept inside the same handler": the scratch clone is removed."""
    env, tree = rig.make(wayland=True, x_window=False, extra_env={"STUB_QA_SCENE": OTHER_SCENE})
    r = rig.play(env, tree, "--scene", SCENE, "--check")
    assert r.returncode == 3, r.stdout + r.stderr
    assert f"PLAY REJECT scene {OTHER_SCENE} wanted {SCENE}" in r.stdout.splitlines(), r.stdout
    pid = rig.stub_pid()
    assert rig.gone(pid, TERM_S) is not None, f"stub {pid} still alive after the scene-mismatch exit"
    assert not scratch_of(r.stdout).exists(), "the scratch clone was left behind"


def test_control_success_path_leaves_no_game_and_removes_scratch(rig):
    """H-084 Tests: "Controls (already green, stay green): ... the success path leave[s] no stub alive"
    (Finding 1: `kill "$gpid"` after the capture). A `--check` run that reaches the scene and gets its proof
    prints `PLAY proof <path> portal`, exits 0, and the stub is gone; the scratch clone is removed
    (H-084 Change 1: the scratch removal is kept)."""
    env, tree = rig.make(wayland=True, x_window=False)
    r = rig.play(env, tree, "--scene", SCENE, "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"PLAY scene {SCENE} reached" in r.stdout.splitlines(), r.stdout
    assert re.search(r"^PLAY proof \S+ portal$", r.stdout, re.M), r.stdout
    pid = rig.stub_pid()
    assert rig.gone(pid, TERM_S) is not None, f"stub {pid} still alive after the success exit"
    assert not scratch_of(r.stdout).exists(), "the scratch clone was left behind"


def test_control_story_without_scene_env_launches_exactly_as_today(rig):
    """H-084 Tests: "A story with no `Scene-env:` line launches exactly as today (the dry-run `launch:` line
    is byte-identical to main's)." H-084 Change 2: "No line, no change (every story that exists today)."
    The dry-run line for a story with `Scene:` carrying a launch argument is pinned to what main prints."""
    env, tree = rig.make(stories={"T-084": f"# T-084\nScene: {SCENE} --foo 3\n"})
    r = rig.play(env, tree, "--story", "T-084", "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    want = (f"launch: {rig.base}/home/.local/bin/godot.real --path {tree} --windowed --resolution {RES} "
            f"{SCENE} -- --foo 3")
    assert want in r.stdout.splitlines(), (want, r.stdout)


def test_control_stub_records_its_environment_without_scene_env(rig):
    """H-084 Tests, positive control for the Scene-env environment tests below (green today): a real
    `--check` run of a story with no `Scene-env:` line reaches the stub, whose recorded environment holds
    the fake HOME and no `OM_FIGHT`, so a missing `OM_FIGHT` there is the feature, not a blind recorder."""
    env, tree = rig.make(wayland=True, x_window=False, stories={"T-084": f"# T-084\nScene: {SCENE}\n"})
    r = rig.play(env, tree, "--story", "T-084", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.loads((rig.base / "stub-env.json").read_text())
    assert rec["env"]["HOME"] == str(rig.base / "home"), rec["env"].get("HOME")
    assert "OM_FIGHT" not in rec["env"], rec["env"].get("OM_FIGHT")


# ---------------------------------------------------------------------------------------------
# RED on main: the game outlives the play (Finding 1)
# ---------------------------------------------------------------------------------------------

def test_wayland_window_reject_leaves_no_game(rig):
    """H-084 Finding 1 / Tests: "with the stub never reaching 30 fps, `play.sh --check` prints `PLAY REJECT
    wayland window ...` and exits 2, and the stub's pid is still alive afterwards ... After the fix: gone
    within DRAFT-play-term-s." The stub prints `FPS: 10` every second; after the window timeout play.sh
    rejects with exit 2 (green half: the leak path was reached); the stub must be gone within TERM_S."""
    env, tree = rig.make(wayland=True, x_window=False, fps=10)
    r = rig.play(env, tree, "--scene", SCENE, "--check", timeout=200)
    assert r.returncode == 2, r.stdout + r.stderr
    assert any(l.startswith("PLAY REJECT wayland window") for l in r.stdout.splitlines()), r.stdout
    pid = rig.stub_pid()
    assert rig.gone(pid, TERM_S) is not None, \
        f"Finding 1: stub {pid} still alive {TERM_S}s after `PLAY REJECT wayland window` (exit 2)"


def test_x11_no_window_reject_leaves_no_game(rig):
    """H-084 Finding 1 / Tests: "Same for the X11 variant (`PLAY REJECT no window`)." No Wayland display,
    xdotool finds no window; play.sh prints `PLAY REJECT no window after ...` and exits 2 (green half); the
    stub must be gone within TERM_S."""
    env, tree = rig.make(wayland=False, x_window=False)
    r = rig.play(env, tree, "--scene", SCENE, "--check", timeout=200)
    assert r.returncode == 2, r.stdout + r.stderr
    assert any(l.startswith("PLAY REJECT no window") for l in r.stdout.splitlines()), r.stdout
    pid = rig.stub_pid()
    assert rig.gone(pid, TERM_S) is not None, \
        f"Finding 1: stub {pid} still alive {TERM_S}s after `PLAY REJECT no window` (exit 2)"


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGINT], ids=["TERM", "INT"])
def test_signal_during_window_wait_leaves_no_game(rig, sig):
    """H-084 Finding 1 / Tests: "`play.sh` sent `TERM` while waiting for the window leaves the stub alive;
    after the fix the stub is gone." Change 1: a trap "on `EXIT`, `INT` and `TERM`". play.sh runs in its own
    process group (as under `proc.py start`); the group gets the signal (the reaper at its TTL kills the
    group; Ctrl-C reaches the foreground group), the game is in its own `setsid` group and does not. The stub
    never reaches 30 fps, so play.sh is in the window wait when the signal lands."""
    env, tree = rig.make(wayland=True, x_window=False, fps=10)
    p = rig.play_bg(env, tree, "--scene", SCENE, "--check")
    assert wait_for(rig.base / "stub-ready", 40), "the stub never came up: " + rig.out()
    assert p.poll() is None, "play.sh ended before the signal: " + rig.out()
    pid = rig.stub_pid()
    assert rig.alive(pid)
    os.killpg(p.pid, sig)
    try:
        p.wait(timeout=PATIENCE_S)
    except subprocess.TimeoutExpired:
        pytest.fail(f"play.sh did not end within {PATIENCE_S}s of {sig.name}: " + rig.out())
    assert rig.gone(pid, TERM_S) is not None, \
        f"Finding 1: stub {pid} still alive {TERM_S}s after play.sh ended on {sig.name}"


def test_term_ignoring_game_is_killed_after_the_term_step(rig):
    """H-084 Tests: "a stub that ignores `TERM` is still gone after the `KILL` step", through play.sh.
    Change 1: "signals the game's process group (`kill -TERM -- -$gpid`, then `KILL` after DRAFT-play-term-s
    5 s if it is still there)". The stub records every TERM it gets and keeps running; play.sh's group is
    TERMed during the window wait. The stub must have been sent TERM first and must be gone after KILL.
    (Red on main: nothing signals it. The green detector control for this is
    test_control_detector_sees_a_term_ignoring_stub_survive_term_and_die_on_kill.)"""
    env, tree = rig.make(wayland=True, x_window=False, fps=10, extra_env={"STUB_IGNORE_TERM": "1"})
    p = rig.play_bg(env, tree, "--scene", SCENE, "--check")
    assert wait_for(rig.base / "stub-ready", 40), "the stub never came up: " + rig.out()
    pid = rig.stub_pid()
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=PATIENCE_S)
    except subprocess.TimeoutExpired:
        pytest.fail(f"play.sh did not end within {PATIENCE_S}s of TERM: " + rig.out())
    assert rig.gone(pid, PATIENCE_S) is not None, \
        f"Finding 1: TERM-ignoring stub {pid} still alive {PATIENCE_S}s after play.sh ended (no KILL step)"
    assert (rig.base / "stub-term").exists(), "the stub was killed without ever being sent TERM first"


# ---------------------------------------------------------------------------------------------
# RED on main: Scene-env (Findings 4; Change 2)
# ---------------------------------------------------------------------------------------------

def scene_env_story(line):
    return {"T-084": f"# T-084\nScene: {SCENE}\n{line}\n"}


def test_scene_env_missing_file_rejects_before_the_build(rig):
    """H-084 Finding 4 / Tests: "a story file with `Scene-env: OM_FIGHT=docs/none.fight.json` (file absent)
    makes `play.sh --story X --check` exit 5 with `PLAY REJECT scene input missing OM_FIGHT`". Change 2:
    "prints `PLAY REJECT scene input missing <KEY> <path>` and exits 5 before the build." The line is on
    stdout like every `PLAY REJECT`; the build stub leaves no mark and the game is never launched."""
    env, tree = rig.make(wayland=True, x_window=False, stories=scene_env_story("Scene-env: OM_FIGHT=docs/none.fight.json"))
    r = rig.play(env, tree, "--story", "T-084", "--check")
    assert r.returncode == 5, f"Finding 4: exit {r.returncode}, want 5\n" + r.stdout + r.stderr
    lines = [l for l in r.stdout.splitlines() if l.startswith("PLAY REJECT scene input missing OM_FIGHT")]
    assert lines and "none.fight.json" in lines[0], r.stdout
    assert not (rig.base / "build-mark").exists(), "the build ran before the missing input was caught"
    assert not rig.pids(), "the game was launched with its input missing"


def test_scene_env_present_file_reaches_the_game_as_an_absolute_path_in_the_tree(rig):
    """H-084 Finding 4 / Tests: "with the file present the stub Godot's environment holds
    `OM_FIGHT=<absolute path in the tree>`". Change 2: "A value that is a path in the tree is resolved
    against the tree before launch. The game starts with those variables set." The stub records its
    environment at launch: OM_FIGHT is absolute, ends with the story's path, lies under the tree play.sh
    was given or its scratch clone, and names a file that existed when the game started."""
    env, tree = rig.make(wayland=True, x_window=False, stories=scene_env_story("Scene-env: OM_FIGHT=docs/h084.fight.json"),
                         files={"docs/h084.fight.json": "{}\n"})
    r = rig.play(env, tree, "--story", "T-084", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.loads((rig.base / "stub-env.json").read_text())
    got = rec["env"].get("OM_FIGHT")
    assert got, "Finding 4: the game started without OM_FIGHT in its environment"
    assert os.path.isabs(got) and got.endswith("docs/h084.fight.json"), got
    assert got.startswith((str(tree) + "/", str(scratch_of(r.stdout)) + "/")), (got, str(tree))
    assert rec["OM_FIGHT_exists"], f"OM_FIGHT={got} named no file when the game started"


def test_scene_env_two_pairs_both_reach_the_game(rig):
    """H-084 Change 2: Machine line `Scene-env: KEY=VALUE [KEY=VALUE ...]` and "The game starts with those
    variables set." Two pairs on the line, one a tree path and one a plain value: both are in the game's
    environment. (How a path value is told from a plain one is not stated; the plain value is `7`.)"""
    env, tree = rig.make(wayland=True, x_window=False,
                         stories=scene_env_story("Scene-env: OM_FIGHT=docs/h084.fight.json OM_SEED=7"),
                         files={"docs/h084.fight.json": "{}\n"})
    r = rig.play(env, tree, "--story", "T-084", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    got = json.loads((rig.base / "stub-env.json").read_text())["env"]
    assert got.get("OM_SEED") == "7", f"Finding 4: OM_SEED in the game's environment is {got.get('OM_SEED')!r}"
    assert got.get("OM_FIGHT", "").endswith("docs/h084.fight.json"), got.get("OM_FIGHT")
