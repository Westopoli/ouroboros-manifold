"""VG-P2 (places lane P2), tests of the growth probe and the town shape: csrc/growth_probe.c (with csrc/economy_lot_noise.c).

Method rev 3: the rule words, word for word.

Bible E-17 (docs/bible/epics/E-17-map-generation.md), the rule this file proves for the outline. The spec marks the lot
order as "R-193-01: a ragged outline at any age"; the rule text reads:

- R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.

Bible E-17, the rule behind the streets (the probe has no lanes; the lane tests are in test_VG_P_p2_lot_noise_lanes.py):

- R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).

Spec docs/northstar/plans/2026-10-13-places-lane-spec.md rev 4a, section "P2 lot-order noise, lanes and the growth
probe" (lines 85-107), the sentences these tests implement:

  "what the player sees is the lots, and the lots are created in the order of a noisy distance with a quota that always
  binds, so the drawn town is a warped disc by construction"

  "`DRAFT-shape-harm` is **0.5, pinned from the controls, not from the probe** (the auditor measured: clean square 0.99,
  diamond 0.99, octagon 0.997, noisy square 0.80, noise blobs 0.13 to 0.20; a rasterised disc 0.48 to 0.84, so a disc is
  not a control); the probe prints its per-seed value beside the pin. If any seed's town measures above 0.5 the P2
  test-writer reports the number to the Architect before changing anything."

THE BIBLE GIVES NO NUMBER for the probe's decay, the front, the death step, the sectors, the share, the pin or the lot
quota. Every number below is a named draft of spec rev 4a: DRAFT-diag-decay 0.9917 (in the probe, P3 replaces
DIAG_DECAY by it), DRAFT-death-floor 100, DRAFT-death-steps 600, DRAFT-shape-sectors 32, DRAFT-shape-harm 0.5,
DRAFT-shape-corr 0.6 (a print label only), DRAFT-seed-differ 0.10, DRAFT-lots-per-age 15, DRAFT-lot-fill 0.6,
DRAFT-lot-scan-radius 48, DRAFT-lot-cap 8192, DRAFT-probe-economy 1.0, DRAFT-core-economy; cited, not drafted:
BASE_DECAY and NONWATER_FAR 0.99 (economy_density.c:27, :34), THRESHOLD_1 0.10 (economy_lots.c:14), P_EPS, P_MIN, EASE,
M_START, M_FULL_TICKS (economy_density.c:35-39). Gap rulings (Architect 2026-10-14): gap 2 (the probe takes lot_cap as
its last argument, 0 or less selects PROBE_LOT_CAP 8192), gap 3 (the divergence build patches BOTH PROBE_BASE_DECAY and
PROBE_NONWATER_FAR to 1.01), gap 4 (death-step bounds on side 240, core (120, 120), age 150; the side 81 and 121 cases
are printed, not asserted), gap 6 (the lot-order key is exact integers), gap 7 (the age-0 core's quota is
floor(0.6 * eligible)).

READING taken by the shape detector of these tests: "one-sided power of harmonics 1 to 16" is |DFT bin k|^2 of the 32
mean-removed samples for k = 1..16, with no weighting.
"""
import ctypes
import math
import pathlib
import re
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
# Same flags as the Makefile's release build, the pattern of tests/csim/test_PP_grid_margin_exact.py:31-33.
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]
SIDE = 240                         # the probe's largest grid
CORE = (120, 120)
DEATH_FLOOR = 100                  # DRAFT-death-floor
DEATH_STEPS = 600                  # DRAFT-death-steps
SECTORS = 32                       # DRAFT-shape-sectors
SHAPE_HARM = 0.5                   # DRAFT-shape-harm
SEED_DIFFER = 0.10                 # DRAFT-seed-differ
LOTS_PER_AGE = 15                  # DRAFT-lots-per-age
THRESHOLD_1 = 0.10                 # economy_lots.c:14
SHAPE_AGES = (10, 20, 30, 40, 100, 200)
SHAPE_SEEDS = tuple(range(1, 11))
BASE_DECAY_RE = re.compile(r"^#define PROBE_BASE_DECAY .*$", re.M)
NONWATER_FAR_RE = re.compile(r"^#define PROBE_NONWATER_FAR .*$", re.M)
PROBE_SRCS = ("terrain_noise.c", "economy_lot_noise.c", "growth_probe.c")


def _cc(out, srcs, include, opt="-O2"):
    flags = [opt if f == "-O2" else f for f in FLAGS]
    res = subprocess.run(["cc", *flags, "-I", str(include), "-shared", "-o", str(out),
                          *[str(s) for s in srcs], "-lm"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]
    return out


def _bind(path):
    h = ctypes.CDLL(str(path))
    h.om_growth_probe_run.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_uint32,
                                      ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_int32),
                                      ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                                      ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_int32),
                                      ctypes.c_int32]
    h.om_growth_probe_run.restype = ctypes.c_int32
    return h


_LIBS = {}


def lib_b(work, opt="-O2"):
    """Library B: terrain_noise.c + economy_lot_noise.c + growth_probe.c (gap 1 ruling; no layout_terrain.c, no world)."""
    key = (str(work), opt)
    if key not in _LIBS:
        out = _cc(work / f"lib_b{opt}.so", [REPO / "csrc" / n for n in PROBE_SRCS], REPO / "csrc", opt)
        _LIBS[key] = _bind(out)
    return _LIBS[key]


def lib_patched(work):
    """A patched COPY of csrc in a temp dir (the pattern of test_PP_grid_margin_exact.py:47-58): both probe decay
    constants replaced by 1.01 (gap 3 ruling), exactly one #define line each."""
    key = (str(work), "patched")
    if key not in _LIBS:
        src = work / "csrc_patched"
        shutil.copytree(REPO / "csrc", src, ignore=shutil.ignore_patterns("pipe"))
        f = src / "growth_probe.c"
        text = f.read_text()
        text, n1 = BASE_DECAY_RE.subn("#define PROBE_BASE_DECAY 1.01", text)
        text, n2 = NONWATER_FAR_RE.subn("#define PROBE_NONWATER_FAR 1.01", text)
        assert n1 == 1, "PROBE_BASE_DECAY define not found exactly once in growth_probe.c"
        assert n2 == 1, "PROBE_NONWATER_FAR define not found exactly once in growth_probe.c"
        f.write_text(text)
        out = _cc(work / "lib_patched.so", [src / n for n in PROBE_SRCS], src)
        _LIBS[key] = _bind(out)
    return _LIBS[key]


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2_probe")


def run(lib, seed, side, cores, ages, lot_cap=0, want=("P", "D", "L")):
    """cores: list of (gx, gy). Returns dict n, death, P, D, L (lists / bytes; None when not asked)."""
    n = len(cores)
    carr = (ctypes.c_uint32 * n)(*[gy * side + gx for gx, gy in cores])
    aarr = (ctypes.c_int32 * n)(*ages)
    cells = side * side
    P = (ctypes.c_double * cells)() if "P" in want else None
    D = (ctypes.c_double * cells)() if "D" in want else None
    L = (ctypes.c_uint8 * cells)() if "L" in want else None
    death = ctypes.c_int32(-7)
    got = lib.om_growth_probe_run(seed, side, n, carr, aarr, P, D, L, ctypes.byref(death), lot_cap)
    return {"n": got, "death": death.value, "P": list(P) if P is not None else None,
            "D": list(D) if D is not None else None, "L": bytes(L) if L is not None else None,
            "raw": (bytes(P) if P is not None else b"") + (bytes(D) if D is not None else b"")
                   + (bytes(L) if L is not None else b"") + got.to_bytes(4, "little", signed=True)
                   + death.value.to_bytes(4, "little", signed=True)}


# ----------------------------------------------------------------------------- shape detector (pure Python)

def profile(cells, side, cx, cy):
    """r(theta): the largest distance in cells from the core cell of any cell of the set, per sector; empty sector 0."""
    r = [0.0] * SECTORS
    for idx in cells:
        dx, dy = idx % side - cx, idx // side - cy
        s = int(math.floor(math.atan2(dy, dx) / (2 * math.pi / SECTORS))) % SECTORS
        d = math.hypot(dx, dy)
        if d > r[s]:
            r[s] = d
    return r


def harmonic_share(r):
    """Power of harmonics 4 and 8 over the power of harmonics 1..16 of the mean-removed profile; 0.0 for zero power."""
    n = len(r)
    m = sum(r) / n
    a = [x - m for x in r]
    p = {}
    for k in range(1, 17):
        re_ = sum(a[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        im_ = sum(a[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        p[k] = re_ * re_ + im_ * im_
    total = sum(p.values())
    return 0.0 if total <= 0.0 else (p[4] + p[8]) / total


def rotation_corr(r, shift):
    """Pearson correlation of r(theta) with itself rotated by `shift` sectors (printed, not asserted)."""
    n = len(r)
    m = sum(r) / n
    a = [x - m for x in r]
    b = [a[(i + shift) % n] for i in range(n)]
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return num / den if den > 0 else 0.0


def lot_cells(lot_core):
    return [i for i, c in enumerate(lot_core) if c != 255]


# ----------------------------------------------------------------------------- positive controls of the shape detector

def _shape_set(pred, ext=40):
    cx, cy = CORE
    return [(cy + dy) * SIDE + cx + dx for dy in range(-ext, ext + 1) for dx in range(-ext, ext + 1) if pred(dx, dy)]


def _sector_of(x, y):
    return int(math.floor(math.atan2(y, x) / (2 * math.pi / SECTORS))) % SECTORS


def _lcg(seed):
    s = seed
    while True:
        s = (s * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        yield (s >> 11) / float(1 << 53)


RADIUS = 20                       # "radius about 20 cells"
SECTOR_NOISE = 0.1                # "sector noise 0.1 of the radius"
OCTAGON_DIAG = 28                 # |dx| + |dy| <= 28 cuts the corners of the 20-cell square (apothem 20, 20 * sqrt 2)


def _control_sets():
    sq = _shape_set(lambda x, y: max(abs(x), abs(y)) <= RADIUS)
    dia = _shape_set(lambda x, y: abs(x) + abs(y) <= RADIUS)
    octa = _shape_set(lambda x, y: max(abs(x), abs(y)) <= RADIUS and abs(x) + abs(y) <= OCTAGON_DIAG)
    g = _lcg(1)
    nz = [(next(g) * 2 - 1) * SECTOR_NOISE for _ in range(SECTORS)]
    noisy = _shape_set(lambda x, y: max(abs(x), abs(y)) <= RADIUS * (1 + nz[_sector_of(x, y)]))
    return {"clean square": sq, "diamond": dia, "octagon": octa, "noisy square": noisy}


def _blob(seed):
    """A noise-warped blob: a disc whose radius is modulated by a smooth low-harmonic function (harmonics 1, 2, 3, 5, 6:
    not a 4-lobed shape)."""
    g = _lcg(100 + seed)
    ph = [next(g) * 2 * math.pi for _ in range(6)]
    amp = {1: 0.12, 2: 0.12, 3: 0.10, 5: 0.06, 6: 0.04}

    def inside(x, y):
        th = math.atan2(y, x)
        return math.hypot(x, y) <= RADIUS * (1 + sum(a * math.cos(k * th + ph[k - 1]) for k, a in amp.items()))
    return _shape_set(inside)


def test_ctrl_shape_detector_flags_known_bad():
    """The detector flags (share above 0.5) a clean square, a noisy square (sector noise 0.1 of the radius), an octagon
    and a diamond. Values printed beside the spec's (square 0.99, diamond 0.99, octagon 0.997, noisy square 0.80)."""
    spec = {"clean square": 0.99, "diamond": 0.99, "octagon": 0.997, "noisy square": 0.80}
    got = {name: harmonic_share(profile(cells, SIDE, *CORE)) for name, cells in _control_sets().items()}
    for name, v in got.items():
        print(f"SHAPE_CTRL {name} share={v:.3f} spec={spec[name]}")
    bad = {k: v for k, v in got.items() if not v > SHAPE_HARM}
    assert not bad, f"control-mismatch: bad shapes not above {SHAPE_HARM}: {bad}"


def test_ctrl_shape_detector_passes_blob():
    """A noise-warped blob passes (share below 0.5). The spec measured noise blobs at 0.13 to 0.20; a rasterised disc
    (0.48 to 0.84) is NOT a control."""
    vals = [harmonic_share(profile(_blob(s), SIDE, *CORE)) for s in range(1, 6)]
    print("SHAPE_CTRL blob shares=" + " ".join(f"{v:.3f}" for v in vals) + " spec=0.13..0.20")
    assert all(v < SHAPE_HARM for v in vals), f"control-mismatch: blob not below {SHAPE_HARM}: {vals}"


# ----------------------------------------------------------------------------- field (library B)

RAYS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def ring_violations(res):
    """Chebyshev ring k in 1..20 whose maximum P exceeds 0.99^k."""
    P, bad = res["P"], []
    cx, cy = CORE
    for k in range(1, 21):
        ring = [P[(cy + dy) * SIDE + cx + dx] for dy in range(-k, k + 1) for dx in range(-k, k + 1)
                if max(abs(dx), abs(dy)) == k]
        if max(ring) > 0.99 ** k:
            bad.append((k, max(ring), 0.99 ** k))
    return bad


def east_reach(res):
    cx, cy = CORE
    return max((gx - cx for gx in range(SIDE) if res["P"][cy * SIDE + gx] > 0.0), default=0)


def death_ok(res):
    return DEATH_FLOOR < res["death"] < DEATH_STEPS and east_reach(res) <= SIDE - 1 - CORE[0]


def test_field_ring_bound(work):
    """One centred core, age 150: P at Chebyshev ring k is at most 0.99^k for k in 1..20 (maximum over the ring)."""
    res = run(lib_b(work), 1, SIDE, [CORE], [150])
    assert res["n"] >= 0
    assert ring_violations(res) == []


def test_field_front_exact(work):
    """The mean of the eight compass-ray reaches (largest distance along the ray with P > 0) after 10 and after 20
    growth steps equals the age exactly."""
    lib = lib_b(work)
    for age in (10, 20):
        res = run(lib, 1, SIDE, [CORE], [age])
        cx, cy = CORE
        reaches = []
        for dx, dy in RAYS:
            reach = 0
            for t in range(1, SIDE):
                x, y = cx + dx * t, cy + dy * t
                if 0 <= x < SIDE and 0 <= y < SIDE and res["P"][y * SIDE + x] > 0.0:
                    reach = t
            reaches.append(reach)
        print(f"PROBE_FRONT age={age} reaches={reaches}")
        assert sum(reaches) / 8.0 == age


def test_field_death_step(work):
    """Gap 4 ruling: side 240, core (120, 120), age 150: out_death_step is above DRAFT-death-floor 100 and below
    DRAFT-death-steps 600, and the farthest cell with P > 0 along the east ray is at most 119 (the front has not left
    the grid on the asserted side). The side-81 and side-121 cases are printed, not asserted."""
    lib = lib_b(work)
    res = run(lib, 1, SIDE, [CORE], [150])
    print(f"PROBE_DEATH side={SIDE} death={res['death']} east_reach={east_reach(res)}")
    for side in (81, 121):
        r = run(lib, 1, side, [(side // 2, side // 2)], [150], want=("P",))
        print(f"PROBE_DEATH side={side} death={r['death']}")
    assert DEATH_FLOOR < res["death"] < DEATH_STEPS, res["death"]
    assert east_reach(res) <= 119


def test_field_lot_cap_argument(work):
    """Gap 2 ruling: age 40 flat core (120, 120): lot_cap 100 gives at most 100 lots; lot_cap -5 and 8192 give the same
    bytes as lot_cap 0 (the default PROBE_LOT_CAP 8192)."""
    lib = lib_b(work)
    base = run(lib, 1, SIDE, [CORE], [40], lot_cap=0)
    capped = run(lib, 1, SIDE, [CORE], [40], lot_cap=100)
    assert 0 < capped["n"] <= 100
    assert run(lib, 1, SIDE, [CORE], [40], lot_cap=-5)["raw"] == base["raw"]
    assert run(lib, 1, SIDE, [CORE], [40], lot_cap=8192)["raw"] == base["raw"]


def test_field_deterministic(work):
    """Same inputs byte-equal (P, density, lot_core, lot count, death step); the same bytes at -O0 and -O2."""
    a, b = lib_b(work, "-O2"), lib_b(work, "-O0")
    cases = [(1, [CORE], [40]), (3, [(60, 70), (150, 140)], [10, 40])]
    for seed, cores, ages in cases:
        r1 = run(a, seed, SIDE, cores, ages)
        r2 = run(a, seed, SIDE, cores, ages)
        r0 = run(b, seed, SIDE, cores, ages)
        assert r1["raw"] == r2["raw"]
        assert r1["raw"] == r0["raw"]
        assert r1["n"] > 0


def test_field_bad_arguments(work):
    """-1 for NULL core_cells, n_cores 0 and 7, side 0 and 241, an age of -1 and 401, a core cell at side*side, and for a
    NULL ages."""
    lib = lib_b(work)
    cells7 = (ctypes.c_uint32 * 7)(*[i * 3 for i in range(7)])
    ages7 = (ctypes.c_int32 * 7)(*([10] * 7))
    death = ctypes.c_int32(0)

    def call(side=SIDE, n=1, cells=cells7, ages=ages7):
        return lib.om_growth_probe_run(1, side, n, cells, ages, None, None, None, ctypes.byref(death), 0)
    assert call() >= 0                                   # control: the call itself is fine
    assert call(cells=None) == -1
    assert call(ages=None) == -1
    assert call(n=0) == -1
    assert call(n=7) == -1
    assert call(side=0) == -1
    assert call(side=241) == -1
    bad_age = (ctypes.c_int32 * 7)(-1, 10, 10, 10, 10, 10, 10)
    assert call(ages=bad_age) == -1
    bad_age = (ctypes.c_int32 * 7)(401, 10, 10, 10, 10, 10, 10)
    assert call(ages=bad_age) == -1
    bad_cell = (ctypes.c_uint32 * 7)(SIDE * SIDE, 1, 2, 3, 4, 5, 6)
    assert call(cells=bad_cell) == -1


def test_field_lot_counts_printed(work):
    """Seed 1, flat grid, core (120, 120), ages 10 and 40: prints PROBE_LOTS (the spec expects about 150 and about 600);
    lots <= DRAFT-lots-per-age 15 * age, and lots == 15 * age when at least 25 * age cells have density >= 0.10 (then
    floor(0.6 * eligible) is at least 15 * age and the third quota term binds on flat dry ground)."""
    lib = lib_b(work)
    for age in (10, 40):
        res = run(lib, 1, SIDE, [CORE], [age])
        eligible = sum(1 for d in res["D"] if d >= THRESHOLD_1)
        print(f"PROBE_LOTS age={age} lots={res['n']} cells_density_ge_0.10={eligible}")
        assert res["n"] == len(lot_cells(res["L"]))
        assert res["n"] <= LOTS_PER_AGE * age
        if eligible >= 25 * age:
            assert res["n"] == LOTS_PER_AGE * age


# ----------------------------------------------------------------------------- shape (library B)

_RUNS = {}


def lots_of(work, age, seed):
    key = (age, seed)
    if key not in _RUNS:
        res = run(lib_b(work), seed, SIDE, [CORE], [age], want=("L",))
        _RUNS[key] = res
    return _RUNS[key]


def test_shape_harmonic_share(work):
    """For core ages 10, 20, 30, 40, 100, 200 and seeds 1..10 (side 240, core (120, 120)): the share of the AC power of
    r(theta) (32 sectors) in harmonics 4 plus 8 is below DRAFT-shape-harm 0.5. One PROBE_SHAPE line per (age, seed) is
    printed BEFORE the assertion; the 90 and 45 degree rotation correlations are printed, not asserted (DRAFT-shape-corr
    0.6 is a print label only)."""
    rows = []
    for age in SHAPE_AGES:
        for seed in SHAPE_SEEDS:
            res = lots_of(work, age, seed)
            r = profile(lot_cells(res["L"]), SIDE, *CORE)
            share = harmonic_share(r)
            rows.append((age, seed, share))
            print(f"PROBE_SHAPE age={age} seed={seed} harm={share:.4f} pin={SHAPE_HARM} lots={res['n']} "
                  f"death={res['death']} corr90={rotation_corr(r, 8):.3f} corr45={rotation_corr(r, 4):.3f} "
                  f"corr_label=0.6")
    over = [(a, s, round(v, 4)) for a, s, v in rows if not v < SHAPE_HARM]
    assert not over, f"harmonic share at or above {SHAPE_HARM} (report to the Architect, do not change anything): {over}"


def test_shape_seeds_differ(work):
    """For each age of 20 and up, seeds s and s+1 (1..10) give lot sets whose symmetric difference is at least
    DRAFT-seed-differ 10 percent of their union. Age 10 is reported only (PROBE_DIFFER lines are printed, nothing is
    asserted for it); its shape is held by the harmonic control (0.17 max at age 10).

    Scope narrowed by Architect ruling 2026-10-14 (TD-VG-P-1; the threshold DRAFT-seed-differ 0.10 is unchanged): a
    hamlet of radius 7 cells sits inside one 8-cell noise lattice unit, so two seeds differ little by construction;
    the small-town look is Westley's to judge on the shot."""
    for age in SHAPE_AGES:
        for seed in range(1, 10):
            a = set(lot_cells(lots_of(work, age, seed)["L"]))
            b = set(lot_cells(lots_of(work, age, seed + 1)["L"]))
            ratio = len(a ^ b) / float(len(a | b))
            print(f"PROBE_DIFFER age={age} seeds={seed},{seed + 1} symdiff_over_union={ratio:.3f}"
                  f"{'' if age >= 20 else ' (reported only)'}")
            if age >= 20:
                assert ratio >= SEED_DIFFER, (age, seed, ratio)


# ----------------------------------------------------------------------------- divergence control

def test_ctrl_field_divergence_patched_build_fails(work):
    """Patched COPY of csrc with PROBE_BASE_DECAY and PROBE_NONWATER_FAR both 1.01 (edge factor 1.0201, above 1): the
    ring bound fails and the death-step test fails (the field never dies); on the real build both pass.

    Readings (reported to the Architect, gap 3): P grows without a clamp on the patched build and passes the int64 limit
    of the Q16 truncation (v * 65536 as an int64) at about growth step 100; the cast of an out-of-range double is
    undefined and on x86 gives INT64_MIN, so P turns negative and a late reading is garbage. The ring bound is therefore
    read at age 20 (rings 1..20 need only 20 steps), the death-step test at age 150 (the real build's death is about
    121; the patched list is still active after the last step, out_death_step == -1), and the age-400 reading, which the
    ruling asks to equal -1, is PRINTED (DIVERGENCE patched death_age400) and not asserted: a scratch reference gave
    death 200 there (the overflow emptied the list)."""
    real, patched = lib_b(work), lib_patched(work)
    r_real = run(real, 1, SIDE, [CORE], [150], want=("P",))
    assert ring_violations(r_real) == []
    assert death_ok(r_real), (r_real["death"], east_reach(r_real))
    r_ring = run(patched, 1, SIDE, [CORE], [20], want=("P",))
    viol = ring_violations(r_ring)
    print(f"DIVERGENCE patched age20 ring_violations={len(viol)} first={viol[:1]}")
    assert viol, "control-mismatch: the patched build still satisfies P at ring k <= 0.99^k"
    r_bad = run(patched, 1, SIDE, [CORE], [150], want=("P",))
    print(f"DIVERGENCE patched death_age150={r_bad['death']}")
    assert not death_ok(r_bad), f"control-mismatch: the patched build passes the death-step test: {r_bad['death']}"
    assert r_bad["death"] == -1, f"control-mismatch: the patched active list emptied at {r_bad['death']} (age 150)"
    r_long = run(patched, 1, SIDE, [CORE], [400], want=("P",))
    print(f"DIVERGENCE patched death_age400={r_long['death']} (printed, not asserted: see the docstring)")
