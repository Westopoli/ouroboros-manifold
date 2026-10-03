"""B7-1 (R-061-04): when the commander dies, the ledger records the region and the outcome band.

R-061-04: "Given a commander death, When recorded, Then the ledger records the region and
outcome band and the chronicle frames it (E-09)." Only the ledger half is tested here.

Drive: the same public calls the pipe handlers make (campaign start, mission start/setup,
assign commander, the commander's unit dies, mission end, time jump). The test never calls
om_outcome_record_commander_death or om_character_kill: the jump has to do that itself.
The expected region is the mission's region and the expected band is the debrief's band for
that mission, both read before the jump; an absent ledger entry reads region 0 / band 0 and the
chosen mission region is asserted nonzero so that absence cannot pass.

Liveness getter: there is no dedicated one; om_character_get_record(...).status is used
(0 active, 1 historical, as GEN_STATUS_HISTORICAL in csrc/generational.c).

RED today: nothing in the mission end or the jump records the death or marks the commander
historical, so the ledger reads empty after the jump.
"""
import ctypes

from conftest import OMDebrief, OmCharacterRecord

FEATURES = list(range(8))
PLAYER = 0
SEED = 7
BRIEFING = 0
GEN_STATUS_HISTORICAL = 1
FATE_KILLED, FATE_SURVIVED = 0, 2


def _campaign(lib, world_factory):
    w = world_factory(n_regions=80, seed=SEED)
    for f in range(9):
        lib.om_world_set_feature(w, f, 1 if f in FEATURES else 0)
    lib.om_world_generate(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    lib.om_campaign_start(w, 1)
    return w


def _mission(lib, w, kill_commander_unit):
    """Play one mission with unit 1 as commander; returns (region, band, fate)."""
    lib.om_mission_start(w, PLAYER)
    region = lib.om_mission_generator_chosen_region(w)
    lib.om_mission_setup(w, region, max(lib.om_mission_generator_chosen_archetype(w), 0), 0)
    assert lib.om_mission_get_force_count(w) >= 1, "fixture: the mission needs a player unit"
    assert lib.om_mission_assign_commander(w, 1) == 0
    if kill_commander_unit:
        lib.om_unit_set_hp(w, 1, 0.0)
    lib.om_mission_end(w)
    lib.om_chapter_set_phase(w, BRIEFING)
    d = OMDebrief()
    assert lib.om_mission_get_debrief(w, ctypes.byref(d)) == 1
    return region, d.band, d.commander_fate


def test_R_061_04_commander_death_records_the_mission_region_and_band(lib, world_factory):
    w = _campaign(lib, world_factory)
    cmd = lib.om_campaign_commander(w)
    assert cmd != 0
    region, band, fate = _mission(lib, w, kill_commander_unit=True)
    assert fate == FATE_KILLED
    assert region != 0, "fixture: region 0 is indistinguishable from an empty ledger entry"
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_ledger_commander_death_region(w, cmd) == region
    assert lib.om_ledger_commander_death_outcome_band(w, cmd) == band


def test_R_061_04_the_dead_commanders_character_is_no_longer_living(lib, world_factory):
    w = _campaign(lib, world_factory)
    cmd = lib.om_campaign_commander(w)
    _mission(lib, w, kill_commander_unit=True)
    assert lib.om_time_jump_run(w, 50) == 0
    rec = OmCharacterRecord()
    assert lib.om_character_get_record(w, cmd, ctypes.byref(rec)) == 0
    assert rec.status == GEN_STATUS_HISTORICAL


def test_R_061_04_control_a_surviving_commander_leaves_no_death_entry(lib, world_factory):
    w = _campaign(lib, world_factory)
    cmd = lib.om_campaign_commander(w)
    region, band, fate = _mission(lib, w, kill_commander_unit=False)
    assert fate == FATE_SURVIVED
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_ledger_commander_death_region(w, cmd) == 0
    assert lib.om_ledger_commander_death_outcome_band(w, cmd) == 0
