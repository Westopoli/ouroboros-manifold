"""ALG-47 Commander pools (docs/bible/algorithms.md), rules R-058-01..R-058-04 (E-08, S-058).

Isolation: pool roll, previous-pool score and weighted draw, nemesis gather and uniform draw,
fallback order, driven on hand-built characters and lineages through ctypes. Draws are forced
with om_rng_force so the expected pick is computed in the test from the row's formula.
Constants are read from csrc/om_constants.h by name.
Unstated: none that block the arithmetic; the order members enter the weighted draw is
the character table order (not stated in the row), Westley's.
"""
import ctypes

import pytest

from alg_consts import const
from conftest import OmSelectionRecord, force_draws, set_edge, set_owner

P_PREV = const("POOL_PREVIOUS_PROB")
P_NEM = const("POOL_NEMESIS_PROB")
P_UNREL = const("POOL_UNRELATED_PROB")
GAP_W = const("SCORE_GAP_WEIGHT")
DEN_W = const("SCORE_DENSITY_WEIGHT")
GAP_PEAK = const("SELECTOR_GAP_BONUS_PEAK")
DEN_PEAK = const("SCORE_DENSITY_PEAK")
PREVIOUS, NEMESIS, UNRELATED = 0, 1, 2
N = 4


def expected_score(chapters_ago, living_nearby):
    return GAP_W * min(chapters_ago, GAP_PEAK) / GAP_PEAK + DEN_W * min(living_nearby, DEN_PEAK) / DEN_PEAK


def _complete_graph(lib, w):
    for a in range(N):
        for b in range(a + 1, N):
            set_edge(lib, w, a, b)


def _lineage(lib, w, lineage, chapters, member_ids, region=0):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=region)
    lib.om_lineage_set_chapter_count(w, lineage_id=lineage, chapters=chapters)
    for m in member_ids:
        lib.om_character_create(w, character_id=m, lineage_id=lineage, region_idx=region, rank=3,
                                birth_tick=0, lifespan=10_000_000)


def _rotate(lib, w, pool):
    rec = OmSelectionRecord()
    lib.om_character_selector_force_rotate(w, lineage_id=99, mission_region=0, reason=0, pool=pool,
                                           out_record=ctypes.byref(rec))
    return rec


def test_ALG_47_pool_probabilities_sum_to_one():
    """ALG-47: the three pool probabilities are a partition of one draw."""
    assert P_PREV + P_NEM + P_UNREL == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("draw,expected", [
    (0.0, PREVIOUS),
    (P_PREV - 1e-9, PREVIOUS),
    (P_PREV, NEMESIS),
    (P_PREV + P_NEM - 1e-9, NEMESIS),
    (P_PREV + P_NEM, UNRELATED),
    (0.999999, UNRELATED),
])
def test_ALG_47_one_draw_selects_the_pool(lib, world_factory, draw, expected):
    """ALG-47 / R-058-01: draw < 0.70 previous, < 0.90 nemesis, else unrelated; boundaries belong to the upper pool."""
    w = world_factory(n_regions=N)
    assert lib.om_selector_roll_pool(w, draw=draw) == expected


def test_ALG_47_pool_positive_control(lib, world_factory):
    """Positive control: a boundary expectation shifted into the wrong pool must be rejected."""
    w = world_factory(n_regions=N)
    got = lib.om_selector_roll_pool(w, draw=P_PREV)
    with pytest.raises(AssertionError):
        assert got == PREVIOUS


@pytest.mark.parametrize("chapters_ago,nearby", [(1, 1), (2, 3), (3, 5), (4, 6), (9, 100), (1, 0)])
def test_ALG_47_previous_score_formula(lib, world_factory, chapters_ago, nearby):
    """ALG-47 / R-058-02: score = 0.6 * min(ago, 4)/4 + 0.4 * min(nearby, 5)/5."""
    w = world_factory(n_regions=N)
    got = lib.om_selector_score_previous_lineage(w, chapters_ago=chapters_ago, living_nearby=nearby)
    assert got == pytest.approx(expected_score(chapters_ago, nearby), abs=1e-12)


def test_ALG_47_previous_score_positive_control(lib, world_factory):
    """Positive control: a score computed without the cap at the peak values must be rejected."""
    w = world_factory(n_regions=N)
    got = lib.om_selector_score_previous_lineage(w, chapters_ago=8, living_nearby=10)
    uncapped = GAP_W * 8 / GAP_PEAK + DEN_W * 10 / DEN_PEAK
    with pytest.raises(AssertionError):
        assert got == pytest.approx(uncapped, abs=1e-9)


def test_ALG_47_previous_pool_weighted_draw_every_member_carries_its_lineage_score(lib, world_factory):
    """ALG-47 / R-058-02: one weighted draw; each nearby member carries its lineage's score.
    Lineage 7 has 1 member (chapters 1) and lineage 8 has 2 members (chapters 4); the member
    weights are s7, s8, s8 in character-table order, with s = expected_score(chapters, living_nearby)."""
    s7 = expected_score(1, 1)
    s8 = expected_score(4, 2)
    total = s7 + 2 * s8
    cases = [
        (0.0, 100),
        (s7 / total - 1e-6, 100),
        (s7 / total + 1e-6, 200),
        ((s7 + s8) / total - 1e-6, 200),
        ((s7 + s8) / total + 1e-6, 201),
        (0.999999, 201),
    ]
    for draw, expected in cases:
        w = world_factory(n_regions=N)
        _complete_graph(lib, w)
        _lineage(lib, w, 7, 1, [100])
        _lineage(lib, w, 8, 4, [200, 201])
        force_draws(lib, w, [draw])
        rec = _rotate(lib, w, PREVIOUS)
        assert rec.commander_id == expected, f"draw {draw}: got {rec.commander_id}, expected {expected}"


def test_ALG_47_previous_pool_members_outside_two_hops_do_not_count(lib, world_factory):
    """ALG-47: only members within SELECTOR_PROXIMITY_HOPS of the mission region are candidates and count as nearby."""
    hops = const("SELECTOR_PROXIMITY_HOPS")
    w = world_factory(n_regions=6)
    for a in range(hops + 1):
        set_edge(lib, w, a, a + 1)
    _lineage(lib, w, 7, 3, [100], region=hops + 1)  # 3 hops from the mission region 0
    _lineage(lib, w, 8, 1, [200], region=hops)      # exactly at the limit
    force_draws(lib, w, [0.0])
    rec = _rotate(lib, w, PREVIOUS)
    assert rec.commander_id == 200


def _nemesis_set(lib, w, n_children, region=0):
    lib.om_character_create(w, character_id=300, lineage_id=0, region_idx=region, rank=3, birth_tick=0, lifespan=1)
    lib.om_character_kill(w, character_id=300, tick=1)  # the previous commander
    lib.om_character_create(w, character_id=301, lineage_id=0, region_idx=region, rank=3, birth_tick=0, lifespan=10_000_000)
    lib.om_character_tag_rival(w, character_id=301, rival_of_character_id=300)  # the rival
    ids = []
    for i in range(n_children):
        cid = 310 + i
        lib.om_character_create_child(w, child_id=cid, parent_id=301, region_idx=region, birth_tick=10, lifespan=10_000_000)
        ids.append(cid)
    return ids


def test_ALG_47_nemesis_gather_excludes_the_rival_and_draws_uniformly(lib, world_factory):
    """ALG-47 / R-058-03: candidates are living descendants of a rival of a previous commander, rival excluded;
    one uniform draw picks index floor(d * n)."""
    for n in (2, 3, 4):
        for k in range(n):
            w = world_factory(n_regions=N)
            _complete_graph(lib, w)
            ids = _nemesis_set(lib, w, n)
            assert lib.om_selector_gather_nemesis_candidates(w, mission_region=0) == n
            assert 301 not in [lib.om_selector_get_nemesis_candidate(w, i) for i in range(n)]
            force_draws(lib, w, [(k + 0.5) / n])
            rec = _rotate(lib, w, NEMESIS)
            assert rec.commander_id == ids[k], f"n={n} k={k}"


def test_ALG_47_nemesis_positive_control_wrong_index_rejected(lib, world_factory):
    """Positive control: the nemesis draw d=0.5 over 2 candidates picks the second, so asserting the first must fail."""
    w = world_factory(n_regions=N)
    _complete_graph(lib, w)
    ids = _nemesis_set(lib, w, 2)
    force_draws(lib, w, [0.5])
    rec = _rotate(lib, w, NEMESIS)
    with pytest.raises(AssertionError):
        assert rec.commander_id == ids[0]


def test_ALG_47_search_order_is_rolled_pool_then_priority_order(lib, world_factory):
    """ALG-47: an empty rolled pool falls through to the others in priority order previous, nemesis, unrelated.
    Nemesis rolled and empty with a previous candidate present -> previous (priority before unrelated)."""
    w = world_factory(n_regions=N)
    _complete_graph(lib, w)
    _lineage(lib, w, 7, 2, [100])
    force_draws(lib, w, [0.0])
    assert _rotate(lib, w, NEMESIS).commander_id == 100
    # Unrelated rolled always yields a fresh character, never the previous-pool member.
    w2 = world_factory(n_regions=N)
    _complete_graph(lib, w2)
    _lineage(lib, w2, 7, 2, [100])
    assert _rotate(lib, w2, UNRELATED).commander_id != 100


def test_ALG_47_unrelated_creates_member_in_owning_faction_with_new_lineage(lib, world_factory):
    """ALG-47 / R-058-04: unrelated = a new lineage_member in the mission region's owning faction and a new lineage."""
    w = world_factory(n_regions=N)
    set_owner(lib, w, 2, faction_id=3)
    cid = lib.om_selector_draw_unrelated(w, mission_region=2)
    assert cid > 0
    assert lib.om_character_faction(w, cid) == 3
    assert lib.om_character_lineage_id(w, cid) > 0
