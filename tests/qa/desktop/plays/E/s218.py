"""S-218 play (lane E1, piece E1h): strongpoints stand on the slopes of the ground map and read by owner colour.
Moment 'slopes': the live scene's qa_state `strongpoints` key (spec section 2 inventory; node StrongpointLayer, E1l/E1p)
lists at least one strongpoint, every one carries an owner, and the owners are not all the same colour key (R-218-08:
distinguishable by owner from units and bases). CONTROL: the owner check flags a doctored all-one-owner list.
Red on main: no `strongpoints` key in qa_state (the layer is not built). Uses the lane C driver, imported by path."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "C"))
import _play  # noqa: E402


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def _owners_distinct(rows):
    return len({r.get("owner") for r in rows}) > 1


def test_s218_strongpoints_on_slopes(game):
    assert not _owners_distinct([{"owner": 0}, {"owner": 0}]), "CONTROL: the owner check missed an all-one-owner list"
    assert _owners_distinct([{"owner": 0}, {"owner": 1}]), "CONTROL: the owner check missed two owners"
    q = _play.qa(game)
    rows = q.get("strongpoints")
    assert isinstance(rows, list) and rows, "qa_state.strongpoints missing or empty; qa keys = %s" % sorted(q)
    assert all("owner" in r and "x" in r and "y" in r for r in rows)
    assert _owners_distinct(rows), "strongpoints do not read by owner"
    _play.evidence(game, "S-218", "slopes")
