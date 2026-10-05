"""Lockstep spec 2026-10-05, module lanes mod-unit, mod-move, mod-macro, mod-fog,
mod-support, mod-mission, mod-mapgen, stage 1: the per-module section hash.

Proves R-139-03 (the checkpoint checksum covers each module's state) and R-139-04
(first_diff names the section, and the unit id for units). Sections: 3 units,
4 movement, 5 mission, 6 fog, 7 macro, 8 support and map.

For each module key (unit, move, mission, fog, macro, support, mapgen) three tests:
  _nonzero      after a real battle has run 100 ticks the section is nonzero
  _deterministic two same-seed worlds agree on the section every tenth tick for 600 ticks
  _isolated     one public-API change that belongs to the module changes that
                section and no other
Run one module with -k, e.g. -k "unit". RED while the hooks are empty (sections read 0).

Public functions used for the changes: om_unit_set_hp, om_command_group_move,
om_mission_set_objective_completion, om_command_ping, om_macro_set_state,
om_structure_set_capture_progress, om_map_add_cover. Every module has one.
"""
import ctypes

import pytest

from b1_macro_scene import ENEMY_FAC, PLAYER_FAC, RAIDER, tactical_world

N_SECTIONS = 9
UNITS, MOVEMENT, MISSION, FOG, MACRO, SUPPORT_MAP = 3, 4, 5, 6, 7, 8
OM_MACRO_PATROL = 2
BATTLE_TICKS = 600


def _battle(lib, world_factory, seed=7):
    """A real battle: two squads closing on each other, plus one structure."""
    w = tactical_world(lib, world_factory, seed=seed)
    ids = [lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, 8000.0 + 40.0 * i, 8300.0, 0) for i in range(3)]
    ids += [lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, 8000.0 + 40.0 * i, 7700.0, 0) for i in range(3)]
    st = lib.om_map_add_structure(w, 9000.0, 8000.0, ENEMY_FAC)
    return w, ids, st


def _secs(lib, w):
    assert lib.om_checksum_section_count() == N_SECTIONS, "section count is not 9"
    arr = (ctypes.c_uint64 * N_SECTIONS)()
    lib.om_world_checksum_full(w, arr, N_SECTIONS)
    return list(arr)


def _run(lib, w, n):
    for _ in range(n):
        lib.om_tactical_step(w)


def _nonzero(lib, world_factory, section):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, 100)
    assert _secs(lib, w)[section] != 0, f"section {section} reads 0 after 100 battle ticks"


def _deterministic(lib, world_factory, section):
    wa, _, _ = _battle(lib, world_factory)
    wb, _, _ = _battle(lib, world_factory)
    seen = set()
    for t in range(1, BATTLE_TICKS + 1):
        lib.om_tactical_step(wa)
        lib.om_tactical_step(wb)
        if t % 10 == 0:
            a, b = _secs(lib, wa)[section], _secs(lib, wb)[section]
            assert a == b, f"tick {t}: section {section} differs between same-seed worlds"
            seen.add(a)
    assert seen != {0}, f"section {section} read 0 at every checkpoint"


def _isolated(lib, world_factory, section, change):
    """Same world twice at tick 100; apply change(w, ids, st) to the second only."""
    wa, _, _ = _battle(lib, world_factory)
    wb, ids, st = _battle(lib, world_factory)
    _run(lib, wa, 100)
    _run(lib, wb, 100)
    before_a, before_b = _secs(lib, wa), _secs(lib, wb)
    assert before_a == before_b, "setup: same-seed worlds differ before the change"
    change(wb, ids, st)
    after = _secs(lib, wb)
    changed = [i for i in range(N_SECTIONS) if after[i] != before_a[i]]
    assert changed == [section], f"change moved sections {changed}, expected only [{section}]"
    return wa, wb, ids


# ---- units (section 3) ----

def test_unit_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, UNITS)


def test_unit_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, UNITS)


def test_unit_hp_change_isolated_and_first_diff_names_unit(lib, world_factory):
    wa, wb, ids = _isolated(lib, world_factory, UNITS,
                            lambda w, ids, st: lib.om_unit_set_hp(w, ids[2], 12.0))
    sec, uid = ctypes.c_uint32(77), ctypes.c_uint32(0)
    assert lib.om_checksum_first_diff(wa, wb, ctypes.byref(sec), ctypes.byref(uid)) == 1
    assert (sec.value, uid.value) == (3, ids[2])


# ---- movement (section 4) ----

def test_move_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, MOVEMENT)


def test_move_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, MOVEMENT)


def test_move_group_order_isolated(lib, world_factory):
    def change(w, ids, st):
        arr = (ctypes.c_uint32 * 3)(*ids[3:])
        lib.om_command_group_move(w, arr, 3, 11000.0, 5000.0)
    _isolated(lib, world_factory, MOVEMENT, change)


# ---- mission (section 5) ----

def test_mission_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, MISSION)


def test_mission_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, MISSION)


def test_mission_objective_progress_isolated(lib, world_factory):
    def change(w, ids, st):
        assert lib.om_mission_objective_count(w) > 0, "setup: mission has no objective"
        lib.om_mission_set_objective_completion(w, 0, 0.37)
    _isolated(lib, world_factory, MISSION, change)


# ---- fog (section 6) ----

def test_fog_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, FOG)


def test_fog_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, FOG)


def test_fog_ping_isolated(lib, world_factory):
    _isolated(lib, world_factory, FOG,
              lambda w, ids, st: lib.om_command_ping(w, ids[3], 0, 8100.0, 7800.0))


# ---- macro (section 7) ----

def test_macro_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, MACRO)


def test_macro_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, MACRO)


def test_macro_behavior_change_isolated(lib, world_factory):
    _isolated(lib, world_factory, MACRO,
              lambda w, ids, st: lib.om_macro_set_state(w, 0, OM_MACRO_PATROL, 1))


# ---- support (section 8, structures) ----

def test_support_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, SUPPORT_MAP)


def test_support_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, SUPPORT_MAP)


def test_support_structure_capture_progress_isolated(lib, world_factory):
    _isolated(lib, world_factory, SUPPORT_MAP,
              lambda w, ids, st: lib.om_structure_set_capture_progress(w, st, 0.41))


# ---- mapgen (section 8, map) ----

def test_mapgen_section_nonzero_after_100_ticks(lib, world_factory):
    _nonzero(lib, world_factory, SUPPORT_MAP)


def test_mapgen_section_deterministic_600_ticks(lib, world_factory):
    _deterministic(lib, world_factory, SUPPORT_MAP)


def test_mapgen_cover_added_isolated(lib, world_factory):
    _isolated(lib, world_factory, SUPPORT_MAP,
              lambda w, ids, st: lib.om_map_add_cover(w, 7000.0, 7000.0, 60.0, 2.0))
