"""Whole-run invariant checker for skill-lab arena fights (read-only wrapper around Engine.step).

Usage as a library: run_one(layout_path, seed, sight, trace=None) -> result dict.
Run from the repo root with the repo venv (so `scripts.skilllab` imports).
"""
import collections
import ctypes
import hashlib
import math
import struct
import sys
import time
import tomllib
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")
from scripts.skilllab import engine as E          # noqa: E402
from scripts.skilllab.arena import features, run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402
from scripts.skilllab.catalogue.produce import presets  # noqa: E402

TPS = 20
BACKSWING = 10
CAT_TURN = {0: 6.0, 1: 4.0, 2: 2.5}   # R-100-02 rad/s for Strike, Line, Siege
GUARD_R = 200.0
NAMES = {
    "I1": "walker ends tick in planar-blocked cell",
    "I1deep": "  of I1: deeper than 1 wu inside the cell",
    "I1b": "walker ends tick on terrain not walkable on its own layer",
    "I1c": "walker ends tick on terrain walkable on no layer",
    "I2a": "unit that fired moved >0.5 wu on the fire tick (not pushed)",
    "I2as": "  of I2a: target was already in weapon range at the start of the tick (walked while able to shoot)",
    "I2b": "unit moved >0.5 wu 1 to 9 ticks after firing (not pushed; offset 10 is the first free tick and is not counted)",
    "I3a": "fire at a target already dead before the step",
    "I3b": "fire with target beyond weapon range (post-move, +1 wu)",
    "I3c": "fire across layers beyond the type's reach",
    "I3d": "fire while can_shoot false after the step (target alive)",
    "I3e": "shot line crosses a blocked cell with neither endpoint inside one",
    "I4a": "target still held a full step after it was dead",
    "I4b": "stuck target: held >20 ticks, not shootable, not closing in (non-guard units)",
    "I4bg": "stuck target, same test, guard units (R-096-08: a guard may hold)",
    "I5": "displacement per tick above type max speed (+0.5), no unit within 40 wu, neither end in a blocked cell",
    "I5b": "  same, but the unit started or ended the tick inside a blocked cell (ejection jump)",
    "I5t": "unit jumped more than 3 x max speed + 15 wu in one tick, whatever its neighbours (a teleport)",
    "I5tL": "  of I5t: together with a layer change",
    "I29": "stalled walker: has a destination, no target, did not move for >40 ticks (counts every tick past 40)",
    "I30": "pacing: 6 direction reversals (>120 deg per 10 ticks) within 600 ticks (flagged at most once per 200 ticks per unit)",
    "I6": "unit outside canvas",
    "I7a": "dead unit moved",
    "I7b": "dead unit fired / fire event from dead attacker",
    "I7c": "dead unit still reports a target id (stale field; replay draws living units only)",
    "I7d": "alive flag and hp disagree (hp<=0 alive, or hp>0 dead), or revived",
    "I8": "shot target not nearest candidate (nearer by >10 wu, visible before and after the step) and not previously engaged (R-087-03)",
    "I8big": "  of I8: nearer candidate was nearer by more than 50 wu",
    "I8r": "  of I8: attacker took damage in the last 40 ticks (return fire R-087-06 may explain)",
    "I9": "no order, no target, not pushed, but moved >0.5 wu (R-097-10/R-099-04)",
    "I9d": "  of I9: took damage in last 40 ticks (flinch R-087-01 may explain)",
    "I10": "hp increased with no friendly Warden within 300 wu (R-083-03 is the only heal)",
    "I10s": "Warden heal larger than 0.075 hp/tick (bible R-083-03: second Warden adds nothing; engine stacks)",
    "I10x": "Warden heal bigger than 0.075 x Wardens in 300 wu",
    "I11": "sampled: can_see and in range (same layer) but not can_shoot",
    "I11x": "  of I11: an endpoint stands in a blocked cell",
    "I11c": "  of I11: no endpoint in a cell, line crosses a blocked cell (fire blocked, sight not)",
    "I11n": "  of I11: same layer, no endpoint in a cell, no crossing: unexplained",
    "I11nl": "  of I11: different layers (slant range / height may explain), no endpoint in a cell, no crossing",
    "I13": "two living same-layer units closer than 28 wu after the step (R-097-05 says 30; 2 wu slack for the push pass)",
    "I13s": "  of I13: closer than 20 wu",
    "I14": "fired while facing >90 deg away from target (R-100-01; the firing arc R-100-04 is DRAFT, not built)",
    "I15": "facing changed faster than the R-100-02 turn rate",
    "I16a": "damage to a unit exceeds sum of ALG-60 hits of the fire events at it",
    "I16b": "damage to a unit with no fire event at it",
    "I16c": "damage below ALG-60 minimum for the fire events at it (hit did not land fully)",
    "I17": "fire gap shorter than attack_interval*20 - 1 ticks",
    "I20": "sampled: can_see beyond sensor radius",
    "I21": "sampled: can_see across a blocked cell, no endpoint inside one",
    "I21x": "sampled: can_see across a blocked cell, an endpoint inside one",
    "I22": "sampled: can_shoot across a blocked cell, no endpoint inside one",
    "I23": "layer flipped and flipped back within 4 ticks",
    "I26": "guard unit farther than GUARD_RADIUS+5 wu from its post (R-096-08)",
    "I27": "unit pursued farther than its sensor radius from its target-anchor (R-096-03/R-087-05)",
}


class Viol:
    def __init__(self):
        self.count = 0
        self.ticks = set()
        self.units = set()
        self.first = None
        self.ex = []
        self.roles = collections.Counter()

    def add(self, tick, unit, detail):
        self.count += 1
        self.roles[detail.split(" ", 1)[0]] += 1
        self.ticks.add(tick)
        self.units.add(unit)
        if self.first is None:
            self.first = (tick, unit, detail)
        if len(self.ex) < 3 and (not self.ex or all(unit != e[1] or tick - e[0] > 200 for e in self.ex)):
            self.ex.append((tick, unit, detail))

    def dump(self):
        return {"count": self.count, "ticks": len(self.ticks), "units": len(self.units), "first": self.first, "examples": self.ex, "roles": dict(self.roles)}


class Chk:
    def __init__(self, eng, w, ctx):
        self.eng, self.w, self.ctx = eng, w, ctx
        self.layout, self.sight = ctx["layout"], ctx["sight"]
        self.viol = collections.defaultdict(Viol)
        self.unit_ticks = 0
        self.tick = 0
        self.md5 = hashlib.md5()
        self.trace_rows = []
        self.extra = collections.defaultdict(collections.Counter)   # side statistics, e.g. offsets of I2b, largest leash overshoot
        self.init_done = False

    # -- setup -------------------------------------------------------------
    def setup(self):
        eng, w, L = self.eng, self.w, self.layout
        self.fac, self.ids = {}, []
        for (wa, f), us in eng._own.items():
            if wa == w.value:
                for u in us:
                    self.fac[u] = f
                    self.ids.append(u)
        self.ids.sort()
        self.typ = {u: eng.unit_type(w, u) for u in self.ids}
        self.st = {t: eng.type_stats(w, t) for t in set(self.typ.values())}
        self.reach = {t: eng.profile_reach(w, t) for t in self.st}
        self.role = {}
        i = 0
        # roles by row order of layout (spawn order is side A rows then side B rows)
        rows = [u["role"] for k in ("side_a", "side_b") for u in L[k]["units"]]
        for u, r in zip(sorted(self.ids, key=lambda x: (self.fac[x], x)), rows):
            self.role[u] = r
        self.start = {u: eng.unit_pos(w, u) for u in self.ids}
        preset = presets()[L["landscape"]]
        self.W, self.H, self.nlayers = preset["width"], preset["height"], preset["layers"]
        sight = self.sight
        stage4 = sight != "off"
        ground = bool(features.bound(L, exact=stage4))
        self.walker = ground or stage4 or L.get("movement") == "walk"
        # blocked planar grid (100 wu cells), as om_map_block_rect sets it
        cols, rows_ = int(self.W // 100), int(self.H // 100)
        self.cols, self.rows = cols, rows_
        grid = bytearray(cols * rows_)
        for x0, y0, x1, y1 in features._engine_boxes(L, exact=stage4):
            gx0, gx1 = max(0, math.floor(x0 / 100)), min(cols - 1, math.ceil(x1 / 100) - 1)
            gy0, gy1 = max(0, math.floor(y0 / 100)), min(rows_ - 1, math.ceil(y1 / 100) - 1)
            for gy in range(gy0, gy1 + 1):
                for gx in range(gx0, gx1 + 1):
                    grid[gy * cols + gx] = 1
        self.blocked = grid
        self.has_blocks = any(grid)
        # terrain walk masks for slope / hills worlds
        self.masks = None
        if features.slopes(L) or (stage4 and features._hills(L)):
            tw, th, _ = eng.terrain_dump_bands(w)
            self.tw = tw
            self.masks = [eng.terrain_walk_mask(w, l) for l in range(self.nlayers)]
        self.has_aoe = any(s["aoe_radius"] > 0 for s in self.st.values())
        # guards
        self.guards = set()
        orders = L.get("orders", "both_same_point")
        if stage4 and orders in ("hold:A", "hold:B"):
            holder = 0 if orders == "hold:A" else 1
            self.guards = {u for u in self.ids if self.fac[u] == holder}
        elif stage4 and orders == "groups":
            from scripts.skilllab.arena import groups
            self.groups_mod = groups
        self.enemy = {u: [e for e in self.ids if self.fac[e] != self.fac[u]] for u in self.ids}
        # previous-state dicts
        self.prev = self.read()
        self.last_fire = {}
        self.last_dmg = {}
        self.stuck = {}          # unit -> (target, run, start_dist)
        self.anchor = {}         # unit -> (target, x, y)
        self.layer_hist = {u: [] for u in self.ids}
        self.prev_facing = {u: self.prev[u]["face"] for u in self.ids}
        n = len(self.ids)
        self.sstep = 5 if n <= 64 else 10 if n <= 100 else 40   # sampled sight/shoot checks: every sstep ticks, the full pair scan every 4th
        self.vis_pre = {}
        self.stall, self.pace_pos, self.pace_vec, self.pace_rev, self.pace_flag = {}, {}, {}, {}, {}
        self.init_done = True

    def snap_vis(self):
        """sight on: which enemies each side's fog shows, read before the step (the state the AI targets from)."""
        lib, w = self.eng._lib, self.w
        liv = [u for u in self.ids if self.prev[u]["alive"]]
        self.vis_pre = {}
        for e in liv:
            for sidef in (0, 1):
                if self.fac[e] != sidef:
                    self.vis_pre[(sidef, e)] = bool(lib.om_player_can_see(w, sidef, e))

    def read(self):
        eng, w = self.eng, self.w
        out = {}
        for u in self.ids:
            al = eng.unit_alive(w, u)
            x, y = eng.unit_pos(w, u)
            out[u] = {"alive": al, "x": x, "y": y, "hp": eng.unit_hp(w, u), "tgt": eng.unit_target(w, u),
                      "layer": int(eng.unit_layer(w, u)), "face": eng.unit_facing(w, u),
                      "dest": eng.unit_destination(w, u) if al else None}
        return out

    # -- geometry helpers -------------------------------------------------
    def cell_blocked(self, x, y):
        cx, cy = int(x // 100), int(y // 100)
        if cx < 0 or cy < 0 or cx >= self.cols or cy >= self.rows:
            return False
        return bool(self.blocked[cy * self.cols + cx])

    def depth(self, x, y):
        """distance from (x,y) to the nearest open-neighbour edge of its blocked cell (0 = on the edge); large if none."""
        cx, cy = int(x // 100), int(y // 100)
        best = 1e9
        for dx, dy, d in ((-1, 0, x - cx * 100), (1, 0, (cx + 1) * 100 - x), (0, -1, y - cy * 100), (0, 1, (cy + 1) * 100 - y)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows and not self.blocked[ny * self.cols + nx]:
                best = min(best, d)
        return best

    def crosses(self, a, b, pa, pb):
        """('cross', endpoint_in_cell) : sampled line a->b enters a blocked cell other than those of its endpoints."""
        if not self.has_blocks:
            return False, False
        ca, cb = (int(pa[0] // 100), int(pa[1] // 100)), (int(pb[0] // 100), int(pb[1] // 100))
        ina, inb = self.cell_blocked(*pa), self.cell_blocked(*pb)
        d = math.dist(pa, pb)
        n = max(2, int(d // 8))
        for i in range(1, n):
            t = i / n
            x, y = pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t
            c = (int(x // 100), int(y // 100))
            if c != ca and c != cb and self.cell_blocked(x, y):
                return True, ina or inb
        return False, ina or inb

    def wardens(self, u, st, living, tag):
        p = st[u]
        return sum(1 for o in living if self.fac[o] == self.fac[u] and self.role[o] == "Warden"
                   and math.hypot(st[o]["x"] - p["x"], st[o]["y"] - p["y"]) <= 300)

    def pushed(self, u, p0, p1, alive_pos):
        """any other unit (alive before the step) within 40 wu of the unit at either end of the tick, measured to the neighbour's pre OR post position
        (a collision push is plausible; deliberately generous so a flagged move is not a push)."""
        for o, (ox, oy, ol) in alive_pos.items():
            if o == u:
                continue
            q = self.cur_post[o]
            for (px, py) in ((p0["x"], p0["y"]), (p1["x"], p1["y"])):
                if math.hypot(ox - px, oy - py) < 40 or math.hypot(q["x"] - px, q["y"] - py) < 40:
                    return True
        return False

    # -- the per-step check -------------------------------------------------
    def after_step(self, pre, ev):
        eng, w, V = self.eng, self.w, self.viol
        self.tick += 1
        t = self.tick
        post = self.read()
        self.cur_post = post
        ids = self.ids
        living_pre = {u for u in ids if pre[u]["alive"]}
        living_post = {u for u in ids if post[u]["alive"]}
        self.unit_ticks += len(living_post)
        alive_pos_pre = {u: (pre[u]["x"], pre[u]["y"], pre[u]["layer"]) for u in living_pre}
        alive_pos_post = {u: (post[u]["x"], post[u]["y"], post[u]["layer"]) for u in living_post}
        alive_pos_both = dict(alive_pos_pre)
        # fires
        fires = collections.defaultdict(list)   # attacker -> [target]
        by_target = collections.defaultdict(list)
        for a, b in ev:
            fires[a].append(b)
            by_target[b].append(a)
        hit_sum_max = {}
        # determinism hash
        h = self.md5
        for u in ids:
            p = post[u]
            h.update(struct.pack("<dddIi", p["x"], p["y"], p["hp"], u, p["tgt"]))

        for u in ids:
            p0, p1 = pre[u], post[u]
            disp = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"])
            ty = self.typ[u]
            stats = self.st[ty]
            role = self.role[u]
            # dead
            if not p0["alive"]:
                if disp > 1e-9:
                    V["I7a"].add(t, u, "dead %s moved %.3f" % (role, disp))
                if p1["tgt"]:
                    V["I7c"].add(t, u, "dead %s holds target %d" % (role, p1["tgt"]))
                if p1["alive"]:
                    V["I7d"].add(t, u, "%s revived hp %.2f" % (role, p1["hp"]))
                if u in fires:
                    V["I7b"].add(t, u, "dead %s fired at %s" % (role, fires[u]))
                continue
            nw = max(self.wardens(u, pre, living_pre, "pre"), self.wardens(u, post, living_post, "post")) if p1["hp"] > p0["hp"] + 1e-9 else 0
            if p1["hp"] > p0["hp"] + 1e-9:
                gain = p1["hp"] - p0["hp"]
                if nw == 0:
                    V["I10"].add(t, u, "hp %.3f -> %.3f, no Warden within 300" % (p0["hp"], p1["hp"]))
                elif not by_target.get(u):
                    if gain > 0.075 * nw + 1e-6:
                        V["I10x"].add(t, u, "%s gained %.4f with %d Wardens" % (role, gain, nw))
                    if gain > 0.075 + 1e-6:
                        V["I10s"].add(t, u, "%s gained %.4f (%d Wardens in 300 wu)" % (role, gain, nw))
            if (p1["hp"] <= 0) == p1["alive"] and not (not p1["alive"] and p1["hp"] <= 0):
                V["I7d"].add(t, u, "%s alive=%s hp=%.3f" % (role, p1["alive"], p1["hp"]))
            if p1["hp"] < p0["hp"] - 1e-9:
                self.last_dmg[u] = t
            recent_dmg = t - self.last_dmg.get(u, -999) <= 40
            if not p1["alive"]:
                if u in fires:   # fired in the tick it died: legal (damage accumulates, applied at once)
                    pass
                self.stuck.pop(u, None)
                self.anchor.pop(u, None)
                continue
            # in canvas
            if not (0 <= p1["x"] <= self.W and 0 <= p1["y"] <= self.H):
                V["I6"].add(t, u, "%s at (%.1f,%.1f) canvas %gx%g" % (role, p1["x"], p1["y"], self.W, self.H))
            # I1
            if self.walker:
                if self.has_blocks and self.cell_blocked(p1["x"], p1["y"]):
                    V["I1"].add(t, u, "%s at (%.2f,%.2f) depth %.2f wu in blocked cell" % (role, p1["x"], p1["y"], self.depth(p1["x"], p1["y"])))
                    if self.depth(p1["x"], p1["y"]) > 1.0:
                        V["I1deep"].add(t, u, "%s depth %.2f wu" % (role, self.depth(p1["x"], p1["y"])))
                if self.masks is not None:
                    cx, cy = int(p1["x"] // 100), int(p1["y"] // 100)
                    if 0 <= cx < self.tw and 0 <= cy < len(self.masks[0]) // self.tw:
                        lay = min(max(p1["layer"], 0), self.nlayers - 1)
                        if not self.masks[lay][cy * self.tw + cx]:
                            V["I1b"].add(t, u, "%s at (%.1f,%.1f) layer %d cell not walkable on it" % (role, p1["x"], p1["y"], p1["layer"]))
                            if not any(m[cy * self.tw + cx] for m in self.masks):
                                V["I1c"].add(t, u, "%s at (%.1f,%.1f) not walkable on any layer" % (role, p1["x"], p1["y"]))
            # I5 speed
            vmax = stats["speed"] / TPS
            pushed = None
            if disp > vmax + 0.5:
                pushed = self.pushed(u, p0, p1, alive_pos_both)
                if not pushed:
                    nearblock = self.has_blocks and (self.cell_blocked(p0["x"], p0["y"]) or self.cell_blocked(p1["x"], p1["y"]))
                    V["I5b" if nearblock else "I5"].add(t, u, "%s moved %.2f wu, max %.2f%s" % (role, disp, vmax, " (start or end in a blocked cell)" if nearblock else ""))
            # I5t teleport: far beyond a push, whatever the neighbours
            if disp > 3 * vmax + 15:
                V["I5t"].add(t, u, "%s jumped %.1f wu in one tick (max %.1f), layer %d -> %d" % (role, disp, vmax, p0["layer"], p1["layer"]))
                if p0["layer"] != p1["layer"]:
                    V["I5tL"].add(t, u, "%s jumped %.1f wu with a layer change %d -> %d" % (role, disp, p0["layer"], p1["layer"]))
            # I29 stalled walker: has a destination, no target, not moving
            if p0["dest"] is not None and not p1["tgt"] and disp < 0.5 and u not in self.guards:
                self.stall[u] = self.stall.get(u, 0) + 1
                if self.stall[u] > 40:
                    V["I29"].add(t, u, "%s has a destination %s, no target, stood still %d ticks" % (role, p1["dest"] and (round(p1["dest"][0]), round(p1["dest"][1])), self.stall[u]))
            else:
                self.stall[u] = 0
            # I30 pacing: net-displacement reversals every 10 ticks
            if t % 10 == 0:
                last = self.pace_pos.get(u)
                self.pace_pos[u] = (p1["x"], p1["y"])
                if last is not None:
                    vx, vy = p1["x"] - last[0], p1["y"] - last[1]
                    pv = self.pace_vec.get(u)
                    if math.hypot(vx, vy) > 10:
                        if pv is not None and vx * pv[0] + vy * pv[1] < -0.5 * math.hypot(vx, vy) * math.hypot(*pv):
                            self.pace_rev.setdefault(u, []).append(t)
                            recent = [x for x in self.pace_rev[u] if t - x <= 600]
                            self.pace_rev[u] = recent
                            if len(recent) >= 6 and t - self.pace_flag.get(u, -999) > 200:
                                self.pace_flag[u] = t
                                V["I30"].add(t, u, "%s reversed direction %d times in 600 ticks (heading change >120 deg per 10 ticks)" % (role, len(recent)))
                        self.pace_vec[u] = (vx, vy)
            # I15 turn
            df = abs((p1["face"] - self.prev_facing[u] + math.pi) % (2 * math.pi) - math.pi)
            cap = CAT_TURN.get(stats["category"], 6.0) / TPS
            if df > cap + 0.02:
                V["I15"].add(t, u, "%s turned %.3f rad, cap %.3f" % (role, df, cap))
            self.prev_facing[u] = p1["face"]
            # fire-related
            fired_now = u in fires
            if fired_now:
                lf = self.last_fire.get(u)
                gap_need = stats["attack_interval"] * TPS
                if lf is not None and t - lf < gap_need - 1:
                    V["I17"].add(t, u, "%s fired again after %d ticks, interval %.1f" % (role, t - lf, gap_need))
                self.last_fire[u] = t
                if disp > 0.5:
                    if pushed is None:
                        pushed = self.pushed(u, p0, p1, alive_pos_both)
                    if not pushed:
                        V["I2a"].add(t, u, "%s moved %.2f wu on fire tick" % (role, disp))
                        # strict: it was already inside weapon range of the target it fires at, measured at the start of the tick
                        for b in fires[u]:
                            if b in pre and pre[b]["alive"] and math.hypot(pre[b]["x"] - p0["x"], pre[b]["y"] - p0["y"]) <= stats["attack_range"] - 1.0:
                                V["I2as"].add(t, u, "%s moved %.2f wu on fire tick although target %d was in range (%.0f <= %.0f) at the start of the tick" % (
                                    role, disp, b, math.hypot(pre[b]["x"] - p0["x"], pre[b]["y"] - p0["y"]), stats["attack_range"]))
                                break
            else:
                lf = self.last_fire.get(u)
                if lf is not None and 1 <= t - lf <= BACKSWING - 1 and disp > 0.5:
                    if pushed is None:
                        pushed = self.pushed(u, p0, p1, alive_pos_both)
                    if not pushed:
                        V["I2b"].add(t, u, "%s moved %.2f wu, %d ticks after firing" % (role, disp, t - lf))
                        self.extra["i2b_offset"][t - lf] += 1
            # I9 stationary
            if (p0["dest"] is None and p1["dest"] is None and not p0["tgt"] and not p1["tgt"] and not fired_now
                    and disp > 0.5 and u not in self.guards):
                if pushed is None:
                    pushed = self.pushed(u, p0, p1, alive_pos_both)
                if not pushed:
                    V["I9"].add(t, u, "%s moved %.2f wu with no order/target" % (role, disp))
                    if recent_dmg:
                        V["I9d"].add(t, u, "recent damage")
            # I4a
            if p1["tgt"] and p0["tgt"] == p1["tgt"] and p1["tgt"] in pre and not pre[p1["tgt"]]["alive"]:
                V["I4a"].add(t, u, "%s keeps dead target %d" % (role, p1["tgt"]))
            # I4b stuck target
            tg = p1["tgt"]
            if tg and tg in post and post[tg]["alive"]:
                d = math.hypot(post[tg]["x"] - p1["x"], post[tg]["y"] - p1["y"])
                if eng.can_shoot(w, u, tg):
                    self.stuck.pop(u, None)
                else:
                    s = self.stuck.get(u)
                    if s is None or s[0] != tg:
                        self.stuck[u] = (tg, 1, d)
                    else:
                        run_ = s[1] + 1
                        self.stuck[u] = (tg, run_, s[2])
                        if run_ > 20 and d > s[2] - 1.0:
                            V["I4bg" if u in self.guards else "I4b"].add(t, u, "%s holds target %d (dist %.0f, start %.0f) %d ticks unshootable" % (role, tg, d, s[2], run_))
                        elif run_ > 20 and d < s[2] - 1.0:
                            self.stuck[u] = (tg, 0, d)   # closing in: restart the window
            else:
                self.stuck.pop(u, None)
            # I27 leash
            if tg:
                an = self.anchor.get(u)
                if an is None or an[0] != tg:
                    self.anchor[u] = (tg, p1["x"], p1["y"])
                elif u not in self.guards:
                    dd = math.hypot(p1["x"] - an[1], p1["y"] - an[2])
                    self.extra["i27_maxover"][u] = max(self.extra["i27_maxover"][u], int(dd - stats["sensor_radius"]))
                    if dd > stats["sensor_radius"] + 25:
                        V["I27"].add(t, u, "%s pursued %.0f wu from anchor (sensor %.0f)" % (role, dd, stats["sensor_radius"]))
            else:
                self.anchor.pop(u, None)
            # I26 guard
            if u in self.guards:
                dd = math.hypot(p1["x"] - self.start[u][0], p1["y"] - self.start[u][1])
                if dd > GUARD_R + 5:
                    V["I26"].add(t, u, "%s guard %.0f wu from post" % (role, dd))
            # I23 layer flip
            lh = self.layer_hist[u]
            lh.append(p1["layer"])
            if len(lh) > 6:
                lh.pop(0)
            if len(lh) >= 3 and lh[-1] != lh[-2]:
                for k in range(2, min(5, len(lh))):
                    if lh[-1 - k] == lh[-1] and all(x == lh[-2] for x in lh[-k:-1]):
                        pass
                if len(lh) >= 3 and lh[-3] == lh[-1] and lh[-2] != lh[-1]:
                    V["I23"].add(t, u, "%s layer %s" % (role, lh[-3:]))

        # fire events: I3, I7b, I8, I14
        sees_cache = {}
        for a, tg_list in fires.items():
            if a not in pre:
                continue
            ra = self.role[a]
            for b in tg_list:
                if not pre[a]["alive"]:
                    continue   # reported as I7b
                sa = self.st[self.typ[a]]
                pa0, pa1 = pre[a], post[a]
                if b not in pre or not pre[b]["alive"]:
                    V["I3a"].add(t, a, "%s fired at dead/unknown %s" % (ra, b))
                    continue
                pb0, pb1 = pre[b], post[b]
                rng = sa["attack_range"]
                d1 = math.hypot(pb1["x"] - pa1["x"], pb1["y"] - pa1["y"])
                d0 = math.hypot(pb0["x"] - pa0["x"], pb0["y"] - pa0["y"])
                if d1 > rng + 1.0:
                    V["I3b"].add(t, a, "%s at %.1f from target, range %.0f" % (ra, d1, rng))
                up, down = self.reach[self.typ[a]]
                dl = pb1["layer"] - pa1["layer"]
                if dl > up or -dl > down:
                    V["I3c"].add(t, a, "%s layer %d fires at layer %d, reach up %d down %d" % (ra, pa1["layer"], pb1["layer"], up, down))
                cs_post = eng.can_shoot(w, a, b)
                if not cs_post and post[b]["alive"]:
                    V["I3d"].add(t, a, "%s fired at %s with can_shoot false after step (d=%.1f)" % (ra, b, d1))
                crossed, endin = self.crosses(a, b, (pa1["x"], pa1["y"]), (pb1["x"], pb1["y"]))
                if crossed and not endin:
                    V["I3e"].add(t, a, "%s -> %s line crosses blocked cell" % (ra, b))
                # I14 facing
                ang = math.atan2(pb1["y"] - pa1["y"], pb1["x"] - pa1["x"])
                dfc = abs((pa1["face"] - ang + math.pi) % (2 * math.pi) - math.pi)
                if dfc > math.pi / 2:
                    V["I14"].add(t, a, "%s facing %.2f rad off target" % (ra, dfc))
                # I8
                if pa0["tgt"] != b:
                    enemies = self.enemy[a]
                    best = None
                    sidef = self.fac[a]
                    for e in enemies:
                        if not pre[e]["alive"]:
                            continue
                        pe = pre[e]
                        de = math.hypot(pe["x"] - pa0["x"], pe["y"] - pa0["y"])
                        if de > rng or de >= d0 - 10.0:
                            continue
                        dl2 = pe["layer"] - pa0["layer"]
                        if dl2 > up or -dl2 > down:
                            continue
                        if self.sight == "on":
                            key = (sidef, e)
                            if key not in sees_cache:
                                sees_cache[key] = bool(eng._lib.om_player_can_see(w, sidef, e))
                            ok = sees_cache[key] and self.vis_pre.get(key, False)   # visible both before and after the step
                        else:
                            ok = True   # sight off: targeting by range only
                        if ok and (best is None or de < best[1]):
                            best = (e, de)
                    if best is not None:
                        V["I8"].add(t, a, "%s shot %s at %.0f while %s was visible at %.0f (prev target %d)" % (ra, b, d0, best[0], best[1], pa0["tgt"]))
                        if t - self.last_dmg.get(a, -999) <= 40:
                            V["I8r"].add(t, a, "recent damage")
                        if best[1] < d0 - 50.0:
                            V["I8big"].add(t, a, "%s shot %s at %.0f while %s was visible at %.0f" % (ra, b, d0, best[0], best[1]))
        # I16 damage vs fire events
        if not self.has_aoe:
            for u in living_pre:
                loss = pre[u]["hp"] - post[u]["hp"]
                evs = by_target.get(u, [])
                nwp, nwq = self.wardens(u, pre, living_pre, "pre"), self.wardens(u, post, living_post, "post")
                if nwp or nwq:
                    if nwp == nwq and len(evs) == 1 and evs[0] in pre and pre[u]["hp"] < self.st[self.typ[u]]["max_hp"] - 1.0 and post[u]["hp"] > 0:
                        sa = self.st[self.typ[evs[0]]]
                        base = sa["base_damage"] * eng.category_multiplier(w, sa["category"], self.st[self.typ[u]]["category"])
                        for heal_name, heal in (("heal_flat", 0.075), ("heal_stack", 0.075 * nwp)):
                            dmg = loss + heal
                            for red_name, red in (("red_none", 0.0), ("red_flat(bible)", 0.1), ("red_linear(ALG-60)", 0.1 * nwp), ("red_halving(engine)", 0.2 * (1 - 0.5 ** nwp))):
                                if abs(dmg - base * (1 - red)) < 1e-3:
                                    self.extra["aura"]["n=%d %s %s" % (min(nwp, 4), heal_name, red_name)] += 1
                        self.extra["aura_n"]["n=%d" % min(nwp, 4)] += 1
                    continue
                if loss > 1e-6 and not evs:
                    V["I16b"].add(t, u, "%s lost %.2f hp with no fire event at it" % (self.role[u], loss))
                if evs:
                    hi = lo = 0.0
                    warden = sum(1 for o in living_pre if self.fac[o] == self.fac[u] and self.role[o] == "Warden"
                                 and math.hypot(pre[o]["x"] - pre[u]["x"], pre[o]["y"] - pre[u]["y"]) <= 300 and o != u)
                    for a in evs:
                        if a not in pre:
                            continue
                        sa = self.st[self.typ[a]]
                        m = eng.category_multiplier(w, sa["category"], self.st[self.typ[u]]["category"])
                        hi += sa["base_damage"] * m
                        lo += sa["base_damage"] * m * max(0.0, 1 - 0.1 * warden)
                    hi = min(hi, pre[u]["hp"])
                    lo = min(lo, pre[u]["hp"])
                    if loss > hi + 1e-3:
                        V["I16a"].add(t, u, "%s lost %.3f, max by events %.3f" % (self.role[u], loss, hi))
                    if loss < lo - 1e-3:
                        V["I16c"].add(t, u, "%s lost %.3f, min by events %.3f (wardens %d)" % (self.role[u], loss, lo, warden))
        # I13 overlap (numpy)
        liv = [u for u in ids if post[u]["alive"]]
        if len(liv) > 1:
            P = np.array([(post[u]["x"], post[u]["y"]) for u in liv])
            Ly = np.array([post[u]["layer"] for u in liv])
            D2 = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)
            m = (D2 < 28.0 ** 2) & (Ly[:, None] == Ly[None, :]) & ~np.eye(len(liv), dtype=bool)
            for i in np.nonzero(m.any(1))[0]:
                u = liv[i]
                j = int(np.argmin(np.where(m[i], D2[i], 1e18)))
                V["I13"].add(t, u, "%s %.1f wu from unit %d" % (self.role[u], math.sqrt(D2[i, j]), liv[j]))
                if D2[i, j] < 20.0 ** 2:
                    V["I13s"].add(t, u, "%s %.1f wu from unit %d" % (self.role[u], math.sqrt(D2[i, j]), liv[j]))
        # sampled sight / shoot checks
        if t % self.sstep == 0 and living_post:
            self.sample(post, t, t % (4 * self.sstep) == 0)
        self.prev = post
        return post

    def sample(self, post, t, full):
        eng, w, V = self.eng, self.w, self.viol
        liv = [u for u in self.ids if post[u]["alive"]]
        for a in liv:
            pa = post[a]
            sa = self.st[self.typ[a]]
            up, down = self.reach[self.typ[a]]
            for b in self.enemy[a]:
                if not post[b]["alive"]:
                    continue
                pb = post[b]
                d = math.hypot(pb["x"] - pa["x"], pb["y"] - pa["y"])
                inrange = d <= sa["attack_range"]
                if not (inrange or (full and True)):
                    continue
                dl = pb["layer"] - pa["layer"]
                seen = eng.can_see(w, a, b)
                if seen and d > sa["sensor_radius"] + 1.0 and full:
                    V["I20"].add(t, a, "%s sees %s at %.0f, sensor %.0f (layers %d,%d)" % (self.role[a], b, d, sa["sensor_radius"], pa["layer"], pb["layer"]))
                if seen and full and self.has_blocks and d <= sa["sensor_radius"]:
                    c, endin = self.crosses(a, b, (pa["x"], pa["y"]), (pb["x"], pb["y"]))
                    if c:
                        V["I21x" if endin else "I21"].add(t, a, "%s sees %s through blocked cell (d=%.0f)" % (self.role[a], b, d))
                if inrange and dl <= up and -dl <= down:
                    cs = eng.can_shoot(w, a, b)
                    if seen and not cs:
                        c11, e11 = self.crosses(a, b, (pa["x"], pa["y"]), (pb["x"], pb["y"]))
                        if not e11:
                            V["I11c" if c11 else ("I11n" if pa["layer"] == pb["layer"] else "I11nl")].add(t, a, "%s sees %s at %.0f (range %.0f), cross=%s, layers %d,%d" % (self.role[a], b, d, sa["attack_range"], c11, pa["layer"], pb["layer"]))
                        V["I11"].add(t, a, "%s sees %s at %.0f (range %.0f) but cannot shoot" % (self.role[a], b, d, sa["attack_range"]))
                        if self.cell_blocked(pa["x"], pa["y"]) or self.cell_blocked(pb["x"], pb["y"]):
                            V["I11x"].add(t, a, "endpoint in blocked cell")
                    if cs and self.has_blocks:
                        c, endin = self.crosses(a, b, (pa["x"], pa["y"]), (pb["x"], pb["y"]))
                        if c and not endin:
                            V["I22"].add(t, a, "%s can_shoot %s across blocked cell" % (self.role[a], b))


ALLOW_R6 = False   # sweep.py sets it: the 33 denied pre-feature layouts (L-0001..33) are old open fields that only fail the "carries its feature" rule R6
_CTX = {}
_orig_step = E.Engine.step.__wrapped__ if hasattr(E.Engine.step, "__wrapped__") else E.Engine.step
_BUMP = E.Engine.step


def _read_events(eng, w):
    lib = eng._lib
    n = lib.om_tactical_event_count(w)
    k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
    out = []
    for i in range(n):
        if lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and k.value == 0:
            out.append((a.value, b.value))
    return out


def step_wrapper(self, w):
    chk = _CTX.get("chk")
    ctx = _CTX.get("ctx")
    if ctx is None:
        return _BUMP(self, w)
    if chk is None or chk.w.value != w.value:
        chk = Chk(self, w, ctx)
        _CTX["chk"] = chk
        chk.setup()
    pre = chk.prev
    if chk.sight != "off":
        chk.snap_vis()
    _BUMP(self, w)
    ev = _read_events(self, w)
    post = chk.after_step(pre, ev)
    tr = ctx.get("trace")
    if tr and tr["lo"] <= chk.tick <= tr["hi"]:
        for u in tr["units"]:
            p = post[u]
            tg = p["tgt"]
            cs = self.can_shoot(w, u, tg) if tg and post.get(tg, {}).get("alive") else None
            nn = min((math.hypot(post[o]["x"] - p["x"], post[o]["y"] - p["y"]) for o in chk.ids if o != u and post[o]["alive"]), default=-1)
            chk.trace_rows.append((chk.tick, u, chk.role[u], round(p["x"], 2), round(p["y"], 2), p["layer"], p["alive"], round(p["hp"], 1), tg, cs,
                                   p["dest"] and (round(p["dest"][0]), round(p["dest"][1])), u in [a for a, _ in ev], "nn=%.1f" % nn))
    return None


E.Engine.step = step_wrapper


def run_one(layout_path, seed, sight, trace=None, cap=CAP_SECONDS):
    layout = tomllib.load(open(layout_path, "rb"))
    res = {"layout": layout["id"], "path": str(layout_path), "seed": seed, "sight": sight,
           "n_a": len(layout["side_a"]["units"]), "n_b": len(layout["side_b"]["units"]),
           "landscape": layout["landscape"], "orders": layout.get("orders", "both_same_point"),
           "features": sorted({f.get("kind") for f in layout.get("features", [])})}
    # the runner's own pre-flight (REJECT lines)
    from scripts.skilllab.catalogue.produce import check_layout, rules
    broken = check_layout(layout, presets(), rules())
    if broken == ["R6"] and ALLOW_R6:
        broken = []
        res["legacy_R6_bypass"] = True
    if broken:
        res["reject"] = "check_layout %s" % (broken,)
        return res
    if layout.get("orders") == "groups":
        bad = run.groups.check(layout)
        if bad:
            res["reject"] = "G2 " + str(bad)
            return res
    pre_sight = "on" if sight == "control" else sight
    if pre_sight == "on":
        wrong = run.layer_mismatch(layout)
        if wrong:
            res["reject"] = "G1 " + wrong
            return res
    miss = run.unreachable(layout, pre_sight)
    if miss:
        res["reject"] = "R8 unreachable " + miss
        return res
    _CTX.clear()
    _CTX["ctx"] = {"layout": layout, "sight": sight, "trace": trace}
    t0 = time.time()
    frames, last, end, orders = run.fight(layout, seed, sight, cap, 100000)
    chk = _CTX.get("chk")
    res["ticks"], res["end"], res["secs"] = last, end, round(time.time() - t0, 1)
    res["alive"] = frames[last]["alive"]
    res["unit_ticks"] = chk.unit_ticks
    res["hash"] = chk.md5.hexdigest()
    res["viol"] = {k: v.dump() for k, v in sorted(chk.viol.items())}
    res["trace"] = chk.trace_rows
    res["extra"] = {k: ({str(a): b for a, b in v.items()} if k != "i27_maxover" else dict(sorted(((str(a), b) for a, b in v.items()), key=lambda x: -x[1])[:5])) for k, v in chk.extra.items()}
    _CTX.clear()
    return res


if __name__ == "__main__":
    import json
    r = run_one(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    r.pop("trace", None)
    print(json.dumps(r, indent=1, default=str))
