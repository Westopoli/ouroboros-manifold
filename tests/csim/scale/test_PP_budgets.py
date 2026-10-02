# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase A::verification 4 (Scale, every wave)
# spec: docs/bible/epics/E-13-movement-and-command.md::Scale requirements (S-097, S-102, R-099-03)
# spec: docs/bible/epics/E-11-units-and-combat.md::Scale requirements
"""Budget guard for every wave of the movement, layers and search plan.

The plan's numbers, never loosened (Westley, E-11 and E-13 Scale requirements, 2026-09-14;
Phase A verification item 4):
  movement and collision   3 ms per tick at 1,000 units, 30 ms at 10,000
  targeting and damage     2 ms per tick at 1,000 units, 25 ms at 10,000
  route queries            1,000 per second
The 10,000 figures are the ones checked at the 10 ticks per second the sim runs above 1,000
live units (R-099-03).

Timing method is the existing scale suite's (_scale_helpers.median_ns / assert_budget: median
of om_tactical_step calls, measured raw against budget / OM_SCALE_CPU_FACTOR; positive control
that the clock is live). om_tactical_step has no finer public entry point, so movement and
targeting are separated by scene, as in test_scale_E13.py and test_scale_E11.py: the movement
scene has one faction (nothing to target), the targeting scene has two factions already in
range of each other (every unit has a target from tick 1).

What differs from those files: the scenes carry the work the plan adds, so the budget is
checked against the new behaviour as it lands.
  - movement: attack-move in blocks of at most 450 wu (control-group blocks, variant B of
    test_scale_E13_dense_moving.py) that march into obstacle discs sitting just ahead of
    each block, so the steering sweep and the group slots have real work every tick;
  - targeting: five engagements at the E-13 layout (2000, 1200, 800, 500, 500 per side),
    gap 100 wu, inside every unit's range, so targeting, hits and return fire run for every
    unit at once; measured over the first ticks, before deaths thin the field (Vanguards:
    500 hp, about 6 damage per second each, so none die in the window);
  - routes: queries across a wall of density cells that force the router off the straight
    line (the open-map query of test_scale_E13.py is answered by a line-of-sight test and
    never reaches the search). Long detours are not budgeted here: the search gives up after
    512 cells (see test_PP_tables.py, test_PP_route_search_reaches_across_the_canvas).
Numbers measured on today's code are printed by assert_budget (run with -s); a miss is a
finding for Westley, never a reason to edit a number here.
"""
import ctypes
import math

from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world

VANGUARD = 2
N_SMALL = 1000
N_LARGE = 10000
MOVE_SMALL_NS = 3_000_000
MOVE_LARGE_NS = 30_000_000
TARGET_SMALL_NS = 2_000_000
TARGET_LARGE_NS = 25_000_000
ROUTE_COUNT = 1000
ROUTE_BUDGET_NS = 1_000_000_000      # 1,000 queries inside one second
SEED = 2026100201
SPACING = 30.0
BLOCK_COLS = 15                      # 15 * 30 wu = 450 wu = OM_MAGIC_BOX_SPREAD_RADIUS
TICKS = 40


def _block(lib, w, faction, n, cols, x0, y0):
    ids = []
    for i in range(n):
        ids.append(lib.om_unit_spawn(w, VANGUARD, faction, x0 + (i % cols) * SPACING,
                                     y0 + (i // cols) * SPACING, 0))
    return ids


def _order(lib, fn, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    fn(w, arr, len(ids), x, y)


def _moved(lib, w, ids, op):
    start = [lib.om_unit_get_pos(w, u) for u in ids]
    med = op()
    end = [lib.om_unit_get_pos(w, u) for u in ids]
    return med, sum(1 for a, b in zip(start, end) if a != b)


# ------------------------------------------------------------------ movement scene

def _movement_scene(lib, n):
    """n units of one faction in blocks of at most 15 x 15, on a lattice 3,000 wu apart, each
    block attack-moving 2,000 wu along +x; four obstacle discs (radius 100) sit 150 to 300 wu
    ahead of every block. At 10,000 units: 45 blocks, 180 discs (the table holds 256)."""
    w = raw_world(lib, 1, SEED, features=[])
    per_block = BLOCK_COLS * BLOCK_COLS
    blocks = math.ceil(n / per_block)
    lattice = math.ceil(math.sqrt(blocks))
    ids_all, left = [], n
    for b in range(blocks):
        bx = 1500.0 + (b % lattice) * 3000.0
        by = 1500.0 + (b // lattice) * 3000.0
        count = min(per_block, left)
        left -= count
        ids = _block(lib, w, 0, count, BLOCK_COLS, bx, by)
        ids_all.extend(ids)
        for k in range(4):
            lib.om_map_add_obstacle(w, bx + 450.0 + 150.0 + 50.0 * k, by + 100.0 + 110.0 * k, 100.0)
        _order(lib, lib.om_command_attack_move, w, ids, bx + 2000.0, by + 100.0)
    return w, ids_all


def _run_movement(lib, n, budget_ns, control):
    w, ids = _movement_scene(lib, n)
    med, moved = _moved(lib, w, ids, lambda: median_ns(lambda: lib.om_tactical_step(w), n=TICKS, warmup=2))
    lib.om_world_free(w)
    assert moved >= 0.9 * len(ids), f"only {moved}/{len(ids)} units moved: the scene is stationary, not the budget"
    assert_budget(med, budget_ns, f"PP movement+collision {n} units (attack-move blocks into obstacles)")
    if control:
        assert_control_violates_budget(med, budget_ns, f"PP movement control {n} units (budget/100)")


# ------------------------------------------------------------------ targeting scene

ENGAGEMENTS = [(2000, 4500.0, 4000.0), (1200, 19500.0, 4000.0), (800, 4500.0, 19500.0),
               (500, 19500.0, 19500.0), (500, 12000.0, 12000.0)]
GAP = 100.0


def _targeting_scene(lib, n):
    """Engagements of n/10 per side at the E-13 layout, scaled to total n, blocks 100 wu apart
    (inside Vanguard range 300): every unit has a hostile to target from the first tick."""
    w = raw_world(lib, 1, SEED, features=[])
    scale = n / N_LARGE
    ids_all = []
    for per_side, cx, cy in ENGAGEMENTS:
        count = max(1, round(per_side * scale))
        cols = max(1, math.ceil(math.sqrt(count)))
        rows = math.ceil(count / cols)
        gw, gh = cols * SPACING, rows * SPACING
        ids_all += _block(lib, w, 0, count, cols, cx - gw - GAP / 2, cy - gh / 2)
        ids_all += _block(lib, w, 1, count, cols, cx + GAP / 2, cy - gh / 2)
    return w, ids_all


def _hp_total(lib, w, ids):
    return sum(lib.om_unit_get_hp(w, u) for u in ids)


def _run_targeting(lib, n, budget_ns, control):
    w, ids = _targeting_scene(lib, n)
    before = _hp_total(lib, w, ids)
    med = median_ns(lambda: lib.om_tactical_step(w), n=TICKS, warmup=2)
    after = _hp_total(lib, w, ids)
    alive = sum(1 for u in ids if lib.om_unit_alive(w, u))
    lib.om_world_free(w)
    assert after < before, "no damage dealt: the scene never engaged, not the budget"
    assert alive == len(ids), f"{len(ids) - alive} units died inside the window: the load is not steady"
    assert_budget(med, budget_ns, f"PP targeting+damage {len(ids)} units (five engagements in range)")
    if control:
        assert_control_violates_budget(med, budget_ns, f"PP targeting control {len(ids)} units (budget/100)")


# ------------------------------------------------------------------ route scene

def _route_scene(lib):
    """One wall of blocked density cells (100 wu cells) at cell column 100 across the whole 24,000 wu
    canvas, with a 3-cell gap at rows 106..108: 237 cells (the density table holds 1,024)."""
    w = raw_world(lib, 1, SEED, features=[])
    for cy in range(0, 240):
        if 106 <= cy <= 108:
            continue
        lib.om_map_set_obstacle_density(w, 100, cy, 0, 1.0)
    return w


def _route_queries(lib, w):
    """1,000 queries from the west side of the wall to the east side, 6 columns apart, at rows 100..103;
    the straight line is blocked, the way round is 9 to 19 cells."""
    lens = []
    for i in range(ROUTE_COUNT):
        x1 = 100.0 * (97 + i % 3) + 50.0
        y1 = 100.0 * (100 + i % 4) + 50.0
        x2 = 100.0 * (102 + i % 3) + 50.0
        y2 = 100.0 * (100 + (i + 1) % 4) + 50.0
        lens.append(lib.om_navmesh_find_path(w, x1, y1, x2, y2, 0))
    return lens


def test_PP_route_queries_1000_per_second_through_a_wall(lib):
    """E-13 scale: route queries under 1,000 per second, with the search really running and finding
    its way round (every answer longer than the 2 of a straight line)."""
    w = _route_scene(lib)
    lens = _route_queries(lib, w)
    med = median_ns(lambda: _route_queries(lib, w), n=10, warmup=1)
    lib.om_world_free(w)
    assert all(n > 2 for n in lens), (
        f"{sum(1 for n in lens if n <= 2)}/{ROUTE_COUNT} queries found no way round: not a budget miss")
    assert_budget(med, ROUTE_BUDGET_NS, f"PP {ROUTE_COUNT} route queries round a wall, per second")
    assert_control_violates_budget(med, ROUTE_BUDGET_NS, f"PP route control, {ROUTE_COUNT} queries (budget/100)")


def test_PP_route_queries_control_open_map_is_not_searched(lib):
    """Positive control for the scene check: the same queries on an open map are all answered by
    line of sight (length 2), so `searched` above counts real searches."""
    w = raw_world(lib, 1, SEED, features=[])
    lens = _route_queries(lib, w)
    lib.om_world_free(w)
    assert all(n == 2 for n in lens)


# ------------------------------------------------------------------ the budget tests

def test_PP_movement_and_collision_1000_units_3ms(lib):
    """E-13 scale: movement and collision, 1,000 units, 3 ms per tick."""
    _run_movement(lib, N_SMALL, MOVE_SMALL_NS, control=False)


def test_PP_movement_and_collision_10000_units_30ms(lib):
    """E-13 scale / R-099-03: movement and collision, 10,000 units, 30 ms per tick."""
    _run_movement(lib, N_LARGE, MOVE_LARGE_NS, control=True)


def test_PP_targeting_and_damage_1000_units_2ms(lib):
    """E-11 scale: targeting and damage, 1,000 units, 2 ms per tick."""
    _run_targeting(lib, N_SMALL, TARGET_SMALL_NS, control=False)


def test_PP_targeting_and_damage_10000_units_25ms(lib):
    """E-11 scale: targeting and damage, 10,000 units, 25 ms per tick."""
    _run_targeting(lib, N_LARGE, TARGET_LARGE_NS, control=True)
