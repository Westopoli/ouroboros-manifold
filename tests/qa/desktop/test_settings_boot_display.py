# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md addendum 4 A10; E-16 R-110-02; piece C3-G5
"""Piece C3-G5: stored resolution and fullscreen are applied at boot.

Real display (Xvfb, software GL), not headless: the headless DisplayServer is a dummy
whose window mode and size do not read back. Boots the game's own
tests/test_settings_boot_applied.gd in its `--probe display` child mode on a settings.cfg
fixture placed in a throwaway XDG_DATA_HOME (never the player's user dir), after the
autoloads are up, and reads DisplayServer back.

project.godot defaults to a fullscreen window, so the windowed fixture is the case that
tells a boot-time apply from the default: resolution_index 1 is 1600x900
(scenes/settings/settings.gd RESOLUTIONS). The Xvfb screen is larger than that and there
is no window manager, so a windowed 1600x900 window is exactly what the stored setting asks for.

No window manager runs under Xvfb, so a window-mode change is not reliably readable
after boot (a fullscreen request reverts to windowed a frame later, and a windowed request
reads back as the project default until then). What is observable is the window size: the
windowed fixture must come back at the stored size, and the fullscreen fixture must come
back at the screen size, not the stored windowed size. The window mode is read before the
first frame and must be fullscreen for the fullscreen fixture.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

import pytest

from daemon_client import REPO_ROOT, find_godot

PROBE_SCRIPT = "res://tests/test_settings_boot_applied.gd"
XVFB_SCREEN = "2560x1600x24"
FULLSCREEN = 3
EXCLUSIVE_FULLSCREEN = 4


def _boot_probe(cfg: str) -> dict:
    scratch = Path(tempfile.mkdtemp(prefix="qa_settings_display."))
    try:
        user_dir = scratch / "xdg" / "data"
        user_dir.mkdir(parents=True)
        (user_dir / "settings.cfg").write_text(cfg)
        (scratch / "saves").mkdir()
        env = dict(os.environ)
        for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
            env.pop(var, None)
        env["XDG_DATA_HOME"] = str(scratch / "xdg")
        env["OM_SAVE_DIR"] = str(scratch / "saves")
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
        cmd = [
            "xvfb-run", "-a", "-s", "-screen 0 %s" % XVFB_SCREEN,
            find_godot(), "--path", str(REPO_ROOT),
            "--display-driver", "x11", "--rendering-driver", "opengl3",
            "--fixed-fps", "30", "--quit-after", "3000",
            "--script", PROBE_SCRIPT, "--", "--probe", "display",
        ]
        proc = subprocess.Popen(cmd, cwd=str(scratch), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True, text=True)
        try:
            out, _ = proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            out, _ = proc.communicate()
            pytest.fail("display probe timed out:\n" + out[-800:])
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        for line in out.splitlines():
            if line.startswith("PROBE "):
                return json.loads(line[6:])
        pytest.fail("no PROBE line from the display child:\n" + out[-800:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_stored_resolution_windowed_is_applied_at_boot():
    probe = _boot_probe("[display]\nresolution_index=1\nfullscreen=false\n")
    stored = probe["stored"]
    # Positive control: the child read the fixture.
    assert stored.get("resolution_index") == 1 and stored.get("fullscreen") is False, stored
    assert probe["window_size"] == [1600, 900], (
        "stored resolution_index=1 (1600x900) but the window is %s at boot" % probe["window_size"])


def test_stored_fullscreen_is_applied_at_boot():
    probe = _boot_probe("[display]\nresolution_index=1\nfullscreen=true\n")
    stored = probe["stored"]
    assert stored.get("resolution_index") == 1 and stored.get("fullscreen") is True, stored
    assert probe["window_mode"] in (FULLSCREEN, EXCLUSIVE_FULLSCREEN), (
        "stored fullscreen=true but the window is mode %s at boot" % probe["window_mode"])
    assert probe["window_size"] == probe["screen_size"], (
        "stored fullscreen=true but the window is %s at boot, the screen is %s" % (probe["window_size"], probe["screen_size"]))
