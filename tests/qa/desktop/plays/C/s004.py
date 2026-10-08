"""S-004 play: a unit mid-transition is visibly in transition (R-004-01, R-004-06). Moment 'transit': select every own unit,
send them across the map with a move click, step in chunks and watch for a unit whose state has bit 4 (section 2); when one
exists the slope view must count it (slope_view.in_transit equals the number of units with state & 4). CONTROL: before the
order no unit is in transit."""
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


def _own(q):
    f = q.get("local_faction", 0)
    return [i for i, u in q.get("units", {}).items() if u.get("faction") == f]


def _in_transit(q):
    return [i for i, u in q.get("units", {}).items() if int(u.get("state", 0)) & 4]


def test_s004_transit_is_visible(game):
    c = game.client
    q0 = _play.qa(game)
    assert not _in_transit(q0), "CONTROL: a unit is in transit before any order"
    c.call("qa_select", [int(i) for i in _own(q0)])
    _play.ground3d(game)
    target = (1700.0, 900.0)  # far corner of the 1920x1080 screen
    c.call("input", "click", target[0], target[1], 2)
    seen = None
    for _ in range(40):
        _play.step(game, 25)
        q = _play.qa(game)
        if _in_transit(q):
            seen = q
            break
    assert seen is not None, "R-004-01: no unit entered layer transit within 1000 ticks of a cross-map move"
    g = _play.ground3d(game)
    _play.evidence(game, "s004", "transit")
    assert g["slope_view"]["in_transit"] == len(_in_transit(_play.qa(game))), "R-004-01: slope view in_transit %r disagrees with the frame" % g["slope_view"]
