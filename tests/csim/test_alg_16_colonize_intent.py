"""ALG-16 Colonize intent (docs/bible/algorithms.md; E-05 R-035-08 colonize cost, S-035).

Rule: the colonize intent commits COLONIZE_COST = 20.0 (a constant, not a
fraction of the budget); its source region is the first owned region adjacent
to the target (region-index order).

Observed through om_tick_decisions (OmDecision.commit / source_idx / target_idx).
Expected values are computed here from the rule, not read back from the C sim.
Positive control: the same world with the target's adjacency moved to a later
region must change the observed source, so the expectation is not vacuous.
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMTier,
    isolate_agents,
    read_decisions,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_tech_multipliers,
)

COLONIZE_COST = 20.0  # ALG-16 / ALG-14


def _colonize_world(lib, world_factory, budget, adjacent_owned):
    """Faction 0 owns regions 0..2; region 3 is empty and unowned. `adjacent_owned`
    lists which owned regions share an edge with the target 3."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=budget, confidence=2.0)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    for idx in range(3):
        set_region(lib, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0,
                   tension=0.0, population=50.0, faction_id=0)
        set_owner(lib, w, idx, 0, held_since=-1)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0,
               tension=0.0, population=0.0, faction_id=-1)
    for idx in adjacent_owned:
        set_edge(lib, w, idx, 3, OMEdge.BOTH)
    lib.om_world_step(w)
    d = read_decisions(lib, w)[0]
    assert d.faction_id == 0
    return d


def test_ALG_16_colonize_commit_is_the_constant_20_and_source_is_first_adjacent_owned(lib, world_factory):
    """ALG-16 / S-035: commit == COLONIZE_COST for any budget >= 20; source == lowest-index owned neighbor of the target."""
    for budget in (20.0, 25.0, 400.0):
        d = _colonize_world(lib, world_factory, budget, adjacent_owned=[1, 2])
        assert d.action == OMAction.COLONIZE
        assert d.target_idx == 3
        assert d.commit == pytest.approx(COLONIZE_COST, abs=1e-9), f"budget {budget}"
        assert d.source_idx == 1, "first owned region adjacent to target 3 is region 1 (region 0 is not adjacent)"


def test_control_ALG_16_a_different_adjacency_moves_the_source(lib, world_factory):
    """Positive control: with only region 2 adjacent the observed source is 2, so 'source == 1' above is a real discrimination, and a wrong expectation fails."""
    d = _colonize_world(lib, world_factory, 25.0, adjacent_owned=[2])
    assert d.action == OMAction.COLONIZE
    assert d.source_idx == 2
    assert d.source_idx != 1
    with pytest.raises(AssertionError):
        assert d.source_idx == 1  # the wrong expectation for this world must fire
