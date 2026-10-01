"""A2 (mission-plays plan) -- om_mission_refresh_context determinism.

R-072-02 / R-072-05 plus the determinism contract: refresh is a pure function
of world state. ASSUMPTION: void om_mission_refresh_context(om_world *w,
int32_t region) is not yet in csrc/ouroboros_sim.h or signatures.toml.
"""
import ctypes

from conftest import OMAction, OMMode, inject_intent, isolate_agents
from test_E10_S072_a2_refresh_telegraph_defensive_stand import (
    ATTACKED,
    QUIET,
    _refresh,
    _telegraphed_frontier,
)
from test_E10_S072_orders_come_from_where_the_world_hurts import read_mission_candidates


def _snapshot(lib, w):
    lib.om_mission_build_candidate_pool(w)
    return [(c.region_idx, c.archetype, c.urgency, c.relevance, c.preference, c.score)
            for c in read_mission_candidates(lib, w)]


def test_R_072_02_refresh_twice_same_result(lib, world_factory):
    """Given a world with a telegraphed attack, When the context is refreshed twice, Then the candidate pool is bit-identical after each refresh (refresh sets, never accumulates)."""
    w = _telegraphed_frontier(lib, world_factory)
    _refresh(lib, w, QUIET)
    _refresh(lib, w, ATTACKED)
    first = _snapshot(lib, w)
    _refresh(lib, w, QUIET)
    _refresh(lib, w, ATTACKED)
    assert first
    assert _snapshot(lib, w) == first


def test_R_072_02_same_seed_two_worlds_same_pool(lib, world_factory):
    """Given two worlds built from the same seed and command stream, When each is refreshed, Then both produce the identical candidate pool."""
    a = _telegraphed_frontier(lib, world_factory)
    b = _telegraphed_frontier(lib, world_factory)
    for w in (a, b):
        _refresh(lib, w, QUIET)
        _refresh(lib, w, ATTACKED)
    snap_a = _snapshot(lib, a)
    assert snap_a
    assert snap_a == _snapshot(lib, b)
