"""PP-unit: formation arrival, nobody mills (E-13 S-099, R-099-04; DEC-movement-sidestep-2026-11-24).

R-099-04: "Given a unit within its arrival radius of its destination (1.5 x collision radius for a formation slot ...)" (22.5 wu for a Raider), "Then it has arrived where it stands".
This file began as R-099-05's proof (the give-up of a unit held within 75 wu of its slot for 40 ticks). The give-up is gone; a group mate no longer blocks a probe and an idle friend steps aside,
so the 20 Raiders of S101's scene all reach their slots and none paces to the last tick.

Scene: S101's own (20 Raiders, 4 x 5 at 35 wu, one group move to (1000, 70)).
"""
import ctypes
import math

from conftest import OMFeature

from test_PP_unit_support import RAIDER, dest, pos, spawn

ARRIVAL_RADIUS = 22.5     # R-099-04: 1.5 x collision radius 15 (S101 scene uses the same number)
SCENE_TICKS = 600         # brief: a bounded number of ticks


def _world(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _group_move(lib, w, ids, x, y):
    lib.om_command_group_move(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), x, y)


def _paces(has_dest_by_tick):
    """Detector: True if the unit's order never ended in the whole trace."""
    return bool(has_dest_by_tick) and all(has_dest_by_tick)



def test_R_099_04_control_detector_trips_on_pacing_and_not_on_an_ended_order():
    """Positive control for _paces: a trace whose order is active for all 600 ticks trips it; a trace
    that ends does not."""
    assert _paces([1] * SCENE_TICKS)
    assert not _paces([1] * 150 + [0] * (SCENE_TICKS - 150))
    assert not _paces([])



def test_R_099_04_s101_scene_every_order_ends_and_nobody_paces(lib, world_factory):
    """S-099 R-099-04: 20 Raiders, one group move; within 600 ticks every unit's order has ended
    (has_dest 0): each arrived, none mills with the order active to the last tick."""
    w = _world(lib, world_factory)
    units = [spawn(lib, w, RAIDER, 0, r * 35.0, c * 35.0) for r in range(4) for c in range(5)]
    _group_move(lib, w, units, 1000.0, 70.0)
    trace = {u: [] for u in units}
    for _ in range(SCENE_TICKS):
        lib.om_tactical_step(w)
        for u in units:
            trace[u].append(dest(lib, w, u)[0])
    pacing = [i for i, u in enumerate(units) if _paces(trace[u])]
    assert not pacing, f"units {pacing} still have an active order after {SCENE_TICKS} ticks (milling)"




def test_R_099_04_normal_arrival_still_ends_by_the_arrival_rule(lib, world_factory):
    """R-099-04 unchanged: a free unit ends its order within 22.5 wu of its slot (arrival, not give-up)."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 40.0)
    _group_move(lib, w, [a, b], 1000.0, 0.0)
    _, sx, sy = dest(lib, w, a)
    for _ in range(SCENE_TICKS):
        lib.om_tactical_step(w)
        if not dest(lib, w, a)[0]:
            break
    assert dest(lib, w, a)[0] == 0
    p = pos(lib, w, a)
    assert math.hypot(p[0] - sx, p[1] - sy) <= ARRIVAL_RADIUS
