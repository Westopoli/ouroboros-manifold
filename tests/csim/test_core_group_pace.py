"""B12-15 -- group move pace: speed_cap uses profile speed, not ability-modified speed.

Reproduces the client's observation: 21 front-edge units group-moved +200 wu
each covered only 48 wu in 60 ticks (0.8 wu/tick) instead of the expected
108-120 wu (0.9-1.0 x Bastion natural speed x 60 ticks).

Root cause: om_command_group_move computed min_speed from om_unit_effective_speed,
which returns 16.0 wu/s for a Fortify-active Bastion (40 wu/s * 0.4).
When 2+ friendlies are within OM_FORTIFY_RADIUS (350 wu), Bastions auto-fortify
after one tactical tick, dragging the whole group to 0.8 wu/tick.

Fix (R-095-01): use mu->native_speed (profile speed, set before ability scan
each step) for the group speed_cap, not om_unit_effective_speed.

Rules: R-095-01 (group capped at slowest member's pace).
"""
import ctypes
import math

import pytest


# OM_FEAT_TACTICAL = 8 (ouroboros_sim.h enum)
_OM_FEAT_TACTICAL = 8

_OM_UT_RAIDER = 0
_OM_UT_BASTION = 5
_FACTION = 0
_LAYER = 0

# Bastion natural speed = 40 wu/s; at 20 tps = 2.0 wu/tick.
# om_unit_profile_speed(NULL, 5) returns 40.0 wu/s (same as OM_ROSTER_BASTION_SPEED).
_OM_TACTICAL_TICK_RATE = 20
_TICKS = 60


def _make_world(lib, n_regions=1, seed=1):
    """World with TACTICAL enabled (E-13 isolation)."""
    from conftest import OMFeature
    w = lib.om_world_new(ctypes.c_uint32(n_regions), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _pos(lib, w, uid):
    x, y = ctypes.c_double(0.0), ctypes.c_double(0.0)
    lib.om_unit_get_pos(w, uid, ctypes.byref(x), ctypes.byref(y))
    return x.value, y.value


def _dist(x0, y0, x1, y1):
    return math.hypot(x1 - x0, y1 - y0)


def test_group_pace_mixed_raider_bastion_after_fortify(lib):
    """R-095-01: a Raider+Bastion group moves at Bastion's NATURAL speed even
    when Bastion has auto-fortified (requires 2+ friendlies within 350 wu).

    Positive control (red on unmodified main, green after fix):
    After 1 step, Bastion auto-fortifies (effective speed -> 16 wu/s = 0.8 wu/tick).
    Pre-fix: min_speed = 16.0, group covers 48 wu in 60 ticks (0.8 wu/tick).
    Post-fix: min_speed = 40.0 (native_speed), group covers ~120 wu (2.0 wu/tick).
    """
    w = _make_world(lib)
    # Spawn 2 Raiders + 1 Bastion within 350 wu so Bastion sees 2+ friendlies.
    r1 = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION,  0.0,  0.0, _LAYER)
    r2 = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION, 30.0,  0.0, _LAYER)
    b1 = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION, 60.0,  0.0, _LAYER)

    # One step lets auto-fortify scan run; Bastion fortifies (ability_active -> 1,
    # effective_speed -> 16.0 wu/s).  Pre-fix: min_speed becomes 16.0 wu/s.
    lib.om_world_step(w)

    assert lib.om_unit_ability_active(w, b1) == 1, (
        "Bastion did not auto-fortify; test fixture invalid "
        "(need 2+ friendlies within 350 wu for auto-fortify)")
    assert pytest.approx(lib.om_unit_effective_speed(w, b1), abs=1e-3) == 16.0, (
        "Fortify-active Bastion effective speed should be 40 * 0.4 = 16.0 wu/s")

    bastion_natural = lib.om_unit_profile_speed(w, _OM_UT_BASTION)  # 40.0 wu/s
    wu_per_tick = bastion_natural / _OM_TACTICAL_TICK_RATE           # 2.0 wu/tick
    min_expected = 0.9 * wu_per_tick * _TICKS                       # 108 wu
    max_expected = wu_per_tick * _TICKS                              # 120 wu

    ids = (ctypes.c_uint32 * 3)(r1, r2, b1)
    # Move toward +200 wu on x axis from each unit's spawn
    click_x = 200.0
    lib.om_command_group_move(w, ids, 3, click_x, 0.0)

    starts = {uid: _pos(lib, w, uid) for uid in [r1, r2, b1]}
    for _ in range(_TICKS):
        lib.om_world_step(w)

    for uid, name in [(r1, "Raider-1"), (r2, "Raider-2"), (b1, "Bastion")]:
        x0, y0 = starts[uid]
        xf, yf = _pos(lib, w, uid)
        d = _dist(x0, y0, xf, yf)
        assert d >= min_expected, (
            "%s moved %.3f wu in %d ticks (%.4f wu/tick), expected >= %.1f wu. "
            "Bastion auto-fortified (eff=16 wu/s) and likely dragged group speed_cap "
            "to 0.4x natural (0.8 wu/tick -> 48 wu).  Fix: use native_speed in "
            "om_command_group_move min_speed loop." % (name, d, _TICKS, d/_TICKS, min_expected))
        assert d <= max_expected + 1.0, (
            "%s moved %.3f wu, expected <= %.1f wu (collision/steering slack +1)" % (name, d, max_expected))

    lib.om_world_free(w)


def test_solo_raider_moves_at_own_speed(lib):
    """R-095-07: a single Raider moves at its own speed.
    Raider natural speed = 150 wu/s = 7.5 wu/tick.  60 ticks expected 405-450 wu.
    Must stay green on unmodified main (solo unit path unchanged by this bug).
    """
    w = _make_world(lib)
    raider = lib.om_unit_spawn(w, _OM_UT_RAIDER, _FACTION, 0.0, 0.0, _LAYER)
    ids = (ctypes.c_uint32 * 1)(raider)
    lib.om_command_move(w, ids, 1, 1000.0, 0.0)

    raider_natural = lib.om_unit_profile_speed(w, _OM_UT_RAIDER)  # 150.0 wu/s
    wu_per_tick = raider_natural / _OM_TACTICAL_TICK_RATE          # 7.5 wu/tick
    min_expected = 0.9 * wu_per_tick * _TICKS                     # 405 wu
    max_expected = wu_per_tick * _TICKS                            # 450 wu

    x0, y0 = _pos(lib, w, raider)
    for _ in range(_TICKS):
        lib.om_world_step(w)
    xf, yf = _pos(lib, w, raider)
    d = _dist(x0, y0, xf, yf)

    assert d >= min_expected, (
        "Solo Raider moved %.3f wu in %d ticks (%.4f wu/tick), expected >= %.1f wu"
        % (d, _TICKS, d/_TICKS, min_expected))
    assert d <= max_expected + 1.0, (
        "Solo Raider moved %.3f wu, expected <= %.1f wu" % (d, max_expected))

    lib.om_world_free(w)


def test_group_pace_dense_21_units(lib):
    """R-095-01 (dense): 19 Raiders + 2 Bastions at 30 wu grid spacing.
    After one step Bastions auto-fortify (21 units, all in 350 wu radius).
    Post-fix: group speed_cap = Bastion natural (40 wu/s), all cover >= 108 wu.
    Without this test the client's front-edge 21-unit scenario is only checked
    via the pipe; this guards regression at the ctypes level.
    """
    w = _make_world(lib)
    spawned = []
    for i in range(19):
        uid = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION, float(i * 30), 0.0, _LAYER)
        spawned.append(uid)
    for i in range(2):
        uid = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION, float((19 + i) * 30), 0.0, _LAYER)
        spawned.append(uid)

    # Step once to allow auto-fortify.
    lib.om_world_step(w)

    bastion_natural = lib.om_unit_profile_speed(w, _OM_UT_BASTION)  # 40 wu/s
    wu_per_tick = bastion_natural / _OM_TACTICAL_TICK_RATE
    min_expected = 0.9 * wu_per_tick * _TICKS   # 108 wu
    max_expected = wu_per_tick * _TICKS + 5.0   # 125 wu slack for collision scatter

    ids = (ctypes.c_uint32 * len(spawned))(*spawned)
    click_x = 1000.0
    lib.om_command_group_move(w, ids, len(spawned), click_x, 0.0)

    starts = {uid: _pos(lib, w, uid) for uid in spawned}
    for _ in range(_TICKS):
        lib.om_world_step(w)

    for i, uid in enumerate(spawned):
        x0, y0 = starts[uid]
        xf, yf = _pos(lib, w, uid)
        d = _dist(x0, y0, xf, yf)
        utype = "Bastion" if i >= 19 else "Raider"
        assert d >= min_expected, (
            "unit[%d] (%s) moved %.3f wu (%.4f wu/tick), expected >= %.1f wu. "
            "Group speed_cap stuck at Fortify-reduced pace (48 wu = pre-fix)" % (i, utype, d, d/_TICKS, min_expected))

    lib.om_world_free(w)
