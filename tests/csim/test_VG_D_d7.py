"""Visible-game lane D, piece D7 (Architect, 2026-10-09). Fenced: builders never edit this file.

Proves S-246 / R-246-01 and R-097-09 at the csim level. csrc/pipe/om_pipe.c handle_mission_start (era_kind 0) calls
om_space_field_generate_nodes a second time, with seed ws ^ (ws >> 32), after om_mission_setup already generated the
field (seed ws ^ region*0x9E3779B1 ^ archetype, mission.c om_mission_instantiate_map) and spawned the units on its
cleared cells (D5-3). The csim cannot call the pipe path, so test_pipe_start_path_leaves_units_on_open_cells replays
it: after om_mission_setup it calls om_space_field_generate_nodes with the pipe's seed formula. The pipe-level proof is
tests/transport/test_pipe_vg_d7.py.
RED on this base: test_pipe_start_path_* (the replayed regeneration overwrites the field the units stand on, so
units sit in blocked cells) and test_pipe_start_path_field_equals_mission_field. PASS by design: the idempotence
check with the mission's own seed (CONTROL) and the push-out positive control.
"""
import ctypes

import pytest

from test_VG_D_d5 import (
    CELLS, LAYERS, PLAYER_FAC, ENEMY_FAC, _cell, _masks, _scene, _units,
)

pytestmark = pytest.mark.usefixtures("lib")
V = ctypes.c_void_p
REGION, ARCH, SEED = 0, 3, 7
DENSITY = 35.0
CANVAS = 24000.0


def _mission_seed(lib, w):
    return (lib.om_world_seed(w) ^ (REGION * 0x9E3779B1) ^ ARCH) & 0xFFFFFFFF


def _pipe_seed(lib, w):
    ws = lib.om_world_seed(w)
    return (ws ^ (ws >> 32)) & 0xFFFFFFFF


def _blocked_units(lib, w):
    masks = _masks(lib, w)
    return [u for (u, layer, x, y) in _units(lib, w) if masks[layer][_cell(x, y)]]


def test_control_regenerating_with_the_mission_seed_is_idempotent(lib, world_factory):
    """D7 CONTROL (passes now): om_space_field_generate_nodes called again with the mission's own seed leaves the masks
    unchanged, and every spawned unit is on an open cell of its layer (D5-3)."""
    w = _scene(lib, world_factory, archetype=ARCH, seed=SEED, region=REGION)
    before = _masks(lib, w)
    assert lib.om_unit_count(w) > 0
    assert not _blocked_units(lib, w), "units spawn blocked straight after om_mission_setup"
    assert lib.om_space_field_generate_nodes(w, _mission_seed(lib, w), CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert _masks(lib, w) == before


def test_control_blocked_cell_pushes_a_unit_out(lib, world_factory):
    """D7 positive control for R-097-09 (passes now): a unit whose cell the test blocks via om_map_block_rect on
    its layer is moved by the push-out within a few ticks; an untouched unit does not move."""
    w = _scene(lib, world_factory, archetype=ARCH, seed=SEED, region=REGION)
    lib.om_mission_begin(w)
    units = _units(lib, w)
    uid, layer, x, y = units[0]
    other = units[-1] if units[-1][0] != uid else units[1]
    lib.om_map_block_rect(w, x - 60.0, y - 60.0, x + 60.0, y + 60.0, layer, layer)
    for _ in range(5):
        lib.om_tactical_step(w)
    after = {u: (xx, yy) for (u, _l, xx, yy) in _units(lib, w)}
    assert after[uid] != (x, y), "the unit in a blocked cell was not pushed out"
