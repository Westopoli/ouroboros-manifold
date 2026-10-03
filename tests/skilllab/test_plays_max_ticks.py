# spec: ruling A201 (b): plays set max_ticks 8000 when max(size, enemy_heads) >= 32, else the 6000 default
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import plays  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.plays import blob_play, damage_play, line_play, max_ticks_for, reach_play  # noqa: E402
from scripts.skilllab.positions import ambush_play, bait_play, fall_back_play  # noqa: E402


def test_constant():
    assert plays.MAX_TICKS_BIG == 8000


@pytest.mark.parametrize("size,heads,want", [(16, 24, 6000), (32, 8, 8000), (16, 32, 8000), (31, 31, 6000),
                                             (32, 32, 8000), (1, 1, 6000)])
def test_max_ticks_for(size, heads, want):
    assert max_ticks_for(size, heads) == want


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play, damage_play])
def test_plain_plays_big_and_small(play):
    assert play(32)(8, False).max_ticks == 8000
    assert play(16)(32, False).max_ticks == 8000
    assert play(16)(24, False).max_ticks == 6000


def test_asym_play_big_and_small():
    mk = lambda n: asym_play(n, Side("blob"), Side("line"))
    assert mk(32)(8, False).max_ticks == 8000
    assert mk(16)(32, False).max_ticks == 8000
    assert mk(16)(24, False).max_ticks == 6000


@pytest.mark.parametrize("play", [bait_play, ambush_play, fall_back_play])
def test_position_plays_at_32_get_8000(play):
    assert play(32)(8, False).max_ticks == 8000
    assert play(16)(8, False).max_ticks == 6000
