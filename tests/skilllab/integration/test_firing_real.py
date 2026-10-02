# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-24
"""AC 24 firing count against the real engine, hand-built geometry.

Side 0: three units in a row, A, B, C along +x. Side 1: one enemy E behind A on the -x side.
Distances from E, as fractions of the Vanguard attack range R: A 0.3, B 0.7, C 1.2.
Replicate shifts are at most 10 world units per axis, far inside every margin (R is read from
the engine, so no position is a magic number).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

UNIT = "Vanguard"
BASE_X, BASE_Y = 400.0, 400.0   # keeps every point positive


class _BlockerEngine:
    """Real Engine plus blockers added to each new world; every other call passes through."""

    def __init__(self, real, blockers):
        self._real = real
        self._blockers = blockers

    def __getattr__(self, name):
        return getattr(self._real, name)

    def new_world(self, *args, **kwargs):
        w = self._real.new_world(*args, **kwargs)
        for x, y, r in self._blockers:
            self._real.add_blocker(w, x, y, r)
        return w


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


@pytest.fixture(scope="module")
def reach(real_engine):
    w = real_engine.new_world(0)
    try:
        stats = real_engine.type_stats(w, real_engine.type_id(UNIT))
    finally:
        real_engine.free_world(w)
    return float(stats["attack_range"])


def _points(reach):
    a = (BASE_X, BASE_Y)
    b = (BASE_X + 0.4 * reach, BASE_Y)
    c = (BASE_X + 0.9 * reach, BASE_Y)
    e = (BASE_X - 0.3 * reach, BASE_Y)
    return a, b, c, e


def _setup(reach):
    a, b, c, e = _points(reach)
    side0 = Group(side=0, unit=UNIT, count=3, formation="points", x=BASE_X, y=BASE_Y,
                  facing_deg=0.0, layer=0, order="idle", params={"points": [a, b, c]})
    side1 = Group(side=1, unit=UNIT, count=1, formation="points", x=e[0], y=e[1],
                  facing_deg=180.0, layer=0, order="idle", params={"points": [e]})
    return Setup(groups=(side0, side1), unit_types={}, abilities=False, max_ticks=10, sample_every=5)


def _tick0(result):
    tick, able0, able1 = result.firing[0]
    assert tick == 0
    return able0, able1


def test_two_of_three_within_reach_reads_2_and_1(real_engine, reach):
    """AC 24 base case, also the no-blocker count the blocker cases compare against."""
    result = fight.fight(_setup(reach), 0, False, engine=real_engine)
    assert _tick0(result) == (2, 1)
    assert result.first_contact_tick == 0


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_count_holds_across_replicate_shifts(real_engine, reach, seed):
    """AC 24 / AC 6: the replicate shift (<= 10 wu per axis) does not change the hand-built count."""
    assert _tick0(fight.fight(_setup(reach), seed, True, engine=real_engine)) == (2, 1)


def test_blocker_between_one_pair_removes_one_shooter_from_the_losing_side(real_engine, reach):
    """AC 24 blocker case: disc between A and B blocks the E-B line only. Side 0 loses B (2 -> 1);
    side 1 still fires through A, so its count is unchanged."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + b[0]) / 2.0, BASE_Y, 0.08 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (1, 1)


def test_blocker_on_every_line_to_the_enemy_removes_the_enemys_shot_too(real_engine, reach):
    """AC 24 blocker case: disc between E and A lies on both E-A and E-B. Side 0 drops 2 -> 0,
    side 1 drops 1 -> 0 (it loses its only pair)."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + e[0]) / 2.0, BASE_Y, 0.07 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (0, 0)
