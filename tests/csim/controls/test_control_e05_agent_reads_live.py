"""Positive control for OM_BUG_AGENT_READS_LIVE.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Live snapshot
read"): "In a 2-faction test where F1 acts first and mutates target region
T, F2's candidate score for T differs when faction iteration order is
inverted ... from the same initial tick state." Enum: OMBugE05.AGENT_READS_LIVE
(OM_BUG_AGENT_READS_LIVE = 100 in csrc/ouroboros_sim.h), "decisions read
post-mutation fields, not the 3a snapshot".

Original version of this control tried to prove the watch-for by having
faction 0 surprise-attack region 1 in step 3f, then checking whether
faction 2's step-3d weakness read for region 1 (computed earlier, in the
same step) picked up the post-attack military. Dead as written, and
unfixable that way (docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md,
finding R7h): step 3d always completes, for every faction, before step 3f
mutates anything, in either a correct or a buggy build, so no candidate's
weakness can ever observe this tick's own later 3f mutation -- the read
happens too early regardless of the bug. Also, `csrc/agent.c`'s
`om_faction_candidates` reads `w->regions[j].military` live unconditionally
for every candidate's weakness -- there is no region-level 3a snapshot to
switch away from; the `w->inject == 100` branch that exists (agent.c:185)
gates only `potential_commit`, from the deciding faction's own budget.

That branch is real and live, just not through "weakness". Step 3b
(`om_faction_step_budget`, ALG-17) runs immediately after the 3a snapshot
and grows every faction's own live budget from its regions' economy, so by
the time step 3d runs, `w->faction_budget[f]` has already diverged from
`w->faction_budget_snapshot[f]` for any faction whose economy is above 8.0
-- no second faction or mid-tick mutation needed. This control isolates
exactly that branch: a single conqueror faction, with a hostile target
military. Its step-3a budget snapshot (100.0) times 0.70 puts its
`net`/`viable` calculation just under its (very high) confidence threshold,
so a clean build's own recompute (final `read_candidates` call re-runs
`om_faction_candidates` fresh against the world's current fields) never
finds an attack worth declaring and the tick's only budget change is 3b's
economy growth. With OM_BUG_AGENT_READS_LIVE injected, potential_commit
uses the tick's already-grown live budget instead, which is just enough to
cross the confidence threshold and get an attack declared and paid for in
step 3d -- so the post-tick budget lands far below the clean, growth-only
value. Verified directly against both the debug build with the bug
injected and with it neutralised (via `om_debug_inject`'s own no-op path):
clean final budget 101.05 (100.0 + (50.0 - 8.0) * 0.025 growth, nothing
declared); injected final budget ~31.05 (the same growth, then a declared
attack spends the rest).
"""
import pytest

from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    isolate_agents,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_control_agent_reads_live_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.AGENT_READS_LIVE)

    # Confidence 200.0 is deliberately high: viable only crosses if
    # potential_commit uses the tick's live (post-3b-growth) budget instead
    # of the frozen 3a snapshot.
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=200.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(dbg, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(dbg, w, 1, 1.0, 1.0, 1.0)

    # Region 0: faction 0's home. Economy 50.0 (> 8.0) is what makes ALG-17
    # grow the live budget above the frozen 3a snapshot this same tick.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    # Region 1: faction 1's region, the only attack candidate.
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, economy=40.0,
               tension=0.0, population=50.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)

    dbg.om_world_step(w)

    assert dbg.om_faction_budget(w, 0) != pytest.approx(101.05, abs=1e-6), (
        "OM_BUG_AGENT_READS_LIVE injected but faction 0's budget after the "
        "tick still reads 101.05 -- ALG-17's per-tick growth only, nothing "
        "declared -- the same as a clean build; potential_commit did not use "
        "the tick's live post-growth budget, so the live-snapshot-read "
        "detector did not trip"
    )
