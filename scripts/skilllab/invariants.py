"""F0 (engine rule fixes 2026-11-08): the whole-run rule checker of the lab.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F0"; the API is pinned by tests/skilllab/test_invariants.py and
tests/skilllab/arena/test_invariants_wiring.py. Evidence: docs/reports/2026-11-07-rule-enforcement.md and the sweep's predicates in
docs/reports/2026-11-07-rule-enforcement/sweep/inv_check.py (reused here, not copied whole).

Two layers:
  check(trace, rules, only=None) -> Report      pure predicates over a recorded per-tick trace (frame 0 is the state before the first step, frame k the
                                                 state after step k, with that step's shots); the class `_Checker` consumes one frame at a time, so a
                                                 fight of 12,000 ticks is not re-scanned every tick
  Monitor(engine, world, width, height, sight)  the online wrapper `run.fight` uses: reads the engine after each step, builds the frame, feeds `_Checker`

A violation is {"rule", "tick", "unit", "detail"}. The cell test of R-207-06 is the engine's own `om_navmesh_is_cell_blocked` (the Monitor binds it),
never a Python re-derivation. Every number below is a DRAFT constant, Westley's to change:
  DRAFT-inv-cell-depth 1 wu     DRAFT-inv-push-radius 40 wu     DRAFT-inv-stuck-ticks 20     DRAFT-inv-step-slack 1.3 wu
and OWN_MOVE 0.5 wu (a displacement above it counts as "moved"), BACKSWING_TICKS 10 (ticks 1 to 9 after a shot are the pause, R-084-04), HEAL_ONE 0.075 hp
(R-083-03), LEASH_SLACK 25 wu (the sweep's I27).
"""
import ctypes
import math

RULES = ("R-207-06", "R-207-07", "R-087-04", "R-084-04", "R-087-03", "R-087-09", "R-083-03", "continuity")

CELL = 100.0                 # the engine's cell, wu (OM_NAVMESH_CELL_SIZE)
DEPTH_TOL = 1.0              # DRAFT-inv-cell-depth
PUSH_RADIUS = 40.0           # DRAFT-inv-push-radius
STUCK_TICKS = 20             # DRAFT-inv-stuck-ticks
STEP_SLACK = 1.3             # DRAFT-inv-step-slack
OWN_MOVE = 0.5
BACKSWING_TICKS = 10
HEAL_ONE = 0.075
LEASH_SLACK = 25.0
TICK_RATE = 20               # scripts/skilllab/fight.py TICKS_PER_SECOND


class Rules:
    """What the checks need to know about the world. blocked_cell(cx, cy, layer) -> bool; max_step / sensor_radius {unit id: wu}; suspended {rule: switch}."""

    def __init__(self, width, height, blocked_cell=None, max_step=None, sensor_radius=None, suspended=None):
        self.width, self.height = float(width), float(height)
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
        self.prev = None
        self.last_shot = {}          # unit -> tick of its last shot (R-084-04)
        self.lock = {}               # unit -> (target, (x, y) where it took that lock) (R-087-03)
        self.stuck = {}              # unit -> [target, frames not shootable, first distance, flagged] (R-087-09)

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
                if "continuity" in on and step is not None and moved > step + STEP_SLACK and not self._pushed(frame, u):
                    out.append(_violation("continuity", tick, u, "moved %.2f wu in a tick (at most %.2f + %.1f), layer %d to %d" % (
                        moved, step, STEP_SLACK, p["layer"], r["layer"])))
            if "R-087-03" in on:
                self._lock(frame, u, r, p, tick, out)
            if "R-087-09" in on:
                self._held(units, u, r, tick, out)
        for a in shooters:
            self.last_shot[a] = tick
        self.prev = frame
        out.sort(key=lambda v: (v["rule"], v["unit"]))
        return out

    def _lock(self, frame, u, r, p, tick, out):
        tgt = r["target"] if r["alive"] else 0
        held = self.lock.get(u)
        if p is not None and p["alive"] and r["alive"] and p["target"] and tgt and tgt != p["target"]:
            old = p["target"]
            o_prev, o_now = self.prev["units"].get(old), frame["units"].get(old)
            seen = p.get("seen", True) and r.get("prev_seen", r.get("seen", True))
            same_order = p.get("order") == r.get("order")
            sr = self.rules.sensor_radius.get(u)
            took = held[1] if held and held[0] == old else (p["x"], p["y"])
            walked = math.hypot(r["x"] - took[0], r["y"] - took[1])
            if o_prev and o_now and o_prev["alive"] and o_now["alive"] and seen and same_order and not (sr is not None and walked > sr + LEASH_SLACK):
                out.append(_violation("R-087-03", tick, u, "target %d -> %d while %d was alive and seen" % (old, tgt, old)))
        if not tgt:
            self.lock.pop(u, None)
        elif not held or held[0] != tgt:
            self.lock[u] = (tgt, (r["x"], r["y"]))

    def _held(self, units, u, r, tick, out):
        tgt = r["target"] if r["alive"] else 0
        t = units.get(tgt) if tgt else None
        if not t or not t["alive"] or r.get("shootable", True):
            self.stuck.pop(u, None)
            return
        dist = math.hypot(t["x"] - r["x"], t["y"] - r["y"])
        run = self.stuck.get(u)
        if run is None or run[0] != tgt or dist < run[2] - 1.0:
            run = self.stuck[u] = [tgt, 0, dist, False]
        run[1] += 1
        if run[1] > STUCK_TICKS and not run[3]:
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
        self._can_shoot, self._can_see = lib.om_combat_can_shoot, lib.om_player_can_see
        self._ids, self._side = [], {}
        for (wa, faction), us in engine._own.items():
            if wa == world.value:
                for u in us:
                    self._ids.append(u)
                    self._side[u] = faction
        self._ids.sort()
        stats = {}
        self._max_step, self._sensor = {}, {}
        down = engine.get_param(world, engine.param_id("OM_TP_SLOPE_DOWN_MULT"))
        for u in self._ids:
            t = engine.unit_type(world, u)
            st = stats.get(t) or stats.setdefault(t, engine.type_stats(world, t))
            self._max_step[u] = st["speed"] * max(1.0, down) / TICK_RATE
            self._sensor[u] = st["sensor_radius"]
        self._cache = {}
        suspended = {"R-087-03": SWITCH_TARGET_BY_SIGHT} if sight == "off" else {}
        self._chk = _Checker(Rules(width, height, self._blocked, self._max_step, self._sensor, suspended))
        self.suspended = dict(self._chk.suspended)
        self.violations = []
        self.tick = 0
        self._ordered = set()
        self._token = {u: 0 for u in self._ids}
        self._frame = self._read(0, [])
        self._chk.feed(self._frame)

    def _blocked(self, cx, cy, layer):
        key = (cx, cy, layer)
        v = self._cache.get(key)
        if v is None:
            v = self._cache[key] = bool(self._cell(self.w, cx, cy, layer))
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

    def _read(self, tick, fires):
        e, w = self.engine, self.w
        prev = self._frame["units"] if getattr(self, "_frame", None) else {}
        units = {}
        for u in self._ids:
            alive = e.unit_alive(w, u)
            x, y = e.unit_pos(w, u)
            tgt = e.unit_target(w, u) if alive else 0
            if tgt < 0 or tgt > 0xFFFFFF00:
                tgt = 0
            row = {"x": x, "y": y, "layer": max(0, int(e.unit_layer(w, u))), "alive": alive, "hp": e.unit_hp(w, u), "side": self._side[u], "target": tgt}
            token = self._token[u] + (1 if u in self._ordered else 0)
            self._token[u] = token
            row["order"] = token
            p = prev.get(u)
            if alive and p is not None and p["alive"] and p["target"] and tgt and tgt != p["target"]:
                row["prev_seen"] = bool(self._can_see(w, self._side[u], p["target"]))
            if alive and tgt:
                row["shootable"] = bool(self._can_shoot(w, u, tgt))
            units[u] = row
        self._ordered = set()
        return {"tick": tick, "units": units, "fires": fires}

    def after_step(self):
        self.tick += 1
        self._frame = self._read(self.tick, self._fires())
        self.violations += self._chk.feed(self._frame)

    def document_keys(self):
        """What a fight document carries (spec F0): `violations` (the first KEEP, by (tick, rule, unit)), `invalid`, and, when a check was not judged, `suspended`."""
        out = {}
        if self.violations:
            out["violations"] = sorted(self.violations, key=lambda v: (v["tick"], v["rule"], v["unit"]))[:KEEP]
            out["invalid"] = True
        if self.suspended:
            out["suspended"] = dict(self.suspended)
        return out
