"""H-025 layout catalogue producer: mass-produces layouts from the recorded rules (rules.toml) on the stage presets (presets.toml).

CLI: python3 -m scripts.skilllab.catalogue.produce --out <dir> --seed <int> [--batch two|one] [--situations <comma list or all>] [--pairs <"16:32,24:24">] [--plant <rule id>]
--batch two (the default, H-025 round two) writes the twelve recipes with landscape features; --situations and --pairs are optional and honoured when given.
--batch one keeps the round-one recipes for history only: batch one is denied (DEC-catalogue-batch1-denied-2026-10-31) and its layouts carry no features, so R6 rejects them.
Every number here that the story does not give is a named DRAFT; Westley rules. Nothing is deduced from a produced layout (DEC-lab-placeholders-no-deductions-2026-10-30).
"""
import argparse
import copy
import functools
import json
import math
import random
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITUATIONS = ["chokepoint", "vantage", "cover", "objective", "staging", "transit", "flank_route", "hazard_anchor", "slope", "city", "trap",
              "open_field"]  # DRAFT-situation-kinds
PITCH = 40.0  # DRAFT-formation-pitch-wu: 30 (R2) plus 10 so rounding and rotation never touch the limit
EDGE_OUTNUMBER = 2  # DRAFT-edge-outnumber-ratio: the side with the positional edge is predicted to win unless outnumbered by more than this
# DRAFT-role-mixes: front to back, one mix per side per layout
MIXES = [("Vanguard", "Raider"), ("Bastion", "Warden", "Bombard"), ("Vanguard", "Interceptor", "Bombard"), ("Raider", "Interceptor"),
         ("Warden", "Vanguard", "Bombard")]
PLANT_RULES = ["R1", "R2", "R3", "R4", "R5", "R6"]  # R7 (arc placement, H-053) has no planted counterpart
ONE_PAIRS = [(16, 16), (16, 32), (32, 16)]  # DRAFT-batch-one, history flag only


def _load(name):
    with open(HERE / name, "rb") as f:
        return tomllib.load(f)


def presets():
    return _load("presets.toml")


def rules():
    return _load("rules.toml")


# ---------------------------------------------------------------- rules

def _violations(layout, presets, rules):
    """[(rule id, detail)] for one layout."""
    out = []
    preset = presets.get(layout.get("landscape"))
    if preset is None:
        return [("R1", "landscape %r is not in presets.toml" % layout.get("landscape"))]
    units = []
    for side in ("side_a", "side_b"):
        s = layout[side]
        if not rules["R4"]["min"] <= s["headcount"] <= rules["R4"]["max"] or s["headcount"] != len(s["units"]):
            out.append(("R4", "%s headcount %s with %d unit rows" % (side, s["headcount"], len(s["units"]))))
        units += [(side, i, u) for i, u in enumerate(s["units"])]
    for side, i, u in units:
        if not (0 <= u["x"] <= preset["width"] and 0 <= u["y"] <= preset["height"]):
            out.append(("R1", "%s unit %d at (%s, %s) is outside %sx%s" % (side, i, u["x"], u["y"], preset["width"], preset["height"])))
        if not 0 <= u["layer"] < preset["layers"]:
            out.append(("R3", "%s unit %d on layer %s, preset has %d" % (side, i, u["layer"], preset["layers"])))
        if u["role"] not in rules["R5"]["roles"]:
            out.append(("R5", "%s unit %d role %r is not in the roster" % (side, i, u["role"])))
    gap = rules["R2"]["min_spacing"]
    for j, (sa, ia, a) in enumerate(units):
        for sb, ib, b in units[j + 1:]:
            d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
            if d < gap:
                out.append(("R2", "%s unit %d and %s unit %d are %.1f apart" % (sa, ia, sb, ib, d)))
    kind, feats = layout.get("situation"), layout.get("features", [])
    if kind != "open_field" and not any(f.get("kind") == kind for f in feats):
        out.append(("R6", "%s layout carries no %s feature" % (kind, kind)))
    pad = rules["R6"]["standoff"]
    rects = [r for f in feats for key in ("walls", "boxes", "buildings") for r in f.get(key, [])] + [f["ridge"] for f in feats if "ridge" in f]
    for side, i, u in units:
        for r in rects:
            if abs(u["x"] - r["x"]) < r["w"] / 2 + pad and abs(u["y"] - r["y"]) < r["h"] / 2 + pad:
                out.append(("R6", "%s unit %d at (%s, %s) is inside a wall, box or building plus %s" % (side, i, u["x"], u["y"], pad)))
                break
    for side in ("side_a", "side_b"):  # R7, arc placement (H-053): a unit tagged `arc` = i lies on its side's arcs[i] ring; with one arc and no tags, every unit does
        arcs, rows = layout[side].get("arcs", []), layout[side]["units"]
        tagged = any("arc" in u for u in rows)
        for i, u in enumerate(rows):
            arc = arcs[u["arc"]] if "arc" in u and arcs else arcs[0] if len(arcs) == 1 and not tagged else None
            if arc is None:
                continue
            d = math.hypot(u["x"] - arc["centre"][0], u["y"] - arc["centre"][1])
            if abs(d - arc["radius"]) > rules["R7"]["tolerance"]:
                out.append(("R7", "arc placement: unit %d is %.1f wu from the centre, radius %g" % (i, d, arc["radius"])))
    return out


def check_layout(layout, presets, rules):
    """The rule ids violated, empty when valid. R1 to R7 only: R8 (reachability) needs the layout's orders and is the arena runner's (scripts/skilllab/arena/run.py)."""
    return sorted({r for r, _ in _violations(layout, presets, rules)})


# ---------------------------------------------------------------- geometry, in the holder-east frame (holder faces west, attacker faces east)

def _block(n, cx, cy, facing, cols=None, layer=0):
    cols = cols or max(1, math.ceil(math.sqrt(n)))
    c, s = math.cos(facing), math.sin(facing)
    out = []
    for i in range(n):
        r, k = divmod(i, cols)
        u, v = -r * PITCH, (k - (min(cols, n - r * cols) - 1) / 2) * PITCH
        out.append((cx + u * c - v * s, cy + u * s + v * c, facing, layer))
    return out


def _arc(n, fx, fy, centre_angle, spread, outward=False, layer=0, rmin=300.0):
    step = spread / n
    r = max(rmin, n * PITCH / spread)
    offs = sorted(range(n), key=lambda i: (abs(i - (n - 1) / 2), i))
    out = []
    for i in offs:
        a = centre_angle + (i - (n - 1) / 2) * step
        out.append((fx + r * math.cos(a), fy + r * math.sin(a), a if outward else a + math.pi, layer))
    return out


def _toward(x, y, tx, ty):
    return math.atan2(ty - y, tx - x)


def _split(n, fracs):
    out = [int(n * f) for f in fracs[:-1]]
    return out + [n - sum(out)]


def _chokepoint(W, H, nh, nt):
    return [_arc(nh, 0.5 * W, 0.5 * H, 0.0, 0.8 * math.pi)], [_block(nt, 0.25 * W, 0.5 * H, 0.0, cols=2)]


def _vantage(W, H, nh, nt):
    return [_block(nh, 0.68 * W, 0.45 * H, math.pi, layer=1)], [_block(nt, 0.28 * W, 0.55 * H, 0.0, cols=math.ceil(nt / 2))]


def _cover(W, H, nh, nt):
    holder = [_block(n, 0.66 * W, y * H, math.pi) for n, y in zip(_split(nh, [1 / 3, 1 / 3, 1 / 3]), (0.3, 0.5, 0.7))]
    return holder, [_block(nt, 0.25 * W, 0.5 * H, 0.0)]


def _objective(W, H, nh, nt):
    return [_block(nh, 0.66 * W, 0.5 * H, math.pi)], [_block(nt, 0.34 * W, 0.5 * H, 0.0)]


def _staging(W, H, nh, nt):
    return ([_block(nh, 0.88 * W, 0.88 * H, _toward(0.88 * W, 0.88 * H, 0.12 * W, 0.12 * H))],
            [_block(nt, 0.12 * W, 0.12 * H, _toward(0.12 * W, 0.12 * H, 0.88 * W, 0.88 * H))])


def _transit(W, H, nh, nt):
    return ([_block(nh, 0.55 * W, 0.8 * H, _toward(0.55 * W, 0.8 * H, 0.4 * W, 0.5 * H))], [_block(nt, 0.3 * W, 0.5 * H, 0.0, cols=3)])


def _flank_route(W, H, nh, nt):
    main, flank = _split(nt, [0.6, 0.4])
    return ([_block(nh, 0.7 * W, 0.5 * H, math.pi)],
            [_block(main, 0.25 * W, 0.5 * H, 0.0), _block(flank, 0.5 * W, 0.12 * H, _toward(0.5 * W, 0.12 * H, 0.7 * W, 0.5 * H))])


def _hazard_anchor(W, H, nh, nt):
    return [_arc(nh, 0.72 * W, 0.5 * H, 0.0, 2 * math.pi, outward=True)], [_block(nt, 0.3 * W, 0.5 * H, 0.0)]


def _slope(W, H, nh, nt):
    front, rear = _split(nh, [0.5, 0.5])
    return ([_block(front, 0.62 * W, 0.5 * H, math.pi, cols=front, layer=1), _block(rear, 0.7 * W, 0.5 * H, math.pi, cols=rear, layer=2)],
            [_block(nt, 0.3 * W, 0.5 * H, 0.0)])


def _city(W, H, nh, nt):
    spots = [(0.6, 0.35, 0), (0.6, 0.65, 1), (0.75, 0.35, 1), (0.75, 0.65, 2)]
    holder = [_block(n, fx * W, fy * H, math.pi, layer=lay) for n, (fx, fy, lay) in zip(_split(nh, [0.25] * 4), spots)]
    return holder, [_block(nt, 0.25 * W, 0.5 * H, 0.0)]


def _trap(W, H, nh, nt):
    bait, wing1, wing2 = _split(nh, [0.25, 0.375, 0.375])
    bx, by = 0.45 * W, 0.5 * H
    return ([_block(bait, bx, by, math.pi), _block(wing1, 0.62 * W, 0.3 * H, _toward(0.62 * W, 0.3 * H, bx, by)),
             _block(wing2, 0.62 * W, 0.7 * H, _toward(0.62 * W, 0.7 * H, bx, by))], [_block(nt, 0.2 * W, 0.5 * H, 0.0)])


def _open_field(W, H, nh, nt):
    return [_block(nh, 0.75 * W, 0.5 * H, math.pi)], [_block(nt, 0.25 * W, 0.5 * H, 0.0)]


# situation -> (preset, who holds the positional edge, builder, the reason in a sentence; {h} holder letter, {t} other side letter)
# DRAFT-situation-recipes: placements, presets and edges are Architect drafts for the first review page.
RECIPES = {
    "chokepoint": ("small_flat", "holder", _chokepoint, "Side {h} holds the arc around the choke and side {t} must come through it in two files, so position outweighs numbers."),
    "vantage": ("small_tiered", "holder", _vantage, "Side {h} stands on the layer above side {t} and sees down onto it, so position outweighs numbers."),
    "cover": ("small_flat", "holder", _cover, "Side {h} sits in three separated clusters and side {t} is one mass in the open, so position outweighs numbers."),
    "objective": ("small_flat", "none", _objective, ""),
    "staging": ("small_flat", "none", _staging, ""),
    "transit": ("small_flat", "holder", _transit, "Side {h} waits off the flank of side {t}'s marching column, so the one at rest outweighs numbers."),
    "flank_route": ("large_tiered", "attacker", _flank_route, "Side {t} sends part of its force round the long way onto side {h}'s flank, so position outweighs numbers."),
    "hazard_anchor": ("small_flat", "holder", _hazard_anchor, "Side {h} stands as a ring that cannot be flanked and side {t} has one front to push, so position outweighs numbers."),
    "slope": ("small_tiered", "holder", _slope, "Side {h} holds two terraces above side {t} and fires down from both, so position outweighs numbers."),
    "city": ("large_tiered", "holder", _city, "Side {h} holds four separate clusters on three layers and side {t} is one mass among them, so position outweighs numbers."),
    "trap": ("small_flat", "holder", _trap, "Side {h} shows a small bait and keeps two wings on either side of it, so the ambush outweighs numbers."),
    "open_field": ("large_flat", "none", _open_field, ""),
}


# ---------------------------------------------------------------- one layout

@functools.cache
def _roster_ranges():
    """{role: attack range in world units} from the sim roster, read through scripts/skilllab/engine.py (om_unit_profile_attack_range) at produce time."""
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(1)
    try:
        return {r: float(e.type_stats(w, e.type_id(r))["attack_range"]) for r in rules()["R5"]["roles"]}
    finally:
        e.free_world(w)


def _round_unit(x, y, f, layer, role):
    return {"role": role, "x": round(float(x), 2), "y": round(float(y), 2), "facing": round(float(f), 4), "layer": int(layer), "range": _roster_ranges()[role]}


def _roles(group, mix):
    chunk = math.ceil(len(group) / len(mix))
    return [mix[min(i // chunk, len(mix) - 1)] for i in range(len(group))]


def _predict(kind, edge, holder, na, nb, template):
    """(prediction, one sentence). Positioning decides unless outnumbered more than EDGE_OUTNUMBER to one."""
    n = {"A": na, "B": nb}
    other = "B" if holder == "A" else "A"
    if edge == "none":
        if na == nb:
            return "draw", "Neither side holds a positional edge in %s and the numbers are even." % kind
        big = "A" if na > nb else "B"
        return big, "Neither side holds a positional edge in %s, so side %s wins on numbers." % (kind, big)
    edge_side = holder if edge == "holder" else other
    why = template.format(h=holder, t=other)
    low = "B" if edge_side == "A" else "A"
    if n[low] > EDGE_OUTNUMBER * n[edge_side]:
        return low, "Side %s outnumbers the side with the %s edge by more than %d to one." % (low, kind.replace("_", " "), EDGE_OUTNUMBER)
    return edge_side, why


def _layout(kind, na, nb, seed, presets):
    rng = random.Random(seed)
    preset_name, edge, builder, _ = RECIPES[kind]
    p = presets[preset_name]
    holder = rng.choice(["A", "B"])
    nh, nt = (na, nb) if holder == "A" else (nb, na)
    holder_groups, attacker_groups = builder(float(p["width"]), float(p["height"]), nh, nt)
    sides = {}
    for letter, groups in (("A", holder_groups if holder == "A" else attacker_groups), ("B", holder_groups if holder == "B" else attacker_groups)):
        mix = rng.choice(MIXES)
        units = []
        for g in groups:
            for (x, y, f, lay), role in zip(g, _roles(g, mix)):
                if holder == "A":  # the frames are built holder-east; the holder on side A mirrors west
                    x, f = p["width"] - x, math.atan2(math.sin(math.pi - f), math.cos(math.pi - f))
                units.append(_round_unit(x, y, f, lay, role))
        sides[letter] = {"headcount": len(units), "units": units}
    predict, why = _predict(kind, edge, holder, na, nb, RECIPES[kind][3])
    return {"id": "", "situation": kind, "landscape": preset_name, "seed": seed, "predict": predict, "predict_why": why, "verdict": "", "feedback": "",
            "defender": holder, "side_a": sides["A"], "side_b": sides["B"]}


# ---------------------------------------------------------------- batch two (H-025 round two): recipes with landscape features

# DRAFT-batch2-headcounts (A:B), in the order of DRAFT-situation-kinds
B2_PAIRS = dict(zip(SITUATIONS, [(16, 32), (24, 24), (8, 8), (32, 32), (8, 64), (64, 8), (48, 12), (12, 48), (40, 56), (64, 64), (16, 16), (32, 16)]))
WALL_THICKNESS = 200  # DRAFT-wall-thickness, wu
STAGING_SIZE = 600  # DRAFT-staging-size, wu
SLOPE_WIDTH = 200  # DRAFT-slope-width, wu
CITY_PITCH = 250  # DRAFT-city-pitch, wu
RIDGE_W = 300  # DRAFT-ridge-w, wu
RIDGE_H = 1400  # DRAFT-ridge-h, wu
MOUTH = round(math.pi / 2, 6)  # the trap's open side is +y; the pocket is written as axis-aligned rectangles, never a rotation field


def _grid(n, cx, cy, facing):
    """A side's block, centred on (cx, cy): rows = ceil(sqrt(n)) along the facing, pitch PITCH, the last row left-aligned. [(x, y, facing)]."""
    rows = math.ceil(math.sqrt(n))
    cols = math.ceil(n / rows)
    c, s = math.cos(facing), math.sin(facing)
    out = []
    for i in range(n):
        r, k = divmod(i, cols)
        fwd, lat = ((rows - 1) / 2 - r) * PITCH, (k - (cols - 1) / 2) * PITCH
        out.append((cx + fwd * c - lat * s, cy + fwd * s + lat * c, facing))
    return out


def _rect(x, y, w, h):
    return {"x": round(float(x), 2), "y": round(float(y), 2), "w": w, "h": h}


def _feature(kind, x, y, **geometry):
    return dict({"kind": kind, "x": round(float(x), 2), "y": round(float(y), 2)}, **geometry)


# Each recipe: (cx, cy) the land's centre -> (feature or None, defender block, attacker block); a block is (cx, cy, facing).
# The defender stands on or behind the feature, the attacker approaches from the mouth or the far side; open_field has no feature, defender block = side A.
def _b2_chokepoint(cx, cy):
    gap, radius, h = 200, 600, 500  # h = radius - gap / 2
    off = gap / 2 + h / 2
    f = _feature("chokepoint", cx, cy, gap=gap, radius=radius, walls=[_rect(cx, cy - off, WALL_THICKNESS, h), _rect(cx, cy + off, WALL_THICKNESS, h)])
    return f, (cx + 500, cy, math.pi), (cx - 900, cy, 0.0)


def _b2_vantage(cx, cy):
    return _feature("vantage", cx, cy, radius=700, height_band=1), (cx + 100, cy, math.pi), (cx - 1100, cy, 0.0)


def _b2_cover(cx, cy):
    boxes = [_rect(cx - 50, cy + dy, 120, 60) for dy in (-200, 0, 200)]  # centres within DRAFT-cover-spread 300 of the feature centre
    return _feature("cover", cx, cy, boxes=boxes), (cx + 250, cy, math.pi), (cx - 1000, cy, 0.0)


def _b2_objective(cx, cy):
    return _feature("objective", cx, cy, radius=300), (cx, cy, math.pi), (cx - 1000, cy, 0.0)


def _b2_staging(cx, cy):
    return _feature("staging", cx + 1000, cy, size=STAGING_SIZE), (cx + 1000, cy, math.pi), (cx - 1000, cy, 0.0)


def _b2_transit(cx, cy):
    pts = [[round(cx - 1300, 2), round(cy, 2)], [round(cx - 300, 2), round(cy, 2)], [round(cx + 700, 2), round(cy, 2)]]
    f = _feature("transit", cx - 1300, cy, points=pts, dest={"x": pts[-1][0], "y": pts[-1][1]})
    return f, (cx - 300, cy + 800, -math.pi / 2), (cx - 1300, cy, 0.0)


def _b2_flank_route(cx, cy):
    pts = [[round(cx + dx, 2), round(cy + dy, 2)] for dx, dy in ((-1100, 0), (-500, 1200), (700, 1300), (1000, 500))]
    ridge = _rect((cx - 1100 + cx + 1000) / 2, cy, RIDGE_W, RIDGE_H)  # centred between the sides on the direct line; the route goes round its +y end
    return _feature("flank_route", cx - 1100, cy, points=pts, ridge=ridge, height_band=1), (cx + 1000, cy, math.pi), (cx - 1100, cy, 0.0)


def _b2_hazard_anchor(cx, cy):
    return _feature("hazard_anchor", cx + 300, cy, radius=500), (cx + 1100, cy, math.pi), (cx - 1100, cy, 0.0)


def _b2_slope(cx, cy):
    f = _feature("slope", cx, cy, length=600, width=SLOPE_WIDTH, heading=0.0, from_band=0, to_band=1)
    return f, (cx + 600, cy, math.pi), (cx - 900, cy, 0.0)


def _b2_city(cx, cy):
    buildings = [_rect(cx + i * CITY_PITCH, cy + j * CITY_PITCH, 100, 100) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return _feature("city", cx, cy, radius=400, buildings=buildings), (cx + 600, cy, math.pi), (cx - 900, cy, 0.0)


def _b2_trap(cx, cy):
    walls = [_rect(cx - 400, cy, 200, 800), _rect(cx + 400, cy, 200, 800), _rect(cx, cy - 500, 1000, 200)]  # a U about the centre, open on the +y side
    return _feature("trap", cx, cy, mouth=MOUTH, walls=walls), (cx, cy, MOUTH), (cx, cy + 1400, -math.pi / 2)


def _b2_open_field(cx, cy):
    return None, (cx - 800, cy, 0.0), (cx + 800, cy, math.pi)


# situation -> (preset, who holds the positional edge, builder, the reason in a sentence naming the feature; {h} defender letter, {t} other side letter)
# DRAFT-situation-recipes: placements and edges are Architect drafts for the review page.
RECIPES2 = {
    "chokepoint": ("small_flat", "holder", _b2_chokepoint, "Side {h} holds the chokepoint walls and side {t} must funnel through the narrow gap, so position outweighs numbers."),
    "vantage": ("small_tiered", "holder", _b2_vantage, "Side {h} stands on the vantage rise above side {t} and sees down onto it, so position outweighs numbers."),
    "cover": ("small_flat", "holder", _b2_cover, "Side {h} shoots from behind the cover boxes at side {t} crossing open ground, so position outweighs numbers."),
    "objective": ("small_flat", "none", _b2_objective, ""),
    "staging": ("small_flat", "none", _b2_staging, ""),
    "transit": ("small_flat", "holder", _b2_transit, "Side {h} waits off the flank of side {t}'s transit column, so the one at rest outweighs numbers."),
    "flank_route": ("small_tiered", "attacker", _b2_flank_route, "Side {t} swings round the flank route onto side {h}'s flank, so position outweighs numbers."),
    "hazard_anchor": ("small_flat", "holder", _b2_hazard_anchor, "Side {h} sits behind the hazard anchor and side {t} must go round it, so position outweighs numbers."),
    "slope": ("small_tiered", "holder", _b2_slope, "Side {h} holds the top of the slope and fires down it at side {t}, so position outweighs numbers."),
    "city": ("small_flat", "holder", _b2_city, "Side {h} holds the ground behind the city buildings and side {t} must cross open ground to reach it, so position outweighs numbers."),
    "trap": ("small_flat", "holder", _b2_trap, "Side {h} waits inside the trap pocket and side {t} must enter by its one mouth, so the ambush outweighs numbers."),
    "open_field": ("small_flat", "none", _b2_open_field, ""),
}


def _layer2(kind, feat, x, y, is_defender):
    """R-001-07: one walkable layer at a point. Vantage: inside the disc is its height_band, outside is 0 (ruling 2); slope: the defender stands on the upper band."""
    if kind == "vantage":
        return feat["height_band"] if math.hypot(x - feat["x"], y - feat["y"]) < feat["radius"] else 0
    return feat["to_band"] if kind == "slope" and is_defender else 0


def _layout2(kind, na, nb, seed, presets):
    rng = random.Random(seed)
    preset_name, edge, builder, template = RECIPES2[kind]
    p = presets[preset_name]
    feat, dblock, ablock = builder(p["width"] / 2, p["height"] / 2)
    if kind == "open_field":
        defender = ""
    elif kind == "chokepoint":  # the holder is the smaller side, which is the point of the situation
        defender = "A" if na < nb else "B" if nb < na else rng.choice(["A", "B"])
    else:
        defender = rng.choice(["A", "B"])
    sides = {}
    for letter, n in (("A", na), ("B", nb)):
        is_def = letter == defender or (kind == "open_field" and letter == "A")
        mix = rng.choice(MIXES)
        grid = _grid(n, *(dblock if is_def else ablock))
        units = []
        for (x, y, f), role in zip(grid, _roles(grid, mix)):
            x, y = round(x, 2), round(y, 2)
            units.append(_round_unit(x, y, f, _layer2(kind, feat, x, y, letter == defender), role))
        sides[letter] = {"headcount": len(units), "units": units}
    if kind == "open_field":
        predict, why = _predict(kind, edge, "A", na, nb, template)
    else:
        predict, why = _predict(kind, edge, defender, na, nb, template)
    layout = {"id": "", "situation": kind, "landscape": preset_name, "seed": seed, "predict": predict, "predict_why": why, "verdict": "", "feedback": "",
              "defender": defender, "side_a": sides["A"], "side_b": sides["B"]}
    if feat is not None:
        layout["features"] = [feat]
    return layout


def _plant(layout, rule, presets):
    """Layouts that break one rule on purpose (the positive control); R6 plants two mutations."""
    d = copy.deepcopy(layout)
    a = d["side_a"]["units"]
    if rule == "R1":
        a[0]["x"] = 1.0e9
    elif rule == "R2":
        a[1]["x"], a[1]["y"] = a[0]["x"], a[0]["y"]
    elif rule == "R3":
        a[0]["layer"] = presets[d["landscape"]]["layers"]
    elif rule == "R4":
        d["side_a"]["headcount"] += 1
    elif rule == "R5":
        a[0]["role"] = "Wizard"
    elif rule == "R6":
        swapped = copy.deepcopy(d)
        for f in swapped["features"]:
            f["kind"] = "vantage" if f["kind"] != "vantage" else "cover"
        d.pop("features")
        return [d, swapped]
    return [d]


# ---------------------------------------------------------------- files

def _q(s):
    return json.dumps(s)


def _tv(v):
    """A TOML value for a bool, number, string, list or inline table."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return _q(v)
    if isinstance(v, list):
        return "[" + ", ".join(_tv(i) for i in v) + "]"
    return "{" + ", ".join("%s = %s" % (k, _tv(x)) for k, x in v.items()) + "}"


def dump_toml(layout):
    lines = ["id = %s" % _q(layout["id"]), "situation = %s" % _q(layout["situation"]), "landscape = %s" % _q(layout["landscape"]),
             "seed = %d" % layout["seed"], "predict = %s" % _q(layout["predict"]), "predict_why = %s" % _q(layout["predict_why"]),
             "verdict = %s" % _q(layout["verdict"]), "feedback = %s" % _q(layout["feedback"]), "defender = %s" % _q(layout.get("defender", ""))]
    if "predict_rate" in layout:  # H-053: P(side A wins), 0 to 1
        lines.append("predict_rate = %r" % float(layout["predict_rate"]))
    if "orders_point" in layout:  # H-053: absent means the midpoint
        lines.append("orders_point = %s" % _tv([float(c) for c in layout["orders_point"]]))
    lines += ["%s = %s" % (k, _q(layout[k])) for k in ("what_to_expect", "approve_means", "deny_means") if k in layout]  # H-053 page text
    if "orders" in layout:  # H-052: "both_same_point" or "hold:A" / "hold:B"; absent means both_same_point
        lines.append("orders = %s" % _q(layout["orders"]))
    for side in ("side_a", "side_b"):
        lines += ["", "[%s]" % side, "headcount = %d" % layout[side]["headcount"]]
        for a in layout[side].get("arcs", []):  # H-053, one entry per arc row
            lines += ["", "[[%s.arcs]]" % side, "centre = %s" % _tv([float(c) for c in a["centre"]]), "radius = %r" % float(a["radius"]),
                      "start_deg = %r" % float(a["start_deg"]), "end_deg = %r" % float(a["end_deg"])]
            if "count" in a:
                lines.append("count = %d" % a["count"])
        for u in layout[side]["units"]:
            lines += ["", "[[%s.units]]" % side, "role = %s" % _q(u["role"]), "x = %r" % u["x"], "y = %r" % u["y"], "facing = %r" % u["facing"],
                      "layer = %d" % u["layer"]] + (["range = %r" % u["range"]] if "range" in u else [])  # a round-one row has no range, and none is invented
            if "arc" in u:   # H-053: which of the side's arcs the unit sits on
                lines.append("arc = %d" % u["arc"])
            if "group" in u:   # stage 4 fix F3: the unit's order group (scripts/skilllab/arena/groups.py)
                lines.append("group = %s" % _q(u["group"]))
    for g in layout.get("order_groups", []):   # stage 4 fix F3: one row per group order, with an optional release trigger
        lines += ["", "[[order_groups]]"] + ["%s = %s" % (k, _tv(v)) for k, v in g.items()]
    for f in layout.get("features", []):
        lines += ["", "[[features]]"] + ["%s = %s" % (k, _tv(v)) for k, v in f.items()]
    return "\n".join(lines) + "\n"


def write_layout(layout, out):
    """Write <id>.toml and <id>.json beside each other; the TOML path."""
    layout.setdefault("defender", "")  # a round-one file has none
    toml_path = Path(out) / (layout["id"] + ".toml")
    toml_path.write_text(dump_toml(layout))
    toml_path.with_suffix(".json").write_text(json.dumps(layout, indent=2) + "\n")
    return toml_path


def _next_number(out):
    nums = [int(m.group(1)) for p in Path(out).glob("L-*.toml") if (m := re.fullmatch(r"L-(\d{4})", p.stem))]
    return max(nums, default=0) + 1


def _run(jobs, seed, out, plant=None, batch="two"):
    """jobs: [(situation, headcount A, headcount B)]. (paths written, layouts rejected). REJECT lines go to stderr."""
    pre, rul = presets(), rules()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    number = _next_number(out)
    build = _layout2 if batch == "two" else _layout
    built = [build(kind, na, nb, seed * 1_000_003 + SITUATIONS.index(kind) * 10_007 + na * 101 + nb, pre) for kind, na, nb in jobs]
    if plant and built:
        source = next((l for l in built if l["situation"] != "open_field"), built[0])
        built += _plant(source, plant, pre)
    written, rejected = [], 0
    for layout in built:
        layout["id"] = "L-%04d" % number
        number += 1
        bad = _violations(layout, pre, rul)
        for rule, detail in bad:
            print("REJECT %s %s %s" % (layout["id"], rule, detail), file=sys.stderr)
        if bad:
            rejected += 1
        else:
            written.append(write_layout(layout, out))
    return written, rejected


def produce(situations, pairs, seed, out):
    """One layout per situation per pair (batch two recipes), deterministic from the seed; the TOML paths written."""
    return _run([(k, na, nb) for k in situations for na, nb in pairs], seed, out)[0]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.catalogue.produce")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--batch", choices=["one", "two"], default="two", help="two (default): the round-two recipes; one: round one, kept for history")
    ap.add_argument("--situations", help="comma list or all (default all)")
    ap.add_argument("--pairs", help='e.g. "16:32,24:24" (default: batch two\'s pair for each situation, batch one\'s three pairs)')
    ap.add_argument("--plant", choices=PLANT_RULES, help="also emit layouts that break this rule (the positive control)")
    a = ap.parse_args(argv)
    situations = SITUATIONS if a.situations in (None, "all") else a.situations.split(",")
    unknown = [s for s in situations if s not in SITUATIONS]
    if unknown:
        ap.error("unknown situation kinds: %s" % unknown)
    if a.pairs:
        pairs = [tuple(int(v) for v in p.split(":")) for p in a.pairs.split(",")]
        jobs = [(k, na, nb) for k in situations for na, nb in pairs]
    elif a.batch == "two":
        jobs = [(k,) + B2_PAIRS[k] for k in situations]
    else:
        jobs = [(k, na, nb) for k in situations for na, nb in ONE_PAIRS]
    _, rejected = _run(jobs, a.seed, a.out, a.plant, a.batch)
    return 2 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
