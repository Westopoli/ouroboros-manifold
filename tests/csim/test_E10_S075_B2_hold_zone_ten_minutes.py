"""B2 (mission-plays plan): the hold-zone objective's required duration is 10
minutes of battle, 12,000 base ticks (R-075-02, Westley 2026-09-30), no longer
the mission's whole time limit; completion = elapsed/required and the mission
ends on completion (R-075-07).

Built through om_mission_build_objectives, the live path, so the required
duration is whatever that path installs (no direct om_mission_setup_hold_zone
override). There is no getter for the required ticks; it is read through
completion = elapsed/required.

See also: tests/csim/test_core_mission_live_termination.py (overrides the
quota with SMALL_HOLD_TICKS; its time-limit test no longer rests on
required == time limit).
"""
import ctypes

import pytest

from conftest import OMArchetype, set_faction, set_owner

HOLD_REQUIRED_TICKS = 12000
PLAYER_FAC = 0
ENEMY_FAC = 1
DEFENSIVE_STAND = 0
RAIDER = 0


class _Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


def _mission(lib, world_factory):
    lib.om_mission_has_ended.argtypes = [ctypes.c_void_p]
    lib.om_mission_has_ended.restype = ctypes.c_int
    w = world_factory(n_regions=2)
    lib.om_world_set_feature(w, 8, 1)  # OMFeature.TACTICAL
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, DEFENSIVE_STAND)
    return w


def _zone_center(lib, w):
    out = _Vec2()
    assert lib.om_objective_get_center(w, 0, ctypes.byref(out)) == 1
    return out.x, out.y


def test_R_075_02_hold_zone_is_not_sized_by_the_time_limit(lib, world_factory):
    """Guard: if the time limit ever equals 12,000 the red/green split of the
    tests below would be vacuous."""
    w = _mission(lib, world_factory)
    assert lib.om_mission_get_time_limit(w) != HOLD_REQUIRED_TICKS, (
        "time limit equals the hold quota: the B2 tests cannot tell the two apart")


def test_R_075_02_built_hold_zone_completion_is_half_at_6000_held_ticks(lib, world_factory):
    w = _mission(lib, world_factory)
    assert lib.om_mission_objective_count(w) == 1
    for _ in range(HOLD_REQUIRED_TICKS // 2):
        lib.om_mission_eval_hold_zone(w, 0, 0)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(0.5, abs=1e-6), (
        "R-075-02: 6,000 uncontested base ticks must be half of the 12,000 required")


def test_R_075_02_built_hold_zone_completes_at_exactly_12000_held_ticks(lib, world_factory):
    w = _mission(lib, world_factory)
    for _ in range(HOLD_REQUIRED_TICKS - 1):
        lib.om_mission_eval_hold_zone(w, 0, 0)
    assert lib.om_mission_get_objective_completion(w, 0) < 1.0
    lib.om_mission_eval_hold_zone(w, 0, 0)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(1.0, abs=1e-9), (
        "R-075-02: completion must reach 1.0 at 12,000 held ticks")


def test_R_075_07_mission_ends_at_12000_held_ticks_not_before(lib, world_factory):
    """Depends on the time limit outlasting 12,000 ticks, which needs the
    R-076-02 base-time table (om_archetype_base_time_ticks; already red in
    test_E10_S076_the_clock.py::test_R_076_02_they_minutes_in_table_q) to match
    the bible. Until then the mission ends at the stale time limit instead."""
    w = _mission(lib, world_factory)
    cx, cy = _zone_center(lib, w)
    # Player alive and inside the zone, no enemy unit anywhere.
    lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, cx, cy, 0)

    ended_at = None
    for i in range(HOLD_REQUIRED_TICKS + 5):
        lib.om_tactical_step(w)
        if lib.om_mission_has_ended(w):
            ended_at = i + 1
            break

    assert ended_at is not None, "mission never ended with the zone held uncontested"
    assert ended_at == HOLD_REQUIRED_TICKS, (
        "R-075-07: mission must end on hold completion at 12,000 steps, ended at %d" % ended_at)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(1.0, abs=1e-6)
