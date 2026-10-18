"""ALG-55 Scoring and selection (docs/bible/algorithms.md), rules R-072-02..R-072-05 (E-10, S-072).

Isolation: om_mission_compute_urgency, om_mission_compute_relevance, om_mission_compute_preference,
om_mission_candidate_score and om_mission_select, each on a hand-built world or hand-injected
candidates. Expected values are computed in the test from the row's formulas; the weights come from the
file-local defines in csrc/mission.c (and csrc/om_constants.h) by name. Stability in the deficit term is
the ALG-09 composite read from the sim (ALG-09 has its own test).
Unstated: the row names the conflict divisors (70, 600) and weights (0.5, 0.3) only as literals, not as
named constants; they are read from the OM_MISSION_CONFLICT_* defines in mission.c, Westley's.
Unstated: "hops from the lineage's first history region by BFS over all edges" is exercised through
om_mission_refresh_context on a chain graph; archetype_count is set through om_mission_set_lineage_context.
"""
import ctypes

import pytest

from alg_consts import const
from conftest import (
    OMArchetype,
    OMComposite,
    OMEdge,
    OMField,
    OMStance,
    OMTier,
    force_draws,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)
from test_E10_S072_orders_come_from_where_the_world_hurts import read_mission_candidates

W_U = const("MISSION_SCORE_URGENCY_WEIGHT")
W_R = const("MISSION_SCORE_RELEVANCE_WEIGHT")
W_P = const("MISSION_SCORE_PREFERENCE_WEIGHT")
UF = const("URGENCY_FIELD_WEIGHT")
UC = const("URGENCY_CONFLICT_WEIGHT")
UH = const("URGENCY_CHAIN_WEIGHT")
RL = const("MISSION_RELEVANCE_LINEAGE_WEIGHT")
RP = const("MISSION_RELEVANCE_PROXIMITY_WEIGHT")
RA = const("MISSION_RELEVANCE_ARCHETYPE_WEIGHT")
MAX_HOPS = const("RELEVANCE_MAX_HOPS")
FIT = const("RELEVANCE_ARCHETYPE_FIT_THRESHOLD")
RARE = const("GENERATOR_RARE_PREFERENCE")
DEFAULT = const("GENERATOR_DEFAULT_PREFERENCE")
TOP_N = const("GENERATOR_TOP_N_CANDIDATES")
BORDER_DIV = const("MISSION_CONFLICT_BORDER_DIVISOR")
ATK_W = const("MISSION_CONFLICT_ATTACK_COUNT_WEIGHT")
ATK_DIV = const("MISSION_CONFLICT_ATTACK_BUDGET_DIVISOR")
ATK_TERM = const("MISSION_CONFLICT_ATTACK_TERM_WEIGHT")
LOSS_W = const("MISSION_CONFLICT_LOSS_COUNT_WEIGHT")
LOSS_TERM = const("MISSION_CONFLICT_LOSS_TERM_WEIGHT")
CHAIN_W = const("MISSION_CHAIN_EVENT_WEIGHT")
STAND = 0  # defensive stand; the urgency/relevance arithmetic does not depend on the archetype


def clamp01(x):
    return max(0.0, min(1.0, x))


def expected_urgency(m, e, stab, hostile_m, attacks, budget_sum, lost, revolts):
    deficit = ((100 - m) + (100 - e) + (100 - stab)) / 300.0
    conflict = clamp01(clamp01(hostile_m / BORDER_DIV)
                       + ATK_TERM * clamp01(ATK_W * attacks + budget_sum / ATK_DIV)
                       + LOSS_TERM * clamp01(LOSS_W * lost))
    chain = clamp01(CHAIN_W * revolts)
    return clamp01(UF * deficit + UC * conflict + UH * chain)


def _urgency_world(lib, world_factory, *, m, e, t, p, hostile_m):
    w = world_factory(n_regions=2)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=100.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_region(lib, w, 0, tier=OMTier.HOME, military=m, economy=e, tension=t, population=p)
    set_region(lib, w, 1, tier=OMTier.HOME, military=hostile_m, economy=50.0, tension=10.0, population=50.0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BORDER)
    return w


@pytest.mark.parametrize("m,e,t,p,hostile_m,attacks,budget,lost,revolts", [
    (40, 40, 40, 50, 70, 1, 300.0, 0, 2),     # the row's three terms all live, conflict at its cap
    (40, 40, 40, 50, 35, 0, 0.0, 0, 0),       # border threat only: 35/70 = 0.5
    (60, 50, 20, 60, 10, 1, 0.0, 0, 0),       # one attack, no budget: 0.5 * min(1, 0.5)
    (60, 50, 20, 60, 10, 0, 150.0, 1, 0),     # budget term plus one lost neighbour
    (60, 50, 20, 60, 10, 4, 900.0, 5, 0),     # attack and loss terms saturate
    (90, 90, 5, 90, 0, 0, 0.0, 0, 5),         # chain saturates at 1.0 (5 events * 0.3 > 1)
    (5, 5, 90, 5, 100, 6, 5000.0, 6, 9),      # everything saturated: urgency clamps at 1.0
])
def test_ALG_55_urgency_formula(lib, world_factory, m, e, t, p, hostile_m, attacks, budget, lost, revolts):
    """ALG-55 / R-072-02: urgency = clamp(0.4 deficit + 0.4 conflict + 0.2 chain)."""
    w = _urgency_world(lib, world_factory, m=m, e=e, t=t, p=p, hostile_m=hostile_m)
    lib.om_mission_set_conflict_context(w, 0, attacks, budget, lost)
    lib.om_mission_set_revolt_events(w, 0, revolts)
    mm = lib.om_region_field(w, 0, OMField.MILITARY)
    ee = lib.om_region_field(w, 0, OMField.ECONOMY)
    stab = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    hm = lib.om_region_field(w, 1, OMField.MILITARY)
    got = lib.om_mission_compute_urgency(w, 0, STAND)
    assert got == pytest.approx(expected_urgency(mm, ee, stab, hm, attacks, budget, lost, revolts), abs=1e-9)


def test_ALG_55_urgency_positive_control_wrong_deficit_divisor_rejected(lib, world_factory):
    """Positive control: a deficit divided by 200 instead of 300 (the OM_BUG_URGENCY_DEFICIT_DIVISOR_WRONG shape) must be rejected."""
    w = _urgency_world(lib, world_factory, m=40, e=40, t=40, p=50, hostile_m=0)
    got = lib.om_mission_compute_urgency(w, 0, STAND)
    stab = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    bad = clamp01(UF * ((100 - 40) + (100 - 40) + (100 - stab)) / 200.0)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(bad, abs=1e-9)


@pytest.mark.parametrize("lineage,hops,times_run", [
    (1.0, 0, 3), (1.0, 2, 1), (0.5, 5, 0), (0.0, 7, 9), (0.5, 3, 2), (0.0, 0, 0),
])
def test_ALG_55_relevance_formula(lib, world_factory, lineage, hops, times_run):
    """ALG-55 / R-072-03: relevance = clamp(0.4 lineage + 0.3 (1 - hops/5) + 0.3 min(1, count/3)), hops capped at 5."""
    w = world_factory(n_regions=3)
    lib.om_mission_set_lineage_context(w, 2, lineage, hops, times_run)
    exp = clamp01(RL * lineage + RP * (1.0 - min(hops, MAX_HOPS) / MAX_HOPS) + RA * min(1.0, times_run / FIT))
    assert lib.om_mission_compute_relevance(w, 2, STAND) == pytest.approx(exp, abs=1e-9)


def test_ALG_55_relevance_lineage_term_from_a_real_lineage(lib, world_factory):
    """ALG-55: lineage = 1.0 if a member lives in the region, 0.5 if the region is only in the lineage history,
    and hops are counted from the lineage's first history region over all edges (here a chain 0-1-2-3).
    Archetype count is 0 (no run recorded), so relevance = 0.4 lineage + 0.3 (1 - hops/5)."""
    w = world_factory(n_regions=4)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=50.0)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=100.0, economy=100.0, tension=0.0, population=100.0)
        set_owner(lib, w, r, 0, held_since=-1)
    for a in range(3):
        set_edge(lib, w, a, a + 1, OMEdge.BOTH)
    lib.om_lineage_create(w, 1, 0)                      # first history region 0
    lib.om_lineage_record_history_region(w, 1, 2)       # region 2 only in the history
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=3, rank=3, birth_tick=0, lifespan=10_000)  # member lives in 3
    lib.om_mission_refresh_context.argtypes = [type(w), ctypes.c_int32]
    lib.om_mission_refresh_context.restype = None
    for r in (2, 3):
        lib.om_mission_refresh_context(w, r)
    rel_history = lib.om_mission_compute_relevance(w, 2, STAND)
    rel_member = lib.om_mission_compute_relevance(w, 3, STAND)
    assert rel_history == pytest.approx(RL * 0.5 + RP * (1.0 - 2 / MAX_HOPS), abs=1e-9)
    assert rel_member == pytest.approx(RL * 1.0 + RP * (1.0 - 3 / MAX_HOPS), abs=1e-9)


def test_ALG_55_preference_rare_default_and_player_weight(lib, world_factory):
    """ALG-55 / R-072-04: 0.1 for a rare archetype, else the player's weight, default 0.5."""
    w = world_factory(n_regions=1)
    assert lib.om_mission_compute_preference(w, 0) == pytest.approx(DEFAULT, abs=1e-12)
    lib.om_mission_set_preference(w, 4, 0.8)
    assert lib.om_mission_compute_preference(w, 4) == pytest.approx(0.8, abs=1e-12)
    assert lib.om_mission_get_archetype_preference_weight(w, 4, 1) == pytest.approx(RARE, abs=1e-12)
    lib.om_mission_set_preference(w, 5, -1.0)
    assert lib.om_mission_compute_preference(w, 5) == pytest.approx(RARE, abs=1e-12)


@pytest.mark.parametrize("u,r,p", [(0.8, 0.6, 0.5), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.3, 0.9, 0.1)])
def test_ALG_55_candidate_score_formula(lib, u, r, p):
    """ALG-55 / R-072-05: score = 0.5 urgency + 0.3 relevance + 0.2 preference."""
    assert lib.om_mission_candidate_score(u, r, p) == pytest.approx(W_U * u + W_R * r + W_P * p, abs=1e-12)


def test_ALG_55_score_positive_control_swapped_weights_rejected(lib):
    """Positive control: urgency and preference weights swapped gives a different number, which must be rejected."""
    got = lib.om_mission_candidate_score(0.8, 0.6, 0.5)
    with pytest.raises(AssertionError):
        assert got == pytest.approx(W_P * 0.8 + W_R * 0.6 + W_U * 0.5, abs=1e-12)


def _inject(lib, w, scores):
    for i, s in enumerate(scores):
        lib.om_mission_inject_candidate(w, i, i % 10, s)


def test_ALG_55_selection_is_a_weighted_draw_over_the_top_five_by_cumulative_score(lib, world_factory):
    """ALG-55: pool = top GENERATOR_TOP_N_CANDIDATES (5) by score; r = U(0, sum); first candidate whose cumulative
    score >= r. Six candidates; the sixth (lowest) is outside the pool and never drawn."""
    scores = [0.90, 0.80, 0.70, 0.60, 0.50, 0.10]
    top = scores[:TOP_N]
    total = sum(top)
    cum = [sum(top[: i + 1]) for i in range(TOP_N)]
    # boundaries are probed 1e-6 either side: r = draw * total is a float product, so an exact tie is not portable
    cases = [(0.0, 0), (cum[0] / total - 1e-6, 0), (cum[0] / total + 1e-6, 1), (cum[2] / total - 1e-6, 2),
             (cum[2] / total + 1e-6, 3), (cum[3] / total + 1e-6, 4), (0.999999, 4)]
    for draw, expected in cases:
        w = world_factory(n_regions=6)
        _inject(lib, w, scores)
        force_draws(lib, w, [draw])
        assert lib.om_mission_select(w) == expected, f"draw {draw}"


def test_ALG_55_selection_pool_is_ordered_by_score_not_insertion(lib, world_factory):
    """ALG-55: with candidates injected in ascending score order, draw 0.0 picks the highest-scoring candidate."""
    scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    w = world_factory(n_regions=8)
    _inject(lib, w, scores)
    force_draws(lib, w, [0.0])
    assert lib.om_mission_select(w) == scores.index(0.7)
