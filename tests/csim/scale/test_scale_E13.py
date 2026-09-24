"""E-13 (docs/bible/epics/E-13-movement-and-command.md), "## Scale
requirements": "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a
miss is escalated): movement and collision for 1,000 units in under 3 ms per
tick, 10,000 in under 30 ms; route queries under 1,000 per second at 60 wu
cells."

Movement + collision has no finer public entry point than the full
om_tactical_step (targeting/damage share the same tick; see E-11's file
header). Route queries are measured as 1,000 om_navmesh_find_path calls
completing within 1 second total (average <1ms/query), matching "1,000 per
second" as a throughput budget.
"""
from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 3_000_000  # 3 ms
BUDGET_LARGE_NS = 30_000_000  # 30 ms
SEED = 2026091413

N_ROUTE_QUERIES = 1000
ROUTE_BUDGET_NS = 1_000_000_000  # 1,000 queries within 1 s


def _build(lib, n, seed):
    # Single faction: this is a movement/collision measurement, not combat --
    # every unit is issued a move order so the tick has real movement work.
    # Spawned on the 24,000 wu canvas grid (sparse -- the 10,000-unit case
    # is ~240 wu apart); no dense variant here, this file's cost is
    # movement/collision, not all-pairs targeting density (see E-11's file
    # header for the dense/sparse split that applies there).
    w = raw_world(lib, 1, seed, features=[])
    ids = spawn_grid(lib, w, n, 0, RAIDER)
    return w, ids


def test_e13_1000_units_movement_and_collision_per_tick(lib):
    import ctypes
    w, ids = _build(lib, N_SMALL, SEED)
    selection = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, selection, len(ids), 12000.0, 12000.0)
    med = median_ns(lambda: lib.om_tactical_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_SMALL_NS, f"E-13 {N_SMALL} units, om_tactical_step (movement+collision)")


def test_e13_10000_units_movement_and_collision_per_tick(lib):
    import ctypes
    w, ids = _build(lib, N_LARGE, SEED)
    selection = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, selection, len(ids), 12000.0, 12000.0)
    med = median_ns(lambda: lib.om_tactical_step(w))
    lib.om_world_free(w)
    assert_budget(med, BUDGET_LARGE_NS, f"E-13 {N_LARGE} units, om_tactical_step (movement+collision)")
    assert_control_violates_budget(med, BUDGET_LARGE_NS, f"E-13 control, {N_LARGE} units (budget/100)")


def test_e13_1000_route_queries_per_second(lib):
    w = raw_world(lib, 1, SEED, features=[])

    def _batch():
        for i in range(N_ROUTE_QUERIES):
            x1 = (i * 37.0) % 24000.0
            y1 = (i * 53.0) % 24000.0
            x2 = 24000.0 - x1
            y2 = 24000.0 - y1
            lib.om_navmesh_find_path(w, x1, y1, x2, y2, 0)

    med = median_ns(_batch, n=20, warmup=2)
    lib.om_world_free(w)
    assert_budget(med, ROUTE_BUDGET_NS, f"E-13 {N_ROUTE_QUERIES} om_navmesh_find_path queries/second")
