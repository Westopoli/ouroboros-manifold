# Rule pins: R-193-01@451aaa, R-193-09@052634, R-191-03@91c415, R-191-06@ffc11c
"""VG-P2 (places lane, spec rev 6a): the growth probe, its field and its shape. Tests for csrc/growth_probe.c
(om_growth_probe_run) on the real hop-cost noise of csrc/economy_field_noise.c.

Rule pins are on line 1 (the rule text below also names R-191-03 and R-191-06).

Rules proved, word for word (docs/bible/epics/E-17-map-generation.md):

R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.

(docs/bible/epics/E-17-map-generation.md:315. "the growth front is ragged from its first ring and a town is
never a square or an octagon at any age" is the sentence this file proves: the first-ring spread, the front
shape, the lots shape, the seeds-differ test and the noise-off control each carry it in their assertion
message in the form of spec rev 6a, `R-193-01: ...; age %d seed %d share %.3f`.)

R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).

(docs/bible/epics/E-17-map-generation.md:323. Lanes are not built by the probe: it has none, and "Lane cells
are never lots"; the lane tests are in test_VG_P_p2_field_noise_lanes.py.)

Spec sentences implemented (docs/northstar/plans/2026-10-13-places-lane-spec.md, P2 section, :113-138):
  "[B R-193-01@451aaa: the field's spread is also multiplied by seeded noise of the terrain generator's family
   with its own salt, so the growth front is ragged from its first ring and a town is never a square or an
   octagon at any age]"
  "every cell carries a **hop cost** of 1, 2 or 3 taken from seeded noise of the terrain family, and the field
   crosses a cell of cost c as if it were c cells wide, in value and in time."
  "the hop into `j` is accepted at growth step `s` only when `floor_mod(s, cost[j]) == 0`"
  "The drawn town is the inner part of that field: lots are created in **descending `density`** (ties by cell
   index) under the quota below, so the town's outline is a density contour of the ragged field, not a disc
   and not a square."
  "`DRAFT-shape-harm` is **0.5, pinned from the controls, not from the probe** (the auditor measured: clean
   square 0.99, diamond 0.99, octagon 0.997, noisy square 0.80, noise blobs 0.13 to 0.20; a rasterised disc
   0.48 to 0.84, so a disc is not a control); the probe prints its per-seed value beside the pin. A front
   value above 0.5 at steps 10 and 20, a lots value above 0.5 at any age from 20, or a first-ring spread under
   `DRAFT-first-ring-spread` 2 is Westley's number"
  "**first ring**: after 10 growth steps the eight compass-ray reaches are not all equal and the largest
   exceeds the smallest by at least `DRAFT-first-ring-spread` 2 cells, and after 10 and 20 steps the reached
   set (cells with `P > 0`) has a 32-sector radial profile whose harmonic 4 plus 8 share is under
   `DRAFT-shape-harm` 0.5 (at steps 3 and 5 ... printed, not asserted)"
  "two seeds give lot sets whose symmetric difference is at least 10 percent of their union
   (`DRAFT-seed-differ`; asserted at ages 20 and up, TD-VG-P-1; age 10 prints its ratios and asserts nothing)"

The bible gives no number for the cost buckets, the lattice, the window, the share or the pin. Each number
below is the spec's or a ruling's, cited as "spec rev 6a, DRAFT-<name>": DRAFT-shape-harm 0.5,
DRAFT-shape-sectors 32, DRAFT-first-ring-spread 2, DRAFT-seed-differ 0.10, DRAFT-death-floor 100,
DRAFT-death-steps 600, DRAFT-lot-fill 0.6, DRAFT-lots-per-age 15, DRAFT-lot-cap 8,192 (PROBE_LOT_CAP, passed
as the tenth argument, GAP 2 ruling), DRAFT-shape-corr 0.6 (a print label only), the controls' sector noise
0.1 of the radius and decay 1.01 (spec "Numbers and drafts", test-only constants).

Scope decisions read from spec rev 6a (origin/main 57ca6949), which postdates the brief's rev 6 text:
  * the field tests (ring bound, east reach, death step) use side 400 with the core at (200, 200), ages 150
    and 400 (box moved, Architect 2026-10-21, GAP 4 superseded by gaps.box; spec :138 "reach under 199");
    the death step is asserted at age 400 (spec :138: age 150 cannot show a death under the active-list rule);
  * the front harmonic share is asserted at steps 10 and 20 and printed at steps 3 and 5 (spec :138);
  * the probe accepts side 1..400 (spec :125), so the bad-side case is 401;
  * the first-ring, front, shape, lots and determinism tests use side 240 with the core at (120, 120) (brief).
  * the lots harmonic share is asserted at ages 20 and later and printed at age 10 (spec rev 6a: at age 10 a
    town has about 86 lots and the share follows the list order the bookkeeping rule sets; the 0.5 draft is
    unchanged);
  * the divergence control runs at age 40 on side 400, seed 1 (spec rev 6a, Architect 2026-10-21);
  * the next active list is built in one pass over the current list in its order: for each source the cells it
    activates this step in the hop's neighbour order, then the source itself when it keeps budget.
TD-VG-P-1 (GAP 11 ruling): the seeds-differ test is asserted at ages 20 and up; age 10 is printed only.

Red reason on the built tree: csrc/field_noise.h, csrc/economy_field_noise.c and csrc/growth_probe.c do
not exist, so the cc build of library B fails (assert res.returncode == 0).
"""
import ctypes
import math
import pathlib
import random
import re
import shutil
import subprocess
import types

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
STUB_C = REPO / "tests" / "csim" / "layout_stub_terrain.c"
# Same flags as the Makefile's release build (the pattern of test_PP_grid_margin_exact.py).
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]

R193_01 = ("R-193-01: the growth front is ragged from its first ring and a town is never a square or an "
           "octagon at any age; age %d seed %d share %.3f")

PROBE_LOT_CAP = 8192            # GAP 2 ruling: the value P3 raises OM_LOT_CAP to
HARM_PIN = 0.5                  # DRAFT-shape-harm
SECTORS = 32                    # DRAFT-shape-sectors
SPREAD_MIN = 2                  # DRAFT-first-ring-spread
DIFFER_MIN = 0.10               # DRAFT-seed-differ
DEATH_FLOOR, DEATH_STEPS = 100, 600   # DRAFT-death-floor, DRAFT-death-steps
SEEDS = range(1, 11)            # DRAFT-test-samples: 10 seeds for the death-step and shape tests
SIDE, CORE_XY = 240, (120, 120)             # shape, first-ring, lots, determinism (brief)
BOX_SIDE, BOX_XY = 400, (200, 200)          # ring bound, east reach, death step (spec rev 6a)
SHAPE_AGES = (10, 20, 30, 40, 100, 200)
DIRS8 = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1)]   # N S E W NE NW SE SW


def cell(xy, side):
    return xy[1] * side + xy[0]


# ---------------------------------------------------------------- build and load
def _cc(out, sources, opt="-O2", include=CSRC):
    flags = [opt if f == "-O2" else f for f in FLAGS]
    res = subprocess.run(["cc", *flags, "-I", str(include), "-shared", "-o", str(out),
                          *[str(s) for s in sources], "-lm"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]
    return out


class Probe:
    """om_growth_probe_run through ctypes; caches the summaries of the runs it makes."""

    def __init__(self, path):
        so = ctypes.CDLL(str(path))
        f = so.om_growth_probe_run
        f.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                      ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_double),
                      ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint8),
                      ctypes.POINTER(ctypes.c_int32), ctypes.c_int32]
        f.restype = ctypes.c_int32
        self.f = f
        self.cache = {}

    def raw(self, seed, side, n_cores, cores, ages, P, D, L, death, lot_cap):
        return self.f(seed, side, n_cores, cores, ages, P, D, L, death, lot_cap)

    def run(self, seed, side, cores, ages, lot_cap=PROBE_LOT_CAP):
        n = side * side
        cc = (ctypes.c_uint32 * len(cores))(*cores)
        aa = (ctypes.c_int32 * len(ages))(*ages)
        P, D, L = (ctypes.c_double * n)(), (ctypes.c_double * n)(), (ctypes.c_uint8 * n)()
        death = ctypes.c_int32(-12345)
        ret = self.f(seed, side, len(cores), cc, aa, P, D, L, ctypes.byref(death), lot_cap)
        return types.SimpleNamespace(ret=ret, P=P, D=D, L=L, death=death.value, side=side)

    def single(self, seed, side, xy, age, lot_cap=PROBE_LOT_CAP):
        return self.run(seed, side, [cell(xy, side)], [age], lot_cap)


def digest(res):
    return (res.ret, res.death, bytes(res.P), bytes(res.D), bytes(res.L))


class Libs:
    """Lazy builds, made inside the test body so a missing P2 file is the test's own failing assertion."""

    def __init__(self, tmp_path_factory):
        self.tmp, self._probe = tmp_path_factory, {}

    def _sources(self):
        return [CSRC / "terrain_noise.c", CSRC / "economy_field_noise.c", STUB_C, CSRC / "growth_probe.c"]

    def probe(self, opt="-O2"):
        """Library B = library A + csrc/growth_probe.c."""
        if opt not in self._probe:
            d = self.tmp.mktemp("p2_lib_b")
            self._probe[opt] = Probe(_cc(d / "lib_b.so", self._sources(), opt=opt))
        return self._probe[opt]

    def _patched(self, name, subs):
        """A patched COPY of csrc in a temp dir (the pattern of test_PP_grid_margin_exact.py): every
        csrc/*.c of the copy is compiled. The real build is made first, so a missing P2 file fails the same way."""
        self.probe()
        if name not in self._probe:
            d = self.tmp.mktemp("p2_" + name)
            src = d / "csrc"
            shutil.copytree(CSRC, src, ignore=shutil.ignore_patterns("pipe"))
            f = src / "growth_probe.c"
            text = f.read_text()
            for rx, repl in subs:
                text, n = rx.subn(repl, text)
                assert n == 1, "%s not found exactly once in growth_probe.c (found %d)" % (rx.pattern, n)
            f.write_text(text)
            self._probe[name] = Probe(_cc(d / ("lib_%s.so" % name), sorted(src.glob("*.c")), include=src))
        return self._probe[name]

    def noise_off(self):
        """Spec :138 noise off: growth_probe.c's one '#define PROBE_HOP_COST(seed, gx, gy) ...' line has its
        right-hand side replaced by 1."""
        return self._patched("noise_off", [(re.compile(r"^#define PROBE_HOP_COST\(seed, gx, gy\).*$", re.M),
                                            "#define PROBE_HOP_COST(seed, gx, gy) 1")])

    def diverged(self):
        """GAP 3 ruling: PROBE_BASE_DECAY and PROBE_NONWATER_FAR both 1.01 (edge factor 1.0201, above 1)."""
        return self._patched("diverged", [(re.compile(r"^#define PROBE_BASE_DECAY .*$", re.M), "#define PROBE_BASE_DECAY 1.01"),
                                          (re.compile(r"^#define PROBE_NONWATER_FAR .*$", re.M), "#define PROBE_NONWATER_FAR 1.01")])


@pytest.fixture(scope="module")
def libs(tmp_path_factory):
    return Libs(tmp_path_factory)


# ---------------------------------------------------------------- measurements (pure Python)
def sector_of(dx, dy):
    return int(math.floor(math.atan2(dy, dx) / (2 * math.pi / SECTORS))) % SECTORS


def profile(cells_xy, cx, cy):
    """r(theta): the largest distance in cells from the core cell of any given cell in each of 32 sectors;
    an empty sector is 0."""
    r = [0.0] * SECTORS
    for gx, gy in cells_xy:
        dx, dy = gx - cx, gy - cy
        d = math.hypot(dx, dy)
        if d > 0.0:
            s = sector_of(dx, dy)
            if d > r[s]:
                r[s] = d
    return r


def harm_share(r):
    """One-sided AC power spectrum of the 32 samples (mean removed, DFT, harmonics 1 to 16):
    (power of harmonics 4 and 8) / (power of harmonics 1 to 16); 0.0 when the total AC power is 0."""
    n = len(r)
    m = sum(r) / n
    x = [v - m for v in r]
    pw = []
    for k in range(1, 17):
        re_ = sum(x[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        im_ = sum(x[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        pw.append(re_ * re_ + im_ * im_)
    tot = sum(pw)
    return (pw[3] + pw[7]) / tot if tot > 1e-9 else 0.0


def rot_corr(r, shift):
    """Pearson correlation of r(theta) with itself rotated by `shift` sectors (8 = 90 degrees, 4 = 45)."""
    a, b = r, r[shift:] + r[:shift]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den > 1e-12 else 0.0


def reached_cells(P, side, cx, cy, radius):
    out = []
    for gy in range(max(0, cy - radius), min(side, cy + radius + 1)):
        for gx in range(max(0, cx - radius), min(side, cx + radius + 1)):
            if P[gy * side + gx] > 0.0:
                out.append((gx, gy))
    return out


def ray_reach(P, side, cx, cy, d):
    """The largest distance k in cells along the ray d with P > 0 (0 when none)."""
    best, k = 0, 1
    while 0 <= cx + k * d[0] < side and 0 <= cy + k * d[1] < side:
        if P[(cy + k * d[1]) * side + cx + k * d[0]] > 0.0:
            best = k
        k += 1
    return best


def ring_max(P, side, cx, cy, kmax=20):
    out = []
    for k in range(1, kmax + 1):
        m = 0.0
        for gy in range(cy - k, cy + k + 1):
            for gx in range(cx - k, cx + k + 1):
                if max(abs(gx - cx), abs(gy - cy)) == k and 0 <= gx < side and 0 <= gy < side:
                    m = max(m, P[gy * side + gx])
        out.append(m)
    return out


def ring_ok(rm):
    """P at Chebyshev ring k is at most 0.99^k for k in 1..20."""
    return all(rm[k - 1] <= 0.99 ** k for k in range(1, len(rm) + 1))


def first_ring_ok(reaches):
    """The first-ring detector: the eight compass reaches are not all equal and the largest exceeds the
    smallest by at least DRAFT-first-ring-spread."""
    return len(set(reaches)) > 1 and max(reaches) - min(reaches) >= SPREAD_MIN


def front(probe, seed, age):
    """The field after `age` growth steps: cached summary of one centred core on the 240 box."""
    key = ("front", seed, age)
    if key not in probe.cache:
        res = probe.single(seed, SIDE, CORE_XY, age)
        assert res.ret >= 0, "probe returned %d" % res.ret
        cx, cy = CORE_XY
        reaches = [ray_reach(res.P, SIDE, cx, cy, d) for d in DIRS8]
        cells = reached_cells(res.P, SIDE, cx, cy, age + 2)
        probe.cache[key] = (reaches, harm_share(profile(cells, cx, cy)), len(cells))
    return probe.cache[key]


def box_run(probe, seed, age):
    """One centred core on the 400 box (spec rev 6a): ring maxima, east reach, death step."""
    key = ("box", seed, age)
    if key not in probe.cache:
        res = probe.single(seed, BOX_SIDE, BOX_XY, age)
        assert res.ret >= 0, "probe returned %d" % res.ret
        cx, cy = BOX_XY
        probe.cache[key] = (ring_max(res.P, BOX_SIDE, cx, cy), ray_reach(res.P, BOX_SIDE, cx, cy, (1, 0)), res.death)
    return probe.cache[key]


def town(probe, seed, age):
    """The lots of one centred core of `age` on the 240 box: profile, lot set, death step, rotation correlations."""
    key = ("town", seed, age)
    if key not in probe.cache:
        res = probe.single(seed, SIDE, CORE_XY, age)
        assert res.ret >= 0, "probe returned %d" % res.ret
        cx, cy = CORE_XY
        idx = [i for i in range(SIDE * SIDE) if res.L[i] != 255]
        r = profile([(i % SIDE, i // SIDE) for i in idx], cx, cy)
        probe.cache[key] = (r, frozenset(idx), res.ret, res.death, rot_corr(r, 8), rot_corr(r, 4))
    return probe.cache[key]


# ---------------------------------------------------------------- field (probe, field)
@pytest.mark.parametrize("age", [150, 400])
def test_field_ring_bound(libs, age):
    """Spec :138 (probe, field), the ring bound: one centred core (side 400, core (200, 200)); P at Chebyshev
    ring k is at most 0.99^k for k in 1..20, seeds 1..10, at ages 150 and 400."""
    probe = libs.probe()
    worst = {}
    for seed in SEEDS:
        rm, _, _ = box_run(probe, seed, age)
        worst[seed] = max(rm[k - 1] / 0.99 ** k for k in range(1, 21))
        print("FIELD_RING age=%d seed=%d worst_ratio_to_bound=%.4f ring1=%.4f ring20=%.4f" % (age, seed, worst[seed], rm[0], rm[19]))
    bad = [s for s in SEEDS if worst[s] > 1.0]
    assert not bad, "P above 0.99^k at some ring for seeds %s (age %d)" % (bad, age)


@pytest.mark.parametrize("age", [150, 400])
def test_field_front_inside_box(libs, age):
    """Spec :138 (probe, field), GAP 4 superseded by the box move (Architect 2026-10-21): the farthest east-ray
    cell with P > 0 lies strictly inside the 400 box, reach under 199 cells, printed at ages 150 and 400.
    A seed touching 199 is reported to the Architect before anything is changed (stop 'front-touches-border')."""
    probe = libs.probe()
    reach = {s: box_run(probe, s, age)[1] for s in SEEDS}
    for s in SEEDS:
        print("PROBE_EAST age=%d seed=%d east=%d" % (age, s, reach[s]))
    bad = {s: r for s, r in reach.items() if r >= 199}
    assert not bad, "front touches the border of the box at age %d: %s" % (age, bad)


def test_field_death_step(libs):
    """Spec :138 (probe, field), DRAFT-death-floor 100, DRAFT-death-steps 600: run at age 400 on the 400 box
    (age 150 cannot show a death under the active-list rule), out_death_step is above 100 and below 600.
    A measured step outside the bounds is reported to the Architect before anything is changed (stop
    'death-step-outside'). Printed: PROBE_DEATH seed=<s> death=<d> east=<r>."""
    probe = libs.probe()
    rows = {}
    for s in SEEDS:
        _, east, death = box_run(probe, s, 400)
        rows[s] = (death, east)
        print("PROBE_DEATH seed=%d death=%d east=%d" % (s, death, east))
    bad = {s: v[0] for s, v in rows.items() if not (DEATH_FLOOR < v[0] < DEATH_STEPS)}
    assert not bad, "death step outside (%d, %d): %s" % (DEATH_FLOOR, DEATH_STEPS, bad)


def test_field_first_ring(libs):
    """Spec :138 first ring, DRAFT-first-ring-spread 2: after 10 growth steps (a core of age 10) the eight
    compass-ray reaches are not all equal and the largest exceeds the smallest by at least 2 cells, seeds 1..10."""
    probe = libs.probe()
    rows = {}
    for seed in SEEDS:
        reaches, share, _ = front(probe, seed, 10)
        rows[seed] = (reaches, max(reaches) - min(reaches), share)
        print("FIELD_FIRST_RING seed=%d reaches=%s spread=%d" % (seed, reaches, rows[seed][1]))
    for seed in SEEDS:
        reaches, spread, share = rows[seed]
        assert len(set(reaches)) > 1, R193_01 % (10, seed, share) + "; reaches %s are all equal" % reaches
        assert spread >= SPREAD_MIN, R193_01 % (10, seed, share) + "; spread %d under %d, reaches %s" % (spread, SPREAD_MIN, reaches)


def test_field_front_shape(libs):
    """Spec :138: after 10 and 20 steps the reached set (cells with P > 0) has a 32-sector radial profile
    whose harmonic 4 plus 8 share is under DRAFT-shape-harm 0.5. At steps 3 and 5 the reached set is 3 to 12
    cells and has no radial profile worth a spectrum, so those two are printed, not asserted (spec rev 6a)."""
    probe = libs.probe()
    rows = []
    for age in (3, 5, 10, 20):
        for seed in SEEDS:
            _, share, ncells = front(probe, seed, age)
            rows.append((age, seed, share))
            print("FIELD_FRONT steps=%d seed=%d harm=%.3f pin=0.5 cells=%d%s" % (age, seed, share, ncells, "" if age >= 10 else " (printed, not asserted)"))
    bad = [(a, s, h) for a, s, h in rows if a >= 10 and not h < HARM_PIN]
    assert not bad, R193_01 % bad[0] + "; all failing (age, seed, share): %s" % bad


def test_field_deterministic(libs):
    """Spec :138: same inputs give byte-equal P, density, lot_core and death step, and the same bytes at -O0
    and -O2. Two cores of ages 10 and 40 on the 240 box."""
    cores, ages = [cell((70, 120), SIDE), cell((160, 120), SIDE)], [10, 40]
    a = libs.probe().run(3, SIDE, cores, ages)
    b = libs.probe().run(3, SIDE, cores, ages)
    c = libs.probe("-O0").run(3, SIDE, cores, ages)
    print("FIELD_DETERMINISTIC lots=%d death=%d repeat_equal=%s o0_equals_o2=%s" % (a.ret, a.death, digest(a) == digest(b), digest(a) == digest(c)))
    assert a.ret > 0, "the two-core run made no lot"
    assert digest(a) == digest(b), "the same inputs gave different bytes"
    assert digest(a) == digest(c), "-O0 and -O2 builds gave different bytes"


def test_field_bad_arguments(libs):
    """Spec :125 and the GAP 2 ruling: -1 for NULL core_cells, NULL ages, n_cores 0 and 7, side 0 and 401,
    an age of -1 and 401, a core cell at side*side; the cap cases: at age 40 lot_cap 100 gives at most 100
    lots, lot_cap 0 and -5 give the same bytes as lot_cap 8192."""
    probe = libs.probe()
    side = 20
    ok_cells = (ctypes.c_uint32 * 7)(*([cell((10, 10), side)] * 7))
    ok_ages = (ctypes.c_int32 * 7)(*([5] * 7))

    def call(seed=1, side=side, n=1, cores=ok_cells, ages=ok_ages, cap=PROBE_LOT_CAP):
        return probe.raw(seed, side, n, cores, ages, None, None, None, None, cap)

    good = call()
    big_cell = (ctypes.c_uint32 * 1)(side * side)
    low_age = (ctypes.c_int32 * 1)(-1)
    high_age = (ctypes.c_int32 * 1)(401)
    cases = {"NULL core_cells": call(cores=None), "NULL ages": call(ages=None), "n_cores 0": call(n=0),
             "n_cores 7": call(n=7), "side 0": call(side=0), "side 401": call(side=401),
             "age -1": call(ages=low_age), "age 401": call(ages=high_age), "core cell at side*side": call(cores=big_cell)}
    print("FIELD_BAD_ARGS good=%d %s" % (good, cases))
    assert good >= 0, "a valid call returned %d" % good
    wrong = {k: v for k, v in cases.items() if v != -1}
    assert not wrong, "bad arguments not rejected with -1: %s" % wrong
    capped = probe.single(1, SIDE, CORE_XY, 40, lot_cap=100)
    full = probe.single(1, SIDE, CORE_XY, 40, lot_cap=PROBE_LOT_CAP)
    zero = probe.single(1, SIDE, CORE_XY, 40, lot_cap=0)
    neg = probe.single(1, SIDE, CORE_XY, 40, lot_cap=-5)
    print("FIELD_LOT_CAP age=40 cap100_lots=%d cap8192_lots=%d" % (capped.ret, full.ret))
    assert 0 <= capped.ret <= 100, "lot_cap 100 gave %d lots" % capped.ret
    assert digest(zero) == digest(full), "lot_cap 0 does not select the default cap"
    assert digest(neg) == digest(full), "lot_cap -5 does not select the default cap"


def test_field_lot_counts_printed(libs):
    """Spec :125 lot rule and GAP 2: seed 1, side 240, core (120, 120), ages 10 and 40: lots equals
    min(15 * age, floor(0.6 * eligible)), eligible = cells with density >= 0.10 (the quota of one core). Exact
    because the field of a core of age at most 40 reaches at most 40 cells, inside the 97 x 97 scan square, and
    the cap term (the lot_cap passed, 8192 * age / age) is at least 600. The spec expects about 150 and 600."""
    probe = libs.probe()
    rows = []
    for age in (10, 40):
        res = probe.single(1, SIDE, CORE_XY, age)
        e = sum(1 for i in range(SIDE * SIDE) if res.D[i] >= 0.10)
        want = min(15 * age, math.floor(0.6 * e))
        rows.append((age, res.ret, e, want))
        print("PROBE_LOTS age=%d lots=%d eligible=%d" % (age, res.ret, e))
    for age, lots, e, want in rows:
        assert lots == want, "age %d: lots %d != min(%d, floor(0.6 * %d)) = %d" % (age, lots, 15 * age, e, want)


# ---------------------------------------------------------------- shape (probe, shape)
def test_shape_harmonic_share(libs):
    """Spec rev 6a :138 (probe, shape), R-193-01: for core ages 10, 20, 30, 40, 100, 200 and seeds 1..10 the radial
    profile r(theta) of the town's lots (32 sectors) has a harmonic 4 plus 8 share under DRAFT-shape-harm 0.5 at
    ages 20 and later; age 10 prints its shares and asserts nothing (a town of about 86 lots follows the list
    order the bookkeeping rule sets, not the field noise; the 0.5 draft is unchanged). One line per (age, seed) is
    printed BEFORE the assertion; the 90 and 45 degree rotation correlations are printed, not asserted
    (DRAFT-shape-corr 0.6 is a print label only). A value from age 20 up that reaches 0.5 is Westley's number:
    the writer reports every seed beside the pin before anything is changed."""
    probe = libs.probe()
    rows = []
    for age in SHAPE_AGES:
        for seed in SEEDS:
            r, lots, n, death, c90, c45 = town(probe, seed, age)
            share = harm_share(r)
            rows.append((age, seed, share))
            print("PROBE_SHAPE age=%d seed=%d harm=%.3f pin=0.5 lots=%d death=%d%s" % (age, seed, share, n, death, " (printed, not asserted)" if age == 10 else ""))
            print("PROBE_ROT age=%d seed=%d corr90=%.3f corr45=%.3f label=0.6 (printed, not asserted)" % (age, seed, c90, c45))
    bad = [(a, s, h) for a, s, h in rows if a >= 20 and not h < HARM_PIN]
    assert not bad, R193_01 % bad[0] + "; all failing (age, seed, share): %s" % bad


def test_shape_seeds_differ(libs):
    """Spec :138 and the GAP 11 ruling (TD-VG-P-1, scope-narrowed): for each age, seeds s and s+1 (1..10) give
    lot sets whose symmetric difference is at least DRAFT-seed-differ 10 percent of their union; asserted for
    ages 20 and up, age 10 prints its ratios and asserts nothing (threshold 0.10 untouched). Every pair is
    printed BEFORE the assertion."""
    probe = libs.probe()
    rows = []
    for age in SHAPE_AGES:
        for s in range(1, 10):
            a, b = town(probe, s, age)[1], town(probe, s + 1, age)[1]
            union = len(a | b)
            ratio = len(a ^ b) / union if union else 0.0
            rows.append((age, s, ratio))
            print("PROBE_DIFFER age=%d seeds=%d,%d ratio=%.3f%s" % (age, s, s + 1, ratio, " (reported only)" if age == 10 else ""))
    bad = [(a, s, r) for a, s, r in rows if a >= 20 and r < DIFFER_MIN]
    assert not bad, R193_01 % bad[0] + "; seeds %d and %d differ by under 10 percent; all failing: %s" % (bad[0][1], bad[0][1] + 1, bad)


# ---------------------------------------------------------------- controls
def _cells_where(pred, cx=120, cy=120, r=30):
    return [(gx, gy) for gy in range(cy - r, cy + r + 1) for gx in range(cx - r, cx + r + 1) if pred(gx - cx, gy - cy)]


def _shapes():
    R = 20
    rng = random.Random(11)
    noise = [rng.uniform(-1.0, 1.0) * 0.1 for _ in range(SECTORS)]          # sector noise 0.1 of the radius
    blob = lambda t: R * (1 + 0.12 * math.cos(t - 0.3) + 0.10 * math.cos(2 * t - 1.1) + 0.08 * math.cos(3 * t + 0.7))
    return {
        "square": _cells_where(lambda dx, dy: max(abs(dx), abs(dy)) <= R),
        "noisy square": _cells_where(lambda dx, dy: max(abs(dx), abs(dy)) <= R * (1 + noise[sector_of(dx, dy)]) if (dx or dy) else True),
        "octagon": _cells_where(lambda dx, dy: abs(dx) <= R and abs(dy) <= R and abs(dx) + abs(dy) <= 28),
        "diamond": _cells_where(lambda dx, dy: abs(dx) + abs(dy) <= R),
        "blob": _cells_where(lambda dx, dy: math.hypot(dx, dy) <= blob(math.atan2(dy, dx))),
    }


def test_ctrl_shape_detector_flags_known_bad():
    """Control: the shape detector flags a clean square, a noisy square (sector noise 0.1 of the radius), an
    octagon and a diamond, built as lot sets about (120, 120) with radius about 20 cells (share above 0.5).
    The spec reports square 0.99, diamond 0.99, octagon 0.997, noisy square 0.80; printed beside ours. A bad
    shape not above 0.5 is a 'control-mismatch' stop, not a retune."""
    vals = {k: harm_share(profile(v, 120, 120)) for k, v in _shapes().items()}
    print("CTRL_SHAPE_BAD " + " ".join("%s=%.3f" % (k.replace(" ", "_"), vals[k]) for k in ("square", "noisy square", "octagon", "diamond"))
          + " (spec: square 0.99 diamond 0.99 octagon 0.997 noisy_square 0.80)")
    for k in ("square", "noisy square", "octagon", "diamond"):
        assert vals[k] > HARM_PIN, R193_01 % (20, 0, vals[k]) + "; the detector does not flag the %s" % k


def test_ctrl_shape_detector_passes_blob():
    """Control: a noise-warped blob (a smooth low-harmonic radius modulation, not a 4-lobed shape: lanes are
    not lobes) passes (share below 0.5); the spec reports noise blobs 0.13 to 0.20. A rasterised disc is not
    a control (spec: 0.48 to 0.84)."""
    v = harm_share(profile(_shapes()["blob"], 120, 120))
    print("CTRL_SHAPE_BLOB blob=%.4f (spec: noise blobs 0.13 to 0.20)" % v)
    assert v < HARM_PIN, R193_01 % (20, 0, v) + "; the detector flags the blob"


def test_ctrl_field_noise_off(libs):
    """Spec :138 noise off, R-193-01: in a patched copy of csrc where growth_probe.c's PROBE_HOP_COST line has
    its right-hand side replaced by 1, the reached set after 10 steps (core age 10) is the Chebyshev square:
    all eight compass reaches equal 10 and the harmonic share is above 0.9, and the first-ring detector of
    test_field_first_ring FAILS; on the real build the same detector passes."""
    real, off = libs.probe(), libs.noise_off()
    bad, shares = [], []
    for seed in (1, 2, 3):
        res = off.single(seed, SIDE, CORE_XY, 10)
        cx, cy = CORE_XY
        reaches = [ray_reach(res.P, SIDE, cx, cy, d) for d in DIRS8]
        share = harm_share(profile(reached_cells(res.P, SIDE, cx, cy, 12), cx, cy))
        shares.append(share)
        real_reaches, real_share, _ = front(real, seed, 10)
        print("CTRL_NOISE_OFF seed=%d off_reaches=%s off_harm=%.3f off_detector_ok=%s real_reaches=%s real_detector_ok=%s"
              % (seed, reaches, share, first_ring_ok(reaches), real_reaches, first_ring_ok(real_reaches)))
        if reaches != [10] * 8:
            bad.append("seed %d: noise-off reaches %s are not all 10" % (seed, reaches))
        if not share > 0.9:
            bad.append("seed %d: noise-off harmonic share %.3f is not above 0.9" % (seed, share))
        if first_ring_ok(reaches):
            bad.append("seed %d: the first-ring detector passes with the noise off" % seed)
        if not first_ring_ok(real_reaches):
            bad.append("seed %d: the first-ring detector fails on the real build" % seed)
    assert not bad, R193_01 % (10, 1, shares[0] if shares else 0.0) + "; " + "; ".join(bad)


def test_ctrl_field_divergence_patched_build_fails(libs):
    """Spec rev 6a :138 divergence control (Architect 2026-10-21): a patched copy where PROBE_BASE_DECAY and
    PROBE_NONWATER_FAR are both 1.01 (edge factor 1.0201, above 1), run at age 40 on side 400, seed 1, core
    (200, 200): the ring-bound detector fails (ring-1 maximum above 0.99; measured 4.98e5) and the death step is
    -1 (the active list is still full at step 40; measured). Both halves are kept, 30 steps before the Q16
    truncation overflows (age 70, where no control is aimed). The real build passes the ring bound at the same
    age, and the real death-step test (test_field_death_step) stays at age 400, its bound checked here from the
    same cached run. If the patched build passes the ring bound or does not return -1, STOP with 'control-mismatch'."""
    real, bad_lib = libs.probe(), libs.diverged()
    rm_real, _, _ = box_run(real, 1, 40)
    _, _, death_real = box_run(real, 1, 400)
    res = bad_lib.single(1, BOX_SIDE, BOX_XY, 40)
    rm_bad = ring_max(res.P, BOX_SIDE, BOX_XY[0], BOX_XY[1])
    print("CTRL_DIVERGENCE age=40 real_ring_ok=%s real_death_age400=%d patched_ring_ok=%s patched_death=%d patched_ring1=%.4g patched_ring20=%.4g"
          % (ring_ok(rm_real), death_real, ring_ok(rm_bad), res.death, rm_bad[0], rm_bad[19]))
    assert ring_ok(rm_real), "the real build fails the ring bound at age 40"
    assert DEATH_FLOOR < death_real < DEATH_STEPS, "the real build fails the death-step test at age 400: %d" % death_real
    assert not ring_ok(rm_bad), "the patched build passes the ring bound at age 40; the detector cannot fail"
    assert rm_bad[0] > 0.99, "the patched build's ring-1 maximum %.4g is not above 0.99" % rm_bad[0]
    assert res.death == -1, "the patched build's active list emptied at step %d at age 40; expected -1" % res.death
