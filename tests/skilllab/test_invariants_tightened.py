# Rule pins: R-087-09, R-004-06, R-004-08
"""Engine rules round 2, T3, checks 3 and 4: `R-087-09` counts only blocked lines, and `continuity` judges layer changes, not every push. Pure predicates; the real
fights are tests/skilllab/arena/test_invariants_round2_wiring.py and test_invariants_continuity_sight_wiring.py. Extends the API of tests/skilllab/test_invariants.py.

R-087-09 (docs/bible/epics/E-11-units-and-combat.md): "Given an idle or attack-moving unit with a target within its attack range whose line of fire is blocked
by units, cover or ground, When evaluated, Then it steers around the blockers ... and if it finds none within 1 s (20 ticks) it drops the target".
continuity serves R-004-08 (docs/bible/epics/E-01-layer-system.md): "a unit that turns back before the midline has not changed layer and one that crosses the midline
and comes back has changed twice" (with R-004-06, 'its transition progress is its position along the slope'): the layer flips, the position does not jump. No rule limits a
collision push, so the Round 2 PUSH_ALLOWANCE (a push explains at most 2.0 wu) is gone (measured: sixteen Vanguards spawned as one blob move 8 to 14 wu on tick 1; L-0061 and
L-0084 report same-layer pushes of 7.7 to 13.9 wu).

THE API THIS FILE PINS:
    Rules(..., attack_range=None)   {unit id: wu}. R-087-09 runs only while the held target is within attack_range[unit] (planar hypot) AND not "shootable"; a frame
                                    whose target is out of range ends the run (the 20 ticks are consecutive in-range ticks). A unit with no entry is treated as in
                                    range (the old behaviour; the Monitor passes every unit's attack range).
    continuity (Rules.max_step, Rules.blocked_cell), for a unit alive in both frames, bound = max_step[unit] + 1.3 (DRAFT-inv-step-slack):
        the unit starts the tick inside a blocked cell (blocked_cell at its starting cell and starting layer) or on a cell blocked for its new layer: not judged
            (the blocked-cell repair placed it; the checker cannot see that flag);
        its layer differs between the two frames: a displacement above the bound is a violation whoever stands near (no friend excuse, no push allowance);
        its layer is the same: a displacement above the bound is a violation unless another living unit (either side) is within PUSH_RADIUS (40 wu,
            DRAFT-inv-push-radius, as in Round 1) of it at either end of the frame.
    PUSH_ALLOWANCE is no longer a rule constant (left unpinned: the behaviour tests below show no allowance exists).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

DRAFT_PUSH_ALLOWANCE = 2.0     # DRAFT-inv-push-allowance, from the open-field measurement on L-0050 (Westley's to change)


@pytest.fixture(scope="module")
def inv():
    return _Module()


# ------------------------------------------------------------------ R-087-09: only blocked lines

def _held(inv, dists, shootable=False, rng=500.0):
    """Unit 1 holds enemy 2, never closing (the unit stands still; the enemy stands at the given distance in each frame), not shootable unless asked."""
    frames = [{1: row(100, 100), 2: row(100 + dists[0], 100, side=1)}]
    for d in dists:
        frames.append({1: row(100, 100, target=2, shootable=shootable), 2: row(100 + d, 100, side=1)})
    return inv.check(trace(*frames), rules(inv, attack_range={1: rng}), only=["R-087-09"]).violations


def test_R_087_09_control_the_old_planted_stall_with_no_range_given_is_still_flagged(inv):
    """Control (green today): R-087-09 with no attack_range given keeps today's behaviour: 25 ticks of an unshootable held target, not closing, is flagged."""
    frames = [{1: row(100, 100), 2: row(500, 100, side=1)}] + [{1: row(100, 100, target=2, shootable=False), 2: row(500, 100, side=1)}] * 25
    v = inv.check(trace(*frames), rules(inv), only=["R-087-09"]).violations
    assert v and v[0]["rule"] == "R-087-09"


def test_R_087_09_a_blocked_line_in_attack_range_for_more_than_20_ticks_is_flagged(inv):
    """R-087-09: planted, the target stands 400 wu away, the attack range is 500, the line is blocked (not shootable) for 25 ticks and the unit does not close in."""
    v = _held(inv, [400.0] * 25)
    assert v and (v[0]["rule"], v[0]["unit"]) == ("R-087-09", 1) and v[0]["tick"] in (21, 22)


def test_R_087_09_a_target_out_of_attack_range_is_not_a_blocked_line(inv):
    """R-087-09 'a target within its attack range': measured on L-0046, unit 68 held a target 383 wu away with range 300 and was reported. Planted: 25 ticks at
    383 wu, range 300, not shootable, not closing: silent. (Red today: reported.)"""
    assert _held(inv, [383.0] * 25, rng=300.0) == []


def test_R_087_09_the_twenty_ticks_must_be_in_range(inv):
    """R-087-09: 15 in-range blocked ticks then 15 out-of-range ones are no 20-tick stall: silent."""
    assert _held(inv, [400.0] * 15 + [600.0] * 15) == []


def test_R_087_09_a_shootable_target_in_range_is_silent(inv):
    """R-087-09 control: in range and shootable for 25 ticks is silent."""
    assert _held(inv, [400.0] * 25, shootable=True) == []


# ------------------------------------------------------------------ continuity: layer changes do not jump; a push on one layer is not judged

BOUND = 3.5 + 1.3          # max_step 3.5 + DRAFT-inv-step-slack 1.3
FLOOR = lambda cx, cy, layer: False   # noqa: E731  (no blocked cell anywhere)


def _leap(inv, dist, near=None, layers=(0, 0), start=(100.0, 100.0), blocked_cell=None, near_alive=True, near_side=0):
    """Unit 1 (max step 3.5) moves `dist` wu east in one tick, layer `layers[0]` to `layers[1]`. `near` is the distance of a second living unit (id 3) from where
    unit 1 LANDS, standing still along the line of the step; unit 2 is a far enemy. Returns the continuity violations."""
    x0, y0 = start
    x1 = x0 + dist
    before = {1: row(x0, y0, layer=layers[0]), 2: row(900, 900, side=1)}
    after = {1: row(x1, y0, layer=layers[1]), 2: row(900, 900, side=1)}
    if near is not None:
        for fr in (before, after):
            fr[3] = row(x1 + near, y0, side=near_side, alive=near_alive)
    return inv.check(trace(before, after), rules(inv, max_step={1: 3.5, 2: 3.5, 3: 3.5}, blocked_cell=blocked_cell), only=["continuity"]).violations


def _said(v):
    return [(x["rule"], x["tick"], x["unit"]) for x in v]


def test_continuity_control_an_unpushed_step_within_the_slack_is_silent(inv):
    """Control (green today): 4.7 wu with max_step 3.5 + slack 1.3 and no neighbour is silent, on one layer and on a layer change."""
    assert _leap(inv, 4.7) == [] and _leap(inv, 4.7, layers=(0, 1)) == []


@pytest.mark.parametrize("dist", [6.5, 6.9, 7.5, 25.0], ids=["6.5", "6.9", "7.5", "25"])
def test_R_004_08_a_same_layer_displacement_beside_a_friend_is_silent(inv, dist):
    """R-004-08 serves continuity (a unit changing layer does not jump); no rule limits a collision push, so on a tick with no layer change a displacement above
    max_step + slack is excused by another living unit within 40 wu (DRAFT-inv-push-radius, as in Round 1). Planted: 6.5 / 6.9 / 7.5 / 25 wu beside a friend 30 wu from
    where the unit lands, same layer: silent. (Red today for 6.9, 7.5 and 25: the Round 2 allowance flags a step more than 2.0 wu over the bound; 6.5 is a control.)"""
    assert _leap(inv, dist, near=30.0) == []


def test_R_004_08_a_same_layer_leap_beside_an_enemy_is_silent(inv):
    """R-004-08 / continuity: 'another living unit' is either side: a 25 wu step with an enemy 30 wu from where the unit lands and no layer change is silent."""
    assert _leap(inv, 25.0, near=30.0, near_side=1) == []


def test_R_004_08_a_same_layer_leap_alone_is_a_violation(inv):
    """R-004-08 / continuity: a 25 wu step with nobody within 40 wu (control, green today) is a violation, tick 1, unit 1; the same with the neighbour 60 wu away
    (outside the push radius) and with the neighbour dead 30 wu away (a living unit is needed)."""
    assert _said(_leap(inv, 25.0)) == [("continuity", 1, 1)]
    assert _said(_leap(inv, 25.0, near=60.0)) == [("continuity", 1, 1)]
    assert _said(_leap(inv, 25.0, near=30.0, near_alive=False)) == [("continuity", 1, 1)]


def test_R_004_08_a_leap_on_a_layer_change_tick_is_a_violation_beside_a_friend(inv):
    """R-004-08 'a unit that turns back before the midline has not changed layer and one that crosses the midline and comes back has changed twice': a unit that changes
    layer does not jump. Planted: 25 wu in one tick, layer 0 to 1, with a friend 30 wu from where it lands: a violation, tick 1, unit 1 (a control, green today: a leap far over
    the Round 2 allowance is flagged; the small excess is in the test below, red today)."""
    assert _said(_leap(inv, 25.0, near=30.0, layers=(0, 1))) == [("continuity", 1, 1)]


@pytest.mark.parametrize("layers", [(0, 1), (1, 0)], ids=["up", "down"])
def test_R_004_08_a_layer_change_beside_a_friend_has_no_push_allowance(inv, layers):
    """R-004-08 / continuity: on a layer-change tick the bound is max_step + slack = 4.8 wu and nothing excuses more: 5.0 and 6.5 wu beside a friend are violations (the
    Round 2 allowance of 2.0 made 6.5 silent), 4.7 wu is silent."""
    assert [bool(_leap(inv, d, near=30.0, layers=layers)) for d in (4.7, 5.0, 6.5)] == [False, True, True]


def test_R_004_08_a_step_at_exactly_the_bound_on_a_layer_change_tick_is_silent(inv):
    """R-004-08 / continuity: a layer-change step of exactly max_step + slack (3.5 + 1.3 = 4.8 wu) is silent; 4.81 wu is a violation (control: the bound is not a blanket
    silence). Premise: the planted displacement equals the bound in the checker's own arithmetic."""
    assert 0.0 + BOUND - 0.0 == BOUND == 4.8
    assert _leap(inv, BOUND, layers=(0, 1), start=(0.0, 100.0)) == []
    assert _said(_leap(inv, BOUND + 0.01, layers=(0, 1), start=(0.0, 100.0))) == [("continuity", 1, 1)]


def test_R_004_08_a_unit_that_starts_the_tick_inside_a_blocked_cell_is_not_judged(inv):
    """R-004-08 / continuity: a unit moved by the blocked-cell repair (`leave_blocked`; the checker cannot see that flag) starts the tick inside a blocked cell. Planted:
    unit 1 starts at (550, 450), inside blocked cell (5, 4) of layer 0, and ends 25 wu east, alone: silent. Control (green today): the same step from an open cell
    (cell (5, 4) blocked, the unit starting at (350, 450)) is a violation, and so is a step that ENDS in the blocked cell from an open one."""
    def blocked(cx, cy, layer):
        return (cx, cy) == (5, 4) and layer == 0
    assert _leap(inv, 25.0, start=(550.0, 450.0), blocked_cell=blocked) == []
    assert _said(_leap(inv, 25.0, start=(350.0, 450.0), blocked_cell=blocked)) == [("continuity", 1, 1)]
    assert _said(_leap(inv, 25.0, start=(490.0, 450.0), blocked_cell=blocked)) == [("continuity", 1, 1)]


def test_R_004_08_a_repair_on_a_layer_change_tick_is_not_judged_either(inv):
    """R-004-08 / continuity: not judged 'that tick' also when the repaired unit changes layer: it starts inside blocked cell (5, 4) of layer 0, ends 25 wu east on layer 1,
    alone: silent. Control (green today): the same layer-change leap from an open cell is a violation."""
    def blocked(cx, cy, layer):
        return (cx, cy) == (5, 4) and layer == 0
    assert _leap(inv, 25.0, start=(550.0, 450.0), layers=(0, 1), blocked_cell=blocked) == []
    assert _said(_leap(inv, 25.0, start=(350.0, 450.0), layers=(0, 1), blocked_cell=blocked)) == [("continuity", 1, 1)]


def test_R_004_08_a_unit_that_starts_on_a_cell_blocked_for_its_new_layer_is_not_judged(inv):
    """R-004-08 / continuity: the starting cell (5, 4) is open on the unit's layer 0 and blocked on layer 1, the layer it ends the tick on (the repair put it back
    onto an open cell): silent for a 25 wu step 0 to 1. Control (green today): the starting cell (3, 4) blocked on no layer is a violation."""
    def blocked(cx, cy, layer):
        return (cx, cy) == (5, 4) and layer == 1
    assert _leap(inv, 25.0, start=(550.0, 450.0), layers=(0, 1), blocked_cell=blocked) == []
    assert _said(_leap(inv, 25.0, start=(350.0, 450.0), layers=(0, 1), blocked_cell=blocked)) == [("continuity", 1, 1)]
