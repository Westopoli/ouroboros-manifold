# Rule pins: R-096-02, R-084-04, R-087-03, R-099-04
"""E-13 R-096-02 / E-11 R-084-04, Round 6 piece E1 (docs/northstar/plans/engine-rules-2026-11-08/round6.md): an attack-move order is not lost in the pause after a shot.

Rule words (docs/bible/epics/E-13-movement-and-command.md, E-11-units-and-combat.md):
  R-096-02  "Given an attack-move, When an enemy its side can see comes within the unit's notice distance (E-11 R-087-04), Then the unit closes to attack range, halts and fires; when the lock ends (E-11 R-087-03:
            the target dies, is lost from sight or leaves the notice distance) it resumes toward the point. The pause after the unit's own shot (E-11 R-084-04) delays the resume and never cancels it: a walker that cannot step keeps its destination and walks when the pause ends, and a move or
            attack-move order given during the pause is kept the same way. Two or more units attack-moved together take formation slots as a move group does (R-095-02 to R-095-04); after every fight
            the group resumes toward the point as a unit attack-moved alone does ... an attack-move is not finished until the unit reaches its point, except that a unit that gives up under R-099-05 ends where it stands".
  R-084-04  "Given a unit fires, When the attack lands, Then the unit pauses movement for 0.5 s (backswing)." A pause, not the end of an order (round6.md E1).
Cause the round names (csrc/walk_route.c, csrc/tactical_move.c): a walker whose speed is zero (the nine ticks after its own shot) is told "no route" and its destination is cleared, so a lock that ends within about five
ticks of the shot leaves the attack-move with no destination and nothing issues the move again; a move order given during the pause is lost the same way. Flying units are not affected.

What the scenes assert, every tick (S is the tick of the unit's shot, read as the first tick the victim's hp is lower):
  PAUSE   on ticks S+1 to S+9 the unit's position is its position at S, bit for bit (no step during the nine ticks);
  HOLD    on every tick from S+9 until the unit arrives it has a destination (round6.md: "holds a destination from the tick the pause ends at the latest");
  WALK    on every tick from S+10 until it arrives the unit moves;
  ARRIVE  the unit's destination ends only within ARRIVE_TOL of its ordered point (its slot, for a group member), and the unit ends there.
Cases: the lock ends by the target dying on the tick of the shot (the shot kills it) and one, two and three ticks after (killed by another unit, set to hp 0 between ticks); by the target leaving the notice distance
and by the target being lost from sight, one, two and three ticks after the shot. Each alone and as a member of a group of three (formation slots, R-095-02). A plain move order given during the pause walks to its
point when the pause ends. Controls green today: a unit whose target is alive does not resume; a walker ordered to a point with no route has no destination; a flying attack-mover resumes after its kill.

Scene: a 2000 x 2000 canvas, default tactical parameters, Raiders (attack range 200, notice distance 220, 7.5 wu a tick) set to the walking kind (flying where the test says so). The unit is at (300,400),
attack-moved to a point 600 wu south of it (alone: (300,1000); in a group of three, the two other Raiders stand 200 wu west of it, and the point is its formation slot, read on tick 1). A Supply (never fires, never
flees, never moves; so nothing is taken by return fire, R-087-06) stands at (510,422): 210 wu from the unit when it acquires at its cohort turn on tick 4, so that it has to close to attack range before it shoots
(the walk of R-087-04, whose end is the resume the defect strikes; a victim already in range at the cohort turn is shot without a walk and no resume follows). The Supply's hp: 1 for the case in which the shot kills
it, a million otherwise (so that only the test kills it). Every case of the brief is staged through the public calls the neighbouring tests use (om_unit_set_hp, om_unit_teleport, om_map_block_rect); none is
left out. Loss of sight is a wall (column x 400..500, y 0..800) built between the unit and the Supply k ticks after the shot, the scene asserting nothing further than that the lock is gone within LOCK_END_BY ticks
(a stealthed Supply is still seen at that range, so stealth does not stage it). The notice distance is left by teleporting the Supply 240 wu north of the unit. Sanity run, 2026-11-18 (not part of the suite): every
test of this file, with the walking kind replaced by the flying kind, passes on this tree, so a scene, a count or an assertion of the file is not what turns the walking cases red.

Detector bounds (not rules; Westley's to change): PAUSE_TICKS 9 (the rule's 0.5 s less the shot's own tick, measured on the flying control), ARRIVE_TOL 30 wu (DRAFT-arrive-tol: about two collision radii), RUN_TICKS 260
(a run limit), LOCK_END_BY 4 ticks (DRAFT-lock-end-ticks: the premise that the lock ended within this many ticks of the hook; a cohort turn may delay it).
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, spawn, step, target

FLYING, WALKING = 0, 1
PAUSE_TICKS = 9                     # nine ticks after the tick of the shot
ARRIVE_TOL = 30.0                   # DRAFT-arrive-tol
RUN_TICKS = 260                     # run limit
LOCK_END_BY = 4                     # DRAFT-lock-end-ticks
BIG_HP = 1.0e6
POINT = (300.0, 1000.0)
UNIT_XY = (300.0, 400.0)
VICTIM_XY = (510.0, 422.0)
NOTICE = 220.0                      # Raider: 200 wu range x 1.1 (E-11 R-087-04)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _world(lib, wf, kind):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, kind) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, kind) == 0
    return w


def _scene(lib, wf, kind, group, victim_hp):
    """The unit u (and, when `group`, two more Raiders to its west) attack-moved to POINT; the Supply victim v east of u. Returns (w, u, v)."""
    w = _world(lib, wf, kind)
    u = spawn(lib, w, RAIDER, 0, *UNIT_XY)
    mates = [spawn(lib, w, RAIDER, 0, UNIT_XY[0] - 200.0, UNIT_XY[1] + 40.0 * i) for i in range(2)] if group else []
    v = spawn(lib, w, SUPPLY, 1, *VICTIM_XY)
    lib.om_unit_set_hp(w, v, victim_hp)
    attack_move(lib, w, [u] + mates, *POINT)
    return w, u, v


def _record(lib, w, u, v):
    return {"p": pos(lib, w, u), "has": dest(lib, w, u)[0] == 1, "dest": dest(lib, w, u)[1:], "tgt": target(lib, w, u), "hp": hp(lib, w, v)}


def _none(t):
    return t is None or t <= 0


def _hook(lib, w, u, v, how):
    """The way the lock is ended after the shot: the victim is killed (by another unit), put beyond the notice distance (240 wu behind the unit), or made unseen by the unit's side."""
    if how == "kill":
        kill(lib, w, v)
    elif how == "notice":
        x, y = pos(lib, w, u)
        lib.om_unit_teleport(w, v, x, y - 240.0, 0)
    elif how == "sight":
        assert lib.om_map_block_rect(w, 410.0, 10.0, 490.0, 790.0, 0, 4) == 0
    else:
        raise AssertionError(how)


def _run_case(lib, w, u, v, how, k, ticks=RUN_TICKS):
    """Step `ticks` ticks. S is the first tick on which the victim's hp is lower than at the start; for k >= 1 the lock is ended by `how` after tick S + k - 1 (so the victim is gone from tick S + k on).
    Returns (records by tick starting at index 1 (index 0 is the start), S, the point the unit was walking to on tick 1, the victim's start hp)."""
    start_hp = hp(lib, w, v)
    rec = [{"p": pos(lib, w, u), "has": True, "dest": None, "tgt": 0, "hp": start_hp}]
    shot = None
    for t in range(1, ticks + 1):
        step(lib, w)
        rec.append(_record(lib, w, u, v))
        if shot is None and rec[t]["hp"] < start_hp:
            shot = t
        if shot is not None and k >= 1 and t == shot + k - 1:
            _hook(lib, w, u, v, how)
    assert shot is not None, "scene broken: the unit never shot its victim in %d ticks" % ticks
    assert rec[1]["has"], "scene broken: the attack-moved unit has no destination on tick 1"
    return rec, shot, rec[1]["dest"], start_hp


def _assert_order_kept(rec, shot, point, what):
    """PAUSE, HOLD, WALK and ARRIVE of the module docstring, every tick."""
    at_shot = rec[shot]["p"]
    for t in range(shot + 1, shot + PAUSE_TICKS + 1):
        assert rec[t]["p"] == at_shot, "%s: tick %d (shot on %d): the unit took a step during the pause, %s -> %s" % (what, t, shot, at_shot, rec[t]["p"])
    arrived = None
    for t in range(shot + PAUSE_TICKS, len(rec)):
        if not rec[t]["has"]:
            arrived = t
            assert _dist(rec[t]["p"], point) <= ARRIVE_TOL, (
                "%s: tick %d (shot on %d): the unit has no destination %.0f wu from its ordered point %s (it is at %s)" % (what, t, shot, _dist(rec[t]["p"], point), point, rec[t]["p"]))
            break
        if t >= shot + PAUSE_TICKS + 1:
            assert rec[t]["p"] != rec[t - 1]["p"], "%s: tick %d (shot on %d): the unit holds a destination and stands still" % (what, t, shot)
    assert arrived is not None, "%s: the unit had not reached its point %s in %d ticks; at %s" % (what, point, len(rec) - 1, rec[-1]["p"])
    assert _dist(rec[arrived]["p"], point) <= ARRIVE_TOL, "%s: ended %.0f wu from its point" % (what, _dist(rec[arrived]["p"], point))


# ------------------------------------------------------------------ the lock ends by death

@pytest.mark.parametrize("group", [False, True], ids=["alone", "group"])
@pytest.mark.parametrize("k", [0, 1, 2, 3], ids=["on_the_shot", "1_tick_after", "2_ticks_after", "3_ticks_after"])
def test_R_096_02_a_walking_attack_mover_whose_target_dies_resumes_to_its_point(lib, world_factory, k, group):
    """R-096-02, as the epic reads now: "when the lock ends (E-11 R-087-03: the target dies, is lost from sight or leaves the notice distance) it resumes toward the point. The pause after the unit's own shot (E-11 R-084-04)
    delays the resume and never cancels it: a walker that cannot step keeps its destination and walks when the pause ends"; "an attack-move is not finished until the unit reaches its point"; and R-084-04 'pauses movement for 0.5 s'
    (a pause, not the end of an order). This function is the death half of the rule's Then (the sibling below ends the lock by distance and by sight, the move-order test below it covers a move given in the pause):
    a walking Raider attack-moved (alone, or in a group of three with a slot) shoots a Supply (it first walks to attack range); the Supply dies on the tick of the shot (k 0: the shot kills it) or k ticks after (killed by another unit). Every tick:
    no step during the nine ticks after the shot, a destination from the tick the pause ends, it walks on and arrives at its point (its slot, in a group)."""
    w, u, v = _scene(lib, world_factory, WALKING, group, 1.0 if k == 0 else BIG_HP)
    rec, shot, point, _ = _run_case(lib, w, u, v, "kill", k)
    if k >= 1:
        assert _none(rec[shot + k + LOCK_END_BY]["tgt"]), "scene broken: the unit still holds a target %d ticks after the kill" % (k + LOCK_END_BY)
    _assert_order_kept(rec, shot, point, "kill %d ticks after the shot, %s" % (k, "group" if group else "alone"))


# ------------------------------------------------------------------ the lock ends by the notice distance or by loss of sight

@pytest.mark.parametrize("group", [False, True], ids=["alone", "group"])
@pytest.mark.parametrize("k", [1, 2, 3], ids=["1_tick_after", "2_ticks_after", "3_ticks_after"])
@pytest.mark.parametrize("how", ["notice", "sight"], ids=["leaves_notice_distance", "lost_from_sight"])
def test_R_096_02_a_walking_attack_mover_whose_lock_ends_by_distance_or_sight_resumes_to_its_point(lib, world_factory, how, k, group):
    """R-096-02 'when the lock ends (E-11 R-087-03: the target dies, is lost from sight or leaves the notice distance) it resumes toward the point': the same scene as the death cases, the Supply kept alive and
    taken from the unit k ticks after its shot, either 240 wu behind the unit (beyond the notice distance 220) or made unseen by the unit's side. Every tick: PAUSE, HOLD, WALK, ARRIVE as above."""
    w, u, v = _scene(lib, world_factory, WALKING, group, BIG_HP)
    rec, shot, point, _ = _run_case(lib, w, u, v, how, k)
    assert _none(rec[shot + k + LOCK_END_BY]["tgt"]), "scene broken: the unit still holds a target %d ticks after the lock was ended by %s" % (k + LOCK_END_BY, how)
    _assert_order_kept(rec, shot, point, "%s %d ticks after the shot, %s" % (how, k, "group" if group else "alone"))


# ------------------------------------------------------------------ a move order given in the pause

@pytest.mark.parametrize("j", [1, 4, 8], ids=["1_tick_after", "4_ticks_after", "8_ticks_after"])
def test_R_096_02_a_move_order_given_in_the_pause_after_a_shot_is_walked_when_the_pause_ends(lib, world_factory, j):
    """R-096-02 'a move or attack-move order given during the pause is kept the same way' (round6.md E1: 'a walker given a move order during the pause after its shot walks to that point when the pause ends'): the Raider has shot the Supply (kept alive) and j ticks later
    is given a plain move to (900,700). Every tick: it takes no step on ticks S+1 to S+9, holds the destination from S+9, walks on and arrives within ARRIVE_TOL of (900,700)."""
    w, u, v = _scene(lib, world_factory, WALKING, False, BIG_HP)
    start_hp = hp(lib, w, v)
    move_to = (900.0, 700.0)
    rec = [None]
    shot = None
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        rec.append(_record(lib, w, u, v))
        if shot is None and rec[t]["hp"] < start_hp:
            shot = t
        if shot is not None and t == shot + j - 1:
            arr = (ctypes.c_uint32 * 1)(u)
            assert lib.om_command_move.raw(w, arr, 1, move_to[0], move_to[1]) == 0
    assert shot is not None, "scene broken: the unit never shot its victim"
    _assert_order_kept(rec, shot, move_to, "move order %d ticks after the shot" % j)


# ------------------------------------------------------------------ controls, green today

def test_R_096_02_control_a_unit_whose_target_is_alive_does_not_resume(lib, world_factory):
    """R-096-02 'when the lock ends ... it resumes': while the lock holds it does not. The Raider shoots a Supply that lives (a million hp); on every tick from the shot on, for 80 ticks, it holds the Supply as its
    target and has not moved. Green today and must stay."""
    w, u, v = _scene(lib, world_factory, WALKING, False, BIG_HP)
    start_hp = hp(lib, w, v)
    shot = None
    for t in range(1, 41):
        step(lib, w)
        if shot is None and hp(lib, w, v) < start_hp:
            shot = t
            at_shot = pos(lib, w, u)
            break
    assert shot is not None, "scene broken: the unit never shot its victim"
    for t in range(shot + 1, shot + 81):
        step(lib, w)
        assert target(lib, w, u) == v, "tick %d (shot on %d): the unit's target is %s, not the living Supply %d" % (t, shot, target(lib, w, u), v)
        assert pos(lib, w, u) == at_shot, "tick %d (shot on %d): the unit left its firing place %s for %s with its target alive" % (t, shot, at_shot, pos(lib, w, u))


def test_R_096_02_control_a_walker_ordered_to_a_point_with_no_route_has_no_destination(lib, world_factory):
    """R-097-01 / R-099-04 (round6.md E1: 'a route that truly does not exist still clears the destination as today'): a wall the height of the canvas cuts the map (the scene of test_PP_move_route.py
    test_R_097_01_no_route_leaves_the_unit_stopped_beside_the_wall_not_inside_a_cell); the walking Raider ordered across it ends with no destination and, once it has none, never has one again. Green today."""
    w = _world(lib, world_factory, WALKING)
    assert lib.om_map_block_rect(w, 510.0, 10.0, 590.0, 1990.0, 0, 4) == 0
    u = spawn(lib, w, RAIDER, 0, *UNIT_XY)
    arr = (ctypes.c_uint32 * 1)(u)
    assert lib.om_command_move.raw(w, arr, 1, 900.0, 400.0) == 0
    cleared = None
    for t in range(1, 201):
        step(lib, w)
        has = dest(lib, w, u)[0] == 1
        if cleared is None and not has:
            cleared = t
        if cleared is not None:
            assert not has, "tick %d: the unit has a destination again after losing it on tick %d" % (t, cleared)
    assert cleared is not None, "the unit ordered across the wall still holds a destination after 200 ticks, at %s" % (pos(lib, w, u),)


def test_R_096_02_control_a_flying_attack_mover_resumes_after_its_kill(lib, world_factory):
    """R-096-02 (round6.md E1: 'Flying units are not affected'): a flying Raider whose target dies on the tick of its shot keeps its destination and arrives at its point: PAUSE, HOLD, WALK, ARRIVE as for
    the walker. Green today and must stay."""
    w, u, v = _scene(lib, world_factory, FLYING, False, 1.0)
    rec, shot, point, _ = _run_case(lib, w, u, v, "kill", 0)
    _assert_order_kept(rec, shot, point, "flying, kill on the shot")
