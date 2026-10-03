# spec: docs/northstar/plans/skilllab-plan.md::Phase S::item 8b (the weighted count reads the engine's own target decision)
"""count_able_weighted counts a unit iff engine.unit_target names a living enemy in range, in reach and shootable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_weighted_target import WeightedTargetFakeEngine  # noqa: E402
from scripts.skilllab.firing import count_able_weighted  # noqa: E402


def world(**kw):
    """s (side 0, weight 2) at the origin, e (side 1, weight 3) 50 away on layer 0; range 100 each."""
    fake = WeightedTargetFakeEngine(**kw)
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, 50.0, 0.0, 0)
    return fake, w, s, e, {s: 100.0, e: 100.0}, {s: 2.0, e: 3.0}


def able(fake, w, s, e, ranges, weights, **kw):
    return count_able_weighted(fake, w, [s], [e], ranges, weights, **kw)


def test_positive_control_target_in_range_and_shootable_counts_its_weight():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    fake.set_target(e, s)
    assert able(fake, w, s, e, ranges, weights) == (2.0, 3.0)


def test_no_target_counts_nothing_even_with_an_enemy_in_range_and_visible():
    fake, w, s, e, ranges, weights = world(can_see_fn=lambda f, o, t: True)
    fake.set_target(s, 0)
    assert able(fake, w, s, e, ranges, weights) == (0.0, 3.0)


def test_dead_target_counts_nothing():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    fake.set_hp(e, 0)
    assert able(fake, w, s, e, ranges, weights)[0] == 0.0


def test_target_not_in_the_living_set_counts_nothing_even_if_the_fake_says_alive():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    assert able(fake, w, s, e, ranges, weights, alive={s}) [0] == 0.0
    assert able(fake, w, s, e, ranges, weights, alive={s, e})[0] == 2.0


def test_target_on_the_shooters_own_side_counts_nothing():
    fake, w, s, e, ranges, weights = world()
    vg = fake.type_id("Vanguard")
    friend = fake.spawn(w, vg, 0, 10.0, 0.0, 0)
    ranges[friend], weights[friend] = 100.0, 1.0
    fake.set_target(s, friend)
    assert count_able_weighted(fake, w, [s, friend], [e], ranges, weights)[0] == weights[friend]


def test_target_out_of_range_counts_nothing():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    ranges[s] = 49.9999
    assert able(fake, w, s, e, ranges, weights)[0] == 0.0
    ranges[s] = 50.0
    assert able(fake, w, s, e, ranges, weights)[0] == 2.0


def test_only_the_engines_target_counts_not_any_other_enemy_in_range():
    fake, w, s, e, ranges, weights = world()
    vg = fake.type_id("Vanguard")
    far = fake.spawn(w, vg, 1, 900.0, 0.0, 0)
    ranges[far], weights[far] = 100.0, 1.0
    fake.set_target(s, far)                       # the engine picked the far one; the near one in range does not count
    assert count_able_weighted(fake, w, [s], [e, far], ranges, weights)[0] == 0.0


def test_reach_rule_still_applies_to_the_target_layer():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    fake.units[e]["layer"] = 1
    assert able(fake, w, s, e, ranges, weights)[0] == 0.0
    assert able(fake, w, s, e, ranges, weights, reach={s: (1, 0), e: (0, 0)})[0] == 2.0
    fake.units[e]["layer"] = 0
    fake.units[s]["layer"] = 2
    assert able(fake, w, s, e, ranges, weights, reach={s: (0, 1)})[0] == 0.0
    assert able(fake, w, s, e, ranges, weights, reach={s: (0, 2)})[0] == 2.0


def test_blocked_can_shoot_counts_nothing():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    fake.block(s, e)
    assert able(fake, w, s, e, ranges, weights)[0] == 0.0


def test_no_can_see_calls_are_made():
    fake, w, s, e, ranges, weights = world(can_see_fn=lambda f, o, t: True)
    fake.set_target(s, e)
    fake.set_target(e, s)
    able(fake, w, s, e, ranges, weights)
    assert fake.calls_named("can_see") == []
    assert fake.calls_named("unit_target")


def test_weights_sum_per_side():
    fake, w, s, e, ranges, weights = world()
    vg = fake.type_id("Vanguard")
    s2 = fake.spawn(w, vg, 0, 10.0, 0.0, 0)
    s3 = fake.spawn(w, vg, 0, 900.0, 0.0, 0)          # its default target (e) is far out of its range
    e2 = fake.spawn(w, vg, 1, 60.0, 0.0, 0)
    ranges.update({s2: 100.0, s3: 100.0, e2: 100.0})
    weights.update({s2: 0.5, s3: 7.0, e2: 1.25})
    assert count_able_weighted(fake, w, [s, s2, s3], [e, e2], ranges, weights) == (2.5, 4.25)


def test_empty_sides_give_zero_zero():
    fake, w, s, e, ranges, weights = world()
    out = count_able_weighted(fake, w, [], [], ranges, weights)
    assert out == (0.0, 0.0) and all(isinstance(v, float) for v in out)
    assert count_able_weighted(fake, w, [s], [], ranges, weights) == (0.0, 0.0)


def test_swapping_the_lists_swaps_the_tuple():
    fake, w, s, e, ranges, weights = world()
    fake.set_target(s, e)
    fake.set_target(e, 0)
    assert count_able_weighted(fake, w, [s], [e], ranges, weights) == (2.0, 0.0)
    assert count_able_weighted(fake, w, [e], [s], ranges, weights) == (0.0, 2.0)
