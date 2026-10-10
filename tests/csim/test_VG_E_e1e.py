"""Visible-game lane E1, piece E1e: free placement on terrain (spec 2026-10-07 rev 6, lane E1; R-168-01, R-193-03;
register Q-168-01 c free placement on terrain). Fenced: builders never edit this file.

Rule proved: om_economy_place(w, building, x, y) claims a 5x5 cell footprint (PLAYER_HALF 2, mockup
scenes/mockups/settlement/settlement_sim.gd, 100 wu cells) centred on the cell holding (x, y). It returns 0 and the world
gains a lot with that building id inside the footprint; it returns nonzero (and changes nothing) when any footprint cell is
unwalkable (om_terrain_walkable_at) or already claimed by an earlier placement. The 2-cell refill ring around the footprint
(REFILL_RING 2, R-193-03) is ring only: ring cells need not be walkable and do not block placement.

NOT asserted: any cap on buildings (Q-168-05 "the existing max on a base" is OPEN; E1 enforces none, flagged here, so a
test that placed many buildings expecting a refusal would be a guess); the refill timing or stage of ring lots (no
number given; E1d owns stages/rubble); owner of the new lot; the building set (E1f).
Red on main: om_economy_place is the K-e stub and returns 0 for everything, so every refusal test fails with
"stub accepted ...". Controls (accept cases, isolation/ring cases) pass on the stub or fail only for the lot reason.
"""
import ctypes

import pytest

W = ctypes.c_void_p
SEED = 11
CANVAS = 16000.0
CELL = 100.0
HALF = 2
RING = 2
BUILDING = 3


class Lot(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("stage", ctypes.c_int32), ("building", ctypes.c_int32), ("owner", ctypes.c_int32)]


@pytest.fixture
def mk(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    lib.om_terrain_walkable_at.argtypes = [W, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_walkable_at.restype = ctypes.c_int
    lib.om_economy_place.argtypes = [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double]
    lib.om_economy_place.restype = ctypes.c_int
    lib.om_lot_count.argtypes, lib.om_lot_count.restype = [W], ctypes.c_uint32
    lib.om_lot_get_at.argtypes, lib.om_lot_get_at.restype = [W, ctypes.c_uint32, ctypes.POINTER(Lot)], ctypes.c_int
    return w


def centre(cx, cy):
    return (cx + 0.5) * CELL, (cy + 0.5) * CELL


def walk(lib, w, cx, cy):
    x, y = centre(cx, cy)
    return lib.om_terrain_walkable_at(w, x, y) == 1


def foot_ok(lib, w, cx, cy):
    return all(walk(lib, w, cx + dx, cy + dy) for dx in range(-HALF, HALF + 1) for dy in range(-HALF, HALF + 1))


def find_free(lib, w, near=(80, 80), skip=()):
    """First centre cell scanning outward in rows from `near` whose whole 5x5 footprint is walkable and clear of `skip`."""
    for cy in range(near[1], 150):
        for cx in range(near[0], 150):
            if (cx, cy) not in skip and foot_ok(lib, w, cx, cy):
                return cx, cy
    raise AssertionError("control: no fully walkable 5x5 footprint on seed 11")


def find_blocked(lib, w):
    """A centre cell whose footprint holds an unwalkable cell but whose own centre cell is walkable."""
    for cy in range(10, 150):
        for cx in range(10, 150):
            if walk(lib, w, cx, cy) and not foot_ok(lib, w, cx, cy):
                return cx, cy
    raise AssertionError("control: seed 11 has no footprint with an unwalkable cell")


def lots(lib, w):
    out = []
    for i in range(lib.om_lot_count(w)):
        lot = Lot()
        assert lib.om_lot_get_at(w, i, ctypes.byref(lot)) == 0
        out.append(lot)
    return out


def place(lib, w, c, b=BUILDING):
    x, y = centre(*c)
    return lib.om_economy_place(w, b, x, y)


def test_control_walkable_footprint_is_accepted(lib, mk):
    """Control (positive for every refusal below): a fully walkable, empty 5x5 is accepted."""
    c = find_free(lib, mk)
    assert place(lib, mk, c) == 0


def test_accepted_placement_creates_a_lot_in_the_footprint(lib, mk):
    """R-168-01: the placed building claims its footprint: a lot with its building id lies inside the 5x5."""
    c = find_free(lib, mk)
    before = len(lots(lib, mk))
    assert place(lib, mk, c) == 0
    new = lots(lib, mk)[before:]
    mine = [l for l in new if l.building == BUILDING]
    assert mine, f"R-168-01: accepted placement made no lot with building {BUILDING} (new lots: {len(new)})"
    cx0, cy0 = centre(*c)
    for l in mine:
        assert abs(l.x - cx0) <= (HALF + 0.5) * CELL and abs(l.y - cy0) <= (HALF + 0.5) * CELL


def test_unwalkable_footprint_cell_is_refused(lib, mk):
    """Q-168-01 c: a footprint touching an unwalkable cell is refused. Red on main: stub accepted."""
    c = find_blocked(lib, mk)
    assert place(lib, mk, c) != 0, "stub accepted a footprint that holds an unwalkable cell"


def test_refused_placement_changes_nothing(lib, mk):
    c = find_blocked(lib, mk)
    before = len(lots(lib, mk))
    place(lib, mk, c)
    assert len(lots(lib, mk)) == before, "a refused placement must leave the lot table unchanged"


def test_same_spot_twice_is_refused(lib, mk):
    """Occupied: the second placement on the same footprint is refused."""
    c = find_free(lib, mk)
    assert place(lib, mk, c) == 0
    assert place(lib, mk, c) != 0, "stub accepted a footprint already claimed"


def test_overlapping_footprint_is_refused(lib, mk):
    """Occupied: a footprint sharing even one cell (centres 4 apart share a column) is refused."""
    c = find_free(lib, mk)
    assert place(lib, mk, c) == 0
    n = (c[0] + 2 * HALF, c[1])
    assert foot_ok(lib, mk, *n), "control: overlap neighbour must itself be walkable"
    assert place(lib, mk, n) != 0, "stub accepted a footprint sharing a cell with a claimed one"


def test_adjacent_footprint_is_accepted(lib, mk):
    """Positive control for the occupied detector: centres 5 apart (edge-adjacent, no shared cell) are accepted, so the
    refusal above is about shared cells, not proximity. The 2-cell refill ring does not block (R-193-03: ring only)."""
    c = find_free(lib, mk)
    assert place(lib, mk, c) == 0
    n = (c[0] + 2 * HALF + 1, c[1])
    if not foot_ok(lib, mk, *n):
        n = find_free(lib, mk, near=(c[0] + 2 * HALF + 1, c[1]), skip={c})
        assert abs(n[0] - c[0]) >= 2 * HALF + 1 or abs(n[1] - c[1]) >= 2 * HALF + 1, "control: no clear neighbour"
    assert place(lib, mk, n) == 0


def test_ring_cell_unwalkable_does_not_block(lib, mk):
    """Isolation of the ring rule: only footprint cells are checked. Find a centre whose 5x5 is walkable but whose 9x9
    (footprint + 2 ring) is not: it is accepted."""
    r = HALF + RING
    for cy in range(10, 150):
        for cx in range(10, 150):
            if foot_ok(lib, mk, cx, cy) and not all(walk(lib, mk, cx + dx, cy + dy)
                                                    for dx in range(-r, r + 1) for dy in range(-r, r + 1)):
                assert place(lib, mk, (cx, cy)) == 0, "a ring cell blocked placement; only footprint cells may"
                return
    pytest.skip("seed 11 has no footprint with an unwalkable ring only")


def test_no_cap_enforced_q_168_05_open(lib, mk):
    """Q-168-05 (the 'existing max' on a base) is OPEN: E1 enforces no cap. Three disjoint placements are all accepted.
    Flagged, not a threshold: do not tighten this to a number until Westley answers."""
    placed = []
    spot = (20, 20)
    for _ in range(3):
        c = find_free(lib, mk, near=spot, skip=set(placed))
        if placed and any(abs(c[0] - p[0]) < 2 * HALF + 1 and abs(c[1] - p[1]) < 2 * HALF + 1 for p in placed):
            spot = (c[0] + 2 * HALF + 1, c[1])
            c = find_free(lib, mk, near=spot)
        assert place(lib, mk, c) == 0
        placed.append(c)
        spot = (c[0] + 2 * HALF + 1, c[1])


def test_placement_is_deterministic(lib, world_factory):
    """Determinism: two worlds, same seed, same placement -> same lot table."""
    rows = []
    for _ in range(2):
        w = world_factory(n_regions=1)
        assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
        assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
        lib.om_terrain_walkable_at.argtypes = [W, ctypes.c_double, ctypes.c_double]
        lib.om_terrain_walkable_at.restype = ctypes.c_int
        lib.om_economy_place.argtypes = [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double]
        lib.om_economy_place.restype = ctypes.c_int
        lib.om_lot_count.argtypes, lib.om_lot_count.restype = [W], ctypes.c_uint32
        lib.om_lot_get_at.argtypes, lib.om_lot_get_at.restype = [W, ctypes.c_uint32, ctypes.POINTER(Lot)], ctypes.c_int
        c = find_free(lib, w)
        assert place(lib, w, c) == 0
        rows.append([(l.id, l.x, l.y, l.stage, l.building, l.owner) for l in lots(lib, w)])
    assert rows[0] == rows[1]
    assert rows[0], "R-168-01: a placement left the lot table empty"
