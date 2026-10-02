# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-24
"""count_able at unit level, on a FakeEngine (no compiler, no library)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest  # noqa: E402
from fakes import FakeEngine  # noqa: E402
from scripts.skilllab.firing import count_able  # noqa: E402


def row_world(enemy_x=140.0, enemy_layer=0, rng=100.0):
    """Three side-0 units in a row at x = 0, 50, 100 and one enemy at (enemy_x, 0).
    Default enemy_x = 140: distances 140, 90, 40 -> exactly two of side 0 within reach 100."""
    fake = FakeEngine()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = [fake.spawn(w, vg, 0, x, 0.0, 0) for x in (0.0, 50.0, 100.0)]
    e = fake.spawn(w, vg, 1, enemy_x, 0.0, enemy_layer)
    ranges = {u: rng for u in a + [e]}
    return fake, w, a, e, ranges


def test_ac24_three_in_a_row_one_enemy_two_in_reach_reads_2_and_1():
    """AC-24: hand-built case reads able0 = 2, able1 = 1."""
    fake, w, a, e, ranges = row_world()
    assert count_able(fake, w, a, [e], ranges) == (2, 1)


def test_ac24_positive_and_negative_control_on_distance():
    """AC-24 / AC-10: enemy out of every reach reads 0; one unit in reach reads 1; both are real counts."""
    fake, w, a, e, ranges = row_world(enemy_x=400.0)
    assert count_able(fake, w, a, [e], ranges) == (0, 0)
    fake, w, a, e, ranges = row_world(enemy_x=170.0)   # distances 170, 120, 70
    assert count_able(fake, w, a, [e], ranges) == (1, 1)


def test_ac24_blocker_on_one_pair_reads_one_fewer_for_that_side():
    """AC-24: a pair that cannot shoot (blocker) costs the shooter its count; the direction is shooter -> enemy."""
    fake, w, a, e, ranges = row_world()
    fake.block(a[1], e, both=True)             # a physical blocker is symmetric
    assert count_able(fake, w, a, [e], ranges) == (1, 1)
    fake, w, a, e, ranges = row_world()
    fake.block(e, a[1]); fake.block(e, a[2])   # enemy cannot shoot either unit in its reach
    assert count_able(fake, w, a, [e], ranges) == (2, 0)
    fake, w, a, e, ranges = row_world()
    fake.block(a[1], e); fake.block(a[2], e)   # side 0 cannot shoot; the enemy still can
    assert count_able(fake, w, a, [e], ranges) == (0, 1)


def test_ac24_blocked_pair_does_not_hide_a_second_open_target():
    """AC-10: able means SOME living enemy is open; one blocked enemy of two does not remove the unit, a unit counts once."""
    fake, w, a, e1, ranges = row_world()
    e2 = fake.spawn(w, fake.type_id("Vanguard"), 1, 140.0, 10.0, 0)
    ranges[e2] = 100.0
    fake.block(a[2], e1, both=True)
    assert count_able(fake, w, a, [e1, e2], ranges) == (2, 2)
    fake.block(a[2], e2, both=True)            # now a3 has no open target
    assert count_able(fake, w, a, [e1, e2], ranges) == (1, 2)


def test_ac24_different_layers_do_not_count():
    """AC-24 / AC-10: a unit may fire only at its own layer; a layer-1 enemy beside layer-0 units reads 0 both ways."""
    fake, w, a, e, ranges = row_world(enemy_layer=1)
    assert count_able(fake, w, a, [e], ranges) == (0, 0)
    fake, w, a, e, ranges = row_world(enemy_layer=1)
    fake.units[a[2]]["layer"] = 1              # positive control: one unit joins the enemy's layer
    assert count_able(fake, w, a, [e], ranges) == (1, 1)


def test_ac24_dead_units_do_not_count():
    """AC-24 / AC-10: a dead shooter and a dead target both drop out of the count."""
    fake, w, a, e, ranges = row_world()
    fake.set_hp(a[2], 0)
    assert count_able(fake, w, a, [e], ranges) == (1, 1)
    fake.set_hp(a[1], 0)
    assert count_able(fake, w, a, [e], ranges) == (0, 0)
    fake, w, a, e, ranges = row_world()
    fake.set_hp(e, 0)
    assert count_able(fake, w, a, [e], ranges) == (0, 0)


def test_ac24_each_unit_uses_its_own_range():
    """AC-10: reach is per unit; a long-range unit counts where a short one beside it does not."""
    fake, w, a, e, ranges = row_world()
    ranges.update({a[0]: 200.0, a[1]: 50.0, a[2]: 100.0, e: 100.0})   # distances 140, 90, 40
    assert count_able(fake, w, a, [e], ranges) == (2, 1)
    ranges[a[0]] = 100.0
    assert count_able(fake, w, a, [e], ranges) == (1, 1)


def test_ac24_empty_side_reads_zero_and_result_is_an_int_pair():
    """AC-10 (existence): an empty list on either side is zero for both, never an error."""
    fake, w, a, e, ranges = row_world()
    assert count_able(fake, w, [], [e], ranges) == (0, 0)
    assert count_able(fake, w, a, [], ranges) == (0, 0)
    out = count_able(fake, w, a, [e], ranges)
    assert isinstance(out, tuple) and all(type(v) is int for v in out)


def test_ac24_count_able_asks_the_engine_with_the_world_and_shooter_first():
    """AC-10 interaction: can_shoot is asked as can_shoot(w, shooter, enemy) for in-reach pairs, side 0 and side 1 shooters."""
    fake, w, a, e, ranges = row_world()
    count_able(fake, w, a, [e], ranges)
    asked = [c[1:] for c in fake.calls_named("can_shoot")]
    assert all(c[0] == w for c in asked)
    pairs = {(c[1], c[2]) for c in asked}
    assert {(a[1], e), (a[2], e)} <= pairs and any(p[0] == e and p[1] in a for p in pairs)


@pytest.mark.parametrize("enemy_x,expected", [(100.0, (1, 1)), (100.0001, (0, 0)), (99.9999, (1, 1))])
def test_ac10_range_test_is_distance_less_or_equal_attack_range(enemy_x, expected):
    """AC-10 (Readings): a target at exactly attack_range counts (<=); a hair beyond does not; a hair inside does."""
    fake = FakeEngine()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, enemy_x, 0.0, 0)
    assert count_able(fake, w, [a], [e], {a: 100.0, e: 100.0}) == expected


@pytest.mark.parametrize("missing", [0, 1, 2, "enemy"])
def test_ac10_a_living_unit_missing_from_ranges_raises_keyerror(missing):
    """AC-10 (Readings): a unit id absent from `ranges` raises KeyError, whichever side it is on."""
    fake, w, a, e, ranges = row_world()
    del ranges[e if missing == "enemy" else a[missing]]
    with pytest.raises(KeyError):
        count_able(fake, w, a, [e], ranges)
