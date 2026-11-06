"""Parent-owned helpers of the S-247 wave 2 tests (not a test file; pytest does not collect it).

Shared by test_layout_kit_cli.py, test_layout_kit_{connected,fairness,bypass,approaches,chokes,bounds}.py and
test_layout_kit_determinism.py, which import it as a sibling module (never across test files).
Spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md ("JSON", "Checks", criteria 5 to 7, "Tests" wave 2).

What is here, and why none of it is the CLI's own code:
  * build_cli / build_probe: cc with the determinism flags of tests/csim/test_VG_P_p1_layout.py:118-121. The CLI
    source defaults to csrc/tools/layout_dump.c; the environment variable LAYOUT_DUMP_SRC points the build at another
    file (the test-writer proves the tests can pass with a throwaway CLI that way).
  * py_checks: the six checks of the spec's "Checks" section written again in Python over a parsed JSON (an
    independent oracle, a Dijkstra of my own), so "the named check is false after --break" is judged by two
    implementations and not by the CLI's own `checks` object alone.
  * apply_break / edit_problems: the deterministic edit of criterion 6 written again in Python from the spec's words
    (fairness: the amended edit, one straight route lane appended from side A's base node to resource 0's node).
  * number_problems / order_problems / text_problems / name_problems: the JSON section's format rules.
  * cli_source: LAYOUT_DUMP_SRC is a test-only redirect (it is not in the spec and the umbrella does not honour it);
    unset, the build is csrc/tools/layout_dump.c.
  * probe_*: the wave 1 probe (tests/csim/layout_kit_probe.c, which calls the engine directly, no JSON) as the
    reference for "the CLI prints what the engine produced".
All JSON numbers are loaded as Decimal so the quantised text compares exactly.
"""
import copy
import heapq
import json
import math
import os
import pathlib
import re
import subprocess
from decimal import Decimal

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
PROBE_SRC = REPO / "tests" / "csim" / "layout_kit_probe.c"
# Flags of tests/csim/test_VG_P_p1_layout.py:118-121 (the Makefile's determinism flags); the opt level is added.
FLAGS = ["-std=c11", "-fPIC", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]

SIDES = ["mirror", "rotate", "separate"]
SEEDS = range(1, 13)
CHECKS = ["connected", "fairness", "bypass", "approaches", "chokes", "bounds"]
ALL36 = [(s, m) for m in SIDES for s in SEEDS]
IDS36 = [f"s{s}-{m}" for s, m in ALL36]
CANVAS = 24000                     # DRAFT_CANVAS_ASSAULT, the CLI default
CHOKE_W_MIN, CHOKE_W_MAX = 300, 700
BYPASS_MIN = 1.5                   # DRAFT_BYPASS_MIN
EQUAL_TOL = 0.10                   # DRAFT_EQUAL_TOL
APPROACHES_MIN = 2
SLACK = 1.0                        # wu: the JSON prints hundredths, sums over a few lanes stay far under this
EDGE_SLACK = 0.01                  # wu: one printed hundredth

# strings of the JSON section, per om_lk_name domain
NAMES = {
    0: ["objective", "base_home", "base_forward", "resource", "expansion"],
    1: ["route", "way_round", "climb", "hidden", "objective_route"],
    2: ["none", "coast", "canyon", "mesa", "ridge", "hill", "plateau", "basin", "bend", "ford", "pass", "gate"],
    3: ["pad", "choke", "vantage", "route", "landform"],
    4: ["keep_open", "keep_closed", "height", "room", "number"],
    5: ["none", "home_ground", "gate", "crossing", "heights", "prize", "objective_ground"],
}
SIDE_TEXT = {0: "A", 1: "B", -1: "none"}

TOP_KEYS = ["schema", "seed", "archetype", "canvas", "sides", "candidate", "drafts", "district", "places", "nodes",
            "lanes", "chokes", "vantages", "requests", "fairness", "checks", "route_count"]
ELEM_KEYS = {
    "places": ["kind", "side", "x", "y", "pad_r", "piece", "node"],
    "nodes": ["x", "y", "place"],
    "lanes": ["kind", "a", "b", "width", "pts"],
    "chokes": ["x", "y", "width", "length", "axis_k", "wall_span", "frac", "lane", "landform", "piece"],
    "vantages": ["x", "y", "radius", "height_bands", "overlooks", "climb", "landform", "piece"],
    "requests": ["kind", "mode", "piece", "name", "x", "y", "r", "w", "len", "span", "frac", "axis_k",
                 "height_bands", "side", "landform"],
}
FAIRNESS_KEYS = ["dist_a_objective", "dist_b_objective", "dist_a_res", "dist_b_res"]
ARRAY_KEYS = ["places", "nodes", "lanes", "chokes", "vantages", "requests"]


# ---- building ---------------------------------------------------------------------------------------------------------
def cli_source():
    """The CLI source to build: LAYOUT_DUMP_SRC when set, else csrc/tools/layout_dump.c."""
    env = os.environ.get("LAYOUT_DUMP_SRC")
    return pathlib.Path(env) if env else CSRC / "tools" / "layout_dump.c"


def engine_sources():
    return sorted(CSRC.glob("layout_kit*.c")) + [CSRC / "terrain_noise.c"]


def build_cli(tmp_path_factory, opt="O2"):
    """cc layout_dump.c + csrc/layout_kit*.c + csrc/terrain_noise.c into a tmpdir; the binary's path."""
    src = cli_source()
    assert src.is_file(), f"{src} does not exist: the CLI is leaf 2 of the S-247 cascade (csrc/tools/layout_dump.c)"
    exe = tmp_path_factory.mktemp("lkcli_" + opt) / "layout_dump"
    r = subprocess.run(["cc", *FLAGS, "-" + opt, "-I", str(CSRC), "-o", str(exe), str(src),
                        *map(str, engine_sources()), "-lm"], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"cc failed: {r.stderr[-3000:]}")
    return exe


def build_probe(tmp_path_factory):
    exe = tmp_path_factory.mktemp("lkprobe") / "layout_kit_probe"
    r = subprocess.run(["cc", *FLAGS, "-O2", "-I", str(CSRC), "-o", str(exe), str(PROBE_SRC),
                        *map(str, engine_sources()), "-lm"], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"cc failed: {r.stderr[-3000:]}")
    return exe


# ---- running (results are cached: the binary is deterministic and a sweep asks the same question many times) ---------
_RUNS = {}


def run(exe, *args):
    key = (str(exe), tuple(map(str, args)))
    if key not in _RUNS:
        _RUNS[key] = subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=120)
    return _RUNS[key]


def dump_args(seed, sides="separate", canvas=None, brk=None):
    a = ["--seed", seed, "--archetype", "assault", "--sides", sides]
    if canvas is not None:
        a += ["--canvas", canvas]
    if brk is not None:
        a += ["--break", brk]
    return a


def dump(exe, seed, sides="separate", canvas=None, brk=None):
    """The JSON text of one layout (stdout of a run that must exit 0)."""
    r = run(exe, *dump_args(seed, sides, canvas, brk))
    if r.returncode != 0:
        raise AssertionError(f"layout_dump {dump_args(seed, sides, canvas, brk)} exited {r.returncode}: {r.stderr[-300:]}")
    return r.stdout


# Counts and indices: the spec types only seed, candidate, route_count and district as integers, so these may print
# whole or quantised (number_problems accepts both); load() turns them into ints so the tests can index with them.
INDEX_FIELDS = {"places": ["node"], "nodes": ["place"], "lanes": ["a", "b"], "chokes": ["axis_k", "lane"],
                "vantages": ["height_bands", "overlooks", "climb"], "requests": ["axis_k", "side"]}


def load(text):
    """JSON text -> dict, every non-integer number a Decimal (exact), the index fields of INDEX_FIELDS ints."""
    lay = json.loads(text, parse_float=Decimal)
    for arr, fields in INDEX_FIELDS.items():
        for el in lay.get(arr, []):
            for f in fields:
                el[f] = [int(v) for v in el[f]] if isinstance(el[f], list) else int(el[f])
    return lay


class Raw(str):
    """A number as printed."""


def load_raw(text):
    """JSON text -> dict whose numbers are Raw strings (the digits as printed), to judge the number format."""
    return json.loads(text, parse_float=Raw, parse_int=Raw)


def wu(v):
    return float(v)


def cents(v):
    return int((Decimal(v) * 100).to_integral_value())


# ---- the six checks again, in Python, over a parsed JSON --------------------------------------------------------------
def lane_len(lane):
    p = lane["pts"]
    return sum(math.hypot(wu(p[i + 1][0]) - wu(p[i][0]), wu(p[i + 1][1]) - wu(p[i][1])) for i in range(len(p) - 1))


def dijkstra(lay, src, skip_lane=None):
    """Route distances from node src over the lanes (node i joined by every lane a/b); math.inf when unreachable."""
    n = len(lay["nodes"])
    dist = [math.inf] * n
    adj = {i: [] for i in range(n)}
    for i, ln in enumerate(lay["lanes"]):
        if i != skip_lane:
            w = lane_len(ln)
            adj[ln["a"]].append((ln["b"], w))
            adj[ln["b"]].append((ln["a"], w))
    dist[src] = 0.0
    heap = [(0.0, src)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > dist[u]:
            continue
        for v, w in adj[u]:
            if du + w < dist[v]:
                dist[v] = du + w
                heapq.heappush(heap, (dist[v], v))
    return dist


def place_nodes(lay, kind):
    return [p["node"] for p in lay["places"] if p["kind"] == kind]


def objective_lanes(lay):
    obj = place_nodes(lay, "objective")[0]
    return obj, [i for i, ln in enumerate(lay["lanes"]) if obj in (ln["a"], ln["b"])]


def py_checks(lay, slack=SLACK):
    """{check name: bool} from places, nodes, lanes, chokes, vantages only (spec "Checks" 1 to 6). `slack` (wu) is
    granted to the inequalities so a hair of rounding in the printed hundredths never flips a verdict."""
    na, nb = place_nodes(lay, "base_forward")[0], place_nodes(lay, "base_home")[0]
    da, db = dijkstra(lay, na), dijkstra(lay, nb)
    out = {"connected": all(math.isfinite(x) for x in da)}
    res = place_nodes(lay, "resource")
    out["fairness"] = len(res) == 2 and all(
        math.isfinite(da[r]) and math.isfinite(db[r]) and abs(da[r] - db[r]) <= EQUAL_TOL * max(da[r], db[r]) + slack
        for r in res)
    byp = True
    for ck in lay["chokes"]:
        ln = lay["lanes"][ck["lane"]]
        avoid = dijkstra(lay, ln["a"], skip_lane=ck["lane"])[ln["b"]]
        byp = byp and math.isfinite(avoid) and avoid >= BYPASS_MIN * lane_len(ln) - slack    # no way round fails
    out["bypass"] = byp
    obj, touching = objective_lanes(lay)
    out["approaches"] = len(touching) >= APPROACHES_MIN and all(
        math.isfinite(dijkstra(lay, na, skip_lane=i)[obj]) for i in touching)
    out["chokes"] = all(CHOKE_W_MIN - 1e-9 <= wu(ck["width"]) <= CHOKE_W_MAX + 1e-9 for ck in lay["chokes"])
    c = wu(lay["canvas"]) + EDGE_SLACK
    inside = lambda v, r=0.0: -EDGE_SLACK <= wu(v) - r and wu(v) + r <= c       # noqa: E731
    ok = all(inside(p["x"], wu(p["pad_r"])) and inside(p["y"], wu(p["pad_r"])) for p in lay["places"])
    ok = ok and all(inside(n["x"]) and inside(n["y"]) for n in lay["nodes"])
    ok = ok and all(inside(x) and inside(y) for ln in lay["lanes"] for x, y in ln["pts"])
    ok = ok and all(inside(k["x"]) and inside(k["y"]) for k in lay["chokes"])
    ok = ok and all(inside(v["x"], wu(v["radius"])) and inside(v["y"], wu(v["radius"])) for v in lay["vantages"])
    out["bounds"] = ok
    return out


def consistency_problems(lay):
    """Everything in a dumped layout that must follow from its own lanes (so run_checks ran after any edit):
    `checks` equals py_checks, `fairness` equals my Dijkstra (1 wu; -1.00 for unreachable), route_count equals the
    number of route / way_round / objective_route lanes."""
    out = []
    mine = py_checks(lay)
    for name in CHECKS:
        if lay["checks"][name] is not mine[name]:
            out.append(f"checks.{name}: json {lay['checks'][name]} vs python {mine[name]}")
    na, nb = place_nodes(lay, "base_forward")[0], place_nodes(lay, "base_home")[0]
    obj = place_nodes(lay, "objective")[0]
    res = place_nodes(lay, "resource")
    da, db = dijkstra(lay, na), dijkstra(lay, nb)
    want = {"dist_a_objective": da[obj], "dist_b_objective": db[obj],
            "dist_a_res": [da[r] for r in res], "dist_b_res": [db[r] for r in res]}
    for key, w in want.items():
        got = lay["fairness"][key]
        for g, m in zip(got if isinstance(got, list) else [got], w if isinstance(w, list) else [w]):
            if (not math.isfinite(m) and g != Decimal("-1")) or (math.isfinite(m) and abs(wu(g) - m) > SLACK):
                out.append(f"fairness.{key}: json {g} vs python {m}")
    routes = sum(1 for ln in lay["lanes"] if ln["kind"] in ("route", "way_round", "objective_route"))
    if lay["route_count"] != routes:
        out.append(f"route_count {lay['route_count']} vs {routes}")
    return out


# ---- the deterministic edits of criterion 6, written again from the spec's words ---------------------------------------
def first_choke_way_round(lay):
    ck = lay["chokes"][0]
    ln = lay["lanes"][ck["lane"]]
    for i, o in enumerate(lay["lanes"]):
        if o["kind"] == "way_round" and {o["a"], o["b"]} == {ln["a"], ln["b"]}:
            return i
    return None


def apply_break(lay, name):
    """The layout after `--break name`, as the spec words it (criterion 6, amended 2026-11-05 for fairness)."""
    lay = copy.deepcopy(lay)
    if name in ("connected", "approaches"):
        obj, touching = objective_lanes(lay)
        drop = touching if name == "connected" else touching[:1]
        lay["lanes"] = [ln for i, ln in enumerate(lay["lanes"]) if i not in drop]
    elif name == "bypass":
        del lay["lanes"][first_choke_way_round(lay)]
    elif name == "chokes":
        lay["chokes"][0]["width"] = Decimal(CHOKE_W_MAX + 100)
    elif name == "bounds":
        edge = lay["canvas"] + 100
        lay["places"][0]["x"] = edge
        lay["nodes"][lay["places"][0]["node"]]["x"] = edge
    elif name == "fairness":      # one straight route lane, side A's base node to resource 0's node, first route lane's width
        r = next(p for p in lay["places"] if p["kind"] == "resource")
        a = next(p for p in lay["places"] if p["kind"] == "base_forward")
        w = next(ln["width"] for ln in lay["lanes"] if ln["kind"] == "route")
        na, nr = lay["nodes"][a["node"]], lay["nodes"][r["node"]]
        lay["lanes"].append({"kind": "route", "a": a["node"], "b": r["node"], "width": w,
                             "pts": [[na["x"], na["y"]], [nr["x"], nr["y"]]]})
    return lay


def _strip(lay, drop_refs):
    d = {k: v for k, v in lay.items() if k not in ("checks", "fairness", "route_count")}
    if drop_refs:     # the spec does not say whether the edit renumbers the lane indices held by chokes and vantages
        d["chokes"] = [{k: v for k, v in c.items() if k != "lane"} for c in lay["chokes"]]
        d["vantages"] = [{k: v for k, v in c.items() if k not in ("overlooks", "climb")} for c in lay["vantages"]]
    return d


def edit_problems(base, broken, name):
    """Differences between the CLI's broken layout and the edit the spec words; [] when it is exactly that edit."""
    want = apply_break(base, name)
    refs = name in ("connected", "bypass", "approaches")     # lanes removed: the spec leaves the held lane indices open
    out = []
    a, b = _strip(want, refs), _strip(broken, refs)
    out += [f"{k} differs" for k in a if a[k] != b.get(k)]
    out += [f"{k} unexpected" for k in b if k not in a]
    return out


# ---- the JSON section's text rules ------------------------------------------------------------------------------------
QUANT = re.compile(r"^-?\d+\.\d\d$")
INTEGER = re.compile(r"^-?\d+$")
EITHER = re.compile(r"^-?\d+(\.\d\d)?$")      # a count or index the spec does not type as whole or quantised


def order_problems(text):
    """Key order of every object, from the raw text."""
    out = []
    pairs = json.loads(text, object_pairs_hook=lambda p: p)
    if [k for k, _ in pairs] != TOP_KEYS:
        out.append(f"top-level keys {[k for k, _ in pairs]}")
    top = dict(pairs)
    for key, want in ELEM_KEYS.items():
        for i, el in enumerate(top.get(key, [])):
            if [k for k, _ in el] != want:
                out.append(f"{key}[{i}] keys {[k for k, _ in el]}")
                break
    if [k for k, _ in top.get("fairness", [])] != FAIRNESS_KEYS:
        out.append("fairness keys")
    if [k for k, _ in top.get("checks", [])] != CHECKS:
        out.append("checks keys")
    return out


def number_problems(text):
    """Every printed number: quantised `[-]int.dd` (every coordinate, width, radius, distance, canvas, frac, request
    height_bands and drafts value), a bare integer for seed, candidate, route_count and district, whole or quantised
    for the other counts and indices; never an exponent, never `-0.00`."""
    raw = load_raw(text)
    out = []

    def chk(v, rx, where):
        if isinstance(v, list):
            for i, e in enumerate(v):
                chk(e, rx, f"{where}[{i}]")
        elif not (isinstance(v, Raw) and rx.match(v)) or v == "-0.00":
            out.append(f"{where}: {v!r}")

    for k in ("seed", "candidate", "route_count"):
        chk(raw[k], INTEGER, k)
    chk(raw["canvas"], QUANT, "canvas")
    for k, v in raw["drafts"].items():
        chk(v, QUANT, f"drafts.{k}")
    chk(raw["district"], INTEGER, "district")
    spec = {"places": {"x": QUANT, "y": QUANT, "pad_r": QUANT, "node": EITHER},
            "nodes": {"x": QUANT, "y": QUANT, "place": EITHER},
            "lanes": {"a": EITHER, "b": EITHER, "width": QUANT, "pts": QUANT},
            "chokes": {"x": QUANT, "y": QUANT, "width": QUANT, "length": QUANT, "wall_span": QUANT, "frac": QUANT,
                       "axis_k": EITHER, "lane": EITHER},
            "vantages": {"x": QUANT, "y": QUANT, "radius": QUANT, "height_bands": EITHER, "overlooks": EITHER,
                         "climb": EITHER},
            "requests": {"x": QUANT, "y": QUANT, "r": QUANT, "w": QUANT, "len": QUANT, "span": QUANT, "frac": QUANT,
                         "height_bands": QUANT, "axis_k": EITHER, "side": EITHER}}
    for arr, fields in spec.items():
        for i, el in enumerate(raw[arr]):
            for f, rx in fields.items():
                chk(el[f], rx, f"{arr}[{i}].{f}")
    for k in FAIRNESS_KEYS:
        chk(raw["fairness"][k], QUANT, f"fairness.{k}")
    return out


def text_problems(text):
    """Layout of the file: ends with one newline, two-space indent, one array element per line, district rows on one
    line each."""
    out = []
    lines = text.split("\n")
    if not text.endswith("}\n") or text.endswith("\n\n") or lines[0] != "{":
        out.append("not `{` ... `}` + one newline")
    lay = json.loads(text)
    tops = [ln[:ln.index('"', 3) + 1] for ln in lines if ln.startswith('  "')]
    if tops != [f'  "{k}"' for k in TOP_KEYS]:
        out.append(f"two-space top-level key lines: {tops[:4]}")
    for key in ARRAY_KEYS + ["district"]:
        start = lines.index(f'  "{key}": [') if f'  "{key}": [' in lines else -1
        if start < 0:
            out.append(f"{key}: no `  \"{key}\": [` line")
            continue
        end = start + 1
        while end < len(lines) and not lines[end].startswith("  ]"):
            end += 1
        body = lines[start + 1:end]
        if len(body) != len(lay[key]) or not all(b.startswith("    ") and not b.startswith("     ") for b in body):
            out.append(f"{key}: {len(body)} lines for {len(lay[key])} elements")
    return out


def name_problems(lay):
    """The strings of the JSON section: archetype, sides, side letters, and every kind/piece/landform/mode name."""
    out = []
    if lay["archetype"] != "assault" or lay["sides"] not in SIDES:
        out.append("archetype/sides")

    def one(val, domain, where):
        if val not in NAMES[domain]:
            out.append(f"{where}: {val!r}")

    for i, p in enumerate(lay["places"]):
        one(p["kind"], 0, f"places[{i}].kind")
        one(p["piece"], 5, f"places[{i}].piece")
        if p["side"] not in ("A", "B", "none"):
            out.append(f"places[{i}].side {p['side']!r}")
    for i, ln in enumerate(lay["lanes"]):
        one(ln["kind"], 1, f"lanes[{i}].kind")
    for arr in ("chokes", "vantages"):
        for i, e in enumerate(lay[arr]):
            one(e["landform"], 2, f"{arr}[{i}].landform")
            one(e["piece"], 5, f"{arr}[{i}].piece")
    for i, q in enumerate(lay["requests"]):
        one(q["kind"], 3, f"requests[{i}].kind")
        one(q["mode"], 4, f"requests[{i}].mode")
        one(q["piece"], 5, f"requests[{i}].piece")
        one(q["landform"], 2, f"requests[{i}].landform")
    return out


# ---- the wave 1 probe as the reference for what the engine produced -------------------------------------------------------
def probe_layout(probe, seed, sides, canvas=CANVAS):
    """The engine's own dump (integer hundredths) for seed, Assault, sides index, canvas; parsed."""
    r = run(probe, "gen", seed, 3, float(canvas), SIDES.index(sides))
    d = {"kv": {}, "fair": {}, "district": [], "place": [], "node": [], "lane": [], "choke": [], "vantage": [],
         "request": []}
    for line in r.stdout.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] in ("place", "node", "lane", "choke", "vantage", "request"):
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


def probe_drafts(probe):
    """[(name, hundredths)] in table order, from om_lk_draft_name/value through the probe."""
    out = []
    for line in run(probe, "drafts").stdout.splitlines():
        t = line.split()
        if t and t[0] == "draft":
            out.append((t[2], int(t[3])))
    return out


def header_draft_names():
    """DRAFT names in the order of the X-macro table of csrc/layout_drafts.h."""
    text = (CSRC / "layout_drafts.h").read_text()
    table = text[text.index("LK_DRAFT_TABLE(X)"):]
    return re.findall(r"X\((DRAFT_\w+),", table)


def probe_problems(lay, pr, tol=1):
    """Differences between the CLI's JSON and the engine's own dump of the same call (hundredths, +-tol)."""
    out = []

    def same(got, want, where):
        if abs(cents(got) - want) > tol:
            out.append(f"{where}: json {got} vs engine {want / 100}")

    def eq(got, want, where):
        if got != want:
            out.append(f"{where}: json {got!r} vs engine {want!r}")

    eq(lay["seed"], pr["kv"].get("seed", lay["seed"]), "seed")
    same(lay["canvas"], pr["kv"]["canvas"], "canvas")
    eq(lay["candidate"], pr["kv"]["candidate"], "candidate")
    eq(lay["route_count"], pr["kv"]["route_count"], "route_count")
    eq(lay["district"], pr["district"], "district")
    for key, rec in (("places", "place"), ("nodes", "node"), ("lanes", "lane"), ("chokes", "choke"),
                     ("vantages", "vantage"), ("requests", "request")):
        eq(len(lay[key]), len(pr[rec]), f"len({key})")
    for e, p in zip(lay["places"], pr["place"]):
        eq((e["kind"], e["side"], e["piece"], e["node"]),
           (NAMES[0][p["kind"]], SIDE_TEXT[p["side"]], NAMES[5][p["piece"]], p["node"]), "place")
        for f in ("x", "y", "pad_r"):
            same(e[f], p[f], f"place.{f}")
    for e, p in zip(lay["nodes"], pr["node"]):
        eq(e["place"], p["place"], "node.place")
        same(e["x"], p["x"], "node.x")
        same(e["y"], p["y"], "node.y")
    for e, p in zip(lay["lanes"], pr["lane"]):
        eq((e["kind"], e["a"], e["b"], len(e["pts"])), (NAMES[1][p["kind"]], p["a"], p["b"], p["n_pts"]), "lane")
        same(e["width"], p["width"], "lane.width")
        for (x, y), (px, py) in zip(e["pts"], p["pts"]):
            same(x, px, "lane.pt.x")
            same(y, py, "lane.pt.y")
    for e, p in zip(lay["chokes"], pr["choke"]):
        eq((e["axis_k"], e["lane"], e["landform"], e["piece"]),
           (p["axis_k"], p["lane"], NAMES[2][p["landform"]], NAMES[5][p["piece"]]), "choke")
        for f in ("x", "y", "width", "length", "wall_span", "frac"):
            same(e[f], p[f], f"choke.{f}")
    for e, p in zip(lay["vantages"], pr["vantage"]):
        eq((e["height_bands"], e["overlooks"], e["climb"], e["landform"], e["piece"]),
           (p["height_bands"], p["overlooks"], [p["climb0"], p["climb1"]], NAMES[2][p["landform"]], NAMES[5][p["piece"]]),
           "vantage")
        for f in ("x", "y", "radius"):
            same(e[f], p[f], f"vantage.{f}")
    for e, p in zip(lay["requests"], pr["request"]):
        eq((e["kind"], e["mode"], e["piece"], e["name"], e["axis_k"], e["side"], e["landform"]),
           (NAMES[3][p["kind"]], NAMES[4][p["mode"]], NAMES[5][p["piece"]], p["name"], p["axis_k"], p["side"],
            NAMES[2][p["landform"]]), "request")
        for f in ("x", "y", "r", "w", "len", "span", "frac", "height_bands"):
            same(e[f], p[f], f"request.{f}")
    f = pr["fair"]
    got = lay["fairness"]
    for g, w, where in ((got["dist_a_objective"], f["dist_a_objective"], "dist_a_objective"),
                        (got["dist_b_objective"], f["dist_b_objective"], "dist_b_objective"),
                        (got["dist_a_res"][0], f["dist_a_res0"], "dist_a_res0"),
                        (got["dist_a_res"][1], f["dist_a_res1"], "dist_a_res1"),
                        (got["dist_b_res"][0], f["dist_b_res0"], "dist_b_res0"),
                        (got["dist_b_res"][1], f["dist_b_res1"], "dist_b_res1")):
        same(g, w, f"fairness.{where}")
    eq([lay["checks"][n] for n in CHECKS], [bool((pr["kv"]["checks"] >> i) & 1) for i in range(6)], "checks")
    return out


# ---- text edits of a written JSON (the file format is fixed, so a line edit keeps it a file this tool wrote) ----------
def delete_lane_line(text, lane_index):
    """The JSON with the lines of lane `lane_index` removed (a comma moved if it was the last element) and the lane
    indices held by chokes and vantages above it lowered by one, so no index points past the end. One that pointed at
    the removed lane now points at the lane that took its place."""
    lines = text.split("\n")
    start = lines.index('  "lanes": [') + 1
    i = start + lane_index
    last = not lines[i].endswith(",")
    del lines[i]
    if last:
        lines[i - 1] = lines[i - 1].rstrip(",")
    low = lambda n: n - 1 if n > lane_index else n      # noqa: E731
    subs = {"chokes": [(r'("lane": )(\d+)', lambda m: m.group(1) + str(low(int(m.group(2)))))],
            "vantages": [(r'("overlooks": )(\d+)', lambda m: m.group(1) + str(low(int(m.group(2))))),
                         (r'("climb": \[\s*)(\d+)(\s*,\s*)(\d+)', lambda m: f"{m.group(1)}{low(int(m.group(2)))}{m.group(3)}{low(int(m.group(4)))}")]}
    for blk, rules in subs.items():
        j = lines.index(f'  "{blk}": [') + 1
        while not lines[j].startswith("  ]"):
            for pat, fn in rules:
                lines[j] = re.sub(pat, fn, lines[j])
            j += 1
    return "\n".join(lines)
