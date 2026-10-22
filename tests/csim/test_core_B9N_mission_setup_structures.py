# Rule pins: R-126-01@71403e, R-126-02@741af4
"""B4 / B9-N: om_mission_setup places reinforcement structures per archetype.

R-126-01: Given a mission, When structures are placed, Then
  count = clamp(floor(region military x 0.06), small [2,4], medium [3,6], large [4,8])
  and the archetype's split assigns player, enemy and neutral owners
  (om_structure_assign_owners), player at least 1.
Canvas size class per archetype: om_map_archetype_canvas_category
(0 small, 1 medium, 2 large).

Observation: the header has no structure-count or map-structure reader, so the
tests scan structure slots 0..63 and count a slot as a placed structure when its
position is not (0, 0). Owner semantics (W-1d): player = om_player_faction,
enemy = om_mission_get_enemy_faction, neutral = -1.
"""
import ctypes
import math

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, OMVec2,
    set_edge, set_faction, set_owner, set_region,
)

DEFENSIVE_STAND = 0
SIEGE_BREAKING = 1
ASSAULT = 3
SUPPRESSION = 4
PLAYER_FAC = 0
ENEMY_FAC = 1
SLOTS = 64


def _scene(lib, world_factory, archetype, military, seed=7):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=military, faction_id=ENEMY_FAC)
    lib.om_mission_setup(w, 0, archetype, 0)
    return w


def placed(lib, w):
    """[(slot, owner, x, y)] for every slot whose position is not (0, 0)."""
    rows = []
    for slot in range(SLOTS):
        pos = OMVec2()
        lib.om_structure_get_position(w, slot, ctypes.byref(pos))
        if pos.x != 0.0 or pos.y != 0.0:
            rows.append((slot, lib.om_structure_get_owner(w, slot), pos.x, pos.y))
    return rows


def split(lib, w, rows):
    player, enemy = lib.om_player_faction(w), lib.om_mission_get_enemy_faction(w)
    p = sum(1 for r in rows if r[1] == player)
    e = sum(1 for r in rows if r[1] == enemy)
    n = sum(1 for r in rows if r[1] == -1)
    return p, e, n


def oracle(lib, archetype, total):
    p, e, n = ctypes.c_uint32(), ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_structure_assign_owners(archetype, total, ctypes.byref(p), ctypes.byref(e), ctypes.byref(n))
    return p.value, e.value, n.value


# ---- positive control: the scanner sees a structure it was told about ----

def test_control_scanner_sees_placed_structure(lib, world_factory):
    """R-126-01 positive control: a hand-placed structure is found by placed(),
    and a world with no mission placed none. Proves the detector can fire."""
    w = world_factory(n_regions=1, seed=3)
    assert placed(lib, w) == [], "control setup: a fresh world must have no placed structures"
    lib.om_structure_init(w, 5, 0, ctypes.c_double(100.0))
    lib.om_structure_set_owner(w, 5, 0)
    lib.om_structure_set_position(w, 5, 1234.0, 2345.0)
    assert placed(lib, w) == [(5, 0, 1234.0, 2345.0)], "control: scanner missed a placed structure"


# ---- count: clamp(floor(military x 0.06), class range) ----

def test_count_clamps_to_class_minimum(lib, world_factory):
    """R-126-01: military 0 -> floor 0 -> clamped up to the class minimum.
    DEFENSIVE_STAND is a medium canvas: [3, 6]; ASSAULT large [4, 8]; SUPPRESSION small [2, 4]."""
    for archetype, expect in ((DEFENSIVE_STAND, 3), (ASSAULT, 4), (SUPPRESSION, 2)):
        w = _scene(lib, world_factory, archetype, military=0.0)
        got = len(placed(lib, w))
        assert got == expect, (
            f"R-126-01: archetype {archetype} military 0 must place the class minimum {expect} "
            f"structures, found {got} -- om_mission_setup places none"
        )


def test_count_clamps_to_class_maximum(lib, world_factory):
    """R-126-01: military 10000 -> floor 600 -> clamped down to the class maximum."""
    for archetype, expect in ((DEFENSIVE_STAND, 6), (ASSAULT, 8), (SUPPRESSION, 4)):
        w = _scene(lib, world_factory, archetype, military=10000.0)
        got = len(placed(lib, w))
        assert got == expect, (
            f"R-126-01: archetype {archetype} military 10000 must place the class maximum {expect} "
            f"structures, found {got}"
        )


def test_count_follows_military_inside_the_range(lib, world_factory):
    """R-126-01: military 80 -> floor(80 x 0.06) = 4, inside medium [3,6] and large [4,8]."""
    for archetype in (DEFENSIVE_STAND, ASSAULT):
        w = _scene(lib, world_factory, archetype, military=80.0)
        assert len(placed(lib, w)) == 4, (
            f"R-126-01: archetype {archetype} military 80 must place floor(80 x 0.06) = 4 structures"
        )


# ---- owners: archetype split, player at least 1 ----

def test_owner_split_defensive_stand(lib, world_factory):
    """R-126-01: defensive stand 50/25/25 of 4 -> 2 player, 1 enemy, 1 neutral."""
    w = _scene(lib, world_factory, DEFENSIVE_STAND, military=80.0)
    got = split(lib, w, placed(lib, w))
    assert got == (2, 1, 1), f"R-126-01: defensive stand 50/25/25 of 4 must be (2, 1, 1), got {got}"


def test_owner_split_assault(lib, world_factory):
    """R-126-01: assault 25/50/25 of 4 -> 1 player, 2 enemy, 1 neutral."""
    w = _scene(lib, world_factory, ASSAULT, military=80.0)
    got = split(lib, w, placed(lib, w))
    assert got == (1, 2, 1), f"R-126-01: assault 25/50/25 of 4 must be (1, 2, 1), got {got}"


def test_owner_split_matches_assign_owners_for_every_archetype(lib, world_factory):
    """R-126-01: for every archetype the placed owners equal om_structure_assign_owners(
    archetype, count), the sum is the count, and the player holds at least 1."""
    for archetype in range(10):
        w = _scene(lib, world_factory, archetype, military=10000.0)
        rows = placed(lib, w)
        total = len(rows)
        assert total >= 2, f"R-126-01: archetype {archetype} placed {total} structures, minimum is 2"
        got = split(lib, w, rows)
        assert sum(got) == total, f"R-126-01: archetype {archetype} owners {got} do not cover all {total} structures"
        assert got == oracle(lib, archetype, total), (
            f"R-126-01: archetype {archetype} owners {got} differ from om_structure_assign_owners "
            f"{oracle(lib, archetype, total)} for {total} structures"
        )
        assert got[0] >= 1, f"R-126-01: archetype {archetype} gave the player no structure"


def test_structures_sit_on_the_canvas(lib, world_factory):
    """R-126-01: every placed structure lies inside the archetype's canvas, and no two share a spot."""
    for archetype in (DEFENSIVE_STAND, ASSAULT, SUPPRESSION):
        w = _scene(lib, world_factory, archetype, military=10000.0)
        canvas = lib.om_map_get_canvas_base_dimension(lib.om_map_archetype_canvas_category(archetype))
        rows = placed(lib, w)
        assert rows, f"R-126-01: archetype {archetype} placed no structures"
        for _, _, x, y in rows:
            assert 0.0 < x < canvas and 0.0 < y < canvas, (
                f"R-126-01: structure at ({x}, {y}) is off the {canvas} canvas"
            )
        assert len({(r[2], r[3]) for r in rows}) == len(rows), "R-126-01: two structures share a position"


def test_second_mission_replaces_the_first_missions_structures(lib, world_factory):
    """R-126-01: a fresh om_mission_setup lays its own structures; the previous mission's do not accumulate."""
    w = _scene(lib, world_factory, DEFENSIVE_STAND, military=10000.0)
    first = len(placed(lib, w))
    lib.om_mission_setup(w, 0, ASSAULT, 0)
    second = len(placed(lib, w))
    assert first == 6 and second == 8, (
        f"R-126-01: setup 1 (medium, mil 10000) must place 6 and setup 2 (large) must place 8 total, got {first} then {second}"
    )


# ---- integration: setup -> held structure -> unit in the tactical list ----

def test_held_structure_from_setup_produces_a_unit_in_the_tactical_list(lib, world_factory):
    """R-126-01/R-126-02 integration: after om_mission_setup, the player's held structure
    produces a unit of its chosen type, of the player faction, at the first free slot of its spawn lattice
    (R-126-02 as rewritten, TD-VG-E-29), within half the capture radius (150) of it, visible in the unit list after om_tactical_step ticks its interval."""
    w = _scene(lib, world_factory, DEFENSIVE_STAND, military=80.0)
    lib.om_mission_set_phase(w, 1)
    lib.om_unit_spawn(w, 0, ENEMY_FAC, 100_000.0, 100_000.0, 0)  # filler: tactical step no-ops with no units
    held = [r for r in placed(lib, w) if r[1] == PLAYER_FAC]
    assert held, "R-126-01: om_mission_setup left the player no held structure"
    slot, _, sx, sy = held[0]
    utype = lib.om_structure_get_unit_type(w, slot)
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(lib.om_unit_power(utype)))
    assert interval > 0, "R-126-02: a placed structure has no production interval"
    mine = lambda: {u for u in range(1, 2048) if lib.om_unit_alive(w, u) and lib.om_unit_get_faction(w, u) == PLAYER_FAC}
    before = mine()
    for _ in range(interval):
        lib.om_tactical_step(w)
    new = [u for u in mine() - before if lib.om_unit_get_unit_type(w, u) == utype
           and math.hypot(lib.om_unit_position_x(w, u) - sx, lib.om_unit_position_y(w, u) - sy) <= 150.0]
    assert new, (
        f"R-126-02: after {interval} steps no new player unit of type {utype} stands within 150 of "
        f"the held structure at ({sx}, {sy})"
    )
