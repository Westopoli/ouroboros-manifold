# spec: docs/stories/H-063.md (arena stage 3); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn
"""H-063, the replay draws the ground and marks blocked units (scenes/proto/fight_replay/fight_replay.gd, sharing scenes/proto/layout_shot/layout_shot.gd).

Story lines proved here:
  "Replay draws the same geometry as the layout shot (shared drawing code from `scenes/proto/layout_shot/layout_shot.gd`, no second drawing) under the units; the stage 2
   readability rules (camera fit, role rings and glyphs, labelled end line) carry over."
  "where the geometry slows or stops a unit (a marker on units blocked for more than 2 s ...)"
  Tests: "`tests/qa/test_fight_replay.py` (features drawn, `qa_state()` lists `features` kinds drawn and `blocked_units` per frame)". This file sits beside it (new file,
  test_fight_replay.py untouched) and reuses its launcher.

Premises dumped (base aac0cd41, 2026-11-02): the layout shot's qa_state `features` is a list of `{kind, x, y}` (layout_shot.gd:588-590); the replay's qa_state has no
`features` and no `blocked_units` key; the replay builds its own layout dict with `situation: "fight_replay"` and no features (fight_replay.gd:94).

OPEN INTERFACES (not in the story; Q for the Architect in the report): (1) how the replay learns the features: this file's fight fixture carries BOTH candidate channels, a top-level
`features` key in the fight file and a `layout_path` pointing at a layout TOML with its `.json` twin beside it (the produce.write_layout pair), and asserts only the
qa_state, so either channel passes. (2) What `blocked_units` holds and where the runner writes it: only the key's presence and type (a list of unit ids, `[]` when none)
are asserted per frame; the marker's content waits on the Architect's ruling.

Controls (green today): the layout shot reports the fixture's feature kinds; the fixture fight validates."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_fight_replay import ReplayGame, ShotGame, SCENE, SHOT_SCENE, RESOLUTION, _key, _state, _write_fight, pick_free_port, wait_for  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WALLS = [{"x": 2000.0, "y": 1650.0, "w": 600.0, "h": 500.0}, {"x": 2000.0, "y": 2350.0, "w": 600.0, "h": 500.0}]
FEATURES = [{"kind": "chokepoint", "x": 2000.0, "y": 2000.0, "gap": 200, "radius": 600, "walls": WALLS}]


def _side(x, face, n=2):
    return {"headcount": n, "units": [{"role": "Vanguard", "x": x + 40.0 * i, "y": 2000.0, "facing": face, "layer": 0, "range": 300.0} for i in range(n)]}


@pytest.fixture()
def staged(tmp_path):
    """(layout json path, fight path): a chokepoint layout (TOML text and JSON twin) and a 3-frame om-fight-2 file naming it, with the features also inline."""
    layout = {"id": "L-0055", "situation": "chokepoint", "landscape": "small_flat", "seed": 1, "predict": "A", "predict_why": "toy", "verdict": "", "feedback": "",
              "defender": "A", "side_a": _side(1000.0, 0.0), "side_b": _side(3000.0, 3.1416), "features": FEATURES}
    lj = tmp_path / "L-0055.json"
    lj.write_text(json.dumps(layout))
    (tmp_path / "L-0055.toml").write_text('id = "L-0055"\n# the JSON twin beside this file carries the same layout\n')
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    doc["layout_id"], doc["layout_path"], doc["features"] = "L-0055", str(tmp_path / "L-0055.toml"), FEATURES
    assert snapshot.validate({k: v for k, v in doc.items() if k != "features"}) == []
    return lj, _write_fight(tmp_path / "L-0055-s1.fight.json", doc)


def _shot_features(lj, monkeypatch):
    monkeypatch.setenv("OM_LAYOUT", str(lj))
    monkeypatch.delenv("OM_SHOT_OUT", raising=False)
    monkeypatch.delenv("OM_FIGHT", raising=False)
    g = ShotGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    g.start()
    try:
        g.wait_for_port(timeout=90.0)
        return wait_for(g.client, lambda r: r.get("scene") == SHOT_SCENE and "qa" in r, timeout=60.0, label="layout_shot scene")["qa"]["features"]
    finally:
        g.stop()


def _replay(fight, monkeypatch):
    monkeypatch.setenv("OM_FIGHT", str(fight))
    for k in ("OM_AUTOPLAY", "OM_SHOT_OUT", "OM_LAYOUT"):
        monkeypatch.delenv(k, raising=False)
    g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    g.start()
    g.wait_for_port(timeout=90.0)
    return g


def test_control_layout_shot_reports_the_fixture_feature_kinds(staged, monkeypatch):
    """H-063 "Replay draws the same geometry as the layout shot". CONTROL (green today): the layout shot on the fixture layout lists one feature of kind
    `chokepoint`, so the replay tests below compare against a shot that works."""
    lj, _ = staged
    feats = _shot_features(lj, monkeypatch)
    assert [f["kind"] for f in feats] == ["chokepoint"], feats


def test_replay_qa_state_lists_the_features_drawn_as_the_shot_does(staged, monkeypatch):
    """H-063 Tests "`qa_state()` lists `features` kinds drawn". The replay's `features` equals the layout shot's list for the same layout (same shape, same entries:
    shared drawing, not a second one)."""
    lj, fight = staged
    want = _shot_features(lj, monkeypatch)
    g = _replay(fight, monkeypatch)
    try:
        qa = _state(g)["qa"]
        assert "features" in qa, "replay qa_state has no `features` (keys: %s)" % sorted(qa)
        assert qa["features"] == want
    finally:
        g.stop()


def test_replay_qa_state_has_blocked_units_on_every_frame(staged, monkeypatch):
    """H-063 Tests "`blocked_units` per frame". On each of the three frames qa_state carries `blocked_units`, a list of unit ids (ints); the fixture has no blocking
    data, so it is `[]` there (content ruling pending, see the module docstring)."""
    _, fight = staged
    g = _replay(fight, monkeypatch)
    try:
        for want_frame in range(3):
            qa = _state(g, want=lambda q, f=want_frame: q.get("frame") == f)["qa"]
            assert isinstance(qa.get("blocked_units"), list), "frame %d: no `blocked_units` list (keys: %s)" % (want_frame, sorted(qa))
            assert all(isinstance(i, int) for i in qa["blocked_units"])
            if want_frame < 2:
                _key(g, "Space")
    finally:
        g.stop()


def test_replay_draws_features_through_the_layout_shot_code_not_a_second_drawing():
    """H-063 "shared drawing code from `scenes/proto/layout_shot/layout_shot.gd`, no second drawing". CONTROL half (green today): layout_shot.gd defines `_add_feature`.
    Red half: fight_replay.gd calls it and defines no feature-drawing function of its own."""
    shot = (ROOT / "scenes/proto/layout_shot/layout_shot.gd").read_text()
    replay = (ROOT / "scenes/proto/fight_replay/fight_replay.gd").read_text()
    assert re.search(r"^func _add_feature\(", shot, re.M)
    assert not re.search(r"^func _add_feature\w*\(", replay, re.M), "fight_replay.gd defines its own feature drawing"
    assert "_add_feature(" in replay, "fight_replay.gd never calls the layout shot's _add_feature"
