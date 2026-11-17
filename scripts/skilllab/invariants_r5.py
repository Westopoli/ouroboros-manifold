"""Engine rules Round 5, G7 (docs/northstar/plans/engine-rules-2026-11-08/round5.md): the predicates the lab checker (`invariants.py`) gained for Westley's rulings of 2026-11-17.

  LockKept        R-087-03  a lock kept on a target beyond the notice distance for more than one cohort period (a return-fire lock excepted)
  UnseenFire      R-087-01  an attack-mover on its way is neither stopped nor re-routed by a hit it cannot see; an idle unit or an arrived attack-mover moves away once and holds
  SlopeCollision  R-097-05  two units within 30 wu on one slope, and a unit that flips layer back and forth across a midline

Each is a small state machine fed one frame at a time by `invariants._Checker.feed`; the frame, row and `Rules` shapes are those of `invariants.py` (this module imports nothing from it, so the
checker can import these constants). The notice distance itself (`NOTICE_MARGIN`, `notice_distance`) is read by the checker's acquire and swap checks as well.
Tests: tests/skilllab/arena/test_invariants_r5_notice_and_lock.py, test_invariants_r5_unseen_fire_and_slope.py. Every number below is a DRAFT constant, Westley's to change:
  DRAFT-notice-margin 0.1   DRAFT-unseen-fire-window 60 frames   DRAFT-slope-slack 1 wu   DRAFT-flip-window 20 frames   DRAFT-slope-near 100 wu (the Monitor's idea of "on a slope")
"""
import ctypes
import math

NOTICE_MARGIN = 0.1          # DRAFT-notice-margin (R-087-04): a unit's notice distance is its attack range times (1 + this), measured as weapon reach is (R-087-10)
KEPT_FRAMES = 4              # R-087-08: one cohort period; a lock is reported in the frame after this many frames beyond the notice distance
UNSEEN_WINDOW = 60           # DRAFT-unseen-fire-window: frames after an unseen hit in which an attack-mover on its way must keep walking (the 60-tick HIT_GAP of the Round 4 unseen oracle)
OWN_MOVE = 0.5               # a displacement above it counts as "moved" (the checker's own constant, repeated: this module cannot import invariants)
SLOPE_GAP = 30.0             # R-097-05: 2 x unit radius 15 wu
SLOPE_SLACK = 1.0            # DRAFT-slope-slack: a pair this close to 30 wu counts as pushed apart
FLIP_CHANGES = 3             # R-097-05 / round5.md G5: three layer changes ...
FLIP_WINDOW = 20             # DRAFT-flip-window: ... within this many frames
SLOPE_NEAR = 100.0           # DRAFT-slope-near (wu): the Monitor counts a unit as on a slope when its cell's centre is this near the slope's midline along its run (the ramp's half-width, hills.RAMP_WU / 2)


def notice_distance(rules, u, layer, other_layer):
    """R-087-04: unit u's attack range times the reach table's multiplier for the two layers times (1 + NOTICE_MARGIN); None when the rules know no attack range for u."""
    rng = rules.attack_range.get(u)
    return None if rng is None else rng * rules.range_mult(layer, other_layer) * (1.0 + NOTICE_MARGIN)


class LockKept:
    """R-087-03 (G7 lock): "a lock kept on a target beyond the notice distance for more than one cohort period is reported, except a return-fire lock". A unit that holds a living, seen target
    standing beyond its notice distance in each of more than KEPT_FRAMES consecutive frames is reported once, in the fifth. `gap(u, row, target id, target row)` -> (distance, notice distance)
    or None; `return_fire(u)` -> whether u's current lock was taken by return fire (R-087-06), which the leash alone bounds (R-087-05)."""

    def __init__(self, gap, return_fire):
        self.gap, self.return_fire = gap, return_fire
        self.run = {}                # unit -> [target, frames beyond the notice distance, reported]

    def feed(self, frame, tick, out):
        units, visible = frame["units"], frame.get("visible")
        for u, r in units.items():
            tgt = r["target"] if r["alive"] else 0
            t = units.get(tgt) if tgt else None
            g = self.gap(u, r, tgt, t) if t is not None and t["alive"] else None
            seen = r.get("seen", True) if visible is None else tgt in visible.get(r["side"], ())
            if g is None or not seen or g[0] <= g[1]:
                self.run.pop(u, None)
                continue
            run = self.run.get(u)
            if run is None or run[0] != tgt:
                run = self.run[u] = [tgt, 0, False]
            run[1] += 1
            if run[1] > KEPT_FRAMES and not run[2] and not self.return_fire(u):
                run[2] = True
                out.append({"rule": "R-087-03", "tick": tick, "unit": u, "detail": "holds %d, %.1f wu away, beyond its notice distance %.1f, for %d frames (a lock ends there, R-087-03)" % (
                    tgt, g[0], g[1], run[1])})


class UnseenFire:
    """R-087-01. Rows carry "dest" ((x, y) or None) and "attack_move" (True when the standing order is an attack-move); a row without "attack_move" is not judged.
    An unseen hit is a (attacker, victim) of the frame's "hits" (or "fires") with the victim alive and holding no target in the previous frame, the attacker in neither the previous nor this
    frame's visible set of the victim's side.
      on the way  an attack-mover with a destination and no target, in the UNSEEN_WINDOW frames after an unseen hit on it (the hit frame excluded), is a violation in a frame in which it
                  did not move (no unit within the push radius) or its destination changed under an unchanged order token: "neither moved nor stopped by such a hit".
      once        a run is a stretch of frames in which a unit with no target and no guard post moves under its own power (not a collision push, no new order), begun from no destination. A run
                  that begins when the unit's previous run followed an unseen hit and no unseen hit has landed on it since that run began is a violation in its first frame: "it holds where
                  the move away ends". A unit whose first run followed no hit (a leash return, a new order) is not judged; a target or a new order forgets the previous run."""

    def __init__(self, guards, pushed, disp):
        self.guards, self.pushed, self.disp = guards, pushed, disp
        self.last_hit = {}           # unit -> tick of the latest unseen hit on it
        self.prev_run = {}           # unit -> (tick its previous run began, whether that run followed an unseen hit)
        self.running = set()         # units inside a run now

    def _unseen_hits(self, frame, prev):
        units, vis_now, vis_prev = frame["units"], frame.get("visible"), prev.get("visible") if prev else None
        if vis_now is None or vis_prev is None:
            return set()
        out = set()
        for a, b in frame.get("hits", frame.get("fires", [])):
            v, pv = units.get(b), prev["units"].get(b)
            if v is None or not v["alive"] or pv is None or pv["target"] or a in vis_now.get(v["side"], ()) or a in vis_prev.get(v["side"], ()):
                continue
            out.add(b)
        return out

    def feed(self, frame, prev, tick, out):
        if prev is None:
            return
        hit = self._unseen_hits(frame, prev)
        for u, r in frame["units"].items():
            p = prev["units"].get(u)
            if "attack_move" not in r or p is None or not p["alive"] or not r["alive"]:
                continue
            if p.get("order") != r.get("order"):
                for d in (self.last_hit, self.prev_run):
                    d.pop(u, None)
                self.running.discard(u)
            if u in hit:
                self.last_hit[u] = tick
            dest, moved = r.get("dest"), self.disp(p, r)
            hit_at = self.last_hit.get(u)
            if r["attack_move"] and dest is not None and not r["target"] and hit_at is not None and 0 < tick - hit_at <= UNSEEN_WINDOW:
                stopped = moved <= OWN_MOVE and not self.pushed(frame, u)
                if stopped or (p.get("dest") is not None and p["dest"] != dest and not p["target"]):
                    out.append({"rule": "R-087-01", "tick": tick, "unit": u, "detail": "an attack-mover on its way %s %d frames after a hit it could not see" % (
                        "stood still" if stopped else "was given another destination", tick - hit_at)})
            if r["target"] or u in self.guards:
                self.prev_run.pop(u, None)
                self.running.discard(u)
            elif moved <= OWN_MOVE:
                if u in self.running and not self.pushed(frame, u):      # a collision push neither starts nor ends a run
                    self.running.discard(u)
            elif u not in self.running and p.get("dest") is None and not self.pushed(frame, u):
                before = self.prev_run.get(u)
                followed = hit_at is not None and (before is None or hit_at >= before[0])
                if before is not None and before[1] and not followed:
                    out.append({"rule": "R-087-01", "tick": tick, "unit": u, "detail": "moved again with no new hit it could not see (its move away of tick %d should have held)" % before[0]})
                self.prev_run[u] = (tick, followed)
                self.running.add(u)


class SlopeCollision:
    """R-097-05. `slope_at(x, y)` -> a hashable id of the slope the point lies on (one id per hill), or None.
      pair  two living units within SLOPE_GAP - SLOPE_SLACK wu of each other (the plane) that both stand on one slope, any layers, are a violation of the lower id in the frame the pair comes
            that close, once while it stays close: the collision pass pushes such a pair apart.
      flip  a unit on a slope whose layer changes in FLIP_CHANGES frames inside FLIP_WINDOW is a violation in the last of them (the changes are forgotten after the report)."""

    def __init__(self, slope_at):
        self.slope_at = slope_at
        self.close = set()           # pairs reported and still close
        self.changes = {}            # unit -> ticks of its recent layer changes

    def feed(self, frame, prev, tick, out):
        on, now = {}, set()
        for u, r in frame["units"].items():
            s = self.slope_at(r["x"], r["y"]) if r["alive"] else None
            if s is not None:
                on.setdefault(s, []).append(u)
            p = prev["units"].get(u) if prev else None
            if p is not None and p["alive"] and r["alive"] and p["layer"] != r["layer"] and (s is not None or self.slope_at(p["x"], p["y"]) is not None):
                ch = [t for t in self.changes.get(u, []) if tick - t <= FLIP_WINDOW] + [tick]
                self.changes[u] = ch
                if len(ch) >= FLIP_CHANGES:
                    self.changes[u] = []
                    out.append({"rule": "R-097-05", "tick": tick, "unit": u, "detail": "changed layer %d times in %d frames on a slope (a flip across the midline)" % (len(ch), tick - ch[0])})
        for ids in on.values():
            ids.sort()
            for i, a in enumerate(ids):
                ra = frame["units"][a]
                for b in ids[i + 1:]:
                    rb = frame["units"][b]
                    d = math.hypot(ra["x"] - rb["x"], ra["y"] - rb["y"])
                    if d < SLOPE_GAP - SLOPE_SLACK:
                        now.add((a, b))
                        if (a, b) not in self.close:
                            out.append({"rule": "R-097-05", "tick": tick, "unit": a, "detail": "%d and %d stand %.1f wu apart on one slope (layers %d and %d), under %.0f wu after the collision pass" % (
                                a, b, d, ra["layer"], rb["layer"], SLOPE_GAP)})
        self.close = now


class _Slope(ctypes.Structure):
    """csrc/ouroboros_sim.h om_slope."""
    _fields_ = [("x0", ctypes.c_double), ("y0", ctypes.c_double), ("x1", ctypes.c_double), ("y1", ctypes.c_double), ("mx", ctypes.c_double), ("my", ctypes.c_double),
                ("length", ctypes.c_double), ("lower_band", ctypes.c_int32), ("upper_band", ctypes.c_int32)]


def slope_at_for(engine, world, cell=100.0):
    """The `Rules.slope_at` of a world with terrain: (x, y) -> an id shared by every point of one hill's slopes, or None.
    The engine lists a slope as a straight run of cells across one band boundary (om_terrain_slope_get, up to 64 cells a side), so `om_terrain_slope_at` answers for flat ground far
    from the ramp too. A point counts as on a slope here only when its cell's centre lies within SLOPE_NEAR of the record's midline (mx, my) along the run, and the records of one hill
    (a radial hill is many one-cell strips) are joined into one id when their near cells touch, diagonals included. Built once, read as a dict."""
    lib = engine._lib
    lib.om_terrain_slope_count.argtypes = [ctypes.c_void_p]
    lib.om_terrain_slope_count.restype = ctypes.c_uint32
    lib.om_terrain_slope_get.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_Slope)]
    lib.om_terrain_slope_get.restype = ctypes.c_int
    cells = {}                               # (cx, cy) -> record indices
    for i in range(lib.om_terrain_slope_count(world)):
        s = _Slope()
        if lib.om_terrain_slope_get(world, i, ctypes.byref(s)) != 0:
            continue
        lox, hix = sorted((int(s.x0 // cell), int(s.x1 // cell)))
        loy, hiy = sorted((int(s.y0 // cell), int(s.y1 // cell)))
        for cx in range(lox, hix + 1):
            for cy in range(loy, hiy + 1):
                along = abs((cx + 0.5) * cell - s.mx) if hix > lox else abs((cy + 0.5) * cell - s.my)
                if along <= SLOPE_NEAR:
                    cells.setdefault((cx, cy), []).append(i)
    parent = {}

    def find(i):
        while parent.setdefault(i, i) != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for (cx, cy), ids in cells.items():
        for i in ids[1:]:
            parent[find(i)] = find(ids[0])
        for dx, dy in ((1, -1), (1, 0), (1, 1), (0, 1)):          # each pair of neighbouring cells once
            for j in cells.get((cx + dx, cy + dy), ()):
                parent[find(j)] = find(ids[0])
    ident = {c: find(ids[0]) for c, ids in cells.items()}

    def slope_at(x, y):
        return ident.get((int(x // cell), int(y // cell))) if x >= 0.0 and y >= 0.0 else None
    return slope_at
