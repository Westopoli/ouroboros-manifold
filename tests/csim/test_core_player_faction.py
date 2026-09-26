"""HDR3 (ABI 3) -- om_player_faction and the legacy-fallback rule.

Three sub-suites:

(a) World configured with faction 2 as player:
    fog keyed to faction 2, mission units keyed to faction 2 (non-player
    faction returns empty), structure ticker keyed to faction 2.

(b) Legacy fallback (no configured player):
    fog still reveals to faction 0 (OM_FOG_PLAYER_FACTION_FALLBACK = 0),
    structure ticker still fires for owner 1 (OM_SUP_PLAYER_OWNER_FALLBACK = 1).

(c) om_player_faction() return value: -1 unconfigured, configured id otherwise.

Not named test_E##, so world_factory's epic-features lookup leaves TACTICAL off
by default; tests that need tactical units turn it on themselves.
"""
import ctypes

from conftest import OMArchetype, OMFeature, set_faction


# ---- constants ---------------------------------------------------------------

class OMUnitType:
    VANGUARD = 2   # sensor radius 700 wu; faction 0 in E-12 scenes


# ---- helpers -----------------------------------------------------------------

def _make_world(lib, seed=1, tactical=False):
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    if tactical:
        lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _bind_fog(lib):
    """Lazy-bind fog and unit functions needed for visibility tests."""
    if getattr(lib, "_core_pf_fog_bound", False):
        return
    V = ctypes.c_void_p
    lib.om_unit_spawn.argtypes = [V, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_int]
    lib.om_unit_spawn.restype = ctypes.c_uint32
    lib.om_visibility_compute.argtypes = [V]
    lib.om_visibility_compute.restype = None
    lib.om_player_can_see.argtypes = [V, ctypes.c_int32, ctypes.c_uint32]
    lib.om_player_can_see.restype = ctypes.c_int
    lib.om_player_can_see_friendly.argtypes = [V, ctypes.c_int32, ctypes.c_uint32]
    lib.om_player_can_see_friendly.restype = ctypes.c_int
    lib._core_pf_fog_bound = True


def _bind_mission(lib):
    """Lazy-bind mission player-units functions."""
    if getattr(lib, "_core_pf_mission_bound", False):
        return
    V = ctypes.c_void_p
    P = ctypes.POINTER
    lib.om_mission_set_player_units.argtypes = [V, ctypes.c_int32, P(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_mission_set_player_units.restype = None
    lib.om_mission_get_player_units.argtypes = [V, ctypes.c_int32, P(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_mission_get_player_units.restype = None
    lib.om_mission_get_player_parity.argtypes = [V, ctypes.c_int32]
    lib.om_mission_get_player_parity.restype = ctypes.c_double
    lib._core_pf_mission_bound = True


def _bind_support(lib):
    """Lazy-bind tactical_support functions."""
    if getattr(lib, "_core_pf_sup_bound", False):
        return
    V = ctypes.c_void_p
    lib.om_structure_init.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double]
    lib.om_structure_init.restype = None
    lib.om_structure_on_owner_changed.argtypes = [V, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32]
    lib.om_structure_on_owner_changed.restype = None
    lib.om_ticker_pop_message.argtypes = [V, ctypes.c_char_p, ctypes.c_uint32]
    lib.om_ticker_pop_message.restype = None
    lib._core_pf_sup_bound = True


# ---- (a) player configured at faction 2 -------------------------------------

def test_a_fog_keyed_to_faction_2(lib):
    """Fog queries use faction 2 when configured; an enemy far from any faction-2
    unit is NOT visible to om_player_can_see(w, 2, ...) even though fog falls
    back to 0 in unconfigured worlds."""
    _bind_fog(lib)
    w = _make_world(lib, tactical=True)
    try:
        set_faction(lib, w, 2, OMArchetype.PLAYER)
        set_faction(lib, w, 0, OMArchetype.CONQUEROR)
        set_faction(lib, w, 1, OMArchetype.CONQUEROR)

        friendly = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 2, 0.0, 0.0, 0)
        enemy_far = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 1, 5000.0, 5000.0, 0)
        enemy_near = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 0, 200.0, 0.0, 0)

        lib.om_visibility_compute(w)

        # Faction-2 unit always sees itself (same faction)
        assert lib.om_player_can_see(w, 2, friendly) == 1
        # Faction-2 friendly: friendly sees nearby enemy (within sensor radius 700)
        assert lib.om_player_can_see(w, 2, enemy_near) == 1
        # Faction-2 does not see far enemy
        assert lib.om_player_can_see(w, 2, enemy_far) == 0

        # om_player_can_see_friendly: unit faction must match faction_id
        assert lib.om_player_can_see_friendly(w, 2, friendly) == 1
        assert lib.om_player_can_see_friendly(w, 2, enemy_near) == 0
    finally:
        lib.om_world_free(w)


def test_a_mission_units_keyed_to_faction_2(lib):
    """om_mission_set_player_units/get_player_units use the player-data slot when
    faction_id matches the configured player (2) and return zeros for others."""
    _bind_mission(lib)
    w = _make_world(lib)
    try:
        set_faction(lib, w, 2, OMArchetype.PLAYER)
        set_faction(lib, w, 0, OMArchetype.CONQUEROR)

        counts_in = (ctypes.c_uint32 * 3)(4, 3, 2)
        lib.om_mission_set_player_units(w, 2, counts_in, 3)

        # Reading back with faction 2 returns stored counts
        counts_out = (ctypes.c_uint32 * 3)()
        lib.om_mission_get_player_units(w, 2, counts_out, 3)
        assert list(counts_out) == [4, 3, 2]

        # Reading with faction 0 (not player) returns zeros
        counts_other = (ctypes.c_uint32 * 3)(9, 9, 9)
        lib.om_mission_get_player_units(w, 0, counts_other, 3)
        assert list(counts_other) == [0, 0, 0]

        # Parity for non-player returns 1.0 default
        parity_other = lib.om_mission_get_player_parity(w, 0)
        assert abs(parity_other - 1.0) < 1e-9

        # Setter for non-player is no-op
        lib.om_mission_set_player_units(w, 0, (ctypes.c_uint32 * 3)(99, 99, 99), 3)
        counts_after = (ctypes.c_uint32 * 3)()
        lib.om_mission_get_player_units(w, 2, counts_after, 3)
        assert list(counts_after) == [4, 3, 2]  # unchanged by the non-player setter
    finally:
        lib.om_world_free(w)


def test_a_structure_ticker_keyed_to_faction_2(lib):
    """om_structure_on_owner_changed fires 'captured' when new owner == configured
    player faction (2) and 'lost' when old owner == configured player (2)."""
    _bind_support(lib)
    w = _make_world(lib, tactical=True)
    try:
        set_faction(lib, w, 2, OMArchetype.PLAYER)
        set_faction(lib, w, 0, OMArchetype.CONQUEROR)
        lib.om_structure_init(w, 0, 0, ctypes.c_double(100.0))

        buf = ctypes.create_string_buffer(256)

        # Enemy owner (0) loses to player (2) -> "captured"
        lib.om_structure_on_owner_changed(w, 0, 0, 2)
        lib.om_ticker_pop_message(w, buf, 256)
        assert b"captured" in buf.value.lower()

        # Player (2) loses to enemy (0) -> "lost"
        lib.om_structure_on_owner_changed(w, 0, 2, 0)
        lib.om_ticker_pop_message(w, buf, 256)
        assert b"lost" in buf.value.lower()

        # Enemy-to-enemy (0->1) -> "changed hands", not captured or lost
        lib.om_structure_on_owner_changed(w, 0, 0, 1)
        lib.om_ticker_pop_message(w, buf, 256)
        msg = buf.value.lower()
        assert b"captured" not in msg
        assert b"lost" not in msg
    finally:
        lib.om_world_free(w)


# ---- (b) legacy fallback: no configured player faction ----------------------

def test_b_fog_fallback_faction_0(lib):
    """With no configured player faction, om_player_can_see(w, 0, ...) still
    works (legacy E-12 scene behaviour: faction 0 is the observer)."""
    _bind_fog(lib)
    w = _make_world(lib, tactical=True)
    try:
        # No set_faction with PLAYER archetype -> om_player_faction(w) == -1
        assert lib.om_player_faction(w) == -1

        friendly = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 0, 0.0, 0.0, 0)
        enemy_near = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 1, 200.0, 0.0, 0)
        enemy_far = lib.om_unit_spawn(w, OMUnitType.VANGUARD, 1, 5000.0, 5000.0, 0)

        lib.om_visibility_compute(w)

        assert lib.om_player_can_see(w, 0, friendly) == 1
        assert lib.om_player_can_see(w, 0, enemy_near) == 1
        assert lib.om_player_can_see(w, 0, enemy_far) == 0
    finally:
        lib.om_world_free(w)


def test_b_support_fallback_owner_1(lib):
    """With no configured player faction, om_structure_on_owner_changed fires
    'captured'/'lost' for owner 1 (OM_SUP_PLAYER_OWNER_FALLBACK = 1), the
    legacy E-15 scene convention."""
    _bind_support(lib)
    w = _make_world(lib, tactical=True)
    try:
        assert lib.om_player_faction(w) == -1
        lib.om_structure_init(w, 0, 0, ctypes.c_double(100.0))

        buf = ctypes.create_string_buffer(256)

        # Old owner 2 (enemy), new owner 1 (legacy player) -> "captured"
        lib.om_structure_on_owner_changed(w, 0, 2, 1)
        lib.om_ticker_pop_message(w, buf, 256)
        assert b"captured" in buf.value.lower()

        # Old owner 1 (legacy player), new owner 2 (enemy) -> "lost"
        lib.om_structure_on_owner_changed(w, 0, 1, 2)
        lib.om_ticker_pop_message(w, buf, 256)
        assert b"lost" in buf.value.lower()
    finally:
        lib.om_world_free(w)


# ---- (c) om_player_faction return value -------------------------------------

def test_c_player_faction_unconfigured_returns_minus_one(lib):
    """World with no in-use PLAYER faction: om_player_faction returns -1."""
    w = _make_world(lib)
    try:
        assert lib.om_player_faction(w) == -1
    finally:
        lib.om_world_free(w)


def test_c_player_faction_configured_returns_faction_id(lib):
    """World with faction 2 set to PLAYER: om_player_faction returns 2."""
    w = _make_world(lib)
    try:
        set_faction(lib, w, 2, OMArchetype.PLAYER)
        assert lib.om_player_faction(w) == 2
    finally:
        lib.om_world_free(w)


def test_c_player_faction_first_used_player_wins(lib):
    """When multiple factions exist, om_player_faction returns the lowest id
    with archetype PLAYER (first in-use, matching the loop in mission.c)."""
    w = _make_world(lib)
    try:
        set_faction(lib, w, 0, OMArchetype.CONQUEROR)
        set_faction(lib, w, 2, OMArchetype.PLAYER)
        set_faction(lib, w, 4, OMArchetype.CONQUEROR)
        assert lib.om_player_faction(w) == 2
    finally:
        lib.om_world_free(w)
