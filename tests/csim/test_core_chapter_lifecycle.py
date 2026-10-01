"""B6 core: the chapter lifecycle (R-055-06) and the rotation path (R-055-04).

Why this is a core test: a pipe campaign has no way to lose a lineage. Seeds 1 to 400
were scanned (world, opening jump, three 50-tick jumps): om_character_count and
om_lineage_count are 0 for every one, because no production code creates a
lineage or a character outside the tests. The architect rulings (B6 item 4) say a
core test through the public functions handle_jump calls proves the rotation path
when no seed does.

The fixture mirrors what the pipe does: handle_set_seed (generate, launch events,
launch mission library, om_campaign_start(w, 1)), handle_mission_start/end
(om_mission_start, om_mission_setup, om_mission_end, phase back to BRIEFING) and
handle_jump (om_time_jump_run). The one piece the fixture has to assume: the lineage
the selector reads is the one the confirmed commander belongs to
(om_character_selector_confirm_commander, then om_campaign_commander); see the
ambiguity list in the B6-tests report.

RED until om_campaign_commander exists and the chapter lifecycle is wired into the
jump: the symbol is declared in csrc/ouroboros_sim.h (B6-contract) but undefined.
"""
import ctypes

import pytest

from conftest import OmCharacterRecord

FEATURES = list(range(8))
GEN_RANK_LINEAGE_MEMBER = 3
GEN_STATUS_ACTIVE = 0
BRIEFING = 0
PLAYER = 0
SEED = 7
LINEAGE = 7
FIRST_COMMANDER = 701
LINEAGE_MEMBER_BASE = 800


def _campaign(lib, world_factory, seed=SEED):
    w = world_factory(n_regions=80, seed=seed)
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    assert lib.om_world_generated(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    lib.om_campaign_start(w, 1)
    return w


def _player_region(lib, w):
    for i in range(lib.om_region_count(w)):
        if lib.om_region_owner(w, i) == PLAYER:
            return i
    pytest.fail("player owns no region after generation")


def _seat_commander(lib, w):
    """One lineage with a living member in every region (so one is always within the
    selector's proximity of whichever region the generator picks, and a stay is never
    a forced rotation), the first of them confirmed as the commander."""
    region = _player_region(lib, w)
    lib.om_lineage_create(w, LINEAGE, region)
    lib.om_character_create(w, FIRST_COMMANDER, LINEAGE, region, GEN_RANK_LINEAGE_MEMBER, 0, 10_000_000)
    for i in range(lib.om_region_count(w)):
        lib.om_character_create(w, LINEAGE_MEMBER_BASE + i, LINEAGE, i, GEN_RANK_LINEAGE_MEMBER, 0, 10_000_000)
    lib.om_character_selector_confirm_commander(w, FIRST_COMMANDER)


def _kill_lineage(lib, w):
    tick = lib.om_world_strategic_tick(w)
    lib.om_character_kill(w, FIRST_COMMANDER, tick)
    for i in range(lib.om_region_count(w)):
        lib.om_character_kill(w, LINEAGE_MEMBER_BASE + i, tick)


def _play_mission(lib, w):
    """What handle_mission_start then handle_mission_end do, minus the pipe frames."""
    region = _player_region(lib, w)
    lib.om_mission_start(w, PLAYER)
    lib.om_mission_setup(w, region, 0, 0)
    lib.om_mission_end(w)
    lib.om_chapter_set_phase(w, BRIEFING)


def _record(lib, w, cid):
    rec = OmCharacterRecord()
    assert lib.om_character_get_record(w, cid, ctypes.byref(rec)) == 0
    return rec


def test_R_055_06_opening_jump_is_chapter_one(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_chapter_get_number(w) == 1


def test_R_055_06_jump_without_a_mission_does_not_advance(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 1


def test_R_055_06_jump_after_a_mission_advances_once(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_chapter_get_number(w) == 1, "the mission itself does not advance the chapter"
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2, "a retry jump with no mission never advances"


def test_R_055_06_control_second_mission_advances_again(lib, world_factory):
    w = _campaign(lib, world_factory)
    for expected in (2, 3):
        _play_mission(lib, w)
        assert lib.om_time_jump_run(w, 50) == 0
        assert lib.om_chapter_get_number(w) == expected


def test_R_055_04_commander_with_a_living_lineage_does_not_rotate(lib, world_factory):
    """Control for the rotation test: same fixture, nobody dies, the commander is still
    a living member of the same lineage (the selector may pick another member of it)."""
    w = _campaign(lib, world_factory)
    _seat_commander(lib, w)
    assert lib.om_campaign_commander(w) == FIRST_COMMANDER
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2
    commander = lib.om_campaign_commander(w)
    assert commander != 0
    assert lib.om_character_lineage_id(w, commander) == LINEAGE
    assert _record(lib, w, commander).status == GEN_STATUS_ACTIVE


def test_R_055_04_lineage_with_no_living_member_rotates_at_the_jump(lib, world_factory):
    w = _campaign(lib, world_factory)
    _seat_commander(lib, w)
    assert lib.om_campaign_commander(w) == FIRST_COMMANDER
    _kill_lineage(lib, w)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    new = lib.om_campaign_commander(w)
    assert new not in (0, FIRST_COMMANDER), "the selector must rotate to a new commander"
    rec = _record(lib, w, new)
    assert rec.status == GEN_STATUS_ACTIVE
    assert rec.lineage_id != LINEAGE
    assert lib.om_chapter_get_number(w) == 2


def test_R_055_04_selector_reads_the_region_the_generator_chose(lib, world_factory):
    """R-055-04: the generator runs first and the selector reads its region; the
    jump leaves them agreeing."""
    w = _campaign(lib, world_factory)
    _seat_commander(lib, w)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_commander(w) != 0, "the selector must have run in this jump"
    assert lib.om_character_selector_input_region(w) == lib.om_mission_generator_chosen_region(w)


def test_R_055_06_rotation_world_is_deterministic(lib, world_factory):
    def trace():
        w = _campaign(lib, world_factory)
        _seat_commander(lib, w)
        _kill_lineage(lib, w)
        _play_mission(lib, w)
        lib.om_time_jump_run(w, 50)
        return (lib.om_campaign_commander(w), lib.om_chapter_get_number(w),
                lib.om_mission_generator_chosen_region(w), lib.om_world_get_state_checksum(w))

    first, second = trace(), trace()
    assert first[0] != 0, "no commander after the jump: the lifecycle is not wired"
    assert first == second
