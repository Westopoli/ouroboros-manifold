"""E-17 S-189 / R-200-03: ground you cannot cross.

Terrain stage 1 spec 2026-10-05, "query" lane: om_terrain_walkable_at is 1 exactly when the
footprint slope is at or below OM_TP_TERRAIN_STEEP_DEG (default 35, set with om_tactical_set_param).
The slope is the mockup's (scenes/mockups/landscape/pass4_terrain.gd slope_tan): over a footprint
`width` wide (one 100 wu cell) take four directions through the cell centre, east-west, north-south
and the two diagonals, each a pair of points half a width out on opposite sides; the steepest
height difference of the four, divided by the width, is tan(slope). Heights come from
om_terrain_height_at, floored at 0 (sea level) as the mockup floors them.

Cells whose tan lies within TAN_MARGIN of the limit are not asserted: the sim keeps heights in
fixed point and may sample the field differently from this reading of the mockup. The test
asserts zero disagreement outside that margin, and that the margin is a small share of cells.
"""
import math
import random

import pytest

SEED = 11
CANVAS = 16000.0
CELL_WU = 100.0
FOOTPRINT_WU = 100.0
DIAG = 0.70710678
SAMPLES = 400
SAMPLE_RNG_SEED = 20261006   # provisional (2026-10-05)
TAN_MARGIN = 0.02            # provisional (2026-10-05): relative band around the limit left unasserted
MAX_MARGIN_SHARE = 0.10      # provisional (2026-10-05)
OM_TP_TERRAIN_STEEP_DEG = 61  # conftest.OMTacParam.TERRAIN_STEEP_DEG
DEFAULT_DEG = 35.0
HIGH_DEG = 60.0
LOW_DEG = 10.0


@pytest.fixture
def mk(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


def _h(lib, w, x, y):
    return max(lib.om_terrain_height_at(w, x, y), 0.0)


def _tan(lib, w, x, y):
    r = FOOTPRINT_WU * 0.5
    rd = r * DIAG
    best = 0.0
    for ox, oy in ((r, 0.0), (0.0, r), (rd, rd), (rd, -rd)):
        d = abs(_h(lib, w, x + ox, y + oy) - _h(lib, w, x - ox, y - oy))
        best = max(best, d)
    return best / FOOTPRINT_WU


def _cells():
    rng = random.Random(SAMPLE_RNG_SEED)
    n = int(CANVAS / CELL_WU)
    return [((rng.randrange(1, n - 1) + 0.5) * CELL_WU, (rng.randrange(1, n - 1) + 0.5) * CELL_WU)
            for _ in range(SAMPLES)]


def _set_limit(lib, w, deg):
    assert lib.om_tactical_set_param(w, OM_TP_TERRAIN_STEEP_DEG, deg) == 0
    assert lib.om_tactical_get_param(w, OM_TP_TERRAIN_STEEP_DEG) == deg


def _walk(lib, w, cells):
    return [lib.om_terrain_walkable_at(w, x, y) for x, y in cells]


def test_S_189_default_is_35_degrees(lib, mk):
    assert lib.om_tactical_get_param(mk, OM_TP_TERRAIN_STEEP_DEG) == DEFAULT_DEG


@pytest.mark.parametrize("deg", [DEFAULT_DEG, HIGH_DEG, LOW_DEG])
def test_S_189_walkable_iff_slope_at_or_below_the_limit(lib, mk, deg):
    _set_limit(lib, mk, deg)
    limit = math.tan(math.radians(deg))
    cells = _cells()
    margin = 0
    for x, y in cells:
        t = _tan(lib, mk, x, y)
        got = lib.om_terrain_walkable_at(mk, x, y)
        assert got in (0, 1)
        if abs(t - limit) <= TAN_MARGIN * limit:
            margin += 1
            continue
        assert got == (1 if t <= limit else 0), \
            f"limit {deg} deg at ({x}, {y}): tan {t:.4f} vs {limit:.4f}, walkable_at {got}"
    assert margin <= MAX_MARGIN_SHARE * SAMPLES
    # positive control: the field has both walkable and unwalkable sampled cells at this limit
    w = _walk(lib, mk, cells)
    assert 1 in w and 0 in w, f"limit {deg} deg: every sampled cell reads {w[0]}"


def test_S_189_raising_the_limit_never_removes_walkable_ground(lib, mk):
    cells = _cells()
    base = _walk(lib, mk, cells)
    _set_limit(lib, mk, HIGH_DEG)
    high = _walk(lib, mk, cells)
    assert all(h >= b for b, h in zip(base, high)), "a walkable cell became unwalkable at the higher limit"
    assert any(h > b for b, h in zip(base, high)), "no unwalkable cell became walkable at 60 degrees"


def test_S_189_lowering_the_limit_never_adds_walkable_ground(lib, mk):
    cells = _cells()
    base = _walk(lib, mk, cells)
    _set_limit(lib, mk, LOW_DEG)
    low = _walk(lib, mk, cells)
    assert all(l <= b for b, l in zip(base, low)), "an unwalkable cell became walkable at the lower limit"
    assert any(l < b for b, l in zip(base, low)), "no walkable cell became unwalkable at 10 degrees"
