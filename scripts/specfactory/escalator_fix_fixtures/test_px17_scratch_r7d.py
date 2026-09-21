"""PX-17 scratch probe (not committed to the repo): does 3d's mode-selection
draw consume the forced-RNG queue? R7d (DECISIONS.md fifth round): it must,
per the header's world RNG contract ("every consumer of the stream... takes
from the same queue"), and pre-fix it read w->rng_state directly instead.

Fixture is R-036-01's own proven-viable setup (tests/csim/test_E05_S036_declared_or_sprung.py
::test_R_036_01_telegraph_preference_0_7_0), which already gives faction 0 a
viable attack candidate against military 70 (telegraph_preference = 0.90).
Only the forced draw changes: 0.95 instead of 0.85, so a 3d that honors the
forced queue must select SURPRISE, not TELEGRAPH. One forced draw is queued
and only one om_world_step runs, so nothing else in the tick can plausibly
consume it (SURPRISE mode declares no telegraph, so no same-tick reactive
reinforce exists to steal it either -- R7d's exact failure shape).
"""
import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMMode,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_decisions,
    read_telegraphs,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)


def test_R7D_forced_3d_draw_is_consumed_by_3d(lib, world_factory):
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.DEFAULT)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=70.0, economy=60.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)

    force_draws(lib, w, [0.95])  # >= pref (0.90) => SURPRISE if 3d honors the forced queue
    lib.om_world_step(w)

    remaining = lib.om_rng_forced_remaining(w)
    decisions = read_decisions(lib, w)
    assert len(decisions) >= 1
    d = decisions[0]
    assert d.faction_id == 0
    assert d.action == OMAction.ATTACK, "fixture is not exercising a real attack decision"
    assert d.telegraph_preference == pytest.approx(0.90), "fixture drifted from R-036-01's own viable setup"

    assert remaining == 0, (
        f"the forced draw (0.95) was never consumed this tick (remaining={remaining}) -- "
        "3d did not check the forced-RNG queue before falling through to the real stream, "
        "and SURPRISE mode declares no telegraph, so no same-tick reactive reinforce exists "
        "to have consumed it instead (R7d's exact failure shape)"
    )
    assert d.mode == OMMode.SURPRISE, (
        f"forced draw 0.95 >= telegraph_preference 0.90 must select SURPRISE (mode={d.mode}); "
        "a TELEGRAPH result here means 3d drew from the real, un-forced stream instead of the "
        "forced queue"
    )
    assert len(read_telegraphs(lib, w)) == 0, "SURPRISE mode must not enqueue a telegraph"
