"""B6 core: the chapter lifecycle (R-055-06), the first commander (R-057-09), the selector
orchestrator (R-055-04, R-061-01) and the lineage categorisation (R-067-02).

Rulings: docs/northstar/plans/2026-10-01-architect-rulings-2.md section 1 and Addendum A1,
Addendum 6 A14 (end reason per jump), A15 (collapse reassigns at the jump), A17 (lineage chapter
counter).

What runs at the end of which jump (R-055-06, ruling 1.2, A15):

    opening jump          generator, selector            (no collapse check, no advance)
    jump after a mission  collapse check, [reassign the player faction when it fired, or stop
                          at the terminal path when no faction survives], generator, selector,
                          chapter advance
    retry jump            generator only

"After a mission" is one marker, read once at the start of the jump: the last mission has a
known band and its consequence is not consumed yet (om_chronicle_has_mission_consequence_flag).
A refused mission arms it exactly like a played one.

Why core: the pipe cannot reach the commander-death path (the commander fate is B7, never
`killed` over the pipe yet) and cannot kill a lineage or empty a faction on demand. The
fixture mirrors what the pipe does: generate, launch events, launch mission library,
om_campaign_start(w, 1) (the opening jump), om_mission_start/setup/end for a played mission,
om_time_jump_run for each jump.

Fixtures, not thresholds: the world seed (7) and the 80 regions.

RED today: om_campaign_commander, om_campaign_lineage, om_chapter_last_end_reason,
om_mission_generator_chosen_archetype and om_lineage_chapter_count are declared in
csrc/ouroboros_sim.h (B6-contract2, B6-contract3) but undefined, so each test that calls one
fails with an undefined symbol (an AttributeError on the library, which counts as red) until
the lifecycle is implemented. The A15 tests are red on the undefined
symbol today too (their mission helper reads the chosen archetype); on the reference patch
without A15 they are red on behaviour (no reassignment, no terminal flag).
"""
import ctypes

import pytest

from conftest import (OmChronicleCluster, OmCharacterRecord, OmSelectionRecord, OMTier,
                      set_region)

FEATURES = list(range(8))
GEN_STATUS_ACTIVE = 0
GEN_RANK_LINEAGE_MEMBER = 3
BRIEFING = 0
PLAYER = 0
SEED = 7
END_NORMAL, END_COMMANDER_DEATH, END_FACTION_COLLAPSED = 0, 1, 2
FATE_KILLED = 0
CAT_LINEAGE_THRIVED, CAT_LINEAGE_SUFFERED, CAT_LINEAGE_QUIET = 2, 3, 4
MEMBER_BASE = 900
CLUSTER_LINEAGE = 1
MAX = 2 ** 32 - 1


def _campaign(lib, world_factory, seed=SEED, features=FEATURES, before_start=None):
    w = world_factory(n_regions=80, seed=seed)
    for f in range(9):
        lib.om_world_set_feature(w, f, 1 if f in features else 0)
    lib.om_world_generate(w)
    assert lib.om_world_generated(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    if before_start:
        before_start(w)
    lib.om_campaign_start(w, 1)
    return w


def _player_regions(lib, w):
    return [i for i in range(lib.om_region_count(w)) if lib.om_region_owner(w, i) == PLAYER]


def _play_mission(lib, w, faction=PLAYER):
    """What handle_mission_start then handle_mission_end do, minus the pipe frames."""
    lib.om_mission_start(w, faction)
    lib.om_mission_setup(w, lib.om_mission_generator_chosen_region(w), max(lib.om_mission_generator_chosen_archetype(w), 0), 0)
    lib.om_mission_end(w)
    lib.om_chapter_set_phase(w, BRIEFING)


def _refuse_mission(lib, w):
    lib.om_mission_start(w, PLAYER)
    lib.om_mission_resolve_refusal(w, _player_regions(lib, w)[0])
    lib.om_chapter_set_phase(w, BRIEFING)


def _play_mission_commander_killed(lib, w):
    lib.om_mission_start(w, PLAYER)
    lib.om_mission_setup(w, lib.om_mission_generator_chosen_region(w), lib.om_mission_generator_chosen_archetype(w), 0)
    assert lib.om_mission_get_force_count(w) >= 1, "fixture: the mission needs a player unit to lose"
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_unit_set_hp(w, 1, 0.0)
    lib.om_mission_end(w)
    lib.om_chapter_set_phase(w, BRIEFING)


def _record(lib, w, cid):
    rec = OmCharacterRecord()
    assert lib.om_character_get_record(w, cid, ctypes.byref(rec)) == 0
    return rec


def _lineage_members(lib, w, lineage):
    ids = [lib.om_character_id_at(w, i) for i in range(lib.om_character_count(w))]
    return [c for c in ids if lib.om_character_lineage_id(w, c) == lineage]


def _kill_lineage(lib, w, lineage):
    tick = lib.om_world_strategic_tick(w)
    for c in _lineage_members(lib, w, lineage):
        lib.om_character_kill(w, c, tick)


def _seat_members_everywhere(lib, w, lineage):
    """A living member of `lineage` in every region, so one is always within the selector's
    proximity of whichever region the generator picks and a stay is never a forced rotation."""
    for i in range(lib.om_region_count(w)):
        lib.om_character_create(w, MEMBER_BASE + i, lineage, i, GEN_RANK_LINEAGE_MEMBER, 0, 10_000_000)


def _empty_player_faction(lib, w):
    for i in _player_regions(lib, w):
        lib.om_region_set_owner(w, i, -1, -1)


def _lineage_chapters(lib, w, lineage, region):
    rec = OmSelectionRecord()
    lib.om_character_selector_run_for_lineage(w, lineage_id=lineage, mission_region=region, out_record=ctypes.byref(rec))
    return rec


def _lineage_clusters(lib, w):
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        lib.om_chronicle_get_cluster(w, i, ctypes.byref(c))
        if c.type == CLUSTER_LINEAGE:
            out.append(c)
    return out


# ---- the opening jump (R-055-06, R-057-09) ----

def test_R_055_06_opening_jump_is_chapter_one_and_ends_no_chapter(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_chapter_get_number(w) == 1
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL


def test_R_057_09_opening_jump_seats_the_first_commander_in_a_new_lineage(lib, world_factory):
    w = _campaign(lib, world_factory)
    commander, lineage = lib.om_campaign_commander(w), lib.om_campaign_lineage(w)
    assert commander != 0, "the selector must seat a commander at the end of the opening jump"
    assert lineage != 0
    rec = _record(lib, w, commander)
    assert rec.status == GEN_STATUS_ACTIVE
    assert rec.lineage_id == lineage
    region = lib.om_mission_generator_chosen_region(w)
    assert rec.region == region, "the first commander is created in the mission region (R-058-04)"
    assert rec.faction == lib.om_region_owner(w, region), "in the mission region's owning faction"
    assert lib.om_lineage_count(w) >= 1


def test_R_057_09_the_first_selection_leaves_exactly_one_lineage(lib, world_factory):
    """The unrelated pool mints a lineage for the character it creates and the rotation mints
    another for the record; only the one the commander belongs to may survive, or the next
    chronicle carries a second, memberless lineage cluster."""
    w = _campaign(lib, world_factory)
    assert lib.om_lineage_count(w) == 1
    assert lib.om_lineage_id_at(w, 0) == lib.om_campaign_lineage(w)


def test_R_057_09_the_first_lineage_chapter_counter_starts_at_one(lib, world_factory):
    w = _campaign(lib, world_factory)
    lineage = lib.om_campaign_lineage(w)
    rec = _lineage_chapters(lib, w, lineage, lib.om_mission_generator_chosen_region(w))
    assert lineage != 0
    assert rec.chapters_in_lineage == 1


def test_R_055_06_the_opening_jump_runs_no_collapse_check(lib, world_factory):
    """Control for the collapse tests below: the player holds nothing when the opening jump
    runs, and the jump still ends no chapter (reason normal, chapter 1)."""
    w = _campaign(lib, world_factory, before_start=lambda w: _empty_player_faction(lib, w))
    assert _player_regions(lib, w) == []
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_chapter_get_number(w) == 1


def test_R_055_04_the_selector_reads_the_region_the_generator_chose(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_campaign_commander(w) != 0, "the selector must have run in the opening jump"
    assert lib.om_character_selector_input_region(w) == lib.om_mission_generator_chosen_region(w)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_character_selector_input_region(w) == lib.om_mission_generator_chosen_region(w)


# ---- the generator owns the draw (ruling 1.4) ----

def test_R_072_05_generator_stores_the_archetype_it_drew_with_the_region(lib, world_factory):
    w = _campaign(lib, world_factory)
    n = lib.om_mission_candidates(w, None, MAX)
    assert n > 0, "fixture: seed %d must leave candidates after the opening jump" % SEED
    assert 0 <= lib.om_mission_generator_chosen_archetype(w) < lib.om_mission_archetype_count(w)


def test_R_072_07_control_generator_reports_minus_one_when_it_found_no_candidate(lib, world_factory):
    """No feature runs, so no trigger fires anywhere and the pool is empty."""
    w = _campaign(lib, world_factory, features=[])
    assert lib.om_mission_candidates(w, None, MAX) == 0, "fixture: the featureless world must have no candidates"
    assert lib.om_mission_generator_chosen_archetype(w) == -1


def test_R_055_06_a_retry_jump_runs_the_generator_again(lib, world_factory):
    """The generator draw happens in every jump (ruling 1.4): after a retry jump the stored
    archetype agrees with the pool the generator saw, not with the opening jump's."""
    w = _campaign(lib, world_factory)
    first = lib.om_mission_generator_chosen_archetype(w)
    seen = {first}
    for _ in range(6):
        assert lib.om_time_jump_run(w, 20) == 0
        n = lib.om_mission_candidates(w, None, MAX)
        a = lib.om_mission_generator_chosen_archetype(w)
        assert (a == -1) == (n == 0), "stored archetype out of step with the pool after a retry jump"
        seen.add(a)
    assert len(seen) >= 2, "six retry jumps never redrew: the generator is not run in the jump"


# ---- the table (ruling 1.2) ----

def test_R_055_06_jump_without_a_mission_does_not_advance(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 1


def test_R_055_06_jump_after_a_mission_advances_once_and_a_retry_does_not(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_chapter_get_number(w) == 1, "the mission itself does not advance the chapter"
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2, "a retry jump with no mission never advances"


def test_R_055_06_control_second_mission_advances_again(lib, world_factory):
    w = _campaign(lib, world_factory)
    for expected in (2, 3):
        _play_mission(lib, w)
        assert lib.om_time_jump_run(w, 50) == 0
        assert lib.om_chapter_get_number(w) == expected


def test_R_055_06_a_refused_mission_arms_the_advance_like_a_played_one(lib, world_factory):
    w = _campaign(lib, world_factory)
    _refuse_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_get_number(w) == 2


def test_R_055_04_commander_with_a_living_lineage_stays(lib, world_factory):
    """Control for the rotation test: same flow, the lineage has a living member in every
    region and nobody dies, so the player stays (fewer than 2 chapters played, R-057-02)."""
    w = _campaign(lib, world_factory)
    lineage = lib.om_campaign_lineage(w)
    _seat_members_everywhere(lib, w, lineage)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    commander = lib.om_campaign_commander(w)
    assert commander != 0
    assert lib.om_campaign_lineage(w) == lineage
    assert lib.om_character_lineage_id(w, commander) == lineage
    assert _record(lib, w, commander).status == GEN_STATUS_ACTIVE


def test_R_057_01_lineage_with_no_living_member_rotates_at_the_post_mission_jump(lib, world_factory):
    w = _campaign(lib, world_factory)
    first, lineage = lib.om_campaign_commander(w), lib.om_campaign_lineage(w)
    _kill_lineage(lib, w, lineage)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    new = lib.om_campaign_commander(w)
    assert new not in (0, first), "the selector must rotate to a new commander"
    assert _record(lib, w, new).status == GEN_STATUS_ACTIVE
    assert lib.om_campaign_lineage(w) not in (0, lineage)
    assert lib.om_chapter_get_number(w) == 2


def test_R_055_06_a_retry_jump_does_not_run_the_selector(lib, world_factory):
    """Same dead lineage as the rotation test, but a jump with no mission before it: the
    selector must not run, so the dead commander stays the campaign's commander."""
    w = _campaign(lib, world_factory)
    first, lineage = lib.om_campaign_commander(w), lib.om_campaign_lineage(w)
    _kill_lineage(lib, w, lineage)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_commander(w) == first
    assert lib.om_campaign_lineage(w) == lineage


def test_R_055_06_the_marker_is_read_once_so_the_jump_after_next_is_a_retry(lib, world_factory):
    """After the post-mission jump consumed the consequence, a second jump is a retry jump:
    the dead lineage is not rotated by it."""
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    lineage = lib.om_campaign_lineage(w)
    commander = lib.om_campaign_commander(w)
    _kill_lineage(lib, w, lineage)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_commander(w) == commander
    assert lib.om_chapter_get_number(w) == 2


# ---- chapter end reason (ruling 1.6) ----

def test_R_062_01_collapse_is_checked_at_the_jump_after_a_mission(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    _empty_player_faction(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_FACTION_COLLAPSED
    assert lib.om_chapter_get_number(w) == 2, "a collapse ends the chapter, the number still advances"


def test_R_062_01_a_retry_jump_runs_no_collapse_check(lib, world_factory):
    w = _campaign(lib, world_factory)
    _empty_player_faction(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_chapter_get_number(w) == 1


def test_R_061_01_commander_killed_in_the_mission_ends_the_chapter_with_commander_death(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission_commander_killed(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_COMMANDER_DEATH
    assert lib.om_chapter_get_number(w) == 2


def test_R_061_01_commander_death_picks_a_living_lineage_member_as_successor(lib, world_factory):
    """The selector orchestrator calls the commander-death path when the last mission's
    commander fate was killed: with a lineage member in every region the successor is a
    living member of the same lineage, not a new lineage and not the dead commander."""
    w = _campaign(lib, world_factory)
    first, lineage = lib.om_campaign_commander(w), lib.om_campaign_lineage(w)
    _seat_members_everywhere(lib, w, lineage)
    _play_mission_commander_killed(lib, w)
    lib.om_character_kill(w, first, lib.om_world_strategic_tick(w))
    assert lib.om_time_jump_run(w, 50) == 0
    new = lib.om_campaign_commander(w)
    assert new not in (0, first)
    assert lib.om_campaign_lineage(w) == lineage
    assert _record(lib, w, new).status == GEN_STATUS_ACTIVE


def test_R_062_01_collapse_wins_over_commander_death(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission_commander_killed(lib, w)
    _empty_player_faction(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_FACTION_COLLAPSED


# ---- lineage categorisation (R-067-02, addendum A1) ----

def test_R_067_02_add_lineage_event_stores_the_category_it_is_given(lib, world_factory):
    for category in (CAT_LINEAGE_THRIVED, CAT_LINEAGE_SUFFERED):
        w = world_factory(n_regions=4)
        lib.om_lineage_create(w, lineage_id=1, home_region=0)
        lib.om_chronicle_add_lineage_event(w, lineage_id=1, region_idx=2, category=category, score=1.0)
        lib.om_chronicle_distill_and_assemble(w)
        clusters = [c for c in _lineage_clusters(lib, w) if c.region == 2]
        assert len(clusters) == 1
        assert clusters[0].category == category


def test_R_067_02_the_jump_categorises_a_lineage_cluster_from_net_values_not_end_values(lib, world_factory):
    """Net inputs are the region's fields at the jump's end minus at its start. Nothing runs
    during this jump (no feature), so the net is zero and the cluster is lineage_quiet, while
    the region's tension is 90 at the end: categorised from the end value alone it would be
    lineage_suffered (tension > 5)."""
    w = _campaign(lib, world_factory, features=[])
    lineage = lib.om_campaign_lineage(w)
    region = lib.om_lineage_history_region(w, lineage, 0)
    assert region >= 0
    set_region(lib, w, region, tier=OMTier.HOME, military=50.0, economy=50.0, tension=90.0,
               population=50.0, faction_id=lib.om_region_owner(w, region))
    assert lib.om_time_jump_run(w, 50) == 0
    mine = [c for c in _lineage_clusters(lib, w) if c.region == region]
    assert len(mine) == 1, "the lineage's region has no lineage cluster"
    assert mine[0].category == CAT_LINEAGE_QUIET


def test_R_067_02_control_categorise_lineage_cluster_reads_the_thresholds_the_jump_relies_on(lib, world_factory):
    w = world_factory(n_regions=2)
    assert lib.om_chronicle_categorize_lineage_cluster(w, template_name=b"", net_eco=0.0, net_mil=0.0, net_ten=90.0) == CAT_LINEAGE_SUFFERED
    assert lib.om_chronicle_categorize_lineage_cluster(w, template_name=b"", net_eco=0.0, net_mil=0.0, net_ten=0.0) == CAT_LINEAGE_QUIET


# ---- determinism ----

def test_R_055_06_lifecycle_world_is_deterministic(lib, world_factory):
    def trace():
        w = _campaign(lib, world_factory)
        _kill_lineage(lib, w, lib.om_campaign_lineage(w))
        _play_mission(lib, w)
        lib.om_time_jump_run(w, 50)
        return (lib.om_campaign_commander(w), lib.om_campaign_lineage(w), lib.om_chapter_get_number(w),
                lib.om_mission_generator_chosen_region(w), lib.om_mission_generator_chosen_archetype(w),
                lib.om_world_get_state_checksum(w))

    first, second = trace(), trace()
    assert first[0] != 0, "no commander after the jump: the lifecycle is not wired"
    assert first == second


# ---- A14: the end reason is per jump ----

def test_R_055_06_a_retry_jump_after_a_collapse_jump_reads_normal_while_the_collapse_jump_read_collapsed(lib, world_factory):
    """The two readings of the getter differ: `om_chapter_last_end_reason` is what the
    latest jump's frame carried, not the reason of the chapter that last ended. The jump
    that ended the chapter by collapse reads 2; the retry jump after it ended no chapter
    and reads 0."""
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    _empty_player_faction(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_FACTION_COLLAPSED
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_chapter_get_number(w) == 2


# ---- A15: collapse reassigns at the jump, before the generator ----

def _survivor_counts(lib, w, collapsed):
    counts = {}
    for i in range(lib.om_region_count(w)):
        f = lib.om_region_owner(w, i)
        if f >= 0 and f != collapsed:
            counts[f] = counts.get(f, 0) + 1
    return counts


def _collapse_jump(lib, w):
    _play_mission(lib, w)
    _empty_player_faction(lib, w)
    assert _survivor_counts(lib, w, PLAYER), "fixture: another faction must survive the collapse"
    assert lib.om_player_faction_check_collapse(w, PLAYER) == 1
    assert lib.om_time_jump_run(w, 50) == 0


def test_R_062_02_collapse_jump_reassigns_the_player_faction_to_a_surviving_faction(lib, world_factory):
    """The reassignment is the code's current choice (most regions, Q-062-01 stays open on
    which faction): the new player faction is the survivor holding the most regions at the
    collapse check, not the collapsed faction. The check runs at the end of the jump and
    nothing after it moves an owner, so the world's owners after the jump are the owners the
    reassignment saw."""
    w = _campaign(lib, world_factory)
    assert lib.om_player_faction(w) == PLAYER
    _collapse_jump(lib, w)
    assert lib.om_chapter_last_end_reason(w) == END_FACTION_COLLAPSED
    new = lib.om_player_faction(w)
    assert new >= 0 and new != PLAYER, "the player faction was not reassigned in the collapse jump"
    counts = _survivor_counts(lib, w, PLAYER)
    assert new in counts, "reassigned to a faction that holds nothing"
    assert counts[new] == max(counts.values())
    assert lib.om_campaign_needs_onboarding(w) == 0, "a survivor exists: not the terminal path"


def test_R_062_02_the_generator_runs_in_the_collapse_jump_after_the_reassignment(lib, world_factory):
    """The generator needs a player faction that holds regions, so it runs after the
    reassignment in the same jump: the pool it built is the pool the world has now, the
    selector read what it chose, and the chapter advanced."""
    w = _campaign(lib, world_factory)
    _collapse_jump(lib, w)
    n = lib.om_mission_candidates(w, None, MAX)
    a = lib.om_mission_generator_chosen_archetype(w)
    assert (a == -1) == (n == 0), "stored archetype out of step with the pool: the generator did not run in the collapse jump"
    assert lib.om_character_selector_input_region(w) == lib.om_mission_generator_chosen_region(w)
    assert lib.om_campaign_commander(w) != 0
    assert lib.om_chapter_get_number(w) == 2


def test_R_062_02_the_reassignment_does_not_fire_again_on_the_next_jump(lib, world_factory):
    """Replaces the assumption that the collapse check fires again until something
    reassigns: the reassignment happened once, the next post-mission jump finds a player
    faction that holds regions, ends a normal chapter and keeps the same player faction."""
    w = _campaign(lib, world_factory)
    _collapse_jump(lib, w)
    new = lib.om_player_faction(w)
    assert new != PLAYER
    _play_mission(lib, w, faction=new)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_player_faction(w) == new
    assert lib.om_chapter_get_number(w) == 3


def test_R_062_02_control_without_a_collapse_the_player_faction_is_not_reassigned(lib, world_factory):
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_chapter_last_end_reason(w) == END_NORMAL
    assert lib.om_player_faction(w) == PLAYER


def _empty_every_region(lib, w):
    for i in range(lib.om_region_count(w)):
        lib.om_region_set_owner(w, i, -1, -1)


def test_R_062_03_no_surviving_faction_stops_the_jump_at_the_terminal_path(lib, world_factory):
    """Nothing holds a region at the collapse check: no generator, no selector, no chapter
    advance, and om_campaign_trigger_terminal_restart is taken (observable as
    om_campaign_needs_onboarding, which it sets). The generator and selector outputs are
    unchanged by the jump: the stored region and archetype, the selector's input region, the
    commander and the lineage. (A generator that ran with every region unowned could
    in principle redraw the same values, so the unchanged outputs alone are weak evidence; the
    needs-onboarding flag and the missing advance are the firm half.)"""
    w = _campaign(lib, world_factory)
    _play_mission(lib, w)
    _empty_every_region(lib, w)
    assert lib.om_campaign_check_surviving_factions(w) == 1, "fixture: no faction must survive"
    assert lib.om_campaign_needs_onboarding(w) == 0
    before = (lib.om_mission_generator_chosen_region(w), lib.om_mission_generator_chosen_archetype(w),
              lib.om_character_selector_input_region(w), lib.om_campaign_commander(w),
              lib.om_campaign_lineage(w))
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_needs_onboarding(w) == 1, "the terminal path was not taken"
    after = (lib.om_mission_generator_chosen_region(w), lib.om_mission_generator_chosen_archetype(w),
             lib.om_character_selector_input_region(w), lib.om_campaign_commander(w),
             lib.om_campaign_lineage(w))
    assert after == before, "the generator or the selector ran after the check found no survivor"
    assert lib.om_chapter_get_number(w) == 1, "no chapter advance on the terminal path"


# ---- A17: the lineage chapter counter ----

def test_R_057_08_a_new_lineage_starts_at_one_chapter(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_lineage_chapter_count(w, lib.om_campaign_lineage(w)) == 1


def test_R_057_08_control_an_unknown_lineage_has_no_chapters(lib, world_factory):
    w = _campaign(lib, world_factory)
    assert lib.om_lineage_chapter_count(w, 4_000_000) == 0


def test_R_057_08_a_stay_adds_one_chapter_to_the_lineage(lib, world_factory):
    w = _campaign(lib, world_factory)
    lineage = lib.om_campaign_lineage(w)
    _seat_members_everywhere(lib, w, lineage)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_lineage(w) == lineage, "fixture: this flow must be a stay"
    assert lib.om_lineage_chapter_count(w, lineage) == 2


def test_R_057_08_a_rotation_gives_the_new_lineage_one_and_leaves_the_old_count(lib, world_factory):
    w = _campaign(lib, world_factory)
    old = lib.om_campaign_lineage(w)
    old_count = lib.om_lineage_chapter_count(w, old)
    _kill_lineage(lib, w, old)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    new = lib.om_campaign_lineage(w)
    assert new not in (0, old), "fixture: this flow must be a rotation"
    assert lib.om_lineage_chapter_count(w, new) == 1
    assert lib.om_lineage_chapter_count(w, old) == old_count


def test_R_057_08_a_retry_jump_changes_no_lineage_count(lib, world_factory):
    w = _campaign(lib, world_factory)
    old = lib.om_campaign_lineage(w)
    _seat_members_everywhere(lib, w, old)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    count = lib.om_lineage_chapter_count(w, old)
    lineages = {lib.om_lineage_id_at(w, i): lib.om_lineage_chapter_count(w, lib.om_lineage_id_at(w, i))
                for i in range(lib.om_lineage_count(w))}
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_lineage_chapter_count(w, old) == count == 2
    assert lineages == {lib.om_lineage_id_at(w, i): lib.om_lineage_chapter_count(w, lib.om_lineage_id_at(w, i))
                        for i in range(lib.om_lineage_count(w))}


def test_R_057_08_a_retry_jump_after_a_rotation_leaves_the_new_lineage_at_one(lib, world_factory):
    w = _campaign(lib, world_factory)
    old = lib.om_campaign_lineage(w)
    _kill_lineage(lib, w, old)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 50) == 0
    new = lib.om_campaign_lineage(w)
    assert new not in (0, old)
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_lineage_chapter_count(w, new) == 1


def test_R_061_02_a_successor_after_the_commanders_death_adds_one_chapter_to_the_kept_lineage(lib, world_factory):
    w = _campaign(lib, world_factory)
    first, lineage = lib.om_campaign_commander(w), lib.om_campaign_lineage(w)
    _seat_members_everywhere(lib, w, lineage)
    _play_mission_commander_killed(lib, w)
    lib.om_character_kill(w, first, lib.om_world_strategic_tick(w))
    assert lib.om_time_jump_run(w, 50) == 0
    assert lib.om_campaign_lineage(w) == lineage, "fixture: the successor must keep the lineage"
    assert lib.om_campaign_commander(w) not in (0, first)
    assert lib.om_lineage_chapter_count(w, lineage) == 2
