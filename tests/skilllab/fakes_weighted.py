"""TimelineFakeEngine plus profile_reach (no compiler, no library).

New Engine method these tests fix (engine.py comes later):
  profile_reach(w, type_id) -> (up, down)   om_unit_profile_reach; nonzero return raises ValueError

Scripting: `reach_by_type` maps type id -> (up, down), default (0, 0); can_see defaults to "everyone sees
everyone" here (pass `can_see_fn` to narrow it; TimelineFakeEngine's own default is "nobody").
"""
from fakes_timeline import TimelineFakeEngine


class WeightedFakeEngine(TimelineFakeEngine):
    def __init__(self, can_see_fn=lambda fake, o, t: True, reach_by_type=None, **kw):
        super().__init__(can_see_fn=can_see_fn, **kw)
        self.reach_by_type = dict(reach_by_type or {})

    def profile_reach(self, w, type_id):
        self.calls.append(("profile_reach", w, type_id))
        return tuple(self.reach_by_type.get(type_id, (0, 0)))
