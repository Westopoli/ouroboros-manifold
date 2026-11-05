# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-7
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-02, criteria 7 to 9 (spec lines 33 to 35): the replay builds the fight file's landscape, draws a control fight without the ground, and shows the
blocked count on its tick line (scenes/proto/fight_replay/fight_replay.gd).

7: `landscape` is read from the fight file ("small_flat" without the key) and `qa_state().landscape` names the preset used.
8: a control fight whose twin layout JSON has `features == []` draws none: `qa_state().features == []` (holds once the twin path is in the fight file; the replay's
   `_load_features` already reads the JSON beside `layout_path`).
9: the tick line is `tick %d  A %d  B %d  blocked %d  frame %d/%d` and `qa_state().hud_tick` is its text.

Launcher and helpers are those of tests/qa/test_fight_replay.py (xvfb, software GL, qa-port); the fight files are hand-written JSON (not run through the arena), like
tests/qa/test_fight_replay_features.py writes them. The scene draws the landscape through the layout shot's own `_add_tier_tint` and `_tiered_terrain`; qa_state carries
no key for the tint, so the drawing itself is a look for Westley (see BOUNDARIES.md)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_fight_replay import ReplayGame, RESOLUTION, SCENE, _hud_lines, _key, _state, _write_fight, pick_free_port  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402

SLOPE = {"kind": "slope", "x": 2000.0, "y": 2000.0, "length": 600, "width": 200, "heading": 0.0, "from_band": 0, "to_band": 1}
TICK_LINE = "tick %d  A %d  B %d  blocked %d  frame %d/%d"


def _side(x, face, layer, n=2):
    return {"headcount": n, "units": [{"role": "Raider", "x": x + 40.0 * i, "y": 2000.0, "facing": face, "layer": layer, "range": 200.0} for i in range(n)]}


def _layout(lid, features):
    return {"id": lid, "situation": "slope", "landscape": "small_tiered", "seed": 1, "predict": "A", "predict_why": "toy", "verdict": "", "feedback": "",
            "defender": "A", "side_a": _side(2480.0, 0.0, 1), "side_b": _side(1000.0, 3.1416, 0), "features": features}


def _stage(tmp_path, stem, features, landscape="small_tiered", blocked=None, units=2, frames=3):
    """A fight file `<stem>-s1.fight.json` whose layout twin `<stem>.json` (beside a TOML stub) carries `features`; `landscape` None leaves the key out, `blocked` is
    {frame index: [unit ids]}. Returns the fight path."""
    (tmp_path / (stem + ".json")).write_text(json.dumps(_layout(stem, features)))
    (tmp_path / (stem + ".toml")).write_text('id = "%s"\n# the JSON twin beside this file carries the same layout\n' % stem)
    doc = snapshot.example(frames=frames, units_per_side=units, schema=snapshot.SCHEMA_V2)
    doc["layout_id"], doc["layout_path"] = stem, str(tmp_path / (stem + ".toml"))
    if landscape is not None:
        doc["landscape"] = landscape
    for i, ids in (blocked or {}).items():
        doc["frames"][i]["blocked"] = ids
    return _write_fight(tmp_path / (stem + "-s1.fight.json"), doc)


def _replay(fight, monkeypatch):
    monkeypatch.setenv("OM_FIGHT", str(fight))
    for k in ("OM_AUTOPLAY", "OM_SHOT_OUT", "OM_LAYOUT"):
        monkeypatch.delenv(k, raising=False)
    g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    g.start()
    g.wait_for_port(timeout=90.0)
    return g


def _qa(fight, monkeypatch, **want):
    g = _replay(fight, monkeypatch)
    try:
        return _state(g, **want)["qa"]
    finally:
        g.stop()


# ---------------------------------------------------------------- criterion 7: landscape

@pytest.mark.parametrize("landscape,want", [("small_tiered", "small_tiered"), ("small_flat", "small_flat"), (None, "small_flat")],
                         ids=["tiered", "flat", "no-key-falls-back-to-flat"])
def test_replay_builds_the_fight_files_landscape(landscape, want, tmp_path, monkeypatch):
    """Criterion 7, spec line 33: `qa_state().landscape` is the preset the replay built: the file's `landscape`, `small_flat` for a file without the key."""
    fight = _stage(tmp_path, "L-0056", [SLOPE], landscape=landscape)
    qa = _qa(fight, monkeypatch)
    assert qa.get("landscape") == want, "qa_state landscape %r, want %r (keys: %s)" % (qa.get("landscape"), want, sorted(qa))
    assert [f["kind"] for f in qa["features"]] == ["slope"], "the slope feature must still be drawn on the tiered landscape"


# ---------------------------------------------------------------- criterion 8: the control draws no features

def test_control_fight_draws_no_features_and_keeps_the_tiered_landscape(tmp_path, monkeypatch):
    """Criterion 8, spec line 34: the control fight's `layout_path` names a twin whose `features` is `[]`; `qa_state().features == []`, while the landscape is still the
    fight file's. The main fight of the same layout, beside it, lists the slope (the twin's emptiness is what removes the ground, not the scene)."""
    main = _stage(tmp_path, "L-0056", [SLOPE])
    control = _stage(tmp_path, "L-0056-control", [])
    assert [f["kind"] for f in _qa(main, monkeypatch)["features"]] == ["slope"]
    qa = _qa(control, monkeypatch)
    assert qa["features"] == []
    assert qa.get("landscape") == "small_tiered"


# ---------------------------------------------------------------- criterion 9: the HUD tick line

def test_hud_tick_line_carries_the_frames_blocked_count_on_every_frame(tmp_path, monkeypatch):
    """Criterion 9, spec line 35: `hud_tick` is `tick %d  A %d  B %d  blocked %d  frame %d/%d` with the current frame's blocked count, it is the text of a HUD Label,
    and `blocked_units` is the same frame's list. Three frames with 0 (no `blocked` key: absent counts as none), 1 and 11 (two digits) blocked units."""
    ids = list(range(1, 13))
    fight = _stage(tmp_path, "L-0057", [SLOPE], blocked={1: [ids[0]], 2: ids[:11]}, units=6)
    doc = json.loads(fight.read_text())
    g = _replay(fight, monkeypatch)
    try:
        for i, count in enumerate((0, 1, 11)):
            st = _state(g, want=lambda q, f=i: q.get("frame") == f)
            frame, qa = doc["frames"][i], st["qa"]
            want = TICK_LINE % (frame["tick"], frame["alive"][0], frame["alive"][1], count, i, 3)
            assert qa.get("hud_tick") == want, "frame %d: hud_tick %r, want %r" % (i, qa.get("hud_tick"), want)
            assert want in _hud_lines(st), "no HUD Label shows %r among %s" % (want, _hud_lines(st))
            assert len(qa["blocked_units"]) == count
            if i < 2:
                _key(g, "Space")
    finally:
        g.stop()
