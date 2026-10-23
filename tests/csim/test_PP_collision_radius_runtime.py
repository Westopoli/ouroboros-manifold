# Rule pins: R-097-03@6f75ba, R-097-09@4d4fa7, R-097-10@a759df, R-099-04@8a3792
"""LAB-REV2-E3: the runtime unit collision radius (Q-LAB-02 (a), Westley 2026-10-06; Architect 2026-10-13 under that
ruling, widening A133 Q-C6 "collision pass only"; docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md ruling 15).

`OM_TP_UNIT_COLLISION_RADIUS` (parameter 8, default 15, range 0 to OM_GRID_CELL_SIZE / 2) is stored and read back
today but read by nothing: csrc/tactical_move.c uses the compile-time OM_UNIT_COLLISION_RADIUS everywhere. Ruling 15:
the runtime value is the body size the sim uses, at the collision pass, the steering probe, the navmesh margins and
the arrival tolerances. Spawn spacing (mission.c, enemy_macro.c, unit.c) and the broad-phase grid layout stay
compile-time and are not tested here.

Rules proved: ALG-68 and spec ruling 15 (the 40 wu steering probe: gather and blocked test at two collision radii; the
blocking radius is code-derived, om_move_probe_clear in csrc/tactical_move.c, ALG-68 only says "within blocking radius"
and R-097-03 only that a unit on the layer blocks the probe),
R-097-10 (the push pass separates a pair to two collision radii), R-099-04 (arrival is within 1.5 collision radii of
a destination), and ruling 15 itself. Every test sets the radius with om_tactical_set_param before the first step.

Red today, all for the same stated reason: the parameter is read nowhere, so a run at radius 10 or 30 is
indistinguishable from a run at 15 (the gap scene's three trajectories hash identically).

Controls (green today and after): radius 15 set explicitly, or never set, reproduces the trace hash recorded below
as TRACE_R15; the gap crossing at radius 15 passes through the gap; the probe scene at radius 15 deflects.

How TRACE_R15 was recorded: `_trace_hash(lib, None)` run on origin/main at 37858c8e with no csrc change (the
parameter unset, so the compile-time 15), 300 ticks of the mixed scene below, sha256 over the little-endian double
x, y of every unit in id order after every tick. Determinism is a contract (no platform transcendentals), so the
constant is portable. Not recorded from a modified tree: if it ever changes, a landing changed the radius-15 path.

Sites covered by a behaviour test: pair push (2 r), arrival (1.5 r), probe blocked and probe gather (2 r; the radius-30
probe scene fails for a builder who scales either alone), the navmesh margins of om_move_leave_blocked and
om_move_nearest_reachable, the route-waypoint reach (2.0 r) and the routed move's last-leg arrival (2.0 r). Each was
checked green with a compile-time stand-in radius of 10 or 30 (OM_UNIT_COLLISION_RADIUS in om_constants.h).

Known holes (no behaviour test): list reach (4 r), collision slack (r), collision mark and sweep reach (2 r), the
sure-blocked margin test (a fast path in front of the probe-blocked test; leaving it at 15 changes no result), and
the group-centroid arrival (tol 1.5 r, shadowed by each unit's own 1.5 r arrival). Where the gap scene at radius 30
would fail only because one of these was missed, that is the builder's failure to find, not a hole in a test.
"""
import ctypes
import hashlib
import math
import struct

import pytest

from conftest import OMFeature, OMTacParam

RAIDER = 0
FACTION = 0
ENEMY = 1   # TD-VG-E-idle-own (test-defect, assumption-changed by the R-097-03/R-097-10 rewrite, Architect 2026-10-23): idle blockers are enemies
LAYER = 0
RADIUS_PARAM = OMTacParam.UNIT_COLLISION_RADIUS
DEFAULT_RADIUS = 15.0
STEP_TOL = 0.05   # numeric slack for the C's cheap trig, not a rule threshold
ARRIVAL_MULT = 1.5   # R-099-04 and csrc/om_constants.h OM_ARRIVAL_TOLERANCE_MULT

# Recorded on the unmodified tree (see the module docstring). Green today.
TRACE_R15 = "9266aad512c513ca24883b28e4cca87963685878a14136619d98caf703b4c5a2"


def _world(lib, radius):
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(1))
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    if radius is not None:
        assert lib.om_tactical_set_param(w, RADIUS_PARAM, float(radius)) == 0
        assert lib.om_tactical_get_param(w, RADIUS_PARAM) == float(radius)
    return w


def _spawn(lib, w, x, y):
    return lib.om_unit_spawn(w, RAIDER, FACTION, x, y, LAYER)


def _spawn_enemy(lib, w, x, y):
    return lib.om_unit_spawn(w, RAIDER, ENEMY, x, y, LAYER)


def _pos(lib, w, u):
    return tuple(lib.om_unit_get_pos(w, u))


# ---- the gap scene: two blockers 80 wu apart, a unit told to cross the line between them -------------------------

BLOCK_A = (1000.0, 1000.0)
BLOCK_B = (1080.0, 1000.0)   # 80 wu from A
LINE_Y = 1000.0


def _gap_run(lib, radius, ticks=300):
    """Returns (x where the mover first crosses y = 1000 or None, final mover pos, the per-tick trajectory)."""
    w = _world(lib, radius)
    try:
        _spawn_enemy(lib, w, *BLOCK_A)
        _spawn_enemy(lib, w, *BLOCK_B)
        m = _spawn(lib, w, 1040.0, 1200.0)           # on the perpendicular bisector, 200 wu above the line
        lib.om_command_move(w, m, 1040.0, 800.0)      # 200 wu below it: the straight path runs through the gap
        crossing_x, prev, traj = None, _pos(lib, w, m), []
        for _ in range(ticks):
            lib.om_tactical_step(w)
            cur = _pos(lib, w, m)
            traj.append(cur)
            if crossing_x is None and prev[1] > LINE_Y >= cur[1]:
                crossing_x = cur[0]
            prev = cur
        return crossing_x, prev, traj
    finally:
        lib.om_world_free(w)


def _through_the_gap(crossing_x):
    return crossing_x is not None and BLOCK_A[0] < crossing_x < BLOCK_B[0]


def test_ruling_15_radius_10_unit_crosses_between_blockers_80_apart(lib):
    """Radius 10 (diameter 20): the gap midpoint is 40 from each blocker, so the unit walks through it.
    Green today too (15 also fits); it is the half of the pair that radius 30 must differ from."""
    crossing_x, final, _ = _gap_run(lib, 10.0)
    assert _through_the_gap(crossing_x), f"radius 10: crossed the line at x={crossing_x}, final {final}"


def test_ruling_15_radius_30_unit_cannot_cross_between_blockers_80_apart(lib):
    """Radius 30 (diameter 60): the midpoint is 40 from each blocker, under the 60 a body needs, so the unit
    may not pass between them (it is pushed back and steers round an end, or stops). Red today: the parameter is
    read nowhere, so the unit crosses at x=1040 exactly as at radius 10."""
    crossing_x, final, _ = _gap_run(lib, 30.0)
    assert not _through_the_gap(crossing_x), f"radius 30: crossed between the blockers at x={crossing_x}, final {final}"


def test_ruling_15_gap_trajectory_depends_on_the_radius(lib):
    """The weakest form of 'the parameter is read': radius 10 and radius 30 give different trajectories. Red today
    (identical)."""
    _, _, t10 = _gap_run(lib, 10.0)
    _, _, t30 = _gap_run(lib, 30.0)
    assert t10 != t30, "radius 10 and radius 30 gave the same 300-tick trajectory: the parameter is read nowhere"


def test_ruling_15_control_radius_15_crosses_between_the_blockers(lib):
    """Control (green today and after): the default radius passes through the 80 wu gap, set or unset, and a
    positive control for _through_the_gap."""
    for radius in (None, DEFAULT_RADIUS):
        crossing_x, final, _ = _gap_run(lib, radius)
        assert _through_the_gap(crossing_x), f"radius {radius}: crossed at x={crossing_x}, final {final}"


# ---- control: radius 15 is byte-identical to today's trace -------------------------------------------------------

def _trace_hash(lib, radius, ticks=300):
    """A mixed scene touching the collision pass, the probe and arrival: the gap scene; an idle overlapping pair;
    a 3 x 2 group move through overlap; a lone mover that arrives. sha256 of every unit's x, y after every tick."""
    w = _world(lib, radius)
    try:
        ids = [_spawn(lib, w, *BLOCK_A), _spawn(lib, w, *BLOCK_B)]
        m = _spawn(lib, w, 1040.0, 1200.0)
        ids.append(m)
        lib.om_command_move(w, m, 1040.0, 800.0)
        ids += [_spawn(lib, w, 2000.0, 1000.0), _spawn(lib, w, 2005.0, 1003.0)]
        grp = [_spawn(lib, w, 1500.0 + 12.0 * (i % 3), 1500.0 + 12.0 * (i // 3)) for i in range(6)]
        ids += grp
        arr = (ctypes.c_uint32 * len(grp))(*grp)
        lib.om_command_group_move(w, arr, len(grp), 1500.0, 1900.0)
        lone = _spawn(lib, w, 500.0, 500.0)
        ids.append(lone)
        lib.om_command_move(w, lone, 500.0, 700.0)
        h = hashlib.sha256()
        for _ in range(ticks):
            lib.om_tactical_step(w)
            for u in ids:
                h.update(struct.pack("<dd", *_pos(lib, w, u)))
        return h.hexdigest()
    finally:
        lib.om_world_free(w)


def test_control_radius_15_trace_is_byte_identical_to_the_recorded_trace(lib):
    """The default (unset) and an explicit 15 both reproduce TRACE_R15. Green today (parameter read nowhere) and
    the fence the builder may not cross: substituting the runtime value must not change a bit at 15."""
    assert _trace_hash(lib, None) == TRACE_R15, "unset radius: trace differs from the one recorded on main"
    assert _trace_hash(lib, DEFAULT_RADIUS) == TRACE_R15, "radius 15 set explicitly: trace differs"


def test_control_the_trace_hash_sees_a_radius_change(lib):
    """Positive control for the hash above: radius 30 gives a different trace. Red today for the stated reason
    (the parameter is read nowhere, so it equals TRACE_R15), green once it is read."""
    assert _trace_hash(lib, 30.0) != TRACE_R15, "radius 30 hashes like radius 15: the parameter is read nowhere"


# ---- site family: pair push spacing (the collision pass, R-097-10) ----------------------------------------------

@pytest.mark.parametrize("radius", [10.0, 30.0])
def test_R_097_10_idle_pair_is_pushed_apart_to_two_radii(lib, radius):
    """Two idle units 5 wu apart: the stationary-pair split (R-097-10, ALG-68) ends with them 2 x radius apart,
    20 at radius 10 and 60 at radius 30. Red today: they end 30 apart whatever the radius."""
    w = _world(lib, radius)
    try:
        a = _spawn(lib, w, 1000.0, 1000.0)
        b = _spawn(lib, w, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        pa, pb = _pos(lib, w, a), _pos(lib, w, b)
        assert math.hypot(pb[0] - pa[0], pb[1] - pa[1]) == pytest.approx(2.0 * radius, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


def test_R_097_10_control_idle_pair_at_radius_15_ends_30_apart(lib):
    """Control (green today and after): the same scene at the default ends 30 apart."""
    w = _world(lib, DEFAULT_RADIUS)
    try:
        a = _spawn(lib, w, 1000.0, 1000.0)
        b = _spawn(lib, w, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        pa, pb = _pos(lib, w, a), _pos(lib, w, b)
        assert math.hypot(pb[0] - pa[0], pb[1] - pa[1]) == pytest.approx(30.0, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


# ---- site family: arrival tolerance (R-099-04) ------------------------------------------------------------------

def _arrival(lib, radius):
    """A lone unit walks 400 wu straight to a destination. Returns (distance to the destination at the last tick
    it had not arrived, distance where it stopped)."""
    w = _world(lib, radius)
    try:
        u = _spawn(lib, w, 1000.0, 1400.0)
        dest = (1000.0, 1000.0)
        lib.om_command_move(w, u, *dest)
        dists = []
        for _ in range(200):
            lib.om_tactical_step(w)
            p = _pos(lib, w, u)
            dists.append(math.hypot(p[0] - dest[0], p[1] - dest[1]))
        stop = dists[-1]
        assert dists[-2] == stop, "scene error: the unit was still moving after 200 ticks"
        last_moving = next(d for d in reversed(dists) if d != stop)
        return last_moving, stop
    finally:
        lib.om_world_free(w)


@pytest.mark.parametrize("radius", [10.0, 30.0])
def test_R_099_04_unit_arrives_within_one_and_a_half_radii(lib, radius):
    """A unit stops the first tick it is within 1.5 x radius of its destination: the step before it stopped it was
    at or beyond 1.5 x radius, where it stopped it is inside. Radius 10: 15; radius 30: 45. Red today: 22.5 for
    both (the unit stops 17.5 away at either radius)."""
    last_moving, stop = _arrival(lib, radius)
    tol = ARRIVAL_MULT * radius
    assert stop < tol, f"radius {radius}: stopped {stop} from the destination, tolerance {tol}"
    assert last_moving >= tol, f"radius {radius}: was already inside {tol} ({last_moving}) one tick before stopping"


def test_R_099_04_control_arrival_at_radius_15_is_22_5(lib):
    """Control (green today and after): at 15 the unit stops inside 22.5 and not before."""
    last_moving, stop = _arrival(lib, DEFAULT_RADIUS)
    assert stop < 22.5 <= last_moving, f"stop {stop}, one tick before {last_moving}"


# ---- site family: steering probe and blocked test (R-097-03) ----------------------------------------------------

def _pass_by(lib, radius, offset):
    """A unit walks +y past an idle blocker `offset` wu to its side (the blocker at x = 1000, the walker on
    x = 1000 + offset). Returns the largest sideways drift of the walker from its straight line."""
    w = _world(lib, radius)
    try:
        _spawn_enemy(lib, w, 1000.0, 1200.0)
        m = _spawn(lib, w, 1000.0 + offset, 1000.0)
        lib.om_command_move(w, m, 1000.0 + offset, 1400.0)
        drift = 0.0
        for _ in range(120):
            lib.om_tactical_step(w)
            drift = max(drift, abs(_pos(lib, w, m)[0] - (1000.0 + offset)))
        return drift
    finally:
        lib.om_world_free(w)


def test_R_097_03_probe_ignores_a_unit_outside_two_radii(lib):
    """Radius 10: a blocker 25 wu abeam is outside the 20 wu body-to-body distance, so neither the 40 wu probe
    (R-097-03) nor the push pass (R-097-10) touches the walker: it stays on its line. Red today: at 15 the 25 wu
    pass is inside 30, the probe is blocked and the walker veers (and is pushed)."""
    assert _pass_by(lib, 10.0, 25.0) < STEP_TOL


def test_R_097_03_control_probe_deflects_a_unit_inside_two_radii(lib):
    """Control (green today and after): at 15 the same 25 wu pass is inside 30 and the walker veers, so a
    straight pass above is a measurement and not a scene that never deflects."""
    assert _pass_by(lib, DEFAULT_RADIUS, 25.0) > 1.0


def _probe_ahead(lib, radius):
    """A blocker stands 90 wu dead ahead of a walker; the walker takes one step. The 40 wu probe point is 50 wu from
    the blocker. Returns the walker's sideways drift |x - 1000| after the step."""
    w = _world(lib, radius)
    try:
        _spawn_enemy(lib, w, 1000.0, 1090.0)
        m = _spawn(lib, w, 1000.0, 1000.0)
        lib.om_command_move(w, m, 1000.0, 1400.0)
        lib.om_tactical_step(w)
        return abs(_pos(lib, w, m)[0] - 1000.0)
    finally:
        lib.om_world_free(w)


def test_R_097_03_probe_is_blocked_by_a_unit_inside_two_radii_at_radius_30(lib):
    """Radius 30: the probe point 40 wu ahead is 50 wu from the blocker, inside 2 x 30 = 60 (outside the radius-15
    figure 30), so the first step sweeps off the straight line. The blocker is 90 wu away, so no push is involved:
    only the probe gather (the blocker must be gathered, 40 + 2 r out) and the blocked test (2 r) see it. Red today
    (the walker goes straight), and it stays red for a builder who scales the blocked test but not the probe
    gather radius, or the gather but not the blocked test. The blocking radius is code-derived (ALG-68 says only
    'within blocking radius'; R-097-03 says a unit on the layer blocks the probe): om_move_probe_clear in
    csrc/tactical_move.c, two collision radii. Spec ruling 15: 'probe gather and blocked'."""
    assert _probe_ahead(lib, 30.0) > 1.0


def test_R_097_03_control_probe_goes_straight_at_radius_15_with_the_blocker_90_ahead(lib):
    """Control (green today and after): at 15 the probe point is 50 wu from the blocker, outside 30, so the same
    scene walks straight; the test above measures a deflection and not a scene that always veers."""
    assert _probe_ahead(lib, DEFAULT_RADIUS) < STEP_TOL
    assert _probe_ahead(lib, None) < STEP_TOL


# ---- site family: navmesh margins and route-waypoint arrival (terrain scenes, built with om_map_block_rect) --------
# The scenes follow tests/csim/test_PP_move_route.py: a 2000 x 2000 canvas, the 100 wu route grid, a wall in column 5.

CANVAS = 2000.0
WALL_FULL = (510.0, 10.0, 590.0, 1990.0)    # column 5, every row: cuts the map
WALL_LOW = (510.0, 10.0, 590.0, 790.0)      # column 5, rows 0..7: open above y = 800
ALL_LAYERS = (0, 4)


def _terrain_world(lib, radius, wall):
    w = _world(lib, radius)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_map_block_rect(w, *wall, *ALL_LAYERS) == 0
    return w


@pytest.mark.parametrize("radius, expect", [(10.0, (490.0, 420.0)), (30.0, (470.0, 430.0))])
def test_ruling_15_navmesh_margin_unit_inside_a_blocked_cell_is_moved_out_by_the_radius(lib, radius, expect):
    """R-097-09 with the margin of ruling 15 (csrc/tactical_move.c om_move_leave_blocked: 'the nearest point of that
    cell at least a collision radius inside it'). An idle unit at (520, 420) is inside the wall (column 5, row 4); the
    nearest open cell is column 4, row 4 (x 400..500, y 400..500) and the unit lands at x = 500 - r, y = clamped to
    [400 + r, 500 - r]: (490, 420) at radius 10 and (470, 430) at radius 30. Red today: (485, 420) at both."""
    w = _terrain_world(lib, radius, WALL_LOW)
    try:
        u = _spawn(lib, w, 520.0, 420.0)
        lib.om_tactical_step(w)
        assert _pos(lib, w, u) == pytest.approx(expect, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


def test_ruling_15_navmesh_margin_control_radius_15_unit_lands_at_485_420(lib):
    """Control (green today and after): at 15 the same scene lands at (485, 420)."""
    w = _terrain_world(lib, DEFAULT_RADIUS, WALL_LOW)
    try:
        u = _spawn(lib, w, 520.0, 420.0)
        lib.om_tactical_step(w)
        assert _pos(lib, w, u) == pytest.approx((485.0, 420.0), abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


def _unreachable_destination(lib, radius):
    """A wall the full height of the canvas; a unit at (300, 400) ordered to (900, 400). The destination has no route
    and is replaced (csrc/tactical_move.c om_move_nearest_reachable) by the nearest reachable point, a radius inside
    its cell. Ties go to the lower cell id, so the cell is column 4, row 3 (x 400..500, y 300..400): the point is
    (500 - r, 400 - r). Read back with om_unit_get_destination after the first tick plans the route."""
    w = _terrain_world(lib, radius, WALL_FULL)
    try:
        u = _spawn(lib, w, 300.0, 400.0)
        lib.om_command_move(w, u, 900.0, 400.0)
        lib.om_tactical_step(w)
        return tuple(lib.om_unit_get_destination(w, u))[-2:]
    finally:
        lib.om_world_free(w)


@pytest.mark.parametrize("radius", [10.0, 30.0])
def test_ruling_15_navmesh_margin_nearest_reachable_point_is_a_radius_inside_its_cell(lib, radius):
    """Radius 10: (490, 390); radius 30: (470, 370). Red today: (485, 385) at both."""
    assert _unreachable_destination(lib, radius) == pytest.approx((500.0 - radius, 400.0 - radius), abs=STEP_TOL)


def test_ruling_15_navmesh_margin_control_nearest_reachable_point_at_radius_15(lib):
    """Control (green today and after): at 15 the replaced destination is (485, 385)."""
    assert _unreachable_destination(lib, DEFAULT_RADIUS) == pytest.approx((485.0, 385.0), abs=STEP_TOL)


def _routed_run(lib, radius, ticks=300):
    """A unit at (300, 400) ordered to (900, 400) behind a wall open above y = 800: it follows route waypoints.
    Returns the per-tick positions. The first waypoint is the centre of cell (4, 8), (450, 850)."""
    w = _terrain_world(lib, radius, WALL_LOW)
    try:
        u = _spawn(lib, w, 300.0, 400.0)
        lib.om_command_move(w, u, 900.0, 400.0)
        trace = []
        for _ in range(ticks):
            lib.om_tactical_step(w)
            trace.append(_pos(lib, w, u))
        return trace
    finally:
        lib.om_world_free(w)


FIRST_WAYPOINT = (450.0, 850.0)
DEST = (900.0, 400.0)
WAYPOINT_MULT = 2.0   # R-099-04 / ALG-68 WAYPOINT_ARRIVE_MULT: a routed move is within 2.0 radii of a waypoint


def _heading(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _first_turn(trace, start=(300.0, 400.0)):
    """(index, position, step length) of the first tick whose heading differs from the one before by more than 0.02
    rad: the tick the unit took its next waypoint."""
    pts = [start] + trace
    step = math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1])
    for i in range(2, len(pts)):
        if abs(_heading(pts[i - 1], pts[i]) - _heading(pts[i - 2], pts[i - 1])) > 0.02:
            return i, pts[i], step
    raise AssertionError("scene error: the routed unit never turned")


@pytest.mark.parametrize("radius", [10.0, 30.0])
def test_R_099_04_unit_takes_a_route_waypoint_inside_two_radii(lib, radius):
    """A unit on a route takes its next waypoint the first tick it is within 2.0 x radius of it (R-099-04, ALG-68
    WAYPOINT_ARRIVE_MULT), so it turns there: just under 20 wu from the first waypoint at radius 10, just under 60 at radius 30 (the turn is
    seen up to two 7.5 wu steps inside the reach: the tick it takes the waypoint it also moves). Red today: it turns
    24.2 from the waypoint at either radius."""
    _, pos, step = _first_turn(_routed_run(lib, radius))
    reach = WAYPOINT_MULT * radius
    d = math.hypot(pos[0] - FIRST_WAYPOINT[0], pos[1] - FIRST_WAYPOINT[1])
    assert reach - 2.0 * step <= d < reach, f"radius {radius}: turned {d:.1f} from the waypoint, expected within [{reach - 2.0 * step:.1f}, {reach})"


def test_R_099_04_control_unit_takes_a_route_waypoint_at_radius_15_inside_30(lib):
    """Control (green today and after): at 15 the turn is 24.2 wu from the waypoint, inside 30 and within two steps
    of it."""
    _, pos, step = _first_turn(_routed_run(lib, DEFAULT_RADIUS))
    d = math.hypot(pos[0] - FIRST_WAYPOINT[0], pos[1] - FIRST_WAYPOINT[1])
    assert 30.0 - 2.0 * step <= d < 30.0, f"turned {d:.1f} from the waypoint, step {step:.1f}"


@pytest.mark.parametrize("radius", [10.0, 30.0])
def test_R_099_04_routed_move_ends_within_two_radii_of_its_destination(lib, radius):
    """The routed move's last leg ends the first tick the unit is within 2.0 x radius of the destination (not the
    1.5 of a direct move): where it stops is at least 2 r - one step and under 2 r from (900, 400). Red today: 24.7
    at both radii."""
    trace = _routed_run(lib, radius)
    stop = trace[-1]
    assert trace[-1] == trace[-2], "scene error: the unit was still moving"
    step = math.hypot(trace[1][0] - trace[0][0], trace[1][1] - trace[0][1])
    d = math.hypot(stop[0] - DEST[0], stop[1] - DEST[1])
    reach = WAYPOINT_MULT * radius
    assert reach - step <= d < reach, f"radius {radius}: stopped {d:.1f} from the destination, expected [{reach - step:.1f}, {reach})"
