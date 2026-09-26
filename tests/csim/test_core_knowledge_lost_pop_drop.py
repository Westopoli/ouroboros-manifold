"""Population-drop leg of ALG-27b Knowledge Lost (R-045-07, R-045-09).

Tests the eligibility leg: avg_p(now) <= avg_p(tick-50) - KNOWLEDGE_LOST_POP_DROP=10.0.
Economy leg (avg_e < 20) tested by the neighbouring test_E06 suite; no duplication here.
"""
import pytest

from conftest import (
    OMArchetype,
    OMTier,
    force_draws,
    read_event_queue,
    set_faction,
    set_owner,
    set_region,
    template_name,
)


def _pop_drop_world(lib, world_factory, *, eco=25.0, pop=50.0, tech=30.0):
    """1-region world; economy >= 20 disables the economy leg so only the
    pop-drop leg can fire. Tick set to 100 so the first call is cooldown-clear
    (100 - last_kl=0 = 100 >= COOLDOWN=100)."""
    w = world_factory(n_regions=1)
    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=tech)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=eco,
               tension=10.0, population=pop)
    set_owner(lib, w, 0, 0)
    lib.om_world_set_tick(w, 100)
    return w


def test_pop_drop_10_fires_knowledge_lost(lib, world_factory):
    """R-045-07 / ALG-27b: faction with eco >= 20 whose avg_p falls by >= 10.0
    over the past 50 ticks becomes eligible; draw < 0.03 fires Knowledge Lost:
    tech -= 5.0, last_kl = tick, event queued.
    RED on main (pop-drop leg absent), GREEN after implementation."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    # Fill ring with 49 samples of pop=50.0 (eco leg ineligible, no draw)
    for _ in range(49):
        lib.om_tech_step(w)

    # Drop by exactly 10.0 -> avg_p_now=40.0 <= avg_p_50_ago=50.0 - 10.0 = 40.0
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=40.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 0, "draw must be consumed when eligible"
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100, "last_kl = firing tick"

    # Knowledge Lost event queued for due_tick = tick+1 = 101
    queued = read_event_queue(lib, w)
    kl = [e for e in queued if template_name(lib, w, e.template_id) == "Knowledge Lost"]
    assert len(kl) >= 1, "Knowledge Lost event must be queued"
    assert kl[0].region_idx == 0, "queued on highest-pop region"

    # Growth over 50 steps then KL delta:
    # 49 * (0.35*0.25*0.5) + 1 * (0.35*0.25*0.4) = 49*0.04375 + 0.035 = 2.17875
    # tech = 30.0 + 2.17875 - 5.0 = 27.17875
    assert lib.om_faction_tech(w, 0) == pytest.approx(27.17875, abs=1e-3)


def test_pop_drop_9_not_eligible(lib, world_factory):
    """R-045-07 / ALG-27b positive control: drop of 9.0 (below 10.0 threshold)
    is not eligible; no draw consumed, tech only grows."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    for _ in range(49):
        lib.om_tech_step(w)

    # Drop by 9.0 -> avg_p=41.0 > 50.0 - 10.0 = 40.0, not eligible
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=41.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "draw must NOT be consumed (drop < 10)"
    assert lib.om_faction_last_knowledge_lost(w, 0) == -1, "no KL fired"


def test_cooldown_blocks_second_pop_drop(lib, world_factory):
    """R-045-09 / ALG-27b: a second qualifying pop-drop within 100 ticks of a
    fired KL does not fire (cooldown blocks it)."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    for _ in range(49):
        lib.om_tech_step(w)

    # First KL fires
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=40.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100

    # Second qualifying drop on the same tick (cooldown = tick - last_kl = 0 < 100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=30.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "cooldown must block second fire"
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100, "last_kl unchanged"


def test_pop_drop_leg_not_eligible_before_50_ticks(lib, world_factory):
    """R-045-07 / ALG-27b: before 50 ticks of history exist the pop-drop leg is
    not eligible; no draw consumed even with a population of 0."""
    # Pop=0.0 would represent a massive drop if 50 ticks of history existed.
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=0.0, tech=30.0)

    # Only 1 step -> len=1 < 50 -> not eligible
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "draw must NOT be consumed before 50 ticks"
    assert lib.om_faction_last_knowledge_lost(w, 0) == -1
