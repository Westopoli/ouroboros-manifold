"""F0 (engine rule fixes 2026-11-08): the whole-run rule checker of the lab.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F0"; the API is pinned by tests/skilllab/test_invariants.py and
tests/skilllab/arena/test_invariants_wiring.py. Evidence: docs/reports/2026-11-07-rule-enforcement.md and the sweep's predicates in
docs/reports/2026-11-07-rule-enforcement/sweep/inv_check.py (reused here, not copied whole).

Two layers:
  check(trace, rules, only=None) -> Report      pure predicates over a recorded per-tick trace (frame 0 is the state before the first step, frame k the
                                                 state after step k, with that step's shots); the class `_Checker` consumes one frame at a time, so a
                                                 fight of 12,000 ticks is not re-scanned every tick
  Monitor(engine, world, width, height, sight)  the online wrapper `run.fight` uses: reads the engine after each step, builds the frame, feeds `_Checker`

Round 2 (engine rules, 2026-11-11) adds: R-087-03 acquisitions (nearest seen enemy, cohort turn, return fire), R-093-02 (fire only at the side's visible set of the previous
frame), R-087-09 only within attack range, continuity judging layer changes (not every push), R-096-08 (guard leash) and R-087-10 (spherical range of a shot). `watch` is the entry the lab
fights use (fight.fight, search.run_search); `Blind` stands in for an engine the checker cannot read. A violation is {"rule", "tick", "unit", "detail"}. The cell test of R-207-06 is the engine's own `om_navmesh_is_cell_blocked` (the Monitor binds it),
never a Python re-derivation. Every number below is a DRAFT constant, Westley's to change:
  DRAFT-inv-cell-depth 1 wu     DRAFT-inv-push-radius 40 wu     DRAFT-inv-stuck-ticks 20     DRAFT-inv-step-slack 1.3 wu
and, Round 2: DRAFT-inv-nearest-tol 1 wu  DRAFT-inv-return-fire-ticks 4  DRAFT-guard-radius 200 wu  DRAFT-guard-leash-slack 1 wu  DRAFT-f7-slant-slack 1 wu
and OWN_MOVE 0.5 wu (a displacement above it counts as "moved"), BACKSWING_TICKS 10 (ticks 1 to 9 after a shot are the pause, R-084-04), HEAL_ONE 0.075 hp
(R-083-03), LEASH_SLACK 25 wu (a unit this close to its leash, or past it, is excused: the engine drops the lock at the leash itself).
"""
import collections
import ctypes
import math

RULES = ("R-207-06", "R-207-07", "R-087-04", "R-084-04", "R-087-03", "R-087-09", "R-083-03", "continuity", "R-093-02", "R-096-08", "R-087-10")

CELL = 100.0                 # the engine's cell, wu (OM_NAVMESH_CELL_SIZE)
DEPTH_TOL = 1.0              # DRAFT-inv-cell-depth
PUSH_RADIUS = 40.0           # DRAFT-inv-push-radius
STUCK_TICKS = 20             # DRAFT-inv-stuck-ticks
STEP_SLACK = 1.3             # DRAFT-inv-step-slack
OWN_MOVE = 0.5
BACKSWING_TICKS = 10
HEAL_ONE = 0.075
LEASH_SLACK = 25.0
GUARD_RADIUS = 200.0         # R-096-08 (DRAFT-guard-radius, Westley's): how far from its post a guard may stand
GUARD_SLACK = 1.0            # DRAFT-guard-leash-slack
SLANT_SLACK = 1.0            # DRAFT-f7-slant-slack: a shot may exceed the attacker's range by this much (the same tick's push pass moves a unit by under 1 wu)
TICK_RATE = 20               # scripts/skilllab/fight.py TICKS_PER_SECOND
NEAREST_TOL = 1.0            # DRAFT-inv-nearest-tol: an acquired target within this much of the nearest eligible enemy counts as the nearest (R-087-03)
RETURN_FIRE_TICKS = 4        # DRAFT-inv-return-fire-ticks: a hit by the target in the frame of the acquisition or the 3 before it is return fire (R-087-06)
COHORT_SLOTS = 4             # R-087-08: a unit acquires at its cohort turn on every 4th tick


UNBOUNDED_CANVAS = "canvas unbounded (no terrain)"    # the reason R-207-07 is suspended on an inf x inf canvas


class Rules:
    """What the checks need to know about the world. blocked_cell(cx, cy, layer) -> bool; max_step {unit id: wu a tick}; sensor_radius {unit id: wu}, the radius a unit
    may walk from its anchor before the leash (R-087-05) drops its target, the Monitor passes max(sensor radius, weapon range); suspended {rule: switch};
    cohort {unit id: slot 0..3} (R-087-03 / R-087-08 acquisitions are checked only for units that have one)."""

    def __init__(self, width, height, blocked_cell=None, max_step=None, sensor_radius=None, suspended=None, reach=None, cohort=None, attack_range=None, guards=None, layer_heights=None,
                 range_mult=None):
        self.range_mult = range_mult or (lambda la, lb: 1.0)   # (shooter layer, target layer) -> the reach table's range multiplier (OM_TP_RANGE_UP_n / DOWN_n); 1.0 on one layer
        self.guards = guards if guards is not None else {}     # {unit id: (post x, post y)}: R-096-08 judges these units only (the Monitor shares the engine's live dict)
        self.layer_heights = layer_heights or []              # band floor height of each layer, wu (om_terrain_band_heights); empty: a flat world
        self.cohort = cohort or {}
        self.attack_range = attack_range or {}     # {unit id: wu}: R-087-09 judges a held target only inside it; no entry: always inside
        self.width, self.height = float(width), float(height)
        self.reach = reach or {}      # {unit id: (layers up, layers down)}: a locked target that moves beyond it is dropped by the engine (R-164-02), not swapped
        self.blocked_cell = blocked_cell
        self.max_step = max_step or {}
        self.sensor_radius = sensor_radius or {}
        self.suspended = suspended or {}


class Report:
    def __init__(self, violations, suspended):
        self.violations = violations
        self.suspended = suspended

    @property
    def invalid(self):
        return bool(self.violations)


def _violation(rule, tick, unit, detail):
    return {"rule": rule, "tick": tick, "unit": unit, "detail": detail}


class _Checker:
    """The checks, one frame at a time. `feed(frame)` returns the violations of that frame ordered by (rule, unit); the caller keeps them in tick order."""

    def __init__(self, rules, only=None):
        self.rules = rules
        wanted = set(RULES if only is None else only)
        self.on = {r for r in wanted if r not in rules.suspended}
        self.suspended = {r: rules.suspended[r] for r in sorted(wanted) if r in rules.suspended}
        if "R-207-07" in self.on and not (math.isfinite(rules.width) and math.isfinite(rules.height)):
            self.on.discard("R-207-07")       # no terrain, no map to be outside of: a lab fight hands the checker inf x inf (see `watch`)
            self.suspended["R-207-07"] = UNBOUNDED_CANVAS
        self.prev = None
        self.last_shot = {}          # unit -> tick of its last shot (R-084-04)
        self.lock = {}               # unit -> (target, (x, y) where it took that lock) (R-087-03)
        self.stuck = {}              # unit -> [target, frames not shootable, first distance, flagged] (R-087-09), a target inside attack range: the violation check
        self.unshot = {}             # the same run for a target at any distance: the engine's give-up window (csrc/unit.c om_tac_giveup), which the swap excuse reads
        self.breached = set()        # guards outside their radius now (R-096-08: one violation per breach, not one per frame)
        self.hit_hist = collections.deque(maxlen=RETURN_FIRE_TICKS)   # the (attacker, victim) pairs of the last frames, this one included (R-087-06)

    # -- helpers
    @staticmethod
    def _disp(a, b):
        return math.hypot(b["x"] - a["x"], b["y"] - a["y"])

    def _pushed(self, frame, u):
        """Another living unit within PUSH_RADIUS of the unit at either end of the frame (its own two positions against the other's two): a collision push."""
        prev, now = self.prev["units"], frame["units"]
        for o in set(prev) | set(now):
            if o == u:
                continue
            p0, p1 = prev.get(o), now.get(o)
            if not ((p0 and p0["alive"]) or (p1 and p1["alive"])):
                continue
            for a in (prev[u], now[u]):
                for b in (p0 or p1, p1 or p0):
                    if math.hypot(b["x"] - a["x"], b["y"] - a["y"]) < PUSH_RADIUS:
                        return True
        return False

    def _repaired(self, p, r):
        """The unit started the frame inside a blocked cell of its starting layer, or on a cell blocked for the layer it ends on: the blocked-cell repair (R-207-06) placed it
        and the checker cannot see that flag, so continuity does not judge it this frame."""
        blocked = self.rules.blocked_cell
        if blocked is None or p["x"] < 0.0 or p["y"] < 0.0:
            return False
        cx, cy = int(p["x"] // CELL), int(p["y"] // CELL)
        return bool(blocked(cx, cy, p["layer"]) or blocked(cx, cy, r["layer"]))

    def _depth(self, x, y, layer):
        """Distance to the nearest face of the blocked cell (x, y) is in that borders an open cell; 1e9 when no neighbour is open."""
        cx, cy = int(x // CELL), int(y // CELL)
        best = 1e9
        for dx, dy, d in ((-1, 0, x - cx * CELL), (1, 0, (cx + 1) * CELL - x), (0, -1, y - cy * CELL), (0, 1, (cy + 1) * CELL - y)):
            if cx + dx >= 0 and cy + dy >= 0 and not self.rules.blocked_cell(cx + dx, cy + dy, layer):
                best = min(best, d)
        return best

    # -- one frame
    def feed(self, frame):
        tick, units, prev = frame["tick"], frame["units"], self.prev
        on, rules, out = self.on, self.rules, []
        fires = frame.get("fires", [])
        self.hit_hist.append(set(frame.get("hits", fires)))
        shooters = {a for a, _ in fires}
        hit = {b for _, b in fires}
        for u in sorted(units):
            r = units[u]
            alive = r["alive"]
            p = prev["units"].get(u) if prev else None
            if alive and "R-207-07" in on and not (0.0 <= r["x"] <= rules.width and 0.0 <= r["y"] <= rules.height):
                out.append(_violation("R-207-07", tick, u, "at (%.1f, %.1f) outside the %.0f x %.0f canvas" % (r["x"], r["y"], rules.width, rules.height)))
            if alive and "R-207-06" in on and rules.blocked_cell is not None and r["x"] >= 0.0 and r["y"] >= 0.0:
                cx, cy = int(r["x"] // CELL), int(r["y"] // CELL)
                if rules.blocked_cell(cx, cy, r["layer"]):
                    depth = self._depth(r["x"], r["y"], r["layer"])
                    if depth > DEPTH_TOL:
                        out.append(_violation("R-207-06", tick, u, "at (%.1f, %.1f), %s wu inside blocked cell (%d, %d) of layer %d" % (
                            r["x"], r["y"], "%.1f" % depth if depth < 1e8 else "far", cx, cy, r["layer"])))
            if alive and "R-096-08" in on and u in rules.guards:
                away = math.hypot(r["x"] - rules.guards[u][0], r["y"] - rules.guards[u][1])
                if away > GUARD_RADIUS + GUARD_SLACK:
                    if u not in self.breached:
                        self.breached.add(u)
                        out.append(_violation("R-096-08", tick, u, "guard ended the frame %.1f wu from its post (radius %.0f + %.0f)" % (away, GUARD_RADIUS, GUARD_SLACK)))
                else:
                    self.breached.discard(u)
            if p is not None and p["alive"] and alive:
                moved = self._disp(p, r)
                if "R-087-04" in on and u in shooters and moved > OWN_MOVE and not self._pushed(frame, u):
                    out.append(_violation("R-087-04", tick, u, "fired on a tick it moved %.2f wu under its own power" % moved))
                lf = self.last_shot.get(u)
                if "R-084-04" in on and u not in shooters and lf is not None and 1 <= tick - lf <= BACKSWING_TICKS - 1 and moved > OWN_MOVE and not self._pushed(frame, u):
                    out.append(_violation("R-084-04", tick, u, "moved %.2f wu %d ticks after its shot at tick %d" % (moved, tick - lf, lf)))
                if "R-083-03" in on and u not in hit and r["hp"] - p["hp"] > HEAL_ONE + 1e-6:
                    out.append(_violation("R-083-03", tick, u, "hp rose %.4f in a tick nothing hit it (one Warden heals %.3f)" % (r["hp"] - p["hp"], HEAL_ONE)))
                step = rules.max_step.get(u)
                if ("continuity" in on and step is not None and moved > step + STEP_SLACK and not self._repaired(p, r)
                        and (p["layer"] != r["layer"] or not self._pushed(frame, u))):
                    out.append(_violation("continuity", tick, u, "moved %.2f wu in a tick (at most %.2f + %.1f), layer %d to %d" % (
                        moved, step, STEP_SLACK, p["layer"], r["layer"])))
            if "R-087-03" in on:
                self._lock(frame, u, r, p, tick, out)
                if u in rules.cohort:
                    self._acquire(frame, u, r, p, tick, out)
            if "R-087-09" in on or "R-087-03" in on:
                self._held(units, u, r, tick, out)
        if "R-087-10" in on:
            self._slant(frame, tick, out)
        if "R-093-02" in on and prev is not None and "visible" in prev:
            self._sight(frame, prev["visible"], tick, out)
        for a in shooters:
            self.last_shot[a] = tick
        self.prev = frame
        out.sort(key=lambda v: (v["rule"], v["unit"]))
        return out

    @staticmethod
    def _in_reach(reach, mine, theirs):
        """csrc/unit.c om_tac_in_reach: the same layer, or within the type's reach up / down."""
        if mine == theirs:
            return True
        return theirs - mine <= reach[0] if theirs > mine else mine - theirs <= reach[1]

    def _lock(self, frame, u, r, p, tick, out):
        """R-087-03. The leash (R-087-05) is its own rule and breaks a lock; the engine measures it from the unit's anchor, the place where its run of targets
        began (a change of target, or a pause with no target, keeps it; a new order resets it), by max(sensor radius, weapon range)."""
        tgt = r["target"] if r["alive"] else 0
        held = self.lock.get(u)
        if p is not None and p["alive"] and r["alive"] and p["target"] and tgt and tgt != p["target"]:
            old = p["target"]
            o_prev, o_now = self.prev["units"].get(old), frame["units"].get(old)
            seen = p.get("seen", True) and r.get("prev_seen", r.get("seen", True))
            same_order = p.get("order") == r.get("order")
            leash = self.rules.sensor_radius.get(u)
            anchor = held[1] if held else (p["x"], p["y"])
            walked = math.hypot(r["x"] - anchor[0], r["y"] - anchor[1])
            reach = self.rules.reach.get(u)
            out_of_reach = reach is not None and any(not self._in_reach(reach, a["layer"], o["layer"]) for a, o in ((p, o_prev), (r, o_now)) if o)
            if (o_prev and o_now and o_prev["alive"] and o_now["alive"] and seen and same_order and not out_of_reach
                    and not (leash is not None and walked > leash - LEASH_SLACK)):
                why = self._gave_up(u, old, p, o_prev)
                if why is None:
                    out.append(_violation("R-087-03", tick, u, "target %d -> %d while %d was alive and seen" % (old, tgt, old)))
        if p is not None and p.get("order") != r.get("order"):
            held = None                      # a new order starts a new anchor
            self.lock.pop(u, None)
        if tgt and (not held or held[0] != tgt):
            self.lock[u] = (tgt, held[1] if held else (r["x"], r["y"]))   # the anchor stays through a pause with no target: an attack-mover keeps it while it pursues

    def _slant(self, frame, tick, out):
        """R-087-10. A shot's distance is spherical: the horizontal distance and the band-height difference of the two layers together. No shot is fired at a target
        beyond the attacker's attack range by that measure (plus SLANT_SLACK). Both ends are read in the frame the shot was reported in."""
        units, heights = frame["units"], self.rules.layer_heights
        for a, b in frame.get("fires", []):
            reach = self.rules.attack_range.get(a)
            if reach is None or a not in units or b not in units:
                continue
            ra, rb = units[a], units[b]
            dz = heights[rb["layer"]] - heights[ra["layer"]] if ra["layer"] < len(heights) and rb["layer"] < len(heights) else 0.0
            slant = math.hypot(self._disp(ra, rb), dz)
            if slant > reach + SLANT_SLACK:
                out.append(_violation("R-087-10", tick, a, "fired at %d, %.1f wu away by slant (%.1f horizontal, %.0f in height), range %.0f" % (b, slant, self._disp(ra, rb), dz, reach)))

    @staticmethod
    def _sight(frame, visible, tick, out):
        """R-093-02. A unit that fires at, or holds, a living target has it in its side's visible set of the previous frame (the state before the step that decided
        it; a shot that kills the target takes it out of the set of its own frame). One violation per unit and frame."""
        units, said = frame["units"], set()
        for a, b in frame.get("fires", []):
            if a in units and b not in visible.get(units[a]["side"], ()):
                said.add(a)
                out.append(_violation("R-093-02", tick, a, "fired at %d, which its side did not see before the step" % b))
        for u, r in units.items():
            t = units.get(r["target"]) if r["alive"] and r["target"] else None
            if t is not None and t["alive"] and u not in said and r["target"] not in visible.get(r["side"], ()):
                out.append(_violation("R-093-02", tick, u, "holds %d, which its side did not see before the step" % r["target"]))

    def _gave_up(self, u, old, p, o_prev):
        """The rule that excuses the end of a lock, or None. R-087-09: the target was held unshootable and not closed in on for the engine's window (STUCK_TICKS, inside attack range
        or not: `om_tac_giveup` asks only whether the target can be shot; one frame less is counted here because the engine drops the lock on the tick that completes the window, which is the swap frame itself). R-096-08: a guard's target
        stood so far from its post (by slant, `_beyond_post`) that no spot inside the radius reaches it with the unit's attack range (an engaged guard that would leave the radius lets go)."""
        run = self.unshot.get(u)
        if run is not None and run[0] == old and run[1] >= STUCK_TICKS - 1:
            return "R-087-09"
        post = self.rules.guards.get(u)
        if post is not None and self._beyond_post(u, p, post, o_prev):
            return "R-096-08"
        return None

    def _beyond_post(self, u, p, post, o_prev):
        """R-096-08 (csrc/unit.c om_tac_guard_engageable): the engine drops a guard's target when it is out of the guard's range and the SLANT distance from the post to the target (horizontal
        distance and the layers' height difference) exceeds GUARD_RADIUS plus the guard's attack range times the layer-offset multiplier. Exact, no slack; judged on the state before the
        step, the previous frame (the guard's layer and the target's layer in it)."""
        heights = self.rules.layer_heights
        la, lb = p["layer"], o_prev["layer"]
        dz = heights[lb] - heights[la] if la < len(heights) and lb < len(heights) else 0.0
        limit = GUARD_RADIUS + self.rules.attack_range.get(u, 0.0) * self.rules.range_mult(la, lb)
        return math.hypot(math.hypot(o_prev["x"] - post[0], o_prev["y"] - post[1]), dz) > limit

    def _acquire(self, frame, u, r, p, tick, out):
        """R-087-03 / R-087-08 / R-087-06. An acquisition is a target other than the previous one when the previous one was none or dead in the previous frame. It is
        judged on the previous frame (the state before the step): the target is the nearest enemy that frame's visible set of the unit's side holds (planar distance,
        within the unit's layer reach), within NEAREST_TOL, and it comes on the unit's cohort turn (tick % 4 == its slot). A hit by the target on the unit in this
        frame or the RETURN_FIRE_TICKS - 1 before it is return fire, which excuses both."""
        tgt = r["target"] if r["alive"] else 0
        prev = self.prev
        if p is None or not p["alive"] or not tgt or tgt == p["target"]:
            return
        old = prev["units"].get(p["target"]) if p["target"] else None
        if old is not None and old["alive"]:
            return
        if any((tgt, u) in hits for hits in self.hit_hist):
            return
        side, vis = p["side"], prev.get("visible")
        reach = self.rules.reach.get(u)
        nearest = mine = None            # distance to the nearest eligible enemy, and to the target when it is eligible
        for e, row in prev["units"].items():
            if not row["alive"] or row["side"] == side or (vis is not None and e not in vis.get(side, ())):
                continue
            if reach is not None and not self._in_reach(reach, p["layer"], row["layer"]):
                continue
            d = self._disp(p, row)
            if e == tgt:
                mine = d
            if nearest is None or d < nearest:
                nearest = d
        if mine is None or mine > nearest + NEAREST_TOL:
            out.append(_violation("R-087-03", tick, u, "acquired %d, not the nearest enemy its side sees (%s; nearest %s wu)" % (
                tgt, "unseen, dead or out of reach" if mine is None else "%.1f wu" % mine, "none" if nearest is None else "%.1f" % nearest)))
        elif tick % COHORT_SLOTS != self.rules.cohort[u]:
            out.append(_violation("R-087-03", tick, u, "acquired %d at tick %d, off its cohort turn (slot %d)" % (tgt, tick, self.rules.cohort[u])))

    @staticmethod
    def _advance(runs, u, tgt, dist):
        """One frame of unit u's run of holding tgt unshootable: [target, frames, distance at the run's start, flagged]; it restarts on another target or when the unit closes in by more than 1 wu."""
        run = runs.get(u)
        if run is None or run[0] != tgt or dist < run[2] - 1.0:
            run = runs[u] = [tgt, 0, dist, False]
        run[1] += 1
        return run

    def _held(self, units, u, r, tick, out):
        tgt = r["target"] if r["alive"] else 0
        t = units.get(tgt) if tgt else None
        if not t or not t["alive"] or r.get("shootable", True):
            self.stuck.pop(u, None)
            self.unshot.pop(u, None)
            return
        dist = math.hypot(t["x"] - r["x"], t["y"] - r["y"])
        self._advance(self.unshot, u, tgt, dist)     # R-087-09 as the engine counts it: whether or not the target is inside attack range (the swap excuse, `_gave_up`)
        reach = self.rules.attack_range.get(u)
        if reach is not None and dist > reach:
            self.stuck.pop(u, None)          # the R-087-09 violation is about a target within attack range; its 20 ticks are consecutive in-range ticks
            return
        run = self._advance(self.stuck, u, tgt, dist)
        if run[1] > STUCK_TICKS and not run[3] and "R-087-09" in self.on:
            run[3] = True
            out.append(_violation("R-087-09", tick, u, "held target %d unshootable for %d ticks without closing in (%.0f wu away)" % (tgt, run[1], dist)))


def check(trace, rules, only=None):
    """The pure checker: every frame of `trace` through `_Checker`. Returns a Report (violations ordered by (tick, rule, unit), suspended, invalid)."""
    chk = _Checker(rules, only)
    found = []
    for frame in trace:
        found += chk.feed(frame)
    return Report(found, chk.suspended)


# ---------------------------------------------------------------------------------------------------- the online wrapper

SWITCH_TARGET_BY_SIGHT = "OM_TP_TARGET_BY_SIGHT"
KEEP = 20          # violations written to a fight document (spec: the first 20)


def suspended_for(sight):
    """{rule: switch} the checker cannot judge in a run with this `sight` ("off", "on" or "control"): sight "off" and the control (`--control sight`, the same fight with
    targeting by sight off) turn targeting by sight off, and R-087-03's clause 'leaves its side's sight' and R-093-02 have no meaning without it."""
    return {"R-087-03": SWITCH_TARGET_BY_SIGHT, "R-093-02": SWITCH_TARGET_BY_SIGHT} if sight in ("off", "control") else {}


class Monitor:
    """`run.fight` builds one after spawning and orders, and calls `after_step()` right after every `engine.step(w)`. It reads the engine's state, builds one frame
    and feeds the checker; `violations` is every violation so far ordered by (tick, rule, unit); `suspended` the {rule: switch} this run cannot judge (sight "off" turns
    targeting by sight off, so R-087-03's "leaves its side's sight" clause has no meaning there). `tick` counts `after_step` calls from 1; the constructor records
    frame 0. `new_order(ids)` tells R-087-03 that the lab gave those units a new order this tick (groups.py does, mid-fight)."""

    def __init__(self, engine, world, width, height, sight):
        self.engine, self.w = engine, world
        lib = engine._lib
        self._cell = lib.om_navmesh_is_cell_blocked
        self._cell.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        self._cell.restype = ctypes.c_int
        self._can_shoot = lib.om_combat_can_shoot
        lib.om_unit_targeting_cohort.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.om_unit_targeting_cohort.restype = ctypes.c_uint32
        lib.om_terrain_band_heights.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
        lib.om_terrain_band_heights.restype = ctypes.c_uint32
        self._ids, self._side = [], {}
        for (wa, faction), us in engine._own.items():
            if wa == world.value:
                for u in us:
                    self._ids.append(u)
                    self._side[u] = faction
        self._ids.sort()
        stats = {}
        self._max_step, self._sensor, self._reach, self._range, self._aoe, cohort = {}, {}, {}, {}, {}, {}
        down = engine.get_param(world, engine.param_id("OM_TP_SLOPE_DOWN_MULT"))
        for u in self._ids:
            t = engine._fast_unit_type(world, u)       # read once per unit and world, shared with firing.py (the lab's read-count budget)
            st = stats.get(t) or stats.setdefault(t, engine.type_stats(world, t))
            self._max_step[u] = st["speed"] * max(1.0, down) / TICK_RATE
            self._sensor[u] = max(st["sensor_radius"], st["attack_range"])   # the leash, om_tac_leash in csrc/unit.c
            self._reach[u] = engine.profile_reach(world, t)
            self._range[u], self._aoe[u] = st["attack_range"], st["aoe_radius"]
            cohort[u] = lib.om_unit_targeting_cohort(world, u)
        buf = (ctypes.c_double * 8)()
        heights = list(buf)[:lib.om_terrain_band_heights(world, buf, 8)]
        up = [1.0] + [engine.get_param(world, engine.param_id("OM_TP_RANGE_UP_%d" % n)) for n in range(1, 5)]       # csrc/unit.c om_tac_offset_mult, OM_REACH_MAX_OFFSET 4
        dn = [1.0] + [engine.get_param(world, engine.param_id("OM_TP_RANGE_DOWN_%d" % n)) for n in range(1, 5)]
        self._range_mult = lambda la, lb: 1.0 if la == lb else ((up if lb > la else dn)[abs(lb - la)] if abs(lb - la) <= 4 else 1.0)
        self._enemies = {s: [u for u in self._ids if self._side[u] != s] for s in set(self._side.values())}
        self._cache = {}
        self._terrain = bool(engine._lib.om_terrain_band_at(world, 0.0, 0.0) > 0)   # a world with no terrain reads band 0 everywhere
        self._posts = {}            # {guard id: (x, y)} where each stood when the lab ordered it to guard; the checker's Rules.guards
        self._chk = _Checker(Rules(width, height, self._blocked, self._max_step, self._sensor, suspended_for(sight), self._reach, cohort, self._range,
                                   self._posts, heights, self._range_mult))
        self.suspended = dict(self._chk.suspended)
        self.violations = []
        self.tick = 0
        self._ordered = set()
        self._token = {u: 0 for u in self._ids}
        self._frame = self._read(0, [])
        self._chk.feed(self._frame)

    def _blocked(self, cx, cy, layer):
        """The engine's own cell test, `om_navmesh_is_cell_blocked`. On a terrain world its bits also hold the ground (R-200-02: layers below a cell's band minus one are
        blocked); that is not a box, wall or building, and a walker climbs a slope cell through it (R-207-06 covers planar obstacles, not slope cells: spec F1), so a
        cell blocked only by the ground counts as open."""
        key = (cx, cy, layer)
        v = self._cache.get(key)
        if v is None:
            v = bool(self._cell(self.w, cx, cy, layer))
            if v and self._terrain and layer < self.engine.terrain_band_at(self.w, cx * CELL + CELL / 2, cy * CELL + CELL / 2) - 1:
                v = False
            self._cache[key] = v
        return v

    def new_order(self, ids):
        """The lab gave `ids` a new order this tick: R-087-03 treats a target change on the next frame as following an order."""
        self._ordered.update(ids)

    def _fires(self):
        e = self.engine
        lib = e._lib
        kind, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        out = []
        for n in range(lib.om_tactical_event_count(self.w)):
            if lib.om_tactical_event_get_at(self.w, n, ctypes.byref(kind), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and kind.value == 0:
                out.append((a.value, b.value))
        return out

    def _hits(self, units, prev, fires):
        """Every (attacker, victim) the step's shots damaged: the target of each shot, and for an area weapon each other enemy of the attacker whose hp fell and that
        stood within the area radius (plus 1 wu) of the target before the step (R-087-06 return fire answers splash too)."""
        out = list(fires)
        for a, b in fires:
            radius = self._aoe.get(a, 0.0)
            if radius > 0 and b in prev:
                for v in self._enemies[self._side[a]]:
                    pv = prev.get(v)
                    if v != b and pv and pv["alive"] and units[v]["hp"] < pv["hp"] - 1e-9 and _Checker._disp(prev[b], pv) <= radius + 1.0:
                        out.append((a, v))
        return out

    def _read(self, tick, fires):
        e, w = self.engine, self.w
        prev = self._frame["units"] if getattr(self, "_frame", None) else {}
        ordered = e.__dict__.get("order_log", {}).pop(w.value, {})     # {unit id: "guard" | "order"}: ordered since the last frame (those before frame 0 included)
        self._ordered |= set(ordered)
        units = {}
        see_unit = e._lib.om_unit_can_see
        for u in self._ids:
            hp = e.unit_hp(w, u)
            alive = hp > 0                       # hp only falls to 0, and the lab counts om_unit_alive reads (fight._run does the same)
            x, y = e.unit_pos(w, u)
            tgt = e.unit_target(w, u) if alive else 0
            if tgt < 0 or tgt > 0xFFFFFF00:
                tgt = 0
            row = {"x": x, "y": y, "layer": max(0, int(e.unit_layer(w, u))), "alive": alive, "hp": hp, "side": self._side[u], "target": tgt}
            token = self._token[u] + (1 if u in self._ordered else 0)
            self._token[u] = token
            row["order"] = token
            p = prev.get(u)
            if alive and p is not None and p["alive"] and p["target"] and tgt and tgt != p["target"]:
                row["prev_seen"] = any(see_unit(w, o, p["target"]) for o in self._ids if self._side[o] == self._side[u] and prev[o]["alive"])   # the engine's own test (om_tac_faction_sees): any living unit of the side sees it
            if alive and tgt:
                row["shootable"] = bool(self._can_shoot(w, u, tgt))
            units[u] = row
        for u, kind in ordered.items():
            if kind == "guard":
                self._posts[u] = (prev[u]["x"], prev[u]["y"]) if u in prev else (units[u]["x"], units[u]["y"])    # an order moves nobody: the post is where it stood
            else:
                self._posts.pop(u, None)
        self._ordered = set()
        see = self.engine._lib.om_player_can_see          # the side's visible set: what its living units see and what its pings reveal (E-12 R-093-02)
        visible = {s: {e for e in es if units[e]["alive"] and see(w, s, e)} for s, es in self._enemies.items()}
        return {"tick": tick, "units": units, "fires": fires, "visible": visible, "hits": self._hits(units, prev, fires)}

    def after_step(self):
        self.tick += 1
        self._frame = self._read(self.tick, self._fires())
        self.violations += self._chk.feed(self._frame)

    def verdict(self):
        """What a lab result carries (FightResult, SearchResult): the first KEEP violations by (tick, rule, unit), whether any rule was broken, the suspended rules."""
        return {"violations": sorted(self.violations, key=lambda v: (v["tick"], v["rule"], v["unit"]))[:KEEP], "invalid": bool(self.violations),
                "suspended": dict(self.suspended)}

    def document_keys(self):
        """What a fight document carries (spec F0): `violations` (the first KEEP, by (tick, rule, unit)) and `invalid`, only when a rule was broken."""
        if not self.violations:
            return {}
        return {"violations": sorted(self.violations, key=lambda v: (v["tick"], v["rule"], v["unit"]))[:KEEP], "invalid": True}


class Blind:
    """Stands in for the Monitor on an engine the checker cannot read (a test double with no library): every rule reports suspended, nothing is judged."""
    violations = []
    tick = 0

    def __init__(self, reason="engine not readable by the checker"):
        self.suspended = {r: reason for r in RULES}

    def after_step(self):
        pass

    def new_order(self, ids):
        pass

    def verdict(self):
        """invalid is None, not False: nothing was judged, so the run is neither broken nor clean (read `suspended`, never treat None as clean)."""
        return {"violations": [], "invalid": None, "suspended": dict(self.suspended)}


def watch(engine, world, width=float("inf"), height=float("inf")):
    """The checker for a lab fight that is stepped by `engine` on `world` (fight.fight, search.run_search): a Monitor, or a Blind one when the engine has no library to read.
    Targeting by sight is read from the world (OM_TP_TARGET_BY_SIGHT, 1 by default); a canvas the lab never set is inf x inf, and R-207-07 is then suspended with the reason UNBOUNDED_CANVAS (no map, nothing to be outside of)."""
    if getattr(engine, "_lib", None) is None or not hasattr(engine, "_own"):
        return Blind()
    off = engine.get_param(world, engine.param_id(SWITCH_TARGET_BY_SIGHT)) == 0
    return Monitor(engine, world, width, height, "off" if off else "on")
