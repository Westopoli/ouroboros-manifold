"""B5 (mission-plays plan): after a mission result is recorded, the time jump's
chronicle opens with the consequence entry (R-065-02: the consequence cluster
is entry 1, categorized success, failure or mixed by the mission outcome).

C-level: om_mission_end records the result, om_time_jump_run (gen_time_jump)
must turn it into the consequence cluster. The pipe jump is a different owner.
"""
import ctypes

from conftest import (
    OMField,
    OMTier,
    OmChronicleCluster,
    OmChronicleEntry,
    load_launch_events,
    queue_external,
    region_neighbors,
    set_edge,
    set_owner,
    set_region,
    template_id,
)


class OMClusterType:
    CONSEQUENCE = 0
    LINEAGE = 1
    CHAIN = 2
    REGIONAL = 3


class OMOutcomeCategory:
    SUCCESS = 0
    FAILURE = 1
    MIXED = 2


CAT_CONSEQUENCE_SUCCESS = 30
CAT_CONSEQUENCE_FAILURE = 31
CAT_CONSEQUENCE_MIXED = 32

MISSION_REGION = 2
DEFENSIVE_STAND = 0
EVACUATION = 7
BAND_TOTAL_FAILURE = 0  # Evacuation (first threshold 0.30) with retention fixed at 1.0 and completion 0: final 0.25
BAND_PARTIAL_FAILURE = 1  # Defensive Stand with retention fixed at 1.0 bottoms out here: final 0.25
BAND_PARTIAL_SUCCESS = 2
BAND_STRONG_SUCCESS = 3
BAND_TOTAL_SUCCESS = 4
BAND_REFUSAL = 5


def _world(lib, world_factory):
    w = world_factory(n_regions=4, seed=7)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _play_mission(lib, w, completion, archetype=DEFENSIVE_STAND):
    lib.om_mission_setup(w, MISSION_REGION, archetype, 0)
    lib.om_mission_build_objectives(w, archetype)
    for i in range(lib.om_mission_objective_count(w)):
        lib.om_mission_set_objective_completion(w, i, completion)
    lib.om_mission_end(w)


def _scroll(lib, w):
    """(cluster, entry-or-None) per scroll entry; entry_get can fail for entries the assembler left unrendered, which is not this file's concern."""
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        e = OmChronicleEntry()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        out.append((c, e if lib.om_chronicle_entry_get(w, i, ctypes.byref(e)) == 1 else None))
    return out


def test_R_065_02_entry_one_is_the_consequence_after_a_successful_mission(lib, world_factory):
    """Given a mission that ended in total success, When a time jump runs, Then entry 1 is the consequence cluster, category success, in the mission's region."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 1.0)
    assert lib.om_mission_get_band(w) == BAND_TOTAL_SUCCESS  # fixture check: the mission result really is recorded

    assert lib.om_time_jump_run(w, 30, None) == 0

    scroll = _scroll(lib, w)
    assert scroll, "jump produced no chronicle entries"
    cluster, entry = scroll[0]
    assert cluster.type == OMClusterType.CONSEQUENCE
    assert cluster.category == OMOutcomeCategory.SUCCESS
    # A zeroed struct would match type 0 / category 0 with no cluster built.
    assert cluster.region == MISSION_REGION
    assert entry is not None
    assert entry.category == CAT_CONSEQUENCE_SUCCESS
    assert entry.region == MISSION_REGION
    assert entry.base_text != b""


def _entry_one_after(lib, w, expected_cluster_category, expected_entry_category):
    assert lib.om_time_jump_run(w, 30, None) == 0
    scroll = _scroll(lib, w)
    assert scroll, "jump produced no chronicle entries"
    cluster, entry = scroll[0]
    assert cluster.type == OMClusterType.CONSEQUENCE
    assert cluster.category == expected_cluster_category
    assert cluster.region == MISSION_REGION
    assert entry is not None
    assert entry.category == expected_entry_category


def test_R_065_02_total_success_band_gives_success(lib, world_factory):
    """Given a mission banded total_success, When a time jump runs, Then entry 1 is the consequence cluster, category success (B5-1)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 1.0)
    assert lib.om_mission_get_band(w) == BAND_TOTAL_SUCCESS
    _entry_one_after(lib, w, OMOutcomeCategory.SUCCESS, CAT_CONSEQUENCE_SUCCESS)


def test_R_065_02_strong_success_band_gives_success(lib, world_factory):
    """Given a mission banded strong_success (Defensive Stand, completion 0.6: final 0.7), When a time jump runs, Then entry 1 is the consequence cluster, category success (B5-1)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 0.6)
    assert lib.om_mission_get_band(w) == BAND_STRONG_SUCCESS
    _entry_one_after(lib, w, OMOutcomeCategory.SUCCESS, CAT_CONSEQUENCE_SUCCESS)


def test_R_065_02_partial_success_band_gives_mixed(lib, world_factory):
    """Given a mission banded partial_success (Defensive Stand, completion 0.4: final 0.55), When a time jump runs, Then entry 1 is the consequence cluster, category mixed (B5-1)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 0.4)
    assert lib.om_mission_get_band(w) == BAND_PARTIAL_SUCCESS
    _entry_one_after(lib, w, OMOutcomeCategory.MIXED, CAT_CONSEQUENCE_MIXED)


def test_R_065_02_partial_failure_band_gives_mixed(lib, world_factory):
    """Given a mission banded partial_failure (every objective at 0, the lowest band Defensive Stand can reach), When a time jump runs, Then entry 1 is the consequence cluster, category mixed (B5-1; was failure before the 2026-10-01 ruling)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 0.0)
    assert lib.om_mission_get_band(w) == BAND_PARTIAL_FAILURE
    _entry_one_after(lib, w, OMOutcomeCategory.MIXED, CAT_CONSEQUENCE_MIXED)


def test_R_065_02_total_failure_band_gives_failure(lib, world_factory):
    """Given a mission banded total_failure (Evacuation, every objective at 0: final 0.25 under its 0.30 first threshold), When a time jump runs, Then entry 1 is the consequence cluster, category failure (B5-1)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 0.0, EVACUATION)
    assert lib.om_mission_get_band(w) == BAND_TOTAL_FAILURE
    _entry_one_after(lib, w, OMOutcomeCategory.FAILURE, CAT_CONSEQUENCE_FAILURE)


def test_R_065_02_refusal_band_gives_failure(lib, world_factory):
    """Given a refused mission (band refusal), When a time jump runs, Then entry 1 is the consequence cluster, category failure, in the refused region (B5-1)."""
    w = _world(lib, world_factory)
    lib.om_mission_setup(w, MISSION_REGION, DEFENSIVE_STAND, 0)
    lib.om_mission_resolve_refusal(w, MISSION_REGION)
    assert lib.om_mission_get_band(w) == BAND_REFUSAL
    _entry_one_after(lib, w, OMOutcomeCategory.FAILURE, CAT_CONSEQUENCE_FAILURE)


def test_R_065_02_consequence_cluster_only_in_the_jump_after_the_mission(lib, world_factory):
    """Given a mission followed by one jump, When a second jump runs with no mission between, Then the second scroll has no consequence cluster (B5-3: the flag clears once the first scroll is built)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 1.0)
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert any(c.type == OMClusterType.CONSEQUENCE for c, _ in _scroll(lib, w))  # fixture check: first jump had one

    assert lib.om_time_jump_run(w, 30, None) == 0

    scroll = _scroll(lib, w)
    assert scroll, "second jump produced no chronicle entries"
    assert all(c.type != OMClusterType.CONSEQUENCE for c, _ in scroll)
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0


def _ripples(lib, w):
    return [
        (c, e) for c, e in _scroll(lib, w)
        if e is not None and ctypes.string_at(lib.om_chronicle_category_name(e.category)) == b"consequence_ripple"
    ]


def _ripple_world(lib, world_factory, adjacent=True):
    """Mission region 2 neighbours region 1 only (nothing when adjacent is False); a Border Incursion queued in region 1 fires during the jump."""
    w = _world(lib, world_factory)
    # The sim has two adjacency stores (region_edge graph behind om_region_neighbors,
    # and the mission.c neighbors[] list); feed both so the test does not pick one.
    if adjacent:
        set_edge(lib, w, MISSION_REGION, 1)
        lib.om_set_neighbors(w, MISSION_REGION, 1)
    load_launch_events(lib, w)
    tid = template_id(lib, w, "Border Incursion")
    assert queue_external(lib, w, 1, tid, due_tick=3, probability=1.0) > 0
    return w


def test_R_065_02_events_in_an_adjacent_region_make_a_ripple_cluster(lib, world_factory):
    """Given a mission in region 2 and an event firing in adjacent region 1 during the next jump, When the scroll is built, Then it has a consequence_ripple entry in region 1 (B5-4, Q-067-01)."""
    w = _ripple_world(lib, world_factory)
    _play_mission(lib, w, 1.0)

    assert lib.om_time_jump_run(w, 30, None) == 0

    ripples = _ripples(lib, w)
    assert ripples, "no consequence_ripple entry for an event in a region adjacent to the mission region"
    assert all(c.region == 1 for c, _ in ripples)


def test_control_R_065_02_same_event_with_no_adjacency_makes_no_ripple(lib, world_factory):
    """Control: the same event in region 1 with the mission region having no neighbours makes no consequence_ripple entry. Proves the ripple test above turns on adjacency, not on any event firing."""
    w = _ripple_world(lib, world_factory, adjacent=False)
    assert 1 not in region_neighbors(lib, w, MISSION_REGION)  # fixture check
    _play_mission(lib, w, 1.0)

    assert lib.om_time_jump_run(w, 30, None) == 0

    assert not _ripples(lib, w)


def test_R_065_02_no_ripple_without_a_mission(lib, world_factory):
    """Given an event firing in a region and no mission since the last jump, When the scroll is built, Then no consequence_ripple entry exists."""
    w = _ripple_world(lib, world_factory)

    assert lib.om_time_jump_run(w, 30, None) == 0

    assert not _ripples(lib, w)


def test_R_065_02_exactly_one_consequence_cluster_in_the_scroll(lib, world_factory):
    """Given one mission result, When a time jump runs, Then the scroll holds exactly one consequence cluster."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 1.0)
    assert lib.om_time_jump_run(w, 30, None) == 0

    n = sum(1 for c, _ in _scroll(lib, w) if c.type == OMClusterType.CONSEQUENCE and c.region == MISSION_REGION)
    assert n == 1


def test_R_065_02_no_mission_result_means_no_consequence_cluster(lib, world_factory):
    """Given no mission was played, When a time jump runs, Then no entry is a consequence cluster (the rule's input is events flagged as consequences of the last mission; there are none). Entry 1 is then whatever R-065-03..05 rank first, which the rule does not pin."""
    w = _world(lib, world_factory)
    assert lib.om_mission_get_band(w) == -1  # fixture check: no result recorded

    assert lib.om_time_jump_run(w, 30, None) == 0

    scroll = _scroll(lib, w)
    assert scroll, "jump produced no chronicle entries"
    assert all(c.type != OMClusterType.CONSEQUENCE for c, _ in scroll)


def test_control_R_065_02_direct_consequence_event_becomes_entry_one(lib, world_factory):
    """Positive control for the detector in this file: a consequence event added by hand (no jump) distills to entry 1 with the same cluster fields the tests above read. Proves _scroll() and the field checks can see a consequence cluster, so the jump tests' red is the jump's gap."""
    w = _world(lib, world_factory)
    lib.om_chronicle_add_consequence_event(w, MISSION_REGION, OMOutcomeCategory.FAILURE)
    lib.om_chronicle_distill_and_assemble(w)

    cluster, entry = _scroll(lib, w)[0]
    assert cluster.type == OMClusterType.CONSEQUENCE
    assert cluster.category == OMOutcomeCategory.FAILURE
    assert cluster.region == MISSION_REGION
    assert entry is not None
    assert entry.category == CAT_CONSEQUENCE_FAILURE
