"""B12-15 / B10c-10 -- group move pace and auto-Fortify yield.

B12-15 root cause: om_command_group_move computed min_speed from
om_unit_effective_speed, which returns 16.0 wu/s for a Fortify-active
Bastion (40 wu/s * 0.4).  When 2+ friendlies are within OM_FORTIFY_RADIUS
(350 wu), Bastions auto-fortify after one tactical tick, dragging the whole
group to 0.8 wu/tick (48.00 wu in 60 ticks instead of about 120).

B10c-10 ruling (R-087-02): an auto-started ability yields to a player order;
a player-cast one does not.  Fix: add fortify_auto flag; auto-Fortify does
not apply the 0.4x speed penalty in om_unit_effective_speed (so the group
speed_cap is computed at native speed) and is cancelled in om_tac_unit_ai
when the unit receives a move order or destination.

Rules: R-086-06 (Fortify speed x0.4), R-086-08 (auto-trigger unchanged),
       R-087-02 (player order wins over auto-engagement), R-095-01 (group
       capped at slowest member's pace).
"""
import ctypes
import math

import pytest


_OM_UT_RAIDER = 0
_OM_UT_BASTION = 5
_FACTION = 0
_LAYER = 0

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
    Post-fix (B10c-10): fortify_auto flag causes om_unit_effective_speed to
    return native speed (40 wu/s) for auto-Fortify, so speed_cap = 40 wu/s.
    """
    w = _make_world(lib)
    # Spawn 2 Raiders + 1 Bastion within 350 wu so Bastion sees 2+ friendlies.
    # Abreast across the march axis (y), not in file along it: group mates block one another
    # (R-097-03, as the Python does), so a column would hold the rear units back.
    r1 = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION, 0.0,  0.0, _LAYER)
    r2 = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION, 0.0, 30.0, _LAYER)
    b1 = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION, 0.0, 60.0, _LAYER)

    # One step lets auto-fortify scan run; Bastion fortifies (ability_active -> 1,
    # effective_speed -> 16.0 wu/s on unmodified main).
    lib.om_world_step(w)

    assert lib.om_unit_ability_active(w, b1) == 1, (
        "Bastion did not auto-fortify; test fixture invalid "
        "(need 2+ friendlies within 350 wu for auto-fortify)")

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
            "to 0.4x natural (0.8 wu/tick -> 48 wu).  Fix: fortify_auto flag lets "
            "om_unit_effective_speed return native speed for auto-Fortify." % (name, d, _TICKS, d/_TICKS, min_expected))
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
        uid = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION, 0.0, float(i * 30), _LAYER)
        spawned.append(uid)
    for i in range(2):
        uid = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION, 0.0, float((19 + i) * 30), _LAYER)
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


def test_group_pace_player_cast_fortify_keeps_penalty(lib):
    """R-086-06 / R-087-02: a player-cast Fortify is NOT cancelled by a move order.
    The group speed_cap uses 0.4 x Bastion native speed (penalty kept).
    After 60 ticks the group covers 0.9 x 0.4 x bastion_speed x 60/20 to
    1.0 x 0.4 x bastion_speed x 60/20 wu.

    This test may pass on unmodified main (player-cast Fortify already caps
    the group at 0.4x speed; no cancel logic changes that).
    """
    w = _make_world(lib)
    raider = lib.om_unit_spawn(w, _OM_UT_RAIDER,  _FACTION,   0.0, 0.0, _LAYER)
    bastion = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION, 60.0, 0.0, _LAYER)

    # Player manually activates Fortify (fortify_auto stays 0).
    ids_b = (ctypes.c_uint32 * 1)(bastion)
    lib.om_command_activate_ability(w, ids_b, 1, 0.0, 0.0)
    lib.om_world_step(w)

    assert lib.om_unit_ability_active(w, bastion) == 1, (
        "Bastion Fortify not active after manual activation + one step")
    bastion_natural = lib.om_unit_profile_speed(w, _OM_UT_BASTION)  # 40.0 wu/s
    # Player-cast: speed penalty must still apply.
    assert pytest.approx(lib.om_unit_effective_speed(w, bastion), abs=1e-3) == bastion_natural * 0.4, (
        "Player-cast Fortify: effective speed must be 0.4 x native (R-086-06)")

    wu_per_tick = bastion_natural * 0.4 / _OM_TACTICAL_TICK_RATE   # 0.8 wu/tick
    min_expected = 0.9 * wu_per_tick * _TICKS                      # 43.2 wu
    max_expected = wu_per_tick * _TICKS                             # 48 wu

    ids = (ctypes.c_uint32 * 2)(raider, bastion)
    lib.om_command_group_move(w, ids, 2, 400.0, 0.0)

    starts = {uid: _pos(lib, w, uid) for uid in [raider, bastion]}
    for _ in range(_TICKS):
        lib.om_world_step(w)

    for uid, name in [(raider, "Raider"), (bastion, "Bastion")]:
        x0, y0 = starts[uid]
        xf, yf = _pos(lib, w, uid)
        d = _dist(x0, y0, xf, yf)
        assert d >= min_expected, (
            "%s moved %.3f wu, expected >= %.1f wu "
            "(player-cast Fortify must keep 0.4x speed penalty)" % (name, d, min_expected))
        assert d <= max_expected + 1.0, (
            "%s moved %.3f wu, expected <= %.1f wu" % (name, d, max_expected))

    lib.om_world_free(w)


def test_auto_fortify_cancelled_by_move_order(lib):
    """R-087-02 / B10c-10: auto-Fortify yields to a player move order.

    Setup: idle Bastion with 2+ friendlies within 350 wu auto-fortifies.
    Action: issue a plain move order to the Bastion.
    Assert: after the next tactical step the ability is inactive and
            effective speed is back to native.

    Control: the same Bastion setup without a move order still auto-fortifies
    (R-086-08 unchanged -- the fix must be exact, not overly broad).
    """
    w = _make_world(lib)
    bastion = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION,   0.0, 0.0, _LAYER)
    lib.om_unit_spawn(w,           _OM_UT_RAIDER,  _FACTION,  50.0, 0.0, _LAYER)
    lib.om_unit_spawn(w,           _OM_UT_RAIDER,  _FACTION, 100.0, 0.0, _LAYER)

    # Step until Bastion auto-fortifies (should happen on tick 1 since
    # suppress_auto=0 for idle unit and 2 friendlies are already in range).
    triggered = False
    for _ in range(5):
        lib.om_world_step(w)
        if lib.om_unit_ability_active(w, bastion):
            triggered = True
            break
    assert triggered, (
        "Bastion did not auto-fortify within 5 steps with 2 friendlies within 350 wu; "
        "test fixture invalid")

    # Issue a plain move order to the fortified Bastion.
    ids = (ctypes.c_uint32 * 1)(bastion)
    lib.om_command_move(w, ids, 1, 500.0, 0.0)

    # Next step: AI must cancel auto-Fortify (R-087-02 auto-yield rule).
    lib.om_world_step(w)
    assert lib.om_unit_ability_active(w, bastion) == 0, (
        "Auto-Fortify should be inactive after move order + one step (R-087-02); "
        "ability still active -- cancel path not implemented")
    bastion_natural = lib.om_unit_profile_speed(w, _OM_UT_BASTION)
    assert pytest.approx(lib.om_unit_effective_speed(w, bastion), abs=1e-3) == bastion_natural, (
        "Effective speed must return to native (%.1f wu/s) after auto-Fortify cancel" % bastion_natural)

    # Control: idle Bastion with 2+ friendlies and NO move order still auto-fortifies
    # (R-086-08 must remain unchanged; the fix must be exact, not too broad).
    lib.om_tactical_reset(w)
    b2   = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION,   0.0, 0.0, _LAYER)
    lib.om_unit_spawn(w,        _OM_UT_RAIDER,  _FACTION,  50.0, 0.0, _LAYER)
    lib.om_unit_spawn(w,        _OM_UT_RAIDER,  _FACTION, 100.0, 0.0, _LAYER)

    triggered2 = False
    for _ in range(5):
        lib.om_world_step(w)
        if lib.om_unit_ability_active(w, b2):
            triggered2 = True
            break
    assert triggered2, (
        "CONTROL FAIL: idle Bastion with 2+ friendlies must still auto-fortify "
        "(R-086-08); fix broke auto-trigger")

    lib.om_world_free(w)


def test_auto_fortify_cancel_no_cooldown_and_re_fortifies(lib):
    """R-087-02 / B10c-11: auto-Fortify cancel leaves cooldown at 0; unit
    re-fortifies on the next idle scan tick after arrival.

    Two assertions (both red on unmodified B10c-10 main):
      1. ability_cooldown == 0.0 one step after the cancel -- the player never
         chose auto-Fortify, so they pay no cooldown penalty.  Pre-fix (B10c-10
         cancel) applies FORTIFY_COOLDOWN_TICKS (1400.0) -- this assertion
         catches that.
      2. Bastion re-fortifies within 10 ticks of arrival at destination --
         cooldown=0 means the autotrigger scan fires on the first idle tick.
         Pre-fix: cooldown=1400 prevents re-trigger for 70 seconds game-time.
    """
    w = _make_world(lib)
    # Raiders placed on the y-axis so the Bastion can move freely along x
    # without collision-steering interference (Raiders still within 350 wu
    # of the Bastion's full travel range, so auto-fortify conditions hold).
    bastion = lib.om_unit_spawn(w, _OM_UT_BASTION, _FACTION,   0.0,   0.0, _LAYER)
    lib.om_unit_spawn(w,           _OM_UT_RAIDER,  _FACTION,   0.0,  50.0, _LAYER)
    lib.om_unit_spawn(w,           _OM_UT_RAIDER,  _FACTION,   0.0, 100.0, _LAYER)

    # Step until Bastion auto-fortifies (2+ friendlies within 350 wu).
    triggered = False
    for _ in range(5):
        lib.om_world_step(w)
        if lib.om_unit_ability_active(w, bastion):
            triggered = True
            break
    assert triggered, (
        "Bastion did not auto-fortify within 5 steps with 2 friendlies within 350 wu; "
        "test fixture invalid")

    # Issue a short move along x (10 wu; Bastion moves 2 wu/tick at native 40 wu/s).
    ids = (ctypes.c_uint32 * 1)(bastion)
    lib.om_command_move(w, ids, 1, 10.0, 0.0)

    # One step: AI cancels auto-Fortify; unit still travelling (suppress_auto=1).
    lib.om_world_step(w)
    assert lib.om_unit_ability_active(w, bastion) == 0, (
        "Auto-Fortify not cancelled after move order + one step (R-087-02)")
    cd = lib.om_unit_ability_cooldown(w, bastion)
    assert cd == pytest.approx(0.0, abs=1e-6), (
        "om_ability_cancel_fortify must leave cooldown at 0.0 (B10c-11 adjustment); "
        "got %.6f.  Pre-fix (B10c-10) applied FORTIFY_COOLDOWN_TICKS (1400.0) -- "
        "auto-yield imposes no cost on the player." % cd)

    # Step until arrival and re-fortify (10 ticks covers a 10 wu move at 2 wu/tick
    # plus one idle scan tick; scan fires immediately because cooldown=0).
    re_fortified = False
    for _ in range(10):
        lib.om_world_step(w)
        if lib.om_unit_ability_active(w, bastion):
            re_fortified = True
            break
    assert re_fortified, (
        "Bastion did not re-fortify after arriving at destination with 2 friendlies "
        "in range (cooldown=0 should allow scan to fire on the first idle tick; "
        "pre-fix cooldown=1400 prevents re-trigger for ~70 s)")

    lib.om_world_free(w)
