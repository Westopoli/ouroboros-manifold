"""VG-P1 (places lane P1, the layout engine): tests/csim/test_VG_P_p1_layout.py.

Spec: docs/northstar/plans/2026-10-13-places-lane-spec.md (rev 4a), section "P1 the engine",
with the Architect gap rulings of 2026-10-14 (stub numbers, stub file, no layout_terrain.c
link, no adapter tests here, boundary conventions, 20 ms asserted, stub struct copy named
om_stub_layout_terrain).

The engine csrc/layout_engine.c is built into its own library with csrc/terrain_noise.c and the
stub tests/csim/layout_stub_terrain.c (cc -shared -I csrc ... -lm, the pattern of
test_PP_grid_margin_exact.py:33-60) and loaded under ctypes default mode: the engine calls no
symbol of csrc/layout_terrain.c (gap 3). No P1 test calls layout_terrain.c or the full library
(gap 4: the adapter tests go into P3).

Red reason on the built tree: csrc/layout_engine.c and csrc/layout_internal.h do not exist, so
the isolation build exits non-zero (assert res.returncode == 0) and the size-link compile fails.
The stub-only checks and every detector control below are green today.

Every test names its rule id in its docstring. Rules proved, quoted word for word (method rev 3;
test_the_quoted_rules_are_the_bibles checks each quote against the files):

E-22 (docs/bible/epics/E-22-economy-and-bases.md):

R-177-02  Given the mission archetype (E-10 S-073), When bases are given, Then the player's base of operations is a grown town only where the archetype gives the player a home or a defended settlement; an attacking archetype has a forward base, a camp and not a town (Westley, 2026-10-13: "depends on the archetype, an attacker can't have a full town since they're attacking, they have a forward base"). The kind of base each side gets is decided by the archetype table below alone (Westley, 2026-10-06).

| Archetype | Player's base | Enemy's base |
|---|---|---|
| Defensive Stand, Multi-Front Defense | home city, generating on site | forward base, supplied from elsewhere |
| Siege Breaking | relief camp outside, supplied, with the city inside as the objective | siege camp |
| Assault, Reconquest | forward base, supplied | the city or fortress being taken |
| Containment, Interception | field camp on the enemy's path | column or staging camp |
| Suppression, Counterinsurgency | garrison in a city | hidden cells among the settlements |
| Rear Guard / Evacuation | the place being left | pursuing forward base |

R-177-06  Given the simulation's situation, When a mission is set up, Then resources are sometimes limited and sometimes abundant, consistent with that situation and slanted by it so that a defender has the better position, and the player always has the means to accomplish the mission even when it is hard; richness is derived from the simulation's existing region fields and composites (E-02), so a region with a big economy gives a mission big resources (Westley, 2026-10-06).

E-17 (docs/bible/epics/E-17-map-generation.md):

R-191-02  Given a land map, When places are found, Then each side has a base of operations (E-22 S-177), and the map has the objective. An attacker's base is the forward base from which he produces (E-22 S-177); supply lines are not an attacker-only rule (Westley, 2026-10-07).

R-191-03  Given a land map, When economic locations are found, Then they are placed throughout the map (E-22 S-177), in numbers that scale with the players and the canvas (Westley, 2026-10-03) [Q-191-05: the counts and the spacing].

R-191-04  Given the objective, When the significant resources are placed, Then each side is at the same distance from the objective and from each significant resource, whatever shape the map takes (Westley, 2026-10-03: only those distances matter, and the more the shapes vary under that constraint the better), except where an archetype's slant says otherwise (Westley, 2026-10-03), so a side picks one or fights for both (E-22 S-177) [Q-191-05: what the distance is measured by, its tolerance, and how much the distances differ on a slanted archetype].

R-191-05  Given the terrain, When expansion sites are found, Then they are settlements that can be grown into further bases (E-22 S-175 and S-177).

R-191-06  Given the terrain, When neutral settlements are found, Then a neutral populace lives in them and they are contested (E-22 S-177). They exist at mission start already grown, each to a seeded age, so that some are small and some big, their size scaled by the region's economy (E-22 R-177-06). They stand where the layout engine's economic locations are (R-191-03), never at hard-coded positions, and growth continues during play (R-193-01). Westley, 2026-10-13: "there should be existing (neutral) towns that contain resources (economy) out on the map, some small some big"; "the economy system needs to be built because that's what will induce 'towns', so let the economy system (layout engine) decide where those go, nothing hard coded."

R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.

Q-191-03 (docs/northstar/ambiguity_register.md), Westley 2026-10-03, verbatim:

"Q191-03: Whatever the layout is, and depending on the archetype (we want to make it fair) there should be an equal distance for both players between both the significant resources and the objective. I don't care what the shape is, I only care about those numbers. However much we can vary the shapes given those constraints I encourage. This will be another part of the same prototype from 191-01, I'd like to approve the product before we integrate it."

Spec sentences that no quoted rule states are named drafts, marked DRAFT-<name> as the spec names
them (DRAFT-places-spacing 4,000 wu, DRAFT-places-floor 0.35, DRAFT-towns-max 6, DRAFT-home-age 40,
DRAFT-town-age-min/max 10/40, DRAFT-resource-clearance 2,400 wu, DRAFT-resource-fairness 600 wu,
DRAFT-satellite-offset 300 wu, DRAFT-defender-slant +10, DRAFT-richness-formula, DRAFT-places-budget
20 ms, ...). "Opposite the objective" is read as the spec P1 step 4 reads it (Westley 2026-09-23 is
cited there; its verbatim string is not in the repo): one resource site on each side of the
objective along the line level between the two bases, each at equal distance from the two bases
within DRAFT-resource-fairness.

Where the spec leaves two readings these tests assert only what both give: step 9 (a resource
site directly after its town, or in the satellite phase in town order): the tests assert the
first three places, that the first two NEUTRAL_SETTLEMENTs host the resource sites, and that
expansion sites follow all towns in town order; step 7's S and N (the sign of y): E and W are
exact, a vertical step is accepted either way; step 3's flatness share at a canvas edge (the
share of the in-canvas cells or of the whole 29-cell disc): the reference model accepts either.
Orientation of d in step 4: the set of resource towns is orientation-free, their order is not
asserted.

Slice map for the builders (test ids):
  SLICE-U2 (argument validation, objective, base kinds, base ages, determinism of the trivial
    result): test_null_pointer_returns_minus_one, test_bad_canvas_returns_minus_one,
    test_bad_archetype_returns_minus_one, test_the_objective_is_first_and_unmoved,
    test_base_kinds_sides_ages_for_all_ten_archetypes, test_all_water_gives_objective_and_two_bases_only,
    test_all_water_result_is_byte_equal_and_out_is_zeroed, test_return_value_equals_out_n.
  SLICE-U3 (grid, score, resource towns and sites, their ages and richness, defender slant,
    no-water for these): test_resource_sites_found_one_each_side, test_resource_sites_are_equidistant,
    test_resource_sites_sit_opposite_each_other_and_clear_of_the_objective,
    test_each_resource_site_is_300_from_a_neutral_settlement, test_resource_towns_come_first_and_clear_of_the_bases,
    test_resource_towns_match_the_reference_score, test_resource_places_are_on_dry_walkable_ground,
    test_resource_town_ages_follow_the_age_noise, test_richness_follows_the_formula_without_a_home_base,
    test_defender_slant_is_plus_10_on_the_site_nearer_the_home_base, test_no_home_base_archetypes_agree,
    test_richness_bounds_and_economy_mean, test_resource_towns_do_not_depend_on_the_archetype.
  SLICE-U4 (other towns, spacing, maximum, satellites, order, cap, the budget, the printed counts,
    the seed sweeps): test_same_inputs_twice_give_byte_equal_results, test_two_seeds_differ_on_the_flat_stub,
    test_no_two_settlements_or_bases_within_4000, test_non_resource_towns_keep_4000_from_the_objective,
    test_at_most_six_settlements_and_home_bases, test_no_place_on_water_or_unwalkable_ground,
    test_other_towns_match_the_reference_score, test_other_town_ages_follow_the_age_noise,
    test_satellites_stand_300_from_a_town_on_the_first_valid_axis_step, test_expansion_sites_only_for_towns_without_a_resource_site,
    test_order_of_places, test_ages_sides_and_richness_by_kind, test_place_count_is_at_most_64,
    test_runtime_under_the_budget_on_the_24000_flat_canvas, test_counts_of_neutral_settlements_are_printed,
    test_the_lying_adapter_is_flagged_on_an_engine_result.
  Stub-only and detector controls (green on the built tree): test_stub_*, test_inputs_are_*,
    test_ctypes_mirror_*, test_control_*, test_the_quoted_rules_are_the_bibles.
"""
import atexit
import ctypes
import math
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
from collections import namedtuple
from functools import lru_cache

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
STUB_SRC = REPO / "tests" / "csim" / "layout_stub_terrain.c"
# Same flags as test_PP_grid_margin_exact.py:33-36 (the Makefile's release build, -O2).
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]
ENGINE_SOURCES = [CSRC / "layout_engine.c", CSRC / "terrain_noise.c", STUB_SRC]
STUB_SOURCES = [CSRC / "terrain_noise.c", STUB_SRC]

# ---- the spec's numbers; every one is a named draft or a rule of the spec ------------------
CANVAS16 = 16000.0            # gap 1: every stub is for a 16,000 wu canvas
CANVAS24 = 24000.0            # the budget run (DRAFT-places-budget is the spec's 24,000 wu figure)
SPACING = 4000.0              # DRAFT-places-spacing
RES_CLEAR = 2400.0            # DRAFT-resource-clearance
RES_FAIR = 600.0              # DRAFT-resource-fairness
SAT_OFFSET = 300.0            # DRAFT-satellite-offset
SAT_TOL = 1.0                 # the spec's "300 wu (+-1)"
TOWNS_MAX = 6                 # DRAFT-towns-max
HOME_AGE = 40                 # DRAFT-home-age
TOWN_AGE_MIN, TOWN_AGE_MAX = 10, 40   # DRAFT-town-age-min, DRAFT-town-age-max
SLANT = 10                    # DRAFT-defender-slant
PLACE_CAP = 64                # OM_PLACE_CAP
BUDGET_S = 0.020              # DRAFT-places-budget
FLOOR = 0.35                  # DRAFT-places-floor
W_WATER, W_FLAT, W_NOISE = 0.45, 0.30, 0.25   # DRAFT-places-weights
WATER_CELLS_R2 = 36           # DRAFT-places-water-radius 600 wu, inclusive, integer squared cell distance (gap 5)
WATER_SAT = 12.0              # DRAFT-places-water-sat
FLAT_CELLS_R2 = 9             # DRAFT-places-flat-radius 300 wu, inclusive
FLAT_DISC = 29                # cells with squared distance <= 9
FLAT_SLOPE = 0.06             # DRAFT-places-flat-slope, strict
GRID_STEP, GRID_OFF = 4, 1    # DRAFT-places-grid: cell indices 1 mod 4
NOISE_LATTICE_WU = 1600       # DRAFT-places-noise-lattice
SALT_PLACES, SALT_AGE, SALT_RICH = 410, 450, 460
OCTAVES, GAIN_Q16 = 3, 32768  # DRAFT-places-noise-octaves, gain 0.5
RICH_BASE, RICH_SLOPE, RICH_MID = 0.2, 0.8, 0.5   # DRAFT-richness-formula
SIDES = (3, 5)                # base_side: player and enemy faction ids (any distinct values)

K_OBJECTIVE, K_HOME, K_FORWARD, K_NEUTRAL, K_RESOURCE, K_EXPANSION = 0, 9, 10, 11, 12, 13
# The E-22 R-177-02 table, archetype ids mission.c:161-170: (player's base kind, enemy's base kind).
H, F = K_HOME, K_FORWARD
BASE_TABLE = {0: (H, F), 1: (F, F), 2: (F, H), 3: (F, H), 4: (H, F),
              5: (H, F), 6: (F, F), 7: (H, F), 8: (F, F), 9: (H, F)}
NO_HOME_ARCHETYPES = (1, 6, 8)


# ---- ctypes mirrors -------------------------------------------------------------------------
class CPlace(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("kind", ctypes.c_int32),
                ("side", ctypes.c_int32), ("age_steps", ctypes.c_int32), ("richness", ctypes.c_int32)]


class CResult(ctypes.Structure):
    _fields_ = [("places", CPlace * PLACE_CAP), ("n", ctypes.c_int32)]


class CTerrain(ctypes.Structure):       # the adapter struct (the stub's out struct has the same layout)
    _fields_ = [("ctx", ctypes.c_void_p), ("height_at", ctypes.c_void_p),
                ("walkable_at", ctypes.c_void_p), ("nearest_walkable", ctypes.c_void_p)]


HEIGHT_FN = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_void_p, ctypes.c_double, ctypes.c_double)
WALK_FN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_double, ctypes.c_double)
NEAR_FN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                           ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double))

Pl = namedtuple("Pl", "x y kind side age rich")
Geo = namedtuple("Geo", "player enemy obj")
# Spawn-like geometry: bases at the top and bottom, 15 wu from the edge, the objective midway.
GEO16 = Geo((8000.0, 15.0), (8000.0, 15985.0), (8000.0, 8000.0))
GEO24 = Geo((12000.0, 15.0), (12000.0, 23985.0), (12000.0, 12000.0))
# The lake stub has its lake about (8000, 8000): the bases and the objective are placed by the test
# on dry walkable ground (x = 3000 is west of the lake and of the cliff).
GEO_LAKE = Geo((3000.0, 15.0), (3000.0, 15985.0), (3000.0, 8000.0))


def geo_for(stub_kind, canvas):
    if stub_kind == 1:
        return GEO_LAKE
    return GEO24 if canvas == CANVAS24 else GEO16


# ---- building and loading -------------------------------------------------------------------
_TMP = []
_BUILT = {}
_LIBS = {}


def _tmpdir():
    if not _TMP:
        _TMP.append(pathlib.Path(tempfile.mkdtemp(prefix="vg_p1_")))
        atexit.register(shutil.rmtree, str(_TMP[0]), True)
    return _TMP[0]


def _build(name, sources):
    if name not in _BUILT:
        out = _tmpdir() / f"lib_{name}.so"
        res = subprocess.run(["cc", *FLAGS, "-I", str(CSRC), "-shared", "-o", str(out),
                              *[str(p) for p in sources], "-lm"], capture_output=True, text=True)
        _BUILT[name] = (res, out)
    return _BUILT[name]


def _lib(name, sources):
    res, out = _build(name, sources)
    assert res.returncode == 0, res.stderr[-3000:]
    if name not in _LIBS:
        _LIBS[name] = ctypes.CDLL(str(out))        # default mode: an unresolved symbol fails the load (gap 3)
    return _LIBS[name]


def stub_lib():
    lib = _lib("stub", STUB_SOURCES)
    lib.om_stub_terrain.argtypes = [ctypes.c_int32, ctypes.POINTER(CTerrain)]
    lib.om_stub_terrain.restype = None
    lib.om_tn_fbm2.argtypes = [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int, ctypes.c_int32]
    lib.om_tn_fbm2.restype = ctypes.c_int32
    return lib


def engine_lib():
    lib = _lib("engine", ENGINE_SOURCES)
    lib.om_layout_places.argtypes = [
        ctypes.c_uint64, ctypes.c_double, ctypes.c_double, ctypes.c_int32, ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(CTerrain), ctypes.POINTER(CResult)]
    lib.om_layout_places.restype = ctypes.c_int
    return lib


class Stub:
    """One stub terrain: the C function pointers, called from Python through ctypes (no Python callbacks)."""

    def __init__(self, kind):
        self.kind = kind
        self.t = CTerrain()
        stub_lib().om_stub_terrain(kind, ctypes.byref(self.t))
        self._h = HEIGHT_FN(self.t.height_at) if self.t.height_at else None
        self._w = WALK_FN(self.t.walkable_at) if self.t.walkable_at else None
        self._n = NEAR_FN(self.t.nearest_walkable) if self.t.nearest_walkable else None

    def height(self, x, y):
        return self._h(self.t.ctx, x, y)

    def walkable(self, x, y):
        return bool(self._w(self.t.ctx, x, y))

    def nearest(self, x, y):
        ox, oy = ctypes.c_double(), ctypes.c_double()
        r = self._n(self.t.ctx, x, y, ctypes.byref(ox), ctypes.byref(oy))
        return r, ox.value, oy.value


@lru_cache(maxsize=None)
def stub(kind):
    return Stub(kind)


def fbm(seed, x_q16, y_q16):
    return stub_lib().om_tn_fbm2(seed, x_q16, y_q16, OCTAVES, GAIN_Q16)


def noise_q16(x_wu):
    """x_q16 = (int32)((int64)x_wu * 65536 / 1600), C truncation."""
    n = int(x_wu) * 65536
    return int(n / NOISE_LATTICE_WU) if n >= 0 else -int(-n / NOISE_LATTICE_WU)


def noise01(seed, salt, x, y):
    return (fbm(seed + salt, noise_q16(x), noise_q16(y)) + 65536) / 131072.0


def age_u_q16(seed, x, y):
    return (fbm(seed + SALT_AGE, noise_q16(x), noise_q16(y)) + 65536) // 2


def expected_age(seed, x, y):
    return TOWN_AGE_MIN + (30 * age_u_q16(seed, x, y) + 32768) // 65536


def expected_richness(seed, econ, x, y):
    n = noise01(seed, SALT_RICH, x, y)
    v = min(1.0, max(0.0, RICH_BASE + RICH_SLOPE * econ * (RICH_MID + n)))
    return int(math.floor(100.0 * v + 0.5))


# ---- running the engine ---------------------------------------------------------------------
Run = namedtuple("Run", "ret n places raw")


def call_engine(seed, canvas_w, canvas_h, arch, econ, geo, stub_kind, dirty=False, nulls=(), timer=None):
    lib = engine_lib()
    st = stub(stub_kind)
    bxy = (ctypes.c_double * 4)(*geo.player, *geo.enemy)
    bsd = (ctypes.c_int32 * 2)(*SIDES)
    out = CResult()
    if dirty:
        ctypes.memset(ctypes.byref(out.places), 0xA5, ctypes.sizeof(out.places))   # n stays 0: a missing zeroing shows as stale bytes, not a crash
    args = {"base_xy": bxy, "base_side": bsd, "t": ctypes.byref(st.t), "out": ctypes.byref(out)}
    for k in nulls:
        args[k] = None
    t0 = time.perf_counter()
    ret = lib.om_layout_places(seed, canvas_w, canvas_h, arch, econ, geo.obj[0], geo.obj[1],
                               args["base_xy"], args["base_side"], args["t"], args["out"])
    if timer is not None:
        timer.append(time.perf_counter() - t0)
    return ret, out


def _as_run(ret, out):
    places = tuple(Pl(p.x, p.y, p.kind, p.side, p.age_steps, p.richness) for p in out.places[:max(0, out.n)])
    raw = ctypes.string_at(ctypes.addressof(out), ctypes.sizeof(out))
    return Run(ret, out.n, places, raw)


@lru_cache(maxsize=None)
def run(seed, stub_kind, arch=0, econ=0.5, canvas=CANVAS16, dirty=False):
    geo = geo_for(stub_kind, canvas)
    ret, out = call_engine(seed, canvas, canvas, arch, econ, geo, stub_kind, dirty)
    return _as_run(ret, out)


STUB_FLAT, STUB_LAKE, STUB_ROLL, STUB_WATER = 0, 1, 2, 3
LAND_STUBS = (STUB_FLAT, STUB_LAKE, STUB_ROLL)
SEEDS64 = tuple(range(1, 65))
SWEEP_ARCHS = (0, 2)        # a HOME base on the player side, then on the enemy side


def bases_of(geo):
    return geo.player, geo.enemy


def of_kind(places, kind):
    return [p for p in places if p.kind == kind]


def dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def xy(p):
    return (p.x, p.y)


def sweep(check, stubs=LAND_STUBS, archs=SWEEP_ARCHS, seeds=SEEDS64, econ=0.5):
    """check(run_result, stub_kind, geo) -> list of problems; collects them all with the seed."""
    bad = []
    for sk in stubs:
        for arch in archs:
            for seed in seeds:
                r = run(seed, sk, arch, econ)
                for prob in check(r, sk, geo_for(sk, CANVAS16)):
                    bad.append(f"stub {sk} arch {arch} seed {seed}: {prob}")
    assert not bad, "\n".join(bad[:12]) + f"\n({len(bad)} problems)"


# ---- the detectors (each has a positive control below) -----------------------------------------
def no_water_violations(places, st):
    """Indices of places on water (height < 0) or on unwalkable ground, judged by stub st."""
    return [i for i, p in enumerate(places) if st.height(p.x, p.y) < 0.0 or not st.walkable(p.x, p.y)]


def equidistance_violations(places, b0, b1):
    """Indices of RESOURCE_SITEs with |D| > 600, D = |p-B0| - |p-B1| (R-191-04, DRAFT-resource-fairness)."""
    return [i for i, p in enumerate(places)
            if p.kind == K_RESOURCE and abs(dist(xy(p), b0) - dist(xy(p), b1)) > RES_FAIR]


def perp(b0, b1):
    dx, dy = b1[0] - b0[0], b1[1] - b0[1]
    ln = math.sqrt(dx * dx + dy * dy)
    return (-dy / ln, dx / ln)


def side_problems(places, b0, b1, obj):
    """Problems with the two resource sites: not exactly two, same side, or under 2,400 wu from the objective."""
    sites = of_kind(places, K_RESOURCE)
    if len(sites) != 2:
        return [f"{len(sites)} resource sites, want 2"]
    d = perp(b0, b1)
    t = [(s.x - obj[0]) * d[0] + (s.y - obj[1]) * d[1] for s in sites]
    out = []
    if not (t[0] * t[1] < 0):
        out.append(f"both sites on one side of the objective (t = {t[0]:.0f}, {t[1]:.0f})")
    for v in t:
        if abs(v) < RES_CLEAR:
            out.append(f"a site is {abs(v):.0f} wu from the objective along d, under {RES_CLEAR:.0f}")
    return out


def spacing_violations(places):
    """Pairs of base or settlement places (kinds 9, 10, 11) closer than 4,000 wu; satellites are exempt."""
    town = [(i, p) for i, p in enumerate(places) if p.kind in (K_HOME, K_FORWARD, K_NEUTRAL)]
    return [(i, j) for a, (i, p) in enumerate(town) for (j, q) in town[a + 1:] if dist(xy(p), xy(q)) < SPACING]


def max_town_violation(places):
    """True when settlements plus HOME bases exceed 6 (DRAFT-towns-max)."""
    return sum(1 for p in places if p.kind in (K_HOME, K_NEUTRAL)) > TOWNS_MAX


def base_kind_problems(places, arch, geo):
    """The R-177-02 table: kind, side, age and position of both bases."""
    exp = BASE_TABLE[arch]
    out = []
    for i, (kind, pos, side) in enumerate(zip(exp, bases_of(geo), SIDES), start=1):
        p = places[i]
        if p.kind != kind:
            out.append(f"place {i}: kind {p.kind}, table says {kind}")
        if p.side != side:
            out.append(f"place {i}: side {p.side}, want {side}")
        if (p.x, p.y) != pos:
            out.append(f"place {i}: at {(p.x, p.y)}, the base was given at {pos}")
        want_age = HOME_AGE if kind == K_HOME else 0
        if p.age != want_age:
            out.append(f"place {i}: age {p.age}, want {want_age}")
    return out


def used_prefix_equal(a, b):
    """Byte equality of n and of the used prefix of two raw om_layout_result buffers."""
    na = int.from_bytes(a[2048:2052], "little", signed=True)
    nb = int.from_bytes(b[2048:2052], "little", signed=True)
    return na == nb and a[:32 * na] == b[:32 * nb]


def slant_problems(base_places, home_places, home_xy):
    """The resource site nearer the HOME base has +10 over the run with no HOME base, the other is equal."""
    out = []
    b = {(p.x, p.y): p.rich for p in of_kind(base_places, K_RESOURCE)}
    h = {(p.x, p.y): p.rich for p in of_kind(home_places, K_RESOURCE)}
    if set(b) != set(h) or len(b) != 2:
        return [f"the sites differ between the runs: {sorted(b)} vs {sorted(h)}"]
    (qa, qb) = sorted(b)
    near = qa if dist(qa, home_xy) < dist(qb, home_xy) else qb if dist(qb, home_xy) < dist(qa, home_xy) else None
    for q in (qa, qb):
        want = b[q] + (SLANT if q == near else 0)
        want = min(100, want)
        if h[q] != want:
            out.append(f"site {q}: richness {h[q]}, want {want}")
    return out


# ---- the reference model of steps 3 to 5 (the score and the towns) -----------------------------
@lru_cache(maxsize=None)
def _grid(stub_kind, canvas):
    st = stub(stub_kind)
    n = int(canvas // 100)
    h = [st.height(i * 100.0 + 50.0, j * 100.0 + 50.0) for j in range(n) for i in range(n)]
    water = [v < 0.0 for v in h]
    slope = [0.0] * (n * n)
    for j in range(n):
        for i in range(n):
            hc = h[j * n + i]
            i1 = i + 1 if i + 1 < n else i - 1      # stepped inward when it would leave the canvas
            j1 = j + 1 if j + 1 < n else j - 1
            slope[j * n + i] = max(abs(h[j * n + i1] - hc), abs(h[j1 * n + i] - hc)) / 100.0
    return n, water, slope


@lru_cache(maxsize=None)
def _candidates(stub_kind, canvas):
    """Valid candidates (cells 1 mod 4, not water, walkable) with their seed-free score terms."""
    st = stub(stub_kind)
    n, water, slope = _grid(stub_kind, canvas)
    out = []
    for j in range(GRID_OFF, n, GRID_STEP):
        for i in range(GRID_OFF, n, GRID_STEP):
            x, y = i * 100.0 + 50.0, j * 100.0 + 50.0
            if water[j * n + i] or not st.walkable(x, y):
                continue
            nw = flat = inside = 0
            for dj in range(-6, 7):
                for di in range(-6, 7):
                    d2 = di * di + dj * dj
                    if d2 > WATER_CELLS_R2:
                        continue
                    ii, jj = i + di, j + dj
                    if not (0 <= ii < n and 0 <= jj < n):
                        continue
                    if water[jj * n + ii]:
                        nw += 1
                    if d2 <= FLAT_CELLS_R2:
                        inside += 1
                        if slope[jj * n + ii] < FLAT_SLOPE:
                            flat += 1
            out.append((x, y, nw, flat, inside))
    return out


def model_towns(seed, stub_kind, canvas, arch, geo, mode):
    """Steps 3 to 5. mode 1: flatness is the share of the in-canvas cells of the disc; mode 2: of all 29.
    Returns (resource, others): resource = [(px, py, qx, qy)], others = [(px, py)] in the order chosen."""
    st = stub(stub_kind)
    scored = []
    for (x, y, nw, flat, inside) in _candidates(stub_kind, canvas):
        flatness = flat / inside if mode == 1 else flat / float(FLAT_DISC)
        s = (W_WATER * min(1.0, nw / WATER_SAT) + W_FLAT * flatness
             + W_NOISE * noise01(seed, SALT_PLACES, x, y))
        scored.append((-s, y, x, s))
    scored.sort()                                       # greatest s, then lower y, then lower x
    b0, b1, obj = geo.player, geo.enemy, geo.obj
    d = perp(b0, b1)

    def D(px, py):
        return dist((px, py), b0) - dist((px, py), b1)

    resource = []
    for sigma in (-1, 1):
        for (_, y, x, s) in scored:
            if sigma * ((x - obj[0]) * d[0] + (y - obj[1]) * d[1]) < RES_CLEAR or abs(D(x, y)) > RES_FAIR:
                continue
            if dist((x, y), b0) < SPACING or dist((x, y), b1) < SPACING:
                continue
            qx, qy = x + sigma * SAT_OFFSET * d[0], y + sigma * SAT_OFFSET * d[1]
            if not (0.0 <= qx < canvas and 0.0 <= qy < canvas):
                continue
            if st.height(qx, qy) < 0.0 or not st.walkable(qx, qy) or abs(D(qx, qy)) > RES_FAIR:
                continue
            resource.append((x, y, qx, qy))
            break
    towns = [(r[0], r[1]) for r in resource]
    n_home = sum(1 for k in BASE_TABLE[arch] if k == K_HOME)
    others = []
    fixed = [b0, b1, obj]
    for (_, y, x, s) in scored:
        if s <= FLOOR or len(towns) + n_home >= TOWNS_MAX:
            break
        if any(dist((x, y), f) < SPACING for f in fixed) or any(dist((x, y), t) < SPACING for t in towns):
            continue
        towns.append((x, y))
        others.append((x, y))
    return resource, others


def model_matches(seed, stub_kind, canvas, arch, r, resource_only=False):
    """Does the engine result r have the model's resource towns (as a set, order of the two not asserted),
    sites, and other towns in order, in either edge-flatness mode?"""
    geo = geo_for(stub_kind, canvas)
    towns = [(p.x, p.y) for p in of_kind(r.places, K_NEUTRAL)]
    sites = sorted((p.x, p.y) for p in of_kind(r.places, K_RESOURCE))
    msgs = []
    for mode in (1, 2):
        resource, others = model_towns(seed, stub_kind, canvas, arch, geo, mode)
        nr = len(resource)
        ok = (len(towns) >= nr
              and set(towns[:nr]) == {(a, b) for (a, b, _, _) in resource}
              and (resource_only or (len(towns) == nr + len(others) and towns[nr:] == others))
              and len(sites) == nr
              and all(abs(s[0] - q[0]) < 1e-6 and abs(s[1] - q[1]) < 1e-6
                      for s, q in zip(sites, sorted((c, d) for (_, _, c, d) in resource))))
        if ok:
            return []
        msgs.append(f"mode {mode}: resource towns {[(a, b) for (a, b, _, _) in resource]}, others {others}")
    return [f"engine towns {towns} sites {sites}; " + " | ".join(msgs)]


# =============================================================================================
# 1. Stub-only checks (green on the built tree)
# =============================================================================================
def _share(st, canvas=CANVAS16):
    n = int(canvas // 100)
    pts = [(i * 100.0 + 50.0, j * 100.0 + 50.0) for j in range(n) for i in range(n)]
    hs = [st.height(x, y) for (x, y) in pts]
    water = sum(1 for v in hs if v < 0.0) / len(pts)
    unwalk = sum(1 for (x, y) in pts if not st.walkable(x, y)) / len(pts)
    return water, unwalk, min(hs), max(hs)


def test_stub_premises_are_dumped():
    """Premises (gap 1): the four stubs over the 16,000 wu canvas, printed and sanity-asserted. Rule id: none
    (fixture)."""
    for kind, name in ((0, "flat"), (1, "lake and cliff"), (2, "rolling"), (3, "all water")):
        st = stub(kind)
        water, unwalk, lo, hi = _share(st)
        samples = [st.height(8000.0, 8000.0), st.height(3000.0, 15.0), st.height(12000.0, 12000.0)]
        print(f"STUB {kind} {name}: water share {water:.4f} unwalkable share {unwalk:.4f} "
              f"height min {lo:.3f} max {hi:.3f} samples (8000,8000) (3000,15) (12000,12000) = "
              + ", ".join(f"{v:.3f}" for v in samples))
        if kind == 0:
            assert (water, unwalk, lo, hi) == (0.0, 0.0, 50.0, 50.0)
        if kind in (1, 2):
            assert 0.0 < water < 1.0 and 0.0 < unwalk < 1.0
        if kind == 3:
            assert (water, unwalk, lo, hi) == (1.0, 1.0, -20.0, -20.0)


def test_stub_flat_is_height_50_walkable_everywhere():
    """Gap 1, kind 0. Rule id: none (fixture)."""
    st = stub(0)
    for (x, y) in ((0.0, 0.0), (8000.0, 8000.0), (15999.0, 15999.0), (123.0, 9876.0)):
        assert st.height(x, y) == 50.0 and st.walkable(x, y)
        assert st.nearest(x, y) == (0, x, y)


def test_stub_lake_and_cliff_numbers():
    """Gap 1, kind 1: lake -20 wu in the radius-2,000 disc about (8000, 8000); height 50 for x < 11,000, 650 from
    11,000; unwalkable in the lake and in x in [10,900, 11,100]. Rule id: none (fixture)."""
    st = stub(1)
    assert st.height(8000.0, 8000.0) == -20.0 and not st.walkable(8000.0, 8000.0)
    assert st.height(5990.0, 8000.0) == 50.0 and st.walkable(5990.0, 8000.0)
    assert st.height(10890.0, 3000.0) == 50.0 and st.walkable(10890.0, 3000.0)
    assert st.height(10950.0, 3000.0) == 50.0 and not st.walkable(10950.0, 3000.0)
    assert st.height(11000.0, 3000.0) == 650.0 and not st.walkable(11000.0, 3000.0)
    assert st.height(11050.0, 3000.0) == 650.0 and not st.walkable(11050.0, 3000.0)
    assert st.height(11200.0, 3000.0) == 650.0 and st.walkable(11200.0, 3000.0)
    assert abs(st.height(11050.0, 3000.0) - st.height(10950.0, 3000.0)) / 100.0 == 6.0   # the slope-6 step
    r, ox, oy = st.nearest(8000.0, 8000.0)
    assert r == 0 and st.walkable(ox, oy) and st.height(ox, oy) >= 0.0


def test_stub_rolling_matches_the_gap_1_formula_and_has_water_and_ground():
    """Gap 1, kind 2: height = 35 + 100 * om_tn_fbm2(1234, x*65536/3200, y*65536/3200, 3, 32768) / 65536 wu;
    water below 0; walkable exactly where not water. Rule id: none (fixture)."""
    st = stub(2)
    n_water = 0
    for j in range(0, 160, 7):
        for i in range(0, 160, 7):
            x, y = i * 100.0 + 50.0, j * 100.0 + 50.0
            f = stub_lib().om_tn_fbm2(1234, int(x) * 65536 // 3200, int(y) * 65536 // 3200, 3, 32768)
            assert st.height(x, y) == 35.0 + 100.0 * f / 65536.0
            assert st.walkable(x, y) == (st.height(x, y) >= 0.0)
            n_water += st.height(x, y) < 0.0
    assert 0 < n_water < 23 * 23


def test_stub_all_water_has_nothing_walkable():
    """Gap 1, kind 3: height -20 everywhere, nothing walkable, nearest_walkable returns -1. Rule id: none."""
    st = stub(3)
    for (x, y) in ((0.0, 0.0), (8000.0, 8000.0), (15999.0, 15999.0)):
        assert st.height(x, y) == -20.0 and not st.walkable(x, y)
        assert st.nearest(x, y)[0] == -1


def test_stub_unknown_kind_leaves_the_struct_zeroed():
    """The stub fixture contract: a kind outside 0..3 zeroes the out struct. Rule id: none (fixture)."""
    t = CTerrain(1, 2, 3, 4)
    stub_lib().om_stub_terrain(7, ctypes.byref(t))
    assert (t.ctx, t.height_at, t.walkable_at, t.nearest_walkable) == (None, None, None, None)


def test_inputs_are_on_dry_walkable_ground():
    """Premise: the objective and both bases the tests pass are dry and walkable on the stub they are used with
    (the lake stub's objective and bases are placed by the test, not in the lake). Rule id: R-191-02."""
    for sk, canvas in ((0, CANVAS16), (0, CANVAS24), (1, CANVAS16), (2, CANVAS16)):
        geo = geo_for(sk, canvas)
        for pt in (geo.player, geo.enemy, geo.obj):
            assert stub(sk).height(*pt) >= 0.0 and stub(sk).walkable(*pt), (sk, pt)


def test_ctypes_mirror_has_the_spec_sizes():
    """The 32-byte om_place (no padding), OM_PLACE_CAP 64, om_layout_result 2,056 bytes. Rule id: none (interface)."""
    assert ctypes.sizeof(CPlace) == 32
    assert [getattr(CPlace, f).offset for f in ("x", "y", "kind", "side", "age_steps", "richness")] == [0, 8, 16, 20, 24, 28]
    assert ctypes.sizeof(CResult) == PLACE_CAP * 32 + 8 and CResult.n.offset == PLACE_CAP * 32
    assert ctypes.sizeof(CTerrain) == 32


def test_the_quoted_rules_are_the_bibles():
    """Method rev 3: every rule quoted in the module docstring is the bible's text, word for word. Rules: R-177-02,
    R-177-06, R-191-02..06, R-193-01, Q-191-03."""
    doc = " ".join(__doc__.split())
    e22 = (REPO / "docs/bible/epics/E-22-economy-and-bases.md").read_text().split("\n")
    e17 = (REPO / "docs/bible/epics/E-17-map-generation.md").read_text().split("\n")
    for lines, rid in ((e22, "R-177-02"), (e22, "R-177-06"), (e17, "R-191-02"), (e17, "R-191-03"),
                       (e17, "R-191-04"), (e17, "R-191-05"), (e17, "R-191-06"), (e17, "R-193-01")):
        text = [l[2:] for l in lines if l.startswith("- " + rid + " ")]
        assert len(text) == 1, rid
        assert " ".join(text[0].split()) in doc, f"{rid} is not quoted word for word"
    i = [k for k, l in enumerate(e22) if l.startswith("- R-177-02 ")][0]
    rows = [l for l in e22[i:i + 14] if l.startswith("|")]
    assert len(rows) == 8 and all(" ".join(r.split()) in doc for r in rows), "the R-177-02 table is not quoted"
    reg = (REPO / "docs/northstar/ambiguity_register.md").read_text()
    m = re.search(r'verbatim: "(Q191-03: .*?)" Read as', reg)
    assert m and " ".join(m.group(1).split()) in doc, "Q-191-03 is not quoted word for word"


# =============================================================================================
# 2. Detector controls (green on the built tree): each detector fails on a known bad input
#    and passes a clean one. Rules: R-191-04 (equal distance), R-191-06 / R-177-02 (spacing and kinds), R-177-06.
# =============================================================================================
B0, B1, OBJ = GEO16.player, GEO16.enemy, GEO16.obj


def mk(kind, x, y, side=-1, age=0, rich=0):
    return Pl(float(x), float(y), kind, side, age, rich)


def _clean_list():
    return [mk(0, 8000, 8000), mk(K_HOME, *B0, SIDES[0], HOME_AGE), mk(K_FORWARD, *B1, SIDES[1]),
            mk(K_NEUTRAL, 11000, 8000, age=20), mk(K_RESOURCE, 11300, 8000, rich=50),
            mk(K_NEUTRAL, 5000, 8000, age=20), mk(K_RESOURCE, 4700, 8000, rich=50)]


def test_control_clean_list_passes_every_detector():
    """Positive control for the controls: a clean hand-built list is not flagged by any detector (so a flagged
    list below is flagged for its defect). Rules: R-191-04, R-191-06."""
    pl = _clean_list()
    assert equidistance_violations(pl, B0, B1) == []
    assert side_problems(pl, B0, B1, OBJ) == []
    assert spacing_violations(pl) == []
    assert not max_town_violation(pl)
    assert no_water_violations(pl, stub(0)) == []
    assert base_kind_problems(pl, 0, GEO16) == []


def test_control_no_water_detector_flags_a_lying_adapter():
    """Positive control, no-water detector: places judged against the all-water stub's true heights are every one
    flagged (a lying adapter claiming dry ground). Rule: R-193-01 (water shapes where towns go)."""
    pl = _clean_list()
    assert len(no_water_violations(pl, stub(3))) == len(pl)
    assert no_water_violations([mk(K_NEUTRAL, 3000, 8000)], stub(1)) == []
    pl_lake = [mk(K_NEUTRAL, 8000, 8000)]                           # in the lake of stub 1
    assert no_water_violations(pl_lake, stub(1)) == [0]
    assert no_water_violations([mk(K_NEUTRAL, 10950, 3000)], stub(1)) == [0]    # on the unwalkable cliff band


def _d_off(x, target):
    """A y below the middle at which D = target at column x (bisection)."""
    lo, hi = 8000.0, 15985.0
    for _ in range(80):
        mid = (lo + hi) / 2
        dv = dist((x, mid), B0) - dist((x, mid), B1)
        lo, hi = (mid, hi) if dv < target else (lo, mid)
    return (lo + hi) / 2


def test_control_equidistance_detector_flags_a_site_900_wu_off():
    """Positive control, equidistance detector (R-191-04): a resource site 900 wu off equidistance fails it; one on
    the bisector and one at 590 wu pass."""
    y = _d_off(11300.0, 900.0)
    assert abs(dist((11300.0, y), B0) - dist((11300.0, y), B1) - 900.0) < 1e-6
    pl = [mk(K_RESOURCE, 11300, y), mk(K_RESOURCE, 4700, 8000)]
    assert equidistance_violations(pl, B0, B1) == [0]
    ok = [mk(K_RESOURCE, 11300, _d_off(11300.0, 590.0)), mk(K_RESOURCE, 4700, 8000)]
    assert equidistance_violations(ok, B0, B1) == []


def test_control_side_detector_flags_both_sites_on_one_side():
    """Positive control, side detector (R-191-04, 'opposite the objective' as the spec reads it): both sites on the
    same side fail it, as do sites under 2,400 wu from the objective and a count other than two."""
    same = [mk(K_RESOURCE, 11300, 8000), mk(K_RESOURCE, 13300, 8000)]
    assert side_problems(same, B0, B1, OBJ)
    near = [mk(K_RESOURCE, 9500, 8000), mk(K_RESOURCE, 4700, 8000)]
    assert side_problems(near, B0, B1, OBJ)
    assert side_problems([mk(K_RESOURCE, 11300, 8000)], B0, B1, OBJ)
    assert side_problems(_clean_list(), B0, B1, OBJ) == []


def test_control_spacing_detector_flags_two_towns_1500_wu_apart():
    """Positive control, spacing detector (R-191-06, DRAFT-places-spacing 4,000 wu): two towns 1,500 wu apart fail
    it; 4,000 apart passes (at least 4,000); a satellite 300 wu from its town is exempt."""
    pl = [mk(K_NEUTRAL, 3000, 8000), mk(K_NEUTRAL, 4500, 8000)]
    assert spacing_violations(pl) == [(0, 1)]
    assert spacing_violations([mk(K_NEUTRAL, 3000, 8000), mk(K_NEUTRAL, 7000, 8000)]) == []
    assert spacing_violations([mk(K_NEUTRAL, 3000, 8000), mk(K_EXPANSION, 3300, 8000)]) == []
    assert spacing_violations([mk(K_HOME, 3000, 8000), mk(K_NEUTRAL, 3500, 8000)]) == [(0, 1)]


def test_control_maximum_detector_flags_seven_towns():
    """Positive control, maximum detector (DRAFT-towns-max 6 settlements and HOME bases together): seven towns
    fail it, six pass, a HOME base counts."""
    seven = [mk(K_NEUTRAL, 1000 + 4000 * i, 8000) for i in range(7)]
    assert max_town_violation(seven)
    assert not max_town_violation(seven[:6])
    assert max_town_violation(seven[:6] + [mk(K_HOME, 8000, 15)])
    assert not max_town_violation(seven[:5] + [mk(K_HOME, 8000, 15)])


def test_control_base_kind_detector_flags_a_swapped_kind():
    """Positive control, base-kind table detector (R-177-02): a base list with the two kinds swapped fails it for
    each archetype whose table row has two different kinds; a wrong age and a moved base fail it too."""
    for arch, (kp, ke) in BASE_TABLE.items():
        good = [mk(0, 8000, 8000), mk(kp, *B0, SIDES[0], HOME_AGE if kp == K_HOME else 0),
                mk(ke, *B1, SIDES[1], HOME_AGE if ke == K_HOME else 0)]
        assert base_kind_problems(good, arch, GEO16) == [], arch
        swapped = [good[0], good[1]._replace(kind=ke), good[2]._replace(kind=kp)]
        assert (base_kind_problems(swapped, arch, GEO16) != []) == (kp != ke), arch
    good0 = [mk(0, 8000, 8000), mk(K_HOME, *B0, SIDES[0], HOME_AGE), mk(K_FORWARD, *B1, SIDES[1])]
    assert base_kind_problems([good0[0], good0[1]._replace(age=39), good0[2]], 0, GEO16)
    assert base_kind_problems([good0[0], good0[1]._replace(x=B0[0] + 1.0), good0[2]], 0, GEO16)


def test_control_byte_equality_detector_flags_one_flipped_byte():
    """Positive control, byte-equality detector: two equal buffers pass; one flipped byte in the used prefix, or in
    n, fails it; a flipped byte beyond the used prefix does not touch the used-prefix check."""
    a = bytearray(ctypes.sizeof(CResult))
    a[:32 * 3] = bytes(range(96))
    a[2048:2052] = (3).to_bytes(4, "little")
    b = bytearray(a)
    assert used_prefix_equal(bytes(a), bytes(b))
    b[40] ^= 1
    assert not used_prefix_equal(bytes(a), bytes(b))
    c = bytearray(a)
    c[2048] = 2
    assert not used_prefix_equal(bytes(a), bytes(c))
    d = bytearray(a)
    d[32 * 3 + 5] ^= 1
    assert used_prefix_equal(bytes(a), bytes(d)) and bytes(a) != bytes(d)


def test_control_richness_slant_detector_flags_an_unslanted_pair():
    """Positive control, richness-slant detector (R-177-06, DRAFT-defender-slant +10): a pair of runs with no slant
    fails it; the +10 on the site nearer the HOME base (player base B0 = (8000, 15)) passes; the cap at 100 holds."""
    sites = [mk(K_RESOURCE, 11300, 7000, rich=40), mk(K_RESOURCE, 4700, 9000, rich=44)]
    base_run = sites
    assert slant_problems(base_run, base_run, B0)                       # unslanted: flagged
    near = sites[0]                                                     # (11300, 7000) is nearer B0
    assert dist(xy(near), B0) < dist(xy(sites[1]), B0)
    slanted = [near._replace(rich=50), sites[1]]
    assert slant_problems(base_run, slanted, B0) == []
    assert slant_problems(base_run, [near._replace(rich=40), sites[1]._replace(rich=54)], B0)   # slant on the wrong site
    capped = [near._replace(rich=95), sites[1]]
    assert slant_problems(capped, [near._replace(rich=100), sites[1]], B0) == []


# =============================================================================================
# 3. The size link (gap 8): red until csrc/layout_internal.h exists
# =============================================================================================
SIZELINK_C = r'''
#include <stddef.h>
#include <stdint.h>
#include "layout_internal.h"
#include "layout_stub_terrain.c"
#define SAME(f) _Static_assert(offsetof(om_layout_terrain, f) == offsetof(om_stub_layout_terrain, f), "offset " #f);
_Static_assert(sizeof(om_layout_terrain) == sizeof(om_stub_layout_terrain), "sizeof the adapter struct");
SAME(ctx) SAME(height_at) SAME(walkable_at) SAME(nearest_walkable)
_Static_assert(sizeof(om_place) == 32, "om_place is 32 bytes, no padding");
_Static_assert(offsetof(om_place, x) == 0 && offsetof(om_place, y) == 8 && offsetof(om_place, kind) == 16, "om_place offsets");
_Static_assert(offsetof(om_place, side) == 20 && offsetof(om_place, age_steps) == 24 && offsetof(om_place, richness) == 28, "om_place offsets");
_Static_assert(OM_PLACE_CAP == 64, "OM_PLACE_CAP");
_Static_assert(offsetof(om_layout_result, n) == 2048 && sizeof(om_layout_result) == 2056, "om_layout_result");
_Static_assert(OM_PLACE_OBJECTIVE == 0 && OM_PLACE_BASE_HOME == 9 && OM_PLACE_BASE_FORWARD == 10, "kind ids");
_Static_assert(OM_PLACE_NEUTRAL_SETTLEMENT == 11 && OM_PLACE_RESOURCE_SITE == 12, "kind ids");
_Static_assert(OM_PLACE_EXPANSION_SITE == 13 && OM_PLACE_ECONOMIC_LOCATION == 14, "kind ids");
'''


def test_stub_adapter_struct_equals_layout_internal_h():
    """Gap 8: a small C file includes csrc/layout_internal.h, then the stub .c, and asserts equal sizeof and
    offsetof of every adapter field, the 32-byte om_place, OM_PLACE_CAP and the kind ids with _Static_assert.
    Rule id: none (interface)."""
    src = _tmpdir() / "sizelink.c"
    src.write_text(SIZELINK_C)
    res = subprocess.run(["cc", "-std=c11", "-fsyntax-only", "-Wall", "-Wextra", "-I", str(CSRC),
                          "-I", str(STUB_SRC.parent), str(src)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]


# =============================================================================================
# 4. The engine (red until csrc/layout_engine.c builds). SLICE-U2 first.
# =============================================================================================
@pytest.mark.parametrize("null", ["base_xy", "base_side", "t", "out"])
def test_null_pointer_returns_minus_one(null):
    """SLICE-U2. Interface: returns -1 on a NULL pointer. Rule id: R-191-01 (places by rule; interface)."""
    ret, _ = call_engine(1, CANVAS16, CANVAS16, 0, 0.5, GEO16, 0, nulls=(null,))
    assert ret == -1


@pytest.mark.parametrize("w,h", [(16050.0, 16050.0), (16000.0, 15900.0), (24100.0, 24100.0)],
                         ids=["not-a-multiple-of-100", "w-differs-from-h", "above-24000"])
def test_bad_canvas_returns_minus_one(w, h):
    """SLICE-U2. Interface: canvas_w == canvas_h, a multiple of 100, at most 24000, else -1. Rule id: R-191-01."""
    ret, _ = call_engine(1, w, h, 0, 0.5, GEO16, 0)
    assert ret == -1
    assert call_engine(1, CANVAS16, CANVAS16, 0, 0.5, GEO16, 0)[0] >= 1       # the same call, a good canvas


@pytest.mark.parametrize("arch", [10, -1])
def test_bad_archetype_returns_minus_one(arch):
    """SLICE-U2. Interface: archetype outside 0..9 returns -1. Rule id: R-177-02 (ten archetypes)."""
    assert call_engine(1, CANVAS16, CANVAS16, arch, 0.5, GEO16, 0)[0] == -1


def test_return_value_equals_out_n():
    """SLICE-U2. Interface: returns out->n (>= 1). Rule id: R-191-02."""
    for sk in (0, 3):
        r = run(1, sk)
        assert r.ret == r.n >= 1


def test_the_objective_is_first_and_unmoved():
    """SLICE-U2, step 1. R-191-02: 'the map has the objective'; kind 0, side -1, at the given position, age 0,
    richness 0; the engine moves no objective."""
    for sk in LAND_STUBS:
        geo = geo_for(sk, CANVAS16)
        p = run(1, sk).places[0]
        assert (p.kind, p.side, p.x, p.y, p.age, p.rich) == (0, -1, geo.obj[0], geo.obj[1], 0, 0)


@pytest.mark.parametrize("arch", range(10))
def test_base_kinds_sides_ages_for_all_ten_archetypes(arch):
    """SLICE-U2, step 2. R-177-02 table, both sides: HOME where the archetype gives the player a home or a defended
    settlement, a FORWARD camp for an attacker; HOME age 40 (DRAFT-home-age), FORWARD 0; bases at the given spawn
    positions, side = base_side[i], player first."""
    for sk in LAND_STUBS:
        r = run(1, sk, arch)
        assert base_kind_problems(r.places, arch, geo_for(sk, CANVAS16)) == []


def test_all_water_gives_objective_and_two_bases_only():
    """SLICE-U2, gap 1 kind 3. R-193-01 (water shapes where towns go): on all water there is no valid candidate,
    so the engine returns the objective and the two bases only: n == 3, no settlement, no resource site, no
    satellite."""
    for arch in range(10):
        r = run(1, STUB_WATER, arch)
        assert r.n == 3 and len(r.places) == 3, arch
        assert [p.kind for p in r.places] == [K_OBJECTIVE, *BASE_TABLE[arch]], arch


def test_all_water_result_is_byte_equal_and_out_is_zeroed():
    """SLICE-U2. Determinism of the trivial result: same inputs twice give a byte-equal used prefix and n; the
    result struct is zeroed before it is filled (a result whose places are pre-filled with 0xA5 gives the same bytes as a clean one)."""
    for arch in (0, 1, 9):
        a = _as_run(*call_engine(7, CANVAS16, CANVAS16, arch, 0.5, GEO16, STUB_WATER))
        b = _as_run(*call_engine(7, CANVAS16, CANVAS16, arch, 0.5, GEO16, STUB_WATER))
        d = _as_run(*call_engine(7, CANVAS16, CANVAS16, arch, 0.5, GEO16, STUB_WATER, dirty=True))
        assert used_prefix_equal(a.raw, b.raw) and used_prefix_equal(a.raw, d.raw)
        assert a.raw == b.raw == d.raw


# ---- SLICE-U3: resource towns and sites -------------------------------------------------------
def test_resource_sites_found_one_each_side():
    """SLICE-U3, step 4. R-191-04, R-177-06 ('the player always has the means'): on the three land stubs, seeds 1
    to 64, exactly two RESOURCE_SITEs are found (DRAFT-resource-sites-min 2: the fixture asserts both found)."""
    sweep(lambda r, sk, g: [] if len(of_kind(r.places, K_RESOURCE)) == 2 else [f"{len(of_kind(r.places, K_RESOURCE))} sites"])


def test_resource_sites_are_equidistant():
    """SLICE-U3, step 4. R-191-04: 'each side is at the same distance from the objective and from each significant
    resource'; the spec's measure |D| <= 600 (DRAFT-resource-fairness) with D = |p-B0| - |p-B1|, seeds 1 to 64."""
    sweep(lambda r, sk, g: [f"site index {i} off equidistance" for i in equidistance_violations(r.places, g.player, g.enemy)])


def test_resource_sites_sit_opposite_each_other_and_clear_of_the_objective():
    """SLICE-U3, step 4. R-191-04 / Q-191-03, 'opposite the objective' as the spec reads it: one site each side of
    the objective along the line level between the bases (sigma*t of opposite signs), each at least 2,400 wu
    (DRAFT-resource-clearance) from it, seeds 1 to 64."""
    sweep(lambda r, sk, g: side_problems(r.places, g.player, g.enemy, g.obj))


def test_each_resource_site_is_300_from_a_neutral_settlement():
    """SLICE-U3, step 4. R-191-06 and R-177-06 (the neutral towns 'that contain resources'): each RESOURCE_SITE is
    300 wu (+-1, DRAFT-satellite-offset) from a NEUTRAL_SETTLEMENT, along d (the perpendicular of the base line)."""
    def check(r, sk, g):
        out = []
        d = perp(g.player, g.enemy)
        towns = of_kind(r.places, K_NEUTRAL)
        for s in of_kind(r.places, K_RESOURCE):
            near = [t for t in towns if abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL]
            if not near:
                out.append(f"site {xy(s)} has no neutral settlement 300 wu away")
                continue
            t = near[0]
            along = abs((s.x - t.x) * d[0] + (s.y - t.y) * d[1])
            if abs(along - SAT_OFFSET) > SAT_TOL:
                out.append(f"site {xy(s)} is not 300 wu from its town along d")
        return out
    sweep(check)


def test_resource_towns_come_first_and_clear_of_the_bases():
    """SLICE-U3, steps 4 and 9. R-191-04: the resource-hosting towns are chosen first, at least 4,000 wu
    (DRAFT-places-spacing) from both bases; the first two NEUTRAL_SETTLEMENTs in the list are the hosts."""
    def check(r, sk, g):
        out = []
        towns = of_kind(r.places, K_NEUTRAL)
        sites = of_kind(r.places, K_RESOURCE)
        hosts = [t for t in towns if any(abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL for s in sites)]
        if len(hosts) != 2 or set(towns[:2]) != set(hosts):
            out.append("the first two neutral settlements are not the two resource hosts")
        for t in hosts:
            if dist(xy(t), g.player) < SPACING or dist(xy(t), g.enemy) < SPACING:
                out.append(f"host {xy(t)} is under 4,000 wu from a base")
        return out
    sweep(check)


def test_resource_towns_match_the_reference_score():
    """SLICE-U3, steps 3 and 4. R-193-01 ('shaped by water, slope'; rivers, coasts and flats drive the score) and
    R-191-04: the score s = 0.45*water_within + 0.30*flatness + 0.25*noise01 (DRAFT-places-weights) on a grid of cells
    1 mod 4 (DRAFT-places-grid), water within 600 wu, flat within 300 wu (inclusive, gap 5; slope under 0.06
    strict), noise lattice 1,600 wu; the resource-hosting towns are the best-scoring valid candidate of each side
    (no floor), with the satellite point q inside the canvas, dry, walkable, |D(q)| <= 600. An independent Python
    model of the spec; the edge-flatness share is accepted either way."""
    bad = []
    for sk in LAND_STUBS:
        for arch in (0, 1):
            for seed in range(1, 9):
                bad += [f"stub {sk} arch {arch} seed {seed}: {m}"
                        for m in model_matches(seed, sk, CANVAS16, arch, run(seed, sk, arch), resource_only=True)]
    assert not bad, "\n".join(bad[:6])


def test_resource_places_are_on_dry_walkable_ground():
    """SLICE-U3, step 4. R-193-01 (water): the resource towns and sites stand on dry walkable ground on all three
    land stubs, seeds 1 to 64 (the lake-and-cliff stub has a lake and an unwalkable band)."""
    def check(r, sk, g):
        pl = [p for p in r.places if p.kind == K_RESOURCE]
        pl += [t for t in of_kind(r.places, K_NEUTRAL)[:2]]
        return [f"{xy(pl[i])} on water or unwalkable" for i in no_water_violations(pl, stub(sk))]
    sweep(check)


def test_resource_town_ages_follow_the_age_noise():
    """SLICE-U3, step 6. R-191-06: neutral settlements 'exist at mission start already grown, each to a seeded age':
    age_steps = 10 + (30*u_q16 + 32768) / 65536, u_q16 = (om_tn_fbm2(seed + 450, x_q16, y_q16, 3, 32768) + 65536) / 2
    at the town's position, for the resource-hosting towns; in [10, 40] (DRAFT-town-age-min, DRAFT-town-age-max)."""
    bad = []
    for sk in LAND_STUBS:
        for seed in SEEDS64:
            for t in of_kind(run(seed, sk, 0).places, K_NEUTRAL)[:2]:
                want = expected_age(seed, t.x, t.y)
                if t.age != want or not (TOWN_AGE_MIN <= t.age <= TOWN_AGE_MAX):
                    bad.append(f"stub {sk} seed {seed}: town {xy(t)} age {t.age}, formula {want}")
    assert not bad, "\n".join(bad[:8])


def _rich_check(seed, econ, arch, sk):
    r = run(seed, sk, arch, econ)
    return [f"seed {seed} site {xy(s)} richness {s.rich}, formula {expected_richness(seed, econ, s.x, s.y)}"
            for s in of_kind(r.places, K_RESOURCE) if s.rich != expected_richness(seed, econ, s.x, s.y)]


def test_richness_follows_the_formula_without_a_home_base():
    """SLICE-U3, step 8. R-177-06: 'resources are sometimes limited and sometimes abundant ... richness is derived
    from the region fields ... a region with a big economy gives a mission big resources': richness =
    round(100 * clamp(0.2 + 0.8 * region_economy * (0.5 + n), 0, 1)), n = noise01 with seed + 460 at the site
    (DRAFT-richness-formula), checked with archetypes 1, 6 and 8 (no HOME base, so no slant) at economies 0.2, 0.6, 1.0."""
    bad = []
    for sk in (STUB_FLAT, STUB_ROLL):
        for arch in NO_HOME_ARCHETYPES:
            for econ in (0.2, 0.6, 1.0):
                for seed in range(1, 17):
                    bad += _rich_check(seed, econ, arch, sk)
    assert not bad, "\n".join(bad[:8])


def test_defender_slant_is_plus_10_on_the_site_nearer_the_home_base():
    """SLICE-U3, step 8. R-177-06: 'slanted ... so that a defender has the better position': when one base is
    BASE_HOME, the resource site nearer that base (strict <, distance from the site point; equal gives no slant, gap 5)
    has +10 (DRAFT-defender-slant) over the same seed run with an archetype with no HOME base (economy 0.2 so nothing
    clamps), capped at 100 (checked at economy 1.0 too)."""
    bad = []
    for sk in (STUB_FLAT, STUB_ROLL, STUB_LAKE):
        geo = geo_for(sk, CANVAS16)
        for arch in (0, 2, 3, 9):
            home_xy = geo.player if BASE_TABLE[arch][0] == K_HOME else geo.enemy
            for econ in (0.2, 1.0):
                for seed in range(1, 17):
                    base = run(seed, sk, 1, econ)
                    home = run(seed, sk, arch, econ)
                    bad += [f"stub {sk} arch {arch} econ {econ} seed {seed}: {m}"
                            for m in slant_problems(base.places, home.places, home_xy)]
    assert not bad, "\n".join(bad[:8])


def test_no_home_base_archetypes_agree():
    """SLICE-U3, step 8. R-177-06: archetypes 1, 6 and 8 (both bases FORWARD) give the same richness for the same
    seed and economy: there is no slant to apply."""
    for sk in (STUB_FLAT, STUB_ROLL):
        for seed in range(1, 17):
            runs = [run(seed, sk, a, 0.2) for a in NO_HOME_ARCHETYPES]
            sites = [[(p.x, p.y, p.rich) for p in of_kind(r.places, K_RESOURCE)] for r in runs]
            assert sites[0] == sites[1] == sites[2], (sk, seed)


def test_resource_towns_do_not_depend_on_the_archetype():
    """SLICE-U3, steps 4 and 8. R-191-04: the resource towns and sites depend on the terrain and the bases, not on
    the archetype (only the richness slant differs)."""
    for sk in (STUB_FLAT, STUB_ROLL, STUB_LAKE):
        for seed in range(1, 9):
            ref = None
            for arch in range(10):
                r = run(seed, sk, arch, 0.5)
                got = (sorted((p.x, p.y) for p in of_kind(r.places, K_RESOURCE)),
                       sorted((p.x, p.y) for p in of_kind(r.places, K_NEUTRAL)[:2]))
                ref = ref or got
                assert got == ref, (sk, seed, arch)


def test_richness_bounds_and_economy_mean():
    """SLICE-U3, step 8. R-177-06: richness in [0, 100], 0 for every other kind, and 'a region with a big economy
    gives a mission big resources': the mean richness at economy 1.0 is greater than at 0.2 over 20 seeds."""
    means = {}
    for econ in (0.2, 1.0):
        vals = []
        for seed in range(1, 21):
            r = run(seed, STUB_FLAT, 1, econ)
            for p in r.places:
                assert 0 <= p.rich <= 100
                if p.kind != K_RESOURCE:
                    assert p.rich == 0
            vals += [p.rich for p in of_kind(r.places, K_RESOURCE)]
        assert vals
        means[econ] = sum(vals) / len(vals)
    print(f"RICHNESS mean at economy 0.2: {means[0.2]:.2f}, at 1.0: {means[1.0]:.2f}")
    assert means[1.0] > means[0.2]


# ---- SLICE-U4: other towns, spacing, maximum, satellites, order, cap, budget, counts, sweeps ---------------
def test_same_inputs_twice_give_byte_equal_results():
    """SLICE-U4. Determinism is a contract (CLAUDE.md): same inputs twice give a byte-equal used prefix and n, and a
    buffer pre-filled with 0xA5 gives the same bytes (the result is zeroed first); seeds 1 to 64, three land stubs."""
    bad = []
    for sk in LAND_STUBS:
        for seed in SEEDS64:
            a = _as_run(*call_engine(seed, CANVAS16, CANVAS16, 0, 0.5, geo_for(sk, CANVAS16), sk))
            b = _as_run(*call_engine(seed, CANVAS16, CANVAS16, 0, 0.5, geo_for(sk, CANVAS16), sk))
            d = _as_run(*call_engine(seed, CANVAS16, CANVAS16, 0, 0.5, geo_for(sk, CANVAS16), sk, dirty=True))
            if not (used_prefix_equal(a.raw, b.raw) and used_prefix_equal(a.raw, d.raw) and a.raw == b.raw == d.raw):
                bad.append((sk, seed))
    assert not bad, bad[:8]


def test_two_seeds_differ_on_the_flat_stub():
    """SLICE-U4. R-191-01 ('each is found by rule on the terrain'; seeded): on the flat stub only the noise differs,
    so two seeds must give different place lists."""
    assert run(1, STUB_FLAT).raw != run(2, STUB_FLAT).raw


def test_no_two_settlements_or_bases_within_4000():
    """SLICE-U4. R-191-06 / R-191-03 (spacing is Q-191-05; DRAFT-places-spacing 4,000 wu): no two settlement or base
    places (kinds 9, 10, 11) are within 4,000 wu of each other; satellites (resource and expansion sites) exempt;
    seeds 1 to 64, three land stubs, a HOME base on each side in turn."""
    sweep(lambda r, sk, g: [f"places {i} and {j} too close" for (i, j) in spacing_violations(r.places)])


def test_non_resource_towns_keep_4000_from_the_objective():
    """SLICE-U4, step 5. DRAFT-places-spacing: towns chosen after the resource-hosting ones are at least 4,000 wu from
    the objective (step 5: 'from every base, the objective and every town chosen')."""
    def check(r, sk, g):
        return [f"town {xy(t)} is {dist(xy(t), g.obj):.0f} wu from the objective"
                for t in of_kind(r.places, K_NEUTRAL)[2:] if dist(xy(t), g.obj) < SPACING]
    sweep(check)


def test_at_most_six_settlements_and_home_bases():
    """SLICE-U4, step 5. DRAFT-towns-max 6: settlements and HOME bases together are at most 6, seeds 1 to 64."""
    sweep(lambda r, sk, g: ["more than 6 settlements and HOME bases"] if max_town_violation(r.places) else [])


def test_no_place_on_water_or_unwalkable_ground():
    """SLICE-U4. R-193-01 (water, slope shape the towns): no place is on water or unwalkable ground on the three land
    stubs (the lake-and-cliff stub has a lake and an unwalkable band), satellites included; the objective and base
    inputs are on dry walkable ground (test_inputs_are_on_dry_walkable_ground); seeds 1 to 64."""
    sweep(lambda r, sk, g: [f"place {i} {xy(r.places[i])} kind {r.places[i].kind} on water or unwalkable ground"
                            for i in no_water_violations(r.places, stub(sk))])


def test_other_towns_match_the_reference_score():
    """SLICE-U4, steps 3 and 5. R-191-06 ('they stand where the layout engine's economic locations are, never at
    hard-coded positions'): after the resource-hosting towns, repeatedly the valid candidate of greatest score that is
    at least 4,000 wu from every base, the objective and every town chosen, while s > 0.35 (DRAFT-places-floor), the
    settlements and HOME bases together fewer than 6 (DRAFT-towns-max). The Python reference model of the spec, seeds
    1 to 8, three land stubs and the 24,000 wu flat canvas, archetype 0 (a HOME base) and 1 (none)."""
    bad = []
    for sk in LAND_STUBS:
        for arch in (0, 1):
            for seed in range(1, 9):
                bad += [f"stub {sk} arch {arch} seed {seed}: {m}"
                        for m in model_matches(seed, sk, CANVAS16, arch, run(seed, sk, arch))]
    for seed in (1, 2):
        bad += [f"24k seed {seed}: {m}" for m in model_matches(seed, STUB_FLAT, CANVAS24, 0,
                                                              run(seed, STUB_FLAT, 0, 0.5, CANVAS24))]
    assert not bad, "\n".join(bad[:6])


def test_other_town_ages_follow_the_age_noise():
    """SLICE-U4, step 6. R-191-06 ('each to a seeded age, so that some are small and some big'): every
    NEUTRAL_SETTLEMENT age_steps = 10 + (30*u_q16 + 32768) / 65536 with u_q16 from om_tn_fbm2(seed + 450) at its
    position, in [10, 40]; HOME 40, FORWARD 0, every other kind 0."""
    bad = []
    for sk in LAND_STUBS:
        for seed in SEEDS64:
            for t in of_kind(run(seed, sk, 0).places, K_NEUTRAL):
                if t.age != expected_age(seed, t.x, t.y) or not (TOWN_AGE_MIN <= t.age <= TOWN_AGE_MAX):
                    bad.append((sk, seed, xy(t), t.age))
    assert not bad, bad[:8]


def _expected_steps(sk, canvas, seed, t, start):
    """The satellite step the spec's rule gives, under both readings of the sign of S and N (y down or up)."""
    st = stub(sk)
    picks = []
    for order in (((1, 0), (0, 1), (-1, 0), (0, -1)), ((1, 0), (0, -1), (-1, 0), (0, 1))):
        for k in range(4):
            dx, dy = order[(start + k) % 4]
            x, y = t.x + dx * SAT_OFFSET, t.y + dy * SAT_OFFSET
            if 0.0 <= x < canvas and 0.0 <= y < canvas and st.height(x, y) >= 0.0 and st.walkable(x, y):
                picks.append((x, y))
                break
        else:
            picks.append(None)
    return picks


def test_satellites_stand_300_from_a_town_on_the_first_valid_axis_step():
    """SLICE-U4, step 7. R-191-05 ('expansion sites ... settlements that can be grown into further bases'): each
    EXPANSION_SITE is 300 wu (DRAFT-satellite-offset) from a NEUTRAL_SETTLEMENT on the first of the four axis steps
    (E, S, W, N, starting at index (u_q16 >> 14) & 3 of the town's age noise) that lands inside the canvas on walkable,
    non-water ground. E and W are exact; the sign of S and N is accepted either way (the spec does not fix y's
    direction). A town with no valid step gets none."""
    bad = []
    for sk in LAND_STUBS:
        for seed in SEEDS64:
            r = run(seed, sk, 0)
            sites = of_kind(r.places, K_EXPANSION)
            hosts = [t for t in of_kind(r.places, K_NEUTRAL)
                     if not any(abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL for s in of_kind(r.places, K_RESOURCE))]
            got = {}
            for s in sites:
                near = [t for t in hosts if abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL]
                if len(near) != 1:
                    bad.append((sk, seed, "site with no unique host", xy(s)))
                    continue
                got[xy(near[0])] = xy(s)
            for t in hosts:
                start = (age_u_q16(seed, t.x, t.y) >> 14) & 3
                picks = _expected_steps(sk, CANVAS16, seed, t, start)
                have = got.get(xy(t))
                if have not in picks:          # picks: one per reading of S and N, None when no step is valid
                    bad.append((sk, seed, "satellite not on the first valid axis step", xy(t), have, picks))
    assert not bad, bad[:6]


def test_expansion_sites_only_for_towns_without_a_resource_site():
    """SLICE-U4, step 7 and gap 5. R-191-05: every NEUTRAL_SETTLEMENT that hosts no resource site gets an
    EXPANSION_SITE and a HOME base gets none; on the flat stub (every town has a valid step) the count of expansion
    sites equals the count of towns that host no resource site."""
    for arch in SWEEP_ARCHS:
        for seed in SEEDS64:
            r = run(seed, STUB_FLAT, arch)
            towns = of_kind(r.places, K_NEUTRAL)
            hosting = [t for t in towns if any(abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL
                                               for s in of_kind(r.places, K_RESOURCE))]
            assert len(of_kind(r.places, K_EXPANSION)) == len(towns) - len(hosting), (arch, seed)


def test_order_of_places():
    """SLICE-U4, step 9. R-191-02: the order is the objective, the player base, the enemy base, then towns in the order
    chosen (resource-hosting towns first), then satellites in the order of their towns. Asserted for both readings of
    where a resource site sits: all expansion sites follow all neutral settlements, in the order of their towns."""
    bad = []
    for sk in LAND_STUBS:
        for arch in SWEEP_ARCHS:
            for seed in SEEDS64:
                pl = run(seed, sk, arch).places
                kinds = [p.kind for p in pl]
                if kinds[:3] != [K_OBJECTIVE, *BASE_TABLE[arch]]:
                    bad.append((sk, arch, seed, "first three"))
                    continue
                if any(k not in (K_NEUTRAL, K_RESOURCE, K_EXPANSION) for k in kinds[3:]):
                    bad.append((sk, arch, seed, "kind after the bases"))
                last_town = max((i for i, k in enumerate(kinds) if k == K_NEUTRAL), default=2)
                first_exp = min((i for i, k in enumerate(kinds) if k == K_EXPANSION), default=len(kinds))
                if first_exp < last_town:
                    bad.append((sk, arch, seed, "an expansion site before the last town"))
                towns = of_kind(pl, K_NEUTRAL)
                idx = []
                for s in of_kind(pl, K_EXPANSION):
                    idx.append(next((i for i, t in enumerate(towns) if abs(dist(xy(s), xy(t)) - SAT_OFFSET) <= SAT_TOL), -1))
                if idx != sorted(idx):
                    bad.append((sk, arch, seed, "expansion sites not in town order"))
    assert not bad, bad[:6]


def test_ages_sides_and_richness_by_kind():
    """SLICE-U4. R-177-02 / R-191-06 / R-177-06: ages HOME 40, FORWARD 0, neutral in [10, 40], every other kind 0;
    side -1 for everything but the two bases; richness 0 for every kind but RESOURCE_SITE, seeds 1 to 64."""
    def check(r, sk, g):
        out = []
        for i, p in enumerate(r.places):
            if p.kind == K_HOME and p.age != HOME_AGE:
                out.append(f"place {i}: HOME age {p.age}")
            if p.kind == K_NEUTRAL and not (TOWN_AGE_MIN <= p.age <= TOWN_AGE_MAX):
                out.append(f"place {i}: neutral age {p.age}")
            if p.kind not in (K_HOME, K_NEUTRAL) and p.age != 0:
                out.append(f"place {i}: kind {p.kind} age {p.age}")
            if i not in (1, 2) and p.side != -1:
                out.append(f"place {i}: side {p.side}")
            if p.kind != K_RESOURCE and p.rich != 0:
                out.append(f"place {i}: kind {p.kind} richness {p.rich}")
            if not (0 <= p.rich <= 100):
                out.append(f"place {i}: richness {p.rich}")
        return out
    sweep(check)


def test_place_count_is_at_most_64():
    """SLICE-U4. OM_PLACE_CAP 64: n <= 64 on every run of the sweeps, and the canvas 24,000 wu run too."""
    sweep(lambda r, sk, g: [f"n = {r.n}"] if not (1 <= r.n <= PLACE_CAP) else [])
    assert 1 <= run(1, STUB_FLAT, 0, 0.5, CANVAS24).n <= PLACE_CAP


def test_runtime_under_the_budget_on_the_24000_flat_canvas():
    """SLICE-U4, gap 7. DRAFT-places-budget 20 ms on the 24,000 wu flat stub (the stub is height 50 everywhere, so
    it does not depend on the canvas): one measured call is asserted, five timings are printed. A flake is a lone red
    that passes alone."""
    geo = geo_for(STUB_FLAT, CANVAS24)
    times = []
    for k in range(5):          # only the library call is timed (the libraries and the stub are loaded by then)
        ret, out = call_engine(1 + k, CANVAS24, CANVAS24, 0, 0.5, geo, STUB_FLAT, timer=times)
        assert ret >= 1
    print("BUDGET timings (ms) of five calls, 24,000 wu flat stub: " + ", ".join(f"{t * 1000:.2f}" for t in times))
    assert times[0] < BUDGET_S, f"first call {times[0] * 1000:.2f} ms >= {BUDGET_S * 1000:.0f} ms"


def test_counts_of_neutral_settlements_are_printed():
    """SLICE-U4. Q-191-05 (counts and spacing are open): the count of NEUTRAL_SETTLEMENTs is printed on the flat stub at
    16,000 and 24,000 wu and on the rolling stub at 16,000 wu, seeds 1 to 64; on the rolling 16,000 wu fixture it is
    asserted at least 2 (DRAFT-fixture-towns-min 2) on every seed."""
    for label, sk, canvas in (("flat 16,000", STUB_FLAT, CANVAS16), ("flat 24,000", STUB_FLAT, CANVAS24),
                              ("rolling 16,000", STUB_ROLL, CANVAS16)):
        counts = [len(of_kind(run(s, sk, 0, 0.5, canvas).places, K_NEUTRAL)) for s in SEEDS64]
        print(f"COUNT neutral settlements, {label}: seed 1 = {counts[0]}, min {min(counts)}, "
              f"mean {sum(counts) / len(counts):.2f}, max {max(counts)}")
        if sk == STUB_ROLL:
            assert min(counts) >= 2, counts


def test_the_lying_adapter_is_flagged_on_an_engine_result():
    """SLICE-U4, positive control with the engine. R-193-01: the engine result on the flat stub, judged against the
    all-water stub's true heights (a lying adapter: every place is on true water), is flagged by the no-water
    detector for every place."""
    pl = run(1, STUB_FLAT, 0).places
    assert len(no_water_violations(pl, stub(STUB_WATER))) == len(pl)
    assert no_water_violations(pl, stub(STUB_FLAT)) == []
