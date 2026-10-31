"""H-025 layout catalogue producer: mass-produces layouts from the recorded rules (rules.toml) on the stage presets (presets.toml).

CLI: python3 -m scripts.skilllab.catalogue.produce --out <dir> --situations <comma list or all> --pairs <"16:16,16:32,32:16"> --seed <int> [--plant <rule id>]
Every number here that the story does not give is a named DRAFT; Westley rules. Nothing is deduced from a produced layout (DEC-lab-placeholders-no-deductions-2026-10-30).
"""
import argparse
import copy
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
PLANT_RULES = ["R1", "R2", "R3", "R4", "R5"]


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
    return out


def check_layout(layout, presets, rules):
    """The rule ids violated, empty when valid."""
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

def _round_unit(x, y, f, layer, role):
    return {"role": role, "x": round(float(x), 2), "y": round(float(y), 2), "facing": round(float(f), 4), "layer": int(layer)}


def _roles(group, mix):
    chunk = math.ceil(len(group) / len(mix))
    return [mix[min(i // chunk, len(mix) - 1)] for i in range(len(group))]


def _predict(kind, edge, holder, na, nb):
    """(prediction, one sentence). Positioning decides unless outnumbered more than EDGE_OUTNUMBER to one."""
    n = {"A": na, "B": nb}
    other = "B" if holder == "A" else "A"
    if edge == "none":
        if na == nb:
            return "draw", "Neither side holds a positional edge in %s and the numbers are even." % kind
        big = "A" if na > nb else "B"
        return big, "Neither side holds a positional edge in %s, so side %s wins on numbers." % (kind, big)
    edge_side = holder if edge == "holder" else other
    why = RECIPES[kind][3].format(h=holder, t=other)
    low = "B" if edge_side == "A" else "A"
    if n[low] > EDGE_OUTNUMBER * n[edge_side]:
        return low, "Side %s outnumbers the side with the edge by more than %d to one." % (low, EDGE_OUTNUMBER)
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
    predict, why = _predict(kind, edge, holder, na, nb)
    return {"id": "", "situation": kind, "landscape": preset_name, "seed": seed, "predict": predict, "predict_why": why, "verdict": "", "feedback": "",
            "side_a": sides["A"], "side_b": sides["B"]}


def _plant(layout, rule, presets):
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
    return d


# ---------------------------------------------------------------- files

def _q(s):
    return json.dumps(s)


def dump_toml(layout):
    lines = ["id = %s" % _q(layout["id"]), "situation = %s" % _q(layout["situation"]), "landscape = %s" % _q(layout["landscape"]),
             "seed = %d" % layout["seed"], "predict = %s" % _q(layout["predict"]), "predict_why = %s" % _q(layout["predict_why"]),
             "verdict = %s" % _q(layout["verdict"]), "feedback = %s" % _q(layout["feedback"])]
    for side in ("side_a", "side_b"):
        lines += ["", "[%s]" % side, "headcount = %d" % layout[side]["headcount"]]
        for u in layout[side]["units"]:
            lines += ["", "[[%s.units]]" % side, "role = %s" % _q(u["role"]), "x = %r" % u["x"], "y = %r" % u["y"], "facing = %r" % u["facing"],
                      "layer = %d" % u["layer"]]
    return "\n".join(lines) + "\n"


def write_layout(layout, out):
    """Write <id>.toml and <id>.json beside each other; the TOML path."""
    toml_path = Path(out) / (layout["id"] + ".toml")
    toml_path.write_text(dump_toml(layout))
    toml_path.with_suffix(".json").write_text(json.dumps(layout, indent=2) + "\n")
    return toml_path


def _next_number(out):
    nums = [int(m.group(1)) for p in Path(out).glob("L-*.toml") if (m := re.fullmatch(r"L-(\d{4})", p.stem))]
    return max(nums, default=0) + 1


def _run(situations, pairs, seed, out, plant=None):
    """(paths written, layouts rejected). REJECT lines go to stderr."""
    pre, rul = presets(), rules()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    number = _next_number(out)
    built = [_layout(kind, na, nb, seed * 1_000_003 + SITUATIONS.index(kind) * 10_007 + na * 101 + nb, pre) for kind in situations for na, nb in pairs]
    if plant and built:
        built.append(_plant(built[0], plant, pre))
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
    """One layout per situation per pair, deterministic from the seed; the TOML paths written."""
    return _run(situations, pairs, seed, out)[0]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.catalogue.produce")
    ap.add_argument("--out", required=True)
    ap.add_argument("--situations", required=True, help="comma list or all")
    ap.add_argument("--pairs", required=True, help='e.g. "16:16,16:32,32:16"')
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--plant", choices=PLANT_RULES, help="also emit one layout that breaks this rule (the positive control)")
    a = ap.parse_args(argv)
    situations = SITUATIONS if a.situations == "all" else a.situations.split(",")
    unknown = [s for s in situations if s not in SITUATIONS]
    if unknown:
        ap.error("unknown situation kinds: %s" % unknown)
    pairs = [tuple(int(v) for v in p.split(":")) for p in a.pairs.split(",")]
    _, rejected = _run(situations, pairs, a.seed, a.out, a.plant)
    return 2 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
