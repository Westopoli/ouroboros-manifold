# Rule pins: R-097-05
"""Round 6, L4 first bullet (docs/northstar/plans/engine-rules-2026-11-08/round6.md): the lab checker reports two units on one layer that stay overlapped.

round6.md L4: "R-097-05, same layer: two units on one layer closer than 28 wu for more than `DRAFT-ramp-settle-ticks` 3 ticks are reported, as the slope pair is. With a planted case it
reports and a legal case it does not. On real fights it reports until E3 is merged: expected, and listed." (The second bullet, an attack-move that ended short of its point, is not tested yet.)
Rule text (docs/bible/epics/E-13-movement-and-command.md R-097-05): "Given two units on the same layer within 30 wu (2 x radius 15) ... When the collision pass runs, Then they are pushed apart
along the line between them until 30 wu apart"; 28 wu is the 30 wu less DRAFT-ramp-slack (2 wu), the sweep's I13 and the slope pair's own limit (`invariants_r5.SLOPE_GAP - SLOPE_SLACK`).

THE API THIS FILE PINS (the lab builder builds to it; frames and rows as in tests/skilllab/test_invariants.py):

    scripts/skilllab/invariants_r6.py
        OVERLAP_GAP            28.0   wu: a pair strictly closer than this is overlapped
        OVERLAP_SETTLE_TICKS   3      DRAFT-ramp-settle-ticks: a pair is reported in the frame in which it has stayed overlapped for more than this many consecutive frames (the fourth)
        SameLayerOverlap       a small state machine like invariants_r5.SlopeCollision: `.feed(frame, prev, tick, out)` appends {"rule": "R-097-05", "tick", "unit": min(a, b), "detail"}
    scripts/skilllab/invariants.py
        imports SameLayerOverlap from invariants_r6 (the same object) and feeds it each frame when "R-097-05" is judged (selected by `only` or by default, and not suspended). It runs
        whether or not `Rules.slope_at` is given. RULES is unchanged (the rule is R-097-05, the pins of its length stay): a pair on one layer AND one slope is still reported once, not twice.
    a pair is two LIVING units on ONE layer, on any side, whatever the ground; units on different layers, and a dead unit, are never part of one. A pair is reported once while it stays close;
    the count restarts when the pair is apart (28 wu or more) for a frame.

Green today: the controls that the existing slope predicate already satisfies (the pair on one layer and one slope is reported once). Red today: everything else, for the missing module or
because the checker does not look at two units on one layer when no slope is given.
"""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

GAP = 28.0
SETTLE = 3                   # DRAFT-ramp-settle-ticks


@pytest.fixture(scope="module")
def inv():
    return _Module()


def keys(vs):
    return [(v["rule"], v["tick"], v["unit"]) for v in vs]


def pair(inv, gap, layers=(0, 0), alive=(True, True), close=range(1, 5), frames=12, far=60.0, only=("R-097-05",), **rule_kw):
    """Units 1 and 2 (side 0) `gap` wu apart in the frames of `close` (the first tick of the run is 1), `far` apart in the others, on `layers`. Returns the violations of `only`."""
    def at(k):
        g = gap if k in close else far
        return {1: row(1000, 1000, layer=layers[0], alive=alive[0]), 2: row(1000 + g, 1000, layer=layers[1], alive=alive[1])}
    tr = trace(*[at(k) for k in range(frames)])
    return inv.check(tr, rules(inv, **rule_kw), only=list(only) if only else None).violations


# ---------------------------------------------------------------------------------------------------------------- the module

def test_R_097_05_the_module_and_its_two_numbers_exist():
    """L4: `scripts/skilllab/invariants_r6.py` holds the predicate with its two numbers. Red today: no such module."""
    try:
        mod = importlib.import_module("scripts.skilllab.invariants_r6")
    except ModuleNotFoundError as err:
        pytest.fail("L4 not built: %s" % err)
    assert (mod.OVERLAP_GAP, mod.OVERLAP_SETTLE_TICKS) == (GAP, SETTLE) and callable(mod.SameLayerOverlap)


def test_R_097_05_the_checker_uses_that_module_s_predicate_and_keeps_its_rule_list(inv):
    """L4 'wired into invariants.py last', as invariants_r5's predicates are: `invariants.SameLayerOverlap` is the module's class, and RULES is the thirteen of Round 5 (the rule is R-097-05).
    Red today: the module is missing."""
    try:
        mod = importlib.import_module("scripts.skilllab.invariants_r6")
    except ModuleNotFoundError as err:
        pytest.fail("L4 not built: %s" % err)
    assert inv.SameLayerOverlap is mod.SameLayerOverlap
    assert tuple(inv.RULES)[-2:] == ("R-087-01", "R-097-05") and len(inv.RULES) == 13


# ---------------------------------------------------------------------------------------------------------------- planted: reported

def test_R_097_05_two_units_on_one_layer_closer_than_28_wu_for_more_than_3_ticks_are_flagged_once(inv):
    """L4 planted case: units 1 and 2 on layer 0, 20 wu apart in ticks 1 to 4 (60 apart before and after, no slope on the map): reported once, in tick 4 (the fourth), for the lower id; and a pair that
    stays close for 12 ticks is still reported once. Red today: the checker judges only pairs on a slope."""
    assert keys(pair(inv, 20.0)) == [("R-097-05", 4, 1)]
    assert keys(pair(inv, 20.0, close=range(1, 10))) == [("R-097-05", 4, 1)]


def test_R_097_05_the_report_names_the_pair_and_the_distance(inv):
    """L4: a violation is {rule, tick, unit, detail} (test_invariants.py): the detail names both unit ids."""
    found = pair(inv, 20.0)
    assert len(found) == 1, found
    v = found[0]
    assert set(v) == {"rule", "tick", "unit", "detail"} and "1" in v["detail"] and "2" in v["detail"]


def test_R_097_05_the_pair_is_reported_on_either_side_and_just_inside_28_wu(inv):
    """L4: 'two units on one layer', whichever side each is on, and the limit is a strict 'closer than 28': 27.9 wu apart for 4 ticks is reported (an enemy pair and a friendly pair alike)."""
    assert keys(pair(inv, 27.9)) == [("R-097-05", 4, 1)]
    frames = [{1: row(1000, 1000), 2: row(1020, 1000, side=1)} for _ in range(6)]
    assert keys(inv.check(trace(*frames), rules(inv), only=["R-097-05"]).violations) == [("R-097-05", 4, 1)]


def test_R_097_05_the_pair_is_reported_on_a_layer_above_zero_too(inv):
    """L4: both units on layer 2: reported in the fourth tick."""
    assert keys(pair(inv, 20.0, layers=(2, 2))) == [("R-097-05", 4, 1)]


def test_R_097_05_a_pair_that_closes_again_after_being_apart_is_reported_again_after_its_own_four_ticks(inv):
    """L4: the count restarts when the pair is apart for a frame: close in ticks 1 to 4 (reported in 4), apart in 5, close in 6 to 9 (reported in 9): two reports, one per run."""
    assert keys(pair(inv, 20.0, close=[1, 2, 3, 4, 6, 7, 8, 9], frames=14)) == [("R-097-05", 4, 1), ("R-097-05", 9, 1)]


# ---------------------------------------------------------------------------------------------------------------- legal: not reported

@pytest.mark.parametrize("gap", [28.0, 30.0, 45.0], ids=["exactly-28", "pushed-apart-30", "far"])
def test_R_097_05_control_28_wu_or_more_apart_is_silent(inv, gap):
    """L4 legal case: the same two units on one layer, 'close' for 8 ticks at 28.0 (the limit itself), 30 (the pass's result) or 45 wu apart: silent."""
    assert pair(inv, gap, close=range(1, 9)) == []


def test_R_097_05_control_under_28_wu_for_3_ticks_or_fewer_is_silent(inv):
    """L4 legal case: 'more than 3 ticks': 20 wu apart in ticks 1 to 3 is silent; so is a pair close for 3 ticks, apart for one and close for 3 more (the count restarts), and a pair that is close
    for one tick only."""
    assert pair(inv, 20.0, close=range(1, 1 + SETTLE)) == []
    assert pair(inv, 20.0, close=[1, 2, 3, 5, 6, 7]) == []
    assert pair(inv, 20.0, close=[4]) == []


def test_R_097_05_control_units_on_different_layers_are_silent(inv):
    """L4 legal case: 'units on different layers' (they do not collide, R-097-05, E-01): 20 wu apart for 8 ticks on layers 0 and 1, and on layers 1 and 2, with no slope: silent."""
    assert pair(inv, 20.0, layers=(0, 1), close=range(1, 9)) == []
    assert pair(inv, 20.0, layers=(1, 2), close=range(1, 9)) == []


def test_R_097_05_control_a_dead_unit_is_not_part_of_a_pair(inv):
    """L4 legal case: 'a dead unit': 20 wu apart for 8 ticks with either unit dead: silent."""
    assert pair(inv, 20.0, alive=(True, False), close=range(1, 9)) == []
    assert pair(inv, 20.0, alive=(False, True), close=range(1, 9)) == []


def test_R_097_05_control_a_unit_that_dies_while_close_ends_the_run(inv):
    """L4: the pair is close in ticks 1 to 3 with both alive, the second unit is dead from tick 4 (still lying 20 wu away): not reported in tick 4 or after."""
    def at(k):
        return {1: row(1000, 1000), 2: row(1020, 1000, alive=k < 4)}
    assert inv.check(trace(*[at(k) for k in range(12)]), rules(inv), only=["R-097-05"]).violations == []


# ---------------------------------------------------------------------------------------------------------------- wiring

def test_R_097_05_wiring_the_pair_is_in_the_default_run_and_only_and_suspension_are_honoured(inv):
    """L4 'wired into invariants.py': with no `only` (every rule) the planted pair is among the violations; `only` naming other rules leaves it out; a Rules that suspends R-097-05 reports
    none and lists it as suspended. Red today: the checker does not judge a pair on flat ground."""
    default = pair(inv, 20.0, only=None)
    assert [k for k in keys(default) if k[0] == "R-097-05"] == [("R-097-05", 4, 1)]
    assert [v for v in pair(inv, 20.0, only=("R-087-04", "R-084-04")) if v["rule"] == "R-097-05"] == []
    tr = trace(*[{1: row(1000, 1000), 2: row(1020, 1000)} for _ in range(8)])
    rep = inv.check(tr, rules(inv, suspended={"R-097-05": "planted"}), only=["R-097-05"])
    assert rep.violations == [] and rep.suspended == {"R-097-05": "planted"}


def test_R_097_05_wiring_one_pair_on_one_layer_and_one_slope_is_reported_once_not_twice(inv):
    """L4 'reported once, as the slope pair is' (control, green today and after): with `slope_at` given and both units on layer 1 on one slope, 20 wu apart for 12 ticks, the checker reports one
    violation in tick 4, not one from the slope predicate and one from this. The same pair on one layer and on flat ground (slope_at given, but off every slope) is reported once, in tick 4:
    that part is red today."""
    on_slope = pair(inv, 20.0, layers=(1, 1), close=range(1, 13), slope_at=lambda x, y: "s1")
    off_slope = pair(inv, 20.0, layers=(1, 1), close=range(1, 13), slope_at=lambda x, y: None)
    assert (keys(on_slope), keys(off_slope)) == ([("R-097-05", 4, 1)], [("R-097-05", 4, 1)])


def test_R_097_05_wiring_two_layers_on_one_slope_stay_the_slope_predicates_alone(inv):
    """L4 (control, green today and after): a pair on different layers that both stand on one slope is the slope predicate's (R-097-05, `invariants_r5.SlopeCollision`): still reported once, in
    tick 4, and this predicate adds nothing for it."""
    assert keys(pair(inv, 20.0, layers=(0, 1), slope_at=lambda x, y: "s1")) == [("R-097-05", 4, 1)]
