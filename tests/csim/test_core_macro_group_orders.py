"""Enemy macro real group orders (B13-8/B9-13).

`om_macro_tick` used to compute `om_macro_command_for_behavior(f->behavior)`
per force every 40-tick evaluation and only LOG it (R-123-02's replay
stream) -- it never issued the order, so enemy forces never moved; only the
per-unit AI auto-engaged whatever came into range on its own.

R-120-02 (Q-120-02, Westley 2026-09-28): advance attack-moves to the
mission's objective until the force has contact (a visible player unit in
range, or damage taken this evaluation), then re-targets the nearest player
unit group centroid; rout ("retreat") moves back toward the enemy spawn
edge. R-123-02 (Q-123-01): macro force 0 is the first enemy force, indexed
separately from the player's.

Each test spawns its own small, controlled enemy squad (RAIDER, the fastest
roster type, 150 wu/s) rather than relying on the mission's RNG-driven force
composition, so distances and margins are deterministic and generous. The
mission is DEFENSIVE_STAND with no conflict context set, so its own composed
enemy force is 0 units (same convention as test_core_wave_spawn.py) and does
not interfere with the hand-placed squad.

RED on main: om_macro_tick never calls a command function, so every
after-tick position below is bit-identical to its before-tick position.
"""
import ctypes
import math

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    OMVec2,
    set_edge,
    set_faction,
    set_owner,
)

RAIDER = 0
DEFENSIVE_STAND = 0
PLAYER_FAC = 0
ENEMY_FAC = 1

# csrc/enemy_macro.c anonymous enums (om_macro_execute_behavior / _set_state).
OM_MACRO_ADVANCE = 0
OM_MACRO_DEFEND = 1
OM_MACRO_RETREAT = 4
OM_MACRO_MOD_CAUTIOUS = 0

# B9-6 fixed MVP layout (csrc/mission.c om_mission_instantiate_map):
# MEDIUM canvas (DEFENSIVE_STAND), objective at canvas/2, enemy spawn anchor
# at (canvas/2, canvas - edge).
CANVAS = 16000.0
EDGE = 15.0  # OM_UNIT_COLLISION_RADIUS
ENEMY_SPAWN_X = CANVAS / 2.0
ENEMY_SPAWN_Y = CANVAS - EDGE
OBJECTIVE_X = CANVAS / 2.0
OBJECTIVE_Y = CANVAS / 2.0


def _tactical_world(lib, world_factory, seed=1):
    """2-region world with factions and a DEFENSIVE_STAND mission (0 composed
    enemy/player units: no conflict context set), so only the hand-placed
    squad each test spawns afterward is in the scene."""
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)  # tactical phase
    return w


def _objective_center(lib, w):
    ctr = OMVec2()
    ok = lib.om_objective_get_center(w, 0, ctypes.byref(ctr))
    assert ok == 1, "setup check: no objective node found"
    return ctr.x, ctr.y


def _centroid(lib, w, ids):
    xs, ys = [], []
    for uid in ids:
        x, y = lib.om_unit_get_pos(w, uid)
        xs.append(x)
        ys.append(y)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _spawn_enemy_cluster(lib, w, n, x0, y0, spacing=40.0):
    """n RAIDER units for ENEMY_FAC in a tight cluster at (x0, y0)."""
    return [lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, x0 + i * spacing, y0, 0) for i in range(n)]


# ---- (a) advance closes ≥50% of the distance to the objective in 600 ticks ----

def test_a_advance_closes_half_the_distance_to_objective_in_600_ticks(lib, world_factory):
    """R-120-02: advance attack-moves toward the mission's objective. With no
    player units in the scene at all (no player input possible), the
    registered force's centroid closes at least 50% of its distance to the
    objective within 600 tactical ticks (30 s at OM_TACTICAL_TICK_RATE=20)."""
    w = _tactical_world(lib, world_factory)
    enemy_ids = _spawn_enemy_cluster(lib, w, 5, ENEMY_SPAWN_X, ENEMY_SPAWN_Y)

    # Setup check: no player units exist in this scene at all (DEFENSIVE_STAND
    # with committed_budget 0 -> 0 composed player units too) -- "no player
    # input" is not just "no command sent", there is no player force to input.
    assert lib.om_unit_count(w) == len(enemy_ids)

    obj_x, obj_y = _objective_center(lib, w)
    cx0, cy0 = _centroid(lib, w, enemy_ids)
    d0 = _dist(cx0, cy0, obj_x, obj_y)
    assert d0 > 1000.0, "setup check: enemy squad should start far from the objective"

    lib.om_tactical_tick_to(w, 600)

    cx1, cy1 = _centroid(lib, w, enemy_ids)
    d1 = _dist(cx1, cy1, obj_x, obj_y)
    assert d1 <= 0.5 * d0, (
        f"R-120-02: enemy centroid distance to objective fell from {d0:.1f} to "
        f"{d1:.1f}, less than the required 50% closure"
    )


# ---- (b) contact re-targets the force to the player unit ----------------------

def _engaged(lib, w, enemy_ids, player_id, player_hp0):
    """The engagement happened (R-087-04): the nearest squad unit is within weapon range of the player's CURRENT position (or the player is dead) and the player's hp is below its start value."""
    rng = lib.om_unit_profile_attack_range(w, RAIDER)
    if lib.om_unit_alive(w, player_id):
        px, py = lib.om_unit_get_pos(w, player_id)
        near = min(_dist(*lib.om_unit_get_pos(w, u), px, py) for u in enemy_ids if lib.om_unit_alive(w, u))
        in_range = near <= rng
    else:
        in_range = True
    return in_range and lib.om_unit_get_hp(w, player_id) < player_hp0


def test_b_contact_with_a_player_unit_retargets_the_force_to_it(lib, world_factory):
    """R-120-02/Q-120-02: once the force has contact (a visible player unit in
    range), it re-targets the nearest player unit group centroid instead of
    the objective. The player unit here sits 500 wu east of the enemy squad
    (well within RAIDER's 800 wu sensor radius) -- a direction perpendicular
    to the objective (due south), so closing on the player and closing on
    the objective are distinguishable. H-057 (R-087-04): idle units engage on
    sight, so the pass mark is the engagement itself at the same tick 150,
    not closing half the gap to the player's start position."""
    w = _tactical_world(lib, world_factory)
    enemy_ids = _spawn_enemy_cluster(lib, w, 3, ENEMY_SPAWN_X, ENEMY_SPAWN_Y)
    player_x, player_y = ENEMY_SPAWN_X + 500.0, ENEMY_SPAWN_Y
    player_id = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, player_x, player_y, 0)
    assert player_id != 0
    player_hp0 = lib.om_unit_get_hp(w, player_id)

    obj_x, obj_y = _objective_center(lib, w)
    cx0, cy0 = _centroid(lib, w, enemy_ids)
    d_player_0 = _dist(cx0, cy0, player_x, player_y)
    d_obj_0 = _dist(cx0, cy0, obj_x, obj_y)
    assert d_player_0 == pytest.approx(500.0, abs=50.0)

    lib.om_tactical_tick_to(w, 150)  # past the first 40-tick evaluation

    cx1, cy1 = _centroid(lib, w, enemy_ids)
    d_obj_1 = _dist(cx1, cy1, obj_x, obj_y)

    assert _engaged(lib, w, enemy_ids, player_id, player_hp0), (
        "Q-120-02: enemy squad did not engage the contacted player unit"
    )
    assert d_obj_1 >= 0.9 * d_obj_0, (
        f"Q-120-02: enemy squad closed on the objective instead of the "
        f"contacted player unit (distance {d_obj_0:.1f} -> {d_obj_1:.1f})"
    )


def test_b_engagement_predicate_control_fails_without_contact(lib, world_factory):
    """Control for test_b: with the player beyond the 800 wu sensor (1500 wu
    east, no contact, no order toward it) the same predicate at tick 150 is
    False."""
    w = _tactical_world(lib, world_factory)
    enemy_ids = _spawn_enemy_cluster(lib, w, 3, ENEMY_SPAWN_X, ENEMY_SPAWN_Y)
    player_id = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, ENEMY_SPAWN_X + 1500.0, ENEMY_SPAWN_Y, 0)
    player_hp0 = lib.om_unit_get_hp(w, player_id)
    lib.om_tactical_tick_to(w, 150)
    assert not _engaged(lib, w, enemy_ids, player_id, player_hp0)


# ---- (c) rout moves the force away from the objective --------------------------

def test_c_rout_moves_the_force_away_from_the_objective(lib, world_factory):
    """R-120-02: rout ("retreat") plain-moves back toward the enemy's own
    spawn edge (csrc/mission.c's fallback point), away from the objective."""
    w = _tactical_world(lib, world_factory)
    # Placed near the objective, simulating a force that had already advanced.
    start_x, start_y = OBJECTIVE_X, OBJECTIVE_Y + 500.0
    enemy_ids = _spawn_enemy_cluster(lib, w, 3, start_x, start_y)

    lib.om_macro_set_state(w, 0, OM_MACRO_RETREAT, OM_MACRO_MOD_CAUTIOUS)
    assert lib.om_macro_get_behavior(w, 0) == OM_MACRO_RETREAT

    obj_x, obj_y = _objective_center(lib, w)
    cx0, cy0 = _centroid(lib, w, enemy_ids)
    d0 = _dist(cx0, cy0, obj_x, obj_y)
    assert d0 == pytest.approx(500.0, abs=50.0)

    lib.om_tactical_tick_to(w, 100)

    cx1, cy1 = _centroid(lib, w, enemy_ids)
    d1 = _dist(cx1, cy1, obj_x, obj_y)
    assert d1 > d0 + 200.0, (
        f"R-120-02: routed force did not move away from the objective "
        f"(distance {d0:.1f} -> {d1:.1f})"
    )
