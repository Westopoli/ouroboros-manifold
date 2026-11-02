"""Shared TCP client + Godot launcher for the desktop QA daemon protocol
(autoload/qa_daemon.gd's --qa-port mode). Mirrors the proven pattern in
scripts/qa_harness.sh's cmd_liveness (private Xvfb, software GL, never the
live seat's DISPLAY, cwd in a scratch dir outside the checkout). Shared by
tests/qa/desktop/test_flow_spine.py and any later desktop QA test under
tests/qa/desktop/ (fenced -- see tests/qa/README.md).
"""
from __future__ import annotations

import atexit
import fcntl
import json
import os
import random
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# project.godot: config/use_custom_user_dir=true, config/custom_user_dir_name="data"
# -- user:// resolves to <XDG_DATA_HOME>/data, so the user dir is computed PER
# INSTANCE at construction (GodotGame.user_dir, DaemonClient.user_dir) from the
# child environment godot_env() builds: the caller's XDG_DATA_HOME when it has a
# non-empty one, else <scratch>/xdg. Never at import, never the machine's
# ~/.local/share/data (FINDING-ambient-user-dir). scenes/privacy_modal/
# privacy_modal.gd's FLAG_PATH ("user://privacy_accepted") lives there.
# See also: scripts/specfactory/merge_gate.sh (the gate exports the same variable)


def godot_env(base_env: dict, scratch: Path, save_dir: Path | None) -> dict:
    """The whole child environment of the game: a copy of base_env without the
    seat's display variables, OM_SAVE_DIR (when save_dir is given), software GL,
    and XDG_DATA_HOME = <scratch>/xdg unless base_env already has a non-empty one.
    Pure: writes nothing."""
    env = dict(base_env)
    for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
        env.pop(var, None)
    if save_dir is not None:
        env["OM_SAVE_DIR"] = str(save_dir)
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env["GALLIUM_DRIVER"] = "llvmpipe"
    if not env.get("XDG_DATA_HOME"):
        env["XDG_DATA_HOME"] = str(scratch / "xdg")
    return env


def _user_dir_for(env: dict, scratch: Path) -> Path:
    xdg = Path(env["XDG_DATA_HOME"])
    if xdg == scratch / "xdg":
        xdg.mkdir(parents=True, exist_ok=True)
    return xdg / "data"


def find_godot() -> str:
    for candidate in ("godot", os.path.expanduser("~/.local/bin/godot")):
        if shutil.which(candidate):
            return candidate
        if os.path.isabs(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("godot binary not found on PATH or at ~/.local/bin/godot")


_PORT_LOCKS: dict[int, int] = {}  # port -> open flock fd, held until release_port_lock or process exit
_PORT_RANGES: dict[int, tuple[int, int]] = {}  # port -> the (lo, hi) its pick_free_port call was given


def _port_lock_dir() -> Path:
    # The push root the sibling scripts use (merge_gate.sh: ${HOME}/Projects/om-push).
    return Path(os.environ.get("HOME") or str(Path.home())) / "Projects" / "om-push" / "tmp" / "qa_ports"


def release_port_lock(port: int) -> None:
    fd = _PORT_LOCKS.pop(port, None)
    if fd is not None:
        os.close(fd)


def pick_free_port(lo: int = 47500, hi: int = 47599) -> int:
    # See also: docs/stories/H-066.md (two concurrent runs picked the same port in the
    # bind-close-listen gap; a per-port flock held for the life of the process fixes the pick)
    ports = list(range(lo, hi + 1))
    random.shuffle(ports)
    lock_dir = _port_lock_dir()
    lock_dir.mkdir(parents=True, exist_ok=True)
    for port in ports:
        fd = os.open(str(lock_dir / ("%d.lock" % port)), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            continue
        if not _port_bindable(port):
            os.close(fd)
            continue
        _PORT_LOCKS[port] = fd
        _PORT_RANGES[port] = (lo, hi)
        return port
    raise RuntimeError("QA PORT REFUSED no free port in range %d-%d" % (lo, hi))


def _port_bindable(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _listener_pids(port: int) -> set[int]:
    """Pids holding a LISTEN socket on :port, from /proc/net/tcp{,6} (state 0A) and /proc/<pid>/fd."""
    inodes = set()
    for name in ("tcp", "tcp6"):
        try:
            lines = Path("/proc/net/" + name).read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            f = line.split()
            if len(f) > 9 and f[3] == "0A" and int(f[1].rsplit(":", 1)[1], 16) == port:
                inodes.add(f[9])
    pids = set()
    want = {"socket:[%s]" % i for i in inodes}
    if not want:
        return pids
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            for fd in (d / "fd").iterdir():
                if os.readlink(str(fd)) in want:
                    pids.add(int(d.name))
                    break
        except OSError:
            continue
    return pids


class _PortRetry(Exception):
    """wait_for_port: this launch is unusable (early exit, cannot listen, foreign listener)."""


class DaemonClient:
    """One TCP round trip per call, matching autoload/qa_daemon.gd's
    newline-delimited-JSON protocol (see its _handle_line/_dispatch)."""

    def __init__(self, port: int, user_dir: Path, timeout: float = 10.0):
        self.port = port
        self.timeout = timeout
        self.user_dir = user_dir

    def call(self, verb: str, *args) -> dict:
        with socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout) as sock:
            sock.sendall((json.dumps([verb, *args]) + "\n").encode())
            sock.settimeout(self.timeout)
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
        if not buf:
            raise ConnectionError("daemon closed connection with no response to %r" % (verb,))
        return json.loads(buf.decode())

    def state(self) -> dict:
        return self.call("state")

    def tree(self) -> dict:
        return self.call("tree")

    def click(self, x: float, y: float, button: int = 1) -> dict:
        # autoload/qa_daemon.gd's _dispatch_input "click" sub-verb; MOUSE_BUTTON_LEFT == 1.
        return self.call("input", "click", x, y, button)

    def screenshot(self, name: str) -> dict:
        # qa_daemon never creates user://qa in --qa-port mode (only qa_driver.gd:30 under
        # --qa-script does); FU: GD-side fix in the lane K harness.
        (self.user_dir / "qa").mkdir(parents=True, exist_ok=True)
        return self.call("screenshot", name)


class GodotGame:
    """Launches the real game (project.godot's run/main_scene, no scene
    argument) under Xvfb with --qa-port/--seed. One instance per test
    module (see the `game` fixture in test_flow_spine.py)."""

    def __init__(self, qa_port: int, seed: int = 1, resolution: str = "1280x720",
                 reset_privacy_flag: bool = True, extra_args: list[str] | None = None,
                 renderer: str | None = None):
        self.renderer = os.environ.get("OM_QA_RENDERER") or renderer or "opengl3"
        self.extra_args = list(extra_args or [])
        self.qa_port = qa_port
        self.seed = seed
        self.resolution = resolution
        self.reset_privacy_flag = reset_privacy_flag
        self.scratch = Path(tempfile.mkdtemp(prefix="qa_flow_spine."))
        self.out_dir = self.scratch / "out"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # C1-3: campaign autosaves land here (OM_SAVE_DIR read by c_bridge.saves_dir()),
        # never in the player's real save directory.
        self.save_dir = self.scratch / "saves"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir = _user_dir_for(godot_env(os.environ, self.scratch, self.save_dir), self.scratch)
        self.client = DaemonClient(qa_port, user_dir=self.user_dir)
        self.proc: subprocess.Popen | None = None
        self._stdout_f = None
        self._stderr_f = None
        self._atexit_registered = False

    def write_privacy_flag(self) -> None:
        """Creates user://privacy_accepted the way privacy_modal.gd's
        _on_accept_pressed() does: FileAccess.open(FLAG_PATH, FileAccess.WRITE)
        then close() -- an empty file. Used by S-C8-07 to force the flag-present
        boot path (see reset_privacy_flag=False)."""
        self.user_dir.mkdir(parents=True, exist_ok=True)
        (self.user_dir / "privacy_accepted").touch()

    def godot_args(self, godot: str = "godot") -> list[str]:
        return [
            "xvfb-run", "-a", "-s", "-screen 0 %sx24" % self.resolution,
            godot, "--path", str(REPO_ROOT),
            "--display-driver", "x11", "--rendering-driver", self.renderer,
            "-w", "--position", "0,0", "--resolution", self.resolution,
            "--fixed-fps", "30",
            "--", "--qa-port", str(self.qa_port), "--seed", str(self.seed),
            *self.extra_args,
        ]

    def start(self) -> None:
        # Reproducible bug (see docs/northstar/plans/push/specs/C8.md "Findings"):
        # once user://privacy_accepted exists, loading_screen.gd never leaves
        # loading_screen -- SimBridge's sim_ready fires while SceneRouter is
        # still mid-transition from privacy_modal, go_to() drops the request
        # (_transitioning guard, no retry), and nothing else ever calls
        # go_to() again. Confirmed with a 90s wait; the Accept-button path
        # (flag absent) does not race the same way and reaches main_menu in
        # under a second. Deleting the flag before every launch is this
        # fenced test's own determinism fixture, not a game fix -- S-C8-01
        # drives the real Accept click either way. S-C8-07 sets
        # reset_privacy_flag=False (and writes the flag itself first) to
        # prove the bug rather than dodge it.
        if self.reset_privacy_flag:
            try:
                (self.user_dir / "privacy_accepted").unlink()
            except FileNotFoundError:
                pass

        godot = find_godot()
        env = godot_env(os.environ, self.scratch, self.save_dir)
        cmd = self.godot_args(godot)
        self._stdout_f = open(self.out_dir / "stdout.log", "wb")
        self._stderr_f = open(self.out_dir / "stderr.log", "wb")
        # start_new_session=True puts xvfb-run and the real godot process it
        # execs (a grandchild, so proc.kill() alone never reaches it) in one
        # process group, so stop() can kill the whole tree at once instead
        # of leaking a headless godot behind an already-dead xvfb-run.
        self.proc = subprocess.Popen(
            cmd, cwd=str(self.scratch), env=env,
            stdout=self._stdout_f, stderr=self._stderr_f,
            start_new_session=True,
        )
        # See also: docs/stories/H-068.md part 5 (a fixture whose first state() raised after a
        # good wait left the game running): no game outlives its pytest process.
        if not self._atexit_registered:
            atexit.register(self.stop)
            self._atexit_registered = True

    def wait_for_port(self, timeout: float = 60.0) -> None:
        # See also: docs/stories/H-066.md (parts 2, 3, 5, 6: a foreign listener, a failed
        # listen and a TCP self-connect each made this return ready on a port the game
        # does not own; a failed wait also leaked the game)
        try:
            for attempt in range(1, 4):
                try:
                    self._wait_once(timeout)
                    return
                except _PortRetry as e:
                    self.stop()
                    if attempt == 3:
                        raise RuntimeError("qa-port gave up after 3 launches: %s" % e) from None
                    # See also: docs/stories/H-068.md part 6 (the retry ignored the caller's range)
                    self.qa_port = pick_free_port(*_PORT_RANGES.get(self.qa_port, (47500, 47599)))
                    self.client.port = self.qa_port
                    self.start()
        except BaseException:
            self.stop()
            raise

    def _wait_once(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise _PortRetry("godot exited before qa-port %d opened (rc=%s)\n--- stderr tail ---\n%s"
                                 % (self.qa_port, self.proc.returncode, self.stderr_tail()))
            if "cannot listen" in self.stderr_tail():
                raise _PortRetry("godot could not listen on %d\n--- stderr tail ---\n%s"
                                 % (self.qa_port, self.stderr_tail()))
            try:
                sock = socket.create_connection(("127.0.0.1", self.qa_port), timeout=1)
            except OSError:
                time.sleep(0.25)
                continue
            with sock:
                # A connect to a closed port inside the ephemeral range can connect to itself.
                if sock.getsockname() == sock.getpeername():
                    time.sleep(0.25)
                    continue
            if self._owned_by_game():
                return
            print("QA PORT FOREIGN %d" % self.qa_port, flush=True)
            raise _PortRetry("foreign listener on %d" % self.qa_port)
        raise TimeoutError(
            "qa-port %d never opened within %ss\n--- stderr tail ---\n%s"
            % (self.qa_port, timeout, self.stderr_tail())
        )

    def _owned_by_game(self) -> bool:
        try:
            pgid = os.getpgid(self.proc.pid)
        except ProcessLookupError:
            return False
        for pid in _listener_pids(self.qa_port):
            try:
                if os.getpgid(pid) == pgid:
                    return True
            except ProcessLookupError:
                continue
        return False

    def stderr_tail(self, n: int = 40) -> str:
        path = self.out_dir / "stderr.log"
        if not path.exists():
            return "(no stderr captured)"
        lines = path.read_text(errors="replace").splitlines()
        return "\n".join(lines[-n:])

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                self.proc.wait(timeout=10)
            except Exception:
                pass
        # The lock is released only once the game is gone and the port binds again, so a
        # second run never takes a port this game still holds (H-066 part 4). A foreign
        # holder never frees it: the wait is capped.
        deadline = time.monotonic() + 1.5
        while not _port_bindable(self.qa_port) and time.monotonic() < deadline:
            time.sleep(0.05)
        release_port_lock(self.qa_port)
        for f in (self._stdout_f, self._stderr_f):
            if f is not None:
                f.close()


def control_center(control: dict) -> tuple[float, float]:
    x, y, w, h = control["rect_px"]
    return x + w / 2.0, y + h / 2.0


def find_control(tree_resp: dict, name: str) -> dict | None:
    """Match a control by the last path segment (its node name), e.g.
    "NewGame" matches ".../HBoxContainer/NewGame"."""
    for c in tree_resp.get("result", {}).get("controls", []):
        if c["path"].rsplit("/", 1)[-1] == name:
            return c
    return None


def control_names(tree_resp: dict) -> list[str]:
    return [c["path"].rsplit("/", 1)[-1] for c in tree_resp.get("result", {}).get("controls", [])]


def wait_for(client: DaemonClient, predicate, timeout: float, poll: float = 0.5, label: str = "") -> dict:
    """Polls state() every `poll` seconds until predicate(state_result) is
    true, or raises with the last scene seen plus the current control names
    (S-C8's "fails with the last scene seen plus the tree control names" rule)."""
    deadline = time.monotonic() + timeout
    last_result: dict = {}
    while time.monotonic() < deadline:
        resp = client.state()
        assert resp.get("ok"), "%s: state call failed: %r" % (label, resp)
        last_result = resp["result"]
        if predicate(last_result):
            return last_result
        time.sleep(poll)
    tree_resp = client.tree()
    raise AssertionError(
        "%s: timed out after %ss; last scene seen = %r; controls present = %r"
        % (label, timeout, last_result.get("scene"), control_names(tree_resp))
    )
