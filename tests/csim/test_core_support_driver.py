"""E-15 S-127 (capture) / S-128 (production) driven purely by om_tactical_step,
under E-13 R-099-03 (tactical tick-period drop). docs/bible/epics/
E-13-movement-and-command.md R-099-03; docs/bible/epics/
E-15-reinforcement-supply-and-hazards.md R-127-01, R-128-01.

R-099-03: above 1,000 live units the tactical tick rate drops from 20 to 10
ticks per second; every per-second quantity is unchanged in real time because
per-tick values scale with the period. Structure capture (R-127-01, "progress
rises by dt / 10 s") and structure production (R-128-01, a timer that fires
every N base ticks) are both per-second quantities, so an orchestrator that
drives them off om_tactical_step must scale with the period exactly like
movement and abilities do.

csrc/tactical_support.c's om_structure_tick_capture is already period-aware
(it reads om_tactical_base_tick and om_tactical_tick_period internally, per
its own comment: "a step that spans 2 base ticks accrues 2"), and
tests/csim/test_E15_S127_taking_a_garrison.py already proves its real-time
schedule for direct calls: 100 direct calls (period 1) reach 0.5 of the 10 s
OM_REINFORCEMENT_CAPTURE_DURATION_SEC, 200 flip the owner. Nothing in
csrc/unit.c's om_tactical_step calls om_structure_tick_capture or
om_structure_tick_production automatically, and nothing increments a
structure's production timer per base tick either (checked directly: no
`->timer +=` or `->timer++` exists anywhere in csrc/) -- that driver wiring
is a separate card (B14-7) not yet built on any of B10c-9-r3, B9-11, or
B14-6. Every test below drives structures ONLY through om_tactical_step, by
design, so it stays red until B14-7 lands; that is the point of this file,
not a defect in it.

Neither om_tactical_tick_period nor om_tactical_base_tick has a header
declaration on main today; the one test below that reads om_tactical_tick_period
(via the period-2 fixture) binds it locally via ctypes, the pattern
tests/csim/test_core_tick_period.py uses.

This file is not named test_E15_..., so world_factory's epic-features lookup
(conftest._epic_for_module) leaves TACTICAL off by default; every test below
turns it on itself with om_world_set_feature. om_tactical_step is a no-op
while n_units == 0 (csrc/unit.c), so every world below carries at least one
spawned unit before it is stepped.
"""
import ctypes
import math

import pytest

from conftest import OMFeature, OMVec2


class OMUnitType:
    RAIDER = 0


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


def test_R_127_01_capture_progress_driven_by_tactical_step_period_1(lib, world_factory):
    """R-127-01, R-099-03: driven ONLY by om_tactical_step (no direct
    om_structure_tick_capture calls), capture progress must reach the same
    real-time schedule test_E15_S127_taking_a_garrison.py proves for direct
    calls: 0.5 at 100 base ticks (5 s of the 10 s capture duration), owner
    flips at 200 base ticks (10 s)."""
    w = _tactical_world(lib, world_factory, seed=1)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)

    lib.om_structure_init(w, 0, 0, 100.0)
    lib.om_structure_set_owner(w, 0, 2)
    lib.om_structure_set_capturing_faction(w, 0, 1)

    for _ in range(100):
        lib.om_tactical_step(w)
    progress = lib.om_structure_get_capture_progress(w, 0)
    assert progress == pytest.approx(0.5, abs=1e-3), (
        "R-127-01: 100 om_tactical_step calls at period 1 must accrue capture the same as "
        "100 direct om_structure_tick_capture calls -- the driver that ticks structures from "
        "om_tactical_step is not wired in yet"
    )

    for _ in range(100):
        lib.om_tactical_step(w)
    assert lib.om_structure_get_owner(w, 0) == 1, (
        "R-127-01: owner flips at 200 base ticks (10 s) driven purely by om_tactical_step"
    )


def test_R_127_01_capture_progress_driven_by_tactical_step_period_2(lib, world_factory):
    """R-099-03: at period 2 the same real-time capture schedule lands in
    half the om_tactical_step calls -- 0.5 at 50 steps (100 base ticks),
    owner flips at 100 steps (200 base ticks)."""
    _bind_tick_period(lib)
    w = _period_2_world(lib, world_factory, seed=2)

    lib.om_structure_init(w, 0, 0, 100.0)
    lib.om_structure_set_owner(w, 0, 2)
    lib.om_structure_set_capturing_faction(w, 0, 1)

    for _ in range(50):
        lib.om_tactical_step(w)
    progress = lib.om_structure_get_capture_progress(w, 0)
    assert progress == pytest.approx(0.5, abs=1e-3), (
        "R-099-03: at period 2, 50 om_tactical_step calls (100 base ticks) must accrue capture "
        "the same as 100 base ticks at period 1"
    )

    for _ in range(50):
        lib.om_tactical_step(w)
    assert lib.om_structure_get_owner(w, 0) == 1, (
        "R-099-03: owner flips at 100 steps (200 base ticks) at period 2 -- half the steps, "
        "the same real time, as period 1"
    )


def test_control_no_capturing_faction_present_progress_stays_0(lib, world_factory):
    """Positive control: with no unopposed capturing faction present, capture
    progress must never rise, proving the assertions above are not reading a
    counter that increments unconditionally regardless of contest state."""
    w = _tactical_world(lib, world_factory, seed=3)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)

    lib.om_structure_init(w, 0, 0, 100.0)
    lib.om_structure_set_owner(w, 0, 2)
    # capturing_faction left at its om_structure_init default (no contest).

    for _ in range(100):
        lib.om_tactical_step(w)
    assert lib.om_structure_get_capture_progress(w, 0) == pytest.approx(0.0, abs=1e-9), (
        "control: no capturing faction present -- progress must stay 0 over 100 steps"
    )


def _faction_1_units(lib, w):
    return {
        uid for uid in range(1, 4096)
        if lib.om_unit_alive(w, uid) and lib.om_unit_get_faction(w, uid) == 1
    }


def _assert_one_unit_materialised(lib, w, before, rule, why):
    """The production counter fired exactly once: one new unit of the owning
    faction, spawned within half the capture radius (150) of the structure, and
    the timer has subtracted exactly one interval (nothing left over)."""
    new = _faction_1_units(lib, w) - before
    assert len(new) == 1, f"{rule}: {why}; expected exactly one new unit, found {len(new)}"
    pos = OMVec2()
    lib.om_structure_get_position(w, 0, ctypes.byref(pos))
    (uid,) = new
    assert math.hypot(lib.om_unit_position_x(w, uid) - pos.x, lib.om_unit_position_y(w, uid) - pos.y) <= 150.0, (
        f"{rule}: the produced unit must spawn within 150 of its structure"
    )
    assert lib.om_structure_get_timer(w, 0) == 0, f"{rule}: the timer must subtract exactly one interval"


def test_R_128_01_production_counter_driven_by_tactical_step_period_1(lib, world_factory):
    """R-128-01, R-099-03: driven ONLY by om_tactical_step (no direct
    om_structure_tick_production or om_structure_set_timer calls), a
    structure's production counter must ready exactly one pending spawn once
    every om_structure_production_interval_ticks base ticks."""
    power = 10.0
    interval_ticks = int(lib.om_structure_production_interval_ticks(power))

    w = _tactical_world(lib, world_factory, seed=10)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)
    lib.om_structure_init(w, 0, 0, power)
    lib.om_structure_set_owner(w, 0, 1)
    before = _faction_1_units(lib, w)

    for _ in range(max(interval_ticks - 1, 0)):
        lib.om_tactical_step(w)
    assert _faction_1_units(lib, w) == before, (
        "R-128-01: no unit materialised before the full interval has elapsed"
    )
    lib.om_tactical_step(w)
    _assert_one_unit_materialised(
        lib, w, before, "R-128-01/R-099-03",
        f"driven purely by om_tactical_step, one unit must materialise after {interval_ticks} "
        f"base ticks (period 1: {interval_ticks} steps)",
    )


def test_R_128_01_production_counter_driven_by_tactical_step_period_2(lib, world_factory):
    """R-099-03: at period 2 the same real-time production interval lands in
    half the om_tactical_step calls."""
    power = 10.0
    interval_ticks = int(lib.om_structure_production_interval_ticks(power))
    steps_at_period_2 = interval_ticks // 2

    _bind_tick_period(lib)
    w = _period_2_world(lib, world_factory, seed=11)
    lib.om_structure_init(w, 0, 0, power)
    lib.om_structure_set_owner(w, 0, 1)
    before = _faction_1_units(lib, w)

    for _ in range(max(steps_at_period_2 - 1, 0)):
        lib.om_tactical_step(w)
    assert _faction_1_units(lib, w) == before, (
        "R-099-03: no unit materialised before the full interval (in base ticks) has elapsed"
    )
    lib.om_tactical_step(w)
    _assert_one_unit_materialised(
        lib, w, before, "R-099-03",
        f"at period 2 the same real-time interval is {steps_at_period_2} steps, half of "
        "period 1's -- the production timer must scale with the tick period like every other "
        "per-second quantity",
    )
