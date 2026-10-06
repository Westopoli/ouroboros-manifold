"""E-17 S-190 / R-190-02 (terrain stage 2, spec 2026-10-06, "unit" lane): spawn on the ground.

In om_unit_spawn_internal a walking type is placed on the band under its position (layer =
om_terrain_band_at - 1; on a slope the band of its side of the midline), whatever layer the caller
passed. A walking type at a position with no walkable cell on that band returns 0, before any unit
state moves (the next unit id is unchanged). A flying type's spawn is unchanged.

Red now: the spawn path is not edited yet, so a walker keeps the caller's layer (stub reason) and a
walker over steep ground spawns instead of returning 0. The flyer test is a GUARD (passes today).
"""
import pytest

from b1_macro_scene import PLAYER_FAC, RAIDER, tactical_world

SEED = 11
CANVAS = 16000.0
CELL_WU = 100.0
OM_MOVE_FLYING, OM_MOVE_WALKING = 0, 1
CALLER_LAYER = 0          # provisional (2026-10-06): a layer that is wrong for every band above 1


@pytest.fixture
def mk(lib, world_factory):
    w = tactical_world(lib, world_factory, seed=7)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


def _cells(lib, w):
    n = int(CANVAS / CELL_WU)
    for j in range(n):
        for i in range(n):
            x, y = (i + 0.5) * CELL_WU, (j + 0.5) * CELL_WU
            yield x, y, lib.om_terrain_band_at(w, x, y), lib.om_terrain_walkable_at(w, x, y)


def _find(lib, w, pred):
    for x, y, band, walk in _cells(lib, w):
        if pred(band, walk):
            return x, y, band
    pytest.fail("seed 11 has no cell for this case")


def test_S_190_walker_spawns_on_its_band(lib, mk):
    assert lib.om_roster_set_movement_kind(mk, RAIDER, OM_MOVE_WALKING) == 0
    x, y, band = _find(lib, mk, lambda b, wk: wk == 1 and b >= 2)
    uid = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, x, y, CALLER_LAYER)
    assert uid != 0
    assert lib.om_unit_get_layer(mk, uid) == band - 1


def test_S_190_walker_on_lowest_band_gets_layer_zero(lib, mk):
    assert lib.om_roster_set_movement_kind(mk, RAIDER, OM_MOVE_WALKING) == 0
    x, y, band = _find(lib, mk, lambda b, wk: wk == 1 and b == 1)
    uid = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, x, y, 3)   # caller layer ignored
    assert uid != 0
    assert lib.om_unit_get_layer(mk, uid) == 0


def test_S_190_flyer_spawn_unchanged(lib, mk):
    assert lib.om_unit_profile_movement_kind(mk, RAIDER) == OM_MOVE_FLYING
    x, y, band = _find(lib, mk, lambda b, wk: wk == 1 and b >= 2)
    uid = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, x, y, CALLER_LAYER)
    assert uid != 0
    assert lib.om_unit_get_layer(mk, uid) == CALLER_LAYER      # not moved to the band
    sx, sy, _ = _find(lib, mk, lambda b, wk: wk == 0)
    uid2 = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, sx, sy, 1)  # a flyer spawns over steep ground
    assert uid2 != 0
    assert lib.om_unit_get_layer(mk, uid2) == 1


def test_S_190_walker_over_steep_ground_returns_zero_and_moves_nothing(lib, mk):
    sx, sy, _ = _find(lib, mk, lambda b, wk: wk == 0)
    probe = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, sx, sy, 0)       # flyer: next id probe
    assert probe != 0
    assert lib.om_roster_set_movement_kind(mk, RAIDER, OM_MOVE_WALKING) == 0
    assert lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, sx, sy, 0) == 0
    assert lib.om_roster_set_movement_kind(mk, RAIDER, OM_MOVE_FLYING) == 0
    ok_x, ok_y, _ = _find(lib, mk, lambda b, wk: wk == 1)
    nxt = lib.om_unit_spawn(mk, RAIDER, PLAYER_FAC, ok_x, ok_y, 0)
    assert nxt == probe + 1, "a refused walker spawn must not advance next_unit_id"
