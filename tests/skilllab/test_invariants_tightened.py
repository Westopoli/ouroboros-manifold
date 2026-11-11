# Rule pins: R-087-09, R-004-06
"""Engine rules round 2, T3, checks 3 and 4: `R-087-09` counts only blocked lines, and `continuity` without the friend excuse. Pure predicates; the real
fights are tests/skilllab/arena/test_invariants_round2_wiring.py. Extends the API of tests/skilllab/test_invariants.py.

R-087-09 (docs/bible/epics/E-11-units-and-combat.md): "Given an idle or attack-moving unit with a target within its attack range whose line of fire is blocked
by units, cover or ground, When evaluated, Then it steers around the blockers ... and if it finds none within 1 s (20 ticks) it drops the target".
continuity: the checker's own rule that no unit leaps (E-13 Invariants; see test_invariants.py); a push may explain at most the overlap it resolves.

THE API THIS FILE PINS:
    Rules(..., attack_range=None)   {unit id: wu}. R-087-09 runs only while the held target is within attack_range[unit] (planar hypot) AND not "shootable";
                                    a frame whose target is out of range ends the run (the 20 ticks are consecutive in-range ticks). A unit with no entry is
                                    treated as in range (the old behaviour; the Monitor passes every unit's attack range).
    PUSH_ALLOWANCE = 2.0            module constant of scripts/skilllab/invariants.py, DRAFT-inv-push-allowance (wu): continuity flags a displacement above
                                    max_step + STEP_SLACK + (PUSH_ALLOWANCE if another living unit is within PUSH_RADIUS (40 wu) at either end, else 0).
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


# ------------------------------------------------------------------ continuity: a push explains only the overlap it resolves

def _jump(inv, dist, neighbour):
    after = {1: row(100 + dist, 100), 2: row(900, 900, side=1)}
    if neighbour:
        after[3] = row(100 + dist + 30, 100)
    before = {1: row(100, 100), 2: row(900, 900, side=1)}
    if neighbour:
        before[3] = row(100 + dist + 30, 100)
    return inv.check(trace(before, after), rules(inv, max_step={1: 3.5, 2: 3.5, 3: 3.5}), only=["continuity"]).violations


def test_continuity_control_an_unpushed_step_within_the_slack_is_silent(inv):
    """Control (green today): 4.7 wu with max_step 3.5 + slack 1.3 and no neighbour is silent."""
    assert _jump(inv, 4.7, False) == []


def test_continuity_push_allowance_is_the_named_draft_two_wu(inv):
    """DRAFT-inv-push-allowance 2.0: the constant exists in the checker with that value."""
    assert inv.PUSH_ALLOWANCE == DRAFT_PUSH_ALLOWANCE


def test_continuity_a_leap_beside_a_friend_is_flagged(inv):
    """continuity: planted, unit 1 moves 25 wu in a tick (max step 3.5) with a unit 30 wu from where it lands. Today the friend excuses it (measured on L-0061:
    629 unit-ticks over max speed + slack, 538 over it by more than 2 wu, all beside a unit, all reported as 0)."""
    v = _jump(inv, 25.0, True)
    assert [(x["rule"], x["tick"], x["unit"]) for x in v] == [("continuity", 1, 1)]


@pytest.mark.parametrize("dist,flagged", [(6.5, False), (6.9, True), (7.5, True)], ids=["within-allowance", "just-over", "over"])
def test_continuity_a_push_explains_at_most_two_wu(inv, dist, flagged):
    """continuity (DRAFT-inv-push-allowance 2.0): beside a friend the limit is max_step 3.5 + slack 1.3 + 2.0 = 6.8 wu: 6.5 silent, 6.9 and 7.5 flagged."""
    assert bool(_jump(inv, dist, True)) == flagged


def test_continuity_the_allowance_is_for_pushed_units_only(inv):
    """continuity: 5.5 wu (0.7 over 4.8) with no neighbour is flagged: the allowance does not apply to an unpushed unit (green today, stays)."""
    assert [x["tick"] for x in _jump(inv, 5.5, False)] == [1]
