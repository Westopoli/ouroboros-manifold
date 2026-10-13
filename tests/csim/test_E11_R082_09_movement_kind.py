"""E-11 R-082-09 (terrain stage 2, spec 2026-10-06, "unit" lane): a unit type has a movement kind.

Contract piece (push/terrain2-base) holds the working bodies of om_roster_set_movement_kind and
om_unit_profile_movement_kind, so every test here is a GUARD: it passes today and keeps the
contract honest while the lanes land. Set and get; an unknown type or kind is refused (1 and 2);
the kind survives save and load; changing it changes the move section hash (checksum section 4).
"""
import ctypes

import pytest

from b1_macro_scene import RAIDER, tactical_world
from test_net_section_hashes import MOVEMENT, _secs

OM_MOVE_FLYING, OM_MOVE_WALKING, OM_MOVE_SWIMMING = 0, 1, 2
UNKNOWN_TYPE = 9999   # provisional (2026-10-06)
NEGATIVE_TYPE = -1
UNKNOWN_KIND = 3      # provisional (2026-10-06): one past OM_MOVE_SWIMMING
NEGATIVE_KIND = -1


def _world(lib, world_factory):
    return tactical_world(lib, world_factory, seed=7)


def _save_load(lib, src, dst):
    size = lib.om_save_state_size(src)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(src, buf, size)
    return lib.om_load_state_read(dst, buf, size)


def test_guard_R_082_09_default_kind_is_flying(lib, world_factory):
    w = _world(lib, world_factory)
    assert lib.om_unit_profile_movement_kind(w, RAIDER) == OM_MOVE_FLYING


@pytest.mark.parametrize("kind", [OM_MOVE_WALKING, OM_MOVE_SWIMMING, OM_MOVE_FLYING])
def test_guard_R_082_09_set_then_get(lib, world_factory, kind):
    w = _world(lib, world_factory)
    assert lib.om_roster_set_movement_kind(w, RAIDER, kind) == 0
    assert lib.om_unit_profile_movement_kind(w, RAIDER) == kind


@pytest.mark.parametrize("bad", [UNKNOWN_TYPE, NEGATIVE_TYPE])
def test_guard_R_082_09_unknown_type_refused(lib, world_factory, bad):
    w = _world(lib, world_factory)
    assert lib.om_roster_set_movement_kind(w, bad, OM_MOVE_WALKING) == 1


@pytest.mark.parametrize("bad", [UNKNOWN_KIND, NEGATIVE_KIND])
def test_guard_R_082_09_unknown_kind_refused_and_unchanged(lib, world_factory, bad):
    w = _world(lib, world_factory)
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_WALKING) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, bad) == 2
    assert lib.om_unit_profile_movement_kind(w, RAIDER) == OM_MOVE_WALKING


def test_guard_R_082_09_kind_changes_move_section_hash(lib, world_factory):
    w = _world(lib, world_factory)
    flying = _secs(lib, w)[MOVEMENT]
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_WALKING) == 0
    walking = _secs(lib, w)[MOVEMENT]
    assert walking != flying
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_FLYING) == 0
    assert _secs(lib, w)[MOVEMENT] == flying


def test_guard_R_082_09_kind_survives_save_and_load(lib, world_factory):
    src = _world(lib, world_factory)
    assert lib.om_roster_set_movement_kind(src, RAIDER, OM_MOVE_WALKING) == 0
    dst = _world(lib, world_factory)
    assert lib.om_unit_profile_movement_kind(dst, RAIDER) == OM_MOVE_FLYING
    assert _save_load(lib, src, dst) == 0
    assert lib.om_unit_profile_movement_kind(dst, RAIDER) == OM_MOVE_WALKING
    assert _secs(lib, dst)[MOVEMENT] == _secs(lib, src)[MOVEMENT]
