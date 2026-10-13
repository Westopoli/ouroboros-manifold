"""ALG-18 Reactive reinforce (docs/bible/algorithms.md; E-05 R-036-05, S-036).

Rule (3e): among telegraphs targeting this faction take the one with the
largest commit. reinforce_prob = min(1, w_defend / 1.5); ONE RNG draw, act if
draw <= reinforce_prob. commit = min(budget * 0.30, telegraph_commit * 0.5);
no intent if commit < 1.0.

Telegraphs are placed with om_intent_inject (attack, telegraph mode) and the
defender's own 3d decision is replaced by an injected ACCUMULATE, so the only
forced draws consumed are the 3e ones. Expected numbers are computed in this
file from the rule. Positive control: a draw just above the probability
removes the reinforce, and a deliberately wrong expectation fails.
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMMode,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_reinforces,
    set_faction,
    set_owner,
    set_region,
    set_tech_multipliers,
)

# ARCHETYPE_DECISION_WEIGHTS defend weight (ALG-14), the w_defend of ALG-18.
W_DEFEND = {
    OMArchetype.CONQUEROR: 0.4,
    OMArchetype.WARLORD: 0.3,
    OMArchetype.FORTIFIER: 1.5,
    OMArchetype.OPPORTUNIST: 0.6,
    OMArchetype.SCHISM: 0.5,
    OMArchetype.PLAYER: 1.5,
    OMArchetype.DEFAULT: 0.8,
    OMArchetype.BREAKAWAY: 0.8,  # not listed: falls to the default 0.8/0.6/0.8
}
FRACTION = 0.30
HALF = 0.5


def _world(lib, world_factory, defender_arch, defender_budget, telegraph_commits):
    """Attackers 0..k-1 (one region each) telegraph at defender faction k, who owns one
    target region per attacker. Economies sit at the floor 8.0 so no budget accrues (ALG-17)."""
    k = len(telegraph_commits)
    w = world_factory(n_regions=2 * k)
    isolate_agents(lib, w)
    for a in range(k):
        set_faction(lib, w, a, OMArchetype.CONQUEROR, budget=1000.0, confidence=2.0)
        set_tech_multipliers(lib, w, a, 1.0, 1.0, 1.0)
        set_region(lib, w, a, tier=OMTier.HOME, military=50.0, economy=8.0,
                   tension=0.0, population=50.0, faction_id=a)
        set_owner(lib, w, a, a, held_since=-1)
    set_faction(lib, w, k, defender_arch, budget=defender_budget)
    set_tech_multipliers(lib, w, k, 1.0, 1.0, 1.0)
    for a in range(k):
        t = k + a
        set_region(lib, w, t, tier=OMTier.HOME, military=40.0, economy=8.0,
                   tension=0.0, population=50.0, faction_id=k)
        set_owner(lib, w, t, k, held_since=-1)
    # The defender's own 3d decision is replaced so it draws nothing before 3e.
    inject_intent(lib, w, k, OMAction.ACCUMULATE, k, k, 0.0)
    for a, c in enumerate(telegraph_commits):
        inject_intent(lib, w, a, OMAction.ATTACK, k + a, a, c, OMMode.TELEGRAPH)
    return w, k


def _reinforces_for(lib, w, defender):
    return [r for r in read_reinforces(lib, w) if r.faction_id == defender]


@pytest.mark.parametrize("arch", sorted(W_DEFEND))
def test_ALG_18_probability_is_min_1_wdefend_over_1_5_with_draw_le(lib, world_factory, arch):
    """ALG-18: act iff draw <= min(1, w_defend/1.5), boundary inclusive, one draw."""
    prob = min(1.0, W_DEFEND[arch] / 1.5)
    # at the boundary the defender acts
    w, k = _world(lib, world_factory, arch, 100.0, [40.0])
    force_draws(lib, w, [prob, 0.5])
    lib.om_world_step(w)
    assert len(_reinforces_for(lib, w, k)) == 1
    # just above the probability it does not (only meaningful when prob < 1)
    if prob < 1.0:
        w2, k2 = _world(lib, world_factory, arch, 100.0, [40.0])
        force_draws(lib, w2, [prob + 1e-6, 0.5])
        lib.om_world_step(w2)
        assert _reinforces_for(lib, w2, k2) == []


@pytest.mark.parametrize("budget,tele,expect", [
    (100.0, 40.0, min(100.0 * FRACTION, 40.0 * HALF)),   # 20.0, telegraph-bound
    (30.0, 100.0, min(30.0 * FRACTION, 100.0 * HALF)),   # 9.0, budget-bound
    (4.0, 100.0, min(4.0 * FRACTION, 100.0 * HALF)),     # 1.2, just above the floor
    (3.0, 100.0, None),                                  # 0.9 < 1.0 -> no intent
    (100.0, 1.9, None),                                  # 0.95 < 1.0 -> no intent
])
def test_ALG_18_commit_is_min_budget_030_telegraph_050_and_none_below_1(lib, world_factory, budget, tele, expect):
    w, k = _world(lib, world_factory, OMArchetype.FORTIFIER, budget, [tele])
    force_draws(lib, w, [0.0, 0.5])
    lib.om_world_step(w)
    got = _reinforces_for(lib, w, k)
    if expect is None:
        assert got == []
    else:
        assert len(got) == 1
        assert got[0].commit == pytest.approx(expect, abs=1e-9)


def test_ALG_18_only_the_largest_telegraph_is_answered_with_one_draw(lib, world_factory):
    """ALG-18: 'among telegraphs targeting this faction, take the one with the largest commit' -- one reinforce for the faction, on the largest telegraph's target, one probability draw."""
    commits = [30.0, 60.0]
    w, k = _world(lib, world_factory, OMArchetype.FORTIFIER, 100.0, commits)
    force_draws(lib, w, [0.0, 0.5, 0.0, 0.5])
    lib.om_world_step(w)
    got = _reinforces_for(lib, w, k)
    largest_target = k + commits.index(max(commits))
    assert len(got) == 1, f"expected one reinforce for the faction, got {[(r.target_idx, r.commit) for r in got]}"
    assert got[0].target_idx == largest_target
    assert got[0].commit == pytest.approx(min(100.0 * FRACTION, max(commits) * HALF), abs=1e-9)


def test_control_ALG_18_detector_fires(lib, world_factory):
    """Positive control: a wrong expectation fails, and a perturbed draw removes the reinforce the main tests count."""
    prob = min(1.0, W_DEFEND[OMArchetype.CONQUEROR] / 1.5)
    w, k = _world(lib, world_factory, OMArchetype.CONQUEROR, 100.0, [40.0])
    force_draws(lib, w, [prob + 1e-6, 0.5])
    lib.om_world_step(w)
    assert _reinforces_for(lib, w, k) == []
    with pytest.raises(AssertionError):
        assert len(_reinforces_for(lib, w, k)) == 1
    w2, k2 = _world(lib, world_factory, OMArchetype.CONQUEROR, 100.0, [40.0])
    force_draws(lib, w2, [prob, 0.5])
    lib.om_world_step(w2)
    got = _reinforces_for(lib, w2, k2)
    assert len(got) == 1
    with pytest.raises(AssertionError):
        assert got[0].commit == pytest.approx(30.0, abs=1e-9)  # budget*0.30 with the wrong binding term
