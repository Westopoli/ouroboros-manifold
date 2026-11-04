"""H-085 proof-on-a-hidden-desktop, second piece: tests for scripts/play.sh `--check` (the hidden desktop by default)
and `--check --real` (the real display and the portal, as today) (docs/stories/H-085.md, Change 2, 3 and Tests).

Story line: "A landing's play proof runs the game on a real GNOME desktop that has no monitor, so it works through the
night with my screens dark, ... and still catches a game that opens and shows only its splash; checking the game on
my real desktop is a separate command I run when I am at the desk."

Nothing here opens a window, captures a real screen or touches the real session, display, bus, HOME, portal,
play.lock or ~/Pictures. Same fakes as tests/method/test_play_proof.py (copied, not imported): a fake tree (a git
repo with a stub build script), a fake HOME whose `.local/bin/godot.real` is a stub Godot, the fake xdg portal on a
private bus. New here, all private to one test run: stub `gnome-shell`, `pipewire`, `wireplumber`, `dbus-run-session`
and `gst-launch-1.0` programs ahead of the real ones on PATH, and a fake Mutter (`org.gnome.Mutter.ScreenCast` and
`org.gnome.Mutter.RemoteDesktop`) on the private bus that the stub `dbus-run-session` hands out. The capture path they
fake is the measured one (H-085 Measured): ScreenCast on the private bus, then `gst-launch-1.0 pipewiresrc` to PNG,
and an Escape key through `org.gnome.Mutter.RemoteDesktop`.

The fake tree carries copies of scripts/specfactory/ and scripts/method/proc.py from this checkout, so
`hidden_desktop.sh` and `hidden_capture.py` run as built. The stubs record every call (argv, environment, time) in one
log; the fake portal and fake Mutter record theirs. One run of play.sh is shared by every test that reads it.

Not tested (H-085 Rulings 8): the "about 3 s" between the two frames; the hidden desktop's life after play.sh ends
("ends by timeout, never by hand"); `--real` without `--check`.

Added after the coordinator's rulings of 2026-11-04 (H-085 Rulings 2, 3, 4): the scrub (the caller's HOME, session bus,
runtime dir, display variables and XAUTHORITY reach neither `hidden_desktop.sh` nor the game, seen through a recording wrapper
in front of the real script and the stub game), hidden mode with no DISPLAY and no WAYLAND_DISPLAY, and the Escape window
(any time after the qa port answers and before the first frame).
"""
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAY = ROOT / "scripts" / "play.sh"
SCENE = "res://scenes/stub/stub.tscn"
RES = "1919x1080"  # H-031 Piece two, DEC-display-fault-measured-2026-10-31
PY3 = "/usr/bin/python3" if Path("/usr/bin/python3").exists() else (shutil.which("python3") or "python3")
DISPLAY_NAME = "wayland-dark"  # H-085 Tests: "`WAYLAND_DISPLAY=wayland-dark`"
ESCAPE = 0xFF1B  # the X11 keysym of Escape
NODE_ID = 42
PLAY_PATIENCE_S = 150  # test patience only: how long the harness waits before it calls one play.sh run hung

# Every stub shares this head: it logs argv, environment, time to one file, and `hold()` waits for the stop file.
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
# dbus-run-session [--] cmd...: run cmd on the fake Mutter's bus (its address is in BUSFILE once the fake is up).
DBUS_BODY = '''
argv = sys.argv[1:]
cmd = argv[argv.index("--") + 1:] if "--" in argv else [a for a in argv if not a.startswith("-")]
env = dict(os.environ)
env["DBUS_SESSION_BUS_ADDRESS"] = open(BUSFILE).read().strip()
os.execvpe(cmd[0], cmd, env)
'''
# gst-launch-1.0 ... multifilesink location=<base>.%02d.png (or filesink location=<file>): writes the planned PNG for this
# invocation (the first call gets plan[0], the second plan[1], later calls the last one), num-buffers copies.
GST_BODY = '''
import shutil
args = sys.argv[1:]
loc = next((a.split("=", 1)[1] for a in args if a.startswith("location=")), "")
n = int(next((a.split("=", 1)[1] for a in args if a.startswith("num-buffers=")), "1"))
plan = json.load(open(PLAN))
cnt = PLAN + ".count"
k = int(open(cnt).read()) if os.path.exists(cnt) else 0
open(cnt, "w").write(str(k + 1))
src = plan[min(k, len(plan) - 1)]
if "%" in loc:
    for i in range(n):
        shutil.copy(src, loc % i)
elif loc:
    shutil.copy(src, loc)
note(invocation=k, src=src, location=loc, n=n)
'''
# A recording wrapper in front of the real hidden_desktop.sh (H-085 Rulings 2): it logs argv and environment like the stubs, then runs
# the real script, renamed hidden_desktop_real.sh beside it. Written in bash so a caller that runs it by `bash <path>` still works.
WRAPPER_PY = '''
import json, os, sys, time
with open(LOG, "a") as f:
    f.write(json.dumps({"stub": "hidden_desktop", "argv": sys.argv[1:], "env": dict(os.environ), "t": time.time(), "pid": os.getpid()}) + "\\n")
'''


def wrapper_source(log):
    return (f"#!/usr/bin/env bash\n{PY3} - \"$@\" <<'PY'\nLOG = {str(log)!r}\n{WRAPPER_PY}PY\n"
            'exec bash "$(dirname "$0")/hidden_desktop_real.sh" "$@"\n')


# The stub Godot: logs like the others, exits at once for --import, answers the QA port with the scene, prints FPS lines.
GODOT_BODY = '''
import socket, threading
argv = sys.argv[1:]
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
            note(qa_answered=True)
    threading.Thread(target=serve, daemon=True).start()
end = time.time() + LIFE
while time.time() < end and not os.path.exists(STOP):
    if "--print-fps" in argv:
        print("FPS: 140", flush=True)
    time.sleep(1)
'''


def stub_source(name, body, log, stop, base, **consts):
    head = (f"#!{PY3}\nimport json, os, sys, time\nLOG, STOP, NAME, BASE = {str(log)!r}, {str(stop)!r}, {name!r}, "
            f"{str(base)!r}\nLIFE = 60\n" + "".join(f"{k} = {str(v)!r}\n" for k, v in consts.items()))
    return head + STUB_RUNTIME + body


# ---------------------------------------------------------------------------------------------
# PNG fixtures
# ---------------------------------------------------------------------------------------------

def write_png(path, kind):
    """A planted PNG: `uniform` (one flat colour), `black`, `varied` (stripes and a gradient) or `varied2` (a different busy
    picture, so the first and second frame of a run can be told apart)."""
    from PIL import Image
    w, h = 400, 225
    img = Image.new("RGB", (w, h), (30, 60, 90) if kind == "uniform" else (0, 0, 0))
    px = img.load()
    if kind == "varied":
        for x in range(w):
            for y in range(h):
                px[x, y] = ((x * 255) // w, (y * 255) // h, 200 if (x // 50) % 2 else 20)
    elif kind == "varied2":
        for x in range(w):
            for y in range(h):
                px[x, y] = (200 if (x // 25 + y // 25) % 2 else 10, (y * 255) // h, (x * 255) // w)
    img.save(path)
    return Path(path)


def pixels(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return im.size, im.tobytes()


# ---------------------------------------------------------------------------------------------
# The fake xdg portal (copied from tests/method/test_play_proof.py, H-031 piece two) and the fake Mutter
# ---------------------------------------------------------------------------------------------

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

# The fake Mutter: ScreenCast (CreateSession, Session.RecordMonitor/Start/Stop, Stream.PipeWireStreamAdded(node)) and
# RemoteDesktop (CreateSession, Session.Start/Stop/NotifyKeyboardKeysym). Every call is logged with the time.
MUTTER_STUB = r"""
import json, sys, time
from gi.repository import Gio, GLib
log, nodeid = sys.argv[1], int(sys.argv[2])
SC, RD = "org.gnome.Mutter.ScreenCast", "org.gnome.Mutter.RemoteDesktop"
def note(**kw):
    with open(log, "a") as f:
        f.write(json.dumps(dict(kw, t=time.time())) + "\n")
def iface(name, body):
    return Gio.DBusNodeInfo.new_for_xml("<node><interface name='%s'>%s</interface></node>" % (name, body)).interfaces[0]
SC_MAIN = iface(SC, "<method name='CreateSession'><arg type='a{sv}' direction='in'/><arg type='o' direction='out'/></method>")
SC_SESSION = iface(SC + ".Session", "<method name='Start'/><method name='Stop'/><method name='RecordMonitor'><arg type='s' direction='in'/>"
                   "<arg type='a{sv}' direction='in'/><arg type='o' direction='out'/></method><signal name='Closed'/>")
SC_STREAM = iface(SC + ".Stream", "<signal name='PipeWireStreamAdded'><arg type='u'/></signal>")
RD_MAIN = iface(RD, "<method name='CreateSession'><arg type='o' direction='out'/></method>")
RD_SESSION = iface(RD + ".Session", "<method name='Start'/><method name='Stop'/><method name='NotifyKeyboardKeysym'>"
                   "<arg type='u' direction='in'/><arg type='b' direction='in'/></method>")
state = {"n": 0, "streams": {}}
def plain(a):
    return a if isinstance(a, (int, str, bool)) else repr(a)
def on_call(conn, sender, path, iface_name, method, params, inv):
    note(iface=iface_name, method=method, path=path, args=[plain(a) for a in params.unpack()])
    if iface_name == SC and method == "CreateSession":
        state["n"] += 1; p = "/org/gnome/Mutter/ScreenCast/Session/u%d" % state["n"]
        conn.register_object(p, SC_SESSION, on_call, None, None)
        inv.return_value(GLib.Variant("(o)", (p,)))
    elif iface_name == SC + ".Session" and method == "RecordMonitor":
        sp = path.replace("/Session/", "/Stream/")
        conn.register_object(sp, SC_STREAM, on_call, None, None)
        state["streams"][path] = sp
        inv.return_value(GLib.Variant("(o)", (sp,)))
    elif iface_name == SC + ".Session" and method == "Start":
        inv.return_value(None)
        sp = state["streams"].get(path)
        if sp:
            def emit():
                conn.emit_signal(None, sp, SC + ".Stream", "PipeWireStreamAdded", GLib.Variant("(u)", (nodeid,)))
                return False
            GLib.timeout_add(300, emit)
    elif iface_name == RD and method == "CreateSession":
        state["n"] += 1; p = "/org/gnome/Mutter/RemoteDesktop/Session/u%d" % state["n"]
        conn.register_object(p, RD_SESSION, on_call, None, None)
        inv.return_value(GLib.Variant("(o)", (p,)))
    else:
        inv.return_value(None)
def on_bus(conn, name):
    conn.register_object("/org/gnome/Mutter/ScreenCast", SC_MAIN, on_call, None, None)
    conn.register_object("/org/gnome/Mutter/RemoteDesktop", RD_MAIN, on_call, None, None)
owned = []
def on_name(conn, name):
    owned.append(name)
    if len(owned) == 2:
        print("READY", flush=True)
Gio.bus_own_name(Gio.BusType.SESSION, SC, Gio.BusNameOwnerFlags.NONE, on_bus, on_name, None)
Gio.bus_own_name(Gio.BusType.SESSION, RD, Gio.BusNameOwnerFlags.NONE, None, on_name, None)
GLib.MainLoop().run()
"""

# The reference client of the measured capture path (gate-evidence/dark-room/dark_capture.py `cast`, dark_keys.py): the
# calls a hidden_capture.py is expected to make. Used only to prove the fake answers them.
MUTTER_CLIENT = r"""
import sys
from gi.repository import Gio, GLib
conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
SC = "org.gnome.Mutter.ScreenCast"; RD = "org.gnome.Mutter.RemoteDesktop"
def call(dest, path, iface, m, args, sig):
    return conn.call_sync(dest, path, iface, m, args, GLib.VariantType(sig) if sig else None, Gio.DBusCallFlags.NONE, 20000, None)
rd = call(RD, "/org/gnome/Mutter/RemoteDesktop", RD, "CreateSession", None, "(o)").unpack()[0]
call(RD, rd, RD + ".Session", "Start", None, None)
for st in (True, False):
    call(RD, rd, RD + ".Session", "NotifyKeyboardKeysym", GLib.Variant("(ub)", (0xff1b, st)), None)
call(RD, rd, RD + ".Session", "Stop", None, None)
sess = call(SC, "/org/gnome/Mutter/ScreenCast", SC, "CreateSession", GLib.Variant("(a{sv})", ({},)), "(o)").unpack()[0]
stream = call(SC, sess, SC + ".Session", "RecordMonitor", GLib.Variant("(sa{sv})", ("Meta-0", {})), "(o)").unpack()[0]
loop, node = GLib.MainLoop(), {}
def on_sig(c, sender, path, iface, signal, params):
    if signal == "PipeWireStreamAdded":
        node["id"] = params.unpack()[0]; loop.quit()
conn.signal_subscribe(SC, SC + ".Stream", "PipeWireStreamAdded", stream, None, Gio.DBusSignalFlags.NONE, on_sig)
call(SC, sess, SC + ".Session", "Start", None, None)
GLib.timeout_add_seconds(10, loop.quit); loop.run()
call(SC, sess, SC + ".Session", "Stop", None, None)
print(node.get("id"))
"""

DBUS_CONF = """<busconfig><type>session</type><listen>unix:path=%s</listen><auth>EXTERNAL</auth>
<policy context="default"><allow send_destination="*" eavesdrop="true"/><allow eavesdrop="true"/>
<allow own="*"/></policy></busconfig>"""


class Service:
    """A private dbus-daemon plus one python3 Gio service on it. `address` is the bus; `calls()` reads the service's log."""

    def __init__(self, base, name, script, args, env=None):
        self.base = Path(base)
        self.log = self.base / f"{name}-calls.log"
        (self.base / f"{name}-dbus.conf").write_text(DBUS_CONF % (self.base / f"{name}-bus"))
        self.bus = subprocess.Popen(["dbus-daemon", "--config-file", str(self.base / f"{name}-dbus.conf"), "--nofork",
                                     "--print-address"], stdout=subprocess.PIPE, text=True, start_new_session=True)
        self.address = self.bus.stdout.readline().strip()
        assert self.address.startswith("unix:"), "private dbus-daemon did not start: " + repr(self.address)
        (self.base / f"{name}.py").write_text(script)
        self.svc = subprocess.Popen([PY3, str(self.base / f"{name}.py"), *[str(a) for a in args(self)]], stdout=subprocess.PIPE,
                                    text=True, env={**os.environ, "PYTHONWARNINGS": "ignore", "DBUS_SESSION_BUS_ADDRESS": self.address, **(env or {})},
                                    start_new_session=True)
        if self.svc.stdout.readline().strip() != "READY":
            self.close()
            raise AssertionError(f"fake {name} did not take its bus name")

    def calls(self):
        out = []
        for l in (self.log.read_text().splitlines() if self.log.exists() else []):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
        return out

    def close(self):
        for p in (self.svc, self.bus):
            p.terminate()
        for p in (self.svc, self.bus):
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill(); p.wait()


class FakePortal(Service):
    """The fake xdg portal on its own bus. `env` is what a caller adds to its environment; `pictures` is where it writes."""

    def __init__(self, base, src_png, home, code=0):
        self.home = Path(home)
        (self.home / ".config").mkdir(parents=True, exist_ok=True)
        (self.home / ".config" / "user-dirs.dirs").write_text('XDG_PICTURES_DIR="%s/Pictures"\n' % self.home)
        self.pictures = self.home / "Pictures"
        super().__init__(base, "portal", PORTAL_STUB, lambda s: [src_png, code, s.log], env={"HOME": str(self.home)})
        self.env = {"DBUS_SESSION_BUS_ADDRESS": self.address, "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config")}


class FakeMutter(Service):
    def __init__(self, base):
        super().__init__(base, "mutter", MUTTER_STUB, lambda s: [s.log, NODE_ID])


# ---------------------------------------------------------------------------------------------
# The rig and one run of play.sh
# ---------------------------------------------------------------------------------------------

SESSION_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_SYSTEM_BUS_ADDRESS", "XDG_RUNTIME_DIR", "XAUTHORITY",
                "SSH_AUTH_SOCK", "XDG_SESSION_ID", "XDG_SESSION_TYPE", "XDG_SESSION_CLASS", "XDG_SEAT", "XDG_VTNR",
                "XDG_SESSION_DESKTOP", "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "GNOME_SETUP_DISPLAY",
                "OM_PUSH_DIR", "OM_SOCK_DIR", "OM_MAIN")  # the OM_ ones: proc.py would write its register into the real om-push


def marked_pids(marker):
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
    """Ends every process still carrying `marker` (a temp dir unique to one run): TERM, then KILL; the marker is re-read
    before each signal so a reused pid is never touched. Returns how many there were."""
    n = len(marked_pids(marker))
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in marked_pids(marker):
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        t0 = time.time()
        while marked_pids(marker) and time.time() - t0 < 3:
            time.sleep(0.1)
    return n


class Run:
    """One world and one play.sh run in it. `frames` are the PNG kinds the stub gst writes for its first, second, ... call;
    `portal_png` is what the fake portal would write; `real` adds --real; `check=False` is the plain real-display run of a human;
    `display=False` takes DISPLAY and WAYLAND_DISPLAY out of the caller's environment; `scrub=True` plants a real-looking session
    in the caller's environment (a dead /run/user bus, other display names) and puts the recording wrapper in front of
    hidden_desktop.sh; `lock_probe` samples play.lock while it runs."""

    def __init__(self, frames=("varied", "varied2"), portal_png="varied", real=False, lock_probe=False, wayland=True,
                 check=True, display=True, scrub=False):
        self.base = Path(tempfile.mkdtemp(prefix="h85-")).resolve()
        self.real, self.lock_probe, self.frames_kind, self.portal_kind, self.wayland = real, lock_probe, frames, portal_png, wayland
        self.check, self.display, self.scrub = check, display, scrub
        self.procs, self.services = [], []
        self.lock_held_samples, self.lock_free_after = 0, None
        self.rc, self.timed_out = None, False

    def setup(self):
        """Builds the world. Separate from __init__ so a failure half way is still torn down (the caller registers the run first)."""
        b, frames, portal_png, wayland = self.base, self.frames_kind, self.portal_kind, self.wayland
        scrub, display = self.scrub, self.display
        self.home = b / "home"; (self.home / ".local" / "bin").mkdir(parents=True)
        self.tmp = b / "tmp"; self.tmp.mkdir()
        self.bin = b / "bin"; self.bin.mkdir()
        (b / "run").mkdir(mode=0o700)
        self.log, self.stop = b / "stubs.log", b / "stop"
        (b / "frames").mkdir()
        self.frame_files = [write_png(b / "frames" / f"f{i}.png", k) for i, k in enumerate(frames)]
        self.portal_src = write_png(b / "portal-src.png", portal_png)
        (b / "plan.json").write_text(json.dumps([str(f) for f in self.frame_files]))
        self.mutter = FakeMutter(b); self.services.append(self.mutter)
        self.portal = FakePortal(b, self.portal_src, self.home); self.services.append(self.portal)
        (b / "hidden-bus-address").write_text(self.mutter.address)
        common = (self.log, self.stop, b)
        for name, body, consts in (("gnome-shell", SHELL_BODY, {}), ("pipewire", HOLD_BODY, {}), ("wireplumber", HOLD_BODY, {}),
                                   ("dbus-run-session", DBUS_BODY, {"BUSFILE": b / "hidden-bus-address"}),
                                   ("gst-launch-1.0", GST_BODY, {"PLAN": b / "plan.json"})):
            (self.bin / name).write_text(stub_source(name, body, *common, **consts)); (self.bin / name).chmod(0o755)
        gd = self.home / ".local" / "bin" / "godot.real"
        gd.write_text(stub_source("godot", GODOT_BODY, *common)); gd.chmod(0o755)
        self.tree = self.make_tree()
        env = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}
        env.update(PATH=f"{self.bin}:{env['PATH']}", TMPDIR=str(self.tmp), DISPLAY=":99", XDG_RUNTIME_DIR=str(b / "run"))
        env.update(self.portal.env)  # HOME (the fake home the stub Godot lives in), the caller's session bus (the fake portal's), XDG_CONFIG_HOME
        if wayland:
            env["WAYLAND_DISPLAY"] = "wayland-99"
        # Variables a clean hidden run must not pass on (H-085 Rulings 2). The planted bus is a dead address that merely looks real
        # (uid 999999 has no /run/user): nothing that connects to it can reach a real session.
        env.update(XAUTHORITY=str(b / "xauth-probe"), SSH_AUTH_SOCK=f"/tmp/h85-leak-ssh-{os.getpid()}", OM_LEAK_PROBE=f"h85-leak-{os.getpid()}")
        if scrub:
            env.update(DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/999999/bus", DISPLAY=":77", WAYLAND_DISPLAY="wayland-77")
        if not display:
            env.pop("DISPLAY", None); env.pop("WAYLAND_DISPLAY", None)
        self.env = env
        self.lock_path = self.home / "Projects" / "om-push" / "play.lock"

    def make_tree(self):
        tree = self.base / "fake_tree"; (tree / "scripts" / "method").mkdir(parents=True)
        (tree / "scripts" / "build_pipe_linux.sh").write_text("#!/bin/sh\nmkdir -p dist/linux && echo stub > dist/linux/ouroboros_pipe\n")
        (tree / "scripts" / "build_pipe_linux.sh").chmod(0o755)
        shutil.copytree(ROOT / "scripts" / "specfactory", tree / "scripts" / "specfactory",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "scripts" / "method" / "proc.py", tree / "scripts" / "method" / "proc.py")
        if self.scrub:
            real = tree / "scripts" / "specfactory" / "hidden_desktop.sh"
            if real.exists():
                real.rename(real.with_name("hidden_desktop_real.sh"))
            real.write_text(wrapper_source(self.log)); real.chmod(0o755)
        (tree / "project.godot").write_text('config_version=5\n[application]\nrun/main_scene="%s"\n' % SCENE)
        g = ["git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g[:3] + ["init", "-q"], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "fake tree"], check=True)
        return tree

    def calls(self, name=None):
        rows = []
        for l in (self.log.read_text().splitlines() if self.log.exists() else []):
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass
        return [r for r in rows if name is None or r["stub"] == name]

    def launch(self):
        """The stub Godot's launch row (the one that is not the --import)."""
        rows = [r for r in self.calls("godot") if "argv" in r and "--import" not in r["argv"]]
        return rows[0] if rows else None

    def qa_first_answer(self):
        """Time of the stub game's first answer on its qa port, or None."""
        rows = [r for r in self.calls("godot") if r.get("qa_answered")]
        return rows[0]["t"] if rows else None

    def try_lock(self):
        """True when play.lock is held by someone else right now."""
        if not self.lock_path.exists():
            return False
        fd = os.open(self.lock_path, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
        finally:
            os.close(fd)

    def execute(self):
        args = (["--tree", str(self.tree), "--scene", SCENE] + (["--check"] if self.check else []) + ["--keep"]
                + (["--real"] if self.real else []))
        out = open(self.base / "play-out.txt", "w")
        p = subprocess.Popen(["bash", str(PLAY), *args], cwd=ROOT, env=self.env, stdout=out, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        self.procs.append(p)
        t0 = time.time()
        while p.poll() is None and time.time() - t0 < PLAY_PATIENCE_S:
            if self.lock_probe and self.launch() is not None and self.try_lock():
                self.lock_held_samples += 1
            time.sleep(0.5)
        if p.poll() is None:
            self.timed_out = True
            os.killpg(p.pid, signal.SIGTERM)
        self.rc = p.wait(timeout=30)
        self.lock_free_after = not self.try_lock()
        out.close()
        return self

    @property
    def stdout(self):
        return (self.base / "play-out.txt").read_text()

    @property
    def lines(self):
        return self.stdout.splitlines()

    @property
    def scratch(self):
        m = re.search(r"^scratch: (\S+)$", self.stdout, re.M)
        assert m, "play.sh printed no `scratch:` line: " + self.stdout
        return Path(m.group(1))

    def proof_line(self):
        for l in self.lines:
            m = re.fullmatch(r"PLAY proof (\S+) (\S+)", l)
            if m:
                return m.groups()
        return None

    def gst_calls(self):
        return [r for r in self.calls("gst-launch-1.0") if "invocation" in r]

    def teardown(self):
        if hasattr(self, "stop"):
            self.stop.touch()
        for p in self.procs:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except OSError:
                pass
        for s in self.services:
            s.close()
        reap_marked(str(self.base))
        shutil.rmtree(self.base, ignore_errors=True)


@pytest.fixture(scope="module")
def runs():
    """`runs(name)` executes the named scenario once and caches it; every scenario is torn down at the end of the module."""
    scenarios = {
        "hidden_ok": dict(frames=("varied", "varied2"), lock_probe=True),
        "hidden_second_flat": dict(frames=("varied", "uniform")),
        "hidden_first_flat": dict(frames=("uniform", "varied2")),
        "real_ok": dict(real=True, portal_png="varied", frames=("varied", "varied2")),
        "hidden_scrub": dict(scrub=True),
        "hidden_nodisplay": dict(display=False),
        "real_nodisplay": dict(real=True, display=False),
        "plain_ok": dict(check=False),
        "plain_nodisplay": dict(check=False, display=False),
    }
    cache, made = {}, []

    def get(name):
        if name not in cache:
            r = Run(**scenarios[name]); made.append(r)
            r.setup()
            cache[name] = r.execute()
        return cache[name]
    try:
        yield get
    finally:
        for r in made:
            r.teardown()


# ---------------------------------------------------------------------------------------------
# Dry-run goldens: what main's play.sh prints (dumped from origin/main bd93d4a3 with HOME=/tmp/fakehome)
# ---------------------------------------------------------------------------------------------

def golden_dry(home, check, wayland):
    """main's `play.sh --tree ROOT --dry-run [--check]` output, built from the pieces main prints."""
    drv = "--display-driver wayland " if wayland else ""
    envp = f"XDG_DATA_HOME={ROOT}/xdg " if check else ""
    s = (f"tree: {ROOT}\nbuild: cd {ROOT} && scripts/build_pipe_linux.sh\n"
         f"launch: {envp}{home}/.local/bin/godot.real --path {ROOT} {drv}--windowed --resolution {RES} -- \n")
    if check:
        s += f"capture: {ROOT}/scripts/specfactory/screen_capture.sh {ROOT}/proof.png\n"
    return s


def dry(args, wayland, home="/tmp/h85-fakehome"):
    env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "DISPLAY")}
    env["HOME"] = home
    if wayland:
        env["WAYLAND_DISPLAY"] = "wayland-99"
    return subprocess.run(["bash", str(PLAY), "--tree", str(ROOT), "--dry-run", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=120)


# ---------------------------------------------------------------------------------------------
# Controls: green today (no hidden-desktop code involved), so a red below means the feature, not the rig
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("wayland", [False, True])
def test_control_plain_dry_run_is_main_s_output_byte_for_byte(wayland):
    """H-085 Tests, positive control for the `--real` dry-run test (green today and after): "`--real` dry-run output is
    byte-identical to main's". Without `--check` nothing in Change 2 or 3 applies, so the plain dry run is main's output
    exactly; this pins the golden builder `golden_dry` and the harness that compares against it."""
    r = dry([], wayland)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout == golden_dry("/tmp/h85-fakehome", check=False, wayland=wayland), r.stdout


def test_control_fake_portal_answers_the_screenshot_contract():
    """H-085 Tests, positive control for "the fake portal got no call (control: `--real` calls it and prints `portal`)"
    (green today; no script under test is involved): a client making the portal's Screenshot call on the fake bus gets
    Response 0 with the file's uri and the fake logs the call, so a hidden-mode run that logs none really did not call it."""
    base = Path(tempfile.mkdtemp(prefix="h85-"))
    try:
        home = base / "home"; home.mkdir()
        portal = FakePortal(base, write_png(base / "src.png", "varied"), home)
        try:
            r = subprocess.run([PY3, "-c", PORTAL_CLIENT], env={**os.environ, **portal.env}, capture_output=True, text=True, timeout=30)
            assert r.returncode == 0 and r.stdout.split()[0] == "0", r.stdout + r.stderr
            assert portal.calls() == [{"method": "Screenshot", "parent": "", "options": {"interactive": False}}]
        finally:
            portal.close()
    finally:
        reap_marked(str(base)); shutil.rmtree(base, ignore_errors=True)


def test_control_fake_mutter_answers_the_measured_capture_calls_and_logs_them():
    """H-085 Measured: "A capture by Mutter ScreenCast through a private pipewire (`gst pipewiresrc` to PNG)" and "an Escape key
    through the private `org.gnome.Mutter.RemoteDesktop` leaves [the Overview]". Positive control (green today): a client
    making the reference calls (RemoteDesktop CreateSession, Start, NotifyKeyboardKeysym Escape down and up, Stop; ScreenCast
    CreateSession, RecordMonitor, Start, the PipeWireStreamAdded signal, Stop) on the fake gets the node id and the fake logs
    each call with its arguments, so the play tests below can tell an Escape and a capture from silence."""
    base = Path(tempfile.mkdtemp(prefix="h85-"))
    try:
        mutter = FakeMutter(base)
        try:
            r = subprocess.run([PY3, "-c", MUTTER_CLIENT], env={**os.environ, "DBUS_SESSION_BUS_ADDRESS": mutter.address},
                               capture_output=True, text=True, timeout=30)
            assert r.returncode == 0 and r.stdout.strip() == str(NODE_ID), r.stdout + r.stderr
            seen = [(c["method"], c["args"]) for c in mutter.calls()]
            assert ("NotifyKeyboardKeysym", [ESCAPE, True]) in seen and ("NotifyKeyboardKeysym", [ESCAPE, False]) in seen, seen
            assert [m for m, _ in seen if m in ("CreateSession", "RecordMonitor", "Start", "Stop")].count("Start") == 2, seen
        finally:
            mutter.close()
    finally:
        reap_marked(str(base)); shutil.rmtree(base, ignore_errors=True)


def test_control_stub_gst_writes_the_planned_frame_for_each_invocation():
    """H-085 Tests, positive control for the frame tests below (green today): the stub `gst-launch-1.0` called twice with the
    measured arguments (`num-buffers`, `multifilesink location=<base>.%02d.png`) writes the first planned PNG on the first call
    and the second on the second, `num-buffers` copies each, so "the proof is the second" is observable."""
    base = Path(tempfile.mkdtemp(prefix="h85-"))
    try:
        a, b = write_png(base / "a.png", "varied"), write_png(base / "b.png", "varied2")
        assert pixels(a) != pixels(b)
        (base / "plan.json").write_text(json.dumps([str(a), str(b)]))
        stub = base / "gst-launch-1.0"
        stub.write_text(stub_source("gst-launch-1.0", GST_BODY, base / "log", base / "stop", base, PLAN=base / "plan.json")); stub.chmod(0o755)
        for n in (1, 2):
            args = ["-q", "pipewiresrc", f"path={NODE_ID}", "num-buffers=3", "!", "videoconvert", "!", "pngenc", "!", "multifilesink",
                    f"location={base}/cast{n}.%02d.png"]
            assert subprocess.run([str(stub), *args], capture_output=True, text=True, timeout=20).returncode == 0
        assert [pixels(base / f"cast1.0{i}.png") for i in range(3)] == [pixels(a)] * 3
        assert [pixels(base / f"cast2.0{i}.png") for i in range(3)] == [pixels(b)] * 3
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_control_planted_pngs_busy_ones_differ_and_flat_ones_are_flat():
    """H-085 Tests, positive control for the flat-frame tests (green today; checks the fixtures, not the script): `varied` and
    `varied2` are busy and differ from each other, `uniform` and `black` are one colour."""
    from PIL import Image
    base = Path(tempfile.mkdtemp(prefix="h85-"))
    try:
        for kind, flat in (("uniform", True), ("black", True), ("varied", False), ("varied2", False)):
            colors = Image.open(write_png(base / f"{kind}.png", kind)).convert("RGB").getcolors(maxcolors=1 << 20)
            assert (len(colors) == 1) == flat, (kind, len(colors))
        assert pixels(base / "varied.png") != pixels(base / "varied2.png")
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# Change 2 and 3, dry runs
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("caller_wayland", [False, True])
def test_check_dry_run_shows_the_wayland_driver_on_wayland_dark_and_no_portal(caller_wayland):
    """H-085 Tests: "`play.sh --check --dry-run` shows the Wayland driver with `WAYLAND_DISPLAY=wayland-dark`, no portal call".
    Change 2: "`play.sh --check` runs the game inside it by default: Wayland driver, `--windowed --resolution $RESOLUTION`".
    Whatever session the caller is in (a Wayland one with WAYLAND_DISPLAY set, or none), the dry run holds
    `--display-driver wayland --windowed --resolution 1919x1080` on the launch line and `WAYLAND_DISPLAY=wayland-dark`, never the
    caller's display name, and no `screen_capture.sh` (the portal capture) anywhere."""
    r = dry(["--check"], caller_wayland)
    assert r.returncode == 0, r.stdout + r.stderr
    launch = [l for l in r.stdout.splitlines() if l.startswith("launch:")]
    assert launch and f"--display-driver wayland --windowed --resolution {RES}" in launch[0], f"launch line lacks the Wayland driver: {launch}"
    assert f"WAYLAND_DISPLAY={DISPLAY_NAME}" in r.stdout, f"no WAYLAND_DISPLAY={DISPLAY_NAME} in the dry run: {r.stdout}"
    assert "wayland-99" not in r.stdout, f"the caller's display name is in the dry run: {r.stdout}"
    assert "screen_capture.sh" not in r.stdout and "portal" not in r.stdout.lower(), f"the dry run still names the portal capture: {r.stdout}"


@pytest.mark.parametrize("wayland", [False, True])
def test_real_check_dry_run_is_main_s_output_byte_for_byte(wayland):
    """H-085 Tests: "`--real` dry-run output is byte-identical to main's". Change 3: "`play.sh --check --real` is today's
    behaviour unchanged: the real display, the portal capture". `--check --real --dry-run` (and `--real --check`) print exactly
    what main's `--check --dry-run` printed: the golden of test_control_plain_dry_run_is_main_s_output_byte_for_byte plus the
    `XDG_DATA_HOME` scratch prefix and the `capture:` line naming screen_capture.sh. Both session kinds."""
    want = golden_dry("/tmp/h85-fakehome", check=True, wayland=wayland)
    for args in (["--check", "--real"], ["--real", "--check"]):
        r = dry(args, wayland)
        assert r.returncode == 0, f"{args}: " + r.stdout + r.stderr
        assert r.stdout == want, f"{args}: " + r.stdout


# ---------------------------------------------------------------------------------------------
# Change 2: the hidden proof (stubs reach the scene)
# ---------------------------------------------------------------------------------------------

def test_check_prints_the_proof_line_ending_hidden_after_the_scene_is_reached(runs):
    """H-085 Tests: "With stubs reaching the scene `--check` prints `PLAY proof <path> hidden`". Change 2: "It prints `PLAY proof
    <path> hidden`". The run exits 0, prints `PLAY scene <scene> reached`, and after it `PLAY proof <scratch>/proof.png hidden`;
    the file exists. Control: test_real_check_calls_the_portal_and_prints_portal (the same run shape, ending `portal`)."""
    r = runs("hidden_ok")
    assert r.rc == 0 and not r.timed_out, r.stdout
    scene_i = next((i for i, l in enumerate(r.lines) if l == f"PLAY scene {SCENE} reached"), None)
    assert scene_i is not None, r.stdout
    found = [(i, l) for i, l in enumerate(r.lines) if re.fullmatch(r"PLAY proof \S+ hidden", l)]
    assert found, "no `PLAY proof <path> hidden` line: " + r.stdout
    assert found[0][0] > scene_i, r.stdout
    path = found[0][1].split()[2]
    assert path == f"{r.scratch}/proof.png" and Path(path).is_file(), (path, r.stdout)


def test_check_does_not_call_the_portal(runs):
    """H-085 Tests: "the fake portal got no call (control: `--real` calls it and prints `portal`)". Change 2: the hidden proof
    replaces the portal capture. The fake portal on the caller's session bus logged no call and wrote nothing to Pictures,
    and no output line ends `portal`."""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    assert r.portal.calls() == [], "the portal was called: " + repr(r.portal.calls())
    assert not list(r.portal.pictures.glob("Screenshot*")) if r.portal.pictures.exists() else True
    assert not any(re.fullmatch(r"PLAY proof \S+ portal", l) for l in r.lines), r.stdout


def test_check_proof_is_the_second_of_two_frames(runs):
    """H-085 Change 2: "`hidden_capture.py` takes two frames about 3 s apart; the proof is the second." The stub `gst-launch-1.0`
    was called twice (one capture per frame), the first call wrote the first planted picture and the second call the second, and
    `proof.png` holds the second (and not the first). The "about 3 s" is not tested: the story gives no tolerance."""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    assert len(r.gst_calls()) == 2, f"expected two frames, got {len(r.gst_calls())}: " + r.stdout
    proof = r.proof_line()
    assert proof and proof[1] == "hidden", r.stdout
    first, second = (pixels(f) for f in r.frame_files)
    assert pixels(proof[0]) == second and pixels(proof[0]) != first, "proof.png is not the second frame"


def test_check_launches_the_game_into_the_hidden_desktop(runs):
    """H-085 Change 2: "`play.sh --check` runs the game inside it by default: Wayland driver, `--windowed --resolution
    $RESOLUTION`". The stub Godot's argv holds `--display-driver wayland --windowed --resolution 1919x1080`; its environment
    names the hidden desktop (WAYLAND_DISPLAY wayland-dark, the XDG_RUNTIME_DIR the stub shell made its socket in, the session
    bus the stub dbus-run-session handed out) and not the caller's wayland-99 or the caller's bus; XDG_DATA_HOME is still the
    scratch `<tree>/xdg` (DEC-play-check-scratch-userdir)."""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    g = r.launch()
    assert g, "the game was never launched: " + r.stdout
    argv = g["argv"]
    assert argv[argv.index("--display-driver") + 1] == "wayland" and "--windowed" in argv, argv
    assert argv[argv.index("--resolution") + 1] == RES, argv
    shell = r.calls("gnome-shell")
    assert shell, "play.sh never started the hidden desktop (no gnome-shell launch): " + r.stdout
    env = g["env"]
    assert env.get("WAYLAND_DISPLAY") == DISPLAY_NAME, env.get("WAYLAND_DISPLAY")
    assert env.get("XDG_RUNTIME_DIR") == shell[0]["env"]["XDG_RUNTIME_DIR"], env.get("XDG_RUNTIME_DIR")
    assert env.get("DBUS_SESSION_BUS_ADDRESS") == r.mutter.address != r.portal.address, env.get("DBUS_SESSION_BUS_ADDRESS")
    assert env.get("XDG_DATA_HOME") == f"{r.scratch}/xdg", env.get("XDG_DATA_HOME")


def test_check_sends_escape_through_the_private_remote_desktop_between_the_qa_answer_and_the_first_frame(runs):
    """H-085 Measured: "The private shell starts in its Overview: an Escape key through the private
    `org.gnome.Mutter.RemoteDesktop` leaves it." Change 2: "the Escape key, `SETTLE_S`, then `hidden_capture.py` takes two
    frames". Rulings 4: "Escape is sent after the qa port answers and before the first frame ... Tests accept any Escape inside
    that interval". On the fake Mutter's bus the Escape keysym was pressed and released (and no other key), after the stub game's
    qa port first answered and before the first frame was taken."""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    keys = [c for c in r.mutter.calls() if c["method"] == "NotifyKeyboardKeysym"]
    assert keys, "no key was sent through the private RemoteDesktop: " + repr(r.mutter.calls())
    assert all(c["args"][0] == ESCAPE for c in keys), [c["args"] for c in keys]
    assert [c["args"][1] for c in keys][:2] == [True, False], [c["args"] for c in keys]
    qa, first_frame = r.qa_first_answer(), r.gst_calls()[0]["t"]
    assert qa is not None, "the stub game's qa port never answered"
    assert qa < keys[0]["t"] < first_frame, f"Escape at {keys[0]['t'] - qa:+.1f}s from the qa answer, first frame at {first_frame - qa:+.1f}s"


def test_check_starts_the_hidden_desktop_through_proc_py_with_a_ttl(runs):
    """H-085 Change 1: "It is started through `proc.py start` with a TTL and ends by `timeout`, never by hand." Reading: play.sh is
    the one that starts it. The process register under the fake HOME (`$HOME/Projects/om-push/procs`, where proc.py writes when
    OM_PUSH_DIR is not set) holds a record whose command names `hidden_desktop.sh` and whose `ttl_s` is a positive integer.
    The TTL's value is not in the story and is not tested. (Not tested: that the daemons end by `timeout`.)"""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    pdir = r.home / "Projects" / "om-push" / "procs"
    recs = []
    for f in sorted(pdir.glob("*.json")) if pdir.exists() else []:
        try:
            recs.append(json.loads(f.read_text()))
        except ValueError:
            pass
    hidden = [x for x in recs if any(str(w).endswith("hidden_desktop.sh") for w in x.get("cmd", []))]
    assert hidden, f"no proc.py record names hidden_desktop.sh (records: {[x.get('cmd') for x in recs]})"
    assert all(isinstance(x.get("ttl_s"), int) and x["ttl_s"] > 0 for x in hidden), [x.get("ttl_s") for x in hidden]


def test_check_keeps_play_lock_while_it_runs_and_frees_it_when_it_exits(runs):
    """H-085 Change 2: "It prints `PLAY proof <path> hidden` and keeps `play.lock` (load stays as today)"; H-059: one run at a time
    holds play.lock until play.sh exits (the game never keeps it). The test took the lock's temperature every half second
    after the game launched: held at least once during the run, and free the moment play.sh exited, though the hidden desktop's
    stub daemons may still be up (a daemon that inherited the lock fd would hold it)."""
    r = runs("hidden_ok")
    assert r.rc == 0, r.stdout
    assert r.lock_held_samples >= 1, "play.lock was never held by the running play.sh"
    assert r.lock_free_after, "play.lock is still held after play.sh exited"


@pytest.mark.parametrize("scenario,why", [("hidden_second_flat", "the second frame, the proof, is flat")])
def test_check_with_a_flat_proof_frame_is_rejected(runs, scenario, why):
    """H-085 Tests: "a planted flat frame prints `PLAY REJECT proof capture failed` (control: a busy one passes)". Change 2: "Blank
    rule as today (reject only at fraction 0)". The stub gst writes a busy first frame and a flat second one: the run prints
    `PLAY REJECT proof capture failed`, exits non-zero and prints no `PLAY proof` line. Control: the hidden_ok run (busy second
    frame) passes in test_check_prints_the_proof_line_ending_hidden_after_the_scene_is_reached."""
    r = runs(scenario)
    assert f"PLAY scene {SCENE} reached" in r.lines, "the run did not reach the scene: " + r.stdout
    assert len(r.gst_calls()) >= 1, "no frame was taken, so no verdict on a flat frame: " + r.stdout
    assert any(l.startswith("PLAY REJECT proof capture failed") for l in r.lines), r.stdout
    assert r.rc not in (0, None) and not any(l.startswith("PLAY proof") for l in r.lines), (r.rc, r.stdout)


def test_check_with_a_flat_first_frame_and_a_busy_second_passes(runs):
    """H-085 Change 2: "takes two frames about 3 s apart; the proof is the second". Reading: the first frame is not judged (a
    compositor's first frame can be stale), so a flat first and a busy second pass and the proof is the second. This is the
    other polarity of test_check_with_a_flat_proof_frame_is_rejected and, with it, pins which frame counts."""
    r = runs("hidden_first_flat")
    assert r.rc == 0, r.stdout
    proof = r.proof_line()
    assert proof and proof[1] == "hidden", f"no `PLAY proof <path> hidden` line (a flat first frame must not reject): {r.stdout}"
    assert pixels(proof[0]) == pixels(r.frame_files[1]), "proof.png is not the (busy) second frame"


# ---------------------------------------------------------------------------------------------
# Change 3: --real is today's behaviour
# ---------------------------------------------------------------------------------------------

def test_real_check_calls_the_portal_and_prints_portal(runs):
    """H-085 Change 3: "`play.sh --check --real` is today's behaviour unchanged: the real display, the portal capture, `PLAY proof
    <path> portal`". Tests: "(control: `--real` calls it and prints `portal`)". The fake portal got exactly one Screenshot call,
    the proof is its picture, the line is `PLAY proof <scratch>/proof.png portal`; the hidden desktop was not started (no
    gnome-shell, no frame, no Mutter call); the game got the caller's own display (WAYLAND_DISPLAY wayland-99, the caller's bus)."""
    r = runs("real_ok")
    assert r.rc == 0, "`--real` is not accepted or the run failed: " + r.stdout
    proof = r.proof_line()
    assert proof and proof[1] == "portal" and proof[0] == f"{r.scratch}/proof.png", r.stdout
    assert len(r.portal.calls()) == 1 and r.portal.calls()[0]["method"] == "Screenshot", r.portal.calls()
    assert pixels(proof[0]) == pixels(r.portal_src)
    assert not r.calls("gnome-shell") and not r.gst_calls() and not r.mutter.calls(), "--real started the hidden desktop"
    env = r.launch()["env"]
    assert env.get("WAYLAND_DISPLAY") == "wayland-99" and env.get("DBUS_SESSION_BUS_ADDRESS") == r.portal.address, env


# ---------------------------------------------------------------------------------------------
# Rulings 2: play.sh scrubs the caller's session; Rulings 3: hidden mode needs no real display
# ---------------------------------------------------------------------------------------------

SESSION_PLANTED = ("HOME", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "DISPLAY", "XAUTHORITY")
LEAK_PROBES = ("OM_LEAK_PROBE", "SSH_AUTH_SOCK")


def test_check_passes_none_of_the_callers_session_to_the_hidden_desktop_or_the_game(runs):
    """H-085 Rulings 2: "`play.sh` starts `hidden_desktop.sh` and the game with a clean environment: only `PATH`, `TMPDIR`, `LANG`, the
    software-EGL variables and the hidden session's own values; never the caller's `HOME`, `DBUS_SESSION_BUS_ADDRESS`,
    `XDG_RUNTIME_DIR`, `WAYLAND_DISPLAY`, `DISPLAY`, `XAUTHORITY`." The caller's environment carries a fake real HOME (the fake home
    the stub game lives in), a dead `unix:path=/run/user/999999/bus`, a XDG_RUNTIME_DIR, `wayland-77`, `:77` and an XAUTHORITY, plus an
    ssh socket and a probe variable. A recording wrapper in front of the real hidden_desktop.sh and the stub game record their
    environments: neither holds any of those values (a different value, or none, is fine: the hidden session's own).
    Control: test_real_check_game_sees_the_callers_session_variables (a `--real` run's game holds every one of them)."""
    r = runs("hidden_scrub")
    wrapper = r.calls("hidden_desktop")
    assert wrapper, "play.sh never ran hidden_desktop.sh: " + r.stdout
    for name in SESSION_PLANTED + LEAK_PROBES:
        assert wrapper[0]["env"].get(name) != r.env[name], f"hidden_desktop.sh was handed the caller's {name}={r.env[name]}"
    game = r.launch()
    assert game, "play.sh never launched the game: " + r.stdout
    for name in SESSION_PLANTED + LEAK_PROBES:
        assert game["env"].get(name) != r.env[name], f"the game was handed the caller's {name}={r.env[name]}"
    assert r.rc == 0 and (r.proof_line() or ("", ""))[1] == "hidden", "the scrubbed run did not prove: " + r.stdout


def test_real_check_game_sees_the_callers_session_variables(runs):
    """H-085 Rulings 2 control: the variables the hidden run must scrub are visible to a `--real` run's game (the real display
    keeps the caller's session; `--real` is today's behaviour, Change 3). The stub game of the `--real` run holds the caller's HOME,
    session bus, runtime dir, WAYLAND_DISPLAY, DISPLAY and XAUTHORITY, so their absence in the hidden run is the scrub and
    not a stub that cannot see them."""
    r = runs("real_ok")
    assert r.rc == 0, "`--real` is not accepted or the run failed: " + r.stdout
    env = r.launch()["env"]
    for name in SESSION_PLANTED:
        assert env.get(name) == r.env[name], f"the --real game lost {name}: {env.get(name)!r} != {r.env[name]!r}"


def test_control_plain_run_game_sees_the_callers_session_variables(runs):
    """H-085 Rulings 2 control, green today: a plain `play.sh` (no `--check`, the human's real-display run) launches the stub game
    with the caller's HOME, session bus, runtime dir, WAYLAND_DISPLAY, DISPLAY and XAUTHORITY intact, so the stub game does record
    them when they are passed."""
    r = runs("plain_ok")
    assert r.rc == 0 and r.launch(), "the plain run did not launch the game: " + r.stdout
    env = r.launch()["env"]
    for name in SESSION_PLANTED:
        assert env.get(name) == r.env[name], f"the plain run's game lost {name}: {env.get(name)!r} != {r.env[name]!r}"


def test_check_without_any_display_variable_runs_and_proves_hidden(runs):
    """H-085 Rulings 3: "Hidden mode needs no real session. `play.sh --check` (hidden) works from a shell with no `DISPLAY` and no
    `WAYLAND_DISPLAY` (a clerk at night)". The caller's environment has neither; the run does not exit `play.sh: no display`, reaches
    the scene and prints `PLAY proof <path> hidden`. Control: test_control_plain_run_without_any_display_variable_exits_no_display
    (the same environment, a real-display run, exits `no display`)."""
    r = runs("hidden_nodisplay")
    assert "DISPLAY" not in r.env and "WAYLAND_DISPLAY" not in r.env, "the rig left a display variable in: " + repr(r.env)
    assert "play.sh: no display" not in r.stdout, "hidden mode asked for a real display: " + r.stdout
    assert r.rc == 0, r.stdout
    proof = r.proof_line()
    assert proof and proof[1] == "hidden" and f"PLAY scene {SCENE} reached" in r.lines, r.stdout


def test_real_check_without_any_display_variable_exits_no_display(runs):
    """H-085 Rulings 3: "only `--real` still exits `play.sh: no display`" ("`--real` with both unset exits \\"no display\\""). With neither
    DISPLAY nor WAYLAND_DISPLAY, `play.sh --check --real` prints `play.sh: no display`, exits non-zero and launches nothing."""
    r = runs("real_nodisplay")
    assert "DISPLAY" not in r.env and "WAYLAND_DISPLAY" not in r.env, "the rig left a display variable in: " + repr(r.env)
    assert "play.sh: no display" in r.lines, "`--real` without a display did not exit `no display`: " + r.stdout
    assert r.rc not in (0, None) and r.launch() is None, (r.rc, r.stdout)


def test_control_plain_run_without_any_display_variable_exits_no_display(runs):
    """H-085 Rulings 3 control, green today and after: a plain real-display `play.sh` with neither DISPLAY nor WAYLAND_DISPLAY prints
    `play.sh: no display`, exits non-zero and launches nothing (DEC-play-display-check-first-2026-10-30), so the hidden run above
    got past a check that the real-display run still fails."""
    r = runs("plain_nodisplay")
    assert "DISPLAY" not in r.env and "WAYLAND_DISPLAY" not in r.env, "the rig left a display variable in: " + repr(r.env)
    assert "play.sh: no display" in r.lines, r.stdout
    assert r.rc not in (0, None) and r.launch() is None, (r.rc, r.stdout)
