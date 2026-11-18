# Rule pins: R-099-04, R-099-05, R-096-02, R-084-04
"""E-13 R-099-04 / R-099-05, Round 6 piece E2 (docs/northstar/plans/engine-rules-2026-11-08/round6.md): a unit walking alone arrives and gives up.

Rule words (docs/bible/epics/E-13-movement-and-command.md):
  R-099-04  "Given a unit within its arrival radius of its destination (1.5 x collision radius for a formation slot, 2 x for a route waypoint), When the tick runs, Then it has arrived where it stands, without
            snapping to the point: its destination is cleared and it is stationary from that tick onward, and any later displacement by collision or direct position change leaves it at the new position with no
            re-approach. This holds for a unit walking alone as for a member of a group; for a unit walking alone it is not built (found 2026-11-18: walkers ordered alone stood 16 to 19 wu from their point with the
            destination still set for 10,000 ticks)".
  R-099-05  "... When it has been within 75 wu (about two slot spacings) of its slot for 40 consecutive ticks (2 s) without arriving, Then it ends its order where it stands, the same state as an arrival (destination
            cleared, stationary from that tick onward); the count resets when the unit leaves the 75 wu disc or arrives ... A unit moving or attack-moving alone gives up the same way, by the same two numbers measured to its
            ordered point, and only while it is trying to walk: a tick on which it holds a target or is in the pause after its own shot sets the count to zero, since a unit that pursues or stands to shoot is itself a
            lone walker whose destination is its target's place (DEC-draws-round6-2026-11-18; ... not built)."
  Round 6 E2: "The count is not written to a save file (a loaded game starts the count again; as the give-up state of Round 2)."
Cause the round names (csrc/tactical_move.c): om_move_walker_step finishes a lone walker only by reaching its aim exactly, so a walker held short of its point by a unit that gives no ground is pushed back every tick
with the destination set, for ever; om_move_giveup_pass skips every unit with no group. Round 5's first try at the 2-radius check on routed lone walkers (git show fd342241c) turned 14 csim tests red: the report
of this test writer lists the existing tests that assert the old reading.

Configuration: the shipped one for a csim scene: walking units (the kind is set, as the lab does), steering and route-around-terrain on (their defaults), targeting by sight on (the default), a 2000 x 2000 canvas.
Every case is asserted per tick. Units that give no ground (a walker is "held" by them):
  FRIEND  an own Vanguard that holds a target and fires (an enemy Supply 250 wu east of it, 1e6 hp, which never fires): engaged, so not idle (R-097-10), and it never moves. As the HELD scene of
          tests/csim/test_E13_R097_10_idle_own_units_yield.py.
  RING    six enemy Supplies (1e6 hp, never fire, never move) on a circle of 30 wu round the walker's point: a walker coming from outside rests against the ring 52 to 60 wu from the point (measured: 53.3, in a
          groove between two of them), inside the 75 wu disc and outside every arrival radius.
  GUARDED the same ring made of own Vanguards that hold a target (an enemy Supply 250 wu west of the point, 1e6 hp): used for an attack-mover, which would take enemy ring units as targets.
How the count is read, as tests/csim/test_PP_unit_giveup.py pins it: after every tick, a tick is "near" when the unit's position REPORTED BY THE PREVIOUS TICK is within 75 wu of its point (positions are reported one tick
behind); `near` counts consecutive near ticks; the order must still be active after the tick that makes near 39 and ended after the tick that makes near 40.

Detector bounds (not rules; Westley's to change): SETTLE_TICKS 3 (R-099-04 "has no destination within 3 ticks": round6.md E2 Proof, DRAFT-arrive-ticks), PAUSE_TICKS 9 (the nine ticks after a shot, as the E1
file), PAUSE_SLACK 3 (DRAFT-pause-slack-ticks: how many ticks either side of the exact boundary the pause case tolerates, the first counted tick after a pause being a convention the rule does not fix), LOAD_SLACK 3
(DRAFT-load-slack-ticks: the same for the first tick after a load), RUN_TICKS 400 (a run limit), LOCK_END_BY 4 (DRAFT-lock-end-ticks: the premise that a lock ended within this many ticks of the hook).
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, spawn, step, target

FLYING, WALKING = 0, 1
CANVAS = 2000.0
RADIUS = 15.0                       # collision radius (R-097-05: 2 x radius 15)
ARRIVE_SLOT = 1.5 * RADIUS          # 22.5 wu
ARRIVE_WAYPOINT = 2.0 * RADIUS      # 30 wu
GIVE_UP_RADIUS = 75.0
GIVE_UP_TICKS = 40
SETTLE_TICKS = 3                    # DRAFT-arrive-ticks
PAUSE_TICKS = 9
PAUSE_SLACK = 3                     # DRAFT-pause-slack-ticks
LOAD_SLACK = 3                      # DRAFT-load-slack-ticks
LOCK_END_BY = 4                     # DRAFT-lock-end-ticks
RUN_TICKS = 400
BIG_HP = 1.0e6
POS_TOL = 1.0e-6                    # numeric slack of a rested unit pushed by a hair, not a rule threshold


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _world(lib, wf, kinds=(RAIDER, VANGUARD), kind=WALKING):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    for k in kinds:
        assert lib.om_roster_set_movement_kind(w, k, kind) == 0
    return w


def _move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def _group_move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_group_move(w, arr, len(ids), float(x), float(y))


def _none(t):
    return t is None or t <= 0


def _supply(lib, w, faction, x, y):
    s = spawn(lib, w, SUPPLY, faction, x, y)
    lib.om_unit_set_hp(w, s, BIG_HP)
    return s


def _friend(lib, w, xy):
    """FRIEND: an own Vanguard at `xy` that holds a target and fires. Returns (friend, its victim)."""
    e = spawn(lib, w, VANGUARD, 0, *xy)
    s = _supply(lib, w, 1, xy[0] + 250.0, xy[1])
    return e, s


def _ring(lib, w, p, kind):
    """RING (enemy Supplies) or GUARDED (own Vanguards that hold a target) of six units 30 wu round `p`."""
    pts = [(p[0] + 30.0 * math.cos(k * math.pi / 3.0), p[1] + 30.0 * math.sin(k * math.pi / 3.0)) for k in range(6)]
    if kind == "enemy":
        return [_supply(lib, w, 1, *q) for q in pts], None
    units = [spawn(lib, w, VANGUARD, 0, *q) for q in pts]
    return units, _supply(lib, w, 1, p[0] - 250.0, p[1])


class Count:
    """The near count of tests/csim/test_PP_unit_giveup.py: a tick is near when the position reported by the previous tick is within 75 wu of the point."""

    def __init__(self, point):
        self.point = point
        self.near = 0
        self.prev = math.inf

    def tick(self, p):
        self.near = self.near + 1 if self.prev <= GIVE_UP_RADIUS else 0
        self.prev = _dist(p, self.point)
        return self.near


# ------------------------------------------------------------------ R-099-04: arrival of a walker ordered alone

def _arrival_run(lib, w, m, point, radius, ticks, what):
    """Every tick: the number of consecutive ticks on which the walker's position is within `radius` of its point with a destination still set never exceeds SETTLE_TICKS; once the destination is cleared it
    stays cleared and the walker stays where it stood. Returns (the trace of (position, has_dest), the first tick within `radius`)."""
    held, first_in, cleared_at, trace = 0, None, None, []
    for t in range(1, ticks + 1):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append((p, has))
        if cleared_at is not None:
            assert not has, "%s: tick %d: the unit has a destination again after losing it on tick %d (R-099-04: no re-approach)" % (what, t, cleared_at)
            assert _dist(p, trace[cleared_at - 1][0]) < POS_TOL, "%s: tick %d: the unit moved after its order ended on tick %d (R-099-04: stationary from that tick onward): %s -> %s" % (what, t, cleared_at, trace[cleared_at - 1][0], p)
            continue
        if _dist(p, point) <= radius:
            if first_in is None:
                first_in = t
            held = held + 1 if has else 0
            assert held <= SETTLE_TICKS, (
                "%s: tick %d: the unit has stood within %.1f wu of its point %s with its destination still set for %d ticks (it is %.1f wu away, at %s; R-099-04: arrived within the arrival radius, destination cleared)" % (
                    what, t, radius, point, held, _dist(p, point), p))
        if not has:
            cleared_at = t
    assert first_in is not None, "scene broken: the unit never came within %.1f wu of its point %s in %d ticks (closest %.1f)" % (radius, point, ticks, min(_dist(p, point) for p, _ in trace))
    return trace, first_in


def test_R_099_04_a_walker_ordered_alone_and_stopped_18_wu_from_its_point_by_a_standing_friend_has_arrived(lib, world_factory):
    """R-099-04 'a unit within its arrival radius (1.5 x collision radius) of its destination has arrived ... its destination is cleared and it is stationary from that tick onward ... This holds for a unit
    walking alone': a Vanguard ordered alone (a plain move, no group) from (300,500) to (600,500); an own Vanguard that holds a target (FRIEND) stands at (612,500), 12 wu behind the point, so the walker rests 18 wu
    in front of it (measured on the Round 5 engine: it stays at (582.0, 500.0), destination set, for ever). Every tick: it never stands within 22.5 wu of its point with a destination for more than 3 ticks; once the
    destination is cleared it is never set again and the walker does not move; the friend never moves."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, 300.0, 500.0)
    e, s = _friend(lib, w, (612.0, 500.0))
    assert _move(lib, w, [m], 600.0, 500.0) == 0
    trace, first_in = _arrival_run(lib, w, m, (600.0, 500.0), ARRIVE_SLOT, RUN_TICKS, "18 wu from the point, stopped by a friend")
    assert pos(lib, w, e) == (612.0, 500.0), "premise: the friend stepped aside"
    assert _dist(trace[-1][0], (600.0, 500.0)) > 10.0, "premise: the walker is at the point instead of resting against the friend (%s)" % (trace[-1][0],)
    assert target(lib, w, e) == s, "premise: the friend does not hold its target (it would be idle and step aside, R-097-10)"


def test_R_099_04_a_lone_walker_that_followed_route_waypoints_has_arrived_inside_2_radii(lib, world_factory):
    """R-099-04 'within its arrival radius (... 2 x for a route waypoint)': a Vanguard ordered alone from (300,500) to (700,500) round a wall (x 400..500, y 0..900, so its route has waypoints: it goes
    north of y 900 and comes back). A friend that holds a target stands at (703,500), 3 wu past the point, so the walker rests 27 wu from the point (measured: 27.0 on the Round 5 engine), outside 1.5 radii and inside 2.
    Every tick: it never stands within 30 wu of its point with a destination for more than 3 ticks; once cleared it stays cleared and stays where it stood."""
    w = _world(lib, world_factory)
    assert lib.om_map_block_rect(w, 410.0, 10.0, 490.0, 890.0, 0, 4) == 0
    m = spawn(lib, w, VANGUARD, 0, 300.0, 500.0)
    _friend(lib, w, (703.0, 500.0))
    assert _move(lib, w, [m], 700.0, 500.0) == 0
    trace, first_in = _arrival_run(lib, w, m, (700.0, 500.0), ARRIVE_WAYPOINT, RUN_TICKS, "routed lone walker resting 27 wu from its point")
    assert max(p[1] for p, _ in trace) > 900.0, "scene broken: the walker never went round the wall (its route had no waypoint); highest y %.0f" % max(p[1] for p, _ in trace)
    assert min(_dist(p, (700.0, 500.0)) for p, _ in trace) > ARRIVE_SLOT, "scene broken: the walker came within 1.5 radii of its point (closest %.1f), so the 2 radii are not what ends it" % min(_dist(p, (700.0, 500.0)) for p, _ in trace)


def test_R_099_04_control_a_lone_walker_resting_27_wu_from_its_point_without_a_route_has_not_arrived(lib, world_factory):
    """R-099-04 '1.5 x collision radius for a formation slot, 2 x for a route waypoint': a lone walker that followed no waypoint (a clear map, a straight walk) has the 1.5 radii only. The scene of the routed
    test without the wall: the walker rests 27 wu from its point against the friend. For the first 30 ticks it has been inside the 75 wu disc it still has its destination (27 wu is not within 22.5; the give-up of
    R-099-05 comes at 40). Green today and must stay green."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, 300.0, 500.0)
    _friend(lib, w, (703.0, 500.0))
    point = (700.0, 500.0)
    assert _move(lib, w, [m], *point) == 0
    c = Count(point)
    settled = 0
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p = pos(lib, w, m)
        near = c.tick(p)
        if 25.0 < _dist(p, point) < 29.0:
            settled += 1
        if settled > 0 and near <= 30:
            assert dest(lib, w, m)[0] == 1, "tick %d: the walker at %.1f wu from its point (%d ticks in the 75 wu disc) has no destination; 27 wu is outside 1.5 radii and it followed no waypoint" % (t, _dist(p, point), near)
        if near >= 30 and settled > 0:
            break
    assert settled > 10, "scene broken: the walker never rested 25 to 29 wu from its point (last %s)" % (pos(lib, w, m),)


def test_R_099_04_control_a_lone_walker_with_a_clear_path_arrives_at_its_point(lib, world_factory):
    """R-099-04: a Raider ordered alone from (300,400) to (900,700), nothing in its way, ends its order within 22.5 wu of the point, never has a destination again and does not move after. On every tick that
    it is 40 wu or more from the point (reported) it still has its destination: a walker 40 wu from its point has not arrived. Green today and must stay green."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    point = (900.0, 700.0)
    assert _move(lib, w, [m], *point) == 0
    cleared_at, trace = None, []
    for t in range(1, 301):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append(p)
        if cleared_at is None and _dist(p, point) >= 40.0:
            assert has, "tick %d: the walker %.1f wu from its point has no destination (it has not arrived)" % (t, _dist(p, point))
        if cleared_at is None and not has:
            cleared_at = t
            assert _dist(p, point) <= ARRIVE_SLOT, "tick %d: the order ended %.1f wu from the point" % (t, _dist(p, point))
        if cleared_at is not None:
            assert not has and _dist(p, trace[cleared_at - 1]) < POS_TOL, "tick %d: the unit moved or took a destination after arriving on tick %d" % (t, cleared_at)
    assert cleared_at is not None, "the unit never arrived: at %s" % (trace[-1],)


def test_R_099_04_control_a_flying_unit_ordered_alone_is_unchanged(lib, world_factory):
    """R-099-04 (round6.md E2 is for walkers): a flying Raider ordered alone from (300,400) to (900,700), nothing in its way, ends its order within 22.5 wu of the point (the steering arrival, 1.5 radii), keeps no
    destination afterwards and does not move after. Green today and must stay green."""
    w = _world(lib, world_factory, kind=FLYING)
    m = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    point = (900.0, 700.0)
    assert _move(lib, w, [m], *point) == 0
    cleared_at, trace = None, []
    for t in range(1, 301):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        trace.append(p)
        if cleared_at is None and not has:
            cleared_at = t
            assert _dist(p, point) <= ARRIVE_SLOT, "tick %d: the flying unit's order ended %.1f wu from the point" % (t, _dist(p, point))
        if cleared_at is not None:
            assert not has and _dist(p, trace[cleared_at - 1]) < POS_TOL, "tick %d: the flying unit moved or took a destination after arriving on tick %d" % (t, cleared_at)
    assert cleared_at is not None, "the flying unit never arrived: at %s" % (trace[-1],)


# ------------------------------------------------------------------ R-099-05: the give-up of a walker ordered alone

RING_POINT = (1000.0, 1000.0)
RING_START = (1300.0, 1000.0)


def _ring_scene(lib, wf):
    """A Raider M ordered alone (a plain move) from (1300,1000) to (1000,1000) which a RING of enemy Supplies holds back: it rests about 53 wu from the point. Returns (w, m)."""
    w = _world(lib, wf)
    _ring(lib, w, RING_POINT, "enemy")
    m = spawn(lib, w, RAIDER, 0, *RING_START)
    assert _move(lib, w, [m], *RING_POINT) == 0
    return w, m


def test_R_099_05_a_walker_ordered_alone_and_held_inside_75_wu_ends_its_order_on_the_40th_tick_not_the_39th(lib, world_factory):
    """R-099-05 'A unit moving alone gives up the same way, by the same two numbers measured to its ordered point': a Raider ordered alone (plain move) is held by a ring of enemy Supplies about 53 wu from its
    point (inside 75 wu, outside every arrival radius). Counting as tests/csim/test_PP_unit_giveup.py does (previous tick's reported position): its destination is still set after the tick that makes the count 39,
    cleared after the tick that makes it 40; it is not an arrival (more than 30 wu from the point); it holds no target on any tick; from that tick on it has no destination and does not move (20 ticks)."""
    w, m = _ring_scene(lib, world_factory)
    c = Count(RING_POINT)
    ended = None
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        near = c.tick(p)
        assert _none(target(lib, w, m)), "tick %d: a plain mover holds a target %s (scene broken)" % (t, target(lib, w, m))
        if near == GIVE_UP_TICKS - 1:
            assert has, "tick %d: the walker gave up after %d consecutive ticks inside 75 wu of its point (before the 40th)" % (t, near)
        if near == GIVE_UP_TICKS:
            assert not has, "tick %d: the walker still has its destination after %d consecutive ticks inside 75 wu of its point, %.1f wu away, and holds no target (R-099-05, lone walker)" % (t, near, _dist(p, RING_POINT))
            assert _dist(p, RING_POINT) > ARRIVE_WAYPOINT, "scene broken: tick %d: an arrival (%.1f wu from the point), not a give-up" % (t, _dist(p, RING_POINT))
            ended = (t, p)
            break
        if not has:
            pytest.fail("tick %d: the order ended with only %d consecutive ticks inside 75 wu (%.1f wu from the point): not the give-up boundary" % (t, near, _dist(p, RING_POINT)))
    assert ended is not None, "the walker never had 40 consecutive ticks inside 75 wu in %d ticks (at %s)" % (RUN_TICKS, pos(lib, w, m))
    for k in range(1, 21):
        step(lib, w)
        assert dest(lib, w, m)[0] == 0, "tick %d (give-up on %d): the destination is set again" % (ended[0] + k, ended[0])
        assert _dist(pos(lib, w, m), ended[1]) < POS_TOL, "tick %d (give-up on %d): the unit moved after ending its order: %s -> %s" % (ended[0] + k, ended[0], ended[1], pos(lib, w, m))


def test_R_099_05_the_count_of_a_walker_alone_starts_again_when_it_leaves_the_disc(lib, world_factory):
    """R-099-05 'the count resets when the unit leaves the 75 wu disc': the ring scene; when the count is 25 the walker is put back at its start, 300 wu from its point (a direct position change, the way
    the E1 file moves a unit; its order stays). It walks back, rests against the ring again. The order is still active after the tick that makes the new consecutive count 39 and cleared after the one that makes
    it 40, although the two visits together are more than 40 ticks."""
    w, m = _ring_scene(lib, world_factory)
    c = Count(RING_POINT)
    first_visit, put_back, ended = 0, None, None
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p, has = pos(lib, w, m), dest(lib, w, m)[0] == 1
        near = c.tick(p)
        if put_back is None:
            first_visit += 1 if near else 0
            assert has, "tick %d: the walker ended its order at count %d, before the put-back (scene broken or an early give-up)" % (t, near)
            if near == 25:
                lib.om_unit_teleport(w, m, RING_START[0], RING_START[1], 0)
                c.prev = _dist(RING_START, RING_POINT)
                put_back = t
                assert dest(lib, w, m)[0] == 1, "scene broken: the put-back took the destination"
            continue
        if near == GIVE_UP_TICKS - 1:
            assert has, "tick %d: the walker gave up at consecutive count %d, %d ticks after the put-back; the count was not reset by leaving the disc (first visit %d ticks)" % (t, near, t - put_back, first_visit)
        if near == GIVE_UP_TICKS:
            assert not has, "tick %d: the walker still has its destination after %d consecutive ticks inside 75 wu since its return" % (t, near)
            ended = t
            break
        if not has:
            pytest.fail("tick %d: the order ended with a consecutive count of %d, %d ticks after the put-back; the count was not reset by leaving the disc (first visit %d ticks)" % (t, near, t - put_back, first_visit))
    assert put_back is not None, "scene broken: the walker never had a count of 25"
    assert ended is not None, "the walker never gave up after its return"


# ---- only while it is trying to walk

def _guarded_scene(lib, wf):
    """A Raider M attack-moved alone from (1300,1000) to (1000,1000) which a GUARDED ring (own Vanguards that hold a target) holds back about 53 wu from the point; V, an enemy Supply (1e6 hp), waits in
    the far corner. Returns (w, m, v, ring)."""
    w = _world(lib, wf)
    ring, s1 = _ring(lib, w, RING_POINT, "own")
    m = spawn(lib, w, RAIDER, 0, *RING_START)
    v = _supply(lib, w, 1, 1900.0, 1900.0)
    assert attack_move(lib, w, [m], *RING_POINT) == 0
    return w, m, v, ring, s1


def _bring_victim_at_count(lib, w, m, v, c, at_count):
    """Step until the count is `at_count`, then put V 60 wu east of the unit (beyond the unit's reach before, inside its range after). Returns the tick."""
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        p = pos(lib, w, m)
        near = c.tick(p)
        assert dest(lib, w, m)[0] == 1, "tick %d: the walker's order ended with count %d before the victim came" % (t, near)
        if near == at_count:
            lib.om_unit_teleport(w, v, p[0] + 60.0, p[1], 0)
            return t
    pytest.fail("scene broken: the walker never had a count of %d (at %s)" % (at_count, pos(lib, w, m)))


def test_R_099_05_a_lone_attack_mover_holding_a_target_keeps_its_order_while_it_holds_it(lib, world_factory):
    """R-099-05 'only while it is trying to walk: a tick on which it holds a target ... sets the count to zero': an attack-moving Raider held by a guarded ring 53 wu from its point (inside the disc, the count
    running); when the count is 20 an enemy Supply V is put 60 wu from it (inside its attack range 200, so it stands to shoot). It holds V as its target and shoots it for 120 ticks (V's hp falls). On every one of
    those ticks it still has its destination and does not move: a count that ran through the shooting would end the order on the 40th tick."""
    w, m, v, ring, s1 = _guarded_scene(lib, world_factory)
    c = Count(RING_POINT)
    tv = _bring_victim_at_count(lib, w, m, v, c, 20)
    assert all(target(lib, w, r) == s1 for r in ring), "scene broken: a ring unit holds no target (it would be idle and step aside)"
    at_rest = pos(lib, w, m)
    held = 0
    for t in range(tv + 1, tv + 121):
        step(lib, w)
        c.tick(pos(lib, w, m))
        if target(lib, w, m) == v:
            held += 1
        if held:
            assert target(lib, w, m) == v, "tick %d: the unit lost its target after %d ticks (V is alive)" % (t, held)
            assert dest(lib, w, m)[0] == 1, "tick %d: the lone attack-mover has ended its order after %d ticks of standing to shoot at V, 60 wu away (R-099-05: no count while it holds a target)" % (t, held)
            assert _dist(pos(lib, w, m), at_rest) < POS_TOL, "tick %d: the unit moved while standing to shoot" % t
    assert held >= 110 and hp(lib, w, v) < BIG_HP, "scene broken: the unit held V for %d ticks, V's hp %s" % (held, hp(lib, w, v))


def test_R_099_05_the_pause_after_its_own_shot_is_not_counted(lib, world_factory):
    """R-099-05 'a tick on which it ... is in the pause after its own shot sets the count to zero': the scene above; V is put 60 wu from the unit when the count is 20, the unit shoots it, and V is taken
    from it on the tick after the unit's first shot S (hp set to 0, the way the E1 file ends a lock by another unit's kill). The nine ticks S+1 to S+9 are the pause; no tick of them is counted. The count starts
    on the first walking tick, S+10: the order is still active on every tick to S+46 (a count of 37) and ended by S+53 (a count of 44, PAUSE_SLACK 3 each way of the 40th, S+49). A count that took in the pause
    ends it about S+40."""
    w, m, v, ring, s1 = _guarded_scene(lib, world_factory)
    c = Count(RING_POINT)
    tv = _bring_victim_at_count(lib, w, m, v, c, 20)
    shot, ended = None, None
    for t in range(tv + 1, tv + 200):
        step(lib, w)
        has = dest(lib, w, m)[0] == 1
        if shot is None:
            assert has, "tick %d: the order ended before the unit had shot" % t
            if hp(lib, w, v) < BIG_HP:
                shot = t
                at_shot = pos(lib, w, m)
                kill(lib, w, v)
            continue
        k = t - shot
        if k <= LOCK_END_BY:
            continue
        assert _none(target(lib, w, m)) or k <= LOCK_END_BY, "tick %d: the unit still holds a target %d ticks after its shot" % (t, k)
        assert _dist(pos(lib, w, m), at_shot) < POS_TOL, "tick %d: the unit moved (it is held by the ring)" % t
        if k <= PAUSE_TICKS + GIVE_UP_TICKS - PAUSE_SLACK:   # S+46: a count of 37
            assert has, "tick %d (shot on %d): the order ended %d ticks after the shot; the pause after the shot (S+1 to S+9) is not counted, the count starts on S+10 and gives up at about S+49 (R-099-05)" % (t, shot, k)
        if not has:
            ended = k
            break
    assert shot is not None, "scene broken: the unit never shot V"
    assert ended is not None, "the unit never gave up after losing its target (the ring holds it): last position %s" % (pos(lib, w, m),)
    assert ended <= PAUSE_TICKS + GIVE_UP_TICKS + PAUSE_SLACK + 1, "the order ended %d ticks after the shot, later than S+%d" % (ended, PAUSE_TICKS + GIVE_UP_TICKS + PAUSE_SLACK + 1)


def test_R_099_05_a_lone_attack_mover_that_stands_to_shoot_keeps_its_order_and_walks_on_after_the_kill(lib, world_factory):
    """R-099-05 / R-096-02 (round6.md E2 'Further proof scene'): a Raider attack-moved alone from (300,400) to (300,1000) has an enemy Supply 60 wu east of it (inside its attack range and its notice distance) with
    1e6 hp. It stands to shoot at it for 100 ticks: every tick it holds the Supply, has a destination, does not move. The Supply is then killed (hp 0 between ticks); within the usual lock-end ticks it
    holds no target and from the end of its pause it walks on and ends its order within 22.5 wu of its ordered point (300,1000). Measured on the Round 5 engine: while it stands to shoot a target 60 wu away its
    destination is its ordered point, 600 wu off; the scene with the destination inside 75 wu is the guarded ring above. Green today and must stay green."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300.0, 400.0)
    v = _supply(lib, w, 1, 360.0, 400.0)
    assert attack_move(lib, w, [u], 300.0, 1000.0) == 0
    held = 0
    for t in range(1, 111):
        step(lib, w)
        if target(lib, w, u) == v:
            held += 1
            if held == 1:
                at_rest = pos(lib, w, u)
        if held:
            assert target(lib, w, u) == v and dest(lib, w, u)[0] == 1 and _dist(pos(lib, w, u), at_rest) < POS_TOL, (
                "tick %d: after %d ticks of standing to shoot: target %s, has destination %s, position %s (at rest %s)" % (t, held, target(lib, w, u), dest(lib, w, u)[0], pos(lib, w, u), at_rest))
    assert held >= 100, "scene broken: the unit held the Supply for only %d ticks" % held
    kill(lib, w, v)
    arrived = None
    for t in range(1, 301):
        step(lib, w)
        if t > LOCK_END_BY:
            assert _none(target(lib, w, u)), "tick %d after the kill: the unit holds a target" % t
        if dest(lib, w, u)[0] == 0:
            arrived = t
            break
    assert arrived is not None, "the unit did not reach its point after the kill, in 300 ticks: at %s" % (pos(lib, w, u),)
    assert _dist(pos(lib, w, u), (300.0, 1000.0)) <= ARRIVE_SLOT, "the order ended %.1f wu from the ordered point, at %s" % (_dist(pos(lib, w, u), (300.0, 1000.0)), pos(lib, w, u))


# ---- a group member's give-up is unchanged

@pytest.mark.parametrize("kind", [FLYING, WALKING], ids=["flying", "walking"])
def test_R_099_05_control_a_group_members_give_up_is_unchanged_40_ticks_75_wu_to_its_slot(lib, world_factory, kind):
    """R-099-05 (first sentence, unchanged): two Raiders at (200,500) and (200,540) given a group move to (1200,500) (the scene of that file moved onto the canvas); the first one's slot is occupied by an enemy Supply parked on it (an own idle unit would step aside for a walker, R-097-10), so the first
    member cannot reach its slot. Counted as tests/csim/test_PP_unit_giveup.py (the same scene): its order is active after the tick that makes the count 39 and ended after the tick that makes it 40, measured
    to its slot, farther than 22.5 wu from the slot. Green today and must stay green; the lone-walker build must not move this boundary."""
    w = _world(lib, world_factory, kind=kind)
    a = spawn(lib, w, RAIDER, 0, 200.0, 500.0)
    b = spawn(lib, w, RAIDER, 0, 200.0, 540.0)
    _group_move(lib, w, [a, b], 1200.0, 500.0)
    _, sx, sy = dest(lib, w, a)
    _supply(lib, w, 1, sx, sy)
    c = Count((sx, sy))
    for t in range(1, 601):
        step(lib, w)
        p, has = pos(lib, w, a), dest(lib, w, a)[0] == 1
        near = c.tick(p)
        if near == GIVE_UP_TICKS - 1:
            assert has, "tick %d: the group member gave up before 40 ticks within 75 wu of its slot" % t
        if near == GIVE_UP_TICKS:
            assert not has, "tick %d: the group member still has its destination after 40 consecutive ticks within 75 wu of its slot" % t
            assert _dist(p, (sx, sy)) > ARRIVE_SLOT, "scene broken: an arrival, not a give-up"
            return
        if not has:
            pytest.fail("tick %d: the group member's order ended with only %d near ticks (%.1f wu from its slot)" % (t, near, _dist(p, (sx, sy))))
    pytest.fail("the group member never accumulated 40 near ticks")


# ---- the count is not saved

def _save(lib, w):
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def test_R_099_05_the_count_of_a_walker_alone_is_not_saved_a_loaded_game_starts_it_again(lib, world_factory):
    """R-099-05 / round6.md E2 'The count is not written to a save file (a loaded game starts the count again; as the give-up state of Round 2)': the ring scene is saved when the walker's count is 25 and
    loaded into a fresh world prepared the same way (feature, canvas, walking kind). The walker is where it was, with its destination. From the load its count starts again: its order is active after the
    load tick that makes 37 (LOAD_SLACK 3 under the exact 40) and ended by load tick 43; a count that was saved would end it about 15 ticks after the load."""
    w, m = _ring_scene(lib, world_factory)
    c = Count(RING_POINT)
    for t in range(1, RUN_TICKS + 1):
        step(lib, w)
        if c.tick(pos(lib, w, m)) == 25:
            break
    else:
        pytest.fail("scene broken: the walker never had a count of 25")
    assert dest(lib, w, m)[0] == 1
    at_save = pos(lib, w, m)
    buf, size = _save(lib, w)
    w2 = _world(lib, world_factory)
    assert lib.om_load_state_read(w2, buf, size) == 0
    assert pos(lib, w2, m) == at_save and dest(lib, w2, m)[0] == 1, "scene broken: the load did not bring back the walker's place and order: %s %s" % (pos(lib, w2, m), dest(lib, w2, m))
    ended = None
    for k in range(1, 61):
        step(lib, w2)
        has = dest(lib, w2, m)[0] == 1
        if k <= GIVE_UP_TICKS - LOAD_SLACK:
            assert has, "load tick %d: the walker gave up %d ticks after the load; its count of 25 was saved (R-099-05: a loaded game starts the count again)" % (k, k)
        if not has:
            ended = k
            break
    assert ended is not None, "the walker never gave up after the load (60 ticks)"
    assert ended <= GIVE_UP_TICKS + LOAD_SLACK, "the walker gave up %d ticks after the load, later than load tick %d" % (ended, GIVE_UP_TICKS + LOAD_SLACK)
