"""B12-16 -- Arrival clears destination; arrived unit stops and holds.

Proves B12-16 ruling (2026-09-26): when a unit reaches its destination it
clears has_dest, becomes stationary, and does not re-approach if subsequently
displaced.  Player-ordered hold and attack-move semantics for non-arrived
units are unchanged.

Related rule: R-099 (S-099, E-13-movement-and-command.md).
"""
import ctypes
import math

import pytest


_OM_UT_RAIDER = 0
_OM_UT_VANGUARD = 2
_FACTION = 0
_LAYER = 0
_OM_ARRIVAL_TOL = 1.5 * 15.0  # OM_ARRIVAL_TOLERANCE_MULT * OM_UNIT_COLLISION_RADIUS = 22.5 wu


def _make_world(lib):
    from conftest import OMFeature
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(1))
    assert w, "om_world_new returned NULL"
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _pos(lib, w, uid):
    return lib.om_unit_get_pos(w, uid)


def _dist(x0, y0, x1, y1):
    return math.hypot(x1 - x0, y1 - y0)


def _run_to_arrival(lib, w, uid, dest_x, dest_y, max_ticks=300):
    """Step until uid within arrival tolerance of dest; then 4 extra steps to ensure snap.

    Raider step = 7.5 wu/tick; worst-case detection at 22.5 wu needs 3 more ticks to snap.
    Returns tick of first detection or None.
    """
    detected = None
    for t in range(max_ticks):
        lib.om_world_step(w)
        x, y = _pos(lib, w, uid)
        if _dist(x, y, dest_x, dest_y) <= _OM_ARRIVAL_TOL:
            detected = t
            break
    if detected is None:
        return None
    for _ in range(4):
        lib.om_world_step(w)
    return detected


def test_R_099_arrived_unit_pushed_stays(lib):
    """R-099: unit reaches dest, is displaced 40 wu; 60 ticks later it stays within 1 wu of pushed spot.

    RED on main (unit re-approaches old destination after push, has_dest=1 on arrival).
    GREEN after fix (arrival clears has_dest; unit is stationary, stays where displaced).
    """
    w = _make_world(lib)
    dest_x, dest_y = 200.0, 0.0
    u = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 0.0, 0.0, _LAYER)
    lib.om_command_move(w, u, dest_x, dest_y)

    t = _run_to_arrival(lib, w, u, dest_x, dest_y)
    assert t is not None, "unit never arrived (fixture problem)"

    # Directly displace the arrived unit 40 wu along x (honest: bypasses collision,
    # which would not push a stationary unit anyway; this tests the re-approach logic).
    ax, ay = _pos(lib, w, u)
    pushed_x, pushed_y = ax + 40.0, ay
    lib.om_unit_set_pos(w, u, pushed_x, pushed_y)

    for _ in range(60):
        lib.om_world_step(w)

    xf, yf = _pos(lib, w, u)
    drift = _dist(xf, yf, pushed_x, pushed_y)
    assert drift <= 1.0, (
        "arrived unit re-approached old dest after displacement: "
        "%.2f wu from pushed spot (expected <= 1.0)" % drift
    )


def test_R_099_arrived_unit_is_stationary(lib):
    """R-099: destination-reached unit is stationary; om_unit_get_current_speed returns 0.

    Stationary accessor: om_unit_get_current_speed.
    RED on main (has_dest=1 at dest keeps speed = effective speed > 0).
    GREEN after fix (has_dest=0 on arrival; om_move_is_stationary returns 1; speed = 0).
    """
    w = _make_world(lib)
    dest_x, dest_y = 150.0, 0.0
    u = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 0.0, 0.0, _LAYER)
    lib.om_command_move(w, u, dest_x, dest_y)

    t = _run_to_arrival(lib, w, u, dest_x, dest_y)
    assert t is not None, "unit never arrived (fixture problem)"

    speed = lib.om_unit_get_current_speed(w, u)
    assert speed == pytest.approx(0.0, abs=1e-4), (
        "arrived unit speed=%.4f, expected 0 (should be stationary)" % speed
    )


def test_R_099_non_arrived_pushed_continues(lib):
    """Positive control (R-099): a unit that has NOT arrived, displaced 40 wu backward, resumes toward dest.

    GREEN before and after fix.
    """
    w = _make_world(lib)
    dest_x, dest_y = 500.0, 0.0
    u = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 0.0, 0.0, _LAYER)
    lib.om_command_move(w, u, dest_x, dest_y)

    # 5 ticks: unit has covered ~37.5 wu, well short of 500 wu dest
    for _ in range(5):
        lib.om_world_step(w)
    x0, y0 = _pos(lib, w, u)
    assert _dist(x0, y0, dest_x, dest_y) > _OM_ARRIVAL_TOL, "unit already arrived (fixture problem)"

    # Displace backward 40 wu
    lib.om_unit_set_pos(w, u, x0 - 40.0, y0)

    # 60 more ticks; unit should have resumed toward dest and be past its pre-push position
    for _ in range(60):
        lib.om_world_step(w)
    xf, yf = _pos(lib, w, u)
    assert xf > x0, (
        "non-arrived unit did not resume toward destination after push: "
        "xf=%.2f, x0=%.2f" % (xf, x0)
    )


def test_R_099_hold_and_attack_move_semantics(lib):
    """R-099: player-ordered hold unit stays; attack-move unit that has not arrived advances.

    GREEN before and after fix.
    """
    w = _make_world(lib)

    # Hold unit: no destination, spawned idle
    hold_u = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 100.0, 0.0, _LAYER)
    hold_x0, hold_y0 = _pos(lib, w, hold_u)

    # Attack-move unit: far destination, has not arrived yet
    atk_u = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 0.0, 50.0, _LAYER)
    lib.om_command_attack_move(w, atk_u, 500.0, 50.0)

    for _ in range(10):
        lib.om_world_step(w)

    hx, hy = _pos(lib, w, hold_u)
    assert _dist(hx, hy, hold_x0, hold_y0) < 1.0, (
        "hold unit moved %.2f wu from spawn, expected < 1.0" % _dist(hx, hy, hold_x0, hold_y0)
    )

    ax, ay = _pos(lib, w, atk_u)
    assert ax > 0.0, (
        "attack-move unit did not advance toward destination: ax=%.2f" % ax
    )
