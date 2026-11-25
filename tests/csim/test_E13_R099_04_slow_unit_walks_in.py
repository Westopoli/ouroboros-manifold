# Rule pins: R-099-04
"""E-13 R-099-04, DEC-movement-sidestep-2026-11-24: a slow unit that is still coming nearer its point is never stopped short; it keeps its destination until it arrives.

Rule words (docs/bible/epics/E-13-movement-and-command.md):
  R-099-04  "Given a unit within its arrival radius of its destination (1.5 x collision radius for a formation slot, 2 x for a route waypoint), When the tick runs, Then it has arrived where it stands".
  (This file began as R-099-05's proof, the give-up that counted ticks without progress. The give-up is gone, DEC-movement-sidestep-2026-11-24; the two scenes that
  proved a walking-in slow unit is not stopped short stay, and prove the arrival.)

Slow unit staged: a custom walking type (id 210, line category, speed 20 wu/s = 1.0 wu a tick, measured: 0.949 wu in x and 0.316 in y a tick, 1.000 along its heading), slower than 1.875 wu a tick.

Configuration: the shipped one for a csim scene: walking units, steering and route-around-terrain on (their defaults), targeting by sight on (the default), a 2000 x 2000 canvas.

Detector bounds (not rules; Westley's to change): CLEAR_PATH_WU 5 (DRAFT-clear-path-wu: where a lone walker's order may end), RUN_TICKS 1500 (a run limit; the slow walk takes 300 to 450 ticks), POS_TOL 1e-6 (a rested unit pushed by a hair).
"""
import ctypes
import math

from conftest import OMFeature
from test_PP_unit_support import RAIDER, VANGUARD, dest, pos, spawn, step

WALKING = 1
CANVAS = 2000.0
SLOW = 210                          # custom type: walking, 1.0 wu a tick
SLOW_SPEED_WU_S = 20.0
SLOW_PACE = 1.0                     # wu a tick; the rule's threshold is 1.875
ARRIVE_SLOT = 22.5                  # 1.5 x radius 15: a slot's arrival radius (R-099-04)
CLEAR_PATH_WU = 5.0                 # DRAFT-clear-path-wu
RUN_TICKS = 1500
POS_TOL = 1.0e-6
PUSH_REACH = 30.5                   # a mate this near at either end of a tick (collision spacing 2 x radius 15, plus slack) may have pushed a rested member: R-097-10, an idle unit steps aside for a mover of its own side


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


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


# ------------------------------------------------------------------ a unit still coming nearer is not stopped short

def test_R_099_04_a_slow_unit_ordered_alone_on_a_clear_path_keeps_its_destination_while_it_comes_nearer_and_reaches_its_point(lib, world_factory):
    """R-099-04 'with a clear path it walks to its point itself': a slow walking unit (1.0 wu a tick) ordered alone (a plain move) from (300,500) to (600,500), nothing in its way. On every tick it still has its destination
    (it is walking in) until it is within 5 wu of the point (CLEAR_PATH_WU), where its order ends and from then on the unit does not move. The walk takes about 300 ticks."""
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
            assert d <= CLEAR_PATH_WU, "tick %d: the order ended %.1f wu from the point with the unit still walking in (it came %.2f wu nearer on the tick before; the unit is still walking in)" % (
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


def test_R_099_04_a_slow_member_of_a_group_walks_to_its_slot_and_reaches_its_arrival_radius(lib, world_factory):
    """R-099-04 'Given a unit within its arrival radius of its destination (1.5 x collision radius for a formation slot ...)' (22.5 wu of its slot): two slow walking units at (200,500) and (200,540) are given a group move to (600,500). Each walks to its slot at 1.0 wu a tick,
    nothing in its way. On every tick it still has its destination while farther than 22.5 wu from its slot; the order of each ends only inside 22.5 wu of the slot (the arrival), and takes no step of its own from then on (a later push by the other member,
    still walking in, leaves it at its new position, R-099-04: measured, 0.41 wu on tick 381)."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, SLOW, 0, 200.0, 500.0)
    b = spawn(lib, w, SLOW, 0, 200.0, 540.0)
    _group_move(lib, w, [a, b], 600.0, 500.0)
    slots = {u: dest(lib, w, u)[1:] for u in (a, b)}
    assert all(dest(lib, w, u)[0] == 1 for u in (a, b)), "premise: a member has no destination after the group order"
    cleared, last = {}, {u: pos(lib, w, u) for u in (a, b)}
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        for u in (a, b):
            p, has = pos(lib, w, u), dest(lib, w, u)[0] == 1
            d = _dist(p, slots[u])
            if u not in cleared and not has:
                cleared[u] = (t, p)
                assert d <= ARRIVE_SLOT + 1.0e-6, "tick %d: member %d's order ended %.1f wu from its slot %s, outside its arrival radius %.1f wu, with the member still walking in (the unit is still walking in)" % (
                    t, u, d, slots[u], ARRIVE_SLOT)
            if u in cleared:
                assert not has, "tick %d: member %d took a destination after its order ended on tick %d" % (t, u, cleared[u][0])
                mate = b if u == a else a
                near_mate = min(_dist(p, pos(lib, w, mate)), _dist(last[u], last[mate])) <= PUSH_REACH
                assert _dist(p, last[u]) < POS_TOL or near_mate, "tick %d: member %d moved %.3f wu with no mate within %.1f wu of it, after its order ended on tick %d (a later push by a mover of its own side stands, R-099-04; a step of its own does not)" % (
                    t, u, _dist(p, last[u]), PUSH_REACH, cleared[u][0])
        last = {u: pos(lib, w, u) for u in (a, b)}
        if len(cleared) == 2 and t >= max(c[0] for c in cleared.values()) + 20:
            break
    assert len(cleared) == 2, "a member never reached its slot in %d ticks (cleared: %s)" % (RUN_TICKS, sorted(cleared))
