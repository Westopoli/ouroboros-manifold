# Rule pins: R-001-05@95c063, R-004-07@c7c723, R-200-04@8681b2
"""VG-W1 (visible-game spec rev 12, Lane W, W1 paragraph; amended by the Rev 12b "W1." paragraph and the rev 12c
batch-2 ruling on gen_id): the walk-route planner changes cost, never routes.

Rules proved (quoted word for word from docs/bible/epics/E-01-layer-system.md):
  R-001-05: "Given a unit ordered to move to a destination, When its route is planned, Then it takes the route with
    the shortest travel time to the goal, counting each transfer, across every layer it may use, [...]; and Given a
    destination blocked on every layer the unit may occupy, When the order is issued, Then the unit paths as close as
    it can and stops"
  R-004-07: "going up the Raider takes 4.4 seconds and the Bastion 16.5 seconds (speed divided by 1.1), and going down
    3.6 and 13.6 seconds (speed times 1.1)"
  R-200-04: "otherwise paths as close as it can and stops (R-001-05)" (the nearest-reachable-cell fallback that
    tests/csim/test_E13_R207_05_walker_routes.py pins)
Spec text (W1 paragraph): "Same routes, same `seconds`, byte for byte; only cost changes." and "asserted under
DRAFT-walk-tick-ms-w1 (red today at about 150 ms)". Rev 12b W1.: "pure Dijkstra, same settle order", "The tick-200
control compares every unit's (x, y, layer) from om_unit_get_* to a table the writer records, not checksum_full".
Rev 12c: "the terrain state gains an unsaved, unhashed uint32_t gen_id, incremented in om_terrain_generate and
ts_save_read; the cache key is (world pointer, gen_id, terrain_epoch, layer, cells_w, cells_h); terrain_epoch is never
bumped at generate (hashed)".

Cases (all green on the unmodified tree except the C perf case, which is red for the stated reason):
  A  parity table: 24 om_walk_route fixtures (seeds 1 to 6, four pairs each, canvas 24,000 wu), pts and seconds exact.
     A reverse-order pass, A2 (free and recreate), A3 (regenerate in place, save and load) are extra controls beyond the
     W1 paragraph, for the cache-key risk (rev 12c: key is world pointer, gen_id, terrain_epoch, layer, cells_w,
     cells_h): a planner that caches per key must not serve one world's cells to another generation.
  D  gen_id invisibility: checksum, checksum_full and the save bytes on seeds 1 and 3 do not move (gen_id is unsaved
     and unhashed). No red-today control is possible (nothing to differ yet); see the mutate-check in the report.
  B  routes unchanged: all 600 walkers' (x, y, layer) after exactly 200 om_world_step calls.
  C  perf: median of 20 om_world_step (5 warm-up) under DRAFT-walk-tick-ms-w1. Red today.
The golden tables at the bottom were recorded by the test writer on origin/main d563d9dc (the built tree: the old
planner), twice in two processes, identical. Fixture parameters are the writer's choice (rev 12b: "The test writer
chooses and lists the fixture parameters").
"""
import ctypes
import hashlib
import time

import pytest

import test_E13_R207_05_walker_routes as routes
from conftest import OMFeature, _world_factory_for
from scale._scale_helpers import median_ns
from test_E16_S111_saving import _load, _save    # the save and load calls the csim save tests use

CANVAS = 24000.0                # wu; 240 x 240 cells
SEEDS = (1, 2, 3, 4, 5, 6)
VANGUARD = 2                    # a Vanguard, speed 80 wu/s; the unit type test_E01_T2_walker_waypoint_arrival uses
KIND_WALKING = 1                # OM_MOVE_WALKING
BIG_CAP = 8192                  # points; R207_05 uses the same cap
PAIR_KINDS = ("long", "short", "mid", "unwalkable-goal")
STALE_ORDER = (0, 2, 3, 1)      # indices into PAIR_KINDS: long, mid, unwalkable-goal, short; see _route_all
N_SECTIONS = 9                  # om_checksum_section_count(); the cap the csim section tests pass
D_STEPS = 20                    # om_world_step calls before the (D) record
D_SEEDS = (1, 3)

# Fixture parameters of the 600-walker world (B and C): the writer's choices, listed in the report.
WALK_SEED = 1
WALK_LAYER = 0                  # the engine layer with the most walkable cells on seed 1 (23,464)
WALK_COLS, WALK_ROWS = 25, 24   # 600 walkers
WALK_ORIGIN = (17450.0, 8450.0)  # wu; cell (174, 84) centre, first 12 x 12 all-walkable window of the largest component
WALK_SPACING = 40.0             # wu; 25 columns x 24 rows span 960 x 920 wu inside that window
WALK_GOAL = (1850.0, 23950.0)   # wu; the largest component's cell farthest from the window (cell (18, 239) centre)
WALK_TICKS_B = 200
WALK_MEDIAN_N, WALK_MEDIAN_WARMUP = 20, 5
PREMISE_MIN_MOVED = 300         # the brief: fewer than 300 moved walkers means the fixture is changed

# DRAFT-walk-tick-ms-w1, spec Lane W paragraph, Westley owns it
DRAFT_WALK_TICK_MS_W1 = 10.0


# ---------------------------------------------------------------- worlds and fixtures

def _prepare(lib, w, generate_seed=None):
    routes._declare(lib)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    if generate_seed is not None:
        assert lib.om_terrain_generate(w, generate_seed, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, KIND_WALKING) == 0
    return w


def _world(lib, make, seed):
    """Like _world at test_E01_T2_walker_waypoint_arrival.py:60-67 (one region, TACTICAL on, canvas, generate, walking)."""
    return _prepare(lib, make(n_regions=1), seed)


def _addr(w):
    return ctypes.cast(w, ctypes.c_void_p).value


def _cell_xy(cell, cw):
    return (cell % cw + 0.5) * routes.CELL, (cell // cw + 0.5) * routes.CELL


def _rows(seed):
    return [r for r in GOLDEN_ROUTES if r[0] == seed]


def _spawn_rows(lib, w, rows):
    cw, _ = routes._grid(lib, w)
    units = []
    for r in rows:
        x, y = _cell_xy(r[3], cw)
        u = lib.om_unit_spawn(w, VANGUARD, 0, x, y, r[2])
        assert u != 0, "spawn refused for fixture %s" % (r[:5],)
        assert lib.om_unit_get_layer(w, u) == r[2], "fixture %s: the walker stands on layer %d" % (r[:5], lib.om_unit_get_layer(w, u))
        units.append(u)
    return units


def _route_all(lib, w, rows, units, tag):
    """Route the four fixtures of one world in the order long, mid, unwalkable-goal, short: the first and the last
    are both on the top layer, so a planner that keeps one cache entry per key and was last used on another world
    of the same pointer, epoch and dimensions is hit stale by the first fixture of the next generation (a planner
    with a cache entry per layer is hit by any of them). Used by the extra controls A2 and A3."""
    for k in STALE_ORDER:
        _check_row(lib, w, units[k], rows[k], tag)


def _flat(pts):
    return tuple(v for p in pts for v in p)


def _record_one(lib, w, unit, goal_cell):
    cw, _ = routes._grid(lib, w)
    n, pts, secs = routes._route(lib, w, unit, *_cell_xy(goal_cell, cw), cap=BIG_CAP)
    return n, secs, _flat(pts)


def _check_row(lib, w, unit, row, tag):
    seed, kind, layer, start, goal, n_want, secs_want, pts_want = row
    n, secs, pts = _record_one(lib, w, unit, goal)
    where = "%s: seed %d %s (start cell %d, goal cell %d)" % (tag, seed, kind, start, goal)
    assert n == n_want, "%s: point count %d, table %d" % (where, n, n_want)
    if pts != pts_want:
        i = next((k for k, (a, b) in enumerate(zip(pts, pts_want)) if a != b), min(len(pts), len(pts_want)))
        raise AssertionError("%s: pts differ from the table at flat index %d (got %r, table %r)" % (
            where, i, pts[i] if i < len(pts) else None, pts_want[i] if i < len(pts_want) else None))
    assert secs == secs_want, "%s: seconds %r, table %r" % (where, secs, secs_want)


def derive_pairs(lib, w):
    """The writer's choice of fixtures, from the walkable cells of the unit layers (used to record GOLDEN_ROUTES and
    by test_A0_the_table_pairs_are_the_derived_ones). A walker's layer is the band of the cell it stands on
    (csrc/unit.c om_unit_spawn_internal: layer = band - 1, the spawn argument is ignored), so a start cell is "on
    layer L" when om_terrain_band_at(cell centre) - 1 == L. Engine layers are ranked by walkable cell count, most
    first; on a layer, `comp` is the largest 8-neighbour component (no corner cutting) of its walk mask, sorted by
    cell index, and `own` its cells on that layer's band.
      long            top layer, own[0] -> comp[-1] (opposite ends of the component)
      short           top layer, own[len // 2] -> the first comp cell at Chebyshev distance 8 from it
      mid             second layer, own[len // 4] -> comp[3 * len // 4]
      unwalkable-goal third layer, own[len // 10] -> the unwalkable cell (mask 0) at the quarter point of the sorted
                      unwalkable cells; the planner falls back to the nearest reachable cell (R-200-04).
    Different layers in one world exercise the layer in the planner's cache key. Returns [(kind, layer, start, goal)]."""
    cw, ch = routes._grid(lib, w)
    masks = [routes._mask(lib, w, L) for L in range(5)]
    rank = sorted(range(5), key=lambda L: (-sum(masks[L]), L))

    def component(L):
        seen, comp = set(), set()
        for i, v in enumerate(masks[L]):
            if v and i not in seen:
                c = routes._component_cells(masks[L], cw, ch, i)
                seen |= c
                if len(c) > len(comp):
                    comp = c
        comp = sorted(comp)
        own = [c for c in comp if lib.om_terrain_band_at(w, *_cell_xy(c, cw)) - 1 == L]
        return comp, own

    (ct, ot), (c2, o2), (c3, o3) = (component(L) for L in rank[:3])
    s_short = ot[len(ot) // 2]
    g_short = next(c for c in ct if max(abs(c % cw - s_short % cw), abs(c // cw - s_short // cw)) == 8)
    dead = [i for i, v in enumerate(masks[rank[2]]) if not v]
    return [("long", rank[0], ot[0], ct[-1]), ("short", rank[0], s_short, g_short),
            ("mid", rank[1], o2[len(o2) // 4], c2[3 * len(c2) // 4]),
            ("unwalkable-goal", rank[2], o3[len(o3) // 10], dead[len(dead) // 4])]


def record_routes(lib, make):
    """Recording run (not a test): the GOLDEN_ROUTES rows, from the planner as built."""
    out = []
    for seed in SEEDS:
        w = _world(lib, make, seed)
        cw, _ = routes._grid(lib, w)
        for kind, layer, start, goal in derive_pairs(lib, w):
            u = lib.om_unit_spawn(w, VANGUARD, 0, *_cell_xy(start, cw), layer)
            assert u != 0 and lib.om_unit_get_layer(w, u) == layer, "premise: the walker stands on layer %d" % layer
            n, secs, pts = _record_one(lib, w, u, goal)
            out.append((seed, kind, layer, start, goal, n, secs, pts))
    return out


# ---------------------------------------------------------------- A: the parity table

def test_A0_positive_control_a_unit_spawns_and_a_route_has_more_than_one_point(lib, world_factory):
    """Green today (R-001-05): the harness works, so a red A or C is the planner's and not the fixture's."""
    w = _world(lib, world_factory, 1)
    row = _rows(1)[0]
    (u,) = _spawn_rows(lib, w, [row])
    assert routes._mask(lib, w, row[2])[row[3]] == 1, "the fixture's start cell is not walkable"
    n, secs, pts = _record_one(lib, w, u, row[4])
    assert n > 1, "om_walk_route returned %d points" % n
    assert secs > 0.0


def test_A0_the_table_pairs_are_the_derived_ones(lib, world_factory):
    """Green today: the (start, goal) cells in the table are what derive_pairs picks, so the table reads the terrain."""
    for seed in SEEDS:
        w = _world(lib, world_factory, seed)
        assert [(seed, k, L, s, g) for k, L, s, g in derive_pairs(lib, w)] == [r[:5] for r in _rows(seed)]


def test_A0_the_table_holds_the_promised_shapes():
    """Green today: 24 fixtures, six unwalkable goals, a route of more than 100 points (spec W1: "24 fixtures")."""
    assert len(GOLDEN_ROUTES) == 24
    assert [r[1] for r in GOLDEN_ROUTES] == list(PAIR_KINDS) * len(SEEDS)
    assert max(r[5] for r in GOLDEN_ROUTES) > 100
    assert all(len(r[7]) == 2 * r[5] for r in GOLDEN_ROUTES)


def test_A_parity_24_fixtures_in_table_order_then_in_reverse(lib, world_factory):
    """Spec W1 paragraph: "Same routes, same `seconds`, byte for byte" (R-001-05, R-004-07, R-200-04). Six worlds up
    front; the table in order, then reversed, in the same process. The reverse pass is an extra control beyond the
    paragraph, for the cache-key risk (rev 12c): the epoch of freshly generated worlds can coincide."""
    worlds = {}
    for seed in SEEDS:
        w = _world(lib, world_factory, seed)
        worlds[seed] = (w, dict(zip((r[1] for r in _rows(seed)), _spawn_rows(lib, w, _rows(seed)))))
    for r in GOLDEN_ROUTES:
        w, units = worlds[r[0]]
        _check_row(lib, w, units[r[1]], r, "forward")
    for r in reversed(GOLDEN_ROUTES):          # extra control beyond the W1 paragraph (cache key)
        w, units = worlds[r[0]]
        _check_row(lib, w, units[r[1]], r, "reverse")


def test_A2_free_and_recreate_twenty_rounds_alternating_seeds_1_and_2(lib):
    """Extra control beyond the W1 paragraph, for the cache-key risk (rev 12c): a world is created, routed and freed,
    twenty times, alternating seed 1 and 2. Every round makes the same call sequence, so every world reaches the same
    terrain_epoch, and a freed world's address is likely to come back: only gen_id (rev 12c) separates the
    generations, so a stale cache hit on a reused address would show here. Best effort at address reuse: the
    addresses are printed (pytest -s). Premise measured 2026-10-12 with a throwaway getter (not
    committed): every round ends at terrain_epoch 3, and 19 of the 20 rounds got the previous address back."""
    make, created = _world_factory_for(lib, None)
    addrs = []
    for rnd in range(20):
        seed = 1 + rnd % 2
        w = _world(lib, make, seed)
        addrs.append(_addr(w))
        rows = _rows(seed)
        _route_all(lib, w, rows, _spawn_rows(lib, w, rows), "A2 round %d" % rnd)
        lib.om_world_free(w)
    print("A2 world addresses:", [hex(a) for a in addrs])
    print("A2 address repeats:", len(addrs) - len(set(addrs)), "of", len(addrs), "rounds reuse an earlier address")


def test_A3_regenerate_in_place_seed_1_then_2_then_1(lib, world_factory):
    """Extra control beyond the W1 paragraph (rev 12c, gen_id): one world, om_terrain_generate seed 1, then seed 2,
    then seed 1 again, on the same canvas and the same pointer; the fixtures of each seed against the table.
    Measured 2026-10-12: om_terrain_generate DOES bump terrain_epoch today (om_map_set_canvas,
    csrc/tactical_move.c:562, and the ground density writes), contrary to the rev 12b/12c text: the epoch reads 3, 5, 7, 9 across prepare and
    the three generates, so here the epoch already separates the generations; the same-pointer same-epoch cases are
    test_A2 (free and recreate) and test_A3_load_over (ts_save_read)."""
    w = _world(lib, world_factory, 1)
    for step, seed in enumerate((1, 2, 1)):
        assert lib.om_terrain_generate(w, seed, CANVAS, CANVAS) == 0
        rows = _rows(seed)
        _route_all(lib, w, rows, _spawn_rows(lib, w, rows), "A3 regenerate step %d" % step)


def test_A3_save_and_load_into_a_fresh_world(lib, world_factory):
    """Extra control beyond the W1 paragraph (rev 12c: ts_save_read also increments gen_id). A seed-1 world with its
    four fixture units is saved (_save: om_save_state_size, om_save_state_write) and loaded into a fresh world with
    `lib.om_load_state_read(w, buf, size)` (_load); the loaded world's fixtures route against the table."""
    src = _world(lib, world_factory, 1)
    rows = _rows(1)
    units = _spawn_rows(lib, src, rows)
    buf, size = _save(lib, src)
    dst = _prepare(lib, world_factory(n_regions=1))
    assert _load(lib, dst, buf, size) == 0
    assert routes._grid(lib, dst) == routes._grid(lib, src)
    _route_all(lib, dst, rows, units, "A3 loaded world")


def test_A3_load_over_a_live_world_that_has_the_same_epoch(lib, world_factory):
    """Extra control beyond the W1 paragraph (rev 12c: same pointer, same terrain_epoch, new gen_id, ts_save_read).
    World X (seed 1) and world S (seed 2) are built by the same call sequence, so they hold the same terrain_epoch.
    X's seed-1 fixtures are routed (warming any cache keyed on X), S is saved and loaded over X (same pointer, the
    save restores S's epoch), and X's units from S (the seed-2 rows) route against the table; then X's own seed-1 save
    is loaded back over it and the seed-1 rows route again. Measured 2026-10-12 (throwaway getter): the epoch is 3
    for X before the load, 3 for S, and 3 for X after it, with the same X pointer: only gen_id differs."""
    x = _world(lib, world_factory, 1)
    x_units = _spawn_rows(lib, x, _rows(1))
    _route_all(lib, x, _rows(1), x_units, "A3b before the load")
    x_buf, x_size = _save(lib, x)
    s = _world(lib, world_factory, 2)
    s_units = _spawn_rows(lib, s, _rows(2))
    s_buf, s_size = _save(lib, s)
    assert _load(lib, x, s_buf, s_size) == 0
    _route_all(lib, x, _rows(2), s_units, "A3b seed-2 world loaded over seed 1")
    assert _load(lib, x, x_buf, x_size) == 0
    _route_all(lib, x, _rows(1), x_units, "A3b seed-1 world loaded back")


# ---------------------------------------------------------------- D: gen_id invisibility

SAVE_SERIAL_OFFSET, SAVE_SERIAL_BYTES = 40, 8   # magic 4 + version 4 + tick 8 + seed 8 + rng state 8 + rng inc 8


def _save_bytes(lib, w):
    """The bytes om_save_state_write produces, with the world serial zeroed. The serial (u64 at offset 40, csrc/save.c
    :310) is om_world_serial_counter++ at om_world_new (csrc/region.c:9, :179), a per-process count of the worlds
    created so far, so the raw bytes depend on how many worlds the process made before this one (found 2026-10-12:
    the second world of a process saves one byte different); it is not terrain state and gen_id has nothing to do
    with it."""
    buf, size = _save(lib, w)
    raw = bytearray(bytes(buf))
    assert int.from_bytes(raw[SAVE_SERIAL_OFFSET:SAVE_SERIAL_OFFSET + SAVE_SERIAL_BYTES], "little") >= 1, "premise: serial"
    raw[SAVE_SERIAL_OFFSET:SAVE_SERIAL_OFFSET + SAVE_SERIAL_BYTES] = bytes(SAVE_SERIAL_BYTES)
    return bytes(raw)


def _triple(lib, w):
    """om_world_checksum, om_world_checksum_full (return value and the nine sections), the length and sha256 of the
    save bytes (world serial zeroed, see _save_bytes)."""
    plain = lib.om_world_checksum(w)
    sec = (ctypes.c_uint64 * N_SECTIONS)()
    ret = lib.om_world_checksum_full(w, sec, N_SECTIONS)
    raw = _save_bytes(lib, w)
    return {"checksum": "%016x" % plain, "full_ret": "%016x" % ret, "sections": ["%016x" % s for s in sec],
            "save_len": len(raw), "save_sha256": hashlib.sha256(raw).hexdigest()}


def _d_world(lib, make, seed, generations=1):
    w = _prepare(lib, make(n_regions=1))
    for _ in range(generations):
        assert lib.om_terrain_generate(w, seed, CANVAS, CANVAS) == 0
    for _ in range(D_STEPS):
        lib.om_world_step(w)
    return w


def record_d(lib, make):
    """Recording run (not a test): the GOLDEN_D dict, from the tree as built."""
    out = {}
    for seed in D_SEEDS:
        src = _d_world(lib, make, seed)
        buf, size = _save(lib, src)
        dst = _prepare(lib, make(n_regions=1))
        assert _load(lib, dst, buf, size) == 0
        out[seed] = {"plain": _triple(lib, src), "loaded": _triple(lib, dst),
                     "twice": _triple(lib, _d_world(lib, make, seed, generations=2))}
    return out


@pytest.mark.parametrize("seed", D_SEEDS)
def test_D_gen_id_is_invisible_to_the_checksums_and_the_save_bytes(lib, world_factory, seed):
    """Batch-2 ruling (rev 12c): gen_id is unsaved and unhashed, so no golden may move. Exact equalities, no
    tolerance, against GOLDEN_D recorded on the unmodified tree: the world after generate and 20 om_world_step; the
    same after a save-then-load round trip into a fresh world (the loaded world re-saved gives the same sha256); and
    a world on which om_terrain_generate was called twice with the same seed (gen_id differs, nothing visible may)."""
    want = GOLDEN_D[seed]
    src = _d_world(lib, world_factory, seed)
    assert _triple(lib, src) == want["plain"], "seed %d: checksum, checksum_full or save bytes moved" % seed
    buf, size = _save(lib, src)
    dst = _prepare(lib, world_factory(n_regions=1))
    assert _load(lib, dst, buf, size) == 0
    assert _triple(lib, dst) == want["loaded"], "seed %d: the loaded world's checksums or re-saved bytes moved" % seed
    twice = _d_world(lib, world_factory, seed, generations=2)
    assert _triple(lib, twice) == want["twice"], "seed %d: a second om_terrain_generate moved something visible" % seed


# ---------------------------------------------------------------- B and C: the 600-walker world

def _walker_world(lib, make):
    """600 walkers (25 x 24 grid, 40 wu apart) on walkable layer 0 of a seed-1, 24,000 wu world, all ordered to the
    far corner of the largest component with one om_command_move. Fixture of test_E01_T2_walker_waypoint_arrival.py:
    60-67, 128-147 scaled to 600 units."""
    w = _world(lib, make, WALK_SEED)
    ids = []
    for j in range(WALK_ROWS):
        for i in range(WALK_COLS):
            u = lib.om_unit_spawn(w, VANGUARD, 0, WALK_ORIGIN[0] + i * WALK_SPACING, WALK_ORIGIN[1] + j * WALK_SPACING,
                                  WALK_LAYER)
            assert u != 0, "spawn refused at grid (%d, %d)" % (i, j)
            ids.append(u)
    assert lib.om_command_move(w, ids, len(ids), *WALK_GOAL) == 0
    return w, ids


def _positions(lib, w, ids):
    return [lib.om_unit_get_pos(w, u) for u in ids]


def record_b(lib, make):
    """Recording run (not a test): the GOLDEN_B rows (x, y, layer), unit-id order, after 200 om_world_step."""
    w, ids = _walker_world(lib, make)
    spawn = _positions(lib, w, ids)
    for _ in range(WALK_TICKS_B):
        lib.om_world_step(w)
    pos = _positions(lib, w, ids)
    rows = [(x, y, lib.om_unit_get_layer(w, u)) for (x, y), u in zip(pos, ids)]
    return rows, sum(1 for a, b in zip(spawn, pos) if a != b)


def test_B_routes_unchanged_every_walker_after_200_ticks(lib, world_factory):
    """Rev 12b W1.: "The tick-200 control compares every unit's (x, y, layer) from om_unit_get_* to a table the writer
    records, not checksum_full". Exact doubles, no tolerance; green today. Premise: the walkers moved and replanned
    legs (R-001-05, R-004-07)."""
    w, ids = _walker_world(lib, world_factory)
    spawn = _positions(lib, w, ids)
    assert len(ids) == len(GOLDEN_B) == 600
    for _ in range(WALK_TICKS_B):
        lib.om_world_step(w)
    pos = _positions(lib, w, ids)
    moved = sum(1 for a, b in zip(spawn, pos) if a != b)
    print("B premise: %d of %d walkers moved from the spawn position in %d ticks" % (moved, len(ids), WALK_TICKS_B))
    assert moved >= PREMISE_MIN_MOVED, "premise: only %d walkers moved" % moved
    bad = [k for k, ((x, y), u) in enumerate(zip(pos, ids)) if (x, y, lib.om_unit_get_layer(w, u)) != GOLDEN_B[k]]
    assert not bad, "%d of 600 walkers differ from the table at tick %d; first: unit index %d got %r, table %r" % (
        len(bad), WALK_TICKS_B, bad[0], (*pos[bad[0]], lib.om_unit_get_layer(w, ids[bad[0]])), GOLDEN_B[bad[0]])


DRAFT_PERF_REPEATS = 7   # DRAFT-perf-repeats (Architect 2026-10-14, TD-VG-W-5), vetoable by Westley


def perf_repeats_ms(lib, make, repeats=DRAFT_PERF_REPEATS, inject_ms=0.0):
    """Run the C measurement `repeats` times, each on a fresh 600-walker world in this process: the median of 20
    om_world_step after 5 warm-up through median_ns. Returns (medians in ms, marching counts). `inject_ms` is the
    positive control: a busy-wait of that many ms inside the timed step (0 in the real test; no sleep, no load hiding)."""
    medians, marchings = [], []
    for _ in range(repeats):
        w, ids = _walker_world(lib, make)
        calls, snap = [], {}

        def op():
            calls.append(1)
            if inject_ms:
                t_end = time.perf_counter() + inject_ms / 1e3
                while time.perf_counter() < t_end:
                    pass
            lib.om_world_step(w)
            if len(calls) == WALK_MEDIAN_WARMUP:
                snap["step5"] = _positions(lib, w, ids)

        medians.append(median_ns(op, n=WALK_MEDIAN_N, warmup=WALK_MEDIAN_WARMUP) / 1e6)
        assert len(calls) == WALK_MEDIAN_WARMUP + WALK_MEDIAN_N
        end = _positions(lib, w, ids)
        marchings.append(sum(1 for a, b in zip(snap["step5"], end) if a != b))
    return medians, marchings


def test_C_a_tick_with_600_walkers_costs_less_than_the_draft(lib, world_factory):
    """THE RED CASE (spec W1: "median of 20 om_world_step after 5 warm-up through median_ns, asserted under
    DRAFT-walk-tick-ms-w1"): wall-clock. TD-VG-W-5 (Architect 2026-10-14): the box runs gates at load about 14 of 16
    cores, so one 20-step median is load noise; the test takes the MINIMUM of DRAFT-perf-repeats (7) such medians, each
    on a fresh world, and asserts it under the unchanged draft. Positive control: test_VG_W_w1_perf_control.py (an
    injected busy-wait fails every repeat). Red today: the median is far above 10 ms (the spec measured about 150 ms
    on 2026-10-10). The premise (walkers still marching through the measured steps) is asserted before the perf line."""
    medians, marchings = perf_repeats_ms(lib, world_factory)
    print("C premise: %s of 600 walkers changed position between step %d and the last step, per repeat" % (
        marchings, WALK_MEDIAN_WARMUP))
    print("C median om_world_step per repeat (ms): %s" % ", ".join("%.3f" % m for m in medians))
    best = min(medians)
    print("C minimum of %d repeats: %.3f ms" % (len(medians), best))
    assert min(marchings) >= PREMISE_MIN_MOVED, "premise: only %d walkers still marching" % min(marchings)
    assert best < DRAFT_WALK_TICK_MS_W1, (
        "minimum of %d medians of %d om_world_step with 600 walkers is %.3f ms, DRAFT-walk-tick-ms-w1 is %.1f ms" % (
            len(medians), WALK_MEDIAN_N, best, DRAFT_WALK_TICK_MS_W1))


# ==== GOLDEN TABLES (begin): recorded 2026-10-12 on origin/main d563d9dc, the unmodified planner ====
GOLDEN_ROUTES = (
    (1, 'long', 0, 17999, 57599, 166, 205.79547119140625,
     (23950.0, 7450.0, 23950.0, 7550.0, 23950.0, 7650.0, 23950.0, 7750.0, 23950.0, 7850.0, 23950.0, 7950.0, 23950.0, 8050.0, 23950.0, 8150.0, 23950.0, 8250.0, 23950.0, 8350.0, 23950.0, 8450.0, 23950.0, 8550.0, 23950.0, 8650.0, 23950.0, 8750.0, 23950.0, 8850.0, 23950.0, 8950.0, 23950.0, 9050.0, 23950.0, 9150.0, 23950.0, 9250.0, 23950.0, 9350.0, 23950.0, 9450.0, 23950.0, 9550.0, 23950.0, 9650.0, 23950.0, 9750.0, 23950.0, 9850.0, 23950.0, 9950.0, 23950.0, 10050.0, 23950.0, 10150.0, 23950.0, 10250.0, 23950.0, 10350.0, 23950.0, 10450.0, 23950.0, 10550.0, 23950.0, 10650.0, 23950.0, 10750.0, 23950.0, 10850.0, 23950.0, 10950.0, 23950.0, 11050.0, 23950.0, 11150.0, 23950.0, 11250.0, 23950.0, 11350.0, 23950.0, 11450.0, 23950.0, 11550.0, 23950.0, 11650.0, 23950.0, 11750.0, 23950.0, 11850.0, 23950.0, 11950.0, 23950.0, 12050.0, 23950.0, 12150.0, 23950.0, 12250.0, 23950.0, 12350.0, 23950.0, 12450.0, 23950.0, 12550.0, 23950.0, 12650.0, 23950.0, 12750.0, 23950.0, 12850.0, 23950.0, 12950.0, 23950.0, 13050.0, 23950.0, 13150.0, 23950.0, 13250.0, 23950.0, 13350.0, 23950.0, 13450.0, 23950.0, 13550.0, 23950.0, 13650.0, 23950.0, 13750.0, 23950.0, 13850.0, 23950.0, 13950.0, 23950.0, 14050.0, 23950.0, 14150.0, 23950.0, 14250.0, 23950.0, 14350.0, 23950.0, 14450.0, 23950.0, 14550.0, 23950.0, 14650.0, 23950.0, 14750.0, 23950.0, 14850.0, 23950.0, 14950.0, 23950.0, 15050.0, 23950.0, 15150.0, 23950.0, 15250.0, 23950.0, 15350.0, 23950.0, 15450.0, 23950.0, 15550.0, 23950.0, 15650.0, 23950.0, 15750.0, 23950.0, 15850.0, 23950.0, 15950.0, 23950.0, 16050.0, 23950.0, 16150.0, 23950.0, 16250.0, 23950.0, 16350.0, 23950.0, 16450.0, 23950.0, 16550.0, 23950.0, 16650.0, 23950.0, 16750.0, 23950.0, 16850.0, 23950.0, 16950.0, 23950.0, 17050.0, 23950.0, 17150.0, 23950.0, 17250.0, 23950.0, 17350.0, 23950.0, 17450.0, 23950.0, 17550.0, 23950.0, 17650.0, 23950.0, 17750.0, 23950.0, 17850.0, 23950.0, 17950.0, 23950.0, 18050.0, 23950.0, 18150.0, 23950.0, 18250.0, 23950.0, 18350.0, 23950.0, 18450.0, 23950.0, 18550.0, 23950.0, 18650.0, 23950.0, 18750.0, 23950.0, 18850.0, 23950.0, 18950.0, 23950.0, 19050.0, 23950.0, 19150.0, 23950.0, 19250.0, 23950.0, 19350.0, 23950.0, 19450.0, 23950.0, 19550.0, 23950.0, 19650.0, 23950.0, 19750.0, 23950.0, 19850.0, 23950.0, 19950.0, 23950.0, 20050.0, 23950.0, 20150.0, 23950.0, 20250.0, 23950.0, 20350.0, 23950.0, 20450.0, 23950.0, 20550.0, 23950.0, 20650.0, 23950.0, 20750.0, 23950.0, 20850.0, 23950.0, 20950.0, 23950.0, 21050.0, 23950.0, 21150.0, 23950.0, 21250.0, 23950.0, 21350.0, 23950.0, 21450.0, 23950.0, 21550.0, 23950.0, 21650.0, 23950.0, 21750.0, 23950.0, 21850.0, 23950.0, 21950.0, 23950.0, 22050.0, 23950.0, 22150.0, 23950.0, 22250.0, 23950.0, 22350.0, 23950.0, 22450.0, 23950.0, 22550.0, 23950.0, 22650.0, 23950.0, 22750.0, 23950.0, 22850.0, 23950.0, 22950.0, 23950.0, 23050.0, 23950.0, 23150.0, 23950.0, 23250.0, 23950.0, 23350.0, 23950.0, 23450.0, 23950.0, 23550.0, 23950.0, 23650.0, 23950.0, 23750.0, 23950.0, 23850.0, 23950.0, 23950.0)),
    (1, 'short', 0, 51328, 49400, 9, 14.1422119140625,
     (20850.0, 21350.0, 20750.0, 21250.0, 20650.0, 21150.0, 20550.0, 21050.0, 20450.0, 20950.0, 20350.0, 20850.0, 20250.0, 20750.0, 20150.0, 20650.0, 20050.0, 20550.0)),
    (1, 'mid', 1, 19548, 33865, 138, 185.0,
     (10850.0, 8150.0, 10750.0, 8150.0, 10650.0, 8150.0, 10550.0, 8150.0, 10450.0, 8150.0, 10350.0, 8150.0, 10250.0, 8150.0, 10150.0, 8150.0, 10050.0, 8150.0, 9950.0, 8150.0, 9850.0, 8150.0, 9750.0, 8150.0, 9650.0, 8150.0, 9550.0, 8150.0, 9450.0, 8150.0, 9350.0, 8050.0, 9250.0, 8050.0, 9150.0, 8050.0, 9050.0, 8050.0, 8950.0, 8050.0, 8850.0, 8050.0, 8750.0, 8050.0, 8650.0, 8050.0, 8550.0, 8050.0, 8450.0, 8050.0, 8350.0, 8050.0, 8250.0, 7950.0, 8150.0, 7850.0, 8050.0, 7750.0, 7950.0, 7750.0, 7850.0, 7750.0, 7750.0, 7750.0, 7650.0, 7750.0, 7550.0, 7750.0, 7450.0, 7750.0, 7350.0, 7750.0, 7250.0, 7750.0, 7150.0, 7750.0, 7050.0, 7750.0, 6950.0, 7750.0, 6850.0, 7750.0, 6750.0, 7750.0, 6650.0, 7750.0, 6550.0, 7750.0, 6450.0, 7750.0, 6350.0, 7750.0, 6250.0, 7750.0, 6150.0, 7750.0, 6050.0, 7750.0, 5950.0, 7750.0, 5850.0, 7750.0, 5750.0, 7750.0, 5650.0, 7750.0, 5550.0, 7750.0, 5450.0, 7650.0, 5350.0, 7550.0, 5250.0, 7450.0, 5150.0, 7350.0, 5050.0, 7350.0, 4950.0, 7250.0, 4850.0, 7150.0, 4750.0, 7050.0, 4650.0, 7050.0, 4550.0, 7050.0, 4450.0, 7050.0, 4350.0, 7050.0, 4250.0, 7050.0, 4250.0, 7150.0, 4150.0, 7250.0, 4150.0, 7350.0, 4150.0, 7450.0, 4150.0, 7550.0, 4050.0, 7650.0, 4050.0, 7750.0, 4050.0, 7850.0, 4050.0, 7950.0, 3950.0, 8050.0, 3850.0, 8150.0, 3750.0, 8250.0, 3650.0, 8350.0, 3550.0, 8450.0, 3450.0, 8550.0, 3450.0, 8650.0, 3450.0, 8750.0, 3450.0, 8850.0, 3450.0, 8950.0, 3450.0, 9050.0, 3450.0, 9150.0, 3450.0, 9250.0, 3450.0, 9350.0, 3450.0, 9450.0, 3350.0, 9550.0, 3250.0, 9650.0, 3150.0, 9750.0, 3150.0, 9850.0, 3050.0, 9950.0, 2950.0, 10050.0, 2850.0, 10150.0, 2750.0, 10250.0, 2650.0, 10350.0, 2550.0, 10450.0, 2550.0, 10550.0, 2550.0, 10650.0, 2550.0, 10750.0, 2550.0, 10850.0, 2550.0, 10950.0, 2550.0, 11050.0, 2550.0, 11150.0, 2550.0, 11250.0, 2550.0, 11350.0, 2550.0, 11450.0, 2550.0, 11550.0, 2550.0, 11650.0, 2550.0, 11750.0, 2550.0, 11850.0, 2550.0, 11950.0, 2550.0, 12050.0, 2550.0, 12150.0, 2550.0, 12250.0, 2550.0, 12350.0, 2550.0, 12450.0, 2550.0, 12550.0, 2550.0, 12650.0, 2550.0, 12750.0, 2550.0, 12850.0, 2550.0, 12950.0, 2550.0, 13050.0, 2550.0, 13150.0, 2550.0, 13250.0, 2550.0, 13350.0, 2550.0, 13450.0, 2550.0, 13550.0, 2550.0, 13650.0, 2550.0, 13750.0, 2550.0, 13850.0, 2550.0, 13950.0, 2550.0, 14050.0, 2550.0, 14150.0)),
    (1, 'unwalkable-goal', 2, 22113, 12795, 32, 35.698089599609375,
     (3350.0, 9250.0, 3350.0, 9150.0, 3350.0, 9050.0, 3350.0, 8950.0, 3350.0, 8850.0, 3350.0, 8750.0, 3350.0, 8650.0, 3350.0, 8550.0, 3350.0, 8450.0, 3350.0, 8350.0, 3350.0, 8250.0, 3350.0, 8150.0, 3350.0, 8050.0, 3350.0, 7950.0, 3350.0, 7850.0, 3350.0, 7750.0, 3350.0, 7650.0, 3350.0, 7550.0, 3350.0, 7450.0, 3350.0, 7350.0, 3350.0, 7250.0, 3350.0, 7150.0, 3350.0, 7050.0, 3450.0, 6950.0, 3450.0, 6850.0, 3450.0, 6750.0, 3450.0, 6650.0, 3450.0, 6550.0, 3450.0, 6450.0, 3450.0, 6350.0, 3450.0, 6250.0, 3450.0, 6150.0)),
    (2, 'long', 0, 80, 57599, 240, 380.7420349121094,
     (8050.0, 50.0, 8050.0, 150.0, 8050.0, 250.0, 8050.0, 350.0, 8150.0, 450.0, 8250.0, 550.0, 8250.0, 650.0, 8250.0, 750.0, 8350.0, 850.0, 8350.0, 950.0, 8350.0, 1050.0, 8350.0, 1150.0, 8350.0, 1250.0, 8350.0, 1350.0, 8350.0, 1450.0, 8350.0, 1550.0, 8350.0, 1650.0, 8350.0, 1750.0, 8350.0, 1850.0, 8350.0, 1950.0, 8350.0, 2050.0, 8350.0, 2150.0, 8350.0, 2250.0, 8350.0, 2350.0, 8350.0, 2450.0, 8350.0, 2550.0, 8350.0, 2650.0, 8350.0, 2750.0, 8350.0, 2850.0, 8350.0, 2950.0, 8350.0, 3050.0, 8350.0, 3150.0, 8350.0, 3250.0, 8350.0, 3350.0, 8350.0, 3450.0, 8350.0, 3550.0, 8350.0, 3650.0, 8350.0, 3750.0, 8350.0, 3850.0, 8350.0, 3950.0, 8350.0, 4050.0, 8350.0, 4150.0, 8350.0, 4250.0, 8350.0, 4350.0, 8350.0, 4450.0, 8350.0, 4550.0, 8350.0, 4650.0, 8350.0, 4750.0, 8350.0, 4850.0, 8350.0, 4950.0, 8350.0, 5050.0, 8350.0, 5150.0, 8350.0, 5250.0, 8350.0, 5350.0, 8350.0, 5450.0, 8350.0, 5550.0, 8350.0, 5650.0, 8350.0, 5750.0, 8350.0, 5850.0, 8350.0, 5950.0, 8350.0, 6050.0, 8350.0, 6150.0, 8350.0, 6250.0, 8350.0, 6350.0, 8350.0, 6450.0, 8350.0, 6550.0, 8350.0, 6650.0, 8350.0, 6750.0, 8350.0, 6850.0, 8350.0, 6950.0, 8350.0, 7050.0, 8350.0, 7150.0, 8350.0, 7250.0, 8350.0, 7350.0, 8350.0, 7450.0, 8350.0, 7550.0, 8350.0, 7650.0, 8350.0, 7750.0, 8350.0, 7850.0, 8350.0, 7950.0, 8350.0, 8050.0, 8350.0, 8150.0, 8350.0, 8250.0, 8350.0, 8350.0, 8450.0, 8450.0, 8550.0, 8550.0, 8650.0, 8650.0, 8750.0, 8750.0, 8850.0, 8850.0, 8950.0, 8950.0, 9050.0, 9050.0, 9150.0, 9150.0, 9250.0, 9250.0, 9350.0, 9350.0, 9450.0, 9450.0, 9550.0, 9550.0, 9650.0, 9650.0, 9750.0, 9750.0, 9850.0, 9850.0, 9950.0, 9950.0, 10050.0, 10050.0, 10150.0, 10150.0, 10250.0, 10250.0, 10350.0, 10350.0, 10450.0, 10450.0, 10550.0, 10550.0, 10650.0, 10650.0, 10750.0, 10750.0, 10850.0, 10850.0, 10950.0, 10950.0, 11050.0, 11050.0, 11150.0, 11150.0, 11250.0, 11250.0, 11350.0, 11350.0, 11450.0, 11450.0, 11550.0, 11550.0, 11650.0, 11650.0, 11750.0, 11750.0, 11850.0, 11850.0, 11950.0, 11950.0, 12050.0, 12050.0, 12150.0, 12150.0, 12250.0, 12250.0, 12350.0, 12350.0, 12450.0, 12450.0, 12550.0, 12550.0, 12650.0, 12650.0, 12750.0, 12750.0, 12850.0, 12850.0, 12950.0, 12950.0, 13050.0, 13050.0, 13150.0, 13150.0, 13250.0, 13250.0, 13350.0, 13350.0, 13450.0, 13450.0, 13550.0, 13550.0, 13650.0, 13650.0, 13750.0, 13750.0, 13850.0, 13850.0, 13950.0, 13950.0, 14050.0, 14050.0, 14150.0, 14150.0, 14250.0, 14250.0, 14350.0, 14350.0, 14450.0, 14450.0, 14550.0, 14550.0, 14650.0, 14650.0, 14750.0, 14750.0, 14850.0, 14850.0, 14950.0, 14950.0, 15050.0, 15050.0, 15150.0, 15150.0, 15250.0, 15250.0, 15350.0, 15350.0, 15450.0, 15450.0, 15550.0, 15550.0, 15650.0, 15650.0, 15750.0, 15750.0, 15850.0, 15850.0, 15950.0, 15950.0, 16050.0, 16050.0, 16150.0, 16150.0, 16250.0, 16250.0, 16350.0, 16350.0, 16450.0, 16450.0, 16550.0, 16550.0, 16650.0, 16650.0, 16750.0, 16750.0, 16850.0, 16850.0, 16950.0, 16950.0, 17050.0, 17050.0, 17150.0, 17150.0, 17250.0, 17250.0, 17350.0, 17350.0, 17450.0, 17450.0, 17550.0, 17550.0, 17650.0, 17650.0, 17750.0, 17750.0, 17850.0, 17850.0, 17950.0, 17950.0, 18050.0, 18050.0, 18150.0, 18150.0, 18250.0, 18250.0, 18350.0, 18350.0, 18450.0, 18450.0, 18550.0, 18550.0, 18650.0, 18650.0, 18750.0, 18750.0, 18850.0, 18850.0, 18950.0, 18950.0, 19050.0, 19050.0, 19150.0, 19150.0, 19250.0, 19250.0, 19350.0, 19350.0, 19450.0, 19450.0, 19550.0, 19550.0, 19650.0, 19650.0, 19750.0, 19750.0, 19850.0, 19850.0, 19950.0, 19950.0, 20050.0, 20050.0, 20150.0, 20150.0, 20250.0, 20250.0, 20350.0, 20350.0, 20450.0, 20450.0, 20550.0, 20550.0, 20650.0, 20650.0, 20750.0, 20750.0, 20850.0, 20850.0, 20950.0, 20950.0, 21050.0, 21050.0, 21150.0, 21150.0, 21250.0, 21250.0, 21350.0, 21350.0, 21450.0, 21450.0, 21550.0, 21550.0, 21650.0, 21650.0, 21750.0, 21750.0, 21850.0, 21850.0, 21950.0, 21950.0, 22050.0, 22050.0, 22150.0, 22150.0, 22250.0, 22250.0, 22350.0, 22350.0, 22450.0, 22450.0, 22550.0, 22550.0, 22650.0, 22650.0, 22750.0, 22750.0, 22850.0, 22850.0, 22950.0, 22950.0, 23050.0, 23050.0, 23150.0, 23150.0, 23250.0, 23250.0, 23350.0, 23350.0, 23450.0, 23450.0, 23550.0, 23550.0, 23650.0, 23650.0, 23750.0, 23750.0, 23850.0, 23850.0, 23950.0, 23950.0)),
    (2, 'short', 0, 31219, 29291, 9, 13.193939208984375,
     (1950.0, 13050.0, 1850.0, 12950.0, 1750.0, 12850.0, 1650.0, 12750.0, 1550.0, 12650.0, 1450.0, 12550.0, 1350.0, 12450.0, 1250.0, 12350.0, 1150.0, 12250.0)),
    (2, 'mid', 1, 36297, 42013, 66, 88.77278137207031,
     (5750.0, 15150.0, 5750.0, 15250.0, 5750.0, 15350.0, 5750.0, 15450.0, 5750.0, 15550.0, 5750.0, 15650.0, 5650.0, 15750.0, 5550.0, 15850.0, 5550.0, 15950.0, 5550.0, 16050.0, 5450.0, 16150.0, 5350.0, 16250.0, 5250.0, 16350.0, 5150.0, 16450.0, 5150.0, 16550.0, 5150.0, 16650.0, 5150.0, 16750.0, 5150.0, 16850.0, 5150.0, 16950.0, 5150.0, 17050.0, 5050.0, 17150.0, 5050.0, 17250.0, 5050.0, 17350.0, 4950.0, 17450.0, 4850.0, 17550.0, 4750.0, 17650.0, 4750.0, 17750.0, 4750.0, 17850.0, 4750.0, 17950.0, 4750.0, 18050.0, 4750.0, 18150.0, 4750.0, 18250.0, 4650.0, 18350.0, 4550.0, 18350.0, 4450.0, 18350.0, 4350.0, 18350.0, 4250.0, 18250.0, 4150.0, 18150.0, 4050.0, 18050.0, 3950.0, 17950.0, 3850.0, 17850.0, 3750.0, 17850.0, 3650.0, 17850.0, 3550.0, 17850.0, 3450.0, 17850.0, 3350.0, 17850.0, 3250.0, 17850.0, 3150.0, 17850.0, 3050.0, 17850.0, 2950.0, 17850.0, 2850.0, 17850.0, 2750.0, 17850.0, 2650.0, 17850.0, 2550.0, 17850.0, 2450.0, 17850.0, 2350.0, 17850.0, 2250.0, 17850.0, 2150.0, 17750.0, 2050.0, 17750.0, 1950.0, 17750.0, 1850.0, 17750.0, 1750.0, 17750.0, 1650.0, 17750.0, 1550.0, 17750.0, 1450.0, 17650.0, 1350.0, 17550.0)),
    (2, 'unwalkable-goal', 2, 16141, 14736, 7, 8.4820556640625,
     (6150.0, 6750.0, 6150.0, 6650.0, 6150.0, 6550.0, 6150.0, 6450.0, 6150.0, 6350.0, 6150.0, 6250.0, 6250.0, 6150.0)),
    (3, 'long', 0, 0, 57599, 275, 445.3628845214844,
     (50.0, 50.0, 150.0, 50.0, 250.0, 50.0, 350.0, 150.0, 450.0, 250.0, 550.0, 350.0, 650.0, 450.0, 750.0, 550.0, 850.0, 650.0, 950.0, 750.0, 1050.0, 850.0, 1150.0, 950.0, 1250.0, 1050.0, 1350.0, 1150.0, 1450.0, 1250.0, 1550.0, 1350.0, 1650.0, 1450.0, 1750.0, 1550.0, 1850.0, 1650.0, 1950.0, 1750.0, 2050.0, 1850.0, 2150.0, 1950.0, 2250.0, 2050.0, 2350.0, 2150.0, 2450.0, 2250.0, 2550.0, 2350.0, 2650.0, 2450.0, 2750.0, 2550.0, 2850.0, 2650.0, 2950.0, 2750.0, 3050.0, 2850.0, 3150.0, 2950.0, 3250.0, 3050.0, 3350.0, 3150.0, 3450.0, 3250.0, 3550.0, 3350.0, 3650.0, 3450.0, 3750.0, 3550.0, 3850.0, 3650.0, 3950.0, 3750.0, 4050.0, 3850.0, 4150.0, 3950.0, 4250.0, 4050.0, 4350.0, 4150.0, 4450.0, 4250.0, 4550.0, 4350.0, 4650.0, 4450.0, 4750.0, 4550.0, 4850.0, 4650.0, 4950.0, 4750.0, 5050.0, 4850.0, 5150.0, 4950.0, 5250.0, 5050.0, 5350.0, 5150.0, 5450.0, 5250.0, 5550.0, 5350.0, 5650.0, 5450.0, 5750.0, 5550.0, 5850.0, 5650.0, 5950.0, 5750.0, 6050.0, 5850.0, 6150.0, 5950.0, 6250.0, 6050.0, 6350.0, 6150.0, 6450.0, 6250.0, 6550.0, 6350.0, 6650.0, 6450.0, 6750.0, 6550.0, 6850.0, 6650.0, 6950.0, 6750.0, 7050.0, 6850.0, 7150.0, 6950.0, 7250.0, 7050.0, 7350.0, 7150.0, 7450.0, 7250.0, 7550.0, 7350.0, 7650.0, 7450.0, 7750.0, 7550.0, 7850.0, 7650.0, 7950.0, 7750.0, 8050.0, 7850.0, 8150.0, 7950.0, 8250.0, 8050.0, 8350.0, 8150.0, 8450.0, 8250.0, 8550.0, 8350.0, 8650.0, 8450.0, 8750.0, 8550.0, 8850.0, 8650.0, 8950.0, 8750.0, 9050.0, 8850.0, 9150.0, 8950.0, 9250.0, 9050.0, 9350.0, 9150.0, 9450.0, 9250.0, 9550.0, 9350.0, 9650.0, 9450.0, 9750.0, 9550.0, 9850.0, 9650.0, 9950.0, 9750.0, 10050.0, 9850.0, 10150.0, 9950.0, 10250.0, 10050.0, 10350.0, 10150.0, 10450.0, 10250.0, 10550.0, 10350.0, 10650.0, 10450.0, 10750.0, 10550.0, 10850.0, 10650.0, 10950.0, 10750.0, 11050.0, 10850.0, 11150.0, 10950.0, 11250.0, 11050.0, 11350.0, 11150.0, 11450.0, 11250.0, 11550.0, 11350.0, 11650.0, 11450.0, 11750.0, 11550.0, 11850.0, 11550.0, 11950.0, 11650.0, 12050.0, 11750.0, 12150.0, 11850.0, 12250.0, 11950.0, 12350.0, 12050.0, 12450.0, 12050.0, 12550.0, 12050.0, 12650.0, 12050.0, 12750.0, 12150.0, 12850.0, 12250.0, 12950.0, 12350.0, 13050.0, 12450.0, 13150.0, 12550.0, 13250.0, 12650.0, 13350.0, 12750.0, 13450.0, 12850.0, 13550.0, 12950.0, 13550.0, 13050.0, 13650.0, 13150.0, 13650.0, 13250.0, 13750.0, 13350.0, 13750.0, 13450.0, 13750.0, 13550.0, 13750.0, 13650.0, 13850.0, 13750.0, 13850.0, 13850.0, 13850.0, 13950.0, 13950.0, 14050.0, 14050.0, 14150.0, 14150.0, 14250.0, 14250.0, 14350.0, 14350.0, 14450.0, 14450.0, 14550.0, 14550.0, 14650.0, 14650.0, 14750.0, 14750.0, 14850.0, 14850.0, 14950.0, 14950.0, 15050.0, 15050.0, 15150.0, 15150.0, 15250.0, 15250.0, 15350.0, 15350.0, 15450.0, 15450.0, 15550.0, 15550.0, 15650.0, 15650.0, 15750.0, 15750.0, 15850.0, 15850.0, 15950.0, 15950.0, 16050.0, 16050.0, 16150.0, 16150.0, 16250.0, 16150.0, 16350.0, 16250.0, 16450.0, 16350.0, 16550.0, 16450.0, 16650.0, 16550.0, 16750.0, 16650.0, 16750.0, 16750.0, 16750.0, 16850.0, 16750.0, 16950.0, 16850.0, 17050.0, 16850.0, 17150.0, 16950.0, 17250.0, 17050.0, 17350.0, 17150.0, 17450.0, 17150.0, 17550.0, 17150.0, 17650.0, 17250.0, 17750.0, 17250.0, 17850.0, 17250.0, 17950.0, 17250.0, 18050.0, 17250.0, 18150.0, 17250.0, 18250.0, 17250.0, 18350.0, 17250.0, 18450.0, 17350.0, 18550.0, 17450.0, 18650.0, 17450.0, 18750.0, 17450.0, 18850.0, 17550.0, 18950.0, 17650.0, 19050.0, 17650.0, 19150.0, 17650.0, 19250.0, 17650.0, 19350.0, 17650.0, 19450.0, 17650.0, 19550.0, 17650.0, 19650.0, 17650.0, 19750.0, 17650.0, 19850.0, 17650.0, 19950.0, 17650.0, 20050.0, 17650.0, 20150.0, 17650.0, 20250.0, 17650.0, 20350.0, 17650.0, 20450.0, 17750.0, 20550.0, 17850.0, 20650.0, 17950.0, 20750.0, 18050.0, 20850.0, 18150.0, 20950.0, 18250.0, 21050.0, 18350.0, 21150.0, 18450.0, 21250.0, 18550.0, 21350.0, 18650.0, 21450.0, 18750.0, 21550.0, 18850.0, 21650.0, 18950.0, 21750.0, 19050.0, 21850.0, 19150.0, 21950.0, 19250.0, 22050.0, 19350.0, 22150.0, 19450.0, 22250.0, 19550.0, 22250.0, 19650.0, 22250.0, 19750.0, 22350.0, 19850.0, 22350.0, 19950.0, 22350.0, 20050.0, 22350.0, 20150.0, 22350.0, 20250.0, 22350.0, 20350.0, 22350.0, 20450.0, 22350.0, 20550.0, 22350.0, 20650.0, 22350.0, 20750.0, 22350.0, 20850.0, 22350.0, 20950.0, 22350.0, 21050.0, 22350.0, 21150.0, 22350.0, 21250.0, 22350.0, 21350.0, 22350.0, 21450.0, 22350.0, 21550.0, 22350.0, 21650.0, 22350.0, 21750.0, 22350.0, 21850.0, 22350.0, 21950.0, 22350.0, 22050.0, 22350.0, 22150.0, 22350.0, 22250.0, 22350.0, 22350.0, 22450.0, 22450.0, 22550.0, 22550.0, 22650.0, 22650.0, 22750.0, 22750.0, 22850.0, 22850.0, 22950.0, 22950.0, 23050.0, 23050.0, 23150.0, 23150.0, 23250.0, 23250.0, 23350.0, 23350.0, 23450.0, 23450.0, 23550.0, 23550.0, 23650.0, 23650.0, 23750.0, 23750.0, 23850.0, 23850.0, 23950.0, 23950.0)),
    (3, 'short', 0, 24023, 22095, 9, 14.1422119140625,
     (2350.0, 10050.0, 2250.0, 9950.0, 2150.0, 9850.0, 2050.0, 9750.0, 1950.0, 9650.0, 1850.0, 9550.0, 1750.0, 9450.0, 1650.0, 9350.0, 1550.0, 9250.0)),
    (3, 'mid', 3, 32609, 36195, 16, 26.236236572265625,
     (20950.0, 13550.0, 20950.0, 13650.0, 20850.0, 13750.0, 20750.0, 13850.0, 20650.0, 13950.0, 20550.0, 14050.0, 20450.0, 14150.0, 20350.0, 14250.0, 20250.0, 14350.0, 20150.0, 14450.0, 20050.0, 14550.0, 19950.0, 14650.0, 19850.0, 14750.0, 19750.0, 14850.0, 19650.0, 14950.0, 19550.0, 15050.0)),
    (3, 'unwalkable-goal', 1, 44550, 14146, 17, 22.536666870117188,
     (15050.0, 18550.0, 15150.0, 18550.0, 15250.0, 18550.0, 15350.0, 18550.0, 15450.0, 18550.0, 15550.0, 18450.0, 15650.0, 18350.0, 15750.0, 18250.0, 15750.0, 18150.0, 15850.0, 18050.0, 15850.0, 17950.0, 15950.0, 17850.0, 15950.0, 17750.0, 15950.0, 17650.0, 15950.0, 17550.0, 15850.0, 17450.0, 15850.0, 17350.0)),
    (4, 'long', 0, 0, 57599, 383, 524.8636169433594,
     (50.0, 50.0, 50.0, 150.0, 50.0, 250.0, 50.0, 350.0, 50.0, 450.0, 50.0, 550.0, 50.0, 650.0, 50.0, 750.0, 50.0, 850.0, 50.0, 950.0, 50.0, 1050.0, 50.0, 1150.0, 50.0, 1250.0, 50.0, 1350.0, 50.0, 1450.0, 50.0, 1550.0, 50.0, 1650.0, 50.0, 1750.0, 50.0, 1850.0, 50.0, 1950.0, 50.0, 2050.0, 50.0, 2150.0, 50.0, 2250.0, 50.0, 2350.0, 50.0, 2450.0, 50.0, 2550.0, 50.0, 2650.0, 50.0, 2750.0, 50.0, 2850.0, 50.0, 2950.0, 50.0, 3050.0, 50.0, 3150.0, 50.0, 3250.0, 50.0, 3350.0, 50.0, 3450.0, 50.0, 3550.0, 50.0, 3650.0, 50.0, 3750.0, 50.0, 3850.0, 50.0, 3950.0, 50.0, 4050.0, 50.0, 4150.0, 50.0, 4250.0, 50.0, 4350.0, 50.0, 4450.0, 50.0, 4550.0, 50.0, 4650.0, 50.0, 4750.0, 50.0, 4850.0, 50.0, 4950.0, 50.0, 5050.0, 50.0, 5150.0, 50.0, 5250.0, 50.0, 5350.0, 50.0, 5450.0, 50.0, 5550.0, 50.0, 5650.0, 50.0, 5750.0, 50.0, 5850.0, 50.0, 5950.0, 50.0, 6050.0, 50.0, 6150.0, 50.0, 6250.0, 50.0, 6350.0, 50.0, 6450.0, 50.0, 6550.0, 50.0, 6650.0, 50.0, 6750.0, 50.0, 6850.0, 50.0, 6950.0, 50.0, 7050.0, 50.0, 7150.0, 50.0, 7250.0, 50.0, 7350.0, 50.0, 7450.0, 50.0, 7550.0, 50.0, 7650.0, 50.0, 7750.0, 50.0, 7850.0, 50.0, 7950.0, 50.0, 8050.0, 50.0, 8150.0, 50.0, 8250.0, 50.0, 8350.0, 50.0, 8450.0, 50.0, 8550.0, 50.0, 8650.0, 50.0, 8750.0, 50.0, 8850.0, 50.0, 8950.0, 50.0, 9050.0, 50.0, 9150.0, 50.0, 9250.0, 50.0, 9350.0, 50.0, 9450.0, 50.0, 9550.0, 50.0, 9650.0, 50.0, 9750.0, 50.0, 9850.0, 50.0, 9950.0, 50.0, 10050.0, 50.0, 10150.0, 50.0, 10250.0, 50.0, 10350.0, 50.0, 10450.0, 50.0, 10550.0, 50.0, 10650.0, 50.0, 10750.0, 50.0, 10850.0, 50.0, 10950.0, 50.0, 11050.0, 50.0, 11150.0, 50.0, 11250.0, 50.0, 11350.0, 50.0, 11450.0, 50.0, 11550.0, 50.0, 11650.0, 50.0, 11750.0, 50.0, 11850.0, 50.0, 11950.0, 50.0, 12050.0, 50.0, 12150.0, 50.0, 12250.0, 50.0, 12350.0, 50.0, 12450.0, 50.0, 12550.0, 150.0, 12650.0, 250.0, 12750.0, 350.0, 12850.0, 450.0, 12950.0, 550.0, 13050.0, 650.0, 13150.0, 750.0, 13250.0, 850.0, 13350.0, 950.0, 13450.0, 1050.0, 13550.0, 1150.0, 13650.0, 1250.0, 13750.0, 1350.0, 13850.0, 1350.0, 13950.0, 1350.0, 14050.0, 1350.0, 14150.0, 1350.0, 14250.0, 1450.0, 14350.0, 1550.0, 14450.0, 1650.0, 14550.0, 1750.0, 14650.0, 1850.0, 14750.0, 1850.0, 14850.0, 1850.0, 14950.0, 1950.0, 15050.0, 2050.0, 15150.0, 2150.0, 15250.0, 2250.0, 15350.0, 2350.0, 15450.0, 2350.0, 15550.0, 2350.0, 15650.0, 2450.0, 15750.0, 2550.0, 15850.0, 2650.0, 15950.0, 2750.0, 16050.0, 2850.0, 16150.0, 2950.0, 16250.0, 3050.0, 16350.0, 3150.0, 16450.0, 3150.0, 16550.0, 3150.0, 16650.0, 3250.0, 16750.0, 3350.0, 16850.0, 3450.0, 16950.0, 3550.0, 17050.0, 3650.0, 17150.0, 3750.0, 17250.0, 3750.0, 17350.0, 3750.0, 17450.0, 3750.0, 17550.0, 3750.0, 17650.0, 3750.0, 17750.0, 3750.0, 17850.0, 3850.0, 17950.0, 3950.0, 18050.0, 4050.0, 18150.0, 4150.0, 18250.0, 4250.0, 18350.0, 4350.0, 18450.0, 4350.0, 18550.0, 4350.0, 18650.0, 4450.0, 18750.0, 4550.0, 18850.0, 4650.0, 18950.0, 4750.0, 19050.0, 4850.0, 19050.0, 4950.0, 19150.0, 5050.0, 19250.0, 5150.0, 19250.0, 5250.0, 19350.0, 5350.0, 19350.0, 5450.0, 19350.0, 5550.0, 19450.0, 5650.0, 19450.0, 5750.0, 19450.0, 5850.0, 19450.0, 5950.0, 19450.0, 6050.0, 19450.0, 6150.0, 19450.0, 6250.0, 19550.0, 6350.0, 19550.0, 6450.0, 19650.0, 6550.0, 19650.0, 6650.0, 19650.0, 6750.0, 19650.0, 6850.0, 19650.0, 6950.0, 19750.0, 7050.0, 19750.0, 7150.0, 19850.0, 7250.0, 19850.0, 7350.0, 19850.0, 7450.0, 19950.0, 7550.0, 19950.0, 7650.0, 20050.0, 7750.0, 20150.0, 7850.0, 20150.0, 7950.0, 20250.0, 8050.0, 20350.0, 8150.0, 20350.0, 8250.0, 20450.0, 8350.0, 20450.0, 8450.0, 20550.0, 8550.0, 20650.0, 8650.0, 20750.0, 8750.0, 20850.0, 8850.0, 20850.0, 8950.0, 20850.0, 9050.0, 20950.0, 9150.0, 20950.0, 9250.0, 20950.0, 9350.0, 20950.0, 9450.0, 21050.0, 9550.0, 21150.0, 9650.0, 21150.0, 9750.0, 21150.0, 9850.0, 21150.0, 9950.0, 21150.0, 10050.0, 21150.0, 10150.0, 21150.0, 10250.0, 21150.0, 10350.0, 21150.0, 10450.0, 21150.0, 10550.0, 21150.0, 10650.0, 21150.0, 10750.0, 21150.0, 10850.0, 21150.0, 10950.0, 21150.0, 11050.0, 21150.0, 11150.0, 21150.0, 11250.0, 21150.0, 11350.0, 21150.0, 11450.0, 21150.0, 11550.0, 21150.0, 11650.0, 21150.0, 11750.0, 21150.0, 11850.0, 21150.0, 11950.0, 21150.0, 12050.0, 21150.0, 12150.0, 21150.0, 12250.0, 21150.0, 12350.0, 21150.0, 12450.0, 21150.0, 12550.0, 21150.0, 12650.0, 21150.0, 12750.0, 21150.0, 12850.0, 21150.0, 12950.0, 21150.0, 13050.0, 21150.0, 13150.0, 21150.0, 13250.0, 21150.0, 13350.0, 21150.0, 13450.0, 21150.0, 13550.0, 21150.0, 13650.0, 21150.0, 13750.0, 21150.0, 13850.0, 21150.0, 13950.0, 21150.0, 14050.0, 21150.0, 14150.0, 21150.0, 14250.0, 21150.0, 14350.0, 21150.0, 14450.0, 21150.0, 14550.0, 21150.0, 14650.0, 21150.0, 14750.0, 21150.0, 14850.0, 21150.0, 14950.0, 21150.0, 15050.0, 21150.0, 15150.0, 21150.0, 15250.0, 21150.0, 15350.0, 21150.0, 15450.0, 21150.0, 15550.0, 21150.0, 15650.0, 21250.0, 15750.0, 21350.0, 15850.0, 21450.0, 15950.0, 21550.0, 16050.0, 21650.0, 16150.0, 21750.0, 16250.0, 21850.0, 16350.0, 21950.0, 16450.0, 22050.0, 16550.0, 22150.0, 16650.0, 22150.0, 16750.0, 22150.0, 16850.0, 22150.0, 16950.0, 22150.0, 17050.0, 22250.0, 17150.0, 22350.0, 17250.0, 22450.0, 17350.0, 22450.0, 17450.0, 22550.0, 17550.0, 22550.0, 17650.0, 22650.0, 17750.0, 22750.0, 17850.0, 22750.0, 17950.0, 22750.0, 18050.0, 22750.0, 18150.0, 22750.0, 18250.0, 22750.0, 18350.0, 22750.0, 18450.0, 22750.0, 18550.0, 22750.0, 18650.0, 22750.0, 18750.0, 22750.0, 18850.0, 22750.0, 18950.0, 22750.0, 19050.0, 22750.0, 19150.0, 22750.0, 19250.0, 22750.0, 19350.0, 22750.0, 19450.0, 22750.0, 19550.0, 22750.0, 19650.0, 22750.0, 19750.0, 22750.0, 19850.0, 22750.0, 19950.0, 22750.0, 20050.0, 22750.0, 20150.0, 22750.0, 20250.0, 22750.0, 20350.0, 22750.0, 20450.0, 22750.0, 20550.0, 22750.0, 20650.0, 22750.0, 20750.0, 22750.0, 20850.0, 22750.0, 20950.0, 22750.0, 21050.0, 22750.0, 21150.0, 22750.0, 21250.0, 22750.0, 21350.0, 22750.0, 21450.0, 22750.0, 21550.0, 22750.0, 21650.0, 22750.0, 21750.0, 22750.0, 21850.0, 22750.0, 21950.0, 22750.0, 22050.0, 22750.0, 22150.0, 22750.0, 22250.0, 22750.0, 22350.0, 22750.0, 22450.0, 22750.0, 22550.0, 22750.0, 22650.0, 22750.0, 22750.0, 22750.0, 22850.0, 22850.0, 22950.0, 22950.0, 23050.0, 23050.0, 23150.0, 23150.0, 23250.0, 23250.0, 23350.0, 23350.0, 23450.0, 23450.0, 23550.0, 23550.0, 23650.0, 23650.0, 23750.0, 23750.0, 23850.0, 23850.0, 23950.0, 23950.0)),
    (4, 'short', 0, 20536, 18608, 9, 13.820770263671875,
     (13650.0, 8550.0, 13550.0, 8450.0, 13450.0, 8350.0, 13350.0, 8250.0, 13250.0, 8150.0, 13150.0, 8050.0, 13050.0, 7950.0, 12950.0, 7850.0, 12850.0, 7750.0)),
    (4, 'mid', 1, 42225, 47231, 35, 52.15838623046875,
     (22550.0, 17550.0, 22450.0, 17550.0, 22350.0, 17650.0, 22250.0, 17650.0, 22150.0, 17650.0, 22050.0, 17650.0, 21950.0, 17650.0, 21850.0, 17650.0, 21750.0, 17650.0, 21650.0, 17750.0, 21550.0, 17850.0, 21450.0, 17950.0, 21350.0, 18050.0, 21250.0, 18150.0, 21150.0, 18250.0, 21050.0, 18250.0, 20950.0, 18350.0, 20850.0, 18350.0, 20750.0, 18350.0, 20650.0, 18350.0, 20550.0, 18350.0, 20450.0, 18350.0, 20350.0, 18450.0, 20250.0, 18550.0, 20150.0, 18650.0, 20050.0, 18750.0, 19950.0, 18850.0, 19850.0, 18950.0, 19750.0, 19050.0, 19650.0, 19150.0, 19550.0, 19250.0, 19450.0, 19350.0, 19350.0, 19450.0, 19250.0, 19550.0, 19150.0, 19650.0)),
    (4, 'unwalkable-goal', 2, 15088, 13605, 91, 125.3560791015625,
     (20850.0, 6250.0, 20850.0, 6350.0, 20850.0, 6450.0, 20850.0, 6550.0, 20750.0, 6650.0, 20650.0, 6750.0, 20650.0, 6850.0, 20650.0, 6950.0, 20650.0, 7050.0, 20650.0, 7150.0, 20650.0, 7250.0, 20650.0, 7350.0, 20650.0, 7450.0, 20550.0, 7550.0, 20550.0, 7650.0, 20550.0, 7750.0, 20550.0, 7850.0, 20550.0, 7950.0, 20650.0, 7950.0, 20750.0, 7950.0, 20850.0, 7850.0, 20950.0, 7750.0, 21050.0, 7650.0, 21150.0, 7550.0, 21250.0, 7550.0, 21350.0, 7550.0, 21450.0, 7450.0, 21550.0, 7350.0, 21650.0, 7250.0, 21650.0, 7150.0, 21650.0, 7050.0, 21650.0, 6950.0, 21650.0, 6850.0, 21650.0, 6750.0, 21650.0, 6650.0, 21650.0, 6550.0, 21650.0, 6450.0, 21650.0, 6350.0, 21650.0, 6250.0, 21650.0, 6150.0, 21650.0, 6050.0, 21650.0, 5950.0, 21650.0, 5850.0, 21550.0, 5750.0, 21450.0, 5650.0, 21350.0, 5650.0, 21250.0, 5650.0, 21150.0, 5650.0, 21050.0, 5650.0, 20950.0, 5650.0, 20850.0, 5650.0, 20750.0, 5650.0, 20650.0, 5650.0, 20550.0, 5650.0, 20450.0, 5650.0, 20350.0, 5750.0, 20250.0, 5850.0, 20250.0, 5950.0, 20150.0, 6050.0, 20050.0, 6150.0, 20050.0, 6250.0, 19950.0, 6350.0, 19950.0, 6450.0, 19950.0, 6550.0, 19950.0, 6650.0, 19950.0, 6750.0, 19950.0, 6850.0, 19850.0, 6950.0, 19750.0, 7050.0, 19650.0, 7150.0, 19550.0, 7250.0, 19450.0, 7350.0, 19350.0, 7450.0, 19250.0, 7550.0, 19150.0, 7650.0, 19050.0, 7750.0, 18950.0, 7850.0, 18850.0, 7950.0, 18750.0, 8050.0, 18650.0, 8050.0, 18550.0, 8050.0, 18450.0, 8050.0, 18350.0, 8050.0, 18250.0, 8050.0, 18150.0, 8050.0, 18050.0, 8050.0, 17950.0, 8050.0, 17850.0, 8050.0, 17750.0, 8050.0, 17650.0, 8050.0, 17550.0, 7950.0)),
    (5, 'long', 0, 0, 57599, 360, 507.33355712890625,
     (50.0, 50.0, 150.0, 150.0, 250.0, 250.0, 350.0, 350.0, 350.0, 450.0, 350.0, 550.0, 450.0, 650.0, 550.0, 750.0, 650.0, 850.0, 750.0, 950.0, 850.0, 1050.0, 850.0, 1150.0, 850.0, 1250.0, 850.0, 1350.0, 850.0, 1450.0, 850.0, 1550.0, 850.0, 1650.0, 850.0, 1750.0, 850.0, 1850.0, 850.0, 1950.0, 850.0, 2050.0, 850.0, 2150.0, 850.0, 2250.0, 850.0, 2350.0, 850.0, 2450.0, 850.0, 2550.0, 950.0, 2650.0, 1050.0, 2750.0, 1150.0, 2850.0, 1250.0, 2950.0, 1350.0, 3050.0, 1450.0, 3150.0, 1550.0, 3250.0, 1650.0, 3350.0, 1750.0, 3450.0, 1850.0, 3550.0, 1950.0, 3650.0, 2050.0, 3750.0, 2150.0, 3850.0, 2250.0, 3950.0, 2350.0, 4050.0, 2450.0, 4150.0, 2550.0, 4250.0, 2650.0, 4350.0, 2750.0, 4450.0, 2850.0, 4550.0, 2850.0, 4650.0, 2850.0, 4750.0, 2850.0, 4850.0, 2850.0, 4950.0, 2950.0, 5050.0, 3050.0, 5150.0, 3150.0, 5250.0, 3150.0, 5350.0, 3250.0, 5450.0, 3350.0, 5550.0, 3350.0, 5650.0, 3350.0, 5750.0, 3450.0, 5850.0, 3550.0, 5950.0, 3650.0, 6050.0, 3750.0, 6150.0, 3850.0, 6250.0, 3950.0, 6350.0, 4050.0, 6450.0, 4150.0, 6550.0, 4250.0, 6650.0, 4350.0, 6750.0, 4350.0, 6850.0, 4350.0, 6950.0, 4350.0, 7050.0, 4350.0, 7150.0, 4350.0, 7250.0, 4350.0, 7350.0, 4350.0, 7450.0, 4350.0, 7550.0, 4350.0, 7650.0, 4350.0, 7750.0, 4350.0, 7850.0, 4350.0, 7950.0, 4350.0, 8050.0, 4350.0, 8150.0, 4350.0, 8250.0, 4350.0, 8350.0, 4350.0, 8450.0, 4350.0, 8550.0, 4350.0, 8650.0, 4350.0, 8750.0, 4350.0, 8850.0, 4350.0, 8950.0, 4350.0, 9050.0, 4350.0, 9150.0, 4350.0, 9250.0, 4350.0, 9350.0, 4350.0, 9450.0, 4350.0, 9550.0, 4350.0, 9650.0, 4350.0, 9750.0, 4350.0, 9850.0, 4350.0, 9950.0, 4350.0, 10050.0, 4350.0, 10150.0, 4350.0, 10250.0, 4350.0, 10350.0, 4350.0, 10450.0, 4350.0, 10550.0, 4350.0, 10650.0, 4350.0, 10750.0, 4350.0, 10850.0, 4350.0, 10950.0, 4350.0, 11050.0, 4350.0, 11150.0, 4350.0, 11250.0, 4350.0, 11350.0, 4350.0, 11450.0, 4350.0, 11550.0, 4350.0, 11650.0, 4350.0, 11750.0, 4350.0, 11850.0, 4350.0, 11950.0, 4350.0, 12050.0, 4350.0, 12150.0, 4350.0, 12250.0, 4350.0, 12350.0, 4350.0, 12450.0, 4350.0, 12550.0, 4350.0, 12650.0, 4350.0, 12750.0, 4350.0, 12850.0, 4350.0, 12950.0, 4350.0, 13050.0, 4350.0, 13150.0, 4350.0, 13250.0, 4350.0, 13350.0, 4350.0, 13450.0, 4350.0, 13550.0, 4350.0, 13650.0, 4350.0, 13750.0, 4350.0, 13850.0, 4350.0, 13950.0, 4350.0, 14050.0, 4350.0, 14150.0, 4350.0, 14250.0, 4350.0, 14350.0, 4350.0, 14450.0, 4350.0, 14550.0, 4350.0, 14650.0, 4350.0, 14750.0, 4350.0, 14850.0, 4450.0, 14950.0, 4550.0, 15050.0, 4550.0, 15150.0, 4550.0, 15250.0, 4550.0, 15350.0, 4650.0, 15450.0, 4650.0, 15550.0, 4750.0, 15650.0, 4850.0, 15750.0, 4850.0, 15850.0, 4850.0, 15950.0, 4850.0, 16050.0, 4850.0, 16150.0, 4850.0, 16250.0, 4850.0, 16350.0, 4850.0, 16450.0, 4850.0, 16550.0, 4850.0, 16650.0, 4850.0, 16750.0, 4850.0, 16850.0, 4950.0, 16950.0, 5050.0, 17050.0, 5150.0, 17150.0, 5250.0, 17250.0, 5350.0, 17350.0, 5450.0, 17450.0, 5550.0, 17550.0, 5650.0, 17650.0, 5750.0, 17750.0, 5850.0, 17850.0, 5950.0, 17950.0, 6050.0, 18050.0, 6150.0, 18150.0, 6250.0, 18250.0, 6350.0, 18350.0, 6450.0, 18450.0, 6550.0, 18550.0, 6650.0, 18650.0, 6750.0, 18750.0, 6850.0, 18850.0, 6950.0, 18950.0, 7050.0, 19050.0, 7150.0, 19150.0, 7250.0, 19250.0, 7350.0, 19350.0, 7450.0, 19450.0, 7550.0, 19550.0, 7650.0, 19650.0, 7750.0, 19750.0, 7850.0, 19850.0, 7950.0, 19950.0, 8050.0, 20050.0, 8150.0, 20150.0, 8250.0, 20250.0, 8350.0, 20350.0, 8450.0, 20450.0, 8550.0, 20550.0, 8650.0, 20550.0, 8750.0, 20650.0, 8850.0, 20750.0, 8950.0, 20750.0, 9050.0, 20850.0, 9150.0, 20850.0, 9250.0, 20850.0, 9350.0, 20950.0, 9450.0, 21050.0, 9550.0, 21050.0, 9650.0, 21050.0, 9750.0, 21050.0, 9850.0, 21050.0, 9950.0, 21050.0, 10050.0, 21050.0, 10150.0, 21050.0, 10250.0, 21050.0, 10350.0, 21050.0, 10450.0, 21050.0, 10550.0, 21050.0, 10650.0, 21050.0, 10750.0, 21050.0, 10850.0, 21050.0, 10950.0, 21050.0, 11050.0, 21050.0, 11150.0, 21050.0, 11250.0, 21050.0, 11350.0, 21050.0, 11450.0, 21050.0, 11550.0, 21050.0, 11650.0, 21050.0, 11750.0, 21050.0, 11850.0, 21050.0, 11950.0, 21050.0, 12050.0, 21050.0, 12150.0, 21050.0, 12250.0, 21050.0, 12350.0, 21050.0, 12450.0, 21050.0, 12550.0, 21050.0, 12650.0, 21050.0, 12750.0, 21050.0, 12850.0, 21050.0, 12950.0, 21050.0, 13050.0, 21150.0, 13150.0, 21250.0, 13250.0, 21350.0, 13350.0, 21450.0, 13450.0, 21550.0, 13550.0, 21650.0, 13650.0, 21750.0, 13750.0, 21850.0, 13850.0, 21950.0, 13950.0, 22050.0, 14050.0, 22150.0, 14150.0, 22250.0, 14250.0, 22250.0, 14350.0, 22250.0, 14450.0, 22350.0, 14550.0, 22350.0, 14650.0, 22350.0, 14750.0, 22350.0, 14850.0, 22350.0, 14950.0, 22450.0, 15050.0, 22450.0, 15150.0, 22450.0, 15250.0, 22450.0, 15350.0, 22450.0, 15450.0, 22450.0, 15550.0, 22450.0, 15650.0, 22450.0, 15750.0, 22450.0, 15850.0, 22450.0, 15950.0, 22450.0, 16050.0, 22450.0, 16150.0, 22450.0, 16250.0, 22450.0, 16350.0, 22450.0, 16450.0, 22450.0, 16550.0, 22450.0, 16650.0, 22450.0, 16750.0, 22450.0, 16850.0, 22450.0, 16950.0, 22450.0, 17050.0, 22450.0, 17150.0, 22450.0, 17250.0, 22450.0, 17350.0, 22450.0, 17450.0, 22450.0, 17550.0, 22450.0, 17650.0, 22450.0, 17750.0, 22450.0, 17850.0, 22450.0, 17950.0, 22450.0, 18050.0, 22450.0, 18150.0, 22450.0, 18250.0, 22450.0, 18350.0, 22450.0, 18450.0, 22450.0, 18550.0, 22450.0, 18650.0, 22450.0, 18750.0, 22450.0, 18850.0, 22450.0, 18950.0, 22450.0, 19050.0, 22450.0, 19150.0, 22450.0, 19250.0, 22450.0, 19350.0, 22450.0, 19450.0, 22450.0, 19550.0, 22450.0, 19650.0, 22450.0, 19750.0, 22450.0, 19850.0, 22450.0, 19950.0, 22450.0, 20050.0, 22450.0, 20150.0, 22450.0, 20250.0, 22450.0, 20350.0, 22450.0, 20450.0, 22450.0, 20550.0, 22450.0, 20650.0, 22450.0, 20750.0, 22450.0, 20850.0, 22450.0, 20950.0, 22450.0, 21050.0, 22450.0, 21150.0, 22450.0, 21250.0, 22450.0, 21350.0, 22450.0, 21450.0, 22450.0, 21550.0, 22450.0, 21650.0, 22450.0, 21750.0, 22450.0, 21850.0, 22450.0, 21950.0, 22450.0, 22050.0, 22450.0, 22150.0, 22450.0, 22250.0, 22450.0, 22350.0, 22450.0, 22450.0, 22450.0, 22550.0, 22550.0, 22650.0, 22650.0, 22750.0, 22750.0, 22850.0, 22850.0, 22950.0, 22950.0, 23050.0, 23050.0, 23150.0, 23150.0, 23250.0, 23250.0, 23350.0, 23350.0, 23450.0, 23450.0, 23550.0, 23550.0, 23650.0, 23650.0, 23750.0, 23750.0, 23850.0, 23850.0, 23950.0, 23950.0)),
    (5, 'short', 0, 23494, 21568, 9, 11.915069580078125,
     (21450.0, 9750.0, 21450.0, 9650.0, 21450.0, 9550.0, 21350.0, 9450.0, 21250.0, 9350.0, 21150.0, 9250.0, 21050.0, 9150.0, 20950.0, 9050.0, 20850.0, 8950.0)),
    (5, 'mid', 2, 38079, 42411, 19, 30.292572021484375,
     (15950.0, 15850.0, 16050.0, 15950.0, 16150.0, 16050.0, 16250.0, 16150.0, 16350.0, 16250.0, 16450.0, 16350.0, 16550.0, 16450.0, 16550.0, 16550.0, 16550.0, 16650.0, 16650.0, 16750.0, 16750.0, 16850.0, 16850.0, 16950.0, 16950.0, 17050.0, 17050.0, 17150.0, 17050.0, 17250.0, 17050.0, 17350.0, 17150.0, 17450.0, 17150.0, 17550.0, 17150.0, 17650.0)),
    (5, 'unwalkable-goal', 1, 15340, 14005, 24, 33.45368957519531,
     (22050.0, 6350.0, 21950.0, 6350.0, 21850.0, 6350.0, 21850.0, 6250.0, 21750.0, 6250.0, 21650.0, 6250.0, 21550.0, 6250.0, 21450.0, 6250.0, 21350.0, 6250.0, 21250.0, 6250.0, 21150.0, 6150.0, 21050.0, 6050.0, 20950.0, 6050.0, 20850.0, 6050.0, 20750.0, 6050.0, 20650.0, 5950.0, 20550.0, 5850.0, 20450.0, 5850.0, 20350.0, 5850.0, 20250.0, 5850.0, 20150.0, 5850.0, 20050.0, 5750.0, 19950.0, 5650.0, 19850.0, 5650.0)),
    (6, 'long', 0, 80, 57599, 292, 418.6243591308594,
     (8050.0, 50.0, 8050.0, 150.0, 8050.0, 250.0, 8050.0, 350.0, 8050.0, 450.0, 8050.0, 550.0, 8050.0, 650.0, 8050.0, 750.0, 8050.0, 850.0, 8050.0, 950.0, 8050.0, 1050.0, 8050.0, 1150.0, 8050.0, 1250.0, 8050.0, 1350.0, 8050.0, 1450.0, 8150.0, 1550.0, 8250.0, 1650.0, 8350.0, 1750.0, 8450.0, 1850.0, 8550.0, 1950.0, 8650.0, 2050.0, 8650.0, 2150.0, 8750.0, 2250.0, 8850.0, 2350.0, 8950.0, 2450.0, 9050.0, 2550.0, 9150.0, 2650.0, 9250.0, 2750.0, 9350.0, 2850.0, 9450.0, 2950.0, 9550.0, 3050.0, 9650.0, 3150.0, 9750.0, 3250.0, 9850.0, 3350.0, 9950.0, 3450.0, 10050.0, 3550.0, 10150.0, 3650.0, 10250.0, 3750.0, 10350.0, 3850.0, 10350.0, 3950.0, 10350.0, 4050.0, 10450.0, 4150.0, 10450.0, 4250.0, 10450.0, 4350.0, 10450.0, 4450.0, 10450.0, 4550.0, 10450.0, 4650.0, 10450.0, 4750.0, 10450.0, 4850.0, 10550.0, 4950.0, 10550.0, 5050.0, 10550.0, 5150.0, 10550.0, 5250.0, 10550.0, 5350.0, 10550.0, 5450.0, 10550.0, 5550.0, 10550.0, 5650.0, 10550.0, 5750.0, 10550.0, 5850.0, 10550.0, 5950.0, 10550.0, 6050.0, 10550.0, 6150.0, 10550.0, 6250.0, 10650.0, 6350.0, 10650.0, 6450.0, 10650.0, 6550.0, 10650.0, 6650.0, 10650.0, 6750.0, 10650.0, 6850.0, 10750.0, 6950.0, 10750.0, 7050.0, 10750.0, 7150.0, 10750.0, 7250.0, 10750.0, 7350.0, 10750.0, 7450.0, 10750.0, 7550.0, 10750.0, 7650.0, 10750.0, 7750.0, 10850.0, 7850.0, 10950.0, 7950.0, 11050.0, 8050.0, 11150.0, 8150.0, 11250.0, 8250.0, 11350.0, 8350.0, 11450.0, 8450.0, 11550.0, 8550.0, 11650.0, 8650.0, 11750.0, 8750.0, 11850.0, 8850.0, 11950.0, 8950.0, 12050.0, 9050.0, 12150.0, 9150.0, 12250.0, 9250.0, 12350.0, 9350.0, 12450.0, 9450.0, 12550.0, 9550.0, 12650.0, 9650.0, 12750.0, 9750.0, 12850.0, 9850.0, 12950.0, 9950.0, 13050.0, 10050.0, 13150.0, 10150.0, 13250.0, 10250.0, 13250.0, 10350.0, 13250.0, 10450.0, 13250.0, 10550.0, 13250.0, 10650.0, 13250.0, 10750.0, 13250.0, 10850.0, 13250.0, 10950.0, 13250.0, 11050.0, 13250.0, 11150.0, 13350.0, 11250.0, 13350.0, 11350.0, 13450.0, 11450.0, 13450.0, 11550.0, 13550.0, 11650.0, 13550.0, 11750.0, 13650.0, 11850.0, 13650.0, 11950.0, 13650.0, 12050.0, 13650.0, 12150.0, 13650.0, 12250.0, 13650.0, 12350.0, 13650.0, 12450.0, 13650.0, 12550.0, 13650.0, 12650.0, 13750.0, 12750.0, 13750.0, 12850.0, 13750.0, 12950.0, 13750.0, 13050.0, 13750.0, 13150.0, 13750.0, 13250.0, 13750.0, 13350.0, 13750.0, 13450.0, 13750.0, 13550.0, 13750.0, 13650.0, 13750.0, 13750.0, 13750.0, 13850.0, 13750.0, 13950.0, 13750.0, 14050.0, 13750.0, 14150.0, 13750.0, 14250.0, 13750.0, 14350.0, 13750.0, 14450.0, 13750.0, 14550.0, 13750.0, 14650.0, 13750.0, 14750.0, 13750.0, 14850.0, 13750.0, 14950.0, 13750.0, 15050.0, 13750.0, 15150.0, 13750.0, 15250.0, 13750.0, 15350.0, 13750.0, 15450.0, 13750.0, 15550.0, 13650.0, 15650.0, 13550.0, 15750.0, 13550.0, 15850.0, 13550.0, 15950.0, 13550.0, 16050.0, 13550.0, 16150.0, 13550.0, 16250.0, 13550.0, 16350.0, 13550.0, 16450.0, 13550.0, 16550.0, 13550.0, 16650.0, 13450.0, 16750.0, 13450.0, 16850.0, 13350.0, 16950.0, 13250.0, 17050.0, 13250.0, 17150.0, 13250.0, 17250.0, 13250.0, 17350.0, 13250.0, 17450.0, 13250.0, 17550.0, 13250.0, 17650.0, 13250.0, 17750.0, 13250.0, 17850.0, 13350.0, 17950.0, 13450.0, 18050.0, 13550.0, 18150.0, 13650.0, 18250.0, 13650.0, 18350.0, 13650.0, 18450.0, 13650.0, 18550.0, 13650.0, 18650.0, 13650.0, 18750.0, 13650.0, 18850.0, 13750.0, 18950.0, 13850.0, 19050.0, 13950.0, 19150.0, 14050.0, 19250.0, 14150.0, 19350.0, 14250.0, 19350.0, 14350.0, 19350.0, 14450.0, 19350.0, 14550.0, 19350.0, 14650.0, 19350.0, 14750.0, 19350.0, 14850.0, 19450.0, 14950.0, 19550.0, 15050.0, 19650.0, 15150.0, 19750.0, 15250.0, 19850.0, 15350.0, 19950.0, 15450.0, 20050.0, 15550.0, 20150.0, 15650.0, 20250.0, 15750.0, 20350.0, 15850.0, 20450.0, 15950.0, 20550.0, 16050.0, 20650.0, 16150.0, 20750.0, 16250.0, 20850.0, 16350.0, 20950.0, 16450.0, 21050.0, 16550.0, 21150.0, 16650.0, 21250.0, 16750.0, 21350.0, 16850.0, 21450.0, 16950.0, 21550.0, 17050.0, 21650.0, 17150.0, 21750.0, 17250.0, 21850.0, 17350.0, 21950.0, 17450.0, 21950.0, 17550.0, 21950.0, 17650.0, 21950.0, 17750.0, 21950.0, 17850.0, 21950.0, 17950.0, 21950.0, 18050.0, 21950.0, 18150.0, 21950.0, 18250.0, 21950.0, 18350.0, 21950.0, 18450.0, 21950.0, 18550.0, 21950.0, 18650.0, 21950.0, 18750.0, 21950.0, 18850.0, 21950.0, 18950.0, 21950.0, 19050.0, 21950.0, 19150.0, 21950.0, 19250.0, 21950.0, 19350.0, 21950.0, 19450.0, 21950.0, 19550.0, 21950.0, 19650.0, 21950.0, 19750.0, 21950.0, 19850.0, 21950.0, 19950.0, 21950.0, 20050.0, 21950.0, 20150.0, 21950.0, 20250.0, 21950.0, 20350.0, 21950.0, 20450.0, 21950.0, 20550.0, 21950.0, 20650.0, 21950.0, 20750.0, 21950.0, 20850.0, 21950.0, 20950.0, 21950.0, 21050.0, 21950.0, 21150.0, 21950.0, 21250.0, 21950.0, 21350.0, 21950.0, 21450.0, 21950.0, 21550.0, 21950.0, 21650.0, 21950.0, 21750.0, 21950.0, 21850.0, 21950.0, 21950.0, 21950.0, 22050.0, 22050.0, 22150.0, 22150.0, 22250.0, 22250.0, 22350.0, 22350.0, 22450.0, 22450.0, 22550.0, 22550.0, 22650.0, 22650.0, 22750.0, 22750.0, 22850.0, 22850.0, 22950.0, 22950.0, 23050.0, 23050.0, 23150.0, 23150.0, 23250.0, 23250.0, 23350.0, 23350.0, 23450.0, 23450.0, 23550.0, 23550.0, 23650.0, 23650.0, 23750.0, 23750.0, 23850.0, 23850.0, 23950.0, 23950.0)),
    (6, 'short', 0, 33360, 31440, 9, 10.0,
     (50.0, 13950.0, 50.0, 13850.0, 50.0, 13750.0, 50.0, 13650.0, 50.0, 13550.0, 50.0, 13450.0, 50.0, 13350.0, 50.0, 13250.0, 50.0, 13150.0)),
    (6, 'mid', 1, 20495, 33221, 54, 65.91520690917969,
     (9550.0, 8550.0, 9550.0, 8650.0, 9550.0, 8750.0, 9550.0, 8850.0, 9550.0, 8950.0, 9550.0, 9050.0, 9550.0, 9150.0, 9550.0, 9250.0, 9550.0, 9350.0, 9550.0, 9450.0, 9550.0, 9550.0, 9550.0, 9650.0, 9550.0, 9750.0, 9550.0, 9850.0, 9550.0, 9950.0, 9550.0, 10050.0, 9550.0, 10150.0, 9550.0, 10250.0, 9550.0, 10350.0, 9550.0, 10450.0, 9550.0, 10550.0, 9550.0, 10650.0, 9550.0, 10750.0, 9550.0, 10850.0, 9550.0, 10950.0, 9550.0, 11050.0, 9550.0, 11150.0, 9550.0, 11250.0, 9550.0, 11350.0, 9550.0, 11450.0, 9650.0, 11550.0, 9750.0, 11650.0, 9850.0, 11750.0, 9950.0, 11850.0, 9950.0, 11950.0, 9950.0, 12050.0, 9950.0, 12150.0, 9950.0, 12250.0, 9950.0, 12350.0, 9950.0, 12450.0, 9950.0, 12550.0, 9950.0, 12650.0, 9950.0, 12750.0, 9950.0, 12850.0, 10050.0, 12950.0, 10050.0, 13050.0, 10050.0, 13150.0, 10050.0, 13250.0, 10050.0, 13350.0, 10150.0, 13450.0, 10150.0, 13550.0, 10150.0, 13650.0, 10150.0, 13750.0, 10150.0, 13850.0)),
    (6, 'unwalkable-goal', 2, 20606, 14561, 3, 2.272735595703125,
     (20650.0, 8550.0, 20650.0, 8450.0, 20650.0, 8350.0)),
)
# TD-VG-W-2: save_sha256 only (save format 10 -> 11; checksum, full_ret, sections and save_len unchanged). Old -> new:
# seed 1 plain and loaded a68c1462...bf06033 -> 0db78a2e...a9df46, seed 1 twice 531c51fe...ed81061 -> 9d55a380...a351519,
# seed 3 plain and loaded 56b3eafd...9a85af -> 4e5a354a...e6771d7b, seed 3 twice e7185fcc...4754322e -> 9d1d36ea...fd96af64.
# TD-VG-E-27: save_sha256 only (save format 11 -> 12; checksum, full_ret, sections and save_len unchanged, recorded from the E7
# build). Old -> new: seed 1 plain and loaded 0db78a2e...a9df46 -> 12de5484...66051a, seed 1 twice 9d55a380...a351519 ->
# 910a377d...59b8d8, seed 3 plain and loaded 4e5a354a...e6771d7b -> dccbaaa0...6272ec, seed 3 twice 9d1d36ea...fd96af64 ->
# afec8b4e...d60753. All six literals moved.
GOLDEN_D = {1: {'loaded': {'checksum': '1c894c9eab51b351',
                'full_ret': '402b8b4089ea4883',
                'save_len': 1423480,
                'save_sha256': 'aa4df09abba6073b348b1d471de005e20e658800808a692654d10c5386bdccbe',
                'sections': ['13259bb6ab30dba9',
                             '57d5e28a158df70e',
                             'bb36e4bc65405e92',
                             '6e756c6c74616374',
                             '640e7e673df7923b',
                             '6d6973735f6e756c',
                             '0000000000006f67',
                             '0000000000006d61',
                             'a39b897013fccca2']},
     'plain': {'checksum': '1c894c9eab51b351',
               'full_ret': '402b8b4089ea4883',
               'save_len': 1423480,
               'save_sha256': 'aa4df09abba6073b348b1d471de005e20e658800808a692654d10c5386bdccbe',
               'sections': ['13259bb6ab30dba9',
                            '57d5e28a158df70e',
                            'bb36e4bc65405e92',
                            '6e756c6c74616374',
                            '640e7e673df7923b',
                            '6d6973735f6e756c',
                            '0000000000006f67',
                            '0000000000006d61',
                            'a39b897013fccca2']},
     'twice': {'checksum': '1c894c9eab51b351',
               'full_ret': 'c98745e9cf9d98b3',
               'save_len': 1423480,
               'save_sha256': '153edc79b70f556dffa56416bc0ba6cbb6ca97c3f3e3f5ba8eb26aa5e3f4feff',
               'sections': ['13259bb6ab30dba9',
                            '57d5e28a158df70e',
                            'bb36e4bc65405e92',
                            '6e756c6c74616374',
                            '8df0e387d4f5c442',
                            '6d6973735f6e756c',
                            '0000000000006f67',
                            '0000000000006d61',
                            'a39b897013fccca2']}},
 3: {'loaded': {'checksum': '1c894c9eab51b351',
                'full_ret': 'db9320bdfd37b18c',
                'save_len': 1423480,
                'save_sha256': 'bf367cc1bcf79bfce050b2a5918025a0c8970959d8ef9a7401078aa25b0c3691',
                'sections': ['13259bb6ab30dba9',
                             '57d5e28a158df70e',
                             'bb36e4bc65405e92',
                             '6e756c6c74616374',
                             '640e7e673df7923b',
                             '6d6973735f6e756c',
                             '0000000000006f67',
                             '0000000000006d61',
                             '0303387bef0e00f8']},
     'plain': {'checksum': '1c894c9eab51b351',
               'full_ret': 'db9320bdfd37b18c',
               'save_len': 1423480,
               'save_sha256': 'bf367cc1bcf79bfce050b2a5918025a0c8970959d8ef9a7401078aa25b0c3691',
               'sections': ['13259bb6ab30dba9',
                            '57d5e28a158df70e',
                            'bb36e4bc65405e92',
                            '6e756c6c74616374',
                            '640e7e673df7923b',
                            '6d6973735f6e756c',
                            '0000000000006f67',
                            '0000000000006d61',
                            '0303387bef0e00f8']},
     'twice': {'checksum': '1c894c9eab51b351',
               'full_ret': '10a151ea4b2ebb8b',
               'save_len': 1423480,
               'save_sha256': 'bd63a9025174990c836e74693611aaff69252f49a524a0b118541fb28ad7275f',
               'sections': ['13259bb6ab30dba9',
                            '57d5e28a158df70e',
                            'bb36e4bc65405e92',
                            '6e756c6c74616374',
                            '8df0e387d4f5c442',
                            '6d6973735f6e756c',
                            '0000000000006f67',
                            '0000000000006d61',
                            '0303387bef0e00f8']}}}
GOLDEN_B = (
    (17686.869270276355, 9187.250368649376, 0),
    (17667.57814182131, 9164.343503543898, 0),
    (17583.976205428742, 8910.339417152605, 0),
    (17579.459190606594, 8880.772184894891, 0),
    (17635.66903699331, 8900.360056210642, 0),
    (17665.212265745682, 8907.120010620936, 0),
    (17655.291702263043, 8878.399285036052, 0),
    (17745.965981948502, 8926.879511298526, 0),
    (17767.534440303694, 8906.060530561539, 0),
    (17861.126466971924, 9039.29894151808, 0),
    (17843.382984085893, 9063.141841130453, 0),
    (17865.158024809414, 9083.592310995162, 0),
    (18344.482395676692, 8963.732059250922, 0),
    (18365.220132631188, 8996.553106018795, 0),
    (18315.789772005242, 9014.434499900752, 0),
    (18345.85660220711, 9018.117278064492, 0),
    (18367.23472773365, 8939.69187782993, 0),
    (18445.307906354185, 9018.225745695028, 0),
    (18499.301613501924, 9061.242030557169, 0),
    (18524.09481981589, 9093.165855242205, 0),
    (18527.063229488565, 9147.460421061503, 0),
    (18473.60350254259, 9036.330612326823, 0),
    (18641.88013819364, 9137.724165059768, 0),
    (18692.331378069244, 9190.380282057613, 0),
    (18736.408869357732, 9147.053303078788, 0),
    (17715.188664590194, 9238.837657411606, 0),
    (17696.12357509297, 9215.731142784676, 0),
    (17589.474452401624, 8939.839457454747, 0),
    (17607.663197527225, 8890.199556813795, 0),
    (17640.54695134905, 8929.35264534183, 0),
    (17668.233044349014, 8936.634636598768, 0),
    (17684.762542114746, 8883.999015289315, 0),
    (17754.51237728927, 8956.54575804174, 0),
    (17774.784261717374, 8934.798359717895, 0),
    (17950.08506094124, 9151.639052833052, 0),
    (17979.585476291042, 9146.294338570928, 0),
    (17924.4496568163, 9136.110550665473, 0),
    (18334.825519620226, 8991.336651866504, 0),
    (18316.764903152696, 8866.79659877767, 0),
    (18334.048564881847, 8891.24877210135, 0),
    (18327.970982818264, 9041.582901644017, 0),
    (18374.83114410632, 8968.546148046573, 0),
    (18456.55697271428, 9061.016642431154, 0),
    (18484.52231067072, 9111.420431786539, 0),
    (18512.947665858497, 9121.008025079578, 0),
    (18577.599624753213, 9150.629699406545, 0),
    (18477.817752498064, 9082.17921259668, 0),
    (18666.606378011693, 9163.96926842493, 0),
    (18717.228107147625, 9216.427773614554, 0),
    (18739.344895919192, 9178.92448689692, 0),
    (17738.608495395198, 9257.565391241376, 0),
    (17742.245030003196, 9225.893522297205, 0),
    (17595.27603422199, 8969.334561888261, 0),
    (17612.117107918046, 8919.61659948566, 0),
    (17646.915640729636, 8958.43441460478, 0),
    (17697.26708050791, 8941.340650789996, 0),
    (17695.744724118227, 8911.721889571281, 0),
    (17783.209819937652, 8963.154808473006, 0),
    (17802.85609870035, 8924.216678925075, 0),
    (17940.76456706905, 9179.941529217618, 0),
    (17959.32373399761, 9202.70229839209, 0),
    (17851.532513375838, 9008.50990401608, 0),
    (18248.602641964724, 9022.411319235463, 0),
    (18279.749721169333, 9015.87017516026, 0),
    (18329.994244059166, 9070.40933680758, 0),
    (18397.60176529788, 9045.980481148606, 0),
    (18360.68244471884, 9073.319661529618, 0),
    (18406.442587754707, 9100.420558065212, 0),
    (18356.79929534138, 9045.040092989488, 0),
    (18551.318205797295, 9165.096167187381, 0),
    (18592.11233151617, 9176.88577189297, 0),
    (18620.30990342719, 9199.618735020085, 0),
    (18640.629049879313, 9222.223542909216, 0),
    (18543.20604227161, 9122.01069893619, 0),
    (18733.16223464121, 9246.892117330646, 0),
    (17764.96102095855, 9282.334182273302, 0),
    (17768.167434586005, 9252.513396693847, 0),
    (17602.55149085174, 8998.693648684857, 0),
    (17617.80645888416, 8948.718342362525, 0),
    (17675.376617194976, 8965.288017468001, 0),
    (17704.686102923828, 8970.667803422402, 0),
    (17674.88516253971, 8855.671689740815, 0),
    (17762.685231835596, 8984.780165254426, 0),
    (17811.401979090915, 8952.991620413204, 0),
    (17978.04791920619, 9225.025361773143, 0),
    (18000.39583753919, 9168.298466766613, 0),
    (17970.223214914386, 9174.573757982631, 0),
    (18219.059837478268, 9027.246290348487, 0),
    (18269.269300363638, 9043.497124318872, 0),
    (18343.305452315344, 9096.565423409204, 0),
    (18391.21999850317, 9074.565693435077, 0),
    (18313.650548624373, 9094.942592753678, 0),
    (18375.186355087193, 9098.685271007322, 0),
    (18421.47350457659, 9126.388651204114, 0),
    (18565.452596825402, 9191.549994147132, 0),
    (18591.214997525112, 9206.915506226778, 0),
    (18611.426116611987, 9229.085546038561, 0),
    (18635.87728465701, 9251.941034809892, 0),
    (18665.67526479061, 9247.89434844891, 0),
    (18740.126058938913, 9281.182724176984, 0),
    (17792.439372438363, 9309.985757485514, 0),
    (17795.081484783645, 9279.987033896396, 0),
    (17623.971942715543, 8977.687949780522, 0),
    (17654.545008147084, 8987.24933074178, 0),
    (17683.336208237273, 8993.727821187205, 0),
    (17712.700391316725, 8999.618407463755, 0),
    (17726.122199908466, 8949.075263159846, 0),
    (17770.913388061956, 9013.198202655018, 0),
    (17791.337117829386, 8991.662252063707, 0),
    (17988.823545716707, 9197.371310033572, 0),
    (18018.38506947365, 9191.7936714562, 0),
    (17880.224860421386, 9016.044335598184, 0),
    (18207.700731200035, 9053.888521459587, 0),
    (18291.358510898415, 9067.177351642547, 0),
    (18298.732340781113, 9038.681265159214, 0),
    (18259.26130033738, 9070.959034226136, 0),
    (18239.833931830697, 8971.238340894964, 0),
    (18357.96416965465, 9122.263531387765, 0),
    (18389.223524355235, 9124.24832026855, 0),
    (18372.577003359616, 9148.122330681319, 0),
    (18403.76787891696, 9149.850375455328, 0),
    (18377.693117807037, 9023.512246307257, 0),
    (18690.88404877158, 9273.227045461646, 0),
    (18714.97461063106, 9297.532707371436, 0),
    (18738.990884065417, 9322.589777816456, 0),
    (17817.478637615797, 9334.952882263695, 0),
    (17822.283817451626, 9305.159531158459, 0),
    (17631.660402569527, 9006.399209069989, 0),
    (17662.900510401243, 9015.939461476191, 0),
    (17692.05124061039, 9022.023062806678, 0),
    (17721.081309994715, 9028.33842963812, 0),
    (17733.488721608228, 8977.881923700867, 0),
    (17800.106043975065, 9020.014797680818, 0),
    (17819.692258831765, 8981.865008638366, 0),
    (17995.929300197466, 9247.866270050627, 0),
    (18007.496515654522, 9219.861775886651, 0),
    (17915.60881149739, 9093.657438993256, 0),
    (18238.49204114327, 9049.371994850388, 0),
    (18197.687586158263, 9081.812491681845, 0),
    (18227.005001375936, 9075.930623045731, 0),
    (18247.063458932505, 9097.515153568422, 0),
    (18278.52645402123, 9093.529468468327, 0),
    (18336.265661338944, 8934.913626450023, 0),
    (18327.81359288073, 9121.06765880144, 0),
    (18342.87668850841, 9147.097680952638, 0),
    (18387.624968059165, 9173.928557514711, 0),
    (18355.65322079372, 8912.11213171703, 0),
    (18661.10320350301, 9277.630281719692, 0),
    (18709.09228744145, 9326.948511268509, 0),
    (18748.804193775795, 9370.55934707663, 0),
    (17840.664068913567, 9358.013262410315, 0),
    (17846.846970285915, 9328.548937670197, 0),
    (17610.34253000819, 9027.706933042311, 0),
    (17672.05989992843, 9044.350918110667, 0),
    (17700.991180475954, 9050.505796817255, 0),
    (17729.90245273289, 9057.049125894186, 0),
    (17741.78792101716, 9006.46328731335, 0),
    (17808.550908250094, 9048.612495083025, 0),
    (17829.302592420336, 9027.876156587323, 0),
    (18002.081845362227, 9296.771950386947, 0),
    (18037.290612466357, 9214.415277948588, 0),
    (18030.147704027855, 9162.918663244838, 0),
    (18239.995068421278, 8941.62188641354, 0),
    (18212.7052345896, 8958.96192223539, 0),
    (18217.378484443972, 9103.068237071973, 0),
    (18266.598131719064, 9119.984781486557, 0),
    (18272.10787156254, 8967.412087018689, 0),
    (18363.384540188665, 8883.1254675348, 0),
    (18357.237618582418, 9172.801135353448, 0),
    (18420.446018019473, 9174.7078430782, 0),
    (18371.38164809753, 9198.293242944545, 0),
    (18340.99378161411, 8849.105882328022, 0),
    (18685.494173568, 9303.091828756244, 0),
    (18724.8920650257, 9352.44747676477, 0),
    (18739.070130875436, 9398.921864536633, 0),
    (17862.5843381118, 9379.660912017973, 0),
    (17869.870002880136, 9350.525045416176, 0),
    (17639.831256023448, 9035.106016309523, 0),
    (17681.047207124993, 9072.952985592892, 0),
    (17710.194071297185, 9079.051004253011, 0),
    (17739.166336830123, 9085.674817590905, 0),
    (17750.247514509516, 9034.965773295338, 0),
    (17833.79133272835, 9136.549605305498, 0),
    (17817.04075463656, 9076.824371402077, 0),
    (18026.26091759729, 9242.132079006014, 0),
    (18014.98072274009, 9269.616851511637, 0),
    (17883.22167652128, 9059.755856960952, 0),
    (18120.260034266583, 9151.146573933542, 0),
    (18150.29628564737, 9148.226072532556, 0),
    (18177.708433139083, 9054.568269223762, 0),
    (18217.352869146052, 9147.71517278631, 0),
    (18235.69873312788, 9124.368474123157, 0),
    (18283.15415560864, 9144.866654173911, 0),
    (18259.148126717024, 8994.468417396976, 0),
    (18342.067894229567, 9198.228771180902, 0),
    (18403.468972341296, 9198.96101627483, 0),
    (18386.971039995322, 9223.56019574125, 0),
    (18401.993963524827, 9249.125750097855, 0),
    (18418.97866326088, 9224.422327208005, 0),
    (18746.415826155782, 9427.988167788473, 0),
    (17882.39545481403, 9402.189108905666, 0),
    (17891.724888620796, 9372.471775161526, 0),
    (17659.017958347056, 9093.317469339843, 0),
    (17697.055446081205, 9106.009914741497, 0),
    (17726.719894458143, 9112.460001427757, 0),
    (17768.248649426485, 9093.080250485453, 0),
    (17758.862826102995, 9063.71246719933, 0),
    (17977.57789846069, 9278.982046187139, 0),
    (17838.477484163133, 9096.969637002461, 0),
    (18032.533222753722, 9292.783433417893, 0),
    (18078.030912919057, 9181.766858087778, 0),
    (18048.22595078133, 9186.640269178331, 0),
    (18090.45263977177, 9154.446865026954, 0),
    (18137.966279240944, 9174.921964997478, 0),
    (18253.337377588035, 9146.101597935634, 0),
    (18313.311874596835, 9146.136125222116, 0),
    (18192.2764258502, 9118.239361676031, 0),
    (18197.67761685027, 9169.518843275984, 0),
    (18296.838545135564, 9119.090151229533, 0),
    (18355.97901667074, 9223.223837389956, 0),
    (18371.10145461472, 9248.80465291047, 0),
    (18385.401873809038, 9274.972767099329, 0),
    (18399.566808615364, 9301.577365887644, 0),
    (18415.013855497265, 9275.852424977855, 0),
    (18766.043357312614, 9450.644717416199, 0),
    (17707.938378594812, 9267.948365973665, 0),
    (17911.575598782027, 9394.963318739072, 0),
    (17649.118176122443, 9063.556281963853, 0),
    (17755.64642861732, 9119.979523803142, 0),
    (17967.641108820106, 9307.23656269585, 0),
    (17991.518924823307, 9324.891501524125, 0),
    (17779.55753000646, 9041.638652366182, 0),
    (18009.82985819425, 9348.448432825679, 0),
    (17784.854666787058, 9126.496138780447, 0),
    (18055.541164652008, 9237.599485705627, 0),
    (18044.075603449906, 9265.436053831256, 0),
    (17887.36953951933, 9103.739683277001, 0),
    (18108.316605595923, 9178.315457679226, 0),
    (18126.197620473587, 9202.275152135277, 0),
    (18169.897509580656, 9091.933814282205, 0),
    (18155.352150062514, 9199.288257332355, 0),
    (18110.387887772402, 9098.179550623701, 0),
    (18268.0840494473, 9170.284329029939, 0),
    (18297.571610802348, 9170.936038441405, 0),
    (18251.749173586682, 9194.791290234283, 0),
    (18282.442529654647, 9195.43948304874, 0),
    (18327.967461534627, 9172.317857453263, 0),
    (18369.857746916405, 9300.569834270484, 0),
    (18383.041768497547, 9327.16201602025, 0),
    (18786.044169187946, 9472.97678930684, 0),
    (17923.6947580519, 9446.44275868875, 0),
    (17903.855479933936, 9423.94861288773, 0),
    (17629.49204574218, 9086.245817135312, 0),
    (17706.444586547117, 9134.57135346948, 0),
    (18020.982544616058, 9320.666621046463, 0),
    (18027.974306685457, 9372.283897978785, 0),
    (17788.157648211185, 9070.37952860308, 0),
    (18056.809409463975, 9367.867559572838, 0),
    (17982.957974143737, 9360.918080922227, 0),
    (18050.046472176575, 9316.300980779171, 0),
    (18073.40139743621, 9261.118050936555, 0),
    (17913.543103262287, 9063.812690460909, 0),
    (18096.577492542634, 9205.799187458471, 0),
    (18144.180656024724, 9226.3797562261, 0),
    (18179.311361344997, 9274.48761311299, 0),
    (18180.204324894396, 9145.229040008895, 0),
    (18132.573676860837, 9123.879626816579, 0),
    (18236.439399637395, 9170.207056233332, 0),
    (18217.088955164345, 9192.99305744337, 0),
    (18267.34336494855, 9220.024731022208, 0),
    (18295.977206206153, 9221.93972926897, 0),
    (18312.20298853902, 9197.079820864215, 0),
    (18471.967209730086, 9388.416323233527, 0),
    (18551.876671345515, 9432.052046265959, 0),
    (18805.02458810926, 9496.190885920183, 0),
    (17953.680778584032, 9471.432665685901, 0),
    (17952.920152946976, 9439.759734937978, 0),
    (17735.48279767313, 9142.202467080675, 0),
    (17764.852648178858, 9148.586608639554, 0),
    (18000.814465190666, 9385.025045216616, 0),
    (18049.23557517374, 9395.751050392813, 0),
    (17797.629544630567, 9099.372182609623, 0),
    (18038.99349968101, 9344.224307812307, 0),
    (17858.582541456533, 9119.235904566403, 0),
    (18061.880861525744, 9288.647826706096, 0),
    (18079.39582912901, 9312.223621429821, 0),
    (18090.98515340247, 9284.922900693236, 0),
    (18173.27070634729, 9222.960962932902, 0),
    (18114.656458544432, 9229.69943800676, 0),
    (18185.676218156925, 9196.251024313984, 0),
    (18196.272705079784, 9298.614075444566, 0),
    (18167.73155620265, 9172.452937278866, 0),
    (18229.3349277109, 8999.34120396072, 0),
    (18234.06572684389, 9217.956184591994, 0),
    (18280.60070543267, 9247.548871994843, 0),
    (18310.242698694106, 9247.963763349126, 0),
    (18326.090095888147, 9222.979626399509, 0),
    (18496.76775624833, 9405.29627846636, 0),
    (18412.70374726807, 9328.618353000904, 0),
    (18824.899362121196, 9518.654819061921, 0),
    (17967.19375940745, 9498.216977311664, 0),
    (17992.22645391319, 9481.333343201626, 0),
    (18002.81338474966, 9509.303947473802, 0),
    (17790.3524681745, 9232.318736887917, 0),
    (18104.64462826491, 9437.864679325041, 0),
    (18086.90820956665, 9412.755001831465, 0),
    (18123.20125054624, 9462.258818763832, 0),
    (18152.55001883544, 9479.709727100633, 0),
    (17805.941307942918, 9147.835153864655, 0),
    (18068.034035162626, 9339.840301592754, 0),
    (18120.217346250258, 9281.434776580232, 0),
    (18102.811172539663, 9257.704298612856, 0),
    (18102.453992975115, 9127.048900772636, 0),
    (18191.087010053474, 9247.035971352723, 0),
    (18185.581686621877, 9326.255186438995, 0),
    (18191.719467033807, 9378.363453871083, 0),
    (18162.472770113305, 9121.077160129491, 0),
    (18203.793581465583, 9219.93848539805, 0),
    (18251.35201945282, 9243.830146990102, 0),
    (18295.541914800142, 9273.815032609553, 0),
    (18353.33773511928, 9326.213615103503, 0),
    (18340.7751971975, 9248.384941166883, 0),
    (18594.461488293055, 9491.222657829243, 0),
    (18432.12583691874, 9251.352183696112, 0),
    (18834.875660878635, 9546.947458795647, 0),
    (17978.095748980606, 9526.265806311985, 0),
    (18005.37768564662, 9539.207032513577, 0),
    (18029.95636084571, 9522.027840074257, 0),
    (17933.217589397285, 9417.188236424396, 0),
    (18021.333556925958, 9407.077482608156, 0),
    (18045.88088684443, 9425.547913970991, 0),
    (18210.430491834355, 9522.917548377098, 0),
    (18180.49810885806, 9520.904478740804, 0),
    (18180.382959531744, 9490.904699731072, 0),
    (18108.743946100985, 9308.47202047298, 0),
    (18131.94014185796, 9253.594760996986, 0),
    (17902.641884828303, 9035.863389277258, 0),
    (18174.190667438503, 9353.950830478112, 0),
    (18162.021939482973, 9381.285061021077, 0),
    (18262.35875993661, 9450.903941034714, 0),
    (18223.687380107833, 9295.231582299115, 0),
    (18140.23704297313, 9094.874923407839, 0),
    (18220.693323103304, 9244.142325977444, 0),
    (18266.499729864994, 9273.94097567733, 0),
    (18282.072167428843, 9300.5674268244, 0),
    (18517.533715593883, 9426.947489343785, 0),
    (18325.309676359993, 9273.645894871583, 0),
    (18649.25793739303, 9537.454003908244, 0),
    (18654.394361083938, 9566.974801098408, 0),
    (18838.67594275584, 9577.238252854053, 0),
    (18018.237145439656, 9621.210350626325, 0),
    (18041.830208122938, 9639.728361595151, 0),
    (18013.571087811215, 9568.154338775092, 0),
    (18038.314034473973, 9551.27227314024, 0),
    (18058.97622808362, 9529.583579918635, 0),
    (17739.998934170955, 9175.94289862087, 0),
    (18024.757443162023, 9488.867769268743, 0),
    (18238.370021317838, 9551.021455993014, 0),
    (18261.964383443363, 9569.549976168617, 0),
    (18097.39001857363, 9335.69526640799, 0),
    (18126.69925098335, 9332.859346419371, 0),
    (18156.58599736848, 9330.007315630874, 0),
    (18137.812583977644, 9305.871477219402, 0),
    (18084.916926075337, 9233.763881009625, 0),
    (18288.661442582215, 9492.080184286939, 0),
    (18179.375712887704, 9405.499604224464, 0),
    (18203.217386122404, 9350.913938144051, 0),
    (18237.430931200226, 9269.037401289328, 0),
    (18323.1566488366, 9327.054803262568, 0),
    (18534.375148767627, 9456.417938563507, 0),
    (18621.651691614847, 9525.711125469183, 0),
    (18310.323158291456, 9299.885037777718, 0),
    (18631.792899317952, 9589.691043719507, 0),
    (18662.049735320314, 9595.960026710498, 0),
    (18843.87806015714, 9607.57710259345, 0),
    (18037.91960050476, 9669.442799144428, 0),
    (18066.269253396484, 9658.042540395438, 0),
    (18043.5149445536, 9580.820084444586, 0),
    (18072.990744948365, 9588.504120438827, 0),
    (18111.770867714913, 9610.399912570301, 0),
    (18067.273276768316, 9559.076784384912, 0),
    (17722.688241967004, 9200.44473396886, 0),
    (18072.700264846986, 9438.991163710389, 0),
    (18288.382597537508, 9583.765389074188, 0),
    (18114.87710526506, 9360.087468627291, 0),
    (18234.53574846101, 9439.68705795882, 0),
    (18253.8216348423, 9479.636101757216, 0),
    (18319.3863638091, 9532.612684121423, 0),
    (18066.797853671484, 9209.853648571945, 0),
    (18318.259299964895, 9472.675201434306, 0),
    (18209.06290556781, 9403.448623175582, 0),
    (18221.462487336183, 9374.23477412085, 0),
    (18207.525414961274, 9271.416497437414, 0),
    (18339.14432470681, 9352.439724382579, 0),
    (18568.232819843637, 9474.503774378043, 0),
    (18612.037062325486, 9614.376970174286, 0),
    (18355.624735341582, 9274.336227311092, 0),
    (18691.820439652678, 9599.642784064115, 0),
    (18433.385542239754, 9299.368457732511, 0),
    (18846.785678667853, 9640.76111071916, 0),
    (18078.295611928294, 9685.526462852937, 0),
    (18104.251030363645, 9700.570265582965, 0),
    (17731.373977068124, 9286.680022349727, 0),
    (18057.408308701626, 9614.126227968443, 0),
    (18127.578528766015, 9636.069905706092, 0),
    (18141.742869076934, 9609.245576440806, 0),
    (18102.25978888882, 9581.959639085853, 0),
    (18284.926061975053, 9613.72733067098, 0),
    (18313.12523626816, 9603.111170910099, 0),
    (18085.476261176966, 9363.265228507275, 0),
    (18132.323864552214, 9384.50247120706, 0),
    (18119.57368180455, 9411.97344448638, 0),
    (18225.990815007273, 9468.44449592528, 0),
    (18149.853074709816, 9277.838839504255, 0),
    (18161.85376010469, 9250.445120502123, 0),
    (18393.36340143151, 9576.512293250506, 0),
    (18258.395014211605, 9421.24592755277, 0),
    (18252.072733138782, 9300.751661122284, 0),
    (18624.903335170937, 9560.492860456432, 0),
    (18442.74254373988, 9327.87190529463, 0),
    (18641.802117441195, 9618.092871896662, 0),
    (18340.206812496614, 9300.071177381897, 0),
    (18682.160031247287, 9653.340653055458, 0),
    (18728.59657403367, 9712.177686422352, 0),
    (18847.59211496185, 9678.397155076973, 0),
    (17940.54656598829, 9763.193990457203, 0),
    (17916.83916700507, 9719.501574490361, 0),
    (18114.205024581905, 9728.870760262438, 0),
    (18144.134158261364, 9726.381510272286, 0),
    (18148.32433843424, 9658.761972211287, 0),
    (18198.650860073936, 9689.665764307276, 0),
    (18176.25896936901, 9669.700715238783, 0),
    (18052.465307735347, 9500.334439550938, 0),
    (17979.078642360924, 9454.367901403168, 0),
    (18315.67024639235, 9633.003024707878, 0),
    (18345.556422834565, 9635.61385937613, 0),
    (18375.346602322217, 9661.272546482913, 0),
    (18419.590308724742, 9598.712230155794, 0),
    (18390.27013403625, 9606.357833335785, 0),
    (18344.402193533493, 9549.556224702297, 0),
    (18440.3129818707, 9621.008510675758, 0),
    (18167.650428266064, 9301.989495942411, 0),
    (18462.372909563455, 9643.479759280977, 0),
    (18238.690529132553, 9398.650784610938, 0),
    (18623.166575922663, 9643.611477372182, 0),
    (18673.40945986926, 9623.726132994454, 0),
    (18709.81817694852, 9688.781708073233, 0),
    (18725.425052143106, 9742.38754902773, 0),
    (18755.979126675826, 9786.893728227225, 0),
    (18752.4301271524, 9755.453762088235, 0),
    (17963.437045227023, 9782.512036359945, 0),
    (17943.498162195046, 9733.212151402064, 0),
    (18135.27791164856, 9755.125254882165, 0),
    (18165.038223477233, 9751.161829741824, 0),
    (18088.713484003547, 9629.592470047308, 0),
    (18103.98991346968, 9655.411662574694, 0),
    (18217.64221354438, 9738.558739243159, 0),
    (18245.504129025667, 9727.446564048958, 0),
    (18194.02142297796, 9719.306417339463, 0),
    (18345.642499934595, 9665.644041765107, 0),
    (18376.6619677944, 9691.243681206384, 0),
    (18405.870217896932, 9698.090280096358, 0),
    (18102.554547259635, 9387.436247074333, 0),
    (18149.73338528033, 9408.675063008219, 0),
    (18411.033312023028, 9628.011711507821, 0),
    (18455.324393877636, 9672.82797925764, 0),
    (18144.78524335987, 9357.213021996567, 0),
    (18484.137357784384, 9664.154573197542, 0),
    (18215.24354442496, 9323.313464196975, 0),
    (18649.598794451635, 9675.673486847209, 0),
    (18653.102376328723, 9645.878773993574, 0),
    (18727.78714866784, 9775.105006160606, 0),
    (18731.89476260731, 9804.80535396914, 0),
    (18735.440168583955, 9834.57761602829, 0),
    (18759.70265574685, 9816.952341821509, 0),
    (18011.577222397318, 9791.540749268785, 0),
    (18007.906395156988, 9822.314291804376, 0),
    (17968.06355473139, 9750.390354990495, 0),
    (17879.159037116024, 9677.16292596861, 0),
    (18164.732899948056, 9781.238571066737, 0),
    (18193.969764434303, 9774.307278776661, 0),
    (18214.849417761165, 9795.848868247964, 0),
    (18268.556084881646, 9746.626360617433, 0),
    (18294.15926000091, 9762.248447546317, 0),
    (18112.82389907037, 9553.887587933254, 0),
    (18222.076152301277, 9708.668298442906, 0),
    (18163.293985066943, 9632.748920277862, 0),
    (18420.028464016414, 9724.539145563116, 0),
    (18439.9314685055, 9746.986203550909, 0),
    (18137.473355532475, 9436.12015969478, 0),
    (18480.919423339506, 9694.045247591255, 0),
    (18510.842843262028, 9690.134619252167, 0),
    (18531.389450204922, 9712.040155580116, 0),
    (18233.70329546461, 9346.96166902428, 0),
    (18560.997100972134, 9777.513626207086, 0),
    (18290.2185188657, 9462.01397080147, 0),
    (18287.73508710171, 9427.450191682314, 0),
    (18735.237532471117, 9864.56202768595, 0),
    (18762.141814463776, 9848.299427077862, 0),
    (18761.999782316852, 9878.299089374379, 0),
    (17984.05320923678, 9804.224031376865, 0),
    (18048.631835558783, 9864.560877759053, 0),
    (17990.81512616826, 9769.944536056266, 0),
    (18072.450060093117, 9846.32502735766, 0),
    (18185.569319009475, 9803.31133995056, 0),
    (18235.54558171987, 9817.694141308539, 0),
    (18257.14548471767, 9838.502768310103, 0),
    (18240.820296436654, 9758.07264063831, 0),
    (18266.342665298795, 9806.701992295817, 0),
    (18292.621714611585, 9792.184468808808, 0),
    (18333.601418255777, 9817.179668040608, 0),
    (18014.373952524333, 9460.722021416235, 0),
    (18424.12577796313, 9775.28090729292, 0),
    (18454.103914479496, 9774.13577367364, 0),
    (18433.133245147717, 9650.191094830254, 0),
    (18499.383093970286, 9717.859592581626, 0),
    (18519.847040862373, 9739.796476535323, 0),
    (18532.980291223597, 9766.786998211252, 0),
    (18550.59259424949, 9742.501083186811, 0),
    (18539.91421827563, 9800.731875645919, 0),
    (18569.516412391207, 9806.27855855439, 0),
    (18320.04448449152, 9502.622039601396, 0),
    (18736.175169916954, 9894.539191147283, 0),
    (18763.198885448037, 9908.27511565674, 0),
    (18763.90542892386, 9938.863357857419, 0),
    (18032.561818690487, 9839.307722207584, 0),
    (18062.908686040893, 9890.908356394675, 0),
    (18088.939085762897, 9905.768377460314, 0),
    (18087.575689115452, 9872.95766272404, 0),
    (18206.356681878642, 9824.942002098209, 0),
    (18228.150809445753, 9846.951070512112, 0),
    (18260.94240391907, 9868.252958956322, 0),
    (18267.0295398328, 9776.580905710576, 0),
    (18302.674552923596, 9820.419032878062, 0),
    (18320.092671740396, 9844.81897693403, 0),
    (18350.09422074176, 9845.243742162062, 0),
    (17928.472441911676, 9370.174274944442, 0),
    (18441.070767350076, 9803.785308919296, 0),
    (18447.752182697743, 9835.044545776125, 0),
    (18167.310924871912, 9433.002555500163, 0),
    (18230.520328695187, 9499.31850677568, 0),
    (18258.83962090163, 9509.212230540059, 0),
    (18538.916007958673, 9839.66182262893, 0),
    (18548.576329126976, 9873.52613972726, 0),
    (18568.752409004133, 9836.533057272674, 0),
    (18561.82070187608, 9900.444285846243, 0),
    (18313.46306569895, 9442.879745055636, 0),
    (18737.56413170828, 9924.505918635865, 0),
    (18740.257973696338, 9957.33572821004, 0),
    (18752.011815666232, 9984.937269989234, 0),
    (18022.41239516706, 9922.450128606446, 0),
    (18043.70123625988, 9943.587423641906, 0),
    (18107.68688642872, 9929.17394499737, 0),
    (18132.69313013708, 9912.55968397078, 0),
    (18113.92126083882, 9889.15846769792, 0),
    (18155.69666195701, 9932.254548355037, 0),
    (18035.623625501023, 9809.464375561223, 0),
    (18277.192615773463, 9893.462944455585, 0),
    (18307.03480211123, 9896.43901435431, 0),
    (18326.960289366325, 9874.014302705866, 0),
    (18356.67289191183, 9878.151921716008, 0),
    (18088.015399716525, 9537.019323060713, 0),
    (18365.796085039274, 9906.730949675504, 0),
    (18322.60034152156, 9789.269520948772, 0),
    (18444.518050179948, 9867.877584356713, 0),
    (18457.117315835345, 9895.103608739691, 0),
    (18451.867752629067, 9948.731787362332, 0),
    (18363.620636464148, 9572.592097842276, 0),
    (18536.42253028025, 9916.705469627443, 0),
    (18535.97983135146, 9951.382054461312, 0),
    (18560.823736637958, 9934.303711648901, 0),
    (18563.056238767425, 10003.413808008696, 0),
    (18561.59289004258, 9967.251924890637, 0),
    (18555.930868602234, 10044.923539932386, 0),
    (18749.469242398376, 10014.82931156706, 0),
    (18064.782900701306, 9964.931355393692, 0),
    (18086.0917567907, 9986.048472909142, 0),
    (18130.543508279505, 9948.60443704199, 0),
    (18157.52110839073, 9962.202040147582, 0),
    (18181.204328871343, 9980.616845145078, 0),
    (18202.114329067022, 10002.128978740253, 0),
    (17801.42845636553, 9601.289488088853, 0),
    (18314.129861162735, 9925.751108197159, 0),
    (18329.76516443187, 9951.364461338591, 0),
    (18335.861959298592, 9904.739848970246, 0),
    (18354.625773238586, 9934.573237146753, 0),
    (18376.19482306275, 9955.424257647443, 0),
    (18391.354581289565, 9981.312126051474, 0),
    (18082.45132416008, 9501.250310161791, 0),
    (18441.360171423836, 9920.632203659414, 0),
    (18448.693280159932, 9978.563322021637, 0),
    (18449.769438310366, 10008.54401386881, 0),
    (18284.633047963227, 9524.532123503715, 0),
    (18510.303500393176, 9786.427852511239, 0),
    (18538.14878889893, 9985.970207973402, 0),
    (18538.434067134516, 10020.554797502582, 0),
    (18548.575444563838, 10074.007273436024, 0),
    (18549.891976075298, 10103.978090958359, 0),
    (18558.276528498758, 10132.782592006948, 0),
    (18749.881510996445, 10044.82647867669, 0),
)
# ==== GOLDEN TABLES (end) ====
