# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 49 condition (i), AMENDED by the Architect's ruling of 2026-10-20 (a side's silence counter advances when no unit of THAT side fired this tick; not "no unit of either side"); FINDING-lab-d11
"""LAB-REV2-L8M2: the lone shooter must not silence its idle victims (scripts/skilllab/fight.py, _Reengage). Tests only; fake engine.

Decision 49 (amended 2026-10-20), condition (i), FINDING-lab-d11: a side's re-engage silence counter advances on a tick when no unit of THAT
side fired (the pre-L8M own-side reading), and condition (ii) (idle-eligible movement only) stands. The L8M tip read (i) as "no unit of either
side fired": one survivor firing every 16 ticks at idle enemies it can hit and they cannot (they stand outside their own range, so they never
reply) zeroed the victims' counter every 16 ticks, the victims never completed their 40-tick window, and the fight capped with a re-engage
count of (0, 0). The side being shot at without replying is the idle-under-attack case and re-engages. Side-level: no per-victim window.

THE FIXTURE (fake engine; nothing real is simulated, so "outside their effective range" is: the victims, side 1, are idle attack-move
units that never fire after tick 10 and have a visible enemy). Side 0 is ONE unit, the lone shooter. At step 10 (tick 10) a victim lands
its one and only hit on the shooter, so the victims' last shot is tick LAST_VICTIM_SHOT = 10. From tick 16 on the shooter hits a victim every
16 ticks (ticks 16, 32, 48, ...: hp falls by one each time, nobody dies). The victims' own-side counter completes at 10 + N = 50 (N =
REENGAGE_SILENCE_TICKS = 40): their re-engage must be ordered by LAST_VICTIM_SHOT + N + SLACK.
SLACK = 1 tick: test_reengage.py and test_drift_fix_reengage.py pin the exact tick convention (a fire at tick t gives the order at t + N);
this file asserts the property that matters (a shot-at, silent side is not delayed past its own window), so it does not re-pin the
off-by-one. The L8M tip's reading cannot meet it: the shooter's hit at tick 16 zeroes the victims' counter, so their first order could come
at 16 + N = 56 at the earliest, and the shooter's next hit at tick 32 zeroes it again: never, while the shooter keeps firing every 16 ticks
(the cap the real fight showed, reengage (0, 0)).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_reengage import G, N, run  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")

SHOT_EVERY = 16
LAST_VICTIM_SHOT = 10
SLACK = 1


def hit(side, index=0):
    """A unit of `side` (the target) loses one hp: the other side has fired this tick."""
    def fn(f):
        u = f.units_of(side)[index]
        f.set_hp(u, f.units[u]["hp"] - 1.0)
    return fn


def fire_every(shooter_side, victims, first_step, last_step, period=SHOT_EVERY):
    """Script events {step: [fn]}: from step `first_step` every `period` steps up to `last_step`, `shooter_side` hits one of the `victims`
    units of the other side, cycling through them."""
    events, n = {}, 0
    for step in range(first_step, last_step + 1, period):
        events.setdefault(step, []).append(hit(1 - shooter_side, n % victims))
        n += 1
    return events


def merged(*scripts):
    out = {}
    for sc in scripts:
        for k, fns in sc.items():
            out.setdefault(k, []).extend(fns)
    return out


def test_a_lone_shooter_firing_every_16_ticks_does_not_silence_the_idle_victims_it_never_gets_a_reply_from():
    """Decision 49 condition (i), amended 2026-10-20; FINDING-lab-d11. Side 0: the lone shooter, one unit, hitting a side-1 unit every 16
    ticks from tick 16 to the cap. Side 1: four idle attack-move victims whose last (only) shot is at tick 10. The victims' counter is their
    own: it completes at 10 + N, so side 1 is re-engaged by 10 + N + SLACK and its reengage count is at least 1. The shooter fires every 16
    ticks, so its own counter never completes (reengage[0] == 0: the control that the fixture is a shooter that keeps firing). Red on the L8M
    tip, where every shot of the shooter zeroed the victims' counter too (reengage (0, 0) by the cap)."""
    cap = LAST_VICTIM_SHOT + N + SLACK
    sc = merged({LAST_VICTIM_SHOT - 1: [hit(0)]}, fire_every(0, 4, SHOT_EVERY - 1, cap))
    res, fake = run([G(0, 1), G(1, 4)], cap=cap, script_events=sc)
    orders = fake.reengage_orders(1)
    assert len(orders) == 1, f"victims never re-engaged by tick {cap}: orders {orders}, reengage {tuple(res.reengage)}"
    tick = orders[0][0]
    assert LAST_VICTIM_SHOT + N <= tick <= LAST_VICTIM_SHOT + N + SLACK, (tick, tuple(res.reengage))
    assert tuple(res.reengage)[1] >= 1, tuple(res.reengage)
    assert tuple(res.reengage)[0] == 0 and fake.reengage_orders(0) == []


def test_the_lone_shooters_victims_are_still_reengaged_long_after_when_the_shooter_keeps_firing():
    """The same fight run for 4 * N ticks, with the shooter firing every 16 ticks throughout: the victims' event count is exactly 1 (one
    trigger; an order that works leaves the side waiting for its next silence period, and no victim fires again), the shooter's is 0. Kills a
    reading in which the victims are re-engaged only once the shooter stops. Red on the L8M tip (reengage (0, 0))."""
    cap = 4 * N
    sc = merged({LAST_VICTIM_SHOT - 1: [hit(0)]}, fire_every(0, 4, SHOT_EVERY - 1, cap))
    res, fake = run([G(0, 1), G(1, 4)], cap=cap, script_events=sc)
    assert [t for t, _i, _g in fake.reengage_orders(1)] == [LAST_VICTIM_SHOT + N], (fake.reengage_orders(1), tuple(res.reengage))
    assert tuple(res.reengage) == (0, 1)


def test_control_a_symmetric_fight_with_both_sides_firing_does_not_reengage_either_side_during_mutual_fire():
    """Positive control, green on the L8M tip and on the amended reading: both sides fire every 16 ticks (side 0 at ticks 16, 32, ...; side 1
    at ticks 8, 24, 40, ...: each side's own fire zeroes its own counter well inside N = 40, whichever way the counters are kept). Neither side
    is re-engaged during 6 * N ticks of mutual fire: reengage (0, 0) and no re-engage order for either. The amended reading does not make a
    side re-engage while its own units are firing."""
    cap = 6 * N
    sc = merged(fire_every(0, 4, SHOT_EVERY - 1, cap), fire_every(1, 4, SHOT_EVERY // 2 - 1, cap))
    res, fake = run([G(0, 4), G(1, 4)], cap=cap, script_events=sc)
    assert tuple(res.reengage) == (0, 0), (fake.reengage_orders(0), fake.reengage_orders(1))
    assert fake.reengage_orders(0) == [] and fake.reengage_orders(1) == []

