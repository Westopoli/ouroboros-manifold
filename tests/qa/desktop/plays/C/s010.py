"""S-010 play: the player sees their force standing on the ground (walker Y = ground height, section 7). Moment 'standing':
ground3d present, units_px lists every own unit, and the screenshot is not blank (differs from its median background by
the same blank-frame detector flow spine row 13 uses, at least 300 px). CONTROL: a uniform image fails the detector."""
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


import numpy as np
from PIL import Image

MIN_DIFF_PX = 300  # test_flow_spine.MIN_TACTICAL_DIFF_PX, a copy of an existing number


def _diff_px(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    med = np.median(a.reshape(-1, 3), axis=0)
    return int((np.abs(a - med).sum(axis=2) > 24).sum())


def test_s010_force_is_drawn_on_the_ground(game, tmp_path):
    blank = tmp_path / "blank.png"
    Image.new("RGB", (64, 64), (90, 90, 90)).save(blank)
    assert _diff_px(blank) < MIN_DIFF_PX, "CONTROL: a uniform image passes the blank-frame detector"
    g = _play.ground3d(game)
    q = _play.qa(game)
    own = [i for i, u in q["units"].items() if u.get("faction") == q.get("local_faction", 0)]
    assert own and all(i in q["units_px"] for i in own), "S-010: own units missing from units_px"
    shot = _play.evidence(game, "s010", "standing")
    assert _diff_px(shot) >= MIN_DIFF_PX, "S-010: the tactical screenshot is blank (%d differing px)" % _diff_px(shot)
