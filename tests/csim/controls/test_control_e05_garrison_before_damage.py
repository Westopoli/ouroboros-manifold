"""Positive control for OM_BUG_GARRISON_BEFORE_DAMAGE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Pre-damage
garrison addition"): "Conquered region's post-battle military does not
equal `(defender_military - damage) + garrison`; or garrison is reduced by
the attack's damage calculation." Enum: OMBugE05.GARRISON_BEFORE_DAMAGE
(OM_BUG_GARRISON_BEFORE_DAMAGE = 106 in csrc/ouroboros_sim.h), "Garrison
added before damage, then destroyed by it."

Reuses the exact fixture from test_E05_S038_taking_a_region.py's
test_R_038_01_region_s_owner_becomes_attacker main block (with lib -> dbg
and world_factory -> dbg_world_factory): a telegraphed breakthrough drops
defender military from 20.0 to 4.0 (net 20.0, Δmilitary -16.0) and conquers
the region with garrison = commit * 0.65 = 42.0 * 0.65 = 27.3. R-038-01
requires the region's final military to be post-damage military plus
garrison: 4.0 + 27.3 = 31.3.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMField,
    OMOutcome,
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


def test_control_garrison_before_damage_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.GARRISON_BEFORE_DAMAGE)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=60.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
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
    # Tick 4: resolves (net = 20.0, breakthrough, Δmilitary = -16.0,
    # post-damage military 4.0 < 5.0 -> conquest, garrison = 42.0 * 0.65).
    force_draws(dbg, w, [1.0, 0.8])
    dbg.om_world_step(w)

    attacks = read_attacks(dbg, w)
    assert len(attacks) == 1, "the telegraphed attack never resolved on tick 4"
    att = attacks[0]
    assert att.outcome == OMOutcome.BREAKTHROUGH
    assert att.conquest == 1
    assert att.garrison == pytest.approx(27.3, abs=1e-6)

    # Clean build: final military = post-damage military (4.0) + garrison
    # (27.3) = 31.3. Inverted: adding garrison before damage, then letting
    # the damage subtraction consume it too, leaves a different total.
    assert dbg.om_region_field(w, 1, OMField.MILITARY) != pytest.approx(31.3, abs=1e-6), (
        "OM_BUG_GARRISON_BEFORE_DAMAGE injected but the conquered region's "
        "final military still reads (defender_military - damage) + garrison "
        "= 31.3 -- the pre-damage-garrison detector did not trip"
    )
