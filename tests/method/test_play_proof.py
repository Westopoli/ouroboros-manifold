"""H-031 proof-by-eyes, first piece: tests for scripts/play.sh (docs/stories/H-031.md).

Nothing here opens a window or captures a screen. play.sh is driven through its
`--dry-run` launch line and through a fake tree, a fake HOME whose
`.local/bin/godot.real` is a stub (it logs its argv, prints `FPS: <n>` once a second
when given `--print-fps`, and answers the QA port's `["state"]` with a scene), and stub
`xdotool` / `xwininfo` programs ahead of the real ones on PATH.
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
SCENE = "res://scenes/stub/stub.tscn"

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
    `--display-driver wayland --windowed --resolution 1920x1080` on the launch line.\""""
    line = dry_launch_line(wayland=True)
    assert "--display-driver wayland --windowed --resolution 1920x1080" in line, line


def test_dry_run_without_wayland_display_has_no_driver_flag_but_windowed():
    """H-031 First piece, Tests: "Dry run without it prints no wayland flag but still
    `--windowed`." (`--resolution 1920x1080` is always present: "always `--windowed
    --resolution <DRAFT-play-resolution 1920x1080>`".)"""
    line = dry_launch_line(wayland=False)
    assert "wayland" not in line and "--display-driver" not in line, line
    assert "--windowed" in line, line
    assert "--resolution 1920x1080" in line, line


def test_real_launch_argv_carries_the_flags_under_wayland_and_not_under_x11():
    """H-031 First piece: "play.sh launches Godot with `--display-driver wayland` when
    `WAYLAND_DISPLAY` is set in the environment, else X11 as today, and always `--windowed
    --resolution <DRAFT-play-resolution 1920x1080>`." Checked on the argv the stub Godot
    received, not only the dry-run line. X11 run is the positive control."""
    base = Path(tempfile.mkdtemp(prefix="h031-argv-"))
    try:
        env, tree, log, stop = make_env(base / "x", map_state="IsViewable")
        r = play(env, tree, "--scene", SCENE)
        stop.touch()
        assert r.returncode == 0, r.stdout + r.stderr
        argv = launch_argv(log)
        assert "--display-driver" not in argv and "wayland" not in argv, argv
        assert "--windowed" in argv and argv[argv.index("--resolution") + 1] == "1920x1080", argv
        env, tree, log, stop = make_env(base / "w", wayland=True, x_window=False)
        r = play(env, tree, "--scene", SCENE, "--check")
        stop.touch()
        argv = launch_argv(log)
        assert argv[argv.index("--display-driver") + 1] == "wayland", argv
        assert "--windowed" in argv and argv[argv.index("--resolution") + 1] == "1920x1080", argv
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
    `FPS: 140` each second."""
    base = Path(tempfile.mkdtemp(prefix="h031-wayland-"))
    try:
        env, tree, log, stop = make_env(base, wayland=True, x_window=False, fps=140)
        r = play(env, tree, "--scene", SCENE, "--check")
        stop.touch()
        assert r.returncode == 0, r.stdout + r.stderr
        assert re.search(r"^PLAY window \d+s wayland$", r.stdout, re.M), r.stdout
        assert f"PLAY scene {SCENE} reached" in r.stdout, r.stdout
        assert "--print-fps" in launch_argv(log), launch_argv(log)
    finally:
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
