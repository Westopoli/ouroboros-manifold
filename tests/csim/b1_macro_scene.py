"""Shared scene helpers for the B1 enemy-state-machine tests (plan item B1,
docs/northstar/plans/2026-09-30-mission-plays-plan.md). Same scene recipe as
test_core_macro_group_orders.py: a 2-region DEFENSIVE_STAND mission with zero
composed units, so only the squads a test spawns are in the scene, and enemy
macro force 0 is registered by the mission (om_macro_init_force)."""
import math

from conftest import OMArchetype, OMEdge, OMFeature, set_edge, set_faction, set_owner

RAIDER = 0
DEFENSIVE_STAND = 0
PLAYER_FAC = 0
ENEMY_FAC = 1

OM_MACRO_ADVANCE = 0
OM_MACRO_DEFEND = 1
OM_MACRO_PATROL = 2
OM_MACRO_AMBUSH = 3
OM_MACRO_RETREAT = 4
OM_MACRO_MOD_CAUTIOUS = 0
OM_MACRO_MOD_AGGRESSIVE = 1
OM_MACRO_CMD_MOVE = 0
OM_MACRO_CMD_ATTACK_MOVE = 1

# csrc/om_constants.h OM_ROSTER_RAIDER_*: weapon range 200, sensor 800, speed 150, hp 250.
RAIDER_RANGE = 200.0
RAIDER_SENSOR = 800.0
RAIDER_HP = 250.0

# B9-6 fixed MVP layout (csrc/mission.c om_mission_instantiate_map).
CANVAS = 16000.0
ENEMY_SPAWN_X = CANVAS / 2.0
ENEMY_SPAWN_Y = CANVAS - 15.0


def tactical_world(lib, world_factory, seed=1):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)
    return w


def spawn_enemy_squad(lib, w, n=3, x0=ENEMY_SPAWN_X, y0=ENEMY_SPAWN_Y, spacing=40.0):
    return [lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, x0 + i * spacing, y0, 0) for i in range(n)]


def centroid(lib, w, ids):
    pts = [lib.om_unit_get_pos(w, uid) for uid in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])
