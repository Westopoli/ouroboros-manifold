"""F5 window control for csrc/mission.c (E-10, wave 1 card B9).

Rule (docs/bible/algorithms.md ALG-55 "Scoring and selection"): "urgency =
clamp(URGENCY_FIELD_WEIGHT(0.4) * deficit + URGENCY_CONFLICT_WEIGHT(0.4) *
conflict + URGENCY_CHAIN_WEIGHT(0.2) * chain); deficit = ((100-m) + (100-e) +
(100-stability)) / 300."

Fixture: one region, military=50, economy=20, tension=0, population=100, no
neighbors (n_regions=1, so max_hostile_neighbor_m is necessarily 0) and the
conflict/chain fixture inputs explicitly zeroed via om_mission_set_conflict_context
and om_mission_set_revolt_events, so conflict=0 and chain=0 and urgency
reduces to exactly `0.4 * deficit`. ALG-09 gives stability = 50*0.40 +
100*0.35 + 100*0.25 = 80.0 exactly (m=50 and p=100 both clear the ALG-09
penalty thresholds, so no rounding-sensitive penalty multiply lands on this
number). deficit = (50 + 80 + 20) / 300 = 0.5; urgency = 0.4*0.5 = 0.20.

PLANT: under OM_BUG_URGENCY_DEFICIT_DIVISOR_WRONG, om_mission_compute_urgency
divides the three-term deficit sum by 200 instead of 300: deficit' =
150/200 = 0.75; urgency' = 0.4*0.75 = 0.30.
"""
import pytest

from conftest import OMBugE10, OMComposite, OMTier, set_region


def test_control_urgency_deficit_divisor_wrong_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE10.URGENCY_DEFICIT_DIVISOR_WRONG)

    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=20.0,
               tension=0.0, population=100.0, faction_id=-1)
    dbg.om_mission_set_conflict_context(w, 0, 0, 0.0, 0)
    dbg.om_mission_set_revolt_events(w, 0, 0)

    stability = dbg.om_region_composite(w, 0, OMComposite.STABILITY)
    assert stability == pytest.approx(80.0, abs=1e-9), "fixture setup: ALG-09 stability must be exactly 80.0"

    urgency = dbg.om_mission_compute_urgency(w, 0, 0)

    correct = 0.4 * ((100.0 - 50.0) + (100.0 - 20.0) + (100.0 - 80.0)) / 300.0
    buggy = 0.4 * ((100.0 - 50.0) + (100.0 - 20.0) + (100.0 - 80.0)) / 200.0
    assert urgency == pytest.approx(buggy, abs=1e-9), (
        f"OM_BUG_URGENCY_DEFICIT_DIVISOR_WRONG injected but urgency still "
        f"reads the correctly-divided {correct} instead of the /200 {buggy} "
        f"-- the detector did not trip"
    )
