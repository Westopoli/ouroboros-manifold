"""E-01 S-200 / R-200-01, R-200-02: the ground is the layers.

Terrain stage 1 spec 2026-10-05, "query" lane. After om_terrain_generate, at any position whose
ground falls in band k (1 to 5): the ground flag (om_terrain_ground_at) is set on that band's
layer and on no other, except on a slope cell where it is set on both bands the slope joins;
layers below the band are blocked (read through om_map_sample_layer_accessibility, which reads
the mapgen blocked bits); the band's layer and the layers above it are open (nothing else blocks
in these worlds). Before generate nothing is blocked; a second generate with another seed
rewrites the bits to match the new bands.

Layer numbering: the mapgen blocked bits and om_map_sample_layer_accessibility use engine layers
0 to OM_LAYER_COUNT - 1 (bible layer n is engine layer n - 1, csrc/ouroboros_sim.h line 31).
The spec does not say which numbering om_terrain_ground_at takes; these tests assume the same
engine layers (band k is engine layer k - 1). Flagged in the report.
"""
import ctypes
import random

import pytest

SEED_A = 11
SEED_B = 12
CANVAS = 16000.0
CELL_WU = 100.0
SAMPLES = 200
SAMPLE_RNG_SEED = 20261005  # provisional (2026-10-05)
LAYERS = 5
SLOPE_PAD_WU = 200.0         # provisional (2026-10-05): a slope cell is within this of its edges' box
MIN_SINGLE_SHARE = 0.5       # provisional (2026-10-05): most positions are not slope cells


class _Slope(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double), ("y0", ctypes.c_double), ("x1", ctypes.c_double),
                ("y1", ctypes.c_double), ("mx", ctypes.c_double), ("my", ctypes.c_double),
                ("length", ctypes.c_double), ("lower_band", ctypes.c_int32),
                ("upper_band", ctypes.c_int32)]


@pytest.fixture
def mk(lib, world_factory):
    def _mk():
        w = world_factory(n_regions=1)
        assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
        return w
    return _mk


def _positions():
    rng = random.Random(SAMPLE_RNG_SEED)
    n = int(CANVAS / CELL_WU)
    return [((rng.randrange(n) + 0.5) * CELL_WU, (rng.randrange(n) + 0.5) * CELL_WU)
            for _ in range(SAMPLES)]


def _open(lib, w, x, y, layer):
    return lib.om_map_sample_layer_accessibility(w, x, y, layer)


def _slopes(lib, w):
    out = []
    for i in range(lib.om_terrain_slope_count(w)):
        s = _Slope()
        assert lib.om_terrain_slope_get(w, i, ctypes.byref(s)) == 0
        out.append(s)
    return out


def _near_slope(slopes, x, y, lo_band, hi_band):
    for s in slopes:
        if s.lower_band == lo_band and s.upper_band == hi_band:
            if (min(s.x0, s.x1) - SLOPE_PAD_WU <= x <= max(s.x0, s.x1) + SLOPE_PAD_WU
                    and min(s.y0, s.y1) - SLOPE_PAD_WU <= y <= max(s.y0, s.y1) + SLOPE_PAD_WU):
                return True
    return False


def _check_world(lib, w, positions):
    """R-200-02 at every position; returns (count blocked cells seen, count single-ground cells)."""
    slopes = _slopes(lib, w)
    blocked_seen = singles = 0
    for x, y in positions:
        band = lib.om_terrain_band_at(w, x, y)
        assert 1 <= band <= LAYERS, f"band {band} at ({x}, {y})"
        ground = [l for l in range(LAYERS) if lib.om_terrain_ground_at(w, l, x, y) == 1]
        assert band - 1 in ground, f"no ground flag on the band's layer {band - 1} at ({x}, {y}): {ground}"
        if len(ground) == 1:
            singles += 1
        else:
            assert len(ground) == 2 and ground[1] == ground[0] + 1, f"ground flags {ground} at ({x}, {y})"
            assert _near_slope(slopes, x, y, ground[0] + 1, ground[1] + 1), \
                f"two ground flags {ground} at ({x}, {y}) away from any slope joining those bands"
        for layer in range(LAYERS):
            if layer < band - 1:
                assert _open(lib, w, x, y, layer) == 0, f"layer {layer} open under band {band} at ({x}, {y})"
                blocked_seen += 1
            else:
                assert _open(lib, w, x, y, layer) == 1, f"layer {layer} blocked at/above band {band} at ({x}, {y})"
    return blocked_seen, singles


def test_R_200_02_ground_flags_and_blocked_bits_follow_the_bands(lib, mk):
    w = mk()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS, CANVAS) == 0
    blocked, singles = _check_world(lib, w, _positions())
    assert blocked > 0, "positive control: no position had a blocked layer, the check proved nothing"
    assert singles >= MIN_SINGLE_SHARE * SAMPLES


def test_R_200_02_before_generate_nothing_is_blocked(lib, mk):
    w = mk()
    for x, y in _positions():
        for layer in range(LAYERS):
            assert _open(lib, w, x, y, layer) == 1, f"layer {layer} blocked before generate at ({x}, {y})"
    assert lib.om_terrain_generate(w, SEED_A, CANVAS, CANVAS) == 0
    blocked = sum(_open(lib, w, x, y, 0) == 0 for x, y in _positions())
    assert blocked > 0, "positive control: generate blocked nothing on layer 0"


def test_R_200_02_regenerate_with_another_seed_rewrites_the_bits(lib, mk):
    w = mk()
    pos = _positions()
    assert lib.om_terrain_generate(w, SEED_A, CANVAS, CANVAS) == 0
    bits_a = [[_open(lib, w, x, y, l) for l in range(LAYERS)] for x, y in pos]
    _check_world(lib, w, pos)
    assert lib.om_terrain_generate(w, SEED_B, CANVAS, CANVAS) == 0
    blocked, _ = _check_world(lib, w, pos)
    assert blocked > 0
    bits_b = [[_open(lib, w, x, y, l) for l in range(LAYERS)] for x, y in pos]
    assert bits_a != bits_b, "a different seed left every sampled blocked bit unchanged"
    fresh = mk()
    assert lib.om_terrain_generate(fresh, SEED_B, CANVAS, CANVAS) == 0
    bits_f = [[_open(lib, fresh, x, y, l) for l in range(LAYERS)] for x, y in pos]
    assert bits_b == bits_f, "regenerate left stale bits from the first seed"
