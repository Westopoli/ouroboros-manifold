"""Positive control for OM_BUG_FRICTION_COUNTS_TRADE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Friction on
trade-only edges"): "`border_friction` log records nonzero friction delta
on a region whose only hostile neighbor is connected across a `trade` edge
(not `border` or `both`)." Enum: OMBugE05.FRICTION_COUNTS_TRADE
(OM_BUG_FRICTION_COUNTS_TRADE = 108 in csrc/ouroboros_sim.h), "trade-only
edges count (Q-041-01 answered: border and both only)".

Reuses the trade-only-edge case (Case 1) from
test_E05_S041_hostile_borders_wear_you_down.py's
test_R_041_02_it_contributes_nothing_hostile_neighbor (with lib -> dbg and
world_factory -> dbg_world_factory), trimmed to the two regions that case
needs: a hostile neighbor connected only by a trade edge must contribute
nothing to friction.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMField,
    OMStance,
    OMTier,
    isolate_agents,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_friction_counts_trade_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w, friction=True)

    set_faction(dbg, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=0.0, confidence=5.0)
    set_faction(dbg, w, 1, OMArchetype.DEFAULT, budget=0.0, tech=0.0, confidence=5.0)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    # Stances hostile both ways (neutral unstated stance)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)

    dbg.om_debug_inject(w, OMBugE05.FRICTION_COUNTS_TRADE)

    # Region 0 (faction 0) and region 1 (faction 1) are hostile neighbors
    # joined only by a trade edge.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=20.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=20.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.TRADE)

    dbg.om_world_step(w)

    # Clean build: a trade-only hostile neighbor contributes nothing, so
    # region 0's tension is untouched at 20.0. Inverted: counting trade-only
    # edges applies the +0.15 tension friction anyway.
    assert dbg.om_region_field(w, 0, OMField.TENSION) != pytest.approx(20.0, abs=1e-6), (
        "OM_BUG_FRICTION_COUNTS_TRADE injected but region 0's tension still "
        "reads 20.0, unchanged by its only hostile neighbor across a "
        "trade-only edge -- the friction-on-trade-only-edges detector did "
        "not trip"
    )
