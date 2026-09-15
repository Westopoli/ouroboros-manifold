"""Positive control for OM_BUG_AGENT_READS_LIVE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Live snapshot
read"): "In a 2-faction test where F1 acts first and mutates target region
T, F2's candidate score for T differs when faction iteration order is
inverted ... from the same initial tick state." Enum: OMBugE05.AGENT_READS_LIVE
(OM_BUG_AGENT_READS_LIVE = 100 in csrc/ouroboros_sim.h), "decisions read
post-mutation fields, not the 3a snapshot".

No filled S-032..S-041 story test in FILLED_DIR exercises this exact
watch-for -- S-034's candidate-scoring tests (test_E05_S034_who_looks_worth_taking.py)
all read one faction's candidates in an otherwise static, single-decision
world, never a second faction's mutation landing mid-tick. Built fresh from
R-034-01's own worked weakness value (military 30 -> weakness 0.70, i.e.
weakness = 1 - military/100, docs/bible/epics/E-05-faction-agents-and-conflict.md)
and the epic's Inputs table ("Tick step 3a: frozen snapshot of all regions
before any mutation this tick"), using only conftest helpers.

Faction 0 (lower id, decided/resolved first under ascending faction-id
order) skips its own 3d decision via an injected surprise attack on region 1
(owned by faction 1), which collapses region 1's military in step 3f.
Faction 2 (a separate, higher-id faction adjacent to region 1) runs its own
ordinary 3d decision this same tick and is never injected, so its candidate
list for region 1 is whatever the sim computes. A correct build computes
every faction's step-3d candidates from the step-3a snapshot, so faction 2's
weakness for region 1 must read 0.70 (from the pre-attack military of 30.0)
no matter what faction 0 does to region 1 later in the same tick's step 3f.
Region count kept to 3 (attacker home, shared target, evaluator home)
because the signature only needs one mutator and one reader sharing a
target in a single tick.
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMMode,
    OMStance,
    OMTier,
    inject_intent,
    isolate_agents,
    read_candidates,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
)


def test_control_agent_reads_live_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=3)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.AGENT_READS_LIVE)

    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_faction(dbg, w, 2, OMArchetype.CONQUEROR, budget=0.0, confidence=8.0)
    # Stances hostile both ways (neutral unstated stance)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_stance(dbg, w, 2, 1, OMStance.HOSTILE)

    # Region 0: faction 0's home, the attack source.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Region 1: faction 1's region, the shared target T. Military 30.0 is
    # R-034-01's own worked value: weakness = 1 - 30/100 = 0.70.
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, economy=40.0,
               tension=0.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    # Region 2: faction 2's home, adjacent to region 1 so it is a candidate.
    set_region(dbg, w, 2, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=2)
    set_owner(dbg, w, 2, 2, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)
    set_edge(dbg, w, 1, 2, OMEdge.BOTH)

    # Faction 0 skips its own 3d decision and surprise-attacks region 1
    # directly, collapsing its military in step 3f of this same tick.
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0,
                  commit=90.0, mode=OMMode.SURPRISE)

    dbg.om_world_step(w)

    cands = [c for c in read_candidates(dbg, w, 2) if c.region_idx == 1]
    assert len(cands) == 1, "faction 2 has no candidate for region 1 to check"
    assert cands[0].weakness != pytest.approx(0.70, abs=1e-6), (
        "OM_BUG_AGENT_READS_LIVE injected but faction 2's candidate weakness "
        "for region 1 still reads 0.70, the step-3a snapshot value -- the "
        "live-snapshot-read detector did not trip"
    )
