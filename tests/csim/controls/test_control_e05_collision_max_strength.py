"""Positive control for OM_BUG_COLLISION_MAX_STRENGTH.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Deterministic
collision selection"): "Over 100 collision runs with identical strength
ratio 40:20 (win probability 40/54 ~= 74.1%), weaker collider wins 0 times
(max strength selection) instead of binomial distribution matching 40/54."
Enum: OMBugE05.COLLISION_MAX_STRENGTH (OM_BUG_COLLISION_MAX_STRENGTH = 104 in
csrc/ouroboros_sim.h), "winner = max strength, no draw".

Reuses (transcribed, not imported -- conftest, pytest, ctypes, math only)
test_E05_S039_when_everyone_wants_the_same_region.py's
`_two_colliders_on_empty` fixture and test_R_039_01_factors_1_0_0_7's own
above-threshold boundary case: two factions commit 40 and 20 to the same
empty region with strengths 40 and 14 (economy factors 1.0 and 0.7), giving
the stronger collider a 40/54 win probability. A weighted draw of 0.75,
just above 40/54 ~= 0.7407, must go to the weaker collider (faction 1); a
max-strength selection always hands it to the stronger one (faction 0)
regardless of the draw.
"""
from conftest import (
    OMAction,
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_collisions,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_collision_max_strength_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=4)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.COLLISION_MAX_STRENGTH)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_faction(dbg, w, 1, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)  # unstated stance: hostile
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)  # unstated tech: none
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    # Faction 0 owns regions 0-1 (economy 100 + 100 = 200 -> factor 1.0);
    # faction 1 owns region 2 (economy 100 -> factor 0.7); region 3 is
    # empty and adjacent to both.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=30.0, economy=100.0,
               tension=0.0, population=50.0, faction_id=0)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=60.0, economy=100.0,
               tension=0.0, population=50.0, faction_id=0)
    set_region(dbg, w, 2, tier=OMTier.HOME, military=30.0, economy=100.0,
               tension=0.0, population=50.0, faction_id=1)
    set_region(dbg, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0,
               tension=0.0, population=0.0, faction_id=-1)
    for idx, fid in ((0, 0), (1, 0), (2, 1)):
        set_owner(dbg, w, idx, fid, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)
    set_edge(dbg, w, 1, 3, OMEdge.BOTH)
    set_edge(dbg, w, 2, 3, OMEdge.BOTH)
    inject_intent(dbg, w, 0, OMAction.COLONIZE, 3, 1, 40.0)
    inject_intent(dbg, w, 1, OMAction.COLONIZE, 3, 2, 20.0)

    # Winner draw 0.75 > 40/54 ~= 0.7407: a weighted draw sends this to
    # faction 1. Refund draw 0.0.
    force_draws(dbg, w, [0.75, 0.0])
    dbg.om_world_step(w)

    cols = [c for c in read_collisions(dbg, w) if c.target_idx == 3]
    assert len(cols) == 1, "expected one collision on region 3"
    c = cols[0]

    # Clean build: winner == 1 (the weaker, strength-14 collider, drawn by
    # the weighted 40/54 probability). Inverted: max-strength selection
    # always picks the strength-40 collider, faction 0.
    assert c.winner != 1, (
        "OM_BUG_COLLISION_MAX_STRENGTH injected but the collision winner at "
        "draw 0.75 (> 40/54) still went to faction 1, the weaker collider "
        "-- the deterministic-collision-selection detector did not trip"
    )
