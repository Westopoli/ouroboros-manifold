# spec: docs/northstar/ROADMAP.md (mac check; bug and harness work, not a story), plan ~/.claude/plans/develop-a-plan-to-shimmering-sparkle.md
"""`scripts/play_mac.sh`: the Mac's twin of `scripts/play.sh` (boot the beta windowed, check it over the QA port, capture the screen, pass or red).

This is bug and harness work, so no `S-###` applies; the requirement is Westley's, 2026-11-06: the beta must run and be checked on his Mac with the
same vocabulary and exit codes as `scripts/play.sh` ("PLAY window", "PLAY scene ... reached", "PLAY proof", "PLAY REJECT ...", exit 0, 1, 2, 3, 4, 64)
and the same console patterns as docs/method/story_loop.md step 5 (`SCRIPT ERROR`, `ERROR:`, `Parser Error`). Contract of this file (decided by the
plan, not by the tests): exit 3 covers a wrong scene and a console error; exit 2 a window that never comes up; exit 1 a failed setup; exit 4 a failed
capture; exit 64 an unknown argument. Not pinned: the wording after the prefix of a REJECT line, the order of other output lines, whether a dry run
prints anything beyond its three lines' prefixes, the name of the line that carries the log path.

Nothing here runs a real Godot, a Mac or the screen. Each case builds a SCRATCH TREE (`<tmp>/tree/{scripts,project.godot}`), copies the real
`scripts/play_mac.sh` in, and stubs everything it calls, as tests/method/test_setup_editor.py's `DarwinRig` does (rig copied, not imported: that file
is not a package): a `uname` that answers Darwin, a PATH made of the stub bin plus symlinks to the ordinary tools (no real `godot`, `screencapture`,
`xdotool` or `flock` can leak in), the Godot stub reached through `OM_GODOT_APP`, a sibling `scripts/setup_editor.sh` that logs and prints
`EDITOR READY`, and a `screencapture` that writes one byte to its last argument. The Godot stub parses `--qa-port N`, prints `FPS: 60` once a second
and answers `["state"]` with `{"ok":true,"result":{"scene":"<OM_STUB_SCENE>"}}` on that port (a python3 process, so killing the launched pid kills it).
HOME is `<tmp>/home`. `OM_PLAY_WINDOW_S` and `OM_PLAY_SETTLE_S` are the script's two seams that keep a case to seconds.

Premises read from the repo, not guessed: project.godot has `run/main_scene="res://scenes/privacy_modal/privacy_modal.tscn"`; play.sh prints
`PLAY window <t>s <driver>`, `PLAY scene <scene> reached`, `PLAY REJECT scene <got> wanted <want>`, `PLAY proof <png> <method>`; scripts/replay.sh:45-46 prints
a dry run with `printf %q`.

Red today for the missing-feature reason: `scripts/play_mac.sh` does not exist. The control case needs no script and is green.
"""
import os
import re
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "play_mac.sh"
MAIN_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
OTHER_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
TOOLS = ("bash", "env", "dirname", "basename", "find", "cp", "mv", "mkdir", "rm", "ls", "head", "tail", "cat", "cut", "tr", "sed", "grep",
         "awk", "mktemp", "chmod", "touch", "sort", "uniq", "wc", "readlink", "pwd", "sleep", "nohup", "date", "python3", "id", "true", "false")

# The Godot stub: a python3 process. Writes its pid, prints OM_STUB_CONSOLE, serves ["state"] on --qa-port (unless OM_STUB_NOQA), prints FPS: 60 every second.
STUB_PY = r'''import json, os, socket, sys, threading, time
a = sys.argv[1:]
open(os.environ["OM_STUB_PID"], "w").write(str(os.getpid()))
for line in os.environ.get("OM_STUB_CONSOLE", "").splitlines():
    print(line, flush=True)
if "--qa-port" in a and not os.environ.get("OM_STUB_NOQA"):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", int(a[a.index("--qa-port") + 1]))); s.listen(5)
    def serve():
        while True:
            c, _ = s.accept(); c.recv(65536)
            c.sendall((json.dumps({"ok": True, "result": {"scene": os.environ["OM_STUB_SCENE"]}}) + "\n").encode()); c.close()
    threading.Thread(target=serve, daemon=True).start()
while True:
    print("FPS: 60", flush=True); time.sleep(1)
'''


def write_exec(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class MacRig:
    """A scratch tree with the real play_mac.sh (when it exists) and a Mac's worth of stubs."""

    def __init__(self, setup="ready", scene=MAIN_SCENE, console="", noqa=False, capture_ok=True):
        self.base = Path(tempfile.mkdtemp(prefix="mac-check-play-")).resolve()
        self.tree, self.home, self.bin, self.tools = (self.base / n for n in ("tree", "home", "bin", "tools"))
        self.log = self.base / "calls.log"
        self.pidfile = self.base / "stub.pid"
        self.app = self.base / "apps" / "Godot.app" / "Contents" / "MacOS" / "Godot"
        self.log.write_text("")
        self.home.mkdir()
        (self.tree / "scripts").mkdir(parents=True)
        (self.tree / "project.godot").write_text(f'config_version=5\n\n[application]\n\nrun/main_scene="{MAIN_SCENE}"\n')
        if SCRIPT.is_file():
            shutil.copy2(SCRIPT, self.tree / "scripts" / "play_mac.sh")
        self.tools.mkdir()
        for name in TOOLS:
            src = shutil.which(name)
            if src:
                (self.tools / name).symlink_to(src)
        write_exec(self.bin / "uname", 'case "$1" in -m) echo arm64;; *) echo Darwin;; esac\n')
        body = {"ready": 'echo "setup" >> {log}; echo "chatter"; echo "EDITOR READY $(pwd)"\n',
                "failed": 'echo "setup" >> {log}; echo "EDITOR SETUP FAILED pipe"; exit 1\n',
                "silent": 'echo "setup" >> {log}; echo "chatter"\n'}[setup]
        write_exec(self.tree / "scripts" / "setup_editor.sh", body.format(log=self.log))
        write_exec(self.bin / "screencapture", f'echo "screencapture $*" >> {self.log}\n'
                   + ('for last; do :; done; printf x > "$last"\n' if capture_ok else "exit 1\n"))
        (self.base / "stub_godot.py").write_text(STUB_PY)
        write_exec(self.app, f'echo "godot-stub $*" >> {self.log}\nexec python3 {self.base / "stub_godot.py"} "$@"\n')
        self.env = {"HOME": str(self.home), "PATH": f"{self.bin}:{self.tools}", "OM_GODOT_APP": str(self.app),
                    "OM_STUB_PID": str(self.pidfile), "OM_STUB_SCENE": scene, "OM_STUB_CONSOLE": console,
                    "OM_PLAY_WINDOW_S": "8", "OM_PLAY_SETTLE_S": "1"}
        if noqa:
            self.env["OM_STUB_NOQA"] = "1"

    def run(self, *args, **env):
        assert SCRIPT.is_file(), f"{SCRIPT} does not exist"
        r = subprocess.run(["bash", str(self.tree / "scripts" / "play_mac.sh"), *args], cwd=str(self.tree), env={**self.env, **env},
                           capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL)
        r.lines = (r.stdout + r.stderr).splitlines()
        return r

    def calls(self):
        return self.log.read_text().splitlines()

    def stub_pid(self):
        return int(self.pidfile.read_text()) if self.pidfile.is_file() else None

    def stub_alive(self, wait=0.0):
        """True while the launched stub process exists; with `wait`, polls that long for it to go."""
        pid = self.stub_pid()
        if pid is None:
            return False
        end = time.time() + wait
        while True:
            try:
                os.kill(pid, 0)
                # a zombie child of a vanished parent still answers kill 0 until reaped; /proc state tells
                state = Path(f"/proc/{pid}/stat")
                if state.is_file() and state.read_text().rsplit(")", 1)[1].split()[0] == "Z":
                    return False
            except ProcessLookupError:
                return False
            if time.time() >= end:
                return True
            time.sleep(0.1)

    def close(self):
        pid = self.stub_pid()
        if pid is not None:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        shutil.rmtree(self.base, ignore_errors=True)


# ---------------------------------------------------------------- positive control (green today)

def test_control_rig():
    """Positive control for every case below: without the script, the stubs answer as the cases assume. `uname -s` prints Darwin and `uname -m` arm64;
    the setup stub logs and prints `EDITOR READY` last (and the failed and silent variants do not); the screencapture stub writes a byte to its last
    argument; the Godot stub, started the way the script starts it, prints the console lines and `FPS: 60`, answers `["state"]` on its `--qa-port` with
    the scene it was told (and, with OM_STUB_NOQA, does not), and dies when killed. A red case below is the missing script, not a broken rig."""
    r = MacRig(console="SCRIPT ERROR: planted")
    try:
        sh = lambda *a, **kw: subprocess.run(list(a), env=r.env, cwd=str(r.tree), capture_output=True, text=True, timeout=30, **kw)
        assert sh("uname", "-s").stdout.strip() == "Darwin" and sh("uname", "-m").stdout.strip() == "arm64"
        for leaked in ("godot", "godot.real", "xdotool", "flock", "setsid", "timeout"):
            assert sh("bash", "-c", f"command -v {leaked}").returncode != 0, f"a real {leaked} leaked onto the rig PATH"
        assert sh("scripts/setup_editor.sh").stdout.splitlines()[-1] == f"EDITOR READY {r.tree}"
        png = r.base / "x.png"
        assert sh("screencapture", "-x", str(png)).returncode == 0 and png.read_bytes() == b"x"
        port = free_port()
        out = r.base / "out.log"
        with open(out, "w") as fh:
            game = subprocess.Popen([str(r.app), "--path", str(r.tree), "--", "--qa-port", str(port)], env=r.env, stdout=fh, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    c = socket.create_connection(("127.0.0.1", port), timeout=2)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise AssertionError("the Godot stub never listened")
            c.sendall(b'["state"]\n')
            assert c.recv(65536) == b'{"ok": true, "result": {"scene": "%s"}}\n' % MAIN_SCENE.encode()
            c.close()
            assert r.stub_pid() == game.pid, "the stub must exec, so the launched pid is the python process"
            time.sleep(0.5)
            text = out.read_text()
            assert "SCRIPT ERROR: planted" in text and "FPS: 60" in text, text
        finally:
            game.kill()
            game.wait()
        assert not r.stub_alive()
        assert r.calls() == ["setup", "screencapture -x " + str(png), f"godot-stub --path {r.tree} -- --qa-port {port}"], r.calls()
    finally:
        r.close()
    n = MacRig(noqa=True, setup="silent")
    try:
        port = free_port()
        game = subprocess.Popen([str(n.app), "--qa-port", str(port)], env=n.env, stdout=subprocess.DEVNULL)
        try:
            time.sleep(1.0)
            assert socket.socket().connect_ex(("127.0.0.1", port)) != 0, "OM_STUB_NOQA must leave the port closed"
        finally:
            game.kill()
            game.wait()
        assert subprocess.run(["scripts/setup_editor.sh"], cwd=str(n.tree), env=n.env, capture_output=True, text=True).stdout.splitlines()[-1] == "chatter"
    finally:
        n.close()


# ---------------------------------------------------------------- the script (red today: it does not exist)

def test_dry_run_prints_three_lines_and_runs_nothing():
    """Plan step 9 / commit 3: `--dry-run` prints `setup:`, `launch:` and `capture:` (as scripts/replay.sh:45-46 prints a dry run) and runs nothing.
    `launch:` carries the Godot app path (found through OM_GODOT_APP), `--windowed --resolution 1919x1080` and `--qa-port`; the three lines come in that
    order; exit 0; the call log is empty (no setup, no Godot, no screencapture), no game is started and no `.play.log` or `proof.png` appears."""
    r = MacRig()
    try:
        p = r.run("--dry-run")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        heads = [l.split(":", 1)[0] for l in p.stdout.splitlines() if re.match(r"(setup|launch|capture):", l)]
        assert heads == ["setup", "launch", "capture"], p.stdout
        launch = next(l for l in p.stdout.splitlines() if l.startswith("launch:"))
        assert str(r.app) in launch and "--windowed --resolution 1919x1080" in launch and "--qa-port" in launch, launch
        assert r.calls() == [], r.calls()
        assert r.stub_pid() is None
        assert not (r.tree / ".play.log").exists() and not (r.tree / "proof.png").exists()
    finally:
        r.close()


def test_check_pass_prints_window_scene_proof_exit_0():
    """Plan step 8 / commit 3: `--check` on a healthy stub game prints `PLAY window <t>s mac`, `PLAY scene <main scene> reached` (the scene the QA port
    reports equals project.godot run/main_scene) and `PLAY proof <tree>/proof.png screencapture`, in that order, and exits 0. proof.png exists (the
    screencapture stub wrote it), setup ran once, `screencapture -x` was called once, and the game was killed. Control: the clean console has no REJECT."""
    r = MacRig()
    try:
        p = r.run("--check")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        out = p.stdout.splitlines()
        win = [i for i, l in enumerate(out) if re.fullmatch(r"PLAY window \d+s mac", l)]
        scene = [i for i, l in enumerate(out) if l == f"PLAY scene {MAIN_SCENE} reached"]
        proof = [i for i, l in enumerate(out) if l == f"PLAY proof {r.tree}/proof.png screencapture"]
        assert win and scene and proof and win[0] < scene[0] < proof[0], out
        assert not any("REJECT" in l for l in p.lines), p.lines
        assert (r.tree / "proof.png").is_file()
        assert r.calls().count("setup") == 1 and sum(c.startswith("screencapture -x") for c in r.calls()) == 1, r.calls()
        assert any(c.startswith("godot-stub") and "--qa-port" in c and "--windowed" in c for c in r.calls()), r.calls()
        assert not r.stub_alive(wait=3), "--check must kill the game it started"
    finally:
        r.close()


def test_wrong_scene_rejects_3_and_scene_argument_then_passes():
    """Plan step 8: the scene the QA port reports must equal `--scene` or run/main_scene, else `PLAY REJECT scene <got> wanted <want>` and exit 3 (as
    play.sh:155-157); the game is killed and nothing is captured. Control in the same case: with `--scene <that scene>` the same stub passes (exit 0,
    `PLAY scene <that scene> reached`) and Godot was launched with the scene path."""
    r = MacRig(scene=OTHER_SCENE)
    try:
        p = r.run("--check")
        assert p.returncode == 3, (p.returncode, p.stdout, p.stderr)
        assert any(l.startswith("PLAY REJECT scene") and OTHER_SCENE in l and MAIN_SCENE in l for l in p.lines), p.lines
        assert not any(c.startswith("screencapture") for c in r.calls()), r.calls()
        assert not (r.tree / "proof.png").exists()
        assert not r.stub_alive(wait=3)
        q = r.run("--check", "--scene", OTHER_SCENE)
        assert q.returncode == 0, (q.returncode, q.stdout, q.stderr)
        assert f"PLAY scene {OTHER_SCENE} reached" in q.lines, q.lines
        assert any(c.startswith("godot-stub") and OTHER_SCENE in c.split("--qa-port")[0] for c in r.calls()), r.calls()
    finally:
        r.close()


def test_error_line_in_log_rejects_console():
    """Plan step 8 / story_loop step 5: after the proof, the game's console is grepped for `SCRIPT ERROR|ERROR:|Parser Error`; a hit prints
    `PLAY REJECT console <first matching line>` and exits 3 (folded into the scene code). Three planted lines, one per pattern, each rejects and names
    its line. CONTROL (GodotSteam-less opens print benign `ERROR` lines, see scripts/setup_editor.sh:61): a bare `ERROR` word without the colon
    does not reject, and neither does a clean console (test_check_pass...)."""
    for planted in ("SCRIPT ERROR: x", "ERROR: x", "Parser Error: x"):
        r = MacRig(console=planted)
        try:
            p = r.run("--check")
            assert p.returncode == 3, (planted, p.returncode, p.stdout, p.stderr)
            assert any(l.startswith("PLAY REJECT console") and planted in l for l in p.lines), (planted, p.lines)
        finally:
            r.close()
    ok = MacRig(console="GodotSteam ERROR benign: library not found\nWARNING: something harmless")
    try:
        p = ok.run("--check")
        assert p.returncode == 0, ("a bare ERROR word must not reject", p.returncode, p.stdout, p.stderr)
        assert not any("REJECT" in l for l in p.lines), p.lines
    finally:
        ok.close()


def test_setup_failure_rejects_1():
    """Plan step 3: scripts/setup_editor.sh is run first and its last line must be `EDITOR READY`; otherwise `PLAY REJECT setup` and exit 1, and no game
    is launched. Both failures: setup exiting 1 with `EDITOR SETUP FAILED pipe`, and setup exiting 0 whose last line is something else."""
    for mode in ("failed", "silent"):
        r = MacRig(setup=mode)
        try:
            p = r.run("--check")
            assert p.returncode == 1, (mode, p.returncode, p.stdout, p.stderr)
            assert any(l.startswith("PLAY REJECT setup") for l in p.lines), (mode, p.lines)
            assert r.calls() == ["setup"], (mode, r.calls())
        finally:
            r.close()


def test_no_qa_answer_rejects_2():
    """Plan step 6: with `--check`, a game whose QA port never answers (FPS lines still print) is a window that did not come up: after
    OM_PLAY_WINDOW_S the script prints a `PLAY REJECT` line naming the window and exits 2 (play.sh:127-136 wording `... window: ...`)."""
    r = MacRig(noqa=True)
    try:
        t0 = time.time()
        p = r.run("--check", OM_PLAY_WINDOW_S="3")
        assert p.returncode == 2, (p.returncode, p.stdout, p.stderr)
        assert any(l.startswith("PLAY REJECT") and "window" in l for l in p.lines), p.lines
        assert not any(l.startswith("PLAY window") for l in p.lines), p.lines
        assert time.time() - t0 < 30, "OM_PLAY_WINDOW_S must bound the wait"
    finally:
        r.close()


def test_capture_failure_rejects_4():
    """Plan step 8: a screencapture that fails (or writes no file) prints `PLAY REJECT` naming the proof and exits 4; the game is still killed.
    Control: the passing case above shows the same rig with a working screencapture exits 0."""
    r = MacRig(capture_ok=False)
    try:
        p = r.run("--check")
        assert p.returncode == 4, (p.returncode, p.stdout, p.stderr)
        assert any(l.startswith("PLAY REJECT") and "proof" in l for l in p.lines), p.lines
        assert not any(l.startswith("PLAY proof") for l in p.lines), p.lines
        assert not r.stub_alive(wait=3)
    finally:
        r.close()


def test_unknown_arg_64():
    """Plan step 1: an unknown argument exits 64 (as play.sh:49-56) before anything runs: no setup, no Godot. Control: `--dry-run` with a known
    argument exits 0 (the dry-run case above)."""
    r = MacRig()
    try:
        p = r.run("--bogus")
        assert p.returncode == 64, (p.returncode, p.stdout, p.stderr)
        assert any("unknown argument" in l and "--bogus" in l for l in p.lines), p.lines
        assert r.calls() == [], r.calls()
    finally:
        r.close()


def test_default_leaves_game_running():
    """Plan step 7 (Westley's playtest mode): without `--check` the script prints `PLAY window ...`, names the game's log (`.play.log`) and exits 0
    leaving the game running; it does not capture, check the scene or print a REJECT. The log it names holds the game's console. The rig's close()
    kills the leftover stub."""
    r = MacRig()
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert any(re.fullmatch(r"PLAY window \d+s mac", l) for l in p.lines), p.lines
        assert any(".play.log" in l for l in p.lines), p.lines
        assert r.stub_alive(), "the game must still be running after the script exits"
        assert not any(c.startswith("screencapture") for c in r.calls()), r.calls()
        assert not any("REJECT" in l or l.startswith("PLAY scene") or l.startswith("PLAY proof") for l in p.lines), p.lines
        assert "FPS: 60" in (r.tree / ".play.log").read_text()
    finally:
        r.close()
