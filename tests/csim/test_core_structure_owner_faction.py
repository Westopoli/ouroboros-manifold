# Rule pins: R-126-01@71403e, R-126-02@2361a1, R-127-04@db7974
"""W-1d: structure owner = E-05 faction id; neutral = -1.

R-126-01: structure owner is an E-05 faction id; neutral structures have owner -1.
R-126-02: a held structure spawns one unit of the owner's faction per production
           interval, at the first free slot of its spawn lattice within half the capture radius
           (OM_REINFORCEMENT_CAPTURE_RADIUS / 2), with no random draw (rewritten, TD-VG-E-29).
R-127-04: capture path writes s->owner = capturing_faction (E-05 id).
"""
import ctypes

import pytest

from conftest import OMArchetype, OMFeature, OMVec2, set_faction


POWER = 10.0  # interval = OM_BASE_PRODUCTION_TIME_SEC * POWER / OM_POWER_NORMALIZATION * OM_TACTICAL_TICK_RATE = 60 ticks


class OMUnitType:
    RAIDER = 0


def _tactical_world_player0(lib, world_factory, *, seed=1):
    """World with TACTICAL feature and faction 0 configured as player."""
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=1.0, tech=1.0, confidence=1.0)
    assert lib.om_player_faction(w) == 0, "setup: faction 0 must be the player"
    return w


def _interval(lib):
    return int(lib.om_structure_production_interval_ticks(ctypes.c_double(POWER)))


def _spawn_position(lib, w, unit_id):
    return (
        ctypes.c_double(lib.om_unit_position_x(w, unit_id)).value,
        ctypes.c_double(lib.om_unit_position_y(w, unit_id)).value,
    )


def _structure_position(lib, w):
    pos = OMVec2()
    lib.om_structure_get_position(w, 0, ctypes.byref(pos))
    return pos.x, pos.y


def _drive_capture(lib, w, structure=0, ticks=200):
    for _ in range(ticks):
        lib.om_structure_tick_capture(w, structure)


# ---- (a) live capture by player faction 0 -> owner 0 -> production ----

def test_player_capture_then_produces_faction0_unit(lib, world_factory):
    """R-126-01/R-126-02/R-127-04: structure starts neutral (-1); player
    (faction 0) captures it through the existing capture path; owner becomes 0;
    production spawns a faction-0 unit at a lattice slot within half the capture radius (TD-VG-E-29).
    RED on main (owner==0 treated as neutral); GREEN after W-1d."""
    w = _tactical_world_player0(lib, world_factory, seed=50)

    # Anchor unit: om_tactical_step needs at least one live unit.
    anchor_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 1_000_000.0, 0)
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(POWER))
    # om_structure_init sets owner = -1 (neutral) after W-1d.
    assert lib.om_structure_get_owner(w, 0) == -1, "R-126-01: initial owner must be -1 (neutral)"

    # Player (faction 0) unopposed capture.
    lib.om_structure_set_capturing_faction(w, 0, 0)
    _drive_capture(lib, w)

    assert lib.om_structure_get_owner(w, 0) == 0, (
        "R-127-04: after 200 ticks of unopposed capture by faction 0, owner must be 0"
    )

    interval = _interval(lib)
    last_id = anchor_id
    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = last_id + 1
    assert lib.om_unit_alive(w, spawned_id), (
        f"R-126-02: player-captured structure (owner=0) must spawn one unit after {interval} steps"
    )
    faction = lib.om_unit_get_faction(w, spawned_id)
    assert faction == 0, (
        f"R-126-02: spawned unit must belong to faction 0 (player), got {faction}"
    )

    # Spawn position within half the capture radius (300 / 2 = 150 wu, inclusive: the lattice bound, TD-VG-E-29) of structure.
    sx, sy = _structure_position(lib, w)
    ux, uy = _spawn_position(lib, w, spawned_id)
    dist = ((ux - sx) ** 2 + (uy - sy) ** 2) ** 0.5
    assert dist <= 150.0 + 1e-6, (
        f"R-126-02: spawn at ({ux:.1f},{uy:.1f}) is {dist:.1f} wu from structure at "
        f"({sx:.1f},{sy:.1f}); must be within half capture radius (150 wu)"
    )


# ---- (b) enemy-owned structure produces enemy-faction unit ----

def test_enemy_owned_structure_produces_enemy_faction_unit(lib, world_factory):
    """R-126-02: owner = enemy faction id (1) -> spawned unit has faction 1.
    RED on main (W-1b maps owner 1 through sup_player_owner_id -> player
    faction 0, wrong faction); GREEN after W-1d (direct spawn for s->owner = 1)."""
    w = _tactical_world_player0(lib, world_factory, seed=51)

    anchor_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 1, 0.0, 1_000_000.0, 0)
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(POWER))
    lib.om_structure_set_owner(w, 0, 1)

    interval = _interval(lib)
    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = anchor_id + 1
    assert lib.om_unit_alive(w, spawned_id), (
        f"R-126-02: enemy-owned structure must spawn one unit after {interval} steps"
    )
    faction = lib.om_unit_get_faction(w, spawned_id)
    assert faction == 1, (
        f"R-126-02: enemy-owned (owner=1) structure must spawn faction-1 unit, got {faction}"
    )


# ---- (c) neutral structure produces nothing (positive control) ----

def test_neutral_structure_produces_nothing(lib, world_factory):
    """R-126-02: neutral structure (default owner from om_structure_init) ->
    no unit spawned. Positive control: GREEN on both main and after W-1d.
    Does not call set_owner explicitly; relies on om_structure_init default
    (0 on main, -1 after W-1d -- both hit the respective neutral guard)."""
    w = _tactical_world_player0(lib, world_factory, seed=52)

    anchor_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 1_000_000.0, 0)
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(POWER))
    # Do NOT call set_owner: rely on the default from om_structure_init.
    # On main: default owner=0 (neutral guard: owner==0). After W-1d: default=-1 (guard: owner<0).

    interval = _interval(lib)
    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = anchor_id + 1
    assert not lib.om_unit_alive(w, spawned_id), (
        "R-126-02: neutral structure (default owner from init) must not spawn any unit"
    )


# ---- (d) owner=0 is NOT neutral after W-1d (the bug this fixes) ----

def test_owner_0_is_not_neutral_with_player_faction_0(lib, world_factory):
    """R-126-02: owner 0 with player faction 0 must NOT be treated as neutral
    (the W-1b bug: s->owner == 0 guard conflated player faction 0 with neutral).
    RED on main (no production); GREEN after W-1d (owner < 0 guard)."""
    w = _tactical_world_player0(lib, world_factory, seed=53)

    anchor_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 1_000_000.0, 0)
    lib.om_structure_init(w, 0, OMUnitType.RAIDER, ctypes.c_double(POWER))
    lib.om_structure_set_owner(w, 0, 0)  # player faction 0

    interval = _interval(lib)
    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = anchor_id + 1
    assert lib.om_unit_alive(w, spawned_id), (
        "R-126-02: owner=0 with player faction 0 must NOT be treated as neutral -- "
        "production must happen (W-1b bug: owner==0 guard skipped faction-0 structures)"
    )


# ---- (e) no structures -> no units spawned (positive control) ----

def test_player_no_structures_no_unit_spawned(lib, world_factory):
    """R-126-02: with no structures, no units appear. Positive control proving
    assertions above cannot pass vacuously. GREEN on both main and after W-1d."""
    w = _tactical_world_player0(lib, world_factory, seed=54)

    anchor_id = lib.om_unit_spawn(w, OMUnitType.RAIDER, 0, 0.0, 1_000_000.0, 0)
    # No om_structure_init call.

    interval = _interval(lib)
    for _ in range(interval):
        lib.om_tactical_step(w)

    spawned_id = anchor_id + 1
    assert not lib.om_unit_alive(w, spawned_id), (
        "R-126-02: no structures -- no unit must appear after stepping "
        f"{interval} tactical steps"
    )
