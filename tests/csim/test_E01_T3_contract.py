"""E-01 terrain stage 3, contract piece (spec 2026-10-06-terrain-stage3-spec.md rev 3, piece "3-contract").

Proves: om_terrain_nearest_walkable (ring search, lowest index on a tie, -1 when none, identity with no
terrain); om_terrain_clear (then om_terrain_present is 0); save format 7 carries era_kind and the
movement-kind table (a saved ground world loads with om_era_kind 1 and the same kinds).
Version-pin tests are NOT here; the contract builder updates them under ledger row TD-SAVE-7.

Both new functions are bound locally (conftest has no bindings); on main they are missing symbols and every
test fails there with AttributeError on the missing symbol. The save test fails on the version word (main
writes 6). NOTE: on main era_kind (fog section) and the movement kinds already round-trip through save, so
the round-trip asserts after the version check pass today; the spec's "era_kind is not saved" premise is
stale on this base.

Cells picked: the steep sample is the first unwalkable cell in row-major order; the tie scene is the first
unwalkable cell (row-major) with two or more equally near walkable cells (squared cell-centre distance);
the expected snap is the lowest cell index (cy * 160 + cx) among the nearest. The -1 probe uses NaN
coordinates (a generated field always has a dry cell, so "none" is otherwise unreachable): provisional,
flagged in the report as a contract reading.
"""
import ctypes
import math

import pytest

SEED = 11
CANVAS = 16000.0
CELL = 100.0
N = 160
MOVE_FLYING, MOVE_WALKING = 0, 1
TYPE_A, TYPE_B = 2, 4   # vanguard, bombard (csrc/unit.c OM_UT_*); two custom kinds, both walking


def _bind(lib):
    P = ctypes.POINTER
    V = ctypes.c_void_p
    f = lib.om_terrain_nearest_walkable   # missing symbol: AttributeError on main
    f.argtypes = [V, ctypes.c_double, ctypes.c_double, P(ctypes.c_double), P(ctypes.c_double)]
    f.restype = ctypes.c_int
    c = lib.om_terrain_clear
    c.argtypes = [V]
    c.restype = None
    return f, c


@pytest.fixture
def ground(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


def _walk_grid(lib, w):
    g = [[bool(lib.om_terrain_walkable_at(w, (cx + .5) * CELL, (cy + .5) * CELL)) for cx in range(N)] for cy in range(N)]
    return g


def _expected(g, cx, cy):
    best = None
    for y in range(N):
        for x in range(N):
            if g[y][x]:
                d = (x - cx) ** 2 + (y - cy) ** 2
                if best is None or d < best[0]:   # row-major scan: first strictly smaller wins = lowest index on a tie
                    best = (d, x, y)
    return best


def _steep_cell(g):
    for y in range(N):
        for x in range(N):
            if not g[y][x]:
                return x, y
    return None


def test_steep_point_snaps_to_nearest_walkable(lib, ground):
    near, _ = _bind(lib)
    g = _walk_grid(lib, ground)
    cell = _steep_cell(g)
    assert cell is not None, "seed 11 has no unwalkable cell; scene pick failed"
    cx, cy = cell
    d, ex, ey = _expected(g, cx, cy)
    ox, oy = ctypes.c_double(), ctypes.c_double()
    assert near(ground, (cx + .5) * CELL, (cy + .5) * CELL, ctypes.byref(ox), ctypes.byref(oy)) == 0
    assert (int(ox.value // CELL), int(oy.value // CELL)) == (ex, ey), (cell, (ox.value, oy.value), (ex, ey))
    assert lib.om_terrain_walkable_at(ground, ox.value, oy.value) == 1


def test_tie_takes_lowest_index(lib, ground):
    near, _ = _bind(lib)
    g = _walk_grid(lib, ground)
    # an unwalkable cell with at least two walkable cells at the minimal distance
    for cy in range(N):
        for cx in range(N):
            if g[cy][cx]:
                continue
            d = _expected(g, cx, cy)[0]
            ties = [(y * N + x) for y in range(N) for x in range(N) if g[y][x] and (x - cx) ** 2 + (y - cy) ** 2 == d]
            if len(ties) >= 2:
                ox, oy = ctypes.c_double(), ctypes.c_double()
                assert near(ground, (cx + .5) * CELL, (cy + .5) * CELL, ctypes.byref(ox), ctypes.byref(oy)) == 0
                got = int(oy.value // CELL) * N + int(ox.value // CELL)
                assert got == min(ties), f"tie at cell ({cx},{cy}): got index {got}, ties {ties}"
                return
    pytest.fail("no tie scene on seed 11; scene pick failed")


def test_walkable_point_unchanged(lib, ground):
    near, _ = _bind(lib)
    g = _walk_grid(lib, ground)
    cx, cy = next((x, y) for y in range(N) for x in range(N) if g[y][x])
    x, y = (cx + .5) * CELL + 13.0, (cy + .5) * CELL - 7.0
    ox, oy = ctypes.c_double(), ctypes.c_double()
    assert near(ground, x, y, ctypes.byref(ox), ctypes.byref(oy)) == 0
    assert (ox.value, oy.value) == (x, y)


def test_minus_one_when_nothing_walkable(lib, world_factory):
    near, _ = _bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    ox, oy = ctypes.c_double(-1.0), ctypes.c_double(-1.0)
    # NaN input has no nearest cell: -1, outputs untouched
    assert near(w, float("nan"), float("nan"), ctypes.byref(ox), ctypes.byref(oy)) == -1
    assert (ox.value, oy.value) == (-1.0, -1.0)


def test_identity_without_terrain(lib, world_factory):
    near, _ = _bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_terrain_present(w) == 0
    ox, oy = ctypes.c_double(), ctypes.c_double()
    assert near(w, 1234.5, 6789.25, ctypes.byref(ox), ctypes.byref(oy)) == 0
    assert (ox.value, oy.value) == (1234.5, 6789.25)


def test_clear_then_not_present(lib, ground):
    _, clear = _bind(lib)
    assert lib.om_terrain_present(ground) == 1
    clear(ground)
    assert lib.om_terrain_present(ground) == 0


def _save(lib, w):
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return buf, n


def test_save_round_trip_keeps_era_kind_and_movement_kinds(lib, world_factory):
    P = ctypes.POINTER
    V = ctypes.c_void_p
    lib.om_save_state_size.argtypes = [V]; lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]; lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]; lib.om_load_state_read.restype = ctypes.c_int
    src = world_factory(n_regions=1)
    assert lib.om_set_era_kind(src, 1) == 0
    assert lib.om_roster_set_movement_kind(src, TYPE_A, MOVE_WALKING) == 0
    assert lib.om_roster_set_movement_kind(src, TYPE_B, MOVE_WALKING) == 0
    buf, n = _save(lib, src)
    assert int.from_bytes(bytes(buf[4:8]), "little") == 12, "K-e5 bumps OM_SAVE_FORMAT_VERSION to 10 (TD-VG-E-16); W2 bumps it to 11 (TD-VG-W-1); E7 bumps it to 12 (TD-VG-E-27)"
    dst = world_factory(n_regions=1)
    assert lib.om_era_kind(dst) == 0   # control: a fresh world is space, kinds default flying
    assert lib.om_unit_profile_movement_kind(dst, TYPE_A) == MOVE_FLYING
    assert lib.om_load_state_read(dst, buf, n) == 0
    assert lib.om_era_kind(dst) == 1, "era_kind not saved: a loaded ground mission reverts to space"
    assert lib.om_unit_profile_movement_kind(dst, TYPE_A) == MOVE_WALKING
    assert lib.om_unit_profile_movement_kind(dst, TYPE_B) == MOVE_WALKING
    other = next(t for t in range(6) if t not in (TYPE_A, TYPE_B))
    assert lib.om_unit_profile_movement_kind(dst, other) == MOVE_FLYING
