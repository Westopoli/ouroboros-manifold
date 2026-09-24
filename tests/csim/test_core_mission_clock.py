"""E-10 S-076 (the clock) / S-075 (hold zone) under E-13 R-099-03 (tactical
tick-period drop). docs/bible/epics/E-13-movement-and-command.md R-099-03;
docs/bible/epics/E-10-missions.md R-076-01/02/03, R-075-02.

R-099-03: above 1,000 live units the tactical tick rate drops from 20 to 10
ticks per second; every per-second quantity is unchanged in real time because
per-tick values scale with the period. The mission deadline (S-076) and the
hold-zone timer (S-075's R-075-02) are both per-second quantities, so both
must be measured in base ticks (om_tactical_base_tick, csrc/unit.c), never in
om_tactical_step call count or a flat per-call increment.

om_mission_is_ended (csrc/mission.c) holds the clock during recon (phase 0),
then compares om_tactical_base_tick(w) against a baseline: om_mission_begin
(csrc/fog.c) takes that baseline immediately via om_mission_on_begin, so a
caller that never polls is_ended between Begin and a late read still gets the
correct elapsed time; a caller that flips the phase off recon directly
(om_mission_set_phase, never calling om_mission_begin) gets a lazy baseline
instead, taken on the first is_ended call after recon
(tactical_baseline_pending, set by om_mission_setup_tactical whenever setup
runs during recon).

Neither om_tactical_tick_period nor om_tactical_base_tick has a header
declaration on main today (both land with card B10c-9-r3); every test below
binds them locally via ctypes, the pattern tests/csim/test_core_tick_period.py
uses, so this file fails loudly on the missing symbol on main rather than
silently skipping.

This file is not named test_E10_..., so world_factory's epic-features lookup
(conftest._epic_for_module) leaves TACTICAL off by default; every test below
turns it on itself with om_world_set_feature. om_tactical_step is a no-op
while n_units == 0 (csrc/unit.c), so every world below carries at least one
spawned unit before it is stepped.
"""
import ctypes

import pytest

from conftest import OMFeature


class OMUnitType:
    RAIDER = 0


OM_FOG_PHASE_RECON = 0
OM_FOG_PHASE_TACTICAL = 1


def _bind_tick_period(lib):
    if getattr(lib, "_tick_period_bound", False):
        return
    lib.om_tactical_tick_period.argtypes = [ctypes.c_void_p]
    lib.om_tactical_tick_period.restype = ctypes.c_uint32
    lib.om_tactical_base_tick.argtypes = [ctypes.c_void_p]
    lib.om_tactical_base_tick.restype = ctypes.c_uint64
    lib._tick_period_bound = True


def _tactical_world(lib, world_factory, seed=1):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _spawn_far_raiders(lib, w, n, *, faction_id=0, y_start=1_000_000.0, spacing=100.0):
    """n Raiders parked far enough from the origin that they never enter any
    other unit's sensor or collision radius (test_core_tick_period.py's
    module docstring explains the distances chosen)."""
    return [
        lib.om_unit_spawn(w, OMUnitType.RAIDER, faction_id, 0.0, y_start + i * spacing, 0)
        for i in range(n)
    ]


def _period_2_world(lib, world_factory, seed=1):
    """999 far filler Raiders plus 1 crossing Raider plus 1 near Raider (all
    faction 0): 1,001 live units. One om_tactical_step call is enough for the
    period to read 2 (test_core_tick_period.py's fixture)."""
    w = _tactical_world(lib, world_factory, seed=seed)
    _spawn_far_raiders(lib, w, 999)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 2_000_000.0, 0)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    lib.om_tactical_step(w)
    assert lib.om_tactical_tick_period(w) == 2, "setup: fixture must already be above the 1,000-live-unit threshold"
    return w


def test_R_099_03_mission_clock_period_1(lib, world_factory):
    """R-076-01/03: recon holds the clock; the deadline (limit=100) is
    measured in base ticks, one per om_tactical_step call at period 1."""
    _bind_tick_period(lib)
    w = _tactical_world(lib, world_factory)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)

    lib.om_mission_set_phase(w, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w, 0, 100)

    for _ in range(7):
        lib.om_tactical_step(w)
    assert lib.om_tactical_tick_period(w) == 1
    assert lib.om_mission_is_ended(w) == 0, "R-076-03: recon holds the clock -- no deadline before Begin"

    base_at_begin = lib.om_tactical_base_tick(w)
    lib.om_mission_begin(w)

    for _ in range(99):
        lib.om_tactical_step(w)
        assert lib.om_mission_is_ended(w) == 0
    lib.om_tactical_step(w)
    assert lib.om_mission_is_ended(w) == 1, "R-076-01: limit 100 reached on the 100th base tick after Begin"

    base_at_ended = lib.om_tactical_base_tick(w)
    assert base_at_ended - base_at_begin == 100, "R-099-03: the deadline is base ticks, one per step at period 1"


def test_R_099_03_mission_clock_period_2(lib, world_factory):
    """R-099-03: at period 2 each om_tactical_step call advances the base
    tick by 2, so the same limit=100 deadline is reached in half the steps
    (50, not 100) -- the deadline holds real time, never step count."""
    _bind_tick_period(lib)
    w = _period_2_world(lib, world_factory)

    lib.om_mission_set_phase(w, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w, 0, 100)

    base_at_begin = lib.om_tactical_base_tick(w)
    lib.om_mission_begin(w)

    for i in range(49):
        lib.om_tactical_step(w)
        assert lib.om_mission_is_ended(w) == 0, f"R-099-03: not yet ended after {i + 1} steps at period 2"
    lib.om_tactical_step(w)
    assert lib.om_mission_is_ended(w) == 1, "R-099-03: ended on the 50th step at period 2 (100 base ticks)"

    base_at_ended = lib.om_tactical_base_tick(w)
    assert base_at_ended - base_at_begin == 100, "R-099-03: base-tick delta from Begin to ended is 100 regardless of period"

    # Positive control: the old, wrong model compared om_tactical_step count
    # directly against the limit, which would not end this mission until the
    # 100th step. This world is already ended (at step 50); by step 100 under
    # the real base-tick model it must still read ended, never having
    # reverted -- proving the "ended at 50" result above is not a fluke of
    # this assertion order.
    for _ in range(50):
        lib.om_tactical_step(w)
    assert lib.om_mission_is_ended(w) == 1, "positive control: still ended well past the old step-count target of 100"


def test_R_099_03_base_tick_delta_from_begin_to_ended_is_period_independent(lib, world_factory):
    """R-099-03: the same limit=100 mission ends exactly 100 base ticks after
    Begin whether the world is at period 1 or period 2 -- the deadline is a
    real-time quantity, not a step count."""
    _bind_tick_period(lib)

    # Bounded loops throughout (never `while not ended: step`): on main
    # om_mission_is_ended is a STUB that always returns 0, which would spin
    # forever rather than fail. 200 steps is comfortably past either period's
    # true end (100 at period 1, 50 at period 2).
    MAX_STEPS = 200

    w1 = _tactical_world(lib, world_factory, seed=100)
    lib.om_unit_spawn(w1, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    lib.om_mission_set_phase(w1, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w1, 0, 100)
    base1_begin = lib.om_tactical_base_tick(w1)
    lib.om_mission_begin(w1)
    for _ in range(MAX_STEPS):
        if lib.om_mission_is_ended(w1):
            break
        lib.om_tactical_step(w1)
    else:
        pytest.fail(f"R-099-03: period-1 mission never ended within {MAX_STEPS} steps")
    base1_ended = lib.om_tactical_base_tick(w1)
    assert base1_ended - base1_begin == 100

    w2 = _period_2_world(lib, world_factory, seed=101)
    lib.om_mission_set_phase(w2, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w2, 0, 100)
    base2_begin = lib.om_tactical_base_tick(w2)
    lib.om_mission_begin(w2)
    for _ in range(MAX_STEPS):
        if lib.om_mission_is_ended(w2):
            break
        lib.om_tactical_step(w2)
    else:
        pytest.fail(f"R-099-03: period-2 mission never ended within {MAX_STEPS} steps")
    base2_ended = lib.om_tactical_base_tick(w2)
    assert base2_ended - base2_begin == 100

    assert (base1_ended - base1_begin) == (base2_ended - base2_begin) == 100, (
        "R-099-03: base-tick delta from Begin to ended must match across both periods"
    )


def test_R_099_03_baseline_taken_at_begin_not_at_first_read(lib, world_factory):
    """R-076-01/03: the deadline baseline is fixed the instant om_mission_begin
    runs (om_mission_on_begin), not deferred to whenever is_ended is first
    polled -- a world polled at step 40 and again at 50 agrees with a sibling
    world whose very first poll comes as late as step 99."""
    _bind_tick_period(lib)

    w_a = _period_2_world(lib, world_factory, seed=110)
    lib.om_mission_set_phase(w_a, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w_a, 0, 100)
    lib.om_mission_begin(w_a)
    for _ in range(40):
        lib.om_tactical_step(w_a)
    assert lib.om_mission_is_ended(w_a) == 0, "R-099-03: first read at step 40 (80 base ticks) is short of the 100 limit"
    for _ in range(10):
        lib.om_tactical_step(w_a)
    assert lib.om_mission_is_ended(w_a) == 1, "R-099-03: ended by step 50 (100 base ticks) after Begin"

    w_b = _period_2_world(lib, world_factory, seed=111)
    lib.om_mission_set_phase(w_b, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w_b, 0, 100)
    lib.om_mission_begin(w_b)
    for _ in range(99):
        lib.om_tactical_step(w_b)
    assert lib.om_mission_is_ended(w_b) == 1, (
        "R-099-03: a first read as late as step 99 still reports the correct elapsed time -- "
        "the baseline was fixed at Begin, never deferred to this first poll"
    )


def test_R_099_03_lazy_baseline_without_begin(lib, world_factory):
    """R-076-01/03: a caller that flips the phase off recon directly
    (om_mission_set_phase, never calling om_mission_begin) still gets a
    working deadline -- the baseline is taken lazily, on the first
    om_mission_is_ended call after recon (tactical_baseline_pending)."""
    _bind_tick_period(lib)
    w = _period_2_world(lib, world_factory, seed=120)

    lib.om_mission_set_phase(w, OM_FOG_PHASE_RECON)
    lib.om_mission_setup_tactical(w, 0, 100)
    lib.om_mission_set_phase(w, OM_FOG_PHASE_TACTICAL)  # no om_mission_begin call

    # Advance a few steps before the first read, to prove the baseline is
    # taken at the read itself, not when the phase flipped.
    for _ in range(3):
        lib.om_tactical_step(w)
    assert lib.om_mission_is_ended(w) == 0, "R-099-03: the first read takes the baseline right here -- elapsed is 0"

    for i in range(49):
        lib.om_tactical_step(w)
        assert lib.om_mission_is_ended(w) == 0, f"R-099-03: not yet ended {i + 1} steps after the lazy baseline"
    lib.om_tactical_step(w)
    assert lib.om_mission_is_ended(w) == 1, "R-099-03: ended 50 steps (100 base ticks) after the lazy baseline, at period 2"


def test_R_075_02_hold_zone_timer_scales_with_tick_period(lib, world_factory):
    """R-075-02, R-099-03: the hold-zone timer is also a per-second quantity
    -- each om_mission_eval_hold_zone call must advance it by the current
    tick period, so it too holds real time when the period drops to 2."""
    _bind_tick_period(lib)

    w1 = _tactical_world(lib, world_factory, seed=130)
    lib.om_unit_spawn(w1, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    lib.om_tactical_step(w1)
    assert lib.om_tactical_tick_period(w1) == 1

    lib.om_mission_setup_hold_zone(w1, 0, 100)
    for _ in range(10):
        lib.om_mission_eval_hold_zone(w1, 0, 0)
    c1 = lib.om_mission_get_objective_completion(w1, 0)
    assert c1 == pytest.approx(0.1, abs=1e-6), "R-075-02: 10 calls at period 1 advance the timer by 10 of 100 required ticks"

    w2 = _period_2_world(lib, world_factory, seed=131)
    lib.om_mission_setup_hold_zone(w2, 0, 100)
    for _ in range(10):
        lib.om_mission_eval_hold_zone(w2, 0, 0)
    c2 = lib.om_mission_get_objective_completion(w2, 0)
    assert c2 == pytest.approx(0.2, abs=1e-6), (
        "R-099-03: at period 2 each eval call advances the timer by 2 base ticks, "
        "so completion is unchanged in real time"
    )
