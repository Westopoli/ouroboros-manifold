"""B5 (mission-plays plan): after a mission result is recorded, the time jump's
chronicle opens with the consequence entry (R-065-02: the consequence cluster
is entry 1, categorized success, failure or mixed by the mission outcome).

C-level: om_mission_end records the result, om_time_jump_run (gen_time_jump)
must turn it into the consequence cluster. The pipe jump is a different owner.
"""
import ctypes

from conftest import OMField, OMTier, OmChronicleCluster, OmChronicleEntry, set_owner, set_region


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

MISSION_REGION = 2
DEFENSIVE_STAND = 0
BAND_PARTIAL_FAILURE = 1  # Defensive Stand with retention fixed at 1.0 bottoms out here: final 0.25
BAND_TOTAL_SUCCESS = 4


def _world(lib, world_factory):
    w = world_factory(n_regions=4, seed=7)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _play_mission(lib, w, completion):
    lib.om_mission_setup(w, MISSION_REGION, DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, DEFENSIVE_STAND)
    lib.om_mission_set_objective_completion(w, 0, completion)
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


def test_R_065_02_entry_one_is_the_consequence_after_a_failed_mission(lib, world_factory):
    """Given a mission that ended in partial failure (every objective at 0, the lowest band this archetype can reach), When a time jump runs, Then entry 1 is the consequence cluster, category failure."""
    w = _world(lib, world_factory)
    _play_mission(lib, w, 0.0)
    assert lib.om_mission_get_band(w) == BAND_PARTIAL_FAILURE

    assert lib.om_time_jump_run(w, 30, None) == 0

    scroll = _scroll(lib, w)
    assert scroll, "jump produced no chronicle entries"
    cluster, entry = scroll[0]
    assert cluster.type == OMClusterType.CONSEQUENCE
    assert cluster.category == OMOutcomeCategory.FAILURE
    assert cluster.region == MISSION_REGION
    assert entry is not None
    assert entry.category == CAT_CONSEQUENCE_FAILURE


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
