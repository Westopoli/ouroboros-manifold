"""Engine rules Round 5, G7 (docs/northstar/plans/engine-rules-2026-11-08/round5.md): the predicates the lab checker (`invariants.py`) gained for Westley's rulings of 2026-11-17.

  LockKept        R-087-03  a lock kept on a target beyond the notice distance for more than one cohort period (a return-fire lock excepted)
  UnseenFire      R-087-01  an attack-mover on its way is neither stopped nor re-routed by a hit it cannot see; an idle unit or an arrived attack-mover moves away once and holds
  SlopeCollision  R-097-05  two units within 30 wu on one slope

Each is a small state machine fed one frame at a time by `invariants._Checker.feed`; the frame, row and `Rules` shapes are those of `invariants.py` (this module imports nothing from it, so the
checker can import these constants). The notice distance itself (`NOTICE_MARGIN`, `notice_distance`) is read by the checker's acquire and swap checks as well.
Tests: tests/skilllab/arena/test_invariants_r5_notice_and_lock.py, test_invariants_r5_unseen_fire_and_slope.py. Every number below is a DRAFT constant, Westley's to change:
  DRAFT-notice-margin 0.1   DRAFT-unseen-fire-window 60 frames   DRAFT-slope-slack 2 wu   DRAFT-slope-settle-ticks 3   DRAFT-slope-crowd 31 wu    DRAFT-slope-near 100 wu (the Monitor's idea of "on a slope")
"""
import ctypes
import math

NOTICE_MARGIN = 0.1          # DRAFT-notice-margin (R-087-04): a unit's notice distance is its attack range times (1 + this), measured as weapon reach is (R-087-10)
KEPT_FRAMES = 4              # R-087-08: one cohort period; a lock is reported in the frame after this many frames beyond the notice distance
UNSEEN_WINDOW = 60           # DRAFT-unseen-fire-window: frames after an unseen hit in which an attack-mover on its way must keep walking (the 60-tick HIT_GAP of the Round 4 unseen oracle)
PURSUIT_MEMORY = 8           # DRAFT-pursuit-memory (frames): a unit that held a target this recently is ending a pursuit, whose destination was the target's place; the walk back to its point (R-087-06) is no re-route by a hit
BACKSWING_TICKS = 10         # R-084-04 (the checker's own constant, repeated): ticks 1 to 9 after a shot are the pause, in which a unit that fired stands
OWN_MOVE = 0.5               # a displacement above it counts as "moved" (the checker's own constant, repeated: this module cannot import invariants)
SLOPE_GAP = 30.0             # R-097-05: 2 x unit radius 15 wu
SLOPE_SLACK = 2.0            # DRAFT-slope-slack: a pair this close to 30 wu counts as pushed apart (the sweep's I13: 28 wu; the engine resolves a pair on a slope at most a pace plus 1 wu a tick, om_move_slope_clamp)
SLOPE_SETTLE_TICKS = 3       # DRAFT-slope-settle-ticks (Architect, round5.md "Third pass"): the step limit on a slope (om_move_slope_clamp) may leave a pair under 30 wu at the end of a tick; it is apart again within this many ticks
SLOPE_CROWD = 31.0           # DRAFT-slope-crowd (wu): a third unit this near a pair (touching, 30 wu and a rounding) is a crowd the 3-iteration pass can leave closer than 30 wu
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
    An unanswerable hit is a (attacker, victim) of the frame's "hits" (or "fires") with the victim alive and holding no target in the previous frame, the attacker either outside the victim's
    layer reach ("see or reach", R-087-01: `in_reach(victim, victim layer, attacker layer)` false) or in neither the previous nor this frame's visible set of the victim's side.
      on the way  an attack-mover with a destination and no target, in the UNSEEN_WINDOW frames after an unseen hit on it (the hit frame excluded), is a violation in a frame in which it
                  did not move (no unit within the push radius) or its destination changed under an unchanged order token, unless it held a target in the PURSUIT_MEMORY frames before (a pursuit
                  ending: the walk back to its point): "neither moved nor stopped by such a hit". A unit that held a target after the hit, or is within BACKSWING_TICKS - 1 frames of its own
                  shot, stands for that reason (R-084-04, R-087-06), not for the hit. A unit that
                  was standing in the frame of the hit and the frame before it (between two targets, waiting its cohort turn) was not stopped by the hit and is not judged for standing.
      once        a run is a stretch of frames in which a unit with no target and no guard post moves under its own power (not a collision push, no new order), begun from no destination. A run
                  that begins when the unit's previous run followed an unseen hit and no unseen hit has landed on it since that run began is a violation in its first frame: "it holds where
                  the move away ends". A unit whose first run followed no hit (a leash return, a new order) is not judged; a target or a new order forgets the previous run."""

    def __init__(self, guards, pushed, disp, in_reach=None):
        self.guards, self.pushed, self.disp, self.in_reach = guards, pushed, disp, in_reach
        self.last_hit = {}           # unit -> tick of the latest unseen hit on it
        self.prev_run = {}           # unit -> (tick its previous run began, whether that run followed an unseen hit)
        self.running = set()         # units inside a run now
        self.shot = {}               # unit -> the last frame in which it fired (the backswing of R-084-04 holds it standing)
        self.held = {}               # unit -> the last frame in which it held a target (R-087-06: a pursuit ends at the next cohort turn after its target is gone, and the unit walks back to its point)
        self.moving = {}             # unit -> whether it moved under no push in the previous frame, the frame of the latest unseen hit on it
        self.walking_at_hit = {}     # unit -> whether it was walking in the frame of its latest unseen hit or the one before

    def _unseen_hits(self, frame, prev):
        units, vis_now, vis_prev = frame["units"], frame.get("visible"), prev.get("visible") if prev else None
        if vis_now is None or vis_prev is None:
            return set()
        out = set()
        for a, b in frame.get("hits", frame.get("fires", [])):
            v, pv = units.get(b), prev["units"].get(b)
            if v is None or not v["alive"] or pv is None or pv["target"]:
                continue
            at = units.get(a)
            reachable = self.in_reach is None or at is None or self.in_reach(b, v["layer"], at["layer"])
            if reachable and (a in vis_now.get(v["side"], ()) or a in vis_prev.get(v["side"], ())):
                continue
            out.add(b)
        return out

    def feed(self, frame, prev, tick, out):
        if prev is None:
            return
        hit = self._unseen_hits(frame, prev)
        for a, _ in frame.get("fires", []):
            self.shot[a] = tick
        for u, r in frame["units"].items():
            p = prev["units"].get(u)
            if "attack_move" not in r or p is None or not p["alive"] or not r["alive"]:
                continue
            if p.get("order") != r.get("order"):
                for d in (self.last_hit, self.prev_run):
                    d.pop(u, None)
                self.running.discard(u)
            dest, moved = r.get("dest"), self.disp(p, r)
            if u in hit:
                self.last_hit[u] = tick
                self.walking_at_hit[u] = moved > OWN_MOVE or self.moving.get(u, False)
            self.moving[u] = moved > OWN_MOVE
            if r["target"]:
                self.held[u] = tick
            hit_at = self.last_hit.get(u)
            if r["attack_move"] and dest is not None and not r["target"] and hit_at is not None and 0 < tick - hit_at <= UNSEEN_WINDOW:
                stopped = (moved <= OWN_MOVE and not self.pushed(frame, u) and self.walking_at_hit.get(u, True)
                           and not self.held.get(u, -1) > hit_at and tick - self.shot.get(u, -BACKSWING_TICKS) > BACKSWING_TICKS - 1)
                rerouted = p.get("dest") is not None and p["dest"] != dest and not p["target"] and tick - self.held.get(u, -PURSUIT_MEMORY - 1) > PURSUIT_MEMORY
                if stopped or rerouted:
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
      pair  two living units within SLOPE_GAP - SLOPE_SLACK wu of each other (the plane) that both stand on one slope, any layers, are a violation of the lower id in the frame the pair has stayed that close for more than
            SLOPE_SETTLE_TICKS consecutive frames (the fourth), once while it stays close: the collision pass pushes such a pair apart within a few ticks, the step limit on a slope may leave it closer meanwhile. A pair with a third living unit within SLOPE_CROWD of either is excused: the pass runs at most
            three iterations a tick, and a crowd can leave a pair closer ("except when the pass hits its iteration cap", E-13 Invariants)."""

    def __init__(self, slope_at):
        self.slope_at = slope_at
        self.close = {}              # pair -> consecutive frames it has been close (reported in the frame the count passes SLOPE_SETTLE_TICKS)

    def feed(self, frame, prev, tick, out):
        on, now = {}, {}
        for u, r in frame["units"].items():
            s = self.slope_at(r["x"], r["y"]) if r["alive"] else None
            if s is not None:
                on.setdefault(s, []).append(u)
        for ids in on.values():
            ids.sort()
            for i, a in enumerate(ids):
                ra = frame["units"][a]
                for b in ids[i + 1:]:
                    rb = frame["units"][b]
                    d = math.hypot(ra["x"] - rb["x"], ra["y"] - rb["y"])
                    if d < SLOPE_GAP - SLOPE_SLACK and not self._crowded(frame, a, b):
                        now[(a, b)] = self.close.get((a, b), 0) + 1
                        if now[(a, b)] == SLOPE_SETTLE_TICKS + 1:
                            out.append({"rule": "R-097-05", "tick": tick, "unit": a, "detail": "%d and %d stand %.1f wu apart on one slope (layers %d and %d), under %.0f wu after the collision pass" % (
                                a, b, d, ra["layer"], rb["layer"], SLOPE_GAP)})
        self.close = now


    @staticmethod
    def _crowded(frame, a, b):
        """A third living unit within SLOPE_CROWD of a or b (the pass's 3-iteration cap can leave such a pair closer than 30 wu)."""
        units = frame["units"]
        for c, rc in units.items():
            if c in (a, b) or not rc["alive"]:
                continue
            for e in (a, b):
                if math.hypot(rc["x"] - units[e]["x"], rc["y"] - units[e]["y"]) < SLOPE_CROWD:
                    return True
        return False


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
