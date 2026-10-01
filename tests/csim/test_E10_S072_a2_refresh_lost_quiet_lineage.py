"""A2 (mission-plays plan) -- om_mission_refresh_context, remaining terms.

R-072-02 (adjacent-lost term, zero-trigger baseline) and R-072-03 (lineage
context). ASSUMPTION: void om_mission_refresh_context(om_world *w, int32_t
region) is not yet in csrc/ouroboros_sim.h or signatures.toml; bound here.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMStance,
    OMTier,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)
from test_E10_S072_orders_come_from_where_the_world_hurts import (
    OMMissionArchetype,
    read_mission_candidates,
)


def _refresh(lib, w, region):
    lib.om_mission_refresh_context.argtypes = [type(w), ctypes.c_int32]
    lib.om_mission_refresh_context.restype = None
    lib.om_mission_refresh_context(w, region)


def test_R_072_02_adjacent_lost_region_raises_urgency(lib, world_factory):
    """Given a player region whose neighbor was lost to another faction (previous owner = player), When the context is refreshed, Then urgency rises by exactly 0.4 * 0.3 * min(1, 0.5 * 1) = 0.06."""
    w = world_factory(n_regions=2)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=100.0)
    set_stance(lib, w, 0, 1, OMStance.NEUTRAL)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, economy=60.0, tension=20.0, population=50.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=40.0, economy=50.0, tension=20.0, population=50.0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_owner(lib, w, 1, 1, held_since=0)
    lib.om_region_set_previous_owner(w, 1, 0)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)

    before = lib.om_mission_compute_urgency(w, 0, OMMissionArchetype.DEFENSIVE_STAND)
    _refresh(lib, w, 0)
    after = lib.om_mission_compute_urgency(w, 0, OMMissionArchetype.DEFENSIVE_STAND)
    assert after - before == pytest.approx(0.4 * 0.3 * 0.5, abs=1e-6)


def _quiet_world(lib, world_factory):
    w = world_factory(n_regions=2)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    for idx in (0, 1):
        # ALG-09 stability = 0.40*100 + 0.35*100 + 0.25*100 = 100, so the deficit term is 0 too.
        set_region(lib, w, idx, tier=OMTier.HOME, military=100.0, economy=100.0, tension=0.0, population=100.0)
        set_owner(lib, w, idx, 0, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    return w


def test_R_072_02_nothing_triggering_leaves_terms_zero(lib, world_factory):
    """Given a fully healthy player region with no hostile neighbor, attack, lost region or revolt, When the context is refreshed, Then urgency and relevance are 0, preference stays the 0.5 default, and the pool holds nothing for the region."""
    w = _quiet_world(lib, world_factory)
    _refresh(lib, w, 0)
    assert lib.om_mission_compute_urgency(w, 0, OMMissionArchetype.DEFENSIVE_STAND) == pytest.approx(0.0, abs=1e-9)
    assert lib.om_mission_compute_relevance(w, 0, OMMissionArchetype.DEFENSIVE_STAND) == pytest.approx(0.0, abs=1e-9)
    assert lib.om_mission_compute_preference(w, OMMissionArchetype.DEFENSIVE_STAND) == pytest.approx(0.5, abs=1e-9)
    lib.om_mission_build_candidate_pool(w)
    assert [c for c in read_mission_candidates(lib, w) if c.region_idx == 0] == []


def test_R_072_03_lineage_history_raises_relevance(lib, world_factory):
    """Given a lineage whose home and recorded history include the region, When the context is refreshed, Then relevance is above 0 (before the refresh it is 0)."""
    w = _quiet_world(lib, world_factory)
    lib.om_lineage_create(w, 1, 0)
    lib.om_lineage_record_history_region(w, 1, 0)
    assert lib.om_mission_compute_relevance(w, 0, OMMissionArchetype.DEFENSIVE_STAND) == 0.0
    _refresh(lib, w, 0)
    assert lib.om_mission_compute_relevance(w, 0, OMMissionArchetype.DEFENSIVE_STAND) > 0.0
