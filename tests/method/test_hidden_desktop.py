"""H-085 proof-on-a-hidden-desktop, first piece: the isolation contract of
scripts/specfactory/hidden_desktop.sh (docs/stories/H-085.md, Change 1 and the Measured section).

Story line: "A landing's play proof runs the game on a real GNOME desktop that has no monitor ... and still
catches a game that opens and shows only its splash".

Measured, why isolation is tested: "One measuring run used the real HOME and the real system bus: it
registered with GDM and the real session's services read home directories (nothing changed). Isolation is
therefore a hard requirement below, tested."

Nothing here opens a window, touches a real session, bus, HOME, portal or play.lock, except the one
slow-tier integration test at the end, which boots the hidden desktop under a private HOME, session bus,
system bus and runtime dir (all under a fresh temp dir) and is skipped, with the reason printed, when
`gnome-shell` or software EGL is missing. Every other test runs the script with `--dry-run`, or with stub
`gnome-shell`, `pipewire`, `wireplumber` and `dbus-run-session` programs ahead of the real ones on PATH.
The caller environment of every test is built from scratch (no ambient variable passes through), so even a
script that forgot to isolate has nothing real to hand on. Each test cleans up the processes it started
from Python, by pid, after checking /proc that the pid still carries this test's temp dir.

Reading choices (the story leaves these open; listed in the writer's report):
- `--dry-run` goes first: `hidden_desktop.sh --dry-run <rundir> <WxH>`.
- The dry run prints an environment in no fixed format; the tests read every `KEY=VALUE` word of the
  output (an `env -i KEY=VAL ... cmd` line, `export KEY=VAL` lines and bare `KEY=VAL` lines all count).
- "the real HOME" is the passwd entry of the current uid; "the real /run/user/<uid> bus" is
  `unix:path=/run/user/<uid>/bus`. Both are handed to the script in its caller environment.
- The env file is whichever file the script leaves directly in the rundir that names WAYLAND_DISPLAY; it
  is read by sourcing it in an empty environment (`env -i bash -c '. file; env -0'`).
"""
import json
import os
import pwd
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HIDDEN = ROOT / "scripts" / "specfactory" / "hidden_desktop.sh"
UID = os.getuid()
REAL_HOME = pwd.getpwuid(UID).pw_dir
REAL_BUS = f"unix:path=/run/user/{UID}/bus"
PY3 = "/usr/bin/python3" if Path("/usr/bin/python3").exists() else (shutil.which("python3") or "python3")
MONITOR = "2560x1440"  # H-085 Change 1: "Virtual monitor `2560x1440` (DRAFT-hidden-monitor ...)"
DISPLAY_NAME = "wayland-dark"  # H-085 Measured: `--wayland-display wayland-dark`
# Test patience only, not a product tolerance: how long the harness waits for the stub desktop to say it is up.
PATIENCE_S = 30

STUB_RUNTIME = '''
def note(**kw):
    with open(LOG, "a") as f:
        f.write(json.dumps(dict(kw, stub=NAME, t=time.time(), pid=os.getpid())) + "\\n")
def hold():
    end = time.time() + LIFE
    while time.time() < end and not os.path.exists(STOP):
        time.sleep(0.2)
note(argv=sys.argv[1:], env=dict(os.environ), cwd=os.getcwd())
'''

# gnome-shell: make the Wayland socket named by --wayland-display in XDG_RUNTIME_DIR, then hold.
SHELL_BODY = '''
import socket
argv = sys.argv[1:]
name = argv[argv.index("--wayland-display") + 1] if "--wayland-display" in argv else "wayland-0"
rt = os.environ.get("XDG_RUNTIME_DIR", "")
if rt and os.path.isdir(rt):
    try:
        s = socket.socket(socket.AF_UNIX); s.bind(os.path.join(rt, name)); s.listen(1)
    except OSError as e:
        note(bind_error=str(e))
hold()
'''
HOLD_BODY = "hold()\n"
# dbus-run-session [--] cmd...: run cmd with a private-looking session bus address (nothing is connected to it here).
DBUS_BODY = '''
argv = sys.argv[1:]
cmd = argv[argv.index("--") + 1:] if "--" in argv else [a for a in argv if not a.startswith("-")]
env = dict(os.environ)
env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=" + os.path.join(BASE, "stub-session-bus")
os.execvpe(cmd[0], cmd, env)
'''


def stub_source(name, body, log, stop, base):
    head = (f"#!{PY3}\nimport json, os, sys, time\nLOG, STOP, NAME, BASE = {str(log)!r}, {str(stop)!r}, "
            f"{name!r}, {str(base)!r}\nLIFE = 60\n")
    return head + STUB_RUNTIME + body


def under(value, root):
    """True when `value` is a path strictly below `root` (symlinks resolved on both sides)."""
    v, r = os.path.realpath(value), os.path.realpath(root)
    return v != r and os.path.commonpath([v, r]) == r


def assignments(text):
    """Every KEY=VALUE word in `text`; each line is shell-split, so `env -i A=1 B=2 cmd`, `export A=1` and a bare
    `A=1` line all give A. Later words win."""
    out = {}
    for line in text.splitlines():
        try:
            words = shlex.split(line, comments=False)
        except ValueError:
            words = line.split()
        for w in words:
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", w, re.S)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def env_file_vars(path):
    """The variables a sourced env file sets, read in an otherwise empty environment."""
    r = subprocess.run(["env", "-i", "bash", "-c", '. "$1"; env -0', "_", str(path)],
                       capture_output=True, text=True, timeout=20)
    assert r.returncode == 0, "env file does not source: " + r.stderr
    return dict(w.split("=", 1) for w in r.stdout.split("\0") if "=" in w)


def marked_pids(marker):
    """Pids (other than this process) whose command line or environment names `marker`, a temp dir unique to one test."""
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == os.getpid():
            continue
        try:
            blob = (d / "cmdline").read_bytes() + b"\0" + (d / "environ").read_bytes()
        except OSError:
            continue
        if marker.encode() in blob:
            out.append(int(d.name))
    return out


def reap_marked(marker):
    """Ends every process still carrying `marker`: TERM, a short wait, then KILL; re-checks the marker before each signal
    so a reused pid is never touched. Returns how many it had to end."""
    pids = marked_pids(marker)
    for sig, wait in ((signal.SIGTERM, 3.0), (signal.SIGKILL, 3.0)):
        for pid in marked_pids(marker):
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        t0 = time.time()
        while marked_pids(marker) and time.time() - t0 < wait:
            time.sleep(0.1)
    return len(pids)


class Rig:
    """One test's world: a temp dir with a fake HOME, a TMPDIR, stub programs, and a rundir for the script."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix="h85-")).resolve()
        self.home = self.base / "home"; self.home.mkdir()
        self.tmp = self.base / "tmp"; self.tmp.mkdir()
        self.bin = self.base / "bin"; self.bin.mkdir()
        self.log, self.stop = self.base / "stubs.log", self.base / "stop"
        self.rundir = self.tmp / "hd"; self.rundir.mkdir(mode=0o700)
        self.procs = []
        for name, body in (("gnome-shell", SHELL_BODY), ("pipewire", HOLD_BODY), ("wireplumber", HOLD_BODY),
                           ("dbus-run-session", DBUS_BODY)):
            p = self.bin / name
            p.write_text(stub_source(name, body, self.log, self.stop, self.base)); p.chmod(0o755)
        self.probes = {"OM_LEAK_PROBE": f"leak-probe-{os.getpid()}-a", "SSH_AUTH_SOCK": f"/tmp/leak-probe-{os.getpid()}-b",
                       "DISPLAY": ":77", "WAYLAND_DISPLAY": "wayland-77", "XDG_SESSION_TYPE": "x-probe"}

    def caller_env(self, **extra):
        """A caller environment built from scratch: stubs first on PATH, a fake HOME, TMPDIR under the temp dir, and planted
        probe variables that an isolated script must not pass on. No ambient variable of this process is copied."""
        env = {"PATH": f"{self.bin}:/usr/local/bin:/usr/bin:/bin", "HOME": str(self.home), "TMPDIR": str(self.tmp),
               "LANG": "C.UTF-8", **self.probes}
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def run(self, *args, env=None, timeout=60):
        return subprocess.run(["bash", str(HIDDEN), *args], cwd=ROOT, env=env or self.caller_env(),
                              capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)

    def dry(self, wxh=MONITOR, env=None):
        return self.run("--dry-run", str(self.rundir), wxh, env=env)

    def start(self, env=None):
        out = open(self.base / "hidden-out.txt", "w")
        p = subprocess.Popen(["bash", str(HIDDEN), str(self.rundir), MONITOR], cwd=ROOT, env=env or self.caller_env(),
                             stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        self.procs.append(p)
        return p

    def out(self):
        f = self.base / "hidden-out.txt"
        return f.read_text() if f.exists() else ""

    def wait_up(self, p):
        """Waits for the `HIDDEN up` line, a REJECT line or the script's exit; returns the output text."""
        t0 = time.time()
        while time.time() - t0 < PATIENCE_S:
            text = self.out()
            if "HIDDEN up" in text or "HIDDEN REJECT" in text or p.poll() is not None:
                break
            time.sleep(0.1)
        return self.out()

    def calls(self, name=None):
        rows = [json.loads(l) for l in self.log.read_text().splitlines()] if self.log.exists() else []
        return [r for r in rows if name is None or r["stub"] == name]

    def wait_calls(self, names, within=10):
        t0 = time.time()
        while time.time() - t0 < within:
            if all(self.calls(n) for n in names):
                break
            time.sleep(0.1)

    def teardown(self):
        self.stop.touch()
        for p in self.procs:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except OSError:
                pass
        for p in self.procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except OSError:
                    pass
        reap_marked(str(self.base))
        shutil.rmtree(self.base, ignore_errors=True)


@pytest.fixture
def rig():
    r = Rig()
    try:
        yield r
    finally:
        r.teardown()


@pytest.fixture(scope="module")
def started():
    """One stub-level start of the script, shared by the tests that read what it did: the Popen, its output at the
    `HIDDEN up` line, and the stub calls after the three daemons have been launched."""
    r = Rig()
    try:
        p = r.start()
        text = r.wait_up(p)
        r.wait_calls(("gnome-shell", "pipewire", "wireplumber"))
        yield r, p, text
    finally:
        r.teardown()


# ---------------------------------------------------------------------------------------------
# Controls: green today (no script under test is involved), so a red below means the script is missing or wrong
# ---------------------------------------------------------------------------------------------

def test_control_assignment_reader_reads_env_i_export_and_bare_forms():
    """H-085 Tests, positive control for the dry-run tests below (green today): the reader that the dry-run tests use
    finds KEY=VALUE in an `env -i` line, an `export` line and a bare line, and ignores flags."""
    text = ("env -i HOME=/t/h XDG_DATA_HOME='/t/d x' dbus-run-session -- gnome-shell --virtual-monitor 2560x1440\n"
            "export GSETTINGS_BACKEND=memory\nXDG_RUNTIME_DIR=/t/rt\nlaunch: --resolution=1x1\n")
    got = assignments(text)
    assert got["HOME"] == "/t/h" and got["XDG_DATA_HOME"] == "/t/d x", got
    assert got["GSETTINGS_BACKEND"] == "memory" and got["XDG_RUNTIME_DIR"] == "/t/rt", got
    assert not any(k.startswith("-") for k in got), got


def test_control_caller_environment_carries_nothing_real_and_the_probes(rig):
    """H-085 Measured (isolation is a hard requirement) and Tests, positive control (green today): the caller environment
    every test hands the script holds no `/run/user/` value, a HOME that is not the real HOME, and the planted probe
    variables, so a probe missing from the script's output means the script isolated, not that the test forgot to plant it."""
    env = rig.caller_env()
    assert not any("/run/user/" in v for v in env.values()), env
    assert env["HOME"] != REAL_HOME and under(env["HOME"], rig.base), env["HOME"]
    assert env["OM_LEAK_PROBE"].startswith("leak-probe-") and env["DISPLAY"] == ":77" and env["WAYLAND_DISPLAY"] == "wayland-77"


def test_control_stub_gnome_shell_binds_its_socket_logs_its_env_and_stops(rig):
    """H-085 Tests, positive control for the stub-level tests below (green today): the stub `gnome-shell` run by itself in a
    private runtime dir binds the Wayland socket named by `--wayland-display`, logs its argv and environment, and exits when
    the stop file appears, so a missing `HIDDEN up` below means the script never launched it."""
    rt = rig.base / "rt"; rt.mkdir(mode=0o700)
    env = {"PATH": "/usr/bin:/bin", "XDG_RUNTIME_DIR": str(rt), "HOME": str(rig.home)}
    p = subprocess.Popen([str(rig.bin / "gnome-shell"), "--headless", "--wayland", "--wayland-display", DISPLAY_NAME],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    rig.procs.append(p)
    t0 = time.time()
    while not (rt / DISPLAY_NAME).exists() and time.time() - t0 < 10:
        time.sleep(0.05)
    assert (rt / DISPLAY_NAME).is_socket(), "the stub made no Wayland socket"
    row = rig.calls("gnome-shell")[0]
    assert row["argv"][-2:] == ["--wayland-display", DISPLAY_NAME] and row["env"]["XDG_RUNTIME_DIR"] == str(rt), row
    rig.stop.touch()
    assert p.wait(timeout=10) == 0


def test_control_marker_scan_sees_a_child_by_its_temp_dir_and_reaps_it(rig):
    """H-085 Tests (cleanup is by pid and by temp dir, never by name; green today): a child whose environment names the rig's
    temp dir is found by the scan, a bystander is not, and the reaper ends the child."""
    child = subprocess.Popen(["sleep", "30"], env={"PATH": "/usr/bin:/bin", "X_MARK": str(rig.base)})
    bystander = subprocess.Popen(["sleep", "30"], env={"PATH": "/usr/bin:/bin"})
    try:
        assert child.pid in marked_pids(str(rig.base)) and bystander.pid not in marked_pids(str(rig.base))
        assert reap_marked(str(rig.base)) == 1
        assert child.wait(timeout=5) != 0 and bystander.poll() is None
    finally:
        bystander.terminate(); bystander.wait(timeout=5)
        if child.poll() is None:
            child.kill(); child.wait()


# ---------------------------------------------------------------------------------------------
# Change 1: the script exists and its dry run shows the isolation
# ---------------------------------------------------------------------------------------------

def test_script_exists_and_is_executable():
    """H-085 Change 1: "`scripts/specfactory/hidden_desktop.sh <rundir> <WxH>` starts the hidden desktop" and Files:
    "`scripts/specfactory/hidden_desktop.sh` (new)". The file is there, executable and a bash script (play.sh runs it by path)."""
    assert HIDDEN.is_file(), f"{HIDDEN} does not exist"
    assert os.access(HIDDEN, os.X_OK), "hidden_desktop.sh is not executable"
    assert HIDDEN.read_text().splitlines()[0].startswith("#!") and "bash" in HIDDEN.read_text().splitlines()[0]


def test_dry_run_exits_0_and_starts_nothing(rig):
    """H-085 Tests: "`hidden_desktop.sh --dry-run` prints an environment ..." A dry run exits 0, prints something, and none of
    the stub programs (`gnome-shell`, `pipewire`, `wireplumber`, `dbus-run-session`) is launched."""
    r = rig.dry()
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip(), "the dry run printed nothing"
    assert rig.calls() == [], "the dry run launched: " + repr([c["stub"] for c in rig.calls()])


def test_dry_run_environment_has_no_run_user_bus_and_private_dirs_under_tmpdir(rig):
    """H-085 Tests: "`hidden_desktop.sh --dry-run` prints an environment with no `/run/user/` bus, a `HOME` and `XDG_*` under
    `TMPDIR`". Change 1: "its own `HOME`, `XDG_RUNTIME_DIR`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME` under
    `TMPDIR`". No `/run/user/` anywhere in the output; those five are printed and sit under TMPDIR; HOME is neither the
    caller's HOME nor the real one; every other XDG_*_HOME / XDG_*_DIR word printed is under TMPDIR too."""
    r = rig.dry()
    assert r.returncode == 0, r.stdout + r.stderr
    text = r.stdout + r.stderr
    assert "/run/user/" not in text, text
    got = assignments(text)
    for key in ("HOME", "XDG_RUNTIME_DIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
        assert key in got, f"{key} is not in the printed environment: " + text
        assert under(got[key], rig.tmp), f"{key}={got[key]} is not under TMPDIR {rig.tmp}"
    assert got["HOME"] not in (REAL_HOME, str(rig.home)), got["HOME"]
    for key, val in got.items():
        if re.fullmatch(r"XDG_[A-Z_]+_(HOME|DIR)", key):
            assert under(val, rig.tmp), f"{key}={val} is not under TMPDIR"


def test_dry_run_gsettings_memory_and_software_egl_variables(rig):
    """H-085 Tests: "... `GSETTINGS_BACKEND=memory`, the software-EGL variables and `--virtual-monitor 2560x1440`". Measured:
    "software EGL works (`GBM_BACKEND=dri GBM_ALWAYS_SOFTWARE=1`, the Mesa EGL vendor file, `LIBGL_ALWAYS_SOFTWARE=1`)". The
    story names no variable for the vendor file, so any `__EGL_VENDOR_LIBRARY_*` variable whose value names mesa counts."""
    r = rig.dry()
    assert r.returncode == 0, r.stdout + r.stderr
    got = assignments(r.stdout + r.stderr)
    assert got.get("GSETTINGS_BACKEND") == "memory", got.get("GSETTINGS_BACKEND")
    assert got.get("GBM_BACKEND") == "dri" and got.get("GBM_ALWAYS_SOFTWARE") == "1", (got.get("GBM_BACKEND"), got.get("GBM_ALWAYS_SOFTWARE"))
    assert got.get("LIBGL_ALWAYS_SOFTWARE") == "1", got.get("LIBGL_ALWAYS_SOFTWARE")
    vendor = [v for k, v in got.items() if k.startswith("__EGL_VENDOR_LIBRARY_")]
    assert vendor and any("mesa" in v.lower() for v in vendor), f"no Mesa EGL vendor file variable: {vendor}"


def test_dry_run_prints_virtual_monitor_from_the_argument(rig):
    """H-085 Tests: "... and `--virtual-monitor 2560x1440`"; Change 1: "`hidden_desktop.sh <rundir> <WxH>` ... Virtual monitor
    `2560x1440`". The size is the <WxH> argument: 2560x1440 prints `--virtual-monitor 2560x1440`; a second size prints that
    size and not 2560x1440 (control: the monitor is not hard-coded in the script)."""
    r = rig.dry(MONITOR)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"--virtual-monitor {MONITOR}" in r.stdout + r.stderr, r.stdout + r.stderr
    r2 = rig.dry("1280x720")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "--virtual-monitor 1280x720" in r2.stdout + r2.stderr and MONITOR not in r2.stdout + r2.stderr, r2.stdout + r2.stderr


def test_dry_run_runs_under_env_i_nothing_ambient_is_passed_on(rig):
    """H-085 Change 1: "it runs under `env -i`". Planted caller variables (a probe, an ssh socket path, a DISPLAY, a
    WAYLAND_DISPLAY, a session type) are in the caller environment (control_caller_environment...), and none of their values
    appears anywhere in the dry-run output; the printed WAYLAND_DISPLAY, if any, is the private one."""
    r = rig.dry()
    text = r.stdout + r.stderr
    assert r.returncode == 0, text
    for key in ("OM_LEAK_PROBE", "SSH_AUTH_SOCK"):
        assert rig.probes[key] not in text, f"{key} leaked into the hidden desktop's environment: " + text
    assert "wayland-77" not in text and "x-probe" not in text, text
    got = assignments(text)
    assert got.get("DISPLAY") != ":77", "the caller's DISPLAY reaches the hidden desktop"
    assert got.get("WAYLAND_DISPLAY", DISPLAY_NAME) == DISPLAY_NAME, got.get("WAYLAND_DISPLAY")


# ---------------------------------------------------------------------------------------------
# Change 1: it refuses to start on anything real
# ---------------------------------------------------------------------------------------------

def reject_line(r):
    lines = [l for l in (r.stdout + "\n" + r.stderr).splitlines() if l.startswith("HIDDEN REJECT not private")]
    return lines[0] if lines else None


def test_private_caller_is_not_rejected(rig):
    """H-085 Tests, positive control: "(positive control: a private one starts)". A caller environment with a private HOME and
    a private session bus address prints no `HIDDEN REJECT` line and the dry run exits 0."""
    r = rig.dry(env=rig.caller_env(DBUS_SESSION_BUS_ADDRESS=f"unix:path={rig.base}/private-bus"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert reject_line(r) is None and "HIDDEN REJECT" not in r.stdout + r.stderr, r.stdout + r.stderr


def test_handed_the_real_session_bus_it_rejects_with_exit_6(rig):
    """H-085 Change 1: "It refuses to start (`HIDDEN REJECT not private <what>`, exit 6) when any variable it would hand on names
    the real `/run/user/<uid>` bus"; Tests: "handed a real `DBUS_SESSION_BUS_ADDRESS` ... it prints `HIDDEN REJECT not private
    ...` and exits 6". The real address is `unix:path=/run/user/<uid>/bus`; the line names the variable or the value as <what>.
    Control: test_private_caller_is_not_rejected."""
    r = rig.dry(env=rig.caller_env(DBUS_SESSION_BUS_ADDRESS=REAL_BUS))
    line = reject_line(r)
    assert line is not None, "no `HIDDEN REJECT not private` line: " + r.stdout + r.stderr
    assert "DBUS_SESSION_BUS_ADDRESS" in line or REAL_BUS in line, line
    assert r.returncode == 6, f"exit {r.returncode}"


def test_handed_the_real_home_it_rejects_with_exit_6(rig):
    """H-085 Change 1: "... or the real HOME"; Tests: "handed ... the real `HOME` it prints `HIDDEN REJECT not private ...` and
    exits 6". The real HOME is the passwd entry of this uid; the line names HOME or the path as <what>.
    Control: test_private_caller_is_not_rejected."""
    r = rig.dry(env=rig.caller_env(HOME=REAL_HOME))
    line = reject_line(r)
    assert line is not None, "no `HIDDEN REJECT not private` line: " + r.stdout + r.stderr
    assert "HOME" in line or REAL_HOME in line, line
    assert r.returncode == 6, f"exit {r.returncode}"


def test_a_rejected_start_launches_nothing(rig):
    """H-085 Change 1: "It refuses to start" and Measured: "it registered with GDM". A real (not dry) run handed the real
    session bus prints the REJECT line, exits 6 and launches none of the four stub programs, so no daemon is ever started
    against anything real. (Stubs only: nothing real runs; the real bus is a string in the caller environment.)"""
    r = rig.run(str(rig.rundir), MONITOR, env=rig.caller_env(DBUS_SESSION_BUS_ADDRESS=REAL_BUS))
    assert reject_line(r) is not None, "no REJECT line: " + r.stdout + r.stderr
    assert r.returncode == 6, f"exit {r.returncode}"
    assert rig.calls() == [], "a rejected start launched: " + repr([c["stub"] for c in rig.calls()])
    assert marked_pids(str(rig.base)) == [], "a rejected start left a process behind"


# ---------------------------------------------------------------------------------------------
# Change 1: a start (stub programs) prints HIDDEN up, leaves an env file, and every daemon sees only private values
# ---------------------------------------------------------------------------------------------

def test_a_start_prints_hidden_up_with_the_rundir_after_the_display_socket_exists(started):
    """H-085 Change 1: "starts the hidden desktop and prints `HIDDEN up <rundir>` with an env file" and Measured: the shell makes
    its Wayland display `wayland-dark`. The output holds the exact line `HIDDEN up <rundir>`, no REJECT line, and by then the
    stub shell's `wayland-dark` socket exists in the runtime dir the stub shell saw."""
    r, p, text = started
    assert f"HIDDEN up {r.rundir}" in text.splitlines(), text
    assert "HIDDEN REJECT" not in text, text
    shell = r.calls("gnome-shell")
    assert shell, "the script never launched gnome-shell: " + text
    assert (Path(shell[0]["env"]["XDG_RUNTIME_DIR"]) / DISPLAY_NAME).is_socket()


def test_gnome_shell_is_launched_headless_on_wayland_dark_with_the_virtual_monitor(started):
    """H-085 Measured: "a second GNOME compositor with no physical monitor (`gnome-shell --headless --wayland --no-x11
    --wayland-display wayland-dark --virtual-monitor 2560x1440`)". The argv the stub shell received."""
    r, p, text = started
    shell = r.calls("gnome-shell")
    assert shell, "the script never launched gnome-shell: " + text
    argv = shell[0]["argv"]
    for flag in ("--headless", "--wayland", "--no-x11"):
        assert flag in argv, (flag, argv)
    assert argv[argv.index("--wayland-display") + 1] == DISPLAY_NAME, argv
    assert argv[argv.index("--virtual-monitor") + 1] == MONITOR, argv


def test_every_daemon_it_starts_sees_only_the_private_environment(started):
    """H-085 Change 1: "Isolation is the contract: it runs under `env -i` with its own `HOME`, `XDG_RUNTIME_DIR`, `XDG_CONFIG_HOME`,
    `XDG_CACHE_HOME`, `XDG_DATA_HOME` under `TMPDIR`, `GSETTINGS_BACKEND=memory`, its own session bus (`dbus-run-session`), a
    private empty system-bus socket, a private pipewire and wireplumber, and software EGL." The environment each stub daemon
    (gnome-shell, pipewire, wireplumber) actually received: no `/run/user/` value, the five directories under TMPDIR, a HOME
    that is not the caller's, GSETTINGS_BACKEND=memory, software EGL, a private system bus, none of the planted caller probes,
    and for the shell the session bus the stub `dbus-run-session` gave (pipewire and wireplumber may run outside it, but
    never on another bus)."""
    r, p, text = started
    stub_bus = f"unix:path={r.base}/stub-session-bus"
    for name in ("gnome-shell", "pipewire", "wireplumber"):
        rows = r.calls(name)
        assert rows, f"{name} was never launched: " + text
        env = rows[0]["env"]
        assert not [k for k, v in env.items() if "/run/user/" in v], (name, env)
        for key in ("HOME", "XDG_RUNTIME_DIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
            assert key in env and under(env[key], r.tmp), (name, key, env.get(key))
        assert env["HOME"] not in (REAL_HOME, str(r.home)), (name, env["HOME"])
        assert env.get("GSETTINGS_BACKEND") == "memory", name
        assert env.get("GBM_BACKEND") == "dri" and env.get("GBM_ALWAYS_SOFTWARE") == "1" and env.get("LIBGL_ALWAYS_SOFTWARE") == "1", name
        if name == "gnome-shell":  # the shell needs the session bus (Mutter's ScreenCast and RemoteDesktop live on it)
            assert env.get("DBUS_SESSION_BUS_ADDRESS") == stub_bus, (name, env.get("DBUS_SESSION_BUS_ADDRESS"))
        else:
            assert env.get("DBUS_SESSION_BUS_ADDRESS", stub_bus) == stub_bus, (name, env.get("DBUS_SESSION_BUS_ADDRESS"))
        sysbus = env.get("DBUS_SYSTEM_BUS_ADDRESS", "")
        assert sysbus and "/run/dbus" not in sysbus and under(sysbus.split("path=", 1)[-1], r.tmp), (name, sysbus)
        assert r.probes["OM_LEAK_PROBE"] not in json.dumps(env) and "SSH_AUTH_SOCK" not in env, (name, "probe leaked")
        assert env.get("DISPLAY") != ":77" and env.get("WAYLAND_DISPLAY", DISPLAY_NAME) == DISPLAY_NAME, (name, "display leaked")


def test_the_env_file_lets_a_caller_reach_the_private_desktop_and_nothing_else(started):
    """H-085 Change 1: "prints `HIDDEN up <rundir>` with an env file" (play.sh and the capture read it to reach the desktop). The
    file the script leaves directly in the rundir that names WAYLAND_DISPLAY, sourced in an empty environment, sets
    WAYLAND_DISPLAY=wayland-dark, the private XDG_RUNTIME_DIR and the private DBUS_SESSION_BUS_ADDRESS, no `/run/user/` value
    and no DISPLAY. (The file's name is not in the story; any file in the rundir that names WAYLAND_DISPLAY is the env file.)"""
    r, p, text = started
    files = [f for f in r.rundir.iterdir() if f.is_file() and "WAYLAND_DISPLAY" in f.read_text(errors="replace")]
    assert files, f"no env file in {r.rundir}: {sorted(x.name for x in r.rundir.iterdir())}"
    env = env_file_vars(files[0])
    assert env.get("WAYLAND_DISPLAY") == DISPLAY_NAME, env
    assert under(env["XDG_RUNTIME_DIR"], r.tmp), env.get("XDG_RUNTIME_DIR")
    assert env.get("DBUS_SESSION_BUS_ADDRESS") == f"unix:path={r.base}/stub-session-bus", env.get("DBUS_SESSION_BUS_ADDRESS")
    assert not [k for k, v in env.items() if "/run/user/" in v] and "DISPLAY" not in env, env


# ---------------------------------------------------------------------------------------------
# The one slow-tier integration test (H-085 Tests, last bullet)
# ---------------------------------------------------------------------------------------------

GODOT = Path(os.environ.get("HOME", "")) / ".local" / "bin" / "godot.real"
MESA_VENDOR = [Path(p) for p in ("/usr/share/glvnd/egl_vendor.d/50_mesa.json", "/etc/glvnd/egl_vendor.d/50_mesa.json")]

STUB_PROJECT = '''config_version=5

[application]
config/name="h085-stub"
run/main_scene="res://stub.tscn"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'''
STUB_SCENE = '''[gd_scene format=3]

[node name="Root" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="Bg" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.1, 0.5, 0.9, 1)

[node name="Bar" type="ColorRect" parent="."]
layout_mode = 0
offset_left = 100.0
offset_top = 100.0
offset_right = 700.0
offset_bottom = 400.0
color = Color(0.95, 0.2, 0.1, 1)
'''

# Mutter ScreenCast through the private session bus, then gstreamer on the pipewire node: the capture path of H-085 Measured
# ("A capture by Mutter ScreenCast through a private pipewire (`gst pipewiresrc` to PNG)"). Refuses a non-private bus.
CAST_CLIENT = r'''
import os, subprocess, sys
from gi.repository import Gio, GLib
assert "/run/user/" not in os.environ["DBUS_SESSION_BUS_ADDRESS"], "refusing: not a private bus"
out = sys.argv[1]
conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
SC = "org.gnome.Mutter.ScreenCast"
def call(path, iface, m, args, sig):
    return conn.call_sync(SC, path, iface, m, args, GLib.VariantType(sig) if sig else None, Gio.DBusCallFlags.NONE, 20000, None)
sess = call("/org/gnome/Mutter/ScreenCast", SC, "CreateSession", GLib.Variant("(a{sv})", ({},)), "(o)").unpack()[0]
stream = call(sess, SC + ".Session", "RecordMonitor", GLib.Variant("(sa{sv})", ("Meta-0", {})), "(o)").unpack()[0]
loop, node = GLib.MainLoop(), {}
def on_sig(c, sender, path, iface, signal, params):
    if signal == "PipeWireStreamAdded":
        node["id"] = params.unpack()[0]; loop.quit()
conn.signal_subscribe(SC, SC + ".Stream", "PipeWireStreamAdded", stream, None, Gio.DBusSignalFlags.NONE, on_sig)
call(sess, SC + ".Session", "Start", None, None)
GLib.timeout_add_seconds(15, loop.quit); loop.run()
if "id" not in node:
    print("no pipewire node"); sys.exit(2)
r = subprocess.run(["timeout", "40", "gst-launch-1.0", "-q", "pipewiresrc", "path=%d" % node["id"], "keepalive-time=250",
                    "num-buffers=3", "!", "videoconvert", "!", "pngenc", "!", "multifilesink", "location=" + out[:-4] + ".%02d.png"],
                   capture_output=True, text=True)
call(sess, SC + ".Session", "Stop", None, None)
print("gst rc", r.returncode, r.stderr[-300:])
sys.exit(0 if r.returncode == 0 else 3)
'''


def integration_missing():
    """The reason the integration test cannot run here, or None. The story: skipped, never failed, when `gnome-shell` or
    software EGL is missing; the other programs are named too so a missing one is a skip with its name, not a red."""
    for tool in ("gnome-shell", "pipewire", "wireplumber", "dbus-run-session", "dbus-daemon", "gst-launch-1.0"):
        if not shutil.which(tool):
            return f"{tool} is not installed"
    if not any(p.exists() for p in MESA_VENDOR):
        return "software EGL is missing (no Mesa EGL vendor file under /usr/share/glvnd/egl_vendor.d)"
    if not GODOT.exists():
        return f"{GODOT} is missing (the game's Godot)"
    try:
        from PIL import Image  # noqa: F401
    except ImportError as e:
        return f"python module missing: {e.name}"
    if subprocess.run([PY3, "-c", "import gi"], capture_output=True).returncode != 0:
        return f"python module missing: gi (for {PY3})"
    return None


def busyness(png):
    """Fraction of pixels off the most common luminance; 0 is a flat frame (the repo's own blank metric)."""
    from PIL import Image
    h = Image.open(png).convert("L").histogram()
    return 1 - max(h) / sum(h)


def test_integration_hidden_desktop_boots_and_shows_a_stub_scene_non_blank():
    """H-085 Tests, last bullet: "One slow-tier integration test boots the real hidden desktop on this box, runs the repo's stub
    scene in it and gets a non-blank frame; it is skipped, never failed, when `gnome-shell` or software EGL is missing, with the
    reason printed." Slow tier: it starts a real gnome-shell, pipewire and wireplumber (about a dozen seconds); it runs under a
    private HOME, session bus, system bus and runtime dir exactly as Change 1 says, and every process it starts is ended by its
    temp dir marker at the end. The repo has no stub scene (no scenes/stub), so the test writes a one-scene Godot project
    (a blue ColorRect with a red bar) in its temp dir and plays that with the repo's Godot flags `--display-driver wayland
    --windowed --resolution 1919x1080`. The frame is taken by Mutter ScreenCast on the private bus; non-blank means the repo's
    blank metric is above 0 (the existing rule: reject only at 0). Not asserted: the script's own capture (hidden_capture.py),
    which the play.sh tests drive."""
    why = integration_missing()
    if why:
        print(f"SKIP integration: {why}", file=sys.stderr, flush=True)
        pytest.skip(why)
    r = Rig()
    try:
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(r.home), "TMPDIR": str(r.tmp), "LANG": "C.UTF-8"}
        p = r.start(env=env)
        text = r.wait_up(p)
        assert f"HIDDEN up {r.rundir}" in text.splitlines(), "hidden desktop did not come up: " + text
        files = [f for f in r.rundir.iterdir() if f.is_file() and "WAYLAND_DISPLAY" in f.read_text(errors="replace")]
        assert files, f"no env file in {r.rundir}"
        denv = env_file_vars(files[0])
        assert denv.get("WAYLAND_DISPLAY") == DISPLAY_NAME and "/run/user/" not in denv.get("DBUS_SESSION_BUS_ADDRESS", "/run/user/"), denv
        proj = r.base / "proj"; proj.mkdir()
        (proj / "project.godot").write_text(STUB_PROJECT); (proj / "stub.tscn").write_text(STUB_SCENE)
        genv = {"PATH": env["PATH"], "HOME": denv.get("HOME", str(r.home)), "TMPDIR": str(r.tmp), "LANG": "C.UTF-8",
                "XDG_RUNTIME_DIR": denv["XDG_RUNTIME_DIR"], "WAYLAND_DISPLAY": DISPLAY_NAME,
                "DBUS_SESSION_BUS_ADDRESS": denv["DBUS_SESSION_BUS_ADDRESS"], "XDG_DATA_HOME": str(r.base / "xdg"),
                "XDG_CACHE_HOME": str(r.base / "cache"), "GSETTINGS_BACKEND": "memory",
                "GBM_BACKEND": "dri", "GBM_ALWAYS_SOFTWARE": "1", "LIBGL_ALWAYS_SOFTWARE": "1"}
        genv.update({k: v for k, v in denv.items() if k.startswith("__EGL_VENDOR_LIBRARY_")})
        game = subprocess.Popen(["timeout", "90", str(GODOT), "--path", str(proj), "--display-driver", "wayland", "--windowed",
                                 "--resolution", "1919x1080"], cwd=str(r.base), env=genv, stdin=subprocess.DEVNULL,
                                stdout=open(r.base / "game.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
        r.procs.append(game)
        time.sleep(12)  # the game reached its qa port in 3 to 4 s on this box; a settle for the first frames (Measured)
        assert game.poll() is None, "the game ended early: " + (r.base / "game.log").read_text()[-600:]
        shot = r.base / "shot.png"
        cap = subprocess.run([PY3, "-c", CAST_CLIENT, str(shot)], env={**genv, "PATH": env["PATH"]}, capture_output=True,
                             text=True, timeout=90)
        frames = sorted(r.base.glob("shot.*.png"))
        assert cap.returncode == 0 and frames, "capture failed: " + cap.stdout + cap.stderr
        assert busyness(frames[-1]) > 0, "the hidden desktop's frame is blank: " + str(frames[-1])
    finally:
        r.teardown()
