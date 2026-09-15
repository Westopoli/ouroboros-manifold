"""Positive control for OM_BUG_SURPRISE_ON_DEFENSE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Inverted
surprise multiplier"): "In `attack` tick log with mode `surprise`,
`effective_attack == commit` (expected `commit x 0.5`) or `effective_defense
== base_defense x 0.5` (expected `base_defense`)." Enum:
OMBugE05.SURPRISE_ON_DEFENSE (OM_BUG_SURPRISE_ON_DEFENSE = 102 in
csrc/ouroboros_sim.h), "0.5 applied to defense, not attack".

Reuses the exact fixture from test_E05_S037_battles_have_a_shape.py's
test_R_037_06_effective_attack_25 (with lib -> dbg and world_factory ->
dbg_world_factory): a conqueror surprise-attacks a defenseless target with
commit 50.0. R-037-06 requires effective attack to be halved to 25.0.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMMode,
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


def test_control_surprise_on_defense_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.SURPRISE_ON_DEFENSE)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=50.0 / 0.70, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.DEFAULT)
    # Stances hostile both ways (neutral unstated stance)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    # Tech multipliers 1.0 (neutral baseline, no tech)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    # Held since -1 indicates held since the world began (entrenchment 2.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=20.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    # Mode draw 0.95 >= 0.7 selects surprise mode, then combat draw 1.0 in 3f.
    force_draws(dbg, w, [0.95, 1.0])
    dbg.om_world_step(w)

    attacks = read_attacks(dbg, w)
    assert len(attacks) == 1, "the surprise attack never resolved on tick 1"
    att = attacks[0]
    assert att.mode == OMMode.SURPRISE

    # Clean build: effective attack = commit * 0.5 = 25.0. Inverted: the
    # 0.5 penalty was moved onto defense, so effective attack stays at the
    # full commit and no longer matches 25.0.
    assert att.effective_attack != pytest.approx(25.0, abs=1e-6), (
        "OM_BUG_SURPRISE_ON_DEFENSE injected but effective_attack still "
        "reads commit * 0.5 = 25.0 -- the surprise-multiplier detector did "
        "not trip"
    )
