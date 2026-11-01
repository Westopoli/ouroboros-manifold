# spec: docs/stories/H-038.md (present-on-boot), DEC-play-check-scratch-userdir-2026-10-30
"""H-038 part 2: the display block of the stored settings runs after the first rendered frame.

Story H-038: "The game draws its first scene on my desktop whatever size the window comes up at, fullscreen included; I never see the splash and
nothing else."
Story test lines proved here: "with the planted file and `--windowed --resolution 1920x1080`, `qa_state()` reports the first scene and a new key
`display_settings_applied_frame` (an int, the engine frame at which the display block ran) of at least 1 within 3 s; red today because the key is
absent (the block runs at frame 0 inside `_ready()`). Positive control: without the planted file the same launch reaches `qa_state()` today.
Negative control: a planted file with `resolution_index=1` yields `window_get_size()` 1600x900 after the apply (the setting still takes effect)."

Fixture: a scratch XDG_DATA_HOME (tests/qa/desktop/daemon_client.py godot_env, the DEC-play-check-scratch-userdir shape; project.godot
`custom_user_dir_name="data"` puts user:// at <XDG_DATA_HOME>/data) holding `data/settings.cfg` with `[display] resolution_index=<n>, fullscreen=false`.
The machine's ~/.local/share and display are never touched: the game runs under its own Xvfb (xvfb-run -a -s '-screen 0 1920x1080x24').

Where the key lives: the story says "`qa_state()` reports ... a new key" and names no nesting. The daemon's `state` reply is {scene, tick, qa, inventory};
the key is accepted at the reply's top level or inside its `qa` dict (UIDataBus is an autoload, so the scene's own `qa` dict is not its natural home).

How `window_get_size()` is observed: the qa daemon has no window-size verb and its screenshot is the 1920x1080 stretched viewport whatever the window is
(dumped 2026-10-31: planted index 1, screenshot 1920x1080, X window 1600x900). The test therefore asks the Xvfb server the size of the game's X window
(`xwininfo -root -tree`, the window named "Ouroboros ..."), which is what `DisplayServer.window_get_size()` sets on X11.

Premises dumped on the built tree (base 56b96343, 2026-10-31), qa-port `state` reply, no key in any run:
  top-level keys: inventory, qa, scene, tick; scene = "res://scenes/privacy_modal/privacy_modal.tscn"; qa = {accepted, plants, scene, tick};
  X window with no planted file: 1920x1080; planted resolution_index=1: 1600x900.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))

from daemon_client import GodotGame, pick_free_port  # noqa: E402

FIRST_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"  # project.godot run/main_scene
KEY = "display_settings_applied_frame"
WITHIN_S = 3.0  # the story: "within 3 s" (after the qa port opens)
POLL_S = 0.1
SCREEN = "1920x1080"


class XGame(GodotGame):
    """GodotGame whose Xvfb display name and XAUTHORITY are written to <scratch>/display, so the test can ask the X server for the game window's size."""

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        at = args.index(godot)
        return args[:at] + ["bash", "-c", 'printf "%s\\n%s\\n" "$DISPLAY" "$XAUTHORITY" > "$0"; exec "$@"', str(self.scratch / "display")] + args[at:]

    def window_size(self) -> tuple[int, int]:
        display, xauth = (self.scratch / "display").read_text().split("\n")[:2]
        out = subprocess.run(["xwininfo", "-display", display, "-root", "-tree"], capture_output=True, text=True, timeout=10,
                             env={**os.environ, "XAUTHORITY": xauth}).stdout
        sizes = [tuple(int(v) for v in m.groups()) for m in re.finditer(r'"Ouroboros[^"]*":[^\n]*?\s(\d+)x(\d+)\+', out)]
        assert sizes, "no X window named Ouroboros under display %s:\n%s" % (display, out[-600:])
        return sizes[0]


@pytest.fixture
def launch(monkeypatch):
    """launch(resolution_index) starts the game (planting settings.cfg when an index is given, none when None) and returns it."""
    assert shutil.which("xvfb-run") and shutil.which("xwininfo"), "xvfb-run and xwininfo are required"
    # Private user dir: godot_env keeps a caller's non-empty XDG_DATA_HOME (the merge gate exports one shared by the whole run), and a planted
    # settings.cfg there outlives this test and breaks S-110 in lane_plays. Unset it so the user dir is <scratch>/xdg, removed with g.scratch.
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    games: list[XGame] = []

    def _launch(resolution_index: int | None) -> XGame:
        g = XGame(pick_free_port(), seed=1, resolution=SCREEN)
        games.append(g)
        assert g.user_dir.is_relative_to(g.scratch), "user dir %s is not under the private scratch %s" % (g.user_dir, g.scratch)
        if resolution_index is not None:
            g.user_dir.mkdir(parents=True, exist_ok=True)
            (g.user_dir / "settings.cfg").write_text("[display]\nresolution_index=%d\nfullscreen=false\n" % resolution_index)
        g.start()
        g.wait_for_port(60)
        return g

    yield _launch
    for g in games:
        g.stop()
        shutil.rmtree(g.scratch, ignore_errors=True)


def _state(g: GodotGame) -> dict:
    resp = g.client.state()
    assert resp.get("ok"), "state call failed: %r" % (resp,)
    return resp["result"]


def _key(state: dict):
    if KEY in state:
        return state[KEY]
    qa = state.get("qa")
    return qa.get(KEY) if isinstance(qa, dict) else None


def _wait_first_scene(g: GodotGame) -> dict:
    deadline = time.monotonic() + WITHIN_S
    state: dict = {}
    while time.monotonic() < deadline:
        state = _state(g)
        if state.get("scene") == FIRST_SCENE:
            return state
        time.sleep(POLL_S)
    raise AssertionError("first scene %s not reported within %ss; last scene = %r" % (FIRST_SCENE, WITHIN_S, state.get("scene")))


def _wait_key(g: GodotGame) -> dict:
    """The first scene is reported and the display block has reported its frame, within WITHIN_S of the port opening."""
    deadline = time.monotonic() + WITHIN_S
    state: dict = {}
    while time.monotonic() < deadline:
        state = _state(g)
        if state.get("scene") == FIRST_SCENE and _key(state) is not None:
            return state
        time.sleep(POLL_S)
    assert state.get("scene") == FIRST_SCENE, "first scene %s not reported within %ss; last scene = %r" % (FIRST_SCENE, WITHIN_S, state.get("scene"))
    raise AssertionError("H-038: qa_state() has no %s within %ss (the display block still runs at frame 0 inside _ready()); state keys = %s, qa keys = %s"
                         % (KEY, WITHIN_S, sorted(state), sorted(state.get("qa", {}))))


def _assert_applied_after_a_frame(state: dict) -> None:
    frame = _key(state)
    assert isinstance(frame, int) and not isinstance(frame, bool), "%s must be an int, got %r" % (KEY, frame)
    assert frame >= 1, "%s = %d: the display block ran before the first rendered frame (story: at least 1)" % (KEY, frame)


def test_planted_1920x1080_settings_apply_after_the_first_frame(launch):
    """H-038 part 2: planted resolution_index=2 (1920x1080, the project viewport), `--windowed --resolution 1920x1080`: the first scene is reported
    and display_settings_applied_frame is an int >= 1 within 3 s. RED today: the key is absent."""
    g = launch(2)
    _assert_applied_after_a_frame(_wait_key(g))


def test_no_planted_settings_still_reaches_qa_state(launch):
    """H-038 part 2 positive control (green today): the same launch with no planted settings.cfg reaches qa_state() on the first scene,
    so a red above means the key is missing, not that the harness is broken."""
    g = launch(None)
    state = _wait_first_scene(g)
    assert state["scene"] == FIRST_SCENE
    assert isinstance(state.get("tick"), int), "state reply lacks an int tick: %r" % (sorted(state),)


def test_planted_1600x900_settings_still_take_effect(launch):
    """H-038 part 2 negative control: planted resolution_index=1 yields window_get_size() 1600x900 after the apply (the setting still takes effect).
    RED today for the missing-key reason: 'after the apply' is only observable once display_settings_applied_frame exists. (The size itself is
    already 1600x900 today; see the next test.)"""
    g = launch(1)
    _assert_applied_after_a_frame(_wait_key(g))
    assert g.window_size() == (1600, 900), "window is %dx%d after the apply, wanted 1600x900" % g.window_size()


def test_planted_1600x900_window_size_settles(launch):
    """H-038 part 2 control (green today): planted resolution_index=1 gives a 1600x900 game window once the first scene is up and 3 s have passed,
    with or without the key; it pins that the fix does not lose the setting."""
    g = launch(1)
    _wait_first_scene(g)
    time.sleep(WITHIN_S)
    assert g.window_size() == (1600, 900), "window is %dx%d, wanted 1600x900" % g.window_size()
