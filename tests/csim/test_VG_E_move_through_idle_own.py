# Rule pins: R-097-03@6f75ba, R-097-10@a759df
"""VG-E-move-through-idle-own: idle own units yield to a mover; enemies do not.

Proves E-13 R-097-03 (the probe and the steering sweep ignore idle units of the mover's side; if no heading is
clear it continues straight, it does not wait) and R-097-10 (an idle unit takes the full displacement from a
mover of its own side, none from an enemy mover, which takes all of it). Scenario and numbers are from the
VG-E-move-through-idle-own paragraph of docs/northstar/plans/2026-10-07-visible-game-spec.md and the ledger row
FINDING-sim-move-blocked-by-idle-own (42 ordered past 26 idle own, terrain-only ground world, seed 1, layer 2).

UNSTATED INTERFACE CHOICES (none needs product code; a gap is a choice the paragraph leaves open):
- The 42 start positions are the row's probe positions, inlined (a 7 x 6 grid, 30 wu steps, y 220 to 380); the
  order is to (11950, 550) from the group centroid (11950, 300), as in the probe.
- The row gives the 26 idle own units only as "y 420 to 480, spacing about 29"; the exact x are not recorded.
  Choice: three rows y 420, 450, 480 of 9, 9 and 8 units, 30 wu apart, centred on x 11950 (9 wide: 11830..12070).
- Architect ruling 2026-10-23 (row 20): the world is the paragraph's: om_terrain_generate with terrain seed 11 on a
  16000 x 16000 canvas, built as tests/csim/test_E01_T2_collision_mask.py does, because the terrain shapes the
  column and a flat canvas tests a different mechanism. Units are Raiders on the walking movement kind, layer 2.
  Column and idle positions stay as the paragraph row gives them (and the writer's idle rows); checked against
  the layer 2 walk mask: none of the 68 falls on masked terrain, so none was moved.
- Architect ruling 2026-10-23 (row 22): "displaced" for the idle units is EVERY one of the 26 ends away from its
  start and alive, as the paragraph says; all 26 stand inside the column's width, none is behind its edge.
- "Arrives": the centroid of the 42 is within DRAFT-idle-own-arrive-wu = 20 wu of the goal after RUN_TICKS; the
  paragraph gives no tick count (the probe watched 1236 ticks): RUN_TICKS = 1200 is the writer's choice.
- "No clear heading": the `waiting` flag has no getter and the :2417 line sits in the PP baseline path, which runs
  only with OM_TP_PURSUE_BY_STEERING 0 (the default 1 uses om_move_steer_step, which already steps straight).
  The test therefore sets the param to 0 and observes position: a waiting walker never leaves its start, a
  stepping one ends 5 wu ahead (pushed back to 30 wu from the enemy). An enemy ring at 35 wu blocks every probe.
- Determinism trace: the units and movement sections (3, 4) of om_world_checksum_full, as the T2 tests do.
"""
import ctypes
import math

import pytest

from conftest import OMFeature, OMTacParam

RAIDER = 0
OWN, ENEMY = 0, 1
OM_MOVE_WALKING = 1
SEED = 1                  # the walker tests' world seed; the terrain scene uses TERRAIN_SEED
TERRAIN_SEED = 11
LAYER = 2
CANVAS = 16000.0
CELL = 100.0
GOAL = (11950.0, 550.0)
ARRIVE_WU = 20.0          # DRAFT-idle-own-arrive-wu
RUN_TICKS = 1200          # writer's choice, see the header
SHORT_WU = 30.0           # the stall on main: 30 wu short of the idle units (ledger row)
COLUMN = [(11850.0, 220.0), (11850.0, 250.0), (11850.0, 280.0), (11850.0, 320.0), (11850.0, 350.0), (11850.0, 380.0), (11880.0, 220.0), (11880.0, 250.0), (11880.0, 280.0), (11880.0, 320.0), (11880.0, 350.0), (11880.0, 380.0), (11920.0, 220.0), (11920.0, 250.0), (11920.0, 280.0), (11920.0, 320.0), (11920.0, 350.0), (11920.0, 380.0), (11950.0, 220.0), (11950.0, 250.0), (11950.0, 280.0), (11950.0, 320.0), (11950.0, 350.0), (11950.0, 380.0), (11980.0, 220.0), (11980.0, 250.0), (11980.0, 280.0), (11980.0, 320.0), (11980.0, 350.0), (11980.0, 380.0), (12020.0, 220.0), (12020.0, 250.0), (12020.0, 280.0), (12020.0, 320.0), (12020.0, 350.0), (12020.0, 380.0), (12050.0, 220.0), (12050.0, 250.0), (12050.0, 280.0), (12050.0, 320.0), (12050.0, 350.0), (12050.0, 380.0)]
IDLE = [(11830.0 + 30.0 * i, y) for y, n in ((420.0, 9), (450.0, 9), (480.0, 8)) for i in range(n)]


def _world(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, TERRAIN_SEED, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_WALKING) == 0
    return w


def _arr(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def _centroid(lib, w, ids):
    ps = [lib.om_unit_get_pos(w, u) for u in ids]
    return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))


def _scene(lib, w, idle_faction):
    col = [lib.om_unit_spawn(w, RAIDER, OWN, x, y, LAYER) for x, y in COLUMN]
    idle = [lib.om_unit_spawn(w, RAIDER, idle_faction, x, y, LAYER) for x, y in IDLE]
    assert all(col) and all(idle) and len(col) == 42 and len(idle) == 26
    return col, idle


def _run(lib, w, col):
    lib.om_command_move(w, _arr(col), len(col), *GOAL)
    for _ in range(RUN_TICKS):
        lib.om_tactical_step(w)


def test_R_097_10_a_column_ordered_past_idle_own_units_arrives(lib, world_factory):
    """R-097-03 / R-097-10: 42 ordered through 26 idle own units arrive within 20 wu of the goal (red on main (a):
    the column stops about 30 wu short and never moves again)."""
    w = _world(lib, world_factory)
    col, _ = _scene(lib, w, OWN)
    _run(lib, w, col)
    c = _centroid(lib, w, col)
    assert math.hypot(c[0] - GOAL[0], c[1] - GOAL[1]) <= ARRIVE_WU, "stopped at %r, goal %r" % (c, GOAL)


def test_R_097_10_idle_own_units_are_displaced_and_alive(lib, world_factory):
    """R-097-10: an idle unit takes the displacement from an own-side mover; every one of the 26 is displaced and alive (red on main
    (a): nothing moves them because the column never reaches them)."""
    w = _world(lib, world_factory)
    col, idle = _scene(lib, w, OWN)
    _run(lib, w, col)
    assert all(lib.om_unit_alive(w, u) for u in idle)
    still = [p for u, p in zip(idle, IDLE) if lib.om_unit_get_pos(w, u) == p]
    assert not still, "idle own units not displaced: %r" % still


def test_R_097_10_positive_control_a_column_through_an_enemy_line_stops_short(lib, world_factory):
    """Positive control for the detector (green on main, stays green): the same scene with the 26 idle units on the
    ENEMY side. An enemy does not yield and still blocks the probe, so the column ends more than 20 wu short of
    the goal and no enemy is moved. A build that lets enemies yield fails this test."""
    w = _world(lib, world_factory)
    col, idle = _scene(lib, w, ENEMY)
    _run(lib, w, col)
    c = _centroid(lib, w, col)
    assert math.hypot(c[0] - GOAL[0], c[1] - GOAL[1]) > ARRIVE_WU, "the column got through the enemy line"
    assert all(lib.om_unit_get_pos(w, u) == p for u, p in zip(idle, IDLE)), "an idle enemy was displaced"


def test_R_097_03_a_walker_with_no_clear_heading_steps_straight(lib, world_factory):
    """R-097-03: when no probe heading is clear it continues straight, it does not wait (red on main (a): the PP
    baseline path (OM_TP_PURSUE_BY_STEERING 0) sets waiting and returns at tactical_move.c:2417, so M never
    leaves (12000, 300) in 100 ticks). M is ordered to (12000, 900); eight enemies stand 35 wu around it, so
    every probe point is blocked. A straight step ends pushed back to 30 wu from the enemy ahead, y 305."""
    w = world_factory(n_regions=1, seed=SEED)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_tactical_set_param(w, OMTacParam.PURSUE_BY_STEERING, 0.0)
    m = lib.om_unit_spawn(w, RAIDER, OWN, 12000.0, 300.0, 0)
    for k in range(8):
        a = math.radians(45.0 * k)
        assert lib.om_unit_spawn(w, RAIDER, ENEMY, 12000.0 + 35.0 * math.cos(a), 300.0 + 35.0 * math.sin(a), 0)
    lib.om_command_move(w, _arr([m]), 1, 12000.0, 900.0)
    for _ in range(100):
        lib.om_tactical_step(w)
    assert lib.om_unit_get_pos(w, m)[1] > 301.0, "the walker never left its start: it waited"


def test_R_097_03_steering_mode_continues_straight_control(lib, world_factory):
    """Control for the test above (green on main, stays green): the default steering mode (OM_TP_PURSUE_BY_STEERING
    1) already steps straight in the same ring, so the same assertion holds there."""
    w = world_factory(n_regions=1, seed=SEED)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    m = lib.om_unit_spawn(w, RAIDER, OWN, 12000.0, 300.0, 0)
    for k in range(8):
        a = math.radians(45.0 * k)
        assert lib.om_unit_spawn(w, RAIDER, ENEMY, 12000.0 + 35.0 * math.cos(a), 300.0 + 35.0 * math.sin(a), 0)
    lib.om_command_move(w, _arr([m]), 1, 12000.0, 900.0)
    for _ in range(100):
        lib.om_tactical_step(w)
    assert lib.om_unit_get_pos(w, m)[1] > 301.0


def _trace(lib, w):
    buf = (ctypes.c_uint64 * 9)()
    lib.om_world_checksum_full(w, buf, 9)
    return (buf[3], buf[4])


def test_R_097_03_same_seed_and_commands_give_a_byte_identical_trace(lib, world_factory):
    """Determinism: two worlds, same seed and command stream, same units and movement sections after the run
    (green on main, stays green)."""
    traces = []
    for _ in range(2):
        w = _world(lib, world_factory)
        col, _ = _scene(lib, w, OWN)
        lib.om_command_move(w, _arr(col), len(col), *GOAL)
        for _ in range(300):
            lib.om_tactical_step(w)
        traces.append(_trace(lib, w))
    assert traces[0] == traces[1]
