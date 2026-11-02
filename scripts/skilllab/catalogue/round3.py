"""H-025 round three, first batch: six layouts for each of the priority kinds chokepoint, vantage, flank_route, city and trap (30 in all), from Westley's
2026-11-01 rules (docs/stories/H-025.md "Round three"): holding sides stand in arcs, a chokepoint arc's range covers the mouth, a surround is arcs on a ring
around the centre force. Side A is blue (the better-positioned side), side B red.

CLI: python3 -m scripts.skilllab.catalogue.round3 --out <dir> [--first-id 55]
Each layout is checked by produce.check_layout (R1 to R7) plus this file's own checks (mouth coverage, walkable city streets); a layout that fails either is
not written and `REJECT <name> <why>` goes to stderr. Exit 2 when any layout was rejected. `predict_rate` is written only where Westley gave a number
(docs/northstar/research/layer_dynamics/heuristics.md); every other layout says so in `predict_why` and carries none. Every number not marked as his is an
Architect-draft default of this file (named DRAFT-r3-*); Westley rules.
Arc rows follow scripts/skilllab/arena/situations.py `_arc_units` (record `centre/radius/start_deg/end_deg/count`, units tagged `arc` = the record's index,
facing the centre, spaced at the chord PITCH). See also scripts/skilllab/catalogue/produce.py (check_layout, write_layout, _grid)."""
import argparse
import math
import random
import sys
from collections import deque
from pathlib import Path

from scripts.skilllab.catalogue.produce import PITCH, _grid, _rect, _round_unit, check_layout, presets, rules, write_layout

BLUE_MIX = ("Vanguard", "Warden")  # DRAFT-r3-blue-mix: ranges 300 and 350, so a ring at 290 to 330 reaches the point it is drawn round
RED_MIX = ("Vanguard", "Raider", "Interceptor")  # DRAFT-r3-red-mix
MOUTH_COVERAGE = 0.5  # DRAFT-mouth-coverage (story)
CITY_STREET_MIN = 40.0  # 2 x the unit radius 15 plus 10 (story, round three city rule)
CITY_SIZES = [(80, 80), (120, 100), (160, 120)]  # DRAFT-r3-city-footprints, three sizes picked per building from the layout's seed
UNIT_RADIUS = 15.0  # OM_UNIT_COLLISION_RADIUS (ALG-68)


# ---------------------------------------------------------------- units

def _roles(n, mix):
    return [mix[i % len(mix)] for i in range(n)]


def _step_deg(radius):
    return math.degrees(2 * math.asin(PITCH / (2 * radius)))


def _ring(units, arcs, cx, cy, radius, centre_deg, n, roles, layer):
    """One ring of n units centred on `centre_deg` (degrees, y south), spaced at the chord PITCH, facing the centre; appends the arc record and tags the units."""
    step = _step_deg(radius)
    start = centre_deg - (n - 1) / 2 * step
    index = len(arcs)
    for k in range(n):
        a = math.radians(start + k * step)
        x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
        units.append(dict(_round_unit(x, y, math.atan2(cy - y, cx - x), layer, roles[k]), arc=index))
    arcs.append({"centre": [cx, cy], "radius": radius, "start_deg": round(start, 4), "end_deg": round(start + (n - 1) * step, 4), "count": n})


def _rings(units, arcs, cx, cy, r0, centre_deg, n, caps, layer, mix=BLUE_MIX):
    """n units in concentric rings r0, r0 + PITCH, ...; ring k holds at most caps[k] (the last cap repeats). Roles cycle through `mix` over the whole group."""
    roles, done, k = _roles(n, mix), 0, 0
    while done < n:
        m = min(n - done, caps[min(k, len(caps) - 1)])
        _ring(units, arcs, cx, cy, r0 + k * PITCH, centre_deg, m, roles[done:done + m], layer)
        done, k = done + m, k + 1


def _block(units, n, cx, cy, facing, layer, mix):
    roles = _roles(n, mix)
    for (x, y, f), role in zip(_grid(n, cx, cy, facing), roles):
        units.append(_round_unit(x, y, f, layer, role))


def _split(n, parts):
    base = [n // parts + (1 if i < n % parts else 0) for i in range(parts)]
    return base


# ---------------------------------------------------------------- checks of this file

def _mouth_coverage(layout, exit_points):
    """The least fraction, over the exit points, of blue's arc units whose own range ring contains the point (the story's DRAFT-mouth-coverage test)."""
    arc_units = [u for u in layout["side_a"]["units"] if "arc" in u]
    worst = 1.0
    for px, py in exit_points:
        hit = sum(1 for u in arc_units if math.hypot(u["x"] - px, u["y"] - py) <= u["range"])
        worst = min(worst, hit / len(arc_units))
    return worst


def _rects(layout):
    out = []
    for f in layout["features"]:
        for key in ("walls", "boxes", "buildings"):
            out += f.get(key, [])
    return out


def _walkable(layout, start, goal):
    """True when a unit of radius 15 can walk from `start` to `goal` over a 20 wu grid with every wall/building rectangle grown by 15 (the city route check)."""
    cell, n = 20.0, 200
    rects = [(r["x"] - r["w"] / 2 - UNIT_RADIUS, r["x"] + r["w"] / 2 + UNIT_RADIUS, r["y"] - r["h"] / 2 - UNIT_RADIUS, r["y"] + r["h"] / 2 + UNIT_RADIUS)
             for r in _rects(layout)]

    def free(i, j):
        x, y = i * cell + cell / 2, j * cell + cell / 2
        return 0 <= i < n and 0 <= j < n and not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in rects)
    s, g = (int(start[0] // cell), int(start[1] // cell)), (int(goal[0] // cell), int(goal[1] // cell))
    seen, queue = {s}, deque([s])
    while queue:
        i, j = queue.popleft()
        if (i, j) == g:
            return True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (i + di, j + dj)
            if nxt not in seen and free(*nxt):
                seen.add(nxt)
                queue.append(nxt)
    return False


def _street_gaps(buildings):
    """The narrowest clear gap between two grid neighbours (same row or column, 300 apart centre to centre), world units."""
    least = 1e9
    for i, p in enumerate(buildings):
        for q in buildings[i + 1:]:
            if p["y"] == q["y"] and abs(p["x"] - q["x"]) == 300:
                least = min(least, 300 - (p["w"] + q["w"]) / 2)
            elif p["x"] == q["x"] and abs(p["y"] - q["y"]) == 300:
                least = min(least, 300 - (p["h"] + q["h"]) / 2)
    return least


# ---------------------------------------------------------------- the five kinds. Each returns (layout fields, notes dict) for one headcount pair and variant.

CX = CY = 2000.0


def chokepoint(nb, nr, variant):
    """Blue arcs flush at the exit of the gap (centred on the exit's centre point), range covering the mouth; red files in from the west."""
    gap, off = 200, 350
    walls = [_rect(CX, CY - off, 200, 500), _rect(CX, CY + off, 200, 500)]
    feature = {"kind": "chokepoint", "x": CX, "y": CY, "gap": gap, "radius": 600, "walls": walls}
    ex, ey = CX + 100.0, CY   # the exit of the gap on blue's side
    a, b, arcs = [], [], []
    reserve = 8 if variant == "reserve" else 0
    n_arc = nb - reserve
    if n_arc <= 14:
        _rings(a, arcs, ex, ey, 250.0, 0.0, n_arc, [n_arc], 0)
    else:
        first = math.ceil(n_arc / 2)
        _rings(a, arcs, ex, ey, 250.0, 0.0, n_arc, [first, n_arc - first], 0)
    if reserve:
        _block(a, reserve, 2900.0, CY, math.pi, 0, BLUE_MIX)
    if variant == "two_blocks":
        n1, n2 = _split(nr, 2)
        _block(b, n1, 1300.0, 1450.0, 0.0, 0, RED_MIX)
        _block(b, n2, 1300.0, 2550.0, 0.0, 0, RED_MIX)
    else:
        _block(b, nr, 1100.0, CY, 0.0, 0, RED_MIX)
    exits = [(ex, ey + t) for t in (-100, -50, 0, 50, 100)]
    return dict(landscape="small_flat", features=[feature], orders="hold:A", defender="A", arcs_a=arcs, a=a, b=b), {"exits": exits}


def vantage(nb, nr, variant):
    """Blue arcs concave toward the red approach, the first ring a hundred units inside the hill's western rim; the hill stands one travel band up."""
    hx, hy, hr = CX, CY, 700.0
    feature = {"kind": "vantage", "x": hx, "y": hy, "radius": hr, "height_band": 1}
    qx, qy = 1100.0, CY   # the arcs' centre, west of the hill, on red's side
    a, b, arcs = [], [], []
    reserve = 8 if variant == "reserve" else 0
    n_arc = nb - reserve
    caps = []
    for k in range(8):   # per ring: the most units that stay inside the hill minus 25 wu at the ring's radius
        r = 300.0 + k * PITCH
        half = 0.0
        while math.hypot(qx + r * math.cos(math.radians(half + 0.5)) - hx, r * math.sin(math.radians(half + 0.5))) <= hr - 25 and half < 80:
            half += 0.5
        caps.append(1 + int(2 * half // _step_deg(r)))
    _rings(a, arcs, qx, qy, 300.0, 0.0, n_arc, caps, 1)
    if reserve:
        _block(a, reserve, 2250.0, CY, math.pi, 1, BLUE_MIX)
    if variant == "two_groups":
        n1, n2 = _split(nr, 2)
        _block(b, n1, 800.0, 1450.0, 0.0, 0, RED_MIX)
        _block(b, n2, 800.0, 2550.0, 0.0, 0, RED_MIX)
    else:
        _block(b, nr, 700.0, CY, 0.0, 0, RED_MIX)
    return dict(landscape="small_tiered", features=[feature], orders="hold:A", defender="A", arcs_a=arcs, a=a, b=b), {}


def flank_route(nb, nr, variant):
    """Red holds at the centre; blue's prongs are arcs on a ring of 300 about it (two prongs east and west, or three at 120 degrees); a ridge and the route
    that goes round it show how the rear prong came. `variant` is the number of prongs."""
    prongs = variant
    ridge = _rect(1100.0, CY, 300, 1400)
    route = [[600.0, 2000.0], [1100.0, 1150.0], [2100.0, 1000.0], [2750.0, 1500.0], [2650.0, 2000.0]]   # DRAFT-flank-behind: ends past red's rear (its east side)
    feature = {"kind": "flank_route", "x": 600.0, "y": CY, "points": route, "ridge": ridge, "height_band": 1}
    centres = {2: [180.0, 0.0], 3: [210.0, 330.0, 90.0]}[prongs]
    a, b, arcs = [], [], []
    for centre_deg, n in zip(centres, _split(nb, prongs)):
        _rings(a, arcs, CX, CY, 300.0, centre_deg, n, [n], 0)
    _block(b, nr, CX, CY, 0.0, 0, RED_MIX)
    return dict(landscape="small_tiered", features=[feature], orders="hold:B", defender="B", arcs_a=arcs, a=a, b=b), {}


def city(nb, nr, variant, seed):
    """Blue inside a city: a 7 by 7 grid on a 300 pitch in three footprints, rows j = -1 and +1 left open as the two west-to-east entry streets (31 buildings, the
    four corners left out); blue's arcs stand on those streets near the west edge; red marches in from the west along them. A `transit` feature marks red's route."""
    rng = random.Random(seed)
    buildings = []
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(j) == 1 or (abs(i) == 3 and abs(j) == 3):
                continue   # the two entry streets; the four corners
            w, h = rng.choice(CITY_SIZES)
            buildings.append(_rect(CX + i * 300, CY + j * 300, w, h))
    feature = {"kind": "city", "x": CX, "y": CY, "radius": 1000, "buildings": buildings}
    goal = (CX, CY + 300.0)
    route = {"kind": "transit", "x": 700.0, "y": CY, "points": [[700.0, CY], [1000.0, CY + 300.0], [CX, CY + 300.0]], "dest": {"x": goal[0], "y": goal[1]}}
    a, b, arcs = [], [], []
    reserve = 8 if variant == "reserve" else 0
    n_arc = nb - reserve
    for m_y, n in ((CY - 300.0, (n_arc + 1) // 2), (CY + 300.0, n_arc // 2)):
        _rings(a, arcs, 1150.0, m_y, 220.0, 0.0, n, [8], 0)
    if reserve:
        _block(a, reserve, 2400.0, CY - 300.0, math.pi, 0, BLUE_MIX)
    if variant == "two_groups":
        n1, n2 = _split(nr, 2)
        _block(b, n1, 700.0, 1700.0, 0.0, 0, RED_MIX)
        _block(b, n2, 700.0, 2300.0, 0.0, 0, RED_MIX)
    else:
        _block(b, nr, 700.0, CY, 0.0, 0, RED_MIX)
    return dict(landscape="small_flat", features=[feature, route], orders="hold:A", defender="A", arcs_a=arcs, a=a, b=b), {"gap": _street_gaps(buildings), "start": (700.0, CY), "goal": goal}


def trap(nb, nr, variant):
    """Red is led into a three-walled pocket (its destination is inside it); blue holds two blocks on hills either side of the mouth and an arc behind red that
    closes the retreat. `variant` 'no_rear' drops the arc (two attack points)."""
    walls = [_rect(1600, 2000, 200, 800), _rect(2400, 2000, 200, 800), _rect(2000, 1500, 1000, 200)]
    feature = {"kind": "trap", "x": CX, "y": CY, "mouth": round(math.pi / 2, 6), "walls": walls}
    hills = [{"kind": "vantage", "x": 1150.0, "y": 2750.0, "radius": 450, "height_band": 1}, {"kind": "vantage", "x": 2850.0, "y": 2750.0, "radius": 450, "height_band": 1}]
    a, b, arcs = [], [], []
    rear = 0 if variant == "no_rear" else max(nb * 2 // 5, 8)
    left, right = _split(nb - rear, 2)
    _block(a, left, 1150.0, 2750.0, 0.0, 1, BLUE_MIX)
    _block(a, right, 2850.0, 2750.0, math.pi, 1, BLUE_MIX)
    if rear:
        _rings(a, arcs, CX, 2400.0, 800.0, 90.0, rear, [rear], 0)
    _block(b, nr, CX, 2900.0, -math.pi / 2, 0, RED_MIX)
    return dict(landscape="small_tiered", features=[feature] + hills, orders="both_same_point", orders_point=[2000.0, 1950.0], defender="A", arcs_a=arcs, a=a, b=b), {}


# ---------------------------------------------------------------- the thirty layouts

# (kind, name, blue, red, variant, rate (Westley's number or None), what the layout is)
CHOKE_FIELDS = "his drawn layout: blue arc flush at the exit, range covering the mouth"
PLAN = [
    ("chokepoint", "choke-24v24", 24, 24, "plain", 0.98, CHOKE_FIELDS),
    ("chokepoint", "choke-16v32", 16, 32, "plain", None, "the same arc at 1:2 against blue"),
    ("chokepoint", "choke-12v48", 12, 48, "plain", None, "the same arc at 1:4 against blue"),
    ("chokepoint", "choke-32v16", 32, 16, "plain", None, "the same arc at 2:1 for blue"),
    ("chokepoint", "choke-24v24-reserve", 24, 24, "reserve", None, "16 in the arc and a reserve block of 8 behind it"),
    ("chokepoint", "choke-20v40-two", 20, 40, "two_blocks", None, "red comes in two blocks from the north-west and south-west, 1:2"),
    ("vantage", "vantage-24v24", 24, 24, "plain", 0.98, "his drawn layout: blue arc near the hill's edge, hill of one travel band"),
    ("vantage", "vantage-16v32", 16, 32, "plain", None, "the same at 1:2 against blue"),
    ("vantage", "vantage-12v48", 12, 48, "plain", None, "the same at 1:4 against blue"),
    ("vantage", "vantage-32v16", 32, 16, "plain", None, "the same at 2:1 for blue"),
    ("vantage", "vantage-24v24-two", 24, 24, "two_groups", None, "red comes in two groups from two angles"),
    ("vantage", "vantage-24v24-reserve", 24, 24, "reserve", None, "16 in the arc and a reserve block of 8 on the hill"),
    ("flank_route", "flank-2prong-24v24", 24, 24, 2, 0.95, "two-pronged surround, equal forces"),
    ("flank_route", "flank-3prong-24v24", 24, 24, 3, 0.95, "three-pronged surround, equal forces"),
    ("flank_route", "flank-3prong-32v32", 32, 32, 3, 0.95, "three-pronged surround, equal forces, larger"),
    ("flank_route", "flank-2prong-12v24", 12, 24, 2, 0.75, "two-pronged surround with half the centre force"),
    ("flank_route", "flank-3prong-16v32", 16, 32, 3, 0.75, "three-pronged surround with half the centre force"),
    ("flank_route", "flank-2prong-12v36", 12, 36, 2, None, "two-pronged surround with a third of the centre force"),
    ("city", "city-24v24", 24, 24, "plain", 0.75, "his drawn layout: blue inside, two entry-street arcs, 31 buildings"),
    ("city", "city-16v32", 16, 32, "plain", None, "the same at 1:2 against blue"),
    ("city", "city-12v48", 12, 48, "plain", None, "the same at 1:4 against blue"),
    ("city", "city-32v16", 32, 16, "plain", None, "the same at 2:1 for blue"),
    ("city", "city-24v24-reserve", 24, 24, "reserve", None, "16 in the entry arcs and a reserve block of 8 on the north street"),
    ("city", "city-16v32-two", 16, 32, "two_groups", None, "red comes in two groups, 1:2"),
    ("trap", "trap-24v24", 24, 24, "plain", None, "red led into the pocket, two hill blocks and a rear arc"),
    ("trap", "trap-16v32", 16, 32, "plain", 0.75, "the trappers have half of the led force"),
    ("trap", "trap-12v48", 12, 48, "plain", None, "the trappers have a quarter of the led force"),
    ("trap", "trap-32v16", 32, 16, "plain", None, "the trappers have twice the led force"),
    ("trap", "trap-24v48", 24, 48, "plain", 0.75, "the trappers have half of the led force, larger"),
    ("trap", "trap-16v16-two", 16, 16, "no_rear", None, "two attack points only (the hill blocks), no rear arc"),
]

SITUATION_WORDS = {
    "chokepoint": ("blue holds the exit of a 200 wu gap in a wall in an arc whose weapon range reaches the mouth; red must come through the gap",
                   "this is a fair chokepoint: the arc is flush on the exit, the mouth is inside the arc's range, and the layout may run in the lab",
                   "the arc, the gap or the ratio does not read as a chokepoint; your note says what it needs"),
    "vantage": ("blue stands in an arc close to the western rim of a hill one travel band up, firing down at red crossing the flat",
                "this is a fair vantage: blue holds the high ground in an arc, and the layout may run in the lab",
                "the hill, the arc or the ratio is wrong for a vantage; your note says what is missing"),
    "flank_route": ("red holds the centre; blue's arcs close on it from two or three sides at once, the rear prong having come round the ridge",
                    "this is a fair flank (a subset of the trap): the surround is real and the layout may run in the lab",
                    "the prongs, the route or the ratio do not make a flank; your note says what does"),
    "city": ("blue stands inside a grid of 31 buildings in three sizes, in two arcs on the two open west-to-east entry streets; red marches in from the west along the marked route",
             "this is a fair city: blue is inside, the streets are walkable, the arcs cover the entries, and the layout may run in the lab",
             "the city is too uniform, the streets or arcs are wrong; your note says what a fair one has"),
    "trap": ("red is led toward the pocket's inside; blue holds hill blocks either side of the mouth and an arc behind red that closes the retreat",
             "this is a fair trap: red is led in, the mouth is closed from high ground at several points, and the layout may run in the lab",
             "the pocket, the lead-in or the closing force is wrong for a trap; your note says what a trapper has"),
}


def build(first_id):
    pre, rul = presets(), rules()
    out_layouts, rejected, notes_out = [], [], []
    for n, (kind, name, nb, nr, variant, rate, what) in enumerate(PLAN):
        seed = 3000 + n
        fields, extra = city(nb, nr, variant, seed) if kind == "city" else globals()[kind](nb, nr, variant)
        expect, approve, deny = SITUATION_WORDS[kind]
        if variant == "no_rear":   # two attack points, no rear arc (story: two or more blocks close the mouth from higher ground)
            expect = "red is led toward the pocket's inside; blue holds two blocks on hills either side of the mouth and no arc behind red"
            approve = "this is a fair two-point trap: red is led in and the mouth is closed from high ground by two blocks, and the layout may run in the lab"
        pred = ("Westley's number for this layout: blue wins %d%% of the time." % round(rate * 100)) if rate is not None else \
               "No win rate is given for this ratio; predict is blue only because blue holds the better position."
        layout = {"id": "L-%04d" % (first_id + n), "situation": kind, "landscape": fields["landscape"], "seed": seed, "predict": "A",
                  "predict_why": "%s (%s). %s" % (what[0].upper() + what[1:], name, pred), "verdict": "", "feedback": "",
                  "defender": fields["defender"], "features": fields["features"], "orders": fields["orders"],
                  "side_a": {"headcount": len(fields["a"]), "units": fields["a"], "arcs": fields["arcs_a"]},
                  "side_b": {"headcount": len(fields["b"]), "units": fields["b"]},
                  "what_to_expect": "%s: %d blue against %d red, %s. %s" % (name, nb, nr, expect, pred),
                  "approve_means": "Approve means: %s; blue's predicted win rate is %s." % (approve, ("%d%%" % round(rate * 100)) if rate is not None else "not set (none given)"),
                  "deny_means": "Deny means: %s." % deny}
        if not layout["side_a"]["arcs"]:
            del layout["side_a"]["arcs"]
        if rate is not None:
            layout["predict_rate"] = rate
        if "orders_point" in fields:
            layout["orders_point"] = fields["orders_point"]
        bad = ["%s %s" % (r, "") for r in check_layout(layout, pre, rul)]
        if kind == "chokepoint":
            cov = _mouth_coverage(layout, extra["exits"])
            layout["mouth_coverage"] = round(cov, 3)
            if cov < MOUTH_COVERAGE:
                bad.append("mouth-coverage %.2f < %.2f" % (cov, MOUTH_COVERAGE))
        if kind == "city":
            if extra["gap"] < CITY_STREET_MIN:
                bad.append("street gap %.1f < %.1f" % (extra["gap"], CITY_STREET_MIN))
            if not _walkable(layout, extra["start"], extra["goal"]):
                bad.append("no walkable route from red's start to the plaza")
        if bad:
            rejected.append((name, bad))
            continue
        out_layouts.append((name, layout))
    return out_layouts, rejected


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--first-id", type=int, default=55)
    args = ap.parse_args(argv)
    layouts, rejected = build(args.first_id)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    for name, layout in layouts:
        mc = layout.pop("mouth_coverage", None)
        write_layout(layout, args.out)
        print("WROTE %s %s %s%s" % (layout["id"], layout["situation"], name, "" if mc is None else " mouth_coverage %.2f" % mc))
    for name, why in rejected:
        print("REJECT %s %s" % (name, "; ".join(why)), file=sys.stderr)
    return 2 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
