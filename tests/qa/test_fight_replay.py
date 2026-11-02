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


# ================================================================ H-040 "Orders and fight end" / H-052: the HUD's end line
# spec: docs/stories/H-040.md "Orders and fight end": "The replay HUD prints `end: wipe|silence|cap` and `STALL` on the last frame." and docs/stories/H-052.md (the
# om-fight-2 file: `orders`, `result.end`, `result.stall`, `winner "stall"`).
# Premises (DRAFT-hud-end-format: the story gives the words, not the line they sit in): the words are read from any Label text, as the HUD test above does; on the
# last frame one Label text contains `end: <end>` (so `end: wipe`, `end: silence`, `end: cap`), and for a stall one Label text contains the word `STALL`. Before the
# last frame no Label text contains `end:` or `STALL`. The v2 documents are built inline from `snapshot.example()` and written raw (the checker only accepts v2 once the
# builder lands it; the scene ignores keys it does not know either way).

def _v2_fight(end: str, stall: bool, tmp_path: Path) -> tuple[Path, dict]:
    doc = snapshot.example(frames=3)
    doc["schema"] = "om-fight-2"
    doc["orders"] = {"mode": "hold_and_attack" if stall else "both_same_point", "point": [120.0, 52.0], "attacker": "B" if stall else None}
    doc["result"]["end"] = end
    doc["result"]["stall"] = stall
    if end != "wipe":   # both sides alive in the last frame
        last = doc["frames"][-1]
        for row in last["units"]:
            row["hp"], row["alive"] = 100.0, True
        last["alive"] = [2, 2]
        doc["result"].update({"survivors": [2, 2], "capped": end == "cap", "winner": "stall" if stall else "draw", "agree": False, "predict": "A"})
    return _write_fight(tmp_path / ("L-0001-%s.fight.json" % end), doc), doc


def test_control_v2_fixture_documents_are_well_formed_json(tmp_path):
    """Control, green today: the three inline v2 fixtures (wipe, silence stall, cap) are written, parse back, and carry the keys the HUD tests rely on (end, stall, a
    last frame whose alive counts match the result's survivors), so a red below is the HUD and not the fixture."""
    for end, stall in (("wipe", False), ("silence", True), ("cap", False)):
        path, doc = _v2_fight(end, stall, tmp_path)
        back = json.loads(path.read_text())
        assert back["result"]["end"] == end and back["result"]["stall"] is stall and back["schema"] == "om-fight-2"
        assert back["frames"][-1]["alive"] == back["result"]["survivors"]


@pytest.mark.parametrize("end,stall,label", [("wipe", False, "end: A wins (wipe)"), ("silence", True, "end: stall (silence)"), ("cap", False, "end: cap")])
def test_hud_prints_the_end_word_on_the_last_frame_and_stall_only_for_a_stall(end, stall, label, tmp_path, monkeypatch):
    """H-040 "Orders and fight end": "The replay HUD prints `end: wipe|silence|cap` and `STALL` on the last frame." Frame 0 shows neither `end:` nor `STALL`; stepping to
    the last frame shows a Label text containing `end: <end>`, and a Label text containing `STALL` if and only if the fight is a stall (end silence with both sides alive)."""
    path, doc = _v2_fight(end, stall, tmp_path)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        assert st["qa"]["frame_count"] == 3
        first = " | ".join(_hud_lines(st))
        assert "end:" not in first and "STALL" not in first, "end or STALL shown on frame 0: %s" % first
        _key(g, "Space")
        _key(g, "Space")
        st = _state(g, lambda q: q["frame"] == 2, timeout=15.0, label="frame 2")
        lines = _hud_lines(st)
        assert any(label in t for t in lines), "no HUD text with %r among Label texts %s" % (label, lines)
        assert any("STALL" in t for t in lines) is stall, "STALL expected %s among Label texts %s" % (stall, lines)
    finally:
        g.stop()


# ================================================================ H-053 stage 2 (arena-stage2-roles-ranges-winrates)
# spec: docs/stories/H-053.md "Replay" and "Interfaces" 4; Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn.
# Interfaces 4, quoted: "Replay `qa_state` gains `targets` (list of `[unit_id, target_id]` for the living units of the current frame that have a target), `first_shot_frame`
# (frame index, not tick, of the first frame in which any unit's hp is lower than in the previous frame; -1 when none), `seed` (the fight's `seed`) and `rate_a` (from
# `<id>.rate.json` beside the fight file when it exists, else `null`). HUD line appends `seed <n>` and, when a rate file exists, `rate <0.00>`. The first-shot marker is a ring
# on the damaged unit on that frame." Tests line: "target lines present in `qa_state`, first-shot frame index equals the first hp drop in the file".
# Visible-only, no test (the marker ring and target line are drawn, qa_state carries no pixels): reported as a gap, judged by eye at the story's play.
# Fixture premise (dumped by the control below): 4 frames of snapshot.example(schema om-fight-2), 2 units a side with ids 1,2 (A) and 3,4 (B); hp is 100.0 on frames 0 and 1,
# B unit 3 drops to 60.0 on frame 2 (the first hp drop, so first_shot_frame 2), A unit 1 targets unit 3 from frame 1 on; unit 2 never has a target.

H053_KEYS = {"targets", "first_shot_frame", "seed", "rate_a"}


def _shot_fight(tmp_path: Path, seed: int = 7, drop: bool = True) -> tuple[Path, dict]:
    doc = snapshot.example(frames=4, schema=snapshot.SCHEMA_V2)
    doc["seed"] = seed
    doc["result"]["survivors"] = [2, 0]
    for n, frame in enumerate(doc["frames"]):
        for u in frame["units"]:
            if u["id"] == 1 and n >= 1:
                u["target"] = 3
        if drop and n == 2:
            for u in frame["units"]:
                if u["id"] == 3:
                    u["hp"] = 60.0
    if not drop:   # nobody is ever hurt: undo the example's last-frame deaths, a capped draw with all four alive
        for u in doc["frames"][-1]["units"]:
            u["hp"], u["alive"] = 100.0, True
        doc["frames"][-1]["alive"] = [2, 2]
        doc["result"].update({"winner": "draw", "survivors": [2, 2], "capped": True, "end": "cap", "agree": False})
    assert snapshot.validate(doc) == [], snapshot.validate(doc)
    return _write_fight(tmp_path / ("L-0001-s%d.fight.json" % seed), doc), doc


def _first_hp_drop(doc: dict) -> int:
    for n in range(1, len(doc["frames"])):
        before = {u["id"]: u["hp"] for u in doc["frames"][n - 1]["units"]}
        if any(u["hp"] < before[u["id"]] for u in doc["frames"][n]["units"]):
            return n
    return -1


def test_control_shot_fixture_has_its_first_hp_drop_on_frame_two_and_a_target_from_frame_one(tmp_path):
    """H-053 control, green today: the fixture validates, its first hp drop (computed here from the file) is frame 2, unit 1 has target 3 on frames 1 to 3, and the
    drop-less variant has none, so a red below is the missing qa_state keys and not the fixture. Also: today's qa_state does not yet carry the H-053 keys is the red's reason."""
    path, doc = _shot_fight(tmp_path)
    assert _first_hp_drop(doc) == 2
    assert [next(u for u in f["units"] if u["id"] == 1)["target"] for f in doc["frames"]] == [None, 3, 3, 3]
    _, quiet = _shot_fight(tmp_path, seed=8, drop=False)
    assert _first_hp_drop(quiet) == -1


def test_qa_state_carries_the_stage2_keys_and_the_seed(tmp_path, monkeypatch):
    """Interfaces 4: qa_state has `targets`, `first_shot_frame`, `seed`, `rate_a`; `seed` is the file's seed (7); with no rate file beside the fight `rate_a` is null."""
    path, doc = _shot_fight(tmp_path)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        qa = _state(g)["qa"]
        assert H053_KEYS <= set(qa), "qa_state keys %s lack %s" % (sorted(qa), sorted(H053_KEYS - set(qa)))
        assert qa["seed"] == 7 and qa["rate_a"] is None
    finally:
        g.stop()


def test_first_shot_frame_equals_the_first_hp_drop_in_the_file(tmp_path, monkeypatch):
    """Tests line "first-shot frame index equals the first hp drop in the file": `first_shot_frame` is the frame index (2), not the tick, and is the same from frame 0 on."""
    path, doc = _shot_fight(tmp_path)
    assert _first_hp_drop(doc) == 2 and doc["frames"][2]["tick"] != 2
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        assert _state(g)["qa"]["first_shot_frame"] == 2
    finally:
        g.stop()


def test_first_shot_frame_is_minus_one_when_no_hp_ever_drops(tmp_path, monkeypatch):
    """Interfaces 4: `first_shot_frame` is -1 when no frame has an hp drop (the detector's negative case)."""
    path, _ = _shot_fight(tmp_path, seed=8, drop=False)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        assert _state(g)["qa"]["first_shot_frame"] == -1
    finally:
        g.stop()


def test_targets_list_the_living_units_with_a_target_on_the_current_frame(tmp_path, monkeypatch):
    """Tests line "target lines present in `qa_state`": frame 0 has no target (`targets` empty); after one step (frame 1) it is [[1, 3]], unit 1 targeting unit 3."""
    path, _ = _shot_fight(tmp_path)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        assert st["qa"].get("targets") == [], "frame 0 targets %r" % (st["qa"].get("targets"),)
        _key(g, "Space")
        st = _state(g, lambda q: q["frame"] == 1, timeout=15.0, label="frame 1")
        assert [list(t) for t in st["qa"].get("targets", [])] == [[1, 3]]
    finally:
        g.stop()


def test_rate_a_comes_from_the_rate_file_beside_the_fight_and_the_hud_shows_seed_and_rate(tmp_path, monkeypatch):
    """Interfaces 4: with `L-0001.rate.json` beside the fight file, `rate_a` is that file's value (0.75) and the HUD line carries `seed 7` and `rate 0.75`; without the rate file the
    HUD has `seed 7` and no `rate`."""
    path, _ = _shot_fight(tmp_path)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        lines = _hud_lines(_state(g))
        assert any("seed 7" in t for t in lines), "no 'seed 7' among Label texts %s" % lines
        assert not any("rate " in t for t in lines), "a rate shown with no rate file: %s" % lines
    finally:
        g.stop()
    (tmp_path / "L-0001.rate.json").write_text(json.dumps({"layout_id": "L-0001", "seeds": [7], "rate_a": 0.75, "predict_rate": 0.75}) + "\n")
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        assert st["qa"].get("rate_a") == 0.75
        lines = _hud_lines(st)
        assert any("seed 7" in t for t in lines) and any("rate 0.75" in t for t in lines), "HUD Label texts %s" % lines
    finally:
        g.stop()


# ================================================================ H-053 defects found at the stage 2 look review (brief to the test writer, 2026-11-02)
# (1) Range rings: the replay builds its rows with range 0.0 and the fight file carried none, so no ring is drawn and the legend prints "<role>: no range". Intended: the fight file
#     has a top-level `ranges` map {role: range} (snapshot.py, run.py) and the replay reads the role's range from it. New qa_state key, named here: `ring_count` = the number of unit
#     range rings the scene has drawn (one per unit whose role has a range above 0; 0 for a file without `ranges`). The legend text is read from the Label texts, as the HUD is.
# (3) End line: the last frame printed the per-fight `winner <w>  predicted <p>  agree|disagree` (the old A/B/draw) even beside a rate file, which contradicts the page. Intended: with a
#     rate file beside the fight (`rate_a` not null) the end line is the rate verdict `rate <rate_a> vs <predict_rate> agree|disagree` from the rate file; with no rate file the old text.
#     New qa_state key, named here: `end_line` = the end HUD line's text on the last frame, "" on any other frame. Floats are written with two decimals (the HUD's `rate %.2f`); the
#     tests use values (0.25, 0.75) that read the same under %.2f, %g and str(), so the number format is not pinned.

def _ranged_fight(tmp_path: Path, ranges: dict | None) -> Path:
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    if ranges is not None:
        doc["ranges"] = ranges
    else:
        doc.pop("ranges", None)
    return _write_fight(tmp_path / "L-0001-s1.fight.json", doc)


def test_control_without_ranges_the_legend_says_no_range_and_the_fixture_has_four_raiders(tmp_path, monkeypatch):
    """Control, green today: a v2 fight file with no `ranges` replays with a legend line `Raider: no range` (the v1 behaviour that must survive for old files) and 4 units on
    frame 0 (the fixture premise for the ring count below)."""
    path = _ranged_fight(tmp_path, None)
    assert sum(len(f["units"]) for f in json.loads(path.read_text())["frames"][:1]) == 4
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        lines = _hud_lines(_state(g))
        assert any("Raider: no range" in t for t in lines), "Label texts %s" % lines
    finally:
        g.stop()


def test_a_file_without_ranges_has_no_rings(tmp_path, monkeypatch):
    """Control for the ring count (red today only because the key is missing): a file with no `ranges` draws 0 rings, `ring_count` 0, and keeps the `no range` legend line."""
    path = _ranged_fight(tmp_path, None)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        assert st["qa"].get("ring_count") == 0, "qa_state keys %s" % sorted(st["qa"])
        assert any("Raider: no range" in t for t in _hud_lines(st))
    finally:
        g.stop()


def test_a_file_with_ranges_draws_a_ring_per_unit_and_the_legend_gives_the_range(tmp_path, monkeypatch):
    """Brief 2026-11-02: "a replay of a fight with ranges has rings and the legend text has no 'no range' line". With `ranges` {"Raider": 200.0} the four Raiders have four rings
    (`ring_count` 4), the legend line reads `Raider: range 200 wu`, and no Label text says `no range`."""
    path = _ranged_fight(tmp_path, {"Raider": 200.0})
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        lines = _hud_lines(st)
        assert st["qa"].get("ring_count") == 4, "ring_count %r, qa_state keys %s" % (st["qa"].get("ring_count"), sorted(st["qa"]))
        assert any("Raider: range 200 wu" in t for t in lines), "Label texts %s" % lines
        assert not any("no range" in t for t in lines), "a 'no range' line with ranges in the file: %s" % lines
    finally:
        g.stop()


def _end_fight(tmp_path: Path, rate: dict | None) -> Path:
    path, _ = _shot_fight(tmp_path)   # winner A, predict A, agree true on the last frame (the old text would read "winner A  predicted A  agree")
    if rate is not None:
        (tmp_path / "L-0001.rate.json").write_text(json.dumps(dict({"layout_id": "L-0001", "seeds": [7]}, **rate)) + "\n")
    return path


def _last_frame(g: ReplayGame) -> dict:
    _state(g)
    _key(g, "Space")
    _key(g, "Space")
    _key(g, "Space")
    return _state(g, lambda q: q["frame"] == 3, timeout=15.0, label="last frame")


def test_control_without_a_rate_file_the_end_line_is_the_old_text(tmp_path, monkeypatch):
    """Control, green today: with no rate file beside the fight the last frame's HUD says `winner A  predicted A  agree` (the old per-fight verdict stays for v1 files)."""
    path = _end_fight(tmp_path, None)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        lines = _hud_lines(_last_frame(g))
        assert any(t.startswith("winner A  predicted A  agree") for t in lines), "Label texts %s" % lines
    finally:
        g.stop()


def test_without_a_rate_file_end_line_is_the_old_text_and_empty_before_the_last_frame(tmp_path, monkeypatch):
    """Brief 2026-11-02: "with no rate file the old text", through the new key: `end_line` is "" on frame 0 and starts `winner A  predicted A  agree` on the last frame."""
    path = _end_fight(tmp_path, None)
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        assert st["qa"].get("end_line") == "", "qa_state keys %s" % sorted(st["qa"])
        st = _last_frame(g)
        assert str(st["qa"].get("end_line", "")).startswith("winner A  predicted A  agree"), st["qa"].get("end_line")
    finally:
        g.stop()


@pytest.mark.parametrize("rate_a,predict_rate,agree,word", [(0.75, 0.75, True, "agree"), (0.25, 0.75, False, "disagree")], ids=["agree", "disagree"])
def test_with_a_rate_file_the_end_line_is_the_rate_verdict(rate_a, predict_rate, agree, word, tmp_path, monkeypatch):
    """Brief 2026-11-02: "when a rate file is beside the fight (rate_a not null) the end line shows the rate verdict (`rate <rate_a> vs <predict_rate> agree|disagree` from the rate file)".
    The fight's own result says agree (winner A, predict A), so the old text would say `agree` in both cases; the line must read the rate file's `agree` and carry no `predicted`."""
    path = _end_fight(tmp_path, {"rate_a": rate_a, "predict_rate": predict_rate, "agree": agree})
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _last_frame(g)
        want = "rate %.2f vs %.2f %s" % (rate_a, predict_rate, word)
        line = str(st["qa"].get("end_line", ""))
        assert want in line and "predicted" not in line, "end_line %r, want it to contain %r (qa_state keys %s)" % (line, want, sorted(st["qa"]))
        lines = _hud_lines(st)
        assert any(want in t and "predicted" not in t for t in lines), "Label texts %s" % lines
    finally:
        g.stop()
