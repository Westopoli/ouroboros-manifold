"""B1-5 (plan 2026-09-30, item B1) integration: the rout and objective-contested
bus flags are fed by play, not by test-only setters.

Rules: R-120-02 (retreat plain-moves to the fallback point, the mission's enemy
spawn edge), R-122-02 (a force sets a bus flag another force's hook can read),
R-122-04 (flags are set during a mission), ALG-76 / Q-120-03 (Westley
2026-09-26: a force routs at 35 percent of its hit points remaining), Q-122-01
(a): the runner sets the flags.

Every test drives a real mission through om_tactical_step only. No
om_macro_set_* setter and no om_macro_player_enter_objective is called.
RED on main: om_macro_update_bus_runner has no caller and nothing feeds the
force hp fraction or the objective-entered flag, so no force retreats and no
flag sets. Getters used: om_macro_get_behavior, om_macro_bus_get_flag,
om_unit_get_order_destination, om_unit_get_order_kind, om_unit_get_hp,
om_objective_get_center / om_objective_get_radius. No getter is missing.
"""
import ctypes

from b1_macro_scene import (
    CANVAS, ENEMY_SPAWN_X, ENEMY_SPAWN_Y, OM_MACRO_RETREAT, PLAYER_FAC, RAIDER, RAIDER_HP,
    spawn_enemy_squad, tactical_world,
)
from conftest import OMVec2

EVAL_STEPS = 200  # several 40-tick macro evaluation intervals at any tactical period
FALLBACK = (CANVAS / 2.0, ENEMY_SPAWN_Y)  # R-120-02: the enemy spawn edge point
OBJ_X, OBJ_Y = CANVAS / 2.0, CANVAS / 2.0


def _step(lib, w, n=EVAL_STEPS):
    for _ in range(n):
        lib.om_tactical_step(w)


def _flag(lib, w, name):
    return lib.om_macro_bus_get_flag(w, name.encode())


def _dest(lib, w, uid):
    d = OMVec2()
    lib.om_unit_get_order_destination(w, uid, ctypes.byref(d))
    return d.x, d.y


def _rout_world(lib, world_factory, hp_each):
    """Enemy squad starts near the objective (so a fallback move is visible),
    runs one evaluation at full hit points, then takes damage to hp_each each."""
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w, n=3, x0=OBJ_X, y0=OBJ_Y + 500.0)
    _step(lib, w, 60)  # full-health evaluation first: start total is 3 * RAIDER_HP
    assert lib.om_macro_get_behavior(w, 0) != OM_MACRO_RETREAT, "setup: force retreated at full hit points"
    for uid in ids:
        lib.om_unit_set_hp(w, uid, hp_each)
    _step(lib, w)
    return w, ids


def test_R_120_02_R_122_02_force_below_35_percent_routs_and_sets_flag(lib, world_factory):
    """ALG-76: 3 x 80 = 240 of 750 hit points is 32 percent, below 35: the force retreats to the fallback point and force_0_routed reads set."""
    w, ids = _rout_world(lib, world_factory, 80.0)
    assert lib.om_macro_get_behavior(w, 0) == OM_MACRO_RETREAT, "ALG-76: force at 32 percent hit points did not retreat"
    for uid in ids:
        x, y = _dest(lib, w, uid)
        assert (x, y) == FALLBACK, f"R-120-02: retreating unit {uid} not moving to the fallback point, dest ({x}, {y})"
    assert _flag(lib, w, "force_0_routed") == 1, "R-122-02: force_0_routed not set on the bus after the force fell below 35 percent"


def test_R_120_02_R_122_02_force_above_35_percent_holds_and_flag_clear(lib, world_factory):
    """Positive control on the same fixture: 3 x 90 = 270 of 750 is 36 percent, above 35: no retreat, no flag."""
    w, ids = _rout_world(lib, world_factory, 90.0)
    assert lib.om_macro_get_behavior(w, 0) != OM_MACRO_RETREAT
    assert _flag(lib, w, "force_0_routed") == 0
    for uid in ids:
        assert _dest(lib, w, uid) != FALLBACK


def _contested_world(lib, world_factory, player_inside):
    w = tactical_world(lib, world_factory)
    spawn_enemy_squad(lib, w)
    c = OMVec2()
    assert lib.om_objective_get_center(w, 0, ctypes.byref(c)) == 1, "setup: no objective centre"
    radius = lib.om_objective_get_radius(w, 0)
    assert radius > 0.0
    off = 0.25 * radius if player_inside else 3.0 * radius
    lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, c.x + off, c.y, 0)
    _step(lib, w)
    return w


def test_R_122_02_player_unit_in_objective_zone_sets_contested_flag(lib, world_factory):
    """R-122-02/R-122-04: a player unit inside the objective-0 zone makes objective_0_contested read set."""
    w = _contested_world(lib, world_factory, True)
    assert _flag(lib, w, "objective_0_contested") == 1, "R-122-02: objective_0_contested not set with a player unit in the zone"


def test_R_122_02_no_player_unit_in_zone_leaves_contested_flag_clear(lib, world_factory):
    """Positive control: the player unit outside the zone leaves the flag clear."""
    w = _contested_world(lib, world_factory, False)
    assert _flag(lib, w, "objective_0_contested") == 0
