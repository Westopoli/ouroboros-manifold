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
