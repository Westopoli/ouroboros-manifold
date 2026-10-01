"""B7 (Q-077-02, R-077-05, R-077-03, S-077): the player assigns the mission
commander; om_mission_end reads commander fate from the assigned unit.

Fixture: two regions, player faction 0 owns region 1, enemy faction 1 owns
the mission region 0 (as test_core_mission_live_termination.py); Siege Breaking
with military=10.0 spawns a nonzero player force (ids 1..force_count in a
fresh world) and an enemy force after it (see test_core_mission_force_accessors.py).

om_mission_assign_commander returns 0 ok, 1 unit missing or not the player's,
2 assigned commander already dead. Assigning a dead unit that is not yet the
commander is left to the pipe handler ("unit dead"); the C return for it is
not pinned here (ambiguity flagged to the architect).

Not covered here (they ship with B6/B7 later): the four R-061 commander-death
symbols and the selector's death path.
"""
import ctypes

from conftest import OMArchetype, OMTier, set_faction, set_owner, set_region

ARCH_SIEGE_BREAKING = 1
FATE_KILLED, FATE_WOUNDED, FATE_SURVIVED = 0, 1, 2
UNKNOWN_UNIT = 99999


def _mission(lib, world_factory):
    w = world_factory(n_regions=2)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 1, held_since=-1)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=10.0, economy=40.0,
               tension=20.0, population=50.0, faction_id=1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=10.0, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    lib.om_mission_setup(w, 0, ARCH_SIEGE_BREAKING, 0)
    n = lib.om_mission_get_force_count(w)
    assert n >= 2, "fixture needs at least two player units to test reassignment"
    return w, n


def _enemy_unit(lib, w, n):
    for uid in range(n + 1, lib.om_unit_count(w) + 1):
        if lib.om_unit_get_faction(w, uid) != 0:
            return uid
    raise AssertionError("fixture spawned no enemy unit")


def _fate(lib, w):
    from conftest import OMDebrief
    out = OMDebrief()
    assert lib.om_mission_get_debrief(w, ctypes.byref(out)) == 1
    return out.commander_fate


def test_R_077_05_assign_a_force_unit_returns_zero_and_is_readable(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_get_commander_unit(w) == 0
    assert lib.om_mission_assign_commander(w, 1) == 0
    assert lib.om_mission_get_commander_unit(w) == 1


def test_R_077_05_unknown_unit_returns_one_and_changes_nothing(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 2) == 0
    assert lib.om_mission_assign_commander(w, UNKNOWN_UNIT) == 1
    assert lib.om_mission_assign_commander(w, 0) == 1
    assert lib.om_mission_get_commander_unit(w) == 2


def test_R_077_05_enemy_unit_returns_one_and_changes_nothing(lib, world_factory):
    w, n = _mission(lib, world_factory)
    enemy = _enemy_unit(lib, w, n)
    assert lib.om_mission_assign_commander(w, enemy) == 1
    assert lib.om_mission_get_commander_unit(w) == 0
    assert lib.om_mission_assign_commander(w, 1) == 0
    assert lib.om_mission_assign_commander(w, enemy) == 1
    assert lib.om_mission_get_commander_unit(w) == 1


def test_R_077_05_reassign_while_the_assigned_unit_lives(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    assert lib.om_mission_assign_commander(w, 2) == 0
    assert lib.om_mission_get_commander_unit(w) == 2


def test_R_077_05_reassign_after_the_assigned_unit_died_returns_two(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_unit_set_hp(w, 1, 0.0)
    assert lib.om_unit_alive(w, 1) == 0
    assert lib.om_mission_assign_commander(w, 2) == 2
    assert lib.om_mission_get_commander_unit(w) == 1


def test_R_077_05_commander_unit_is_zero_without_a_mission(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_mission_get_commander_unit(w) == 0
    assert lib.om_mission_assign_commander(w, 1) == 1


def test_R_077_03_end_with_the_commander_unit_dead_reports_killed(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_unit_set_hp(w, 1, 0.0)
    lib.om_mission_end(w)
    assert _fate(lib, w) == FATE_KILLED


def test_R_077_03_end_with_the_commander_unit_hurt_reports_wounded(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    ty = lib.om_unit_get_unit_type(w, 1)
    max_hp = lib.om_unit_profile_max_hp(w, ty)
    lib.om_unit_set_hp(w, 1, max_hp * 0.1)
    lib.om_mission_end(w)
    assert _fate(lib, w) == FATE_WOUNDED


def test_R_077_03_end_with_the_commander_unit_unhurt_reports_survived(lib, world_factory):
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_mission_end(w)
    assert _fate(lib, w) == FATE_SURVIVED


def test_R_077_03_fate_follows_the_reassigned_unit_not_the_first(lib, world_factory):
    """Unit 1 dies after being replaced by unit 2 (reassign was legal while 1
    lived); the fate is unit 2's."""
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    assert lib.om_mission_assign_commander(w, 2) == 0
    lib.om_unit_set_hp(w, 1, 0.0)
    lib.om_mission_end(w)
    assert _fate(lib, w) == FATE_SURVIVED


def test_R_077_03_control_killing_a_non_commander_does_not_kill_the_commander(lib, world_factory):
    """Positive control for the killed case: the same death on the assigned
    unit gives killed (test above); on another unit it gives survived."""
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_unit_set_hp(w, 2, 0.0)
    lib.om_mission_end(w)
    assert _fate(lib, w) == FATE_SURVIVED


def test_R_077_03_end_with_no_commander_assigned_reports_survived(lib, world_factory):
    w, n = _mission(lib, world_factory)
    lib.om_unit_set_hp(w, 1, 0.0)
    lib.om_mission_end(w)
    assert lib.om_mission_get_commander_unit(w) == 0
    assert _fate(lib, w) == FATE_SURVIVED


def test_R_077_05_region_delta_is_available_after_end_with_a_commander(lib, world_factory):
    """The debrief frame reads the region delta and the fate from the same
    ended mission; assigning a commander must not disturb the delta."""
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_mission_end(w)
    d = [ctypes.c_double() for _ in range(4)]
    lib.om_mission_get_region_delta.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_double)] * 4
    lib.om_mission_get_region_delta.restype = ctypes.c_int
    assert lib.om_mission_get_region_delta(w, *[ctypes.byref(x) for x in d]) == 1
    assert _fate(lib, w) == FATE_SURVIVED


def test_R_077_05_a_new_mission_setup_clears_the_assigned_commander(lib, world_factory):
    """The pipe's mission frame after mission_start carries commander_unit 0
    (docs/architecture.md); a commander from an earlier mission must not
    survive into the next one."""
    w, n = _mission(lib, world_factory)
    assert lib.om_mission_assign_commander(w, 1) == 0
    lib.om_mission_end(w)
    lib.om_mission_setup(w, 0, ARCH_SIEGE_BREAKING, 0)
    assert lib.om_mission_get_commander_unit(w) == 0
