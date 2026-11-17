"""Test-local oracle for the engine rule fixes (spec docs/northstar/plans/engine-rules-2026-11-08/spec.md, Round 1).

Holds no tests. It records a real lab fight tick by tick (it wraps `Engine.step`, as stage 4's tests do) and answers the
rule questions from engine state alone. It deliberately does NOT import scripts/skilllab/invariants.py (the F0 product
module): these tests prove F1 to F4 independently of the checker that F0 ships, so a bug in the checker cannot hide a
bug in the engine.

Predicates derived from docs/reports/2026-11-07-rule-enforcement/sweep/inv_check.py (I1, I2a/I2b, I8, I10s); every
number below is a detector bound named after the spec's DRAFT constants, Westley's to change:
  DEPTH_TOL      DRAFT-inv-cell-depth 1 wu       a unit may sit up to 1 wu inside a blocked cell (rounding of a face)
  PUSH_RADIUS    DRAFT-inv-push-radius 40 wu     another unit this close excuses a displacement (collision push)
  OWN_MOVE       0.5 wu                           displacement above this on a tick counts as "moved"
  HEAL_ONE       0.075 hp                         R-083-03: one Warden's heal per tick, a second adds nothing
  NOTICE_MARGIN  DRAFT-notice-margin 0.1          R-087-04 (Round 5): a unit's notice distance to an enemy is its attack range, times the reach table's multiplier for the
                                                  enemy's layer, times 1 + 0.1, measured as weapon reach is (R-087-10, slant between two walkers)
  RETURN_FIRE_TICKS 4                             R-087-06: a hit by the target in the 4 ticks up to a pick is return fire (the checker's DRAFT-inv-return-fire-ticks)
  COHORT_PERIOD  4                                R-087-08: a lock kept beyond the notice distance for more than one cohort period is reported (G7)

Use:
    with oracle.recording() as recs:
        frames, last, end, orders = run.fight(layout, 1, "on", cap_seconds, 100000)
    rec = oracle.only(recs)
    oracle.cell_entries(rec)      # [(tick, unit, depth)]  R-207-06
"""
import contextlib
import functools
import math
import tomllib
from pathlib import Path

from scripts.skilllab.engine import Engine

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"

DEPTH_TOL = 1.0
PUSH_RADIUS = 40.0
OWN_MOVE = 0.5
HEAL_ONE = 0.075
NOTICE_MARGIN = 0.1       # DRAFT-notice-margin (round5.md G1), Westley's number to change
RETURN_FIRE_TICKS = 4
COHORT_PERIOD = 4
BACKSWING_TICKS = 10      # R-084-04: the 0.5 s pause after a shot is 10 ticks; ticks 1 to 9 after the shot are inside it (inv_check I2b)
CELL = 100.0
TICK = 20


def catalogue(name):
    with open(CATALOGUE / (name + ".toml"), "rb") as f:
        return tomllib.load(f)


class Recorder:
    """Every tick: `pre` and `post` unit rows, the fire events, who sees whom, which post positions stand in a blocked cell."""

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
        import ctypes
        buf = (ctypes.c_double * 8)()
        eng._lib.om_terrain_band_heights.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
        eng._lib.om_terrain_band_heights.restype = ctypes.c_uint32
        n_bands = eng._lib.om_terrain_band_heights(w, buf, 8)
        self.heights = list(buf)[:n_bands]       # band floor height of each layer (a flat world: empty), for R-087-10's slant
        self.mult_up = [1.0] + [eng.get_param(w, eng.param_id("OM_TP_RANGE_UP_%d" % i)) for i in range(1, 5)]       # the reach table, csrc/unit.c om_tac_offset_mult
        self.mult_down = [1.0] + [eng.get_param(w, eng.param_id("OM_TP_RANGE_DOWN_%d" % i)) for i in range(1, 5)]
        self.flyers = {u for u in self.ids if eng.movement_kind(w, self.typ[u]) == 0}      # OM_MOVE_FLYING: reach is measured flat when either end flies
        self.canvas = None          # filled by the test when it knows it (cells outside the canvas are not tested)
        self.ticks = []             # one dict per step: n, pre, post, fires, hits, vis_pre, vis_post, cell
        self.n = 0
        self.blocked = set()

    def row(self, u):
        eng, w = self.eng, self.w
        alive = eng.unit_alive(w, u)
        x, y = eng.unit_pos(w, u)
        return {"alive": alive, "x": x, "y": y, "layer": int(eng.unit_layer(w, u)), "hp": eng.unit_hp(w, u),
                "tgt": eng.unit_target(w, u), "dest": eng.unit_destination(w, u) if alive else None}

    def snap(self):
        return {u: self.row(u) for u in self.ids}

    def vis(self, snap):
        lib, w = self.eng._lib, self.w
        out = {}
        for e in self.ids:
            if snap[e]["alive"]:
                for s in (0, 1):
                    if self.side[e] != s:
                        out[(s, e)] = bool(lib.om_player_can_see(w, s, e))
        return out

    def blocked_cell(self, x, y, layer):
        cx, cy = int(x // CELL), int(y // CELL)
        if x < 0 or y < 0:
            return False
        return bool(self.eng._lib.om_navmesh_is_cell_blocked(self.w, cx, cy, int(layer)))

    def depth(self, x, y, layer):
        """Distance to the nearest face of the blocked cell that borders an open cell (0 = on the face)."""
        cx, cy = int(x // CELL), int(y // CELL)
        best = 1e9
        for dx, dy, d in ((-1, 0, x - cx * CELL), (1, 0, (cx + 1) * CELL - x), (0, -1, y - cy * CELL), (0, 1, (cy + 1) * CELL - y)):
            if cx + dx >= 0 and cy + dy >= 0 and not self.eng._lib.om_navmesh_is_cell_blocked(self.w, cx + dx, cy + dy, int(layer)):
                best = min(best, d)
        return best

    def scan_blocked(self):
        """Every (cx, cy, layer) the engine calls blocked, for cells 0..119 and layers 0..4 (the largest lab canvas), read once before the first step so
        that a finished fight can still be asked (the world is freed when the runner returns)."""
        lib, w = self.eng._lib, self.w
        self.blocked = {(cx, cy, layer) for layer in range(5) for cx in range(120) for cy in range(120) if lib.om_navmesh_is_cell_blocked(w, cx, cy, layer)}

    def hits_of(self, pre, post, fires):
        """Every (attacker, victim) the step's shots damaged, as the lab checker's Monitor reads them (scripts/skilllab/invariants.py `_hits`): the target of each shot, and for an area weapon
        each other enemy of the attacker whose hp fell and that stood within the area radius (plus 1 wu) of the target before the step. R-087-06 return fire answers splash too."""
        out = list(fires)
        for a, b in fires:
            radius = self.stats[self.typ[a]]["aoe_radius"]
            if radius > 0 and b in pre:
                for v in self.ids:
                    if v != b and self.side[v] != self.side[a] and pre[v]["alive"] and post[v]["hp"] < pre[v]["hp"] - 1e-9 and math.hypot(pre[b]["x"] - pre[v]["x"], pre[b]["y"] - pre[v]["y"]) <= radius + 1.0:
                        out.append((a, v))
        return out

    def step(self, orig):
        if self.n == 0:
            self.scan_blocked()
        pre = self.snap()
        vis_pre = self.vis(pre)
        orig(self.eng, self.w)
        self.n += 1
        post = self.snap()
        fires = []
        eng = self.eng
        import ctypes
        k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        for i in range(eng._lib.om_tactical_event_count(self.w)):
            if eng._lib.om_tactical_event_get_at(self.w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and k.value == 0:
                fires.append((a.value, b.value))
        hits = self.hits_of(pre, post, fires)
        cell = {}
        for u in self.ids:
            p = post[u]
            if p["alive"] and self.blocked_cell(p["x"], p["y"], p["layer"]):
                cell[u] = self.depth(p["x"], p["y"], p["layer"])
        self.ticks.append({"n": self.n, "pre": pre, "post": post, "fires": fires, "hits": hits, "vis_pre": vis_pre, "vis_post": self.vis(post), "cell": cell})


@contextlib.contextmanager
def recording():
    """Patch Engine.step so that every world stepped through it is recorded; yields {world address: Recorder}."""
    recs = {}
    orig = Engine.step

    def step(self, w):
        rec = recs.get(w.value)
        if rec is None:
            rec = recs[w.value] = Recorder(self, w)
        rec.step(orig)

    Engine.step = step
    try:
        yield recs
    finally:
        Engine.step = orig


def only(recs):
    assert len(recs) == 1, "expected the fight to step exactly one world, got %d" % len(recs)
    return next(iter(recs.values()))


FIGHT_SECONDS = 100       # DRAFT-oracle-seconds: how long each recorded catalogue fight runs (2000 ticks; the first violations of every kind are inside it)


def fight_layout(layout, sight, seconds=FIGHT_SECONDS, seed=1):
    """Run `layout` (a dict) through the arena runner's own `fight` and return its Recorder. `sight` is "off", "on" or "control"."""
    from scripts.skilllab.arena import run
    with recording() as recs:
        run.fight(layout, seed, sight, seconds, 100000)
    return only(recs)


@functools.lru_cache(maxsize=None)
def played(name, sight, seconds=FIGHT_SECONDS):
    """The recorded fight of catalogue layout `name` (cached for the session: several test files read the same fight)."""
    return fight_layout(catalogue(name), sight, seconds)


# ---------------------------------------------------------------- the predicates (each returns [(tick, unit, detail)])

def _disp(a, b):
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def _pushed(rec, tk, u):
    """Another living unit within PUSH_RADIUS of the unit at either end of the tick (the inv_check `pushed` test, as generous)."""
    pre, post = tk["pre"], tk["post"]
    for o in rec.ids:
        if o == u or not pre[o]["alive"]:
            continue
        for p in (pre[u], post[u]):
            for q in (pre[o], post[o]):
                if math.hypot(q["x"] - p["x"], q["y"] - p["y"]) < PUSH_RADIUS:
                    return True
    return False


def unit_ticks(rec):
    return sum(1 for tk in rec.ticks for u in rec.ids if tk["post"][u]["alive"])


def cell_entries(rec, tol=DEPTH_TOL):
    """R-207-06: a living unit ends the tick inside a planar blocked cell of its layer, deeper than `tol` wu."""
    return [(tk["n"], u, d) for tk in rec.ticks for u, d in tk["cell"].items() if d > tol]


def cell_touches(rec):
    """R-207-06 without the depth tolerance: every unit-tick inside a blocked cell at all."""
    return [(tk["n"], u, d) for tk in rec.ticks for u, d in tk["cell"].items()]


def outside_canvas(rec, width, height):
    """R-207-07: a living unit ends the tick outside the canvas."""
    return [(tk["n"], u, (p["x"], p["y"])) for tk in rec.ticks for u, p in tk["post"].items()
            if p["alive"] and not (0 <= p["x"] <= width and 0 <= p["y"] <= height)]


def fired_while_moving(rec):
    """R-087-04: a unit fired on a tick on which it moved under its own power (displacement above OWN_MOVE, no neighbour within PUSH_RADIUS)."""
    out = []
    for tk in rec.ticks:
        for a, _ in tk["fires"]:
            d = _disp(tk["pre"][a], tk["post"][a])
            if tk["pre"][a]["alive"] and d > OWN_MOVE and not _pushed(rec, tk, a):
                out.append((tk["n"], a, d))
    return list(dict.fromkeys(out))


def moved_in_backswing(rec):
    """R-084-04: a unit moved under its own power 1 to 9 ticks after a shot."""
    out, last = [], {}
    for tk in rec.ticks:
        fired = {a for a, _ in tk["fires"]}
        for u in rec.ids:
            if not tk["pre"][u]["alive"]:
                continue
            lf = last.get(u)
            if u not in fired and lf is not None and 1 <= tk["n"] - lf <= BACKSWING_TICKS - 1:
                d = _disp(tk["pre"][u], tk["post"][u])
                if d > OWN_MOVE and not _pushed(rec, tk, u):
                    out.append((tk["n"], u, d))
        for a in fired:
            last[a] = tk["n"]
    return out


def notice(rec, u, a, b, brow):
    """(distance, notice distance) from unit u (row `a`) to unit b (row `brow`), both read in the same state: the distance is the weapon reach's (horizontal, and the layers' band-height
    difference between two walkers, R-087-10); the notice distance is u's attack range times the reach table's multiplier for b's layer times 1 + NOTICE_MARGIN (R-087-04)."""
    la, lb = a["layer"], brow["layer"]
    horiz = _disp(a, brow)
    flat = u in rec.flyers or b in rec.flyers or la >= len(rec.heights) or lb >= len(rec.heights)
    dist = horiz if flat else math.hypot(horiz, rec.heights[lb] - rec.heights[la])
    mult = 1.0 if la == lb or abs(lb - la) > 4 else (rec.mult_up if lb > la else rec.mult_down)[abs(lb - la)]
    return dist, rec.stats[rec.typ[u]]["attack_range"] * mult * (1 + NOTICE_MARGIN)


def lock_swaps(rec, sensor_slack=25.0):
    """R-087-03 / R-087-08 (rewritten for Round 5): a unit's target changed to another living enemy while the old target was alive and still seen by the unit's side, with no
    new order (the destination is not cleared or set across the tick: the lab gives its own orders once, at tick 0). Two ends are legal and not swaps: the leash (R-087-05: a unit
    that has walked farther than its sensor radius + slack since it took the old lock, inv_check I27) and the notice distance (R-087-03 "leaves the unit's notice distance": the old
    target stood beyond the unit's notice distance in the state the step decided on, the pre-step state; R-087-06 return fire is exempt from the distance end, so a target that hit the
    unit within RETURN_FIRE_TICKS before the step never ends it)."""
    out = []
    for tk in rec.ticks:
        pre, post = tk["pre"], tk["post"]
        for u in rec.ids:
            p0, p1 = pre[u], post[u]
            old, new = p0["tgt"], p1["tgt"]
            if not (p0["alive"] and p1["alive"] and old and new and old != new and pre[old]["alive"] and post[old]["alive"]):
                continue
            side = rec.side[u]
            if not (tk["vis_pre"].get((side, old), True) and tk["vis_post"].get((side, old), True)):
                continue
            if p0["dest"] is None or p1["dest"] is None:
                continue   # the engine is re-issuing the unit's own order this tick (a lost target's last position, unit.c:2207): a new order breaks a lock
            if _walked_since_lock(rec, u, tk) > rec.stats[rec.typ[u]]["sensor_radius"] + sensor_slack:
                continue
            dist, limit = notice(rec, u, p0, old, pre[old])
            if dist > limit and not _hit_by(rec, tk["n"], old, u):
                continue   # the target left the notice distance: the lock ended there, the pick after it is a new one
            out.append((tk["n"], u, "target %d -> %d while %d alive and seen" % (old, new, old)))
    return out


def _hit_by(rec, n, attacker, victim):
    """R-087-06: `attacker` hit `victim` (the target of its shot, or a splash victim of it) in tick n or the RETURN_FIRE_TICKS - 1 before it (return fire's window; the checker's DRAFT-inv-return-fire-ticks)."""
    return any((attacker, victim) in tk["hits"] for tk in rec.ticks[max(0, n - RETURN_FIRE_TICKS):n])


def picks_beyond_notice(rec):
    """R-087-04 (Round 5): a unit with no living target before the step ends it holding an enemy that stood beyond its notice distance in the pre-step state, and that enemy did
    not hit it within RETURN_FIRE_TICKS (R-087-06). [(tick, unit, target, distance, notice distance)]."""
    out = []
    for tk in rec.ticks:
        pre, post = tk["pre"], tk["post"]
        for u in rec.ids:
            p0, p1 = pre[u], post[u]
            new = p1["tgt"]
            if not (p0["alive"] and p1["alive"] and new and new != p0["tgt"] and new in pre and pre[new]["alive"] and rec.side[new] != rec.side[u]):
                continue
            if p0["tgt"] and pre[p0["tgt"]]["alive"]:
                continue   # a swap, not a pick: lock_swaps judges it
            dist, limit = notice(rec, u, p0, new, pre[new])
            if dist > limit and not _hit_by(rec, tk["n"], new, u):
                out.append((tk["n"], u, new, round(dist, 1), round(limit, 1)))
    return out


def locks_beyond_notice(rec):
    """R-087-03 (G7 lock): a unit holds a living enemy that stands beyond its notice distance (post-tick state) in more than COHORT_PERIOD consecutive ticks, and the lock was not
    taken by return fire (the target hit the unit within RETURN_FIRE_TICKS up to the tick the lock began; return fire is exempt until the lock ends). One entry per run, in its
    COHORT_PERIOD + 1 th tick: [(tick, unit, target, distance, notice distance)]."""
    out, run, began = [], {}, {}
    for tk in rec.ticks:
        post, pre = tk["post"], tk["pre"]
        for u in rec.ids:
            t = post[u]["tgt"] if post[u]["alive"] else 0
            if not t or not post[t]["alive"] or rec.side[t] == rec.side[u]:
                run.pop(u, None)
                began.pop(u, None)
                continue
            if began.get(u, (None,))[0] != t:
                began[u] = (t, _hit_by(rec, tk["n"], t, u))
            dist, limit = notice(rec, u, post[u], t, post[t])
            if dist <= limit or began[u][1]:
                run.pop(u, None)
                continue
            r = run.get(u)
            r = run[u] = (t, r[1] + 1) if r and r[0] == t else (t, 1)
            if r[1] == COHORT_PERIOD + 1:
                out.append((tk["n"], u, t, round(dist, 1), round(limit, 1)))
    return out


def _walked_since_lock(rec, u, tk):
    """Distance from where the unit took its current lock (the earliest tick of the unbroken run of the old target) to where it stands now."""
    old = tk["pre"][u]["tgt"]
    start = tk["pre"][u]
    for prev in reversed(rec.ticks[:tk["n"] - 1]):
        if prev["post"][u]["tgt"] != old:
            break
        start = prev["post"][u]
    return _disp(start, tk["post"][u])


def warden_overheal(rec):
    """R-083-03: a unit's hp rose by more than one Warden's heal in a tick on which nothing hit it (a second Warden adds nothing)."""
    out = []
    for tk in rec.ticks:
        hit = {b for _, b in tk["fires"]}
        for u in rec.ids:
            p0, p1 = tk["pre"][u], tk["post"][u]
            if p0["alive"] and p1["alive"] and u not in hit and p1["hp"] - p0["hp"] > HEAL_ONE + 1e-6:
                out.append((tk["n"], u, p1["hp"] - p0["hp"]))
    return out


def distinct_units(hits):
    return len({h[1] for h in hits})


def invariants_trace(rec):
    """The recorded fight as the trace `scripts/skilllab/invariants.check` takes (the contract is in tests/skilllab/test_invariants.py): frame 0 is the state
    before the first step, frame k the state after step k with that step's shots (`fires`) and the units they damaged, splash included (`hits`); `seen` is whether the unit's side sees its target, `order` whether the
    unit has a destination."""
    def frame(tick, snap, vis, fires, hits=None):
        units = {}
        for u in rec.ids:
            r = snap[u]
            units[u] = {"x": r["x"], "y": r["y"], "layer": r["layer"], "alive": r["alive"], "hp": r["hp"], "side": rec.side[u], "target": r["tgt"],
                        "seen": vis.get((rec.side[u], r["tgt"]), True) if r["tgt"] else True, "order": r["dest"] is None}
        return {"tick": tick, "units": units, "fires": list(fires), "hits": list(fires if hits is None else hits)}
    out = [frame(0, rec.ticks[0]["pre"], rec.ticks[0]["vis_pre"], [])]
    out += [frame(tk["n"], tk["post"], tk["vis_post"], tk["fires"], tk["hits"]) for tk in rec.ticks]
    return out
