"""The order timeline of fight(): Steps that issue later orders (plan Phase S)."""
import math

ORDERS = ("attack_move", "move", "group_move", "idle", "guard", "ping", "set_layer", "set_emission")
NO_MOVE = ("idle", "guard", "ping", "set_layer", "set_emission")


def first_anchors(setup):
    anchors = {}
    for g in setup.groups:
        anchors.setdefault(g.side, (g.x, g.y))
    return anchors


def validate(setup):
    for s in setup.timeline:
        if not isinstance(s.group, int) or not 0 <= s.group < len(setup.groups):
            raise ValueError("step group %r out of range" % (s.group,))
        if s.order not in ORDERS:
            raise ValueError("unknown order %r" % (s.order,))
        kind = s.when[0] if len(s.when) else None
        if kind == "seen" and len(s.when) == 1:
            pass
        elif kind == "tick" and len(s.when) == 2 and s.when[1] >= 0:
            pass
        elif kind == "arrive" and len(s.when) == 2 and s.when[1] > 0:
            pass
        elif kind == "arrive_all" and len(s.when) == 2 and s.when[1] > 0:
            pass
        else:
            raise ValueError("bad step condition %r" % (s.when,))
        if s.order not in NO_MOVE and s.goal is not None and (
                not isinstance(s.goal, (tuple, list)) or len(s.goal) != 2):
            raise ValueError("step goal must be (x, y), got %r" % (s.goal,))


class Timeline:
    def __init__(self, engine, w, setup, ids_by_group, goals):
        """goals: {group index: goal of its latest move/attack_move}, updated as steps fire."""
        self.engine, self.w, self.setup, self.ids, self.goals = engine, w, setup, ids_by_group, goals
        self.start_goals = dict(goals)
        self.anchors = first_anchors(setup)
        self.pending = list(range(len(setup.timeline)))
        self.fired = []

    def check(self, tick, hp, zero=False):
        """Fire every due pending step in listed order; zero=True checks only ("tick", 0) (before any step)."""
        for i in list(self.pending):
            s = self.setup.timeline[i]
            alive = [u for u in self.ids[s.group] if hp[u] > 0]
            if not alive:
                self.pending.remove(i)
            elif self._due(s, alive, tick, hp, zero):
                self.pending.remove(i)
                self._issue(s, alive, hp)
                self.fired.append((i, tick))

    def _due(self, s, alive, tick, hp, zero):
        kind = s.when[0]
        if zero:
            return kind == "tick" and s.when[1] == 0
        if kind == "tick":
            return tick >= s.when[1]
        if kind == "arrive":
            goal = self.goals.get(s.group)
            if goal is None:
                return False
            pos = [self.engine.unit_pos(self.w, u) for u in alive]
            cx, cy = sum(p[0] for p in pos) / len(pos), sum(p[1] for p in pos) / len(pos)
            return math.hypot(cx - goal[0], cy - goal[1]) <= s.when[1]
        if kind == "arrive_all":
            for gi, goal in self.start_goals.items():
                living = [u for u in self.ids[gi] if hp[u] > 0]
                if not living:
                    continue
                pos = [self.engine.unit_pos(self.w, u) for u in living]
                cx, cy = sum(p[0] for p in pos) / len(pos), sum(p[1] for p in pos) / len(pos)
                if math.hypot(cx - goal[0], cy - goal[1]) > s.when[1]:
                    return False
            return True
        others = [u for gi, g in enumerate(self.setup.groups) if g.side != self.setup.groups[s.group].side
                  for u in self.ids[gi] if hp[u] > 0]
        return any(self.engine.can_see(self.w, a, t) for a in alive for t in others)

    def _issue(self, s, alive, hp):
        if s.order == "ping":
            for gi in range(len(self.setup.groups)):
                for u in self.ids[gi]:
                    if hp[u] > 0:
                        self.engine.ping(self.w, u, s.layer, s.goal[0], s.goal[1])
            return
        if s.order == "set_layer":
            self.engine.set_layer(self.w, alive, s.layer)
            return
        if s.order == "set_emission":
            self.engine.set_emission(self.w, alive, s.on)
            return
        if s.order == "idle":
            self.engine.clear_orders(self.w, alive)
            return
        if s.order == "guard":
            self.engine.order_guard(self.w, alive)
            return
        goal = s.goal if s.goal is not None else self.anchors[1 - self.setup.groups[s.group].side]
        getattr(self.engine, "order_" + s.order)(self.w, alive, goal[0], goal[1])
        self.goals[s.group] = goal
