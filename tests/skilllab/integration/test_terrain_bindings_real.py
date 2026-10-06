# spec: terrain stage 1, lab lane - terrain_generate, band/walkable readers, dump, and blocked bits on movement (R-200-01, R-200-02)
"""Each test fails with 'engine wrapper has no <name>' until scripts/skilllab/engine.py binds it.

Wrapper names (world handle first): terrain_generate(w, seed, canvas) -> int (0 = ok; square canvas),
terrain_band_at(w, x, y) -> int, terrain_walkable_at(w, x, y) -> bool, terrain_dump_bands(w) -> (cells_w, cells_h, bytes)
row-major, index cy * cells_w + cx; cells are 100 wu.
"""
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402

SEED, CANVAS, CELL = 11, 16000.0, 100.0


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


@pytest.fixture
def world(lib):
    w = lib.new_world(0)
    yield w
    lib.free_world(w)


def _need(lib, *names):
    for n in names:
        assert hasattr(lib, n), "engine wrapper has no %s" % n


def _centre(cx, cy):
    return (cx + 0.5) * CELL, (cy + 0.5) * CELL


def test_1_generate_returns_zero_and_dump_is_the_grid(lib, world):
    _need(lib, "terrain_generate", "terrain_dump_bands")
    assert lib.terrain_generate(world, SEED, CANVAS) == 0
    cw, ch, bands = lib.terrain_dump_bands(world)
    assert cw == ch == int(CANVAS / CELL) and len(bands) == cw * ch
    assert set(bands) <= {1, 2, 3, 4, 5} and len(set(bands)) == 5, "every band has ground (R-200-01)"


def test_2_band_and_walkable_agree_with_the_dump_at_50_cells(lib, world):
    _need(lib, "terrain_generate", "terrain_band_at", "terrain_walkable_at", "terrain_dump_bands")
    assert lib.terrain_generate(world, SEED, CANVAS) == 0
    cw, ch, bands = lib.terrain_dump_bands(world)
    rng = random.Random(5)
    walk = 0
    for _ in range(50):
        cx, cy = rng.randrange(cw), rng.randrange(ch)
        x, y = _centre(cx, cy)
        assert lib.terrain_band_at(world, x, y) == bands[cy * cw + cx]
        wk = lib.terrain_walkable_at(world, x, y)
        assert wk in (True, False)
        walk += wk
    assert walk > 0, "control: some sampled cells are walkable"


def _find_pair(bands, cw, ch):
    """A band-1 cell and a band >= 3 cell about 1000 to 1500 wu apart (10 to 15 cells along a row)."""
    for cy in range(2, ch - 2):
        for cx in range(2, cw - 20):
            for d in range(10, 16):
                if bands[cy * cw + cx] == 1 and bands[cy * cw + cx + d] >= 3:
                    return (cx, cy), (cx + d, cy)
    raise AssertionError("no band-1 to band-3+ pair on seed %d" % SEED)


def _walk(lib, w, layer, start, goal):
    # ROUTE_ACROSS_LAYERS is on by default: an order into ground blocked on the unit's layer makes it climb to an
    # open layer and stay there (layer 0 -> 2 for band 3), which is correct play but not what this test measures.
    # Off, the unit must stop at the edge on its own layer.
    lib.set_param(w, lib.param_id("OM_TP_ROUTE_ACROSS_LAYERS"), 0.0)
    u = lib.spawn(w, lib.type_id("Vanguard"), 0, *_centre(*start), layer)
    gx, gy = _centre(*goal)
    lib.order_move(w, [u], gx, gy)
    for _ in range(600):
        lib.step(w)
    ux, uy = lib.unit_pos(w, u)
    assert lib.unit_layer(w, u) == layer, "unit stayed on its layer"
    cw, _, bands = lib.terrain_dump_bands(w)
    assert layer >= bands[int(uy // CELL) * cw + int(ux // CELL)] - 1, "unit stands in a cell open on its layer (R-200-02)"
    return ((ux - gx) ** 2 + (uy - gy) ** 2) ** 0.5


def test_3_layer_0_cannot_enter_band_3_but_layer_4_can(lib):
    _need(lib, "terrain_generate", "terrain_dump_bands")
    dist = {}
    for layer in (0, 4):
        w = lib.new_world(0)
        try:
            assert lib.terrain_generate(w, SEED, CANVAS) == 0
            cw, ch, bands = lib.terrain_dump_bands(w)
            start, goal = _find_pair(bands, cw, ch)
            dist[layer] = _walk(lib, w, layer, start, goal)
        finally:
            lib.free_world(w)
    assert dist[4] < 100.0, "control: on layer 4 the same order arrives (%.0f wu short)" % dist[4]
    assert dist[0] > 100.0, "layer 0 must not arrive in a band-3+ cell (%.0f wu short)" % dist[0]


def test_4_same_seed_twice_identical_dumps(lib):
    _need(lib, "terrain_generate", "terrain_dump_bands")
    dumps = []
    for _ in range(2):
        w = lib.new_world(0)
        try:
            assert lib.terrain_generate(w, SEED, CANVAS) == 0
            dumps.append(lib.terrain_dump_bands(w))
        finally:
            lib.free_world(w)
    assert dumps[0] == dumps[1]
    w = lib.new_world(0)
    try:
        assert lib.terrain_generate(w, SEED + 1, CANVAS) == 0
        assert lib.terrain_dump_bands(w) != dumps[0], "control: another seed differs"
    finally:
        lib.free_world(w)
