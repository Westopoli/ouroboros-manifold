# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 item 4 as corrected by the Architect's 2026-10-20 ruling (L8M, relayed; the damage_up caps README calls it decision 49); the number DRAFT-reengage-moved-wu = 1 wu is Westley's and unchanged
"""LAB-REV2-L8M: what counts as 'moved' for the re-engage silence counter (scripts/skilllab/fight.py, _Reengage). Tests only.

THE RULE (Architect, 2026-10-20). A side's silence counter ADVANCES on a tick when (i) no unit of EITHER side fired this tick (a unit fires
when an enemy unit's hp falls), and (ii) no IDLE-ELIGIBLE unit of that side is displaced by MORE than contract.REENGAGE_MOVED_WU (strictly;
Euclidean; DRAFT-reengage-moved-wu, 1 wu, Westley's number) from its position at the WINDOW START (the tick the counter was last zeroed; at
the very start, the spawn). Otherwise the counter is zeroed and a new window starts (a fresh reference for the side's living units).
IDLE-ELIGIBLE (the existing definition, unchanged): no destination (engine.unit_destination is None) AND the unit holds an attack-move role
(a guard holder, or a group whose latest order is move/group_move/idle/guard, does not). A unit holding a destination is NOT tested for
movement and NEVER zeroes the counter; when the counter completes the re-engage orders go to the idle-eligible units only, and a
destination-holder gets no order at all (its destination and its order state are untouched).
Why: a unit that holds an unreachable destination and shuttles in a ~70 wu loop (period ~40 ticks) zeroed the old counter forever (old
reading: ANY living unit displaced above 1 wu from its position at the last reset, destination or not, and a hit zeroed only the shooter's
side): the capped damage_up fight (tests/skilllab/integration/test_reengage_moved_real.py).

WHAT THESE TESTS PIN AND DO NOT PIN
  Pinned: the jitter loop and a steady march of a destination-holder never zero the counter; idle teammates are re-engaged one order each at
  tick N; the holder is never ordered; the strict > 1 wu line on an idle unit with a jittering holder beside it; a guard-role unit is not
  idle-eligible so its displacement does not count; a creep of an idle unit is measured from the window start, not from the previous tick.
  NOT PINNED (a question for the Architect, see the report): a unit that held a destination during the window and then arrives (becomes
  idle-eligible): whether its displacement since the window start zeroes the counter on arrival (reading the window-start reference
  literally) or the counter keeps running (reference refreshed while it held a destination). No test here has a unit change from holder to
  idle inside a window, apart from the two opening ticks, where every unit of the fake engine holds the opening destination for two steps
  (fakes_reengage.arrive_after = 2) and has not moved.
  The a-hit-by-either-side rule is pinned in test_reengage.py (the three rewritten fire tests); the strict boundary and the Euclidean
  distance in test_drift_fix_reengage.py (settle_then rewritten); both are ledger row TD-LAB-REV2-L8M-moved.
Fakes: fakes_reengage.ReengageFakeEngine; run/G/N/only/kill from test_reengage.py. set_dest is the destination of a holder; set_pos in the
fake's step script moves it."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import contract  # noqa: E402
from test_reengage import G, N, mean_pos, only, run  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")

DEST = (500.0, 0.0)     # the holder's (unreachable, in the loop case) destination


def holder_script(index, path, last, dest=True):
    """Script events {k: [fn]} for k in 0..last: step k + 1 places side 0's unit `index` at path(k, spawn_x, spawn_y); step 0 also gives it
    the permanent destination DEST (set_dest wins over any order) unless dest is False."""
    spawn = {}

    def make(k):
        def fn(f):
            u = f.units_of(0)[index]
            if k == 0:
                spawn["p"] = (f.units[u]["x"], f.units[u]["y"])
                if dest:
                    f.set_dest(u, DEST)
            x, y = path(k, *spawn["p"])
            f.set_pos(u, x, y)
        return fn
    return {k: [make(k)] for k in range(last + 1)}


def loop(k, x0, y0, radius=35.0, period=40):
    """A closed loop of diameter 70 wu through the spawn point, one lap per `period` ticks."""
    a = 2.0 * math.pi * (k + 1) / period
    return x0 + radius * (math.cos(a) - 1.0), y0 + radius * math.sin(a)


def march(k, x0, y0, step=2.0):
    return x0 + step * (k + 1), y0


def merged(*scripts):
    out = {}
    for sc in scripts:
        for k, fns in sc.items():
            out.setdefault(k, []).extend(fns)
    return out


def displace(index, dx, dy=0.0):
    def fn(f):
        u = f.units_of(0)[index]
        f.set_pos(u, f.units[u]["x"] + dx, f.units[u]["y"] + dy)
    return fn


def holder_of(fake):
    return fake.units_of(0)[0]


def orders_to(fake, u):
    """Every order issued after the opening that names unit u (the opening orders are at tick 0)."""
    return [o for o in fake.order_log if o[0] > 0 and u in o[2]]


# ---------------------------------------------------------------------------------------------------------- the jitter loop

def test_a_destination_holder_looping_70_wu_does_not_stop_the_idle_units_being_reengaged():
    """The traced stall. Side 0: eight units, the first holds a destination and shuttles round a 70 wu loop with a period of 40 ticks (it
    is displaced above 1 wu from where it stood at every window start); seven are idle; every enemy is visible and out of range.
    At tick N the counter completes: ONE event, seven per-unit orders, none for the holder. Red on the old counter (the loop zeroes it each
    tick: no order for side 0 at all)."""
    res, fake = run([G(0, 8), G(1, 2)], cap=3 * N, script_events=holder_script(0, loop, 3 * N))
    holder, idle = holder_of(fake), fake.units_of(0)[1:]
    calls = fake.reengage_calls(0)
    assert len(calls) == 7 and {t for t, _i, _g in calls} == {N}, calls
    assert sorted(u for _t, ids, _g in calls for u in ids) == sorted(idle)
    assert all(len(ids) == 1 for _t, ids, _g in calls)
    assert all(g == pytest.approx(mean_pos(fake, fake.units_of(1))) for _t, _i, g in calls)
    assert len(fake.reengage_orders(0)) == 1 and res.reengage[0] == 1, fake.reengage_orders(0)
    assert orders_to(fake, holder) == []
    assert fake.unit_destination(None, holder) == DEST


def test_control_the_loop_really_moves_the_holder_more_than_one_wu_from_the_window_start():
    """Positive control for the fixture: within a lap (bar the tick it closes the loop) the holder stands more than the threshold from where it started and
    swings 60 wu and more away within a lap (so a counter that tested it would be zeroed), and side 1, which has no holder, is re-engaged at
    N like side 0."""
    res, fake = run([G(0, 8), G(1, 2)], cap=N, script_events=holder_script(0, loop, N))
    x0, y0 = next((x, y) for u, _t, _f, x, y, _l in fake.spawn_log() if u == holder_of(fake))
    away = [math.hypot(x - x0, y - y0) for x, y in (loop(k, x0, y0) for k in range(N - 1))]
    assert min(away) > contract.REENGAGE_MOVED_WU and max(away) > 60.0
    assert only(fake.reengage_orders(1))[0] == N


# ---------------------------------------------------------------------------------------------------------- the marching holder

def test_a_marching_destination_holder_is_left_alone_while_its_idle_teammates_are_reengaged():
    """Positive control of the mechanism: the holder advances 2 wu a tick towards its destination (never idle, never silent); its three idle
    teammates are re-engaged at N, one order each. The holder's order state is byte-identical: no order call names it after the opening and
    its destination is the one it had."""
    res, fake = run([G(0, 4), G(1, 2)], cap=N + 5, script_events=holder_script(0, march, N + 5))
    holder, idle = holder_of(fake), fake.units_of(0)[1:]
    calls = fake.reengage_calls(0)
    assert [t for t, _i, _g in calls] == [N] * 3 and sorted(u for _t, ids, _g in calls for u in ids) == sorted(idle), calls
    assert all(len(ids) == 1 for _t, ids, _g in calls)
    assert orders_to(fake, holder) == []
    assert fake.dest[holder] == DEST and fake.unit_destination(None, holder) == DEST
    assert res.reengage[0] == 1 and len(fake.reengage_orders(0)) == 1


def test_control_the_same_march_without_a_destination_zeroes_the_counter():
    """Negative control: the marching unit with NO destination is idle-eligible, so its march (2 wu a tick) zeroes the counter every tick
    and side 0 is not re-engaged by tick N + 5; side 1 is (shows the scene would re-engage)."""
    res, fake = run([G(0, 4), G(1, 2)], cap=N + 5, script_events=holder_script(0, march, N + 5, dest=False))
    assert fake.reengage_orders(0) == [] and res.reengage[0] == 0
    assert only(fake.reengage_orders(1))[0] == N


# ---------------------------------------------------------------------------------------------------------- the 1 wu line on an idle unit

@pytest.mark.parametrize("dx,moved", [
    (5.0, True),            # well above the line
    (1.001, True),
    (1.0, False),           # exactly the line: strict greater-than
    (0.999, False),
    (0.5, False),
])
def test_an_idle_unit_displaced_above_one_wu_zeroes_the_counter_with_a_jittering_holder_beside_it(dx, moved):
    """Side 0: a looping holder plus three idle units. The second unit (idle) is displaced by dx from where it stands at tick N - 4. Above
    1 wu it zeroes the counter (order at 2N - 4); at or below it does not (order at N); the holder's loop zeroes nothing either way.
    Side 1 is the control: at N."""
    sc = merged(holder_script(0, loop, 2 * N + 5), {N - 5: [displace(1, dx)]})
    res, fake = run([G(0, 4), G(1, 2)], cap=2 * N + 5, script_events=sc)
    assert only(fake.reengage_orders(0))[0] == (2 * N - 4 if moved else N)
    assert only(fake.reengage_orders(1))[0] == N
    assert holder_of(fake) not in [u for _t, ids, _g in fake.reengage_calls(0) for u in ids]


def test_a_creep_of_an_idle_unit_is_measured_from_the_window_start_not_from_the_previous_tick():
    """0.05 wu a tick is 2 wu by tick N: above the line from the window start (the spawn), yet far below it from one tick to the next.
    Side 0 (a looping holder plus the creeping idle unit) is zeroed and is not re-engaged at N; side 1 is. Kills 'reference = previous tick'."""
    def creeper(k, x0, y0):
        return x0 + 0.05 * (k + 1), y0
    spawn = {}

    def make(k):
        def fn(f):
            u = f.units_of(0)[1]
            spawn.setdefault("p", (f.units[u]["x"], f.units[u]["y"]))
            f.set_pos(u, creeper(k, *spawn["p"])[0], spawn["p"][1])
        return fn
    sc = merged(holder_script(0, loop, N + 5), {k: [make(k)] for k in range(N + 5)})
    res, fake = run([G(0, 3), G(1, 2)], cap=N + 3, script_events=sc)
    assert fake.reengage_orders(0) == [] and only(fake.reengage_orders(1))[0] == N


# ---------------------------------------------------------------------------------------------------------- a hit by either side

@pytest.mark.parametrize("victim", (0, 1))
def test_a_hit_on_a_side_that_never_fired_still_zeroes_its_counter(victim):
    """Condition (i): no unit of EITHER side fired. A unit of `victim` loses hp at tick N - 4 (the other side fired; `victim` did not), so both
    counters restart: both sides are re-engaged at 2N - 4, the victim included (the old counter zeroed only the shooter's side: N). Both sides
    carry a looping holder, so a late order cannot be the holder's doing."""
    def hit(f):
        f.set_hp(f.units_of(victim)[1], 90.0)
    res, fake = run([G(0, 4), G(1, 4)], cap=2 * N + 5, script_events=merged(holder_script(0, loop, 2 * N + 5), {N - 5: [hit]}))
    assert {t for t, _i, _g in fake.reengage_calls(victim)} == {N - 4 + N}
    assert {t for t, _i, _g in fake.reengage_calls(1 - victim)} == {N - 4 + N}


# ---------------------------------------------------------------------------------------------------------- who is idle-eligible

def test_a_guard_role_unit_is_not_idle_eligible_so_its_displacement_does_not_count():
    """The existing definition: idle needs the attack-move role. A guard-stance unit displaced 5 wu at tick N - 4 (pushed) is not tested; the
    attack-move units of the side are re-engaged at N and the guard unit gets no order. Control: the same displacement of an attack-move unit
    delays the order to 2N - 4."""
    guard = G(0, 2, order="guard")
    res, fake = run([G(0, 3), guard, G(1, 2)], cap=2 * N + 5, script_events={N - 5: [displace(3, 5.0)]})
    attack, guards = fake.units_of(0)[:3], fake.units_of(0)[3:]
    calls = fake.reengage_calls(0)
    assert {t for t, _i, _g in calls} == {N} and sorted(u for _t, ids, _g in calls for u in ids) == sorted(attack), calls
    assert all(orders_to(fake, g) == [] for g in guards)
    res2, fake2 = run([G(0, 3), guard, G(1, 2)], cap=2 * N + 5, script_events={N - 5: [displace(0, 5.0)]})
    assert {t for t, _i, _g in fake2.reengage_calls(0)} == {2 * N - 4}


def test_the_threshold_is_still_the_draft_one_wu():
    """The number is unchanged by the ruling (Westley's, DRAFT-reengage-moved-wu): one test also here so that this file alone fails if it moves."""
    assert contract.REENGAGE_MOVED_WU == 1.0
