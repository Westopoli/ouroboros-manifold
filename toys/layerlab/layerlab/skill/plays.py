"""Stage 3 K2: plays and composition (SPEC.md 14.3).

Each of the five slots (where, shape, layer, info, matchup) has a naive default and a skilled override; the 32
combinations are `compose` with each subset. Only S3 reads the information in K2 (the route feeds no slot yet).
"""
import copy
import itertools
import math
import statistics
from dataclasses import dataclass, field

from .. import ffi, formations, scenario, terrain
from . import situation
from .cost import counts_for_heads
from .rstar import rstar as _rstar, rstar_windows

SKILLS = ("S1", "S2", "S3", "S4", "S5")
SLOT = {"S1": "where", "S2": "shape", "S3": "layer", "S4": "info", "S5": "matchup"}

_ROSTER = situation.ROSTER
_BEATS = {"strike": "siege", "line": "strike", "siege": "line"}
_ACROSS = 20                    # units across a line abreast (1000 world units at spacing 50)
_BLOB_COLS = 5
_ARC = 80.0                     # S2 concave arc, degrees
_STANDOFF = 1.5                 # S1 barrier and block: weapon ranges from the feature
_COVER_GAP = 60.0               # S1 cover: past the disc edge
_PLATEAU_BEYOND = 300.0         # S1 ramp_defense: past the slope's top edge
_LANE_INSET = 25.0              # S1 lane: inside the exit end
_EDGE_STEP = 50.0
_EDGE_TRIES = 40
_ARENA_MARGIN = 100.0
_BIAS_FLAG = 0.15               # SPEC 14.2: side_bias above this flags a situation
_FLIP = {"A": "B", "B": "A"}

_LEVER = {"LA": (1.0, 1.0), "LB": (0.8, 1.0), "LC": (0.8, 0.8)}   # (range up, damage up) per layer (README 6.3)


# ---- lever configurations (moved from experiments/configs.py) -----------------------------------

def _table(up, down=1.0):
    t = [0.0] * 9
    t[4] = 1.0
    for k in range(1, 5):
        t[4 + k] = up ** k          # target k layers above the shooter
        t[4 - k] = down ** k        # target k layers below the shooter
    return t


def apply_config(scn, cfg):
    """LA vision only; LB adds a range penalty firing up (0.8 per layer); LC adds a damage penalty (0.8).
    See also: experiments/configs.py, the original tables (kept working, not edited)."""
    if cfg not in _LEVER:
        raise ValueError(cfg)
    ru, d = _LEVER[cfg]
    rng, dmg = _table(ru), _table(d)
    s = scenario.set_path(scn, "rules.range_mult", rng)
    s = scenario.set_path(s, "rules.dmg_mult", dmg)
    return scenario.set_path(s, "rules.aoe_layer_mult", dmg)


def all_combinations():
    return [frozenset(c) for n in range(len(SKILLS) + 1) for c in itertools.combinations(SKILLS, n)]


# ---- geometry helpers ---------------------------------------------------------------------------

def _spacing(sit):
    return max(50.0, situation.min_spacing(sit.jitter))


def _anchor(sit, side):
    return tuple(sit.anchor_A if side == 0 else sit.anchor_B)


def _facing(sit, side):
    return sit.facing_A if side == 0 else sit.facing_B


def _bearing(src, dst):
    return math.degrees(math.atan2(dst[1] - src[1], dst[0] - src[0]))


def _back(f_deg):
    r = math.radians(f_deg)
    return (-math.cos(r), -math.sin(r))


def _lateral_axis(sit):
    """Unit vector across the approach (anchor A to anchor B rotated +90), the same for both sides."""
    ax, ay = sit.anchor_A
    bx, by = sit.anchor_B
    d = math.hypot(bx - ax, by - ay)
    return (-(by - ay) / d, (bx - ax) / d)


def _type_order(counts):
    return sorted((t for t, n in counts.items() if n > 0),
                  key=lambda t: (_ROSTER.index(t) if t in _ROSTER else len(_ROSTER), t))


def _type_def(base, name):
    return {**base.get("type_defaults", {}), **base["types"][name]}


def _min_range(base, counts):
    return min(float(_type_def(base, t)["range"]) for t in counts if counts[t] > 0)


def _evenly(n, cap):
    ranks = -(-n // cap)
    return [n // ranks + (1 if r < n % ranks else 0) for r in range(ranks)]


def _line_rows(n, p0, f_deg, sp, across):
    """A line abreast in ranks: at most `across` units in a rank, further ranks `sp` behind, away from the enemy."""
    back = _back(f_deg)
    rows = []
    for r, m in enumerate(_evenly(n, across)):
        c = (p0[0] + back[0] * sp * r, p0[1] + back[1] * sp * r)
        pts = [(x, y) for x, y, _ in formations.place("line", m, c[0], c[1], f_deg, sp)]
        rows.append({"kind": "line", "n": m, "c": c, "f": f_deg, "sp": sp, "pts": pts})
    return rows


def _concave_rows(n, center, axis_deg, r0, sp, arc):
    """Concave rows around `center`, each spanning `arc` degrees centred on `axis_deg`; ranks at +sp radius."""
    cap = int(arc / math.degrees(2.0 * math.asin(sp / (2.0 * r0))) + 1e-9) + 1
    sizes = _evenly(n, cap)
    first = sizes[0]
    g0 = r0 / 2.0
    if first > 1:
        g0 = max(g0, (sp / 2.0) / math.sin(math.radians(arc / (first - 1)) / 2.0))
    g0 = min(g0, r0 - sp / 2.0)
    rows = []
    for r, m in enumerate(sizes):
        radius, goal_radius = r0 + sp * r, g0 + sp * r
        angles = [axis_deg] if m == 1 else [axis_deg - arc / 2.0 + k * arc / (m - 1) for k in range(m)]
        cs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in angles]
        rows.append({
            "kind": "concave", "n": m, "arc": arc, "center": center, "R": radius, "angles": angles,
            "pts": [(round(center[0] + radius * c, 6), round(center[1] + radius * s, 6)) for c, s in cs],
            "goals": [[round(center[0] + goal_radius * c, 6), round(center[1] + goal_radius * s, 6)]
                      for c, s in cs],
        })
    return rows


def _assign(rows, order, counts, lat):
    """Deal the types, in `order`, along the force's lateral axis: each type holds a contiguous band."""
    slots = sorted(((round(x * lat[0] + y * lat[1], 3), ri, i)
                    for ri, row in enumerate(rows) for i, (x, y) in enumerate(row["pts"])))
    seq = [t for t in order for _ in range(counts[t])]
    for row in rows:
        row["types"] = [None] * row["n"]
    for (_, ri, i), t in zip(slots, seq):
        rows[ri]["types"][i] = t


def _runs(types):
    out, start = [], 0
    for i in range(1, len(types) + 1):
        if i == len(types) or types[i] != types[start]:
            out.append((types[start], start, i - 1))
            start = i
    return out


def _centre(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _emit_rows(rows, order, common, hold, shift):
    """One group dict per (type, rank): a contiguous run of one rank. Goals translate the start by `shift`."""
    out = []
    for ri, row in enumerate(rows):
        for t, i, j in _runs(row["types"]):
            m = j - i + 1
            g = dict(common, type=t, count=m)
            if row["kind"] == "line":
                x, y = _centre(row["pts"][i:j + 1])
                g.update(formation="line", x=x, y=y, facing=row["f"], spacing=row["sp"])
            else:
                whole = m == row["n"]
                a = row["angles"]
                mid = (a[i] + a[j]) / 2.0
                cx, cy = row["center"]
                g.update(formation="concave", center=[cx, cy], R=row["R"], facing=common["facing"],
                         arc_deg=row["arc"] if whole else (j - i) * row["arc"] / (row["n"] - 1),
                         x=cx + row["R"] * math.cos(math.radians(mid)),
                         y=cy + row["R"] * math.sin(math.radians(mid)))
            if hold:
                g["order"] = "hold"
            else:
                g["order"] = "attack_move"
                if row["kind"] == "line":
                    g["goals"] = [[round(x + shift[0], 6), round(y + shift[1], 6)] for x, y in row["pts"][i:j + 1]]
                else:
                    g["goals"] = row["goals"][i:j + 1]
            out.append((order.index(t), ri, i, g))
    return [g for *_, g in sorted(out, key=lambda e: e[:3])]


def _blob_groups(order, counts, p0, f_deg, sp, cols, common, hold, shift):
    """Boxes `cols` wide, one per type, stacked front to back in `order` and centred on `p0`."""
    back = _back(f_deg)
    rows = {t: -(-counts[t] // cols) for t in order}
    total = sum(rows.values())
    out, before = [], 0
    for t in order:
        off = before + (rows[t] - 1) / 2.0 - (total - 1) / 2.0
        before += rows[t]
        cx, cy = p0[0] + back[0] * sp * off, p0[1] + back[1] * sp * off
        g = dict(common, type=t, count=counts[t], formation="box", cols=cols, x=cx, y=cy, facing=f_deg, spacing=sp)
        if hold:
            g["order"] = "hold"
        else:
            g["order"] = "attack_move"
            pts = formations.place("box", counts[t], cx, cy, f_deg, sp, cols=cols)
            g["goals"] = [[round(x + shift[0], 6), round(y + shift[1], 6)] for x, y, _ in pts]
        out.append(g)
    return out


# ---- S1: where ----------------------------------------------------------------------------------

def _first_slope(t):
    grid = terrain._Grid(int(t["w_cells"]), int(t["h_cells"]))
    slopes = terrain._apply_preset(t.get("preset", "flat"), t, grid, float(t["cell"])) + terrain._extras(t, "slope")
    return terrain._normalise_slope("slope", slopes[0]) if slopes else None


def _clamp(p, t):
    w, h = t["w_cells"] * t["cell"], t["h_cells"] * t["cell"]
    return (min(max(p[0], _ARENA_MARGIN), w - _ARENA_MARGIN), min(max(p[1], _ARENA_MARGIN), h - _ARENA_MARGIN))


def _hold_point(sit, base, side, counts, sp):
    """(point, facing, across) of the best defensive point the terrain gives, or None where none is better."""
    t = base["terrain"]
    own, foe = _anchor(sit, side), _anchor(sit, 1 - side)
    fam = sit.family
    cell = float(t["cell"])
    if fam == "lane":
        wt, ch = int(t.get("wt", 4)), int(t.get("ch", 8))
        cx = int(t.get("cx", int(t["w_cells"]) // 2))
        xl = (cx - wt // 2) * cell
        xr = xl + wt * cell
        lo = int(t["h_cells"]) // 2 - ch // 2
        y_mid = (lo + ch / 2.0) * cell
        s = 1.0 if own[0] > (xl + xr) / 2.0 else -1.0         # own side of the strip: +1 right
        x = (xr - _LANE_INSET) if s > 0 else (xl + _LANE_INSET)
        across = max(1, int((ch * cell - 2.0 * (sit.jitter + 5.0)) // sp) + 1)
        return (x, y_mid), (180.0 if s > 0 else 0.0), across
    if fam == "ramp_defense":
        s = _first_slope(t)
        top = (s["x0"] + s["dx"] * s["length"], s["y0"] + s["dy"] * s["length"])
        return ((top[0] + s["dx"] * _PLATEAU_BEYOND, top[1] + s["dy"] * _PLATEAU_BEYOND),
                _bearing((0.0, 0.0), (-s["dx"], -s["dy"])), _ACROSS)
    stand = _STANDOFF * _min_range(base, counts)
    if fam == "cover":
        discs = t.get("cover") or []
        if not discs:
            return None
        d = max(discs, key=lambda c: c["r"])
        v = (d["x"] - foe[0], d["y"] - foe[1])
        n = math.hypot(*v)
        v = (v[0] / n, v[1] / n)
        gap = d["r"] + _COVER_GAP
        return (d["x"] + v[0] * gap, d["y"] + v[1] * gap), _bearing((0, 0), (-v[0], -v[1])), \
            max(1, int(2.0 * d["r"] // sp))
    if fam == "wall" or (fam == "barrier_ramp" and t.get("preset") == "ramp"):
        if fam == "wall":
            wt = int(t.get("wt", 4))
            cx = int(t.get("cx", int(t["w_cells"]) // 2))
            xl = (cx - wt // 2) * cell
            xr = xl + wt * cell
            left = own[0] < (xl + xr) / 2.0
        else:
            xl = xr = int(t["x1"]) * cell
            left = own[0] < xl
        x = xl - stand if left else xr + stand
        px, py = _clamp((x, own[1]), t)
        return (px, py), (0.0 if left else 180.0), _ACROSS
    if fam == "block":
        bw, bh = int(t.get("bw", 10)), int(t.get("bh", 10))
        cx = int(t.get("cx", int(t["w_cells"]) // 2))
        cy = int(t.get("cy", int(t["h_cells"]) // 2))
        x0, y0 = (cx - bw // 2) * cell, (cy - bh // 2) * cell
        c = (x0 + bw * cell / 2.0, y0 + bh * cell / 2.0)
        v = (own[0] - c[0], own[1] - c[1])
        n = math.hypot(*v)
        v = (v[0] / n, v[1] / n) if n > 1e-9 else (-1.0, 0.0)
        reach = min(bw * cell / 2.0 / abs(v[0]) if abs(v[0]) > 1e-9 else math.inf,
                    bh * cell / 2.0 / abs(v[1]) if abs(v[1]) > 1e-9 else math.inf)
        p = _clamp((c[0] + v[0] * (reach + stand), c[1] + v[1] * (reach + stand)), t)
        return p, _bearing((0, 0), (-v[0], -v[1])), _ACROSS
    return None


def _clear_of_slopes(sit, rows, layer):
    return all(situation.goal_clear(sit, x, y, layer) for row in rows for x, y in row["pts"])


# ---- composition --------------------------------------------------------------------------------

def _layer(sit, skills, layer):
    """S3 stands one above the believed enemy layer, clipped to 1..5; without it the side stands on `layer`
    (the caller's hint for a naive side) or `sit.layer`."""
    if "S3" not in skills:
        return sit.layer if layer is None else layer
    return min(5, max(1, (sit.hidden["layer"] if "S4" in skills else sit.layer) + 1))


def _beat_order(sit, base, side, order, counts, enemy, ladder):
    """Own types in the order that puts each opposite the enemy type it beats (ties by roster order)."""
    e_counts = {t: n for t, n in (enemy[1] if enemy else counts).items() if n > 0}
    foe = _compose(sit, base, 1 - side, e_counts, frozenset(), ladder, None, True)
    lat = _lateral_axis(sit)
    by_cat = {}
    for g in foe:
        pts = formations.place(g["formation"], g["count"], g["x"], g["y"], g["facing"], g.get("spacing", 37.5),
                               **{k: g[k] for k in ("cols",) if k in g})
        cat = base["types"][g["type"]]["category"]
        by_cat.setdefault(cat, []).extend(x * lat[0] + y * lat[1] for x, y, _ in pts)

    def key(t):
        want = by_cat.get(_BEATS[base["types"][t]["category"]])
        return (0, sum(want) / len(want), order.index(t)) if want else (1, 0.0, order.index(t))

    return sorted(order, key=key)


def _compose(sit, base, side, counts, skills, ladder, enemy, larger, arc=_ARC, layer=None):
    """`larger`: this side has more heads than the enemy. The larger side attacks (R* is measured with it made to
    attack); a side that holds by choice (S1's point, or the hold ladder) does so only when it is not larger."""
    letter = "AB"[side]
    own, foe = _anchor(sit, side), _anchor(sit, 1 - side)
    sp = _spacing(sit)
    order = _type_order(counts)
    f = _bearing(own, foe) if "S5" in skills else _facing(sit, side)    # S5 lays the line exactly across the approach
    p0, across, hold_point = own, _ACROSS, False
    s1 = "S1" in skills and sit.family != "flat"      # no better point on a flat map: S1 is exactly the naive play
    if s1:
        spot = _hold_point(sit, base, side, counts, sp)
        if spot is not None:
            p0, f, across = spot
            hold_point = True
    if hold_point and sit.family not in ("lane", "ramp_defense", "cover"):
        outward = _back(f)
        for _ in range(_EDGE_TRIES):
            rows = _line_rows(sum(counts.values()), p0, f, sp, across)
            if _clear_of_slopes(sit, rows, sit.layer):
                break
            p0 = (p0[0] - outward[0] * _EDGE_STEP, p0[1] - outward[1] * _EDGE_STEP)
    if "S5" in skills:
        order = _beat_order(sit, base, side, order, counts, enemy, ladder)
    hold = (s1 and not larger) or ("S2" not in skills and not (ladder != "hold" or larger))
    common = {"side": letter, "layer": _layer(sit, skills, layer), "target_policy": "nearest", "facing": f}
    shift = (foe[0] - p0[0], foe[1] - p0[1])
    n = sum(counts.values())
    if "S2" in skills:
        center = foe
        axis = _bearing(foe, p0)
        r0 = math.hypot(p0[0] - foe[0], p0[1] - foe[1]) if s1 else 0.5 * sit.approach_distance
        rows = _concave_rows(n, center, axis, r0, sp, arc)
        _assign(rows, order, counts, _lateral_axis(sit))
        return _emit_rows(rows, order, common, hold, shift)
    if ladder == "blob":
        return _blob_groups(order, counts, p0, f, sp, min(_BLOB_COLS, across), common, hold, shift)
    rows = _line_rows(n, p0, f, sp, across)
    _assign(rows, order, counts, _lateral_axis(sit))
    return _emit_rows(rows, order, common, hold, shift)


def compose(sit, side, size, skills, ladder="line", enemy=None, layer=None):
    """`size` is a number of heads. `layer`: where a side without S3 stands (default `sit.layer`); build_scenario
    sets it for a naive side."""
    base = situation.base_scenario(sit)
    counts = counts_for_heads(sit.mix, size, base)
    larger = enemy is not None and sum(counts.values()) > sum(enemy[1].values())
    return _compose(sit, base, side, counts, frozenset(skills), ladder, enemy, larger, layer=layer)


# ---- scenarios for rstar ------------------------------------------------------------------------

def _fit_arc(sit, base, counts, skills, ladder):
    """The widest S2 arc (80 degrees first, then narrower by 10) at which the skilled force alone converts: the
    spec concave at R = 0.5 x approach leaves the arena on most situations. Returns (arc, None), or
    (None, the error) when no arc fits."""
    err = None
    for arc in itertools.takewhile(lambda a: a > 0, (_ARC - 10.0 * k for k in itertools.count())):
        scn = copy.deepcopy(base)
        scn["groups"] = _compose(sit, base, 0, counts, skills, ladder, None, False, arc)
        try:
            scenario.to_c(scn)
            return arc, None
        except ValueError as e:
            err = e
    return None, err


def build_scenario(sit, skills, size, ladder="line", processes=None, config=None):
    """`build(ratio, swap)` for rstar. `swap` exchanges only the side labels, so positions stay with the geometry
    (the skilled play always starts from anchor A) and a side-index bias cancels. `processes` is accepted for
    signature compatibility and unused: fights are run by the solver."""
    skills = frozenset(skills)
    base = situation.base_scenario(sit)
    if config is not None:
        base = apply_config(base, config)
    skilled_counts = counts_for_heads(sit.mix, size, base)
    naive_layer = sit.layer if config is None else sit.hidden["layer"]   # base rules: no cross-layer fire, nothing to scout
    arc, arc_error = _fit_arc(sit, base, skilled_counts, skills, ladder) if "S2" in skills else (_ARC, None)

    def build(ratio, swap):
        if arc is None:
            raise arc_error
        naive_counts = counts_for_heads(sit.mix, int(ratio * size + 0.5), base)
        if sum(skilled_counts.values()) + sum(naive_counts.values()) > ffi.MAX_UNITS:
            raise ValueError("%d units exceed LL_MAX_UNITS %d" % (sum(skilled_counts.values())
                                                                    + sum(naive_counts.values()), ffi.MAX_UNITS))
        scn = copy.deepcopy(base)
        scn["groups"] = []
        skilled_heads, naive_heads = sum(skilled_counts.values()), sum(naive_counts.values())
        mine = _compose(sit, base, 0, skilled_counts, skills, ladder, (sit.mix, naive_counts),
                        skilled_heads > naive_heads, arc)
        theirs = _compose(sit, base, 1, naive_counts, frozenset(), ladder, (sit.mix, skilled_counts),
                          naive_heads > skilled_heads, layer=naive_layer)
        if swap:
            mine = [dict(g, side="B") for g in mine]
            theirs = [dict(g, side="A") for g in theirs]
        groups = mine + theirs
        scn["groups"] = [g for g in groups if g["side"] == "A"] + [g for g in groups if g["side"] == "B"]
        scenario.to_c(scn)                      # an unbuildable layout (outside the arena, blocked cells) raises here
        return scn

    build.arc = arc
    return build


# ---- profile ------------------------------------------------------------------------------------

@dataclass
class Profile:
    cells: list = field(default_factory=list)

    def aggregate(self, map_set=None):
        """Per combination, over the cells of `map_set` ("space", "land"; None for all): the median premium over
        cells with a premium, how many there are, and how many cells have none (invalid, above or below the
        scan, short scan, unbuildable): counted, never averaged."""
        out = {}
        for c in self.cells:
            if map_set is not None and c["map_set"] != map_set:
                continue
            out.setdefault(c["combo"], []).append(c)
        return {
            combo: {
                "median_premium": statistics.median(p) if (p := [c["premium"] for c in cells
                                                                 if c["valid"] and c["premium"] is not None]) else None,
                "n_valid": len(p),
                "n_invalid": len(cells) - len(p),
            } for combo, cells in out.items()
        }


def _flags(sit, res, combo, arc, windows):
    flags = ["situation: " + r for r in situation.validate(sit)]
    if not res.points:
        flags.append("unbuildable")
    if not windows:
        flags.append("no_windows")
    for name in ("above_scan", "below_scan", "short_scan", "rerun"):
        if getattr(res, name):
            flags.append(name)
    if not res.valid:
        flags.append("non_monotonic")
    if situation.side_bias(res) > _BIAS_FLAG:
        flags.append("side_bias")
    if "S4" in combo:
        flags.append("info=given")
    if arc is not None and arc < _ARC:
        flags.append("s2_arc=%g" % arc)
    return flags


def _windows(build, res):
    return rstar_windows(build, res) if res.points and res.valid else []


def profile(sits, sizes=(8, 16), ladder="line", config=None, processes=None, ratios=None, refine=None,
            seeds=(0, 1), combos=None, win_margin=0.02):
    kw = {"seeds": tuple(seeds), "processes": processes, "win_margin": win_margin}
    if ratios is not None:
        kw["ratios"] = tuple(ratios)
    if refine is not None:
        kw["refine"] = refine
    prof = Profile()
    for sit in sits:
        for size in sizes:
            naive_build = build_scenario(sit, frozenset(), size, ladder, config=config)
            naive = _rstar(naive_build, size=size, **kw)
            naive_windows = None
            for combo in (all_combinations() if combos is None else combos):
                build = build_scenario(sit, combo, size, ladder, config=config)
                if combo:
                    res = _rstar(build, size=size, **kw)
                    windows = _windows(build, res)
                else:
                    res = naive
                    naive_windows = _windows(naive_build, naive) if naive_windows is None else naive_windows
                    windows = naive_windows
                valid = bool(res.points) and res.valid and naive.valid and not res.short_scan
                premium = None
                if valid and res.value is not None and naive.value is not None:
                    premium = res.value / naive.value
                prof.cells.append({
                    "situation": sit.id, "combo": combo, "size": size, "value": res.value, "valid": valid,
                    "r0": naive.value, "premium": premium, "flags": _flags(sit, res, combo, build.arc, windows),
                    "map_set": sit.map_set, "refusable": sit.refusable, "value_cost": res.value_cost,
                    "firing_adv_at_rstar": res.firing_adv_at_rstar, "firing_adv_equal": res.firing_adv_equal,
                    "win_margin": win_margin, "windows": windows,
                })
    return prof
