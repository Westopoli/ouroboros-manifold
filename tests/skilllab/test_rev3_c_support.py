# Rule pins: R-164-01@511d57
# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7, test T9, defect D7; ledger FINDING-lab-d7, FINDING-lab-d11); piece LAB-REV3-C
"""LAB-REV3-C test support: the structural oracle, the fake engine with reach and live layers, the real-engine oracle hook.
Imported by the other test_rev3_c_*.py files; its own tests are the oracle's positive controls (green on the base).

THE ORACLE (independent of the builder): a unit `a` at layer la with reach (up, down) can reach a unit `b` at layer lb iff
-down <= lb - la <= up (R-164-01; the same line scenes._no_reach reads). Only LIVING units count, layers are the LIVE layers.
  side s "can reach" = some living unit of s can reach some living enemy.
  mutual   : neither side can reach  -> verdict `no_reach_stall` (R7)
  decided s: side s can reach and the other side cannot (so every living unit of s is unreachable by every living enemy and at least
             one unit of s can reach a living enemy) -> verdict `decided_one_way_reach` (FINDING-lab-d11, Architect ruling 2026-10-20)
The two are disjoint by construction. Effective range, vision and knob scaling never enter."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_reengage import ReengageFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

STALL = "no_reach_stall"
DECIDED = "decided_one_way_reach"

# the bible's reach table (R-164-01) as the plays write it (plays_space._REACH): the entries a Setup carries into the engine
RAIDER = {"base": "Raider", "reach": (1, 1)}
INTERCEPTOR = {"base": "Interceptor", "reach": (2, 1)}
BOMBARD = {"base": "Bombard", "reach": (0, 2)}
TYPES = {"Raider": RAIDER, "Interceptor": INTERCEPTOR, "Bombard": BOMBARD}


def can_reach(reach, la, lb):
    up, down = reach
    return -down <= lb - la <= up


def oracle(units):
    """units: [(side, (up, down), layer)] of the LIVING units. Returns None, ("mutual",) or ("decided", side)."""
    if not any(u[0] == 0 for u in units) or not any(u[0] == 1 for u in units):
        return None
    reaches = [any(can_reach(a[1], a[2], b[2]) for a in units if a[0] == s for b in units if b[0] != s) for s in (0, 1)]
    if not reaches[0] and not reaches[1]:
        return ("mutual",)
    if reaches[0] != reaches[1]:
        return ("decided", 0 if reaches[0] else 1)
    return None


class ReachLayerFake(ReengageFakeEngine):
    """ReengageFakeEngine plus the three reads a structural end condition needs: profile_reach (the reach set with set_reach, else the
    library default (0, 0)), unit_layer (already in FakeEngine; a script may change units[u]["layer"] mid-fight), unit_type."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.reach = {}

    def set_reach(self, w, type_id, up, down):
        self.calls.append(("set_reach", w, type_id, up, down))
        self.reach[type_id] = (up, down)

    def profile_reach(self, w, type_id):
        self.calls.append(("profile_reach", w, type_id))
        return self.reach.get(type_id, (0, 0))

    def unit_type(self, w, u):
        self.calls.append(("unit_type", w, u))
        return self.units[u]["type"]

    def living(self):
        """[(side, reach, layer)] of the living units, from the fake's own state (the oracle's input)."""
        return [(self.units[u]["faction"], self.reach.get(self.units[u]["type"], (0, 0)), self.units[u]["layer"])
                for u in self.spawn_order if self.units[u]["hp"] > 0]


def G(side, unit, count, layer, x=None, order="attack_move"):
    return Group(side=side, unit=unit, count=count, formation="line", x=(-300.0 if side == 0 else 300.0) if x is None else x, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=layer, order=order, goal=None, params={"spacing": 30.0})


def run(groups, cap=400, events=None, swap=False, unit_types=None):
    """fight() on a ReachLayerFake. events {k: [fn(fake)]} runs inside step number k + 1 (k steps already taken), so a hit it makes is
    read by fight() at tick k + 1. Returns (result, fake)."""
    from scripts.skilllab.fight import fight
    fake = ReachLayerFake()
    if events:
        fake.script = lambda t, f: [fn(f) for fn in events.get(t, [])]
    setup = Setup(groups=tuple(groups), unit_types=dict(TYPES if unit_types is None else unit_types), abilities=False, max_ticks=cap,
                  sample_every=5)
    return fight(setup, 0, swap, engine=fake), fake


def kill(side, index):
    """Event: the `index`-th unit (spawn order) of the faction that Setup side `side` is (swap False: the same number)."""
    def fn(f):
        f.set_hp(f.units_of(side)[index], 0.0)
    return fn


def to_layer(side, index, layer):
    def fn(f):
        f.units[f.units_of(side)[index]]["layer"] = layer
    return fn


# ---- the oracle's own positive controls (green on the base) -----------------------------------------------------------------------

V, R, I, B = (0, 0), (1, 1), (2, 1), (0, 2)


def test_oracle_mutual_when_nobody_reaches_anybody():
    """Vanguards (0, 0) two layers apart: mutual. Positive control for the mutual detector."""
    assert oracle([(0, V, 0), (1, V, 2)]) == ("mutual",)


def test_oracle_decided_when_one_side_reaches_and_cannot_be_reached():
    """Interceptor (2, 1) on layer 0 reaches the Vanguard on layer 2 (up 2); the Vanguard (0, 0) cannot reach layer 0."""
    assert oracle([(0, I, 0), (1, V, 2)]) == ("decided", 0)
    assert oracle([(1, I, 0), (0, V, 2)]) == ("decided", 1)


def test_oracle_none_when_reach_runs_both_ways_or_a_side_is_empty():
    assert oracle([(0, R, 1), (1, R, 0)]) is None
    assert oracle([(0, I, 0), (0, V, 2), (1, V, 2)]) is None       # one reachable unit (the Vanguard on layer 2) blocks the tag
    assert oracle([(0, I, 0)]) is None


def test_oracle_reach_is_by_layer_offset_not_by_type_name():
    """A reach-capable type with no target layer is no reach: Interceptor on layer 0 cannot reach layer 3, Raider on layer 3 cannot reach layer 0."""
    assert oracle([(0, I, 0), (1, R, 3)]) == ("mutual",)
    assert oracle([(0, B, 2), (1, V, 0)]) == ("decided", 0)        # Bombard (0, 2): down 2
    assert oracle([(0, B, 0), (1, V, 2)]) == ("mutual",)           # the Bombard cannot fire up


@pytest.mark.usefixtures("seam")
def test_the_fake_reports_the_reach_the_setup_set_and_the_default_zero_for_the_rest():
    """The fake's profile_reach answers what fight() sets through Setup.unit_types (registered types: built-in ids for same-name entries, from 100 otherwise) and (0, 0) for a type with no reach set."""
    from scripts.skilllab.fight import fight
    fake = ReachLayerFake()
    setup = Setup(groups=(G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 2)), unit_types=dict(TYPES), max_ticks=3, sample_every=5)
    fight(setup, 0, False, engine=fake)
    kinds = sorted(set(fake.reach.values()))
    assert (2, 1) in kinds
    assert sorted(fake.living()) == sorted([(0, (2, 1), 0), (1, (0, 0), 2)])
    assert oracle(fake.living()) == ("decided", 0)


# ---- the real-engine oracle hook (integration tests) ------------------------------------------------------------------------------

def oracle_engine():
    """An Engine whose step() also reads, after every tick, the oracle state of the REAL world (types from om_unit_get_unit_type, reach
    from om_unit_profile_reach, layers from om_unit_get_layer, hp from the library), recording the first tick of each state in
    `first`: {"mutual": tick} and {("decided", side): tick}. It changes nothing in the simulation."""
    from scripts.skilllab.engine import Engine

    class OracleEngine(Engine):
        def __init__(self):
            super().__init__()
            self.t, self.first, self._rc = 0, {}, {}

        def new_world(self, seed):
            self.t, self.first, self._rc = 0, {}, {}
            return super().new_world(seed)

        def step(self, w):
            super().step(w)
            self.t += 1
            units = []
            for side in (0, 1):
                for u in self._own.get((w.value, side), []):
                    if self.unit_alive(w, u):
                        ty = self.unit_type(w, u)
                        if ty not in self._rc:
                            self._rc[ty] = self.profile_reach(w, ty)
                        units.append((side, self._rc[ty], self.unit_layer(w, u)))
            state = oracle(units)
            if state is not None:
                key = "mutual" if state[0] == "mutual" else state
                self.first.setdefault(key, self.t)

    return OracleEngine()
