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
