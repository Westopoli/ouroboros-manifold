# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 28 point 3 (the attack-move idle cap, the lab's re-engage order); E-13 R-096-02, R-096-08, R-099-05
"""LAB-REV2-L8: fight() re-engages a silent side. Fake-engine tests of the trigger (tests only; the builder writes scripts/skilllab).

THE RULE (Architect decision 28 point 3). When a side has had NO unit fire or move for REENGAGE_SILENCE_TICKS while an enemy is
visible to it, every idle unit of that side holding an attack-move role is attack-moved onto the enemy centroid; a guard-stance
holder never gets it (R-096-08). Both sides, naive baselines included. A cap after a re-engage stays a defect (outcome "cap").

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
      fire by side s at tick t   some enemy-of-s unit's hp read by the loop (engine.unit_hp) is lower at tick t than at tick t-1
                                  (the loop already reads it every tick)
      move by side s at tick t   some living unit of s reads engine.unit_pos(w, u) different from the previous tick's reading
                                  (tick 0 is the spawn reading; compared with plain inequality)
      silent tick                a tick t >= 1 on which side s had neither
      idle unit                  a living unit with engine.unit_destination(w, u) is None
      visible enemy              engine.visible_enemies(w, s, living_enemy_ids) is non-empty (the side's sight, om_player_can_see);
                                  read only when a re-engage could fire
      attack-move role           a lab-side record per unit: set by the opening Group.order == "attack_move" and by a timeline
                                  Step "attack_move"; cleared by "move", "group_move", "idle", "guard" (opening or Step). Ping,
                                  set_layer and set_emission leave it alone. A re-engage keeps the role.

    TRIGGER: side s keeps a counter of consecutive silent ticks (a fire or a move of s zeroes it). When it has reached
      REENGAGE_SILENCE_TICKS, a visible enemy exists and at least one living idle attack-move unit exists, the side re-engages at
      once (the order is issued in the loop iteration after engine.step number N, so a fake engine's step_count reads N for the first
      one): ONE engine.order_attack_move(w, ids, x, y) call, ids = every such unit, (x, y) = the mean of engine.unit_pos over the
      side's living enemy units at that moment. reengage[s] += 1 (events, not units). The side then waits for activity: no further
      re-engage for that side until a fire or a move of that side has zeroed the counter and it has again counted
      REENGAGE_SILENCE_TICKS silent ticks ("once per silence period"). If no enemy is visible, or no unit is idle, the counter keeps
      counting and the re-engage fires on the first tick all three conditions hold.
    The fight ends only as today (elimination, or the cap): a re-engage never ends a fight or hides a cap.
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


def run(groups, cap, fake=None, timeline=(), swap=False, script_events=None):
    """fight() on a ReengageFakeEngine; script_events {k: callable(fake)} runs inside step number k+1 (k steps already taken)."""
    if fake is None:
        fake = ReengageFakeEngine()
    if script_events:
        fake.script = lambda t, f: [fn(f) for fn in script_events.get(t, [])]
    setup = Setup(groups=tuple(groups), unit_types={}, abilities=False, max_ticks=cap, sample_every=5, timeline=tuple(timeline))
    return fight(setup, 0, swap, engine=fake), fake


def mean_pos(fake, ids):
    pts = [(fake.units[u]["x"], fake.units[u]["y"]) for u in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def nudge(side, index=0, dx=1.0):
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
    res, fake = run([G(0), G(1)], cap=3 * N + 5)
    assert len(fake.reengage_orders(0)) == 1 and len(fake.reengage_orders(1)) == 1
    assert tuple(res.reengage) == (1, 1)


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
    """A side fires when an enemy unit loses hp. The wounded side did not fire: it re-engages at N; the shooter at hit tick + N."""
    k = N - 5
    res, fake = run([G(0), G(1)], cap=2 * N + 5, script_events={k: [wound(1 - side)]})
    assert only(fake.reengage_orders(side))[0] == k + 1 + N
    assert only(fake.reengage_orders(1 - side))[0] == N


def test_a_kill_is_a_hit_and_a_dead_unit_is_not_ordered():
    """The unit killed on the first step is side 0's: side 1 fired at tick 1 (re-engages at 1 + N), side 0 did nothing (at N) and
    its order lists only the survivor."""
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
])
def test_only_a_unit_whose_latest_order_is_attack_move_holds_the_role(opening, step, ordered):
    """The lab tracks each group's role from its opening order and its timeline steps. Side 1 (plain attack-move) is the control in
    every run and is always ordered at N; side 0's group is ordered exactly when its latest order is an attack-move."""
    timeline = [] if step is None else [Step(group=0, when=("tick", 0), order=step)]
    res, fake = run([G(0, 2, order=opening), G(1, 2)], cap=N + 5, timeline=timeline)
    assert only(fake.reengage_orders(1))[0] == N
    got = fake.reengage_orders(0)
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


def test_the_goal_is_the_centroid_of_the_living_enemies_where_they_stand_when_the_order_is_issued():
    """Side 1 has three units. At step 4 one is killed (a hit by side 0) and another walks 200 wu (a move by side 1): both sides'
    silence restarts at tick 4, so both orders come at 4 + N. Side 0's goal is the mean of the two living side-1 units at their new
    places, not of three, not of where they started."""
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


def test_the_enemy_centroid_is_taken_on_a_raised_enemy_layer_too():
    """Decision 2's point is an (x, y); an enemy side standing on layer 2 still gets its plain mean (the order carries no layer)."""
    raised = dataclasses.replace(G(1, 3), layer=2)
    res, fake = run([G(0, 2), raised], cap=N + 5)
    assert only(fake.reengage_orders(0))[2] == pytest.approx(mean_pos(fake, fake.units_of(1)))


# ---------------------------------------------------------------------------------------------------------- counts, caps, no-op runs

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
