"""Positive control for OM_BUG_ENTRENCH_CURRENT_TICK.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Current-tick
entrenchment"): "In `attack` tick log on a region conquered at tick t,
entrenchment evaluated at tick t + 20 reads 2.0 instead of 1.0 + (20/100) *
1.0 = 1.20; or newly conquered region (`held_since == tick`) reads
entrenchment > 1.0." Enum: OMBugE05.ENTRENCH_CURRENT_TICK
(OM_BUG_ENTRENCH_CURRENT_TICK = 103 in csrc/ouroboros_sim.h), "entrenchment
reads the live tick, not the snapshot held-since".

Adapted from test_E05_S038_taking_a_region.py's
test_R_038_05_its_held_since_tick_t ramp check (with lib -> dbg and
world_factory -> dbg_world_factory), which sets held_since directly rather
than conquering by combat -- the epic's R-038-05 ramp formula (ALG-13) reads
ratio = min(1, (tick - held_since) / 100), and the e2e table's own worked
number is exactly t + 20 -> 1.20, so region 1 is planted with held_since = 1
and the world is stepped to tick 21 (t + 20).
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    isolate_agents,
    read_candidates,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_entrench_current_tick_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.ENTRENCH_CURRENT_TICK)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=0.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    # Economy 8.0 on the attacker's region keeps Δbudget at 0 across the run.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Region 1 was conquered at tick 1 (held_since = 1), planted directly.
    set_region(dbg, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    for _ in range(21):
        dbg.om_world_step(w)  # last step lands on tick 21 = t + 20

    cands = [c for c in read_candidates(dbg, w, 0) if c.region_idx == 1]
    assert len(cands) == 1, "faction 0 has no candidate for region 1 at tick 21"

    # Clean build: ratio = (21 - 1) / 100 = 0.20 -> entrenchment = 1.20.
    # Inverted: reading the live tick instead of held-since drives the
    # ratio to 1.0 regardless of held-since, pinning entrenchment at 2.0.
    assert cands[0].entrenchment != pytest.approx(1.20, abs=1e-6), (
        "OM_BUG_ENTRENCH_CURRENT_TICK injected but entrenchment at t + 20 "
        "still reads 1.0 + (20/100) * 1.0 = 1.20 -- the "
        "current-tick-entrenchment detector did not trip"
    )
