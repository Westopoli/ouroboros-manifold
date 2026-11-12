"""E-11 R-087-04 / R-084-04 (engine rules round 3, T9 item 2): a unit that takes a target just outside its range during the pause after a shot walks to it once the pause ends.

Rule words, word for word (docs/bible/epics/E-11-units-and-combat.md):
  R-087-04  "... it acquires the nearest such enemy at its cohort turn (R-087-08), anchors where it stands (R-087-05) and walks toward it until the enemy is within attack range, then halts and fires ..."
  R-084-04  "Given a unit fires, When the attack lands, Then the unit pauses movement for 0.5 s (backswing)."
Rule pins: R-087-04, R-084-04, R-087-03.

Trace (engine-rules-baseline/x2/log2.txt, repro2.py): the cover close-up fixture, unit 13 (a walking Vanguard-class unit, range 300, speed 80) fires at tick 352 and is in the pause through tick
362; at tick 356 it takes target 6 at 301.3 wu; the chase (csrc/unit.c om_tac_chase) orders a move, the route planner refuses it because the unit's speed is 0 during the pause and drops the
destination; the chase then believes the order is already given (`issued` equals the target's place) and never orders again; the unit stands 20 ticks until the give-up drops the target.
The lab twin is the strict xfail tests/skilllab/arena/test_invariants_round2b_wiring.py::test_R_087_04_finding_a_unit_holding_a_target_just_outside_attack_range_walks_toward_it: it stays in
place; once the engine fix lands it passes and its marker comes off (a later Test-defect commit).

Scene (the shipped configuration: walking kind, terrain-free 2000 x 2000 canvas, targeting by sight on, abilities as the lab leaves them): a Vanguard U (attack range 300, speed 80 = 4 wu a tick,
attack interval 1.2 s = 24 ticks, walking kind) at (300, 400), attack-moving to (1800, 400); a Supply S1 of faction 1 at (550, 400) with 1 hp (never fires; the first shot kills it). On the tick
f that S1 dies, a second Supply S2 (hp 1e6) is spawned 301.3 wu south of U's place (the trace's 301.3). The cohort slot of U is 0 (it acquires on ticks 4, 8, ...).
Premises dumped 2026-11-11 (main 7ba38983): f = 4 (S1 dies at the first shot, tick 4); U takes S2 at tick 8 (inside the pause, ticks 5 to 13) in the walker and the flier alike; the walker's dest is then
dropped (has_dest 0) and it stands at (311.38, 403.79) for 40 more ticks, 301.3 wu from S2, firing nothing; the flier (movement kind 0, the control) keeps its destination, moves on tick 14 (f + 10)
and fires at S2 on tick 28 (= f + 24, the attack interval).
Braced (dumped, NOT asserted): a Vanguard with Brace activated by hand (om_command_activate_ability), attack-moving, S2 at 301.3 wu: it takes S2 at tick 4, its speed is 0 for all 120 ticks measured
(Brace phase 1 for 40 ticks, then phase 2 and no end in sight), the walker's destination is dropped as in the pause and the flier keeps it, and neither moves. R-086-03 says a braced Vanguard "is
immobile at once"; no rule says a braced unit walks on by itself once it has a target, so there is no rule to assert here (a gap for the Architect: what a braced unit with an out-of-range
target does).

Detector bounds (not rules; Westley's to change): BACKSWING_TICKS 10 (the pause is ticks 1 to 9 after the shot, tick 10 is the first free one, as tests/csim/test_E11_R087_04_a_moving_unit_does_not_fire.py),
FIRE_GAP_MAX 2 ticks (the same file), ATTACK_INTERVAL_TICKS 24 (Vanguard 1.2 s, measured: shots at ticks 4, 28, 52 in the flier control).
DRAFT-chase-in-range-ticks = BACKSWING_TICKS + ceil((gap) / step) + FIRE_GAP_MAX = 10 + 1 + 2 = 13 ticks after the shot: U is within attack range of S2.
DRAFT-chase-fire-ticks = ATTACK_INTERVAL_TICKS + FIRE_GAP_MAX = 26 ticks after the shot: S2 is hit (the next shot is due 24 ticks after the last).
"""
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import SUPPLY, VANGUARD, attack_move, dest, pos, spawn, step, target

GAP = 301.3                     # wu outside the range of 300, the trace's number
BACKSWING_TICKS = 10
FIRE_GAP_MAX = 2
ATTACK_INTERVAL_TICKS = 24
STEP_WU = 4.0                   # Vanguard speed 80 wu/s at 20 ticks a second
IN_RANGE_TICKS = BACKSWING_TICKS + math.ceil((GAP - 300.0) / STEP_WU) + FIRE_GAP_MAX     # DRAFT-chase-in-range-ticks 13
FIRE_TICKS = ATTACK_INTERVAL_TICKS + FIRE_GAP_MAX                                          # DRAFT-chase-fire-ticks 26
ACQUIRE_TICKS = 4               # one cohort period (OM_TARGETING_COHORT_COUNT)
BIG_HP = 1.0e6
WALKING, FLYING = 1, 0


def _world(lib, wf, kind):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, kind) == 0
    return w


def _play(lib, wf, kind, after_shot, ticks=60):
    """Run the scene. `after_shot` True: S1 dies on tick f and S2 appears then (the pause case); False: S2 appears on tick 1, U free to move. Returns a dict of what happened."""
    w = _world(lib, wf, kind)
    u = spawn(lib, w, VANGUARD, 0, 300, 400)
    s1 = None
    if after_shot:
        s1 = spawn(lib, w, SUPPLY, 1, 550, 400)
        lib.om_unit_set_hp(w, s1, 1.0)
    attack_move(lib, w, [u], 1800, 400)
    out = {"f": None, "spawn": None, "acq": None, "in_range": None, "fires": [], "gap0": None, "dest_after_acq": None, "rows": []}
    s2 = None
    h2 = BIG_HP
    for n in range(1, ticks + 1):
        step(lib, w)
        if s2 is None and (not after_shot or lib.om_unit_get_hp(w, s1) <= 0):
            out["f"] = n if after_shot else None
            out["spawn"] = n
            p = pos(lib, w, u)
            s2 = spawn(lib, w, SUPPLY, 1, p[0], p[1] + GAP)
            lib.om_unit_set_hp(w, s2, BIG_HP)
            out["gap0"] = math.dist(p, pos(lib, w, s2))
            continue
        if s2 is None:
            continue
        d = math.dist(pos(lib, w, u), pos(lib, w, s2))
        if out["acq"] is None and target(lib, w, u) == s2:
            out["acq"] = n
            out["dest_after_acq"] = dest(lib, w, u)[0]
        if out["in_range"] is None and d <= 300.0:
            out["in_range"] = n
        if lib.om_unit_get_hp(w, s2) < h2:
            out["fires"].append(n)
            h2 = lib.om_unit_get_hp(w, s2)
        out["rows"].append((n, round(d, 2)))
    out["final_dist"] = math.dist(pos(lib, w, u), pos(lib, w, s2))
    return out


# ------------------------------------------------------------------ controls: green today

@pytest.mark.parametrize("kind", [WALKING, FLYING], ids=["walker", "flier"])
def test_R_087_04_control_the_scene_acquires_inside_the_pause(lib, world_factory, kind):
    """R-084-04 + R-087-04 control (green today, the premise of the red tests): the Vanguard fires its first shot on tick f = 4 (S1 dies), S2 appears 301.3 wu away (outside range 300) and U takes it
    at its cohort turn on tick 8, which is inside the pause (ticks f + 1 to f + 9), walker and flier alike."""
    o = _play(lib, world_factory, kind, True, ticks=20)
    assert o["f"] == 4 and 300.0 < o["gap0"] <= 302.0, (o["f"], o["gap0"])
    assert o["acq"] is not None and o["f"] < o["acq"] <= o["f"] + BACKSWING_TICKS - 1, "S2 was taken on tick %s, the pause is ticks %d to %d" % (o["acq"], o["f"] + 1, o["f"] + 9)


def test_R_087_04_control_a_flier_that_takes_a_target_in_the_pause_walks_to_it_and_fires(lib, world_factory):
    """R-087-04 control (green today): the same scene with the Vanguard a flier (movement kind 0): it keeps its destination through the pause, closes to within 300 wu by tick f + 13 and
    hits S2 by tick f + 26 (the attack interval, 24 ticks after its first shot). Proves the scene and the two bounds, so the walker's red is the walker's."""
    o = _play(lib, world_factory, FLYING, True)
    assert o["in_range"] is not None and o["in_range"] <= o["f"] + IN_RANGE_TICKS, "in range at tick %s, bound f + %d = %d" % (o["in_range"], IN_RANGE_TICKS, o["f"] + IN_RANGE_TICKS)
    assert o["fires"] and o["fires"][0] <= o["f"] + FIRE_TICKS, "first hit on S2 at %s, bound f + %d = %d" % (o["fires"][:1], FIRE_TICKS, o["f"] + FIRE_TICKS)


def test_R_087_04_control_a_walker_free_to_move_that_takes_a_target_outside_range_walks_at_once(lib, world_factory):
    """R-087-04 'walks toward it until the enemy is within attack range, then halts and fires' control (green today): the walker with S2 301.3 wu away from tick 1 and no shot before it (no pause)
    takes S2 at its cohort turn and has closed to within 300 wu and hit it within ACQUIRE_TICKS + 1 + FIRE_GAP_MAX = 7 ticks of the tick S2 appeared. Measured: taken tick 4, first hit tick 4."""
    o = _play(lib, world_factory, WALKING, False, ticks=40)
    assert o["acq"] is not None and o["acq"] - o["spawn"] <= ACQUIRE_TICKS, o
    assert o["in_range"] is not None and o["in_range"] - o["spawn"] <= ACQUIRE_TICKS + 1 + FIRE_GAP_MAX, o["rows"][:12]
    assert o["fires"] and o["fires"][0] - o["spawn"] <= ACQUIRE_TICKS + 1 + FIRE_GAP_MAX, o["fires"][:3]


# ------------------------------------------------------------------ red today

def test_R_087_04_a_walker_that_takes_a_target_outside_range_in_the_pause_walks_to_it_once_the_pause_ends(lib, world_factory):
    """R-087-04 'walks toward it until the enemy is within attack range' + R-084-04 (the pause is 0.5 s, then the unit moves again): the walker takes S2 (301.3 wu, range 300) on tick 8, inside the
    pause that ends after tick f + 9 = 13; by tick f + 13 (DRAFT-chase-in-range-ticks) it is within 300 wu of S2. Red today: the route planner drops the chase's destination in the pause (speed 0),
    the chase believes the order is given, and the walker stands at 301.3 wu for as long as the scene runs (40 ticks measured). Break that turns it red: the engine as it is on main 7ba38983
    (csrc/unit.c om_tac_chase returns early when `issued` equals the target's place)."""
    o = _play(lib, world_factory, WALKING, True)
    assert o["acq"] is not None and o["f"] < o["acq"] <= o["f"] + BACKSWING_TICKS - 1, "scene broken: S2 not taken inside the pause: %s" % o["acq"]
    assert o["in_range"] is not None and o["in_range"] <= o["f"] + IN_RANGE_TICKS, "the walker never came within 300 wu of S2 by tick f + %d = %d (distance now %.2f, in range at %s)" % (
        IN_RANGE_TICKS, o["f"] + IN_RANGE_TICKS, o["final_dist"], o["in_range"])


def test_R_087_04_a_walker_that_takes_a_target_outside_range_in_the_pause_fires_at_it(lib, world_factory):
    """R-087-04 '... then halts and fires': the same walker hits S2 by tick f + 26 (DRAFT-chase-fire-ticks: the attack interval 24 ticks after the shot, plus FIRE_GAP_MAX 2). Red today: it never walks, so
    it never fires (no hit in 56 ticks after the shot)."""
    o = _play(lib, world_factory, WALKING, True)
    assert o["fires"] and o["fires"][0] <= o["f"] + FIRE_TICKS, "no hit on S2 by tick f + %d = %d (hits %s, distance now %.2f)" % (FIRE_TICKS, o["f"] + FIRE_TICKS, o["fires"][:3], o["final_dist"])
