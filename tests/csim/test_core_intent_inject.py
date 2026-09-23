"""Pinned regression for R8f (docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md).

Rule proved: R-046-04 / the om_intent_inject header contract
(csrc/ouroboros_sim.h, "intent injection (fixture)"): "A faction with an
injected intent this tick skips its own 3d decision." R8f found
om_step_decisions did not implement that skip -- an injected intent and the
faction's own freshly recomputed decision both resolved, so a single injected
faction produced two attacks in one tick. Fixed on main (om_step_decisions
now preserves any decision already stamped with the applying tick and skips
recomputing that faction). This file pins the contract so a regression fails
loudly: the injected faction never doubles its own decision, while an
unrelated, uninjected faction's own independent decision is untouched by
someone else's injection (the contract only replaces the injected faction's
OWN 3d decision, nothing else's).
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMFeature,
    OMMode,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_attacks,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)


def test_R_046_04_injected_intent_replaces_own_decision_not_doubles_it(lib, world_factory):
    """Given a faction whose own 3d decision would also be a viable attack,
    When an intent is injected for that faction this tick, Then exactly one
    attack resolves -- the injected one -- not the injected attack plus an
    autonomous re-decision (R8f)."""
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)

    # Faction 0: budget 100 makes its own natural attack decision viable
    # (potential_commit = 100 * 0.70 = 70.0, comfortably beats a weak target).
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=100.0, tech=0.0)
    # Faction 1: budget 0 so IT never has a viable attack of its own -- this
    # test isolates the injected faction's own-decision suppression, not
    # bilateral hostile decision-making (a separate, out-of-scope question).
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=0.0, tech=0.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)

    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=20.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=1)
    set_owner(lib, w, 0, 0, held_since=0)
    set_owner(lib, w, 1, 1, held_since=0)
    set_edge(lib, w, 0, 1, OMEdge.BORDER)

    # Inject a commit (15.0) that the faction's own recompute would never
    # pick on its own (its natural commit would be 70.0 = budget * 0.70), so
    # a surviving natural decision is unambiguous in the result.
    inject_intent(lib, w, 0, OMAction.ATTACK, 1, 0, 15.0, OMMode.SURPRISE)
    force_draws(lib, w, [1.0] * 6)

    lib.om_world_step(w)

    attacks = read_attacks(lib, w)
    assert len(attacks) == 1, (
        f"expected exactly one attack (the injected one), got "
        f"{[(a.attacker, a.target_idx, a.commit) for a in attacks]}"
    )
    assert attacks[0].attacker == 0
    assert attacks[0].target_idx == 1
    assert attacks[0].commit == pytest.approx(15.0)


def test_control_two_attacks_when_injection_is_for_a_different_faction(lib, world_factory):
    """Positive control: injecting an intent for one faction does not suppress
    a DIFFERENT, uninjected faction's own independent decision. Two unrelated
    hostile pairs; faction 0 is injected, faction 2 decides naturally --
    both attacks resolve (R8f only replaces the injected faction's own 3d
    decision, nothing else's)."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)

    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=100.0, tech=0.0)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=0.0, tech=0.0)
    set_faction(lib, w, 2, OMArchetype.CONQUEROR, budget=100.0, tech=0.0)
    set_faction(lib, w, 3, OMArchetype.FORTIFIER, budget=0.0, tech=0.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_stance(lib, w, 2, 3, OMStance.HOSTILE)

    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=20.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=1)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=2)
    set_region(lib, w, 3, tier=OMTier.HOME, military=20.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=3)
    set_owner(lib, w, 0, 0, held_since=0)
    set_owner(lib, w, 1, 1, held_since=0)
    set_owner(lib, w, 2, 2, held_since=0)
    set_owner(lib, w, 3, 3, held_since=0)
    set_edge(lib, w, 0, 1, OMEdge.BORDER)
    set_edge(lib, w, 2, 3, OMEdge.BORDER)

    inject_intent(lib, w, 0, OMAction.ATTACK, 1, 0, 15.0, OMMode.SURPRISE)
    force_draws(lib, w, [1.0] * 10)

    lib.om_world_step(w)

    attacks = read_attacks(lib, w)
    assert len(attacks) == 2, (
        f"expected the injected attack plus faction 2's own independent "
        f"attack, got {[(a.attacker, a.target_idx, a.commit) for a in attacks]}"
    )
    by_attacker = {a.attacker: a for a in attacks}
    assert set(by_attacker) == {0, 2}
    assert by_attacker[0].commit == pytest.approx(15.0)
    assert by_attacker[2].commit == pytest.approx(70.0)  # faction 2's own 0.70 * budget
