# Rule pins: DEC-movement-sidestep-2026-11-24 (3), R-097-03, ALG-68
"""Movement-sidestep LS1 (c): a detour keeps the side it was first taken on until the straight line to the aim is clear; it is dropped the tick the line is clear.

Rule words (docs/northstar/story_reviews/westley/decisions.md, DEC-movement-sidestep-2026-11-24, point 3): "a detour keeps the side it was first taken on until the
straight line to the aim is clear (replaces the 60 wu hold)". R-097-03: "it probes 40 wu ahead; if a unit ... blocks the probe ... it tries +30, -30, +60, -60, +90 and
-90 degrees from its heading, in that order, and takes the first clear one". Spec: docs/northstar/plans/movement-sidestep-2026-11-24/spec.md "The behaviour" 3 and "Tests" (c).

Scene (flyers; see sidestep_support.py): a mover M at (500, 1000) is moved to (3000, 1000), 7.5 wu a tick. Enemy Supplies (never fire, never move) are the blockers; the
test reads the probe itself from the positions at the start of each tick (`straight_blocked`: a blocker within 30 wu of the point 40 wu ahead).
  FLIP scene: E1 (540, 990) blocks the straight line and +30, so M's first deflection is +30 degrees (left, y rising); E2 (592, 1040) keeps the straight line blocked when M
  has gone 60 wu along the detour (8 ticks), and blocks +30 there but not -30. Under the 60 wu hold M re-sweeps on tick 9, finds -30 clear and turns right (y falling) while
  the line is still blocked. Committed to the left it may only try left angles: it never steps right while the line stays blocked. The MIRROR scene is the same scene reflected
  about y = 1000 (first deflection right, then the old rule turns left).
  CLEAR scene: E1 alone at (532, 972): the line is blocked on tick 1 and clear from tick 2; under the 60 wu hold M keeps going at 30 degrees for 8 ticks with a clear line;
  committed-until-clear it steps straight at the aim from the first tick the line is clear.
Measured on main 2026-11-24 (the red): FLIP, tick 9 the step is -30.7 degrees with the line blocked; CLEAR, ticks 2 to 8 step at +30 degrees with the line clear.
Controls green today: the first deflection (+30 degrees, or -30 mirrored) and the straight line when nothing blocks it.
"""
import math

import pytest

from sidestep_support import RAIDER, move, run_steps, spawn, straight_blocked, supply, world

M0 = (500.0, 1000.0)
AIM = (3000.0, 1000.0)
SCENES = {
    "flip": ((540.0, 990.0), (592.0, 1040.0)),
    "mirror": ((540.0, 1010.0), (592.0, 960.0)),
    "clear": ((532.0, 972.0),),
}
TICKS = 24
STEP_TOL = 0.01          # wu of y a push may add on the wrong side; a turn is over 3 wu


def _run(lib, wf, scene):
    w = world(lib, wf)
    m = spawn(lib, w, RAIDER, 0, *M0)
    blockers = SCENES[scene]
    for b in blockers:
        supply(lib, w, 1, *b)
    assert move(lib, w, [m], *AIM) == 0
    tr = run_steps(lib, w, m, TICKS)
    rows = []
    for i in range(1, len(tr)):
        sx, sy = tr[i][0] - tr[i - 1][0], tr[i][1] - tr[i - 1][1]
        to_aim = (AIM[0] - tr[i - 1][0], AIM[1] - tr[i - 1][1])
        cosang = (sx * to_aim[0] + sy * to_aim[1]) / (math.hypot(sx, sy) * math.hypot(*to_aim))
        rows.append({"tick": i, "dy": sy, "blocked": straight_blocked(tr[i - 1], AIM, blockers), "deg_off_aim": math.degrees(math.acos(max(-1.0, min(1.0, cosang))))})
    return rows


@pytest.mark.parametrize("scene,side", [("flip", 1), ("mirror", -1)])
def test_DEC_movement_sidestep_a_unit_that_deflected_to_one_side_does_not_deflect_to_the_other_while_the_line_stays_blocked(lib, world_factory, scene, side):
    """DEC-movement-sidestep-2026-11-24 (3) 'a detour keeps the side it was first taken on until the straight line to the aim is clear': per tick, on every tick after the first
    deflection on which the straight line is blocked, M's step does not go to the other side (side * dy >= -0.01): never right after deflecting left, never left after right.
    Premises asserted: the first step goes to `side` (a deflection at all), and at least 8 later ticks have the line blocked (so the check has ticks to judge).
    Red today: the 60 wu hold ends on tick 9 and the re-sweep takes -30 (or +30 mirrored) with the line still blocked."""
    rows = _run(lib, world_factory, scene)
    assert side * rows[0]["dy"] > 3.0, "premise: the first step deflects to side %+d: dy %.3f" % (side, rows[0]["dy"])
    judged = [r for r in rows[1:] if r["blocked"]]
    assert len(judged) >= 8, "premise: only %d ticks with the line blocked" % len(judged)
    bad = [(r["tick"], round(r["dy"], 2)) for r in judged if side * r["dy"] < -STEP_TOL]
    assert not bad, "M turned to the other side on ticks %s (tick, dy) with the straight line still blocked; the detour keeps its side until the line is clear" % (bad,)


@pytest.mark.parametrize("scene,side", [("flip", 1), ("mirror", -1), ("clear", 1)])
def test_DEC_movement_sidestep_control_the_first_deflection_is_the_first_clear_angle(lib, world_factory, scene, side):
    """Control (green today and after), R-097-03 '+30, -30, +60, -60 ... takes the first clear one': with the line blocked on tick 1 M's first step is +30 degrees (y rising) for the
    flip and clear scenes, -30 for the mirror scene (E1 blocks the other 30 degree angle). Proves the harness reads a deflection and its side; the tests around it are red for the hold."""
    rows = _run(lib, world_factory, scene)
    assert rows[0]["blocked"], "premise: the line is blocked on tick 1"
    ang = math.degrees(math.atan2(rows[0]["dy"], math.sqrt(7.5 ** 2 - rows[0]["dy"] ** 2)))
    assert abs(ang - 30.0 * side) < 1.0, "first step at %.1f degrees, wanted %+d" % (ang, 30 * side)


def test_DEC_movement_sidestep_the_detour_is_dropped_on_the_first_tick_the_straight_line_is_clear(lib, world_factory):
    """DEC-movement-sidestep-2026-11-24 (3) '... until the straight line to the aim is clear' (replaces the 60 wu hold): in the CLEAR scene, from the first tick whose start-of-tick
    probe is clear, every step points at the aim (within 0.5 degrees; nothing is within collision reach of M, so no push). Premise: the line is clear from tick 2 on and
    stays clear. Red today: M keeps its 30 degree heading for 60 wu (ticks 2 to 8) with a clear line."""
    rows = _run(lib, world_factory, "clear")
    assert rows[0]["blocked"] and not rows[1]["blocked"], "premise: blocked on tick 1, clear on tick 2: %s" % ([r["blocked"] for r in rows[:3]],)
    assert not any(r["blocked"] for r in rows[1:]), "premise: the line stays clear after tick 1"
    off = [(r["tick"], round(r["deg_off_aim"], 1)) for r in rows[1:] if r["deg_off_aim"] > 0.5]
    assert not off, "with the straight line clear M still steps off the aim on ticks %s (tick, degrees off the aim): the old 60 wu hold" % (off,)


def test_DEC_movement_sidestep_control_with_nothing_in_the_way_the_unit_steps_straight_at_the_aim(lib, world_factory):
    """Control (green today and after): no blocker; every step points at the aim. The detector `deg_off_aim` reads 0 for a straight walk, so its red above is the hold, not noise."""
    w = world(lib, world_factory)
    m = spawn(lib, w, RAIDER, 0, *M0)
    move(lib, w, [m], *AIM)
    tr = run_steps(lib, w, m, 10)
    assert all(abs(tr[i][1] - M0[1]) < 1e-9 for i in range(len(tr)))
