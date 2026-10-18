"""CHRON-CONTEXT: the time jump scores each event with the ALG-50 context terms.

Spec: docs/northstar/plans/2026-10-18-chron-context-spec.md (W3 (b), chain length
filled per jump). E-09 R-066-02 / R-066-04: significance = base * (1 + 0.5 mission
region + 0.3 attached character + 0.1 * min(L, 5) chain length when L > 1 + 0.8
lineage member in the region).

How the tests read a jump's per-region peak: the REGIONAL clusters of the scroll
(om_chronicle_get_cluster, peak_score) after om_time_jump_run. Events are fired
inside the jump from queued externals (om_event_queue_external) and from a
hand-built template library (om_events_load), so tier and delta are known.
The expected values come from om_chronicle_calculate_score, the ALG-50 oracle the
pass will call, so the tests do not restate the tier table or the constants.

Reading the mission region: om_mission_last_region (SIM-LOGS is not landed). What
it returns before any mission has ended is the builder's sentinel; every region
here is picked so no test depends on it.
"""
import ctypes

import pytest

from conftest import (
    OMField,
    OMTier,
    OMTrigger,
    OMCond,
    OmChronicleCluster,
    OmEventTemplate,
    load_launch_events,
    queue_external,
    read_events,
    set_edge,
    set_owner,
    set_region,
)

CTYPE_REGIONAL = 3
MISSION_REGION = 2
DEFENSIVE_STAND = 0

# Library layout. The jump's tier comes from the launch tier table by template id
# (generational.c GEN_LAUNCH_EVENT_TIER: ids 0, 1 and 3 are tier 4), so the hand-built
# templates sit on those ids and all score at tier 4.
TID_CHAIN_HEAD = 0   # spawns TID_CHAIN_TAIL one tick later, same region, same chain tag
TID_CHAIN_TAIL = 1
TID_FILLER = 2
TID_LONE = 3         # same effect as the chain pair, no spawn
TID_FLOOD = 4        # PROBABILITY trigger: fires every tick in a region with any military, never at military 0
TIER = 4
EFFECT = (4.0, -3.0, 2.0, 1.0)  # military, economy, tension, population


def _template(tid, name, *, effect=EFFECT, spawn_to=None, trigger=OMTrigger.NONE):
    t = OmEventTemplate()
    t.id = tid
    t.name = name.encode()
    t.trigger_kind = trigger
    if trigger == OMTrigger.PROBABILITY:
        t.trigger_field = OMField.MILITARY
        t.prob_base = 1000.0   # p = min(1, 1000 * mil / 100): 1 above military 0.1, exactly 0 at military 0
        t.prob_exponent = 1.0
        t.cooldown_ticks = 0
    for f in range(OMField.COUNT):
        t.effect[f] = effect[f]
    if spawn_to is not None:
        t.n_spawns = 1
        t.spawns[0].template_id = spawn_to
        t.spawns[0].delay_min = 1
        t.spawns[0].delay_max = 1
        t.spawns[0].cond_kind = OMCond.NONE
        t.spawns[0].probability = 1.0
    return t


def _load_library(lib, w, with_flood=False):
    load_launch_events(lib, w)  # binds the event API
    ts = [
        _template(TID_CHAIN_HEAD, "ctx_head", spawn_to=TID_CHAIN_TAIL),
        _template(TID_CHAIN_TAIL, "ctx_tail"),
        _template(TID_FILLER, "ctx_filler"),
        _template(TID_LONE, "ctx_lone"),
    ]
    if with_flood:
        ts.append(_template(TID_FLOOD, "ctx_flood", effect=(0.0, 0.0, 0.0, 0.0), trigger=OMTrigger.PROBABILITY))
    arr = (OmEventTemplate * len(ts))(*ts)
    assert lib.om_events_load(w, arr, len(ts)) == 0


def _world(lib, world_factory, n_regions=4, seed=7):
    w = world_factory(n_regions=n_regions, seed=seed)
    for r in range(n_regions):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _end_mission(lib, w, region=MISSION_REGION):
    lib.om_mission_setup(w, region, DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, DEFENSIVE_STAND)
    for i in range(lib.om_mission_objective_count(w)):
        lib.om_mission_set_objective_completion(w, i, 1.0)
    lib.om_mission_end(w)
    assert lib.om_mission_last_region(w) == region  # fixture check: the mission really ended there


def _peaks(lib, w):
    """Region -> the highest REGIONAL cluster peak_score in the scroll."""
    out = {}
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        if c.type == CTYPE_REGIONAL:
            out[c.region] = max(out.get(c.region, 0.0), c.peak_score)
    return out


def _dsum():
    return sum(abs(x) for x in EFFECT)


def _expect(lib, w, *, mission=0, character=0, chain=0, lineage=0, tier=TIER, dsum=None):
    return lib.om_chronicle_calculate_score(w, tier, _dsum() if dsum is None else dsum,
                                            mission, character, chain, lineage)


def _jump(lib, w, ticks=30):
    assert lib.om_time_jump_run(w, ticks, None) == 0


# ---- (1) the mission-region term ----

def test_R_066_02_event_in_the_last_mission_region_scores_one_and_a_half_times(lib, world_factory):
    """Given a mission that ended in region 2 and identical events in region 2 and region 1, When a jump runs, Then region 2's peak is the base times 1.5 and region 1's is the base."""
    w = _world(lib, world_factory)
    _load_library(lib, w)
    _end_mission(lib, w)
    assert queue_external(lib, w, MISSION_REGION, TID_LONE, due_tick=3) > 0
    assert queue_external(lib, w, 1, TID_LONE, due_tick=3) > 0

    _jump(lib, w)

    peaks = _peaks(lib, w)
    base = _expect(lib, w)
    assert peaks[1] == pytest.approx(base, abs=1e-6)  # the other region keeps the plain base
    assert peaks[MISSION_REGION] == pytest.approx(base * 1.5, abs=1e-6)
    assert peaks[MISSION_REGION] == pytest.approx(peaks[1] * 1.5, abs=1e-6)


def test_R_066_02_no_mission_ended_no_mission_region_bonus(lib, world_factory):
    """Given no mission has ended, When identical events fire in regions 1 and 2, Then both peaks are the plain base (the +0.5 needs a mission)."""
    w = _world(lib, world_factory)
    _load_library(lib, w)
    for r in (1, 2):
        assert queue_external(lib, w, r, TID_LONE, due_tick=3) > 0

    _jump(lib, w)

    peaks = _peaks(lib, w)
    base = _expect(lib, w)
    for r in (1, 2):
        assert peaks[r] == pytest.approx(base, abs=1e-6)


def test_control_hand_built_value_without_the_mission_term_fails_the_mission_test(lib, world_factory):
    """Positive control: the oracle separates the two cases, so the mission test's red is the jump's term being 0 and not an oracle that cannot tell 1.0 from 1.5."""
    w = _world(lib, world_factory)
    assert _expect(lib, w, mission=1) == pytest.approx(_expect(lib, w) * 1.5, abs=1e-9)
    assert _expect(lib, w, mission=1) != pytest.approx(_expect(lib, w), abs=1e-6)


# ---- (2) the chain-length term (W3 b) ----

def test_R_066_02_two_event_chain_scores_plus_point_two(lib, world_factory):
    """Given a two-event chain (a template and the one follow-up it spawns, one chain tag) in region 1 and a lone event of the same tier and delta in region 3, When a jump runs, Then region 1's peak is the base times 1.2 and region 3's is the base."""
    w = _world(lib, world_factory)
    _load_library(lib, w)
    assert queue_external(lib, w, 1, TID_CHAIN_HEAD, due_tick=3) > 0
    assert queue_external(lib, w, 3, TID_LONE, due_tick=3) > 0

    _jump(lib, w)

    peaks = _peaks(lib, w)
    assert peaks[3] == pytest.approx(_expect(lib, w), abs=1e-6)
    assert peaks[1] == pytest.approx(_expect(lib, w, chain=2), abs=1e-6)
    assert peaks[1] == pytest.approx(peaks[3] * 1.2, abs=1e-6)


def test_control_wrong_chain_count_fails_the_chain_test(lib, world_factory):
    """Positive control: hand-built expected values for chain counts 1, 3 and 2 differ, so a pass that counted the chain wrong (or not at all) cannot satisfy the chain test."""
    w = _world(lib, world_factory)
    two = _expect(lib, w, chain=2)
    assert two == pytest.approx(_expect(lib, w) * 1.2, abs=1e-9)
    assert _expect(lib, w, chain=3) == pytest.approx(_expect(lib, w) * 1.3, abs=1e-9)
    assert two != pytest.approx(_expect(lib, w, chain=3), abs=1e-6)
    assert two != pytest.approx(_expect(lib, w, chain=1), abs=1e-6)


def test_R_066_04_chain_term_ignores_a_lone_tagged_event(lib, world_factory):
    """Given a queued event with its own chain tag and no follow-up, When a jump runs, Then it scores chain length 1: no chain bonus (L > 1 only)."""
    w = _world(lib, world_factory)
    _load_library(lib, w)
    assert queue_external(lib, w, 1, TID_LONE, due_tick=3) > 0
    _jump(lib, w)
    assert _peaks(lib, w)[1] == pytest.approx(_expect(lib, w), abs=1e-6)


# ---- (3) the lineage term is unchanged by the pass ----

def _lineage_world(lib, world_factory, lifespan, seed=7):
    w = _world(lib, world_factory, seed=seed)
    set_edge(lib, w, 1, 0)  # a descendant that spreads needs an inhabited neighbour
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_character_create(w, character_id=1, lineage_id=1, region_idx=1, rank=3, birth_tick=0, lifespan=lifespan)
    _load_library(lib, w)
    assert queue_external(lib, w, 1, TID_LONE, due_tick=3) > 0
    assert queue_external(lib, w, 3, TID_LONE, due_tick=3) > 0
    return w


def test_R_066_02_lineage_member_keeps_plus_point_eight(lib, world_factory):
    """Given a lineage member living in region 1 through the jump, When identical events fire in region 1 and region 3, Then region 1's peak is the base times 1.8 and region 3's is the base (pins behaviour that is unchanged)."""
    w = _lineage_world(lib, world_factory, lifespan=100000)
    _jump(lib, w)
    peaks = _peaks(lib, w)
    assert peaks[1] == pytest.approx(_expect(lib, w, lineage=1), abs=1e-6)
    assert peaks[3] == pytest.approx(_expect(lib, w), abs=1e-6)


def test_R_066_02_member_who_dies_in_the_jump_still_counted_at_scoring_time(lib, world_factory):
    """Given a lineage member in region 1 whose lifespan ends inside the jump (the death pass removes them after the loop) and no one left in region 1 once the jump is over, When an event fires in region 1 at tick 3, Then region 1's peak is still the loop-era base times 1.8: the member was alive at scoring time. A pass placed after om_process_natural_deaths would score 1.0 here and fail.

    The jump always generates at least one descendant of a living lineage, born in the parent's region unless it spreads to a neighbour; the test walks seeds until the descendant spreads (region 1 empty after the jump), so the late pass has nobody to find."""
    for seed in range(1, 60):
        w = _lineage_world(lib, world_factory, lifespan=10, seed=seed)
        _jump(lib, w, ticks=60)
        if lib.om_lineage_member_in_region(w, 1, 1) == 0:
            break
    else:
        pytest.fail("no seed in 1..59 moved the descendant out of region 1: the late-pass control cannot be built")
    assert _peaks(lib, w)[1] == pytest.approx(_expect(lib, w, lineage=1), abs=1e-6)
    assert _peaks(lib, w)[1] != pytest.approx(_expect(lib, w), abs=1e-6)


def test_R_066_02_lineage_and_mission_and_chain_terms_add(lib, world_factory):
    """Given a lineage member, a mission and a two-event chain all in region 2, When a jump runs, Then the multiplier is 1 + 0.5 + 0.2 + 0.8 (the terms add, they do not replace each other)."""
    w = _world(lib, world_factory)
    _load_library(lib, w)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_character_create(w, character_id=1, lineage_id=1, region_idx=MISSION_REGION, rank=3, birth_tick=0, lifespan=100000)
    _end_mission(lib, w)
    assert queue_external(lib, w, MISSION_REGION, TID_CHAIN_HEAD, due_tick=3) > 0
    _jump(lib, w)
    assert _peaks(lib, w)[MISSION_REGION] == pytest.approx(_expect(lib, w, mission=1, chain=2, lineage=1), abs=1e-6)


# ---- (4) the record cap ----

FLOOD_REGIONS = 120          # fired log holds 128 per tick; 120 flood regions leave room for one queued event
LATE_TICK = 95               # past tick 8192 / 120 = 68: the records are full by then
MISSION_FLOOD_REGION = 120   # military 0: its trigger probability is 0, so only the queued event fires there


def _flood_world(lib, world_factory, queued_due_tick):
    n = FLOOD_REGIONS + 1
    w = world_factory(n_regions=n, seed=7)
    for r in range(n):
        set_region(lib, w, r, tier=OMTier.HOME, military=100.0 if r < FLOOD_REGIONS else 0.0,
                   economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    _load_library(lib, w, with_flood=True)
    _end_mission(lib, w, MISSION_FLOOD_REGION)
    assert queue_external(lib, w, MISSION_FLOOD_REGION, TID_LONE, due_tick=queued_due_tick) > 0
    return w


def _flood_jump(lib, w):
    _jump(lib, w, ticks=100)
    return _peaks(lib, w)


def test_R_066_02_cap_flood_world_reaches_the_cap(lib, world_factory):
    """Fixture check: the flood world really fires more than 8,192 events in the jump (120 flood regions every tick for 100 ticks is 12,000). Counted by replaying the same world tick by tick and reading om_tick_events."""
    w = _flood_world(lib, world_factory, queued_due_tick=LATE_TICK)
    total = 0
    for _ in range(100):
        lib.om_world_step(w)
        total += len(read_events(lib, w))
    assert total > 8192, f"flood world fired only {total} events; the cap test below proves nothing"


def test_R_066_02_events_past_the_cap_are_dropped_from_the_pass_but_not_the_scroll(lib, world_factory):
    """Given more than DRAFT-chron-rec-cap (8,192) events in a 100-tick jump and a mission region whose only event fires at tick 95 (past the cap), When the jump runs, Then that event scores as the loop did (no mission bonus: it was not stored) and the region is still in the scroll."""
    w = _flood_world(lib, world_factory, queued_due_tick=LATE_TICK)
    peaks = _flood_jump(lib, w)
    assert MISSION_FLOOD_REGION in peaks  # no region lost from active[]
    assert peaks[MISSION_FLOOD_REGION] == pytest.approx(_expect(lib, w), abs=1e-6)


def test_R_066_02_event_inside_the_cap_in_the_same_flood_gets_the_mission_bonus(lib, world_factory):
    """Control for the cap test: the same flood with the mission region's event at tick 3 (stored) scores base times 1.5, so the cap test's plain base is the drop and not a pass that never runs under load."""
    w = _flood_world(lib, world_factory, queued_due_tick=3)
    peaks = _flood_jump(lib, w)
    assert peaks[MISSION_FLOOD_REGION] == pytest.approx(_expect(lib, w, mission=1), abs=1e-6)


# ---- (5) the S070 control ----

def test_control_S070_runs_green_unchanged():
    """Control: the S-070 file (lineage +0.8 via om_chronicle_score_event, signature untouched) passes when run in-process as it stands."""
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    rc = pytest.main(["-q", "-p", "no:cacheprovider", str(here / "test_E09_S070_my_family_is_always_in_the_story.py")])
    assert rc == 0
