# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 items 2, 3 and 4 (Architect, 2026-10-19; item 4's number is Westley's)
"""LAB-REV2-FIX round 2: the re-engage issues one order per idle unit, retries a no-op, and counts a move only above 1 wu.

INTERFACE FOR THE BUILDER
  scripts/skilllab/contract.py
    REENGAGE_MOVED_WU = 1.0      # DRAFT-reengage-moved-wu (Westley's number): the word DRAFT on this definition line; a float
  scripts/skilllab/report.py     report.DRAFT_TEXT gains "DRAFT-reengage-moved-wu" (listed once, always, in the artifact header;
                                 test_report.py pins the list, ledger TD-LAB-REV2-FIX-moved)
  scripts/skilllab/fight.py      _Reengage:
    ITEM 2 (per-unit). When a side re-engages it calls engine.order_attack_move(w, [u], x, y) ONCE PER idle attack-move unit u, (x, y) the
      same centroid of the enemies the side sees for every unit; never order_group_move, never a multi-unit call, never fight._chunks,
      whatever Setup.orders_per_unit says (the re-engage is a lab-issued order exempt from the play's orders mode). The event count is
      unchanged: reengage[s] += 1 per trigger, however many units were ordered. Why: om_command_group_move gives each unit the slot
      click + (own position - group centroid), so a straggler's slot is where it already stands (a no-op).
    ITEM 3 (no-op retry). An engage is a NO-OP when, one tick after it (the loop iteration after engine step N + 1), every unit it ordered
      still reads engine.unit_destination(w, u) is None. A no-op re-arms the side at once and zeroes its silence counter, so the side
      retries after another REENGAGE_SILENCE_TICKS silent ticks. The retry tick is NOT PINNED between 2N and 2N + 1 (counted from the
      order or from the tick that found the no-op); each retry is one more event (reengage[s] += 1: every trigger is one event). An
      engage after which at least one ordered unit has a destination is not a no-op and is not retried inside the same silence period.
    ITEM 4 (moved), as ruled by the Architect on 2026-10-20 (L8M; ledger TD-LAB-REV2-L8M-moved; the full rule and its tests are in
      test_drift_fix_moved.py): a side has MOVED only when an IDLE-ELIGIBLE living unit of it (no destination, attack-move role; a unit
      holding a destination is never tested) is displaced by MORE than contract.REENGAGE_MOVED_WU (strictly, Euclidean: L1 and Chebyshev fail
      the (0.6, 0.6) and (0.8, 0.8) cases; exactly 1 wu is not a move) from its position at the WINDOW START, the tick the side's counter was
      last zeroed (at the very start, the spawn); a rolling reference fails 5 tests of test_reengage.py and 7+ cases here. ANY such unit
      moving above the threshold moves the side (not the first unit, not the centroid). Every zeroing (a move, a hit dealt by the side itself,
      the re-arm after a no-op) takes a fresh reference for the side's living units; a hit dealt to the side zeroes nothing (decision 49 as amended by decision 50,
      condition (i); FINDING-lab-d11). DRAFT number: contract.REENGAGE_MOVED_WU = 1 wu.
    UNPINNED, THE BUILDER'S CHOICE (two interface points the tests do not fix): (a) a no-op check made on a side that fired or moved
      between the order and the check: the check may be skipped (the reset has already re-armed the side) or run; (b) the retry tick
      between 2N and 2N + 1, and every ordered unit dying (nothing left to check) are not pinned. PINNED: an ordered unit that is DEAD at
      the check is not counted: the check reads the living ordered units only (test_a_dead_ordered_unit_is_not_counted_in_the_noop_check).
Fakes: fakes_reengage.ReengageFakeEngine (arrive_after=2 default = an order that works, arrive_after=None = every order a no-op)."""
import dataclasses
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_reengage import ReengageFakeEngine  # noqa: E402
from scripts.skilllab import contract, report  # noqa: E402
from test_reengage import G, N, kill, mean_pos, only, run  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")


# ---------------------------------------------------------------------------------------------------------- item 2: one order per idle unit

@pytest.mark.parametrize("per_unit", (True, False))
def test_every_idle_unit_gets_its_own_attack_move_onto_the_enemy_centroid(per_unit):
    """Positive control of the whole mechanism: side 0 has three units, side 1 two. Each unit of each side is ordered by a call that
    names it alone, all onto the one centroid of the enemy, at tick N; no group move is issued; the count is one event per side."""
    res, fake = run([G(0, 3), G(1, 2)], cap=N + 5, orders_per_unit=per_unit)
    for side, want in ((0, 3), (1, 2)):
        calls = fake.reengage_calls(side)
        assert len(calls) == want and {t for t, _i, _g in calls} == {N}, calls
        assert sorted(u for _t, ids, _g in calls for u in ids) == sorted(fake.units_of(side))
        assert all(len(ids) == 1 for _t, ids, _g in calls)
        assert all(g == pytest.approx(mean_pos(fake, fake.units_of(1 - side))) for _t, _i, g in calls)
    assert [o for o in fake.order_log if o[0] > 0 and o[1] != "attack_move"] == []
    assert tuple(res.reengage) == (1, 1)


@pytest.mark.parametrize("per_unit", (True, False))
def test_a_spread_side_is_ordered_unit_by_unit_with_no_chunk_offsets(per_unit):
    """The straggler case: four units 600 wu apart (fight._chunks would split a group order and give each chunk an offset). Each unit
    is ordered alone onto the plain centroid, not onto click + offset."""
    wide = dataclasses.replace(G(0, 4), params={"spacing": 600.0})
    res, fake = run([wide, G(1, 2)], cap=N + 5, orders_per_unit=per_unit)
    calls = fake.reengage_calls(0)
    assert len(calls) == 4 and all(len(ids) == 1 for _t, ids, _g in calls)
    centroid = mean_pos(fake, fake.units_of(1))
    assert all(g == pytest.approx(centroid) for _t, _i, g in calls)
    assert res.reengage[0] == 1


def test_only_idle_living_attack_move_units_are_ordered_one_each():
    """Three units, one with a destination (not idle), one killed on the first step: one call, for the third."""
    def busy(f):
        f.set_dest(f.units_of(0)[0], (0.0, 0.0))
    res, fake = run([G(0, 3), G(1, 2)], cap=N + 5, script_events={0: [busy, kill(0, 1)]})
    calls = fake.reengage_calls(0)
    assert [ids for _t, ids, _g in calls] == [[fake.units_of(0)[2]]] and calls[0][0] == N    # decision 49 as amended by decision 50: side 0 did not fire, the kill of its unit does not delay it (TD-LAB-REV2-L8M-moved: N + 1 on the L8M tip)


# ---------------------------------------------------------------------------------------------------------- item 3: a no-op engage is retried

class FirstEngageFake(ReengageFakeEngine):
    """The first re-engage of `side` (the orders issued at its first post-opening tick) takes effect for only its first `effective`
    orders (0: a no-op), or, with `works`, for the orders whose ordinal (0 = the first order of that tick) is in `works`; every later
    order works. Needs the default arrive_after."""

    def __init__(self, side=0, effective=0, works=None, **kw):
        super().__init__(**kw)
        self.side, self.effective, self.works, self.first_tick, self.taken = side, effective, works, None, 0

    def _give(self, ids, goal):
        if self.step_count > 0 and goal is not None and set(ids) <= set(self.units_of(self.side)):
            if self.first_tick is None:
                self.first_tick = self.step_count
            if self.step_count == self.first_tick:
                self.taken += 1
                if (self.taken - 1) not in self.works if self.works is not None else self.taken > self.effective:
                    return
        super()._give(ids, goal)


def test_a_noop_engage_is_retried_after_another_window_and_the_retry_is_an_event():
    res, fake = run([G(0, 3), G(1, 2)], cap=3 * N + 5, fake=FirstEngageFake(side=0, effective=0))
    ticks = [t for t, _i, _g in fake.reengage_orders(0)]
    assert len(ticks) == 2 and ticks[0] == N, ticks
    assert 2 * N <= ticks[1] <= 2 * N + 1, ticks           # counted from the order or from the tick that found the no-op: not pinned
    assert [len(c[1]) for c in fake.reengage_calls(0)] == [1] * 6          # three units, two events, per unit each time
    assert tuple(res.reengage) == (2, 1)
    assert [t for t, _i, _g in fake.reengage_orders(1)] == [N]          # control: the side whose order worked is not retried


def test_an_engage_that_works_is_not_retried_in_the_same_silence_period():
    """Negative control: the same fight with a working first order has one event per side over three windows."""
    res, fake = run([G(0, 3), G(1, 2)], cap=3 * N + 5)
    assert tuple(res.reengage) == (1, 1) and [t for t, _i, _g in fake.reengage_orders(0)] == [N]


def test_a_partly_effective_engage_is_not_a_noop():
    """One of the three ordered units has a destination one tick later: not a no-op, so no retry."""
    res, fake = run([G(0, 3), G(1, 2)], cap=3 * N + 5, fake=FirstEngageFake(side=0, effective=1))
    assert [t for t, _i, _g in fake.reengage_orders(0)] == [N] and tuple(res.reengage) == (1, 1)


def test_a_working_order_on_a_later_unit_is_not_a_noop():
    """Kills 'only the first ordered unit is looked at': three units, only the THIRD order takes effect. Not a no-op, so no retry."""
    res, fake = run([G(0, 3), G(1, 2)], cap=3 * N + 5, fake=FirstEngageFake(side=0, works={2}))
    assert [t for t, _i, _g in fake.reengage_orders(0)] == [N] and tuple(res.reengage) == (1, 1)


def test_control_the_same_engage_with_no_working_order_is_retried():
    """Control for the test above: works=set() is the all-no-op engage."""
    res, fake = run([G(0, 3), G(1, 2)], cap=3 * N + 5, fake=FirstEngageFake(side=0, works=set()))
    assert len(fake.reengage_orders(0)) == 2 and tuple(res.reengage) == (2, 1)


def test_a_dead_ordered_unit_is_not_counted_in_the_noop_check():
    """PINNED (audit item 5). Two units are ordered; the first one's order works (a destination) and the unit is killed in the next step; the
    second one's order is a no-op. The check reads the LIVING ordered units: the second has no destination, so the engage is a no-op and is
    retried. A builder that counted the dead unit's destination would see a working order and never retry."""
    res, fake = run([G(0, 2), G(1, 2)], cap=3 * N + 5, fake=FirstEngageFake(side=0, works={0}), script_events={N: [kill(0, 0)]})
    assert [t for t, _i, _g in fake.reengage_orders(0)][0] == N
    assert len(fake.reengage_orders(0)) == 2, fake.reengage_orders(0)


def test_an_engage_that_never_works_is_retried_every_window_not_every_tick():
    res, fake = run([G(0, 2), G(1, 2)], cap=4 * N + 10, fake=ReengageFakeEngine(arrive_after=None))
    for side in (0, 1):
        ticks = [t for t, _i, _g in fake.reengage_orders(side)]
        assert ticks[0] == N and len(ticks) >= 3, ticks
        assert all(N <= b - a <= N + 1 for a, b in zip(ticks, ticks[1:])), ticks
        assert res.reengage[side] == len(ticks)


# ---------------------------------------------------------------------------------------------------------- item 4: moved means more than 1 wu

def test_the_moved_threshold_is_the_draft_one_world_unit():
    """DRAFT-reengage-moved-wu: Westley's number; contract.REENGAGE_MOVED_WU, the word DRAFT on its definition line."""
    assert hasattr(contract, "REENGAGE_MOVED_WU"), "contract.REENGAGE_MOVED_WU is not defined"
    assert isinstance(contract.REENGAGE_MOVED_WU, float) and contract.REENGAGE_MOVED_WU == 1.0
    lines = [ln for ln in (ROOT / "scripts" / "skilllab" / "contract.py").read_text().splitlines() if re.match(r"^REENGAGE_MOVED_WU\s*=", ln)]
    assert len(lines) == 1 and "DRAFT" in lines[0] and "DRAFT-reengage-moved-wu" in lines[0]


def test_the_artifact_header_text_names_the_moved_draft():
    assert "DRAFT-reengage-moved-wu" in report.DRAFT_TEXT


def creep(per_tick, last):
    """Script events {k: fn} that slide side 0's first unit by `per_tick` wu per step, steps 1 to last + 1."""
    start = {}

    def make(k):
        def fn(f):
            u = f.units_of(0)[0]
            start.setdefault("p", (f.units[u]["x"], f.units[u]["y"]))
            f.set_pos(u, start["p"][0] + per_tick * (k + 1), start["p"][1])
        return fn
    return {k: [make(k)] for k in range(last + 1)}


def test_a_creep_of_under_one_wu_over_the_window_is_silence():
    """0.02 wu per tick is 0.8 wu by tick N (0.84 by the cap): every tick's position differs, no move. Side 0 is re-engaged at N like
    its motionless enemy (control)."""
    res, fake = run([G(0), G(1)], cap=N + 3, script_events=creep(0.02, N + 2))
    assert only(fake.reengage_orders(0))[0] == N and only(fake.reengage_orders(1))[0] == N


def test_a_slide_of_more_than_one_wu_over_the_window_is_a_move():
    """Positive control for the detector: 0.05 wu per tick is 2 wu by tick N, so side 0 has moved and is not re-engaged at N."""
    res, fake = run([G(0), G(1)], cap=N + 3, script_events=creep(0.05, N + 2))
    assert [t for t, _i, _g in fake.reengage_orders(0)] == [] and only(fake.reengage_orders(1))[0] == N


def settle_then(dx, dy=0.0, k=N - 5):
    """TD-LAB-REV2-L8M-moved (was: the first unit jumped to the origin in step 1, a 'move' that zeroed the counter at tick 1 and made the
    unmoved order N + 1; under the L8M ruling a unit still holding its opening destination is never tested, and the window starts at the
    spawn). Side 0's first idle unit is displaced by (dx, dy) from where it stands in step k + 1 (tick N - 4)."""
    def displace(f):
        u = f.units_of(0)[0]
        f.set_pos(u, f.units[u]["x"] + dx, f.units[u]["y"] + dy)
    return {k: [displace]}


@pytest.mark.parametrize("dx,dy,moved", [
    (1.0, 0.0, False),        # exactly 1 wu: the boundary, strict greater-than
    (0.999, 0.0, False),
    (-1.0, 0.0, False),
    (0.0, 1.0, False),
    (1.001, 0.0, True),
    (-1.5, 0.0, True),
    (0.0, 2.0, True),
    (0.8, 0.8, True),         # 1.13 wu Euclid: moved (Chebyshev would read 0.8: not moved)
    (0.6, 0.6, False),        # 0.85 wu Euclid: not moved (L1 would read 1.2: moved)
])
def test_a_displacement_counts_as_a_move_only_above_one_wu(dx, dy, moved):
    """A displacement of (dx, dy) of the first unit from its spawn at tick N - 4 restarts the silence (order at 2N - 4) when it is above 1 wu
    and does not (order at N) when it is not. Side 1 is the control."""
    res, fake = run([G(0), G(1)], cap=2 * N + 5, script_events=settle_then(dx, dy))
    assert only(fake.reengage_orders(0))[0] == (2 * N - 4 if moved else N)
    assert only(fake.reengage_orders(1))[0] == N


def test_any_unit_of_a_side_moving_above_the_threshold_moves_the_side():
    """Three units, only the THIRD slides 2 wu at tick N - 4 (the other two stand still): the side has moved and is re-engaged at 2N - 4. Kills
    'first unit only' and 'centroid of the side' (the centroid moves 0.67 wu). Side 1 is the control."""
    third = {N - 5: [nudge_third(2.0)]}
    res, fake = run([G(0, 3), G(1, 2)], cap=2 * N + 5, script_events=third)
    assert only(fake.reengage_orders(0))[0] == 2 * N - 4 and only(fake.reengage_orders(1))[0] == N


def test_control_the_same_unit_sliding_half_a_wu_leaves_the_side_silent():
    res, fake = run([G(0, 3), G(1, 2)], cap=2 * N + 5, script_events={N - 5: [nudge_third(0.5)]})
    assert only(fake.reengage_orders(0))[0] == N


def nudge_third(dx):
    def fn(f):
        u = f.units_of(0)[2]
        f.set_pos(u, f.units[u]["x"] + dx, f.units[u]["y"])
    return fn
