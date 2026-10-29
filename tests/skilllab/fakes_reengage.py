"""ReengageFakeEngine (LAB-REV2-L8): everything a re-engage fight() reads or issues, on the fake (no compiler, no library).

TimelineFakeEngine (order_log, clear_orders, can_see) plus:
  order_guard / order_group_move   logged in `calls` and in `order_log` as kinds "guard" (goal None) and "group_move"
  set_canvas / block_rect / add_cover   logged and ignored (a placed naive scene carries terrain)
  ping / set_layer / set_emission   logged in `calls` only (never in `order_log`, never a destination): the non-order timeline steps
  unit_destination(w, u) -> (x, y) | None   the unit's scripted destination; None is idle (om_unit_get_destination returns 0)
  visible_enemies(w, side, enemy_ids) -> set   {e for e in enemy_ids if visible_fn(self, side, e)}; default: every enemy is visible

Scripting (not logged): set_dest(u, dest), a permanent scripted destination (None clears it and wins over an order's).
What an order_attack_move / order_move / order_group_move does to a unit's destination (LAB-REV2-FIX, decision 43 item 3):
  default (arrive_after=2)   the unit has the order's goal as its destination while step_count < (steps taken at the order) + 2, then
                             None again (it arrived and idles): an order that WORKS, one tick later the unit still has a destination
  arrive_after=None          every order is a NO-OP: the destination stays what set_dest left (None), the re-engage's no-op case
  orders_set_dest=True       the destination is permanent (a clear_orders / order_guard clears it)
Visibility is a function of the fake's step_count, so a test can make an enemy appear at a chosen tick.

`reengage_orders(side)` is the post-opening attack-move EVENTS aimed at `side`'s units: [(tick, unit_ids, (x, y))], tick = engine
steps taken when the order was issued; orders issued at the same tick onto the same goal are ONE event whose ids are all their units
(decision 43 item 2: a re-engage is one order per idle unit, and the count stays one event per trigger). `reengage_calls(side)` is the
same without the merging: one entry per order_attack_move call. The opening orders and timeline steps at ("tick", 0) are tick 0 and
never listed; an attack_move STEP at a later tick is listed like any other (a test that has one filters it out by its tick).
"""
from fakes_timeline import TimelineFakeEngine


class ReengageFakeEngine(TimelineFakeEngine):
    def __init__(self, visible_fn=None, orders_set_dest=False, arrive_after=2, **kw):
        super().__init__(**kw)
        self.visible_fn = visible_fn
        self.orders_set_dest = orders_set_dest
        self.arrive_after = arrive_after
        self.dest = {}
        self.until = {}

    def set_dest(self, u, dest):
        self.dest[u] = dest

    def reengage_calls(self, side):
        mine = set(self.units_of(side))
        return [(t, ids, goal) for t, kind, ids, goal in self.order_log
                if kind == "attack_move" and t > 0 and ids and set(ids) <= mine]

    def reengage_orders(self, side):
        events = []
        for t, ids, goal in self.reengage_calls(side):
            if events and events[-1][0] == t and events[-1][2] == goal:
                events[-1][1].extend(ids)
            else:
                events.append((t, list(ids), goal))
        return events

    def _give(self, ids, goal):
        if self.orders_set_dest:
            for u in ids:
                self.dest[u] = goal
        elif self.arrive_after is not None:
            for u in ids:
                self.until[u] = (goal, self.step_count + self.arrive_after)

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
        if u in self.dest:
            return self.dest[u]
        goal, until = self.until.get(u, (None, 0))
        return goal if self.step_count < until else None

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
