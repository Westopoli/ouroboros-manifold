"""Enemy wave spawn: 50 units appear in the world after the arrival tick (R-124-02).

Uses the ctypes library directly (like test_pipe_tactical_world.py's world
fixture) because the binary pipe has no rng_force command. The wave is
forced via om_rng_force before the tactical run.

RED on main (spawn code absent: count delta = 0). GREEN after W-1f.
"""
import ctypes
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIB_PATH  = ROOT / "libouroboros.so"
PIPE      = ROOT / "pipe/ouroboros_pipe"

pytestmark = pytest.mark.skipif(
    not LIB_PATH.exists(),
    reason="libouroboros.so not built"
)

OM_UT_RAIDER      = 0
OM_UT_INTERCEPTOR = 1
OM_UT_VANGUARD    = 2
OM_UT_WARDEN      = 3
OM_UT_BOMBARD     = 4
OM_UT_BASTION     = 5

EXPECTED_COUNTS = {
    OM_UT_RAIDER:      15,
    OM_UT_INTERCEPTOR: 10,
    OM_UT_VANGUARD:    15,
    OM_UT_WARDEN:       5,
    OM_UT_BOMBARD:      3,
    OM_UT_BASTION:      2,
}
EXPECTED_WAVE_SIZE = sum(EXPECTED_COUNTS.values())  # 50

PLAYER_FAC = 0
ENEMY_FAC  = 1
DEFENSIVE_STAND = 0


@pytest.fixture(scope="module")
def lib():
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim  # noqa: PLC0415
    return csim.load_lib()


@pytest.fixture(scope="module")
def wave_world(lib):
    """World set up for a wave that fires at tick 41 (roll=0.10, dir=S, offset=0)."""
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim  # noqa: PLC0415
    import ctypes as ct

    w = lib.om_world_new(ct.c_uint32(2), ct.c_uint64(1))
    assert w, "om_world_new returned NULL"

    lib.om_world_set_feature(w, 1, 1)   # OMFeature.FACTIONS = 1
    lib.om_world_set_feature(w, 8, 1)   # OMFeature.TACTICAL = 8

    csim.set_faction(lib, w, PLAYER_FAC, 0)   # OMArchetype.PLAYER = 0
    csim.set_faction(lib, w, ENEMY_FAC,  1)   # OMArchetype.CONQUEROR = 1
    csim.set_owner(lib, w, 0, ENEMY_FAC,  held_since=-1)
    csim.set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    csim.set_edge(lib, w, 0, 1)

    # om_mission_setup not bound by csim._bind_generated at module level;
    # bind here directly.
    lib.om_mission_setup.argtypes = [
        ct.c_void_p, ct.c_uint32, ct.c_uint32, ct.c_uint32,
    ]
    lib.om_mission_setup.restype = None
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)  # tactical phase

    csim.force_draws(lib, w, [0.10, 0.5, 0.0])
    lib.om_tactical_tick_to(w, 41)

    yield w
    lib.om_world_free(w)


def _count_faction_units(lib, w, faction_id):
    total_in_reg = lib.om_unit_count(w)
    lib.om_unit_get_unit_type.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.om_unit_get_unit_type.restype  = ctypes.c_int32
    counts = {}
    scanned = 0
    i = 0
    while scanned < total_in_reg and i < 11000:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if not uid:
            continue
        scanned += 1
        if lib.om_unit_get_faction(w, uid) != faction_id:
            continue
        utype = lib.om_unit_get_unit_type(w, uid)
        counts[utype] = counts.get(utype, 0) + 1
    return counts


# ---- wave spawn: enemy unit count rises by exactly 50 after arrival tick -------

def test_wave_spawn_adds_50_enemy_units(wave_world, lib):
    """R-124-02: enemy unit count rises by exactly 50 after the arrival tick."""
    counts = _count_faction_units(lib, wave_world, ENEMY_FAC)
    total = sum(counts.values())
    assert total == EXPECTED_WAVE_SIZE, (
        f"R-124-02: expected {EXPECTED_WAVE_SIZE} enemy units after wave arrival, "
        f"got {total}. Wave spawn likely not implemented (W-1f)."
    )


def test_wave_spawn_composition_matches_alg75(wave_world, lib):
    """R-124-02: per-type counts match ALG-75 (Q-124-02, Westley 2026-09-28)."""
    counts = _count_faction_units(lib, wave_world, ENEMY_FAC)
    for utype, expected in EXPECTED_COUNTS.items():
        got = counts.get(utype, 0)
        assert got == expected, (
            f"R-124-02 ALG-75: unit type {utype}: expected {expected}, got {got}"
        )
