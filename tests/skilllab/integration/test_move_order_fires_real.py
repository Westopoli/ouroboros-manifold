# spec: Architect ruling A198 - the fact the stop line depends on: a unit on a move order never fires while walking
# LAB-REV2-L2 inventory (Q-LAB-03): KEPT unchanged. 'closest approach' is a distance, not the retired approach opening.
"""A group on a move order walks through idle enemies without targeting or hurting them; the attack-move control fires.

Measured 2026-10-03 with the production library: move order, closest approach 30 wu, zero damage, no target at any tick;
attack-move, first damage at tick 151, closest approach 296.
"""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _walk(library, order):
    e = library
    van = e.type_id("Vanguard")
    w = e.new_world(0)
    try:
        for k, v in batches.BASE_SETTINGS.items():
            e.set_param(w, e.param_id(k), float(v))
        e.disable_abilities(w)
        walkers = [e.spawn(w, van, 0, 0.0, 400.0 + 30 * i, 0) for i in range(4)]
        idle = [e.spawn(w, van, 1, 900.0, 400.0 + 30 * i, 0) for i in range(4)]
        (e.order_move if order == "move" else e.order_attack_move)(w, walkers, 1500.0, 500.0)
        hp0 = sum(e.unit_hp(w, u) for u in idle)
        damaged, targets, closest = False, 0, 1e9
        for _ in range(300):
            e.step(w)
            damaged = damaged or sum(e.unit_hp(w, u) for u in idle) < hp0
            targets = max(targets, sum(1 for u in walkers if e.unit_target(w, u) != 0))
            closest = min(closest, min(math.dist(e.unit_pos(w, a), e.unit_pos(w, b)) for a in walkers for b in idle))
        return damaged, targets, closest
    finally:
        e.free_world(w)


def test_a_unit_on_a_move_order_does_not_target_or_fire_while_walking(library):
    damaged, targets, closest = _walk(library, "move")
    assert not damaged and targets == 0
    assert closest < 100   # it walked straight through the idle enemies: nothing stopped it


def test_positive_control_attack_move_targets_and_fires(library):
    damaged, targets, closest = _walk(library, "attack_move")
    assert damaged and targets > 0
    assert closest > 200   # it halted at its attack range
