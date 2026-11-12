# Rule pins: R-087-03, R-087-09, R-096-08
"""Engine rules round 2, repin: the lock check's excuses, which no test covered (scripts/skilllab/invariants.py `_gave_up`, commit f6225f93).

R-087-03: a lock is held while its target lives and is seen; swapping to another target then is a violation. R-087-09: a unit that holds a target within attack
range whose line is blocked, and does not close in, gives it up after DRAFT-inv-stuck-ticks 20 consecutive ticks; the swap that ends such a lock is not an R-087-03
violation. R-096-08: a guard whose held target stands so far beyond the guard's radius that no spot inside the radius reaches it lets go of it; that swap is not one either.

Planted frames, the pure checker (R-087-03 only selected): unit 1 stands still at (100, 100) with attack range 500, holds enemy 2 at 400 wu with the line blocked
(`shootable` False) for N frames, then takes enemy 4 (still alive and seen, order unchanged).

PREMISE, measured 2026-11-11 on s/engine-rules-r2-repin (the Round 2 engine and checker), L-0046 seed 1 sight on (`arena.run`, 1612 ticks), `_gave_up` instrumented
at every swap that reaches it (274 swaps): 229 swaps came with the swapper's stuck run on the old target at exactly 20 frames (none at any other length) and were
excused as R-087-09; 45 came with no stuck run and were judged as swaps (the fight reports one INVALID R-087-03, tick 207 unit 68). So the engine gives a lock up
after 20 unshootable in-range frames, and the checker (which excuses from 19 frames, one less than the engine's window) excuses the engine's own give-up.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

ENGINE_WINDOW = 20       # frames: measured on L-0046 above; the checker's DRAFT-inv-stuck-ticks


@pytest.fixture(scope="module")
def inv():
    return _Module()


def _swap_after(inv, stuck_frames, shootable_between=None):
    """R-087-03 violations of a trace where unit 1 holds enemy 2 unshootable in frames 1..stuck_frames and takes enemy 4 in frame stuck_frames + 1."""
    frames = [{1: row(100, 100), 2: row(500, 100, side=1), 4: row(480, 140, side=1)}]
    for k in range(1, stuck_frames + 1):
        shoot = shootable_between is not None and k in shootable_between
        frames.append({1: row(100, 100, target=2, shootable=shoot), 2: row(500, 100, side=1), 4: row(480, 140, side=1)})
    frames.append({1: row(100, 100, target=4), 2: row(500, 100, side=1), 4: row(480, 140, side=1)})
    return inv.check(trace(*frames), rules(inv, attack_range={1: 500.0}), only=["R-087-03"]).violations


def test_R_087_03_control_the_swap_of_a_lock_that_was_never_stuck_is_flagged(inv):
    """Control: a shootable lock swapped away (nothing excuses it) is an R-087-03 violation, so the tests below are not silent for want of a check."""
    assert [(v["rule"], v["unit"]) for v in _swap_after(inv, ENGINE_WINDOW, shootable_between=range(1, ENGINE_WINDOW + 1))] == [("R-087-03", 1)]


def test_R_087_03_a_lock_given_up_after_the_r_087_09_window_is_not_a_swap(inv):
    """R-087-09 excuse: the target was unshootable, in range and not closed in on for the engine's 20 frames (measured on L-0046); taking another target then is silent."""
    assert _swap_after(inv, ENGINE_WINDOW) == []


@pytest.mark.parametrize("stuck_frames", [1, 2, 10])
def test_R_087_03_a_lock_that_ended_soon_after_it_became_unshootable_is_a_swap(inv, stuck_frames):
    """R-087-09 excuse, the other side: the same swap one tick after the target became unshootable (and after 2 and 10 frames) is an R-087-03 violation."""
    got = _swap_after(inv, stuck_frames)
    assert [(v["rule"], v["tick"], v["unit"]) for v in got] == [("R-087-03", stuck_frames + 1, 1)]


def _guard_swap(inv, old_at):
    """A guard (post (100, 100), radius 200 + 1, attack range 100) holds enemy 2 standing `old_at` wu from the post (shootable), takes enemy 4 at tick 3."""
    def frame(target):
        return {1: row(100, 100, target=target), 2: row(100 + old_at, 100, side=1), 4: row(100, 140, side=1)}
    frames = [frame(0), frame(2), frame(2), frame(4)]
    return inv.check(trace(*frames), rules(inv, attack_range={1: 100.0}, guards={1: (100.0, 100.0)}), only=["R-087-03"]).violations


def test_R_087_03_a_guards_lock_beyond_what_its_radius_can_reach_is_not_a_swap(inv):
    """R-096-08 excuse: the target stands 600 wu from the post, beyond radius 200 + 1 + attack range 100 = 301; the guard letting go of it is silent."""
    assert _guard_swap(inv, 600.0) == []


def test_R_087_03_a_guards_lock_it_could_have_kept_is_a_swap(inv):
    """R-096-08 excuse, the other side: the target stands 250 wu from the post, inside what the radius reaches (301): the same swap is an R-087-03 violation."""
    assert [(v["rule"], v["tick"], v["unit"]) for v in _guard_swap(inv, 250.0)] == [("R-087-03", 3, 1)]


# ------------------------------------------------------------------ Round 2, T8: two excuses measured wrong (R-096-08 radius, R-087-09 window)
#
# 1. Guard radius drop. R-096-08 (E-13): "... each unit takes its position as its post and engages any target its side can see ..., stepping toward it no farther than [the radius] ...
# a target [that] leaves the radius, never chasing past it". The engine drops a guard's target when the SLANT distance from the guard's post to the target (horizontal distance and the
# band-height difference of the two layers, R-087-10 spherical reach) exceeds 200 (DRAFT-guard-radius) plus the guard's attack range (times the layer-offset multiplier, 1.0 here:
# OM_TP_RANGE_UP_1 = OM_TP_RANGE_DOWN_1 = 1.0), judged on the PREVIOUS frame's positions (the state before the step). The checker (`_gave_up`) measures horizontal distance and adds a 1 wu
# slack, so it does not excuse these two measured drops (2026-11-11, this tree): L-0061 seed 1 tick 42 unit 19 (target 28 at 496.40 wu from the post, layers 1 and 0, height difference 60,
# slant 500.01, limit 200 + 300 = 500) and L-0084 seed 1 tick 349 unit 14 (target 62 at 526.85 wu, height difference 160, slant 550.6, limit 200 + 350 = 550).
# Pinned: the excuse is `slant(post, target in the previous frame) > 200 + attack range`, no slack (the engine's own number is exact), the heights from Rules.layer_heights.
HEIGHTS = [70.0, 130.0, 230.0]         # band floors: layer 1 is 60 wu above layer 0, layer 2 is 160 above it (L-0061 / L-0084 differences)


def _guard_slant_swap(inv, prev_slant, dz, rng, guard_layer, target_layer, now_slant=None):
    """A guard (post (100, 100), on `guard_layer`, attack range `rng`) holds enemy 2 on `target_layer`, whose slant distance from the post is `prev_slant` in frames 0 to 2 (the
    height difference `dz` is part of it) and `now_slant` (default the same) in frame 3, the frame in which it takes enemy 4. Returns the R-087-03 violations as (rule, tick, unit)."""
    def at(slant):
        return 100.0 + math.sqrt(slant ** 2 - dz ** 2)
    now_slant = prev_slant if now_slant is None else now_slant
    def frame(target, slant):
        return {1: row(100, 100, target=target, layer=guard_layer), 2: row(at(slant), 100, side=1, layer=target_layer), 4: row(100, 140, side=1, layer=guard_layer)}
    frames = [frame(0, prev_slant), frame(2, prev_slant), frame(2, prev_slant), frame(4, now_slant)]
    got = inv.check(trace(*frames), rules(inv, attack_range={1: rng}, guards={1: (100.0, 100.0)}, layer_heights=list(HEIGHTS)), only=["R-087-03"]).violations
    return [(v["rule"], v["tick"], v["unit"]) for v in got]


def test_R_096_08_a_guard_drops_a_target_just_beyond_radius_plus_range_by_slant_without_a_swap_violation_L0061(inv):
    """R-096-08 (L-0061 seed 1 tick 42, unit 19): range 300, the target 496.40 wu from the post horizontally and 60 wu up or down (layers 1 and 0), 500.01 wu by slant, limit 500: the
    guard letting go of it is silent. Red today: horizontal 496.40 - 201 = 295.4 is under the range 300, so the checker calls it a swap."""
    assert _guard_slant_swap(inv, 500.01, 60.0, 300.0, 1, 0) == []


def test_R_096_08_a_guard_drops_a_target_just_beyond_radius_plus_range_by_slant_without_a_swap_violation_L0084(inv):
    """R-096-08 (L-0084 seed 1 tick 349, unit 14): range 350, the target 526.85 wu horizontally from the post and 160 wu down (layers 2 and 0), 550.6 wu by slant, limit 550: silent.
    Red today for the same reason (526.85 - 201 = 325.85 under 350)."""
    assert _guard_slant_swap(inv, 550.6, 160.0, 350.0, 2, 0) == []


def test_R_096_08_a_guard_that_drops_a_target_inside_radius_plus_range_by_slant_is_a_swap_violation(inv):
    """R-096-08 control (green today and after): the same guard (range 300, layers 1 and 0) drops a target at slant 480 with the limit at 500: nothing excuses it, an R-087-03 violation at
    the swap frame."""
    assert _guard_slant_swap(inv, 480.0, 60.0, 300.0, 1, 0) == [("R-087-03", 3, 1)]


def test_R_096_08_the_drop_is_judged_on_the_previous_frames_positions(inv):
    """R-096-08: the engine decides on the state before the step. The target is 480 wu by slant from the post in frames 0 to 2 and has moved to 520 by frame 3 (the swap frame): the engine
    saw 480 and had no radius reason: an R-087-03 violation. Red today: the checker also tests the swap frame's own positions. And the other way round (520 before, 480 after) is excused
    (green today and after)."""
    assert (_guard_slant_swap(inv, 480.0, 60.0, 300.0, 1, 0, now_slant=520.0), _guard_slant_swap(inv, 520.0, 60.0, 300.0, 1, 0, now_slant=480.0)) == ([("R-087-03", 3, 1)], [])


def _swap_out_of_range(inv, stuck_frames, start=301.3, closing=0.0, rng=300.0):
    """Unit 1 (attack range `rng`, no route, standing still unless `closing` > 0 wu a frame) holds enemy 2 `start` wu away beyond its range, unshootable, in frames 1..stuck_frames and takes
    enemy 4 in the next frame. Returns the R-087-03 violations as (rule, tick, unit)."""
    def frame(k, target):
        return {1: row(100 + closing * k, 100, target=target, shootable=False), 2: row(100 + start, 100, side=1), 4: row(480, 140, side=1)}
    frames = [{1: row(100, 100), 2: row(100 + start, 100, side=1), 4: row(480, 140, side=1)}]
    frames += [frame(k, 2) for k in range(1, stuck_frames + 1)]
    frames.append(frame(stuck_frames + 1, 4))
    return [(v["rule"], v["tick"], v["unit"]) for v in inv.check(trace(*frames), rules(inv, attack_range={1: rng}), only=["R-087-03"]).violations]


def test_R_087_09_the_engines_window_counts_a_held_target_just_outside_attack_range(inv):
    """R-087-09 window as the engine counts it (csrc/unit.c om_tac_giveup: 'unshootable and not closed in on', whether or not the target is inside attack range; `om_tac_shootable`
    false and distance not falling by more than 1 wu below the run's start, 20 ticks, then the target is dropped): unit 1 holds enemy 2 at 301.3 wu with range 300, standing still with
    no route, for 20 frames, and takes another target in the next: silent. Measured: cover close-up fixture tick 376, unit 13, target 6 at 301.3 wu, range 300, held from tick 356,
    dest None; the swap is the engine's give-up. Red today: `_held` resets the run whenever the target is beyond range, so no run reaches 19 and the swap is flagged."""
    assert _swap_out_of_range(inv, 20) == []


def test_R_087_09_control_a_target_outside_range_held_for_ten_frames_is_still_a_swap(inv):
    """R-087-09 control (green today and after): the same out-of-range hold for only 10 frames is not a give-up: the swap is an R-087-03 violation."""
    assert _swap_out_of_range(inv, 10) == [("R-087-03", 11, 1)]


def test_R_087_09_control_a_unit_closing_in_on_a_target_outside_range_has_not_given_up(inv):
    """R-087-09 control (green today and after): the unit walks toward enemy 2 by 2 wu a frame (350 wu at the start, 310 after 20 frames, still outside range 300): the distance keeps
    falling, 'not closed in on' does not hold, the swap is an R-087-03 violation."""
    assert _swap_out_of_range(inv, 20, start=350.0, closing=2.0) == [("R-087-03", 21, 1)]


@pytest.mark.parametrize("dist,expect_report", [(301.3, False), (400.0, False), (250.0, True)], ids=["just-outside", "far-outside", "inside"])
def test_R_087_09_the_violation_still_judges_only_a_target_inside_attack_range(inv, dist, expect_report):
    """R-087-09 'a target within its attack range whose line of fire is blocked' (control, green today and after; the checker's violation check stays as it is): unit 1 (range 300) stands still
    and holds enemy 2 unshootable for 30 frames: an R-087-09 report only when the target is inside range (250 wu), none at 301.3 or 400."""
    frames = [{1: row(100, 100), 2: row(100 + dist, 100, side=1)}]
    frames += [{1: row(100, 100, target=2, shootable=False), 2: row(100 + dist, 100, side=1)} for _ in range(30)]
    got = inv.check(trace(*frames), rules(inv, attack_range={1: 300.0}), only=["R-087-09"]).violations
    assert bool(got) == expect_report, got
