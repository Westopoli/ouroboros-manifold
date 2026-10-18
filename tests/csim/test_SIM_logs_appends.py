"""SIM-LOGS, the appends: which call site writes which log entry, and the times_run / window_start latch.

Spec: docs/northstar/plans/2026-10-15-sim-logs-spec.md rev 4 ("Appends", "Accessors").

RED today: om_simlog_* do not exist in libouroboros.so; they are bound here with ctypes straight
from the Accessors paragraph (conftest.py is not edited). One test is red by assertion instead of by
symbol: test_attack_conquest_sets_previous_owner (today om_region_previous_owner returns -1 after an
attack conquest; that is the resolve.c:479 fix). The controls that need no new symbol are green.

Names the spec leaves implicit, decided here:
  om_simlog_conquest_count / _get_at and om_simlog_event_count / _get_at ("the same pair");
  om_simlog_times_run(w, lineage_id, archetype) -> uint32_t, om_simlog_window_start(w) -> int64_t;
  "the tick" of window_start is om_world_strategic_tick(w) at the call; the seated lineage is
  om_campaign_lineage(w) when non-zero, else the last created lineage (om_lineage_id_at(w, n-1));
  the archetype counted is the one passed to om_mission_setup.
The guard-bypass sub-claim ("past the attacks_n < OM_MAX_REGIONS guard") is not tested here: no
fixture of this suite fills the per-tick buffer; the builder's landing report should say so.
"""
import ctypes

import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMFeature,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_attacks,
    read_events,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
    template_id,
)

from test_SIM_logs_ring import (  # the one place the struct mirrors and accessors are defined
    OM_CONQ_ATTACK,
    OM_CONQ_COLONISATION,
    OM_CONQ_MISSION,
    OM_CONQ_REVOLT,
    bind_logs,
    campaign,
    conquest_world,
    event_world,
    full_hash,
    read_log,
    save_bytes,
)

BAND_TOTAL_SUCCESS = 4
ARCH_ASSAULT = 3


# ---- one resolved attack per record site ----

def _telegraph_world(lib, world_factory):
    """test_E05_S036 R-036-03: conqueror 0 telegraphs 70 against region 1 on tick 1; it matures on tick 4."""
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=50.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=40.0, economy=60.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    return w


def test_unmatured_telegraph_adds_nothing(lib, world_factory):
    """Positive control: declared on tick 1, still pending on ticks 1 to 3, so no attack entry yet (resolve.c:237)."""
    bind_logs(lib)
    w = _telegraph_world(lib, world_factory)
    force_draws(lib, w, [0.1, 0.5, 0.5])
    lib.om_world_step(w)
    for _ in range(2):
        force_draws(lib, w, [0.5, 0.5])
        lib.om_world_step(w)
    assert read_attacks(lib, w) == []
    assert lib.om_simlog_attack_count(w) == 0
    assert lib.om_simlog_conquest_count(w) == 0


def test_telegraph_maturity_logs_one_attack_with_its_commit(lib, world_factory):
    bind_logs(lib)
    w = _telegraph_world(lib, world_factory)
    force_draws(lib, w, [0.1, 0.5, 0.5])
    lib.om_world_step(w)
    for _ in range(2):
        force_draws(lib, w, [0.5, 0.5])
        lib.om_world_step(w)
    force_draws(lib, w, [1.0])
    lib.om_world_step(w)
    rec = read_attacks(lib, w)
    assert len(rec) == 1
    assert read_log(lib, w, "attack") == [(4, 0, 1, pytest.approx(70.0, abs=1e-6))]
    assert rec[0].commit == pytest.approx(70.0, abs=1e-6)


def test_surprise_attack_logs_one_attack(lib, world_factory):
    """resolve.c:416 site: test_E05_S036 R-036-04, resolved on the declaring tick."""
    bind_logs(lib)
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.DEFAULT)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=30.0, economy=60.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    force_draws(lib, w, [0.95, 1.0])
    lib.om_world_step(w)
    assert len(read_attacks(lib, w)) == 1
    assert read_log(lib, w, "attack") == [(1, 0, 1, pytest.approx(70.0, abs=1e-6))]


def test_betrayal_logs_an_attack(lib, world_factory):
    """diplomacy.c:264-284: test_E06_S044 R-044-01 case A, faction 0 betrays its partner."""
    bind_logs(lib)
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    lib.om_world_set_feature(w, OMFeature.DIPLOMACY, 1)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=50.0, tech=0.0)
    set_faction(lib, w, 1, OMArchetype.WARLORD, budget=50.0, tech=0.0)
    set_stance(lib, w, 0, 1, OMStance.COOPERATIVE)
    for idx, mil in enumerate((60.0, 60.0, 20.0, 20.0)):
        set_region(lib, w, idx, tier=OMTier.HOME, military=mil, economy=50.0, tension=20.0, population=50.0)
    for idx, fid in enumerate((0, 0, 1, 1)):
        set_owner(lib, w, idx, fid)
    set_edge(lib, w, 1, 2, OMEdge.BORDER)
    force_draws(lib, w, [0.001, 0.001])
    lib.om_world_step(w)
    rec = read_attacks(lib, w)
    assert len(rec) == 1
    log = read_log(lib, w, "attack")
    assert log == [(int(rec[0].tick), 0, int(rec[0].target_idx), pytest.approx(rec[0].commit))]


# ---- conquests ----

def test_attack_conquest_logs_kind_0(lib, world_factory):
    bind_logs(lib)
    w = conquest_world(lib, world_factory)
    assert read_log(lib, w, "conquest") == [(4, 1, 1, 0, OM_CONQ_ATTACK)]
    assert len(read_log(lib, w, "attack")) == 1


def test_attack_conquest_sets_previous_owner(lib, world_factory):
    """The red line for the resolve.c:479 fix. Needs no new symbol: today this returns -1 (never set by attacks)."""
    w = conquest_world(lib, world_factory)
    assert lib.om_region_previous_owner(w, 1) == 1


def test_mission_transfer_logs_kind_1_and_sets_previous_owner(lib, world_factory):
    """mission.c:938 via om_mission_apply_consequences: a total-success Assault hands region 1 to the player."""
    bind_logs(lib)
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.PLAYER, budget=0.0)
    set_faction(lib, w, 1, OMArchetype.DEFAULT, budget=0.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    player = lib.om_player_faction(w)
    assert player == 0, "fixture: the player faction owns region 0"
    lib.om_mission_apply_consequences(w, 1, ARCH_ASSAULT, BAND_TOTAL_SUCCESS)
    assert lib.om_region_owner(w, 1) == 0, "fixture: the transfer happened"
    assert lib.om_region_previous_owner(w, 1) == 1
    log = read_log(lib, w, "conquest")
    assert len(log) == 1 and log[0][1:] == (1, 1, 0, OM_CONQ_MISSION)


def test_lifecycle_revolt_logs_kind_2_and_the_event(lib, world_factory):
    """lifecycle.c:237-238: the breakaway takes region 0 from faction 0 into new faction 1; the revolt event is logged too."""
    bind_logs(lib)
    w = event_world(lib, world_factory)
    assert read_log(lib, w, "conquest") == [(1, 0, 0, 1, OM_CONQ_REVOLT)]


def test_fired_event_logs_template_region_and_chain_tag(lib, world_factory):
    bind_logs(lib)
    w = event_world(lib, world_factory)
    fired = read_events(lib, w)
    assert len(fired) == 1
    tid = template_id(lib, w, "Revolt Entrenched")
    log = read_log(lib, w, "event")
    assert log == [(int(fired[0].tick), 0, tid, int(fired[0].chain_tag), int(fired[0].creates_faction))]


def _colonise_world(lib, world_factory, both):
    """test_E05_S039 wiring fixture: empty region 3 is colonised by faction 0 (solo) or contested by 0 and 1 (collision)."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=60.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 2, tier=OMTier.HOME, military=30.0, economy=100.0, tension=0.0, population=50.0, faction_id=1)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    for idx, fid in ((0, 0), (1, 0), (2, 1)):
        set_owner(lib, w, idx, fid, held_since=-1)
    set_edge(lib, w, 1, 3, OMEdge.BOTH)
    set_edge(lib, w, 2, 3, OMEdge.BOTH)
    inject_intent(lib, w, 0, OMAction.COLONIZE, 3, 1, 40.0)
    if both:
        inject_intent(lib, w, 1, OMAction.COLONIZE, 3, 2, 20.0)
        force_draws(lib, w, [0.1, 0.0])
    else:
        force_draws(lib, w, [0.1])
    lib.om_world_step(w)
    return w


@pytest.mark.parametrize("both", [False, True], ids=["solo_resolve_c540", "collision_c172"])
def test_colonisation_logs_kind_5_with_no_old_owner(lib, world_factory, both):
    bind_logs(lib)
    w = _colonise_world(lib, world_factory, both)
    owner = lib.om_region_owner(w, 3)
    assert owner in (0, 1)
    log = read_log(lib, w, "conquest")
    assert [e for e in log if e[1] == 3] == [(1, 3, -1, owner, OM_CONQ_COLONISATION)]


# ---- times_run, window_start ----

def _seated(lib, w):
    lineage = lib.om_campaign_lineage(w)
    return lineage if lineage else lib.om_lineage_id_at(w, lib.om_lineage_count(w) - 1)


def _begin_mission(lib, w, archetype=ARCH_ASSAULT):
    lib.om_mission_start(w, 0)
    lib.om_mission_setup(w, lib.om_mission_generator_chosen_region(w), archetype, 0)


def _times_run_setup(lib):
    bind_logs(lib)
    lib.om_simlog_times_run.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
    lib.om_simlog_times_run.restype = ctypes.c_uint32
    w = campaign(lib)
    assert lib.om_time_jump_run(w, 50, None) == 0
    return w


def test_times_run_rises_once_on_mission_end_and_not_on_a_second_call(lib):
    w = _times_run_setup(lib)
    try:
        seated = _seated(lib, w)
        row_before = [lib.om_simlog_times_run(w, seated, a) for a in range(10)]
        assert row_before[ARCH_ASSAULT] == 0
        _begin_mission(lib, w)
        lib.om_mission_end(w)
        row = [lib.om_simlog_times_run(w, seated, a) for a in range(10)]
        assert row[ARCH_ASSAULT] == 1, "exactly one for the seated lineage's archetype"
        assert [r for i, r in enumerate(row) if i != ARCH_ASSAULT] == [r for i, r in enumerate(row_before) if i != ARCH_ASSAULT]
        assert lib.om_simlog_window_start(w) == lib.om_world_strategic_tick(w)
        lib.om_mission_end(w)
        assert lib.om_simlog_times_run(w, seated, ARCH_ASSAULT) == 1, "a second om_mission_end must not double-count"
    finally:
        lib.om_world_free(w)


def test_refusal_sets_window_start_and_counts_no_run(lib):
    w = _times_run_setup(lib)
    try:
        seated = _seated(lib, w)
        assert lib.om_simlog_window_start(w) == 0, "campaign start: the first chapter counts everything"
        lib.om_mission_start(w, 0)
        region = next(i for i in range(lib.om_region_count(w)) if lib.om_region_owner(w, i) == 0)
        lib.om_mission_resolve_refusal(w, region)
        assert lib.om_simlog_window_start(w) == lib.om_world_strategic_tick(w) > 0
        assert [lib.om_simlog_times_run(w, seated, a) for a in range(10)] == [0] * 10
    finally:
        lib.om_world_free(w)


def test_window_start_follows_each_end_to_the_new_tick(lib):
    w = _times_run_setup(lib)
    try:
        _begin_mission(lib, w)
        lib.om_mission_end(w)
        first = lib.om_simlog_window_start(w)
        assert first == lib.om_world_strategic_tick(w)
        lib.om_chapter_set_phase(w, 0)
        assert lib.om_time_jump_run(w, 50, None) == 0
        assert lib.om_simlog_window_start(w) == first, "a jump does not move the window"
        _begin_mission(lib, w)
        lib.om_mission_end(w)
        assert lib.om_simlog_window_start(w) == lib.om_world_strategic_tick(w) > first
    finally:
        lib.om_world_free(w)


# ---- positive controls: the save notices an append ----

def test_save_before_an_append_differs_from_save_after(lib, world_factory):
    bind_logs(lib)
    w = _telegraph_world(lib, world_factory)
    force_draws(lib, w, [0.1, 0.5, 0.5])
    lib.om_world_step(w)
    for _ in range(2):
        force_draws(lib, w, [0.5, 0.5])
        lib.om_world_step(w)
    assert lib.om_simlog_attack_count(w) == 0
    before_bytes, before_hash = save_bytes(lib, w), full_hash(lib, w)
    force_draws(lib, w, [1.0])
    lib.om_world_step(w)
    assert lib.om_simlog_attack_count(w) == 1
    assert save_bytes(lib, w) != before_bytes
    assert full_hash(lib, w)[0] != before_hash[0]
