"""E-13 S-099 R-099-03 -- tactical tick period drops under high unit count.

R-099-03 (docs/bible/epics/E-13-movement-and-command.md, decision A, Westley
2026-09-24): above 1,000 live units the tactical tick rate drops from 20 to
10 ticks per second, on a tick boundary, and returns when the count crosses
back downward; every per-second quantity (speed, attack interval, ability
duration and cooldown, drift) is unchanged in real time because per-tick
values scale with the tick period; every peer switches on the same tick.

Accessor chosen for this contract: `uint32_t om_tactical_tick_period(const
om_world *w)`, returning the current period in base ticks (1 at 20 ticks/s,
2 at 10 ticks/s). csrc/ouroboros_sim.h has no such symbol yet, so it is
bound locally here via ctypes (the pattern test_E16_S111_saving.py uses for
its pre-freeze symbols) -- every test below is expected to fail on that
missing symbol on main today, not on an assertion. The implementer should
add the matching declaration to the header and wire the real function so
this file's local binding becomes redundant with a future conftest.py
generated binder.

This file is not named test_E13_..., so world_factory's epic-features
lookup (conftest._epic_for_module) does not find E-13 and leaves TACTICAL
off by default (docs/northstar/spec_factory/mvp_features.toml [default]).
Each test below turns TACTICAL on itself with om_world_set_feature, the
same way tests/csim/conftest.py's own isolate_agents() turns features on
and off explicitly.

"Live" units, for the purpose of killing units back down across the
threshold, means hp > 0 -- the same alive test csrc/unit.c uses pervasively
(`u->in_use && u->hp <= 0.0` skips a unit everywhere; om_unit_alive() is
exactly `row->hp > 0.0`). Tests kill a unit with om_unit_set_hp(w, id, 0.0)
rather than any despawn call, because csrc/unit.c has no removal path today
(in_use is never cleared once a unit is spawned) -- om_unit_count() would
not reflect a kill, so it is never used as the live-unit gate here.

Filler units are spawned 1,000,000+ wu away from the one Raider whose
position is measured, so Raider sensor_radius (800 wu, csrc/unit.c
OM_ROSTER_RAIDER_SENSOR) and collision separation never reach across the
two groups and cannot confound the per-step distance measured by the
moving Raider. All units share faction 0 (never hostile to each other) so
none of them auto-triggers Surge (om_ability_autotrigger_scan requires an
enemy in range).

Raider roster numbers (csrc/unit.c, not csrc/om_constants.h -- the brief
that ordered this file names the wrong header; these are #define in
unit.c): OM_ROSTER_RAIDER_SPEED 150.0 wu/s -> 7.5 wu per tick at 20
ticks/s (R-099-02). Surge ability (csrc/unit.c): OM_ABILITY_SURGE_DURATION_
TICKS 60 (60 base ticks = 3 s at 20 ticks/s) and OM_ABILITY_SURGE_COOLDOWN_
TICKS 1500.0 (75 s); at period 2 the 3 s duration must read as 30
om_tactical_step calls instead of 60, per R-099-03.
"""
import ctypes
import math

import pytest

from conftest import OMFeature


class OMUnitType:
    RAIDER = 0
    INTERCEPTOR = 1
    VANGUARD = 2
    WARDEN = 3
    BOMBARD = 4
    BASTION = 5


RAIDER_SPEED_PER_TICK_AT_PERIOD_1 = 7.5
SURGE_DURATION_BASE_TICKS = 60
SURGE_COOLDOWN_BASE_TICKS = 1500.0


def _bind_tick_period(lib):
    if getattr(lib, "_tick_period_bound", False):
        return
    lib.om_tactical_tick_period.argtypes = [ctypes.c_void_p]
    lib.om_tactical_tick_period.restype = ctypes.c_uint32
    lib._tick_period_bound = True


def _spawn_far_raiders(lib, w, n, *, faction_id=0, y_start=1_000_000.0, spacing=100.0):
    """n Raiders parked far enough from the origin that they never enter any
    other unit's sensor or collision radius (see module docstring)."""
    return [
        lib.om_unit_spawn(w, OMUnitType.RAIDER, faction_id, 0.0, y_start + i * spacing, 0)
        for i in range(n)
    ]


def _tactical_world(lib, world_factory, seed=1):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def test_R_099_03_period_1_at_or_below_1000_live_units(lib, world_factory):
    """Given 1,000 or fewer live units, When a tactical tick runs, Then the
    period is 1 (20 ticks/s) and a Raider ordered to move covers 7.5 wu per
    om_tactical_step (R-099-02's unchanged real-time speed)."""
    _bind_tick_period(lib)
    w = _tactical_world(lib, world_factory)
    _spawn_far_raiders(lib, w, 999)
    mover = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)

    rc = lib.om_command_move(w, mover, 10_000_000.0, 0.0)
    assert rc == 0

    lib.om_tactical_step(w)

    period = lib.om_tactical_tick_period(w)
    assert period == 1, "R-099-03: 1,000 live units is the threshold itself, not above it -- period must stay 1"

    # om_unit_position_x/y read unit.c's row cache, refreshed at the start of
    # the next om_tactical_step (tactical_move.c syncs lazily): a read right
    # after a step still reflects the position before that step's move. Two
    # consecutive reads, one step apart, cancel the lag and isolate the
    # distance moved during the one step between them.
    x1, y1 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    lib.om_tactical_step(w)
    x2, y2 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    dist = math.hypot(x2 - x1, y2 - y1)
    assert pytest.approx(dist, abs=1e-3) == RAIDER_SPEED_PER_TICK_AT_PERIOD_1, (
        "R-099-03: at period 1 a Raider still covers exactly 7.5 wu per om_tactical_step"
    )
    # Positive control: proves the distance assertion above actually discriminates
    # period 1 from period 2 -- if this ever silently matched the period-2 distance,
    # every period-1 assertion in this file would be worthless.
    assert dist != pytest.approx(15.0, abs=1e-3), (
        "R-099-03 positive control: period-1 movement must not equal the period-2 distance"
    )


def test_R_099_03_period_2_above_1000_live_units(lib, world_factory):
    """Given more than 1,000 live units, When the tick boundary that crosses
    the threshold runs, Then the period becomes 2 (10 ticks/s) on that same
    boundary, a Raider covers 15 wu in that one om_tactical_step (150 wu/s
    unchanged in real time), and a Surge (60 base ticks = 3 s) plays out over
    30 om_tactical_step calls instead of 60, with cooldown still reading
    1,500 (base-tick units) once it expires."""
    _bind_tick_period(lib)
    w = _tactical_world(lib, world_factory)
    _spawn_far_raiders(lib, w, 999)
    mover = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    crossing_unit = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 2_000_000.0, 0)
    assert crossing_unit is not None

    rc = lib.om_command_move(w, mover, 10_000_000.0, 0.0)
    assert rc == 0

    lib.om_tactical_step(w)

    period = lib.om_tactical_tick_period(w)
    assert period == 2, (
        "R-099-03: above 1,000 live units the period drops to 2 on the tick "
        "boundary that crosses the threshold"
    )

    # See test_R_099_03_period_1_at_or_below_1000_live_units: the position
    # getter lags one step behind tactical_move.c's lazy sync, so the delta
    # between two consecutive post-step reads is what isolates one step's
    # distance.
    x1, y1 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    lib.om_tactical_step(w)
    x2, y2 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    dist = math.hypot(x2 - x1, y2 - y1)
    assert pytest.approx(dist, abs=1e-3) == 2 * RAIDER_SPEED_PER_TICK_AT_PERIOD_1, (
        "R-099-03: per-tick distance doubles at period 2 so the Raider's 150 wu/s "
        "real-time speed (R-099-02) is unchanged"
    )

    surge_unit = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 3_000_000.0, 0)
    base_speed = lib.om_unit_profile_speed(w, OMUnitType.RAIDER)
    rc = lib.om_command_activate_ability(w, [surge_unit], 1, 0.0, 0.0)
    assert rc == 0

    steps_at_period_2 = SURGE_DURATION_BASE_TICKS // period
    assert steps_at_period_2 == 30
    for _ in range(steps_at_period_2):
        lib.om_tactical_step(w)
        assert lib.om_unit_effective_speed(w, surge_unit) == pytest.approx(base_speed * 2.5, abs=1e-6), (
            "R-099-03: Surge's 3 s duration is 30 om_tactical_step calls at period 2, "
            "not the 60 it takes at period 1 -- the buff must still be active here"
        )

    lib.om_tactical_step(w)
    assert lib.om_unit_effective_speed(w, surge_unit) == pytest.approx(base_speed, abs=1e-6), (
        "R-099-03: Surge must have expired by the 31st om_tactical_step call at period 2"
    )
    assert lib.om_unit_ability_cooldown(w, surge_unit) == pytest.approx(SURGE_COOLDOWN_BASE_TICKS, abs=1.0), (
        "R-099-03: cooldown reads the same 1,500 base-tick (75 s) value regardless of "
        "period -- ability cooldown length is unchanged in real time"
    )


def test_R_099_03_period_returns_to_1_crossing_back_down(lib, world_factory):
    """Given a population above 1,000 live units that a kill brings back to
    1,000 or fewer, When the next tick boundary runs, Then the period
    returns to 1."""
    _bind_tick_period(lib)
    w = _tactical_world(lib, world_factory)
    _spawn_far_raiders(lib, w, 999)
    mover = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    extra = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 2_000_000.0, 0)

    rc = lib.om_command_move(w, mover, 10_000_000.0, 0.0)
    assert rc == 0

    lib.om_tactical_step(w)
    assert lib.om_tactical_tick_period(w) == 2, (
        "setup: 1,001 live units must already be above the threshold before the down-cross"
    )

    lib.om_unit_set_hp(w, extra, 0.0)
    assert lib.om_unit_alive(w, extra) == 0

    lib.om_tactical_step(w)
    period = lib.om_tactical_tick_period(w)
    assert period == 1, (
        "R-099-03: crossing back to 1,000 or fewer live units on a tick boundary "
        "returns the period to 1"
    )

    x0, y0 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    lib.om_tactical_step(w)
    x1, y1 = lib.om_unit_position_x(w, mover), lib.om_unit_position_y(w, mover)
    dist = math.hypot(x1 - x0, y1 - y0)
    assert pytest.approx(dist, abs=1e-3) == RAIDER_SPEED_PER_TICK_AT_PERIOD_1, (
        "R-099-03: back at period 1 the Raider covers 7.5 wu per step again"
    )


def test_R_099_03_determinism_across_peers_on_the_crossing_tick(lib, world_factory):
    """Given two worlds built from the same seed and driven by the same
    command stream, When both cross the 1,000-live-unit threshold, Then both
    land on the same period on the same tick, and 50 om_tactical_step calls
    after the crossing tick both worlds report identical checksums (every
    peer in a multiplayer session switches on the same tick)."""
    _bind_tick_period(lib)
    outcomes = []
    for _ in range(2):
        w = _tactical_world(lib, world_factory, seed=4242)
        _spawn_far_raiders(lib, w, 999)
        mover = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
        rc = lib.om_command_move(w, mover, 10_000_000.0, 0.0)
        assert rc == 0

        for _ in range(5):
            lib.om_tactical_step(w)
        assert lib.om_tactical_tick_period(w) == 1, "setup: still at or below 1,000 before the crossing spawn"

        lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 2_000_000.0, 0)

        lib.om_tactical_step(w)  # the crossing tick itself
        period_on_crossing_tick = lib.om_tactical_tick_period(w)

        for _ in range(49):
            lib.om_tactical_step(w)

        outcomes.append((period_on_crossing_tick, lib.om_world_get_state_checksum(w)))

    (period_a, checksum_a), (period_b, checksum_b) = outcomes
    assert period_a == period_b == 2, (
        "R-099-03: two peers with the same seed and command stream cross on the same tick "
        "and land on the same period"
    )
    assert checksum_a == checksum_b, (
        "R-099-03: same seed, same command stream, byte-identical trace -- checksums must "
        "match 50 om_tactical_step calls after the crossing tick (determinism contract)"
    )
