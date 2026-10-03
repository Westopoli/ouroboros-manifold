# spec: Architect ruling A198 (R-095-02/R-095-03) - a "group_move" Group is chunked like attack_move/move
"""A group_move group wider than SLOT_RADIUS is split into chunks, each given goal + its centroid offset. Fake engine."""
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_group_move import GroupMoveFakeEngine  # noqa: E402
from scripts.skilllab import fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

GOAL = (500.0, 40.0)


def _group(count, side=0, formation="line", goal=GOAL):
    params = {"spacing": 30} if formation == "line" else {"radius": 100.0}
    return Group(side=side, unit="Vanguard", count=count, formation=formation, x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order="group_move", goal=goal,
                 params=params)


def _run(group):
    other = Group(side=1 - group.side, unit="Vanguard", count=1, formation="blob", x=0.0, y=0.0, facing_deg=0.0,
                  layer=0, order="idle", params={"radius": 10.0})
    setup = Setup(groups=(group, other), unit_types={})
    eng = GroupMoveFakeEngine()
    w = eng.new_world(0)
    types = fight._register_types(eng, w, setup)
    ids, ranges, rng = {}, {}, random.Random(0)
    for side in (0, 1):
        fight._spawn_side(eng, w, setup, side, types, rng, ids, ranges)
    eng.calls.clear()
    goals = fight._issue_orders(eng, w, setup, ids)
    orders = [c for c in eng.calls if c[0].startswith("order_")]
    return eng, orders, ids[0], goals   # the group under test is group index 0 (ids is keyed by group index)


def _centroid(eng, unit_ids):
    pts = [(eng.units[u]["x"], eng.units[u]["y"]) for u in unit_ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _max_dist(eng, unit_ids):
    cx, cy = _centroid(eng, unit_ids)
    return max(math.hypot(eng.units[u]["x"] - cx, eng.units[u]["y"] - cy) for u in unit_ids)


@pytest.mark.parametrize("count,calls", [(1, 1), (16, 1), (32, 2), (64, 3)])
def test_calls_per_line_width(count, calls):
    eng, orders, ids, goals = _run(_group(count))
    assert len(orders) == calls and all(o[0] == "order_group_move" for o in orders)
    flat = [u for o in orders for u in o[2]]
    assert sorted(flat) == sorted(ids) and len(set(flat)) == len(flat)
    assert goals[0] == GOAL


def test_32_line_chunks_carry_their_centroid_offset():
    eng, orders, ids, _ = _run(_group(32))
    gx, gy = _centroid(eng, ids)
    assert sorted(len(o[2]) for o in orders) == [16, 16]
    for o in orders:
        assert _max_dist(eng, o[2]) <= fight.SLOT_RADIUS
        cx, cy = _centroid(eng, o[2])
        assert o[3] == pytest.approx(GOAL[0] + (cx - gx)) and o[4] == pytest.approx(GOAL[1] + (cy - gy))
    assert orders[0][3:] != orders[1][3:]


def test_blob_of_32_is_one_call_with_the_original_goal():
    eng, orders, ids, _ = _run(_group(32, formation="blob"))
    assert len(orders) == 1 and orders[0][2] == ids and (orders[0][3], orders[0][4]) == GOAL


def test_side_one_splits_the_same_way():
    eng, orders, ids, goals = _run(_group(32, side=1, goal=(-500.0, 40.0)))
    gx, gy = _centroid(eng, ids)
    assert len(orders) == 2
    for o in orders:
        cx, cy = _centroid(eng, o[2])
        assert o[3] == pytest.approx(-500.0 + (cx - gx)) and o[4] == pytest.approx(40.0 + (cy - gy))
    assert goals[0] == (-500.0, 40.0)
