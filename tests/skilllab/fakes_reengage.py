"""ReengageFakeEngine (LAB-REV2-L8): everything a re-engage fight() reads or issues, on the fake (no compiler, no library).

TimelineFakeEngine (order_log, clear_orders, can_see) plus:
  order_guard / order_group_move   logged in `calls` and in `order_log` as kinds "guard" (goal None) and "group_move"
  set_canvas / block_rect / add_cover   logged and ignored (a placed naive scene carries terrain)
  ping / set_layer / set_emission   logged in `calls` only (never in `order_log`, never a destination): the non-order timeline steps
  unit_destination(w, u) -> (x, y) | None   the unit's scripted destination; None is idle (om_unit_get_destination returns 0)
  visible_enemies(w, side, enemy_ids) -> set   {e for e in enemy_ids if visible_fn(self, side, e)}; default: every enemy is visible

Scripting (not logged): set_dest(u, dest). With orders_set_dest=True an order_attack_move / order_move / order_group_move gives
its units that destination and a clear_orders / order_guard clears it; with the default False only set_dest changes it, so a
fight stays "idle" through every order (the lab-side role record, not the destination, is what the test then probes).
Visibility is a function of the fake's step_count, so a test can make an enemy appear at a chosen tick.

`reengage_orders(side)` is the post-opening attack-move orders aimed at `side`'s units: [(tick, unit_ids, (x, y))], tick = engine
steps taken when the order was issued. The opening orders and timeline steps at ("tick", 0) are tick 0 and never listed; an attack_move STEP at a later tick is listed
like any other (a test that has one filters it out by its tick).
"""
from fakes_timeline import TimelineFakeEngine


class ReengageFakeEngine(TimelineFakeEngine):
    def __init__(self, visible_fn=None, orders_set_dest=False, **kw):
        super().__init__(**kw)
        self.visible_fn = visible_fn
        self.orders_set_dest = orders_set_dest
        self.dest = {}

    def set_dest(self, u, dest):
        self.dest[u] = dest

    def reengage_orders(self, side):
        mine = set(self.units_of(side))
        return [(t, ids, goal) for t, kind, ids, goal in self.order_log
                if kind == "attack_move" and t > 0 and ids and set(ids) <= mine]

    def _give(self, ids, goal):
        if self.orders_set_dest:
            for u in ids:
                self.dest[u] = goal

    def order_attack_move(self, w, unit_ids, x, y):
        super().order_attack_move(w, unit_ids, x, y)
        self._give(unit_ids, (x, y))

    def order_move(self, w, unit_ids, x, y):
        super().order_move(w, unit_ids, x, y)
        self._give(unit_ids, (x, y))

    def order_group_move(self, w, unit_ids, x, y):
        self.calls.append(("order_group_move", w, list(unit_ids), x, y))
        self.order_log.append((self.step_count, "group_move", list(unit_ids), (x, y)))
        self._give(unit_ids, (x, y))
        return 1

    def order_guard(self, w, unit_ids):
        self.calls.append(("order_guard", w, list(unit_ids)))
        self.order_log.append((self.step_count, "guard", list(unit_ids), None))
        self._give(unit_ids, None)

    def clear_orders(self, w, unit_ids):
        super().clear_orders(w, unit_ids)
        self._give(unit_ids, None)

    def unit_destination(self, w, u):
        self.calls.append(("unit_destination", w, u))
        return self.dest.get(u)

    def visible_enemies(self, w, side, enemy_ids):
        self.calls.append(("visible_enemies", w, side, list(enemy_ids)))
        if self.visible_fn is None:
            return set(enemy_ids)
        return {e for e in enemy_ids if self.visible_fn(self, side, e)}

    def ping(self, w, caster, layer, x, y):
        self.calls.append(("ping", w, caster, layer, x, y))

    def set_layer(self, w, unit_ids, layer):
        self.calls.append(("set_layer", w, list(unit_ids), layer))

    def set_emission(self, w, unit_ids, on):
        self.calls.append(("set_emission", w, list(unit_ids), on))

    def set_canvas(self, w, width, height):
        self.calls.append(("set_canvas", w, width, height))

    def block_rect(self, w, x0, y0, x1, y1, layer_lo, layer_hi):
        self.calls.append(("block_rect", w, x0, y0, x1, y1, layer_lo, layer_hi))

    def add_cover(self, w, x, y, radius, height):
        self.calls.append(("add_cover", w, x, y, radius, height))
        return 1
