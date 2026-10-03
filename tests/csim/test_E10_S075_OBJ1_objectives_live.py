"""OBJ-1 (R-075-03, R-075-04, R-129-02): destroy_targets and escort_to_extraction
objectives must score from a live mission, driven only through om_tactical_step.

Today om_mission_build_objectives sets only the kind for these (csrc/mission.c)
and om_mission_tactical_tick evaluates only hold_zone and eliminate_force, so
Siege Breaking, Assault, Interception and Evacuation can never score.

What "designated target" means is not ruled (Q-OBJ-1 in the report): these
tests use the one reading every candidate agrees on -- when EVERY enemy unit
and EVERY enemy structure is dead, completion is 1.0, and with none dead it is
0.0. No test here asserts a fractional completion (the target count is not
ruled), and the escort test is skipped (extraction point and escort set are
not ruled).
"""
import ctypes

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region,
)

PLAYER_FAC = 0
ENEMY_FAC = 1
SLOTS = 64
SIEGE_BREAKING, ASSAULT, INTERCEPTION, EVACUATION = 1, 3, 6, 7
# Interception is left out: with no declared enemy attack its enemy power is 0 and the
# mission spawns no units at all (Q-OBJ-4 in the report), so there is nothing to destroy.
DESTROY_ARCHETYPES = [SIEGE_BREAKING, ASSAULT]


def _live_mission(lib, world_factory, archetype):
    w = world_factory(n_regions=2, seed=7)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, faction_id=ENEMY_FAC)
    set_region(lib, w, 1, tier=OMTier.HOME, military=60.0, faction_id=PLAYER_FAC)
    lib.om_mission_setup(w, 0, archetype, 0)
    lib.om_mission_build_objectives(w, archetype)
    return w


def _units(lib, w, faction):
    ids = []
    for i in range(lib.om_unit_count(w)):
        uid = lib.om_unit_id_at(w, i)
        if uid and lib.om_unit_get_faction(w, uid) == faction:
            ids.append(uid)
    return ids


def _enemy_structures(lib, w):
    class V(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
    out = []
    for s in range(SLOTS):
        p = V()
        lib.om_structure_get_position(w, s, ctypes.byref(p))
        if (p.x or p.y) and lib.om_structure_get_owner(w, s) == ENEMY_FAC:
            out.append(s)
    return out


def _kill_all_enemies(lib, w):
    for uid in _units(lib, w, ENEMY_FAC):
        lib.om_unit_set_hp(w, uid, 0.0)
    for s in _enemy_structures(lib, w):
        lib.om_structure_apply_damage(w, s, 1.0e9, 0)


@pytest.mark.parametrize("archetype", DESTROY_ARCHETYPES)
def test_destroy_targets_scores_zero_untouched_and_ends_nothing(lib, world_factory, archetype):
    """R-075-03 baseline: no target destroyed -> completion 0, mission still running."""
    w = _live_mission(lib, world_factory, archetype)
    assert _units(lib, w, PLAYER_FAC), "setup: mission spawned no player units"
    for _ in range(5):
        lib.om_tactical_step(w)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(0.0, abs=1e-6)
    assert lib.om_mission_has_ended(w) == 0


@pytest.mark.parametrize("archetype", DESTROY_ARCHETYPES)
def test_destroy_targets_completes_when_every_target_is_dead(lib, world_factory, archetype):
    """R-075-03 / R-075-07: all designated targets destroyed -> completion 1.0 and the
    mission ends on it. Under any reading of 'target', killing every enemy unit and
    structure destroys all of them."""
    w = _live_mission(lib, world_factory, archetype)
    _kill_all_enemies(lib, w)
    for _ in range(5):
        lib.om_tactical_step(w)
    assert lib.om_mission_get_objective_completion(w, 0) == pytest.approx(1.0, abs=1e-6), (
        "destroy_targets completion stayed at 0 although every enemy unit and structure is dead: "
        "om_mission_tactical_tick never evaluates destroy_targets")
    assert lib.om_mission_has_ended(w) == 1, "mission did not end on its completed primary objective"


@pytest.mark.skip(reason="Q-OBJ-2/3: the rules do not say which units are escorted, how many, or where the "
                         "extraction point is (R-075-04, R-129-02 give only 'within 200 wu'); a test would "
                         "have to call om_mission_setup_extraction_point itself, which is the unreached "
                         "function this unit must wire")
def test_escort_completes_when_escorted_units_reach_extraction(lib, world_factory):
    pass
