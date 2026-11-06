# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-1
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-2
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-3
"""S-247 wave 1, leaf 1: the layout kit engine, driven through the parent-owned probe tests/csim/layout_kit_probe.c.

R-112-01 R-112-02 R-112-03 R-112-04 R-112-05 R-112-07 R-112-08 R-113-01 R-113-02 R-113-03 R-113-04.
Red until leaf 1 replaces the sentinel bodies of csrc/layout_kit.c (they return -1 / NULL / 0). Every expectation is
computed here from the spec's numbers and from the dumped lanes (an independent Dijkstra), never from the engine's own
check bits alone. Dumps print doubles as integer hundredths (the probe's rule), so geometry tolerances are 0.02 wu.
Budget: at most 40 assertions in this file and test_layout_kit_header.py together (counted by `assert` statements;
the `assert`s of the shared helpers count too).
"""
import heapq
import math
import pathlib
import re
import subprocess
from functools import lru_cache

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
PROBE = REPO / "tests" / "csim" / "layout_kit_probe.c"
# Flags of tests/csim/test_VG_P_p1_layout.py:118-121 (the Makefile's determinism flags); OPT is swapped for -O0.
FLAGS = ["-std=c11", "-fPIC", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]

# ---- the spec's numbers (spec.md "Named drafts" and "Design"); every one is a named draft ----------------------------
ARCH_ASSAULT = 3
CANVAS = 24000.0            # DRAFT_CANVAS_ASSAULT
CANVAS_MIN, CANVAS_MAX = 8000.0, 64000.0
CHOKE_W_MIN, CHOKE_W_MAX = 300.0, 700.0
BYPASS_MIN, BYPASS_MAX = 1.5, 2.4
EQUAL_TOL = 0.10            # DRAFT_EQUAL_TOL
APPROACHES_MIN = 2
CANDIDATES = 5
BANDS_MIN, BANDS_MAX = 1, 3
SEEDS = range(1, 13)
SIDES = {0: "mirror", 1: "rotate", 2: "separate"}
SLACK = 1.0                 # wu: the dump quantises to 0.01 wu; path sums over a few lanes stay well under 1 wu
GEO_SLACK = 0.02            # wu: two quantised coordinates
ON_LANE = 0.05              # wu: a choke point must lie this close to its lane polyline (quantised coordinates)
FRAC_TOL = 0.006            # a choke's frac prints in hundredths of the lane, so 0.005 of rounding plus a little
SEPARATE_MIN = 10           # seeds of 12 whose side B is neither the mirror nor the rotation of side A (spec: 10 of 12)

NAMES = {
    0: ["objective", "base_home", "base_forward", "resource", "expansion"],
    1: ["route", "way_round", "climb", "hidden", "objective_route"],
    2: ["none", "coast", "canyon", "mesa", "ridge", "hill", "plateau", "basin", "bend", "ford", "pass", "gate"],
    3: ["pad", "choke", "vantage", "route", "landform"],
    4: ["keep_open", "keep_closed", "height", "room", "number"],
    5: ["none", "home_ground", "gate", "crossing", "heights", "prize", "objective_ground"],
}
K_OBJ, K_HOME, K_FWD, K_RES, K_EXP = 0, 1, 2, 3, 4
L_ROUTE, L_WAY, L_CLIMB, L_HIDDEN, L_OBJROUTE = 0, 1, 2, 3, 4
R_PAD, R_CHOKE, R_VANT, R_ROUTE, R_LAND = 0, 1, 2, 3, 4
M_OPEN, M_HEIGHT, M_ROOM, M_NUMBER = 0, 2, 3, 4
CHOKE_LANDFORMS = {NAMES[2].index(n) for n in ("ford", "pass", "gate", "canyon")}
VANTAGE_LANDFORMS = {NAMES[2].index(n) for n in ("ridge", "hill", "mesa")}
PIECE = {n: i for i, n in enumerate(NAMES[5])}

# DRAFT name -> value (spec.md "Named drafts" plus DRAFT_AXIS_STEPS of "Determinism")
NAMED_DRAFTS = {
    "DRAFT_CANVAS_MIN": 8000, "DRAFT_CANVAS_MAX": 64000, "DRAFT_CANVAS_ASSAULT": 24000,
    "DRAFT_CHOKE_W_MIN": 300, "DRAFT_CHOKE_W_MAX": 700, "DRAFT_BYPASS_MIN": 1.5, "DRAFT_BYPASS_MAX": 2.4,
    "DRAFT_ASSAULT_CROSSINGS": 1, "DRAFT_ASSAULT_HEIGHTS": 1, "DRAFT_ASSAULT_PRIZES": 1,
    "DRAFT_VANTAGE_BANDS_MIN": 1, "DRAFT_VANTAGE_BANDS_MAX": 3, "DRAFT_MEANDER_MIN": 1.0, "DRAFT_MEANDER_MAX": 1.6,
    "DRAFT_MEANDER_STEPS": 12, "DRAFT_EQUAL_TOL": 0.10, "DRAFT_CANDIDATES": 5, "DRAFT_APPROACHES_MIN": 2,
    "DRAFT_JSON_QUANT": 0.01, "DRAFT_PX_WU": 20, "DRAFT_AXIS_STEPS": 24,
}


# ---- building and running the probe ----------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def probes(tmp_path_factory):
    """The probe built once at -O2 and once at -O0 against csrc/layout_kit*.c and csrc/terrain_noise.c."""
    out = {}
    for opt in ("O2", "O0"):
        exe = tmp_path_factory.mktemp("lkprobe_" + opt) / "layout_kit_probe"
        srcs = sorted(CSRC.glob("layout_kit*.c")) + [CSRC / "terrain_noise.c"]
        r = subprocess.run(["cc", *FLAGS, "-" + opt, "-I", str(CSRC), "-o", str(exe), str(PROBE),
                            *map(str, srcs), "-lm"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-3000:]
        out[opt] = exe
    return out


def _run(exe, *args):
    r = subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (args, r.returncode, r.stderr[-500:])
    return r.stdout


@lru_cache(maxsize=None)
def _gen_text(exe, seed, arch, canvas, sides):
    return _run(exe, "gen", seed, arch, canvas, sides)


def gen(probes, seed, sides, canvas=CANVAS, arch=ARCH_ASSAULT, opt="O2"):
    """A generated layout, parsed; fails loudly (not with a KeyError) when the engine did not return 0."""
    text = _gen_text(probes[opt], seed, arch, repr(float(canvas)), sides)
    assert text.startswith("rc 0\n"), f"om_lk_generate(seed={seed}, canvas={canvas}, sides={sides}) -> {text.strip()[:40]}"
    return parse(text)


REC_KEYS = ("place", "node", "lane", "choke", "vantage", "request")


def parse(text):
    """Probe text -> dict. Integer values stay raw (hundredths of a wu where the probe prints doubles)."""
    d = {"kv": {}, "fair": {}, "district": [], "text": text}
    for k in REC_KEYS:
        d[k] = []
    for line in text.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] in REC_KEYS:
            rec = {}
            for tok in t[2:]:
                a, _, b = tok.partition("=")
                if a == "pts":
                    rec[a] = [tuple(int(v) for v in p.split(",")) for p in b.split(";") if p]
                elif a == "name":
                    rec[a] = b
                else:
                    rec[a] = int(b)
            d[t[0]].append(rec)
        elif t[0] == "fair":
            d["fair"] = {a: int(b) for a, _, b in (tok.partition("=") for tok in t[1:])}
        elif t[0] == "district":
            d["district"].append([int(v) for v in t[2:]])
        elif len(t) == 2:
            d["kv"][t[0]] = int(t[1])
    return d


def wu(v):
    return v / 100.0


# ---- independent geometry: the route graph rebuilt from the dumped lanes (spec "Checks": all lanes join a and b) ------
def lane_len(lane):
    p = lane["pts"]
    return sum(math.hypot(wu(p[i + 1][0] - p[i][0]), wu(p[i + 1][1] - p[i][1])) for i in range(len(p) - 1))


def dijkstra(d, src, skip_lane=None):
    dist = [math.inf] * len(d["node"])
    dist[src] = 0.0
    heap = [(0.0, src)]
    adj = {i: [] for i in range(len(d["node"]))}
    for i, ln in enumerate(d["lane"]):
        if i != skip_lane:
            adj[ln["a"]].append((ln["b"], lane_len(ln)))
            adj[ln["b"]].append((ln["a"], lane_len(ln)))
    while heap:
        du, u = heapq.heappop(heap)
        if du > dist[u]:
            continue
        for v, w in adj[u]:
            if du + w < dist[v]:
                dist[v] = du + w
                heapq.heappush(heap, (dist[v], v))
    return dist


def arc_position(lane, x, y):
    """(distance in wu from (x, y) to the lane polyline, fraction 0..1 of the polyline length at the nearest point)."""
    pts = [(wu(a), wu(b)) for a, b in lane["pts"]]
    total, acc, best = lane_len(lane), 0.0, (math.inf, 0.0)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        seg = math.hypot(dx, dy)
        t = 0.0 if seg == 0 else max(0.0, min(1.0, ((wu(x) - x0) * dx + (wu(y) - y0) * dy) / (seg * seg)))
        dist = math.hypot(wu(x) - (x0 + t * dx), wu(y) - (y0 + t * dy))
        if dist < best[0]:
            best = (dist, (acc + t * seg) / total)
        acc += seg
    return best


def places_of(d, kind):
    return [p for p in d["place"] if p["kind"] == kind]


def base_nodes(d):
    return places_of(d, K_FWD)[0]["node"], places_of(d, K_HOME)[0]["node"]   # side A, side B


ALL36 = [(s, m) for m in SIDES for s in SEEDS]
IDS36 = [f"s{s}-{SIDES[m]}" for s, m in ALL36]


# ---- return codes -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("arch,canvas,sides,want", [
    (3, 24000, 0, 0), (3, 24000, 1, 0), (3, 24000, 2, 0),
    (-1, 24000, 0, -2), (0, 24000, 0, -2), (2, 24000, 0, -2), (4, 24000, 0, -2), (9, 24000, 0, -2), (10, 24000, 0, -2),
    (3, 7999, 0, -3), (3, 8000, 0, 0), (3, 64000, 0, 0), (3, 64001, 0, -3), (3, 0, 0, -3), (3, -24000, 0, -3),
    (3, 24000, -1, -3), (3, 24000, 3, -3),
    # combinations: the header's order is NULL out, then archetype, then canvas and sides mode
    (9, 0, 0, -2), (9, 24000, 3, -2), (-1, 7999, 9, -2), (10, 64001, -1, -2), (3, 0, 3, -3), (3, 64001, -1, -3),
])
def test_S_247_return_codes_and_range_boundaries(probes, arch, canvas, sides, want):
    """S-247 R-112-01: -2 for an archetype outside 0..9 or not built (only Assault), -3 for a canvas outside
    8,000..64,000 (both ends inclusive) or a sides mode outside 0..2 (header contract, spec 'Design' step 1); when
    two faults meet the archetype's -2 wins over the canvas's and sides mode's -3 (overlord ruling Q2)."""
    d = parse(_run(probes["O2"], "gen", 1, arch, float(canvas), sides))
    assert d["kv"]["rc"] == want


def test_S_247_null_out_returns_minus_one(probes):
    """S-247 R-112-01: a NULL out is -1 (header contract), where the same call with an out struct returns 0 (the
    sentinel returns -1 for everything, so the first value keeps this test red until the engine is built); -1 also
    wins over a bad archetype, canvas and sides mode together (overlord ruling Q2: NULL out is checked first)."""
    rc = lambda *a: parse(_run(probes["O2"], "null", *a))["kv"]["rc"]
    assert (gen(probes, 1, 2)["kv"]["rc"], rc(), rc(9, 0.0, 3), rc(3, 0.0, 0)) == (0, -1, -1, -1)


# ---- the layout is made, whole, every seed and mode ------------------------------------------------------------------
@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_all_six_checks_pass(probes, seed, sides):
    """S-247 R-112-05: seeds 1..12 x three sides modes: checks == 0x3F, each of the six bits set (the kit needs no luck)."""
    d = gen(probes, seed, sides)
    bits = [d["kv"][f"check_{n}"] for n in ("connected", "fairness", "bypass", "approaches", "chokes", "bounds")]
    assert (d["kv"]["rc"], d["kv"]["checks"], bits) == (0, 0x3F, [1] * 6)


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_places_and_counts_are_the_assault_budget(probes, seed, sides):
    """S-247 R-113-01 R-113-02 R-112-07: exactly one objective, one base per side (forward camp = side A, home =
    side B), two resources, two expansions (one per side), one crossing, one height, >= 2 approach
    lanes and the objective still reachable from side A's base with any one of them removed."""
    d = gen(probes, seed, sides)
    k = d["kv"]
    got = {"objective": k["count_objective"], "home": k["count_base_home"], "forward": k["count_base_forward"],
           "resource": k["count_resource"], "expansion": k["count_expansion"], "chokes": k["count_chokes"],
           "vantages": k["count_vantages"]}
    obj_node = places_of(d, K_OBJ)[0]["node"]
    approaches = sum(1 for ln in d["lane"] if obj_node in (ln["a"], ln["b"]))
    sides_of = (places_of(d, K_FWD)[0]["side"], places_of(d, K_HOME)[0]["side"], sorted(p["side"] for p in places_of(d, K_EXP)))
    # spec check 4: removing any one lane of the objective leaves it reachable from side A's base (own Dijkstra)
    na = base_nodes(d)[0]
    cut_ok = all(math.isfinite(dijkstra(d, na, skip_lane=i)[obj_node]) for i, ln in enumerate(d["lane"]) if obj_node in (ln["a"], ln["b"]))
    assert (got, sides_of, approaches >= APPROACHES_MIN, cut_ok) == (
        {"objective": 1, "home": 1, "forward": 1, "resource": 2, "expansion": 2, "chokes": 1, "vantages": 1},
        (0, 1, [0, 1]), True, True)


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_fairness_is_true_on_the_dumped_lanes(probes, seed, sides):
    """S-247 R-112-05 R-112-07: a Dijkstra I wrote here over the dumped lanes: both resources are equal-distance from
    the two bases within DRAFT_EQUAL_TOL, every node is reachable from side A's base (check 1), the objective is nearer
    side B's base than side A's (Q-191-11, the slant), and
    the engine's own reported fairness numbers agree with mine to 1 wu."""
    d = gen(probes, seed, sides)
    na, nb = base_nodes(d)
    da, db = dijkstra(d, na), dijkstra(d, nb)
    res = [p["node"] for p in places_of(d, K_RES)]
    obj = places_of(d, K_OBJ)[0]["node"]
    unfair = [(da[r], db[r]) for r in res if abs(da[r] - db[r]) > EQUAL_TOL * max(da[r], db[r]) + SLACK]
    assert unfair == [] and all(math.isfinite(x) for x in da) and db[obj] < da[obj]   # check 1 (connected), own oracle
    f = d["fair"]
    reported = [f["dist_a_objective"], f["dist_b_objective"], f["dist_a_res0"], f["dist_a_res1"],
                f["dist_b_res0"], f["dist_b_res1"]]
    mine = [da[obj], db[obj], da[res[0]], da[res[1]], db[res[0]], db[res[1]]]
    assert all(abs(wu(a) - b) <= SLACK for a, b in zip(reported, mine))


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_chokes_have_width_axis_and_a_way_round(probes, seed, sides):
    """S-247 R-113-03 R-112-05 R-112-07: each choke is 300..700 wu wide with a length, a wall span, an axis in
    15-degree steps 0..11 and a position 0..1 on a spine lane (route or objective_route), its point lying on that
    lane at that fraction of its length; its lane has a way_round lane between the same two nodes whose length is
    1.5..2.4 times the lane's, and no path avoiding the lane is shorter than 1.5 times it."""
    d = gen(probes, seed, sides)
    bad, short = [], []
    for ck in d["choke"]:
        w = wu(ck["width"])
        ok = (CHOKE_W_MIN <= w <= CHOKE_W_MAX and ck["length"] > 0 and ck["wall_span"] > 0 and 0 <= ck["axis_k"] <= 11
              and 0 <= ck["frac"] <= 100 and 0 <= ck["lane"] < len(d["lane"]))
        if ok:     # on the spine, at frac of its lane (spec Design 3 and header)
            lane = d["lane"][ck["lane"]]
            dist, at = arc_position(lane, ck["x"], ck["y"])
            ok = lane["kind"] in (L_ROUTE, L_OBJROUTE) and dist <= ON_LANE and abs(at - ck["frac"] / 100.0) <= FRAC_TOL
        if not ok:
            bad.append(ck)
            continue
        lane = d["lane"][ck["lane"]]
        through = lane_len(lane)
        rounds = [lane_len(o) for i, o in enumerate(d["lane"]) if o["kind"] == L_WAY and i != ck["lane"]
                  and {o["a"], o["b"]} == {lane["a"], lane["b"]}]
        avoid = dijkstra(d, lane["a"], skip_lane=ck["lane"])[lane["b"]]
        if not rounds or any(not (BYPASS_MIN - 0.002 <= r / through <= BYPASS_MAX + 0.002) for r in rounds) \
                or avoid < BYPASS_MIN * through - SLACK:
            short.append((ck["lane"], through, rounds, avoid))
    assert bad == [] and short == []


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_each_vantage_has_two_climbs_and_one_overlook(probes, seed, sides):
    """S-247 R-113-04: a vantage has 1..3 height bands, overlooks one spine lane (route or objective_route) and is
    reached by two distinct climb lanes, each ending within the vantage's radius of it."""
    d = gen(probes, seed, sides)
    n = len(d["lane"])
    bad = []
    for v in d["vantage"]:
        c0, c1, ov = v["climb0"], v["climb1"], v["overlooks"]
        ok = (BANDS_MIN <= v["height_bands"] <= BANDS_MAX and c0 != c1 and 0 <= c0 < n and 0 <= c1 < n
              and 0 <= ov < n and d["lane"][c0]["kind"] == L_CLIMB and d["lane"][c1]["kind"] == L_CLIMB
              and d["lane"][ov]["kind"] in (L_ROUTE, L_OBJROUTE)
              and all(any(math.hypot(wu(px - v["x"]), wu(py - v["y"])) <= wu(v["radius"]) + GEO_SLACK
                          for px, py in (d["lane"][c]["pts"][0], d["lane"][c]["pts"][-1])) for c in (c0, c1)))
        if not ok:
            bad.append(v)
    assert bad == []


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_pieces_and_landforms_are_named(probes, seed, sides):
    """S-247 R-112-03 R-112-04: objective ground / prize / crossing / heights pieces on their places; a crossing's
    landform is ford, pass, gate or canyon and a heights' is ridge, hill or mesa."""
    d = gen(probes, seed, sides)
    pieces = (places_of(d, K_OBJ)[0]["piece"], sorted(p["piece"] for p in places_of(d, K_RES)),
              [c["piece"] for c in d["choke"]], [v["piece"] for v in d["vantage"]])
    assert pieces == (PIECE["objective_ground"], [PIECE["prize"]] * 2, [PIECE["crossing"]], [PIECE["heights"]]) \
        and all(c["landform"] in CHOKE_LANDFORMS for c in d["choke"]) \
        and all(v["landform"] in VANTAGE_LANDFORMS for v in d["vantage"])


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_the_request_list_covers_the_layout(probes, seed, sides):
    """S-247 R-112-04 (the B3 seam): a room pad request per place named base_a, base_b,
    objective, site_0.. (the sites are the resources and expansions); a keep_open
    choke request per choke with its numbers; a height vantage request per vantage with side +1 when nearer side A's
    base by straight line, -1 nearer B's, 0 equal; a number route request per route/way_round/objective_route lane;
    a keep_open landform request for every landform a choke or vantage carries."""
    d = gen(probes, seed, sides)
    rq = d["request"]
    by = {k: [r for r in rq if r["kind"] == k] for k in (R_PAD, R_CHOKE, R_VANT, R_ROUTE, R_LAND)}
    a, b = places_of(d, K_FWD)[0], places_of(d, K_HOME)[0]
    names = {r["name"]: (r["x"], r["y"]) for r in by[R_PAD]}
    xy = lambda ps: sorted((p["x"], p["y"]) for p in ps)
    assert sorted((r["x"], r["y"], r["r"]) for r in by[R_PAD]) == sorted((p["x"], p["y"], p["pad_r"]) for p in d["place"]) \
        and all(r["mode"] == M_ROOM for r in by[R_PAD]) \
        and sorted(names) == ["base_a", "base_b", "objective", "site_0", "site_1", "site_2", "site_3"] \
        and (names["base_a"], names["base_b"], names["objective"]) == ((a["x"], a["y"]), (b["x"], b["y"]), xy(places_of(d, K_OBJ))[0]) \
        and sorted(v for k, v in names.items() if k.startswith("site_")) == xy(places_of(d, K_RES) + places_of(d, K_EXP))
    assert sorted((r["x"], r["y"], r["w"], r["len"], r["span"], r["frac"], r["axis_k"], r["mode"]) for r in by[R_CHOKE]) == \
        sorted((c["x"], c["y"], c["width"], c["length"], c["wall_span"], c["frac"], c["axis_k"], M_OPEN) for c in d["choke"])

    def side_of(v):
        da = (v["x"] - a["x"]) ** 2 + (v["y"] - a["y"]) ** 2
        db = (v["x"] - b["x"]) ** 2 + (v["y"] - b["y"]) ** 2
        return 1 if da < db else (-1 if db < da else 0)
    assert sorted((r["x"], r["y"], r["r"], r["height_bands"], r["side"], r["mode"]) for r in by[R_VANT]) == \
        sorted((v["x"], v["y"], v["radius"], v["height_bands"] * 100, side_of(v), M_HEIGHT) for v in d["vantage"])
    lanes = [ln for ln in d["lane"] if ln["kind"] in (L_ROUTE, L_WAY, L_OBJROUTE)]
    assert d["kv"]["count_lanes"] == len(d["lane"]) and len(by[R_ROUTE]) == len(lanes) == d["kv"]["route_count"] \
        and sorted((r["r"], r["mode"]) for r in by[R_ROUTE]) == sorted((ln["width"], M_NUMBER) for ln in lanes)
    named = sorted([c["landform"] for c in d["choke"]] + [v["landform"] for v in d["vantage"]])
    got = sorted(r["landform"] for r in by[R_LAND])
    assert all(r["mode"] == M_OPEN for r in by[R_LAND]) and all(g in got for g in named)


# ---- determinism ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_two_runs_give_identical_dumps(probes, seed, sides):
    """S-247 R-112-01: the same seed, kind, canvas and sides mode give a byte-identical layout on a second run."""
    first = gen(probes, seed, sides)["text"]            # fails unless rc 0: two identical failures are not determinism
    assert _run(probes["O2"], "gen", seed, ARCH_ASSAULT, repr(CANVAS), sides) == first


@pytest.mark.parametrize("sides", sorted(SIDES), ids=list(SIDES.values()))
def test_S_247_a_second_call_in_one_process_starts_from_nothing(probes, sides):
    """S-247 R-112-01: the header's "fills *out (zeroed first)" and no state kept between calls: in one process, one
    struct filled with 0xA5, seed 5 then seed 9 then seed 5 again print three dumps; the third equals the first, and
    each equals the single-run dump of its seed; every unused array slot is zero after each call (checked field by field)."""
    out = _run(probes["O2"], "chain", 5, 9, ARCH_ASSAULT, repr(CANVAS), sides)
    runs = re.split(r"^run \d\n", out, flags=re.M)[1:]
    tail = runs[-1].splitlines()[-1] if runs else ""
    runs = [r.replace(tail + "\n", "") for r in runs]
    assert (runs, tail) == ([gen(probes, 5, sides)["text"], gen(probes, 9, sides)["text"], gen(probes, 5, sides)["text"]],
                            "tail_clean 1 1 1")


@pytest.mark.parametrize("seed,sides", ALL36, ids=IDS36)
def test_S_247_O0_and_O2_builds_agree(probes, seed, sides):
    """S-247 R-112-01: the -O0 and -O2 probe binaries print identical dumps over the 36 layouts."""
    assert gen(probes, seed, sides, opt="O0")["text"] == gen(probes, seed, sides, opt="O2")["text"]


@pytest.mark.parametrize("sides", sorted(SIDES), ids=list(SIDES.values()))
def test_S_247_different_seeds_make_different_layouts(probes, sides):
    """S-247 R-112-01: seeds 1..12 give at least 10 distinct layouts (the dump minus its seed line)."""
    dumps = {"\n".join(ln for ln in gen(probes, s, sides)["text"].splitlines() if not ln.startswith("seed "))
             for s in SEEDS}
    assert len(dumps) >= 10


# ---- canvas and sides modes -------------------------------------------------------------------------------------------
# the two extremes stress the fixed 300..700 wu choke widths most, so they get every seed; the default one seed
CANVAS_CASES = [(CANVAS, 3)] + [(c, s) for c in (CANVAS_MIN, CANVAS_MAX) for s in SEEDS]


@pytest.mark.parametrize("canvas,seed", CANVAS_CASES, ids=[f"c{int(c)}-s{s}" for c, s in CANVAS_CASES])
@pytest.mark.parametrize("sides", sorted(SIDES), ids=list(SIDES.values()))
def test_S_247_stays_on_the_canvas_with_chokes_300_to_700(probes, canvas, seed, sides):
    """S-247 R-112-05 R-112-07: at the smallest and largest canvas (seeds 1..12) and the default one (seed 3) every
    place pad, node, lane point, choke and vantage circle lies on the canvas (checked here on the dump), choke widths
    stay 300..700 wu; all six checks pass at the default canvas (criterion 1), at the two extremes the chokes and
    bounds checks pass (the spec asks no more of them)."""
    d = gen(probes, seed, sides, canvas=canvas)
    need = 0x3F if canvas == CANVAS else 0x30           # OM_LK_CHECKS_ALL, or OM_LK_CHECK_CHOKES | OM_LK_CHECK_BOUNDS
    assert d["kv"]["rc"] == 0 and d["kv"]["checks"] & need == need and wu(d["kv"]["canvas"]) == canvas
    inside = lambda x, y, r=0.0: r - GEO_SLACK <= x <= canvas - r + GEO_SLACK and r - GEO_SLACK <= y <= canvas - r + GEO_SLACK
    pts = [(wu(x), wu(y)) for ln in d["lane"] for x, y in ln["pts"]]
    out = ([p for p in d["place"] if not inside(wu(p["x"]), wu(p["y"]), wu(p["pad_r"]))]
           + [n for n in d["node"] if not inside(wu(n["x"]), wu(n["y"]))]
           + [q for q in pts if not inside(*q)]
           + [c for c in d["choke"] if not inside(wu(c["x"]), wu(c["y"]))]
           + [v for v in d["vantage"] if not inside(wu(v["x"]), wu(v["y"]), wu(v["radius"]))]
           + [c for c in d["choke"] if not CHOKE_W_MIN - GEO_SLACK <= wu(c["width"]) <= CHOKE_W_MAX + GEO_SLACK])
    assert out == []


def test_S_247_the_dump_echoes_its_inputs_and_fills_every_district_role(probes):
    """S-247 R-112-01 R-112-02: seed, archetype, sides mode and canvas are echoed; the kept candidate is one of the
    DRAFT_CANDIDATES; in all 36 layouts the 8 x 8 district grid holds all six roles (home A/B, near A/B, contested,
    objective) and the grid is not the same for every seed."""
    k = gen(probes, 7, 1, canvas=30000)["kv"]
    grids, short = set(), []
    for seed, m in ALL36:
        dd = gen(probes, seed, m)
        roles = {v for row in dd["district"] for v in row}
        grids.add(str(dd["district"]))
        if not ({1, 2, 3, 4, 5, 6} <= roles and len(dd["district"]) == 8 and all(len(r) == 8 for r in dd["district"])):
            short.append((seed, m))
    assert (k["seed"], k["archetype"], k["sides_mode"], wu(k["canvas"])) == (7, ARCH_ASSAULT, 1, 30000.0) \
        and 0 <= k["candidate"] < CANDIDATES and short == [] and len(grids) > 1


def _pair(d):
    """Expansion sites as (side A point, side B point) in wu."""
    e = {p["side"]: (wu(p["x"]), wu(p["y"])) for p in places_of(d, K_EXP)}
    return e[0], e[1]


@pytest.mark.parametrize("mode", ["mirror", "rotate", "separate"])
def test_S_247_sides_modes_shape_side_b(probes, mode):
    """S-247 R-112-08: rotate puts side B's expansion at side A's turned half a turn about the centre; mirror at
    side A's reflected across the map's mid line (x = canvas/2 or y = canvas/2); the expansion pair only is asserted
    (overlord ruling Q4: the spec is silent on bases and on the prize pair, which is fair by route distance, not by
    geometry); separate is neither for at least 10 of 12 seeds (side B grown from its own stream)."""
    m = {"mirror": 0, "rotate": 1, "separate": 2}[mode]
    close = lambda p, q: abs(p[0] - q[0]) <= GEO_SLACK and abs(p[1] - q[1]) <= GEO_SLACK
    rot = lambda p: (CANVAS - p[0], CANVAS - p[1])
    mirrors = (lambda p: (CANVAS - p[0], p[1]), lambda p: (p[0], CANVAS - p[1]))
    tag = []
    for s in SEEDS:
        a, b = _pair(gen(probes, s, m))
        tag.append((close(b, rot(a)), any(close(b, f(a)) for f in mirrors)))
    holds = {"rotate": all(t[0] for t in tag), "mirror": all(t[1] for t in tag),
             "separate": sum(1 for t in tag if not (t[0] or t[1])) >= SEPARATE_MIN}
    assert holds[mode], tag


# ---- names and drafts -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("domain", [-1] + sorted(NAMES) + [6])
def test_S_247_om_lk_name_lists_the_json_strings(probes, domain):
    """S-247 R-112-04 (spec 'JSON'): om_lk_name returns the lower-case strings of the JSON section for ids in range
    and NULL for -1 and for one past the last id; a domain outside 0..5 is NULL for every id (overlord ruling Q1)."""
    lines = _run(probes["O2"], "names").splitlines()
    rows = [ln.split() for ln in lines if ln.startswith(f"name {domain} ")]
    got = {int(r[2]): r[3] for r in rows}
    names = NAMES.get(domain, [])
    # the anchor row keeps the two out-of-range domains red on the sentinel, whose NULLs are right for them
    assert got == {-1: "NULL", **dict(enumerate(names)), len(names): "NULL"} and "name 0 0 objective" in lines


def test_S_247_the_drafts_table_lists_the_named_drafts(probes):
    """S-247 R-112-01 (spec 'Named drafts'): om_lk_draft_count/name/value list at least every named draft with the
    spec's value (printed in hundredths), names unique, in the DRAFT_ namespace and in the order of the X(DRAFT_...)
    entries of LK_DRAFT_TABLE in csrc/layout_drafts.h (criterion 3: "in order"); index -1 and the count give NULL and
    0.0 (overlord ruling Q3)."""
    lines = _run(probes["O2"], "drafts").splitlines()
    count = int(lines[0].split()[1])
    rows = [ln.split() for ln in lines[1:] if ln.startswith("draft ")]
    table = {r[2]: int(r[3]) for r in rows}
    drafts_h = CSRC / "layout_drafts.h"
    order = re.findall(r"\bX\(\s*(DRAFT_\w+)\s*,", drafts_h.read_text() if drafts_h.is_file() else "")
    oob = [ln.split() for ln in lines if ln.startswith("oob ")]
    assert count == len(rows) and len(table) == len(rows) and all(n.startswith("DRAFT_") for n in table) \
        and count >= len(NAMED_DRAFTS) and [r[2] for r in rows] == order \
        and oob == [["oob", "-1", "NULL", "0"], ["oob", str(count), "NULL", "0"]]
    assert {n: table.get(n) for n in NAMED_DRAFTS} == {n: round(v * 100) for n, v in NAMED_DRAFTS.items()}
