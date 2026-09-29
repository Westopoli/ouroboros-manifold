"""Backing HDR4-2's mission `force` accessors (docs/northstar's
gap-fix-and-migration-plan.md): om_mission_get_force_count and
om_mission_get_force_unit report the PLAYER's spawned force units only --
the ones om_mission_instantiate_map spawns for the player faction via the
static om_mission_spawn_force in csrc/mission.c -- never the enemy's.

Neither accessor exists yet (they are not in csrc/ouroboros_sim.h / bound in
conftest.py), so every test below is RED: the first call to either symbol
raises AttributeError (undefined symbol in libouroboros.so). These are
written bare, unbound, the way test_core_* red tests in this suite call a
not-yet-added symbol directly off `lib`.

Fixture note: om_mission_compose_force (csrc/mission.c) needs a nonzero
enemy force to produce a nonzero player force. Archetype 1 (Siege Breaking)
takes the "otherwise" branch of om_mission_compute_enemy_power -- enemy
power = region military * OM_MILITARY_TO_POWER_SCALE -- with no conflict
context required (the DEFENSIVE_STAND/MULTI_FRONT_DEFENSE/INTERCEPTION
archetypes need om_mission_set_conflict_context first or their committed
budget is 0). A region with military=10.0 already yields a player force of
a few hundred units; military=90.0 yields a few thousand -- verified
empirically against the existing om_mission_get_player_units accessor
before writing this file.

Player units are spawned before the enemy's in om_mission_instantiate_map,
and om_unit_spawn's ids start at 1 (csrc/unit.c om_tactical_reset), so in a
fresh world (no other unit spawns) the i-th player force unit (0-indexed)
is real spawned unit id i + 1 -- verified empirically that
om_unit_get_unit_type(w, i + 1) matches the type om_mission_compose_force's
counts array implies for index i (types visited in ascending order 0..5,
each repeated its count).
"""
import ctypes

from conftest import OMTier, set_region

OM_MISSION_ARCH_SIEGE_BREAKING = 1  # csrc/mission.c OM_MISSION_ARCH_SIEGE_BREAKING


def _setup_mission(lib, w, region_idx, military, archetype=OM_MISSION_ARCH_SIEGE_BREAKING):
    set_region(lib, w, region_idx, tier=OMTier.HOME, military=military, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    lib.om_mission_setup(w, region_idx, archetype, 0)


def _player_unit_total(lib, w):
    counts = (ctypes.c_uint32 * 6)()
    lib.om_mission_get_player_units(w, counts, 6)
    return counts, sum(counts[i] for i in range(6))


def test_force_count_matches_player_units_sum(lib, world_factory):
    """om_mission_get_force_count(w) equals the sum of om_mission_get_player_units'
    per-type counts -- the player's force only."""
    w = world_factory(n_regions=1)
    _setup_mission(lib, w, 0, military=10.0)

    _, expected_total = _player_unit_total(lib, w)
    assert expected_total > 0, "fixture must produce a nonzero player force"

    assert lib.om_mission_get_force_count(w) == expected_total


def test_force_unit_reports_type_matching_the_real_spawned_unit(lib, world_factory):
    """Every om_mission_get_force_unit(w, i, ...) up to the force count succeeds
    (returns 1), reports a valid unit type, and that type matches the real
    spawned unit's type read via the existing om_unit_get_unit_type accessor
    on the global unit id om_mission_spawn_force would have produced for
    local index i (id = i + 1, see module docstring). Tier's source is not
    decided yet -- only that the call succeeds and returns some tier value
    is checked."""
    w = world_factory(n_regions=1)
    _setup_mission(lib, w, 0, military=10.0)

    counts, total = _player_unit_total(lib, w)
    assert total > 0

    expected_types = []
    for t in range(6):
        expected_types += [t] * counts[t]

    out_type = ctypes.c_int32()
    out_tier = ctypes.c_int32()
    for i, expected_type in enumerate(expected_types):
        ok = lib.om_mission_get_force_unit(w, i, ctypes.byref(out_type), ctypes.byref(out_tier))
        assert ok == 1
        assert 0 <= out_type.value < 6
        assert out_type.value == expected_type

        real_unit_id = i + 1  # unit ids start at 1; player force spawns first
        assert lib.om_unit_get_unit_type(w, real_unit_id) == out_type.value


def test_force_unit_out_of_range_returns_zero(lib, world_factory):
    """om_mission_get_force_unit returns 0 (failure) one past the end, and for
    a wildly out-of-range index, with no crash."""
    w = world_factory(n_regions=1)
    _setup_mission(lib, w, 0, military=10.0)

    _, total = _player_unit_total(lib, w)
    assert total > 0

    out_type = ctypes.c_int32()
    out_tier = ctypes.c_int32()
    assert lib.om_mission_get_force_unit(w, total, ctypes.byref(out_type), ctypes.byref(out_tier)) == 0
    assert lib.om_mission_get_force_unit(w, total + 1000, ctypes.byref(out_type), ctypes.byref(out_tier)) == 0


def test_control_force_count_differs_with_a_different_player_force(lib, world_factory):
    """Positive control: a different mission setup (a region with different
    military, same archetype) yields a different total player force count,
    proving om_mission_get_force_count is not reading a hardcoded constant."""
    w_low = world_factory(n_regions=1)
    _setup_mission(lib, w_low, 0, military=10.0)
    _, total_low = _player_unit_total(lib, w_low)

    w_high = world_factory(n_regions=1)
    _setup_mission(lib, w_high, 0, military=90.0)
    _, total_high = _player_unit_total(lib, w_high)

    assert total_low != total_high, "fixture must actually vary the player force size"

    assert lib.om_mission_get_force_count(w_low) == total_low
    assert lib.om_mission_get_force_count(w_high) == total_high
