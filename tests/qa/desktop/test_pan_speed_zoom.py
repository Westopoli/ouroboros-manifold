# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 10 A25; E-16 R-103-09, R-110-02
"""A25: camera pan speed is constant on screen and scaled by the Settings slider.

Real display (Xvfb, software GL). Boots tests/test_settings_pan_speed.gd in its `--probe pan`
child mode on a settings.cfg fixture in a throwaway XDG_DATA_HOME, mounts the live tactical_c view
and measures camera travel over 5 fixed-step pan frames (1/30 s) for a held arrow key and for the
pointer resting on the right viewport edge, at two zooms: the zoom is halved first (`_zoom_by(0.5)`, zoom1) and then doubled
(`_zoom_by(2.0)`, zoom2), so the opening fit (ZOOM_MAX / ZOOM_STEP) is never clamped.

Zoom direction: in tactical_view.gd zoom 1.0 is zoomed OUT (the whole canvas fits the screen
height, ZOOM_MIN) and zoom 4.0 is zoomed IN, so doubling the zoom halves the world distance:
world(zoom 1) / world(zoom 2) == 2, and screen pixels (world * world scale) are equal.

Slider fixture key (named by the test): [camera] pan_speed, 0.5 to 2.0, default 1.0, times the A6
base PAN_SPEED_PX = 600 px/s.

Positive control (run by hand, not committed): with `PAN_SPEED_PX * delta / _world_scale` in
tactical_view.gd `_pan_input` replaced by `... / _fit_scale` (zoom scaling removed),
test_screen_speed_is_constant_across_zoom must fail.
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

PROBE_SCRIPT = "res://tests/test_settings_pan_speed.gd"
XVFB_SCREEN = "1920x1080x24"
BASE_PX_PER_S = 600.0
FRAMES = 5
DELTA = 1.0 / 30.0


def _boot_probe(cfg: str) -> dict:
    scratch = Path(tempfile.mkdtemp(prefix="qa_pan_speed."))
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
            "--script", PROBE_SCRIPT, "--", "--probe", "pan",
        ]
        proc = subprocess.Popen(cmd, cwd=str(scratch), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True, text=True)
        try:
            out, _ = proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            out, _ = proc.communicate()
            pytest.fail("pan probe timed out:\n" + out[-800:])
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        for line in out.splitlines():
            if line.startswith("PROBE "):
                return json.loads(line[6:])
        pytest.fail("no PROBE line from the pan child:\n" + out[-800:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _fixture(speed: float | None, extra: str = "") -> str:
    body = "" if speed is None else "pan_speed=%s\n" % speed
    return "[camera]\n%s%s" % (body, extra)


@pytest.fixture(scope="module")
def default_probe() -> dict:
    probe = _boot_probe(_fixture(None))
    # Control: the view mounted, the zoom really changed the scale, and the camera moved.
    assert probe["canvas"] > 0, probe
    assert probe["zoom2"]["scale"] == pytest.approx(2 * probe["zoom1"]["scale"], rel=1e-6), probe
    for z in ("zoom1", "zoom2"):
        for inp in ("key", "edge"):
            assert probe[z][inp]["world"] > 0, "no pan with %s at %s: %s" % (inp, z, probe)
            assert probe[z][inp]["cross"] < 1e-6, "pan crossed the axis: %s" % probe
    return probe


@pytest.mark.parametrize("inp", ["key", "edge"])
def test_screen_speed_is_constant_across_zoom(default_probe, inp):
    """R-103-09: same screen pixels at both zooms, world distance in proportion (ratio 2)."""
    z1, z2 = default_probe["zoom1"][inp], default_probe["zoom2"][inp]
    assert z1["screen"] == pytest.approx(z2["screen"], rel=0.02), (
        "%s pan: %.1f screen px at zoom 1.0 vs %.1f at zoom 2.0" % (inp, z1["screen"], z2["screen"]))
    assert z1["world"] / z2["world"] == pytest.approx(2.0, rel=0.02), (
        "%s pan: world distance %.1f at zoom 1.0 vs %.1f at zoom 2.0, expected ratio 2" % (inp, z1["world"], z2["world"]))


@pytest.mark.parametrize("inp", ["key", "edge"])
def test_default_slider_is_the_a6_base_speed(default_probe, inp):
    """Default 1.0 is the A6 base 600 px/s on screen."""
    want = BASE_PX_PER_S * FRAMES * DELTA
    got = default_probe["zoom1"][inp]["screen"]
    assert got == pytest.approx(want, rel=0.02), "%s pan moved %.1f screen px, expected %.1f" % (inp, got, want)


@pytest.mark.parametrize("speed", [2.0, 0.5])
@pytest.mark.parametrize("inp", ["key", "edge"])
def test_slider_scales_screen_speed(default_probe, speed, inp):
    probe = _boot_probe(_fixture(speed))
    assert probe["stored"].get("pan_speed") == pytest.approx(speed), probe["stored"]
    want = default_probe["zoom1"][inp]["screen"] * speed
    for z in ("zoom1", "zoom2"):
        got = probe[z][inp]["screen"]
        assert got == pytest.approx(want, rel=0.02), (
            "pan_speed=%s %s pan at %s moved %.1f screen px, expected %.1f" % (speed, inp, z, got, want))


def test_lowest_slider_position_still_edge_scrolls():
    probe = _boot_probe(_fixture(0.5))
    assert probe["stored"].get("pan_speed") == pytest.approx(0.5), probe["stored"]
    assert probe["zoom1"]["edge"]["world"] > 0, "pan_speed=0.5 switched edge scroll off: %s" % probe["zoom1"]["edge"]


def test_stale_edge_scroll_key_changes_nothing(default_probe):
    probe = _boot_probe(_fixture(None, "edge_scroll=false\n"))
    for z in ("zoom1", "zoom2"):
        got = probe[z]["edge"]["screen"]
        want = default_probe[z]["edge"]["screen"]
        assert got == pytest.approx(want, rel=0.001), (
            "stale edge_scroll=false changed the edge pan at %s: %.1f vs %.1f screen px" % (z, got, want))
