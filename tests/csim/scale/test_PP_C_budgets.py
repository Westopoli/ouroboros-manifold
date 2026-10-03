# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md A185 (Addendum 64): scale budgets for G3
# spec: docs/bible/epics/E-11-units-and-combat.md::Scale requirements
"""Phase C G3 budgets, OM_SCALE=1 only, never loosened (A185):
  visibility          2 ms per tick at 1,000 units, 20 ms at 10,000 (spatial hashing)
  targeting + damage  25 ms per tick at 10,000 units with sight and reach on
Same method as test_PP_budgets.py: raw median against budget / OM_SCALE_CPU_FACTOR (1.35) through
assert_budget, with a budget/100 control that proves the clock is live. A miss is a finding for
Westley, never a reason to edit a number here.

Visibility scene: two factions mixed (alternating) over the open 24,000 wu map, Raider and Vanguard
alternating, a third of the units on layer 1, OM_TP_TARGET_BY_SIGHT 1, reach (1 up, 1 down) set for
Vanguard so half the units carry reach. Timed: om_tactical_step on the idle scene (no orders, no movement), median
of TICKS calls. om_visibility_compute is not timed: it is a 0.6 microsecond cache call today (no
public entry runs the side-sight pass alone), so the whole step is the honest upper bound for the
visibility cost. UNCLEAR for Westley: if G3 adds a separate visibility entry point, time that instead. Targeting scene: test_PP_budgets' five-engagement scene with TARGET_BY_SIGHT 1 and
Vanguard reach (1, 1), timed as om_tactical_step.
"""
import math

from ._scale_helpers import CANVAS, assert_budget, assert_control_violates_budget, median_ns, raw_world
from .test_PP_budgets import TICKS, _hp_total, _targeting_scene

RAIDER, VANGUARD = 0, 2
TBS = 4  # OM_TP_TARGET_BY_SIGHT
SEED = 2026100301
VIS_SMALL_NS = 2_000_000
VIS_LARGE_NS = 20_000_000
TARGET_LARGE_NS = 25_000_000


def _sight_and_reach(lib, w):
    assert lib.om_tactical_set_param(w, TBS, 1.0) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, 1, 1) == 0


def _visibility_scene(lib, n):
    w = raw_world(lib, 1, SEED, features=[])
    _sight_and_reach(lib, w)
    cols = math.ceil(math.sqrt(n))
    sp = CANVAS / cols
    for i in range(n):
        x, y = sp * 0.5 + (i % cols) * sp, sp * 0.5 + (i // cols) * sp
        faction = (i % cols + i // cols) % 2
        utype = RAIDER if i % 2 == 0 else VANGUARD
        layer = 1 if i % 3 == 0 else 0
        assert lib.om_unit_spawn(w, utype, faction, x, y, layer) != 0
    return w


def _run_visibility(lib, n, budget_ns, control):
    w = _visibility_scene(lib, n)
    med = median_ns(lambda: lib.om_tactical_step(w), n=TICKS, warmup=2)
    lib.om_world_free(w)
    assert_budget(med, budget_ns, f"G3 visibility (idle om_tactical_step) {n} units, sight 1, reach on for a share")
    if control:
        assert_control_violates_budget(med, budget_ns, f"G3 visibility control {n} units (budget/100)")


def test_PP_C_visibility_1000_units_2ms(lib):
    """A185: visibility, 1,000 units, 2 ms per tick."""
    _run_visibility(lib, 1000, VIS_SMALL_NS, control=True)


def test_PP_C_visibility_10000_units_20ms(lib):
    """A185: visibility, 10,000 units, 20 ms per tick (spatial hashing)."""
    _run_visibility(lib, 10000, VIS_LARGE_NS, control=True)


def test_PP_C_targeting_and_damage_10000_units_25ms_with_sight_and_reach(lib):
    """A185: targeting and damage, 10,000 units, 25 ms per tick, sight and reach on."""
    w, ids = _targeting_scene(lib, 10000)
    _sight_and_reach(lib, w)
    before = _hp_total(lib, w, ids)
    med = median_ns(lambda: lib.om_tactical_step(w), n=TICKS, warmup=2)
    after = _hp_total(lib, w, ids)
    alive = sum(1 for u in ids if lib.om_unit_alive(w, u))
    lib.om_world_free(w)
    assert after < before, "no damage dealt: the scene never engaged, not the budget"
    assert alive == len(ids), f"{len(ids) - alive} units died inside the window: the load is not steady"
    assert_budget(med, TARGET_LARGE_NS, f"G3 targeting+damage {len(ids)} units, sight and reach on")
    assert_control_violates_budget(med, TARGET_LARGE_NS, f"G3 targeting control {len(ids)} units (budget/100)")
