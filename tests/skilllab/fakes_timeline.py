"""TraceFakeEngine (so Setup.trace works) plus the two Engine methods the order timeline adds (no compiler, no library).

New Engine methods these tests fix (the harness must supply them; scripts/skilllab/engine.py comes later):
  can_see(w, observer, target) -> bool   om_unit_can_see(const om_world*, uint32, uint32) != 0; per unit, not side sight
  clear_orders(w, unit_ids)    -> None   om_unit_clear_orders per unit id; the fake logs one call with the id list

Scripting on top of FakeEngine:
  - `sees(fake, observer, target)` is the optional `can_see_fn`; default is nobody sees anybody;
  - `order_log` is [(tick, kind, unit_ids, goal)] for every order issued, tick = engine steps taken so far
    (0 for the initial orders); kind is "attack_move", "move" or "idle" (clear_orders, goal None).
"""
from fakes_trace import TraceFakeEngine


class TimelineFakeEngine(TraceFakeEngine):
    def __init__(self, can_see_fn=None, **kw):
        super().__init__(**kw)
        self.can_see_fn = can_see_fn
        self.order_log = []

    def orders_of(self, kind):
        return [o for o in self.order_log if o[1] == kind]

    def order_attack_move(self, w, unit_ids, x, y):
        super().order_attack_move(w, unit_ids, x, y)
        self.order_log.append((self.step_count, "attack_move", list(unit_ids), (x, y)))

    def order_move(self, w, unit_ids, x, y):
        super().order_move(w, unit_ids, x, y)
        self.order_log.append((self.step_count, "move", list(unit_ids), (x, y)))

    def clear_orders(self, w, unit_ids):
        self.calls.append(("clear_orders", w, list(unit_ids)))
        self.order_log.append((self.step_count, "idle", list(unit_ids), None))

    def can_see(self, w, observer, target):
        self.calls.append(("can_see", w, observer, target))
        if self.can_see_fn is None:
            return False
        return bool(self.can_see_fn(self, observer, target))
