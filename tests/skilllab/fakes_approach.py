"""GroupMoveFakeEngine whose units walk: a unit with a destination goes 5 wu per tick toward it and stops on it.

order_move sets the destination to the click point for every unit; order_group_move gives each unit its own slot
(click point + the unit's offset from the group centroid, like om_command_group_move); order_attack_move,
clear_orders and order_guard clear it (an attack-moving fake unit stays put; only the walk is simulated).
`attack_log` is [(tick, unit_ids, centroid at that moment)] per attack_move; `move_goals` is [(unit_ids, click point)]
for every order_move and order_group_move in call order.
"""
import math

from fakes_group_move import GroupMoveFakeEngine

WALK = 5.0


class WalkingFakeEngine(GroupMoveFakeEngine):
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

    def order_group_move(self, w, unit_ids, x, y):
        gid = super().order_group_move(w, unit_ids, x, y)
        self.move_goals.append((list(unit_ids), (x, y)))
        pos = [(self.units[u]["x"], self.units[u]["y"]) for u in unit_ids]
        cx, cy = sum(p[0] for p in pos) / len(pos), sum(p[1] for p in pos) / len(pos)
        for u, p in zip(unit_ids, pos):
            self.dest[u] = (x + p[0] - cx, y + p[1] - cy)
        return gid

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
