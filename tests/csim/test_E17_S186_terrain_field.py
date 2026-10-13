"""E-17 S-186 / R-186-04, R-186-07, E-01 S-200 / R-200-01: the terrain field generator.

Terrain stage 1 spec 2026-10-05, "gen" lane: om_terrain_generate fills a seeded 100 wu
height field; the band array (om_terrain_dump_bands) is byte-identical for a seed across
processes, differs between seeds, holds all five bands (R-200-01), keeps heights in the
relief range, refuses canvases the mapgen grid cannot hold, and replaces any old field.

Relief range: the spec says "peaks 3,000 to 5,000 wu as the mockup". The mockup
(origin/push/proto-land-iter:scenes/mockups/landscape/pass4_terrain.gd) fixes
DRY_LEVEL_WU = 60.0 (lowest dry ground), MIN_RELIEF_DEFAULT = 2500.0 (highest minus
lowest dry ground, line 10) and BENCH_STEP_WU = 300.0; so no height is below 0 and the
highest point lies in [3,000, 5,000].
"""
import ctypes
import hashlib
import json
import pathlib
import subprocess
import sys
import time

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = REPO_ROOT / "libouroboros.so"

SEED_A = 11
SEED_B = 12
CANVAS_BASE = 16000.0
CANVAS_BIG = 24000.0
CANVAS_REFUSED = 32000.0
CELL_WU = 100.0
BAND_COUNT = 5
# Relief range, from the spec table and pass4_terrain.gd (see module docstring).
HEIGHT_FLOOR_WU = 0.0       # mockup DRY_LEVEL_WU = 60.0 is the lowest dry ground
PEAK_LO_WU = 3000.0         # spec: peaks 3,000 to 5,000 wu
PEAK_HI_WU = 5000.0
# Budgets (R-186-07 allows 5 s; spec asks for these, measured).
BUDGET_16K_S = 1.0
BUDGET_24K_S = 2.0

_CHILD = """
import ctypes, hashlib, sys
lib = ctypes.CDLL(sys.argv[1])
W = ctypes.c_void_p
lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]; lib.om_world_new.restype = W
lib.om_map_set_canvas.argtypes = [W, ctypes.c_double, ctypes.c_double]
lib.om_terrain_generate.argtypes = [W, ctypes.c_uint64, ctypes.c_double, ctypes.c_double]
lib.om_terrain_cells.argtypes = [W, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
lib.om_terrain_cells.restype = ctypes.c_uint32
lib.om_terrain_dump_bands.argtypes = [W, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint32]
lib.om_terrain_dump_bands.restype = ctypes.c_uint32
w = lib.om_world_new(1, 1)
c = float(sys.argv[3])
lib.om_map_set_canvas(w, c, c)
rc = lib.om_terrain_generate(w, int(sys.argv[2]), c, c)
cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
n = cw.value * ch.value
buf = (ctypes.c_uint8 * max(n, 1))()
got = lib.om_terrain_dump_bands(w, buf, n)
print(rc, got, hashlib.sha256(bytes(buf)[:got]).hexdigest())
"""


def _child_hash(seed):
    res = subprocess.run([sys.executable, "-c", _CHILD, str(LIB_PATH), str(seed), str(CANVAS_BASE)],
                         capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stderr
    rc, got, digest = res.stdout.split()
    return int(rc), int(got), digest


@pytest.fixture
def mk(lib, world_factory):
    """Fresh world with the mapgen canvas set to a square of side `canvas`."""
    def _mk(canvas=CANVAS_BASE):
        w = world_factory(n_regions=1)
        assert lib.om_map_set_canvas(w, canvas, canvas) == 0
        return w
    return _mk


def _bands(lib, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value * ch.value
    buf = (ctypes.c_uint8 * max(n, 1))()
    got = lib.om_terrain_dump_bands(w, buf, n)
    return cw.value, ch.value, bytes(buf)[:got]


def test_generate_succeeds_and_field_present(lib, mk):
    w = mk()
    assert lib.om_terrain_present(w) == 0
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    assert lib.om_terrain_present(w) == 1
    cw, ch, data = _bands(lib, w)
    assert (cw, ch) == (int(CANVAS_BASE / CELL_WU),) * 2
    assert len(data) == cw * ch


def test_band_array_identical_across_two_processes():
    first, second = _child_hash(SEED_A), _child_hash(SEED_A)
    assert first[0] == 0, f"generate returned {first[0]} in the child"
    assert first[1] > 0, "empty band dump"
    assert first == second


def test_different_seeds_differ(lib, mk):
    wa, wb = mk(), mk()
    assert lib.om_terrain_generate(wa, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    assert lib.om_terrain_generate(wb, SEED_B, CANVAS_BASE, CANVAS_BASE) == 0
    a, b = _bands(lib, wa)[2], _bands(lib, wb)[2]
    assert a and b and a != b


def test_R_200_01_every_band_has_ground(lib, mk):
    w = mk()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    data = _bands(lib, w)[2]
    assert data, "empty band dump"
    present = set(data)
    assert present <= set(range(1, BAND_COUNT + 1)), sorted(present)
    for band in range(1, BAND_COUNT + 1):
        assert band in present, f"band {band} nowhere in the field"


def test_heights_inside_relief_range(lib, mk):
    w = mk()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    cw, ch, data = _bands(lib, w)
    assert data, "empty field"
    hs = [lib.om_terrain_height_at(w, (cx + 0.5) * CELL_WU, (cy + 0.5) * CELL_WU)
          for cy in range(ch) for cx in range(cw)]
    assert min(hs) >= HEIGHT_FLOOR_WU, min(hs)
    assert PEAK_LO_WU <= max(hs) <= PEAK_HI_WU, max(hs)
    assert lib.om_terrain_height_at(w, -1.0, -1.0) == 0.0
    assert lib.om_terrain_height_at(w, CANVAS_BASE + 1.0, 0.0) == 0.0


def test_band_heights_five_increasing_floors(lib, mk):
    w = mk()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    out = (ctypes.c_double * BAND_COUNT)()
    n = lib.om_terrain_band_heights(w, out, BAND_COUNT)
    assert n == BAND_COUNT
    floors = list(out)
    assert all(floors[i] < floors[i + 1] for i in range(BAND_COUNT - 1)), floors


def test_oversize_canvas_refused_and_field_untouched(lib, mk):
    w = mk(CANVAS_BASE)
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    before = _bands(lib, w)
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_REFUSED, CANVAS_REFUSED) != 0
    assert lib.om_terrain_present(w) == 1
    assert _bands(lib, w) == before
    fresh = mk(CANVAS_BASE)
    assert lib.om_terrain_generate(fresh, SEED_A, CANVAS_REFUSED, CANVAS_REFUSED) != 0
    assert lib.om_terrain_present(fresh) == 0


def test_generate_twice_replaces_the_field(lib, mk):
    w, ref = mk(), mk()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS_BASE, CANVAS_BASE) == 0
    assert lib.om_terrain_generate(w, SEED_B, CANVAS_BASE, CANVAS_BASE) == 0
    assert lib.om_terrain_generate(ref, SEED_B, CANVAS_BASE, CANVAS_BASE) == 0
    got, want = _bands(lib, w)[2], _bands(lib, ref)[2]
    assert got and got == want


# budget test (measured, not a correctness check)
@pytest.mark.parametrize("canvas,limit", [(CANVAS_BASE, BUDGET_16K_S), (CANVAS_BIG, BUDGET_24K_S)])
def test_generation_time_budget(lib, mk, canvas, limit):
    w = mk(canvas)
    t0 = time.perf_counter()
    rc = lib.om_terrain_generate(w, SEED_A, canvas, canvas)
    dt = time.perf_counter() - t0
    assert rc == 0, f"generate refused {canvas}"
    assert lib.om_terrain_present(w) == 1
    assert dt < limit, f"{canvas:.0f} wu took {dt:.3f} s, budget {limit} s"
