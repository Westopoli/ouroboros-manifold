"""W-1b Stage B: structure production spawns units for the right faction.

R-126-02: a held structure with a chosen unit type spawns one unit of the
owner's faction per production interval, positioned within half the capture
radius, driven by om_tactical_step.
R-126-06: om_mission_get_reinforcement_trickle stays 0.

Faction mapping (fixture convention -> E-05 faction id):
  owner 1 = player -> sup_player_owner_id(w): om_player_faction(w) when >= 0,
                      else OM_SUP_PLAYER_OWNER_FALLBACK = 1 (no player configured).
  owner 2 = enemy  -> spawn skipped (no public om_mission_get_enemy_faction;
                      mission.c:1980 static fn uses mission_region from private
                      state at mission.c:289). Leftover W-1b.
  owner 0 = neutral -> no production (guarded in driver; tested below).
  live capture sets s->owner = E-05 faction id directly; player faction 0 = owner 0
      = treated as neutral = no production (known interaction gap; documented in (e)).
"""
import ctypes

import pytest

from conftest import OMArchetype, OMFeature, set_faction


class OMUnitType:
    RAIDER = 0


def _tactical_world(lib, world_factory, *, seed=1):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


# ---- (a) player-held structure, no player faction configured (legacy fallback) ----

def test_player_structure_spawns_legacy_faction(lib, world_factory):
    """R-126-02: owner 1, no configured player faction -> om_player_faction
    returns -1 -> fallback faction 1 (OM_SUP_PLAYER_OWNER_FALLBACK).
    Spawned unit must have faction 1."""
    w = _tactical_world(lib, world_factory, seed=20)
    assert lib.om_player_faction(w) == -1, (
        "setup: unconfigured world must have no player faction"
    )
    initial_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 100_000.0, 0)

    power = 10.0
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(power))
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(power))
    lib.om_structure_set_owner(w, 0, 1)

    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = initial_id + 1
    assert lib.om_unit_alive(w, spawned_id), (
        "R-126-02: owner 1 must spawn one unit after the production interval "
        f"({interval} steps) -- om_unit_spawn not called from production driver"
    )
    faction = lib.om_unit_get_faction(w, spawned_id)
    assert faction == 1, (
        f"R-126-02: no player faction configured -- spawned unit must have "
        f"faction 1 (OM_SUP_PLAYER_OWNER_FALLBACK), got {faction}"
    )


# ---- (a2) player-held structure, player faction configured at 0 ----

def test_player_structure_spawns_configured_player_faction(lib, world_factory):
    """R-126-02: with faction 0 configured as OM_ARCH_PLAYER, om_player_faction
    returns 0. Owner 1 must spawn a unit with faction 0, not faction 1."""
    w = _tactical_world(lib, world_factory, seed=21)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=1.0, tech=1.0, confidence=1.0)
    assert lib.om_player_faction(w) == 0, (
        "setup: om_faction_set with ARCH_PLAYER at 0 must make om_player_faction return 0"
    )

    # Spawn a filler unit so om_tactical_step runs (no-op when n_units == 0).
    initial_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 1, 0.0, 100_000.0, 0)

    power = 10.0
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(power))
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(power))
    lib.om_structure_set_owner(w, 0, 1)

    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = initial_id + 1
    assert lib.om_unit_alive(w, spawned_id), (
        "R-126-02: owner 1 must spawn one unit after the production interval; "
        "wiring not calling om_unit_spawn"
    )
    faction = lib.om_unit_get_faction(w, spawned_id)
    assert faction == 0, (
        f"R-126-02: player faction configured at 0 -- spawned unit must have "
        f"faction 0 (om_player_faction(w)), got {faction}; "
        "mapping must use sup_player_owner_id, not hardcode s->owner"
    )


# ---- (b) enemy-held structure: blocked, no public accessor ----

@pytest.mark.xfail(
    reason=(
        "HELD: mission.c has no public om_mission_get_enemy_faction accessor. "
        "Static om_mission_enemy_faction (mission.c:1980) uses mission_region "
        "(private mission state field at mission.c:289). Owner 2 spawn skipped "
        "in production driver until mission.c exposes the enemy faction id."
    ),
    strict=False,
)
def test_enemy_structure_spawns_enemy_faction(lib, world_factory):
    """R-126-02: owner 2 must spawn a unit of the mission's enemy faction.
    HELD: no public om_mission_get_enemy_faction(w). Owner 2 is currently
    skipped in the production driver (leftover W-1b)."""
    pytest.xfail("no public om_mission_get_enemy_faction -- owner 2 spawn not wired")


# ---- (c) neutral structure produces nothing ----

def test_neutral_structure_produces_nothing(lib, world_factory):
    """R-126-02: owner 0 (neutral) must not spawn any unit."""
    w = _tactical_world(lib, world_factory, seed=22)
    initial_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 100_000.0, 0)

    power = 10.0
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(power))
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(power))
    # owner defaults to 0 (neutral) from om_structure_init

    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = initial_id + 1
    assert not lib.om_unit_alive(w, spawned_id), (
        "R-126-02: neutral structure (owner=0) must not spawn any unit"
    )


# ---- (d) zero structures, positive control ----

def test_zero_structures_no_units_spawned(lib, world_factory):
    """R-126-06: with no structures configured, no units appear after stepping.
    Positive control: proves unit-count assertions above cannot pass vacuously."""
    w = _tactical_world(lib, world_factory, seed=23)
    initial_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 100_000.0, 0)

    power = 10.0
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(power))
    # No om_structure_init call -- no structures.

    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = initial_id + 1
    assert not lib.om_unit_alive(w, spawned_id), (
        "R-126-06: no structures -- no unit must appear after stepping "
        f"{interval} tactical steps"
    )


# ---- (e) live-capture interaction ----

def test_player_capture_owner0_skips_production(lib, world_factory):
    """Interaction (R-126-02 / live-capture path): live capture writes
    s->owner = capturing_faction (an E-05 faction id). If the player is
    faction 0, s->owner = 0. The production driver guards owner == 0 as
    neutral (tactical_support.c line 829) and skips production. This is
    a known interaction gap: player-captured structures (faction 0) do not
    produce under the current mapping; option (a) resolves this by switching
    the owner id space to E-05 faction ids with neutral = -1."""
    w = _tactical_world(lib, world_factory, seed=24)
    initial_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 0.0, 0)

    power = 10.0
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(power))
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(power))
    # Live capture by player faction 0 -> s->owner = 0 (E-05 faction id).
    lib.om_structure_set_owner(w, 0, 0)

    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = initial_id + 1
    assert not lib.om_unit_alive(w, spawned_id), (
        "Interaction: owner=0 from live capture (player faction 0) is treated as "
        "neutral by the production driver (line 829) -- no unit is produced. "
        "Known gap: option (a) needed to distinguish neutral (-1) from player (0)."
    )
