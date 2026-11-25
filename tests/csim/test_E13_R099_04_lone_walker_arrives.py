# Rule pins: R-099-04, R-096-02
"""E-13 R-099-04 / R-096-02, DEC-movement-sidestep-2026-11-24: a unit ordered alone walks to its point itself, and an attack-mover that stands to shoot keeps its order.

Rule words (docs/bible/epics/E-13-movement-and-command.md):
  R-099-04  "A walker ordered alone has no arrival radius: with a clear path it walks to its point itself (tests hold a lone walker to within 1 wu of its route's end and a guard to within 5 wu of its post);
            a flying unit ordered alone stops within 1.5 radii of its point, as its steering always has".
  R-096-02  an attack-move keeps its order through a fight and walks on after the kill.
  (This file began as R-099-05's proof, the give-up of a unit held near its point. The give-up is gone, DEC-movement-sidestep-2026-11-24: a held unit keeps its order and sidesteps;
  the tests of the give-up went with it, the ones that prove the arrival and the kept order stay.)

Configuration: the shipped one for a csim scene: walking units (the kind is set, as the lab does; flying where the test says so), steering and route-around-terrain on (their defaults), targeting by sight on (the
default), a 2000 x 2000 canvas.

Detector bounds (not rules; Westley's to change): PAUSE_TICKS 9 and PAUSE_SLACK 3 (DRAFT-pause-slack-ticks) as the E1 file, RUN_TICKS 400 (a run limit), LOCK_END_BY 4 (DRAFT-lock-end-ticks: the premise that a lock
ended within this many ticks of the hook), CLEAR_PATH_WU 5 (the end of a lone walk with a clear path: the existing tests hold it to 1 wu and a guard to 5; DRAFT-clear-path-wu).
"""
import ctypes
import math

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, spawn, step, target

FLYING, WALKING = 0, 1
CANVAS = 2000.0
RADIUS = 15.0                       # collision radius (R-097-05: 2 x radius 15)
ARRIVE_SLOT = 1.5 * RADIUS          # 22.5 wu: the steering arrival of a flyer and of a group slot, not a lone walker's
PAUSE_TICKS = 9
PAUSE_SLACK = 3                     # DRAFT-pause-slack-ticks
CLEAR_PATH_WU = 5.0                 # DRAFT-clear-path-wu
LOCK_END_BY = 4                     # DRAFT-lock-end-ticks
RUN_TICKS = 400
BIG_HP = 1.0e6
POS_TOL = 1.0e-6                    # numeric slack of a rested unit pushed by a hair, not a rule threshold


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _world(lib, wf, kinds=(RAIDER, VANGUARD), kind=WALKING):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    for k in kinds:
        assert lib.om_roster_set_movement_kind(w, k, kind) == 0
    return w


def _move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def _none(t):
    return t is None or t <= 0


def _supply(lib, w, faction, x, y):
    s = spawn(lib, w, SUPPLY, faction, x, y)
    lib.om_unit_set_hp(w, s, BIG_HP)
    return s


def test_R_099_04_control_a_lone_walker_with_a_clear_path_walks_to_its_point_itself(lib, world_factory):
    """R-099-04 'A walker ordered alone has no arrival radius: with a clear path it walks to its point itself': a Raider ordered alone from (300,400) to (900,700), nothing in its way, ends its order within 5 wu of
    the point (CLEAR_PATH_WU: a build that gave it an arrival radius would stop it 22 or 30 wu short), never has a destination again and does not move after. On every tick that it is 40 wu or more from the
    point (reported) it still has its destination. Green today and must stay green."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    point = (900.0, 700.0)
    assert _move(lib, w, [m], *point) == 0
    cleared_at, trace = None, []
    for t in range(1, 301):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append(p)
        if cleared_at is None and _dist(p, point) >= 40.0:
            assert has, "tick %d: the walker %.1f wu from its point has no destination (it has not arrived)" % (t, _dist(p, point))
        if cleared_at is None and not has:
            cleared_at = t
            assert _dist(p, point) <= CLEAR_PATH_WU, "tick %d: the order ended %.1f wu from the point (a lone walker with a clear path walks to it; R-099-04)" % (t, _dist(p, point))
        if cleared_at is not None:
            assert not has and _dist(p, trace[cleared_at - 1]) < POS_TOL, "tick %d: the unit moved or took a destination after arriving on tick %d" % (t, cleared_at)
    assert cleared_at is not None, "the unit never arrived: at %s" % (trace[-1],)


def test_R_099_04_control_a_flying_unit_ordered_alone_is_unchanged(lib, world_factory):
    """R-099-04 'a flying unit ordered alone stops within 1.5 radii of its point, as its steering always has': a flying Raider ordered alone from (300,400) to (900,700), nothing in its way, ends its order within 22.5 wu of the point (the steering arrival, 1.5 radii), keeps no
    destination afterwards and does not move after. Green today and must stay green."""
    w = _world(lib, world_factory, kind=FLYING)
    m = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    point = (900.0, 700.0)
    assert _move(lib, w, [m], *point) == 0
    cleared_at, trace = None, []
    for t in range(1, 301):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append(p)
        if cleared_at is None and not has:
            cleared_at = t
            assert _dist(p, point) <= ARRIVE_SLOT, "tick %d: the flying unit's order ended %.1f wu from the point" % (t, _dist(p, point))
        if cleared_at is not None:
            assert not has and _dist(p, trace[cleared_at - 1]) < POS_TOL, "tick %d: the flying unit moved or took a destination after arriving on tick %d" % (t, cleared_at)
    assert cleared_at is not None, "the flying unit never arrived: at %s" % (trace[-1],)






def test_R_096_02_a_lone_attack_mover_that_stands_to_shoot_keeps_its_order_and_walks_on_after_the_kill(lib, world_factory):
    """R-096-02: a Raider attack-moved alone from (300,400) to (300,1000) has an enemy Supply 60 wu east of it (inside its attack range and its notice distance) with
    1e6 hp. It stands to shoot at it for 100 ticks: every tick it holds the Supply, has a destination, does not move. The Supply is then killed (hp 0 between ticks); within the usual lock-end ticks it
    holds no target and from the end of its pause it walks on and ends its order within 22.5 wu of its ordered point (300,1000). Measured on the Round 5 engine: while it stands to shoot a target 60 wu away its
    destination is its ordered point, 600 wu off. Green before the give-up was removed and after."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    v = _supply(lib, w, 1, 360.0, 400.0)
    assert attack_move(lib, w, [u], 300.0, 1000.0) == 0
    held = 0
    for t in range(1, 111):
        step(lib, w)
        if target(lib, w, u) == v:
            held += 1
            if held == 1:
                at_rest = pos(lib, w, u)
        if held:
            assert target(lib, w, u) == v and dest(lib, w, u)[0] == 1 and _dist(pos(lib, w, u), at_rest) < POS_TOL, (
                "tick %d: after %d ticks of standing to shoot: target %s, has destination %s, position %s (at rest %s)" % (t, held, target(lib, w, u), dest(lib, w, u)[0], pos(lib, w, u), at_rest))
    assert held >= 100, "scene broken: the unit held the Supply for only %d ticks" % held
    kill(lib, w, v)
    arrived = None
    for t in range(1, 301):
        step(lib, w)
        if t > LOCK_END_BY:
            assert _none(target(lib, w, u)), "tick %d after the kill: the unit holds a target" % t
        if dest(lib, w, u)[0] == 0:
            arrived = t
            break
    assert arrived is not None, "the unit did not reach its point after the kill, in 300 ticks: at %s" % (pos(lib, w, u),)
    assert _dist(pos(lib, w, u), (300.0, 1000.0)) <= ARRIVE_SLOT, "the order ended %.1f wu from the ordered point, at %s" % (_dist(pos(lib, w, u), (300.0, 1000.0)), pos(lib, w, u))
