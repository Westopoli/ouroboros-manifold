"""Positive control for OM_BUG_SAME_TICK_REDECLARE.

Watch-for (DECISIONS.md Seventh round, C3 ruling): "A faction re-declares an
attack against a target it already has a resolved attack against this same
tick." Enum: OMBugE05.SAME_TICK_REDECLARE (OM_BUG_SAME_TICK_REDECLARE = 110
in csrc/ouroboros_sim.h).

ALG-14/15 (C3, DECISIONS.md Seventh round): at most one resolved attack per
attacker-target pair per tick. A faction may attack the same target again on
the *next* tick if the previous attack failed and it still has the
resources; within one tick, step 3d does not re-declare against a target
whose attack this faction already resolved this tick.

Reuses the exact fixture from test_E05_S038_taking_a_region.py's
test_R_038_01_region_s_owner_becomes_attacker: a telegraphed breakthrough
matures on tick 4 in step 3c, crushing the target to military 4.0 before
step 3d runs. Clean build: step 3d sees the resolved attack against region 1
already on record and does not re-declare; `len(attacks) == 1`. With the bug
injected, 3d ignores that record and re-declares, producing a second,
same-tick attack against the now-defenseless target.
"""
from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_attacks,
    read_telegraphs,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_same_tick_redeclare_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.SAME_TICK_REDECLARE)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=60.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Defender military 20.0, held since the world began (entrenchment 2.0).
    set_region(dbg, w, 1, tier=OMTier.HOME, military=20.0, economy=16.0,
               tension=10.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    # Tick 1: telegraph declared (commit = 42.0).
    force_draws(dbg, w, [0.1, 0.5])
    dbg.om_world_step(w)
    assert len(read_telegraphs(dbg, w)) == 1
    # Ticks 2-3: sits pending.
    dbg.om_world_step(w)
    dbg.om_world_step(w)
    # Tick 4: telegraph matures in step 3c (net = 20.0, breakthrough,
    # post-damage military 4.0 < 5.0). Clean build: step 3d sees this
    # resolved attack on record and does not re-declare.
    force_draws(dbg, w, [1.0, 0.8])
    dbg.om_world_step(w)

    attacks = read_attacks(dbg, w)
    assert len(attacks) != 1, (
        "OM_BUG_SAME_TICK_REDECLARE injected but only one attack resolved "
        "this tick -- the same-tick-redeclare detector did not trip"
    )
