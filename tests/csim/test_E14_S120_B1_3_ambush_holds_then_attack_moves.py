# Rule pins: R-087-04@74cc9c, R-120-02@5c2e20
"""B1-3 (plan 2026-09-30, item B1): ambush holds in cover until a player group
enters range, then becomes advance_aggressive and attack-moves (R-120-02).

RED on main: ambush has no order branch and nothing ever calls
om_macro_trigger_ambush, so the force stays AMBUSH and hidden forever even
with a player unit parked in its sensor range.

The bible's "trigger radius" is undefined (Q-120-02 gives no number). These
tests use "a player unit this force can see" (om_unit_can_see, the same
contact test advance uses; RAIDER sensor 800 wu) as the trigger, put the
player at 700 wu (visible, outside the 200 wu weapon range so the force must
MOVE to engage) for the contact case and at 2000 wu (out of sight) for the
hold case, and flag the choice in the report.
"""
import pytest

from b1_macro_scene import (
    ENEMY_SPAWN_X, ENEMY_SPAWN_Y, OM_MACRO_ADVANCE, OM_MACRO_AMBUSH, OM_MACRO_MOD_AGGRESSIVE,
    OM_MACRO_MOD_CAUTIOUS, PLAYER_FAC, RAIDER, RAIDER_RANGE, RAIDER_SENSOR,
    centroid, dist, spawn_enemy_squad, tactical_world,
)

NEAR = 700.0
FAR = 2000.0


def _ambush_scene(lib, world_factory, player_dx):
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w)
    lib.om_macro_set_state(w, 0, OM_MACRO_AMBUSH, OM_MACRO_MOD_CAUTIOUS)
    player = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, ENEMY_SPAWN_X + player_dx, ENEMY_SPAWN_Y, 0)
    assert player != 0
    return w, ids, player


def test_R_120_02_ambush_holds_while_no_player_is_in_range(lib, world_factory):
    """R-120-02: ambush holds hidden until an enemy enters its trigger radius: with the player out of sight for 600 ticks the squad does not move, stays hidden and stays in ambush. Also the control for the contact test below: the contact test's movement is caused by the player being in range."""
    w, ids, _ = _ambush_scene(lib, world_factory, FAR)
    assert FAR > RAIDER_SENSOR
    start = centroid(lib, w, ids)
    lib.om_tactical_tick_to(w, 600)
    assert dist(start, centroid(lib, w, ids)) == pytest.approx(0.0, abs=1e-6)
    assert lib.om_macro_get_behavior(w, 0) == OM_MACRO_AMBUSH
    assert lib.om_macro_is_hidden(w, 0) == 1


def test_R_120_02_ambush_triggers_to_advance_aggressive_on_contact(lib, world_factory):
    """R-120-02: when a player unit enters range the ambush becomes advance_aggressive (and unhides) within a few macro evaluations, and never resets."""
    w, ids, _ = _ambush_scene(lib, world_factory, NEAR)
    assert RAIDER_RANGE < NEAR < RAIDER_SENSOR
    lib.om_tactical_tick_to(w, 120)  # three 40-tick evaluations
    assert lib.om_macro_get_behavior(w, 0) == OM_MACRO_ADVANCE, "R-120-02: player in range, ambush never triggered"
    assert lib.om_macro_get_modifier(w, 0) == OM_MACRO_MOD_AGGRESSIVE
    assert lib.om_macro_is_hidden(w, 0) == 0
    lib.om_tactical_tick_to(w, 400)
    assert lib.om_macro_get_behavior(w, 0) == OM_MACRO_ADVANCE, "R-120-02: ambush reset after triggering"


def _engaged(lib, w, ids, player, player_hp0):
    """The engagement happened (R-087-04): the nearest squad unit is within weapon range of the player's CURRENT position (or the player is dead) and the player's hp is below its start value."""
    rng = lib.om_unit_profile_attack_range(w, RAIDER)
    if lib.om_unit_alive(w, player):
        px, py = lib.om_unit_get_pos(w, player)
        near = min(dist(lib.om_unit_get_pos(w, u), (px, py)) for u in ids if lib.om_unit_alive(w, u))
        in_range = near <= rng
    else:
        in_range = True
    return in_range and lib.om_unit_get_hp(w, player) < player_hp0


def test_R_120_02_ambushers_attack_move_toward_the_trigger(lib, world_factory):
    """R-120-02: once triggered the squad attack-moves toward the player and the engagement happens by tick 150: the nearest squad unit is within weapon range of the player's current position (or the player is dead) and the player has lost hp. Sample tick unchanged (150); H-057 idle units engage on sight, so the player no longer stands untouched and 'closed half the gap to its start' no longer holds (R-087-04)."""
    w, ids, player = _ambush_scene(lib, world_factory, NEAR)
    hp0 = lib.om_unit_get_hp(w, player)
    lib.om_tactical_tick_to(w, 150)
    assert _engaged(lib, w, ids, player, hp0), "R-120-02: ambushers did not engage the player"


def test_R_120_02_engagement_predicate_control_fails_without_contact(lib, world_factory):
    """Control for the test above: with the player out of sight (FAR, ambush never triggers, squad gets no order) the same predicate at the same tick is False."""
    w, ids, player = _ambush_scene(lib, world_factory, FAR)
    hp0 = lib.om_unit_get_hp(w, player)
    lib.om_tactical_tick_to(w, 150)
    assert not _engaged(lib, w, ids, player, hp0)
