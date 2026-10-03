"""FakeEngine plus set_reach (om_roster_set_reach) and profile_reach; the call log gets ("set_reach", w, type_id, up, down)."""
from fakes import FakeEngine


class ReachFakeEngine(FakeEngine):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.reach = {}

    def set_reach(self, w, type_id, up, down):
        self.calls.append(("set_reach", w, type_id, up, down))
        self.reach[type_id] = (up, down)

    def profile_reach(self, w, type_id):
        self.calls.append(("profile_reach", w, type_id))
        return self.reach.get(type_id, (0, 0))
