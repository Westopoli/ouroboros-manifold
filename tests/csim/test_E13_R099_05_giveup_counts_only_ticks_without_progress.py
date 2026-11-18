# Rule pins: R-099-05, R-099-04, R-001-06
"""E-13 R-099-05, Round 6 piece E2 (docs/northstar/plans/engine-rules-2026-11-08/round6.md, DEC-giveup-progress-2026-11-18): the give-up counts only ticks without progress.

Rule words (docs/bible/epics/E-13-movement-and-command.md):
  R-099-05  "... When it has been within 75 wu (about two slot spacings) of its slot for 40 consecutive ticks (2 s) without arriving, Then it ends its order where it stands ... the count resets when the unit leaves the
            75 wu disc or arrives ... Only a tick on which the unit came no nearer its slot is counted: a tick that brings it nearer by more than 0.1 wu is not counted and does not reset the count, so a slow unit that is
            still walking in is never stopped short (DEC-giveup-progress-2026-11-18: counting every tick inside the disc ends the order of any unit slower than 1.875 wu a tick on a clear path, a Bastion climbing a slope
            about 2 wu short of its point and a Fortified one about 43 wu short; not built). A unit that is held makes no such tick and still ends on the 40th. A unit moving or attack-moving alone ... gives up the same
            way, by the same two numbers measured to its ordered point."
  R-099-04  "A unit ordered alone has no arrival radius: with a clear path it walks to its point itself (tests hold a lone walker to within 1 wu of its route's end and a guard to within 5 wu of its post)", and a unit
            under a group move arrives within 1.5 x its collision radius of its slot.

How the count is read (the rule's two numbers, the convention of tests/csim/test_PP_unit_giveup.py and tests/csim/test_E13_R099_05_lone_walker_arrives_and_gives_up.py): the pass runs at the top of a tick on the
positions the last tick ended with, so a tick is "near" when the position REPORTED BY THE PREVIOUS TICK is within 75 wu of the point; the tick is "progress" when that position is nearer the point than the one before
it (reported two ticks back) by more than 0.1 wu (COLLISION_SETTLE_EPS). `ProgressCount` below keeps that count; a tick that is near and not progress adds one, a progress tick adds none and does not reset, leaving the
disc resets. The unit's order must still be active after the tick that makes the count 39 and ended after the tick that makes it 40. A unit that stands still from tick 1 inside the disc makes no progress on tick 1
either (its first counted tick is tick 1; a build that read a stale "before the step" position there would count from tick 2, and the controls below catch it).

Slow unit staged: a custom walking type (id 210, line category, speed 20 wu/s = 1.0 wu a tick, measured: 0.949 wu in x and 0.316 in y a tick, 1.000 along its heading), slower than 1.875 wu a tick. Fortified
Bastion (0.8 wu a tick) cannot be staged by a lone order: a Bastion that is ordered to move cancels its fortify (csrc/unit.c, om_ability_cancel_fortify on an order), so the custom type stands for it; the slope test
(tests/csim/test_E01_R004_07_slope_time.py) is the Bastion case and is judged after the rebuild.

Configuration: the shipped one for a csim scene: walking units, steering and route-around-terrain on (their defaults), targeting by sight on (the default), a 2000 x 2000 canvas.

Detector bounds (not rules; Westley's to change): CLEAR_PATH_WU 5 (DRAFT-clear-path-wu, as the other file: where a lone walker's order may end), PROGRESS_EPS 0.1 (COLLISION_SETTLE_EPS, the rule's own),
RUN_TICKS 1500 (a run limit; the slow walk takes 300 to 450 ticks), POS_TOL 1e-6 (a rested unit pushed by a hair), HELD_TOL 0.05 (the most a held unit may drift in a tick, premise of the held scenes).
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, dest, pos, spawn, step, target

WALKING = 1
CANVAS = 2000.0
SLOW = 210                          # custom type: walking, 1.0 wu a tick
SLOW_SPEED_WU_S = 20.0
SLOW_PACE = 1.0                     # wu a tick; the rule's threshold is 1.875
GIVE_UP_RADIUS = 75.0
GIVE_UP_TICKS = 40
ARRIVE_SLOT = 22.5                  # 1.5 x radius 15: a slot's arrival radius (R-099-04)
CLEAR_PATH_WU = 5.0                 # DRAFT-clear-path-wu
PROGRESS_EPS = 0.1                  # COLLISION_SETTLE_EPS
RUN_TICKS = 1500
POS_TOL = 1.0e-6
HELD_TOL = 0.05
BIG_HP = 1.0e6


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class ProgressCount:
    """The count of R-099-05 as the rule words it: a tick is counted when the position reported by the previous tick is within 75 wu of the point and did not come nearer it, by more than 0.1 wu, than the
    position reported before that. `start` is the unit's position when the order was given (tick 1's two positions)."""

    def __init__(self, point, start):
        self.point = point
        self.near = 0
        self.prev = _dist(start, point)
        self.prev2 = self.prev

    def tick(self, p):
        """Call after each step with the position that step reported; returns the count after the tick."""
        if self.prev > GIVE_UP_RADIUS:
            self.near = 0
        elif self.prev2 - self.prev <= PROGRESS_EPS:
            self.near += 1
        self.prev2, self.prev = self.prev, _dist(p, self.point)
        return self.near

    def teleported(self, p):
        """The unit was put at `p` between ticks (a direct position change): the next tick reads it as the position the last tick ended with; the one before it stays."""
        self.prev = _dist(p, self.point)


def _world(lib, wf, kinds=(RAIDER, VANGUARD, SLOW)):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_roster_register_custom_unit(w, SLOW, 1, b"slow_walker", 500.0, 5.0, 1.0, 100.0, SLOW_SPEED_WU_S, 100.0, 1.0, 0.0, 0) == 0
    for k in kinds:
        assert lib.om_roster_set_movement_kind(w, k, WALKING) == 0
    return w


def _move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def _group_move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_group_move(w, arr, len(ids), float(x), float(y))


def _supply(lib, w, faction, x, y):
    s = spawn(lib, w, SUPPLY, faction, x, y)
    lib.om_unit_set_hp(w, s, BIG_HP)
    return s


def _friend(lib, w, xy):
    """FRIEND: an own Vanguard at `xy` that holds a target and fires (an enemy Supply 250 wu east of it, 1e6 hp, which never fires): engaged, so not idle (R-097-10), and it never moves."""
    e = spawn(lib, w, VANGUARD, 0, *xy)
    s = _supply(lib, w, 1, xy[0] + 250.0, xy[1])
    return e, s


def _none(t):
    return t is None or t <= 0


# ------------------------------------------------------------------ a unit still coming nearer is not stopped short

def test_R_099_05_a_slow_unit_ordered_alone_on_a_clear_path_keeps_its_destination_while_it_comes_nearer_and_reaches_its_point(lib, world_factory):
    """R-099-05 'a tick that brings it nearer by more than 0.1 wu is not counted ... a slow unit that is still walking in is never stopped short' with R-099-04 'with a clear path it walks to its point itself': a slow
    walking unit (1.0 wu a tick) ordered alone (a plain move) from (300,500) to (600,500), nothing in its way. On every tick on which it came nearer its point by more than 0.1 wu it still has its destination
    (it is walking in; the count of a rule that skips progress ticks stays at zero), whatever its distance (the 75 wu disc is entered with about 300 ticks to spare); the order ends only within 5 wu of the point
    (CLEAR_PATH_WU), and from then on the unit does not move. Red today: the count takes every tick inside the disc, so the order ends on the 40th, about 36 wu from the point, with the unit still coming nearer."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, SLOW, 0, 300.0, 500.0)
    point = (600.0, 500.0)
    assert _move(lib, w, [m], *point) == 0
    cleared_at, trace, d_prev, gain = None, [], _dist((300.0, 500.0), point), 0.0   # d_prev: the distance after the tick before; gain: how much nearer that tick brought it
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append(p)
        d = _dist(p, point)
        if cleared_at is None and not has:
            cleared_at = t
            assert d <= CLEAR_PATH_WU, "tick %d: the order ended %.1f wu from the point with the unit still walking in (it came %.2f wu nearer on the tick before; R-099-05 counts only ticks without progress)" % (
                t, d, gain)
        if cleared_at is not None:
            assert not has and _dist(p, trace[cleared_at - 1]) < POS_TOL, "tick %d: the unit moved or took a destination after its order ended on tick %d" % (t, cleared_at)
            if t >= cleared_at + 20:
                break
        gain, d_prev = d_prev - d, d
    assert cleared_at is not None, "the slow unit never reached its point in %d ticks: at %s" % (RUN_TICKS, trace[-1])
    assert cleared_at > 150, "premise: the slow unit's walk was only %d ticks (it should take about 300)" % cleared_at
    _slow_pace_premise_trace(trace)


def _slow_pace_premise_trace(trace):
    """Premise read from the walk: its steps are 0.5 to 1.875 wu on the first ticks."""
    steps = [_dist(trace[k], trace[k - 1]) for k in range(1, 20)]
    assert all(0.5 < s < 1.875 for s in steps), "premise: the unit's pace on its first ticks is %s (wanted about 1.0, under 1.875 wu a tick)" % ([round(s, 3) for s in steps],)


def test_R_099_05_a_slow_member_of_a_group_walks_to_its_slot_and_reaches_its_arrival_radius(lib, world_factory):
    """R-099-05 (the same clause for a group member, 'measured to its slot') with R-099-04 (a unit under a group move arrives within 1.5 x radius = 22.5 wu of its slot): two slow walking units at (200,500) and
    (200,540) are given a group move to (600,500). Each walks to its slot at 1.0 wu a tick, nothing in its way. On every tick it still has its destination while farther than 22.5 wu from its slot; the order of
    each ends only inside 22.5 wu of the slot (the arrival), and each is stationary from then on. Red today: both end on the 40th tick inside the 75 wu disc, 35 wu short of their slots (measured)."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, SLOW, 0, 200.0, 500.0)
    b = spawn(lib, w, SLOW, 0, 200.0, 540.0)
    _group_move(lib, w, [a, b], 600.0, 500.0)
    slots = {u: dest(lib, w, u)[1:] for u in (a, b)}
    assert all(dest(lib, w, u)[0] == 1 for u in (a, b)), "premise: a member has no destination after the group order"
    cleared = {}
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        for u in (a, b):
            p, has = pos(lib, w, u), dest(lib, w, u)[0] == 1
            d = _dist(p, slots[u])
            if u not in cleared and not has:
                cleared[u] = (t, p)
                assert d <= ARRIVE_SLOT + 1.0e-6, "tick %d: member %d's order ended %.1f wu from its slot %s, outside its arrival radius %.1f wu, with the member still walking in (R-099-05 counts only ticks without progress)" % (
                    t, u, d, slots[u], ARRIVE_SLOT)
            if u in cleared:
                assert not has and _dist(p, cleared[u][1]) < POS_TOL, "tick %d: member %d moved or took a destination after its order ended on tick %d" % (t, u, cleared[u][0])
        if len(cleared) == 2 and t >= max(c[0] for c in cleared.values()) + 20:
            break
    assert len(cleared) == 2, "a member never reached its slot in %d ticks (cleared: %s)" % (RUN_TICKS, sorted(cleared))


# ------------------------------------------------------------------ a held unit still ends on the 40th tick (controls, green today)

def _run_held(lib, w, u, point, c, what):
    """Steps until the unit's order ends, asserting per tick: the order is active after the tick that makes the count 39 and ended after the one that makes it 40 (never before: not the give-up boundary);
    the unit holds no target. From the give-up the unit has no destination
    and does not move for 20 ticks. Returns the tick of the give-up."""
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p, has = pos(lib, w, u), dest(lib, w, u)[0] == 1
        near = c.tick(p)
        assert _none(target(lib, w, u)), "%s: tick %d: the unit holds a target %s (scene broken)" % (what, t, target(lib, w, u))
        if near == GIVE_UP_TICKS - 1:
            assert has, "%s: tick %d: the order ended with a count of %d (before the 40th counted tick)" % (what, t, near)
        if near == GIVE_UP_TICKS:
            assert not has, "%s: tick %d: the unit still has its destination after %d counted ticks inside 75 wu of its point, %.1f wu away (R-099-05)" % (what, t, near, _dist(p, point))
            end_pos, ended = p, t
            break
        if not has:
            pytest.fail("%s: tick %d: the order ended with a count of only %d (%.1f wu from the point): not the give-up boundary" % (what, t, near, _dist(p, point)))
    else:
        pytest.fail("%s: the count never reached 40 in %d ticks (at %s)" % (what, RUN_TICKS, pos(lib, w, u)))
    for k in range(1, 21):
        step(lib, w)
        assert dest(lib, w, u)[0] == 0, "%s: tick %d (give-up on %d): the destination is set again" % (what, ended + k, ended)
        assert _dist(pos(lib, w, u), end_pos) < POS_TOL, "%s: tick %d (give-up on %d): the unit moved after ending its order" % (what, ended + k, ended)
    return ended


HELD_POINT = (600.0, 500.0)
HELD_REST = (582.0, 500.0)          # 30 wu from FRIEND at (612,500): where a walker rests against it (measured by the other file), 18 wu from the point


def _held_scene(lib, wf):
    """A Vanguard ordered alone to (600,500), standing where it would rest against FRIEND (612,500): 18 wu from its point, pressed against the friend, so that no tick brings it nearer. Returns (w, m, friend)."""
    w = _world(lib, wf)
    m = spawn(lib, w, VANGUARD, 0, *HELD_REST)
    e, s = _friend(lib, w, (612.0, 500.0))
    assert _move(lib, w, [m], *HELD_POINT) == 0
    return w, m, e


def test_R_099_05_control_a_held_walker_ordered_alone_still_ends_its_order_on_the_40th_tick_not_the_39th(lib, world_factory):
    """R-099-05 'A unit that is held makes no such tick and still ends on the 40th': a Vanguard ordered alone stands pressed against an own Vanguard that holds a target (FRIEND), 18 wu from its point, inside the
    75 wu disc from tick 1 and not coming nearer on any tick (premise: it never gets 0.1 wu nearer). Its destination is still set after the tick that makes the count 39 (tick 39) and cleared after tick 40;
    it then has no destination and does not move (20 ticks); the friend never moves. Green today (every tick is counted) and must stay green: the progress clause must not delay a held unit."""
    w, m, e = _held_scene(lib, world_factory)
    c = ProgressCount(HELD_POINT, HELD_REST)
    ended = _run_held(lib, w, m, HELD_POINT, c, "held 18 wu from its point by a friend")
    assert ended == GIVE_UP_TICKS, "the held walker's order ended on tick %d, not on the 40th (it comes no nearer on any tick)" % ended
    assert _dist(pos(lib, w, m), HELD_REST) < HELD_TOL, "premise: the walker did not stay where it was put: at %s" % (pos(lib, w, m),)
    assert pos(lib, w, e) == (612.0, 500.0), "premise: the friend stepped aside"


def test_R_099_05_control_a_held_group_member_still_ends_its_order_on_the_40th_tick_not_the_39th(lib, world_factory):
    """R-099-05 'A unit that is held makes no such tick and still ends on the 40th', the group member: two Raiders at (200,500) and (200,540) are given a group move to (1200,500); an enemy Supply (1e6 hp) is
    put on the first member's slot (an own idle unit would step aside for a walker, R-097-10), and the member is put 30 wu west of its slot (a direct position change, its order stays): pressed against the
    Supply, inside the 75 wu disc, 30 wu from the slot (outside the 22.5 wu arrival radius), coming no nearer on any tick. Its destination is still set after tick 39 and cleared after tick 40; it then does not move
    (20 ticks). Green today and must stay green."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, RAIDER, 0, 200.0, 500.0)
    b = spawn(lib, w, RAIDER, 0, 200.0, 540.0)
    _group_move(lib, w, [a, b], 1200.0, 500.0)
    _, sx, sy = dest(lib, w, a)
    _supply(lib, w, 1, sx, sy)
    put = (sx - 30.0, sy)
    lib.om_unit_teleport(w, a, put[0], put[1], 0)
    assert dest(lib, w, a)[0] == 1, "scene broken: the put-back took the member's destination"
    c = ProgressCount((sx, sy), put)
    ended = _run_held(lib, w, a, (sx, sy), c, "group member held 30 wu from its slot by a Supply")
    assert ended == GIVE_UP_TICKS, "the held member's order ended on tick %d, not on the 40th (it comes no nearer on any tick)" % ended
    assert _dist(pos(lib, w, a), (sx, sy)) > ARRIVE_SLOT, "scene broken: an arrival (%.1f wu from the slot), not a give-up" % _dist(pos(lib, w, a), (sx, sy))


# ------------------------------------------------------------------ progress ticks are not counted and do not reset

def test_R_099_05_ticks_that_come_nearer_inside_the_disc_are_not_counted_and_do_not_reset_the_count(lib, world_factory):
    """R-099-05 'a tick that brings it nearer by more than 0.1 wu is not counted and does not reset the count': the held scene above (a Vanguard pressed against FRIEND, 18 wu from its point, held from tick 1);
    after tick 15 (a count of 15) the Vanguard is put 30 wu back, at (552,500), 48 wu from the point and still inside the 75 wu disc (a direct position change; its order stays). It walks back toward the point
    and rests against the friend again: about 8 ticks on each of which it comes nearer by 4 wu or less (premise: at least 5 such ticks, none of them leaving the disc). Those ticks are not counted and the count is not reset by them: the order is
    still active after the tick on which the count (the held ticks only) is 39 and ended after the one on which it is 40, which is tick 40 plus the number of progress ticks. A count that takes in the walking-in
    ends it on tick 40 (red today); a count that is reset by it ends it on tick 15 + the walk + 40, 8 or more ticks later than the held ticks give."""
    w, m, e = _held_scene(lib, world_factory)
    c = ProgressCount(HELD_POINT, HELD_REST)
    back = (552.0, 500.0)
    seen = {"progress": 0, "prev": _dist(HELD_REST, HELD_POINT), "left": False}

    near_hist = []
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        d = _dist(p, HELD_POINT)
        if t > 15:
            if seen["prev"] - d > PROGRESS_EPS:
                seen["progress"] += 1
            seen["left"] = seen["left"] or d > GIVE_UP_RADIUS
        seen["prev"] = d
        near = c.tick(p)
        near_hist.append(near)
        assert _none(target(lib, w, m)), "tick %d: the unit holds a target (scene broken)" % t
        if near == GIVE_UP_TICKS - 1:
            assert has, "tick %d: the order ended with a count of %d" % (t, near)
        if near == GIVE_UP_TICKS:
            assert not has, "tick %d: the order is still active after %d counted ticks (held ticks only; %d progress ticks after the put-back, 15 held ticks before it); a count that takes in the ticks of the walk-in ended it earlier, one that is reset by them ends it later: the count was %s" % (
                t, near, seen["progress"], near_hist)
            ended = t
            break
        if not has:
            pytest.fail("tick %d: the order ended with a count of only %d held ticks (%d progress ticks so far, which the rule does not count): a count that takes in the walk-in" % (t, near, seen["progress"]))
        if t == 15:
            lib.om_unit_teleport(w, m, back[0], back[1], 0)
            c.teleported(back)
            seen["prev"] = _dist(back, HELD_POINT)
            assert dest(lib, w, m)[0] == 1, "scene broken: the put-back took the destination"
    else:
        pytest.fail("the count never reached 40 in %d ticks" % RUN_TICKS)
    assert seen["progress"] >= 5, "premise: the put-back unit came nearer on only %d ticks (it should walk 30 wu back at 4 wu a tick)" % seen["progress"]
    assert not seen["left"], "premise: the unit left the 75 wu disc"
    assert ended >= GIVE_UP_TICKS + seen["progress"] - 1, "the order ended on tick %d, before the held ticks total 40 (40 + the %d ticks of walking in, give or take the tick of the put-back)" % (ended, seen["progress"])


# ------------------------------------------------------------------ for the tests of other files that hold a lone mover at a unit

def check_destination_by_count(has, positions, point, start, what):
    """Per tick, the rule's count applied to a recorded run (used by the R-097-10 files, which hold a lone mover at a unit): `has[k]` is whether the unit has a destination after tick k+1, `positions[k]` its position
    then, `start` where it stood when ordered. The destination is kept on every tick on which the count (ProgressCount: ticks inside the 75 wu disc on which the unit came no nearer by more than 0.1 wu) is under 40
    (so through the 39th), cleared on the tick that makes it 40, and from then on the unit has none and stands exactly where it stood on that tick. The run must be long enough to contain the give-up. Returns its tick."""
    c = ProgressCount(point, start)
    ended = None
    for k, (h, p) in enumerate(zip(has, positions)):
        t = k + 1
        if ended is not None:
            assert not h, "%s: tick %d: the destination is set again after the give-up on tick %d" % (what, t, ended[0])
            assert _dist(p, ended[1]) < POS_TOL, "%s: tick %d: the unit moved after its order ended on tick %d" % (what, t, ended[0])
            continue
        near = c.tick(p)
        if near < GIVE_UP_TICKS:
            assert h, "%s: tick %d: the order ended with a count of %d held ticks inside the 75 wu disc (R-099-05: the 39th still keeps it; a tick that came nearer is not counted); the unit is %.1f wu from its point" % (what, t, near, _dist(p, point))
        else:
            assert not h, "%s: tick %d: the unit still has its destination after %d held ticks inside the 75 wu disc, %.1f wu from its point (R-099-05, the 40th ends it)" % (what, t, near, _dist(p, point))
            ended = (t, p)
    assert ended is not None, "%s: the run of %d ticks holds fewer than 40 counted ticks, or the order never ended (count %d)" % (what, len(has), c.near)
    return ended[0]
