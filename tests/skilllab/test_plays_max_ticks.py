# spec: ruling A201 (b) as changed 2026-10-06 (Westley, tick cap, provisional; TD-LAB-tick-cap): one cap of 12000 for big and small cells alike
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import plays  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.plays import blob_play, damage_play, line_play, max_ticks_for, reach_play  # noqa: E402
from scripts.skilllab.positions import ambush_play, bait_play, fall_back_play  # noqa: E402


def test_constant():
    """LAB-REV2-FIX (decision 41 ruling 7, TD-LAB-REV2-FIX-maxticks): MAX_TICKS_BIG is dead logic (it equalled the Setup default) and is
    deleted; the cap every play carries is the Setup default, 12000 (the parametrized cases below keep that)."""
    assert not hasattr(plays, "MAX_TICKS_BIG")
    assert Setup(groups=(), unit_types={}).max_ticks == 12000 == max_ticks_for(48, 48) == max_ticks_for(8, 8)


@pytest.mark.parametrize("size,heads,want", [(16, 24, 12000), (32, 8, 12000), (16, 32, 12000), (31, 31, 12000),
                                             (32, 32, 12000), (1, 1, 12000)])
def test_max_ticks_for(size, heads, want):
    assert max_ticks_for(size, heads) == want


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play, damage_play])
def test_plain_plays_big_and_small(play):
    assert play(32)(8, False).max_ticks == 12000
    assert play(16)(32, False).max_ticks == 12000
    assert play(16)(24, False).max_ticks == 12000


def test_asym_play_big_and_small():
    mk = lambda n: asym_play(n, Side("blob"), Side("line"))
    assert mk(32)(8, False).max_ticks == 12000
    assert mk(16)(32, False).max_ticks == 12000
    assert mk(16)(24, False).max_ticks == 12000


@pytest.mark.parametrize("play", [bait_play, ambush_play, fall_back_play])
def test_position_plays_at_32_get_12000(play):
    assert play(32)(8, False).max_ticks == 12000
    assert play(16)(8, False).max_ticks == 12000
