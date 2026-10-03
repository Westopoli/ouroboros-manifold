# spec: Architect ruling A198 - fight() runs Setup.approach through approach_setup before spawning
"""fight with Setup.approach on a WalkingFakeEngine: group_move first, attack_move on arrival (both sides together); off is byte-identical."""
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_approach import WalkingFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402


def G(side, count=4, order="attack_move", x=None):
    x = (-1000.0 if side == 0 else 1000.0) if x is None else x
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=None, params={"spacing": 30})


def S(approach=0.95, groups=None, **kw):
    return Setup(groups=groups or (G(0), G(1)), unit_types={}, max_ticks=400, stalemate_ticks=1000,
                 sample_every=5, approach=approach, **kw)


def run(setup, seed=0, swap=False):
    fake = WalkingFakeEngine()
    return fight(setup, seed, swap, engine=fake), fake


def idx(fake, name, nth=0):
    return [i for i, c in enumerate(fake.calls) if c[0] == name][nth]


def test_every_mover_group_is_ordered_to_group_move_before_any_attack_move():
    _, fake = run(S())
    moves = fake.calls_named("order_group_move")
    assert len(moves) == 2
    assert fake.calls_named("order_move") == []
    assert idx(fake, "order_group_move", 1) < idx(fake, "order_attack_move", 0)
    assert [o[1] for o in fake.order_log[:2]] == ["group_move", "group_move"]
    assert [o[0] for o in fake.order_log[:2]] == [0, 0]


def test_attack_move_is_issued_only_after_the_group_is_near_its_move_goal():
    result, fake = run(S())
    assert len(fake.attack_log) == 2
    for (tick, ids, centre), (_ids, goal) in zip(sorted(fake.attack_log, key=lambda a: a[1]),
                                                 sorted(fake.move_goals, key=lambda m: m[0])):
        assert ids == _ids
        assert tick > 0
        assert math.hypot(centre[0] - goal[0], centre[1] - goal[1]) <= 60.0


def test_both_sides_switch_to_attack_move_on_the_same_tick():
    """arrive_all: the nearer side waits for the farther one (here the sides are unequal in width and distance)."""
    result, fake = run(S(groups=(G(0, count=4, x=-1000.0), G(1, count=4, x=600.0))))
    assert len({t for t, _, _ in fake.attack_log}) == 1 and len(fake.attack_log) == 2
    assert len({t for _, t in result.steps_fired}) == 1


def test_the_walkers_really_walk_so_the_arrival_is_not_instant():
    """Positive control for the check above: at tick 0 the groups are far from their goals."""
    _, fake = run(S())
    for ids, goal in fake.move_goals:
        c = (sum(fake.units[u]["x"] for u in ids) / len(ids), 0.0)
        assert abs(c[0] - goal[0]) <= 60.0                       # now (end of fight) they are there
    first = min(a[0] for a in fake.attack_log)
    assert first >= 100                                         # about 950 wu of travel at 5 wu a tick, shared by two sides


def test_steps_fired_lists_the_approach_steps_with_their_ticks():
    result, fake = run(S())
    assert [i for i, _ in result.steps_fired] == [0, 1]
    assert [t for _, t in result.steps_fired] == sorted(a[0] for a in fake.attack_log)
    assert all(t > 0 for _, t in result.steps_fired)


def test_off_is_identical_to_a_setup_without_the_field():
    plain = Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=400, stalemate_ticks=1000, sample_every=5)
    off = dataclasses.replace(plain, approach=0.0)
    (r1, f1), (r2, f2) = run(plain), run(off)
    assert r1 == r2
    assert f1.calls == f2.calls
    assert f1.calls_named("order_group_move") == []
    assert r1.steps_fired == ()
    assert [o[:2] for o in f1.order_log] == [(0, "attack_move"), (0, "attack_move")]


def test_off_digest_matches_for_every_swap_and_seed():
    plain = Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=60, stalemate_ticks=1000, sample_every=5)
    for seed in range(3):
        for swap in (False, True):
            a, b = run(plain, seed, swap), run(dataclasses.replace(plain, approach=0.0), seed, swap)
            assert a[0] == b[0] and a[1].calls == b[1].calls


def test_spawns_are_the_original_positions_and_orders_follow_the_spawns():
    _, fake = run(S())
    _, off = run(S(approach=0.0))
    assert fake.spawn_log() == off.spawn_log()
    assert idx(fake, "_spawned", 7) < idx(fake, "order_group_move", 0)


def test_range_comes_from_the_registered_types():
    """A longer attack range stops the walkers further out (S = 0.95 x range)."""
    far = WalkingFakeEngine()
    far._types[2] = dict(far._types[2], attack_range=300.0)
    fight(S(), 0, False, engine=far)
    _, short = run(S())
    gap_far = abs(far.move_goals[1][1][0] - far.move_goals[0][1][0])
    gap_short = abs(short.move_goals[1][1][0] - short.move_goals[0][1][0])
    assert gap_far > gap_short


def test_idle_side_stays_and_the_mover_walks_all_of_it():
    result, fake = run(S(groups=(G(0), G(1, order="idle"))))
    assert len(fake.calls_named("order_group_move")) == 1
    assert len(fake.attack_log) == 1
    assert [i for i, _ in result.steps_fired] == [0]


def test_bad_headcounts_still_raise():
    bad = S(groups=(G(0, count=0), G(1)))
    with pytest.raises(ValueError):
        run(bad)
    with pytest.raises(ValueError):
        run(S(groups=(G(0), G(1, count=0))))


def test_an_existing_timeline_with_approach_on_raises():
    from scripts.skilllab.contract import Step
    with pytest.raises(ValueError, match="approach needs an empty timeline"):
        run(S(timeline=(Step(0, ("tick", 5), "idle"),)))
