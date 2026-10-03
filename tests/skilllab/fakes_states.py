"""FakeEngine plus scripted positions, destinations and can_shoot answers for the states tests.

  pos_fn[u](tick)    -> (x, y)           where the unit is at the tick (read at call time; tick = steps taken so far)
  dest_fn[u](tick)   -> (x, y) | None    what unit_destination returns
  shoot_fn(tick, a, b) -> bool           can_shoot answer (default True)
  hp_at[u] = tick                         the unit's hp reads 0 from that tick on (tick = steps taken)
Units not scripted keep the position they spawned at and have no destination.
"""
from fakes import FakeEngine


class StatesFakeEngine(FakeEngine):
    def __init__(self, pos_fn=None, dest_fn=None, shoot_fn=None, hp_at=None, **kw):
        super().__init__(**kw)
        self.pos_fn = dict(pos_fn or {})
        self.dest_fn = dict(dest_fn or {})
        self.shoot_fn = shoot_fn
        self.hp_at = dict(hp_at or {})

    @property
    def tick(self):
        return self.step_count

    def unit_pos(self, w, u):
        self.calls.append(("unit_pos", w, u))
        if u in self.pos_fn:
            return tuple(float(v) for v in self.pos_fn[u](self.tick))
        return (self.units[u]["x"], self.units[u]["y"])

    def unit_target(self, w, u):
        return 0

    def unit_facing(self, w, u):
        return 0.0

    def unit_hp(self, w, u):
        self.calls.append(("unit_hp", w, u))
        if u in self.hp_at and self.tick >= self.hp_at[u]:
            return 0.0
        return self.units[u]["hp"]

    def unit_alive(self, w, u):
        self.calls.append(("unit_alive", w, u))
        return self.unit_hp_quiet(u) > 0

    def unit_hp_quiet(self, u):
        if u in self.hp_at and self.tick >= self.hp_at[u]:
            return 0.0
        return self.units[u]["hp"]

    def can_shoot(self, w, a, b):
        self.calls.append(("can_shoot", w, a, b))
        return True if self.shoot_fn is None else bool(self.shoot_fn(self.tick, a, b))

    def unit_destination(self, w, u):
        self.calls.append(("unit_destination", w, u))
        fn = self.dest_fn.get(u)
        return None if fn is None else fn(self.tick)
