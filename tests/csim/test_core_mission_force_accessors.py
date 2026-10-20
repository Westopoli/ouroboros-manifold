"""S-079 / R-079-01 (briefing assets), A4 ruling 5-6: om_mission_get_force_count
and om_mission_get_force_unit report the player's spawned force only.

Fixture: Siege Breaking (archetype 1) takes the plain enemy-power branch, so a
region with military=10.0 yields a nonzero player force with no conflict
context. Player units spawn before the enemy's and unit ids start at 1, so the
i-th player force unit is unit id i + 1 in a fresh world.

No test asserts a tier value: no per-unit tier source exists yet (flagged to
the architect); only that the out parameter is writable and the call succeeds.
"""
import ctypes

from conftest import OMTier, set_region

ARCH_SIEGE_BREAKING = 1
ROSTER_10, START_10, CUT_10 = [24, 38, 21, 137, 30, 13], 158, [14, 23, 13, 82, 18, 8]  # TD-VG-E-34: F 263, p 1, e 1, share 0.5
ROSTER_90, START_90 = [301, 434, 271, 846, 363, 206], 1453  # TD-VG-E-34: F 2421, p 2, e 2, share 0.5


def _setup(lib, w, military, archetype=ARCH_SIEGE_BREAKING):
    set_region(lib, w, 0, tier=OMTier.HOME, military=military, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    lib.om_mission_setup(w, 0, archetype, 0)


def _player_counts(lib, w):
    counts = (ctypes.c_uint32 * 6)()
    lib.om_mission_get_player_units(w, 0, counts, 6)
    return list(counts)


def test_R_079_01_force_count_equals_player_units_sum(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w, 10.0)
    assert _player_counts(lib, w) == ROSTER_10, "premise: the composed roster F 263"
    assert lib.om_mission_get_force_count(w) == START_10  # was sum(roster) = 263: the player spawns start_units of F


def test_R_079_01_force_unit_types_match_spawned_units(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w, 10.0)
    assert _player_counts(lib, w) == ROSTER_10, "premise: the composed roster F 263"
    expected = []
    for t, n in enumerate(CUT_10):  # was the roster itself: the player spawns the cut of it (start_units 158)
        expected += [t] * n
    assert len(expected) == START_10
    ty, tier = ctypes.c_int32(-1), ctypes.c_int32(-1)
    for i, want in enumerate(expected):
        assert lib.om_mission_get_force_unit(w, i, ctypes.byref(ty), ctypes.byref(tier)) == 1
        assert 0 <= ty.value < 6
        assert ty.value == want
        assert lib.om_unit_get_unit_type(w, i + 1) == ty.value


def test_R_079_01_force_unit_out_of_range_returns_zero(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w, 10.0)
    total = lib.om_mission_get_force_count(w)
    assert total > 0
    ty, tier = ctypes.c_int32(), ctypes.c_int32()
    assert lib.om_mission_get_force_unit(w, total, ctypes.byref(ty), ctypes.byref(tier)) == 0
    assert lib.om_mission_get_force_unit(w, total + 1000, ctypes.byref(ty), ctypes.byref(tier)) == 0


def test_R_079_01_force_unit_accepts_null_outs(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w, 10.0)
    assert lib.om_mission_get_force_unit(w, 0, None, None) == 1


def test_R_079_01_force_count_excludes_enemy_units(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w, 10.0)
    assert lib.om_unit_count(w) > lib.om_mission_get_force_count(w) > 0


def test_R_079_01_control_force_count_tracks_force_size(lib, world_factory):
    """Positive control: a bigger region yields a different count, so the
    accessor is not a constant."""
    lo = world_factory(n_regions=1)
    _setup(lib, lo, 10.0)
    hi = world_factory(n_regions=1)
    _setup(lib, hi, 90.0)
    assert _player_counts(lib, lo) == ROSTER_10 and _player_counts(lib, hi) == ROSTER_90, "premise: F 263 and F 2421"
    t_lo, t_hi = START_10, START_90  # was sum(roster): 263 and 2421; the player spawns start_units of F
    assert t_lo != t_hi
    assert lib.om_mission_get_force_count(lo) == t_lo
    assert lib.om_mission_get_force_count(hi) == t_hi


def test_R_079_01_force_count_zero_without_a_mission(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_mission_get_force_count(w) == 0
    ty, tier = ctypes.c_int32(), ctypes.c_int32()
    assert lib.om_mission_get_force_unit(w, 0, ctypes.byref(ty), ctypes.byref(tier)) == 0
