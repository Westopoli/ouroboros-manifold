"""F5 window control for csrc/diplomacy.c (E-06, wave 1 card B5).

Rule (docs/bible/algorithms.md ALG-27 "Growth"): over a faction's owned
inhabited regions, `growth = BASE_TECH_RATE(0.35) * (avg_e/100) *
max(TECH_POPULATION_FLOOR(0.3), avg_p/100)`; `tech = min(100, tech + growth)`.
With one owned region economy=80.0, population=10.0: avg_p/100=0.10 is below
the floor 0.3, so the floor term wins: growth = 0.35*0.8*0.3 = 0.084.

PLANT: under OM_BUG_TECH_GROWTH_TERMS_SWAPPED, om_tech_step computes
`growth = BASE_TECH_RATE * (avg_p/100) * max(TECH_POPULATION_FLOOR, avg_e/100)`
-- avg_e and avg_p swapped between the direct ratio term and the
floor-clamped term. With the same fixture: 0.35 * 0.10 * max(0.3, 0.8) =
0.35*0.10*0.8 = 0.028 (population's low 10 no longer triggers the floor;
economy's high 80 does nothing since it is never compared to the floor).
Starting tech 50.0 -> correct 50.084, buggy 50.028.
"""
import pytest

from conftest import OMArchetype, OMBugE06, OMTier, set_faction, set_owner, set_region


def test_control_tech_growth_terms_swapped_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE06.TECH_GROWTH_TERMS_SWAPPED)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=0.0, tech=50.0, confidence=2.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=0.0, economy=80.0,
               tension=0.0, population=10.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)

    dbg.om_tech_step(w)

    tech_after = dbg.om_faction_tech(w, 0)
    correct = 50.0 + 0.35 * (80.0 / 100.0) * max(0.3, 10.0 / 100.0)
    buggy = 50.0 + 0.35 * (10.0 / 100.0) * max(0.3, 80.0 / 100.0)
    assert tech_after == pytest.approx(buggy, abs=1e-9), (
        f"OM_BUG_TECH_GROWTH_TERMS_SWAPPED injected but tech still reads "
        f"the correct growth ({correct}) instead of the avg_e/avg_p-swapped "
        f"growth ({buggy}) -- the detector did not trip"
    )
