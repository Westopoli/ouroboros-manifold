"""The firing count (spec 2026-10-14 "Lab data contract", harness clause 10): the units able to fire, their type weight, the
per-unit can_engage code, and the parity check between the composed gates and the engine's own om_combat_can_engage.

Until E0 is on main (probe: can_engage reads -1 for a living hostile pair) the code is composed from public queries, in the
engine's diagnostic order: 1 out of reach, 2 not seen by the side, 3 out of range at the offset, 4 outside the arc, 5 line
blocked. After E0 the code is the engine's own answer and the composition is the parity check.
"""
import math

_TWO_PI = 2.0 * math.pi


class _Sample:
    """One instant: the living units of both sides, with the per-call caches the gates need."""

    def __init__(self, engine, w, units0, units1, arc_deg):
        self.e, self.w, self.arc = engine, w, float(arc_deg)
        self.sides = (self._living(units0), self._living(units1))
        self._visible = {}
        self._type = {}
        self._mult = {}
        self._codes = {}
        self.engine_mode = self._probe()

    def _living(self, units):
        e, w = self.e, self.w
        alive = getattr(e, "_fast_unit_alive", e.unit_alive)    # the memoised reads exist on the real engine only
        utype = getattr(e, "_fast_unit_type", e.unit_type)
        out = {}
        for u in sorted(set(units)):
            if alive(w, u):
                x, y = e.unit_pos(w, u)
                out[u] = (x, y, e.unit_layer(w, u), utype(w, u))
        return out

    def _probe(self):
        s0, s1 = self.sides
        if not s0 or not s1:
            return False
        a, b = next(iter(s0)), next(iter(s1))
        return self.e.can_engage(self.w, a, b) != -1 or self.e.can_engage(self.w, b, a) != -1

    def type_info(self, t):
        if t not in self._type:
            stats = self.e.type_stats(self.w, t)
            self._type[t] = (float(stats["attack_range"]), self.e.profile_reach(self.w, t), stats["category"])
        return self._type[t]

    def visible(self, side):
        if side not in self._visible:
            self._visible[side] = self.e.visible_enemies(self.w, side, list(self.sides[1 - side]))
        return self._visible[side]

    def offset_mult(self, off):
        m = self._mult.get(off)
        if m is None:
            k = abs(off)
            if off == 0 or k > 4:
                m = 1.0
            else:
                name = "OM_TP_RANGE_%s_%d" % ("UP" if off > 0 else "DOWN", k)
                m = self.e.get_param(self.w, self.e.param_id(name))
            self._mult[off] = m
        return m

    def composed(self, side, u, v):
        x, y, layer, t = self.sides[side][u]
        ex, ey, elayer, _ = self.sides[1 - side][v]
        rng, (up, down), _ = self.type_info(t)
        off = elayer - layer
        if off > up or -off > down:
            return 1
        if v not in self.visible(side):
            return 2
        reach = rng * self.offset_mult(off)
        dx, dy = ex - x, ey - y
        if dx * dx + dy * dy > reach * reach:
            return 3
        if self.arc < 360.0:
            d = math.atan2(dy, dx) - self.e.unit_facing(self.w, u)
            while d > math.pi:
                d -= _TWO_PI
            while d < -math.pi:
                d += _TWO_PI
            if abs(d) > math.radians(self.arc / 2.0):
                return 4
        if not self.e.can_shoot(self.w, u, v):
            return 5
        return 0

    def code(self, side, u, v):
        key = (u, v)
        if key not in self._codes:
            self._codes[key] = self.e.can_engage(self.w, u, v) if self.engine_mode else self.composed(side, u, v)
        return self._codes[key]

    def record(self, side, u):
        """(code, target of record) for one living unit; (-1, 0) when no living hostile exists."""
        enemies = self.sides[1 - side]
        if not enemies:
            return -1, 0
        t = self.e.unit_target(self.w, u)
        tc = None
        if t in enemies:
            tc = self.code(side, u, t)
            if tc == 0:
                return 0, t
        x, y, layer, ut = self.sides[side][u]
        order = sorted([((ex - x) ** 2 + (ey - y) ** 2, v) for v, (ex, ey, _, _) in enemies.items()])
        engine_mode = self.engine_mode
        if not engine_mode:     # the gates of composed(), in its order, with the per-unit terms hoisted out of the pair loop
            w, can_shoot, offset_mult, arc = self.w, self.e.can_shoot, self.offset_mult, self.arc
            rng, (up, down), _ = self.type_info(ut)
            vis, half, facing, mult = self.visible(side), math.radians(self.arc / 2.0), None, self._mult
        first = None
        for _, v in order:      # nearest first, ties by lower id: squared distance, then id
            if v == t:
                c = tc
            elif engine_mode:
                c = self.code(side, u, v)
            else:
                ex, ey, elayer, _ = enemies[v]
                off = elayer - layer
                if off > up or -off > down:
                    c = 1
                elif v not in vis:
                    c = 2
                else:
                    m = mult.get(off)
                    if m is None:
                        m = offset_mult(off)
                    reach = rng * m
                    dx, dy = ex - x, ey - y
                    if dx * dx + dy * dy > reach * reach:
                        c = 3
                    else:
                        c = 0
                        if arc < 360.0:
                            if facing is None:
                                facing = self.e.unit_facing(w, u)
                            d = math.atan2(dy, dx) - facing
                            while d > math.pi:
                                d -= _TWO_PI
                            while d < -math.pi:
                                d += _TWO_PI
                            if abs(d) > half:
                                c = 4
                        if c == 0 and not can_shoot(w, u, v):
                            c = 5
            if c == 0:
                return 0, v
            if first is None:
                first = (c, v)
        return first

    def records(self):
        if not hasattr(self, "_rec"):
            self._rec = {(side, u): self.record(side, u) for side in (0, 1) for u in self.sides[side]}
        return self._rec


_last = {}      # id(engine) -> (engine, key, sample); the engine reference keeps id() from being reused


def _sample(engine, w, units0, units1, arc_deg):
    """One _Sample per (engine, world, epoch, units, arc); never cached for an engine without an int epoch."""
    ep = getattr(engine, "epoch", None)
    if type(ep) is not int:
        return _Sample(engine, w, units0, units1, arc_deg)
    key = (w.value, ep, tuple(units0), tuple(units1), float(arc_deg))
    hit = _last.get(id(engine))
    if hit is not None and hit[0] is engine and hit[1] == key:
        return hit[2]
    s = _Sample(engine, w, units0, units1, arc_deg)
    _last[id(engine)] = (engine, key, s)
    return s


def count_able(engine, w, units0, units1, arc_deg):
    """(able0, able1): living units whose code is 0 against some living enemy."""
    rec = _sample(engine, w, units0, units1, arc_deg).records()
    return tuple(sum(1 for (s, _), (c, _) in rec.items() if s == side and c == 0) for side in (0, 1))


def count_weighted(engine, w, units0, units1, arc_deg):
    """(weight0, weight1): the category multiplier of each code-0 unit's category against its target of record's, summed."""
    s = _sample(engine, w, units0, units1, arc_deg)
    totals, mult = [0.0, 0.0], {}
    for (side, u), (c, t) in sorted(s.records().items()):
        if c == 0:
            pair = (s.type_info(s.sides[side][u][3])[2], s.type_info(s.sides[1 - side][t][3])[2])
            if pair not in mult:
                mult[pair] = float(engine.category_multiplier(w, *pair))
            totals[side] += mult[pair]
    return tuple(totals)


def states(engine, w, units0, units1, arc_deg):
    """[(unit, code)] ordered by unit id, dead units omitted; code is the can_engage result against the target of record."""
    rec = _sample(engine, w, units0, units1, arc_deg).records()
    return sorted((u, int(c)) for (_, u), (c, _) in rec.items())


def parity(engine, w, units0, units1, arc_deg):
    """Units whose composed able answer differs from the engine's can_engage; [] when E0 is absent."""
    s = _Sample(engine, w, units0, units1, arc_deg)
    if not s.engine_mode:
        return []
    out = []
    for side in (0, 1):
        for u in s.sides[side]:
            enemies = s.sides[1 - side]
            composed = any(s.composed(side, u, v) == 0 for v in enemies)
            engaged = any(engine.can_engage(w, u, v) == 0 for v in enemies)
            if composed != engaged:
                out.append(u)
    return sorted(out)
