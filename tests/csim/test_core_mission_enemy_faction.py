"""om_mission_get_enemy_faction public accessor.

Covers E-14 (enemy-owned structure production) and E-15 (tactical support).
No R-### id for this accessor specifically; story S-124 (E-14 enemy faction id
exposure) is the closest owner -- named S-124 throughout because no rule id
exists in the bible for this symbol.

Static derivation (mission.c ~1986):
  - region owner != player -> return owner
  - region owner == player -> return strongest hostile neighbour's owner
  - fallback (no case above) -> player==0 ? 1 : 0

Public accessor:
  - no mission in progress -> -1
  - else -> om_mission_enemy_faction(w, st->mission_region, om_player_faction(w))

RED on main (symbol missing; conftest binding raises AttributeError). GREEN after.
"""
import ctypes

import pytest

from conftest import OMArchetype, OMEdge, OMStance, set_edge, set_faction, set_owner, set_stance


class OMMissionArchetype:
    DEFENSIVE_STAND = 0


def _make_world(lib, n_regions=1, seed=1):
    w = lib.om_world_new(ctypes.c_uint32(n_regions), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    return w


# ---- (a) no mission -> -1 -------------------------------------------------------

def test_a_no_mission_returns_minus_one(lib):
    """S-124: no om_mission_setup -> om_mission_get_enemy_faction returns -1."""
    w = _make_world(lib)
    try:
        result = lib.om_mission_get_enemy_faction(w)
        assert result == -1, f"expected -1, got {result}"
    finally:
        lib.om_world_free(w)


# ---- (b) mission on enemy-owned region -> that faction id -----------------------

def test_b_enemy_faction_equals_region_owner_when_owner_is_not_player(lib):
    """S-124: mission region owned by faction 1; player is faction 0.
    Static: owner(0) >= 0 and owner(0) != player(0) is False... wait, region
    owned by faction 1, so owner=1, player=0, 1 != 0 -> return 1.
    Public accessor must return 1 and that is the faction the map instantiates
    enemy units for (by construction: only one enemy candidate exists)."""
    w = _make_world(lib, n_regions=2)
    try:
        set_faction(lib, w, 0, OMArchetype.PLAYER)
        set_faction(lib, w, 1, OMArchetype.CONQUEROR)
        # Region 0 owned by enemy faction 1; region 1 owned by player faction 0.
        set_owner(lib, w, 0, 1, held_since=-1)
        set_owner(lib, w, 1, 0, held_since=-1)
        # No edge needed; owner != player path fires immediately.
        lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
        result = lib.om_mission_get_enemy_faction(w)
        assert result == 1, f"expected 1 (enemy owner), got {result}"
    finally:
        lib.om_world_free(w)


def test_b_enemy_faction_hostile_neighbour_when_owner_is_player(lib):
    """S-124: mission region owned by player (0); hostile neighbour owned by
    faction 1 with high military -> accessor returns 1 (neighbour scan path)."""
    w = _make_world(lib, n_regions=3)
    try:
        set_faction(lib, w, 0, OMArchetype.PLAYER)
        set_faction(lib, w, 1, OMArchetype.CONQUEROR)
        set_stance(lib, w, 0, 1, OMStance.HOSTILE)
        # Region 0 owned by player; region 1 owned by hostile faction 1;
        # region 2 unrelated.
        set_owner(lib, w, 0, 0, held_since=-1)
        set_owner(lib, w, 1, 1, held_since=-1)
        # Connect region 0 <-> region 1 so region 1 is a neighbour.
        set_edge(lib, w, 0, 1, OMEdge.BOTH)
        lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
        result = lib.om_mission_get_enemy_faction(w)
        assert result == 1, f"expected 1 (hostile neighbour), got {result}"
    finally:
        lib.om_world_free(w)


# ---- (c) determinism: no RNG draw, same value on repeat calls -------------------

def test_c_no_rng_draw(lib):
    """S-124: calling om_mission_get_enemy_faction ten times does not advance RNG.
    om_world_get_state_checksum before == after."""
    w = _make_world(lib, n_regions=2)
    try:
        set_faction(lib, w, 0, OMArchetype.PLAYER)
        set_faction(lib, w, 1, OMArchetype.CONQUEROR)
        set_owner(lib, w, 0, 1, held_since=-1)
        set_owner(lib, w, 1, 0, held_since=-1)
        lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
        before = lib.om_world_get_state_checksum(w)
        for _ in range(10):
            lib.om_mission_get_enemy_faction(w)
        after = lib.om_world_get_state_checksum(w)
        assert before == after, "state checksum changed: accessor drew from RNG or mutated state"
    finally:
        lib.om_world_free(w)


def test_c_identical_worlds_give_identical_values(lib):
    """S-124: same seed, same setup -> same enemy faction id (determinism)."""
    results = []
    for _ in range(2):
        w = _make_world(lib, n_regions=2, seed=42)
        try:
            set_faction(lib, w, 0, OMArchetype.PLAYER)
            set_faction(lib, w, 1, OMArchetype.CONQUEROR)
            set_owner(lib, w, 0, 1, held_since=-1)
            set_owner(lib, w, 1, 0, held_since=-1)
            lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
            results.append(lib.om_mission_get_enemy_faction(w))
        finally:
            lib.om_world_free(w)
    assert results[0] == results[1], f"non-deterministic: {results}"


# ---- (d) positive control: different hostile faction yields different id --------

def test_d_different_hostile_neighbour_yields_different_id(lib):
    """S-124 positive control: scene with faction 2 as the region owner yields 2,
    not 1 (a scene with 1 returns 1 per test_b). Proves the accessor cannot return
    a fixed constant vacuously."""
    w = _make_world(lib, n_regions=2)
    try:
        set_faction(lib, w, 0, OMArchetype.PLAYER)
        set_faction(lib, w, 2, OMArchetype.CONQUEROR)
        # Region 0 owned by faction 2 (not 1); player is 0.
        set_owner(lib, w, 0, 2, held_since=-1)
        set_owner(lib, w, 1, 0, held_since=-1)
        lib.om_mission_setup(w, 0, OMMissionArchetype.DEFENSIVE_STAND, 0)
        result_2 = lib.om_mission_get_enemy_faction(w)
        assert result_2 == 2, f"expected 2 (faction 2 owns mission region), got {result_2}"
        # Must differ from the faction-1 scene in test_b.
        assert result_2 != 1, "positive control failed: returned 1 when owner is faction 2"
    finally:
        lib.om_world_free(w)
