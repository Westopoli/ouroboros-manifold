"""Lanes and hard bodies on a slope (SPEC.md 5.9 "Lanes" and "Bodies on a slope", 5.10 "Slope mouths", 6 ramp).

Feature under test (NOT built when this file was written): a slope is `width` wide and carries lanes; a unit on
a slope keeps one lane and is a hard body against other units on the SAME slope. Today every unit on a slope
rides the centre line and they stack on one point.

Geometry (ramp x1 40, sl 600, sw 200, g 1, h 1, the 80 x 40 grid of 50 unit cells, SPEC 6): the plateau starts
at x = 2000; the slope's bottom edge centre is (1975, 1000), direction +x, so the slope axis is the line
y = 1000 and the left normal (-dy, dx) is +y: a unit's lateral offset is y - 1000. Top edge centre (2575, 1000)
on the plateau (layer 2). Body radius 15, body width 30. Usable half-width h = max(0, sw / 2 - 15): sw 200 gives
85 and lane offsets 0, +30, -30, +60, -60 (|offset| <= 85); sw 100 gives 35 and lanes 0, +30, -30; sw 30 gives 0
and the single lane 0. Mount reach is max(15, 25) = 25 from the edge centre; a unit spawned within 25 of the
edge centre mounts on tick 0 and its lane is its lateral offset rounded to the nearest lane.

Conventions (copied from test_slope_mouth.py / test_slope_mouth_speed.py):
- Walkers are `raider` copies with movement_kind walk. One inert enemy raider is parked on layer 5 at
  (3900, 150) so the run has both sides (a side with no units loses at once, SPEC 5.11); same-layer-only fire
  keeps it inert. `spawn_jitter` 0 unless a test says otherwise; `stalemate_ticks` is 3000 unless stated.
- "On the slope" is trace flag bit2. The trace is float32; lane offsets 0, 30, 60 are exact in it, tolerance 1e-6.
- How a unit is made to STAND on the slope (tests 2b, 3b): a MOVE order whose goal is a point on the slope axis
  (2275, 1000), the slope's midpoint. The goal cell is plateau (blocked on layer 1, open on layer 2), so the goal
  layer is 2 and the walker climbs; it arrives within 1.5 * 15 = 22.5 of the point ON the slope, and an arrived
  MOVE unit has no goal and stops where it is (SPEC 5.9, 5.10). No enemy is needed. It only works for a unit in
  lane 0 (a lane +30 unit is 30 > 22.5 away and climbs past), so those tests use `sw` 30 (one lane).

Expected today (centre line, stacked): red are the lane spread, lane choice by lateral position, the dismount
offset, hard bodies on the slope, queueing, the width tests, lane crossing, the head-on deadlock and the E3 mean.
Green today (already working, guards, not regression catchers of the new feature): the lane-membership test
(every offset is 0, which is a lane), the single-lane twins, timing, off-slope units (test 6) and determinism.

SPEC gaps filled here:
- "After the first tick on the slope": the lane offset is asserted from the second on-slope tick of each unit
  (the first is the placement tick; it is asserted too in the single walker test 1c).
- Which lane two walkers land in cannot be derived without the lateral arrival position; the same-lane tests
  therefore use sw 30 where there is only one lane. The wide variant asserts only what holds whatever lane is
  chosen (distance >= 29).
- Head-on in one lane (test 4b) has no SPEC number for where they meet; asserted: neither dismounts, they never
  pass (up-mover x < down-mover x every tick), the run is a stalemate, spacing >= 29.
- E3 (test 7): defenders 300 beyond the top edge (the brief), not the 60 of experiments/e3_ramp.py.
"""
import numpy as np
import pytest

import layerlab.run as runmod
from layerlab.ffi import WIN_STALEMATE
from conftest import add_type, grp, make_scenario, unit_trace

R = 15.0
BODY = 2 * R                          # 30, the lane pitch
OVERLAP_BELOW = BODY - 1.0            # 29
AXIS_Y = 1000.0
BOTTOM = (1975.0, AXIS_Y)
SL = 600.0
TOP = (1975.0 + SL, AXIS_Y)
GOAL_BEYOND = [TOP[0] + 60.0, AXIS_Y]   # (2635, 1000) on the plateau
GOAL_ON_SLOPE = [2275.0, AXIS_Y]        # the slope's midpoint
LANES_200 = [0.0, 30.0, -30.0, 60.0, -60.0]
TOL = 1e-6
MAX_TICKS = 3000


# ---- helpers -----------------------------------------------------------------------------------

def _scn(groups, sw=200.0, speed=80.0, rules=None, run=None, sl=SL):
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    ru = {"max_ticks": MAX_TICKS, "stalemate_ticks": 3000}
    ru.update(run or {})
    scn = make_scenario(groups, terrain={"preset": "ramp", "x1": 40, "sl": float(sl), "sw": float(sw),
                                         "g": 1, "h": 1}, rules=r, run=ru)
    return add_type(scn, "walker", "raider", movement_kind="walk", speed=float(speed))


def _enemy():
    return grp("B", "raider", 3900.0, 150.0, 5)


def _box(n=10, goal=GOAL_BEYOND):
    return grp("A", "walker", 900.0, AXIS_Y, 1, count=n, formation="box", cols=5, spacing=31.0,
               order="move", goal=list(goal))


def _crowd(sw=200.0, speed=80.0, n=10, **kw):
    return _scn([_box(n), _enemy()], sw=sw, speed=speed, **kw)


def _lone(x, y, layer, goal, sw=200.0, speed=150.0, **kw):
    return _scn([grp("A", "walker", x, y, layer, order="move", goal=list(goal)), _enemy()],
                sw=sw, speed=speed, **kw)


def _on(res, units):
    """(units, ticks) bool: trace flag bit2."""
    return np.stack([unit_trace(res, i).on_slope for i in units])


def _offsets(res, units):
    """(units, ticks) lateral offset y - 1000 (the slope axis is the line y = 1000)."""
    return np.stack([unit_trace(res, i).y - AXIS_Y for i in units])


def _xs(res, units):
    return np.stack([unit_trace(res, i).x for i in units])


def _slope_pair_distances(res, units):
    """(pairs, ticks) xy distance of every pair i < j, NaN on ticks where either is off the slope or dead."""
    on = _on(res, units) & np.stack([unit_trace(res, i).alive.astype(bool) for i in units])
    x = np.stack([unit_trace(res, i).x for i in units])
    y = np.stack([unit_trace(res, i).y for i in units])
    out = []
    for a in range(len(units)):
        for b in range(a + 1, len(units)):
            d = np.hypot(x[a] - x[b], y[a] - y[b])
            out.append(np.where(on[a] & on[b], d, np.nan))
    return np.array(out)


def _first_on(res, i):
    on = np.flatnonzero(unit_trace(res, i).on_slope)
    return int(on[0]) if len(on) else None


def _last_on(res, units):
    on = np.flatnonzero(_on(res, units).any(axis=0))
    return int(on.max()) if len(on) else None


def _nearest_lane_dev(off, lanes):
    """Smallest |off - lane| over the lane offsets, elementwise."""
    return np.min(np.abs(np.asarray(off)[..., None] - np.asarray(lanes)), axis=-1)


def _after_first_tick(res, units):
    """Per unit: (offsets while on the slope, excluding that unit's first on-slope tick)."""
    on, off = _on(res, units), _offsets(res, units)
    out = []
    for k in range(len(units)):
        idx = np.flatnonzero(on[k])
        out.append(off[k][idx[1:]] if len(idx) else np.array([]))
    return out


def _all_mounted(res, units):
    assert _on(res, units).any(axis=1).all(), "units that never mounted: %s" % [
        i for i in units if _first_on(res, i) is None]


# ---- test 1: lanes -----------------------------------------------------------------------------

def test_every_offset_on_a_wide_slope_is_a_lane_offset():
    """SPEC 5.9 Lanes (green today, the centre line is lane 0; it guards the offsets once spread): ten walkers
    on sw 200 (h = 85, lanes 0, +30, -30, +60, -60): from each unit's second on-slope tick its lateral offset is
    within 1e-6 of one of the lane offsets. Every unit mounts, so the check is not empty."""
    res = runmod.run(_crowd(), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    offs = _after_first_tick(res, units)
    assert sum(len(o) for o in offs) > 100
    for i, o in enumerate(offs):
        dev = _nearest_lane_dev(o, LANES_200)
        assert (dev <= TOL).all(), "unit %d offsets off the lane grid: %s" % (i, np.unique(o[dev > TOL])[:5])


def test_units_spread_over_at_least_three_lanes_on_a_wide_slope():
    """SPEC 5.9 Lanes (red today: everyone at offset 0): with sw 200 the ten walkers are on at least 3 different
    lanes at some tick (counted among units on the slope at that tick)."""
    res = runmod.run(_crowd(), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    on, off = _on(res, units), _offsets(res, units)
    most = 0
    for t in range(on.shape[1]):
        lanes = {round(float(v)) for v in off[on[:, t], t]}
        most = max(most, len(lanes))
    assert most >= 3, "at most %d lane(s) in use at once" % most


def test_a_unit_keeps_its_lane_while_on_the_slope():
    """SPEC 5.9 Lanes ("it keeps its lane until it dismounts"; green today, offset 0 throughout): each unit's
    offset is constant over its time on the slope (within 1e-6 of its first on-slope offset)."""
    res = runmod.run(_crowd(), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    on, off = _on(res, units), _offsets(res, units)
    for k in range(10):
        o = off[k][on[k]]
        assert np.abs(o - o[0]).max() <= TOL, "unit %d changed lane: %s" % (k, np.unique(o))


def test_sw_100_has_three_lanes_and_never_uses_a_fourth():
    """SPEC 5.9 Lanes (the spread half is red today): sw 100, h = 35, lanes 0, +30, -30; offsets after each unit's
    first on-slope tick are on that grid (|offset| <= 35 so never +-60), and at least 2 lanes are in use at once."""
    res = runmod.run(_crowd(sw=100.0), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    for o in _after_first_tick(res, units):
        assert (_nearest_lane_dev(o, [0.0, 30.0, -30.0]) <= TOL).all()
    on, off = _on(res, units), _offsets(res, units)
    most = max(len({round(float(v)) for v in off[on[:, t], t]}) for t in range(on.shape[1]))
    assert most >= 2, "only %d lane in use at once" % most


def test_sw_30_has_one_lane_the_axis():
    """SPEC 5.9 Lanes, negative twin (green today and after): sw 30 (h = 0, narrower than two bodies) has the
    single lane at the axis: every on-slope offset is 0 within 1e-6, and all ten still climb."""
    res = runmod.run(_crowd(sw=30.0), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    for o in _after_first_tick(res, units):
        assert (np.abs(o) <= TOL).all()
    assert all(res.unit[i]["alive"] and res.unit[i]["layer"] == 2 for i in units)


@pytest.mark.parametrize("y, lane", [(1024.0, 30.0), (1020.0, 30.0), (1016.0, 30.0), (1014.0, 0.0),
                                     (1010.0, 0.0), (1002.0, 0.0)])
def test_the_lane_is_the_nearest_to_the_lateral_position_at_mounting(y, lane):
    """SPEC 5.9 Lanes ("rounded to the nearest lane"; red today for the +30 rows, the lane 0 rows are the negative
    twins): a lone walker spawned at (1975, y) on layer 1, within the 25 mount reach of the edge centre (lateral
    24, 20, 16, 14, 10, 2), mounts on tick 0 and rides at lane `lane` from its FIRST on-slope tick, and
    dismounts at the top edge at the same offset (SPEC 5.9 "dismounts at the same lateral offset": its first
    off-slope tick is at x = 2575, y = 1000 + lane, layer 2).
    Gap: a lane -30 cannot be reached by position in this preset. The slope's edge centre (y = 1000) lies in the
    cell row that starts at 1000, so a walker coming from below (rows under 1000) first steps up into that row and
    mounts with a small positive lateral offset. Lane -30 is covered by occupancy in the next test."""
    res = runmod.run(_lone(1975.0, y, 1, GOAL_BEYOND), seed=0, trace=True)
    tr = unit_trace(res, 0)
    idx = np.flatnonzero(tr.on_slope)
    assert len(idx) > 0 and idx[0] <= 1
    assert np.abs(tr.y[idx] - (AXIS_Y + lane)).max() <= TOL, "offsets %s, want %s" % (
        np.unique(tr.y[idx] - AXIS_Y), lane)
    after = idx[-1] + 1
    assert tr.alive[after] and tr.layer[after] == 2
    assert abs(tr.x[after] - TOP[0]) <= 1e-3 and abs(tr.y[after] - (AXIS_Y + lane)) <= 1e-3, (
        "dismounted at (%g, %g)" % (tr.x[after], tr.y[after]))


def test_walkers_mounting_together_take_the_nearest_free_lanes_in_order_and_the_extra_one_waits():
    """SPEC 5.9 Lanes ("if another unit on the same slope is already within one body width of the entry point on
    that lane, the nearest free lane instead; if every lane is occupied the walker waits"; red today: all at 0,
    all mount on tick 0): six walkers, one group each, all spawned at (1975, 1005) on layer 1 (lateral 5, inside
    the reach), speed 150, sw 200 (lanes 0, +30, -30, +60, -60). In index order, in the same tick, they take
    lanes 0, +30, -30, +60, -60 (nearest free: 5, 25, 35, 55, 65 away; the lower lane index wins ties). The
    sixth finds all five lanes occupied at the entry and does not mount that tick: its first on-slope tick is
    later than the others' and it then rides in some lane of the grid. No two on-slope units are closer than 29."""
    g = [grp("A", "walker", 1975.0, 1005.0, 1, order="move", goal=list(GOAL_BEYOND)) for _ in range(6)]
    res = runmod.run(_scn(g + [_enemy()], sw=200.0, speed=150.0, run={"max_ticks": 600}), seed=0, trace=True)
    units = list(range(6))
    _all_mounted(res, units)
    firsts = [_first_on(res, i) for i in units]
    lanes = [0.0, 30.0, -30.0, 60.0, -60.0]
    for i in range(5):
        tr = unit_trace(res, i)
        assert firsts[i] == firsts[0], "unit %d mounted at %d, unit 0 at %d" % (i, firsts[i], firsts[0])
        assert abs(tr.y[firsts[i]] - (AXIS_Y + lanes[i])) <= TOL, "unit %d lane %g, want %g" % (
            i, tr.y[firsts[i]] - AXIS_Y, lanes[i])
    assert firsts[5] > firsts[0], "the sixth walker found a free lane at tick %d" % firsts[5]
    t6 = unit_trace(res, 5)
    assert _nearest_lane_dev(t6.y[t6.on_slope][1:] - AXIS_Y, lanes).max() <= TOL
    d = _slope_pair_distances(res, units)
    assert not (d < OVERLAP_BELOW).any()


# ---- test 2: hard bodies on a slope ------------------------------------------------------------

@pytest.mark.parametrize("speed", [80.0, 150.0])
@pytest.mark.parametrize("sw", [200.0, 30.0])
def test_no_two_units_on_the_slope_are_closer_than_29(sw, speed):
    """SPEC 5.9 Bodies on a slope (red today: they stack): ten walkers; at no tick are two units on the slope
    (bit2) closer than 29. Non-vacuous: at least two units are on the slope together at some tick, and all ten
    climb to layer 2 (the queue does not deadlock)."""
    res = runmod.run(_crowd(sw=sw, speed=speed), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    assert _on(res, units).sum(axis=0).max() >= 2
    d = _slope_pair_distances(res, units)
    close = np.flatnonzero((d < OVERLAP_BELOW).any(axis=0))
    assert len(close) == 0, "pairs on the slope closer than 29 at ticks %s (min %.2f)" % (
        close[:5], np.nanmin(d))
    assert all(res.unit[i]["alive"] and res.unit[i]["layer"] == 2 for i in units)


def _queue_scn(sw):
    """Front walker (1900, 1000) and rear walker (1840, 1000) on layer 1, speed 80, both MOVE to the slope
    midpoint (2275, 1000): each climbs and stops on the slope on arrival (module docstring). The front mounts
    about tick 19, the rear about 15 ticks later when the front is 60 up the slope (free entry)."""
    g = [grp("A", "walker", 1900.0, AXIS_Y, 1, order="move", goal=list(GOAL_ON_SLOPE)),
         grp("A", "walker", 1840.0, AXIS_Y, 1, order="move", goal=list(GOAL_ON_SLOPE)),
         _enemy()]
    return _scn(g, sw=sw, speed=80.0, run={"max_ticks": 600})


def test_front_unit_stops_on_the_slope_and_the_rear_queues_behind_it_in_a_single_lane():
    """SPEC 5.9 Bodies on a slope (red today: both ride to the goal and stack, distance ~4): sw 30 (one lane),
    the front unit stops on the slope at the goal (non-vacuous: from some tick on its x is constant, still on
    the slope, x within 22.5 of 2275); the rear never passes it (rear x <= front x - 29 on every tick both are
    on the slope), stays on the slope, and the two are never closer than 29."""
    res = runmod.run(_queue_scn(30.0), seed=0, trace=True)
    f, r = unit_trace(res, 0), unit_trace(res, 1)
    assert f.on_slope[-1] and r.on_slope[-1], "front/rear not both on the slope at the end"
    assert abs(f.x[-1] - GOAL_ON_SLOPE[0]) <= 1.5 * R + 1e-6, "front did not stop at the goal: x %g" % f.x[-1]
    assert np.ptp(f.x[-100:]) <= TOL and np.ptp(f.y[-100:]) <= TOL, "front still moving at the end"
    both = f.on_slope & r.on_slope
    assert both.sum() > 100
    assert (f.x[both] - r.x[both] >= OVERLAP_BELOW).all(), "rear within 29 of (or past) the front, e.g. at ticks %s" % (
        np.flatnonzero(both & (f.x - r.x < OVERLAP_BELOW))[:5])
    d = np.hypot(f.x - r.x, f.y - r.y)
    assert (d[both] >= OVERLAP_BELOW).all()


def test_front_stopped_on_a_wide_slope_never_has_a_unit_within_29():
    """SPEC 5.9 Bodies on a slope (red today): the same scenario on sw 200. The rear may queue in the front's
    lane or take another lane (SPEC 5.9, either); whichever, the two on-slope units are never closer than 29.
    Non-vacuous: the front stops on the slope at the goal and both are on the slope together for 100+ ticks."""
    # On a wide slope the front unit mounts in the lane nearest where it arrives (SPEC 5.9: here +30, not 0: it
    # arrives about 15 off the axis), and a goal on the axis can never be reached from another lane (the arrival
    # radius is 22.5), so the unit would climb past it. So: a first run finds the lane the front unit takes, and the
    # run under test gives it a goal in that lane. (The first version assumed lane 0: a test defect found by the
    # slope-bodies builder.)
    probe = runmod.run(_queue_scn(200.0), seed=0, trace=True)
    p0 = unit_trace(probe, 0)
    first = int(np.flatnonzero(p0.on_slope)[0])
    lane = 30.0 * round((p0.y[first] - AXIS_Y) / 30.0)
    scn = _queue_scn(200.0)
    scn["groups"][0]["goal"] = [GOAL_ON_SLOPE[0], AXIS_Y + lane]
    res = runmod.run(scn, seed=0, trace=True)
    f, r = unit_trace(res, 0), unit_trace(res, 1)
    assert f.on_slope[-1] and abs(f.x[-1] - GOAL_ON_SLOPE[0]) <= 1.5 * R + 1e-6
    both = f.on_slope & r.on_slope
    assert both.sum() > 100
    d = np.hypot(f.x - r.x, f.y - r.y)
    assert (d[both] >= OVERLAP_BELOW).all(), "closer than 29 at ticks %s (min %.2f)" % (
        np.flatnonzero(both & (d < OVERLAP_BELOW))[:5], d[both].min())


def test_a_lone_stopped_unit_on_the_slope_is_a_positive_control_for_the_stop_trick():
    """Positive control for tests 2b/2c (green today): a lone walker with the MOVE goal on the slope midpoint
    does stop on the slope, so the scenario really makes a unit stand there."""
    res = runmod.run(_lone(1900.0, AXIS_Y, 1, GOAL_ON_SLOPE, sw=30.0, speed=80.0, run={"max_ticks": 400}),
                     seed=0, trace=True)
    u = unit_trace(res, 0)
    assert u.on_slope[-1] and abs(u.x[-1] - GOAL_ON_SLOPE[0]) <= 1.5 * R + 1e-6
    assert np.ptp(u.x[-100:]) <= TOL


# ---- test 3: width matters (the E3 bug) --------------------------------------------------------

def _mount_span_and_last_dismount(sw):
    res = runmod.run(_crowd(sw=sw, speed=80.0), seed=0, trace=True)
    units = list(range(10))
    _all_mounted(res, units)
    firsts = [_first_on(res, i) for i in units]
    return max(firsts) - min(firsts), _last_on(res, units) + 1


def test_a_narrow_slope_strings_the_climbers_out_more_than_a_wide_one():
    """SPEC 5.9 Lanes / Bodies on a slope (red today: sw changes nothing): same ten walkers at speed 80; the time
    from the first unit's first on-slope tick to the last unit's is strictly larger with sw 30 (single file,
    one mount per 30 units of axis, about 8 ticks at speed 80) than with sw 200 (five lanes abreast)."""
    narrow, _ = _mount_span_and_last_dismount(30.0)
    wide, _ = _mount_span_and_last_dismount(200.0)
    assert narrow > wide, "mount span: sw 30 -> %d ticks, sw 200 -> %d ticks" % (narrow, wide)


def test_a_wide_slope_clears_sooner_than_a_narrow_one():
    """SPEC 5.9 (red today): the tick of the last dismount (the last tick any unit has bit2, plus one) is strictly
    earlier with sw 200 than with sw 30 at equal speed."""
    _, narrow = _mount_span_and_last_dismount(30.0)
    _, wide = _mount_span_and_last_dismount(200.0)
    assert wide < narrow, "last dismount: sw 200 -> tick %d, sw 30 -> tick %d" % (wide, narrow)


def test_single_file_mounts_are_spaced_by_a_body_of_axis():
    """SPEC 5.9 Lanes (red today): on sw 30 (one lane) a walker mounts only when no unit on the slope is within 30
    of the entry along the axis, and a unit climbs 4 per tick at speed 80, so consecutive first-mount ticks are at
    least 7 apart (30 / 4 = 7.5)."""
    res = runmod.run(_crowd(sw=30.0, speed=80.0), seed=0, trace=True)
    firsts = sorted(_first_on(res, i) for i in range(10))
    gaps = np.diff(firsts)
    assert gaps.min() >= 7, "first-mount gaps %s" % gaps.tolist()


# ---- test 4: lanes pass, one lane does not -----------------------------------------------------

def _crossing_scn(y_up, y_down, sw, speed=150.0, stale=3000, max_ticks=3000):
    """Side A up-mover at (1975, y_up) on layer 1 ordered to the plateau; side A down-mover at (2575, y_down) on
    layer 2 ordered to the ground point (1500, 1000). Both are within the 25 mount reach of their edge centre, so
    both mount on tick 0 (lane from the lateral position) and meet near the midline."""
    g = [grp("A", "walker", 1975.0, y_up, 1, order="move", goal=list(GOAL_BEYOND)),
         grp("A", "walker", 2575.0, y_down, 2, order="move", goal=[1500.0, AXIS_Y]),
         _enemy()]
    return _scn(g, sw=sw, speed=speed, run={"stalemate_ticks": stale, "max_ticks": max_ticks})


def test_units_in_different_lanes_pass_each_other_and_both_complete():
    """SPEC 5.9 Bodies on a slope ("in different lanes they pass"; red today: both on the axis, distance 0 where
    they cross): the up-mover in lane +30 (spawn y 1020) and the down-mover in lane 0 (spawn y 1005) cross near
    the midline at distance >= 29 (their lanes are 30 apart), and both complete: the up-mover ends alive on
    layer 2, the down-mover alive on layer 1, each with a layer change. Non-vacuous: they swap x order.
    Gap: the brief's lanes +30 and -30 are not reachable by position (see the lane-choice test), so +30 and 0."""
    res = runmod.run(_crossing_scn(1020.0, 1005.0, 200.0), seed=0, trace=True)
    up, down = unit_trace(res, 0), unit_trace(res, 1)
    assert res.unit[0]["alive"] and res.unit[0]["layer"] == 2 and res.unit[0]["transitions"] >= 1
    assert res.unit[1]["alive"] and res.unit[1]["layer"] == 1 and res.unit[1]["transitions"] >= 1
    both = up.on_slope & down.on_slope
    assert both.sum() > 20
    assert np.abs(up.y[up.on_slope] - (AXIS_Y + 30.0)).max() <= TOL
    assert np.abs(down.y[down.on_slope] - AXIS_Y).max() <= TOL
    d = np.hypot(up.x - down.x, up.y - down.y)
    assert (d[both] >= OVERLAP_BELOW).all(), "closest approach on the slope %.2f" % d[both].min()
    assert (both & (up.x > down.x)).any(), "they never crossed"


def test_units_in_the_same_lane_do_not_pass_and_the_run_is_a_stalemate():
    """SPEC 5.9 ("two units meeting head-on in one lane block each other and deadlock (ends in a stalemate)"; red
    today: they pass through each other and both dismount): sw 30 (one lane), the up-mover at (1975, 1000) and
    the down-mover at (2575, 1000) mount on tick 0 and meet. The deadlock, documented: both end the run still on
    the slope (bit2 at the last tick, never dismounted), the up-mover's x is below the down-mover's at every tick
    both are on the slope, they are never closer than 29, and the result is WIN_STALEMATE (600 quiet ticks)."""
    res = runmod.run(_crossing_scn(AXIS_Y, AXIS_Y, 30.0, stale=600, max_ticks=1500), seed=0, trace=True)
    up, down = unit_trace(res, 0), unit_trace(res, 1)
    assert up.on_slope[-1] and down.on_slope[-1], "a unit left the slope: it passed (or never mounted)"
    both = up.on_slope & down.on_slope
    assert both.sum() > 400
    assert (up.x[both] < down.x[both]).all(), "the units passed each other"
    d = np.hypot(up.x - down.x, up.y - down.y)
    assert (d[both] >= OVERLAP_BELOW).all()
    assert res.winner == WIN_STALEMATE


# ---- test 5: timing unchanged ------------------------------------------------------------------

@pytest.mark.parametrize("speed, ticks", [(150.0, 80), (40.0, 300)])
@pytest.mark.parametrize("sw, y", [(200.0, AXIS_Y), (200.0, 1020.0), (30.0, 1020.0)])
def test_a_lone_walker_takes_the_r_004_07_time_whatever_its_lane(speed, ticks, sw, y):
    """SPEC 5.9 R-004-07 (green today, must stay green): the number of on-slope ticks of a lone walker on sl 600
    is 80 at speed 150 and 300 at speed 40 (+-1), in lane 0 or in lane +30 (spawn y 1020), on a wide or a
    one-lane slope. The lateral offset does not change the travel time."""
    res = runmod.run(_lone(1975.0, y, 1, GOAL_BEYOND, sw=sw, speed=speed, run={"max_ticks": 800}),
                     seed=0, trace=True)
    n = int(unit_trace(res, 0).on_slope.sum())
    assert abs(n - ticks) <= 1, "%d on-slope ticks, want %d" % (n, ticks)
    assert res.unit[0]["layer"] == 2


# ---- test 6: off-slope units never block or are blocked ----------------------------------------

@pytest.mark.parametrize("stander", [(1975.0, 1000.0), (1975.0, 1020.0)])
def test_a_standing_unit_at_the_entry_neither_blocks_the_climber_nor_is_pushed(stander):
    """SPEC 5.9 "Mounting is never blocked by bodies", "units off the slope never block it and are never blocked
    by it", 5.10 slope mouths (green today, a guard): a friendly walker holds on layer 1 at the slope's foot, on
    the edge centre (1975, 1000) or beside it (1975, 1020), both off the slope and inside the 40 mouth. A walker
    from (1900, 1000) mounts, climbs in 80 +-1 ticks at speed 150 and ends on layer 2, in lane 0 (the standing
    unit does not push it to another lane); the standing unit never moves."""
    g = [grp("A", "walker", stander[0], stander[1], 1, order="hold"),
         grp("A", "walker", 1900.0, AXIS_Y, 1, order="move", goal=list(GOAL_BEYOND)),
         _enemy()]
    res = runmod.run(_scn(g, speed=150.0, run={"max_ticks": 600}), seed=0, trace=True)
    c, s = unit_trace(res, 1), unit_trace(res, 0)
    assert res.unit[1]["alive"] and res.unit[1]["layer"] == 2 and res.unit[1]["transitions"] >= 1
    assert abs(int(c.on_slope.sum()) - 80) <= 1
    assert np.abs(c.y[c.on_slope] - AXIS_Y).max() <= TOL
    assert not s.on_slope.any()
    assert np.ptp(s.x) <= TOL and np.ptp(s.y) <= TOL, "the standing unit was pushed"


def test_a_unit_standing_on_the_plateau_above_the_slope_does_not_stop_a_climber():
    """SPEC 5.9 (green today, a guard): a friendly walker holds on layer 2 at (2275, 1000), over the slope's
    midpoint but off the slope. The climber passes through its xy without being refused or delayed (80 +-1
    on-slope ticks at speed 150) and the holder is not pushed."""
    g = [grp("A", "walker", 2275.0, AXIS_Y, 2, order="hold"),
         grp("A", "walker", 1900.0, AXIS_Y, 1, order="move", goal=list(GOAL_BEYOND)),
         _enemy()]
    res = runmod.run(_scn(g, speed=150.0, run={"max_ticks": 600}), seed=0, trace=True)
    c, s = unit_trace(res, 1), unit_trace(res, 0)
    assert res.unit[1]["alive"] and res.unit[1]["layer"] == 2
    assert abs(int(c.on_slope.sum()) - 80) <= 1
    assert np.ptp(s.x) <= TOL and np.ptp(s.y) <= TOL


def test_a_holder_at_the_edge_centre_does_not_delay_the_climber():
    """SPEC 5.9 (negative twin of the on-slope blocking, green today): a friendly walker holds on layer 1 at the
    edge centre (1975, 1000), off the slope, while a second walker climbs from (1900, 1000) in lane 0; its
    on-slope tick count is the lone-walker 80 +-1 (a stopped unit ON the slope would queue it, test 2b)."""
    g = [grp("A", "walker", 1975.0, AXIS_Y, 1, order="hold"),
         grp("A", "walker", 1900.0, AXIS_Y, 1, order="move", goal=list(GOAL_BEYOND)),
         _enemy()]
    res = runmod.run(_scn(g, speed=150.0, run={"max_ticks": 600}), seed=0, trace=True)
    c = unit_trace(res, 1)
    assert abs(int(c.on_slope.sum()) - 80) <= 1


# ---- test 7: the E3 outcome moves --------------------------------------------------------------

def _e3_scn():
    top = TOP[0]
    dx, dy = top + 300.0, AXIS_Y
    g = [grp("A", "walker", 900.0, AXIS_Y, 1, count=10, formation="box", cols=5, spacing=31.0, facing=0.0,
             order="attack_move", goal=[dx, dy]),
         grp("B", "walker", dx, dy, 2, count=10, formation="box", cols=5, spacing=31.0, facing=180.0,
             order="hold", goal=[dx, dy])]
    scn = _scn(g, sw=200.0, speed=80.0, rules={"spawn_jitter": 10.0, "chase_when_idle": 1},
               run={"stalemate_ticks": 3000, "max_ticks": 6000})
    return scn


def test_e3_attackers_no_longer_win_with_the_stacking_advantage():
    """SPEC 5.9 (README 6.2 E3; red today: about 7.3 survivors, the climbers stack on one point and arrive as a
    blob): 10 walking attackers on layer 1 attack-move to 10 holding walking defenders on layer 2, 300 beyond
    the top edge, default rules except chase_when_idle 1, sl 600, speed 80, spawn_jitter 10 (the lab default):
    over seeds 0..19 the mean attacker survivors is below 6.0."""
    scn = _e3_scn()
    surv = [runmod.run(scn, seed=s).survivors[0] for s in range(20)]
    mean = sum(surv) / len(surv)
    assert mean < 6.0, "mean attacker survivors %.2f (per seed %s)" % (mean, surv)


# ---- test 8: determinism -----------------------------------------------------------------------

def test_a_crowded_climb_is_byte_identical_for_the_same_seed():
    """SPEC 9 / E-01 R-004-05 (green today, must stay): the crowded climb twice with the same seed gives identical
    result bytes and trace bytes; the climb really happened (units on the slope)."""
    a = runmod.run(_crowd(rules={"spawn_jitter": 10.0}), seed=3, trace=True)
    b = runmod.run(_crowd(rules={"spawn_jitter": 10.0}), seed=3, trace=True)
    assert a.raw == b.raw
    assert np.ascontiguousarray(a.trace).tobytes() == np.ascontiguousarray(b.trace).tobytes()
    assert _on(a, list(range(10))).any()


@pytest.mark.parametrize("sw", [200.0, 30.0])
def test_o0_and_o2_libraries_agree_on_a_crowded_climb(sw):
    """SPEC 9 (green today, must stay): the O0 and O2 builds give identical result bytes and trace bytes on the
    crowded climb, for lanes (sw 200) and the single file (sw 30)."""
    for seed in (0, 1):
        a = runmod.run(_crowd(sw=sw, rules={"spawn_jitter": 10.0}), seed=seed, trace=True, lib="O0")
        b = runmod.run(_crowd(sw=sw, rules={"spawn_jitter": 10.0}), seed=seed, trace=True, lib="O2")
        assert a.raw == b.raw, "raw differs O0 vs O2 at seed %d" % seed
        assert np.ascontiguousarray(a.trace).tobytes() == np.ascontiguousarray(b.trace).tobytes()
