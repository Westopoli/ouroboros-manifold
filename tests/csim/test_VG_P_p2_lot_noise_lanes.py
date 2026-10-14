"""VG-P2 (places lane P2), tests of the lot-order noise and the lanes: csrc/lot_noise.h, csrc/economy_lot_noise.c.

Method rev 3: the rule words, word for word.

Bible E-17 (docs/bible/epics/E-17-map-generation.md), the rule this file proves for the outline (the spec comment on
om_lot_noise_q16 reads "R-193-01: a ragged outline at any age"; the lot noise g makes the drawn town a warped disc):

- R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.

Bible E-17, the rule the lanes prove (streets along contour lines and rivers; no fixed grid):

- R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).

Spec docs/northstar/plans/2026-10-13-places-lane-spec.md rev 4a, section "P2 lot-order noise, lanes and the growth
probe" (lines 85-107), the sentences these tests implement:

  "what the player sees is the lots, and the lots are created in the order of a noisy distance with a quota that always
  binds, so the drawn town is a warped disc by construction"

  "`DRAFT-shape-harm` is **0.5, pinned from the controls, not from the probe** (the auditor measured: clean square 0.99,
  diamond 0.99, octagon 0.997, noisy square 0.80, noise blobs 0.13 to 0.20; a rasterised disc 0.48 to 0.84, so a disc is
  not a control)"   (asserted in test_VG_P_p2_probe_shape.py)

  "`om_lane_build` replaces `gx%4==3 || gy%4==3` (`economy_density.c:106`; R-193-09, streets along contour lines and
  rivers). Per cell, at lane level L (0..3): contour lane when `floor(h/(150*2^L))` ... differs between the cell and its
  east neighbour (gx+1) or its neighbour at gy+1; water lane when any of its eight neighbours is water; fallback lane
  when no contour or water lane cell lies within `DRAFT-lane-fallback-reach` 4 cells (Chebyshev) ... Level per cell =
  the level of its nearest core (Chebyshev; ties to the lower index). Cap: a core's level is the lowest L in 0..3 for
  which lane cells are at most 30 percent of the non-water cells in the 41 x 41 window around its core cell."

THE BIBLE GIVES NO NUMBER for the noise band, the noise lattice, the pinned range, the lane contour interval, the
fallback period and warp, the fallback reach, the lane share cap or the window. Every number below is a named draft of
spec rev 4a (cited where used): DRAFT-lot-noise-band 0.7..1.4, DRAFT-lot-noise-octaves 3 (gain 0.5),
DRAFT-lot-noise-lattice 800 wu, DRAFT-lot-noise-range (measured), DRAFT-noise-range-slack 0 to 0.05 of the span,
DRAFT-noise-edge 0.02, DRAFT-test-samples 10,000 cells and seeds 1..64, DRAFT-lane-contour 150 wu, DRAFT-lane-fallback
(period 4 cells, warp +-3 cells, lattice 800 wu), DRAFT-lane-fallback-reach 4 cells, DRAFT-lane-share 0.30,
DRAFT-lane-window 20 cells. Gap rulings (Architect 2026-10-14): gap 1 (the lane builder takes the P1 callback struct and
tests water itself as height_at < 0.0, links no layout_terrain.c), gap 5 (the pin sample is the 100 x 100 block at the
origin for seeds 1..64), gap 8 reading (an off-grid neighbour is skipped; the window is clipped to the grid; the share
is non-water lane cells over non-water cells, 0 when none; heights at the cell centre).

READINGS taken by the independent Python model of these tests (spec words, no number added):
  * a cell centre is ((gx + 0.5) * 100, (gy + 0.5) * 100) wu;
  * the mask "at level L" is the mask with every cell at level L; the cap test needs it (a core's level is found from
    lane cells at each L over its window) and a cell's lane value is the mask at the level of its nearest core;
  * the pin slack: 0 <= measured_min - lo <= 0.05 * (measured_max - measured_min), and the same for hi.

Tie rule (documented, test_lane_ties_to_lower_core): cells equally near two cores (Chebyshev) take the level of the
LOWER core index, so reordering the core list can change those cells.
"""
import ctypes
import math
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
# Same flags as the Makefile's release build (CFLAGS_COMMON + CFLAGS_DET_BASE, -O2), the pattern of
# tests/csim/test_PP_grid_margin_exact.py:31-33.
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]
CELL_WU = 100.0
SIDE = 160                       # the 16,000 wu canvas of the P1 stubs
LANE_INTERVAL_WU = 150.0         # DRAFT-lane-contour
LANE_REACH = 4                   # DRAFT-lane-fallback-reach
LANE_WINDOW = 20                 # DRAFT-lane-window (41 x 41)
LANE_SHARE_NUM, LANE_SHARE_DEN = 3, 10    # DRAFT-lane-share 0.30
NOISE_LO_G, NOISE_HI_G = 45875, 91750      # DRAFT-lot-noise-band 0.7..1.4 in Q16
NOISE_EDGE = 0.02                # DRAFT-noise-edge
NOISE_SLACK = 0.05               # DRAFT-noise-range-slack (upper end of 0 to 0.05)
NOISE_SEEDS = range(1, 65)       # DRAFT-test-samples: seeds 1..64
NOISE_BLOCK = 100                # gap 5: the 100 x 100 block at the origin = 10,000 cells
SALT_LOT = 420                   # spec P1 salts: lot threshold seed + 420
LANE_SEEDS = (1, 2, 3)

P2_STUBS_C = r"""
/* test stubs of tests/csim/test_VG_P_p2_lot_noise_lanes.py: heights only, behind the P1 callback struct (own copy of the
 * struct, same layout as om_layout_terrain). kinds: 0 constant height, 1 gentle ramp, 2 steep ramp, 3 split ramp. */
#include <stdint.h>
typedef struct p2_terrain {
    void *ctx;
    double (*height_at)(void *ctx, double x, double y);
    int    (*walkable_at)(void *ctx, double x, double y);
    int    (*nearest_walkable)(void *ctx, double x, double y, double *ox, double *oy);
} p2_terrain;
static const int32_t p2_kinds[4] = {0, 1, 2, 3};
static double p2_height(void *ctx, double x, double y) {
    int32_t k = *(const int32_t *)ctx;
    (void)y;
    if (k == 0) return 200.0;                    /* constant */
    if (k == 1) return 20.0 + 0.25 * x;          /* gentle: 25 wu per 100 wu cell, a level-0 contour every 6 cells */
    if (k == 2) return 1.5 * x;                  /* steep: 150 wu per cell = one level-0 contour interval per cell */
    return x < 8000.0 ? 20.0 + 0.25 * x : 2000.0 + 1.5 * (x - 8000.0);   /* split: gentle west, steep east of x = 8000 */
}
static int p2_walk(void *ctx, double x, double y) { (void)ctx; (void)x; (void)y; return 1; }
static int p2_near(void *ctx, double x, double y, double *ox, double *oy) { (void)ctx; *ox = x; *oy = y; return 0; }
void p2_stub(int32_t kind, p2_terrain *out) {
    out->ctx = (void *)&p2_kinds[kind];
    out->height_at = p2_height;
    out->walkable_at = p2_walk;
    out->nearest_walkable = p2_near;
}
"""

P1_KIND = {"flat": 0, "lake": 1, "rolling": 2, "water": 3}
P2_KIND = {"const": 0, "gentle": 1, "steep": 2, "split": 3}


class Terrain(ctypes.Structure):
    """ctypes mirror of om_layout_terrain (csrc/layout_internal.h): four pointers."""
    _fields_ = [("ctx", ctypes.c_void_p), ("height_at", ctypes.c_void_p),
                ("walkable_at", ctypes.c_void_p), ("nearest_walkable", ctypes.c_void_p)]


HEIGHT_FN = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_void_p, ctypes.c_double, ctypes.c_double)


def _cc(out, srcs, opt="-O2"):
    flags = [opt if f == "-O2" else f for f in FLAGS]
    res = subprocess.run(["cc", *flags, "-I", str(REPO / "csrc"), "-shared", "-o", str(out),
                          *[str(s) for s in srcs], "-lm"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]
    return out


_LIBS = {}


def _load_lib(work, opt, with_p2):
    key = (str(work), opt, with_p2)
    if key in _LIBS:
        return _LIBS[key]
    stubs = work / "p2_stubs.c"
    stubs.write_text(P2_STUBS_C)
    srcs = [REPO / "csrc/terrain_noise.c", REPO / "tests/csim/layout_stub_terrain.c", stubs]
    if with_p2:
        srcs.append(REPO / "csrc/economy_lot_noise.c")
    name = f"lib_a{'_p2' if with_p2 else '_p1'}{opt}.so"
    h = ctypes.CDLL(str(_cc(work / name, srcs, opt)))
    h.om_tn_fbm2.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int, ctypes.c_int32]
    h.om_tn_fbm2.restype = ctypes.c_int32
    h.om_stub_terrain.argtypes = [ctypes.c_int32, ctypes.POINTER(Terrain)]
    h.p2_stub.argtypes = [ctypes.c_int32, ctypes.POINTER(Terrain)]
    if with_p2:
        h.om_lot_noise_q16.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32]
        h.om_lot_noise_q16.restype = ctypes.c_uint32
        h.om_lot_noise_range.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32)]
        h.om_lane_build.argtypes = [ctypes.POINTER(Terrain), ctypes.c_uint64, ctypes.c_int32,
                                    ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
                                    ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]
    _LIBS[key] = h
    return h


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2_lane")


def make_terrain(lib, name):
    t = Terrain()
    if name in P1_KIND:
        lib.om_stub_terrain(P1_KIND[name], ctypes.byref(t))
    else:
        lib.p2_stub(P2_KIND[name], ctypes.byref(t))
    assert t.height_at, f"stub {name} did not fill the struct"
    return t


def height_grid(t, side=SIDE):
    f = HEIGHT_FN(t.height_at)
    return [[f(t.ctx, (gx + 0.5) * CELL_WU, (gy + 0.5) * CELL_WU) for gx in range(side)] for gy in range(side)]


def run_lanes(lib, t, seed, cores, side=SIDE):
    """cores: list of (gx, gy). Returns (lane bytes, levels list)."""
    n = len(cores)
    arr = (ctypes.c_uint32 * n)(*[gy * side + gx for gx, gy in cores])
    lane = (ctypes.c_uint8 * (side * side))(*([7] * (side * side)))   # sentinel: every cell must be written
    lev = (ctypes.c_uint8 * n)(*([9] * n))
    lib.om_lane_build(ctypes.byref(t), seed, side, arr, n, lane, lev)
    return bytes(lane), list(lev)


# ----------------------------------------------------------------------------- the independent lane model

def _prefix(mask, side):
    p = [[0] * (side + 1) for _ in range(side + 1)]
    for y in range(side):
        run = 0
        for x in range(side):
            run += mask[y * side + x]
            p[y + 1][x + 1] = p[y][x + 1] + run
    return p


def _box(p, x0, y0, x1, y1):
    return p[y1 + 1][x1 + 1] - p[y0][x1 + 1] - p[y1 + 1][x0] + p[y0][x0]


def contour_mask(h, side, level):
    interval = LANE_INTERVAL_WU * (1 << level)
    fl = [[math.floor(v / interval) for v in row] for row in h]
    out = bytearray(side * side)
    for gy in range(side):
        for gx in range(side):
            c = fl[gy][gx]
            if (gx + 1 < side and fl[gy][gx + 1] != c) or (gy + 1 < side and fl[gy + 1][gx] != c):
                out[gy * side + gx] = 1
    return out


def water_mask(h, side):
    """1 where any of the eight on-grid neighbours is water (height_at < 0.0)."""
    out = bytearray(side * side)
    for gy in range(side):
        for gx in range(side):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and 0 <= gx + dx < side and 0 <= gy + dy < side and h[gy + dy][gx + dx] < 0.0:
                        out[gy * side + gx] = 1
    return out


def warp_tables(lib, seed, side):
    wx, wy = [0] * (side * side), [0] * (side * side)
    for gy in range(side):
        for gx in range(side):
            fx = lib.om_tn_fbm2(seed + 430, gx * 8192, gy * 8192, 2, 32768)
            fy = lib.om_tn_fbm2(seed + 440, gx * 8192, gy * 8192, 2, 32768)
            wx[gy * side + gx] = (3 * fx + 32768) // 65536      # python // floors, as the spec's floor_div
            wy[gy * side + gx] = (3 * fy + 32768) // 65536
    return wx, wy


def lane_masks(lib, h, side, seed):
    """The lane mask with every cell at level L, for L in 0..3 (the model of the spec's per-cell rule)."""
    wx, wy = warp_tables(lib, seed, side)
    water = water_mask(h, side)
    masks = []
    for level in range(4):
        base = bytearray(a | b for a, b in zip(contour_mask(h, side, level), water))
        p = _prefix(base, side)
        period = 4 << level
        m = bytearray(side * side)
        for gy in range(side):
            for gx in range(side):
                i = gy * side + gx
                if base[i]:
                    m[i] = 1
                    continue
                near = _box(p, max(0, gx - LANE_REACH), max(0, gy - LANE_REACH),
                            min(side - 1, gx + LANE_REACH), min(side - 1, gy + LANE_REACH))
                if near == 0 and (((gx + wx[i]) % period) == period - 1 or ((gy + wy[i]) % period) == period - 1):
                    m[i] = 1
        masks.append(m)
    return masks


def window_counts(mask, h, side, cx, cy):
    lane = nonwater = 0
    for gy in range(max(0, cy - LANE_WINDOW), min(side - 1, cy + LANE_WINDOW) + 1):
        for gx in range(max(0, cx - LANE_WINDOW), min(side - 1, cx + LANE_WINDOW) + 1):
            if h[gy][gx] >= 0.0:
                nonwater += 1
                lane += mask[gy * side + gx]
    return lane, nonwater


def over_cap(lane, nonwater):
    """share > 0.30, in integers (DRAFT-lane-share)."""
    return lane * LANE_SHARE_DEN > LANE_SHARE_NUM * nonwater


def model_level(masks, h, side, cx, cy):
    for level in range(4):
        lane, nonwater = window_counts(masks[level], h, side, cx, cy)
        if not over_cap(lane, nonwater):
            return level
    return 3


def nearest_core_level(cores, levels, gx, gy):
    best, bi = None, -1
    for i, (cx, cy) in enumerate(cores):
        d = max(abs(gx - cx), abs(gy - cy))
        if best is None or d < best:      # strict: ties keep the lower index
            best, bi = d, i
    return levels[bi]


def expected_lanes(masks, cores, levels, side):
    out = bytearray(side * side)
    for gy in range(side):
        for gx in range(side):
            out[gy * side + gx] = masks[nearest_core_level(cores, levels, gx, gy)][gy * side + gx]
    return bytes(out)


# ----------------------------------------------------------------------------- positive control, green today

def test_ctrl_p1_stub_builds(work):
    """Library A's P1 part (terrain_noise.c + P1's stub, without economy_lot_noise.c) compiles and links and the stub
    fills the struct: red below then means the P2 files are missing, not that the harness is broken."""
    lib = _load_lib(work, "-O2", with_p2=False)
    t = Terrain()
    lib.om_stub_terrain(0, ctypes.byref(t))
    assert t.height_at and t.ctx
    f = HEIGHT_FN(t.height_at)
    assert f(t.ctx, 0.0, 0.0) == 50.0          # P1 kind 0 flat: STUB_FLAT_H


# ----------------------------------------------------------------------------- noise

_SWEEP = {}


def _sweep(lib):
    """gs and fs over the gap 5 sample: 100 x 100 block at the origin, seeds 1..64."""
    if id(lib) in _SWEEP:
        return _SWEEP[id(lib)]
    gs, fs = [], []
    for seed in NOISE_SEEDS:
        for gy in range(NOISE_BLOCK):
            for gx in range(NOISE_BLOCK):
                gs.append(lib.om_lot_noise_q16(seed, gx, gy))
                fs.append(lib.om_tn_fbm2(seed + SALT_LOT, gx * 8192, gy * 8192, 3, 32768))
    _SWEEP[id(lib)] = (gs, fs)
    return gs, fs


def test_noise_range_and_edges(work):
    """g lies in [45875, 91750] for 10,000 cells of every seed 1..64; the sweep minimum and maximum are within
    DRAFT-noise-edge 0.02 of 0.7 and 1.4 (the rescale works); g equals the spec's formula on the pinned range."""
    lib = _load_lib(work, "-O2", with_p2=True)
    lo, hi = ctypes.c_int32(), ctypes.c_int32()
    lib.om_lot_noise_range(ctypes.byref(lo), ctypes.byref(hi))
    assert lo.value < hi.value
    gs, fs = _sweep(lib)
    assert len(gs) == 640000
    assert min(gs) >= NOISE_LO_G and max(gs) <= NOISE_HI_G, (min(gs), max(gs))
    gmin, gmax = min(gs) / 65536.0, max(gs) / 65536.0
    print(f"NOISE_EDGE g_min={gmin:.4f} g_max={gmax:.4f}")
    assert abs(gmin - 0.7) <= NOISE_EDGE, gmin
    assert abs(gmax - 1.4) <= NOISE_EDGE, gmax
    # the spec formula: v = clamp(((f - lo) * 65536) / (hi - lo), 0, 65536); g = 45875 + ((v * 45875) >> 16)
    for g, f in zip(gs, fs):
        v = min(65536, max(0, ((f - lo.value) * 65536) // (hi.value - lo.value)))
        assert g == NOISE_LO_G + ((v * 45875) >> 16), (g, f)


def test_noise_pinned_range(work):
    """lo <= every om_tn_fbm2 value of the sample, hi >= every value; each pin within DRAFT-noise-range-slack 0 to 0.05
    of the measured span of its measured extreme. Prints the measurement so a builder can pin from it."""
    lib = _load_lib(work, "-O2", with_p2=True)
    lo, hi = ctypes.c_int32(), ctypes.c_int32()
    lib.om_lot_noise_range(ctypes.byref(lo), ctypes.byref(hi))
    _, fs = _sweep(lib)
    mn, mx = min(fs), max(fs)
    print(f"NOISE_RANGE measured_min={mn} measured_max={mx} lo={lo.value} hi={hi.value}")
    assert lo.value <= mn, (lo.value, mn)
    assert hi.value >= mx, (hi.value, mx)
    span = mx - mn
    assert mn - lo.value <= NOISE_SLACK * span, (mn - lo.value, NOISE_SLACK * span)
    assert hi.value - mx <= NOISE_SLACK * span, (hi.value - mx, NOISE_SLACK * span)


def test_noise_deterministic(work):
    """Same seed, same value; two seeds differ somewhere; the same values at -O0 and -O2."""
    a = _load_lib(work, "-O2", with_p2=True)
    b = _load_lib(work, "-O0", with_p2=True)
    cells = [(gx, gy) for gy in range(0, 120, 7) for gx in range(0, 120, 5)]
    v1 = [a.om_lot_noise_q16(5, gx, gy) for gx, gy in cells]
    v2 = [a.om_lot_noise_q16(5, gx, gy) for gx, gy in cells]
    v3 = [a.om_lot_noise_q16(6, gx, gy) for gx, gy in cells]
    v0 = [b.om_lot_noise_q16(5, gx, gy) for gx, gy in cells]
    assert v1 == v2
    assert v1 != v3
    assert v1 == v0


# ----------------------------------------------------------------------------- lanes

@pytest.mark.parametrize("seed", LANE_SEEDS)
def test_lane_flat_stub_fallback_only(work, seed):
    """Flat stub (constant height, no water): no cell is a contour or water lane cell, every lane cell is a fallback
    cell of the warped period grid (the model reproduces the mask exactly), and every core reaches level 1 or more (the
    period-4 grid is 44 percent lane, above the 30 percent cap)."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, "flat")
    h = height_grid(t)
    cores = [(40, 40), (120, 60), (80, 140)]
    lane, levels = run_lanes(lib, t, seed, cores)
    assert set(lane) <= {0, 1}, "om_lane_build must write 0 or 1 into every cell"
    for lv in range(4):
        assert sum(contour_mask(h, SIDE, lv)) == 0     # premise: no contour on the flat stub
    assert sum(water_mask(h, SIDE)) == 0               # premise: no water
    masks = lane_masks(lib, h, SIDE, seed)
    p0 = _prefix(masks[0], SIDE)
    share0 = _box(p0, 20, 20, 60, 60) / 1681.0
    print(f"LANE_FLAT seed={seed} levels={levels} level0_share_at_core0={share0:.3f}")
    assert share0 > 0.30                               # the period-4 grid is above the cap
    assert all(1 <= lv <= 3 for lv in levels), levels
    want_levels = [model_level(masks, h, SIDE, cx, cy) for cx, cy in cores]
    assert levels == want_levels
    assert lane == expected_lanes(masks, cores, levels, SIDE)


@pytest.mark.parametrize("seed", (1, 2))
def test_lane_ramp_follows_contours(work, seed):
    """On the ramp stub, lane cells exist along the contour lines: every cell whose floor(h / (150 * 2^L)) differs from
    the east or south neighbour is a lane cell (independent Python model), and the whole mask equals the model."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, "gentle")
    h = height_grid(t)
    cores = [(80, 80)]
    lane, levels = run_lanes(lib, t, seed, cores)
    masks = lane_masks(lib, h, SIDE, seed)
    level = model_level(masks, h, SIDE, 80, 80)
    print(f"LANE_RAMP seed={seed} level={levels[0]} model_level={level}")
    assert levels == [level]
    contour = contour_mask(h, SIDE, level)
    n_contour = sum(contour)
    assert n_contour > 0
    missing = [i for i in range(SIDE * SIDE) if contour[i] and not lane[i]]
    assert not missing, f"{len(missing)} contour cells are not lane cells, first {missing[:5]}"
    assert lane == bytes(masks[level])


def test_ctrl_lane_constant_height_zero_contour(work):
    """The contour counter works: zero contour lane cells at every level on the constant-height stub, more than zero on
    the ramp; and the real mask on the constant stub holds no cell the model does not call a fallback cell."""
    lib = _load_lib(work, "-O2", with_p2=True)
    tc, tr = make_terrain(lib, "const"), make_terrain(lib, "gentle")
    hc, hr = height_grid(tc), height_grid(tr)
    for lv in range(4):
        assert sum(contour_mask(hc, SIDE, lv)) == 0
        assert sum(contour_mask(hr, SIDE, lv)) > 0
    lane, levels = run_lanes(lib, tc, 4, [(80, 80)])
    masks = lane_masks(lib, hc, SIDE, 4)
    assert lane == bytes(masks[levels[0]])
    assert sum(lane) > 0                                # fallback lanes exist: the grid is there, the contours are not


def test_lane_lake_shore_ring(work):
    """Lake stub (P1 kind 1): every non-water cell with a water neighbour among its eight is a lane cell; and every
    non-water cell equals the model (contour at the lake and the cliff, shore ring, fallback elsewhere)."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, "lake")
    h = height_grid(t)
    cores = [(20, 20), (140, 140), (50, 80)]
    lane, levels = run_lanes(lib, t, 1, cores)
    wn = water_mask(h, SIDE)
    ring = [i for i in range(SIDE * SIDE) if h[i // SIDE][i % SIDE] >= 0.0 and wn[i]]
    assert len(ring) > 100                              # the lake is there
    missing = [i for i in ring if not lane[i]]
    assert not missing, f"{len(missing)} shore cells are not lane cells, first {missing[:5]}"
    # non-water cells against the model, one core at a time (a single level per scene)
    masks = lane_masks(lib, h, SIDE, 1)
    for core in cores:
        lane1, lev1 = run_lanes(lib, t, 1, [core])
        assert lev1 == [model_level(masks, h, SIDE, *core)]
        exp = masks[lev1[0]]
        bad = [i for i in range(SIDE * SIDE) if h[i // SIDE][i % SIDE] >= 0.0 and lane1[i] != exp[i]]
        assert not bad, f"core {core}: {len(bad)} non-water cells differ from the model, first {bad[:5]}"


SCENES = [("flat", 1), ("gentle", 1), ("steep", 1), ("split", 1), ("lake", 1), ("rolling", 1)]
CAP_CORES = [(80, 80), (3, 3), (156, 10), (10, 150), (130, 100)]    # centre, three clipped corners, off-centre


@pytest.mark.parametrize("name,seed", SCENES)
def test_lane_cap(work, name, seed):
    """For every core window (41 x 41, clipped) the lane share of non-water cells is at most 30 percent or the core is
    at level 3, and the level equals the model's (lowest L meeting the cap). The flat stub reaches level 1."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, name)
    h = height_grid(t)
    masks = lane_masks(lib, h, SIDE, seed)
    for core in CAP_CORES:
        lane, levels = run_lanes(lib, t, seed, [core])
        lane_n, nonwater = window_counts(lane, h, SIDE, *core)
        print(f"LANE_CAP scene={name} core={core} level={levels[0]} window_lane={lane_n} nonwater={nonwater}")
        assert not over_cap(lane_n, nonwater) or levels[0] == 3, (name, core, levels, lane_n, nonwater)
        assert levels == [model_level(masks, h, SIDE, *core)]
        if name == "flat":
            assert levels[0] >= 1


def test_ctrl_lane_steep_ramp(work):
    """On the steep ramp (one contour interval per cell) more than 30 percent of a window is lane at level 0, so the
    share detector FAILS there, and the cap test passes only because the level rises. Prints the level."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, "steep")
    h = height_grid(t)
    masks = lane_masks(lib, h, SIDE, 1)
    l0, nw0 = window_counts(masks[0], h, SIDE, 80, 80)
    assert over_cap(l0, nw0)                            # the detector flags level 0
    lane, levels = run_lanes(lib, t, 1, [(80, 80)])
    print(f"LANE_STEEP level={levels[0]} level0_share={l0 / nw0:.3f}")
    assert levels[0] >= 1                               # the level rose
    lane_n, nonwater = window_counts(lane, h, SIDE, 80, 80)
    assert not over_cap(lane_n, nonwater)               # and the cap holds at the level it reached
    assert levels == [model_level(masks, h, SIDE, 80, 80)]


def test_lane_ties_to_lower_core(work):
    """Cells equally near two cores take the level of the lower core index. Split stub: the west core (40, 80) reaches
    level 0 (gentle ramp), the east core (120, 80) level 2 (steep ramp). The column gx = 80 is equidistant (Chebyshev
    40 from both): it is a level-0 contour column (lane) when the west core is index 0, and not a lane at level 2 when
    the east core is index 0. The column gx = 100 is nearer the east core in both orders: never a lane. NOTE: reordering
    the core list can change those tie cells (documented behaviour of the spec)."""
    lib = _load_lib(work, "-O2", with_p2=True)
    t = make_terrain(lib, "split")
    west, east = (40, 80), (120, 80)
    lane_we, lev_we = run_lanes(lib, t, 1, [west, east])
    lane_ew, lev_ew = run_lanes(lib, t, 1, [east, west])
    print(f"LANE_TIES levels west-first={lev_we} east-first={lev_ew}")
    assert lev_we == [0, 2]
    assert lev_ew == [2, 0]
    for gy in range(SIDE):
        assert lane_we[gy * SIDE + 80] == 1, ("west core is index 0: tie column is a level-0 contour lane", gy)
        assert lane_ew[gy * SIDE + 80] == 0, ("east core is index 0: tie column at level 2 is not a lane", gy)
    # gx = 100 is strictly nearer the east core only while |gy - 80| < 60 (beyond that the row distance ties both cores)
    for gy in range(21, 140):
        assert lane_we[gy * SIDE + 100] == 0 and lane_ew[gy * SIDE + 100] == 0, ("nearer the east core: level 2", gy)


def test_lane_deterministic(work):
    """Same inputs, byte-equal output; the same bytes from the -O0 and the -O2 builds."""
    a = _load_lib(work, "-O2", with_p2=True)
    b = _load_lib(work, "-O0", with_p2=True)
    scenes = [("flat", [(40, 40), (120, 60), (80, 140)]), ("split", [(40, 80), (120, 80)]), ("lake", [(20, 20), (50, 80)])]
    for name, cores in scenes:
        ta, tb = make_terrain(a, name), make_terrain(b, name)
        r1 = run_lanes(a, ta, 9, cores)
        r2 = run_lanes(a, ta, 9, cores)
        r0 = run_lanes(b, tb, 9, cores)
        assert r1 == r2, name
        assert r1 == r0, name
        assert run_lanes(a, ta, 10, cores) != r1 or name != "flat"   # the seed moves the fallback warp on the flat stub
