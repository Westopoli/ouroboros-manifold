"""Positive control for OM_BUG_INJECT_IGNORED.

Watch-for (DECISIONS.md R8): "om_intent_inject is a no-op under FACTIONS" --
om_step_decisions wiped every injected intent on its own decisions_n = 0
reset and recomputed the faction's decision fresh, silently discarding
whatever the caller injected. The header's om_intent_inject contract says
"a faction with an injected intent this tick skips its own 3d decision";
OM_BUG_INJECT_IGNORED (OM_BUG_INJECT_IGNORED = 111 in csrc/ouroboros_sim.h)
reverts to that old behavior for this control.

Faction 0 (conqueror, budget 100.0) naturally scores a full-commit attack
(potential_commit = 100.0 * 0.70 = 70.0) against faction 1's weak, valuable
region. Injecting an ATTACK intent of commit 60.0 against the same target
should override that -- the resolved attack's commit is 60.0 on the clean
build, and reverts to the natural 70.0 with the bug injected.
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMMode,
    OMAction,
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
    set_tech_multipliers,
)


def _build(dbg, dbg_world_factory, inject_bug):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    if inject_bug:
        dbg.om_debug_inject(w, OMBugE05.INJECT_IGNORED)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=10.0, economy=50.0,
               tension=10.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    # Inject a SURPRISE attack, commit 60.0, against faction 1's region --
    # faction 0's own 3d would otherwise pick the full potential_commit,
    # 100.0 * 0.70 = 70.0, against the same, only viable target. Force the
    # mode draw to 0.9 (>= pref 0.50: conqueror 0.70 - 0.20 for a target
    # under military 30) so the bug's natural recompute also lands on
    # SURPRISE mode -- otherwise it may draw TELEGRAPH instead, which
    # correctly waits 3 ticks and never resolves this tick either way,
    # collapsing the control's clean-vs-buggy distinction.
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0,
                  commit=60.0, mode=OMMode.SURPRISE)
    force_draws(dbg, w, [0.9])

    dbg.om_world_step(w)

    attacks = read_attacks(dbg, w)
    assert len(attacks) == 1, "the injected attack never resolved on tick 1"
    return attacks[0]


def test_control_inject_ignored_trips_the_detector(dbg, dbg_world_factory):
    clean = _build(dbg, dbg_world_factory, inject_bug=False)
    assert clean.commit == pytest.approx(60.0, abs=1e-6), (
        "clean build: the injected commit (60.0) should reach resolution "
        f"unchanged, got {clean.commit}"
    )

    buggy = _build(dbg, dbg_world_factory, inject_bug=True)
    assert buggy.commit != pytest.approx(60.0, abs=1e-6), (
        "OM_BUG_INJECT_IGNORED injected but the resolved commit is still "
        "60.0 (the injected value) -- the inject-ignored detector did not trip"
    )
    assert buggy.commit == pytest.approx(70.0, abs=1e-6), (
        f"expected the natural recompute (100.0 * 0.70 = 70.0), got {buggy.commit}"
    )
