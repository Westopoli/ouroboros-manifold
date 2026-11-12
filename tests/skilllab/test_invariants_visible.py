# Rule pins: R-093-02
"""Engine rules round 2, T3, check 2: `R-093-02` fire only at what your side sees. Pure predicates; the real fights are
tests/skilllab/arena/test_invariants_round2_wiring.py.

R-093-02 (docs/bible/epics/E-12-fog-and-sensors.md): "Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is in its
side's visible set: the union of what that side's living units see ... and what its pings reveal".

THE API THIS FILE PINS: RULES gains "R-093-02" as its last entry. In frame k > 0, every unit in "fires" (attacker, target) and every living unit whose
"target" is a living unit has that target in frame[k-1]["visible"][side of the unit] (the state before the step that decided it; measured on L-0039 and
L-0061: 0 violations in 551 and 1947 shots and 22,110 and 47,862 held-target ticks against the previous frame's set, 11 and 104 shots against the
frame's own set, because the shot killed the target). A frame with no "visible" key is not checked. violation {"rule": "R-093-02", "tick": k, "unit": u}.
Rules(suspended={"R-093-02": switch}) suspends it: no violation, Report.suspended names the switch (targeting by sight off).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401


@pytest.fixture(scope="module")
def inv():
    return _Module()


def frames(target=0, fires_at=None, visible=frozenset({2}), prev_visible=None, ticks=4):
    """Unit 1 (side 0) and enemy 2 (side 1) stand still; unit 1 holds `target` from frame 2 on. `visible` is side 0's set in every frame, `prev_visible` the
    set of frame 1 only (to plant a target that was not seen before the step)."""
    out = []
    for k in range(ticks + 1):
        units = {1: row(100, 100, target=target if k >= 2 else 0), 2: row(300, 100, side=1)}
        fires = [(1, 2)] if fires_at == k else []
        out.append((units, fires))
    tr = trace(*out)
    for fr in tr:
        fr["visible"] = {0: set(visible), 1: {1}}
    if prev_visible is not None:
        tr[1]["visible"] = {0: set(prev_visible), 1: {1}}
    return tr


def test_R_093_02_control_a_unit_that_sees_its_target_is_silent(inv):
    """Control (green today): a clean trace through check() reports nothing for any rule."""
    assert inv.check(frames(target=2), rules(inv)).violations == []


def test_R_093_02_rules_lists_it_ninth(inv):
    """R-093-02 is one of the checks, appended to RULES as the ninth; R-096-08 and R-087-10 were appended after it (eleven checks in all)."""
    assert tuple(inv.RULES)[8] == "R-093-02" and len(inv.RULES) == 11


def test_R_093_02_a_unit_that_holds_an_unseen_target_is_flagged(inv):
    """R-093-02 'acquires, pursues': planted, unit 1 holds enemy 2 from frame 2 while side 0's set is empty."""
    v = inv.check(frames(target=2, visible=()), rules(inv), only=["R-093-02"]).violations
    assert [(x["rule"], x["tick"], x["unit"]) for x in v][:1] == [("R-093-02", 2, 1)]


def test_R_093_02_a_unit_that_fires_at_an_unseen_target_is_flagged(inv):
    """R-093-02 'fires at': planted, unit 1 fires at enemy 2 in frame 3 while side 0 does not see it (it holds no target in the trace)."""
    v = inv.check(frames(fires_at=3, visible=()), rules(inv), only=["R-093-02"]).violations
    assert [(x["rule"], x["tick"], x["unit"]) for x in v] == [("R-093-02", 3, 1)]


def test_R_093_02_the_set_before_the_step_decides(inv):
    """R-093-02 (measured): enemy 2 seen in frame 1 and gone from the set in frame 2, when unit 1 shoots it in frame 2 (a shot that kills a target takes it out of
    the set): silent. Control: unseen in frame 1 and seen in frame 2: flagged."""
    ok = frames(fires_at=2, visible=(), prev_visible={2})
    bad = frames(fires_at=2, visible={2}, prev_visible=())
    got = (inv.check(ok, rules(inv), only=["R-093-02"]).violations, [v["tick"] for v in inv.check(bad, rules(inv), only=["R-093-02"]).violations])
    assert got == ([], [2])


def test_R_093_02_a_trace_with_no_visible_set_is_not_checked(inv):
    """The existing traces carry no "visible": silent (no false flags on the old API)."""
    tr = trace(*[{1: row(100, 100, target=2), 2: row(300, 100, side=1)}] * 4)
    assert inv.check(tr, rules(inv), only=["R-093-02"]).violations == []


def test_R_093_02_is_suspended_when_targeting_by_sight_is_off(inv):
    """R-093-02 with OM_TP_TARGET_BY_SIGHT off: no violation, and the report names the switch (never a silent pass)."""
    rep = inv.check(frames(target=2, visible=()), rules(inv, suspended={"R-093-02": "OM_TP_TARGET_BY_SIGHT"}), only=["R-093-02"])
    assert (rep.violations, rep.suspended, rep.invalid) == ([], {"R-093-02": "OM_TP_TARGET_BY_SIGHT"}, False)


def test_R_093_02_the_monitor_suspends_it_with_sight_off(inv):
    """suspended_for("off") names R-093-02 as well as R-087-03; "on" suspends neither."""
    assert (inv.suspended_for("off"), inv.suspended_for("on")) == (
        {"R-087-03": "OM_TP_TARGET_BY_SIGHT", "R-093-02": "OM_TP_TARGET_BY_SIGHT"}, {})


# ------------------------------------------------------------------ Round 2, T8: one tick of lag on sight (R-093-02)
#
# R-093-02 (E-12): "Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is in its side's visible set". The engine validates a lock against sight
# at the start of its tick and drops an unseen target on the NEXT tick, so for one frame a unit still holds a target that was missing from the previous frame's visible set. Measured
# 2026-11-11 on this tree: L-0084 seed 1 sight on, tick 1754, units 33, 39 and 40 each "holds 93, which its side did not see before the step" (the only three R-093-02 reports of the
# fight's 3718 ticks; tests/skilllab/arena/test_invariants_round2b_wiring.py). THE PINNED SEMANTICS: a unit that already held the target in the previous frame is excused the FIRST frame
# in which the previous frame's visible set lacks it; the second consecutive such frame is a violation (reported at that frame, once per unit and frame). A unit that ACQUIRES an unseen
# target (its previous target was another or none) is a violation at once, and a shot at a target outside the previous frame's visible set is a violation at once (no grace for a shot).
# The existing tests above (acquisition of an unseen target at frame 2, a shot at an unseen one) are unchanged by this.

def lag_frames(held, visible, fires_at=None):
    """Unit 1 (side 0) and enemy 2 (side 1) stand still. `held`: the unit's target in frames 0.. (a list of 0 or 2); `visible`: side 0's visible set in frames 0.. (a list of sets);
    `fires_at` the frame in which unit 1 fires at enemy 2."""
    tr = trace(*[({1: row(100, 100, target=t), 2: row(300, 100, side=1)}, [(1, 2)] if fires_at == k else []) for k, t in enumerate(held)])
    for fr, vis in zip(tr, visible):
        fr["visible"] = {0: set(vis), 1: {1}}
    return tr


def lag_hits(inv, tr):
    return [(v["rule"], v["tick"], v["unit"]) for v in inv.check(tr, rules(inv), only=["R-093-02"]).violations]


def test_R_093_02_a_held_target_that_goes_unseen_for_one_frame_and_is_dropped_on_the_next_is_not_a_violation(inv):
    """R-093-02 with the engine's one-tick lag: enemy 2 is seen in frames 0 to 2 and missing from the visible set from frame 2 on (the engine sees it gone at the start of tick 3 and
    drops it on tick 4). Unit 1 holds it in frames 1 to 3 and drops it in frame 4: the frame-3 check (the visible set of frame 2 lacks it) is the one lagged frame: silent. Red today:
    the check reports unit 1 at tick 3 (L-0084 tick 1754, units 33, 39, 40)."""
    tr = lag_frames(held=[0, 2, 2, 2, 0, 0], visible=[{2}, {2}, set(), set(), set(), set()])
    assert lag_hits(inv, tr) == []


def test_R_093_02_a_held_target_that_stays_unseen_for_two_frames_is_a_violation(inv):
    """R-093-02: the same trace but the unit holds enemy 2 for a second frame after it went missing (frames 3 and 4 against the sets of frames 2 and 3): the first is the lag, the second is
    a violation, reported at frame 4 and only there. Red today: it is reported at frame 3 as well."""
    tr = lag_frames(held=[0, 2, 2, 2, 2, 0], visible=[{2}, {2}, set(), set(), set(), set()])
    assert lag_hits(inv, tr) == [("R-093-02", 4, 1)]


def test_R_093_02_a_shot_at_a_target_outside_the_visible_set_is_a_violation_at_once(inv):
    """R-093-02 'fires at' (no grace for a shot): the unit holds enemy 2 from frame 1, it goes missing from the visible set in frame 2, and unit 1 fires at it in frame 3, the first frame
    in which the previous frame's set lacks it: a violation at frame 3, and it is the shot that is reported. Green today and after (the control that the lag is not a free shot)."""
    tr = lag_frames(held=[0, 2, 2, 2, 0], visible=[{2}, {2}, set(), set(), set()], fires_at=3)
    got = inv.check(tr, rules(inv), only=["R-093-02"]).violations
    assert [(v["rule"], v["tick"], v["unit"]) for v in got] == [("R-093-02", 3, 1)] and "fired" in got[0]["detail"]


def test_R_093_02_a_unit_that_acquires_an_unseen_target_is_a_violation_at_once(inv):
    """R-093-02 'acquires' (no grace for an acquisition): unit 1 has no target in frames 0 and 1, takes enemy 2 in frame 2 while the visible set of frame 1 does not hold it: a violation at
    frame 2. Green today and after: the grace is for a lock the unit already held, not for taking an unseen target."""
    tr = lag_frames(held=[0, 0, 2, 2, 0], visible=[set()] * 5)
    assert lag_hits(inv, tr)[:1] == [("R-093-02", 2, 1)]


def test_R_093_02_a_target_seen_in_every_frame_is_silent(inv):
    """R-093-02 control (green today and after): the lag trace with the target seen in every frame is silent."""
    assert lag_hits(inv, lag_frames(held=[0, 2, 2, 2, 2, 0], visible=[{2}] * 6)) == []
