"""Shared TCP client + Godot launcher for the desktop QA daemon protocol
(autoload/qa_daemon.gd's --qa-port mode). Mirrors the proven pattern in
scripts/qa_harness.sh's cmd_liveness (private Xvfb, software GL, never the
live seat's DISPLAY, cwd in a scratch dir outside the checkout). Shared by
tests/qa/desktop/test_flow_spine.py and any later desktop QA test under
tests/qa/desktop/ (fenced -- see tests/qa/README.md).
"""
from __future__ import annotations

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


def pick_free_port(lo: int = 47500, hi: int = 47599) -> int:
    for _ in range(50):
        port = random.randint(lo, hi)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            s.close()
    raise RuntimeError("no free port found in range %d-%d" % (lo, hi))


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

    def wait_for_port(self, timeout: float = 60.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    "godot exited before qa-port %d opened (rc=%s)\n--- stderr tail ---\n%s"
                    % (self.qa_port, self.proc.returncode, self.stderr_tail())
                )
            try:
                with socket.create_connection(("127.0.0.1", self.qa_port), timeout=1):
                    return
            except OSError:
                time.sleep(0.25)
        raise TimeoutError(
            "qa-port %d never opened within %ss\n--- stderr tail ---\n%s"
            % (self.qa_port, timeout, self.stderr_tail())
        )

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
