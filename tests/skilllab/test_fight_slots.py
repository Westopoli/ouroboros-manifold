# spec: Architect ruling A187 item 1 (slots kept for wide shapes, R-095-02/R-095-03) - scripts/skilllab/fight.py _issue_orders ; LAB-REV2-L2: Setup.orders_per_unit=False keeps the chunked group order under test
"""A wide group is split into chunks that each stay within SLOT_RADIUS of their own centroid. Fake engine; no library."""
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from tests.skilllab.fakes import FakeEngine  # noqa: E402

GOAL = (500.0, 40.0)
ORDERS = ("order_attack_move", "order_move")


def _group(count, side=0, formation="line", order="attack_move", goal=GOAL):
    params = {"spacing": 30} if formation == "line" else {"radius": 100.0}
    return Group(side=side, unit="Vanguard", count=count, formation=formation, x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params=params)


def _run(group):
    """Spawn the group (plus an idle enemy so each side has a unit) and issue orders; return (engine, orders, ids, goals)."""
    other = Group(side=1 - group.side, unit="Vanguard", count=1, formation="blob", x=0.0, y=0.0, facing_deg=0.0,
                  layer=0, order="idle", params={"radius": 10.0})
    setup = Setup(groups=(group, other), unit_types={}, orders_per_unit=False)   # LAB-REV2-L2: the chunked group order is the orders_per_unit=False path
    eng = FakeEngine()
    w = eng.new_world(0)
    types = fight._register_types(eng, w, setup)
    ids, ranges = {}, {}
    rng = random.Random(0)
    for side in (0, 1):
        fight._spawn_side(eng, w, setup, side, types, rng, ids, ranges)
    eng.calls.clear()
    goals = fight._issue_orders(eng, w, setup, ids)
    orders = [c for c in eng.calls if c[0] in ORDERS]
    return eng, orders, ids[0], goals


def _centroid(eng, unit_ids):
    pts = [(eng.units[u]["x"], eng.units[u]["y"]) for u in unit_ids]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _max_dist(eng, unit_ids):
    cx, cy = _centroid(eng, unit_ids)
    return max(math.hypot(eng.units[u]["x"] - cx, eng.units[u]["y"] - cy) for u in unit_ids)


def _check_cover(orders, ids):
    flat = [u for o in orders for u in o[2]]
    assert sorted(flat) == sorted(ids) and len(set(flat)) == len(flat)


def test_slot_radius_is_public_and_440():
    assert fight.SLOT_RADIUS == 440


def test_line_of_16_is_one_call_with_the_original_goal():
    eng, orders, ids, goals = _run(_group(16))
    assert len(orders) == 1
    assert orders[0][0] == "order_attack_move" and orders[0][2] == ids
    assert (orders[0][3], orders[0][4]) == GOAL
    assert goals[0] == GOAL


def test_line_of_32_splits_into_two_equal_chunks():
    eng, orders, ids, goals = _run(_group(32))
    assert len(orders) == 2
    assert sorted(len(o[2]) for o in orders) == [16, 16]
    _check_cover(orders, ids)
    gx, gy = _centroid(eng, ids)
    for o in orders:
        assert _max_dist(eng, o[2]) <= fight.SLOT_RADIUS
        cx, cy = _centroid(eng, o[2])
        assert o[3] == pytest.approx(GOAL[0] + (cx - gx)) and o[4] == pytest.approx(GOAL[1] + (cy - gy))
    assert orders[0][3:] != orders[1][3:]
    assert goals[0] == GOAL


def test_chunks_are_cut_along_the_axis_of_greater_spread():
    eng, orders, ids, _ = _run(_group(32))
    ys = [sorted(eng.units[u]["y"] for u in o[2]) for o in orders]
    ys.sort()
    assert ys[0][-1] <= ys[1][0]      # the line runs along y, so chunks do not interleave in y


def test_line_of_64_needs_three_or_more_calls_and_covers_every_unit_once():
    eng, orders, ids, _ = _run(_group(64))
    assert len(orders) >= 3
    _check_cover(orders, ids)
    sizes = [len(o[2]) for o in orders]
    assert max(sizes) - min(sizes) <= 1
    assert all(_max_dist(eng, o[2]) <= fight.SLOT_RADIUS for o in orders)


def test_smallest_k_is_used_for_64():
    eng, orders, ids, _ = _run(_group(64))
    assert len(orders) == 3


def test_blob_of_32_is_one_call():
    eng, orders, ids, _ = _run(_group(32, formation="blob"))
    assert len(orders) == 1 and orders[0][2] == ids and (orders[0][3], orders[0][4]) == GOAL


def test_move_order_is_split_like_attack_move():
    eng, orders, ids, _ = _run(_group(32, order="move"))
    assert [o[0] for o in orders] == ["order_move", "order_move"]
    assert sorted(len(o[2]) for o in orders) == [16, 16]
    _check_cover(orders, ids)


def test_idle_group_issues_nothing():
    eng, orders, ids, goals = _run(_group(32, order="idle"))
    assert orders == [] and 0 not in goals


def test_single_unit_is_one_call():
    eng, orders, ids, _ = _run(_group(1))
    assert len(orders) == 1 and orders[0][2] == ids and (orders[0][3], orders[0][4]) == GOAL


def test_side_one_splits_the_same_way():
    eng, orders, ids, goals = _run(_group(32, side=1, goal=(-500.0, 40.0)))
    other = [u for u in eng.units_of(1)]
    assert len(orders) == 2 and sorted(len(o[2]) for o in orders) == [16, 16]
    _check_cover(orders, other)
    assert all(_max_dist(eng, o[2]) <= fight.SLOT_RADIUS for o in orders)
    gx, gy = _centroid(eng, other)
    for o in orders:
        cx, cy = _centroid(eng, o[2])
        assert o[3] == pytest.approx(-500.0 + (cx - gx)) and o[4] == pytest.approx(40.0 + (cy - gy))
    assert goals[0] == (-500.0, 40.0)


def test_positive_control_one_call_would_exceed_the_radius():
    """The old behaviour (one call for the 32 line) puts a unit beyond 440 of the centroid, so the split is needed."""
    eng, orders, ids, _ = _run(_group(32))
    assert _max_dist(eng, ids) > fight.SLOT_RADIUS
    eng16, _, ids16, _ = _run(_group(16))
    assert _max_dist(eng16, ids16) <= fight.SLOT_RADIUS
