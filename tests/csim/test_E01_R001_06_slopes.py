"""E-01 R-001-06 (and R-200-03): slopes, and the terrain in the save.

Terrain stage 1 spec 2026-10-05, "query" lane: a slope is a run of walkable cells crossing a band
boundary. Seeds 11 to 13 have slopes. Every slope joins adjacent bands (upper = lower + 1; the
spec's stage 1 slopes cross one boundary), has a positive length, a midline between its edges, a
bottom edge cell in the lower band, a top edge cell in the upper band, and every cell along it is
walkable. Save round trip: om_save_state_write then om_load_state_read into a fresh prepared world
gives an equal checksum section 8 (support and map, where the terrain hash lives) and equal dumped
bands; a truncated save is refused and leaves the target unchanged.
"""
import ctypes
import math

import pytest

from test_net_section_hashes import _secs, SUPPORT_MAP

SEEDS = (11, 12, 13)
CANVAS = 16000.0
CELL_WU = 100.0
STEP_WU = 50.0                # provisional (2026-10-05): sampling step along a slope
EDGE_EPS_WU = 1e-6            # provisional (2026-10-05)
TRUNCATE_BYTES = 3


class _Slope(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double), ("y0", ctypes.c_double), ("x1", ctypes.c_double),
                ("y1", ctypes.c_double), ("mx", ctypes.c_double), ("my", ctypes.c_double),
                ("length", ctypes.c_double), ("lower_band", ctypes.c_int32),
                ("upper_band", ctypes.c_int32)]


def _gen(lib, world_factory, seed):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, seed, CANVAS, CANVAS) == 0
    return w


def _slopes(lib, w):
    out = []
    for i in range(lib.om_terrain_slope_count(w)):
        s = _Slope()
        assert lib.om_terrain_slope_get(w, i, ctypes.byref(s)) == 0
        out.append(s)
    return out


def _bands(lib, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value * ch.value
    buf = (ctypes.c_uint8 * max(n, 1))()
    got = lib.om_terrain_dump_bands(w, buf, n)
    return bytes(buf)[:got]


@pytest.mark.parametrize("seed", SEEDS)
def test_R_001_06_seed_has_slopes(lib, world_factory, seed):
    w = _gen(lib, world_factory, seed)
    assert lib.om_terrain_slope_count(w) > 0, f"seed {seed} has no slope"


@pytest.mark.parametrize("seed", SEEDS)
def test_R_001_06_every_slope_joins_adjacent_bands_edge_to_edge(lib, world_factory, seed):
    w = _gen(lib, world_factory, seed)
    slopes = _slopes(lib, w)
    assert slopes, "positive control: no slopes to check"
    for i, s in enumerate(slopes):
        assert s.upper_band == s.lower_band + 1, f"slope {i}: bands {s.lower_band} to {s.upper_band}"
        assert s.length > 0.0, f"slope {i}: length {s.length}"
        assert min(s.x0, s.x1) - EDGE_EPS_WU <= s.mx <= max(s.x0, s.x1) + EDGE_EPS_WU, f"slope {i}: midline x outside its edges"
        assert min(s.y0, s.y1) - EDGE_EPS_WU <= s.my <= max(s.y0, s.y1) + EDGE_EPS_WU, f"slope {i}: midline y outside its edges"
        assert lib.om_terrain_band_at(w, s.x0, s.y0) == s.lower_band, f"slope {i}: bottom edge not in the lower band"
        assert lib.om_terrain_band_at(w, s.x1, s.y1) == s.upper_band, f"slope {i}: top edge not in the upper band"


@pytest.mark.parametrize("seed", SEEDS)
def test_R_001_06_every_cell_along_a_slope_is_walkable(lib, world_factory, seed):
    w = _gen(lib, world_factory, seed)
    slopes = _slopes(lib, w)
    assert slopes, "positive control: no slopes to check"
    for i, s in enumerate(slopes):
        n = max(1, int(math.ceil(math.hypot(s.x1 - s.x0, s.y1 - s.y0) / STEP_WU)))
        for k in range(n + 1):
            t = k / n
            x, y = s.x0 + (s.x1 - s.x0) * t, s.y0 + (s.y1 - s.y0) * t
            assert lib.om_terrain_walkable_at(w, x, y) == 1, f"slope {i}: ({x}, {y}) not walkable"


# ---- save round trip (module state: terrain) ----

def _bind(lib):
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int


def _save(lib, w):
    _bind(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _target(lib, world_factory, seed=999):
    from conftest import OMFeature
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def test_save_round_trip_keeps_section_8_and_bands(lib, world_factory):
    wa = _gen(lib, world_factory, SEEDS[0])
    sec_a = _secs(lib, wa)[SUPPORT_MAP]
    wo = _gen(lib, world_factory, SEEDS[1])
    assert sec_a != 0 and sec_a != _secs(lib, wo)[SUPPORT_MAP], \
        "positive control: section 8 does not move with the terrain"
    buf, size = _save(lib, wa)
    wb = _target(lib, world_factory)
    assert lib.om_load_state_read(wb, buf, size) == 0
    assert _secs(lib, wb)[SUPPORT_MAP] == sec_a, "section 8 differs after the load"
    bands = _bands(lib, wa)
    assert bands and _bands(lib, wb) == bands, "dumped bands differ after the load"


def test_save_truncated_is_refused_and_target_unchanged(lib, world_factory):
    wa = _gen(lib, world_factory, SEEDS[0])
    buf, size = _save(lib, wa)
    wb = _target(lib, world_factory)
    before = _secs(lib, wb)
    cut = size - TRUNCATE_BYTES
    trunc = (ctypes.c_uint8 * cut)(*bytes(buf)[:cut])
    assert lib.om_load_state_read(wb, trunc, cut) != 0, "a truncated save must be refused"
    assert _secs(lib, wb) == before, "a refused load changed the target's checksum"
    assert lib.om_terrain_present(wb) == 0
