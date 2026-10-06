"""E-17 S-190: the walk mask (terrain stage 2, spec 2026-10-06, "mask" lane).

om_terrain_walk_mask(w, layer, out, cap): one byte per cell, 1 where a walker may stand on that engine
layer: (cell band == layer + 1 AND walkable) OR (the cell is in a slope's run, one of whose bands is
layer + 1, AND walkable). A slope's run is the bounding box of its two endpoint cells. The expected
mask is rebuilt here from om_terrain_band_at, om_terrain_walkable_at and the slope list
(om_terrain_slope_count / om_terrain_slope_get), not from om_terrain_ground_at.
om_terrain_slope_at: the lowest-index slope whose run contains the cell and whose bands match the
cell's band, else -1.

Seed 11, canvas 16,000 (160 x 160 cells, 60 slopes). Sampled cells are drawn by a fixed-seed generator
(SAMPLE_RNG_SEED): half uniformly over the map, half from slope runs, so slope cells are exercised.
Cells picked: the 200 sampled cells are a pure function of SAMPLE_RNG_SEED (first uniform cell is
printed in a failure message); the both-layers test walks every slope run, so it picks no single cell.
"""
import ctypes
import random

import pytest

SEED = 11
CANVAS = 16000.0
CELL_WU = 100.0
N_CELLS = 160
LAYERS = 5
SAMPLES_UNIFORM = 100         # provisional (2026-10-06); 200 sampled cells in all
SAMPLES_SLOPE = 100           # provisional (2026-10-06)
SAMPLE_RNG_SEED = 20261006    # provisional (2026-10-06)


@pytest.fixture
def mk(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


def _slopes(lib, w, om_slope):
    out = []
    for i in range(lib.om_terrain_slope_count(w)):
        s = om_slope()
        assert lib.om_terrain_slope_get(w, i, ctypes.byref(s)) == 0
        out.append(s)
    return out


def _runs(slopes):
    """Per slope: (cx_lo, cx_hi, cy_lo, cy_hi), the bounding box of its two endpoint cells."""
    runs = []
    for s in slopes:
        ax, bx = int(s.x0 // CELL_WU), int(s.x1 // CELL_WU)
        ay, by = int(s.y0 // CELL_WU), int(s.y1 // CELL_WU)
        runs.append((min(ax, bx), max(ax, bx), min(ay, by), max(ay, by)))
    return runs


def _masks(lib, w):
    out = []
    for layer in range(LAYERS):
        buf = (ctypes.c_uint8 * (N_CELLS * N_CELLS))()
        assert lib.om_terrain_walk_mask(w, layer, buf, N_CELLS * N_CELLS) == N_CELLS * N_CELLS
        out.append(buf)
    return out


def _centre(cx, cy):
    return (cx + 0.5) * CELL_WU, (cy + 0.5) * CELL_WU


def _sample(runs):
    rng = random.Random(SAMPLE_RNG_SEED)
    cells = [(rng.randrange(N_CELLS), rng.randrange(N_CELLS)) for _ in range(SAMPLES_UNIFORM)]
    for _ in range(SAMPLES_SLOPE):
        x0, x1, y0, y1 = runs[rng.randrange(len(runs))]
        cells.append((rng.randint(x0, x1), rng.randint(y0, y1)))
    return cells


def _expected(lib, w, runs, slopes, layer, cx, cy):
    x, y = _centre(cx, cy)
    if not lib.om_terrain_walkable_at(w, x, y):
        return 0
    if lib.om_terrain_band_at(w, x, y) == layer + 1:
        return 1
    for r, s in zip(runs, slopes):
        if r[0] <= cx <= r[1] and r[2] <= cy <= r[3] and layer + 1 in (s.lower_band, s.upper_band):
            return 1
    return 0


@pytest.fixture
def om_slope():
    import conftest
    return conftest.OMSlope


def test_S_190_count_only_returns_the_cell_count(lib, mk):
    assert lib.om_terrain_walk_mask(mk, 0, None, 0) == N_CELLS * N_CELLS


def test_S_190_mask_matches_band_walkable_and_slopes_at_200_cells(lib, mk, om_slope):
    slopes = _slopes(lib, mk, om_slope)
    assert len(slopes) > 0
    runs = _runs(slopes)
    masks = _masks(lib, mk)
    cells = _sample(runs)
    assert len(cells) == SAMPLES_UNIFORM + SAMPLES_SLOPE
    ones = 0
    for cx, cy in cells:
        for layer in range(LAYERS):
            want = _expected(lib, mk, runs, slopes, layer, cx, cy)
            got = masks[layer][cy * N_CELLS + cx]
            assert got == want, f"layer {layer} cell ({cx},{cy}): mask {got}, expected {want}"
            ones += want
    # positive control: the sample reaches walkable cells, so an all-zero mask cannot pass
    assert ones > len(cells) // 2


def test_S_190_a_slope_cells_run_is_in_both_layers_masks(lib, mk, om_slope):
    slopes = _slopes(lib, mk, om_slope)
    runs = _runs(slopes)
    masks = _masks(lib, mk)
    both = 0
    for i, (s, (x0, x1, y0, y1)) in enumerate(zip(slopes, runs)):
        lo, hi = s.lower_band - 1, s.upper_band - 1
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                x, y = _centre(cx, cy)
                if not lib.om_terrain_walkable_at(mk, x, y):
                    continue
                assert masks[lo][cy * N_CELLS + cx] == 1, f"slope {i} cell ({cx},{cy}) missing from layer {lo}"
                assert masks[hi][cy * N_CELLS + cx] == 1, f"slope {i} cell ({cx},{cy}) missing from layer {hi}"
                both += 1
    assert both > 0, "no walkable slope cell found; the test would prove nothing"


def test_S_190_slope_at_is_the_lowest_matching_slope_or_minus_one(lib, mk, om_slope):
    slopes = _slopes(lib, mk, om_slope)
    runs = _runs(slopes)
    hit = 0
    for cx, cy in _sample(runs):
        x, y = _centre(cx, cy)
        band = lib.om_terrain_band_at(mk, x, y)
        want = -1
        for i, (r, s) in enumerate(zip(runs, slopes)):
            if r[0] <= cx <= r[1] and r[2] <= cy <= r[3] and band in (s.lower_band, s.upper_band):
                want = i
                break
        out = om_slope()
        got = lib.om_terrain_slope_at(mk, x, y, ctypes.byref(out))
        assert got == want, f"cell ({cx},{cy}) band {band}: slope_at {got}, expected {want}"
        if want >= 0:
            hit += 1
            assert (out.lower_band, out.upper_band) == (slopes[want].lower_band, slopes[want].upper_band)
            assert out.length == slopes[want].length
    assert hit > 0, "no sampled cell sits on a slope; the test would prove nothing"
