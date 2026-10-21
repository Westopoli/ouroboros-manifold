# Rule pins: R-193-01@451aaa, R-193-09@052634, R-191-03@91c415, R-191-06@ffc11c
"""VG-P2 (places lane, spec rev 6a): field noise and lanes. Tests for csrc/field_noise.h and
csrc/economy_field_noise.c (om_field_hop_cost, om_field_noise_range, om_field_apply_cost, om_lane_build).

Rule pins are on line 1 (the rule text below also names R-191-03 and R-191-06).

Rules proved, word for word (docs/bible/epics/E-17-map-generation.md):

R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.

(docs/bible/epics/E-17-map-generation.md:315; "the growth front is ragged from its first ring and a town is
never a square or an octagon at any age" is the sentence this file proves for the noise tests; the shape
and front tests are in test_VG_P_p2_probe_shape.py.)

R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).

(docs/bible/epics/E-17-map-generation.md:323; the lane tests prove "streets along contour lines and rivers".)

Spec sentences implemented (docs/northstar/plans/2026-10-13-places-lane-spec.md, P2 section, :113-138):
  "[B R-193-01@451aaa: the field's spread is also multiplied by seeded noise of the terrain generator's family
   with its own salt, so the growth front is ragged from its first ring and a town is never a square or an
   octagon at any age]"
  "every cell carries a **hop cost** of 1, 2 or 3 taken from seeded noise of the terrain family, and the field
   crosses a cell of cost c as if it were c cells wide, in value and in time. The value rule is
   `v = P[i] · factor(i, j)^cost[j]` ... applied `cost[j]` times as left-to-right repeated multiplication
   `((P · f) · f) · f` in one shared helper `om_field_apply_cost(double v, double f, uint8_t cost)` ... no `pow`"
  "(noise) `om_field_hop_cost` over 10,000 cells is always 1, 2 or 3; over the seed sweep each cost holds
   between 15 and 55 percent of the cells (`DRAFT-field-cost-share`, expecting about 33 each; the test prints
   the shares); the same seed reproduces, two seeds differ; the pinned range holds as above."
  "(lanes) lane mask on the flat stub has no contour or water lanes and the fallback grid only; on a ramp stub
   lanes lie along contours; on a lake stub the shore ring is lane; the cap: every window is at most 30 percent
   lane or level 3, and the flat stub reaches level 1 (the period-4 grid is 44 percent lane); same inputs
   byte-equal; cells equally near two cores go to the lower index (asserted, and documented: reordering the
   core list can change those cells)."

The bible gives no number for the cost buckets, the lattice, the window, the share or the pin. Each number
below is the spec's, cited as "spec rev 6a, DRAFT-<name>": DRAFT-field-noise-octaves 3 (gain 0.5),
DRAFT-field-noise-lattice (cell index * 8192), DRAFT-field-noise-range (measured here, GAP 5 sample: the
100 x 100 block at the origin for each seed 1..64), DRAFT-noise-range-slack (0 to 0.05 of the measured span),
DRAFT-field-cost-share (15 to 55 percent), DRAFT-lane-contour 150 wu, DRAFT-lane-fallback (period 4 cells,
warp up to +-3 cells), DRAFT-lane-fallback-reach 4 cells, DRAFT-lane-share 0.30, DRAFT-lane-window 20 cells.
GAP 12 ruling (Architect 2026-10-20): om_field_apply_cost is ((v * f) * f) * f, cost times, left to right.
GAP 1 ruling (Architect 2026-10-14): om_lane_build takes the P1 om_layout_terrain callback struct and tests
water itself (height_at < 0.0); the test libraries link only csrc/terrain_noise.c, csrc/economy_field_noise.c
and P1's tests/csim/layout_stub_terrain.c. Gap 8 reading (null action): off-grid neighbours are skipped, the
window is clipped to the grid, the share is non-water lane cells / non-water cells, heights are read at the
cell centre ((gx + 0.5) * 100 wu).

Red reason on the built tree: csrc/field_noise.h and csrc/economy_field_noise.c do not exist, so the cc
build of library A fails (assert res.returncode == 0). test_ctrl_p1_stub_builds is green today: P1's stub
and csrc/terrain_noise.c build without the P2 files.
"""
import ctypes
import math
import pathlib
import random
import struct
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
STUB_C = REPO / "tests" / "csim" / "layout_stub_terrain.c"
# Same flags as the Makefile's release build (the pattern of test_PP_grid_margin_exact.py).
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]

R193_01 = ("R-193-01: the growth front is ragged from its first ring and a town is never a square or an "
           "octagon at any age; age %d seed %d share %.3f")
R193_09 = "R-193-09: the generator leaves open streets along the contour lines and rivers by rule"

SWEEP_SEEDS = range(1, 65)          # GAP 5 ruling: seeds 1..64
BLOCK = 100                         # GAP 5 ruling: the 100 x 100 block at the origin, 10,000 cells
FULL_SIDE = 240                     # GAP 5 ruling: the extremes over the full 240 x 240 grid are printed
SLACK = 0.05                        # DRAFT-noise-range-slack, 0 to 0.05 of the measured span
LANE_SHARE = 0.30                   # DRAFT-lane-share
LANE_WINDOW = 20                    # DRAFT-lane-window (41 x 41)
LANE_REACH = 4                      # DRAFT-lane-fallback-reach


# ---------------------------------------------------------------- build and load
def _cc(out, sources, opt="-O2", include=CSRC):
    flags = [opt if f == "-O2" else f for f in FLAGS]
    res = subprocess.run(["cc", *flags, "-I", str(include), "-shared", "-o", str(out),
                          *[str(s) for s in sources], "-lm"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]
    return out


HEIGHT_FN = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_void_p, ctypes.c_double, ctypes.c_double)
WALK_FN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_double, ctypes.c_double)
NEAR_FN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                           ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double))


class Terrain(ctypes.Structure):
    """Mirror of om_layout_terrain (csrc/layout_internal.h); filled by C stubs, no Python callbacks."""
    _fields_ = [("ctx", ctypes.c_void_p), ("height_at", HEIGHT_FN),
                ("walkable_at", WALK_FN), ("nearest_walkable", NEAR_FN)]


# Extra stubs, C source written to the temp dir (the brief: a constant-height stub, a ramp with contour
# lines along gx, a steep ramp of one contour interval per cell at level 0, and a split for the tie test).
EXTRA_STUBS_C = r"""
#include <stdint.h>
typedef struct om_stub_layout_terrain {
    void *ctx;
    double (*height_at)(void *ctx, double x, double y);
    int    (*walkable_at)(void *ctx, double x, double y);
    int    (*nearest_walkable)(void *ctx, double x, double y, double *ox, double *oy);
} om_stub_layout_terrain;
static const int32_t kinds[4] = {0, 1, 2, 3};
static double stub_h(void *ctx, double x, double y) {
    int32_t k = *(const int32_t *)ctx;
    (void)y;
    if (k == 0) return 500.0;                          /* constant height */
    if (k == 1) return 1000.0 + 0.15 * x;              /* ramp: 15 wu per 100 wu cell, contours along gx */
    if (k == 2) return 1000.0 + 1.5 * x;               /* steep ramp: 150 wu per cell, one interval per cell at level 0 */
    return x < 7000.0 ? 500.0 : 1000.0 + 1.5 * (x - 7000.0);   /* split: flat west of 7,000 wu, steep ramp east */
}
static int stub_w(void *ctx, double x, double y) { (void)ctx; (void)x; (void)y; return 1; }
static int stub_n(void *ctx, double x, double y, double *ox, double *oy) { (void)ctx; *ox = x; *oy = y; return 0; }
void om_test_stub(int32_t kind, om_stub_layout_terrain *out) {
    out->ctx = 0; out->height_at = 0; out->walkable_at = 0; out->nearest_walkable = 0;
    if (kind < 0 || kind > 3) return;
    out->ctx = (void *)&kinds[kind];
    out->height_at = stub_h; out->walkable_at = stub_w; out->nearest_walkable = stub_n;
}
"""
STUB_CONST, STUB_RAMP, STUB_STEEP, STUB_SPLIT = 0, 1, 2, 3


class LibA:
    """Library A: csrc/terrain_noise.c + csrc/economy_field_noise.c + P1's stub (+ the extra stubs)."""

    def __init__(self, path, stubs_path):
        so = ctypes.CDLL(str(path))
        self.so = so
        so.om_tn_fbm2.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int, ctypes.c_int32]
        so.om_tn_fbm2.restype = ctypes.c_int32
        so.om_field_hop_cost.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32]
        so.om_field_hop_cost.restype = ctypes.c_uint8
        so.om_field_noise_range.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32)]
        so.om_field_apply_cost.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_uint8]
        so.om_field_apply_cost.restype = ctypes.c_double
        so.om_lane_build.argtypes = [ctypes.POINTER(Terrain), ctypes.c_uint64, ctypes.c_int32,
                                     ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
                                     ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]
        so.om_stub_terrain.argtypes = [ctypes.c_int32, ctypes.POINTER(Terrain)]
        self.fbm, self.hop, self.apply = so.om_tn_fbm2, so.om_field_hop_cost, so.om_field_apply_cost
        if stubs_path is not None:
            xs = ctypes.CDLL(str(stubs_path))
            xs.om_test_stub.argtypes = [ctypes.c_int32, ctypes.POINTER(Terrain)]
            self.xs = xs

    def range(self):
        lo, hi = ctypes.c_int32(), ctypes.c_int32()
        self.so.om_field_noise_range(ctypes.byref(lo), ctypes.byref(hi))
        return lo.value, hi.value

    def p1_stub(self, kind):
        t = Terrain()
        self.so.om_stub_terrain(kind, ctypes.byref(t))
        assert t.height_at, "P1 stub kind %d left the struct zeroed" % kind
        return t

    def extra_stub(self, kind):
        t = Terrain()
        self.xs.om_test_stub(kind, ctypes.byref(t))
        assert t.height_at, "extra stub kind %d left the struct zeroed" % kind
        return t

    def lane(self, term, seed, side, cores):
        n = side * side
        cc = (ctypes.c_uint32 * len(cores))(*cores)
        lane = (ctypes.c_uint8 * n)()
        lev = (ctypes.c_uint8 * len(cores))()
        self.so.om_lane_build(ctypes.byref(term), seed, side, cc, len(cores), lane, lev)
        return bytes(lane), bytes(lev)


def _build_a(tmp, opt):
    stubs_c = tmp / "extra_stubs.c"
    stubs_c.write_text(EXTRA_STUBS_C)
    stubs = _cc(tmp / ("extra_stubs_%s.so" % opt), [stubs_c], opt=opt)
    so = _cc(tmp / ("lib_a_%s.so" % opt), [CSRC / "terrain_noise.c", CSRC / "economy_field_noise.c", STUB_C], opt=opt)
    return LibA(so, stubs)


class Lazy:
    """Builds library A on the first attribute access, inside the test body, so a missing P2 file is the
    test's own failing assertion (assert res.returncode == 0) and not a fixture error."""

    def __init__(self, make):
        self._make, self._real = make, None

    def __getattr__(self, name):
        if self._real is None:
            self._real = self._make()
        return getattr(self._real, name)


@pytest.fixture(scope="module")
def lib_a(tmp_path_factory):
    return Lazy(lambda: _build_a(tmp_path_factory.mktemp("p2_lib_a_o2"), "-O2"))


@pytest.fixture(scope="module")
def lib_a_o0(tmp_path_factory):
    return Lazy(lambda: _build_a(tmp_path_factory.mktemp("p2_lib_a_o0"), "-O0"))


# ---------------------------------------------------------------- positive control, green today
def test_ctrl_p1_stub_builds(tmp_path):
    """Positive control, green on the built tree: terrain_noise.c and P1's stub (without the P2 files)
    compile and link, om_stub_terrain(0, &t) fills the struct and t.height_at returns a number. So red
    elsewhere means the P2 files are missing and not that the harness is broken."""
    so = ctypes.CDLL(str(_cc(tmp_path / "ctrl.so", [CSRC / "terrain_noise.c", STUB_C])))
    so.om_stub_terrain.argtypes = [ctypes.c_int32, ctypes.POINTER(Terrain)]
    t = Terrain()
    so.om_stub_terrain(0, ctypes.byref(t))
    h0 = t.height_at(t.ctx, 0.0, 0.0)
    h1 = t.height_at(t.ctx, 12000.0, 12000.0)
    print("CTRL_P1 kind=0 height_at(0,0)=%r height_at(12000,12000)=%r" % (h0, h1))
    assert t.height_at and t.walkable_at and t.nearest_walkable, "stub left a callback null"
    assert h0 == h1 and h0 > 0.0, "flat stub height is not a positive constant: %r %r" % (h0, h1)


# ---------------------------------------------------------------- noise
@pytest.fixture(scope="module")
def sample(lib_a):
    """GAP 5 ruling: per seed 1..64, the 100 x 100 block at the origin: hop costs and fbm values.
    A callable, computed once on the first call (inside the test body)."""
    box = []

    def get():
        if not box:
            costs, fbms = {}, {}
            for seed in SWEEP_SEEDS:
                cs, fs = [], []
                for gy in range(BLOCK):
                    for gx in range(BLOCK):
                        cs.append(lib_a.hop(seed, gx, gy))
                        fs.append(lib_a.fbm(seed + 420, gx * 8192, gy * 8192, 3, 32768))
                costs[seed], fbms[seed] = cs, fs
            box.append((costs, fbms))
        return box[0]
    return get


def test_noise_cost_values(sample):
    """Spec :138 (noise): om_field_hop_cost over the 10,000 cells of each seed 1..64 is only 1, 2 or 3."""
    costs, _ = sample()
    seen = sorted({c for cs in costs.values() for c in cs})
    print("FIELD_COST_VALUES seen=%s cells=%d" % (seen, sum(len(v) for v in costs.values())))
    assert set(seen) <= {1, 2, 3}, "R-193-01: the field's spread is multiplied by seeded noise; costs seen %s" % seen
    assert len(seen) == 3, "R-193-01: the field's spread is multiplied by seeded noise; costs seen %s" % seen


def test_noise_cost_shares(sample):
    """Spec :138 (noise), DRAFT-field-cost-share: pooled over the sweep each cost holds 15 to 55 percent of
    the cells; the shares are printed (about 33 each is expected, spec rev 6a quantile buckets)."""
    costs, _ = sample()
    pooled = {1: 0, 2: 0, 3: 0}
    per_seed = {1: [], 2: [], 3: []}
    for seed, cs in costs.items():
        for c in (1, 2, 3):
            k = cs.count(c)
            pooled[c] += k
            per_seed[c].append(k / len(cs))
    total = sum(pooled.values())
    share = {c: pooled[c] / total for c in pooled}
    print("FIELD_COST_SHARE cost1=%.4f cost2=%.4f cost3=%.4f" % (share[1], share[2], share[3]))
    for c in (1, 2, 3):
        print("FIELD_COST_SHARE_SEED cost=%d min=%.4f max=%.4f" % (c, min(per_seed[c]), max(per_seed[c])))
    for c in (1, 2, 3):
        assert 0.15 <= share[c] <= 0.55, \
            "R-193-01: the field's spread is multiplied by seeded noise; cost %d share %.3f outside 0.15..0.55" % (c, share[c])


def test_noise_deterministic(lib_a):
    """Spec :138: the same seed reproduces, two seeds differ."""
    def grid(seed):
        return [lib_a.hop(seed, gx, gy) for gy in range(BLOCK) for gx in range(BLOCK)]
    a, b, c = grid(7), grid(7), grid(8)
    differ = sum(1 for x, y in zip(a, c) if x != y)
    print("FIELD_DETERMINISTIC seed7_twice_equal=%s seed7_vs_seed8_differing_cells=%d" % (a == b, differ))
    assert a == b, "R-193-01: seeded noise: the same seed must reproduce its costs"
    assert differ > 0, "R-193-01: seeded noise: two seeds must differ somewhere"


def _bits(x):
    return struct.pack("<d", x)


def _pairs():
    rng = random.Random(20261021)
    return [(rng.uniform(0.02, 1.0), rng.uniform(0.97, 0.99)) for _ in range(2000)]


def test_noise_apply_cost(lib_a):
    """GAP 12 ruling (Architect 2026-10-20): om_field_apply_cost(v, f, c) is ((v * f) * f) * f with c
    multiplications, left to right, bit for bit; for c = 1 it equals v * f."""
    bad = []
    for v, f in _pairs():
        want = {1: v * f, 2: (v * f) * f, 3: ((v * f) * f) * f}
        for c in (1, 2, 3):
            got = lib_a.apply(v, f, c)
            if _bits(got) != _bits(want[c]):
                bad.append((c, v, f, got, want[c]))
    print("FIELD_APPLY_COST samples=%d mismatches=%d first=%r" % (len(_pairs()), len(bad), bad[:1]))
    assert not bad, "GAP 12: om_field_apply_cost must be ((v * f) * f) * f left to right: %r" % bad[:1]


def test_ctrl_noise_apply_cost_order_detector(lib_a):
    """Control for test_noise_apply_cost: the product in the other order, v * (f * f * f), differs from the
    helper for at least one sample pair, so the bit-for-bit detector can tell the two orders apart."""
    differ = sum(1 for v, f in _pairs() if _bits(lib_a.apply(v, f, 3)) != _bits(v * (f * f * f)))
    print("CTRL_APPLY_COST_ORDER cost3 pairs_where_other_order_differs=%d of %d" % (differ, len(_pairs())))
    assert differ > 0, "GAP 12: the other-order product never differs from the helper; the detector cannot tell the orders apart"


def test_noise_pinned_range(lib_a, sample):
    """Spec :138 (the pinned range holds), DRAFT-field-noise-range, DRAFT-noise-range-slack, GAP 5: lo <= the
    measured minimum, the measured maximum <= hi, and each pin lies within 0 to 0.05 of the measured span of
    its measured extreme. The extremes over the full 240 x 240 grid for the same seeds are printed."""
    _, fbms = sample()
    mn = min(min(v) for v in fbms.values())
    mx = max(max(v) for v in fbms.values())
    lo, hi = lib_a.range()
    full_mn, full_mx = None, None
    for seed in SWEEP_SEEDS:
        for gy in range(FULL_SIDE):
            for gx in range(FULL_SIDE):
                f = lib_a.fbm(seed + 420, gx * 8192, gy * 8192, 3, 32768)
                if full_mn is None or f < full_mn:
                    full_mn = f
                if full_mx is None or f > full_mx:
                    full_mx = f
    print("NOISE_RANGE measured_min=%d measured_max=%d lo=%d hi=%d" % (mn, mx, lo, hi))
    print("NOISE_RANGE_FULL240 min=%d max=%d inside_pin=%s" % (full_mn, full_mx, lo <= full_mn and full_mx <= hi))
    span = mx - mn
    assert lo <= mn, "DRAFT-field-noise-range: lo %d above the measured minimum %d" % (lo, mn)
    assert mx <= hi, "DRAFT-field-noise-range: hi %d below the measured maximum %d" % (hi, mx)
    assert mn - lo <= SLACK * span, "DRAFT-noise-range-slack: lo %d is more than 0.05 of the span %d below %d" % (lo, span, mn)
    assert hi - mx <= SLACK * span, "DRAFT-noise-range-slack: hi %d is more than 0.05 of the span %d above %d" % (hi, span, mx)


# ---------------------------------------------------------------- lane model (independent Python model of spec :133)
def heights(term, side):
    return [term.height_at(term.ctx, (gx + 0.5) * 100.0, (gy + 0.5) * 100.0)
            for gy in range(side) for gx in range(side)]


def warp(lib, seed, side):
    wx, wy = [], []
    for gy in range(side):
        for gx in range(side):
            fx = lib.fbm(seed + 430, gx * 8192, gy * 8192, 2, 32768)
            fy = lib.fbm(seed + 440, gx * 8192, gy * 8192, 2, 32768)
            wx.append((3 * fx + 32768) // 65536)         # floor_div by hand semantics: Python // floors
            wy.append((3 * fy + 32768) // 65536)
    return wx, wy


def contour_mask(H, side, level):
    interval = 150.0 * (1 << level)                      # DRAFT-lane-contour 150 wu
    fl = [math.floor(h / interval) for h in H]
    m = [0] * (side * side)
    for gy in range(side):
        for gx in range(side):
            i = gy * side + gx
            if gx + 1 < side and fl[i + 1] != fl[i]:
                m[i] = 1
            if gy + 1 < side and fl[i + side] != fl[i]:
                m[i] = 1
    return m


def water_adj_mask(H, side):
    m = [0] * (side * side)
    for gy in range(side):
        for gx in range(side):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and 0 <= gx + dx < side and 0 <= gy + dy < side and H[(gy + dy) * side + gx + dx] < 0.0:
                        m[gy * side + gx] = 1
    return m


def dilate(mask, side, r):
    rows = [0] * (side * side)
    for gy in range(side):
        for gx in range(side):
            if mask[gy * side + gx]:
                for x in range(max(0, gx - r), min(side, gx + r + 1)):
                    rows[gy * side + x] = 1
    out = [0] * (side * side)
    for gy in range(side):
        for gx in range(side):
            if rows[gy * side + gx]:
                for y in range(max(0, gy - r), min(side, gy + r + 1)):
                    out[y * side + gx] = 1
    return out


def fallback_cond(W, side, level, i):
    period = 4 * (1 << level)                            # DRAFT-lane-fallback, doubling with the level
    gx, gy = i % side, i // side
    return (gx + W[0][i]) % period == period - 1 or (gy + W[1][i]) % period == period - 1


def model_lane(H, W, side, level):
    """contour | water | fallback where no contour or water lane lies within 4 cells (Chebyshev)."""
    contour = contour_mask(H, side, level)
    water = water_adj_mask(H, side)
    anyl = [a | b for a, b in zip(contour, water)]
    near = dilate(anyl, side, LANE_REACH)
    lane = [1 if (anyl[i] or (not near[i] and fallback_cond(W, side, level, i))) else 0 for i in range(side * side)]
    return lane, contour, water


def window_share(lane, H, side, core):
    cx, cy = core % side, core // side
    nonwater = lanes = 0
    for gy in range(max(0, cy - LANE_WINDOW), min(side, cy + LANE_WINDOW + 1)):
        for gx in range(max(0, cx - LANE_WINDOW), min(side, cx + LANE_WINDOW + 1)):
            i = gy * side + gx
            if H[i] >= 0.0:
                nonwater += 1
                lanes += 1 if lane[i] else 0
    return (lanes / nonwater) if nonwater else 0.0


# ---------------------------------------------------------------- lanes
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_lane_flat_stub_fallback_only(lib_a, seed):
    """Spec :138 (lanes): on the flat stub (constant height, no water) no cell is a contour or water lane
    cell, every lane cell is a fallback cell of the warped period grid, and the core's level reaches 1 (the
    period-4 grid is 44 percent lane, above the 30 percent cap)."""
    side = 120
    core = 60 * side + 60
    t = lib_a.p1_stub(0)
    H = heights(t, side)
    lane, lev = lib_a.lane(t, seed, side, [core])
    level = lev[0]
    W = warp(lib_a, seed, side)
    expect, contour, water = model_lane(H, W, side, level)
    share0 = window_share([1 if fallback_cond(W, side, 0, i) else 0 for i in range(side * side)], H, side, core)
    print("LANE_FLAT seed=%d level=%d lane_cells=%d contour=%d water=%d level0_window_share=%.3f"
          % (seed, level, sum(lane), sum(contour), sum(water), share0))
    assert sum(contour) == 0 and sum(water) == 0, R193_09
    assert list(lane) == expect, R193_09 + ": the lane mask on the flat stub is not the fallback grid only"
    assert level == 1, R193_09 + ": the flat stub's core level is %d, expected 1" % level
    assert share0 > LANE_SHARE, R193_09 + ": the period-4 grid is only %.3f lane" % share0


@pytest.mark.parametrize("seed", [1, 2])
def test_lane_ramp_follows_contours(lib_a, seed):
    """Spec :138 (lanes): on the ramp stub lanes lie along contours: every cell whose floor(h / (150 * 2^L))
    differs from its east or its gy + 1 neighbour is a lane cell (independent Python model), and the whole
    mask is contour lanes plus the fallback grid where no contour is within 4 cells."""
    side = 120
    core = 60 * side + 60
    t = lib_a.extra_stub(STUB_RAMP)
    H = heights(t, side)
    lane, lev = lib_a.lane(t, seed, side, [core])
    level = lev[0]
    W = warp(lib_a, seed, side)
    expect, contour, water = model_lane(H, W, side, level)
    contour_cols = sorted({i % side for i in range(side * side) if contour[i]})
    missing = [i for i in range(side * side) if contour[i] and not lane[i]]
    print("LANE_RAMP seed=%d level=%d contour_cells=%d contour_columns=%s missing=%d"
          % (seed, level, sum(contour), contour_cols[:8], len(missing)))
    assert sum(contour) > 0, R193_09 + ": the ramp has no contour cells in the model"
    assert not missing, R193_09 + ": %d contour cells are not lane cells" % len(missing)
    assert list(lane) == expect, R193_09 + ": the ramp's lane mask is not contour lanes plus the fallback grid"


def test_ctrl_lane_constant_height_zero_contour(lib_a):
    """Control (spec :138): the constant-height stub gives zero contour lane cells and the ramp gives more
    than zero (the counter works); on the constant stub every C lane cell is a fallback cell."""
    side, seed = 120, 1
    core = 60 * side + 60
    counts = {}
    for name, kind in (("constant", STUB_CONST), ("ramp", STUB_RAMP)):
        t = lib_a.extra_stub(kind)
        H = heights(t, side)
        counts[name] = sum(contour_mask(H, side, 0))
    t = lib_a.extra_stub(STUB_CONST)
    H = heights(t, side)
    lane, lev = lib_a.lane(t, seed, side, [core])
    W = warp(lib_a, seed, side)
    expect, _, _ = model_lane(H, W, side, lev[0])
    print("CTRL_LANE_CONTOUR constant=%d ramp=%d constant_lane_is_fallback_only=%s" % (counts["constant"], counts["ramp"], list(lane) == expect))
    assert counts["constant"] == 0, R193_09 + ": the constant stub shows contour cells"
    assert counts["ramp"] > 0, R193_09 + ": the contour counter finds nothing on the ramp"
    assert list(lane) == expect, R193_09 + ": a lane cell on the constant stub is not a fallback cell"


def test_lane_lake_shore_ring(lib_a):
    """Spec :138 (lanes): on the lake stub (P1 kind 1) every non-water cell with a water neighbour among its
    eight is a lane cell (the shore ring)."""
    side, seed = 160, 3
    t = lib_a.p1_stub(1)
    H = heights(t, side)
    lane, lev = lib_a.lane(t, seed, side, [30 * side + 30])
    wa = water_adj_mask(H, side)
    ring = [i for i in range(side * side) if H[i] >= 0.0 and wa[i]]
    missing = [i for i in ring if not lane[i]]
    print("LANE_LAKE shore_cells=%d missing=%d water_cells=%d" % (len(ring), len(missing), sum(1 for h in H if h < 0.0)))
    assert len(ring) > 0, R193_09 + ": no shore cell on the lake stub"
    assert not missing, R193_09 + ": %d shore cells are not lane cells" % len(missing)


def _c(gx, gy, side=160):
    return gy * side + gx


CAP_SCENES = {
    # name: (stub source, kind, side, cores at least 41 cells apart so every core window holds only its own cells)
    "flat": ("p1", 0, 160, [_c(40, 40), _c(120, 40), _c(40, 120), _c(120, 120)]),
    "lake": ("p1", 1, 160, [_c(30, 30), _c(130, 30), _c(80, 80), _c(30, 130), _c(130, 130)]),
    "rolling": ("p1", 2, 160, [_c(30, 30), _c(100, 30), _c(30, 100), _c(100, 100)]),
    "ramp": ("x", STUB_RAMP, 160, [_c(30, 30), _c(100, 30), _c(30, 100), _c(100, 100)]),
    "split": ("x", STUB_SPLIT, 160, [_c(20, 60), _c(100, 60)]),
}


@pytest.mark.parametrize("scene", sorted(CAP_SCENES))
def test_lane_cap(lib_a, scene):
    """Spec :138 (lanes), DRAFT-lane-share, DRAFT-lane-window: for every core window (41 x 41, clipped) the
    lane share of non-water cells is at most 30 percent, or the core is at level 3; the flat stub reaches
    level 1. The cores are at least 41 cells apart so each window holds only cells of its own core."""
    src, kind, side, cores = CAP_SCENES[scene]
    t = lib_a.p1_stub(kind) if src == "p1" else lib_a.extra_stub(kind)
    H = heights(t, side)
    lane, lev = lib_a.lane(t, 5, side, cores)
    shares = [window_share(lane, H, side, c) for c in cores]
    print("LANE_CAP scene=%s levels=%s shares=%s" % (scene, list(lev), ["%.3f" % s for s in shares]))
    for c, s, lv in zip(cores, shares, lev):
        assert lv <= 3, R193_09 + ": level %d above 3" % lv
        assert s <= LANE_SHARE or lv == 3, R193_09 + ": core %d window lane share %.3f above 0.30 at level %d" % (c, s, lv)
    if scene == "flat":
        assert list(lev) == [1] * len(cores), R193_09 + ": the flat stub levels are %s, expected all 1" % list(lev)


def test_ctrl_lane_steep_ramp(lib_a):
    """Control (spec :138): on the steep ramp (one contour interval per cell) more than 30 percent of a
    window is lane at level 0, so the share detector FAILS there, and the cap test passes only because the
    level rises. The level seen is printed."""
    side, seed = 120, 1
    core = 60 * side + 60
    t = lib_a.extra_stub(STUB_STEEP)
    H = heights(t, side)
    W = warp(lib_a, seed, side)
    lane0, _, _ = model_lane(H, W, side, 0)
    share0 = window_share(lane0, H, side, core)
    lane, lev = lib_a.lane(t, seed, side, [core])
    share_l = window_share(lane, H, side, core)
    print("CTRL_LANE_STEEP level0_share=%.3f level_seen=%d share_at_level=%.3f" % (share0, lev[0], share_l))
    assert share0 > LANE_SHARE, R193_09 + ": level-0 share %.3f is not above 0.30; the detector cannot fail here" % share0
    assert lev[0] >= 1, R193_09 + ": the level did not rise on the steep ramp"
    assert share_l <= LANE_SHARE or lev[0] == 3, R193_09 + ": share %.3f above 0.30 at level %d" % (share_l, lev[0])


def test_lane_ties_to_lower_core(lib_a):
    """Spec :138 (lanes): cells equally near two cores (Chebyshev) take the level of the lower core index.
    The split stub is flat west of 7,000 wu (core 0, level 1) and a steep ramp east (core 1, level 2), so the
    tie column gx = 60 reads differently at the two levels. DOCUMENTED: reordering the core list can change
    those cells; the swapped order is asserted to follow the new lower index."""
    side, seed = 160, 4
    c0, c1 = 60 * side + 20, 60 * side + 100
    t = lib_a.extra_stub(STUB_SPLIT)
    H = heights(t, side)
    W = warp(lib_a, seed, side)
    ties = [gy * side + 60 for gy in range(20, 101)]
    contour_near = dilate(contour_mask(H, side, 0), side, LANE_REACH)
    assert not any(contour_near[i] for i in ties), "split stub has a contour near the tie column"
    lane_a, lev_a = lib_a.lane(t, seed, side, [c0, c1])
    lane_b, lev_b = lib_a.lane(t, seed, side, [c1, c0])
    la, lb = lev_a[0], lev_a[1]
    fb = lambda i, lv: 1 if fallback_cond(W, side, lv, i) else 0
    print("LANE_TIES levels_core0=%d core1=%d swapped=%s tie_cells=%d differing_between_levels=%d"
          % (la, lb, list(lev_b), len(ties), sum(1 for i in ties if fb(i, la) != fb(i, lb))))
    assert la != lb, R193_09 + ": the two cores have the same level %d; the tie cannot be seen" % la
    assert list(lev_b) == [lb, la], R193_09 + ": a core's level changed with the core order"
    assert any(fb(i, la) != fb(i, lb) for i in ties), R193_09 + ": the tie cells read the same at both levels"
    assert all(lane_a[i] == fb(i, la) for i in ties), R193_09 + ": a tie cell does not take the lower core's level"
    assert all(lane_b[i] == fb(i, lb) for i in ties), R193_09 + ": after reordering, a tie cell does not take the new lower core's level"


def test_lane_deterministic(lib_a, lib_a_o0):
    """Spec :138 (lanes): same inputs give byte-equal output, and the same bytes at -O0 and -O2."""
    side, seed = 160, 6
    cores = [30 * side + 30, 100 * side + 100]
    t2 = lib_a.p1_stub(1)
    t0 = lib_a_o0.p1_stub(1)
    a1, l1 = lib_a.lane(t2, seed, side, cores)
    a2, l2 = lib_a.lane(t2, seed, side, cores)
    b, lb = lib_a_o0.lane(t0, seed, side, cores)
    print("LANE_DETERMINISTIC repeat_equal=%s o0_equals_o2=%s lane_cells=%d" % (a1 == a2 and l1 == l2, a1 == b and l1 == lb, sum(a1)))
    assert a1 == a2 and l1 == l2, R193_09 + ": the same inputs gave different lane bytes"
    assert a1 == b and l1 == lb, R193_09 + ": -O0 and -O2 builds gave different lane bytes"
