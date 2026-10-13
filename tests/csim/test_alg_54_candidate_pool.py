"""ALG-54 Candidate pool (docs/bible/algorithms.md), proving R-072-01 (S-072, E-10).

Regions = the player's regions plus every neighbor (all edge types), excluding empty tier. For each
region and each of the 10 archetypes the trigger function returns fired; fired pairs enter the pool.
The Reconquest trigger (owner is not the player and the region's previous owner is the player) is
the probe: it depends on nothing but ownership, so whether a region enters the pool says whether the
region set is the one ALG-54 describes. The Defensive Stand trigger probes player-owned regions.
"""
import ctypes

from conftest import OMArchetype, OMEdge, OMStance, OMTier, set_edge, set_faction, set_owner, set_region, set_stance

RECONQUEST, DEFENSIVE_STAND = 2, 0


class _Cand(ctypes.Structure):
    _fields_ = [
        ("region_idx", ctypes.c_uint32), ("archetype", ctypes.c_uint32), ("urgency", ctypes.c_double),
        ("relevance", ctypes.c_double), ("preference", ctypes.c_double), ("score", ctypes.c_double),
    ]


def _pool(lib, w):
    lib.om_mission_build_candidate_pool(w)
    buf = (_Cand * 128)()
    n = lib.om_mission_candidates(w, buf, 128)
    return {(buf[i].region_idx, buf[i].archetype) for i in range(n)}


def _world(lib, world_factory, n=8):
    w = world_factory(n_regions=n)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=50.0)
    for r in range(n):
        set_region(lib, w, r, tier=OMTier.HOME, military=60.0, economy=60.0, tension=20.0, population=60.0)
    set_owner(lib, w, 0, 0)  # the player's one region
    return w


def _lost_to(lib, w, region, owner, tier=OMTier.HOME):
    """A region the player once held (previous owner = player) and that now belongs to `owner` (-1 = nobody)."""
    set_region(lib, w, region, tier=tier, military=60.0, economy=60.0, tension=20.0, population=60.0 if tier != OMTier.EMPTY else 0.0)
    set_owner(lib, w, region, owner)
    lib.om_region_set_previous_owner(w, region, 0)


def test_control_ALG_54_probe_fires_where_the_rule_says_and_not_elsewhere(lib, world_factory):
    """Positive control: the Reconquest probe enters the pool for an adjacent lost region, and a lost region that is not adjacent to the player stays out; the same probe on the same region without a previous owner of the player stays out."""
    w = _world(lib, world_factory)
    set_edge(lib, w, 0, 1)
    _lost_to(lib, w, 1, 1)
    _lost_to(lib, w, 5, 1)  # not adjacent to region 0
    set_owner(lib, w, 2, 1)  # owned by the enemy, previous owner none
    set_edge(lib, w, 0, 2)
    pool = _pool(lib, w)
    assert (1, RECONQUEST) in pool
    assert (5, RECONQUEST) not in pool
    assert (2, RECONQUEST) not in pool


def test_ALG_54_neighbors_of_every_edge_type_are_candidate_regions(lib, world_factory):
    """ALG-54: every neighbor of a player region, whatever the edge type (border, trade, both), is a candidate region."""
    w = _world(lib, world_factory)
    for r, edge in ((1, OMEdge.BORDER), (2, OMEdge.TRADE), (3, OMEdge.BOTH)):
        set_edge(lib, w, 0, r, edge)
        _lost_to(lib, w, r, 1)
    pool = _pool(lib, w)
    assert {(1, RECONQUEST), (2, RECONQUEST), (3, RECONQUEST)} <= pool


def test_ALG_54_only_the_players_regions_and_their_neighbors(lib, world_factory):
    """ALG-54: a region two hops from every player region is not a candidate; a neighbor of a second player region is."""
    w = _world(lib, world_factory)
    set_owner(lib, w, 4, 0)  # the player's second region
    set_edge(lib, w, 0, 1)
    set_edge(lib, w, 1, 2)  # 2 is two hops from region 0 ...
    set_edge(lib, w, 4, 5)  # ... and 5 is adjacent to the second player region
    for r in (1, 2, 5):
        _lost_to(lib, w, r, 1)
    pool = _pool(lib, w)
    assert (1, RECONQUEST) in pool and (5, RECONQUEST) in pool
    assert (2, RECONQUEST) not in pool


def test_ALG_54_player_regions_enter_through_their_own_triggers(lib, world_factory):
    """ALG-54: a player region with a hostile neighbor fires Defensive Stand and is in the pool; the player's quiet region is not."""
    w = _world(lib, world_factory)
    set_owner(lib, w, 1, 0)
    set_owner(lib, w, 2, 1)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_edge(lib, w, 0, 2)  # region 0 faces the enemy
    set_edge(lib, w, 0, 1)
    pool = _pool(lib, w)
    assert (0, DEFENSIVE_STAND) in pool
    assert not any(r == 1 and a == DEFENSIVE_STAND for r, a in pool)


def test_ALG_54_an_unowned_neighbor_with_population_is_not_empty_tier(lib, world_factory):
    """ALG-54: only the empty tier is excluded. A neighbor with no owner but a frontier tier, once held by the player (previous owner = player), fires Reconquest and enters the pool; the C pool skips every unowned region."""
    w = _world(lib, world_factory)
    set_edge(lib, w, 0, 1)
    _lost_to(lib, w, 1, -1, tier=OMTier.FRONTIER)
    assert (1, RECONQUEST) in _pool(lib, w), "unowned frontier neighbor with previous owner = player missing from the pool"


def test_ALG_54_empty_tier_regions_are_excluded(lib, world_factory):
    """ALG-54: 'excluding empty tier'. A neighbor of empty tier that an enemy still lists as its owner and the player once held must stay out of the pool; the C pool tests ownership, never the tier."""
    w = _world(lib, world_factory)
    set_edge(lib, w, 0, 1)
    _lost_to(lib, w, 1, 1, tier=OMTier.EMPTY)
    assert (1, RECONQUEST) not in _pool(lib, w), "empty-tier region entered the pool"
