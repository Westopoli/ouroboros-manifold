"""S-132 play: walkers read as a force, not dots (shapes ship regardless of Q-132-02; seen-reachable lane C list).
Moment 'force': ground3d present, units_px has one entry per unit in the frame, and no two own units project to the same
pixel unless they share a position in the frame (a stack of models must not collapse to a point). CONTROL: the same
check flags a doctored pair of units forced onto one pixel."""
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


def _collapsed(units_px, units):
    seen = {}
    bad = []
    for i, p in units_px.items():
        key = tuple(round(v) for v in _play.px(p))
        j = seen.setdefault(key, i)
        if j != i and (units[i]["x"], units[i]["y"]) != (units[j]["x"], units[j]["y"]):
            bad.append((j, i))
    return bad


def test_s132_force_is_not_collapsed(game):
    doc_units = {"a": {"x": 0.0, "y": 0.0}, "b": {"x": 50.0, "y": 0.0}}
    assert _collapsed({"a": [10, 10], "b": [10, 10]}, doc_units) == [("a", "b")], "CONTROL: the collapse check missed two units on one pixel"
    _play.ground3d(game)
    q = _play.qa(game)
    _play.evidence(game, "s132", "force")
    assert len(q["units_px"]) == q["unit_count"], "S-132: units_px %d vs unit_count %d" % (len(q["units_px"]), q["unit_count"])
    assert _collapsed(q["units_px"], q["units"]) == [], "S-132: distinct units project to one pixel: %s" % _collapsed(q["units_px"], q["units"])
