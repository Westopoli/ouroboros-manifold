"""TimelineFakeEngine whose units walk: a unit with a move destination goes 5 wu per tick toward it and stops on it.

order_move sets the destination; order_attack_move, clear_orders and order_guard clear it (an attack-moving fake
unit stays put; only the walk is simulated). `attack_log` is [(tick, unit_ids, centroid at that moment)] per attack_move.
"""
import math

from fakes_timeline import TimelineFakeEngine

WALK = 5.0


class WalkingFakeEngine(TimelineFakeEngine):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.dest = {}
        self.attack_log = []
        self.move_goals = []     # [(unit_ids, (x, y))] in call order

    def order_move(self, w, unit_ids, x, y):
        super().order_move(w, unit_ids, x, y)
        self.move_goals.append((list(unit_ids), (x, y)))
        for u in unit_ids:
            self.dest[u] = (x, y)

    def order_attack_move(self, w, unit_ids, x, y):
        super().order_attack_move(w, unit_ids, x, y)
        pos = [(self.units[u]["x"], self.units[u]["y"]) for u in unit_ids]
        self.attack_log.append((self.step_count, list(unit_ids),
                                (sum(p[0] for p in pos) / len(pos), sum(p[1] for p in pos) / len(pos))))
        for u in unit_ids:
            self.dest.pop(u, None)

    def clear_orders(self, w, unit_ids):
        super().clear_orders(w, unit_ids)
        for u in unit_ids:
            self.dest.pop(u, None)

    def step(self, w):
        for u, (x, y) in list(self.dest.items()):
            d = math.hypot(x - self.units[u]["x"], y - self.units[u]["y"])
            if d <= WALK:
                self.units[u]["x"], self.units[u]["y"] = float(x), float(y)
                del self.dest[u]
            else:
                self.units[u]["x"] += (x - self.units[u]["x"]) / d * WALK
                self.units[u]["y"] += (y - self.units[u]["y"]) / d * WALK
        super().step(w)
