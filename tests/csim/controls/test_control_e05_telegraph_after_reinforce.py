"""Positive control for OM_BUG_TELEGRAPH_AFTER_REINFORCE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Telegraph /
reinforce inversion"): "Tick log shows telegraph resolution entry preceding
defender's reactive reinforce entry for the same attack in the same tick; or
defender reinforced military is not reflected in effective defense at battle
resolution." Enum: OMBugE05.TELEGRAPH_AFTER_REINFORCE
(OM_BUG_TELEGRAPH_AFTER_REINFORCE = 101 in csrc/ouroboros_sim.h), "3c runs
after 3e".

Original version of this control declared a single telegraph on tick 1 and
checked whether the declaration tick's own reactive reinforce fired. Dead as
written, and unfixable that way (docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md,
finding R9): `om_step_reinforce` (3e) only reacts to telegraphs whose
`declared_tick == w->tick`, i.e. ones `om_step_decisions` (3d) just declared
this same tick; `om_step_telegraphs` (3c) only touches telegraphs that are at
least 3 ticks old. Moving 3c's position relative to 3d/3e changes nothing 3c
would have touched on a telegraph's own declaration tick, so a freshly
declared telegraph's reactive reinforce fires identically whichever side of
3d/3e the 3c call lands on. Confirmed directly: two independent scenarios
against the debug build, byte-identical either way.

The reorder is observable at a different point: `om_step_reinforce`'s
reactive-reinforce headroom (`(tier_cap - target.military) / tier_cap`) reads
the target's *current* military, and if the correct order (3c before 3e) has
already applied a same-tick telegraph maturation's damage to that same
target, that reduced military changes the headroom -- and therefore the
reinforce's own `d_military` -- for a second, unrelated telegraph declared
against the same target this same tick. This control uses two attackers
sharing one target `T` (owned by a third, fortifier faction): faction 0's
telegraph, declared on tick 1 (via `inject_intent`, so its own step-3d
recompute never runs again -- high confidence keeps it from ever declaring a
second one), matures on tick 4 in step 3c, damaging T. Faction 2's telegraph
is injected immediately before the tick-4 step so its `declared_tick` is
exactly 4, giving T's defender a fresh declaration to reactively reinforce
against in step 3e of that same tick. In the correct order, 3c's damage to T
already landed by the time 3e computes headroom for faction 2's declaration;
under the injected reorder, 3e runs first, computing headroom against T's
undamaged military, and the forced-draw queue (FIFO, drained by whichever
step actually calls `om_rng_draw` first) is consumed in a different order
too. Both effects land on the same observable field. Verified directly:
clean build's tick-4 reinforce record has `d_military` = 3.1429309981935623;
with OM_BUG_TELEGRAPH_AFTER_REINFORCE injected, 2.492991348464528 -- same
seed, same forced draws, same fixture, different order, different number.
"""
from conftest import (
    OMAction,
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMMode,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_reinforces,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)

import pytest


def test_control_telegraph_after_reinforce_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=3)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.TELEGRAPH_AFTER_REINFORCE)

    # Confidence sky-high on both attackers: neither ever declares anything
    # through its own step-3d recompute -- every telegraph in this control
    # comes from an explicit inject_intent, so the two attackers' own tick
    # order never adds an uncontrolled extra draw or a redundant decision.
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=999999.0)  # attacker A
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=50.0, confidence=999999.0)   # defender, owns T
    set_faction(dbg, w, 2, OMArchetype.CONQUEROR, budget=100.0, confidence=999999.0)  # attacker B
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_stance(dbg, w, 2, 1, OMStance.HOSTILE)
    for f in range(3):
        set_tech_multipliers(dbg, w, f, 1.0, 1.0, 1.0)

    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Region 1: T, the shared target.
    set_region(dbg, w, 1, tier=OMTier.HOME, military=40.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_region(dbg, w, 2, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0, faction_id=2)
    set_owner(dbg, w, 2, 2, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)
    set_edge(dbg, w, 2, 1, OMEdge.BOTH)

    # A's telegraph: declared_tick = current tick (0) + 1 = 1, matures tick 4.
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0,
                  commit=40.0, mode=OMMode.TELEGRAPH)

    for _ in range(3):
        dbg.om_world_step(w)  # ticks 1, 2, 3

    # B's telegraph, injected right before the tick-4 step so its
    # declared_tick is exactly 4 -- a fresh declaration this same tick, for
    # the defender's step-3e reactive reinforce to react to.
    inject_intent(dbg, w, 2, OMAction.ATTACK, target_idx=1, source_idx=2,
                  commit=40.0, mode=OMMode.TELEGRAPH)

    # Tick 4 draws: A's matured-telegraph stochastic (3c), then the
    # defender's reactive-reinforce probability and variance draws (3e) --
    # in that order on a correct build; the injected reorder drains this
    # same FIFO queue in the opposite order instead.
    force_draws(dbg, w, [1.0, 0.0, 0.5])
    dbg.om_world_step(w)  # tick 4

    reinforces = read_reinforces(dbg, w)
    assert len(reinforces) == 1, "the defender's reactive reinforce against B's tick-4 telegraph never fired -- this control's own setup is broken, not the detector"

    assert reinforces[0].d_military != pytest.approx(3.1429309981935623, abs=1e-6), (
        "OM_BUG_TELEGRAPH_AFTER_REINFORCE injected but the tick-4 reinforce's "
        "d_military still reads 3.1429309981935623, the same as a clean "
        "build -- 3e's headroom read T's military before 3c's same-tick "
        "damage was (or was not) already applied, and the reorder made no "
        "observable difference -- the telegraph/reinforce-order detector did "
        "not trip"
    )
