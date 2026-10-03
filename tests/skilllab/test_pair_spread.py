# spec: Architect ruling A187 item 2 (pair spread) - scripts/skilllab/scan.py pair_spread
"""pair_spread(cell): per seed the mean margin of its two side-swapped fights, then the lowest and highest. No engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import CellResult, FightResult  # noqa: E402
from scripts.skilllab.scan import pair_spread  # noqa: E402


def _f(margin):
    return FightResult(outcome="side0", margin=margin, strength_left=(1.0, 0.0), survivors=(1, 0), heads=(1, 1),
                       ticks=10, first_contact_tick=0, firing=[(0, 1, 1)], firing_unit_seconds=(0.25, 0.25))


def _cell(margins):
    return CellResult(enemy_heads=5, fights=[_f(m) for m in margins], mean_margin=sum(margins) / len(margins), won=True)


def test_one_seed_gives_low_equal_high():
    low, high = pair_spread(_cell([0.3, 0.5]))
    assert low == high == pytest.approx(0.4)


def test_three_seeds_hand_computed():
    # swap False seeds 0..2: 0.2 0.4 0.6; swap True seeds 0..2: 0.0 0.2 -0.2 -> pairs 0.1 0.3 0.2
    low, high = pair_spread(_cell([0.2, 0.4, 0.6, 0.0, 0.2, -0.2]))
    assert (low, high) == (pytest.approx(0.1), pytest.approx(0.3))


def test_pairs_are_fight_i_with_fight_i_plus_half():
    # a wrong pairing (neighbours) would give 0.0 to 1.0; the right one pairs 1.0 with -1.0 and 0.0 with 0.0
    low, high = pair_spread(_cell([1.0, 0.0, -1.0, 0.0]))
    assert (low, high) == (pytest.approx(0.0), pytest.approx(0.0))


def test_positive_control_identical_fights():
    low, high = pair_spread(_cell([0.25] * 8))
    assert low == pytest.approx(0.25) and high == pytest.approx(0.25)


def test_odd_fight_count_raises():
    with pytest.raises(ValueError):
        pair_spread(_cell([0.1, 0.2, 0.3]))
