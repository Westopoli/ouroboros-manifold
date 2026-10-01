"""S-062 -- faction after collapse: the rotation pools restricted to surviving factions.

R-062-02, Q-062-01 (answered 2026-09-13, option b), ruling A24 (architect-rulings-2.md,
Addendum 10). Piece B6-collapse-pick (csrc/generational.c), tests first.

The rule: the previous-descendant pool, then the nemesis-descendant pool (R-058-01 to
R-058-03) run restricted to candidates whose faction still holds a region; the player joins
the faction of the candidate drawn. With both pools empty, the surviving faction with the
most regions, uniform among ties.

What these tests pin and what they leave open:
- The pools' 2 hops are measured from the last mission's region (om_mission_last_region,
  ruling A26, R-062-02). Most fixtures use a complete edge graph, so every candidate is within
  2 hops of that region; the last-region tests below use a line graph and move the region.
- A previous-pool candidate more than 2 hops from the last mission region is not in the pool
  (R-058-02) and a nemesis descendant more than 2 hops away is not in the nemesis pool
  (R-058-03); with both pools empty the most-regions rule applies.
- A fixture with a non-empty pool pins the result whichever pool the 0.70/0.20/0.10 roll
  lands on (a rolled-empty pool falls through previous, then nemesis); the unrelated pool is
  not a collapse pool in these fixtures.
- The tie is pinned as: over seeds both tied factions appear, and the same seed gives the
  same faction. The single-largest case pins the winner only; whether the sim consumes a
  draw there is not pinned (the rule does not say).
- A candidate's faction is the faction field of the character record.
"""
import pytest

from conftest import set_edge, set_owner

PLAYER = 0
GEN_RANK_LINEAGE_MEMBER = 3
TIE_SEEDS = range(1, 33)
N = 6


def _complete_graph(lib, w, n=N):
    for a in range(n):
        for b in range(a + 1, n):
            set_edge(lib, w, a, b)


def _owners(lib, w, owners):
    for region, faction in enumerate(owners):
        set_owner(lib, w, region, faction_id=faction)


def _played_lineage(lib, w, lineage, faction, region, member_id, chapters=2):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=region)
    lib.om_lineage_set_chapter_count(w, lineage_id=lineage, chapters=chapters)
    lib.om_character_create(w, character_id=member_id, lineage_id=lineage, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)
    lib.om_character_set_faction(w, member_id, faction_id=faction)


def _nemesis_descendant(lib, w, rival_id, commander_id, child_id, rival_faction, child_faction, region):
    """A previous commander, an enemy rival of it, and the rival's living child. The rival
    and child belong to no lineage record, so the previous pool stays empty."""
    lib.om_character_create(w, character_id=commander_id, lineage_id=0, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=1)
    lib.om_character_kill(w, commander_id, 1)
    lib.om_character_create(w, character_id=rival_id, lineage_id=0, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)
    lib.om_character_set_faction(w, rival_id, faction_id=rival_faction)
    lib.om_character_tag_rival(w, character_id=rival_id, rival_of_character_id=commander_id)
    lib.om_character_create_child(w, child_id=child_id, parent_id=rival_id, region_idx=region,
                                  birth_tick=10, lifespan=10_000_000)
    lib.om_character_set_faction(w, child_id, faction_id=child_faction)


# faction 1: 1 region, faction 2: 3 regions (largest), faction 3: 2 regions; player faction 0 holds none.
SIZED = [1, 2, 2, 2, 3, 3]


def _pick(lib, w):
    return lib.om_player_faction_reassign_on_collapse(w, player_faction=PLAYER)


def test_R_062_02_q_062_01_a_surviving_previous_lineage_in_a_smaller_faction_wins_over_the_largest(lib, world_factory):
    """Given a previously played lineage with a living member in the smaller surviving faction 1, When the player's faction collapses, Then the player joins faction 1, not faction 2 which holds the most regions."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, SIZED)
        _played_lineage(lib, w, lineage=7, faction=1, region=0, member_id=100)
        assert _pick(lib, w) == 1, f"seed {seed}: the previous-descendant pool must decide, not the region count"


def test_R_062_02_q_062_01_only_nemesis_descendants_survive_player_joins_the_nemesis_faction(lib, world_factory):
    """Given the previous pool is empty and a living descendant of a rival lives in surviving faction 1, When the player's faction collapses, Then the player joins faction 1, not faction 2 which holds the most regions."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, SIZED)
        _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                            rival_faction=3, child_faction=1, region=0)
        assert lib.om_lineage_count(w) == 0, "fixture: the previous pool must be empty"
        assert _pick(lib, w) == 1, f"seed {seed}: the nemesis-descendant pool must decide, and the rival itself is not a candidate"


def test_R_062_02_q_062_01_previous_pool_is_tried_before_the_nemesis_pool(lib, world_factory):
    """Given a previous lineage member in faction 1 and a nemesis descendant in faction 3, When the player's faction collapses, Then the player joins faction 1 or 3 by the pool roll, never the largest faction 2, and over seeds both appear."""
    picked = set()
    for seed in TIE_SEEDS:
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, SIZED)
        _played_lineage(lib, w, lineage=7, faction=1, region=0, member_id=100)
        _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                            rival_faction=2, child_faction=3, region=0)
        picked.add(_pick(lib, w))
    assert picked <= {1, 3}, f"a pool candidate's faction must be chosen, got {sorted(picked)}"
    assert picked == {1, 3}, "the pool roll never reached the nemesis pool (0.20) or the previous pool (0.70) over the seeds"


def test_R_062_02_q_062_01_both_pools_empty_the_single_largest_surviving_faction_wins(lib, world_factory):
    """Given both pools are empty, When the player's faction collapses, Then the surviving faction with the most regions is chosen."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, [1, 2, 2, 2, 3, 3])
        assert _pick(lib, w) == 2


def test_R_062_02_q_062_01_both_pools_empty_a_tie_is_a_uniform_draw_from_the_seeded_stream(lib, world_factory):
    """Given both pools are empty and factions 2 and 3 tie for the most regions, When the player's faction collapses, Then the choice is a draw from the seeded stream: over seeds both appear, faction 1 (fewer regions) never does."""
    picked = set()
    for seed in TIE_SEEDS:
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, [2, 2, 3, 3, 1, -1])
        picked.add(_pick(lib, w))
    assert picked <= {2, 3}, f"only a tied-largest faction may be chosen, got {sorted(picked)}"
    assert picked == {2, 3}, f"a tie must be broken by the seeded draw, not by faction id; only {sorted(picked)} appeared over {len(TIE_SEEDS)} seeds"


def test_R_062_02_q_062_01_same_seed_same_pick(lib, world_factory):
    """Given the same seed and the same fixture, When the faction is chosen twice in two worlds, Then the pick is identical, in a pool fixture and in a tie fixture."""
    def build(seed):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, [2, 2, 3, 3, 1, -1])
        _played_lineage(lib, w, lineage=7, faction=1, region=0, member_id=100)
        _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                            rival_faction=2, child_faction=3, region=0)
        return _pick(lib, w)

    for seed in (3, 11, 19):
        assert build(seed) == build(seed), f"seed {seed}: the same seed and fixture gave different picks"


def test_R_062_02_control_a_candidate_in_a_dead_faction_is_never_chosen(lib, world_factory):
    """Positive control: a previous lineage member and a nemesis descendant both belong to faction 4, which holds no region, and faction 1 survives with the fewest regions; Then neither pool may yield faction 4 and the pick falls to the most-regions rule (faction 2)."""
    for seed in TIE_SEEDS:
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, SIZED)
        _played_lineage(lib, w, lineage=7, faction=4, region=0, member_id=100)
        _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                            rival_faction=4, child_faction=4, region=0)
        assert _pick(lib, w) == 2, f"seed {seed}: a dead faction's candidate must not count, so the most-regions fallback applies"


def test_R_062_02_control_the_player_never_rejoins_its_own_collapsed_faction(lib, world_factory):
    """Positive control: the collapsed faction 0 has the highest-scoring previous lineage and a nemesis descendant; Then the player joins a surviving faction, never faction 0."""
    for seed in TIE_SEEDS:
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _owners(lib, w, SIZED)
        _played_lineage(lib, w, lineage=7, faction=PLAYER, region=0, member_id=100, chapters=8)
        _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                            rival_faction=PLAYER, child_faction=PLAYER, region=0)
        pick = _pick(lib, w)
        assert pick != PLAYER and pick in (1, 2, 3), f"seed {seed}: picked {pick}"
        assert pick == 2, f"seed {seed}: no surviving pool candidate, so the most-regions fallback applies"


# ---- the pools' 2 hops are measured from the last mission's region (A26) ----

def _line_graph(lib, w, n=N):
    for a in range(n - 1):
        set_edge(lib, w, a, a + 1)


def _last_mission_region(lib, w, region):
    lib.om_mission_start(w, PLAYER)
    lib.om_mission_setup(w, region, 0, 0)
    assert lib.om_mission_last_region(w) == region, "fixture: the last mission region must read back"


# line 0-1-2-3-4-5; faction 2 holds the most regions, faction 1 holds regions 4 and 5, faction 3 region 3.
LINE_OWNERS = [2, 2, 2, 3, 1, 1]


def test_R_062_02_the_previous_pool_is_measured_from_the_last_mission_region(lib, world_factory):
    """Given a lineage member in faction 1 at region 5 and one in faction 3 at region 1 on a line graph, When the last mission was at region 0 or 2 only the faction 3 member is within 2 hops and faction 3 is picked, at region 5 only the faction 1 member is and faction 1 is picked, at region 3 both are and either is picked; never the largest faction 2."""
    cases = {0: 3, 2: 3, 5: 1, 3: None}
    for last_region, expected in cases.items():
        for seed in (1, 2, 3, 4):
            w = world_factory(n_regions=N, seed=seed)
            _line_graph(lib, w)
            _owners(lib, w, LINE_OWNERS)
            _played_lineage(lib, w, lineage=7, faction=1, region=5, member_id=100)
            _played_lineage(lib, w, lineage=8, faction=3, region=1, member_id=101)
            _last_mission_region(lib, w, last_region)
            pick = _pick(lib, w)
            if expected is None:
                assert pick in (1, 3), f"last region {last_region}, seed {seed}: both members are in range, got {pick}"
            else:
                assert pick == expected, f"last region {last_region}, seed {seed}: got {pick}, expected {expected}"


def test_R_062_02_a_nemesis_descendant_beyond_2_hops_of_the_last_mission_region_is_not_a_candidate(lib, world_factory):
    """Given a nemesis descendant of faction 1 at region 5 and no previous lineage, When the last mission was at region 0 (5 hops away), Then the pools are empty and the most-regions faction 2 wins; when it was at region 4, the descendant is in range and faction 1 wins."""
    for seed in (1, 2, 3, 4):
        for last_region, expected in ((0, 2), (4, 1)):
            w = world_factory(n_regions=N, seed=seed)
            _line_graph(lib, w)
            _owners(lib, w, LINE_OWNERS)
            _nemesis_descendant(lib, w, rival_id=200, commander_id=201, child_id=202,
                                rival_faction=3, child_faction=1, region=5)
            _last_mission_region(lib, w, last_region)
            assert _pick(lib, w) == expected, f"last region {last_region}, seed {seed}"


# ---- applied: the collapse jump hands the player faction to the drawn candidate's faction ----

def test_R_062_02_q_062_01_the_collapse_jump_applies_the_pool_pick_to_the_player_faction(lib, world_factory):
    """Given a played lineage seated everywhere in the smallest surviving faction, When the jump after a mission finds the player's faction empty, Then om_player_faction reads that faction and the archetype swap leaves exactly one player faction."""
    from test_core_chapter_lifecycle import _campaign, _play_mission, _empty_player_faction, _survivor_counts

    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    _empty_player_faction(lib, w)
    counts = _survivor_counts(lib, w, PLAYER)
    assert len(counts) >= 2, "fixture: at least two survivors"
    smallest = min(counts, key=lambda f: (counts[f], f))
    assert counts[smallest] < max(counts.values()), "fixture: the target survivor must not hold the most regions"
    lib.om_lineage_create(w, lineage_id=9000, home_region=0)
    lib.om_lineage_set_chapter_count(w, lineage_id=9000, chapters=2)
    for i in range(lib.om_region_count(w)):
        lib.om_character_create(w, 9100 + i, 9000, i, GEN_RANK_LINEAGE_MEMBER, 0, 10_000_000)
        lib.om_character_set_faction(w, 9100 + i, faction_id=smallest)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_player_faction(w) == smallest, "the jump did not apply the pool pick to the player faction"
