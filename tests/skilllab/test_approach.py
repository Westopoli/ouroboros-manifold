# spec: Architect ruling A198 - Setup.approach and the hold-to-contact opening (scripts/skilllab/approach.py)
"""approach_setup: pure function, no engine. Off or nothing to do returns the same object; otherwise movers become
`group_move` groups to a stop line and an ("arrive_all", 60.0) attack_move Step per mover group follows."""
import copy
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.approach import approach_setup  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

RANGES = {"Vanguard": 300.0, "Raider": 200.0}
APPROACH = 0.95


def G(side, count=8, unit="Vanguard", formation="line", x=None, y=0.0, order="attack_move", goal=None, params=None):
    x = (-1000.0 if side == 0 else 1000.0) if x is None else x
    if params is None:
        params = {"spacing": 30} if formation == "line" else {"radius": 80.0}
    return Group(side=side, unit=unit, count=count, formation=formation, x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params=params)


def S(groups, approach=APPROACH, **kw):
    return Setup(groups=tuple(groups), unit_types={}, approach=approach, **kw)


def pts(g):
    return place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def side_points(setup, side):
    return [p for g in setup.groups if g.side == side for p in pts(g)]


def direction(setup):
    c0, c1 = centroid(side_points(setup, 0)), centroid(side_points(setup, 1))
    n = math.hypot(c1[0] - c0[0], c1[1] - c0[1])
    return ((c1[0] - c0[0]) / n, (c1[1] - c0[1]) / n)


def gap(setup, d):
    f0 = max(p[0] * d[0] + p[1] * d[1] for p in side_points(setup, 0))
    f1 = min(p[0] * d[0] + p[1] * d[1] for p in side_points(setup, 1))
    return f1 - f0


def moved_gap(original, result, d):
    """Front gap after movers travel to their goals as rigid shifts of their placed points."""
    shifted = []
    for g, r in zip(original.groups, result.groups):
        p = pts(g)
        if r.order == "group_move":
            c = centroid(p)
            p = [(x + r.goal[0] - c[0], y + r.goal[1] - c[1]) for x, y in p]
        shifted.append((g.side, p))
    f0 = max(x * d[0] + y * d[1] for s, p in shifted if s == 0 for x, y in p)
    f1 = min(x * d[0] + y * d[1] for s, p in shifted if s == 1 for x, y in p)
    return f1 - f0


def shift_of(g, r):
    c = centroid(pts(g))
    return r.goal[0] - c[0], r.goal[1] - c[1]


# ---- no-ops -------------------------------------------------------------------------------------------------

def test_off_returns_the_same_object():
    s = S((G(0), G(1)), approach=0.0)
    assert approach_setup(s, RANGES) is s


def test_default_is_off():
    assert Setup(groups=(G(0), G(1)), unit_types={}).approach == 0.0


def test_no_movers_returns_the_same_object():
    s = S((G(0, order="idle"), G(1, order="guard")))
    assert approach_setup(s, RANGES) is s
    s = S((G(0, order="move", goal=(0.0, 0.0)), G(1, order="idle")))
    assert approach_setup(s, RANGES) is s


def test_already_in_range_returns_the_same_object():
    s = S((G(0, x=-100.0), G(1, x=100.0)))        # fronts about 200 apart, S = 285
    d = direction(s)
    assert gap(s, d) <= 0.95 * 300
    assert approach_setup(s, RANGES) is s


def test_overlapping_fronts_count_as_in_range():
    s = S((G(0, x=100.0), G(1, x=-100.0)))        # side 0 stands past side 1: negative gap
    assert approach_setup(s, RANGES) is s


def test_identical_centroids_return_the_same_object():
    s = S((G(0, x=0.0), G(1, x=0.0)))
    assert approach_setup(s, RANGES) is s


# ---- two mover sides ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("formation,n0,n1", [("line", 16, 12), ("blob", 16, 12), ("line", 32, 32), ("blob", 5, 7)])
def test_two_sided_fronts_end_at_the_stop_distance(formation, n0, n1):
    s = S((G(0, n0, formation=formation), G(1, n1, formation=formation)))
    d = direction(s)
    stop = APPROACH * 300.0
    assert gap(s, d) > stop                                       # positive control: the opening is out of range
    r = approach_setup(s, RANGES)
    assert r is not s
    assert [g.order for g in r.groups] == ["group_move", "group_move"]
    assert moved_gap(s, r, d) == pytest.approx(stop, abs=1e-6)
    assert gap(s, d) > stop and moved_gap(s, r, d) <= stop + 1e-6


def test_each_side_travels_half_along_its_direction():
    s = S((G(0, 16, formation="line"), G(1, 12, formation="line")))
    d = direction(s)
    travel = gap(s, d) - APPROACH * 300.0
    s0, s1 = shift_of(s.groups[0], approach_setup(s, RANGES).groups[0]), shift_of(s.groups[1], approach_setup(s, RANGES).groups[1])
    assert s0 == pytest.approx((d[0] * travel / 2, d[1] * travel / 2), abs=1e-6)
    assert s1 == pytest.approx((-d[0] * travel / 2, -d[1] * travel / 2), abs=1e-6)


def test_diagonal_direction_is_followed():
    s = S((G(0, 8, formation="blob", x=-900.0, y=-600.0), G(1, 8, formation="blob", x=900.0, y=500.0)))
    d = direction(s)
    assert abs(d[1]) > 0.1
    r = approach_setup(s, RANGES)
    assert moved_gap(s, r, d) == pytest.approx(APPROACH * 300.0, abs=1e-6)
    sh = shift_of(s.groups[0], r.groups[0])
    assert sh[1] * d[0] - sh[0] * d[1] == pytest.approx(0.0, abs=1e-6)     # shift parallel to d


# ---- one mover side -----------------------------------------------------------------------------------------

def test_one_mover_side_travels_the_whole_way_and_the_guard_is_untouched():
    s = S((G(0, 16), G(1, 12, order="guard")))
    d = direction(s)
    travel = gap(s, d) - APPROACH * 300.0
    r = approach_setup(s, RANGES)
    assert r.groups[1] == s.groups[1]
    assert r.groups[0].order == "group_move"
    assert shift_of(s.groups[0], r.groups[0]) == pytest.approx((d[0] * travel, d[1] * travel), abs=1e-6)
    assert moved_gap(s, r, d) == pytest.approx(APPROACH * 300.0, abs=1e-6)
    assert len(r.timeline) == 1 and r.timeline[0].group == 0


def test_one_mover_side_1_travels_against_d():
    s = S((G(0, 16, order="idle"), G(1, 12)))
    d = direction(s)
    travel = gap(s, d) - APPROACH * 300.0
    r = approach_setup(s, RANGES)
    assert r.groups[0] == s.groups[0]
    assert shift_of(s.groups[1], r.groups[1]) == pytest.approx((-d[0] * travel, -d[1] * travel), abs=1e-6)


def test_guard_and_move_groups_do_not_move_but_still_count_for_the_fronts():
    s = S((G(0, 8), G(0, 8, y=400.0, order="idle"), G(1, 12)))
    d = direction(s)
    r = approach_setup(s, RANGES)
    assert r.groups[1] == s.groups[1]
    assert [g.order for g in r.groups] == ["group_move", "idle", "group_move"]
    assert [st.group for st in r.timeline] == [0, 2]


# ---- steps --------------------------------------------------------------------------------------------------

def test_one_arrive_step_per_mover_group_keeps_the_original_goal():
    goal = (123.0, 45.0)
    s = S((G(0, 8), G(0, 8, y=300.0, goal=goal), G(1, 12)))
    r = approach_setup(s, RANGES)
    assert r.timeline == (Step(group=0, when=("arrive_all", 60.0), order="attack_move", goal=None),
                          Step(group=1, when=("arrive_all", 60.0), order="attack_move", goal=goal),
                          Step(group=2, when=("arrive_all", 60.0), order="attack_move", goal=None))


def test_steps_are_appended_in_group_index_order_and_skip_non_movers():
    s = S((G(0, 8, order="idle"), G(1, 12), G(1, 4, y=300.0)))
    r = approach_setup(s, RANGES)
    assert [(st.group, st.order) for st in r.timeline] == [(1, "attack_move"), (2, "attack_move")]
    assert all(st.when == ("arrive_all", 60.0) for st in r.timeline)


def test_existing_timeline_raises():
    s = S((G(0), G(1)), timeline=(Step(0, ("tick", 5), "idle"),))
    with pytest.raises(ValueError, match="approach needs an empty timeline"):
        approach_setup(s, RANGES)


# ---- ranges -------------------------------------------------------------------------------------------------

def test_the_smaller_range_over_both_sides_sets_the_stop():
    s = S((G(0, 8, unit="Raider"), G(1, 8, unit="Vanguard")))
    d = direction(s)
    r = approach_setup(s, RANGES)
    assert moved_gap(s, r, d) == pytest.approx(0.95 * 200.0, abs=1e-6)


def test_range_of_a_mixed_unit_group_counts_even_when_it_is_the_enemy_side():
    s = S((G(0, 8, unit="Vanguard"), G(1, 8, unit="Vanguard"), G(1, 2, unit="Raider", y=500.0)))
    d = direction(s)
    r = approach_setup(s, RANGES)
    assert moved_gap(s, r, d) == pytest.approx(0.95 * 200.0, abs=1e-6)


def test_stop_factor_scales_the_stop():
    s = S((G(0, 8), G(1, 8)), approach=0.5)
    d = direction(s)
    assert moved_gap(s, approach_setup(s, RANGES), d) == pytest.approx(150.0, abs=1e-6)


# ---- points groups (mixed side) -----------------------------------------------------------------------------

def test_points_groups_of_a_side_shift_by_the_same_vector():
    left = [(-1000.0 + 5 * i, 30.0 * i) for i in range(4)]
    mixed = [(-1000.0 + 7 * i, -30.0 * i - 30) for i in range(3)]
    a = G(0, 4, formation="points", x=0.0, y=0.0, params={"points": left})
    b = G(0, 3, unit="Raider", formation="points", x=0.0, y=0.0, params={"points": mixed})
    s = S((a, b, G(1, 8)))
    d = direction(s)
    r = approach_setup(s, RANGES)
    assert r.groups[0].order == r.groups[1].order == "group_move"
    assert shift_of(a, r.groups[0]) == pytest.approx(shift_of(b, r.groups[1]), abs=1e-6)
    assert moved_gap(s, r, d) == pytest.approx(APPROACH * 200.0, abs=1e-6)


# ---- purity -------------------------------------------------------------------------------------------------

def test_input_is_not_mutated():
    s = S((G(0, 16), G(1, 12, formation="blob")))
    before = copy.deepcopy(s)
    approach_setup(s, RANGES)
    assert s == before


def test_deterministic():
    s = S((G(0, 16), G(1, 12, formation="blob")))
    assert approach_setup(s, RANGES) == approach_setup(s, RANGES)


def test_everything_else_is_unchanged_and_approach_stays():
    s = S((G(0), G(1)), max_ticks=77, settings={"OM_TP_PURSUE_BY_STEERING": 1}, weighted=True)
    r = approach_setup(s, RANGES)
    assert r.approach == APPROACH
    assert dataclasses.replace(r, groups=s.groups, timeline=()) == s
    assert [(g.unit, g.count, g.formation, g.x, g.y, g.params) for g in r.groups] == \
        [(g.unit, g.count, g.formation, g.x, g.y, g.params) for g in s.groups]
