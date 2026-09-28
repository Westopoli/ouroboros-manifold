"""Enemy external reinforcement wave: unit spawn composition and placement (R-124-02).

Wave size is ALG-75's standard composition (OM_COMPOSITION_BASE 50 units:
raider 15, interceptor 10, vanguard 15, warden 5, bombard 3, bastion 2).
Q-124-02 closed 2026-09-28 (Westley). Built as W-1f.

RED on main (no units spawned: count stays 0). GREEN after W-1f.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    OMStance,
    force_draws,
    set_edge,
    set_faction,
    set_owner,
    set_stance,
)

# OM_UT_* indices match unit.c file-static defines (raider=0 .. bastion=5).
OM_UT_RAIDER      = 0
OM_UT_INTERCEPTOR = 1
OM_UT_VANGUARD    = 2
OM_UT_WARDEN      = 3
OM_UT_BOMBARD     = 4
OM_UT_BASTION     = 5

# ALG-75 (Q-124-02, Westley 2026-09-28).
EXPECTED_COUNTS = {
    OM_UT_RAIDER:      15,
    OM_UT_INTERCEPTOR: 10,
    OM_UT_VANGUARD:    15,
    OM_UT_WARDEN:       5,
    OM_UT_BOMBARD:      3,
    OM_UT_BASTION:      2,
}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())  # 50

DEFENSIVE_STAND = 0
PLAYER_FAC = 0
ENEMY_FAC  = 1


def _bind_unit_type(lib):
    if getattr(lib, "_unit_type_bound", False):
        return
    lib.om_unit_get_unit_type.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.om_unit_get_unit_type.restype  = ctypes.c_int32
    lib._unit_type_bound = True


def _bind_mission_setup(lib):
    if getattr(lib, "_mission_setup_bound", False):
        return
    V = ctypes.c_void_p
    lib.om_mission_setup.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
    lib.om_mission_setup.restype  = None
    lib._mission_setup_bound = True


def _tactical_world(lib, world_factory, seed=1):
    """2-region world with factions and a mission so enemy faction is derivable."""
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC,  OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC,  held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    _bind_mission_setup(lib)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)  # tactical phase
    return w


def _count_units_by_type(lib, w, faction_id):
    """Return dict {type_id: count} for all in-registry units of faction_id."""
    _bind_unit_type(lib)
    total = lib.om_unit_count(w)
    counts = {}
    scanned = 0
    i = 0
    while scanned < total and i < 11000:  # OM_MAX_UNITS=10100
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if not uid:
            continue
        scanned += 1
        if lib.om_unit_get_faction(w, uid) != faction_id:
            continue
        utype = lib.om_unit_get_unit_type(w, uid)
        counts[utype] = counts.get(utype, 0) + 1
    return counts


# ---- (a) exactly 50 enemy units at arrival tick with correct per-type counts ------

def test_a_wave_spawns_50_units_at_arrival_tick(lib, world_factory):
    """R-124-02: wave spawns OM_COMPOSITION_BASE=50 units at arrival tick,
    composition matches ALG-75 (15/10/15/5/3/2)."""
    w = _tactical_world(lib, world_factory)
    # 3 draws: roll=0.10 < 0.21 (wave fires), direction=2 (S), arrival_offset=0.0
    force_draws(lib, w, [0.10, 0.5, 0.0])

    lib.om_tactical_tick_to(w, 41)

    counts = _count_units_by_type(lib, w, ENEMY_FAC)
    total = sum(counts.values())
    assert total == EXPECTED_TOTAL, (
        f"R-124-02: expected {EXPECTED_TOTAL} enemy units at arrival tick, got {total}"
    )
    for utype, expected in EXPECTED_COUNTS.items():
        got = counts.get(utype, 0)
        assert got == expected, (
            f"R-124-02: unit type {utype}: expected {expected}, got {got} "
            f"(ALG-75 composition, Q-124-02)"
        )


# ---- (b) positive control: no enemy units before arrival tick ------------------

def test_b_no_enemy_units_before_arrival_tick(lib, world_factory):
    """R-124-02 positive control: step to arrival_tick - 1 (tick 40); wave
    has not fired yet so enemy unit count from this wave is 0."""
    w = _tactical_world(lib, world_factory)
    force_draws(lib, w, [0.10, 0.5, 0.0])

    lib.om_tactical_tick_to(w, 40)

    counts = _count_units_by_type(lib, w, ENEMY_FAC)
    total = sum(counts.values())
    assert total == 0, (
        f"R-124-02 positive control: expected 0 enemy units before arrival "
        f"tick, got {total}"
    )


# ---- (c) spawned units belong to om_mission_get_enemy_faction -----------------

def test_c_spawned_units_are_enemy_faction(lib, world_factory):
    """R-124-02: all 50 units belong to om_mission_get_enemy_faction."""
    w = _tactical_world(lib, world_factory)
    force_draws(lib, w, [0.10, 0.5, 0.0])

    lib.om_tactical_tick_to(w, 41)

    enemy_fac = lib.om_mission_get_enemy_faction(w)
    assert enemy_fac == ENEMY_FAC, (
        f"test setup: om_mission_get_enemy_faction returned {enemy_fac}, expected {ENEMY_FAC}"
    )
    counts = _count_units_by_type(lib, w, enemy_fac)
    total = sum(counts.values())
    assert total == EXPECTED_TOTAL, (
        f"R-124-02: {total} of {EXPECTED_TOTAL} units belong to the enemy faction"
    )


# ---- (d) once-only: no second spawn past another evaluation boundary ----------

def test_d_once_only_no_second_spawn(lib, world_factory):
    """R-124-02: reinforcement_spawned flag prevents a second wave. Run 80+
    more ticks past the arrival; enemy unit count must not grow.
    Scene has no other enemy-unit source (no player spawn, only our roll)."""
    w = _tactical_world(lib, world_factory)
    # Load enough draws so a second evaluation at tick 80 does NOT fire a
    # second wave. The once-per-mission guard (reinforcement_spawned) should
    # prevent any second spawn regardless, but we also force the second roll
    # above threshold to isolate the guard from the probability check.
    force_draws(lib, w, [0.10, 0.5, 0.0, 0.30])  # tick-40 fires; tick-80 roll=0.30 > 0.21

    lib.om_tactical_tick_to(w, 41)

    counts_at_arrival = _count_units_by_type(lib, w, ENEMY_FAC)
    total_at_arrival = sum(counts_at_arrival.values())
    assert total_at_arrival == EXPECTED_TOTAL, (
        f"R-124-02: setup check failed -- expected {EXPECTED_TOTAL} at tick 41, "
        f"got {total_at_arrival}"
    )

    lib.om_tactical_tick_to(w, 130)

    counts_after = _count_units_by_type(lib, w, ENEMY_FAC)
    total_after = sum(counts_after.values())
    # Unit count may drop (deaths) but never increase past the arrival total.
    assert total_after <= total_at_arrival, (
        f"R-124-02 once-only: enemy count grew from {total_at_arrival} to "
        f"{total_after} after 89 more ticks -- second spawn fired"
    )
