"""B5 (architect rulings round 2, section 1.3 and 2): the one marker for 'a jump that follows
a mission' is exposed by om_chronicle_has_mission_consequence_flag (R-078-06): 1 while the last
mission has a known band and its consequence is not yet consumed, 0 otherwise. The consumed flag
is saved, so a save/load keeps the marker and never repeats a consequence.
"""
import ctypes

from conftest import OMTier, OmChronicleCluster, set_owner, set_region

CONSEQUENCE_CLUSTER = 0
MISSION_REGION = 2
DEFENSIVE_STAND = 0


def _world(lib, world_factory, seed=7):
    w = world_factory(n_regions=4, seed=seed)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _play_mission(lib, w, completion=1.0):
    lib.om_mission_setup(w, MISSION_REGION, DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, DEFENSIVE_STAND)
    for i in range(lib.om_mission_objective_count(w)):
        lib.om_mission_set_objective_completion(w, i, completion)
    lib.om_mission_end(w)


def _n_consequence_clusters(lib, w):
    n = 0
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        if c.type == CONSEQUENCE_CLUSTER:
            n += 1
    return n


def _bind_save(lib):
    if getattr(lib, "_b5f_save_bound", False):
        return
    V = ctypes.c_void_p
    P = ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib._b5f_save_bound = True


def _roundtrip(lib, world_factory, src, seed=8):
    _bind_save(lib)
    size = lib.om_save_state_size(src)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(src, buf, size)
    dst = world_factory(n_regions=4, seed=seed)
    assert lib.om_load_state_read(dst, buf, size) == 0
    return dst


def test_R_078_06_flag_is_set_once_a_mission_result_awaits_its_jump(lib, world_factory):
    """Given a mission whose result is recorded and no jump yet, Then the consequence flag reads 1."""
    w = _world(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_mission_get_band(w) == 4  # fixture check: total success recorded
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 1


def test_R_078_06_flag_is_set_by_a_refused_mission_too(lib, world_factory):
    """Given a refused mission (refusal is a band), Then the flag reads 1 until the jump consumes it."""
    w = _world(lib, world_factory)
    lib.om_mission_setup(w, MISSION_REGION, DEFENSIVE_STAND, 0)
    lib.om_mission_resolve_refusal(w, MISSION_REGION)
    assert lib.om_mission_get_band(w) == 5  # fixture check: refusal band
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 1


def test_control_R_078_06_flag_is_zero_with_no_mission(lib, world_factory):
    """Control: with no mission result recorded the flag is 0, before and after a jump."""
    w = _world(lib, world_factory)
    assert lib.om_mission_get_band(w) == -1  # fixture check
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0


def test_R_078_06_flag_clears_when_the_jump_consumes_the_consequence(lib, world_factory):
    """Given a mission then a jump that shows the consequence, Then the flag is 0 after that jump and stays 0 after a second jump (the second jump shows no consequence)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 1  # fixture check: armed
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert _n_consequence_clusters(lib, w) == 1  # fixture check: first jump shows it
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert _n_consequence_clusters(lib, w) == 0
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0


def test_R_078_06_a_new_mission_rearms_the_flag(lib, world_factory):
    """Given a consumed consequence, When another mission ends, Then the flag reads 1 again."""
    w = _world(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 0  # fixture check
    _play_mission(lib, w)
    assert lib.om_chronicle_has_mission_consequence_flag(w) == 1


def test_R_111_01_save_before_the_jump_keeps_the_pending_consequence(lib, world_factory):
    """Given a world saved after a mission and before the jump, When loaded and jumped, Then the flag survives (1 after load) and the jump shows exactly one consequence cluster."""
    src = _world(lib, world_factory)
    _play_mission(lib, src)
    dst = _roundtrip(lib, world_factory, src)
    assert lib.om_mission_get_band(dst) == 4
    assert lib.om_chronicle_has_mission_consequence_flag(dst) == 1
    assert lib.om_time_jump_run(dst, 30, None) == 0
    assert _n_consequence_clusters(lib, dst) == 1


def test_R_111_01_the_mission_result_survives_save_and_load(lib, world_factory):
    """Given a world saved after a mission, When loaded, Then the band and region of the result are still there. Without them a pending consequence is lost, and a consumed one cannot be told from 'no mission' (mission.c installs no save hooks: w->mission_state_size is never set)."""
    src = _world(lib, world_factory)
    _play_mission(lib, src)
    dst = _roundtrip(lib, world_factory, src)
    assert lib.om_mission_get_band(dst) == 4
    assert lib.om_mission_last_region(dst) == MISSION_REGION


def test_R_111_01_save_after_the_jump_does_not_repeat_the_consequence(lib, world_factory):
    """Given a world saved after the jump consumed its consequence, When loaded and jumped again, Then the flag is 0 after load and the next jump shows no consequence cluster. Regression guard: today it passes only because the band is not saved (see the survives test); it must keep passing once it is."""
    src = _world(lib, world_factory)
    _play_mission(lib, src)
    assert lib.om_time_jump_run(src, 30, None) == 0
    assert _n_consequence_clusters(lib, src) == 1  # fixture check: it was shown once
    dst = _roundtrip(lib, world_factory, src)
    assert lib.om_chronicle_has_mission_consequence_flag(dst) == 0
    assert lib.om_time_jump_run(dst, 30, None) == 0
    assert _n_consequence_clusters(lib, dst) == 0


def test_R_065_02_a_second_mission_gets_its_own_consequence_in_the_next_jump(lib, world_factory):
    """Given a mission, a jump that consumed its consequence, then a second mission and a second jump, Then the second jump's scroll holds exactly one consequence cluster (the consumed marker is per mission result, not once per campaign)."""
    w = _world(lib, world_factory)
    _play_mission(lib, w)
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert _n_consequence_clusters(lib, w) == 1  # fixture check
    _play_mission(lib, w, 0.0)
    assert lib.om_time_jump_run(w, 30, None) == 0
    assert _n_consequence_clusters(lib, w) == 1
