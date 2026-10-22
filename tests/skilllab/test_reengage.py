# Rule pins: R-096-02@e8ae96, R-096-08@629328, R-099-05@ea8d02
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 28 point 3 (the attack-move idle cap, the lab's re-engage order) and decision 33 (readings 1 to 4), amended by decision 43 items 2 to 4 (per-unit orders, no-op retry, the 1 wu moved threshold: tests in test_drift_fix_reengage.py); E-13 R-096-02, R-096-08, R-099-05
"""LAB-REV2-L8: fight() re-engages a silent side. Fake-engine tests of the trigger (tests only; the builder writes scripts/skilllab).

THE RULE (Architect decision 28 point 3, 'moved' semantics as ruled 2026-10-20, L8M, and amended the same day: the counter is the side's OWN; decision 49
as amended by decision 50 (condition (i)); the full rule is in test_drift_fix_moved.py, ledger TD-LAB-REV2-L8M-moved). A side with no ACTIVITY for REENGAGE_SILENCE_TICKS
while an enemy is visible to it has every idle unit holding an attack-move role attack-moved onto the enemy centroid; a guard-stance holder
never gets it (R-096-08). Both sides, naive baselines included. A cap after a re-engage stays a defect (outcome "cap"). ACTIVITY on a tick,
for a side, is: a unit of THAT side fired (a hit dealt by the side zeroes the side's counter and no other: a side that is shot at and does
not reply keeps counting, FINDING-lab-d11), or an idle-eligible living unit of the side is displaced by more than DRAFT-reengage-moved-wu
(1 wu) from its position at the window start (the tick the counter was last zeroed). A unit holding a destination is never tested for
movement. The fire tests below keep their pre-L8M expectations (ledger row).

INTERFACE FOR THE BUILDER (every name below is what these tests import or read; nothing else is pinned)

  scripts/skilllab/contract.py
    REENGAGE_SILENCE_TICKS = 40      # DRAFT (Westley's number: the R-099-05 window, 40 ticks = 2 s); an int
    FightResult.reengage: tuple = (0, 0)   # (side 0 count, side 1 count): re-engage EVENTS per side; default (0, 0)
                                           # (decision 1 style default; every existing FightResult(...) call omits it)
  scripts/skilllab/rows.py
    fight_row adds the two int columns `reengage_0`, `reengage_1` (from FightResult.reengage) AFTER `prefight` (the spec lists them
    last) and BEFORE any feat_* column; both names join rows._FIXED (a label named like them raises ValueError).
  scripts/skilllab/fight.py   (the lab-side re-engage, in the tick loop next to timeline.check)

    OBSERVABLES, all on the Engine methods the lab already has (no new Engine method):
      fire at tick t             some unit's hp read by the loop (engine.unit_hp) is lower at tick t than at tick t-1 (the loop already
                                  reads it every tick): it zeroes the counter of the SHOOTER's side only
      move by side s at tick t   some idle-eligible living unit of s (no destination, attack-move role) reads engine.unit_pos(w, u) more
                                  than DRAFT-reengage-moved-wu from its position at the window start (tick 0 is the spawn reading)
      silent tick                a tick t >= 1 on which side s had neither a fire by s nor a move of s
      idle unit                  a living unit with engine.unit_destination(w, u) is None
      visible enemy              engine.visible_enemies(w, s, living_enemy_ids) is non-empty (the side's sight, om_player_can_see);
                                  read only when a re-engage could fire
      attack-move role           a lab-side record per unit: set by the opening Group.order == "attack_move" and by a timeline
                                  Step "attack_move"; cleared by "move", "group_move", "idle", "guard" (opening or Step). Ping,
                                  set_layer and set_emission leave it alone. A re-engage keeps the role.

    TRIGGER: side s keeps a counter of consecutive silent ticks (a fire BY s, or a move of s, zeroes it and starts a new window). When it has reached
      REENGAGE_SILENCE_TICKS, a visible enemy exists and at least one living idle attack-move unit exists, the side re-engages at
      once (the order is issued in the loop iteration after engine.step number N, so a fake engine's step_count reads N for the first
      one): ONE engine.order_attack_move(w, [u], x, y) call PER such unit (decision 43 item 2, amending decision 33 item 2: a group
      order gives each unit the slot click + (its own position - the group centroid), so a straggler's slot is where it already
      stands), (x, y) = the mean of engine.unit_pos over the
      side's living enemy units THAT ARE VISIBLE to it, i.e. the set engine.visible_enemies returned (decision 33 item 4: never all the
      living enemies, fog would leak into the orders). The order is an (x, y): each unit keeps its own layer and the enemy's layer is
      ignored (decision 33 item 3). reengage[s] += 1: events, one per trigger, not units ordered and not calls (decision 33 item 2, kept by decision 43). The tests
      here read EVENTS (fakes_reengage.reengage_orders merges the per-unit calls of one tick onto one goal); the per-unit calls are
      pinned in test_drift_fix_reengage.py.
      The side then waits for activity: no further re-engage for that side until a fire by that side or a move of that side has zeroed the counter
      and it has again counted REENGAGE_SILENCE_TICKS silent ticks ("once per silence period", decision 33 item 1: an unbroken silence
      is one event, and a re-engage that produces no movement leaves the side silent, so the fight caps). If no enemy is visible, or no
      unit is idle, the counter keeps counting and the re-engage fires on the first tick all three conditions hold (an idle unit that
      appears late, or an enemy that comes into sight late, is ordered at that tick).
    THE RE-ENGAGE IGNORES Setup.orders_per_unit AND THE fight._chunks 450 wu SPLIT (decision 33 item 2, decision 43 item 2): one call per
      idle attack-move unit, whatever orders_per_unit says and however far apart the units stand (tests below).
    The fight ends only as today (elimination, or the cap): a re-engage never ends a fight or hides a cap.

    NOT PINNED (the builder's choice; no test here decides them): the order of the re-engage against timeline.check on the same tick
      (a Step that fires on tick t and a re-engage due on tick t); whether a re-engage is issued on the cap tick itself (the fight is
      over); a unit that dies on the very tick of the re-engage (a dead unit is never ordered, pinned by
      test_a_kill_is_a_hit_and_a_dead_unit_is_not_ordered only for a unit dead the tick before).

    ROWS (test_reengage_rows.py): reengage_0 and reengage_1 join rows._FIXED, as the spec "CSV columns" list says. Decision 34's
      "the fixed-key list in rows.py is unchanged" means only the `point` label (a sweep.py label, not a fixed key); it does not
      forbid these two names.

    SPEED (FINDING-speed-marks-unmet; test_speed.py's 30 s test is pre-existing red and Westley's number, untouched here): read
      positions sparingly. A naive per-tick unit_pos read of every living unit adds about 19% to a fight's time. The move observable
      needs only a cheap read (for instance the sides' units only, and none once a side's counter cannot matter).
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes import FakeEngine  # noqa: E402
from fakes_reengage import ReengageFakeEngine  # noqa: E402
from scripts.skilllab import contract, maps, scenes  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

N = getattr(contract, "REENGAGE_SILENCE_TICKS", 40)   # the fallback only keeps the other tests red for their own reason


def G(side, count=2, order="attack_move", unit="Vanguard"):
    return Group(side=side, unit=unit, count=count, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=None, params={"spacing": 30.0})


def run(groups, cap, fake=None, timeline=(), swap=False, script_events=None, orders_per_unit=True):
    """fight() on a ReengageFakeEngine; script_events {k: callable(fake)} runs inside step number k+1 (k steps already taken)."""
    if fake is None:
        fake = ReengageFakeEngine()
    if script_events:
        fake.script = lambda t, f: [fn(f) for fn in script_events.get(t, [])]
    setup = Setup(groups=tuple(groups), unit_types={}, abilities=False, max_ticks=cap, sample_every=5, timeline=tuple(timeline),
                  orders_per_unit=orders_per_unit)
    return fight(setup, 0, swap, engine=fake), fake


def mean_pos(fake, ids):
    pts = [(fake.units[u]["x"], fake.units[u]["y"]) for u in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def nudge(side, index=0, dx=2.0):      # TD-LAB-REV2-FIX-reengage-moved: was 1.0; a move counts only above DRAFT-reengage-moved-wu = 1 wu
    def fn(f):
        u = f.units_of(side)[index]
        f.set_pos(u, f.units[u]["x"] + dx, f.units[u]["y"])
    return fn


def wound(victim_side, index=0, hp=90.0):
    def fn(f):
        f.set_hp(f.units_of(victim_side)[index], hp)
    return fn


def kill(side, index=0):
    def fn(f):
        f.set_hp(f.units_of(side)[index], 0.0)
    return fn


def clear_dest(side):
    def fn(f):
        for u in f.units_of(side):
            f.set_dest(u, None)
    return fn


def give_dest(side):
    def fn(f):
        for u in f.units_of(side):
            f.set_dest(u, (0.0, 0.0))
    return fn


def reengages(fake, side, step_ticks=()):
    """The re-engage orders of `side`, without the orders its own attack_move STEPS issued (those are at `step_ticks`)."""
    return [o for o in fake.reengage_orders(side) if o[0] not in step_ticks]


def only(orders):
    assert len(orders) == 1, orders
    return orders[0]


# ---------------------------------------------------------------------------------------------------------- the number

def test_the_silence_window_is_the_draft_forty_ticks():
    """DRAFT-reengage-silence-ticks: Westley's number (the R-099-05 window, 2 s at 20 ticks per second); defined in contract.py."""
    assert hasattr(contract, "REENGAGE_SILENCE_TICKS"), "contract.REENGAGE_SILENCE_TICKS is not defined"
    assert isinstance(contract.REENGAGE_SILENCE_TICKS, int) and contract.REENGAGE_SILENCE_TICKS == 40


# ---------------------------------------------------------------------------------------------------------- the trigger

def test_a_silent_visible_idle_side_is_reengaged_once_at_the_window_both_sides():
    """Positive control of the whole mechanism: nobody fires or moves, everything visible, every unit idle -> each side gets ONE
    attack-move of all its units onto the enemy centroid, issued with N engine steps taken."""
    res, fake = run([G(0, 3), G(1, 2)], cap=N + 5)
    for side in (0, 1):
        tick, ids, goal = only(fake.reengage_orders(side))
        assert tick == N
        assert sorted(ids) == sorted(fake.units_of(side))
        assert goal == pytest.approx(mean_pos(fake, fake.units_of(1 - side)))
    assert tuple(res.reengage) == (1, 1)


def test_no_order_before_the_window():
    """Negative control: a fight that ends one tick short of the window has seen no re-engage."""
    res, fake = run([G(0), G(1)], cap=N - 1)
    assert fake.reengage_orders(0) == [] and fake.reengage_orders(1) == []
    assert tuple(res.reengage) == (0, 0)


def test_one_reengage_per_silence_period_then_again_after_activity():
    """Unbroken silence gives one re-engage, not one every window. After the side moves (its own unit) and goes quiet again, a new
    period counts from that move: side 0 moves at tick M, so its second order is at M + N; side 1 stays at its single one."""
    moved_at = N + 6           # the nudge runs in step number N + 6, so side 0 moves at tick N + 6
    res, fake = run([G(0), G(1)], cap=2 * N + 20, script_events={N + 5: [nudge(0)]})
    assert [t for t, _i, _g in fake.reengage_orders(0)] == [N, moved_at + N]
    assert [t for t, _i, _g in fake.reengage_orders(1)] == [N]
    assert tuple(res.reengage) == (2, 1)


def test_unbroken_silence_for_several_windows_is_still_one_event():
    """TD-LAB-REV2-FIX-reengage-orders: the fake's orders now take effect (arrive_after=2 by default); a no-op order is retried
    (decision 43 item 3, test_drift_fix_reengage.py), an order that works is not."""
    res, fake = run([G(0), G(1)], cap=3 * N + 5)
    assert len(fake.reengage_orders(0)) == 1 and len(fake.reengage_orders(1)) == 1
    assert tuple(res.reengage) == (1, 1)


@pytest.mark.parametrize("side", (0, 1))
def test_a_hit_dealt_after_a_reengage_rearms_the_shooter_like_a_move(side):
    """Decision 33 item 1 for fire, decision 49 as amended by decision 50 (condition (i)) (the side's own counter; FINDING-lab-d11): after its first
    re-engage at N, `side` deals a hit (an enemy unit loses hp in step N + 5, so at tick N + 6): its second order is at hit tick + N. The
    wounded side did not fire and stays at its single one (TD-LAB-REV2-L8M-moved: the L8M tip had both at hit tick + N and (2, 2))."""
    hit_at = N + 6
    res, fake = run([G(0), G(1)], cap=2 * N + 20, script_events={N + 5: [wound(1 - side)]})
    assert [t for t, _i, _g in fake.reengage_orders(side)] == [N, hit_at + N]
    assert [t for t, _i, _g in fake.reengage_orders(1 - side)] == [N]
    assert tuple(res.reengage)[side] == 2 and tuple(res.reengage)[1 - side] == 1


@pytest.mark.parametrize("side", (0, 1))
def test_a_move_by_a_side_restarts_only_that_sides_silence(side):
    """Positive control for the reset: the mover waits to M + N, the other side is unaffected and goes at N."""
    k = N - 5
    res, fake = run([G(0), G(1)], cap=2 * N + 5, script_events={k: [nudge(side)]})
    assert only(fake.reengage_orders(side))[0] == k + 1 + N
    assert only(fake.reengage_orders(1 - side))[0] == N
    assert tuple(res.reengage) == (1, 1)


@pytest.mark.parametrize("side", (0, 1))
def test_a_hit_dealt_restarts_the_shooters_silence_not_the_targets(side):
    """Decision 49 as amended by decision 50 (condition (i)) (the side's own counter; FINDING-lab-d11; TD-LAB-REV2-L8M-moved: the L8M tip delayed the
    target too). A side fires when an enemy unit loses hp. The wounded side did not fire: it re-engages at N; the shooter at hit tick + N."""
    k = N - 5
    res, fake = run([G(0), G(1)], cap=2 * N + 5, script_events={k: [wound(1 - side)]})
    assert only(fake.reengage_orders(side))[0] == k + 1 + N
    assert only(fake.reengage_orders(1 - side))[0] == N


def test_a_kill_is_a_hit_and_a_dead_unit_is_not_ordered():
    """Decision 49 as amended by decision 50 (condition (i)) (TD-LAB-REV2-L8M-moved: the L8M tip had side 0 at N + 1). The unit killed on the first
    step is side 0's: side 1 fired at tick 1 (re-engages at 1 + N), side 0 did nothing (at N) and its order lists only the survivor."""
    res, fake = run([G(0, 2), G(1, 2)], cap=N + 10, script_events={0: [kill(0, 0)]})
    dead, alive = fake.units_of(0)
    tick, ids, _goal = only(fake.reengage_orders(0))
    assert tick == N and list(ids) == [alive]
    assert only(fake.reengage_orders(1))[0] == N + 1


def test_a_side_that_sees_no_enemy_is_not_reengaged():
    """Negative: side 0 sees nobody (never re-engaged, count 0); positive control: side 1 sees everybody (re-engaged at N)."""
    res, fake = run([G(0), G(1)], cap=2 * N,
                    fake=ReengageFakeEngine(visible_fn=lambda f, side, e: side == 1))
    assert fake.reengage_orders(0) == []
    assert only(fake.reengage_orders(1))[0] == N
    assert tuple(res.reengage) == (0, 1)


def test_an_enemy_that_comes_into_sight_after_the_window_is_met_at_the_first_tick_it_is_seen():
    """The counter keeps counting while nothing is visible: side 0 first sees an enemy at tick V > N and is ordered at V."""
    v = N + 7
    res, fake = run([G(0), G(1)], cap=v + 10,
                    fake=ReengageFakeEngine(visible_fn=lambda f, side, e: side == 1 or f.step_count >= v))
    assert only(fake.reengage_orders(0))[0] == v
    assert only(fake.reengage_orders(1))[0] == N


def test_a_guard_holder_is_never_reengaged_and_keeps_its_post():
    """R-096-08: a guard holds. Side 0 guards (no order at all, count 0); side 1, attack-moving, is sent at the guards' centroid."""
    res, fake = run([G(0, 3, order="guard"), G(1, 2)], cap=3 * N)
    assert fake.reengage_orders(0) == []
    tick, ids, goal = only(fake.reengage_orders(1))
    assert tick == N and goal == pytest.approx(mean_pos(fake, fake.units_of(0)))
    assert tuple(res.reengage) == (0, 1)
    assert [o for o in fake.order_log if o[1] == "guard" and o[0] > 0] == []


def test_only_the_attack_move_group_of_a_mixed_side_is_ordered():
    """One side, two groups: a guard group and an attack-move group. The re-engage names the attack-move group's units only."""
    res, fake = run([G(0, 2, order="guard"), G(0, 2), G(1, 2)], cap=N + 5)
    guards, movers = fake.units_of(0)[:2], fake.units_of(0)[2:]
    tick, ids, _goal = only(fake.reengage_orders(0))
    assert tick == N and sorted(ids) == sorted(movers) and not set(ids) & set(guards)
    assert only(fake.reengage_orders(1))[0] == N


@pytest.mark.parametrize("opening,step,ordered", [
    ("attack_move", None, True),
    ("attack_move", "guard", False),
    ("attack_move", "idle", False),
    ("attack_move", "move", False),
    ("attack_move", "group_move", False),
    ("guard", "attack_move", True),
    ("idle", "attack_move", True),
    ("move", None, False),
    ("group_move", None, False),
    ("idle", None, False),
    ("guard", None, False),
    ("attack_move", "ping", True),
    ("attack_move", "set_layer", True),
    ("attack_move", "set_emission", True),
    ("guard", "ping", False),
])
def test_only_a_unit_whose_latest_order_is_attack_move_holds_the_role(opening, step, ordered):
    """The lab tracks each group's role from its opening order and its timeline steps. Side 1 (plain attack-move) is the control in
    every run and is always ordered at N; side 0's group is ordered exactly when its latest order is an attack-move. A ping, a
    set_layer and a set_emission are not orders of movement: they leave the role as it was (the attack-move holder is still
    ordered at N; the guard holder stays unordered)."""
    extra = dict(ping=dict(goal=(0.0, 0.0), layer=0), set_layer=dict(layer=1), set_emission=dict(on=True)).get(step, {})
    timeline = [] if step is None else [Step(group=0, when=("tick", 0), order=step, **extra)]
    res, fake = run([G(0, 2, order=opening), G(1, 2)], cap=N + 5, timeline=timeline)
    assert only(fake.reengage_orders(1))[0] == N
    got = fake.reengage_orders(0)
    if ordered:
        assert only(got)[0] == N and sorted(only(got)[1]) == sorted(fake.units_of(0))
    else:
        assert got == []
    assert res.reengage[0] == (1 if ordered else 0)


@pytest.mark.parametrize("opening,step,ordered", [
    ("attack_move", "guard", False),
    ("guard", "attack_move", True),
    ("attack_move", "idle", False),
    ("attack_move", "move", False),
    ("idle", "attack_move", True),
])
@pytest.mark.parametrize("when", [("tick", 10), ("seen",)])
def test_a_later_step_changes_the_role_too_by_tick_or_by_sight(opening, step, ordered, when):
    """Steps after tick 0 count: a Step at ("tick", 10) or ("seen",) (can_see on, so it fires at tick 1) takes the role away from
    an attack-move holder (guard, idle, move) or gives it to a guard or idle holder (attack_move), before the window N. The
    attack_move STEP's own order is not a re-engage (filtered by its tick); side 1 is the control, ordered at N."""
    k = when[1] if when[0] == "tick" else 1
    fake = ReengageFakeEngine(can_see_fn=lambda f, o, t: True)
    res, fake = run([G(0, 2, order=opening), G(1, 2)], cap=N + 5, fake=fake, timeline=[Step(group=0, when=when, order=step)])
    assert only(fake.reengage_orders(1))[0] == N
    got = reengages(fake, 0, step_ticks=(k,))
    if ordered:
        assert only(got)[0] == N and sorted(only(got)[1]) == sorted(fake.units_of(0))
    else:
        assert got == []
    assert res.reengage[0] == (1 if ordered else 0)


def test_a_unit_with_a_destination_is_not_idle_and_is_left_alone():
    """The unit that still has somewhere to go is not ordered; the stuck side is silent, so its idle unit is. All idle: the one
    destination holder alone -> the other two are ordered."""
    fake = ReengageFakeEngine()
    res, fake = run([G(0, 3), G(1, 2)], cap=N + 5, fake=fake, script_events={0: [lambda f: f.set_dest(f.units_of(0)[0], (0.0, 0.0))]})
    first, others = fake.units_of(0)[0], fake.units_of(0)[1:]
    tick, ids, _goal = only(fake.reengage_orders(0))
    assert tick == N and sorted(ids) == sorted(others) and first not in ids


def test_a_side_with_no_idle_unit_gets_no_order_and_no_count():
    res, fake = run([G(0, 2), G(1, 2)], cap=2 * N,
                    script_events={0: [lambda f: [f.set_dest(u, (0.0, 0.0)) for u in f.units_of(0)]]})
    assert fake.reengage_orders(0) == []
    assert only(fake.reengage_orders(1))[0] == N
    assert tuple(res.reengage) == (0, 1)


def test_an_idle_unit_that_appears_after_the_window_is_ordered_at_the_first_tick_it_is_idle():
    """Side 0 sees an enemy at N but every one of its units still has a destination; at tick V > N its destinations are cleared and
    it is ordered at V (the silence period was not used up by the tick that found nobody idle). Side 1 is idle throughout: N."""
    v = N + 9
    res, fake = run([G(0), G(1)], cap=v + 10, script_events={0: [give_dest(0)], v - 1: [clear_dest(0)]})
    assert only(fake.reengage_orders(0))[0] == v
    assert only(fake.reengage_orders(1))[0] == N
    assert tuple(res.reengage) == (1, 1)


def test_the_goal_is_the_centroid_of_the_living_visible_enemies_where_they_stand_when_the_order_is_issued():
    """Side 1 has three units, all visible to side 0 here. At step 4 one is killed (a hit by side 0) and another walks 200 wu (a move
    by side 1): both sides' silence restarts at tick 4, so both orders come at 4 + N. Side 0's goal is the mean of the two living
    side-1 units at their new places, not of three, not of where they started. (What fog takes out of the set: the next test.)"""
    start = None

    def snapshot(f):
        nonlocal start
        start = mean_pos(f, f.units_of(1))

    events = {0: [snapshot], 3: [kill(1, 0), nudge(1, 1, dx=200.0)]}
    res, fake = run([G(0, 2), G(1, 3)], cap=N + 10, script_events=events)
    dead, walked, stayed = fake.units_of(1)
    want = mean_pos(fake, [walked, stayed])
    tick, _ids, goal = only(fake.reengage_orders(0))
    assert tick == 4 + N
    assert goal == pytest.approx(want)
    assert goal != pytest.approx(mean_pos(fake, fake.units_of(1))) and goal != pytest.approx(start)
    tick1, _ids1, goal1 = only(fake.reengage_orders(1))
    assert tick1 == 4 + N and goal1 == pytest.approx(mean_pos(fake, fake.units_of(0)))


def test_the_centroid_is_taken_over_the_enemies_the_ordering_side_can_see_never_all_the_living():
    """Decision 33 item 4. Side 1 has three units; side 0 sees only two of them (the third stands behind the fog). Side 0's goal is
    the mean of the two it sees; the mean of all three living (which would leak what side 0 cannot see) must not be the goal.
    Side 1 sees all of side 0 and gets the plain mean of side 0 (control: the visible set equals the living set)."""
    hidden = {}

    def visible(f, side, e):
        hidden.setdefault("u", f.units_of(1)[2])
        return not (side == 0 and e == hidden["u"])

    res, fake = run([G(0, 2), G(1, 3)], cap=N + 5, fake=ReengageFakeEngine(visible_fn=visible))
    seen, fogged = fake.units_of(1)[:2], fake.units_of(1)[2]
    tick, _ids, goal = only(fake.reengage_orders(0))
    assert tick == N and goal == pytest.approx(mean_pos(fake, seen))
    assert goal != pytest.approx(mean_pos(fake, fake.units_of(1))) and fogged not in seen
    assert only(fake.reengage_orders(1))[2] == pytest.approx(mean_pos(fake, fake.units_of(0)))


def test_the_enemy_centroid_is_taken_on_a_raised_enemy_layer_too():
    """Decision 33 item 3: the order is an (x, y) and each unit keeps its own layer; an enemy side standing on layer 2 still gets its
    plain mean over all its visible units on every layer (the order carries no layer, and no layer filters the set)."""
    raised = dataclasses.replace(G(1, 3), layer=2)
    res, fake = run([G(0, 2), raised], cap=N + 5)
    assert only(fake.reengage_orders(0))[2] == pytest.approx(mean_pos(fake, fake.units_of(1)))


# ---------------------------------------------------------------------------------------------------------- counts, caps, no-op runs

@pytest.mark.parametrize("per_unit", (True, False))
def test_the_reengage_is_one_event_whatever_orders_per_unit_says_and_however_spread_the_units_are(per_unit):
    """Decision 33 item 2 as amended by decision 43 item 2 (TD-LAB-REV2-FIX-reengage-orders; was ..._is_one_call_...): one EVENT per
    trigger whatever orders_per_unit says and however far apart the units stand (units further apart than 450 wu from their centroid
    would be split in chunks by fight._chunks). Side 0 is four units 600 wu apart; the event lists all four and the count is 1. The
    calls inside the event are one per unit (test_drift_fix_reengage.py)."""
    wide = dataclasses.replace(G(0, 4), params={"spacing": 600.0})
    res, fake = run([wide, G(1, 2)], cap=N + 5, orders_per_unit=per_unit)
    tick, ids, _goal = only(fake.reengage_orders(0))
    assert tick == N and sorted(ids) == sorted(fake.units_of(0)) and len(ids) == 4
    assert res.reengage[0] == 1 and only(fake.reengage_orders(1))[0] == N


def test_the_count_follows_the_side_not_the_spawn_order():
    """swap=True spawns side 1 first; reengage[0] is still side 0's (side 0 sees nobody, side 1 sees all)."""
    for swap in (False, True):
        res, _ = run([G(0), G(1)], cap=2 * N, swap=swap,
                     fake=ReengageFakeEngine(visible_fn=lambda f, side, e: side == 1))
        assert tuple(res.reengage) == (0, 1), swap


def test_a_cap_after_a_reengage_stays_a_cap():
    """Decision 23 and 28: elimination is the only end. Nothing dies here, so the fight runs to the cap and says so."""
    res, fake = run([G(0), G(1)], cap=2 * N)
    assert res.outcome == "cap" and res.ticks == 2 * N and res.winner is None
    assert sum(res.reengage) > 0


def test_a_fight_that_never_triggers_issues_no_order_after_the_opening_and_counts_zero():
    """Detector control: sight off for both sides, long silence -> no order after tick 0, reengage (0, 0)."""
    fake = ReengageFakeEngine(visible_fn=lambda f, side, e: False)
    res, fake = run([G(0), G(1)], cap=3 * N, fake=fake)
    assert [o for o in fake.order_log if o[0] > 0] == []
    assert tuple(res.reengage) == (0, 0)


def test_an_older_fake_engine_without_sight_runs_and_counts_zero():
    """The base FakeEngine answers visible_enemies with an empty set: every pre-L8 fake fight is unchanged."""
    setup = Setup(groups=(G(0), G(1)), unit_types={}, abilities=False, max_ticks=3 * N, sample_every=5)
    res = fight(setup, 0, False, engine=FakeEngine())
    assert tuple(res.reengage) == (0, 0) and res.outcome == "cap"


def test_the_whole_result_is_deterministic():
    a, _ = run([G(0, 3), G(1, 2)], cap=2 * N + 7, script_events={N + 5: [nudge(0)]})
    b, _ = run([G(0, 3), G(1, 2)], cap=2 * N + 7, script_events={N + 5: [nudge(0)]})
    assert a == b and tuple(a.reengage) == (2, 1)


# ---------------------------------------------------------------------------------------------------------- the scenes of the lab

def _feats():
    return maps.Features(choke_count=1, choke_width_wu=4 * maps.LAYOUT_BODY_WU, choke_width_bodies=4.0, lane_count=1,
                         blocked_layer_ranges=(), fight_layer_blocked=False, cover_density_corridor=0.1, start_distance=1400.0,
                         detour_ratio=0.0, blocked_layer_top=4)


def test_the_naive_attacker_is_reengaged_and_the_naive_guard_defender_is_not():
    """Ruling 2: naive baselines get the order. The naive scene is a side-0 attack-moving blob against a side-1 guard blob: side 0
    is sent onto the guards' centroid at N, the guards keep their post."""
    f = _feats()
    layout = maps.layout_map(f, 7)
    setup = scenes.placed_scene(layout, "naive", f.start_distance, f)(16, False)
    setup = dataclasses.replace(setup, max_ticks=N + 5)
    fake = ReengageFakeEngine()
    res = fight(setup, 0, False, engine=fake)
    tick, ids, goal = only(fake.reengage_orders(0))
    assert tick == N and sorted(ids) == sorted(fake.units_of(0))
    assert goal == pytest.approx(mean_pos(fake, fake.units_of(1)))
    assert fake.reengage_orders(1) == []
    assert tuple(res.reengage) == (1, 0)


def test_a_meeting_scene_re_aims_both_sides_at_each_others_centroid_not_at_the_shared_point():
    """The objective (meeting) scene sends both sides to one point; the re-engage replaces that goal with the enemy centroid."""
    setup = dataclasses.replace(scenes.objective_scene(2800.0)(16, False), max_ticks=N + 5)
    fake = ReengageFakeEngine()
    res = fight(setup, 0, False, engine=fake)
    for side in (0, 1):
        tick, ids, goal = only(fake.reengage_orders(side))
        assert tick == N and sorted(ids) == sorted(fake.units_of(side))
        assert goal == pytest.approx(mean_pos(fake, fake.units_of(1 - side)))
        assert goal != pytest.approx(tuple(setup.point))
    assert tuple(res.reengage) == (1, 1)
