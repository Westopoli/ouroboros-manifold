"""Shared scenes for the movement-sidestep tests (piece LS1, story movement-sidestep, DEC-movement-sidestep-2026-11-24). Holds no tests.

Units are of the default movement kind (flying) unless a test says otherwise: the steering probe and its sweep (om_move_steer_step,
tactical_move.c) run for them; a walking unit's step (om_move_walker_step) never reads the probe, so the probe tests need flyers and the
lab fights they mirror (L-0054, SIT-0106, sight off, no ground features) are flyers too. Blockers that must stand still are Supplies
(never fire, never move) or guards.
"""
import ctypes
import math

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, dest, pos, spawn, step  # noqa: F401

CANVAS = 4000.0
BIG_HP = 1.0e6
PROBE_DIST = 40.0                # OM_STEERING_PROBE_DIST
BLOCK_DIAMETER = 30.0            # 2 x collision radius 15 (ms->radius)
ARRIVE_SLOT = 22.5               # R-099-04: 1.5 x radius, a formation slot and a flying unit alone


def world(lib, wf, walking=()):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    for k in walking:
        assert lib.om_roster_set_movement_kind(w, k, 1) == 0
    return w


def _raw(fn):
    return getattr(fn, "raw", fn)


def _ids(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def move(lib, w, ids, x, y):
    return _raw(lib.om_command_move)(w, _ids(ids), len(ids), float(x), float(y))


def group_move(lib, w, ids, x, y):
    return lib.om_command_group_move(w, _ids(ids), len(ids), float(x), float(y))


def attack_move(lib, w, ids, x, y):
    return _raw(lib.om_command_attack_move)(w, _ids(ids), len(ids), float(x), float(y))


def guard(lib, w, ids):
    return _raw(lib.om_command_guard)(w, _ids(ids), len(ids))


def supply(lib, w, faction, x, y):
    s = spawn(lib, w, SUPPLY, faction, x, y)
    lib.om_unit_set_hp(w, s, BIG_HP)
    return s


def engaged_friend(lib, w, xy):
    """An own Vanguard at xy that holds a target and fires at an enemy Supply 250 wu east of it (1e6 hp, never fires): not idle, never moves."""
    e = spawn(lib, w, VANGUARD, 0, *xy)
    lib.om_unit_set_hp(w, e, BIG_HP)
    s = supply(lib, w, 1, xy[0] + 250.0, xy[1])
    return e, s


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def run_steps(lib, w, uid, n):
    """Positions of uid before the run and after each of n ticks."""
    out = [pos(lib, w, uid)]
    for _ in range(n):
        step(lib, w)
        out.append(pos(lib, w, uid))
    return out


def straight_blocked(p, aim, blockers, tip=PROBE_DIST):
    """The test's own reading of the probe: the tip 40 wu from p toward aim is within one diameter of a blocker's position (positions at the start of the tick)."""
    d = dist(p, aim)
    tx, ty = p[0] + tip * (aim[0] - p[0]) / d, p[1] + tip * (aim[1] - p[1]) / d
    return any(dist((tx, ty), b) < BLOCK_DIAMETER for b in blockers)
