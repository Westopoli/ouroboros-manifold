# Rule pins: R-001-07@8f31c3
# spec: docs/stories/H-040.md "Part 3: replay scene" (arena-stage1-flat-field), docs/stories/H-039.md (the om-fight-1 file), DEC-lab-staircase-2026-10-31
"""H-040 part 3, the fight replay scene: res://scenes/proto/fight_replay/fight_replay.tscn.

Story H-040: "I place two groups of one unit type on an open field, both attack-move, and I watch the fight happen in the game and see who won against
who I said would win."

Scene contract (Part 3), quoted: "Reads `OM_FIGHT` (a `fight.json` path, parsed with `JSON.parse_string`; unknown keys ignored). Draws frame 0 exactly as the
layout shot draws a layout ... Space or Right steps one frame; Left steps back; `OM_AUTOPLAY=1` advances at DRAFT-replay-fps 1 frame per second ... HUD line
top-left: `tick <t>  A <alive_a>  B <alive_b>  frame <i>/<n>`; after the last frame: `winner <w>  predicted <p>  <agree|disagree>`. `OM_SHOT_OUT=<dir>` saves
`frame-<i>.png` for every frame (30 render frames settle before the first, 2 between) and quits. `qa_state()`: `scene`, `fight_id`, `frame`, `frame_count`,
`tick`, `alive_a`, `alive_b`, `result` (the result table), `autoplay` (bool)."
Story tests, quoted: "headless run with `OM_FIGHT` on `snapshot.example(frames=3)` written to a temp file; `frame_count` equals 3; stepping (qa daemon key press or
`OM_AUTOPLAY=1` after 2.5 s) reaches `frame` 2 with `alive_a`, `alive_b` from the file; `OM_SHOT_OUT` yields 3 PNGs none blank (reuse the look metric, uniform
fraction below 1); positive control: the same file with one frame removed gives `frame_count` 2."

The scene is launched the desktop-QA way, exactly as tests/qa/test_layout_shot.py launches the layout shot (tests/qa/desktop/daemon_client.py GodotGame: a private
Xvfb via xvfb-run, software GL, --qa-port, scratch XDG_DATA_HOME, never the real display, never the screenshot portal), with the scene path inserted before the `--`.
H-035 import rule: this file launches Godot, so the gate imports the tree first (merge_gate.sh, acceptance file mentions GodotGame).

The stepping keys are sent as qa-daemon `input key <name>` (Godot key names `Space`, `Right`, `Left`). The look metric is the gate's own
scripts/specfactory/merge_gate_support.py frame_busyness (fraction of pixels off the most common luminance; screen_capture.sh rejects at 0 only, the near-uniform
threshold is Westley's and not given), so "none blank" asserts the fraction is above 0, which is the story's "uniform fraction below 1".

Positive controls (green today): snapshot.example(3) validates and the one-frame-removed file validates too; the layout shot scene, which the replay scene reuses,
launches the same way on a toy layout and answers qa_state; the look metric rejects a flat PNG and accepts a varied one.

Red on the built tree: scenes/proto/fight_replay/ does not exist, so Godot opens no scene and the qa-port never serves a fight_replay qa_state.

Visible-only, no test (gaps, reported): sides A blue and B red, facing arrows, glyph at least 14 px, legend, camera margin 0.15 (qa_state carries none of these),
the dead unit as a flat grey marker at its last position, a target as a thin line. Only the HUD line is read, from the daemon's Label texts (hud_texts), which
presumes the HUD is a Label control (name not given by the story, so any Label text is searched).
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))
sys.path.insert(0, str(ROOT))

from daemon_client import GodotGame, pick_free_port, wait_for  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402
from scripts.specfactory.merge_gate_support import frame_busyness  # noqa: E402

SCENE = "res://scenes/proto/fight_replay/fight_replay.tscn"
SHOT_SCENE = "res://scenes/proto/layout_shot/layout_shot.tscn"
STATE_KEYS = {"scene", "fight_id", "frame", "frame_count", "tick", "alive_a", "alive_b", "result", "autoplay"}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
RESOLUTION = "1920x1080"
QUIT_TIMEOUT = 240  # seconds for a SHOT_OUT run to save every frame and quit (a harness bound, not a tolerance on the scene)


class ReplayGame(GodotGame):
    """GodotGame that opens `scene`: the scene path goes before the `--` that starts the user args."""

    scene = SCENE

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        args.insert(args.index("--"), self.scene)
        return args


class ShotGame(ReplayGame):
    scene = SHOT_SCENE


def _write_fight(path: Path, doc: dict) -> Path:
    """Raw JSON like snapshot.write (sorted keys, indent 2), so a fixture with an extra key can be written without the checker refusing it."""
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def fight3(tmp_path) -> tuple[Path, dict]:
    doc = snapshot.example(frames=3)
    assert snapshot.validate(doc) == []
    path = tmp_path / "L-0001-s1.fight.json"
    snapshot.write(doc, path)
    return path, doc


def _open(monkeypatch, fight: Path, autoplay: bool = False, shot_out: Path | None = None) -> ReplayGame:
    monkeypatch.setenv("OM_FIGHT", str(fight))
    monkeypatch.delenv("OM_AUTOPLAY", raising=False)
    monkeypatch.delenv("OM_SHOT_OUT", raising=False)
    monkeypatch.delenv("OM_LAYOUT", raising=False)
    if autoplay:
        monkeypatch.setenv("OM_AUTOPLAY", "1")
    if shot_out is not None:
        monkeypatch.setenv("OM_SHOT_OUT", str(shot_out))
    g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    g.start()
    return g


def _state(g: ReplayGame, want=lambda qa: True, timeout: float = 60.0, label: str = "fight_replay scene") -> dict:
    """The scene's full daemon state once it is the current scene and `want(qa)` holds."""
    return wait_for(g.client, lambda r: r.get("scene") == SCENE and "qa" in r and want(r["qa"]), timeout=timeout, label=label)


def _key(g: ReplayGame, name: str) -> None:
    resp = g.client.call("input", "key", name)
    assert resp.get("ok"), "key %s refused: %r" % (name, resp)
    g.client.call("input", "wait_frames", 3)


def _hud_lines(state: dict) -> list[str]:
    return [t for t in state["inventory"]["hud_texts"].values() if isinstance(t, str)]


# ---------------------------------------------------------------- positive controls (green today)

def test_control_example_fixture_validates_and_a_frame_removed_file_is_still_valid(tmp_path):
    """H-040 Part 3 test "`snapshot.example(frames=3)` written to a temp file ... the same file with one frame removed gives `frame_count` 2". CONTROL: the fixture
    validates, writes and reads back through the H-039 checker with three frames, and the one-frame-removed copy is a valid document with two, so a red below is
    the missing scene and not a bad fixture."""
    doc = snapshot.example(frames=3)
    path = tmp_path / "ok.fight.json"
    snapshot.write(doc, path)
    assert len(snapshot.read(path)["frames"]) == 3
    cut = copy.deepcopy(doc)
    del cut["frames"][1]
    assert snapshot.validate(cut) == []
    assert len(cut["frames"]) == 2


def test_control_blank_metric_rejects_a_flat_png_and_accepts_a_varied_one(tmp_path):
    """H-040 Part 3 "`OM_SHOT_OUT` yields 3 PNGs none blank (reuse the look metric, uniform fraction below 1)". CONTROL: the gate's frame_busyness is 0 for a flat
    PNG and above 0 for a varied one, so the check below does flag a blank frame."""
    from PIL import Image
    flat, varied = tmp_path / "flat.png", tmp_path / "varied.png"
    Image.new("RGB", (64, 48), (0, 0, 0)).save(flat)
    im = Image.new("RGB", (64, 48), (30, 60, 90))
    for x in range(0, 64, 4):
        for y in range(48):
            im.putpixel((x, y), (200, 40 + y, 40))
    im.save(varied)
    assert frame_busyness(flat) == 0.0
    assert frame_busyness(varied) > 0.0


def test_control_layout_shot_launches_the_same_way_and_answers_qa_state(tmp_path, monkeypatch):
    """H-040 Part 3 "reuses the layout shot's drawing" and "launches Godot; H-035 import rule applies". CONTROL: the scene the replay reuses launches through this
    file's harness (ReplayGame with another scene path: xvfb, software GL, qa-port) on a hand-written two-unit layout and serves a qa_state with its layout_id,
    so a red below is the missing replay scene and not the launcher."""
    side = lambda x, face: {"headcount": 2, "units": [{"role": "Vanguard", "x": x + 40.0 * i, "y": 1900.0, "facing": face, "layer": 0, "range": 90.0}
                                                      for i in range(2)]}
    layout = tmp_path / "toy.json"
    layout.write_text(json.dumps({"id": "L-9002", "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "A", "predict_why": "toy",
                                  "verdict": "", "feedback": "", "defender": "", "side_a": side(800.0, 0.0), "side_b": side(3200.0, 3.1416)}))
    monkeypatch.setenv("OM_LAYOUT", str(layout))
    monkeypatch.delenv("OM_SHOT_OUT", raising=False)
    g = ShotGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    g.start()
    try:
        g.wait_for_port(timeout=90.0)
        res = wait_for(g.client, lambda r: r.get("scene") == SHOT_SCENE and "qa" in r, timeout=60.0, label="layout_shot scene")
        assert res["qa"]["layout_id"] == "L-9002" and res["qa"]["unit_count"] == 4
        assert g.client.call("input", "key", "Space").get("ok") is True  # the key verb the stepping tests use is served
    finally:
        g.stop()


# ---------------------------------------------------------------- the scene (red until it exists)

def test_scene_files_exist():
    """H-040 Part 3 "`scenes/proto/fight_replay/fight_replay.tscn` and `fight_replay.gd` (plus `.uid`), new files"."""
    base = ROOT / "scenes" / "proto" / "fight_replay"
    assert (base / "fight_replay.tscn").is_file(), "no fight_replay.tscn"
    assert (base / "fight_replay.gd").is_file(), "no fight_replay.gd"
    assert (base / "fight_replay.gd.uid").is_file(), "no fight_replay.gd.uid (a Godot script's sidecar is committed with it)"


def test_qa_state_inventory_at_frame_zero(fight3, monkeypatch):
    """H-040 Part 3 "`qa_state()`: `scene`, `fight_id`, `frame`, `frame_count`, `tick`, `alive_a`, `alive_b`, `result` (the result table), `autoplay` (bool)" and
    the test "`frame_count` equals 3": with OM_FIGHT on snapshot.example(frames=3) the scene opens on frame 0 with every value from the file; autoplay is false
    when OM_AUTOPLAY is unset, and without it the frame does not move by itself."""
    path, doc = fight3
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        qa = _state(g)["qa"]
        assert STATE_KEYS <= set(qa), "qa_state keys %s lack %s" % (sorted(qa), sorted(STATE_KEYS - set(qa)))
        assert qa["scene"] == SCENE
        assert qa["fight_id"] == doc["layout_id"], "fight_id %r, the file's layout_id is %r" % (qa["fight_id"], doc["layout_id"])
        assert qa["frame_count"] == 3, "frame_count %r, the file has 3 frames" % qa["frame_count"]
        assert qa["frame"] == 0
        assert qa["tick"] == doc["frames"][0]["tick"]
        assert [qa["alive_a"], qa["alive_b"]] == doc["frames"][0]["alive"]
        assert qa["result"] == doc["result"], "result %r, the file's result table is %r" % (qa["result"], doc["result"])
        assert qa["autoplay"] is False
        time.sleep(3.0)
        assert _state(g)["qa"]["frame"] == 0, "frame moved with OM_AUTOPLAY unset"
    finally:
        g.stop()


def test_stepping_with_keys_reaches_the_last_frame_and_the_file_s_alive_counts(fight3, monkeypatch):
    """H-040 Part 3 "Space or Right steps one frame; Left steps back" and the test "stepping (qa daemon key press ...) reaches `frame` 2 with `alive_a`, `alive_b`
    from the file": Space then Right reach frame 2, tick and alive counts of the file's last frame; Left goes back to frame 1 with that frame's counts."""
    path, doc = fight3
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        _state(g)
        _key(g, "Space")
        qa = _state(g, lambda q: q["frame"] == 1)["qa"]
        assert (qa["tick"], [qa["alive_a"], qa["alive_b"]]) == (doc["frames"][1]["tick"], doc["frames"][1]["alive"])
        _key(g, "Right")
        qa = _state(g, lambda q: q["frame"] == 2, timeout=15.0, label="frame 2 after Space, Right")["qa"]
        assert qa["tick"] == doc["frames"][2]["tick"]
        assert [qa["alive_a"], qa["alive_b"]] == doc["frames"][2]["alive"]
        assert [qa["alive_a"], qa["alive_b"]] != doc["frames"][1]["alive"], "fixture premise: the last frame's counts differ from frame 1's"
        _key(g, "Left")
        qa = _state(g, lambda q: q["frame"] == 1, timeout=15.0, label="frame 1 after Left")["qa"]
        assert [qa["alive_a"], qa["alive_b"]] == doc["frames"][1]["alive"]
    finally:
        g.stop()


def test_autoplay_advances_to_the_last_frame(fight3, monkeypatch):
    """H-040 Part 3 "`OM_AUTOPLAY=1` advances at DRAFT-replay-fps 1 frame per second" and the test "`OM_AUTOPLAY=1` after 2.5 s ... reaches `frame` 2": with
    OM_AUTOPLAY=1 qa_state reports autoplay true and, with no key pressed, frame 2 with the file's last-frame alive counts. The rate is not timed (no tolerance given)."""
    path, doc = fight3
    g = _open(monkeypatch, path, autoplay=True)
    try:
        g.wait_for_port(timeout=90.0)
        assert _state(g)["qa"]["autoplay"] is True
        qa = _state(g, lambda q: q["frame"] == 2, timeout=30.0, label="frame 2 under OM_AUTOPLAY=1")["qa"]
        assert [qa["alive_a"], qa["alive_b"]] == doc["frames"][2]["alive"]
        assert qa["tick"] == doc["frames"][2]["tick"]
    finally:
        g.stop()


def test_hud_line_names_the_tick_and_the_alive_counts(fight3, monkeypatch):
    """H-040 Part 3 "HUD line top-left: `tick <t>  A <alive_a>  B <alive_b>  frame <i>/<n>`; after the last frame: `winner <w>  predicted <p>  <agree|disagree>`".
    Read from the daemon's Label texts; <i> is not pinned (the story does not say whether it counts from 0 or 1). The example fight is won by A as predicted."""
    path, doc = fight3
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        first = doc["frames"][0]
        line0 = r"tick %d  A %d  B %d  frame \d+/3" % (first["tick"], first["alive"][0], first["alive"][1])
        st = _state(g)
        assert any(re.fullmatch(line0, t) for t in _hud_lines(st)), "no HUD line like %r among Label texts %s" % (line0, _hud_lines(st))
        _key(g, "Space")
        _key(g, "Space")
        last = doc["frames"][2]
        st = _state(g, lambda q: q["frame"] == 2, timeout=15.0, label="frame 2")
        line2 = r"tick %d  A %d  B %d  frame \d+/3" % (last["tick"], last["alive"][0], last["alive"][1])
        assert any(re.fullmatch(line2, t) for t in _hud_lines(st)), "no HUD line like %r among Label texts %s" % (line2, _hud_lines(st))
        res = doc["result"]
        verdict = "agree" if res["agree"] else "disagree"
        end = "winner %s  predicted %s  %s" % (res["winner"], res["predict"], verdict)
        assert end in _hud_lines(st), "no end line %r among Label texts %s" % (end, _hud_lines(st))
    finally:
        g.stop()


def test_unknown_keys_in_the_file_are_ignored(tmp_path, monkeypatch):
    """H-040 Part 3 "Reads `OM_FIGHT` (a `fight.json` path, parsed with `JSON.parse_string`; unknown keys ignored)" and H-039 "a reader ignores keys it does not
    know": a file with an unknown top-level key and an unknown unit key (the stage-4 `seen`) still opens with frame_count 3."""
    doc = snapshot.example(frames=3)
    doc["future_key"] = {"x": 1}
    for frame in doc["frames"]:
        for unit in frame["units"]:
            unit["seen"] = []
    assert snapshot.validate(doc), "fixture premise: the checker rejects unknown keys, so this file is raw"
    g = _open(monkeypatch, _write_fight(tmp_path / "extra.fight.json", doc))
    try:
        g.wait_for_port(timeout=90.0)
        assert _state(g)["qa"]["frame_count"] == 3
    finally:
        g.stop()


def test_one_frame_removed_gives_frame_count_two(tmp_path, monkeypatch):
    """H-040 Part 3 "positive control: the same file with one frame removed gives `frame_count` 2": the middle frame is dropped, so frame_count follows the file and
    is not a constant 3; stepping to the last frame lands on frame 1 with the file's last-frame tick."""
    doc = snapshot.example(frames=3)
    del doc["frames"][1]
    g = _open(monkeypatch, _write_fight(tmp_path / "two.fight.json", doc))
    try:
        g.wait_for_port(timeout=90.0)
        assert _state(g)["qa"]["frame_count"] == 2
        _key(g, "Space")
        qa = _state(g, lambda q: q["frame"] == 1, timeout=15.0, label="last frame of two")["qa"]
        assert qa["tick"] == doc["frames"][1]["tick"] and [qa["alive_a"], qa["alive_b"]] == doc["frames"][1]["alive"]
    finally:
        g.stop()


def test_shot_out_saves_one_png_per_frame_none_blank_and_quits(fight3, tmp_path, monkeypatch):
    """H-040 Part 3 "`OM_SHOT_OUT=<dir>` saves `frame-<i>.png` for every frame (30 render frames settle before the first, 2 between) and quits" and the test
    "`OM_SHOT_OUT` yields 3 PNGs none blank (reuse the look metric, uniform fraction below 1)": frame-0.png, frame-1.png, frame-2.png are PNGs whose look metric is
    above 0, the process exits by itself, and the first and last frame differ (the HUD line and the dead side change)."""
    path, _ = fight3
    out = tmp_path / "shots"
    out.mkdir()
    g = _open(monkeypatch, path, shot_out=out)
    try:
        try:
            g.proc.wait(timeout=QUIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            pytest.fail("the scene did not quit after saving the frames (OM_SHOT_OUT set); stderr tail:\n" + g.stderr_tail())
        names = sorted(p.name for p in out.iterdir())
        assert names == ["frame-0.png", "frame-1.png", "frame-2.png"], "OM_SHOT_OUT dir holds %s; stderr tail:\n%s" % (names, g.stderr_tail())
        for name in names:
            assert (out / name).read_bytes()[:8] == PNG_MAGIC, "%s is not a PNG" % name
            assert frame_busyness(out / name) > 0.0, "%s is blank (uniform fraction 1)" % name
        assert (out / "frame-0.png").read_bytes() != (out / "frame-2.png").read_bytes(), "frame-0.png and frame-2.png are identical"
    finally:
        g.stop()
