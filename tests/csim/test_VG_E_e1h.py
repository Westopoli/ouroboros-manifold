"""Visible-game lane E1, piece E1h: strongpoints on the slopes between height bands (csrc/strongpoint.c).
Spec docs/northstar/plans/2026-10-07-visible-game-spec.md rev 6 (lane E1, section 2, section 7 liberties). Fenced:
builders never edit this file.

Proves: R-218-01 (strongpoints stand on slopes of a ground map; count = R-126-01's, capped by the slopes there are;
owner split = R-126-01's archetype split, player at least 1), R-218-02 (holding one gives a position and
production, owner mirrors the structure's owner, state 1 held / 0 free), R-218-05 (destroyed -> rubble, state 2,
and it can be refounded; this replaces R-127-03 "never rebuilt"), R-218-06 (no fixed 0.20 / 0.80 force split),
R-218-07 / Q-118-03 (a strongpoint does not drift), K-e getters (ascending ids, shapes, out-of-range, determinism).

SUPERSEDED RULING: tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_04_starting_force_0_20_f
encodes R-126-04's fifth/rest split, retired by R-218-06; tests/csim/test_E15_S127_taking_a_garrison.py (if it
asserts "never rebuilt", R-127-03) is retired by R-218-05. The clerk rules those through a ledger row.

ASSUMPTIONS (none is a number; each is the smallest reading, flagged for the E1h builder): a strongpoint's id equals
its structure slot (so om_structure_get_owner/position(w, id) mirror the row); the strongpoints are created by
om_mission_setup on a ground era (om_set_era_kind 1), the one place structures are placed today; refounding a
rubble strongpoint is om_economy_place(w, building, x, y) at its position returning 0 (E1e's refusals do not
apply to a rubble lot's own footprint), after which its state leaves 2.
Q-168-05 (a base's "existing max") is open: no cap is asserted anywhere.
On main strongpoint.c is a stub: the table is always empty, so every non-control test fails on that.
"""
import ctypes
import math

import pytest

from conftest import (OMArchetype, OMEdge, OMFeature, OMTier, OMVec2,
                      set_edge, set_faction, set_owner, set_region)

W = ctypes.c_void_p
P = ctypes.POINTER
SLOTS = 64
PLAYER, ENEMY = 0, 1
DEFENSIVE_STAND, SIEGE_BREAKING, ASSAULT, SUPPRESSION = 0, 1, 3, 4
STATE_FREE, STATE_HELD, STATE_RUBBLE = 0, 1, 2


class Strongpoint(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("owner", ctypes.c_int32), ("state", ctypes.c_int32)]


class Slope(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double), ("y0", ctypes.c_double), ("x1", ctypes.c_double), ("y1", ctypes.c_double),
                ("mx", ctypes.c_double), ("my", ctypes.c_double), ("length", ctypes.c_double),
                ("lower_band", ctypes.c_int32), ("upper_band", ctypes.c_int32)]


def bind(lib):
    missing = [n for n in ("om_strongpoint_count", "om_strongpoint_get_at", "om_economy_place") if not hasattr(lib, n)]
    assert not missing, f"K-e symbols missing: {missing}"
    lib.om_strongpoint_count.argtypes, lib.om_strongpoint_count.restype = [W], ctypes.c_uint32
    lib.om_strongpoint_get_at.argtypes, lib.om_strongpoint_get_at.restype = [W, ctypes.c_uint32, P(Strongpoint)], ctypes.c_int
    lib.om_economy_place.argtypes, lib.om_economy_place.restype = [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double], ctypes.c_int
    lib.om_terrain_slope_count.argtypes, lib.om_terrain_slope_count.restype = [W], ctypes.c_uint32
    lib.om_terrain_slope_at.argtypes = [W, ctypes.c_double, ctypes.c_double, P(Slope)]
    lib.om_terrain_slope_at.restype = ctypes.c_int
    lib.om_terrain_band_at.argtypes, lib.om_terrain_band_at.restype = [W, ctypes.c_double, ctypes.c_double], ctypes.c_int
    lib.om_set_era_kind.argtypes, lib.om_set_era_kind.restype = [W, ctypes.c_int], ctypes.c_int


def scene(lib, world_factory, archetype=DEFENSIVE_STAND, military=0.0, seed=7, era=1):
    bind(lib)
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_set_era_kind(w, era)
    set_faction(lib, w, PLAYER, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY, held_since=-1)
    set_owner(lib, w, 1, PLAYER, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=military, faction_id=ENEMY)
    lib.om_mission_setup(w, 0, archetype, 0)
    lib.om_mission_begin.argtypes, lib.om_mission_begin.restype = [W], None
    lib.om_mission_begin(w)  # TD-VG-E-5: R-092 recon stops the clock until begin
    return w


def sps(lib, w):
    out = []
    for i in range(lib.om_strongpoint_count(w)):
        s = Strongpoint()
        assert lib.om_strongpoint_get_at(w, i, ctypes.byref(s)) == 0
        out.append((s.id, s.x, s.y, s.owner, s.state))
    return out


def slot_pos(lib, w, slot):
    p = OMVec2()
    lib.om_structure_get_position(w, slot, ctypes.byref(p))
    return p.x, p.y


def expected_count(lib, w, archetype, military):
    cat = lib.om_map_archetype_canvas_category(archetype)
    return lib.om_structure_compute_count(ctypes.c_double(military), cat)


def oracle_split(lib, archetype, total):
    p, e, n = ctypes.c_uint32(), ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_structure_assign_owners(archetype, total, ctypes.byref(p), ctypes.byref(e), ctypes.byref(n))
    return p.value, e.value, n.value


# ---- positive controls (pass on main): each detector can fire ----

def test_control_slope_detector_fires(lib, world_factory):
    """Control: a ground mission has slopes, and om_terrain_slope_at answers >= 0 at a slope's own midpoint
    but a flat-band probe far from every slope answers -1; so 'strongpoint is on a slope' can be true and false."""
    w = scene(lib, world_factory)
    n = lib.om_terrain_slope_count(w)
    assert n > 0, "control setup: a ground mission must have slopes"
    s = Slope()
    assert lib.om_terrain_slope_get(w, 0, ctypes.byref(s)) == 0
    assert lib.om_terrain_slope_at(w, s.mx, s.my, None) >= 0, "control: slope probe misses a slope midpoint"
    assert lib.om_terrain_slope_at(w, -50.0, -50.0, None) < 0, "control: slope probe fires off the map"


def test_control_count_oracle(lib, world_factory):
    """Control: the R-126-01 oracle gives the class minimum at military 0 (medium 3) and the split sums to the count."""
    bind(lib)
    w = scene(lib, world_factory)
    assert expected_count(lib, w, DEFENSIVE_STAND, 0.0) == 3
    p, e, n = oracle_split(lib, DEFENSIVE_STAND, 6)
    assert p + e + n == 6 and p >= 1


def test_control_getter_out_of_range(lib, world_factory):
    """Control: the K-e getter refuses an index past the end (1) and a null out (1) and does not write."""
    w = scene(lib, world_factory)
    s = Strongpoint(id=99, x=-1.0, y=-1.0, owner=-9, state=-9)
    assert lib.om_strongpoint_get_at(w, lib.om_strongpoint_count(w), ctypes.byref(s)) == 1
    assert (s.id, s.owner, s.state) == (99, -9, -9)
    assert lib.om_strongpoint_get_at(w, 0, None) == 1
    assert lib.om_strongpoint_count(None) == 0


# ---- R-218-01: where and how many ----

def test_strongpoints_exist_on_ground_map(lib, world_factory):
    """R-218-01: a ground mission with slopes has strongpoints. Red on main: the table is the K-e empty stub."""
    w = scene(lib, world_factory)
    assert lib.om_strongpoint_count(w) > 0, "no strongpoints placed (csrc/strongpoint.c is a stub)"


def test_every_strongpoint_stands_on_a_slope(lib, world_factory):
    """R-218-01: each strongpoint's point lies on a slope between two height bands (om_terrain_slope_at >= 0)."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    assert rows, "no strongpoints placed"
    for sid, x, y, _o, _s in rows:
        assert lib.om_terrain_slope_at(w, x, y, None) >= 0, f"strongpoint {sid} at ({x},{y}) is not on a slope"


def test_count_is_r126_01_capped_by_slopes(lib, world_factory):
    """R-218-01: count = min(R-126-01 count, slopes there are), for three archetypes and military values."""
    for arch, mil in ((DEFENSIVE_STAND, 0.0), (ASSAULT, 0.0), (SUPPRESSION, 500.0), (ASSAULT, 3000.0)):
        w = scene(lib, world_factory, arch, mil)
        want = min(expected_count(lib, w, arch, mil), lib.om_terrain_slope_count(w))
        assert lib.om_strongpoint_count(w) == want, f"archetype {arch} military {mil}: want {want}"


def test_few_slopes_gives_as_many_as_there_are(lib, world_factory):
    """R-218-01 / R-192-01: never more strongpoints than slopes; ids are distinct and ascending; positions distinct."""
    w = scene(lib, world_factory, ASSAULT, 3000.0)
    rows = sps(lib, w)
    assert rows and len(rows) <= lib.om_terrain_slope_count(w)
    ids = [r[0] for r in rows]
    assert ids == sorted(set(ids)), "ids must be unique and ascending"
    assert len({(r[1], r[2]) for r in rows}) == len(rows), "two strongpoints on one spot"


def test_owner_split_is_the_archetype_split(lib, world_factory):
    """R-218-01 / R-126-01: owners follow om_structure_assign_owners for the placed count; player at least 1."""
    for arch in (DEFENSIVE_STAND, SIEGE_BREAKING, ASSAULT):
        w = scene(lib, world_factory, arch, 0.0)
        rows = sps(lib, w)
        assert rows, "no strongpoints placed"
        p, e, n = oracle_split(lib, arch, len(rows))
        player, enemy = lib.om_player_faction(w), lib.om_mission_get_enemy_faction(w)
        got = (sum(r[3] == player for r in rows), sum(r[3] == enemy for r in rows), sum(r[3] == -1 for r in rows))
        assert got == (p, e, n) and got[0] >= 1, f"archetype {arch}: got {got} want {(p, e, n)}"


def test_space_era_has_no_strongpoints_on_slopes(lib, world_factory):
    """Isolation: a space era (kind 0) has no height bands, hence no slope strongpoints (R-218-01 'land map')."""
    w = scene(lib, world_factory, era=0)
    assert lib.om_strongpoint_count(w) == 0


def test_same_seed_same_table_other_seed_differs(lib, world_factory):
    """Determinism (R-218-01 is seed-driven): the same seed gives the identical table, another seed a different one."""
    a, b = sps(lib, scene(lib, world_factory, seed=7)), sps(lib, scene(lib, world_factory, seed=7))
    c = sps(lib, scene(lib, world_factory, seed=11))
    assert a and a == b, "same seed must give a non-empty identical table"
    assert a != c, "a different seed must move the strongpoints"


# ---- R-218-02: holding gives a position and production ----

def test_owner_and_state_mirror_the_structure(lib, world_factory):
    """R-218-02 / K-e: owner equals the structure's owner (id = slot, assumed); state 1 when held by a faction, 0 free."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    assert rows
    for sid, x, y, owner, state in rows:
        assert lib.om_structure_get_owner(w, sid) == owner
        assert slot_pos(lib, w, sid) == (x, y)
        assert state == (STATE_HELD if owner >= 0 else STATE_FREE)


def test_capture_changes_owner_and_state(lib, world_factory):
    """R-218-02: when a side takes a free strongpoint the row goes held with that owner; control: it was free before."""
    w = scene(lib, world_factory, ASSAULT, 3000.0)
    free = [r for r in sps(lib, w) if r[3] == -1]
    if not free:  # an archetype without neutrals: hand a held one back to neutral first
        sid = sps(lib, w)[0][0]
        lib.om_structure_set_owner(w, sid, -1)
        free = [r for r in sps(lib, w) if r[0] == sid]
    sid = free[0][0]
    assert free[0][4] == STATE_FREE, "control: the strongpoint must read free before capture"
    lib.om_structure_set_owner(w, sid, PLAYER)
    row = [r for r in sps(lib, w) if r[0] == sid][0]
    assert (row[3], row[4]) == (PLAYER, STATE_HELD)


def _advance(lib, w, interval):
    """TD-VG-E-7: om_tactical_step returns before om_support_tick on a unit-less world (csrc/unit.c), so move the clock."""
    lib.om_tactical_tick.argtypes, lib.om_tactical_tick.restype = [W], ctypes.c_uint64
    lib.om_tactical_tick_to.argtypes, lib.om_tactical_tick_to.restype = [W, ctypes.c_uint64], ctypes.c_uint64
    lib.om_tactical_tick_to(w, lib.om_tactical_tick(w) + interval)


def test_held_strongpoint_produces_a_unit(lib, world_factory):
    """R-218-02 / R-218-03: a held strongpoint spawns a unit of its holder's faction within one production interval;
    control: a free (neutral) strongpoint spawns none."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    held = [r for r in rows if r[3] >= 0]
    assert held, "no held strongpoint"
    sid, _x, _y, owner, _s = held[0]
    lib.om_structure_init(w, sid, 0, ctypes.c_double(10.0))
    lib.om_structure_set_owner(w, sid, owner)
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(10.0))
    before = lib.om_unit_count(w)
    _advance(lib, w, interval)
    assert lib.om_unit_count(w) > before, "a held strongpoint produced nothing"
    lib.om_structure_set_owner(w, sid, -1)
    mid = lib.om_unit_count(w)
    _advance(lib, w, interval)
    assert lib.om_unit_count(w) == mid, "control: a free strongpoint must not produce"


# ---- R-218-05: rubble and refounding (replaces R-127-03) ----

def _destroy(lib, w, sid):
    lib.om_structure_apply_damage(w, sid, ctypes.c_double(1.0e9), 0)


def test_destroyed_falls_to_rubble_and_stays_listed(lib, world_factory):
    """R-218-05: at 0 HP the strongpoint stays in the table with state 2 (R-127-03's 'removed' no longer holds)."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    n0 = len(rows)
    assert n0
    sid = rows[0][0]
    assert [r for r in rows if r[0] == sid][0][4] != STATE_RUBBLE, "control: not rubble before the attack"
    _destroy(lib, w, sid)
    after = sps(lib, w)
    assert len(after) == n0, "a destroyed strongpoint must stay in the table"
    assert [r for r in after if r[0] == sid][0][4] == STATE_RUBBLE


def test_rubble_produces_nothing(lib, world_factory):
    """R-218-05 / R-218-02: rubble gives no production."""
    w = scene(lib, world_factory)
    held = [r for r in sps(lib, w) if r[3] >= 0]
    assert held
    sid, _x, _y, owner, _s = held[0]
    lib.om_structure_init(w, sid, 0, ctypes.c_double(10.0))
    lib.om_structure_set_owner(w, sid, owner)
    _destroy(lib, w, sid)
    interval = lib.om_structure_production_interval_ticks(ctypes.c_double(10.0))
    before = lib.om_unit_count(w)
    for _ in range(interval + 1):
        lib.om_tactical_step(w)
    assert lib.om_unit_count(w) == before


def test_rubble_can_be_refounded(lib, world_factory):
    """R-218-05: placing at a rubble strongpoint is accepted and its state leaves rubble (ASSUMED mechanism, header)."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    assert rows
    sid, x, y = rows[0][0], rows[0][1], rows[0][2]
    _destroy(lib, w, sid)
    assert [r for r in sps(lib, w) if r[0] == sid][0][4] == STATE_RUBBLE
    assert lib.om_economy_place(w, 0, x, y) == 0, "refounding a rubble strongpoint was refused"
    row = [r for r in sps(lib, w) if r[0] == sid][0]
    assert row[4] != STATE_RUBBLE, "still rubble after refounding"
    assert row[1:3] == (x, y), "refounding must not move it (R-218-07)"


# ---- R-218-06 / R-218-07 ----

def test_no_fixed_force_split(lib, world_factory):
    """R-218-06: R-126-04's 0.20 starting-force split is dropped, so om_mission_compute_starting_force(F) != 0.20 F."""
    bind(lib)
    lib.om_mission_compute_starting_force.argtypes = [ctypes.c_double, ctypes.c_double]  # (F, share): E7, TD-VG-E-28
    lib.om_mission_compute_starting_force.restype = ctypes.c_double
    # share 0.5, not 0.0: at share 0 the ruled floor is exactly a fifth (DRAFT-e7-floor-knee), 20.0, and the assertion would fail
    # on a correct build; the point of this test is that the split is no longer a fixed 0.20 of F.
    got = lib.om_mission_compute_starting_force(100.0, 0.5)
    assert not math.isclose(got, 20.0, abs_tol=1e-5), "the fixed fifth is still applied (R-126-04 retired by R-218-06)"


def test_strongpoints_do_not_drift(lib, world_factory):
    """R-218-07 / Q-118-03 (a): positions at mission start equal positions after 600 ticks of play, held or not."""
    w = scene(lib, world_factory)
    before = sps(lib, w)
    assert before
    for _ in range(600):
        lib.om_tactical_step(w)
    after = sps(lib, w)
    assert [(r[0], r[1], r[2]) for r in after] == [(r[0], r[1], r[2]) for r in before]


# ---- integration: save round-trip and checksum ----

def test_save_roundtrip_keeps_table_and_checksum(lib, world_factory):
    """Integration: the strongpoint table survives om_save_state_write / om_load_state_read and the full checksum
    changes when the table does (state hashed, K-e)."""
    w = scene(lib, world_factory)
    rows = sps(lib, w)
    assert rows
    lib.om_save_state_size.argtypes, lib.om_save_state_size.restype = [W], ctypes.c_uint32
    lib.om_save_state_write.argtypes, lib.om_save_state_write.restype = [W, P(ctypes.c_uint8), ctypes.c_uint32], None
    lib.om_load_state_read.argtypes, lib.om_load_state_read.restype = [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int
    lib.om_world_checksum_full.argtypes, lib.om_world_checksum_full.restype = [W, P(ctypes.c_uint64), ctypes.c_uint32], ctypes.c_uint64  # TD-VG-E-7
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    h0 = lib.om_world_checksum_full(w, None, 0)
    _destroy(lib, w, rows[0][0])
    assert lib.om_world_checksum_full(w, None, 0) != h0, "checksum does not see a strongpoint going to rubble"
    assert lib.om_load_state_read(w, buf, n) == 0
    assert sps(lib, w) == rows
    assert lib.om_world_checksum_full(w, None, 0) == h0
