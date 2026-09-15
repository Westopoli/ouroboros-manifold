"""S-039 -- When everyone wants the same region.

R-039-01, R-039-02, R-039-03, R-039-04, R-039-05, R-039-06. Formulas: ALG-23
(multi-faction collision), ALG-24 (colonize), ALG-20 to ALG-22 (attack against
an owned target) in algorithms.md.

Intents are injected with om_intent_inject so the commits the rules quote
(40 and 20 against one empty region) exist exactly; the injecting factions skip
their own 3d decision that tick. Draw order per docs/northstar/e2e/E-05.md:
collision winner draw, refund draw, one stochastic draw per applied attack
(owned target only), then the colony-penalty draw when the margin is narrow.
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMField,
    OMMode,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_attacks,
    read_collisions,
    read_colonizations,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def _two_colliders_on_empty(lib, world_factory, *, commit0=40.0, commit1=20.0,
                            budget0=200.0, budget1=200.0, eco0=200.0, eco1=100.0):
    """Faction 0 owns regions 0 and 1 (economies summing to eco0), faction 1
    owns region 2 (economy eco1); region 3 is empty and adjacent to 1 and 2.
    Both inject a colonize intent on region 3 with the given commits."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=budget0, confidence=5.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=budget1, confidence=5.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)  # unstated stance: hostile
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)  # unstated tech: none
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    half = eco0 / 2.0
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=half, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=60.0, economy=half, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 2, tier=OMTier.HOME, military=30.0, economy=eco1, tension=0.0, population=50.0, faction_id=1)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    for idx, fid in ((0, 0), (1, 0), (2, 1)):
        set_owner(lib, w, idx, fid, held_since=-1)  # held since the world began
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_edge(lib, w, 1, 3, OMEdge.BOTH)
    set_edge(lib, w, 2, 3, OMEdge.BOTH)
    inject_intent(lib, w, 0, OMAction.COLONIZE, 3, 1, commit0)
    inject_intent(lib, w, 1, OMAction.COLONIZE, 3, 2, commit1)
    return w


def _collision_on(lib, w, target_idx):
    cols = [c for c in read_collisions(lib, w) if c.target_idx == target_idx]
    assert len(cols) == 1, f"expected one collision on region {target_idx}, got {len(cols)}"
    return cols[0]


def test_R_039_01_factors_1_0_0_7(lib, world_factory):
    """Given two factions commit 40 and 20 to the same empty region, with total economies 200 and 100, When the collision resolves, Then factors are 1.0 and 0.7, strengths 40 and 14, and the first wins with probability 40/54 on one draw."""
    w = _two_colliders_on_empty(lib, world_factory)
    # winner draw 0.70 < 40/54 = 0.7407: faction 0 wins; refund draw 0.0
    force_draws(lib, w, [0.70, 0.0])
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.n_colliders == 2
    by_faction = {c.faction[i]: i for i in range(c.n_colliders)}
    i0, i1 = by_faction[0], by_faction[1]
    assert c.commit[i0] == pytest.approx(40.0, abs=1e-6)
    assert c.commit[i1] == pytest.approx(20.0, abs=1e-6)
    assert c.economy_factor[i0] == pytest.approx(1.0, abs=1e-6)
    assert c.economy_factor[i1] == pytest.approx(0.7, abs=1e-6)
    assert c.strength[i0] == pytest.approx(40.0, abs=1e-6)
    assert c.strength[i1] == pytest.approx(14.0, abs=1e-6)
    assert c.winner == 0

    # The winner is drawn once with probability 40/54: a draw just above it
    # goes to faction 1. Strict boundary: u < 40/54 picks the first.
    w_hi = _two_colliders_on_empty(lib, world_factory)
    force_draws(lib, w_hi, [0.75, 0.0])
    lib.om_world_step(w_hi)
    assert _collision_on(lib, w_hi, 3).winner == 1

    w_at = _two_colliders_on_empty(lib, world_factory)
    force_draws(lib, w_at, [40.0 / 54.0, 0.0])
    lib.om_world_step(w_at)
    assert _collision_on(lib, w_at, 3).winner == 1


def test_R_039_02_opposition_0_35_ceiling_0(lib, world_factory):
    """Given the first wins, When retention is computed, Then opposition = 0.35, ceiling = 0.4 · (1 − 0.35 · 0.6) = 0.316, refund = 40 · U(0, 0.316), and the loser spends all 20."""
    w = _two_colliders_on_empty(lib, world_factory)
    # winner draw 0.5 (faction 0 wins), refund draw 0.5 -> refund = 40 * 0.5 * 0.316 = 6.32
    force_draws(lib, w, [0.5, 0.5])
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.winner == 0
    assert c.retention_ceiling == pytest.approx(0.316, abs=1e-6)
    assert c.refund == pytest.approx(6.32, abs=1e-6)
    assert 0.0 <= c.refund <= 40.0 * 0.316 + 1e-9
    # budgets: the winner spends commit minus refund; the loser spends all 20
    assert lib.om_faction_budget(w, 0) == pytest.approx(200.0 - (40.0 - 6.32), abs=1e-6)
    assert lib.om_faction_budget(w, 1) == pytest.approx(200.0 - 20.0, abs=1e-6)

    # refund draw 0.0 -> refund 0; refund draw just under 1.0 -> refund just under the cap
    w0 = _two_colliders_on_empty(lib, world_factory)
    force_draws(lib, w0, [0.5, 0.0])
    lib.om_world_step(w0)
    assert _collision_on(lib, w0, 3).refund == pytest.approx(0.0, abs=1e-9)


def test_R_039_03_its_highest_military_region_gains(lib, world_factory):
    """Given the loser's budget was 50, When its tension hit applies, Then its highest-military region gains 5.0 · 20/50 = 2.0 tension."""
    w = world_factory(n_regions=5)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=50.0, confidence=5.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    # loser owns regions 1 (military 30) and 2 (military 60, the highest): the hit lands on 2
    set_region(lib, w, 1, tier=OMTier.HOME, military=30.0, economy=50.0, tension=10.0, population=50.0, faction_id=1)
    set_region(lib, w, 2, tier=OMTier.HOME, military=60.0, economy=50.0, tension=10.0, population=50.0, faction_id=1)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    set_region(lib, w, 4, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    for idx, fid in ((0, 0), (1, 1), (2, 1)):
        set_owner(lib, w, idx, fid, held_since=-1)
    set_edge(lib, w, 0, 3, OMEdge.BOTH)
    set_edge(lib, w, 1, 3, OMEdge.BOTH)
    set_edge(lib, w, 1, 2, OMEdge.BOTH)
    inject_intent(lib, w, 0, OMAction.COLONIZE, 3, 0, 40.0)
    inject_intent(lib, w, 1, OMAction.COLONIZE, 3, 1, 20.0)
    force_draws(lib, w, [0.1, 0.0])  # faction 0 wins; no refund
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.winner == 0
    i1 = [c.faction[i] for i in range(c.n_colliders)].index(1)
    assert c.loser_tension[i1] == pytest.approx(2.0, abs=1e-6)
    assert lib.om_region_field(w, 2, OMField.TENSION) == pytest.approx(12.0, abs=1e-6)
    assert lib.om_region_field(w, 1, OMField.TENSION) == pytest.approx(10.0, abs=1e-6)
    assert lib.om_faction_budget(w, 1) == pytest.approx(30.0, abs=1e-6)


def test_R_039_04_starter_military_10_0_margin(lib, world_factory):
    """Given the target is empty and margin = 40/54 = 0.741 ≥ 0.6, When colonized, Then starter military is 10.0; Given margin 0.55, Then starter military = 10 · U(0.5, 0.70)."""
    w = _two_colliders_on_empty(lib, world_factory)
    force_draws(lib, w, [0.5, 0.0])  # faction 0 wins, no refund; margin 0.741 draws no penalty
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.margin == pytest.approx(40.0 / 54.0, abs=1e-6)
    cols = read_colonizations(lib, w)
    assert len(cols) == 1
    assert cols[0].faction_id == 0 and cols[0].target_idx == 3
    assert cols[0].start_military == pytest.approx(10.0, abs=1e-6)
    assert lib.om_region_owner(w, 3) == 0
    assert lib.om_region_field(w, 3, OMField.MILITARY) == pytest.approx(10.0, abs=1e-6)
    assert lib.om_region_field(w, 3, OMField.ECONOMY) == pytest.approx(20.0, abs=1e-6)
    assert lib.om_region_field(w, 3, OMField.TENSION) == pytest.approx(20.0, abs=1e-6)
    assert lib.om_region_field(w, 3, OMField.POPULATION) == pytest.approx(25.0, abs=1e-6)

    # margin 0.55: equal economies so factors are 1.0, commits 55 and 45 give
    # strengths 55 / 45 and margin 55/100 = 0.55 < 0.6; penalty draw 0.5 ->
    # starter = 10 * (0.5 + 0.5 * 0.20) = 6.0
    w_n = _two_colliders_on_empty(lib, world_factory, commit0=55.0, commit1=45.0, eco0=100.0, eco1=100.0)
    force_draws(lib, w_n, [0.1, 0.0, 0.5])  # winner, refund, colony penalty
    lib.om_world_step(w_n)
    c_n = _collision_on(lib, w_n, 3)
    assert c_n.margin == pytest.approx(0.55, abs=1e-6)
    col = read_colonizations(lib, w_n)[0]
    assert col.start_military == pytest.approx(6.0, abs=1e-6)
    assert 10.0 * 0.5 <= col.start_military <= 10.0 * 0.70

    # margin exactly 0.6 is not narrow: commits 60 and 40 -> full 10.0, no penalty draw consumed
    w_at = _two_colliders_on_empty(lib, world_factory, commit0=60.0, commit1=40.0, eco0=100.0, eco1=100.0)
    force_draws(lib, w_at, [0.1, 0.0])
    lib.om_world_step(w_at)
    assert _collision_on(lib, w_at, 3).margin == pytest.approx(0.6, abs=1e-6)
    assert read_colonizations(lib, w_at)[0].start_military == pytest.approx(10.0, abs=1e-6)
    assert lib.om_rng_forced_remaining(w_at) == 0


def _two_attackers_on_owned(lib, world_factory, *, defender_military):
    """Faction 2 owns region 3 (military as given, held since the start, so
    entrenchment 2.0 and defense = military * 0.55 * 2.0). Factions 0 and 1
    inject surprise-free attacks with commits 40 and 20; economies 200 and 100."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    for fid in (0, 1, 2):
        set_faction(lib, w, fid, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
        set_tech_multipliers(lib, w, fid, 1.0, 1.0, 1.0)
    for a in (0, 1, 2):
        for b in (0, 1, 2):
            if a != b:
                set_stance(lib, w, a, b, OMStance.HOSTILE, both_ways=False)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=1)
    set_region(lib, w, 3, tier=OMTier.HOME, military=defender_military, economy=50.0, tension=10.0, population=50.0, faction_id=2)
    for idx, fid in ((0, 0), (1, 0), (2, 1), (3, 2)):
        set_owner(lib, w, idx, fid, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_edge(lib, w, 1, 3, OMEdge.BOTH)
    set_edge(lib, w, 2, 3, OMEdge.BOTH)
    # faction 2's own 3d decision must not add an intent: budget 0 means accumulate
    set_faction(lib, w, 2, OMArchetype.CONQUEROR, budget=0.0, confidence=5.0)
    inject_intent(lib, w, 0, OMAction.ATTACK, 3, 1, 40.0, OMMode.TELEGRAPH)
    inject_intent(lib, w, 1, OMAction.ATTACK, 3, 2, 20.0, OMMode.TELEGRAPH)
    return w


def test_R_039_05_each_collider_s_strength_applied(lib, world_factory):
    """Given the target is owned by a third faction with military 30, When the collision resolves, Then each collider's strength is applied against defense 33 with its own stochastic draw, damages sum, and a conquest goes to the winner if military falls below 5."""
    # Injected telegraphed attacks resolve at tick + 3 (R-036-03); the
    # collision groups them by target on the resolving tick.
    w = _two_attackers_on_owned(lib, world_factory, defender_military=30.0)
    lib.om_world_step(w)  # tick 1: both declared
    lib.om_world_step(w)  # tick 2
    lib.om_world_step(w)  # tick 3
    # tick 4 draws: winner 0.1 (faction 0), refund 0.0, stochastic 1.0 for each applied attack
    force_draws(lib, w, [0.1, 0.0, 1.0, 1.0])
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.n_colliders == 2 and c.winner == 0
    atts = sorted([a for a in read_attacks(lib, w) if a.target_idx == 3], key=lambda a: a.attacker)
    assert len(atts) == 2
    assert all(a.collision == 1 for a in atts)
    # strengths 40 and 14 (economy factors 1.0 and 0.7) against defense 30 * 0.55 * 2.0 = 33
    assert atts[0].effective_attack == pytest.approx(40.0, abs=1e-6)
    assert atts[1].effective_attack == pytest.approx(14.0, abs=1e-6)
    assert atts[0].effective_defense == pytest.approx(33.0, abs=1e-6)
    assert atts[1].effective_defense == pytest.approx(33.0, abs=1e-6)
    # net 7 -> contested: -3.5 military; net -19 -> repelled: -0.10 * 14 = -1.4
    assert atts[0].d_military == pytest.approx(-3.5, abs=1e-6)
    assert atts[1].d_military == pytest.approx(-1.4, abs=1e-6)
    assert atts[0].conquest == 0 and atts[1].conquest == 0
    assert lib.om_region_field(w, 3, OMField.MILITARY) == pytest.approx(30.0 - 3.5 - 1.4, abs=1e-6)
    assert lib.om_region_owner(w, 3) == 2

    # A defender at military 5 (defense 5.5): net 34.5 breakthrough from the
    # winner, damages sum below 5.0, conquest goes to the winner with its garrison
    w_c = _two_attackers_on_owned(lib, world_factory, defender_military=5.0)
    for _ in range(3):
        lib.om_world_step(w_c)
    force_draws(lib, w_c, [0.1, 0.0, 1.0, 1.0, 0.99, 0.5])  # winner, refund, 2 attacks, unrest roll (no fire), delay
    lib.om_world_step(w_c)
    assert lib.om_region_owner(w_c, 3) == 0
    conq = [a for a in read_attacks(lib, w_c) if a.target_idx == 3 and a.conquest == 1]
    assert len(conq) == 1 and conq[0].attacker == 0
    assert conq[0].garrison == pytest.approx(40.0 * 0.65, abs=1e-6)


def test_R_039_06_same_rules_apply_with_second(lib, world_factory):
    """Given three or more colliders, When resolved, Then the same rules apply with second-best = the strongest loser."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    for fid in (0, 1, 2):
        set_faction(lib, w, fid, OMArchetype.CONQUEROR, budget=100.0, confidence=5.0)
        set_tech_multipliers(lib, w, fid, 1.0, 1.0, 1.0)
    for a in (0, 1, 2):
        for b in (0, 1, 2):
            if a != b:
                set_stance(lib, w, a, b, OMStance.HOSTILE, both_ways=False)
    # equal economies so every factor is 1.0 and strengths equal commits 40, 20, 10
    for idx, fid in ((0, 0), (1, 1), (2, 2)):
        set_region(lib, w, idx, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=fid)
        set_owner(lib, w, idx, fid, held_since=-1)
        set_edge(lib, w, idx, 3, OMEdge.BOTH)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    inject_intent(lib, w, 0, OMAction.COLONIZE, 3, 0, 40.0)
    inject_intent(lib, w, 1, OMAction.COLONIZE, 3, 1, 20.0)
    inject_intent(lib, w, 2, OMAction.COLONIZE, 3, 2, 10.0)
    force_draws(lib, w, [0.1, 0.0])  # winner draw picks faction 0 (40/70), refund 0
    lib.om_world_step(w)
    c = _collision_on(lib, w, 3)
    assert c.n_colliders == 3 and c.winner == 0
    by = {c.faction[i]: i for i in range(c.n_colliders)}
    assert c.strength[by[0]] == pytest.approx(40.0, abs=1e-6)
    assert c.strength[by[1]] == pytest.approx(20.0, abs=1e-6)
    assert c.strength[by[2]] == pytest.approx(10.0, abs=1e-6)
    # second-best is the strongest loser (20): margin 40/60; opposition (20+10)/40 = 0.75
    assert c.margin == pytest.approx(40.0 / 60.0, abs=1e-6)
    assert c.retention_ceiling == pytest.approx(0.4 * (1.0 - 0.75 * 0.6), abs=1e-6)
    # every loser spends its full commit and takes 5.0 * commit / budget tension
    assert lib.om_faction_budget(w, 1) == pytest.approx(80.0, abs=1e-6)
    assert lib.om_faction_budget(w, 2) == pytest.approx(90.0, abs=1e-6)
    assert c.loser_tension[by[1]] == pytest.approx(5.0 * 20.0 / 100.0, abs=1e-6)
    assert c.loser_tension[by[2]] == pytest.approx(5.0 * 10.0 / 100.0, abs=1e-6)
    assert c.loser_tension[by[0]] == pytest.approx(0.0, abs=1e-9)
    # winner draw at 40/70 exactly goes to the next collider in strength order
    w_b = world_factory(n_regions=4)
    isolate_agents(lib, w_b)
    for fid in (0, 1, 2):
        set_faction(lib, w_b, fid, OMArchetype.CONQUEROR, budget=100.0, confidence=5.0)
        set_tech_multipliers(lib, w_b, fid, 1.0, 1.0, 1.0)
    for a in (0, 1, 2):
        for b in (0, 1, 2):
            if a != b:
                set_stance(lib, w_b, a, b, OMStance.HOSTILE, both_ways=False)
    for idx, fid in ((0, 0), (1, 1), (2, 2)):
        set_region(lib, w_b, idx, tier=OMTier.HOME, military=50.0, economy=100.0, tension=0.0, population=50.0, faction_id=fid)
        set_owner(lib, w_b, idx, fid, held_since=-1)
        set_edge(lib, w_b, idx, 3, OMEdge.BOTH)
    set_region(lib, w_b, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    inject_intent(lib, w_b, 0, OMAction.COLONIZE, 3, 0, 40.0)
    inject_intent(lib, w_b, 1, OMAction.COLONIZE, 3, 1, 20.0)
    inject_intent(lib, w_b, 2, OMAction.COLONIZE, 3, 2, 10.0)
    force_draws(lib, w_b, [40.0 / 70.0 + 1e-9, 0.0])
    lib.om_world_step(w_b)
    assert _collision_on(lib, w_b, 3).winner == 1
