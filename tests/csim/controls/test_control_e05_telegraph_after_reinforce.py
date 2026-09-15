"""Positive control for OM_BUG_TELEGRAPH_AFTER_REINFORCE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Telegraph /
reinforce inversion"): "Tick log shows telegraph resolution entry preceding
defender's reactive reinforce entry for the same attack in the same tick; or
defender reinforced military is not reflected in effective defense at battle
resolution." Enum: OMBugE05.TELEGRAPH_AFTER_REINFORCE
(OM_BUG_TELEGRAPH_AFTER_REINFORCE = 101 in csrc/ouroboros_sim.h), "3c runs
after 3e".

Reuses the tick-1 half of test_E05_S036_declared_or_sprung.py's
test_R_036_03_it_resolves_in_step_3c fixture (with lib -> dbg and
world_factory -> dbg_world_factory): a conqueror declares a telegraphed
attack against a fortifier's region on tick 1. R-036-03 requires the
fortifier's one reactive reinforce to fire in step 3e of that same
declaration tick. The correct step order is 3c (resolve telegraphs that
matured before this tick) then 3d (decide, which may declare new
telegraphs) then 3e (reactive reinforce against telegraphs just declared in
3d). If 3c is swapped to run after 3e, step 3e executes before 3d has
declared anything new this tick, so the reactive reinforce for a telegraph
declared on this very tick has nothing to react to yet and never fires.
Only tick 1 is needed -- the swap's effect is visible on the declaration
tick itself, so the world never has to run to the tick-4 resolution.
"""
from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_reinforces,
    read_telegraphs,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_telegraph_after_reinforce_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.TELEGRAPH_AFTER_REINFORCE)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=50.0)
    # Stances hostile both ways (neutral unstated stance)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    # Tech multipliers 1.0 (neutral baseline, no tech)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=40.0, economy=60.0,
               tension=0.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    # Tick 1: mode draw 0.1 < 0.9 selects telegraph; 0.5 for the reactive
    # reinforce probability draw; 0.5 for its variance draw.
    force_draws(dbg, w, [0.1, 0.5, 0.5])
    dbg.om_world_step(w)

    pending_t1 = read_telegraphs(dbg, w)
    assert len(pending_t1) == 1, "faction 0's telegraph was never declared on tick 1"

    reinforces_t1 = read_reinforces(dbg, w)
    assert len(reinforces_t1) != 1, (
        "OM_BUG_TELEGRAPH_AFTER_REINFORCE injected but the defender's one "
        "reactive reinforce still fired in step 3e of the declaration tick "
        "(len == 1, same as the clean build) -- the telegraph/reinforce-order "
        "detector did not trip"
    )
