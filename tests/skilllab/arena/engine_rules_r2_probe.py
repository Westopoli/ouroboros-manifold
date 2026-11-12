"""Test-local probe for the engine rule fixes, Round 2 (F7 spherical distance, F8 layer change). Holds no tests.

Like engine_rules_oracle.py (Round 1) it wraps `Engine.step` and reads engine state after every step; unlike it, it needs the LIVE world each tick (the band heights, the
sight and fire answers), so it computes its rows inside the wrapper. It does not import scripts/skilllab/invariants.py (F0's product): the F7 and F8 tests prove their fixes
independently of the checker, so a lax checker cannot hide a broken rule (the checker's `continuity` excuses any unit with a neighbour within 40 wu; see test_engine_rules_f8).

Per tick and per living unit that holds a target:  a row (tick, a, t, flat, dz_floor, dz_cont, range, la, lb, see, shoot) where
  flat       horizontal distance, wu                         dz_floor   height of t's layer minus height of a's layer, band floors from om_terrain_band_heights
  dz_cont    the same from om_terrain_height_at (the unit's own terrain height; differs from dz_floor on a plateau above its band floor and on a ramp)
  range      the type's attack range (the cross-layer multipliers OM_TP_RANGE_UP_1 / DOWN_1 are asserted to be 1.0 by the F7 test)
  see, shoot om_unit_can_see(a, t) and om_combat_can_shoot(a, t) at that moment
and per tick the shots (attacker, target) of the step, and every unit's before and after position and layer.

DRAFT numbers (Westley's to change): SLANT_SLACK 1.0 wu (the engine's shot is decided on a position that the same tick's push pass may move by under 1 wu), STEP_SLACK 1.3 wu
(DRAFT-inv-step-slack, the F0 constant), PUSH_FREE true (no push excuse at all: on an open field with 24 walkers 4 of 103,542 unit-ticks move more than 1.3 wu above their top step, by 1.47 to 2.01 wu, a push in a pack, measured on L-0050 on 2026-11-12;
the layer-change tests that use this probe have no push excuse, so a push on a layer-change tick of that size would read as a jump).
"""
import contextlib
import ctypes
import functools
import math

from scripts.skilllab.engine import Engine

SLANT_SLACK = 1.0
STEP_SLACK = 1.3
TICK = 20


class Run:
    def __init__(self, eng, w):
        self.eng, self.w = eng, w
        self.ids, self.side = [], {}
        for (wa, f), us in eng._own.items():
            if wa == w.value:
                for u in us:
                    self.ids.append(u)
                    self.side[u] = f
        self.ids.sort()
        self.typ = {u: eng.unit_type(w, u) for u in self.ids}
        self.stats = {t: eng.type_stats(w, t) for t in set(self.typ.values())}
        buf = (ctypes.c_double * 8)()
        n = eng._lib.om_terrain_band_heights(w, buf, 8)
        self.heights = list(buf)[:n]
        self.down = eng.get_param(w, eng.param_id("OM_TP_SLOPE_DOWN_MULT"))
        self.range_mult = [eng.get_param(w, eng.param_id(p)) for p in ("OM_TP_RANGE_UP_1", "OM_TP_RANGE_DOWN_1")]
        eng._lib.om_terrain_height_at.restype = ctypes.c_double
        eng._lib.om_terrain_height_at.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
        self.n = 0
        self.rows = []       # held-target rows (see module docstring)
        self.fires = []      # (tick, attacker, target)
        self.moves = []      # (tick, unit, displacement, layer before, layer after, top step)
        self.dumps = {}      # tick -> {unit: dict} for the units a test asked about
        self.watch = {}      # tick -> [unit ids] to dump in full

    def unit(self, u):
        e, w = self.eng, self.w
        x, y = e.unit_pos(w, u)
        return {"alive": e.unit_alive(w, u), "x": x, "y": y, "layer": int(e.unit_layer(w, u)), "tgt": e.unit_target(w, u)}

    def step(self, orig):
        e, w, lib = self.eng, self.w, self.eng._lib
        pre = {u: self.unit(u) for u in self.ids}
        orig(e, w)
        self.n += 1
        post = {u: self.unit(u) for u in self.ids}
        kind, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        for i in range(lib.om_tactical_event_count(w)):
            if lib.om_tactical_event_get_at(w, i, ctypes.byref(kind), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and kind.value == 0:
                self.fires.append((self.n, a.value, b.value))
        for u in self.ids:
            p0, p1 = pre[u], post[u]
            if p0["alive"] and p1["alive"]:
                top = self.stats[self.typ[u]]["speed"] * max(1.0, self.down) / TICK
                self.moves.append((self.n, u, math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]), p0["layer"], p1["layer"], top))
            tg = p1["tgt"]
            if p1["alive"] and tg and tg in post and post[tg]["alive"]:
                q = post[tg]
                la, lb = p1["layer"], q["layer"]
                h = self.heights
                dzf = (h[lb] - h[la]) if (h and la < len(h) and lb < len(h)) else 0.0
                dzc = lib.om_terrain_height_at(w, q["x"], q["y"]) - lib.om_terrain_height_at(w, p1["x"], p1["y"]) if h else 0.0
                self.rows.append((self.n, u, tg, math.hypot(q["x"] - p1["x"], q["y"] - p1["y"]), dzf, dzc,
                                  self.stats[self.typ[u]]["attack_range"], la, lb, bool(lib.om_unit_can_see(w, u, tg)), bool(lib.om_combat_can_shoot(w, u, tg))))
        if self.n in self.watch:
            self.dumps[self.n] = {u: dict(post[u], see={v: bool(lib.om_unit_can_see(w, u, v)) for v in self.watch[self.n] if v != u},
                                         shoot={v: bool(lib.om_combat_can_shoot(w, u, v)) for v in self.watch[self.n] if v != u})
                                  for u in self.watch[self.n] if u in post}


@contextlib.contextmanager
def probing(watch=None):
    """Patch Engine.step; yields {world address: Run}. `watch` {tick: [unit ids]} asks for a full dump of those units at those ticks."""
    runs = {}
    orig = Engine.step

    def step(self, w):
        r = runs.get(w.value)
        if r is None:
            r = runs[w.value] = Run(self, w)
            r.watch = dict(watch or {})
        r.step(orig)

    Engine.step = step
    try:
        yield runs
    finally:
        Engine.step = orig


def only(runs):
    assert len(runs) == 1, "expected the fight to step exactly one world, got %d" % len(runs)
    return next(iter(runs.values()))


@functools.lru_cache(maxsize=None)
def played(name, sight="on", seconds=600, watch=None):
    """The probed fight of catalogue layout `name` (cached for the session)."""
    from scripts.skilllab.arena import run
    import engine_rules_oracle as oracle
    with probing(dict(watch) if watch else None) as runs:
        run.fight(oracle.catalogue(name), 1, sight, seconds, 100000)
    return only(runs)
