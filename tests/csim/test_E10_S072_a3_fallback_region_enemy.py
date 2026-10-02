"""A3 fallback picks in core (architect rulings 2026-10-01 round 2, A40 and A41).

Q-072-01 / R-072-07 / R-072-08: when the mission generator finds no candidate, the fallback
is a Defensive Stand on the player's weakest region, against the nearest enemy.

  * om_mission_fallback_region(w): the player's weakest region is the lowest ALG-09 stability
    composite (OM_C_STABILITY), ties to the lowest region index (Westley, 2026-09-30). The
    military-plus-economy form is stale (A41).
  * om_mission_fallback_enemy(w, region_idx): the non-player, non-neutral faction nearest
    region_idx by connection hops (BFS over the region graph, a faction's distance is the
    minimum over its regions); ties to the highest total military (sum of OM_F_MILITARY over
    its regions, "tie" meaning within OM_TIE_EPSILON), then the lowest faction id; -1 when
    no faction qualifies (A40).

Isolation tests on constructed worlds (hard-fixture setters, no generator, no pipe). Each
pick has a positive control: a reference with the wrong rule (military plus economy for the
region; plain `>` for the near-tie enemy; military-only or nearest-region-only for the enemy)
gives a different answer on the very fixture the test asserts against, so a test that a
wrong implementation would pass cannot slip in.

Red on main: om_mission_fallback_enemy is not defined in libouroboros.so (the symbol is
declared by push/A3fb-contract, implemented with this piece's sim change), so the enemy
tests fail at first use of the symbol; the region tests with a stability/military+economy
split are red because main still ranks by military plus economy.
"""
import math
from collections import deque

import pytest

from conftest import OMArchetype, OMTier, set_edge, set_faction, set_owner, set_region

OM_TIE_EPSILON = 1e-12  # csrc/om_internal.h
M_MILITARY, M_ECONOMY = 0, 1
C_STABILITY = 0
PLAYER = 0


def _build(lib, world_factory, regions, edges):
    """regions: list of (owner, military, economy, tension, population); owner -1 is neutral.
    edges: list of (a, b). Every faction id that owns a region is registered; 0 is the player."""
    w = world_factory(n_regions=len(regions), seed=1)
    for fid in sorted({o for o, *_ in regions if o >= 0} | {PLAYER}):
        set_faction(lib, w, fid, OMArchetype.PLAYER if fid == PLAYER else OMArchetype.CONQUEROR)
    for i, (owner, mil, eco, ten, pop) in enumerate(regions):
        set_region(lib, w, i, tier=OMTier.HOME, military=mil, economy=eco, tension=ten,
                   population=pop, faction_id=owner)
        set_owner(lib, w, i, owner)
    for a, b in edges:
        set_edge(lib, w, a, b)
    return w


def _stability(lib, w, i):
    return lib.om_region_composite(w, i, C_STABILITY)


def _region_by_stability(lib, w, regions):
    own = [i for i, r in enumerate(regions) if r[0] == PLAYER]
    return min(own, key=lambda i: (_stability(lib, w, i), i))


def _region_by_military_plus_economy(lib, w, regions):
    own = [i for i, r in enumerate(regions) if r[0] == PLAYER]
    return min(own, key=lambda i: (lib.om_region_field(w, i, M_MILITARY) + lib.om_region_field(w, i, M_ECONOMY), i))


def _hops(n, edges, src):
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    dist, queue = {src: 0}, deque([src])
    while queue:
        x = queue.popleft()
        for y in adj[x]:
            if y not in dist:
                dist[y] = dist[x] + 1
                queue.append(y)
    return dist


def _enemy_reference(lib, w, regions, edges, region, eps=OM_TIE_EPSILON, nearest_region_only=False, ignore_hops=False):
    """The rule (eps = OM_TIE_EPSILON); the wrong variants are the positive controls."""
    dist = _hops(len(regions), edges, region)
    best = None  # (faction, hops, military)
    for f in sorted({r[0] for r in regions if r[0] >= 0 and r[0] != PLAYER}):
        owned = [i for i, r in enumerate(regions) if r[0] == f and i in dist]
        if not owned:
            continue
        hops = 0 if ignore_hops else min(dist[i] for i in owned)
        if nearest_region_only:
            near = min(owned, key=lambda i: (dist[i], i))
            mil = lib.om_region_field(w, near, M_MILITARY)
        else:
            mil = sum(lib.om_region_field(w, i, M_MILITARY) for i in owned)
        if best is None or hops < best[1] or (hops == best[1] and mil > best[2] + eps):
            best = (f, hops, mil)
    return -1 if best is None else best[0]


# ---- om_mission_fallback_region (R-072-07, A41) ----

# r0: low military plus economy, middling stability. r1: high economy. r2: the lowest stability
# (high military and economy, but tension 90 and population 30). r3: another faction's, the
# lowest of all and ignored. stability: r0 45.00, r1 53.75, r2 35.00.
REGION_SPLIT = [
    (PLAYER, 20.0, 10.0, 30.0, 50.0),
    (PLAYER, 20.0, 90.0, 5.0, 50.0),
    (PLAYER, 60.0, 60.0, 90.0, 30.0),
    (1, 10.0, 0.0, 99.0, 20.0),
]
REGION_EDGES = [(0, 1), (1, 2), (2, 3)]


def test_R_072_07_fallback_region_is_the_lowest_stability_composite(lib, world_factory):
    """R-072-07 (Q-072-01): the weakest player region has the lowest OM_C_STABILITY composite."""
    w = _build(lib, world_factory, REGION_SPLIT, REGION_EDGES)
    assert lib.om_mission_fallback_region(w) == 2 == _region_by_stability(lib, w, REGION_SPLIT)


def test_R_072_07_control_military_plus_economy_would_pick_another_region(lib, world_factory):
    """Positive control: the stale military-plus-economy reference picks region 0 on this very
    world, so the test above is not satisfied by the stale rule."""
    w = _build(lib, world_factory, REGION_SPLIT, REGION_EDGES)
    assert _region_by_military_plus_economy(lib, w, REGION_SPLIT) == 0
    assert _region_by_military_plus_economy(lib, w, REGION_SPLIT) != _region_by_stability(lib, w, REGION_SPLIT)


def test_R_072_07_fallback_region_ignores_other_factions_regions(lib, world_factory):
    """Region 3 belongs to faction 1 and has the lowest stability of the world; it is not the player's."""
    w = _build(lib, world_factory, REGION_SPLIT, REGION_EDGES)
    assert _stability(lib, w, 3) < min(_stability(lib, w, i) for i in range(3))
    assert lib.om_mission_fallback_region(w) != 3


def test_R_072_07_stability_ties_go_to_the_lowest_region_index(lib, world_factory):
    """Regions 2 and 3 have identical fields and the lowest stability; the lower index (2) wins."""
    regions = [
        (PLAYER, 40.0, 40.0, 20.0, 60.0),
        (PLAYER, 40.0, 5.0, 10.0, 60.0),
        (PLAYER, 15.0, 50.0, 70.0, 40.0),
        (PLAYER, 15.0, 50.0, 70.0, 40.0),
        (1, 50.0, 50.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    w = _build(lib, world_factory, regions, edges)
    assert _stability(lib, w, 2) == _stability(lib, w, 3) < min(_stability(lib, w, 0), _stability(lib, w, 1))
    assert lib.om_mission_fallback_region(w) == 2


def test_R_072_07_control_a_last_wins_reference_differs_on_the_tie(lib, world_factory):
    """Positive control: breaking the stability tie to the highest index names region 1, not 0."""
    regions = [
        (PLAYER, 15.0, 50.0, 70.0, 40.0),
        (PLAYER, 15.0, 50.0, 70.0, 40.0),
        (PLAYER, 40.0, 40.0, 20.0, 60.0),
    ]
    w = _build(lib, world_factory, regions, [(0, 1), (1, 2)])
    own = [0, 1, 2]
    last_wins = min(own, key=lambda i: (_stability(lib, w, i), -i))
    assert last_wins == 1 != _region_by_stability(lib, w, regions) == 0
    assert lib.om_mission_fallback_region(w) == 0


# ---- om_mission_fallback_enemy (R-072-08, A40) ----

def _enemy(lib, world_factory, regions, edges, region=0):
    w = _build(lib, world_factory, regions, edges)
    return w, lib.om_mission_fallback_enemy(w, region)


def test_R_072_08_nearest_faction_by_hops_beats_a_stronger_far_one(lib, world_factory):
    """Path 0-1-2-3-4. Faction 2 is 2 hops from region 0 with military 10, faction 1 is 4 hops with 90."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (2, 10.0, 20.0, 20.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (1, 90.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 2 == _enemy_reference(lib, w, regions, edges, 0)


def test_R_072_08_control_military_only_reference_differs_from_the_nearest(lib, world_factory):
    """Positive control: ignoring hops names faction 1 on the same world."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (2, 10.0, 20.0, 20.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (1, 90.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    w = _build(lib, world_factory, regions, edges)
    assert _enemy_reference(lib, w, regions, edges, 0, ignore_hops=True) == 1
    assert lib.om_mission_fallback_enemy(w, 0) == 2


def test_R_072_08_a_faction_distance_is_its_nearest_region(lib, world_factory):
    """Faction 1 owns regions 1 (1 hop) and 4 (4 hops); faction 2 owns region 2 (2 hops). Faction 1 is nearest."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (1, 5.0, 20.0, 20.0, 50.0),
        (2, 80.0, 20.0, 20.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (1, 5.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 1 == _enemy_reference(lib, w, regions, edges, 0)


def test_R_072_08_hop_ties_go_to_the_highest_total_military_over_all_regions(lib, world_factory):
    """Factions 1 and 2 are both 1 hop from region 0. Faction 2's nearest region is stronger (30 against 20),
    but faction 1's total over two regions is 35 against 30."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (1, 20.0, 20.0, 20.0, 50.0),
        (2, 30.0, 20.0, 20.0, 50.0),
        (1, 15.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (0, 2), (1, 3)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 1 == _enemy_reference(lib, w, regions, edges, 0)


def test_R_072_08_control_nearest_region_military_reference_differs(lib, world_factory):
    """Positive control: comparing only the nearest region's military names faction 2."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (1, 20.0, 20.0, 20.0, 50.0),
        (2, 30.0, 20.0, 20.0, 50.0),
        (1, 15.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (0, 2), (1, 3)]
    w = _build(lib, world_factory, regions, edges)
    assert _enemy_reference(lib, w, regions, edges, 0, nearest_region_only=True) == 2
    assert lib.om_mission_fallback_enemy(w, 0) == 1


def test_R_072_08_equal_totals_go_to_the_lowest_faction_id(lib, world_factory):
    """Factions 1 and 2 tie on hops and military exactly; faction 2 owns the lower region index,
    the lowest faction id (1) still wins."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (2, 40.0, 20.0, 20.0, 50.0),
        (1, 40.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (0, 2)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 1 == _enemy_reference(lib, w, regions, edges, 0)


NEAR_TIE = [
    (PLAYER, 30.0, 30.0, 30.0, 50.0),
    (2, 50.0 + 5e-13, 20.0, 20.0, 50.0),
    (1, 50.0, 20.0, 20.0, 50.0),
]
NEAR_TIE_EDGES = [(0, 1), (0, 2)]


def test_R_072_08_totals_within_tie_epsilon_pick_the_lowest_faction_id(lib, world_factory):
    """Faction 2 leads faction 1 by 5e-13, inside OM_TIE_EPSILON but not bit-equal: they tie, faction 1 wins."""
    w = _build(lib, world_factory, NEAR_TIE, NEAR_TIE_EDGES)
    gap = lib.om_region_field(w, 1, M_MILITARY) - lib.om_region_field(w, 2, M_MILITARY)
    assert 0.0 < gap < OM_TIE_EPSILON
    assert lib.om_mission_fallback_enemy(w, 0) == 1 == _enemy_reference(lib, w, NEAR_TIE, NEAR_TIE_EDGES, 0)


def test_R_072_08_control_plain_greater_than_reference_differs_on_the_near_tie(lib, world_factory):
    """Positive control: a plain `>` reference (no epsilon) names faction 2 on the same fixture."""
    w = _build(lib, world_factory, NEAR_TIE, NEAR_TIE_EDGES)
    assert _enemy_reference(lib, w, NEAR_TIE, NEAR_TIE_EDGES, 0, eps=0.0) == 2


def test_R_072_08_control_a_gap_outside_epsilon_picks_the_larger_total(lib, world_factory):
    """Positive control: the same fixture with the gap widened to 1e-3 picks faction 2, so only the
    sub-epsilon case flips the answer."""
    regions = list(NEAR_TIE)
    regions[1] = (2, 50.0 + 1e-3, 20.0, 20.0, 50.0)
    w = _build(lib, world_factory, regions, NEAR_TIE_EDGES)
    assert lib.om_mission_fallback_enemy(w, 0) == 2 == _enemy_reference(lib, w, regions, NEAR_TIE_EDGES, 0)


def test_R_072_08_the_player_and_neutral_regions_are_never_the_enemy(lib, world_factory):
    """The player owns the adjacent regions and a neutral region sits next door with the highest
    military; the enemy is the only other faction, two hops out."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (PLAYER, 90.0, 30.0, 30.0, 50.0),
        (-1, 99.0, 20.0, 20.0, 50.0),
        (1, 5.0, 20.0, 20.0, 50.0),
    ]
    edges = [(0, 1), (0, 2), (1, 3)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 1


def test_R_072_08_a_single_other_faction_is_the_enemy_however_far(lib, world_factory):
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (-1, 0.0, 0.0, 0.0, 0.0),
        (1, 5.0, 20.0, 20.0, 50.0),
    ]
    w, enemy = _enemy(lib, world_factory, regions, [(0, 1), (1, 2), (2, 3)])
    assert enemy == 1


def test_R_072_08_no_candidate_faction_answers_minus_one(lib, world_factory):
    """Only the player and neutral regions exist: there is no enemy to name."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (PLAYER, 40.0, 30.0, 30.0, 50.0),
        (-1, 50.0, 20.0, 20.0, 50.0),
    ]
    w, enemy = _enemy(lib, world_factory, regions, [(0, 1), (1, 2)])
    assert enemy == -1


# ---- om_mission_fallback_enemy over unreachable factions (A50, architect rulings 2026-10-01
# round 2, Addendum 22) ----
# A faction no hop path reaches from the region counts as equally far (all unreachable factions
# tie on distance), so the tie rule picks among them: highest total military across all its
# regions (a tie being within OM_TIE_EPSILON), then the lowest faction id. A reachable faction is
# always nearer than an unreachable one. -1 stays the answer only when no faction owns a region.
# Red today: om_mission_fallback_enemy skips unreachable factions, so these answer -1.
# (No existing test pins unreachable = -1: test_R_072_08_no_candidate_faction_answers_minus_one
# has no other faction at all and stays right. `_enemy_reference` above skips factions it cannot
# reach, but only as a helper; no assertion here relies on that for an unreachable fixture, so
# no test-defect row is needed.)

def _unreachable_reference(lib, w, regions, edges, region, eps=OM_TIE_EPSILON, wrong=None):
    """A50 rule: hops for reachable factions, equal (infinite) for the rest, then total military
    (within eps tied), then the lowest id. `wrong` is the positive-control variant."""
    dist = _hops(len(regions), edges, region)
    best = None  # (faction, hops, military)
    for f in sorted({r[0] for r in regions if r[0] >= 0 and r[0] != PLAYER}):
        owned = [i for i, r in enumerate(regions) if r[0] == f]
        hops = min((dist[i] for i in owned if i in dist), default=10 ** 9)
        if wrong == "strongest_region":
            mil = max(lib.om_region_field(w, i, M_MILITARY) for i in owned)
        else:
            mil = sum(lib.om_region_field(w, i, M_MILITARY) for i in owned)
        if wrong == "lowest_id":
            mil = 0.0
        if best is None or hops < best[1] or (hops == best[1] and mil > best[2] + eps):
            best = (f, hops, mil)
    return -1 if best is None else best[0]


# Region 0 is the player's, alone (no edges at all). Faction 1: 40. Faction 2: 60 (strongest
# single region). Faction 3: two regions of 35, total 70.
UNREACHABLE = [
    (PLAYER, 30.0, 30.0, 30.0, 50.0),
    (1, 40.0, 20.0, 20.0, 50.0),
    (2, 60.0, 20.0, 20.0, 50.0),
    (3, 35.0, 20.0, 20.0, 50.0),
    (3, 35.0, 20.0, 20.0, 50.0),
]


def test_R_072_08_unreachable_factions_tie_on_distance_and_the_highest_total_wins(lib, world_factory):
    """No faction is reachable from region 0, so all tie; faction 3 holds the highest total (70)."""
    w, enemy = _enemy(lib, world_factory, UNREACHABLE, [])
    assert enemy == 3 == _unreachable_reference(lib, w, UNREACHABLE, [], 0)


def test_R_072_08_control_unreachable_wrong_rules_name_other_factions(lib, world_factory):
    """Positive control: strongest-region-only names faction 2, lowest-id-only names faction 1, on
    the very world above; so the test above is not satisfied by either wrong rule."""
    w = _build(lib, world_factory, UNREACHABLE, [])
    assert _unreachable_reference(lib, w, UNREACHABLE, [], 0, wrong="strongest_region") == 2
    assert _unreachable_reference(lib, w, UNREACHABLE, [], 0, wrong="lowest_id") == 1
    assert _unreachable_reference(lib, w, UNREACHABLE, [], 0) == 3


def test_R_072_08_unreachable_equal_totals_go_to_the_lowest_faction_id(lib, world_factory):
    """Factions 1 and 2 tie exactly and are unreachable; faction 2 holds the lower region index, and
    the lowest id (1) wins."""
    regions = [
        (PLAYER, 30.0, 30.0, 30.0, 50.0),
        (2, 50.0, 20.0, 20.0, 50.0),
        (1, 50.0, 20.0, 20.0, 50.0),
    ]
    w, enemy = _enemy(lib, world_factory, regions, [])
    assert enemy == 1 == _unreachable_reference(lib, w, regions, [], 0)


def test_R_072_08_unreachable_totals_within_tie_epsilon_pick_the_lowest_faction_id(lib, world_factory):
    """Faction 2 leads faction 1 by 5e-13 (inside OM_TIE_EPSILON, not bit-equal), both unreachable:
    they tie and faction 1 wins."""
    w = _build(lib, world_factory, NEAR_TIE, [])
    gap = lib.om_region_field(w, 1, M_MILITARY) - lib.om_region_field(w, 2, M_MILITARY)
    assert 0.0 < gap < OM_TIE_EPSILON
    assert lib.om_mission_fallback_enemy(w, 0) == 1 == _unreachable_reference(lib, w, NEAR_TIE, [], 0)


def test_R_072_08_control_unreachable_plain_greater_than_names_the_other_faction(lib, world_factory):
    """Positive control: a plain `>` reference names faction 2 on the near-tie world, so the
    sub-epsilon test above is not satisfied by it."""
    w = _build(lib, world_factory, NEAR_TIE, [])
    assert _unreachable_reference(lib, w, NEAR_TIE, [], 0, eps=0.0) == 2


def test_R_072_08_unreachable_gap_outside_epsilon_picks_the_larger_total(lib, world_factory):
    """The near-tie world with the gap widened to 1e-3 (outside epsilon): faction 2 wins on total."""
    regions = list(NEAR_TIE)
    regions[1] = (2, 50.0 + 1e-3, 20.0, 20.0, 50.0)
    w, enemy = _enemy(lib, world_factory, regions, [])
    assert enemy == 2 == _unreachable_reference(lib, w, regions, [], 0)


def test_R_072_08_a_reachable_weak_faction_beats_unreachable_strong_ones(lib, world_factory):
    """Positive control (passes today): faction 1 (40) is joined to region 0 through neutral region
    5 (2 hops); factions 2 and 3 stay unreachable with more military. Hops still decide."""
    regions = UNREACHABLE + [(-1, 0.0, 0.0, 0.0, 0.0)]
    edges = [(0, 5), (5, 1)]
    w, enemy = _enemy(lib, world_factory, regions, edges)
    assert enemy == 1 == _unreachable_reference(lib, w, regions, edges, 0)


def test_R_072_08_an_unreachable_enemy_beats_no_enemy(lib, world_factory):
    """Positive control for -1: the one other faction is unreachable and still the answer; with its
    region handed to the player there is no enemy and the answer is -1 (the pipe's error case)."""
    regions = [(PLAYER, 30.0, 30.0, 30.0, 50.0), (1, 40.0, 20.0, 20.0, 50.0)]
    w, enemy = _enemy(lib, world_factory, regions, [])
    assert enemy == 1
    regions = [(PLAYER, 30.0, 30.0, 30.0, 50.0), (PLAYER, 40.0, 20.0, 20.0, 50.0)]
    w, enemy = _enemy(lib, world_factory, regions, [])
    assert enemy == -1
