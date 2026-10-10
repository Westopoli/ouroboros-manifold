"""VG-CONTRACT-E2 (K-e2): the economy entry points and the three rule edits wired with them.

Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 8, "Lane E1 part a2: the K-e2 amendment".
Rules: R-218-01 (ground structure count capped at the slope count), R-218-05 (a structure at 0 HP stays
listed), R-218-06 (starting force is the whole force, reinforcement capacity 0; liberty 2026-10-10).
The entry points are internal (csrc/economy_internal.h) but exported by the shared object, so ctypes finds them.
"""
import ctypes

import pytest

from conftest import OMTier, set_faction, set_owner, set_region, set_edge, OMArchetype, OMEdge, OMFeature

W = ctypes.c_void_p
U32, I32, U64, D = ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64, ctypes.c_double

# (name, argtypes, restype) exactly as the spec states them.
ENTRIES = [
    ("om_economy_init", [W], None),
    ("om_economy_step", [W, U64], None),
    ("om_economy_on_structure_owner", [W, U32, I32, I32], None),
    ("om_economy_on_structure_damage", [W, U32, D], None),
    ("om_economy_on_area_hit", [W, D, D, D], None),
    ("om_economy_on_mission_end", [W], None),
    ("om_density_init", [W], None),
    ("om_density_step", [W, U64], None),
    ("om_lots_init", [W], None),
    ("om_lots_step", [W, U64], None),
    ("om_lots_on_area_hit", [W, D, D, D], None),
    ("om_waves_init", [W], None),
    ("om_waves_step", [W, U64], None),
    ("om_waves_log", [W, U32, I32, D, D], None),
    ("om_waves_on_structure_owner", [W, U32, I32, I32], None),
    ("om_waves_on_mission_end", [W], None),
    ("om_strongpoint_init", [W], None),
    ("om_strongpoint_step", [W, U64], None),
    ("om_strongpoint_on_structure_owner", [W, U32, I32, I32], None),
    ("om_strongpoint_on_structure_damage", [W, U32, D], None),
]


def _has(lib, name):
    try:
        getattr(lib, name)
        return True
    except AttributeError:
        return False


def _missing(lib, names):
    return [n for n in names if not _has(lib, n)]


def test_ke2_detector_names_a_missing_symbol(lib):
    """Positive control: the lookup detector reports a symbol that cannot exist."""
    assert _missing(lib, ["om_no_such_entry_ke2_control", "om_world_new"]) == ["om_no_such_entry_ke2_control"]


def test_ke2_entry_points_exist(lib):
    """K-e2: every declared entry point is exported by the built library (on main: missing symbols)."""
    missing = _missing(lib, [e[0] for e in ENTRIES])
    assert not missing, f"entry points missing from the shared object: {missing}"


def test_ke2_entry_points_callable_with_stated_signatures(lib, world_factory):
    """K-e2: each entry is callable with the stated argument types on a plain world (no-op bodies must not crash)."""
    missing = _missing(lib, [e[0] for e in ENTRIES])
    assert not missing, f"entry points missing from the shared object: {missing}"
    w = world_factory(n_regions=1)
    args = {W: w, U64: 1, U32: 0, I32: 0, D: 0.0}
    for name, argtypes, restype in ENTRIES:
        fn = getattr(lib, name)
        fn.argtypes = argtypes
        fn.restype = restype
        fn(*[args[t] for t in argtypes])


def _ground_mission(lib, world_factory, archetype, seed=7):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 1, held_since=-1)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=2000.0, faction_id=1)
    assert lib.om_set_era_kind(w, 1) == 0
    lib.om_mission_setup(w, 0, archetype, 0)
    return w


def _over_cap(count, slopes):
    return count > slopes


def test_ke2_cap_detector_control():
    """Positive control: the cap detector fires on 5 structures over 3 slopes and not on 3 over 3."""
    assert _over_cap(5, 3) and not _over_cap(3, 3)


@pytest.mark.parametrize("archetype", [0, 1, 2, 3, 4])
def test_R_218_01_ground_structure_count_at_most_slope_count(lib, world_factory, archetype):
    """R-218-01: in a ground era the structure count never exceeds om_terrain_slope_count."""
    w = _ground_mission(lib, world_factory, archetype)
    slopes = lib.om_terrain_slope_count(w)
    count = lib.om_structure_count(w)
    assert not _over_cap(count, slopes), f"{count} structures over {slopes} slopes"


def test_R_218_06_starting_force_is_the_whole_force(lib):
    """R-218-06 (liberty 2026-10-10): om_mission_compute_starting_force(F) == F."""
    lib.om_mission_compute_starting_force.argtypes = [D]
    lib.om_mission_compute_starting_force.restype = D
    assert lib.om_mission_compute_starting_force(1000.0) == 1000.0


def test_R_218_06_reinforcement_capacity_is_zero(lib):
    """R-218-06: om_mission_compute_reinforcement_capacity(1000.0, 1200) == 0.0."""
    lib.om_mission_compute_reinforcement_capacity.argtypes = [D, U64]
    lib.om_mission_compute_reinforcement_capacity.restype = D
    assert lib.om_mission_compute_reinforcement_capacity(1000.0, 1200) == 0.0


def test_R_218_06_detector_control(lib):
    """Positive control: a non-whole starting force (a 0.2 share) is distinguishable from F."""
    assert 0.2 * 1000.0 != 1000.0


def _hp(lib, w, s):
    return ctypes.c_double(lib.om_structure_get_hp(w, s)).value


def test_R_218_05_control_partial_damage_leaves_hp(lib, world_factory):
    """Positive control: the HP reader sees a partial hit (2900 after 100 damage), so 0 below is not a stuck reader."""
    w = world_factory(n_regions=1)
    lib.om_structure_init(w, 0, 0, D(100.0))
    lib.om_structure_apply_damage(w, 0, D(100.0), 0)
    assert _hp(lib, w, 0) == pytest.approx(2900.0, abs=1e-5)


def test_R_218_05_structure_at_zero_hp_stays_listed(lib, world_factory):
    """R-218-05: damage to 0 HP leaves the structure listed (count unchanged) with HP 0."""
    w = world_factory(n_regions=1)
    lib.om_structure_init(w, 0, 0, D(100.0))
    before = lib.om_structure_count(w)
    assert before >= 1
    lib.om_structure_apply_damage(w, 0, D(3000.0), 0)
    assert _hp(lib, w, 0) == pytest.approx(0.0, abs=1e-5)
    assert lib.om_structure_count(w) == before
