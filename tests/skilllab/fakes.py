"""Deterministic in-memory stand-in for scripts.skilllab.engine.Engine (spec AC 3 methods only).

No compiler, no library. Everything is scriptable and every call is recorded in order:
  - positions, layers and hp are plain numbers you set (spawn, set_pos, set_hp);
  - can_shoot is True unless a pair is blocked (block) or can_shoot_fn says otherwise;
  - `script(tick, fake)` runs inside step(), before the step counter advances, and may call
    set_hp / set_pos to play out a damage script (tick = number of steps taken before this one);
  - `calls` is the ordered log of (method_name, *args) for every Engine method called.
Unit ids start at 1 and count up in spawn order, like the real library.
"""
from __future__ import annotations

BUILTIN_IDS = {"Raider": 0, "Interceptor": 1, "Vanguard": 2, "Warden": 3, "Bombard": 4, "Bastion": 5}

# AC 3: type_stats returns exactly these nine keys (no role, no ability_id).
STAT_KEYS = ("category", "max_hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius",
             "layer_transition_time", "aoe_radius")
# AC 5: register_unit_type takes these eleven (the nine plus role and ability_id), like om_roster_register_custom_unit.
REGISTER_KEYS = STAT_KEYS + ("role", "ability_id")

_BASE = {"category": 1, "base_damage": 10.0, "attack_interval": 20.0,
         "speed": 5.0, "sensor_radius": 200.0, "layer_transition_time": 0.0,
         "aoe_radius": 0.0}
_HP_RANGE = {"Raider": (70.0, 80.0), "Interceptor": (60.0, 90.0), "Vanguard": (100.0, 100.0),
             "Warden": (40.0, 60.0), "Bombard": (30.0, 150.0), "Bastion": (200.0, 40.0)}


def default_stats():
    return {name: dict(_BASE, max_hp=hp, attack_range=rng) for name, (hp, rng) in _HP_RANGE.items()}


class FakeEngine:
    def __init__(self, stats=None, can_shoot_fn=None, script=None, spawn_hp_scale=1.0):
        self._stats_by_name = default_stats()
        for name, st in (stats or {}).items():
            self._stats_by_name[name] = dict(st)
        self._types = {BUILTIN_IDS[n]: dict(s) for n, s in self._stats_by_name.items() if n in BUILTIN_IDS}
        self.can_shoot_fn = can_shoot_fn
        self.script = script
        self.spawn_hp_scale = spawn_hp_scale
        self.calls = []
        self.units = {}            # id -> dict(type, faction, x, y, layer, hp)
        self.spawn_order = []      # ids in spawn order
        self.step_count = 0
        self.worlds_made = 0
        self.worlds_freed = []
        self.registered = {}       # type_id -> stats passed to register_unit_type
        self.blocked = set()       # ordered (a, b): a cannot shoot b
        self._next_id = 1

    # ---- scripting helpers (not Engine methods, not logged) ----
    def units_of(self, faction):
        return [u for u in self.spawn_order if self.units[u]["faction"] == faction]

    def set_hp(self, u, hp):
        self.units[u]["hp"] = float(hp)

    def set_pos(self, u, x, y):
        self.units[u]["x"], self.units[u]["y"] = float(x), float(y)

    def block(self, a, b, both=False):
        self.blocked.add((a, b))
        if both:
            self.blocked.add((b, a))

    def calls_named(self, name):
        return [c for c in self.calls if c[0] == name]

    def spawn_log(self):
        """[(unit_id, type_id, faction, x, y, layer)] in call order."""
        return [c[1:] for c in self.calls if c[0] == "_spawned"]

    # ---- Engine methods (spec AC 3) ----
    def new_world(self, seed):
        self.calls.append(("new_world", seed))
        self.worlds_made += 1
        self.world = ("fake-world", self.worlds_made)
        return self.world

    def free_world(self, w):
        self.calls.append(("free_world", w))
        self.worlds_freed.append(w)

    def register_unit_type(self, w, type_id, stats):
        missing = [k for k in REGISTER_KEYS if k not in stats]
        if missing:       # the real engine needs role and ability_id too: whoever calls us must supply them
            raise KeyError("register_unit_type stats lack %s" % missing)
        self.calls.append(("register_unit_type", w, type_id, dict(stats)))
        self.registered[type_id] = dict(stats)
        self._types[type_id] = dict(stats)
        return 0

    def type_id(self, name):
        self.calls.append(("type_id", name))
        if name not in BUILTIN_IDS:
            raise ValueError("unknown unit type %r" % (name,))
        return BUILTIN_IDS[name]

    def type_stats(self, w, type_id):
        self.calls.append(("type_stats", w, type_id))
        return {k: self._types[type_id][k] for k in STAT_KEYS}

    def disable_abilities(self, w):
        self.calls.append(("disable_abilities", w))

    def spawn(self, w, type_id, faction, x, y, layer):
        self.calls.append(("spawn", w, type_id, faction, x, y, layer))
        u = self._next_id
        self._next_id += 1
        hp = self._types[type_id]["max_hp"] * self.spawn_hp_scale
        self.units[u] = {"type": type_id, "faction": faction, "x": float(x), "y": float(y),
                         "layer": layer, "hp": float(hp)}
        self.spawn_order.append(u)
        self.calls.append(("_spawned", u, type_id, faction, x, y, layer))
        return u

    def order_attack_move(self, w, unit_ids, x, y):
        self.calls.append(("order_attack_move", w, list(unit_ids), x, y))

    def order_move(self, w, unit_ids, x, y):
        self.calls.append(("order_move", w, list(unit_ids), x, y))

    def step(self, w):
        self.calls.append(("step", w))
        if self.script is not None:
            self.script(self.step_count, self)
        self.step_count += 1

    def unit_hp(self, w, u):
        self.calls.append(("unit_hp", w, u))
        return self.units[u]["hp"]

    def unit_pos(self, w, u):
        self.calls.append(("unit_pos", w, u))
        return (self.units[u]["x"], self.units[u]["y"])

    def unit_layer(self, w, u):
        self.calls.append(("unit_layer", w, u))
        return self.units[u]["layer"]

    def unit_alive(self, w, u):
        self.calls.append(("unit_alive", w, u))
        return self.units[u]["hp"] > 0

    def can_shoot(self, w, a, b):
        self.calls.append(("can_shoot", w, a, b))
        if (a, b) in self.blocked:
            return False
        if self.can_shoot_fn is not None:
            return bool(self.can_shoot_fn(self, a, b))
        return True

    def add_blocker(self, w, x, y, radius):
        self.calls.append(("add_blocker", w, x, y, radius))

    # LAB-REV2-L8 (re-engage): the two reads fight() makes once a side has been silent for REENGAGE_SILENCE_TICKS.
    # Defaults keep every older fake fight unchanged: no unit has a destination, no side sees an enemy, so no re-engage can fire.
    def unit_destination(self, w, u):
        self.calls.append(("unit_destination", w, u))
        return None

    def visible_enemies(self, w, side, enemy_ids):
        self.calls.append(("visible_enemies", w, side, list(enemy_ids)))
        return set()


# ---- the L1/L2 seam (spec 2026-10-14 "Lab data contract": the four firing.py functions fight.py calls) ----
# LAB-REV2-L2: fight() reads the firing count, the weighted count, the unit states and the parity only through
#   firing.count_able(engine, w, units0, units1, arc_deg) -> (int, int)
#   firing.count_weighted(engine, w, units0, units1, arc_deg) -> (float, float)
#   firing.states(engine, w, units0, units1, arc_deg) -> [(unit, code)]
#   firing.parity(engine, w, units0, units1, arc_deg) -> [unit]
# L1 builds firing.py against the public engine queries; L2's fight tests stand a Seam in for it, so they need no
# fake of visible_enemies, profile_reach and the rest. Each reading call is logged; a Seam never edits engine.calls.
class Seam:
    def __init__(self):
        self.calls = []        # [(name, engine, w, units0, units1, arc_deg, tick)]
        self.able = None       # fn(tick) -> (a0, a1); default: the old same-layer in-range can_shoot rule on the fake's units
        self.weighted = None   # fn(tick) -> (w0, w1); default: one per able unit
        self.codes = None      # fn(tick, unit) -> int; default: 0 for an able unit, -1 otherwise
        self.parity_units = []

    def _peek(self, engine, fn):
        n = len(engine.calls)
        try:
            return fn()
        finally:
            del engine.calls[n:]

    def _able_units(self, engine, w, units0, units1):
        def compute():
            live = [[u for u in us if engine.unit_hp(w, u) > 0] for us in (units0, units1)]
            out = [set(), set()]
            for s in (0, 1):
                for u in live[s]:
                    x, y = engine.unit_pos(w, u)
                    rng = engine._types[engine.units[u]["type"]]["attack_range"]
                    for e in live[1 - s]:
                        ex, ey = engine.unit_pos(w, e)
                        if (engine.unit_layer(w, u) == engine.unit_layer(w, e)
                                and (ex - x) ** 2 + (ey - y) ** 2 <= rng * rng and engine.can_shoot(w, u, e)):
                            out[s].add(u)
                            break
            return out, live
        return self._peek(engine, compute)

    def _log(self, name, engine, w, units0, units1, arc_deg):
        self.calls.append((name, engine, w, list(units0), list(units1), arc_deg, engine.step_count))

    def count_able(self, engine, w, units0, units1, arc_deg):
        self._log("count_able", engine, w, units0, units1, arc_deg)
        if self.able is not None:
            return tuple(self.able(engine.step_count))
        able, _ = self._able_units(engine, w, units0, units1)
        return len(able[0]), len(able[1])

    def count_weighted(self, engine, w, units0, units1, arc_deg):
        self._log("count_weighted", engine, w, units0, units1, arc_deg)
        if self.weighted is not None:
            return tuple(float(v) for v in self.weighted(engine.step_count))
        able, _ = self._able_units(engine, w, units0, units1)
        return float(len(able[0])), float(len(able[1]))

    def states(self, engine, w, units0, units1, arc_deg):
        self._log("states", engine, w, units0, units1, arc_deg)
        able, live = self._able_units(engine, w, units0, units1)
        mine = able[0] | able[1]
        code = self.codes or (lambda tick, u: 0 if u in mine else -1)
        return [(u, code(engine.step_count, u)) for u in sorted(live[0] + live[1])]

    def parity(self, engine, w, units0, units1, arc_deg):
        self._log("parity", engine, w, units0, units1, arc_deg)
        return list(self.parity_units)

    def calls_named(self, name):
        return [c for c in self.calls if c[0] == name]


def install_seam(monkeypatch, seam):
    """Replace the four firing functions on scripts.skilllab.firing and, when fight.py imported them by name, on fight."""
    import scripts.skilllab.fight as fight_mod
    import scripts.skilllab.firing as firing_mod
    for name in ("count_able", "count_weighted", "states", "parity"):
        monkeypatch.setattr(firing_mod, name, getattr(seam, name), raising=False)
        monkeypatch.setattr(fight_mod, name, getattr(seam, name), raising=False)
    return seam
