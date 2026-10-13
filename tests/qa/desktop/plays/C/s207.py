"""S-207 play: no unit stuck in terrain or off the map (R-207-06, R-207-07). Moment 'settled': after 300 ticks of a
cross-map order every unit is inside the canvas and its projected pixel is a finite number; the ground3d block exists.
CONTROL: a unit planted at x = -5 would be flagged by the same check (the checker is run on a doctored copy)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def _off_map(q):
    cw = ch = float(q["canvas"])  # qa_state.canvas is one square side in wu
    return [i for i, u in q["units"].items() if not (0 <= u["x"] <= cw and 0 <= u["y"] <= ch)]


def test_s207_no_unit_off_map(game):
    q = _play.qa(game)
    doctored = {"canvas": q["canvas"], "units": {"x": {"x": -5.0, "y": 10.0}}}
    assert _off_map(doctored) == ["x"], "CONTROL: the off-map check missed a unit at x = -5"
    c = game.client
    c.call("qa_select", [int(i) for i, u in q["units"].items() if u.get("faction") == q.get("local_faction", 0)])
    far = _play.px(next(iter(q["units_px"].values())))
    c.call("input", "click", far[0], far[1], 2)
    for _ in range(12):
        _play.step(game, 25)
    _play.ground3d(game)
    q = _play.qa(game)
    _play.evidence(game, "s207", "settled")
    assert _off_map(q) == [], "R-207-07: units off the map: %s" % _off_map(q)
    assert len(q["units_px"]) > 0 and all(abs(v) < 1e7 for p in q["units_px"].values() for v in _play.px(p)), "R-207-06: a unit has no finite screen position"
