"""H-028 stable-beta-build (docs/stories/H-028.md, Tests and Interfaces): tests for
`scripts/beta_refresh.sh`, the repo templates `scripts/beta/om-beta` and
`scripts/beta/ouroboros-beta.desktop`, and the Linux export preset path.

Nothing here runs Godot, opens a window or touches the real HOME or `~/Projects/om-push`: the refresh
script runs only in its `--dry-run` and `--check-capture` modes, always with HOME and `--root` pointing
into a tmpdir. Red today for the missing-feature reason: `scripts/beta_refresh.sh`, `scripts/beta/` and
the export path do not exist.

Story Tests, one block each:
- "A dry run of the refresh script prints the export and symlink steps."
- "The capture check rejects a planted uniform image (positive control)."
- "The desktop entry file parses and points at an existing path."
Interfaces (ruled 2026-11-02) pin the CLI, the repo paths and the six DRY lines.
"""
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import zlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFRESH = ROOT / "scripts" / "beta_refresh.sh"
OM_BETA = ROOT / "scripts" / "beta" / "om-beta"
DESKTOP = ROOT / "scripts" / "beta" / "ouroboros-beta.desktop"
PRESETS = ROOT / "export_presets.cfg"
SHA = "0123abc"
BINARY = "ouroboros_beta.x86_64"
HOME_PATH = "$HOME/Projects/om-push/beta/current/" + BINARY  # Interfaces 1: template Exec / launcher binary path

sys.path.insert(0, str(ROOT / "scripts" / "specfactory"))
from merge_gate_support import frame_busyness  # noqa: E402  (the function screen_capture.sh and --check-capture use)


def tmp(prefix):
    return Path(tempfile.mkdtemp(prefix=prefix))


def write_png(path, kind):
    """A planted 8-bit RGB PNG (stdlib only): `uniform` (one flat colour), `black`, `varied` (stripes and a
    gradient) or `near` (flat but for one pixel)."""
    w, h = 64, 48
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            if kind == "uniform":
                px = (30, 60, 90)
            elif kind == "black":
                px = (0, 0, 0)
            elif kind == "near":
                px = (200, 200, 200) if (x, y) == (3, 5) else (30, 60, 90)
            else:
                px = ((x * 255) // w, (y * 255) // h, 200 if (x // 8) % 2 else 20)
            row += bytes(px)
        rows.append(b"\x00" + bytes(row))

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body))

    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
    Path(path).write_bytes(data)
    return Path(path)


def run_refresh(args, home):
    assert REFRESH.is_file(), f"{REFRESH} does not exist"
    env = dict(os.environ, HOME=str(home))
    return subprocess.run([str(REFRESH), *args], capture_output=True, text=True, timeout=60, env=env)


def parse_desktop(text):
    """{key: value} of the `[Desktop Entry]` group; None when the group is missing."""
    group, out = None, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            group = m.group(1)
        elif group == "Desktop Entry" and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out if "[Desktop Entry]" in text else None


def linux_export_path():
    """`export_path` of the preset named Linux in export_presets.cfg (None when there is no such preset)."""
    block = None
    for m in re.finditer(r"^\[preset\.\d+\]\n(.*?)(?=^\[preset\.\d+\]\n|\Z)", PRESETS.read_text(), re.S | re.M):
        if re.search(r'^name="Linux"$', m.group(1), re.M):
            block = m.group(1)
    if block is None:
        return None
    return re.search(r'^export_path="(.*)"$', block, re.M).group(1)


# ---------------------------------------------------------------- positive controls (green today)

def test_control_planted_pngs_and_metric():
    """Positive control for the capture tests (H-028 Tests: "The capture check rejects a planted uniform
    image (positive control)."): the flat fixtures have blank fraction 0, the varied and near-uniform ones
    have more, measured by the same `frame_busyness` the story names. Checks the fixtures, not the script."""
    base = tmp("h028-png-ctl-")
    flat = [frame_busyness(write_png(base / f"{k}.png", k)) for k in ("uniform", "black")]
    assert flat == [0.0, 0.0], flat
    near = frame_busyness(write_png(base / "near.png", "near"))
    busy = frame_busyness(write_png(base / "varied.png", "varied"))
    assert 0 < near < busy, (near, busy)


def test_control_desktop_parser_and_preset_reader():
    """Positive control for the desktop-entry and export-path tests (H-028 Tests: "The desktop entry file
    parses and points at an existing path."): the parser reads a known-good entry and refuses a text with no
    group, and the repo's export_presets.cfg already has the `Linux` preset the story edits."""
    good = parse_desktop("[Desktop Entry]\nType=Application\nName=X\nExec=/bin/true\n")
    assert good == {"Type": "Application", "Name": "X", "Exec": "/bin/true"}, good
    assert parse_desktop("Type=Application\n") is None
    assert linux_export_path() is not None, "export_presets.cfg has no preset named Linux"


# ---------------------------------------------------------------- dry run (integration test)

def dry_run(home, root, tree, sha=SHA):
    return run_refresh(["--dry-run", "--root", str(root), "--tree", str(tree), "--sha", sha], home)


def test_refresh_script_exists_and_is_executable():
    """H-028 Interfaces 1 and 3: `scripts/beta_refresh.sh` is the script the clerk runs after a landing
    ("The clerk's landing, after the push, exports current main ..."); it is run directly."""
    assert REFRESH.is_file(), f"{REFRESH} does not exist"
    assert os.access(REFRESH, os.X_OK), f"{REFRESH} is not executable"


def test_dry_run_prints_the_six_steps_in_order():
    """H-028 Tests: "A dry run of the refresh script prints the export and symlink steps." Interfaces 3:
    `--dry-run [--root <dir>] [--tree <dir>] [--sha <sha>]` prints, in this order, six DRY lines (godot.real
    export, pipe build, `ln -sfn` link, the two installs, keep last 3). `$HOME` in the install lines may be
    printed literally or already substituted by the run's HOME."""
    base = tmp("h028-dry-")
    home, root, tree = base / "home", base / "om-push", base / "tree"
    for d in (home, root, tree):
        d.mkdir()
    r = dry_run(home, root, tree)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    got = [l for l in r.stdout.splitlines() if l.startswith("DRY ")]
    b = f"{root}/beta"
    want = [
        f'DRY export: godot.real --headless --path {tree} --export-release "Linux" {b}/{SHA}/{BINARY}',
        f"DRY pipe: scripts/build_pipe_linux.sh -> {b}/{SHA}/ouroboros_pipe",
        f"DRY link: ln -sfn {b}/{SHA} {b}/current",
    ]
    assert got[:3] == want, got
    assert len(got) == 6, got
    for line, (src, dst) in zip(got[3:5], ((f"{tree}/scripts/beta/om-beta", ".local/bin/om-beta"),
                                           (f"{tree}/scripts/beta/ouroboros-beta.desktop",
                                            ".local/share/applications/ouroboros-beta.desktop"))):
        m = re.fullmatch(r"DRY install: (\S+) -> (\$HOME|" + re.escape(str(home)) + r")/" + re.escape(dst), line)
        assert m and m.group(1) == src, line
    assert got[5] == f"DRY keep: last 3 builds under {b}/", got[5]


def test_dry_run_changes_nothing():
    """H-028 Interfaces 3: "`--dry-run` ... changes nothing". Isolation: the run leaves the root, the tree
    and the HOME it was given empty (no beta/ directory, no installed launcher or desktop entry)."""
    base = tmp("h028-dry-nochange-")
    home, root, tree = base / "home", base / "om-push", base / "tree"
    for d in (home, root, tree):
        d.mkdir()
    r = dry_run(home, root, tree)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert not any(home.iterdir()), list(home.rglob("*"))
    assert not any(root.iterdir()), list(root.rglob("*"))
    assert not any(tree.iterdir()), list(tree.rglob("*"))


# ---------------------------------------------------------------- capture check

def check_capture(png):
    return run_refresh(["--check-capture", str(png)], tmp("h028-cap-home-"))


def test_check_capture_rejects_planted_uniform_image():
    """H-028 Tests: "The capture check rejects a planted uniform image (positive control)." Interfaces 2:
    `--check-capture <png>` exits 3 and prints `CAPTURE REJECT uniform` when the image is uniform
    (blank fraction 0, the threshold `screen_capture.sh` has today). A flat colour and flat black both."""
    base = tmp("h028-cap-uniform-")
    for kind in ("uniform", "black"):
        r = check_capture(write_png(base / f"{kind}.png", kind))
        assert r.returncode == 3, (kind, r.returncode, r.stdout, r.stderr)
        assert "CAPTURE REJECT uniform" in r.stdout.splitlines(), (kind, r.stdout)


def test_check_capture_accepts_busy_image_with_its_fraction():
    """H-028 Tests: "The capture check rejects a planted uniform image (positive control)." Positive control
    on the script itself, Interfaces 2: a busy image exits 0 and prints `CAPTURE OK <fraction>`, the fraction
    being `frame_busyness` of that image (a thin call into it, not a second metric)."""
    base = tmp("h028-cap-busy-")
    png = write_png(base / "varied.png", "varied")
    r = check_capture(png)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    m = [re.fullmatch(r"CAPTURE OK (\d+(?:\.\d+)?)", l) for l in r.stdout.splitlines()]
    m = [x for x in m if x]
    assert len(m) == 1, r.stdout
    assert abs(float(m[0].group(1)) - frame_busyness(png)) < 1e-3, (m[0].group(1), frame_busyness(png))


def test_check_capture_only_rejects_blank_fraction_zero():
    """H-028 Interfaces 2: "The REJECT threshold stays what `screen_capture.sh` has today (blank fraction
    0)." A near-uniform image (one pixel off the flat colour, fraction > 0) is therefore not rejected."""
    base = tmp("h028-cap-near-")
    r = check_capture(write_png(base / "near.png", "near"))
    assert r.returncode == 0 and re.search(r"^CAPTURE OK ", r.stdout, re.M), (r.returncode, r.stdout, r.stderr)


def test_check_capture_calls_frame_busyness_without_a_copy():
    """H-028 Interfaces 2: "It is a thin call into `frame_busyness` from
    `scripts/specfactory/merge_gate_support.py` (the same function `screen_capture.sh` uses), no copy."
    The script names that module and function."""
    text = REFRESH.read_text()
    assert "merge_gate_support" in text and "frame_busyness" in text, "no call into merge_gate_support.frame_busyness"


# ---------------------------------------------------------------- desktop entry and launcher

def test_desktop_entry_template_parses_and_points_at_the_beta_binary():
    """H-028 Tests: "The desktop entry file parses and points at an existing path." Interfaces 1: the repo
    template `scripts/beta/ouroboros-beta.desktop` has `Type=Application`, a `Name`, and an `Exec` that
    names `$HOME/Projects/om-push/beta/current/ouroboros_beta.x86_64`; with HOME set to a tmpdir holding a
    binary at that path, the Exec's path resolves to an existing executable. Launch: "Neither passes a scene
    argument, so the game boots to its normal first scene.\""""
    assert DESKTOP.is_file(), f"{DESKTOP} does not exist"
    entry = parse_desktop(DESKTOP.read_text())
    assert entry is not None, "no [Desktop Entry] group"
    assert entry.get("Type") == "Application", entry
    assert entry.get("Name"), entry
    exe = entry.get("Exec", "")
    assert exe, entry
    assert HOME_PATH in exe or HOME_PATH.replace("$HOME", "${HOME}") in exe, exe
    assert not re.search(r"res://|\.tscn|--scene", exe), f"Exec passes a scene argument: {exe}"
    home = tmp("h028-desktop-home-")
    binary = home / "Projects" / "om-push" / "beta" / "current" / BINARY
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    tokens = [t.replace("${HOME}", str(home)).replace("$HOME", str(home)) for t in shlex.split(exe)]
    paths = [t for t in tokens if t.endswith(BINARY)] or [t for t in tokens if BINARY in t]
    assert paths, tokens
    assert Path(paths[0]).is_file() and os.access(paths[0], os.X_OK), paths


def test_desktop_entry_and_dry_run_agree_on_the_binary_and_current_link():
    """H-028 Interfaces 1 and 3: the template's `Exec=` is the export's output name under the `current`
    link, i.e. the same `ouroboros_beta.x86_64` and `<root>/beta/current` the dry run prints for the export
    and the symlink ("pointing at `beta/current/<binary>`")."""
    base = tmp("h028-agree-")
    home, root, tree = base / "home", base / "om-push", base / "tree"
    for d in (home, root, tree):
        d.mkdir()
    r = dry_run(home, root, tree)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    export = next(l for l in r.stdout.splitlines() if l.startswith("DRY export:"))
    link = next(l for l in r.stdout.splitlines() if l.startswith("DRY link:"))
    assert export.endswith("/" + BINARY), export
    assert link.endswith(f"{root}/beta/current"), link
    entry = parse_desktop(DESKTOP.read_text())
    assert entry and "/beta/current/" + BINARY in entry.get("Exec", ""), entry


def test_om_beta_launcher_exists_is_executable_and_runs_the_binary_without_a_scene():
    """H-028 Launch: "A one-line command `om-beta` on PATH ... that runs the same binary under the user's
    own session env. Neither passes a scene argument, so the game boots to its normal first scene."
    Interfaces 1: the repo template `scripts/beta/om-beta` is executable and runs
    `$HOME/Projects/om-push/beta/current/ouroboros_beta.x86_64`. Run with HOME at a tmpdir holding a stub
    binary: the stub is started with no scene argument and sees the caller's environment."""
    assert OM_BETA.is_file(), f"{OM_BETA} does not exist"
    assert OM_BETA.stat().st_mode & stat.S_IXUSR, "om-beta is not executable"
    home = tmp("h028-launcher-home-")
    binary = home / "Projects" / "om-push" / "beta" / "current" / BINARY
    binary.parent.mkdir(parents=True)
    log = home / "stub.log"
    binary.write_text('#!/bin/sh\necho "ARGV:$*" > "$STUB_LOG"\necho "DISPLAY:$DISPLAY" >> "$STUB_LOG"\n')
    binary.chmod(0o755)
    env = dict(os.environ, HOME=str(home), STUB_LOG=str(log), DISPLAY=":42")
    r = subprocess.run([str(OM_BETA)], capture_output=True, text=True, timeout=30, env=env)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    lines = log.read_text().splitlines()
    assert lines == ["ARGV:", "DISPLAY::42"], lines


# ---------------------------------------------------------------- export preset

def test_linux_export_preset_path_is_set():
    """H-028 Build: "`export_presets.cfg` already has a `Linux` preset with an empty `export_path`; the
    first piece sets the path". Interfaces 3: it is set to `dist/linux/ouroboros_beta.x86_64`."""
    assert linux_export_path() == "dist/linux/" + BINARY, linux_export_path()
