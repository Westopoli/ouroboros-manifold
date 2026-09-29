"""B9-N: mission scoring wired live off the real battlefield instead of never
running at all (2026-09-28 QA-run wiring brief). Covers the hold_zone half of
R-075-02 end to end (real unit positions -> om_mission_eval_hold_zone -> the
objective's own completion), R-075-07's termination check
(om_mission_check_terminated) driven by that live completion and by the real
R-076-01 time limit, and that om_mission_end (band, commander fate,
consequences) is the same call this path and the client's explicit
mission_end both use.

Not covered here (see the report; already covered by
tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py's fixed-
value calls): destroy_targets and escort_to_extraction, which this wiring
leaves unevaluated -- no live mission marks a "designated target" subset or
places an extraction point yet.

om_tactical_step is a no-op while n_units == 0 (csrc/unit.c), so every
scenario below spawns at least the player unit that proves it is alive.
"""
import ctypes

import pytest

from conftest import OMArchetype, set_faction, set_owner


class OMMissionArchetype:
    DEFENSIVE_STAND = 0


class OMUnitType:
    RAIDER = 0


PLAYER_FAC = 0
ENEMY_FAC = 1
# Small hold quota so the "success" and "blocked" scenarios run in a handful
# of tactical steps instead of the real (1000+ tick) time limit; the time
# limit itself is exercised at its real value in
# test_time_limit_ends_the_mission_even_with_no_objective_progress below.
SMALL_HOLD_TICKS = 5


def _bind_has_ended(lib):
    if getattr(lib, "_has_ended_bound", False):
        return
    lib.om_mission_has_ended.argtypes = [ctypes.c_void_p]
    lib.om_mission_has_ended.restype = ctypes.c_int
    lib._has_ended_bound = True


def _setup_hold_zone_mission(lib, world_factory):
    """S-072..S-076 setup a real hold_zone mission (Defensive Stand) on a
    two-region world: region 0 (the mission region) owned by the enemy
    faction 1, region 1 owned by the player faction 0 -- the same
    owner-based enemy-faction derivation test_core_mission_enemy_faction.py
    pins (mission.c's static om_mission_enemy_faction: owner != player ->
    that owner)."""
    _bind_has_ended(lib)
    w = world_factory(n_regions=2)
    lib.om_world_set_feature(w, 8, 1)  # OMFeature.TACTICAL
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)

    lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, OMMissionArchetype.DEFENSIVE_STAND)
    return w


def _zone_center(lib, w):
    class OMVec2(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
    out = OMVec2()
    ok = lib.om_objective_get_center(w, 0, ctypes.byref(out))
    assert ok == 1, "om_objective_get_center found no objective node -- om_mission_setup did not instantiate a map"
    return out.x, out.y


# ---- R-075-02 / R-075-07: only player units inside -> hold completes, mission ends in a success band ----

def test_hold_with_only_player_units_inside_ends_mission_with_success_band(lib, world_factory):
    w = _setup_hold_zone_mission(lib, world_factory)
    lib.om_mission_setup_hold_zone(w, 0, SMALL_HOLD_TICKS)
    cx, cy = _zone_center(lib, w)

    # Player unit far from the zone (proves player_alive) and one right on
    # the objective, no enemy unit anywhere -- "only player units inside".
    lib.om_unit_spawn(w, OMUnitType.RAIDER, PLAYER_FAC, cx + 5000.0, cy, 0)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, PLAYER_FAC, cx, cy, 0)

    for _ in range(SMALL_HOLD_TICKS):
        lib.om_tactical_step(w)

    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(1.0, abs=1e-6), (
        "hold_zone completion did not reach 1.0 after %d uncontested ticks" % SMALL_HOLD_TICKS)
    assert lib.om_mission_has_ended(w) == 1, "mission did not auto-end once the primary objective completed"
    band = lib.om_mission_get_band(w)
    assert band == 4, "expected band 4 (total_success: final=1.0 on Defensive Stand's [0.20,0.40,0.60,0.80] thresholds), got %r" % band


# ---- R-075-02: enemy-only occupancy blocks the hold timer -- the opposite of the case above ----

def test_enemy_only_occupancy_blocks_the_hold_and_the_mission_does_not_end(lib, world_factory):
    w = _setup_hold_zone_mission(lib, world_factory)
    lib.om_mission_setup_hold_zone(w, 0, SMALL_HOLD_TICKS)
    cx, cy = _zone_center(lib, w)

    # Player alive, but far away; an enemy unit sits on the objective the
    # whole time (a freshly spawned unit with no order does not move --
    # csrc/unit.c om_tac_unit_ai only seeks a target within attack_range or
    # under an ATTACK_MOVE order, neither of which applies here).
    lib.om_unit_spawn(w, OMUnitType.RAIDER, PLAYER_FAC, cx + 5000.0, cy, 0)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, ENEMY_FAC, cx, cy, 0)

    for _ in range(SMALL_HOLD_TICKS * 2):
        lib.om_tactical_step(w)

    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(0.0, abs=1e-6), (
        "hold_zone completion advanced despite an enemy unit inside the zone the whole time")
    assert lib.om_mission_has_ended(w) == 0, (
        "mission auto-ended even though neither the objective nor the (far larger) time limit was reached")


# ---- R-075-07 / R-076-01: the time limit ends the mission with no objective progress ----

def test_time_limit_ends_the_mission_even_with_no_objective_progress(lib, world_factory):
    w = _setup_hold_zone_mission(lib, world_factory)
    # Leave hold_required_ticks at its real, live-computed value (the time
    # limit itself, see the report) -- this test proves the *time limit*
    # path, not a shortened quota, so no override here.
    limit = lib.om_mission_get_time_limit(w)
    assert limit > 0, "om_mission_get_time_limit returned 0 for a set-up mission"
    cx, cy = _zone_center(lib, w)

    lib.om_unit_spawn(w, OMUnitType.RAIDER, PLAYER_FAC, cx + 5000.0, cy, 0)
    lib.om_unit_spawn(w, OMUnitType.RAIDER, ENEMY_FAC, cx, cy, 0)  # blocks the hold forever

    ended_at = None
    for i in range(limit + 5):
        lib.om_tactical_step(w)
        if lib.om_mission_has_ended(w):
            ended_at = i + 1
            break

    assert ended_at is not None, "mission never ended within time_limit + 5 tactical steps"
    assert ended_at <= limit + 2, "mission ended too late relative to its own time limit (%d vs limit %d)" % (ended_at, limit)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(0.0, abs=1e-6), (
        "objective completion was nonzero -- the time-limit path should have ended this, not objective completion")
    band = lib.om_mission_get_band(w)
    assert band in (0, 1), "expected a failing band (total_failure/partial_failure) with 0 objective score, got %r" % band
