"""VG-W2 (visible-game spec rev 12c, Lane W, paragraph "W2, stored routes"; amended by the Rev 12b "W1." paragraph, the Rev 12c
batch 2 and the Architect rulings of 2026-10-12 and 2026-10-13 on the layout, the getter and the end of a truncated plan):
a walker plans once per order and walks the stored points. Routes do not change, a layer change replans, the stored route is
saved and hashed.

Rules proved (word for word):
  [B R-001-05] "the route with the shortest travel time, changing layer wherever that shortens it"
      (docs/bible/epics/E-01-layer-system.md R-001-05: "Given a unit ordered to move to a destination, When its route is
      planned, Then it takes the route with the shortest travel time to the goal, counting each transfer, across every layer
      it may use").
  [B R-004-07] "speed / 1.1 up, x 1.1 down" (the routes may not change: R-004-07, "going up the Raider takes 4.4 seconds and
      the Bastion 16.5 seconds (speed divided by 1.1), and going down 3.6 and 13.6 seconds (speed times 1.1)").
  Spec, W2 paragraph: "the walker plans once per order or epoch change and walks the stored points; on arrival at point i it
      aims at i + 1 without replanning", "Replan only when plan_valid is 0 at order time, the epoch differs, or the destination
      changed", "Routes remain identical by construction", "a save round trip at tick 50 mid-walk restores route_n, route_i and
      the points and the walk continues to the same checksum at tick 200 as an unsaved run", "a terrain change replans",
      "the 600-walker median under 3 ms", "Named draft DRAFT-walk-tick-ms-w2 3 ms for the same 600-walker fixture".
  Architect rulings 2026-10-12/13 (taken as written, quoted in the cases): the getter om_move_route_get returns route_n (0
      without a row or route), writes route_i, fills min(route_n, cap) interleaved pairs, reads through om_move_get and never
      touches a checksum; the fourth replan trigger (a layer change); the load refusals (route_n > 512, route_i >= route_n when
      route_n > 0, route_i != 0 when route_n is 0, route_ends_at_goal > 1, a cell at or above 280, unit_id != row index);
      "A plan with n > OM_MOVE_WALK_PTS stores nothing (route_n = 0) and keeps today's per-waypoint replan unchanged".

THE FIXTURE is the W1 file's 600-walker world, imported read-only (tests/csim/test_VG_W_w1_planner.py: _walker_world :375,
_positions :391, _prepare, the constants WALK_*): seed 1 on om_terrain_generate, canvas 24,000 wu (240 x 240 cells), Vanguard
(type 2, walking), 25 x 24 walkers 40 wu apart on layer 0 from (17450, 8450), one om_command_move of all to (1850, 23950).
Dumped by the writer on origin/main c762aab4 (premises): the walkers' planned routes have 308 to 317 points (below 512); a
step moves a walker 4.4 wu; the planner ignores om_map_block_rect (see T0).

Cases. Green on the built tree (origin/main plus the docs, no W2 source): C0, T0, T, F, L_positions. Red, each for the stated
reason: P (median far above 3 ms); S A T2 E R G G2 K L_getter (the getter symbol om_move_route_get is absent, asserted by
name; R is also red for the unit_id refusal, which is absent today).
  C0   positive control: the world builds, 20 steps, walkers moved; om_move_terrain_epoch(NULL) == 0 and a live world's
       epoch is +1 after om_map_block_rect.
  P    perf: median of 20 om_world_step after 5 warm-up under DRAFT_WALK_TICK_MS_W2.
  S    save round trip mid-walk at tick 50, to tick 200.
  A    the stored route is the plan.
  T    a terrain change that changes the walkable cells (om_terrain_set_heights ditch) makes walkers go around: green today,
       no getter. T0 pins why T does not use om_map_block_rect.
  T2   the same through the getter: the stored route differs and route_i restarts.
  E    a new order replans.
  R    load refusals.
  F    fresh-row hash (GAP 7): a read does not change the checksum.
  G    the getter is a read: no checksum change; cap; no row. K: a reused id reports route_n 0.
  L    a plan longer than 512 points stores nothing and keeps today's walk.
  Architect ruling 2026-10-14 (TD-VG-W-4 controls, after the checker's findings on origin/push/vg-w2s 09130f3e):
  N1   a slope crossing of the stored route marks the route stale; the next waypoint arrival replans (seed 7, one walker).
  N2   an ORDERED layer change discards the stored route and replans at once.
  N3   a stale route is never saved as live: after an arrival or a stop the saved and hashed state has route_n 0, route_i 0.
"""
import ctypes
import math
import struct

import test_E13_R207_05_walker_routes as routes
import test_VG_W_w1_planner as w1    # imported read-only: the 600-walker fixture, so "the same fixture" holds by construction
from scale._scale_helpers import median_ns
from test_E16_S111_saving import _load, _save

SENTINEL = -12345.0
GET_CAP = 512                    # OM_MOVE_WALK_PTS, the stored-point bound the Architect ruling gives
CELL = 100.0                     # OM_TERRAIN_CELL_WU
MAX_CELLS = 280                  # OM_TERRAIN_MAX_CELLS, the fixed bound of the cell refusal
N_SECTIONS = w1.N_SECTIONS

# DRAFT-walk-tick-ms-w2, spec Lane W W2 paragraph, ledger row, Westley owns it
DRAFT_WALK_TICK_MS_W2 = 3.0

SAVE_TICK, END_TICK = 50, 200    # spec: "a save round trip at tick 50 mid-walk ... the same checksum at tick 200"
GOAL2 = (23950.0, 9450.0)        # the writer's choice: a layer-0 cell of the walkers' component, reachable in 72 points
SAMPLE = (0, 299, 599)           # indices into ids: three walkers across the grid

# (T) the ditch: cells cx 184..188, cy 100..102 (x 18400..18900, y 10000..10300). Chosen from the dump: 595 of the 600
# routes planned at tick 50 pass through it, the front walkers are 400 wu short of it at tick 50.
DITCH_CX, DITCH_CY = (184, 188), (100, 102)

# (L): flat 7000 cm terrain with seven east/west ridges (40000 cm rows) at these cell rows, each with a 4-cell gap at
# alternating ends: the walk from (250, 250) to (250, 23750) is 1895 points (dumped), above OM_MOVE_WALK_PTS 512.
L_RIDGE_ROWS = (30, 60, 90, 120, 150, 180, 210)
L_FLAT_CM, L_RIDGE_CM, L_GAP_CELLS = 7000, 40000, 4
L_LONG_START, L_LONG_GOAL = (250.0, 250.0), (250.0, 23750.0)
L_SHORT_START, L_SHORT_GOAL = (450.0, 250.0), (450.0, 2450.0)
L_TICKS = (100, 300)


# ---------------------------------------------------------------- bindings (all declared here)

def _bind(lib):
    """The internal functions this file uses, declared here. om_walk_route and om_move_terrain_epoch exist today; a symbol
    that is absent today (om_move_route_get) is looked up by name in _route_get_fn and FAILS the case, never skips it."""
    if getattr(lib, "_vgw2_bound", False):
        return
    V, P = ctypes.c_void_p, ctypes.POINTER
    routes._declare(lib)                                         # om_walk_route
    lib.om_move_terrain_epoch.argtypes = [V]
    lib.om_move_terrain_epoch.restype = ctypes.c_uint32
    lib.om_terrain_get_heights.argtypes = [V, P(ctypes.c_int32), ctypes.c_uint32]
    lib.om_terrain_get_heights.restype = ctypes.c_uint32
    lib.om_terrain_set_heights.argtypes = [V, P(ctypes.c_int32), ctypes.c_uint32, ctypes.c_uint32]
    lib.om_terrain_set_heights.restype = ctypes.c_int
    lib.om_tactical_reset.argtypes = [V]
    lib.om_tactical_reset.restype = None
    lib._vgw2_bound = True


def _route_get_fn(lib):
    """uint32_t om_move_route_get(const om_world *w, uint32_t unit_id, uint32_t *route_i, double *pts, uint32_t cap), the
    Architect ruling 2026-10-13. Absent today: the missing symbol is the stated red reason."""
    _bind(lib)
    assert hasattr(lib, "om_move_route_get"), (
        "om_move_route_get is absent from libouroboros.so (VG-W2 getter not built): csrc/om_internal.h declares it beside "
        "om_move_terrain_epoch and csrc/tactical_move.c defines it")
    fn = lib.om_move_route_get
    fn.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_double),
                   ctypes.c_uint32]
    fn.restype = ctypes.c_uint32
    return fn


def _route_read(lib, w, u, cap=GET_CAP):
    """(route_n, route_i, [(x, y)] of min(route_n, cap) pairs). Slot 0 is the unit's own pad and is never compared: the
    ruling stores planner points 1..n-1 only."""
    fn = _route_get_fn(lib)
    ri = ctypes.c_uint32(0xFFFFFFFF)
    buf = (ctypes.c_double * (2 * cap))(*([SENTINEL] * (2 * cap)))
    n = fn(w, u, ctypes.byref(ri), buf, cap)
    return n, ri.value, [(buf[2 * k], buf[2 * k + 1]) for k in range(min(n, cap))]


def _stored(lib, w, u):
    """(route_n, route_i, stored points 1..route_n - 1): slot 0 is the pad the ruling never writes or hashes, so it is never
    compared."""
    n, ri, pairs = _route_read(lib, w, u)
    return n, ri, pairs[1:]


def _full(lib, w):
    """om_world_checksum_full: (return value, the nine section words)."""
    sec = (ctypes.c_uint64 * N_SECTIONS)()
    ret = lib.om_world_checksum_full(w, sec, N_SECTIONS)
    return ret, tuple(sec)


def _pos_layer(lib, w, ids):
    return [(*lib.om_unit_get_pos(w, u), lib.om_unit_get_layer(w, u)) for u in ids]


def _steps(lib, w, n):
    for _ in range(n):
        lib.om_world_step(w)


def _world_at(lib, make, ticks):
    w, ids = w1._walker_world(lib, make)
    _steps(lib, w, ticks)
    return w, ids


def _small_walker_world(lib, make, ticks, n=10):
    """n walkers of the W1 fixture (first row, 40 wu apart, the same goal), stepped `ticks`: for cases that need a free unit
    slot (the 600-walker world is at the 600-unit cap)."""
    w = w1._world(lib, make, w1.WALK_SEED)
    ids = [lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0] + k * w1.WALK_SPACING, w1.WALK_ORIGIN[1], w1.WALK_LAYER)
           for k in range(n)]
    assert all(ids)
    assert lib.om_command_move(w, ids, len(ids), *w1.WALK_GOAL) == 0
    _steps(lib, w, ticks)
    return w, ids


def _plan(lib, w, u, goal):
    """The planner's route (n, [(x, y)]) for unit u, from its row position to goal."""
    n, pts, _ = routes._route(lib, w, u, goal[0], goal[1], cap=w1.BIG_CAP)
    return n, pts


def _cells(pts):
    return {(int(x // CELL), int(y // CELL)) for x, y in pts}


# ---------------------------------------------------------------- C0: the positive control, green today

def test_C0_positive_control_world_runs_and_the_epoch_getter_reads(lib, world_factory):
    """[B R-001-05] / [B R-004-07] fixture control. The 600-walker world builds, 20 om_world_step run and the walkers moved.
    om_move_terrain_epoch(NULL) == 0: Architect ruling 2026-10-12, the getter's fallback is 0 (tactical_move.c:555-557
    "w ? om_ms(w)->terrain_epoch : 0"); the surviving undertest mutant changed that 0 to 1, so the exact value is asserted.
    And the non-NULL branch reads the real epoch: it is the value before an om_map_block_rect plus 1 after it."""
    _bind(lib)
    w, ids = w1._walker_world(lib, world_factory)
    spawn = w1._positions(lib, w, ids)
    _steps(lib, w, 20)
    pos = w1._positions(lib, w, ids)
    moved = sum(1 for a, b in zip(spawn, pos) if a != b)
    print("C0 premise: %d of %d walkers moved in 20 steps; first walker %r -> %r" % (moved, len(ids), spawn[0], pos[0]))
    assert moved >= 1, "premise: no walker moved in 20 steps"
    # The mutant 0 -> 1 in "w ? ... : 0" (tactical_move.c:557) is killed by this exact value:
    assert lib.om_move_terrain_epoch(None) == 0, "om_move_terrain_epoch(NULL) must be 0 (ruling 2026-10-12)"
    live = w1._world(lib, world_factory, w1.WALK_SEED)
    e0 = lib.om_move_terrain_epoch(live)
    assert lib.om_map_block_rect(live, 100.0, 100.0, 300.0, 300.0, 0, 0) == 0
    e1 = lib.om_move_terrain_epoch(live)
    print("C0 premise: live world epoch %d before om_map_block_rect, %d after" % (e0, e1))
    assert e1 == e0 + 1, "a live world's epoch must be read from the world and rise by one per terrain change"


# ---------------------------------------------------------------- P: perf, red today

def test_P_a_tick_with_600_walkers_costs_less_than_the_w2_draft(lib, world_factory):
    """Spec W2: "the 600-walker median under 3 ms", "Named draft DRAFT-walk-tick-ms-w2 3 ms for the same 600-walker
    fixture": median of 20 om_world_step after 5 warm-up through median_ns (tests/csim/scale/_scale_helpers.py:93) on the
    W1 fixture. Wall clock; never loosen the 3 ms. TD-VG-W-6 (Architect 2026-10-14): the box runs gates at load 14 to 23
    of 16 cores, so one median is load noise; the test takes the MINIMUM of DRAFT-perf-repeats (7) such medians through
    w1.perf_repeats_ms (the same helper as the W1 test, TD-VG-W-5), prints all seven, and asserts the minimum under the
    unchanged 3 ms. Positive control: test_VG_W_w2_perf_control.py runs this very test with a 5 ms busy-wait injected
    into the timed step and expects it to fail. The premise (walkers still marching through the measured steps) is
    asserted before the perf line."""
    medians, marchings = w1.perf_repeats_ms(lib, world_factory)
    print("P premise: %s of 600 walkers changed position between step %d and the last step, per repeat" % (
        marchings, w1.WALK_MEDIAN_WARMUP))
    print("P median om_world_step per repeat (ms): %s" % ", ".join("%.3f" % m for m in medians))
    best = min(medians)
    print("P minimum of %d repeats: %.3f ms" % (len(medians), best))
    assert len(medians) == w1.DRAFT_PERF_REPEATS
    assert min(marchings) >= w1.PREMISE_MIN_MOVED, "premise: only %d walkers still marching" % min(marchings)
    assert best < DRAFT_WALK_TICK_MS_W2, (
        "minimum of %d medians of %d om_world_step with 600 walkers is %.3f ms, DRAFT-walk-tick-ms-w2 is %.1f ms" % (
            len(medians), w1.WALK_MEDIAN_N, best, DRAFT_WALK_TICK_MS_W2))


# ---------------------------------------------------------------- S: the save round trip, red today

def test_S_a_mid_walk_save_restores_the_stored_route_and_the_walk_continues_identically(lib, world_factory):
    """Spec W2: "a save round trip at tick 50 mid-walk restores route_n, route_i and the points and the walk continues to
    the same checksum at tick 200 as an unsaved run". 600 walkers (all keep a multi-point route: 308 to 317 points). Three
    sampled walkers are dumped; every walker's (route_n, route_i, points) through the getter is equal after the load, exact
    doubles; both worlds step to tick 200; every unit's (x, y, layer) and om_world_checksum_full (return value and the nine
    section words) of the saved-and-loaded run equal those of a world stepped straight to 200. [B R-001-05] [B R-004-07]:
    the walk is the same walk. Red today: om_move_route_get is absent."""
    _bind(lib)
    ref, ids = _world_at(lib, world_factory, SAVE_TICK)          # the unsaved reference
    src, ids_s = _world_at(lib, world_factory, SAVE_TICK)        # the world that is saved
    assert ids == ids_s
    for k in SAMPLE:
        n, ri, pairs = _route_read(lib, src, ids[k])
        print("S premise: walker %d (index %d): route_n %d, route_i %d, points 1..3 %r" % (ids[k], k, n, ri, pairs[1:4]))
        assert n > 1, "premise: route_n %d" % n
        assert 1 <= ri < n, "premise: route_i %d with route_n %d" % (ri, n)
        assert len(pairs) >= 3
    reads_src = {u: _stored(lib, src, u) for u in ids}
    buf, size = _save(lib, src)
    dst = w1._prepare(lib, world_factory(n_regions=1))
    assert _load(lib, dst, buf, size) == 0
    bad = [u for u in ids if _stored(lib, dst, u) != reads_src[u]]
    assert not bad, "after the load %d of 600 walkers read a different (route_n, route_i, points); first: unit %d, before %r, after %r" % (
        len(bad), bad[0], reads_src[bad[0]][:2], _stored(lib, dst, bad[0])[:2])
    _steps(lib, ref, END_TICK - SAVE_TICK)
    _steps(lib, dst, END_TICK - SAVE_TICK)
    p_ref, p_dst = _pos_layer(lib, ref, ids), _pos_layer(lib, dst, ids)
    diff = [k for k, (a, b) in enumerate(zip(p_ref, p_dst)) if a != b]
    assert not diff, "at tick %d %d of 600 units differ between the unsaved and the loaded run; first: unit %d %r vs %r" % (
        END_TICK, len(diff), ids[diff[0]], p_ref[diff[0]], p_dst[diff[0]])
    f_ref, f_dst = _full(lib, ref), _full(lib, dst)
    print("S checksum_full at tick %d: unsaved %016x, loaded %016x" % (END_TICK, f_ref[0], f_dst[0]))
    assert f_ref[0] == f_dst[0], "om_world_checksum_full return value differs between the unsaved and the loaded run"
    assert f_ref[1] == f_dst[1], "a checksum_full section differs: %r" % (
        [i for i in range(N_SECTIONS) if f_ref[1][i] != f_dst[1][i]],)


# ---------------------------------------------------------------- A: the stored route is the plan, red today

def test_A_the_stored_route_is_the_plan_the_planner_returns(lib, world_factory):
    """Spec W2: "the walker plans once per order ... the stored route is the same pts". [B R-001-05]: the route is the
    shortest-time route, which om_walk_route returns. Before any step the planner is asked for every walker's route from
    its position to the goal; after the first tick the getter's stored points (slots 1 to route_n - 1; slot 0 is the pad
    and is not compared) are equal to the planner's points 1.., exact doubles, route_n equals the planner's count and
    route_i is 1, the layout ruling's start index (a walker moves 4.4 wu in a tick; point 1 is at least 50 wu away).
    Red today: om_move_route_get is absent."""
    _bind(lib)
    w, ids = w1._walker_world(lib, world_factory)
    expect = {u: _plan(lib, w, u, w1.WALK_GOAL) for u in ids}
    _steps(lib, w, 1)
    k0 = SAMPLE[0]
    n0, ri0, pairs0 = _route_read(lib, w, ids[k0])
    print("A premise: walker %d planner n %d, getter route_n %d, route_i %d; planner pts[1:3] %r, getter pairs[1:3] %r" % (
        ids[k0], expect[ids[k0]][0], n0, ri0, expect[ids[k0]][1][1:3], pairs0[1:3]))
    bad = []
    for u in ids:
        n, ri, pairs = _route_read(lib, w, u)
        exp_n, exp_pts = expect[u]
        if n != exp_n or ri != 1 or pairs[1:] != exp_pts[1:]:
            bad.append((u, n, exp_n, ri))
    assert not bad, "%d of 600 stored routes differ from the planner's; first: unit %d route_n %d (planner %d), route_i %d" % (
        len(bad), *bad[0])


# ---------------------------------------------------------------- T0, T, T2: a terrain change replans

def _ditch_cells():
    return [(cx, cy) for cy in range(DITCH_CY[0], DITCH_CY[1] + 1) for cx in range(DITCH_CX[0], DITCH_CX[1] + 1)]


def _in_ditch(p):
    return DITCH_CX[0] * CELL <= p[0] < (DITCH_CX[1] + 1) * CELL and DITCH_CY[0] * CELL <= p[1] < (DITCH_CY[1] + 1) * CELL


def _dig_ditch(lib, w):
    """Terrain change that the planner sees: the heights of the ditch cells go to 0 cm (below the dry level, so the band
    floors stay), through om_terrain_set_heights (K-e5 test hook), which re-derives the walk masks and bumps the epoch."""
    n = 240 * 240
    heights = (ctypes.c_int32 * n)()
    assert lib.om_terrain_get_heights(w, heights, n) == n
    for cx, cy in _ditch_cells():
        heights[cy * 240 + cx] = 0
    e0 = lib.om_move_terrain_epoch(w)
    assert lib.om_terrain_set_heights(w, heights, 240, 240) == 1
    assert lib.om_move_terrain_epoch(w) == e0 + 1, "the terrain change must bump the epoch"


def test_T0_block_rect_bumps_the_epoch_but_the_planner_does_not_see_it(lib, world_factory):
    """Premise of case T, dumped (the brief named om_map_block_rect; the dump shows it cannot make walkers go around).
    om_map_block_rect writes the mapgen blocked bits and bumps the epoch (om_move_terrain_changed), but om_walk_route reads
    only om_terrain_walk_mask (csrc/walk_route.c:232, csrc/terrain.c:1251), derived at generate and by
    om_terrain_apply_ground: a rectangle across the walkers' path leaves every planned route byte-equal. So a block_rect
    replan produces the same route, and T uses a change the planner sees. Green today."""
    _bind(lib)
    w, ids = _world_at(lib, world_factory, SAVE_TICK)
    before = _plan(lib, w, ids[0], w1.WALK_GOAL)
    cx0, cx1 = DITCH_CX
    cy0, cy1 = DITCH_CY
    e0 = lib.om_move_terrain_epoch(w)
    assert lib.om_map_block_rect(w, cx0 * CELL, cy0 * CELL, (cx1 + 1) * CELL, (cy1 + 1) * CELL, 0, 0) == 0
    after = _plan(lib, w, ids[0], w1.WALK_GOAL)
    through = _cells(before[1]) & set(_ditch_cells())
    print("T0 premise: epoch %d -> %d; the planned route (%d points) passes %d of the rectangle's cells, identical after: %s" % (
        e0, lib.om_move_terrain_epoch(w), before[0], len(through), before == after))
    assert lib.om_move_terrain_epoch(w) == e0 + 1
    assert through, "premise: the rectangle is not on walker %d's path" % ids[0]
    assert before == after, "om_map_block_rect changed the planner's route: case T could use it"


def test_T_a_terrain_change_across_the_path_makes_the_walkers_go_around(lib, world_factory):
    """Spec W2: "a terrain change ... mid-walk replans (control green today)". [B R-001-05]: the shortest-time route on the
    changed terrain. Control, no getter. After tick 50 a 5 x 3 cell ditch (om_terrain_set_heights, T0 says why not
    om_map_block_rect) is dug across the walkers' path. How the ditch was proved to be on the path: (a) 595 of the 600
    routes planned at tick 50 pass through its cells; (b) in an identical twin world without the ditch, walkers stand inside
    the ditch rectangle during ticks 50..250 (premise asserted); (c) no walker stands in it at tick 50. In the ditched world
    no unit stands inside the rectangle on any of the 200 ticks after the change, the new planned route of every affected
    walker avoids it, and the affected walkers are still progressing: their summed distance to the goal fell."""
    _bind(lib)
    twin, ids = _world_at(lib, world_factory, SAVE_TICK)
    w, ids2 = _world_at(lib, world_factory, SAVE_TICK)
    assert ids == ids2
    start = w1._positions(lib, w, ids)
    ditch = set(_ditch_cells())
    old = {u: _plan(lib, w, u, w1.WALK_GOAL) for u in ids}
    affected = [u for u in ids if _cells(old[u][1][1:]) & ditch]
    assert not any(_in_ditch(p) for p in start), "premise: a walker stands in the ditch rectangle at tick 50"
    print("T premise: %d of %d routes planned at tick %d pass through the ditch rectangle" % (len(affected), len(ids), SAVE_TICK))
    assert affected
    twin_max = 0
    for _ in range(END_TICK):
        _steps(lib, twin, 1)
        twin_max = max(twin_max, sum(1 for p in w1._positions(lib, twin, ids) if _in_ditch(p)))
    print("T control: in the twin without the ditch up to %d walkers stand in the rectangle on one tick" % twin_max)
    assert twin_max > 0, "premise: the ditch rectangle is not on the walkers' path (no walker of the twin enters it)"
    _dig_ditch(lib, w)
    for u in affected:
        n, pts = _plan(lib, w, u, w1.WALK_GOAL)
        assert not (_cells(pts[1:]) & ditch), "premise: the planner's new route of unit %d still crosses the ditch" % u
    worst = 0
    for _ in range(END_TICK):
        _steps(lib, w, 1)
        worst = max(worst, sum(1 for p in w1._positions(lib, w, ids) if _in_ditch(p)))
    end = w1._positions(lib, w, ids)
    assert worst == 0, "%d walkers stood inside the dug rectangle on one tick after the change" % worst

    def dist(p):
        return math.hypot(p[0] - w1.WALK_GOAL[0], p[1] - w1.WALK_GOAL[1])

    idx = {u: i for i, u in enumerate(ids)}
    before = sum(dist(start[idx[u]]) for u in affected)
    after = sum(dist(end[idx[u]]) for u in affected)
    fell = sum(1 for u in affected if dist(end[idx[u]]) < dist(start[idx[u]]))
    print("T: affected walkers summed distance to the goal %.1f -> %.1f; %d of %d individually closer" % (before, after, fell, len(affected)))
    assert after < before, "the affected walkers did not progress toward the goal"


def test_T2_a_terrain_change_replans_the_stored_route_and_route_i_restarts(lib, world_factory):
    """The same change through the getter. The stored route of a walker whose route crosses the ditch differs from the one
    stored before (a control twin world, no change, keeps its stored points one tick later: no replan without a trigger),
    and its route_i restarts: it was above 1 before for the walkers that had passed a point (they moved 220 wu) and is 1 for every walker after the replan tick (Architect layout
    ruling: route_i starts at 1; the first aim is at least 50 wu away so one tick cannot advance it). Spec W2: "a terrain
    epoch change ... clears the stored route and replans". Red today: om_move_route_get is absent."""
    _bind(lib)
    twin, ids = _world_at(lib, world_factory, SAVE_TICK)
    w, _ = _world_at(lib, world_factory, SAVE_TICK)
    ditch = set(_ditch_cells())
    old = {u: _plan(lib, w, u, w1.WALK_GOAL) for u in ids}
    affected = [u for u in ids if _cells(old[u][1][1:]) & ditch]
    stored_before = {u: _stored(lib, w, u) for u in ids}
    twin_before = {u: _stored(lib, twin, u) for u in ids}
    advanced = sum(1 for u in affected if stored_before[u][1] > 1)
    print("T2 premise: %d affected walkers, %d with route_i above 1 before the change; walker %d route_n %d, route_i %d" % (
        len(affected), advanced, affected[0], stored_before[affected[0]][0], stored_before[affected[0]][1]))
    assert advanced > 0, "premise: every route_i is still at its start index at tick %d" % SAVE_TICK
    _dig_ditch(lib, w)
    _steps(lib, w, 1)
    _steps(lib, twin, 1)
    same_twin = [u for u in ids if _stored(lib, twin, u)[2] != twin_before[u][2]]
    assert not same_twin, "control: %d twin walkers changed their stored points with no trigger (first: unit %d)" % (
        len(same_twin), same_twin[0])
    still = [u for u in affected if _stored(lib, w, u)[2] == stored_before[u][2]]
    assert not still, "%d affected walkers kept the stored route after the terrain change; first: unit %d" % (len(still), still[0])
    restarted = [u for u in ids if _stored(lib, w, u)[1] != 1]
    assert not restarted, "%d walkers' route_i did not restart at 1; first: unit %d route_i %d" % (
        len(restarted), restarted[0], _stored(lib, w, restarted[0])[1])


# ---------------------------------------------------------------- E: a new order replans, red today

def test_E_a_new_order_replaces_the_stored_route_with_one_ending_at_the_new_destination(lib, world_factory):
    """Spec W2: "Replan only when ... the destination changed". At tick 50 every walker gets a second om_command_move to
    GOAL2. After the next tick the stored route is the planner's route to GOAL2 (planned from the position at the order,
    points 1.. exact), ends at GOAL2, route_i is 1, and it differs from the route stored before. [B R-001-05]. Red today:
    om_move_route_get is absent."""
    _bind(lib)
    w, ids = _world_at(lib, world_factory, SAVE_TICK)
    old = {u: _route_read(lib, w, u) for u in ids}
    assert lib.om_command_move(w, ids, len(ids), *GOAL2) == 0
    expect = {u: _plan(lib, w, u, GOAL2) for u in ids}
    n0, p0 = expect[ids[0]]
    print("E premise: walker %d planner route to GOAL2 %r has %d points, last %r; stored before has route_n %d" % (
        ids[0], GOAL2, n0, p0[-1], old[ids[0]][0]))
    assert p0[-1] == GOAL2, "premise: GOAL2 is not reachable for walker %d" % ids[0]
    _steps(lib, w, 1)
    bad = []
    for u in ids:
        n, ri, pairs = _route_read(lib, w, u)
        exp_n, exp_pts = expect[u]
        if n != exp_n or ri != 1 or pairs[1:] != exp_pts[1:] or pairs[-1] != exp_pts[-1] or pairs[1:] == old[u][2][1:]:
            bad.append((u, n, exp_n, ri))
    assert not bad, "%d of 600 stored routes are not the new order's plan; first: unit %d route_n %d (planner %d), route_i %d" % (
        len(bad), *bad[0])


# ---------------------------------------------------------------- R: load refusals, red today

def _find_block(raw, n, ri, cell):
    """Locate a walker's route block without a hard-coded offset: the bytes route_n, route_i, a flag word (0 or 1, the
    getter cannot tell route_ends_at_goal: the last point is the same either way for a goal at a cell centre) and the cell
    (cx, cy) of the first stored point, little-endian, with the word width 4, then 8, then 2 bytes. Returns (width, offset of
    route_n, flag) of the first match."""
    for width in (4, 8, 2):
        def word(v):
            return int(v).to_bytes(width, "little")
        for flag in (1, 0):
            pat = word(n) + word(ri) + word(flag) + word(cell[0]) + word(cell[1])
            at = raw.find(pat)
            if at >= 0:
                return width, at, flag
    return None


def _patched(raw, at, width, slot, value):
    """A copy of raw with the width-byte word number `slot` after offset `at` set to `value`."""
    out = bytearray(raw)
    out[at + slot * width: at + (slot + 1) * width] = int(value).to_bytes(width, "little")
    return out


def _try_load(lib, make, data, label):
    """Load `data` into a fresh world of the same construction; return (rc, checksum_full before, after)."""
    size = len(data)
    buf = (ctypes.c_uint8 * size).from_buffer(bytearray(data))
    dst = w1._prepare(lib, make(n_regions=1))
    before = _full(lib, dst)
    rc = _load(lib, dst, buf, size)
    after = _full(lib, dst)
    print("R %s: om_load_state_read returned %d; target checksum_full %s" % (label, rc, "unchanged" if before == after else "CHANGED"))
    return rc, before, after


def test_R_a_save_with_a_bad_route_block_is_refused_and_leaves_the_target_untouched(lib, world_factory):
    """Architect layout ruling 2026-10-13 (taken as written): "Read rejects: route_n > OM_MOVE_WALK_PTS, (route_n ?
    route_i >= route_n : route_i != 0), route_ends_at_goal > 1, any cx or cy >= OM_TERRAIN_MAX_CELLS (280; a fixed bound
    ...), and after mu->unit_id = mv_get_u32(&r) add: if (mu->unit_id != id) r.ok = 0". [B R-111-03 in spirit]: "a refused
    load never touches the destination world" (csrc/save.c). A mid-walk save is taken at tick 50; one walker's route block
    is found in the bytes (see _find_block: the exact route_n, route_i, flag, first cell read through the getter, word width
    tried 4, 8, 2; the match offset and width are printed) and patched: route_n 513; route_i = route_n + 1; route_i =
    route_n; route_ends_at_goal 2; cx 280; cy 280; route_n 0 with route_i 1; and the walker's unit_id word (found by its
    in_use, unit_id, x, y bytes) altered. Each is refused (non-zero) and the target world's checksum_full is unchanged.
    Controls: the unpatched bytes load (0), and a patch to a VALID value (route_i + 1) loads (0), so the patching itself
    does not break a load. Red today: om_move_route_get is absent."""
    _bind(lib)
    src, ids = _world_at(lib, world_factory, SAVE_TICK)
    u = ids[0]
    n, ri, pairs = _route_read(lib, src, u)
    cell = (int(pairs[1][0] // CELL), int(pairs[1][1] // CELL))
    assert 1 <= ri < n - 1 and n > 2, "premise: route_n %d route_i %d" % (n, ri)
    buf, size = _save(lib, src)
    raw = bytes(buf)
    found = _find_block(raw, n, ri, cell)
    print("R premise: walker %d route_n %d route_i %d first cell %r; save %d bytes; route block found (width, offset, flag): %r" % (
        u, n, ri, cell, size, found))
    assert found is not None, "the walker's route block (route_n, route_i, flag, cx, cy) is not in the save bytes with 2, 4 or 8 byte words"
    width, at, _flag = found
    x, y = lib.om_unit_get_pos(src, u)
    row = struct.pack("<I", 1) + struct.pack("<I", u) + struct.pack("<d", x) + struct.pack("<d", y)
    row_at = raw.find(row)
    print("R premise: unit row (in_use, unit_id, x, y) found at byte %d (%d matches)" % (row_at, raw.count(row)))
    assert row_at >= 0, "the unit row (in_use, unit_id, x, y) is not in the save bytes"
    rc, _, _ = _try_load(lib, world_factory, raw, "control unpatched")
    assert rc == 0, "control: the unpatched mid-walk save does not load (%d)" % rc
    rc, _, _ = _try_load(lib, world_factory, bytes(_patched(raw, at, width, 1, ri + 1)), "control route_i %d (valid)" % (ri + 1))
    assert rc == 0, "control: a valid route_i patch does not load (%d)" % rc
    row_patch = bytearray(raw)
    row_patch[row_at + 4: row_at + 8] = struct.pack("<I", u + 2)
    cases = [
        ("route_n 513", bytes(_patched(raw, at, width, 0, 513))),
        ("route_i above route_n", bytes(_patched(raw, at, width, 1, n + 1))),
        ("route_i == route_n", bytes(_patched(raw, at, width, 1, n))),
        ("route_ends_at_goal 2", bytes(_patched(raw, at, width, 2, 2))),
        ("cx 280", bytes(_patched(raw, at, width, 3, MAX_CELLS))),
        ("cy 280", bytes(_patched(raw, at, width, 4, MAX_CELLS))),
        ("route_n 0 with route_i 1", bytes(_patched(raw, at, width, 0, 0))),
        ("unit_id altered", bytes(row_patch)),
    ]
    missed = []
    for label, data in cases:
        rc, before, after = _try_load(lib, world_factory, data, label)
        if rc == 0:
            missed.append("%s: accepted" % label)
        elif before != after:
            missed.append("%s: refused but the target world changed" % label)
    assert not missed, "load refusals missing: %s" % "; ".join(missed)


# ---------------------------------------------------------------- F: fresh-row hash (GAP 7), green today and after

def test_F_a_read_of_a_position_does_not_change_the_checksum_of_an_idle_row(lib, world_factory):
    """GAP 7 (csrc/tactical_move.c:3330, "A row still in the state om_move_touch gives a new row hashes as an absent one:
    reads such as om_unit_get_pos create rows lazily, and a read must never change the checksum"). After W2 the row carries
    route_n, route_i, a flag and plan_layer, and a still-default row must keep hashing as absent: idle units in a stepped
    world are read with om_unit_get_pos and om_world_checksum_full (return value and nine sections) must not move. Green
    today and after.
    SCOPE NARROWED, said in the report: the brief's literal case (a unit spawned after the last step, its first read creates
    the row) is red TODAY: the movement section (4) changes because the read raises ms->discovery_max (hashed first at
    om_move_section_hash) or creates the move state; that is a finding for the Architect, not a W2 requirement, and is not
    asserted here."""
    _bind(lib)
    w = w1._world(lib, world_factory, w1.WALK_SEED)
    ids = [lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0] + 40.0 * k, w1.WALK_ORIGIN[1], w1.WALK_LAYER) for k in range(5)]
    assert all(ids)
    _steps(lib, w, 3)
    before = _full(lib, w)
    size0 = lib.om_save_state_size(w)
    for u in ids:
        lib.om_unit_get_pos(w, u)
        lib.om_unit_get_layer(w, u)
    after = _full(lib, w)
    print("F premise: 5 idle units, 3 steps; save size %d -> %d; sections changed: %r" % (
        size0, lib.om_save_state_size(w), [i for i in range(N_SECTIONS) if before[1][i] != after[1][i]]))
    assert before == after, "a position read changed om_world_checksum_full"


# ---------------------------------------------------------------- G, K: the getter is a read, red today

def test_G_the_getter_is_a_read_and_obeys_cap_and_a_missing_row(lib, world_factory):
    """Architect getter ruling 2026-10-13 (taken as written): "Returns route_n (0 without a row or route), writes route_i,
    fills min(route_n, cap) interleaved (x, y) pairs ..., reads through om_move_get never om_move_touch (a read changes no
    checksum; test: checksum before and after a call equal)". A 10-walker world (the 600-unit world has no free slot) stepped to tick 20 with a unit spawned afterwards (it
    has no movement row; touching it would raise discovery_max and move the movement section): the getter returns 0 for it,
    for id 0 and for an id that does not exist, and no call changes om_world_checksum_full. With cap 3 the call still
    returns route_n and writes exactly three pairs (the rest of the buffer keeps its sentinel). Red today: absent."""
    _bind(lib)
    w, ids = _small_walker_world(lib, world_factory, 20)         # the 600-unit world is at the 600-unit cap: no 601st unit
    late = lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0] + 600.0, w1.WALK_ORIGIN[1], w1.WALK_LAYER)
    assert late == len(ids) + 1, "premise: the late unit was not spawned (%d)" % late
    before = _full(lib, w)
    n_full, ri_full, pairs_full = _route_read(lib, w, ids[0])
    assert n_full > 3
    ri = ctypes.c_uint32(0)
    small = (ctypes.c_double * (2 * n_full))(*([SENTINEL] * (2 * n_full)))
    n_small = _route_get_fn(lib)(w, ids[0], ctypes.byref(ri), small, 3)
    written = sum(1 for k in range(n_full) if small[2 * k] != SENTINEL or small[2 * k + 1] != SENTINEL)
    print("G premise: route_n %d, route_i %d; with cap 3: returned %d, pairs written %d" % (n_full, ri_full, n_small, written))
    assert n_small == n_full and ri.value == ri_full, "cap 3: returned %d (route_n %d), route_i %d" % (n_small, n_full, ri.value)
    assert written == 3 and [(small[2 * k], small[2 * k + 1]) for k in range(3)] == pairs_full[:3], "cap 3 must write exactly the first three pairs"
    for u in (late, 0, 99999):
        assert _route_read(lib, w, u)[0] == 0, "unit %d has no movement row and must report route_n 0" % u
    after = _full(lib, w)
    assert before == after, "calling the getter changed om_world_checksum_full (it must read through om_move_get, not om_move_touch)"


def test_G2_the_getter_on_a_world_without_movement_state_reads_zero_and_changes_nothing(lib, world_factory):
    """The same sentence for a world that never stepped (no movement state yet): a read changes no checksum. Red today:
    absent."""
    _bind(lib)
    w = w1._world(lib, world_factory, w1.WALK_SEED)
    u = lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0], w1.WALK_ORIGIN[1], w1.WALK_LAYER)
    before = _full(lib, w)
    assert _route_read(lib, w, u)[0] == 0
    assert _full(lib, w) == before, "the getter changed om_world_checksum_full on a world without movement state"


def test_K_a_reused_unit_id_reports_route_n_zero(lib, world_factory):
    """Architect layout ruling: "om_move_touch on a fresh row zeroes route_n, route_i, the flag and plan_layer (test: a
    killed id reused reports route_n 0)". Ids are reused only after om_tactical_reset (csrc/unit.c:2460, "A reset battle
    reuses unit ids from 1"): a walker with a stored route, the reset, a new unit that gets the same id, a step: the new
    unit's route_n is 0 and route_i 0. Red today: absent."""
    _bind(lib)
    w, ids = _world_at(lib, world_factory, 5)
    n, ri, _ = _route_read(lib, w, ids[0])
    print("K premise: unit %d had route_n %d, route_i %d before the reset" % (ids[0], n, ri))
    assert n > 1
    lib.om_tactical_reset(w)
    assert lib.om_roster_set_movement_kind(w, w1.VANGUARD, w1.KIND_WALKING) == 0
    again = lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0], w1.WALK_ORIGIN[1], w1.WALK_LAYER)
    assert again == ids[0], "premise: the reset did not reuse id %d (got %d)" % (ids[0], again)
    _steps(lib, w, 1)
    assert _route_read(lib, w, again)[:2] == (0, 0), "a reused id must start with no stored route"


# ---------------------------------------------------------------- L: a plan longer than 512 points

def _long_world(lib, make):
    """Flat terrain with seven ridges (alternating 4-cell gaps) through om_terrain_set_heights; a long walker and a short
    walker, each ordered to its goal."""
    w = w1._world(lib, make, w1.WALK_SEED)
    n = 240 * 240
    heights = (ctypes.c_int32 * n)(*([L_FLAT_CM] * n))
    for k, row in enumerate(L_RIDGE_ROWS):
        for cx in range(240):
            gap = cx >= 240 - L_GAP_CELLS if k % 2 == 0 else cx < L_GAP_CELLS
            if not gap:
                heights[row * 240 + cx] = L_RIDGE_CM
    assert lib.om_terrain_set_heights(w, heights, 240, 240) == 1
    long_u = lib.om_unit_spawn(w, w1.VANGUARD, 0, *L_LONG_START, 0)
    short_u = lib.om_unit_spawn(w, w1.VANGUARD, 0, *L_SHORT_START, 0)
    assert long_u and short_u
    assert lib.om_command_move(w, [long_u], 1, *L_LONG_GOAL) == 0
    assert lib.om_command_move(w, [short_u], 1, *L_SHORT_GOAL) == 0
    return w, long_u, short_u


def record_l(lib, make):
    """Recording run (not a test): GOLDEN_L, (x, y, layer) of the long and the short walker at L_TICKS, from the tree as built."""
    _bind(lib)
    w, lu, su = _long_world(lib, make)
    out = {}
    t = 0
    for stop in L_TICKS:
        _steps(lib, w, stop - t)
        t = stop
        out[stop] = tuple(_pos_layer(lib, w, (lu, su)))
    return out


def test_L_positions_a_plan_beyond_512_points_walks_as_today(lib, world_factory):
    """Rule: "Routes remain identical by construction"; Architect ruling: "A plan with n > OM_MOVE_WALK_PTS stores nothing
    (route_n = 0) and keeps today's per-waypoint replan unchanged". Premise dumped: the long walker's plan has 1895 points,
    the short walker's 23. The two walkers' (x, y, layer) at ticks 100 and 300 equal GOLDEN_L, recorded by the writer on
    origin/main c762aab4 (the per-waypoint replan), twice in two processes, identical. Green today; the detector of the
    ruling "GOLDEN_B and GOLDEN_ROUTES are the detector" for the long plan and the short stored route in open terrain."""
    _bind(lib)
    w, lu, su = _long_world(lib, world_factory)
    n_long, _ = _plan(lib, w, lu, L_LONG_GOAL)
    n_short, _ = _plan(lib, w, su, L_SHORT_GOAL)
    print("L premise: long plan %d points, short plan %d points (OM_MOVE_WALK_PTS %d)" % (n_long, n_short, GET_CAP))
    assert n_long > GET_CAP >= n_short
    t = 0
    for stop in L_TICKS:
        _steps(lib, w, stop - t)
        t = stop
        got = tuple(_pos_layer(lib, w, (lu, su)))
        assert got == GOLDEN_L[stop], "tick %d: (long, short) walkers at %r, table %r" % (stop, got, GOLDEN_L[stop])


def test_L_getter_a_plan_beyond_512_points_stores_nothing_and_a_short_one_does(lib, world_factory):
    """The Architect's end-of-plan ruling through the getter: the long walker (1895 points, above OM_MOVE_WALK_PTS 512)
    reports route_n 0 after the first tick and after 300 ticks, still moving (its position changed), while the short
    walker in the same world (23 points) reports route_n 23 and a valid route_i: control, so a 0 means 'not stored' and not
    'getter broken'. Red today: om_move_route_get is absent."""
    _bind(lib)
    w, lu, su = _long_world(lib, world_factory)
    n_short, _ = _plan(lib, w, su, L_SHORT_GOAL)
    start = _pos_layer(lib, w, (lu,))[0]
    for tick in (1, 300):
        _steps(lib, w, 1 if tick == 1 else 299)
        ln, lri, _ = _route_read(lib, w, lu)
        sn, sri, _ = _route_read(lib, w, su)
        print("L tick %d: long route_n %d (route_i %d), short route_n %d (route_i %d)" % (tick, ln, lri, sn, sri))
        assert sn == n_short and 1 <= sri < sn, "control: the short walker's stored route is route_n %d route_i %d (planner %d)" % (sn, sri, n_short)
        assert ln == 0, "a 1895-point plan must store nothing, route_n is %d" % ln
    assert _pos_layer(lib, w, (lu,))[0] != start, "premise: the long walker did not move"


# ---------------------------------------------------------------- N1, N2, N3: the Architect ruling of 2026-10-14

STALE_SEED, STALE_CANVAS = 7, 12000.0
STALE_START, STALE_START_LAYER, STALE_GOAL = (10450.0, 4450.0), 1, (7150.0, 1550.0)
STALE_TICKS = (41, 42, 48, 1200)


def _stale_world(lib, make):
    """The checker's single-walker world: seed 7 on a 12,000 wu canvas (120 x 120 cells), one walking Vanguard (id 1) on layer 1
    at STALE_START, ordered to STALE_GOAL (a goal the planner cannot reach: it paths to a stand-in cell and stops)."""
    _bind(lib)
    w = make(n_regions=1)
    lib.om_world_set_feature(w, w1.OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, STALE_CANVAS, STALE_CANVAS) == 0
    assert lib.om_terrain_generate(w, STALE_SEED, STALE_CANVAS, STALE_CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, w1.VANGUARD, w1.KIND_WALKING) == 0
    u = lib.om_unit_spawn(w, w1.VANGUARD, 0, *STALE_START, STALE_START_LAYER)
    assert u == 1, "premise: the walker is unit id 1 (got %d)" % u
    assert lib.om_command_move(w, [u], 1, *STALE_GOAL) == 0
    return w, u


def test_N1_a_slope_crossing_of_the_stored_route_is_stale_and_the_next_waypoint_replans_like_the_old_walker(lib, world_factory):
    """Architect ruling 2026-10-14 (TD-VG-W-4 control): "a slope crossing made by the walker's stored route updates plan_layer
    (no replan at the crossing; the slope tests stay green) and marks the stored route STALE; at the NEXT waypoint arrival the
    walker discards it and replans on its current layer, exactly as the old walker did, so routes and `seconds` are
    byte-identical to the old tree again". [B R-004-07] the slope crossing; [B R-001-05] a goal blocked on every layer: the
    unit "paths as close as it can and stops". Seed 7, 12,000 wu canvas, one walker (unit id 1, layer 1) from (10450, 4450)
    to the unreachable (7150, 1550). It climbs from layer 1 to 2 at tick 42 by the walker's own slope crossing. GOLDEN_STALE is
    the old tree's (the unmodified walker, per-waypoint replan; measured by the checker and re-measured by the writer on
    origin/main b64ff6d2): at tick 48 (10275.45454545453, 4450.0, layer 2); at tick 1200 it stands at (6750, 2850) on layer 3.
    The build at 09130f3e keeps the pre-crossing stored route past the crossing and gives (10276.216182500768,
    4447.773099120325, 2) at tick 48. The positions at ticks 48 and 1200 must be equal to the old tree's, exactly."""
    w, u = _stale_world(lib, world_factory)
    n, pts = _plan(lib, w, u, STALE_GOAL)
    print("N1 premise: planner route %d points, last %r, goal %r" % (n, pts[-1], STALE_GOAL))
    assert pts[-1] != STALE_GOAL, "premise: the goal is reachable, it must not be"
    t = 0
    for stop in STALE_TICKS:
        _steps(lib, w, stop - t)
        t = stop
        got = _pos_layer(lib, w, (u,))[0]
        if stop == 41:
            assert got[2] == 1, "premise: the walker already left layer 1 at tick 41 (%r)" % (got,)
        elif stop == 42:
            assert got[2] == 2, "premise: the walker did not climb from layer 1 to 2 at tick 42 (%r)" % (got,)
        else:
            print("N1 tick %d: walker at %r, old tree %r" % (stop, got, GOLDEN_STALE[stop]))
            assert got == GOLDEN_STALE[stop], "tick %d: walker at %r, the old tree (per-waypoint replan) at %r" % (
                stop, got, GOLDEN_STALE[stop])


LAYER_ORDER_TARGET, LAYER_ORDER_TICKS = 3, (24, 25, 50)


def test_N2_an_ordered_layer_change_discards_the_stored_route_and_replans_at_once(lib, world_factory):
    """Architect ruling 2026-10-14 (TD-VG-W-4 control): the stale-route rule covers only "a slope crossing made by the walker's
    stored route"; every other layer change of a walker with a stored route replans at once on the new layer (the fourth
    replan trigger, ruling 2026-10-13: "a layer change"). [B R-001-05] the route is planned from where the unit is, on the
    layer it is on. A walker is ordered to another layer by om_command_set_layer, which R-001-07 makes a no-op for a walker
    (tests/csim/test_E01_R001_07_walking_kind.py), so the order is given while the Vanguard type is set to flying and the type
    is set back to walking before the first step; the transfer lands at tick 25 on the old tree and on the build. Ten walkers
    of the W1 fixture at tick 50 hold a 317-point route (route_i 3 or more); unit 1 is ordered to layer 3. At tick 24 it is
    still on layer 0 and its route equals the twin's (a twin world without the order keeps route_n 317 and a route_i above 1
    at tick 25: the control that a restart at 1 is the order's doing); at tick 25 it is on layer 3 and its stored route is NOT
    the old one (route_n differs, route_i is 1, re-stored: route_n 2 or more); its positions at ticks 25 and 50 equal
    GOLDEN_LAYER_ORDER, measured on origin/main b64ff6d2 (the old walker replans every waypoint). May already be green on the
    build: then it is the positive control of the ruling."""
    _bind(lib)
    ref, ids = _small_walker_world(lib, world_factory, 50)
    w, ids_w = _small_walker_world(lib, world_factory, 50)
    assert ids == ids_w
    u = ids[0]
    before = _route_read(lib, w, u)
    print("N2 premise: unit %d layer %d, route_n %d, route_i %d at tick 50" % (u, lib.om_unit_get_layer(w, u), before[0], before[1]))
    assert before[0] > 2 and before[1] > 1 and lib.om_unit_get_layer(w, u) == 0, "premise: no stored route on layer 0"
    assert lib.om_roster_set_movement_kind(w, w1.VANGUARD, 0) == 0                 # flying, for the order only
    assert lib.om_command_set_layer(w, (ctypes.c_uint32 * 1)(u), 1, LAYER_ORDER_TARGET) == 0
    assert lib.om_roster_set_movement_kind(w, w1.VANGUARD, w1.KIND_WALKING) == 0
    t = 0
    for stop in LAYER_ORDER_TICKS:
        _steps(lib, w, stop - t)
        _steps(lib, ref, stop - t)
        t = stop
        got, route, twin = _pos_layer(lib, w, (u,))[0], _route_read(lib, w, u), _route_read(lib, ref, u)
        print("N2 tick %d: walker at %r, route_n %d route_i %d; twin without the order: route_n %d route_i %d" % (
            stop, got, route[0], route[1], twin[0], twin[1]))
        if stop == LAYER_ORDER_TICKS[0]:
            assert got[2] == 0, "premise: the transfer landed before tick 25 (%r)" % (got,)
            assert route[:2] == twin[:2], "no layer change yet, but the stored route differs from the twin's"
        elif stop == LAYER_ORDER_TICKS[1]:
            assert got[2] == LAYER_ORDER_TARGET, "premise: the transfer did not land at tick 25 (%r)" % (got,)
            assert twin[0] == before[0] and twin[1] > 1, "control: the twin's route_n %d route_i %d" % (twin[0], twin[1])
            assert route[0] >= 2 and route[1] == 1 and route[0] != before[0], (
                "an ordered layer change must replan at once on the new layer: route_n %d route_i %d (stored before: %d, %d)" % (
                    route[0], route[1], before[0], before[1]))
        assert got == GOLDEN_LAYER_ORDER.get(stop, got), "tick %d: walker at %r, the old tree at %r" % (
            stop, got, GOLDEN_LAYER_ORDER.get(stop))


def _n3_check(lib, make, w, dead, live, label):
    """`dead` units have no order (the event happened), `live` units are walking. The saved and hashed state must carry route_n 0
    and route_i 0 for every dead unit, read through the getter before the save and after the load; two saves of the same world
    are byte-identical; the load reproduces om_world_checksum_full; the live units' routes round-trip (the control that a 0 is
    not the getter failing)."""
    stale = {u: _route_read(lib, w, u)[:2] for u in dead}
    print("N3 %s: dead units' (route_n, route_i) %r; live units' %r" % (label, stale, {u: _route_read(lib, w, u)[:2] for u in live}))
    assert all(_route_read(lib, w, u)[0] > 1 for u in live), "premise: a live unit has no stored route"
    assert all(v == (0, 0) for v in stale.values()), "%s: a unit with no order still carries a stored route (route_n, route_i): %r" % (
        label, {u: v for u, v in stale.items() if v != (0, 0)})
    buf1, size1 = _save(lib, w)
    buf2, size2 = _save(lib, w)
    assert bytes(buf1) == bytes(buf2), "%s: two saves of the same world differ" % label
    dst = w1._prepare(lib, make(n_regions=1))
    assert _load(lib, dst, buf1, size1) == 0
    for u in dead:
        assert _route_read(lib, dst, u)[:2] == (0, 0), "%s: after the load unit %d carries a stored route" % (label, u)
    for u in live:
        assert _stored(lib, dst, u) == _stored(lib, w, u), "%s: after the load live unit %d reads a different route" % (label, u)
    assert _full(lib, dst) == _full(lib, w), "%s: om_world_checksum_full differs after the round trip" % label


def test_N3_a_walker_that_arrived_saves_and_hashes_no_route(lib, world_factory):
    """Architect ruling 2026-10-14 (TD-VG-W-4 control, finding F2 of the checker): a stale route is never saved as live; after a
    plan_valid = 0 or has_dest = 0 event (arrival, relocation, terrain guard, transit) the saved and hashed state carries
    route_n 0 and route_i 0. Event here: the arrival. One walker is ordered to the sixth point of its own planned route (a
    reachable cell, about 550 wu away) and stepped until it stops; a second walker keeps walking the long route (the control).
    Expected green on the build: the arrival branch clears the route."""
    _bind(lib)
    w = w1._world(lib, world_factory, w1.WALK_SEED)
    a = lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0], w1.WALK_ORIGIN[1], w1.WALK_LAYER)
    b = lib.om_unit_spawn(w, w1.VANGUARD, 0, w1.WALK_ORIGIN[0] + w1.WALK_SPACING, w1.WALK_ORIGIN[1], w1.WALK_LAYER)
    assert a and b
    n, pts = _plan(lib, w, a, w1.WALK_GOAL)
    near = pts[6]
    assert lib.om_command_move(w, [a], 1, *near) == 0
    assert lib.om_command_move(w, [b], 1, *w1.WALK_GOAL) == 0
    _steps(lib, w, 40)
    mid = _route_read(lib, w, a)
    print("N3 premise: walker %d to %r, route_n %d route_i %d at tick 40" % (a, near, mid[0], mid[1]))
    assert mid[0] > 1, "premise: the short walk stores no route"
    _steps(lib, w, 460)
    x, y = lib.om_unit_get_pos(w, a)
    print("N3 arrival: walker %d at (%.1f, %.1f), goal %r" % (a, x, y, near))
    assert math.hypot(x - near[0], y - near[1]) < 20.0, "premise: the walker did not arrive"
    _n3_check(lib, world_factory, w, [a], [b], "arrival")


def test_N3_a_walker_stopped_by_an_order_saves_and_hashes_no_route(lib, world_factory):
    """Architect ruling 2026-10-14 (TD-VG-W-4 control, finding F2): after a has_dest = 0 event the saved and hashed state carries
    route_n 0 and route_i 0. Event here: om_unit_clear_orders (csrc/tactical_move.c:3039, which om_command_guard calls) on one of
    two walkers 30 ticks into a 317-point walk; one step later the stopped walker is still where it stopped (premise: it has no
    order) and must hold no route; the other walker keeps its stored route (control). Red if the stop leaves the stale route_n
    of the order it ended."""
    _bind(lib)
    w, ids = _small_walker_world(lib, world_factory, 30, n=2)
    a, b = ids
    before = _route_read(lib, w, a)
    print("N3 premise: walker %d route_n %d route_i %d before the stop" % (a, before[0], before[1]))
    assert before[0] > 2, "premise: the walk stores no route"
    lib.om_unit_clear_orders(w, a)
    pos = lib.om_unit_get_pos(w, a)
    _steps(lib, w, 1)
    assert lib.om_unit_get_pos(w, a) == pos, "premise: the stopped walker moved"
    _n3_check(lib, world_factory, w, [a], [b], "stop")


# ==== GOLDEN TABLE (begin): recorded 2026-10-13 on origin/main c762aab4, the unmodified walker (per-waypoint replan) ====
GOLDEN_L = {
    100: ((650.0, 250.0, 0), (450.0, 650.0, 0)),
    300: ((1450.0, 250.0, 0), (450.0, 1450.0, 0)),
}
# N1 and N2: recorded by the writer 2026-10-14 on origin/main b64ff6d2 (the old walker, per-waypoint replan); N1 equals the
# checker's values. N2 is also equal on the build at 09130f3e (positive control). Each row is (x, y, layer) of the walker.
GOLDEN_STALE = {
    48: (10275.45454545453, 4450.0, 2),
    1200: (6750.0, 2850.0, 3),
}
GOLDEN_LAYER_ORDER = {
    25: (17449.372024048957, 6581.3636779130875, 3),
    50: (17449.806604379126, 6490.455625740275, 3),
}
# ==== GOLDEN TABLE (end) ====
