"""Population-drop leg of ALG-27b Knowledge Lost (R-045-07, R-045-09).

Tests the eligibility leg: avg_p(now) <= avg_p(tick-50) - KNOWLEDGE_LOST_POP_DROP=10.0.
Economy leg (avg_e < 20) tested by the neighbouring test_E06 suite; no duplication here.

Ring semantics after the off-by-one fix (B5c-1 rev 2):
  pl = pre-push length; pop-drop eligible on the 51st push (pl==50 before push),
  when ring[ph] holds the sample from exactly 50 pushes ago.
  The 50th push has pl=49 < 50 and is NOT eligible.
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
    (100 - last_kl=-1 = 101 >= COOLDOWN=100). om_tech_step does not advance
    the tick, so all direct calls see tick=100."""
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
    RED on main (pop-drop leg absent), GREEN after implementation.

    50 setup calls fill the ring (pl reaches 50 pre-51st-push).
    tech = 30 + 50*0.04375 + 0.035 - 5.0 = 27.2225"""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    # Fill ring: 50 samples of pop=50.0 -> len reaches 50, head wraps to 0.
    # Economy leg ineligible (eco=25 >= 20), no draw consumed.
    for _ in range(50):
        lib.om_tech_step(w)

    # 51st push: drop by exactly 10.0 -> avg_p=40.0 <= ring[head=0]=50.0 - 10.0=40.0
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

    # Growth: 50 * (0.35*0.25*0.5) + 1 * (0.35*0.25*0.4) = 2.1875 + 0.035 = 2.2225
    # tech = 30.0 + 2.2225 - 5.0 = 27.2225
    assert lib.om_faction_tech(w, 0) == pytest.approx(27.2225, abs=1e-3)


def test_pop_drop_9_not_eligible(lib, world_factory):
    """R-045-07 / ALG-27b positive control: drop of 9.0 (below 10.0 threshold)
    is not eligible; no draw consumed, tech only grows.

    GREEN on main (pop-drop leg absent -- leg missing means no draw consumed,
    which is the expected result; this test is green trivially on main).
    GREEN on candidate (9 < threshold 10 -> not eligible).
    Would be RED if threshold were 9 (9.0 <= 50.0-9.0=41.0 is true -> eligible
    -> draw consumed -> rng_forced_remaining==0 -> assertion fails).

    50 setup calls; 51st call has pop=41.0 (drop=9.0 from ring's 50.0)."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    for _ in range(50):
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
    fired KL does not fire (cooldown blocks it). om_tech_step does not advance
    tick, so both qualifying calls see tick=100; the second has last_kl=100,
    delta=0 < COOLDOWN=100."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    for _ in range(50):
        lib.om_tech_step(w)

    # First KL fires on 51st push (drop 10.0, eligible)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=40.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100

    # Second qualifying drop on tick=100 (cooldown = tick - last_kl = 0 < 100)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=30.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "cooldown must block second fire"
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100, "last_kl unchanged"


def test_pop_drop_leg_not_eligible_before_50_ticks(lib, world_factory):
    """R-045-07 / ALG-27b: before 50 ticks of history exist the pop-drop leg is
    not eligible; no draw consumed even with a population of 0.
    pl=0 before first push -> gate pl==50 fails."""
    # Pop=0.0 would represent a massive drop if 50 ticks of history existed.
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=0.0, tech=30.0)

    # Only 1 step -> pl=0 before push < 50 -> not eligible
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "draw must NOT be consumed before 50 ticks"
    assert lib.om_faction_last_knowledge_lost(w, 0) == -1


def test_50tick_sample_used_not_49tick(lib, world_factory):
    """ALG-27b: ring reads the sample from exactly 50 pushes ago (not 49).
    Setup: ring[oldest]=50.0 (50 pushes ago), ring[next]=41.0 (49 pushes ago).
    Current pop=40.0 -> drop vs 50-tick-ago = 10.0 (eligible) but drop vs
    49-tick-ago = 1.0 (not eligible).
    RED on buggy ring (reads 49-tick slot -> drop=1.0 -> not eligible -> draw not consumed).
    GREEN after fix (reads 50-tick slot -> drop=10.0 -> eligible -> draw consumed).

    50 total setup calls: 1 with pop=50, 49 with pop=41. Ring full, head=0,
    ring[0]=50.0 (oldest). 51st call pop=40.0 fires KL.
    tech = 30 + 1*0.04375 + 49*0.035875 + 0.035 - 5.0 = 26.836625"""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    # 1 push with pop=50 -> ring[0]=50.0, head=1, len=1
    lib.om_tech_step(w)

    # 49 pushes with pop=41 -> ring[1..49]=41.0, head=0, len=50 (ring full)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=41.0, faction_id=0)
    for _ in range(49):
        lib.om_tech_step(w)

    # 51st push: pop=40.0 -> oldest ring[0]=50.0, drop=10.0 >= 10.0 -> eligible
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=40.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 0, "draw consumed: 50-tick drop=10.0 is eligible"
    assert lib.om_faction_last_knowledge_lost(w, 0) == 100

    # tech = 30 + 0.04375 + 49*0.035875 + 0.035 - 5.0 = 26.836625
    assert lib.om_faction_tech(w, 0) == pytest.approx(26.836625, abs=1e-3)


def test_49tick_sample_drop_not_eligible(lib, world_factory):
    """ALG-27b mirror: ring reads 50-tick-ago slot, so a large drop relative to
    49 ticks ago but small relative to 50 ticks ago is NOT eligible.
    Setup: ring[oldest=0]=50.0 (50 pushes ago), ring[1]=60.0 (49 pushes ago).
    Current pop=49.0 -> drop vs 50-tick-ago = 1.0 (not eligible) but drop vs
    49-tick-ago = 11.0 (would fire on buggy ring).
    RED on buggy ring (reads 49-tick slot -> drop=11.0 -> eligible -> draw consumed).
    GREEN after fix (reads 50-tick slot -> drop=1.0 -> not eligible -> draw kept).

    50 total setup calls: 1 with pop=50, 1 with pop=60, 48 with pop=60. Ring
    full, head=0, ring[0]=50.0 (oldest), ring[1]=60.0."""
    w = _pop_drop_world(lib, world_factory, eco=25.0, pop=50.0, tech=30.0)

    # 1 push with pop=50 -> ring[0]=50.0
    lib.om_tech_step(w)

    # 1 push with pop=60 -> ring[1]=60.0
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=60.0, faction_id=0)
    lib.om_tech_step(w)

    # 48 more pushes with pop=60 -> ring[2..49]=60.0, head=0, len=50 (ring full)
    for _ in range(48):
        lib.om_tech_step(w)

    # 51st push: pop=49.0 -> oldest ring[0]=50.0, drop=1.0 < 10.0 -> NOT eligible
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
               tension=10.0, population=49.0, faction_id=0)
    force_draws(lib, w, [0.01])
    lib.om_tech_step(w)

    assert lib.om_rng_forced_remaining(w) == 1, "draw NOT consumed: 50-tick drop=1.0 < 10.0"
    assert lib.om_faction_last_knowledge_lost(w, 0) == -1, "no KL fired"
