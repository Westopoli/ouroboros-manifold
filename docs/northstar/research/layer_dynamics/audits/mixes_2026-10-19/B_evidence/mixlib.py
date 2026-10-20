"""Analyst B helpers: same-mix scenes on the real engine through the lab's own fight() (read-only use of scripts/skilllab)."""
import math, sys, json, time, collections
sys.path.insert(0, "/home/westopoli/Projects/om-push/wt/mixB")
from scripts.skilllab.contract import Group, Setup
from scripts.skilllab import plays_space, pool, scan as scan_mod

REACH = {"Raider": (1, 1), "Interceptor": (2, 1), "Bombard": (0, 2), "Bastion": (0, 2)}  # E-01 R-164-01; Line types (0,0) builtin

def types_for(mix):
    # Vanguard and Warden stay builtin (reach 0,0 = Line reach; Warden keeps its aura only as builtin type 3)
    return {n: {"base": n, "reach": REACH[n]} for n, _ in mix if n in REACH}

def scale(mix, heads):
    total = sum(c for _, c in mix)
    want = [c * heads / total for _, c in mix]
    counts = [max(1, int(w)) for w in want]
    while sum(counts) < heads:
        i = max(range(len(want)), key=lambda i: want[i] - counts[i]); counts[i] += 1
    while sum(counts) > heads:
        i = min((i for i in range(len(want)) if counts[i] > 1), key=lambda i: want[i] - counts[i]); counts[i] -= 1
    return [(n, c) for (n, _), c in zip(mix, counts)]

def blob(side, unit, n, x, y=0.0, layer=0, order="attack_move"):
    return Group(side=side, unit=unit, count=n, formation="blob", x=x, y=y, facing_deg=0.0 if side == 0 else 180.0,
                 layer=layer, order=order, params={"radius": 80 + 12 * math.sqrt(n)})

def line(side, unit, n, x, y=0.0, layer=0, spacing=30.0, order="attack_move"):
    return Group(side=side, unit=unit, count=n, formation="line", x=x, y=y, facing_deg=0.0 if side == 0 else 180.0,
                 layer=layer, order=order, params={"spacing": spacing})

GAP = 900.0

def naive_side1(mix, heads, layer=0):
    return [blob(1, u, c, GAP / 2, layer=layer) for u, c in scale(mix, heads)]

def build_naive(mix, settings=None):
    def build(enemy_heads, swap):
        g0 = [blob(0, u, c, -GAP / 2) for u, c in mix]
        return Setup(groups=tuple(g0 + naive_side1(mix, enemy_heads)), unit_types=types_for(mix), point=(0.0, 0.0),
                     settings=dict(settings or {}))
    return build

def build_custom(mix, side0_fn, settings=None, enemy_layer=0):
    """side0_fn(mix) -> list of side-0 Groups (16 units, same mix); side 1 is the naive blob per type on enemy_layer."""
    def build(enemy_heads, swap):
        return Setup(groups=tuple(side0_fn(mix) + naive_side1(mix, enemy_heads, enemy_layer)), unit_types=types_for(mix),
                     point=(0.0, 0.0), settings=dict(settings or {}))
    return build

def summarize(fights):
    oc = collections.Counter(f.outcome for f in fights)
    ag = collections.Counter(f.agreement for f in fights)
    return {"outcomes": dict(oc), "agreement": dict(ag), "mean_ticks": round(sum(f.ticks for f in fights) / len(fights)),
            "mean_margin": round(sum(f.margin for f in fights) / len(fights), 3),
            "win0": oc.get("side0", 0), "n": len(fights)}
