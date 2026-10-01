"""A2 (mission-plays plan) -- om_mission_refresh_context, telegraphed attack.

R-072-02 (conflict term: recent attacks and attack budget) feeding R-072-05
(selection) and the S-072 "obviously working" fixture: a player frontier under
a telegraphed attack selects Defensive Stand. The conflict context is NEVER set
through om_mission_set_conflict_context here; only om_mission_refresh_context
may fill it from world state.

ASSUMPTION: void om_mission_refresh_context(om_world *w, int32_t region) is not
yet declared in csrc/ouroboros_sim.h or signatures.toml; this file binds the
intended signature itself.
"""
import ctypes

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMMode,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_telegraphs,
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

ATTACKED = 1
QUIET = 0


def _refresh(lib, w, region):
    lib.om_mission_refresh_context.argtypes = [type(w), ctypes.c_int32]
    lib.om_mission_refresh_context.restype = None
    lib.om_mission_refresh_context(w, region)


def _telegraphed_frontier(lib, world_factory):
    """Regions 0 and 1 are identical player frontiers facing identical hostile
    neighbors (2 and 3). Faction 1 telegraphs an attack from 3 onto region 1
    (the higher index, so a tie would resolve to region 0 and fail)."""
    w = world_factory(n_regions=4)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=100.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    for idx, owner in ((0, 0), (1, 0), (2, 1), (3, 1)):
        set_region(lib, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0, tension=20.0, population=50.0)
        set_owner(lib, w, idx, owner, held_since=-1)
    set_edge(lib, w, 0, 2, OMEdge.BORDER)
    set_edge(lib, w, 1, 3, OMEdge.BORDER)
    isolate_agents(lib, w)
    inject_intent(lib, w, 1, OMAction.ATTACK, ATTACKED, 3, 50.0, mode=OMMode.TELEGRAPH)
    lib.om_world_step(w)
    assert any(t.target_idx == ATTACKED for t in read_telegraphs(lib, w)), "fixture: telegraph not pending"
    return w


def test_R_072_02_telegraphed_attack_selects_defensive_stand(lib, world_factory):
    """Given a player region with a pending telegraphed attack and a twin quiet region, When the context is refreshed from world state and selection runs, Then Defensive Stand on the attacked region has the strictly highest score and is the selected mission."""
    w = _telegraphed_frontier(lib, world_factory)
    _refresh(lib, w, QUIET)
    _refresh(lib, w, ATTACKED)

    lib.om_mission_build_candidate_pool(w)
    pool = read_mission_candidates(lib, w)
    attacked_ds = [c for c in pool if c.region_idx == ATTACKED and c.archetype == OMMissionArchetype.DEFENSIVE_STAND]
    assert len(attacked_ds) == 1
    others = [c.score for c in pool if c is not attacked_ds[0]]
    assert all(attacked_ds[0].score > s for s in others)

    force_draws(lib, w, [0.0])
    chosen = pool[lib.om_mission_select(w)]
    assert (chosen.region_idx, chosen.archetype) == (ATTACKED, OMMissionArchetype.DEFENSIVE_STAND)


def test_R_072_02_telegraphed_attack_raises_conflict_term(lib, world_factory):
    """Given a pending telegraphed attack on a region, When the context is refreshed, Then that region's urgency rises by at least the recent-attack term 0.4 * 0.5 * (0.5 * 1) = 0.1 and the quiet twin's urgency does not move."""
    w = _telegraphed_frontier(lib, world_factory)
    before_attacked = lib.om_mission_compute_urgency(w, ATTACKED, OMMissionArchetype.DEFENSIVE_STAND)
    before_quiet = lib.om_mission_compute_urgency(w, QUIET, OMMissionArchetype.DEFENSIVE_STAND)
    _refresh(lib, w, QUIET)
    _refresh(lib, w, ATTACKED)
    after_attacked = lib.om_mission_compute_urgency(w, ATTACKED, OMMissionArchetype.DEFENSIVE_STAND)
    after_quiet = lib.om_mission_compute_urgency(w, QUIET, OMMissionArchetype.DEFENSIVE_STAND)
    assert after_attacked - before_attacked >= 0.1 - 1e-9
    assert after_quiet == before_quiet
