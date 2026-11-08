"""E-13 Invariants / R-207-06 / R-207-07 / R-097-01 / R-207-05 / R-190-07 (engine rule fixes 2026-11-08, F1): a unit never enters a
blocked cell, and a walker routes round an obstacle.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F1"; evidence docs/reports/2026-11-07-rule-enforcement.md and
appendix A (14 position writers, one guarded). Bug fix, not a story. Rulings: Westley 2026-11-07 "lab boxes are obstacles, never
entered".

Rule words proved (docs/bible/epics/E-13-*.md, as written 2026-11-08):
  E-13 Invariants   "A unit never enters a blocked cell."
  R-207-06          a unit is never inside a blocked cell at the end of a tick (a unit placed inside one, such as a wall built on it, is
                    ejected: the repair this file keeps as a control)
  R-207-07          a unit's position is always inside the canvas
  R-097-01          a route is the shortest path on the 100 wu grid
  R-207-05          a walker's route is the least-time path on its layer
  R-190-07          "an obstacle is a detour, never a full stop"
Rule pins: R-207-06, R-207-07, R-097-01, R-207-05, R-190-07, R-097-03.

Scene: a 2000 x 2000 canvas, one box, column x 500..600 by y 0..800 on every layer (om_map_block_rect, the lab's call). The only
oracle for "blocked" is the engine's own om_navmesh_is_cell_blocked(cx, cy, layer), never a Python re-derivation. Units are the
built-in roster (Raider speed 150 wu/s = 7.5 wu per tick), walking kind where the test says so, flying (the default) otherwise.

Measured on the unfixed tree (2026-11-08, Raider, goal (900, 400) across the box from (300, 400)):
  walker, no terrain  121 of 300 ticks inside the box, parked at (492, 450) saw-toothing, never arrives (router blind to mapgen boxes)
  walker, flat terrain 13 ticks inside the box (walk mask ignores the box once terrain exists), arrives
  twelve walkers      1271 unit-ticks inside the box in 400 ticks
  kiting unit         65 of 200 ticks inside, flier or walker (kiting move has no guard); retreat point outside the canvas: x reaches 2007.5
Controls green today: flier across the box (steer step guards), flinch beside the box and at the canvas edge, a plain move past the
canvas edge, a unit with a wall built on it is ejected, and a free walker is unaffected by a box it does not meet.

Detector bounds (not rules; Westley's to change): DEPTH 0 wu (the end of a tick in a blocked cell at all counts here: a csim scene has no
sub-cell rounding to excuse; the lab oracle allows the 1 wu of DRAFT-inv-cell-depth), ARRIVE 40 wu, RUN limits are generous run caps.
"""
import ctypes

import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, pos, spawn, step

CANVAS = 2000.0
BOX = (500.0, 0.0, 600.0, 800.0)      # column 5, rows 0..7, every layer
GOAL = (900.0, 400.0)
ARRIVE = 40.0                          # detector bound
RUN = 600                              # generous cap: the detour is about 1200 wu at 7.5 wu per tick
WALKING = 1                            # OM_MOVE_WALKING
SEED = 11


def _world(lib, wf, walk, box=True, terrain=False):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    if terrain:
        # flat terrain: every cell one band, so the walk mask of layer 0 is open and the box is the only obstacle (as the lab's apply does)
        assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
        cm = (ctypes.c_int32 * 400)(*([7000] * 400))
        assert lib.om_terrain_set_heights(w, cm, 20, 20) == 1
    if walk:
        for t in (RAIDER, VANGUARD):
            assert lib.om_roster_set_movement_kind(w, t, WALKING) == 0
    if box:
        assert lib.om_map_block_rect(w, *BOX, 0, 4) == 0
    return w


def _blocked(lib, w, p, layer=0):
    return bool(lib.om_navmesh_is_cell_blocked(w, int(p[0] // 100), int(p[1] // 100), layer))


def _inside_ticks(lib, w, units, ticks, layer=0):
    """Per tick: every (tick, unit, position) that ends a tick inside a blocked cell of its layer."""
    bad = []
    for t in range(1, ticks + 1):
        step(lib, w)
        for u in units:
            p = pos(lib, w, u)
            if _blocked(lib, w, p, layer):
                bad.append((t, u, (round(p[0], 1), round(p[1], 1))))
    return bad


def _order(lib, w, kind, ids, goal):
    if kind == "attack_move":
        attack_move(lib, w, ids, *goal)
    else:
        lib.om_command_move(w, ids, len(ids), *goal)


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# ------------------------------------------------------------------ red today: the walker, the kiting move

@pytest.mark.parametrize("kind", ["move", "attack_move"])
def test_R_207_06_a_walker_ordered_across_a_box_never_ends_a_tick_in_a_blocked_cell(lib, world_factory, kind):
    """R-207-06 / E-13 Invariants: 'A unit never enters a blocked cell.' One walker, ordered from (300,400) to (900,400) across the box,
    ends no tick inside it. Red today: the walker step has no guard (121 of 300 ticks inside, the saw-tooth at the face)."""
    w = _world(lib, world_factory, walk=True)
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    _order(lib, w, kind, [a], GOAL)
    bad = _inside_ticks(lib, w, [a], 300)
    assert not bad, "%d of 300 ticks inside a blocked cell, first %s" % (len(bad), bad[:3])


@pytest.mark.parametrize("kind", ["move", "attack_move"])
def test_R_097_01_a_walker_ordered_across_a_box_goes_round_it_and_arrives(lib, world_factory, kind):
    """R-097-01 / R-207-05 / R-190-07 'an obstacle is a detour, never a full stop': the same walker reaches the far side. The box ends at
    y = 800, so the shortest path round it is open. Red today: the router does not see mapgen boxes with no terrain, the walker parks
    at the face ((492, 450)) and never arrives."""
    w = _world(lib, world_factory, walk=True)
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    _order(lib, w, kind, [a], GOAL)
    for _ in range(RUN):
        step(lib, w)
        if _dist(pos(lib, w, a), GOAL) <= ARRIVE:
            return
    pytest.fail("never arrived: at %s after %d ticks, goal %s" % (tuple(round(v, 1) for v in pos(lib, w, a)), RUN, GOAL))


def test_R_207_06_a_walker_on_a_terrain_world_does_not_walk_through_a_box(lib, world_factory):
    """R-207-06 with terrain (E-01 R-001-07 walk mask): once terrain exists the walker's blocked test reads the walk mask and ignores the
    box (tactical_move.c:1276). Flat terrain, box on every layer, same order. Red today: 13 ticks inside the box."""
    w = _world(lib, world_factory, walk=True, terrain=True)
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    lib.om_command_move(w, [a], 1, *GOAL)
    bad = _inside_ticks(lib, w, [a], 300)
    assert not bad, "%d ticks inside a blocked cell on a terrain world, first %s" % (len(bad), bad[:3])


def test_R_097_01_a_walker_on_a_terrain_world_still_arrives(lib, world_factory):
    """R-097-01: the router must agree with the blocked test on a terrain world too (one definition of blocked). It arrives, and it
    has not been inside the box on the way. Red today: it arrives, through the box."""
    w = _world(lib, world_factory, walk=True, terrain=True)
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    lib.om_command_move(w, [a], 1, *GOAL)
    inside = 0
    for _ in range(RUN):
        step(lib, w)
        inside += _blocked(lib, w, pos(lib, w, a))
        if _dist(pos(lib, w, a), GOAL) <= ARRIVE:
            break
    else:
        pytest.fail("never arrived at %s, at %s" % (GOAL, pos(lib, w, a)))
    assert inside == 0, "arrived, but %d ticks of the way were inside the box" % inside


def test_R_207_06_twelve_attack_moving_walkers_never_end_a_tick_in_a_blocked_cell(lib, world_factory):
    """R-207-06: a blob of 12 walkers pushing into the same face (collision pushes included: the PUSH writer). Red today:
    1271 unit-ticks inside in 400 ticks."""
    w = _world(lib, world_factory, walk=True)
    ids = [spawn(lib, w, RAIDER, 0, 300 + 30 * (i % 3), 300 + 30 * (i // 3)) for i in range(12)]
    attack_move(lib, w, ids, *GOAL)
    bad = _inside_ticks(lib, w, ids, 400)
    assert not bad, "%d unit-ticks inside a blocked cell, first %s" % (len(bad), bad[:3])


@pytest.mark.parametrize("walk", [True, False], ids=["walker", "flier"])
def test_R_207_06_a_kiting_unit_retreating_across_a_box_never_ends_a_tick_in_a_blocked_cell(lib, world_factory, walk):
    """R-207-06: a kiting unit (om_command_attack_target_kiting) at (450,400) with its retreat point (900,400) across the box. The
    kiting move (tactical_move.c:2414) has no guard. Red today: 65 of 200 ticks inside, flier or walker."""
    w = _world(lib, world_factory, walk=walk)
    a = spawn(lib, w, RAIDER, 0, 450, 400)
    t = spawn(lib, w, SUPPLY, 1, 300, 400)
    lib.om_command_attack_target_kiting(w, a, t, *GOAL)
    bad = _inside_ticks(lib, w, [a], 200)
    assert not bad, "%d of 200 ticks inside a blocked cell, first %s" % (len(bad), bad[:3])


def test_R_207_07_a_kiting_unit_whose_retreat_point_is_outside_the_canvas_stays_inside_it(lib, world_factory):
    """R-207-07: 'position inside the canvas'. Kiting retreat point (3000, 400) on a 2000 canvas. Red today: x reaches 2007.5."""
    w = _world(lib, world_factory, walk=False, box=False)
    a = spawn(lib, w, RAIDER, 0, 1900, 400)
    t = spawn(lib, w, SUPPLY, 1, 1700, 400)
    lib.om_command_attack_target_kiting(w, a, t, 3000.0, 400.0)
    worst = 0.0
    for _ in range(100):
        step(lib, w)
        worst = max(worst, pos(lib, w, a)[0])
    assert worst <= CANVAS, "x reached %.1f on a canvas %.0f wide" % (worst, CANVAS)


# ------------------------------------------------------------------ green today: controls that must stay

@pytest.mark.parametrize("walk", [True, False], ids=["walker", "flier"])
def test_R_207_07_control_a_plain_move_past_the_canvas_edge_stays_inside_it(lib, world_factory, walk):
    """R-207-07 control (green today): a move order to (3000, 400) ends at the edge, never beyond it, walker or flier."""
    w = _world(lib, world_factory, walk=walk, box=False)
    a = spawn(lib, w, RAIDER, 0, 1800, 400)
    lib.om_command_move(w, [a], 1, 3000.0, 400.0)
    worst = 0.0
    for _ in range(100):
        step(lib, w)
        worst = max(worst, pos(lib, w, a)[0])
    assert worst <= CANVAS


def test_R_207_06_control_a_flier_ordered_across_a_box_stays_out_and_arrives(lib, world_factory):
    """Control (green today, the steer step guards entry): the flying Raider crosses with no tick inside and arrives. Proves the box
    scene, the oracle and the goal are sound, so the walker tests above are red for the walker's sake."""
    w = _world(lib, world_factory, walk=False)
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    lib.om_command_move(w, [a], 1, *GOAL)
    inside = 0
    arrived = False
    for _ in range(RUN):
        step(lib, w)
        inside += _blocked(lib, w, pos(lib, w, a))
        if _dist(pos(lib, w, a), GOAL) <= ARRIVE:
            arrived = True
            break
    assert inside == 0 and arrived, "flier: %d ticks inside, arrived %s" % (inside, arrived)


def test_R_207_06_control_a_walker_that_never_meets_the_box_walks_straight(lib, world_factory):
    """Control (green today and after): with the box away from its line (y 1200 to 2000) the same walker walks the straight line, so the
    detour is the box's doing: it arrives within the straight-line time plus 10 per cent."""
    w = _world(lib, world_factory, walk=True, box=False)
    assert lib.om_map_block_rect(w, 500.0, 1200.0, 600.0, 1999.0, 0, 4) == 0
    a = spawn(lib, w, RAIDER, 0, 300, 400)
    lib.om_command_move(w, [a], 1, *GOAL)
    straight_ticks = _dist((300, 400), GOAL) / 7.5
    for t in range(1, int(straight_ticks * 1.1) + 2):
        step(lib, w)
        if _dist(pos(lib, w, a), GOAL) <= ARRIVE:
            return
    pytest.fail("a free walker did not arrive in %d ticks, at %s" % (straight_ticks * 1.1, pos(lib, w, a)))


def _flinch_scene(lib, wf, victim_xy, attacker_xy, box):
    """A Vanguard (layer 0, reach 0 up 0 down) is shot by a Raider on layer 1 (reach 0 up 1 down) it cannot reach: it flinches
    (R-087-01, the flee step of unit.c), directly away from the attacker."""
    w = _world(lib, wf, walk=False, box=box)
    v = spawn(lib, w, VANGUARD, 1, *victim_xy, 0)
    spawn(lib, w, RAIDER, 0, *attacker_xy, 1)
    lib.om_roster_set_reach(w, RAIDER, 0, 1)
    lib.om_roster_set_reach(w, VANGUARD, 0, 0)
    return w, v


def test_R_207_06_control_a_flinching_unit_beside_a_box_does_not_enter_it(lib, world_factory):
    """Control (green today, must stay when the flinch step is routed through the move side, F1 build 2): the victim at (480,400) flees
    +x toward the box. It flinches (scene control) and ends no tick in the box."""
    w, v = _flinch_scene(lib, world_factory, (480, 400), (330, 400), box=True)
    seen = False
    bad = []
    for t in range(1, 121):
        step(lib, w)
        seen = seen or bool(lib.om_unit_in_flinch(w, v))
        p = pos(lib, w, v)
        if _blocked(lib, w, p):
            bad.append((t, p))
    assert seen, "scene broken: the victim never flinched"
    assert not bad, "flinching unit inside a blocked cell: %s" % bad[:3]


def test_R_207_07_control_a_flinching_unit_at_the_canvas_edge_stays_inside_it(lib, world_factory):
    """Control (green today): the victim at (1960,400) flees +x, toward the edge, and stays inside the canvas."""
    w, v = _flinch_scene(lib, world_factory, (1960, 400), (1810, 400), box=False)
    seen, worst = False, 0.0
    for _ in range(120):
        step(lib, w)
        seen = seen or bool(lib.om_unit_in_flinch(w, v))
        worst = max(worst, pos(lib, w, v)[0])
    assert seen, "scene broken: the victim never flinched"
    assert worst <= CANVAS


@pytest.mark.parametrize("walk", [True, False], ids=["walker", "flier"])
def test_R_207_06_control_a_unit_a_wall_is_built_on_is_ejected(lib, world_factory, walk):
    """R-207-06 repair (keep om_move_leave_blocked, F1 build 4; green today): a unit placed inside a cell, a wall built on it, is out of
    every blocked cell within 5 ticks. It is the repair for a unit placed there, not a way a unit gets in."""
    w = _world(lib, world_factory, walk=walk, box=False)
    a = spawn(lib, w, RAIDER, 0, 550, 400)
    assert lib.om_map_block_rect(w, 500.0, 300.0, 600.0, 500.0, 0, 4) == 0
    assert _blocked(lib, w, pos(lib, w, a)), "scene broken: the wall is not on the unit"
    step(lib, w, 5)
    assert not _blocked(lib, w, pos(lib, w, a)), "still inside the wall after 5 ticks at %s" % (pos(lib, w, a),)
