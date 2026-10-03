"""WeightedFakeEngine whose unit_target answers like an engine that has already acquired its nearest enemy.

Scripting: `set_target(u, t)` (t = 0 for none) overrides the default; the default target of a living unit is the
lowest-id living unit of the other faction, 0 when there is none. Every call is logged like the other fakes.
"""
from fakes_weighted import WeightedFakeEngine


class WeightedTargetFakeEngine(WeightedFakeEngine):
    def unit_target(self, w, u):
        self.calls.append(("unit_target", w, u))
        if u in self.targets:
            return self.targets[u]
        faction = self.units[u]["faction"]
        for e in self.spawn_order:
            if self.units[e]["faction"] != faction and self.units[e]["hp"] > 0:
                return e
        return 0
