"""Stage 3 K1: situations and guards (SPEC.md 14.2)."""
import copy
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .. import ffi, scenario, terrain
from ..run import run

FAMILIES = ("flat", "block", "wall", "barrier_ramp", "lane", "ramp_defense", "cover")
ROSTER = ("raider", "interceptor", "vanguard", "warden", "bombard", "bastion")
MAP_SET = {"flat": "space", "block": "space", "wall": "space", "lane": "space", "cover": "space",
           "barrier_ramp": "land", "ramp_defense": "land"}
_REFUSAL = {   # family -> (the larger side could decline the fight, why)
    "flat": (True, "open ground: the larger side can go round"),
    "block": (True, "the larger side can go round the block"),
    "wall": (True, "the larger side can go round the wall's ends"),
    "cover": (True, "open ground: the larger side can go round the cover"),
    "barrier_ramp": (True, "another route or layer exists around the barrier"),
    "lane": (False, "the corridor is the only way through"),
    "ramp_defense": (False, "the slope is the only way up to the plateau"),
}

_BASE = Path(__file__).resolve().parents[2] / "scenarios" / "base.toml"
_DIMS = {"w_cells": 80, "h_cells": 40, "cell": 50.0, "layer_spacing": 0.0}
_CELL = _DIMS["cell"]
_MIN_APPROACH = 600.0
_EDGE_CLEAR = 100.0
_MOUTH_RADIUS = 40.0
_OVERLAP_BELOW = 29.0
_OVERLAP_FROM = 21          # SPEC "over ticks after 20"
_STUCK_WINDOW = 400
_STUCK_MOVE = 5.0
_ASYMMETRY = 100.0
_SPAWN_ACROSS = 20          # units across a rank (plays._ACROSS)
_SPAWN_RANKS = 7            # ranks behind it for 128 heads
_SPAWN_STEP = 50.0          # spacing between units and between ranks
_TRIES = 1000


@dataclass
class Situation:
    id: int
    seed: int
    family: str
    terrain: dict
    anchor_A: tuple
    anchor_B: tuple
    facing_A: float
    facing_B: float
    mix: dict                   # type name to share of heads, multiples of 0.25 summing to 1
    hidden: dict
    approach_distance: float
    jitter: float = 10.0
    layer: int = 3
    notes: list = field(default_factory=list)

    @property
    def map_set(self):
        return MAP_SET[self.family]

    @property
    def refusable(self):
        return _REFUSAL[self.family][0]

    @property
    def refusable_reason(self):
        return _REFUSAL[self.family][1]


def min_spacing(jitter, body_radius=15.0):
    return 2 * body_radius + 2 * jitter


def spacing_ok(spacing, jitter, body_radius=15.0):
    return spacing >= min_spacing(jitter, body_radius)


def run_params(sit, slowest_speed=40.0):
    stalemate = max(400, math.ceil(1.5 * sit.approach_distance / slowest_speed * 20))
    return {"stalemate_ticks": stalemate, "max_ticks": min(20000, 6 * stalemate)}


def base_scenario(sit):
    scn = scenario.load(_BASE)
    scn["terrain"] = {**scn["terrain"], **copy.deepcopy(sit.terrain)}
    scn["rules"]["spawn_jitter"] = sit.jitter
    scn["run"].update(run_params(sit))
    scn["groups"] = []
    return scn


def side_bias(rstar_result):
    return rstar_result.label_gap


# ---- slope edges -------------------------------------------------------------------------------

def _edges(terrain_dict):
    """(x, y, layer) of every slope edge centre: the bottom edge is on bottom_layer, the top edge on top_layer."""
    slopes = []
    if terrain_dict.get("preset", "flat") == "ramp":
        grid = terrain._Grid(int(terrain_dict.get("w_cells", _DIMS["w_cells"])),
                             int(terrain_dict.get("h_cells", _DIMS["h_cells"])))
        slopes += terrain._apply_preset("ramp", terrain_dict, grid, float(terrain_dict.get("cell", _CELL)))
    slopes += terrain._extras(terrain_dict, "slope")
    out = []
    for i, s in enumerate(slopes):
        s = terrain._normalise_slope("terrain.slope[%d]" % i, s)
        out.append((s["x0"], s["y0"], s["bottom_layer"]))
        out.append((s["x0"] + s["dx"] * s["length"], s["y0"] + s["dy"] * s["length"], s["top_layer"]))
    return out


def goal_clear(sit, x, y, layer):
    return all(math.hypot(x - ex, y - ey) >= _EDGE_CLEAR
               for ex, ey, el in _edges(sit.terrain) if el == layer)


def _spawn_layers(built, anchor, facing):
    """The layers open over every in-arena cell a force of up to 128 heads spawns on: ranks of 20 across
    the facing, the further ranks behind the anchor (cells outside the arena fail to build elsewhere)."""
    f = math.radians(facing)
    ax, ay, px, py = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    mask = 0b11111
    for r in range(_SPAWN_RANKS):
        for i in range(_SPAWN_ACROSS):
            lat, dep = (i - (_SPAWN_ACROSS - 1) / 2.0) * _SPAWN_STEP, -r * _SPAWN_STEP
            cr = terrain.cell_of(built.w_cells, built.h_cells, built.cell,
                                 anchor[0] + dep * ax + lat * px, anchor[1] + dep * ay + lat * py)
            if cr is not None:
                mask &= built.open[cr[1] * built.w_cells + cr[0]]
    return {k for k in range(1, 6) if mask & (1 << (k - 1))}


def validate(sit):
    reasons = []
    t = {**_DIMS, **sit.terrain}
    width, height = t["w_cells"] * t["cell"], t["h_cells"] * t["cell"]
    try:
        built = terrain.build(t)
    except ValueError as e:
        built = None
        reasons.append("terrain does not build: %s" % e)
    for name, (x, y) in (("A", sit.anchor_A), ("B", sit.anchor_B)):
        if not (0.0 <= x < width and 0.0 <= y < height):
            reasons.append("anchor %s (%g, %g) is outside the arena" % (name, x, y))
            continue
        if built is None:
            continue
        c, r = terrain.cell_of(built.w_cells, built.h_cells, built.cell, x, y)
        if not built.open[r * built.w_cells + c] & (1 << (sit.layer - 1)):
            reasons.append("anchor %s (%g, %g) is not open on layer %d (blocked)" % (name, x, y, sit.layer))
        if not goal_clear(sit, x, y, sit.layer):
            reasons.append("anchor %s (%g, %g) is within %g of a slope edge on layer %d"
                           % (name, x, y, _EDGE_CLEAR, sit.layer))
        if sit.hidden["layer"] not in _spawn_layers(built, (x, y), sit.facing_A if name == "A" else sit.facing_B):
            reasons.append("hidden layer %d is closed over the spawn ranks at anchor %s"
                           % (sit.hidden["layer"], name))
    if sit.approach_distance < _MIN_APPROACH:
        reasons.append("approach_distance %g is below %g" % (sit.approach_distance, _MIN_APPROACH))
    if abs(sum(sit.mix.values()) - 1.0) > 1e-9:
        reasons.append("mix shares sum to %g, not 1" % sum(sit.mix.values()))
    return reasons


# ---- sampling ----------------------------------------------------------------------------------

def _pt(x, y):
    return (round(x, 1), round(y, 1))


def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def _flank(rng, left, right, y0, spread=250.0):
    """Anchors on opposite sides of a feature spanning x in [left, right]: one near, one far; which label
    sits on the near side is drawn. Returns (A, B, near_label)."""
    near, far = rng.uniform(200.0, 450.0), rng.uniform(650.0, 1100.0)
    p_near = _pt(left - near, _clip(y0 + rng.uniform(-spread, spread), 300.0, 1700.0))
    p_far = _pt(right + far, _clip(y0 + rng.uniform(-spread, spread), 300.0, 1700.0))
    if rng.random() < 0.5:
        return p_near, p_far, "A"
    return p_far, p_near, "B"


def _span(centre, width):
    """World-unit bounds of a strip of `width` cells the way terrain places it around cell `centre`."""
    lo = (centre - width // 2) * _CELL
    return lo, lo + width * _CELL


def _flat(rng):
    a = _pt(rng.uniform(300.0, 1500.0), rng.uniform(600.0, 1400.0))
    b = _pt(rng.uniform(2500.0, 3700.0), rng.uniform(600.0, 1400.0))
    a, b = (a, b) if rng.random() < 0.5 else (b, a)
    return {"preset": "flat"}, a, b, None, []


def _block(rng):
    bw, bh = rng.randrange(6, 15), rng.randrange(6, 15)
    cx, cy = rng.randrange(34, 47), rng.randrange(16, 25)
    if (cx, cy) == (40, 20):
        cx = 36
    t = {"preset": "block", "bw": bw, "bh": bh, "h": rng.choice((2, 3, 4)), "cx": cx, "cy": cy}
    left, right = _span(cx, bw)
    top, bottom = _span(cy, bh)
    a, b, near = _flank(rng, left, right, (top + bottom) / 2.0)
    return t, a, b, ("point", ((left + right) / 2.0, (top + bottom) / 2.0)), ["near side: " + near]


def _wall(rng):
    wt, cx = rng.choice((2, 4, 6)), rng.randrange(34, 47)
    t = {"preset": "wall", "wt": wt, "end_gap": rng.randrange(4, 11), "h": rng.choice((2, 3, 4)), "cx": cx}
    left, right = _span(cx, wt)
    a, b, near = _flank(rng, left, right, 1000.0)
    return t, a, b, ("line", (left + right) / 2.0), ["near side: " + near]


def _lane(rng):
    wt, cx = rng.choice((4, 6, 8, 10)), rng.randrange(34, 47)
    t = {"preset": "lane", "wt": wt, "ch": rng.choice((4, 6, 8)), "h": rng.choice((2, 3, 4)), "cx": cx}
    left, right = _span(cx, wt)
    a, b, near = _flank(rng, left, right, 1000.0, spread=150.0)
    return t, a, b, ("line", (left + right) / 2.0), ["near side: " + near]


def _ramp(rng, defense):
    """Anchors on opposite sides of the face: one on the ground, one on the plateau (SPEC 6 ramp preset).
    `defense` puts the plateau side close behind the top edge; otherwise it is drawn further out."""
    x1, cy, sl = rng.randrange(34, 47), rng.randrange(16, 25), rng.choice((500.0, 600.0, 700.0, 800.0))
    t = {"preset": "ramp", "x1": x1, "sl": sl, "sw": rng.choice((200.0, 300.0)), "g": 1,
         "h": 2 if defense else rng.choice((1, 2)), "cy": cy}
    bottom = x1 * _CELL - _CELL / 2.0
    top, y0 = bottom + sl, cy * _CELL
    ground_gap = rng.uniform(700.0, 1500.0) if defense else rng.uniform(300.0, 1200.0)
    plateau_gap = rng.uniform(200.0, 450.0) if defense else rng.uniform(450.0, 1000.0)
    ground = _pt(bottom - ground_gap, _clip(y0 + rng.uniform(-250.0, 250.0), 300.0, 1700.0))
    plateau = _pt(top + plateau_gap, _clip(y0 + rng.uniform(-250.0, 250.0), 300.0, 1700.0))
    a, b, held = (plateau, ground, "A") if rng.random() < 0.5 else (ground, plateau, "B")
    note = ("defender on the plateau: " if defense else "plateau side: ") + held
    return t, a, b, ("point", (bottom, y0)), [note]


def _cover(rng):
    left = _pt(rng.uniform(400.0, 1300.0), rng.uniform(700.0, 1300.0))
    right = _pt(rng.uniform(2700.0, 3600.0), rng.uniform(700.0, 1300.0))
    a, b, near = (left, right, "A") if rng.random() < 0.5 else (right, left, "B")
    near_p, far_p = (a, b) if near == "A" else (b, a)
    toward = 1.0 if far_p[0] > near_p[0] else -1.0
    height_layer = rng.choice((2, 3, 4))
    discs = [{"x": round(near_p[0] + toward * rng.uniform(300.0, 500.0), 1),
              "y": round(near_p[1] + rng.uniform(-150.0, 150.0), 1),
              "r": round(rng.uniform(100.0, 160.0), 1), "height_layer": height_layer}]
    for _ in range(rng.choice((0, 1, 2))):
        discs.append({"x": round(rng.uniform(1600.0, 2400.0), 1), "y": round(rng.uniform(700.0, 1300.0), 1),
                      "r": round(rng.uniform(50.0, 90.0), 1), "height_layer": height_layer})
    vantage = [{"x": round(rng.uniform(1500.0, 2500.0), 1), "y": round(rng.uniform(300.0, 1700.0), 1),
                "r": round(rng.uniform(60.0, 120.0), 1)} for _ in range(rng.choice((1, 2)))]
    t = {"preset": "flat", "cover": discs, "vantage": vantage}
    return t, a, b, ("point", (discs[0]["x"], discs[0]["y"])), ["big cover on side: " + near]


_BUILDERS = {
    "flat": _flat, "block": _block, "wall": _wall, "lane": _lane, "cover": _cover,
    "barrier_ramp": lambda rng: _ramp(rng, False), "ramp_defense": lambda rng: _ramp(rng, True),
}


def _feature_dist(feature, p):
    kind, where = feature
    return math.dist(p, where) if kind == "point" else abs(p[0] - where)


def _facing(src, dst):
    return round(math.degrees(math.atan2(dst[1] - src[1], dst[0] - src[0])), 1)


def _draw_mix(rng):
    k = rng.choice((1, 2, 3))
    types = sorted(rng.sample(range(len(ROSTER)), k))
    if k == 1:
        quarters = [4]
    elif k == 2:
        a = rng.choice((1, 2, 3))
        quarters = [a, 4 - a]
    else:
        big = rng.randrange(3)
        quarters = [2 if i == big else 1 for i in range(3)]
    return {ROSTER[t]: 0.25 * q for t, q in zip(types, quarters)}


def _hidden_layers(terr, a, b):
    """The hidden-layer candidates (2 to 4) open over the spawn ranks at both anchors."""
    try:
        built = terrain.build({**_DIMS, **terr})
    except ValueError:
        return []
    spawns = [_spawn_layers(built, p, _facing(p, q)) for p, q in ((a, b), (b, a))]
    return [k for k in (2, 3, 4) if all(k in layers for layers in spawns)]


def _draw(rng, idx, seed, family):
    for _ in range(_TRIES):
        terr, a, b, feature, notes = _BUILDERS[family](rng)
        terr = {**terr, "layer_spacing": 0.0}
        mix, route = _draw_mix(rng), rng.randrange(2)
        layers = _hidden_layers(terr, a, b)
        if not layers:
            continue
        sit = Situation(
            id=idx, seed=seed, family=family, terrain=terr, anchor_A=a, anchor_B=b,
            facing_A=_facing(a, b), facing_B=_facing(b, a), mix=mix,
            hidden={"route": route, "layer": rng.choice(layers)},
            approach_distance=math.dist(a, b), notes=notes)
        asymmetric = feature is None or abs(
            _feature_dist(feature, a) - _feature_dist(feature, b)) > _ASYMMETRY
        if asymmetric and validate(sit) == []:
            return sit
    raise RuntimeError("no valid %s situation in %d draws" % (family, _TRIES))


def sample_situations(n, seed, families=None):
    rng = random.Random(seed)
    fams = list(FAMILIES if families is None else families)
    out, order = [], []
    for i in range(n):
        if not order:
            order = list(fams)
            rng.shuffle(order)
        out.append(_draw(rng, i, seed, order.pop()))
    return out


# ---- audit -------------------------------------------------------------------------------------

def _near_mouth(x, y, layer, edges):
    near = np.zeros(x.shape, dtype=bool)
    for ex, ey, el in edges:
        near |= (layer == el) & (np.hypot(x - ex, y - ey) <= _MOUTH_RADIUS)
    return near


def _overlap_pairs_max(trace, edges):
    ticks, n = trace.shape
    if ticks <= _OVERLAP_FROM or n < 2:
        return 0
    iu, ju = np.triu_indices(n, 1)
    chunk = max(1, 2_000_000 // len(iu))
    best = 0
    for lo in range(_OVERLAP_FROM, ticks, chunk):
        seg = trace[lo:lo + chunk]
        x, y = seg["x"].astype(np.float64), seg["y"].astype(np.float64)
        layer = seg["layer"].astype(int)
        ok = seg["alive"].astype(bool) & ((seg["flags"] & 4) == 0) & ~_near_mouth(x, y, layer, edges)
        d = np.hypot(x[:, iu] - x[:, ju], y[:, iu] - y[:, ju])
        pairs = ok[:, iu] & ok[:, ju] & (layer[:, iu] == layer[:, ju]) & (d < _OVERLAP_BELOW)
        best = max(best, int(pairs.sum(axis=1).max()))
    return best


def _stuck_units(scn, trace):
    ticks, n = trace.shape
    if ticks <= _STUCK_WINDOW:
        return 0
    orders, ranges = [], []
    defaults = scn.get("type_defaults", {})
    for g in scn.get("groups", []):
        orders += [g.get("order", "hold")] * int(g["count"])
        ranges += [float({**defaults, **scn["types"][g["type"]]}["range"])] * int(g["count"])
    win = trace[-(_STUCK_WINDOW + 1):]
    x, y = win["x"].astype(np.float64), win["y"].astype(np.float64)
    alive, side = win["alive"].astype(bool), win["side"].astype(int)
    moved = np.hypot(x[-1] - x[0], y[-1] - y[0])
    stuck = 0
    for i in range(n):
        if not alive[-1, i] or orders[i] == "hold" or moved[i] >= _STUCK_MOVE:
            continue
        foes = np.flatnonzero(side[-1] != side[-1, i])
        reach = np.hypot(x[:, foes] - x[:, [i]], y[:, foes] - y[:, [i]]) <= ranges[i]
        if not (reach & alive[:, foes]).any():
            stuck += 1
    return stuck


def audit(scn, seed, lib="O2"):
    res = run(scn, seed=seed, trace=True, lib=lib)
    return {
        "overlap_pairs_max": _overlap_pairs_max(res.trace, _edges(scn["terrain"])),
        "stuck_units": _stuck_units(scn, res.trace),
        "contact": res.first_contact_tick >= 0,
        "stalemate": res.winner == ffi.WIN_STALEMATE,
        "ticks": res.ticks,
    }
