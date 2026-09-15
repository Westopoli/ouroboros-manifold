"""Positive control for OM_BUG_CONQUEST_ON_BAND.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Conquest
checked on outcome band"): "An attack with outcome band `breakthrough`
leaves defender military at 6.0 (>= 5.0) and records `conquest: true`; or
outcome band `contested` reduces defender military to 3.0 (< 5.0) and
records `conquest: false`." Enum: OMBugE05.CONQUEST_ON_BAND
(OM_BUG_CONQUEST_ON_BAND = 105 in csrc/ouroboros_sim.h).

Reuses the exact fixture from test_E05_S038_taking_a_region.py's
test_R_038_02_conquest_happens_exactly_as_after (with lib -> dbg and
world_factory -> dbg_world_factory): a telegraphed attack resolves as
CONTESTED (net 4.0, the band below breakthrough) but still drops defender
military from 6.0 to 4.0, below the 5.0 conquest threshold. R-038-02
requires conquest to fire anyway, exactly as after a breakthrough, because
conquest is checked on post-damage military, not on the outcome band.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMOutcome,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_attacks,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_conquest_on_band_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.CONQUEST_ON_BAND)

    # commit = 10.6 (telegraph budget = 10.6 / 0.70); defense = 6 * 0.55 *
    # 2.0 = 6.6; net = 10.6 - 6.6 = 4.0 (contested band, 0 < net <= 15.0).
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=10.6 / 0.70, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Defender military 6.0, held since the world began (entrenchment 2.0).
    set_region(dbg, w, 1, tier=OMTier.HOME, military=6.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    # Tick 1: telegraph declared (mode draw 0.1, reinforce prob draw 0.5).
    force_draws(dbg, w, [0.1, 0.5])
    dbg.om_world_step(w)
    # Ticks 2-3: sits pending.
    dbg.om_world_step(w)
    dbg.om_world_step(w)
    # Tick 4: resolves with combat draw 1.0 (net = 4.0) and conquest-unrest
    # probability draw 0.8.
    force_draws(dbg, w, [1.0, 0.8])
    dbg.om_world_step(w)

    attacks = read_attacks(dbg, w)
    assert len(attacks) == 1, "the telegraphed attack never resolved on tick 4"
    att = attacks[0]
    assert att.outcome == OMOutcome.CONTESTED
    assert att.d_military == pytest.approx(-2.0, abs=1e-6)  # military 6.0 -> 4.0

    # Clean build: conquest fires (post-damage military 4.0 < 5.0) even
    # though the outcome band is CONTESTED, not BREAKTHROUGH. Inverted:
    # checking conquest on the outcome band instead of post-damage military
    # withholds conquest for a CONTESTED result.
    assert att.conquest != 1, (
        "OM_BUG_CONQUEST_ON_BAND injected but a CONTESTED attack that drove "
        "defender military to 4.0 (< 5.0) still recorded conquest: true -- "
        "the conquest-checked-on-band detector did not trip"
    )
