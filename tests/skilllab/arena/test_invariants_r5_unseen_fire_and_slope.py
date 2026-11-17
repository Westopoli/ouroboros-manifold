# Rule pins: R-087-01, R-097-05, R-004-06
"""Engine rules round 5, G7 (docs/northstar/plans/engine-rules-2026-11-08/round5.md): the two new predicates of the lab checker, unseen fire (R-087-01) and slope collision
(R-097-05). Pure predicates over planted frames (`scripts/skilllab/invariants.check`); the whole runs on L-0061, L-0080 and the six hill layouts are G4 and G5's tests. The
checker is the lab builder's: these tests are red until it is built, each for the reason the test says.

Rule text as it reads on this branch (docs/bible/epics/E-11-units-and-combat.md R-087-01, E-13-movement-and-command.md R-097-05):
R-087-01: "Given an idle unit, or an attack-moving unit that has arrived at its point, with no target, that takes damage from an attacker it cannot see or cannot reach, When the loop
runs, Then it leaves the line of fire instead of standing in it: it moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends; it does not walk
back into the fire ... While it holds it acquires and returns fire as any idle unit does (R-087-04, R-087-06), and a repeat hit it still cannot answer moves it again. An attack-moving unit
still on its way to its point is neither moved nor stopped by such a hit: it keeps walking its attack-move ... A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit".
R-097-05: "Given two units on the same layer within 30 wu (2 x radius 15), or two units within 30 wu that both stand on the same slope, whichever side of its midline each is on (E-01 R-001-06),
When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick."
Round 5 G4 whole-run statement: "no walker with an attack-move destination stands still under unseen fire, and no unit moves away more than once without a new hit". G5: "no two units on one
slope closer than 30 wu after the pass except at the iteration cap" (Third pass: a pair is reported only after more than DRAFT-slope-settle-ticks = 3 ticks under 30 wu). The flip clause of G5 ("no unit flips
layer back and forth across a midline") is withdrawn (second pass: a layer on a slope is its side of the midline, E-01 R-004-06): a unit that changes layer three times in 20 ticks is silent.

THE API THIS FILE PINS (the lab builder builds to it; frames, `visible` and `hits` as in tests/skilllab/test_invariants_nearest.py):

    RULES                     the eleven of tests/skilllab/test_invariants.py, then "R-087-01", "R-097-05" appended (that file's pin of the tuple is rewritten to match when the checker is built)
    row keys (optional)       "dest": (x, y) or None, the unit's destination (Engine.unit_destination); "attack_move": True when the unit's standing order is an attack-move, arrived or not
                              (an idle unit and a plain mover: False or absent). A row with no "attack_move" key is not judged by R-087-01.
    unseen hit                a (attacker, victim) in a frame's "fires" with the victim alive, holding no target in the previous frame, and the attacker in neither the previous nor this
                              frame's "visible" set of the victim's side.
    R-087-01  on the way      a unit with attack_move True and dest not None, target 0, in a frame inside UNSEEN_WINDOW frames after an unseen hit on it (the hit frame excluded) is a violation
                              when it moved no more than 0.5 wu that frame with no other unit within 40 wu (stopped), or when its dest differs from the previous frame's with an unchanged
                              "order" token (its destination was changed); one violation per such unit and frame.
    R-087-01  once            an idle unit or an attack-mover that has arrived (dest None, target 0, not a guard) that moves under its own power (more than 0.5 wu, no unit within 40 wu, no new
                              "order" token) in a run of frames that no unseen hit on it since its previous run began started, where that previous run itself followed an unseen hit, is a violation
                              in the first frame of the run: a second move away without a new hit. A unit whose first run followed no unseen hit is not judged (a leash return, a new order).
    UNSEEN_WINDOW             60 frames, DRAFT-unseen-fire-window (the 60-tick HIT_GAP of tests/skilllab/arena/engine_rules_unseen_oracle.py); the tests keep 20 frames either side of it.
    Rules(slope_at=...)       callable (x, y) -> a hashable id of the slope the point lies on, or None off every slope. R-097-05: two living units within 30 wu - SLOPE_SLACK (2 wu,
                              DRAFT-slope-slack) of each other that both stand on the same slope (any layers) are a violation of unit min(a, b) in the frame in which they have stayed that close for
                              more than SLOPE_SETTLE_TICKS (3, DRAFT-slope-settle-ticks) consecutive frames (the fourth), once while they stay close. A layer change is never a violation.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

UNSEEN_WINDOW = 60           # DRAFT-unseen-fire-window
SLOPE_SLACK = 2.0            # DRAFT-slope-slack (wu): a pair this close to 30 wu counts as pushed apart
FAR = (3000.0, 100.0)


@pytest.fixture(scope="module")
def inv():
    return _Module()


def keys(vs):
    return [(v["rule"], v["tick"], v["unit"]) for v in vs]


def test_R_087_01_the_rule_list_ends_with_unseen_fire_and_slope_collision(inv):
    """R-087-01 / R-097-05 (G7): the two new checks are listed after the eleven of Round 2, in that order. Red today: eleven rules."""
    assert tuple(inv.RULES)[-2:] == ("R-087-01", "R-097-05") and len(inv.RULES) == 13


# ---------------------------------------------------------------------------------------------------------------- R-087-01, on the way

def march(inv, n=40, hit_at=5, seen_hit=False, still_from=None, redirect_from=None, step=3.0, tail=0, attacker_layer=0, reach=None, engage_at=None):
    """Unit 1 (side 0) attack-moves east along y 100 toward (3000, 100), `step` wu a frame, with unit 3 (side 1, 500 wu south, on `attacker_layer`) firing at it in frame `hit_at` (an attacker its side does
    not see unless `seen_hit`). It stops from frame `still_from`, or its destination is rewritten to a point behind it from frame `redirect_from` while it walks back. `reach` is the unit's layer reach
    ((up, down) layers, `Rules(reach=...)`). `engage_at`: from that frame the unit holds a seen enemy (unit 2, 200 wu ahead), fires at it in that frame, stands still, and enemy 2 is dead from two frames
    later, the unit's target with it (it halted to fire). Returns R-087-01 violations."""
    frames, x, dest = [], 100.0, FAR
    for k in range(n + 1):
        if engage_at is not None and k >= engage_at:
            pass
        elif still_from is not None and k >= still_from:
            pass
        elif redirect_from is not None and k >= redirect_from:
            x -= step
            dest = (x - 200.0, 100.0)
        elif k > 0:
            x += step
        engaged = engage_at is not None and engage_at <= k < engage_at + 2
        r1 = row(x, 100, target=2 if engaged else 0, dest=dest, attack_move=True, order=7)
        units = {1: r1, 3: row(x, 600, side=1, layer=attacker_layer)}
        if engage_at is not None and k >= engage_at:
            units[2] = row(x + 200, 100, side=1, alive=engaged)
        fires = ([(3, 1)] if k == hit_at else []) + ([(1, 2)] if k == engage_at else [])
        frames.append((units, fires))
    tr = trace(*frames)
    for k, fr in enumerate(tr):
        seen = ({3} if seen_hit else set()) | ({2} if engage_at is not None and k >= engage_at else set())
        fr["visible"] = {0: seen, 1: {1}}
        fr["hits"] = [f for f in fr["fires"] if f[1] == 1]
    return inv.check(tr, rules(inv, attack_range={1: 300.0}, reach={1: reach} if reach else {}), only=["R-087-01"]).violations


def test_R_087_01_an_attack_mover_on_its_way_that_stands_still_under_unseen_fire_is_flagged(inv):
    """R-087-01: "An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit". Planted: unit 1 walks toward (3000, 100), is hit in tick 5 by an attacker its
    side does not see, and stands still from tick 6 with its destination unchanged. Flagged in tick 6 (the first frame it did not move). Red today: no such check."""
    assert keys(march(inv, still_from=6))[:1] == [("R-087-01", 6, 1)]


def test_R_087_01_control_the_attack_mover_that_keeps_walking_is_silent(inv):
    """R-087-01 control (green today and after): the same hit, the unit keeps closing on its point 3 wu a frame for 40 frames: nothing is reported."""
    assert march(inv) == []


def test_R_087_01_an_attack_mover_whose_destination_is_taken_from_it_is_flagged(inv):
    """R-087-01: "its destination unchanged". Planted: after the hit in tick 5 the unit walks back 3 wu a frame and its destination becomes a point 200 wu behind it (the old engine's move
    away that sent it back to its point afterwards). Flagged from tick 6. Red today: no such check."""
    assert keys(march(inv, redirect_from=6))[:1] == [("R-087-01", 6, 1)]


def test_R_087_01_control_a_stop_after_the_window_or_after_a_seen_hit_is_silent(inv):
    """R-087-01 control: the unit stands still from tick 90 (85 frames after the hit, past UNSEEN_WINDOW 60): not under unseen fire any more, silent; and the same stop from tick 6 after a
    hit by an attacker its side DOES see (it may halt to fight it) is silent: a hit the unit can answer is not unseen."""
    assert march(inv, n=120, still_from=UNSEEN_WINDOW + 30) == []
    assert march(inv, still_from=6, seen_hit=True) == []


def test_R_087_01_control_a_unit_that_halts_to_fire_at_a_seen_target_after_an_unseen_hit_is_silent(inv):
    """R-087-01 (checker excuse, round5.md Third pass): hit in tick 5 by an attacker its side does not see, the attack-mover takes a seen enemy in tick 6, fires at it and stands where it is (the enemy
    dies two frames later and the unit's target with it): silent for the 34 frames to the end of the trace, past the backswing: it halted to fight, not for the hit. Opposite case: the same unit and hit that
    stands still from tick 6 and never takes a target is reported (tick 6 first)."""
    assert march(inv, engage_at=6) == []
    assert keys(march(inv, still_from=6))[:1] == [("R-087-01", 6, 1)]


def test_R_087_01_a_hit_from_an_attacker_the_side_sees_and_the_unit_cannot_reach_is_one_it_cannot_answer(inv):
    """R-087-01: "an attacker it cannot see or cannot reach" (checker excuse, round5.md Third pass). Unit 1 (layer 0, reach up 0 and down 1) is hit in tick 5 by attacker 3, which its side SEES, standing
    on layer 1 (one layer above, outside its reach): the unit stands still from tick 6: reported in tick 6. Opposite cases: the same seen attacker on layer 0, inside its reach: silent (a hit it can answer);
    the attacker on layer 1 but the unit able to reach one layer up (reach 1, 1): silent."""
    assert keys(march(inv, seen_hit=True, still_from=6, attacker_layer=1, reach=(0, 1)))[:1] == [("R-087-01", 6, 1)]
    assert march(inv, seen_hit=True, still_from=6, attacker_layer=0, reach=(0, 1)) == []
    assert march(inv, seen_hit=True, still_from=6, attacker_layer=1, reach=(1, 1)) == []


# ---------------------------------------------------------------------------------------------------------------- R-087-01, once

def pace(inv, second_hit_at=None, second_run_at=62, arrived_attack_mover=False, plain_mover=False, targeted=False, pushed=False, guard=False):
    """Unit 1 (side 0) idle (or an arrived attack-mover) at x 1000, hit once in tick 5 by an unseen attacker (unit 3, side 1); it moves 10 wu a frame west for 20 frames (a move away of
    200 wu, ticks 6 to 25), holds, and moves 10 wu a frame again for 20 frames from tick `second_run_at`. A second unseen hit in tick `second_hit_at`. Returns R-087-01 violations."""
    frames, x = [], 1000.0
    for k in range(120):
        if 6 <= k <= 25 or second_run_at <= k < second_run_at + 20:
            x -= 10.0
        r1 = row(x, 100, target=(2 if (targeted and k >= second_run_at) else 0), dest=None, attack_move=arrived_attack_mover, order=7)
        if plain_mover:
            r1.update(dest=(0.0, 100.0), attack_move=False)
        units = {1: r1, 3: row(x + 500, 600, side=1)}
        if targeted:
            units[2] = row(x - 200, 100, side=1)
        if pushed:
            units[4] = row(x + 20, 100)            # a friend within 40 wu: the run is a collision push
        frames.append((units, [(3, 1)] if k in (5, second_hit_at) else []))
    tr = trace(*frames)
    for fr in tr:
        fr["visible"] = {0: {2} if targeted else set(), 1: {1}}
        fr["hits"] = list(fr["fires"])
    return inv.check(tr, rules(inv, attack_range={1: 300.0}, guards={1: (1000.0, 100.0)} if guard else {}), only=["R-087-01"]).violations


@pytest.mark.parametrize("arrived", [False, True], ids=["idle", "arrived-attack-mover"])
def test_R_087_01_a_second_move_away_without_a_new_hit_is_flagged(inv, arrived):
    """R-087-01: "it moves 200 wu directly away ... and it holds where the move away ends; it does not walk back into the fire". Planted (the 57-move-away unit of 2026-11-17): hit once in
    tick 5, it moves away in ticks 6 to 25, holds, and moves again from tick 62 with no hit since: flagged in tick 62, for an idle unit and for an arrived attack-mover. Red today: no such check."""
    assert keys(pace(inv, arrived_attack_mover=arrived)) == [("R-087-01", 62, 1)]


@pytest.mark.parametrize("arrived", [False, True], ids=["idle", "arrived-attack-mover"])
def test_R_087_01_control_a_unit_that_moves_away_once_and_holds_is_silent(inv, arrived):
    """R-087-01 control (green today and after): the same unit that holds from tick 26 to the end (the second run is pushed out past the trace) is silent."""
    assert pace(inv, second_run_at=500, arrived_attack_mover=arrived) == []


def test_R_087_01_control_a_repeat_hit_it_cannot_answer_moves_it_again_legally(inv):
    """R-087-01: "a repeat hit it still cannot answer moves it again". Planted: the same second run, but an unseen hit landed in tick 55: silent."""
    assert pace(inv, second_hit_at=55) == []


def test_R_087_01_control_plain_movers_guards_pushes_and_pursuers_are_not_judged(inv):
    """R-087-01 control: the second run is legal for a plain mover (it has a destination and no attack-move), for a guard ("a guard ... ignore[s] the hit"), for a unit whose run is a
    collision push (a friend 20 wu away) and for one that holds a target (it pursues): none is a second move away."""
    assert (pace(inv, plain_mover=True), pace(inv, guard=True), pace(inv, pushed=True), pace(inv, targeted=True)) == ([], [], [], [])


# ---------------------------------------------------------------------------------------------------------------- R-097-05

SLOPE_SETTLE_TICKS = 3       # DRAFT-slope-settle-ticks: the step limit on a slope may leave a pair under 30 wu for this many ticks; the fourth is reported


def pair(inv, gap, layers=(0, 1), slopes=("s1", "s1"), alive=(True, True), frames=12, close=range(1, 5), flat_gap=60.0):
    """Units 1 and 2 (side 0), `gap` wu apart in the frames of `close` (the first tick of the run is 1) and `flat_gap` apart in the others, on layers `layers`; `slopes` the slope each stands on (None: off
    every slope). Returns R-097-05 violations."""
    def at(k):
        g = gap if k in close else flat_gap
        return {1: row(1000, 1000, layer=layers[0], alive=alive[0]), 2: row(1000 + g, 1000, layer=layers[1], alive=alive[1])}
    tr = trace(*[at(k) for k in range(frames)])

    def slope_at(x, y):
        return slopes[0] if x == 1000.0 else slopes[1]
    return inv.check(tr, rules(inv, slope_at=slope_at), only=["R-097-05"]).violations


def test_R_097_05_two_units_on_one_slope_closer_than_30_wu_for_more_than_3_ticks_are_flagged_across_the_layer_line(inv):
    """R-097-05: "two units within 30 wu that both stand on the same slope, whichever side of its midline each is on"; round5.md Third pass: a pair is reported only after more than
    DRAFT-slope-settle-ticks = 3 ticks under 30 wu. Planted: units 1 (layer 0) and 2 (layer 1) on one slope 20 wu apart in ticks 1 to 4 (60 apart before and after): flagged once, in tick 4 (the
    fourth), for the lower id. Controls: 3 ticks close (1 to 3) is silent, and a pair close for 3 ticks, apart for one and close for 3 more is silent (the count restarts)."""
    assert keys(pair(inv, 20.0)) == [("R-097-05", 4, 1)]
    assert pair(inv, 20.0, close=range(1, 1 + SLOPE_SETTLE_TICKS)) == []
    assert pair(inv, 20.0, close=[1, 2, 3, 5, 6, 7]) == []


def test_R_097_05_the_same_pair_on_one_layer_is_flagged_too(inv):
    """R-097-05: the slope case is by slope, not by layer: two units on layer 1, on one slope, 20 wu apart for 4 ticks are flagged in the fourth, and once for a pair that stays close for 12 ticks.
    Control: the same pair 3 ticks is silent."""
    assert keys(pair(inv, 20.0, layers=(1, 1))) == [("R-097-05", 4, 1)]
    assert keys(pair(inv, 20.0, layers=(1, 1), close=range(1, 10))) == [("R-097-05", 4, 1)]
    assert pair(inv, 20.0, layers=(1, 1), close=range(1, 4)) == []


@pytest.mark.parametrize("gap", [30.0, 28.5, 45.0], ids=["pushed-apart-30", "inside-the-slack", "far"])
def test_R_097_05_control_a_pair_pushed_to_30_wu_is_silent(inv, gap):
    """R-097-05 control (green today and after): the same two units, close for 8 ticks, 30 wu apart (the pass's result), 28.5 apart (inside the DRAFT-slope-slack of 2 wu) or 45 apart are silent."""
    assert pair(inv, gap, close=range(1, 9)) == []


def test_R_097_05_control_units_not_on_one_slope_are_not_judged(inv):
    """R-097-05 control: "Units on different layers that are not on one slope still do not collide" (round5.md G5): the same 20 wu pair, close for 8 ticks, on flat ground (no slope), with one unit on a
    slope and the other off it, on two different slopes, or with one of them dead, is silent."""
    close = range(1, 9)
    assert [pair(inv, 20.0, slopes=(None, None), close=close), pair(inv, 20.0, slopes=("s1", None), close=close), pair(inv, 20.0, slopes=("s1", "s2"), close=close),
            pair(inv, 20.0, alive=(True, False), close=close)] == [[], [], [], []]


def flips(inv, changes):
    """Unit 1 changes layer in each frame of `changes` (0, 1, 0, ...), alone on a slope. Returns R-097-05 violations."""
    layer, tr = 0, []
    for k in range(60):
        if k in changes:
            layer = 1 - layer
        tr.append({1: row(1000 + k, 1000, layer=layer)})
    return inv.check(trace(*tr), rules(inv, slope_at=lambda x, y: "s1"), only=["R-097-05"]).violations


def test_R_097_05_a_unit_that_flips_layer_three_times_in_20_ticks_is_not_reported(inv):
    """R-097-05 (round5.md second pass: the flip predicate is withdrawn; a unit's layer on a slope is its side of the midline, E-01 R-004-06, so a push across the midline is a legal change):
    layer changes in ticks 10, 14 and 18 (up, down, up) are silent. Control: the withdrawn predicate would have reported tick 18; a unit that is also closer than 30 wu to another for 4 ticks is still
    reported, so the check is still running."""
    assert flips(inv, {10, 14, 18}) == []
    assert keys(pair(inv, 20.0)) == [("R-097-05", 4, 1)]


def test_R_097_05_control_two_changes_or_three_far_apart_are_silent(inv):
    """R-097-05 control (green today and after): up and back down (ticks 10 and 14) is a legal pass over the midline, and three changes 20 ticks apart (10, 30, 50) are three separate crossings."""
    assert flips(inv, {10, 14}) == [] and flips(inv, {10, 30, 50}) == []
