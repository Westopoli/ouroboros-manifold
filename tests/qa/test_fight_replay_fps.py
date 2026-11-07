# spec: docs/stories/H-088.md (closeup replay: watch a fight like a video, Westley's request 2026-11-07)
# Rule pins: none (lab harness story H-088)
"""H-088 closeup, part B: `scenes/proto/fight_replay/fight_replay.gd` takes its autoplay speed from the environment variable OM_FPS.

FPS-1 OM_FPS is a float > 0, frames per second of autoplay; unset, empty, non-numeric or <= 0 falls back to REPLAY_FPS 1.0.
FPS-2 `qa_state()` reports the speed in effect as `autoplay_fps` (a number), whether or not OM_AUTOPLAY is set.
FPS-3 autoplay steps at that speed (a slow OM_FPS is slower than the default).
FPS-4 a dense closeup file (many frames, `snapshot_every` K) loads and `frame_count` equals the file's frame count.

Premises dumped 2026-11-07 on base 633ea3e4: `qa_state()` today has the keys of tests/qa/test_fight_replay.py (STATE_KEYS and the later additions) and no `autoplay_fps`;
the scene reads no OM_FPS; autoplay steps once per 1/REPLAY_FPS second. Launcher and helpers are those of tests/qa/test_fight_replay.py (xvfb, software GL, qa-port).
Existing qa_state key checks (STATE_KEYS, H053_KEYS, ...) are subset checks (`<=`), so the new key breaks none of them; no existing test needs a `Test-defect:` edit for it.
The positive control (green today) is a hand-made 60-frame file: the scene already loads a file with more than 20 frames."""
from __future__ import annotations

import copy
import importlib
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skilllab" / "arena"))
from test_fight_replay import _open, _state, _write_fight, fight3  # noqa: E402,F401  (fight3 is a fixture)
import h063_fixtures as fx  # noqa: E402
import h088_fixtures as f8  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402


def _qa(monkeypatch, path, fps, autoplay=False):
    """Open the scene on `path` with OM_FPS set to `fps` (None: unset) and return the first full qa_state; the game is stopped before return."""
    if fps is None:
        monkeypatch.delenv("OM_FPS", raising=False)
    else:
        monkeypatch.setenv("OM_FPS", fps)
    g = _open(monkeypatch, path, autoplay=autoplay)
    try:
        g.wait_for_port(timeout=90.0)
        return _state(g)["qa"]
    finally:
        g.stop()


def _dense_example(frames=60):
    """snapshot.example(frames=3) stretched to `frames` frames one tick apart (a hand-made dense file; not through snapshot.validate, which caps frames at 20)."""
    doc = snapshot.example(frames=3)
    base = doc["frames"][1]
    doc["frames"] = [doc["frames"][0]] + [dict(copy.deepcopy(base), tick=t) for t in range(1, frames)]
    doc["snapshot_every"] = 1
    doc["result"]["ticks"] = frames - 1
    return doc


# ---------------------------------------------------------------- FPS-4 control and dense file

def test_control_a_dense_hand_made_file_loads_with_its_frame_count(tmp_path, monkeypatch):
    """CONTROL (green today, must stay green), FPS-4: a 60-frame file (more than the 20 the checker allows) opens and `frame_count` is 60, the last frame's tick is 59, so a
    red below is the closeup module and not the scene."""
    path = _write_fight(tmp_path / "L-0001-s1.fight.json", _dense_example(60))
    qa = _qa(monkeypatch, path, None)
    assert (qa["frame_count"], qa["frame"], qa["tick"]) == (60, 0, 0)


def test_fps4_a_closeup_file_loads_and_frame_count_is_the_files_frame_count(tmp_path, monkeypatch):
    """FPS-4 ("a dense closeup file loads and `frame_count` equals the file's frame count"): `closeup` on the h088 open field (Raider vs Vanguard, sight on, 575 ticks) with K 10
    writes 59 frames (0, 10 ... 570 and 575); the scene opens on it with `frame_count` 59 and `fight_id` the layout's."""
    closeup = importlib.import_module("scripts.skilllab.arena.closeup")
    lay = f8.open_layout("L-9920", roles=("Raider", "Vanguard"))
    layout_path, out = fx.write(lay, tmp_path / "layouts"), tmp_path / "dense"
    code = closeup.main(["--layout", str(layout_path), "--seed", "1", "--sight", "on", "--every-ticks", "10", "--out", str(out)])
    f = out / "L-9920-s1-every10.fight.json"
    doc = json.loads(f.read_text()) if f.exists() else {"frames": []}
    qa = _qa(monkeypatch, f, None) if f.exists() else {}
    assert (code, len(doc["frames"]), qa.get("frame_count"), qa.get("fight_id")) == (0, 59, 59, "L-9920")


# ---------------------------------------------------------------- FPS-1, FPS-2

@pytest.mark.parametrize("env,want", [
    ("4", 4.0), ("0.5", 0.5), ("12.5", 12.5),   # a float > 0 is the speed in effect
    (None, 1.0), ("", 1.0),                      # unset or empty: REPLAY_FPS
    ("0", 1.0), ("-3", 1.0), ("abc", 1.0),       # zero, negative, non-numeric: REPLAY_FPS
])
def test_fps1_fps2_qa_state_reports_the_autoplay_speed_in_effect(fight3, monkeypatch, env, want):
    """FPS-1 ("OM_FPS (float > 0, frames per second); unset, empty, non-numeric or <= 0 falls back to the current REPLAY_FPS 1.0") and FPS-2 ("`qa_state()` reports the speed in
    effect as a new key `autoplay_fps`"): with the OM_FPS of each case `qa_state()["autoplay_fps"]` is the float wanted (OM_AUTOPLAY unset, the speed is reported all the same)."""
    path, _ = fight3
    qa = _qa(monkeypatch, path, env)
    assert (qa.get("autoplay_fps"), type(qa.get("autoplay_fps")).__name__ in ("float", "int"), qa.get("autoplay")) == (want, True, False)


# ---------------------------------------------------------------- FPS-3 the speed drives autoplay

def test_fps3_a_slow_om_fps_autoplays_slower_than_the_default(fight3, monkeypatch):
    """FPS-3 ("autoplay speed from the environment variable OM_FPS"): with OM_AUTOPLAY=1 and OM_FPS=0.25 (one step per 4 s) the cursor is still at frame 0 or 1 three seconds
    after the scene is up, where the default 1 frame a second has reached the last frame (2) by then; and `autoplay_fps` is 0.25. (The rate is otherwise not timed: no
    tolerance is given, so the test only separates a quarter of the default from the default.)"""
    path, _ = fight3
    monkeypatch.setenv("OM_FPS", "0.25")
    g = _open(monkeypatch, path, autoplay=True)
    try:
        g.wait_for_port(timeout=90.0)
        first = _state(g)["qa"]
        time.sleep(3.0)
        later = _state(g)["qa"]
        assert later["frame"] <= 1, "frame %d three seconds in at OM_FPS=0.25: the scene still steps once a second" % later["frame"]
        assert first.get("autoplay_fps") == 0.25
    finally:
        g.stop()
