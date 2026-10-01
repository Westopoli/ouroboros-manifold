"""B1-4 (plan 2026-09-30, item B1) integration: a force in ambush fires on
contact through the real tactical step (om_tactical_step), not through a
direct om_macro_tick call.

RED on main: the ambush force is never ordered to close, the player sits at
700 wu outside the 200 wu RAIDER weapon range, and nobody fires.
Trigger range is flagged undefined; see test_E14_S120_B1_3 docstring.
"""
from b1_macro_scene import (
    ENEMY_SPAWN_X, ENEMY_SPAWN_Y, OM_MACRO_AMBUSH, OM_MACRO_MOD_CAUTIOUS, PLAYER_FAC,
    RAIDER, RAIDER_HP, spawn_enemy_squad, tactical_world,
)

MAX_STEPS = 1500


def _run(lib, world_factory, player_dx):
    w = tactical_world(lib, world_factory)
    spawn_enemy_squad(lib, w)
    lib.om_macro_set_state(w, 0, OM_MACRO_AMBUSH, OM_MACRO_MOD_CAUTIOUS)
    player = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, ENEMY_SPAWN_X + player_dx, ENEMY_SPAWN_Y, 0)
    first_damage_step = None
    for step in range(MAX_STEPS):
        lib.om_tactical_step(w)
        if lib.om_unit_get_hp(w, player) < RAIDER_HP:
            first_damage_step = step
            break
    return first_damage_step


def test_R_120_02_ambush_force_fires_on_contact_through_tactical_step(lib, world_factory):
    """R-120-02 integration: a hidden ambush force with a player unit in range attack-moves in and damages it, driven only by om_tactical_step."""
    step = _run(lib, world_factory, 700.0)
    assert step is not None, "R-120-02: ambush force never fired on a player unit in range within the step budget"


def test_R_120_02_ambush_force_does_not_fire_when_nobody_enters_range(lib, world_factory):
    """Positive control for the integration test: the same scene with the player out of sight takes no damage over the same budget, so the damage above is caused by the trigger."""
    assert _run(lib, world_factory, 2000.0) is None
