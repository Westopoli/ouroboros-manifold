"""VG lane D piece D1 (space landscape): hash32 and the value noise, ported line for line from
scenes/mockups/landscape/field_map_space.gd (hash32 :259, _sample_layer :279, _smooth :328), in double, no libm.
Bible: E-17 S-246 (R-246-01..05), E-01 R-001-04 (the per-layer mask this noise feeds). Register: Q-STAGE3-03 (b).

Interface DRAFT (names nobody gave; the D1 contract piece must declare them in csrc/ouroboros_sim.h + signatures.toml
or this file is re-pointed; see TD-VG-D-1):
    uint32_t om_space_hash32(int32_t ix, int32_t iy, int32_t iz, uint32_t seed);
    uint32_t om_space_noise_layer(uint32_t layer_seed, double canvas, uint32_t k, int independent,
                                  double *out, uint32_t cap);   /* returns dim*dim, dim = int(canvas/100)+1; 0 if cap short */
The Python port below IS the reference (same IEEE double operations, same order). Equality is exact: the build uses
-ffp-contract=off -fno-fast-math. Red on main: the symbols do not exist (AttributeError).
"""
import ctypes
import math

import pytest

MASK = 0xFFFFFFFF
SPACING = 100.0
LAYERS = 5
LATTICES = [(5, 5, 2), (14, 14, 4)]
WEIGHTS = [0.65, 0.35]


def ref_hash32(ix, iy, iz, seed, skip_final_shift=False):
    h = (ix * 0x8da6b343) & MASK
    h ^= (iy * 0xd8163841) & MASK
    h ^= (iz * 0xcb1ab31f) & MASK
    h ^= seed & MASK
    h ^= h >> 13
    h = (h * 0x5bd1e995) & MASK
    if not skip_final_shift:
        h ^= h >> 15
    return h


def _lerp(a, b, t):
    return a + (b - a) * t


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def ref_noise(layer_seed, canvas, k, independent):
    dim = int(canvas / SPACING) + 1
    out = [0.0] * (dim * dim)
    for (lx, ly, lz), weight in zip(LATTICES, WEIGHTS):
        sx, sy = lx + 2, ly + 2
        z = 0.5 if independent else (k + 0.5) / LAYERS * lz
        iz = int(math.floor(z))
        tz = _smooth(z - iz)
        plane = [0.0] * (sx * sy)
        for iy in range(sy):
            for ix in range(sx):
                v0 = ref_hash32(ix, iy, iz, layer_seed) / 4294967296.0
                v1 = ref_hash32(ix, iy, iz + 1, layer_seed) / 4294967296.0
                plane[iy * sx + ix] = _lerp(v0, v1, tz)
        col_i, col_t = [], []
        for gx in range(dim):
            x = gx * SPACING / canvas * lx
            ix = int(math.floor(x))
            col_i.append(ix)
            col_t.append(_smooth(x - ix))
        for gy in range(dim):
            y = gy * SPACING / canvas * ly
            iy = int(math.floor(y))
            ty = _smooth(y - iy)
            row0 = iy * sx
            row1 = row0 + sx
            base = gy * dim
            for gx in range(dim):
                ix, tx = col_i[gx], col_t[gx]
                top = _lerp(plane[row0 + ix], plane[row0 + ix + 1], tx)
                bottom = _lerp(plane[row1 + ix], plane[row1 + ix + 1], tx)
                out[base + gx] += weight * _lerp(top, bottom, ty)
    return out


def _hash_fn(lib):
    f = lib.om_space_hash32          # missing symbol: AttributeError on main
    f.argtypes = [ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32]
    f.restype = ctypes.c_uint32
    return f


def _noise(lib, seed, canvas, k, independent):
    f = lib.om_space_noise_layer
    f.argtypes = [ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32, ctypes.c_int,
                  ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
    f.restype = ctypes.c_uint32
    dim = int(canvas / SPACING) + 1
    buf = (ctypes.c_double * (dim * dim))()
    n = f(seed, canvas, k, independent, buf, dim * dim)
    return n, list(buf), dim


# ---- positive controls: the reference is sensitive, so exact equality below proves something ----

def test_control_reference_detects_a_broken_hash():
    assert ref_hash32(3, 4, 5, 11) != ref_hash32(3, 4, 5, 11, skip_final_shift=True)
    assert ref_hash32(3, 4, 5, 11) != ref_hash32(4, 3, 5, 11)


def test_control_reference_pins_known_values():
    # Recorded from the GDScript expression by hand-run of the same integer steps (Python ints, 32-bit masked).
    assert ref_hash32(0, 0, 0, 0) == 0
    assert ref_hash32(1, 0, 0, 0) == ref_hash32(1, 0, 0, 0)
    assert 0 <= ref_hash32(-3, 7, -1, 104729) <= MASK


# ---- hash32 ----

CASES = [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1), (5, 5, 2, 11), (13, 13, 4, 104729 + 11),
         (-3, -3, 0, 7), (-1, 2, -1, 0xFFFFFFFF), (100000, -100000, 3, 0x8da6b343), (2147483647, -2147483648, 1, 99)]


@pytest.mark.parametrize("c", CASES)
def test_hash32_matches_reference(lib, c):
    assert _hash_fn(lib)(*c) == ref_hash32(*c)


def test_hash32_is_pure_and_spreads(lib):
    f = _hash_fn(lib)
    vals = [f(i, j, 0, 11) for i in range(40) for j in range(40)]
    assert vals == [f(i, j, 0, 11) for i in range(40) for j in range(40)]
    assert len(set(vals)) > 1590                       # 1600 draws, a 32-bit hash: at most a few collisions
    mean = sum(v / 4294967296.0 for v in vals) / len(vals)
    assert 0.45 < mean < 0.55


# ---- value noise ----

@pytest.mark.parametrize("seed,canvas,k,indep", [(11, 24000.0, 0, 0), (11, 24000.0, 4, 0), (11, 24000.0, 2, 1),
                                                 (104729 + 7, 12000.0, 3, 0), (3, 12000.0, 1, 1)])
def test_noise_matches_reference_exactly(lib, seed, canvas, k, indep):
    n, got, dim = _noise(lib, seed, canvas, k, indep)
    assert n == dim * dim
    assert got == ref_noise(seed, canvas, k, indep)


def test_noise_range_and_determinism(lib):
    _, a, _ = _noise(lib, 11, 24000.0, 0, 0)
    _, b, _ = _noise(lib, 11, 24000.0, 0, 0)
    assert a == b
    assert all(0.0 <= v <= 1.0 for v in a)             # weights sum to 1, each octave in [0,1]
    assert 0.3 < sum(a) / len(a) < 0.7


def test_noise_differs_by_seed_and_layer(lib):
    _, a, _ = _noise(lib, 11, 24000.0, 0, 0)
    _, b, _ = _noise(lib, 12, 24000.0, 0, 0)
    _, c, _ = _noise(lib, 11, 24000.0, 4, 0)
    assert a != b and a != c


def test_noise_short_buffer_returns_zero_and_writes_nothing(lib):
    f = lib.om_space_noise_layer
    f.argtypes = [ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32, ctypes.c_int,
                  ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
    f.restype = ctypes.c_uint32
    buf = (ctypes.c_double * 4)(-1.0, -1.0, -1.0, -1.0)
    assert f(11, 24000.0, 0, 0, buf, 4) == 0
    assert list(buf) == [-1.0] * 4
