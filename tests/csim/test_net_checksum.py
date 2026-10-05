"""Lockstep spec 2026-10-05, lane "cksum": the full-state checksum.

Proves R-139-03 (a checkpoint checksum over region fields, faction state, RNG
state, unit store) and the section naming that R-139-04 relies on (the first
differing field is named by section, and by unit id for units). Section order
is the spec's: 0 regions, 1 factions, 2 rng, 3 units, 4 movement, 5 mission,
6 fog, 7 macro, 8 support and map.

Core tests (regions, factions, rng, count, names, determinism, first_diff,
cross-process) must be RED while checksum_full.c holds stubs. Tests marked
xfail(strict=False) below need the module section hooks (units, movement,
mission, fog, macro, support and map); those hooks are empty on this branch
and land in layer 2.

Drawing from the rng: the public API has no bare draw, so the rng tests queue
forced draws with om_rng_force, which changes only rng state (section 2).
"""
import ctypes
import pathlib
import subprocess
import sys

import pytest

from conftest import OMArchetype, OMTier, set_faction, set_region
from b1_macro_scene import RAIDER, ENEMY_FAC, PLAYER_FAC, tactical_world

HERE = pathlib.Path(__file__).resolve().parent
N_SECTIONS = 9
SECTION_NAMES = ["regions", "factions", "rng", "units", "movement", "mission",
                 "fog", "macro", "support and map"]

needs_module_hooks = pytest.mark.xfail(
    strict=False, reason="module section hooks land in layer 2")


def _full(lib, w):
    """(combined, sections[9]) via om_world_checksum_full; asserts the count first."""
    assert lib.om_checksum_section_count() == N_SECTIONS, "section count is not 9"
    arr = (ctypes.c_uint64 * N_SECTIONS)()
    combined = lib.om_world_checksum_full(w, arr, N_SECTIONS)
    return combined, list(arr)


def _strategic_world(lib, world_factory, seed):
    w = world_factory(n_regions=3, seed=seed)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0, tension=18.0,
               population=60.0, econ_phase=0.3, tension_phase=1.1, faction_id=1)
    set_region(lib, w, 1, tier=OMTier.FRONTIER, military=20.0, economy=35.0, tension=55.0,
               population=30.0, econ_phase=2.5, tension_phase=4.2)
    set_region(lib, w, 2, tier=OMTier.HOME, military=80.0, economy=90.0, tension=5.0,
               population=70.0, econ_phase=5.9, tension_phase=0.1, faction_id=1)
    return w


def _battle_world(lib, world_factory, seed):
    w = tactical_world(lib, world_factory, seed=seed)
    ids = [lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, 8000.0 + 40.0 * i, 12000.0, 0) for i in range(3)]
    ids += [lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, 8000.0 + 40.0 * i, 4000.0, 0) for i in range(3)]
    return w, ids


def _diff_sections(a, b):
    return [i for i in range(N_SECTIONS) if a[i] != b[i]]


def test_R_139_03_section_count_is_nine(lib):
    assert lib.om_checksum_section_count() == N_SECTIONS


def test_R_139_03_section_names_in_spec_order(lib):
    assert lib.om_checksum_section_count() == N_SECTIONS
    names = [lib.om_checksum_section_name(i).decode() for i in range(N_SECTIONS)]
    assert names == SECTION_NAMES


def test_R_139_03_full_fills_sections_and_combined(lib, world_factory):
    w = _strategic_world(lib, world_factory, 5)
    combined, secs = _full(lib, w)
    assert combined != 0
    assert secs[0] != 0 and secs[1] != 0 and secs[2] != 0, "regions, factions, rng sections left empty"


def test_R_139_03_combined_changes_when_any_section_changes(lib, world_factory):
    w = _strategic_world(lib, world_factory, 5)
    base, _ = _full(lib, w)
    set_region(lib, w, 1, tier=OMTier.FRONTIER, military=21.0, economy=35.0, tension=55.0,
               population=30.0, econ_phase=2.5, tension_phase=4.2)
    c_region, _ = _full(lib, w)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    c_faction, _ = _full(lib, w)
    draws = (ctypes.c_double * 1)(0.25)
    lib.om_rng_force(w, draws, 1)
    c_rng, _ = _full(lib, w)
    assert len({base, c_region, c_faction, c_rng}) == 4


def test_R_139_03_same_seed_agrees_every_section_200_strategic_ticks(lib, world_factory):
    wa = _strategic_world(lib, world_factory, 99999)
    wb = _strategic_world(lib, world_factory, 99999)
    for t in range(200):
        # om_world_run returns the cumulative tick, not the ticks just run
        assert lib.om_world_run(wa, 1) == t + 1 and lib.om_world_run(wb, 1) == t + 1
        ca, sa = _full(lib, wa)
        cb, sb = _full(lib, wb)
        assert (ca, sa) == (cb, sb), f"strategic tick {t}: sections differ {_diff_sections(sa, sb)}"
    assert ca != 0


def test_R_139_03_same_seed_agrees_every_section_300_tick_battle(lib, world_factory):
    wa, _ = _battle_world(lib, world_factory, 7)
    wb, _ = _battle_world(lib, world_factory, 7)
    for t in range(300):
        lib.om_tactical_step(wa)
        lib.om_tactical_step(wb)
        ca, sa = _full(lib, wa)
        cb, sb = _full(lib, wb)
        assert (ca, sa) == (cb, sb), f"battle tick {t}: sections differ {_diff_sections(sa, sb)}"
    assert ca != 0


def test_R_139_03_region_field_changes_only_section_0(lib, world_factory):
    wa = _strategic_world(lib, world_factory, 3)
    wb = _strategic_world(lib, world_factory, 3)
    _, sa = _full(lib, wa)
    set_region(lib, wb, 1, tier=OMTier.FRONTIER, military=20.0, economy=36.0, tension=55.0,
               population=30.0, econ_phase=2.5, tension_phase=4.2)
    _, sb = _full(lib, wb)
    assert _diff_sections(sa, sb) == [0]


def test_R_139_03_rng_draw_changes_only_section_2(lib, world_factory):
    wa = _strategic_world(lib, world_factory, 3)
    wb = _strategic_world(lib, world_factory, 3)
    _, sa = _full(lib, wa)
    lib.om_rng_force(wb, (ctypes.c_double * 1)(0.5), 1)
    _, sb = _full(lib, wb)
    assert _diff_sections(sa, sb) == [2]


def test_R_139_04_first_diff_identical_returns_0(lib, world_factory):
    wa = _strategic_world(lib, world_factory, 3)
    wb = _strategic_world(lib, world_factory, 3)
    _full(lib, wa)
    sec, uid = ctypes.c_uint32(77), ctypes.c_uint32(77)
    assert lib.om_checksum_first_diff(wa, wb, ctypes.byref(sec), ctypes.byref(uid)) == 0


def test_R_139_04_first_diff_names_the_section(lib, world_factory):
    wa = _strategic_world(lib, world_factory, 3)
    wb = _strategic_world(lib, world_factory, 3)
    assert lib.om_checksum_section_count() == N_SECTIONS
    set_region(lib, wb, 2, tier=OMTier.HOME, military=81.0, economy=90.0, tension=5.0,
               population=70.0, econ_phase=5.9, tension_phase=0.1, faction_id=1)
    sec, uid = ctypes.c_uint32(77), ctypes.c_uint32(0)
    assert lib.om_checksum_first_diff(wa, wb, ctypes.byref(sec), ctypes.byref(uid)) == 1
    assert sec.value == 0


_SCRIPT = """
import sys
sys.path.insert(0, %r)
import ctypes
import conftest
from conftest import OMTier, set_region
lib = conftest.load_lib()
w = lib.om_world_new(ctypes.c_uint32(3), ctypes.c_uint64(4242))
set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0, tension=18.0,
           population=60.0, econ_phase=0.3, tension_phase=1.1, faction_id=1)
lib.om_world_run(w, 50)
arr = (ctypes.c_uint64 * 9)()
print(lib.om_world_checksum_full(w, arr, 9), list(arr))
"""


def test_R_139_01_combined_stable_across_two_processes(lib):
    assert lib.om_checksum_section_count() == N_SECTIONS
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-c", _SCRIPT % str(HERE)], cwd=str(HERE),
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-2000:]
        outs.append(r.stdout.strip().splitlines()[-1])
    assert outs[0] == outs[1]
    assert not outs[0].startswith("0 "), "combined value is 0"


# ---- NEEDS MODULE SECTIONS (units, movement, ...): hooks are empty on this branch ----

def test_R_139_03_unit_hp_changes_only_section_3_and_first_diff_names_unit(lib, world_factory):
    wa, ids_a = _battle_world(lib, world_factory, 7)
    wb, ids_b = _battle_world(lib, world_factory, 7)
    _, sa = _full(lib, wa)
    lib.om_unit_set_hp(wb, ids_b[2], 12.0)
    _, sb = _full(lib, wb)
    assert _diff_sections(sa, sb) == [3]
    sec, uid = ctypes.c_uint32(77), ctypes.c_uint32(0)
    assert lib.om_checksum_first_diff(wa, wb, ctypes.byref(sec), ctypes.byref(uid)) == 1
    assert (sec.value, uid.value) == (3, ids_b[2])


def test_R_139_03_move_order_changes_section_4(lib, world_factory):
    wa, ids_a = _battle_world(lib, world_factory, 7)
    wb, ids_b = _battle_world(lib, world_factory, 7)
    _, sa = _full(lib, wa)
    # a group move reaches the movement module; om_unit_order_move only writes the
    # support module's order record (section 8)
    arr = (ctypes.c_uint32 * 3)(*ids_b[3:])
    lib.om_command_group_move(wb, arr, 3, 9000.0, 5000.0)
    _, sb = _full(lib, wb)
    assert 4 in _diff_sections(sa, sb)
