# spec: Architect ruling A198 (R-095-02) - Engine.order_group_move through the production library
"""om_command_group_move gives each unit its own slot: goal + (own position - group centroid). EXPECTED RED until
Engine.order_group_move exists."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402

GOAL = (600.0, 0.0)
# Measured with order_move on this layout: the first unit reaches its goal and goes idle (then fires) at tick 170;
# idle enemies shoot the walkers from the start, so only the walkers' own targeting and their damage are asserted.
WALK_TICKS = 150


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _world(library, enemies=()):
    w = library.new_world(0)
    library.disable_abilities(w)
    tid = library.type_id("Vanguard")
    mine = [library.spawn(w, tid, 0, 0.0, 30.0 * i, 0) for i in range(4)]
    foes = [library.spawn(w, tid, 1, x, y, 0) for x, y in enemies]
    return w, mine, foes


def test_group_move_gives_each_unit_its_own_slot(library):
    w, ids, _ = _world(library)
    try:
        pos = [library.unit_pos(w, u) for u in ids]
        cx, cy = sum(p[0] for p in pos) / 4, sum(p[1] for p in pos) / 4
        library.order_group_move(w, ids, *GOAL)
        dests = [library.unit_destination(w, u) for u in ids]
        assert all(d is not None for d in dests) and len(set(dests)) == 4
        for d, p in zip(dests, pos):
            assert d[0] == pytest.approx(GOAL[0] + p[0] - cx, abs=1e-6)
            assert d[1] == pytest.approx(GOAL[1] + p[1] - cy, abs=1e-6)
    finally:
        library.free_world(w)


def test_positive_control_plain_move_sends_every_unit_to_the_goal(library):
    w, ids, _ = _world(library)
    try:
        library.order_move(w, ids, *GOAL)
        assert [library.unit_destination(w, u) for u in ids] == [GOAL] * 4
    finally:
        library.free_world(w)


def test_group_move_returns_a_group_id_and_a_single_unit_does_not_raise(library):
    w, ids, _ = _world(library)
    try:
        assert library.order_group_move(w, ids[:1], *GOAL) >= 0
        assert library.order_group_move(w, ids, *GOAL) > 0
    finally:
        library.free_world(w)


def test_a_unit_on_a_group_move_never_targets_or_fires_while_walking(library):
    foes = [(150.0, 30.0 * i) for i in range(4)] + [(300.0, 30.0 * i) for i in range(4)]
    w, ids, enemies = _world(library, foes)
    try:
        start = {u: library.unit_hp(w, u) for u in enemies}
        library.order_group_move(w, ids, *GOAL)
        for _ in range(WALK_TICKS):
            library.step(w)
            assert all(library.unit_target(w, u) == 0 for u in ids)
        assert {u: library.unit_hp(w, u) for u in enemies} == start
    finally:
        library.free_world(w)
