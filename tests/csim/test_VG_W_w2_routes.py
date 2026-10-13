"""VG-W2 (visible-game spec rev 12c, Lane W, paragraph "W2, stored routes"; amended by the Rev 12b "W1." ruling, the
Rev 12c batch-2 text and the Architect rulings of 2026-10-12 on the save-and-hash layout, the route getter and the
end of a truncated plan): a walking unit plans its route once, stores the points, walks them and saves them.

Rules proved (quoted word for word):
  [B R-001-05] "the route with the shortest travel time, changing layer wherever that shortens it"
      (bible docs/bible/epics/E-01-layer-system.md R-001-05: "it takes the route with the shortest travel time to the
      goal, counting each transfer, across every layer it may use"). A stored route is the planner's route; storing it
      may not change which route a walker takes, and a terrain change or a new order must still replan.
  [B R-004-07] "speed / 1.1 up, x 1.1 down" (bible R-004-07: "going up the Raider takes 4.4 seconds and the Bastion
      16.5 seconds (speed divided by 1.1), and going down 3.6 and 13.6 seconds (speed times 1.1)"). The routes may not
      change: the stored points are the points om_walk_route returned.
Spec text proved (W2 paragraph, "Lane W: walk routes"): "the walker plans once per order or epoch change and walks the
stored points; on arrival at point `i` it aims at `i + 1` without replanning"; "Replan only when `plan_valid` is 0 at
order time, the epoch differs, or the destination changed"; "Named draft `DRAFT-walk-tick-ms-w2` 3 ms for the same
600-walker fixture"; "a save round trip at tick 50 mid-walk restores `route_n`, `route_i` and the points and the walk
continues to the same checksum at tick 200 as an unsaved run (red: fields absent)"; "a terrain change
(`om_map_block_rect`) mid-walk replans (control green today)". Rev 12b "W1.": W2's owns list loses the getter
`om_move_terrain_epoch`. Architect rulings 2026-10-12 (taken as written): the SAVE AND HASH LAYOUT (points live in
om_move_state as uint16 cells; the row gains route_n, route_i, route_ends_at_goal at its end; read rejects route_n >
OM_MOVE_WALK_PTS, (route_n ? route_i >= route_n : route_i != 0), route_ends_at_goal > 1, cx >= cells_w, cy >= cells_h);
the ROUTE GETTER `uint32_t om_move_route_get(const om_world *w, uint32_t unit_id, uint32_t *route_i, double *pts,
uint32_t cap)` (internal, no ABI change, reads without om_move_touch); END OF A TRUNCATED PLAN ("A plan with n >
OM_MOVE_WALK_PTS stores nothing (route_n = 0) and keeps today's per-waypoint replan unchanged"; "A terrain epoch change
or a new destination clears the stored route and replans"). Rev 12c batch 2 and the E7 paragraph: save format 11 here,
E7 takes 12 after W2 (ledger TD-VG-E-27).

Cases (red today means the red reason stated; the file is run on origin/main plus the docs branch, no W2 source):
  C0  positive control, green today: the 600-walker world builds and walks; om_move_terrain_epoch(NULL) == 0 and a live
      world's epoch moves by exactly 1 per om_map_block_rect.
  P   perf: median of 20 om_world_step (5 warm-up) under DRAFT-walk-tick-ms-w2. Red today (about 8 ms).
  S   save round trip at tick 50 mid-walk. Red today: om_move_route_get is absent.
  A   the stored route is the plan: pairs 1.. equal om_walk_route's points 1.., route_i is 1. Red: getter absent.
  T   terrain change replans (control, green today, does not use the getter).
  T2  the same through the getter. Red: getter absent.
  T3  an om_map_block_rect epoch bump alone restarts route_i (spec's named call). Red: getter absent.
  E   a new order replans. Red: getter absent.
  R   load rejections of route_n > 512 and route_i > route_n, plus controls. Red: getter absent.
  F   a read of a fresh movement row does not move the checksum (green today and after; GAP 7).
  G   getter hygiene: no row, no order, cap, no checksum change. Red: getter absent.
  K   a unit id reused after om_tactical_reset reports route_n 0. Red: getter absent.
  L   a plan longer than 512 points stores nothing and the walker still walks as today. Red: getter absent.

Fixture (imported read-only from tests/csim/test_VG_W_w1_planner.py, the same 600-walker fixture the spec names:
_walker_world :375, _positions :391, the C case's body at :424): seed-1 world, canvas 24,000 wu (240 x 240 cells),
Vanguard (type 2), engine layer 0, 25 x 24 grid at 40 wu from (17450, 8450), one om_command_move of all 600 to
(1850, 23950). Planner route of walker 0 at tick 1: 315 points (dumped by the case that uses it).

Reading the layout rulings (the writer's inference; the report flags it for the Architect): route_n is the planner's
point count n including point 0 (the unit), so the walker's aim index route_i runs 1 .. route_n - 1 and a stored route
has route_n >= 2; the getter's pair 0 is the unit's own start slot and is never asserted. Pairs 1 .. route_n - 1 are
the planner's points 1 .. n - 1, the last being (dest_x, dest_y) when the goal was reached. The widths of route_n,
route_i, route_ends_at_goal and of the cells in the save bytes are not given: case R finds them by search.

Movement is replayed lazily by the first accessor after a step (tactical_move.c file header, om_move_sync); every case
reads the 600 positions (a sync) before it calls the getter, so the getter sees the state after the step.
Thresholds: only DRAFT_WALK_TICK_MS_W2; everything else is exact equality.
"""
import ctypes
import math

import test_E13_R207_05_walker_routes as routes
import test_VG_W_w1_planner as w1      # read-only import: the 600-walker fixture, not edited
from scale._scale_helpers import median_ns
from test_E16_S111_saving import _load, _save    # the save and load calls the csim save tests use

SENT = -12345.0
BIG_CAP = 8192                  # points; the same cap test_VG_W_w1_planner uses
OM_MOVE_WALK_PTS = 512          # csrc/tactical_move.c:2131
ROUTE_CAP = OM_MOVE_WALK_PTS + 8   # getter buffer: room for route_n <= 512 and a probe past it
N_SECTIONS = 9
TICK_MID = 50                   # the spec's "tick 50 mid-walk"
TICK_END = 200                  # the spec's "tick 200"
WITNESS_IDX = (0, 299, 599)     # walker indices (unit-id order) whose routes are read; first, middle, last
WAYPOINT_ARRIVE_WU = 30.0       # OM_WAYPOINT_ARRIVE_MULT * OM_UNIT_COLLISION_RADIUS (tactical_move.c:2171 comment)
NEW_GOAL = (23950.0, 7450.0)    # wu; cell (239, 74) centre, the 'long' fixture start of test_VG_W_w1_planner seed 1
PIT_AHEAD_POINTS = 6            # fixture choice (not a threshold): the pit sits on the front walker's route point 6
PIT_HALF_CELLS = 1              # 3 x 3 cells of height 0 cm (the walk mask also drops their sloped neighbours)
PIT_HEIGHT_CM = 0               # below the dry level (6000 cm, terrain.c:425), so band floors are unchanged
SAMPLE_EVERY = 10               # ticks between samples of "who stands where"
T_TICKS = 200                   # ticks after the terrain change
LONG_WALLS = (4, 9, 14, 19)     # wall rows of the serpentine of case L
LONG_WALL_CM, LONG_FLOOR_CM = 27000, 7000
LONG_GAP_CELLS = 4
LONG_START, LONG_GOAL = (23050.0, 250.0), (250.0, 2350.0)
LONG_TICKS = (200, 400, 600, 800, 1000)

# DRAFT-walk-tick-ms-w2, spec Lane W W2 paragraph, ledger row, Westley owns it
DRAFT_WALK_TICK_MS_W2 = 3.0


# ---------------------------------------------------------------- bindings (all declared here, none from conftest)

def _bind_epoch(lib):
    """om_move_terrain_epoch exists on origin/main (W1 landed it), so this binding is green today."""
    lib.om_move_terrain_epoch.argtypes = [ctypes.c_void_p]
    lib.om_move_terrain_epoch.restype = ctypes.c_uint32


def _bind(lib):
    """Bind both internal functions. A binding to a symbol that is absent fails the test, never skips it."""
    _bind_epoch(lib)
    try:
        fn = lib.om_move_route_get
    except AttributeError:
        raise AssertionError("om_move_route_get is absent from libouroboros.so: the VG-W2 route getter "
                             "(csrc/om_internal.h, body in csrc/tactical_move.c) does not exist yet")
    fn.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                   ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
    fn.restype = ctypes.c_uint32
    routes._declare(lib)       # om_walk_route
    return fn


def _route_get(lib, w, unit, cap=ROUTE_CAP):
    """(route_n, route_i, [(x, y)] * min(route_n, cap)); route_i starts at a sentinel so a getter that does not write
    it shows."""
    fn = _bind(lib)
    pts = (ctypes.c_double * (2 * cap))(*([SENT] * (2 * cap)))
    ri = ctypes.c_uint32(0xDEADBEEF)
    n = fn(w, unit, ctypes.byref(ri), pts, cap)
    return n, ri.value, [(pts[2 * k], pts[2 * k + 1]) for k in range(min(n, cap))]


def _plan(lib, w, unit, goal):
    """What om_walk_route returns for the unit now: (n, [(x, y)] * n, seconds)."""
    return routes._route(lib, w, unit, *goal, cap=BIG_CAP)


def _sync(lib, w, ids):
    """Reads every position: the first accessor replays the pending movement ticks (see the module docstring)."""
    return w1._positions(lib, w, ids)


def _cks(lib, w):
    sec = (ctypes.c_uint64 * N_SECTIONS)()
    full = lib.om_world_checksum_full(w, sec, N_SECTIONS)
    return full, tuple(sec)


def _cell(p):
    return int(p[0] // routes.CELL), int(p[1] // routes.CELL)


def _walker_world_at(lib, make, ticks):
    w, ids = w1._walker_world(lib, make)
    for _ in range(ticks):
        lib.om_world_step(w)
    _sync(lib, w, ids)
    return w, ids


def _unit_state(lib, w, ids):
    return [(*lib.om_unit_get_pos(w, u), lib.om_unit_get_layer(w, u)) for u in ids]


# ---------------------------------------------------------------- C0

def test_C0_positive_control_world_walks_and_the_epoch_getter_reads_the_real_epoch(lib, world_factory):
    """Green today. Premise dumped: the 600-walker world builds, 20 om_world_step run and walkers moved.
    Architect ruling 2026-10-12: the epoch getter's fallback value is 0 (tactical_move.c:555-557,
    `w ? om_ms(w)->terrain_epoch : 0`); the surviving undertest mutant changed that 0 to 1, so the exact value is
    asserted. A second assertion reads the non-NULL branch: the epoch of a live world moves by exactly 1 per
    om_map_block_rect (tactical_mapgen.c:875 om_move_terrain_changed)."""
    _bind_epoch(lib)
    w, ids = w1._walker_world(lib, world_factory)
    spawn = _sync(lib, w, ids)
    for _ in range(20):
        lib.om_world_step(w)
    pos = _sync(lib, w, ids)
    moved = sum(1 for a, b in zip(spawn, pos) if a != b)
    e0 = lib.om_move_terrain_epoch(w)
    assert lib.om_map_block_rect(w, 100.0, 100.0, 200.0, 200.0, 0, 0) == 0
    e1 = lib.om_move_terrain_epoch(w)
    print("C0 premise: %d walkers built, %d of %d moved in 20 ticks; epoch before block_rect %d, after %d" % (
        len(ids), moved, len(ids), e0, e1))
    assert len(ids) == 600 and moved >= w1.PREMISE_MIN_MOVED, "premise: only %d of 600 walkers moved" % moved
    # The surviving mutant of the fallback: `w ? ... : 0` changed to `: 1`.
    assert lib.om_move_terrain_epoch(None) == 0, "om_move_terrain_epoch(NULL) must answer 0 (tactical_move.c:557)"
    assert e1 == e0 + 1, "the non-NULL branch must read the real epoch: %d then %d" % (e0, e1)


# ---------------------------------------------------------------- P

def test_P_a_tick_with_600_walkers_costs_less_than_the_w2_draft(lib, world_factory):
    """THE PERF CASE (spec W2: "Named draft DRAFT-walk-tick-ms-w2 3 ms for the same 600-walker fixture"; median of 20
    om_world_step after 5 warm-up through median_ns(op, n=20, warmup=5)). Red today: W1 landed at about 8 ms. The
    premise (walkers still marching through the measured steps) is asserted before the perf line."""
    w, ids = w1._walker_world(lib, world_factory)
    calls, snap = [], {}

    def op():
        calls.append(1)
        lib.om_world_step(w)
        if len(calls) == w1.WALK_MEDIAN_WARMUP:
            snap["step5"] = w1._positions(lib, w, ids)

    median_ms = median_ns(op, n=w1.WALK_MEDIAN_N, warmup=w1.WALK_MEDIAN_WARMUP) / 1e6
    end = w1._positions(lib, w, ids)
    marching = sum(1 for a, b in zip(snap["step5"], end) if a != b)
    print("P premise: %d of %d walkers changed position between step %d and step %d" % (
        marching, len(ids), w1.WALK_MEDIAN_WARMUP, len(calls)))
    print("P median om_world_step: %.3f ms" % median_ms)
    assert len(calls) == w1.WALK_MEDIAN_WARMUP + w1.WALK_MEDIAN_N
    assert marching >= w1.PREMISE_MIN_MOVED, "premise: only %d walkers still marching" % marching
    # DRAFT-walk-tick-ms-w2, spec Lane W W2 paragraph, ledger row, Westley owns it
    assert median_ms < DRAFT_WALK_TICK_MS_W2, (
        "median of %d om_world_step with 600 walkers is %.3f ms, DRAFT-walk-tick-ms-w2 is %.1f ms" % (
            w1.WALK_MEDIAN_N, median_ms, DRAFT_WALK_TICK_MS_W2))


# ---------------------------------------------------------------- S

def _read_witnesses(lib, w, ids):
    out = {}
    for k in WITNESS_IDX:
        out[k] = _route_get(lib, w, ids[k])
    return out


def test_S_save_round_trip_mid_walk_restores_the_routes_and_the_walk_continues(lib, world_factory):
    """Spec W2: "a save round trip at tick 50 mid-walk restores route_n, route_i and the points and the walk continues
    to the same checksum at tick 200 as an unsaved run (red: fields absent)". 600 walkers (all keep a 300-point
    route). Three worlds of one construction: REF steps straight to 200; SRC steps to 50, is saved, steps to 200; DST
    loads the save into a fresh world of the same construction and steps 150 more. Red today: om_move_route_get is
    absent (the first read below). Exact doubles; pair 0 of a route is the unit's own slot and is not compared."""
    _bind(lib)
    src, ids = _walker_world_at(lib, world_factory, TICK_MID)
    before = _read_witnesses(lib, src, ids)
    for k, (n, ri, pts) in before.items():
        print("S premise: walker index %d (unit %d) at tick %d: route_n %d, route_i %d, first stored pairs %r, last %r" % (
            k, ids[k], TICK_MID, n, ri, pts[1:3], pts[-1]))
        assert n > 1, "premise: walker %d has route_n %d (no multi-point route at tick %d)" % (k, n, TICK_MID)
        assert 1 <= ri < n, "premise: walker %d has route_i %d with route_n %d" % (k, ri, n)
    buf, size = _save(lib, src)
    dst = w1._prepare(lib, world_factory(n_regions=1))
    assert _load(lib, dst, buf, size) == 0
    after = _read_witnesses(lib, dst, ids)
    for k in WITNESS_IDX:
        nb, rb, pb = before[k]
        na, ra, pa = after[k]
        assert (na, ra) == (nb, rb), "walker %d: loaded (route_n, route_i) %r, saved %r" % (k, (na, ra), (nb, rb))
        assert pa[1:] == pb[1:], "walker %d: loaded stored points differ from the saved ones" % k
    ref, _ = _walker_world_at(lib, world_factory, TICK_END)
    for _ in range(TICK_END - TICK_MID):
        lib.om_world_step(src)
        lib.om_world_step(dst)
    s_ref, s_src, s_dst = (_unit_state(lib, x, ids) for x in (ref, src, dst))
    assert s_dst == s_ref, "loaded run differs from the unsaved run at tick %d: first unit index %d" % (
        TICK_END, next(k for k, (a, b) in enumerate(zip(s_dst, s_ref)) if a != b))
    assert s_src == s_ref, "saving changed the saved run: first unit index %d" % next(
        k for k, (a, b) in enumerate(zip(s_src, s_ref)) if a != b)
    c_ref, c_src, c_dst = (_cks(lib, x) for x in (ref, src, dst))
    print("S checksum_full at tick %d: ref %r, saved-and-loaded %r" % (TICK_END, c_ref[0], c_dst[0]))
    assert c_dst == c_ref, "om_world_checksum_full (return and nine sections) of the loaded run differs from the unsaved run"
    assert c_src == c_ref, "om_world_checksum_full of the saved run differs from the unsaved run"


# ---------------------------------------------------------------- A

def test_A_the_stored_route_is_the_plan(lib, world_factory):
    """Spec W2: "the walker plans once per order ... and walks the stored points" and "Routes remain identical by
    construction (W1's parity table is the proof: the stored route is the same `pts`)" [B R-001-05, R-004-07]. At the
    first tick after the order the stored pairs 1.. of a walker equal the points 1.. om_walk_route returns for it to the
    goal, exactly, route_n equals the planner's point count, and route_i is the layout ruling's start index 1 (the
    walkers stand on cell centres 100 wu or more from point 1, outside the 30 wu arrival radius). Red today: getter
    absent. The plan is taken before the step (a pure function of the row position the walker plans from)."""
    _bind(lib)
    w, ids = w1._walker_world(lib, world_factory)
    _sync(lib, w, ids)
    plans = {k: _plan(lib, w, ids[k], w1.WALK_GOAL) for k in WITNESS_IDX}
    spawn = _sync(lib, w, ids)
    lib.om_world_step(w)
    _sync(lib, w, ids)
    for k in WITNESS_IDX:
        n, pts, _ = plans[k]
        rn, ri, rpts = _route_get(lib, w, ids[k])
        d1 = math.dist(spawn[k], pts[1])
        print("A premise: walker index %d (unit %d) planner n %d, goal point %r; stored route_n %d, route_i %d, "
              "distance from its start to point 1 %.1f wu" % (k, ids[k], n, pts[-1], rn, ri, d1))
        assert n > 2 and d1 >= WAYPOINT_ARRIVE_WU, "premise: planner n %d, distance to point 1 %.1f" % (n, d1)
        assert rn == n, "walker %d: route_n %d, planner point count %d" % (k, rn, n)
        assert ri == 1, "walker %d: route_i %d, the layout ruling's start index is 1" % (k, ri)
        assert rpts[1:] == pts[1:], "walker %d: stored points differ from om_walk_route's at pair %d" % (
            k, next(i for i, (a, b) in enumerate(zip(rpts[1:], pts[1:]), 1) if a != b))


# ---------------------------------------------------------------- T, T2, T3

def _hole(lib, w, ids):
    """Sets a 3 x 3 pit on the route of the walker furthest along (largest y at the moment), PIT_AHEAD_POINTS ahead of
    it, through om_terrain_set_heights (the K-e5 test hook; it rewrites the walk masks and bumps the epoch, terrain.c:
    1113-1138). Returns (blocked, front_index, rect_cells): the layer-0 cells walkable before and not after.
    om_map_block_rect cannot do this: it sets mapgen bits, the terrain walk mask the planner reads is not derived from
    them (terrain.c:886; walk_route.c:232), so a route planned after it is the same route (dumped by case T3)."""
    pos = _sync(lib, w, ids)
    front = max(range(len(ids)), key=lambda k: (pos[k][1], -k))
    n, pts, _ = _plan(lib, w, ids[front], w1.WALK_GOAL)
    assert n > PIT_AHEAD_POINTS + 2, "premise: the front walker's route has %d points" % n
    cx, cy = _cell(pts[PIT_AHEAD_POINTS])
    cw, ch = routes._grid(lib, w)
    heights = (ctypes.c_int32 * (cw * ch))()
    assert lib.om_terrain_get_heights(w, heights, cw * ch) == cw * ch
    floors_before = (ctypes.c_double * 8)()
    nb = lib.om_terrain_band_heights(w, floors_before, 8)
    mask_before = routes._mask(lib, w, 0)
    rect = [(x, y) for y in range(cy - PIT_HALF_CELLS, cy + PIT_HALF_CELLS + 1)
            for x in range(cx - PIT_HALF_CELLS, cx + PIT_HALF_CELLS + 1)]
    for x, y in rect:
        heights[y * cw + x] = PIT_HEIGHT_CM
    lib.om_terrain_set_heights.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32, ctypes.c_uint32]
    assert lib.om_terrain_set_heights(w, heights, cw, ch) == 1
    floors_after = (ctypes.c_double * 8)()
    lib.om_terrain_band_heights(w, floors_after, 8)
    mask_after = routes._mask(lib, w, 0)
    blocked = {i for i in range(cw * ch) if mask_before[i] and not mask_after[i]}
    changed_back = sum(1 for i in range(cw * ch) if not mask_before[i] and mask_after[i])
    print("T premise: front walker index %d at %r, pit centre cell (%d, %d) = route point %d; %d layer-0 cells became "
          "unwalkable, %d became walkable; band floors unchanged: %s" % (
              front, pos[front], cx, cy, PIT_AHEAD_POINTS, len(blocked), changed_back,
              list(floors_before)[:nb] == list(floors_after)[:nb]))
    assert len(blocked) >= len(rect), "premise: only %d cells became unwalkable" % len(blocked)
    assert list(floors_before)[:nb] == list(floors_after)[:nb], "premise: the pit moved the band floors"
    assert not any(_cell(p)[1] * cw + _cell(p)[0] in blocked for p in pos), "premise: a walker stands in the pit"
    return blocked, front, (cx, cy)


def _in(blocked, cw, p):
    c = _cell(p)
    return c[1] * cw + c[0] in blocked


def _run_t(lib, make, change):
    """The tick-50 world, optionally with the pit; samples who stands in the pit cells every SAMPLE_EVERY ticks for
    T_TICKS ticks. Returns (blocked, secs50, secs_end, inside_ever, samples, world, ids); secs are the planner's
    remaining travel seconds to the goal of each walker (change run only, else None)."""
    w, ids = _walker_world_at(lib, make, TICK_MID)
    p50 = _sync(lib, w, ids)
    if change:
        blocked, front, _ = _hole(lib, w, ids)
    else:
        # The control run needs the same cells: laid out on a twin world, recorded as a plain set (no change here).
        tw, tids = _walker_world_at(lib, make, TICK_MID)
        blocked, front, _ = _hole(lib, tw, tids)
    cw, _ = routes._grid(lib, w)
    secs50 = [_plan(lib, w, u, w1.WALK_GOAL)[2] for u in ids] if change else None
    inside_ever, samples = set(), []
    for t in range(T_TICKS):
        lib.om_world_step(w)
        if t % SAMPLE_EVERY == SAMPLE_EVERY - 1:
            pos = _sync(lib, w, ids)
            hit = [k for k, p in enumerate(pos) if _in(blocked, cw, p)]
            inside_ever.update(hit)
            samples.append(len(hit))
    _sync(lib, w, ids)
    secs_end = [_plan(lib, w, u, w1.WALK_GOAL)[2] for u in ids] if change else None
    return blocked, secs50, secs_end, inside_ever, samples, w, ids


def test_T_terrain_change_mid_walk_replans_and_the_walkers_go_around(lib, world_factory):
    """Spec W2: "a terrain change mid-walk replans (control green today)" [B R-001-05]. CONTROL, GREEN TODAY, does not
    use the getter. At tick 50 a 3 x 3 pit is cut into the terrain ahead of the front walker (see _hole for why not
    om_map_block_rect: that call leaves the walk mask and so the route unchanged). Proof the pit lies on the path of
    at least one walker: in a twin run with no change, walkers stand in the pit cells at some sample (premise). With the
    pit, over the next 200 ticks no unit stands in a cell that became unwalkable at any sample, and every walker
    that would have crossed it still gets closer to the goal (the planner's remaining travel seconds fall)."""
    base = _run_t(lib, world_factory, False)
    blocked, secs50, secs_end, inside_ever, samples, w, ids = _run_t(lib, world_factory, True)
    control_hits, control_ever = base[4], base[3]
    print("T premise: control run (no change) samples of walkers in the pit cells every %d ticks: %r, %d distinct "
          "walkers" % (SAMPLE_EVERY, control_hits, len(control_ever)))
    print("T result: with the pit, walkers in the pit cells per sample: %r; distinct %d" % (samples, len(inside_ever)))
    assert control_ever, "premise: no walker enters the pit cells without the change, so they are not on any path"
    assert not inside_ever, "%d walkers stood in unwalkable pit cells after the change" % len(inside_ever)
    # "Closer to the goal" is the planner's remaining travel time (om_walk_route seconds) at tick 50 (after the change)
    # and at tick 250: the straight-line distance is not monotone for a walker that goes round a pit.
    worse = [k for k in control_ever if not secs_end[k] < secs50[k]]
    print("T result: %d walkers would have crossed the pit; remaining travel seconds to the goal fell for %d of them" % (
        len(control_ever), len(control_ever) - len(worse)))
    assert not worse, "walkers %r did not get closer to the goal in %d ticks (first: %.1f -> %.1f s)" % (
        worse[:5], T_TICKS, secs50[worse[0]], secs_end[worse[0]])


def test_T2_terrain_change_replaces_the_stored_route_through_the_getter(lib, world_factory):
    """Spec W2: "Replan only when plan_valid is 0 at order time, the epoch differs, or the destination changed" and
    "A terrain epoch change or a new destination clears the stored route and replans" (Architect ruling). After the
    pit of case T, the stored route of every walker whose old route crossed a newly unwalkable cell differs from the
    one before, avoids those cells, and route_i has restarted (the walker has just replanned: route_i is 1, or 2 when
    it is already inside the arrival radius of point 1). Red today: getter absent."""
    _bind(lib)
    w, ids = _walker_world_at(lib, world_factory, TICK_MID)
    blocked, front, _ = _hole(lib, w, ids)
    cw, _ = routes._grid(lib, w)
    # Routes before the change were planned on the old terrain: read them from the getter, but the world was already
    # changed by _hole; so rebuild the twin before-state from a second world at tick 50.
    tw, tids = _walker_world_at(lib, world_factory, TICK_MID)
    before = {k: _route_get(lib, tw, tids[k]) for k in range(len(tids))}
    affected = [k for k in range(len(ids)) if any(
        _in(blocked, cw, p) for p in before[k][2][max(before[k][1], 1):])]
    print("T2 premise: %d walkers' stored routes cross a newly unwalkable cell; route_i before for the first three: %r" % (
        len(affected), [before[k][1] for k in affected[:3]]))
    assert len(affected) >= 3, "premise: fewer than 3 stored routes cross the pit"
    lib.om_world_step(w)
    _sync(lib, w, ids)
    for k in affected[:3]:
        nb, rb, pb = before[k]
        na, ra, pa = _route_get(lib, w, ids[k])
        print("T2: walker index %d: route_n %d -> %d, route_i %d -> %d" % (k, nb, na, rb, ra))
        assert pa[1:] != pb[1:], "walker %d: the stored route is the one planned before the terrain change" % k
        assert not any(_in(blocked, cw, p) for p in pa[1:]), "walker %d: the new route crosses an unwalkable cell" % k
        assert 1 <= ra <= 2, "walker %d: route_i %d after the replan (starts at 1)" % (k, ra)
        assert ra < rb, "walker %d: route_i %d did not restart (was %d)" % (k, ra, rb)


def test_T3_an_epoch_bump_from_block_rect_alone_restarts_the_route(lib, world_factory):
    """Spec W2: "a terrain change (`om_map_block_rect`) mid-walk replans". om_map_block_rect bumps the epoch by 1 (case
    C0) and the walker replans on its next step even though the walk mask, and so the route, is unchanged. A rectangle
    far from the walkers (the canvas corner) changes no route; the stored route is replanned from the walker's cell:
    route_i restarts and route_n shrinks by the cells already walked. Red today: getter absent."""
    _bind(lib)
    w, ids = _walker_world_at(lib, world_factory, TICK_MID)
    before = _read_witnesses(lib, w, ids)
    e0 = lib.om_move_terrain_epoch(w)
    assert lib.om_map_block_rect(w, 100.0, 100.0, 400.0, 400.0, 0, 0) == 0
    assert lib.om_move_terrain_epoch(w) == e0 + 1
    lib.om_world_step(w)
    _sync(lib, w, ids)
    for k in WITNESS_IDX:
        nb, rb, pb = before[k]
        na, ra, pa = _route_get(lib, w, ids[k])
        print("T3: walker index %d: route_n %d -> %d, route_i %d -> %d" % (k, nb, na, rb, ra))
        assert rb >= 2, "premise: walker %d had route_i %d at tick %d" % (k, rb, TICK_MID)
        assert na < nb, "walker %d: route_n %d was not replanned from the walker's cell (was %d)" % (k, na, nb)
        assert 1 <= ra <= 2 and ra < rb, "walker %d: route_i %d did not restart (was %d)" % (k, ra, rb)


# ---------------------------------------------------------------- E

def test_E_a_new_order_replaces_the_stored_route(lib, world_factory):
    """Spec W2: "the destination changed" is a replan trigger; Architect: "A terrain epoch change or a new destination
    clears the stored route and replans". At tick 50 all 600 walkers are ordered to another destination; after one step
    the stored route of a walker ends at the new destination and equals the points om_walk_route returns for it
    (taken before the step, from the same position). Red today: getter absent."""
    _bind(lib)
    w, ids = _walker_world_at(lib, world_factory, TICK_MID)
    old = _read_witnesses(lib, w, ids)
    assert lib.om_command_move(w, ids, len(ids), *NEW_GOAL) == 0
    plans = {k: _plan(lib, w, ids[k], NEW_GOAL) for k in WITNESS_IDX}
    lib.om_world_step(w)
    _sync(lib, w, ids)
    for k in WITNESS_IDX:
        n, pts, _ = plans[k]
        rn, ri, rpts = _route_get(lib, w, ids[k])
        print("E: walker index %d: planner n to %r is %d (ends at %r); stored route_n %d route_i %d, old route_n %d" % (
            k, NEW_GOAL, n, pts[-1], rn, ri, old[k][0]))
        assert n > 2 and pts[-1] == NEW_GOAL, "premise: the new destination is not reachable from walker %d" % k
        assert rpts[-1] == NEW_GOAL, "walker %d: the stored route ends at %r, not the new destination" % (k, rpts[-1])
        assert (rn, rpts[1:]) == (n, pts[1:]), "walker %d: the stored route is not om_walk_route's route to the new goal" % k
        assert rpts[1:] != old[k][2][1:], "walker %d: the stored route did not change" % k
        assert 1 <= ri <= 2, "walker %d: route_i %d after the new order" % (k, ri)


# ---------------------------------------------------------------- R

def _le(v, width):
    return int(v).to_bytes(width, "little")


def _locate_block(raw, rn, ri, p1, p2):
    """Offsets of (route_n, route_i) in the save bytes: for each width 2, 4, 8 the bytes le(route_n) + le(route_i),
    kept when, within the next 64 bytes, the cell pairs of stored points 1 and 2 follow as four consecutive values of
    one width (cx1, cy1, cx2, cy2). Returns [(offset, width, cell_width)]."""
    cells = [int(p1[0] // routes.CELL), int(p1[1] // routes.CELL), int(p2[0] // routes.CELL), int(p2[1] // routes.CELL)]
    found = []
    for w in (2, 4, 8):
        head = _le(rn, w) + _le(ri, w)
        at = raw.find(head)
        while at >= 0:
            window = raw[at + 2 * w: at + 2 * w + 64]
            for cwid in (2, 4, 8):
                tail = b"".join(_le(c, cwid) for c in cells)
                if window.find(tail) >= 0:
                    found.append((at, w, cwid))
            at = raw.find(head, at + 1)
    return found


SLOT_MOVE, SLOT_LAST = 6, 10     # OM_SAVE_SLOT_MOVE .. OM_SAVE_SLOT_TERRAIN (csrc/om_internal.h:45-49); the slots
                                 # are written in this fixed order and the movement slot is followed by 7, 8, 9, 10


def _slot_header(raw, at):
    """Offsets q of the movement slot header (u8 id 6, u32 length, csrc/save.c:140) that spans offset `at` and is
    followed by the headers of slots 7, 8, 9 and 10 whose lengths end exactly at the end of the buffer. Searched
    backwards from `at`; the caller asserts the result is unique."""
    found = []
    for q in range(at - 5, max(at - 6_000_000, 0), -1):
        if raw[q] != SLOT_MOVE:
            continue
        blen = int.from_bytes(raw[q + 1:q + 5], "little")
        pos = q + 5 + blen
        if not (q + 5 <= at < pos <= len(raw)):
            continue
        for slot in range(SLOT_MOVE + 1, SLOT_LAST + 1):
            if pos + 5 > len(raw) or raw[pos] != slot:
                pos = -1
                break
            pos += 5 + int.from_bytes(raw[pos + 1:pos + 5], "little")
        if pos == len(raw):
            found.append((q, blen))
    return found


def _regrown(raw, at, wid, cwid, rn, new_n, cell2_at, hdr):
    """The save bytes with the walker's route made new_n points long: new_n - rn copies of its last stored pair are
    inserted after the last pair, route_n is patched to new_n and the slot length grows by the bytes added, so the
    buffer stays structurally valid and only the value of route_n (not a misparse) can make a reader refuse it."""
    q, blen = hdr
    p1 = cell2_at - 2 * cwid
    end = p1 + (rn - 1) * 2 * cwid
    extra = raw[end - 2 * cwid:end] * (new_n - rn)
    data = bytearray(raw[:end] + extra + raw[end:])
    data[at:at + wid] = _le(new_n, wid)
    data[q + 1:q + 5] = _le(blen + len(extra), 4)
    return data


def test_R_load_rejects_bad_route_fields_and_a_good_copy_loads(lib, world_factory):
    """Architect layout ruling: "Read rejects route_n > OM_MOVE_WALK_PTS, (route_n ? route_i >= route_n : route_i != 0),
    route_ends_at_goal > 1, any cx >= cells_w or cy >= cells_h"; R-111-03 (a refused load leaves the world untouched).
    A mid-walk save is taken; the route block of one walker is found in the bytes by searching for the exact bytes of
    its route_n and route_i (read through the getter) followed within 64 bytes by its first two stored cells, at widths
    2, 4 and 8 little-endian (the widths are not in the ruling). (i) route_n patched to 513 with 513 - route_n pairs
    inserted and the slot length (u32 after the slot id byte, csrc/save.c:140) grown to match, so the bytes stay
    parseable and only the value can be refused, and (ii) route_i patched to route_n + 1, make om_load_state_read
    return non-zero and leave the target world's checksum unchanged (i-control: route_n + 1 with one pair added loads); (iii) the
    unpatched bytes load (0); (iv) control: route_i patched to route_n - 1, a valid value, also loads, so a patched byte
    alone does not cause a refusal, and (v) the same for stored cell 2 moved one cell east. The two valid patches give
    a different om_world_checksum_full from the unpatched load: the route fields are hashed (the layout ruling: the
    hash "takes, in this order and at the end of the row" the same fields). Red today: getter absent."""
    _bind(lib)
    src, ids = _walker_world_at(lib, world_factory, TICK_MID)
    buf, size = _save(lib, src)
    raw = bytes(buf)
    spot = None
    pts_k = None
    for k in range(len(ids)):
        rn, ri, pts = _route_get(lib, src, ids[k])
        assert rn >= 4 and 1 <= ri < rn, "premise: walker %d has route_n %d route_i %d" % (k, rn, ri)
        hits = _locate_block(raw, rn, ri, pts[1], pts[2])
        if len(hits) == 1:
            spot = (k, rn, ri, hits[0])
            pts_k = pts
            break
    assert spot, "the route block of no walker was found uniquely in the %d save bytes" % size
    k, rn, ri, (at, wid, cwid) = spot
    print("R premise: save of %d bytes; walker index %d (unit %d) route_n %d route_i %d found once at offset %d, "
          "field width %d, cell width %d" % (size, k, ids[k], rn, ri, at, wid, cwid))

    cell2_at = None    # offset of the cx of stored point 2, found as the cells of points 1 and 2 follow the head
    head_w = raw[at + 2 * wid: at + 2 * wid + 64]
    tail1 = b"".join(_le(c, cwid) for c in (int(pts_k[1][0] // routes.CELL), int(pts_k[1][1] // routes.CELL)))
    tail2 = tail1 + b"".join(_le(c, cwid) for c in (int(pts_k[2][0] // routes.CELL), int(pts_k[2][1] // routes.CELL)))
    cell2_at = at + 2 * wid + head_w.find(tail2) + len(tail1)

    hdr = _slot_header(raw, at)
    print("R premise: slot header candidates (offset, length): %r" % (hdr,))
    assert len(hdr) == 1, "the slot header of the movement blob was not found uniquely"

    def attempt(patch_n=None, patch_i=None, patch_cx2=None, grow_to=None):
        data = bytearray(raw) if grow_to is None else _regrown(raw, at, wid, cwid, rn, grow_to, cell2_at, hdr[0])
        if patch_cx2 is not None:
            data[cell2_at:cell2_at + cwid] = _le(patch_cx2, cwid)
        if patch_n is not None:
            data[at:at + wid] = _le(patch_n, wid)
        if patch_i is not None:
            data[at + wid:at + 2 * wid] = _le(patch_i, wid)
        arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(bytes(data))
        dst = w1._prepare(lib, world_factory(n_regions=1))
        pre = _cks(lib, dst)
        rc = _load(lib, dst, arr, len(data))
        post = _cks(lib, dst)
        return rc, pre == post, post

    rc, _, _ = attempt(grow_to=rn + 1)
    print("R (i-control) route_n %d with one pair added and the slot length grown: load returned %d" % (rn + 1, rc))
    assert rc == 0, "a structurally valid save with route_n %d (one pair added) was refused: the regrown bytes are wrong" % (rn + 1)
    rc, same, _ = attempt(grow_to=OM_MOVE_WALK_PTS + 1)
    print("R (i) route_n 513, %d pairs added, slot length grown: load returned %d, target untouched %s" % (
        OM_MOVE_WALK_PTS + 1 - rn, rc, same))
    assert rc != 0, "a save with route_n 513 (> OM_MOVE_WALK_PTS) was accepted"
    assert same, "the refused load (route_n 513) changed the target world"
    rc, same, _ = attempt(patch_i=rn + 1)
    print("R (ii) route_i %d (route_n %d): load returned %d, target untouched %s" % (rn + 1, rn, rc, same))
    assert rc != 0, "a save with route_i above route_n was accepted"
    assert same, "the refused load (route_i above route_n) changed the target world"
    rc, _, c_good = attempt()
    print("R (iii) unpatched copy: load returned %d" % rc)
    assert rc == 0, "the unpatched save did not load"
    rc, _, c_i = attempt(patch_i=rn - 1)
    print("R (iv) route_i %d, a valid value: load returned %d" % (rn - 1, rc))
    assert rc == 0, "a valid patched route_i (%d of route_n %d) was refused: the patch alone breaks the load" % (rn - 1, rn)
    cx2 = int(pts_k[2][0] // routes.CELL)
    rc, _, c_cx = attempt(patch_cx2=cx2 + 1)
    print("R (v) stored cell 2 moved one cell east: load returned %d" % rc)
    assert rc == 0, "a valid patched stored cell was refused"
    # [B determinism contract] the route fields are part of the movement hash: a changed route_i or stored cell
    # changes om_world_checksum_full of the loaded world.
    assert c_i != c_good, "route_i is not hashed: a loaded route_i %d gives the same checksum_full as route_i %d" % (rn - 1, ri)
    assert c_cx != c_good, "the stored cells are not hashed: moving cell 2 one cell east left checksum_full unchanged"


# ---------------------------------------------------------------- F

def test_F_reading_a_fresh_movement_row_does_not_change_the_checksum(lib, world_factory):
    """GAP 7, green today and after (tactical_move.c:3330: "a read must never change the checksum"; the fresh-row test
    mv_row_is_fresh must cover the route fields too). Unit 2 is read first so the movement table already spans both
    ids; then unit 1, which has no movement row yet, is read with om_unit_get_pos: the row is created (the save grows,
    dumped) and om_world_checksum_full (return and nine sections) must not move. Not asserted, reported as a finding:
    the very first read of a world's highest id does change section 4 (the table grows, discovery_max)."""
    w = w1._world(lib, world_factory, w1.WALK_SEED)
    u1 = lib.om_unit_spawn(w, w1.VANGUARD, 0, 17450.0, 8450.0, 0)
    u2 = lib.om_unit_spawn(w, w1.VANGUARD, 0, 17550.0, 8450.0, 0)
    assert (u1, u2) == (1, 2)
    lib.om_unit_get_pos(w, u2)
    size0, c0 = lib.om_save_state_size(w), _cks(lib, w)
    assert lib.om_unit_get_pos(w, u1) == (17450.0, 8450.0)
    size1, c1 = lib.om_save_state_size(w), _cks(lib, w)
    print("F premise: save size %d -> %d bytes (the row of unit 1 was created by the read)" % (size0, size1))
    assert size1 > size0, "premise: the read of unit 1 created no movement row"
    assert c1 == c0, "reading a fresh movement row changed om_world_checksum_full"


# ---------------------------------------------------------------- G, K

def test_G_getter_returns_zero_without_a_route_honours_cap_and_never_moves_the_checksum(lib, world_factory):
    """Architect getter ruling: "Returns route_n (0 without a row or route), writes route_i, fills min(route_n, cap)
    interleaved (x, y) pairs ..., reads through om_move_get never om_move_touch (a read changes no checksum; test:
    checksum before and after a call equal)". Red today: getter absent."""
    fn = _bind(lib)
    w, ids = _walker_world_at(lib, world_factory, TICK_MID)
    # No row / no route.
    for unit in (0, 1_000_000):
        assert _route_get(lib, w, unit)[0] == 0, "unit id %d has no row: route_n must be 0" % unit
    idle = lib.om_unit_spawn(w, w1.VANGUARD, 0, 1000.0, 1000.0, 0)
    assert idle and _route_get(lib, w, idle)[0] == 0, "a unit with no order has route_n 0"
    # cap smaller than route_n: returns route_n, writes only cap pairs.
    n, ri, pts = _route_get(lib, w, ids[0])
    pts3 = (ctypes.c_double * 6)(*([SENT] * 6))
    ri3 = ctypes.c_uint32(0xDEADBEEF)
    n3 = fn(w, ids[0], ctypes.byref(ri3), pts3, 3)
    print("G: route_n %d with cap %d, route_i %d" % (n3, 3, ri3.value))
    assert (n3, ri3.value) == (n, ri) and n > 3, "cap 3: returned %d (route_n %d), route_i %d" % (n3, n, ri3.value)
    assert [(pts3[2 * i], pts3[2 * i + 1]) for i in range(1, 3)] == pts[1:3], "cap 3: pairs 1 and 2 differ"
    # The checksum before and after a getter call.
    pre = _cks(lib, w)
    for k in WITNESS_IDX:
        _route_get(lib, w, ids[k])
    _route_get(lib, w, idle)
    _route_get(lib, w, 1_000_000)
    assert _cks(lib, w) == pre, "a getter call changed om_world_checksum_full"


def test_K_a_unit_id_reused_after_a_tactical_reset_reports_no_route(lib, world_factory):
    """Architect layout ruling: "om_move_touch on a fresh row zeroes route_n, route_i and the flag (test: a killed id
    reused reports route_n 0)". om_tactical_reset (unit.c:2466) frees the movement state and restarts unit ids from 1;
    a unit spawned afterwards under id 1 reports route_n 0 and the checksum after the same read is unchanged. Red
    today: getter absent."""
    _bind(lib)
    w, ids = _walker_world_at(lib, world_factory, 10)
    assert _route_get(lib, w, ids[0])[0] > 1, "premise: unit %d has a route before the reset" % ids[0]
    lib.om_tactical_reset(w)
    u = lib.om_unit_spawn(w, w1.VANGUARD, 0, 17450.0, 8450.0, 0)
    print("K: unit id after the reset: %d" % u)
    assert u == ids[0], "premise: unit ids restart at %d, got %d" % (ids[0], u)
    assert _route_get(lib, w, u)[0] == 0, "the reused id %d reports a route from its previous life" % u


# ---------------------------------------------------------------- L

def _serpentine_world(lib, make):
    """A seed-1 world with its terrain replaced (om_terrain_set_heights) by flat 7000 cm ground cut by four 3-row cliff
    walls (27000 cm), gaps of LONG_GAP_CELLS cells alternating at the east and west edge: one Vanguard at LONG_START
    ordered to LONG_GOAL, starting 9 cells from the east gap, walks the corridors."""
    w = w1._world(lib, make, w1.WALK_SEED)
    cw, ch = routes._grid(lib, w)
    flat = (ctypes.c_int32 * (cw * ch))(*([LONG_FLOOR_CM] * (cw * ch)))
    for k, wy in enumerate(LONG_WALLS):
        for x in range(cw):
            gap = (x >= cw - LONG_GAP_CELLS) if k % 2 == 0 else (x < LONG_GAP_CELLS)
            if not gap:
                flat[wy * cw + x] = LONG_WALL_CM
    lib.om_terrain_set_heights.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32, ctypes.c_uint32]
    assert lib.om_terrain_set_heights(w, flat, cw, ch) == 1
    u = lib.om_unit_spawn(w, w1.VANGUARD, 0, *LONG_START, 0)
    assert u == 1 and lib.om_unit_get_layer(w, u) == 0
    assert lib.om_command_move(w, [u], 1, *LONG_GOAL) == 0
    return w, u


def _l_trace(lib, make):
    """(planner n, pts, seconds, {tick: (x, y)} at LONG_TICKS) of the case-L walker."""
    w, u = _serpentine_world(lib, make)
    n, pts, secs = _plan(lib, w, u, LONG_GOAL)
    got = {}
    for t in range(1, max(LONG_TICKS) + 1):
        lib.om_world_step(w)
        if t in LONG_TICKS:
            got[t] = lib.om_unit_get_pos(w, u)
    return w, u, n, pts, secs, got


def record_l(lib, make):
    """Recording run (not a test): the GOLDEN_L dict, from the tree as built before W2."""
    return _l_trace(lib, make)[5]


def test_L_a_plan_longer_than_512_points_stores_nothing_and_walks_as_today(lib, world_factory):
    """Architect ruling, END OF A TRUNCATED PLAN: "A plan with n > OM_MOVE_WALK_PTS stores nothing (route_n = 0) and
    keeps today's per-waypoint replan unchanged; the spec sentence 'stores the first 512' is withdrawn." One walker on
    a serpentine of cliff walls (flat ground, 240 x 240 cells) has a 724-point plan (premise dumped). The getter reports
    route_n 0 (red today: getter absent) and the walker's (x, y) at ticks 200, 400, 600, 800 and 1000 equal GOLDEN_L, recorded
    on the tree as built before W2 (green today: the per-waypoint replan unchanged), exact doubles."""
    _bind(lib)
    w, u, n, pts, secs, got = _l_trace(lib, world_factory)
    print("L premise: planner n %d (> %d), seconds %.3f, ends at %r, walk cells %d" % (
        n, OM_MOVE_WALK_PTS, secs, pts[-1], sum(routes._mask(lib, w, 0))))
    print("L positions: %r" % got)
    assert n > OM_MOVE_WALK_PTS and pts[-1] == LONG_GOAL, "premise: planner returned %d points ending at %r" % (n, pts[-1])
    assert _route_get(lib, w, u)[0] == 0, "a %d-point plan must store nothing (route_n 0)" % n
    assert got == GOLDEN_L, "the walker's trace on the >512-point plan differs from the pre-W2 record: %r" % got


# GOLDEN_L: (x, y) of the case-L walker, recorded 2026-10-13 on origin/main c2c119ea plus the docs branch (no W2 code), twice, identical;
# the plan has 724 points.
GOLDEN_L = {
    200: (23745.39368146413, 424.28605049834715),
    400: (23100.09171713164, 649.9964822902768),
    600: (22300.09171720182, 649.9999999881755),
    800: (21500.09171720182, 649.9999999999997),
    1000: (20700.09171720182, 649.9999999999997),
}
