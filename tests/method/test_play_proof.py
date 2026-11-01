"""H-031 proof-by-eyes, first piece and piece two: tests for scripts/play.sh and
scripts/specfactory/screen_capture.sh (docs/stories/H-031.md).

Nothing here opens a window or captures a screen. play.sh is driven through its
`--dry-run` launch line and through a fake tree, a fake HOME whose
`.local/bin/godot.real` is a stub (it logs its argv, prints `FPS: <n>` once a second
when given `--print-fps`, and answers the QA port's `["state"]` with a scene), and stub
`xdotool` / `xwininfo` programs ahead of the real ones on PATH.

Piece two adds a fake xdg-desktop-portal: a private dbus-daemon and a python3 Gio service that owns
`org.freedesktop.portal.Desktop` and answers `org.freedesktop.portal.Screenshot.Screenshot` the way the
portal does (reply with a request handle, then emit `Request.Response`; on success write
`~/Pictures/Screenshot-N.png` under a fake HOME). The real portal and the real screen are never touched.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAY = ROOT / "scripts" / "play.sh"
CAPTURE = ROOT / "scripts" / "specfactory" / "screen_capture.sh"
SCENE = "res://scenes/stub/stub.tscn"
# H-031 Piece two: "`RESOLUTION` becomes `1919x1080` (DRAFT-play-resolution, was 1920x1080)".
RES = "1919x1080"

GODOT_STUB = '''#!/usr/bin/env python3
import json, os, socket, sys, threading, time
argv = sys.argv[1:]
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps(argv) + "\\n")
if "--import" in argv:
    sys.exit(0)
scene = next((a for a in argv if a.startswith("res://")), "")
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
end = time.time() + 40  # a stub nobody kills ends by itself
while time.time() < end and not os.path.exists(os.environ["STUB_STOP"]):
    if "--print-fps" in argv:
        print("FPS: " + os.environ.get("STUB_FPS", "140"), flush=True)
    time.sleep(1)
'''


def make_env(base, map_state=None, fps=140, wayland=False, x_window=True):
    """A fake tree (a git repo with a stub build script and a project.godot), a fake HOME with the
    godot stub, stub xdotool/xwininfo on PATH. Returns (env, tree, log, stop)."""
    base = Path(base)
    home = base / "home"; (home / ".local" / "bin").mkdir(parents=True)
    godot = home / ".local" / "bin" / "godot.real"
    godot.write_text(GODOT_STUB); godot.chmod(0o755)
    bindir = base / "bin"; bindir.mkdir()
    # xdotool finds a window by name: the stub finds one, or none (a Wayland session has no X window)
    (bindir / "xdotool").write_text("#!/bin/sh\n" + ("echo 12345\nexit 0\n" if x_window else "exit 1\n"))
    (bindir / "xwininfo").write_text(
        "#!/bin/sh\necho 'xwininfo: Window id: 0x3a00007 \"Ouroboros (DEBUG)\"'\n"
        "echo '  Map State: %s'\nexit 0\n" % (map_state or "IsUnMapped"))
    for p in bindir.iterdir():
        p.chmod(0o755)
    tree = base / "fake_tree"; (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "build_pipe_linux.sh").write_text(
        "#!/bin/sh\nmkdir -p dist/linux && echo stub > dist/linux/ouroboros_pipe\n")
    (tree / "scripts" / "build_pipe_linux.sh").chmod(0o755)
    if CAPTURE.exists():  # Piece two: the capture script rides along, wherever play.sh looks for it
        (tree / "scripts" / "specfactory").mkdir(parents=True)
        shutil.copy(CAPTURE, tree / "scripts" / "specfactory" / "screen_capture.sh")
    (tree / "project.godot").write_text('config_version=5\n[application]\nrun/main_scene="%s"\n' % SCENE)
    g = ["git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g[:3] + ["init", "-q"], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-qm", "fake tree"], check=True)
    (base / "tmp").mkdir()
    log, stop = base / "godot-argv.log", base / "stop"
    env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
    env.update(HOME=str(home), PATH=f"{bindir}:{env['PATH']}", TMPDIR=str(base / "tmp"),
               DISPLAY=":99", STUB_LOG=str(log), STUB_STOP=str(stop), STUB_FPS=str(fps))
    if wayland:
        env["WAYLAND_DISPLAY"] = "wayland-99"
    # Piece two: --check now captures through the portal. Never the real session bus: a dead one here,
    # replaced by FakePortal's where a test plants a portal.
    (base / "run").mkdir()
    env.update(DBUS_SESSION_BUS_ADDRESS=f"unix:path={base}/no-bus", XDG_RUNTIME_DIR=str(base / "run"))
    return env, tree, log, stop


def play(env, tree, *args, timeout=150):
    return subprocess.run(["bash", str(PLAY), "--tree", str(tree), *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=timeout)


def launch_argv(log):
    """The argv of the stub's launch call (the one that is not the --import)."""
    for _ in range(100):  # the stub is detached; give it a moment to write its line
        calls = [json.loads(l) for l in Path(log).read_text().splitlines()] if Path(log).exists() else []
        launches = [c for c in calls if "--import" not in c]
        if launches:
            break
        time.sleep(0.1)
    assert launches, "godot was never launched: " + repr(calls)
    return launches[0]


def dry_launch_line(wayland):
    env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY",)}
    if wayland:
        env["WAYLAND_DISPLAY"] = "wayland-99"
    r = subprocess.run(["bash", str(PLAY), "--tree", str(ROOT), "--dry-run"], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [l for l in r.stdout.splitlines() if l.startswith("launch:")]
    assert lines, r.stdout
    return lines[0]


def test_control_dry_run_prints_a_launch_line_with_path():
    """Positive control for the dry-run tests (H-001 behaviour 8, green today): the dry run
    prints a `launch:` line carrying `--path`, so a red below means the flags are missing."""
    line = dry_launch_line(wayland=False)
    assert "godot.real --path" in line, line


def test_dry_run_with_wayland_display_adds_driver_windowed_resolution():
    """H-031 First piece, Tests: "Dry run with `WAYLAND_DISPLAY` set prints
    `--display-driver wayland --windowed --resolution <DRAFT-play-resolution>` on the launch line", the
    resolution re-pinned by Piece two: "`RESOLUTION` becomes `1919x1080` (DRAFT-play-resolution, was
    1920x1080)" (DEC-display-fault-measured-2026-10-31)."""
    line = dry_launch_line(wayland=True)
    assert f"--display-driver wayland --windowed --resolution {RES}" in line, line


def test_dry_run_without_wayland_display_has_no_driver_flag_but_windowed():
    """H-031 First piece, Tests: "Dry run without it prints no wayland flag but still
    `--windowed`." (The resolution is always present: "always `--windowed --resolution
    <DRAFT-play-resolution>`", now 1919x1080 by Piece two, DEC-display-fault-measured-2026-10-31.)"""
    line = dry_launch_line(wayland=False)
    assert "wayland" not in line and "--display-driver" not in line, line
    assert "--windowed" in line, line
    assert f"--resolution {RES}" in line, line


def test_real_launch_argv_carries_the_flags_under_wayland_and_not_under_x11():
    """H-031 First piece: "play.sh launches Godot with `--display-driver wayland` when
    `WAYLAND_DISPLAY` is set in the environment, else X11 as today, and always `--windowed
    --resolution <DRAFT-play-resolution>`", the value 1919x1080 since Piece two
    (DEC-display-fault-measured-2026-10-31). Checked on the argv the stub Godot received, not only the
    dry-run line. X11 run is the positive control."""
    base = Path(tempfile.mkdtemp(prefix="h031-argv-"))
    try:
        env, tree, log, stop = make_env(base / "x", map_state="IsViewable")
        r = play(env, tree, "--scene", SCENE)
        stop.touch()
        assert r.returncode == 0, r.stdout + r.stderr
        argv = launch_argv(log)
        assert "--display-driver" not in argv and "wayland" not in argv, argv
        assert "--windowed" in argv and argv[argv.index("--resolution") + 1] == RES, argv
        env, tree, log, stop = make_env(base / "w", wayland=True, x_window=False)
        r = play(env, tree, "--scene", SCENE, "--check")
        stop.touch()
        argv = launch_argv(log)
        assert argv[argv.index("--display-driver") + 1] == "wayland", argv
        assert "--windowed" in argv and argv[argv.index("--resolution") + 1] == RES, argv
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_x11_viewable_window_passes_control():
    """Positive control for the unmapped test. H-031 First piece: "Window check under X11:
    the old xwininfo check stays and additionally requires Map State IsViewable". A stub
    xwininfo reporting `Map State: IsViewable` prints `PLAY window <s>s` and exits 0."""
    base = Path(tempfile.mkdtemp(prefix="h031-viewable-"))
    try:
        env, tree, log, stop = make_env(base, map_state="IsViewable")
        r = play(env, tree, "--scene", SCENE)
        stop.touch()
        assert r.returncode == 0, r.stdout + r.stderr
        assert re.search(r"^PLAY window \d+s$", r.stdout, re.M), r.stdout
        assert "PLAY REJECT" not in r.stdout, r.stdout
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_x11_unmapped_window_is_rejected():
    """H-031 First piece, Tests: "A planted xwininfo stub reporting IsUnMapped under X11
    gives `PLAY REJECT window unmapped IsUnMapped` (positive control: IsViewable passes)."
    First piece: "otherwise it prints `PLAY REJECT window unmapped <state>`." xdotool still
    finds the window by name (as it does today on an unmapped one)."""
    base = Path(tempfile.mkdtemp(prefix="h031-unmapped-"))
    try:
        env, tree, log, stop = make_env(base, map_state="IsUnMapped")
        r = play(env, tree, "--scene", SCENE)
        stop.touch()
        assert "PLAY REJECT window unmapped IsUnMapped" in r.stdout.splitlines(), r.stdout + r.stderr
        assert r.returncode != 0, "play.sh exited 0 on an unmapped window"
        assert not re.search(r"^PLAY window \d+s$", r.stdout, re.M), r.stdout
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_wayland_check_prints_window_line_with_seconds_and_wayland():
    """H-031 First piece: "Window check under the Wayland driver (no X window, so no
    xwininfo): the QA daemon answers `qa_state()` with the scene AND Godot's `--print-fps`
    output shows at least DRAFT-play-min-fps 30 fps lines for DRAFT 3 consecutive seconds.
    It prints `PLAY window <s>s wayland`." Stub: xdotool finds no X window, xwininfo says
    IsUnMapped (so neither may decide the result), stub Godot answers the scene and prints
    `FPS: 140` each second. Piece two: "`play.sh --check` calls it after the scene is reached", so a
    `--check` run needs a portal to exit 0: the fake one answers (play_check_with_portal)."""
    base = Path(tempfile.mkdtemp(prefix="h031-wayland-"))
    portal = None
    try:
        r, portal = play_check_with_portal(base, "varied")
        assert r.returncode == 0, r.stdout + r.stderr
        assert re.search(r"^PLAY window \d+s wayland$", r.stdout, re.M), r.stdout
        assert f"PLAY scene {SCENE} reached" in r.stdout, r.stdout
        assert "--print-fps" in launch_argv(base / "env" / "godot-argv.log"), r.stdout
    finally:
        if portal:
            portal.close()
        shutil.rmtree(base, ignore_errors=True)


def test_wayland_check_with_low_fps_does_not_print_the_window_line():
    """H-031 First piece: "at least DRAFT-play-min-fps 30 fps lines for DRAFT 3 consecutive
    seconds". A stub Godot printing `FPS: 10` each second never meets it, so the
    `PLAY window <s>s wayland` line is not printed and the run does not exit 0.
    Positive control: test_wayland_check_prints_window_line_with_seconds_and_wayland (140 fps)."""
    base = Path(tempfile.mkdtemp(prefix="h031-lowfps-"))
    try:
        env, tree, log, stop = make_env(base, wayland=True, x_window=False, fps=10)
        r = play(env, tree, "--scene", SCENE, "--check")
        stop.touch()
        argv = launch_argv(log)  # the Wayland path was taken (else no-window rejects would pass this vacuously)
        assert argv[argv.index("--display-driver") + 1] == "wayland", argv
        assert not re.search(r"^PLAY window \d+s wayland$", r.stdout, re.M), r.stdout
        assert r.returncode != 0, r.stdout + r.stderr
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# H-031 Piece two: the dry-run resolution and the portal capture (docs/stories/H-031.md, Piece two)
# ---------------------------------------------------------------------------------------------

PORTAL_PY = "/usr/bin/python3" if Path("/usr/bin/python3").exists() else (shutil.which("python3") or "python3")

PORTAL_STUB = r"""
import json, os, shutil, sys
from gi.repository import Gio, GLib
src, code, log = sys.argv[1], int(sys.argv[2]), sys.argv[3]
XML = '''<node><interface name="org.freedesktop.portal.Screenshot">
<method name="Screenshot"><arg type="s" name="parent_window" direction="in"/>
<arg type="a{sv}" name="options" direction="in"/><arg type="o" name="handle" direction="out"/></method>
</interface></node>'''
def on_call(conn, sender, path, iface, method, params, inv):
    parent, options = params.unpack()
    with open(log, "a") as f:
        f.write(json.dumps({"method": method, "parent": parent, "options": options}) + "\n")
    handle = "/org/freedesktop/portal/desktop/request/%s/t1" % sender.lstrip(":").replace(".", "_")
    inv.return_value(GLib.Variant("(o)", (handle,)))
    def respond():
        results = {}
        if code == 0:
            pics = os.path.join(os.environ["HOME"], "Pictures"); os.makedirs(pics, exist_ok=True)
            n = len([x for x in os.listdir(pics) if x.startswith("Screenshot")]) + 1
            dst = os.path.join(pics, "Screenshot-%d.png" % n)
            shutil.copy(src, dst)
            results = {"uri": GLib.Variant("s", "file://" + dst)}
        conn.emit_signal(None, handle, "org.freedesktop.portal.Request", "Response",
                         GLib.Variant("(ua{sv})", (code, results)))
        return False
    GLib.timeout_add(100, respond)
def on_bus(conn, name):
    conn.register_object("/org/freedesktop/portal/desktop", Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0],
                         on_call, None, None)
def on_name(conn, name):
    print("READY", flush=True)
Gio.bus_own_name(Gio.BusType.SESSION, "org.freedesktop.portal.Desktop", Gio.BusNameOwnerFlags.NONE,
                 on_bus, on_name, None)
GLib.MainLoop().run()
"""

PORTAL_CLIENT = r"""
from gi.repository import Gio, GLib
conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
loop = GLib.MainLoop(); got = {}
def on_resp(c, sender, path, iface, signal, params):
    code, results = params.unpack(); got["code"] = code; got["uri"] = results.get("uri", ""); loop.quit()
conn.signal_subscribe("org.freedesktop.portal.Desktop", "org.freedesktop.portal.Request", "Response",
                      None, None, Gio.DBusSignalFlags.NONE, on_resp)
conn.call_sync("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop",
               "org.freedesktop.portal.Screenshot", "Screenshot",
               GLib.Variant("(sa{sv})", ("", {"interactive": GLib.Variant("b", False)})),
               GLib.VariantType("(o)"), Gio.DBusCallFlags.NONE, 10000, None)
GLib.timeout_add_seconds(10, loop.quit)
loop.run()
print(got.get("code"), got.get("uri", ""))
"""

DBUS_CONF = """<busconfig><type>session</type><listen>unix:path=%s</listen><auth>EXTERNAL</auth>
<policy context="default"><allow send_destination="*" eavesdrop="true"/><allow eavesdrop="true"/>
<allow own="*"/></policy></busconfig>"""


def write_png(path, kind):
    """A planted PNG: `uniform` (one flat colour), `black` (blank) or `varied` (stripes and a gradient)."""
    from PIL import Image
    w, h = 400, 225
    img = Image.new("RGB", (w, h), (30, 60, 90) if kind == "uniform" else (0, 0, 0))
    if kind == "varied":
        px = img.load()
        for x in range(w):
            for y in range(h):
                px[x, y] = ((x * 255) // w, (y * 255) // h, 200 if (x // 50) % 2 else 20)
    img.save(path)
    return Path(path)


def pixels(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return im.size, im.tobytes()


class FakePortal:
    """A private session bus with the fake portal on it. `env` is what a caller adds to its environment
    (DBUS_SESSION_BUS_ADDRESS, HOME with a user-dirs file); `calls()` is what the portal was asked.
    `home` is the HOME both the portal and the script under test see (default: a fresh one)."""

    def __init__(self, base, src_png, code=0, home=None):
        self.base = Path(base)
        self.home = Path(home) if home else self.base / "phome"
        (self.home / ".config").mkdir(parents=True, exist_ok=True)
        (self.home / ".config" / "user-dirs.dirs").write_text('XDG_PICTURES_DIR="%s/Pictures"\n' % self.home)
        self.pictures = self.home / "Pictures"
        self.log = self.base / "portal-calls.log"
        (self.base / "dbus.conf").write_text(DBUS_CONF % (self.base / "bus"))
        self.bus = subprocess.Popen(["dbus-daemon", "--config-file", str(self.base / "dbus.conf"), "--nofork",
                                     "--print-address"], stdout=subprocess.PIPE, text=True)
        self.address = self.bus.stdout.readline().strip()
        assert self.address.startswith("unix:"), "private dbus-daemon did not start: " + repr(self.address)
        self.env = {"DBUS_SESSION_BUS_ADDRESS": self.address, "HOME": str(self.home),
                    "XDG_CONFIG_HOME": str(self.home / ".config")}
        (self.base / "portal_stub.py").write_text(PORTAL_STUB)
        self.svc = subprocess.Popen([PORTAL_PY, str(self.base / "portal_stub.py"), str(src_png), str(code),
                                     str(self.log)], stdout=subprocess.PIPE, text=True, env={**os.environ, **self.env})
        assert self.svc.stdout.readline().strip() == "READY", "fake portal did not take its bus name"

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()] if self.log.exists() else []

    def plant_stale(self, png):
        """An older Screenshot-1.png from some earlier capture: the newest must win."""
        self.pictures.mkdir(exist_ok=True)
        old = self.pictures / "Screenshot-1.png"
        shutil.copy(png, old); os.utime(old, (946684800, 946684800))

    def close(self):
        for p in (self.svc, self.bus):
            p.terminate()
        for p in (self.svc, self.bus):
            p.wait(timeout=10)


def capture_env(base, portal):
    """The env for running screen_capture.sh: fake HOME and bus, a stub xdotool that finds no window
    (so the whole desktop is kept), no display variables."""
    bindir = Path(base) / "capbin"; bindir.mkdir(exist_ok=True)
    (bindir / "xdotool").write_text("#!/bin/sh\nexit 1\n"); (bindir / "xdotool").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
    env.update(portal.env); env["PATH"] = f"{bindir}:{env['PATH']}"
    return env


def run_capture(env, out):
    return subprocess.run(["bash", str(CAPTURE), str(out)], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=60)


def test_control_fake_portal_answers_the_screenshot_contract():
    """Positive control for every portal test below (green today; no script under test is involved).
    H-031 Piece two: "call `org.freedesktop.portal.Screenshot.Screenshot("", {"interactive": False})`
    ... subscribe to `Request.Response` ... which writes `~/Pictures/Screenshot-N.png`". A client that
    makes exactly that call on the fake bus gets Response 0 with the file's uri, the fake logs the empty
    parent window and `{"interactive": False}`, and the PNG is in the fake HOME's Pictures."""
    base = Path(tempfile.mkdtemp(prefix="h031-portal-ctl-"))
    try:
        src = write_png(base / "src.png", "varied")
        portal = FakePortal(base, src)
        try:
            r = subprocess.run([PORTAL_PY, "-c", PORTAL_CLIENT], env={**os.environ, **portal.env},
                               capture_output=True, text=True, timeout=30)
            assert r.returncode == 0, r.stdout + r.stderr
            code, uri = r.stdout.split()
            assert code == "0" and uri.startswith("file://") and uri.endswith(".png"), r.stdout
            assert portal.calls() == [{"method": "Screenshot", "parent": "", "options": {"interactive": False}}]
            shots = sorted(portal.pictures.glob("Screenshot-*.png"))
            assert len(shots) == 1 and pixels(shots[0]) == pixels(src), shots
        finally:
            portal.close()
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_control_make_env_never_points_at_the_real_session_bus():
    """Positive control for the hermetic env (green today): a `--check` run of play.sh must not reach
    the real xdg portal on the tester's desktop, so make_env gives it a bus address that is not the
    ambient one and a private XDG_RUNTIME_DIR (so Gio's /run/user/N/bus fallback is closed too)."""
    base = Path(tempfile.mkdtemp(prefix="h031-env-ctl-"))
    try:
        env, tree, log, stop = make_env(base, wayland=True)
        assert env["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path={base}/no-bus", env["DBUS_SESSION_BUS_ADDRESS"]
        assert env["XDG_RUNTIME_DIR"] == str(base / "run"), env["XDG_RUNTIME_DIR"]
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_control_planted_pngs_differ():
    """Positive control for the uniform tests: the varied PNG is not flat and the flat ones are
    (green today; checks the fixture, not the script)."""
    base = Path(tempfile.mkdtemp(prefix="h031-png-ctl-"))
    try:
        from PIL import Image
        for kind, flat in (("uniform", True), ("black", True), ("varied", False)):
            colors = Image.open(write_png(base / f"{kind}.png", kind)).convert("RGB").getcolors(maxcolors=1 << 20)
            assert (len(colors) == 1) == flat, (kind, len(colors))
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_dry_run_resolution_is_1919x1080_not_the_project_viewport():
    """H-031 Piece two: "`scripts/play.sh`: `RESOLUTION` becomes `1919x1080` (DRAFT-play-resolution, was
    1920x1080) ... The dry-run line shows it." and Tests: "dry run prints `--resolution 1919x1080`".
    A request equal to the project viewport 1920x1080 presents only the splash
    (DEC-display-fault-measured-2026-10-31), so the line must not carry it. Both session kinds."""
    for wayland in (False, True):
        line = dry_launch_line(wayland=wayland)
        assert "--resolution 1919x1080" in line, line
        assert "1920x1080" not in line, line


def test_dry_run_check_prints_the_capture_step():
    """H-031 Tests: "The dry run prints the capture step." and Proof: "`play.sh --check` writes
    `<scratch>/proof.png` with that script". `--dry-run --check` names `screen_capture.sh` and
    `proof.png` in its output. (The story gives no line format; this pins only the two names.)"""
    r = subprocess.run(["bash", str(PLAY), "--tree", str(ROOT), "--dry-run", "--check"], cwd=ROOT,
                       env={k: v for k, v in os.environ.items() if k != "WAYLAND_DISPLAY"},
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "launch:" in r.stdout, r.stdout  # control: the dry run itself works
    assert "screen_capture.sh" in r.stdout and "proof.png" in r.stdout, r.stdout


def test_screen_capture_portal_success_prints_capture_line_and_copies_the_png():
    """H-031 Piece two: "a planted portal stub that writes a known PNG makes `screen_capture.sh` print
    `CAPTURE portal <out>` and the file matches". Also: "the script copies the newest such file to
    `<out.png>`" (an older Screenshot-1.png from an earlier capture is planted and must lose) and the
    portal is called as "Screenshot("", {"interactive": False})". xdotool finds no window, so "else keeps
    the whole desktop": the output has the planted PNG's size and pixels."""
    base = Path(tempfile.mkdtemp(prefix="h031-cap-ok-"))
    try:
        src = write_png(base / "src.png", "varied")
        stale = write_png(base / "stale.png", "uniform")
        portal = FakePortal(base, src)
        try:
            portal.plant_stale(stale)
            out = base / "out.png"
            r = run_capture(capture_env(base, portal), out)
            assert f"CAPTURE portal {out}" in r.stdout.splitlines(), r.stdout + r.stderr
            assert r.returncode == 0, r.stdout + r.stderr
            assert pixels(out) == pixels(src), "the output is not the newest portal screenshot"
            assert portal.calls() == [{"method": "Screenshot", "parent": "", "options": {"interactive": False}}]
        finally:
            portal.close()
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_screen_capture_rejects_a_blank_or_uniform_png():
    """H-031 Piece two: "a planted uniform PNG fails the proof (positive control: a planted non-uniform one
    passes)"; Capture: "A capture that is blank or near-uniform fails." A portal that writes a flat
    colour, or a black PNG, makes the script exit non-zero, print a REJECT line and no `CAPTURE portal`
    line. Control: test_screen_capture_portal_success_prints_capture_line_and_copies_the_png (non-uniform
    passes). The near-uniform threshold is not given by the story, so only flat images are planted."""
    for kind in ("uniform", "black"):
        base = Path(tempfile.mkdtemp(prefix=f"h031-cap-{kind}-"))
        try:
            portal = FakePortal(base, write_png(base / "src.png", kind))
            try:
                r = run_capture(capture_env(base, portal), base / "out.png")
                assert portal.calls(), f"{kind}: the script never called the portal: " + r.stdout + r.stderr
                assert r.returncode != 0, f"{kind}: exit 0 on a flat capture: " + r.stdout + r.stderr
                assert "REJECT" in r.stdout, f"{kind}: " + r.stdout + r.stderr
                assert not any(l.startswith("CAPTURE portal") for l in r.stdout.splitlines()), r.stdout
            finally:
                portal.close()
        finally:
            shutil.rmtree(base, ignore_errors=True)


def test_screen_capture_portal_denial_prints_reject_and_exits_2():
    """H-031 Piece two: "a stub that returns the portal's denial code prints `CAPTURE REJECT portal
    denied`" and "a denial prints `CAPTURE REJECT portal denied` and exits 2". The xdg Request.Response
    codes other than 0 are 1 (cancelled by the user) and 2 (ended some other way); the story names no
    number, so both are planted. No output file is written."""
    for code in (1, 2):
        base = Path(tempfile.mkdtemp(prefix=f"h031-cap-deny{code}-"))
        try:
            portal = FakePortal(base, write_png(base / "src.png", "varied"), code=code)
            try:
                out = base / "out.png"
                r = run_capture(capture_env(base, portal), out)
                assert portal.calls(), f"code {code}: the script never called the portal: " + r.stdout + r.stderr
                assert "CAPTURE REJECT portal denied" in r.stdout.splitlines(), f"code {code}: " + r.stdout + r.stderr
                assert r.returncode == 2, f"code {code}: exit {r.returncode}"
                assert not out.exists(), "a denied capture left an output file"
            finally:
                portal.close()
        finally:
            shutil.rmtree(base, ignore_errors=True)


def play_check_with_portal(base, src_kind):
    """play.sh --check on the Wayland path: stub Godot, the fake portal on a private bus and in the stub
    Godot's fake HOME, the fake tree carrying the capture script (make_env). `--keep` leaves the scratch
    clone so proof.png can be read. Returns (result, portal); the caller closes the portal."""
    base = Path(base)
    env, tree, log, stop = make_env(base / "env", wayland=True, x_window=False)
    portal = FakePortal(base, write_png(base / "src.png", src_kind), home=env["HOME"])
    env.update(portal.env)
    try:
        r = play(env, tree, "--scene", SCENE, "--check", "--keep")
    finally:
        stop.touch()
    return r, portal


def test_play_check_prints_proof_line_with_portal_and_the_png_is_the_capture():
    """H-031 Piece two: "`play.sh --check` calls it after the scene is reached and prints
    `PLAY proof <path> portal`"; Proof: "`play.sh --check` writes `<scratch>/proof.png` with that script
    after the scene is reached". Wayland path, stub Godot, fake portal writing a varied PNG: the proof
    line follows the `PLAY scene ... reached` line, names `<scratch>/proof.png`, and that file is the
    portal's PNG."""
    base = Path(tempfile.mkdtemp(prefix="h031-proof-"))
    portal = None
    try:
        r, portal = play_check_with_portal(base, "varied")
        assert r.returncode == 0, r.stdout + r.stderr
        lines = r.stdout.splitlines()
        scene_i = next((i for i, l in enumerate(lines) if l == f"PLAY scene {SCENE} reached"), None)
        assert scene_i is not None, r.stdout
        found = [(i, re.fullmatch(r"PLAY proof (\S+) portal", l)) for i, l in enumerate(lines)]
        found = [(i, x) for i, x in found if x]
        assert found, "no `PLAY proof <path> portal` line: " + r.stdout + r.stderr
        i, x = found[0]
        assert i > scene_i, "the proof line must come after the scene is reached: " + r.stdout
        scratch = next(l.split(": ", 1)[1] for l in lines if l.startswith("scratch: "))
        assert x.group(1) == f"{scratch}/proof.png", (x.group(1), scratch)
        assert pixels(x.group(1)) == pixels(base / "src.png")
    finally:
        if portal:
            portal.close()
        shutil.rmtree(base, ignore_errors=True)


def test_play_check_with_a_uniform_capture_fails_the_proof():
    """H-031 Piece two: "`play.sh --check` calls it ... the blank or near-uniform test fails the proof."
    A fake portal that writes a flat PNG: play.sh exits non-zero and prints no `PLAY proof` line.
    Control: test_play_check_prints_proof_line_with_portal_and_the_png_is_the_capture (varied passes)
    and the scene line below, which shows the run reached the capture point."""
    base = Path(tempfile.mkdtemp(prefix="h031-proof-flat-"))
    portal = None
    try:
        r, portal = play_check_with_portal(base, "uniform")
        assert f"PLAY scene {SCENE} reached" in r.stdout, "the run did not reach the scene: " + r.stdout + r.stderr
        assert portal.calls(), "play.sh --check never called the portal: " + r.stdout + r.stderr
        assert r.returncode != 0, "play.sh exited 0 with a flat proof: " + r.stdout + r.stderr
        assert not any(l.startswith("PLAY proof") for l in r.stdout.splitlines()), r.stdout
    finally:
        if portal:
            portal.close()
        shutil.rmtree(base, ignore_errors=True)
