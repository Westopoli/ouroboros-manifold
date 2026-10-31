"""FakeEngine plus the five Engine methods the trace and settings binding add (no compiler, no library).

New Engine methods these tests fix (the harness must supply them; scripts/skilllab/engine.py comes later):
  unit_target(w, u)      -> int    the unit id it is aiming at, 0 for none (om_unit_get_target)
  unit_facing(w, u)      -> float  radians (om_unit_get_facing)
  unit_type(w, u)        -> int    the unit's type id (om_unit_get_unit_type); the fake gives 0. unit_layer is FakeEngine's own.
  param_id(name)         -> int    the library's own enum value of an `OM_TP_*` name; ValueError if unknown
  get_param(w, param)    -> float  (om_tactical_get_param)
  set_param(w, param, v) -> None   ValueError when the library refuses it (om_tactical_set_param returns -1)

The fake's parameter ids are deliberately not 0..n-1 so a harness that guessed an id instead of asking
`param_id` is caught. The fake's table is a stand-in; the real names, defaults and ranges are the contract
document's (plan appendix PP-contract; defaults here are the plan's: the four switches 1, the leash order 0,
the target policy 0).
"""
from fakes import FakeEngine

# name -> (id, default, lo, hi)
PARAMS = {
    "OM_TP_PURSUE_BY_STEERING": (41, 1.0, 0.0, 1.0),
    "OM_TP_ROUTE_AROUND_TERRAIN": (42, 1.0, 0.0, 1.0),
    "OM_TP_TARGET_BY_SIGHT": (43, 1.0, 0.0, 1.0),
    "OM_TP_ROUTE_ACROSS_LAYERS": (44, 1.0, 0.0, 1.0),
    "OM_TP_LEASH_BEFORE_DAMAGE": (45, 0.0, 0.0, 1.0),
    "OM_TP_TARGET_POLICY": (46, 0.0, 0.0, 1.0),
    "OM_TP_FIRING_ARC_DEG": (47, 360.0, 5.0, 360.0),    # LAB-REV2-E0: real, default 360, lo 5 (Architect decision 48; was 10), hi 360
}
_BY_ID = {v[0]: (k,) + v[1:] for k, v in PARAMS.items()}
MUTATING = ("new_world", "free_world", "register_unit_type", "disable_abilities", "spawn", "order_attack_move",
            "order_move", "step", "set_param", "add_blocker")


class TraceFakeEngine(FakeEngine):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.targets = {}      # unit id -> target id (default 0)
        self.facings = {}      # unit id -> radians (default 0.0)
        self.params = {}       # param id -> value, reset by new_world

    def new_world(self, seed):
        self.params = {pid: d for pid, (_n, d, _lo, _hi) in _BY_ID.items()}
        return super().new_world(seed)

    # scripting helpers (not logged)
    def set_target(self, u, target):
        self.targets[u] = target

    def set_facing(self, u, radians):
        self.facings[u] = float(radians)

    def mutating_calls(self):
        return [c for c in self.calls if c[0] in MUTATING]

    # new Engine methods
    def unit_target(self, w, u):
        self.calls.append(("unit_target", w, u))
        return self.targets.get(u, 0)

    def unit_facing(self, w, u):
        self.calls.append(("unit_facing", w, u))
        return self.facings.get(u, 0.0)

    def unit_type(self, w, u):
        self.calls.append(("unit_type", w, u))
        return 0

    def param_id(self, name):
        self.calls.append(("param_id", name))
        if name not in PARAMS:
            raise ValueError("unknown parameter %r" % (name,))
        return PARAMS[name][0]

    def get_param(self, w, param):
        self.calls.append(("get_param", w, param))
        return self.params[param]

    def set_param(self, w, param, value):
        self.calls.append(("set_param", w, param, value))
        if param not in _BY_ID:
            raise ValueError("unknown parameter id %r" % (param,))
        _n, _d, lo, hi = _BY_ID[param]
        if not lo <= value <= hi:
            raise ValueError("%s: %r is outside %r..%r" % (_n, value, lo, hi))
        self.params[param] = float(value)
