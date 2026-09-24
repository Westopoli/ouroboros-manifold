"""E-13 (docs/bible/epics/E-13-movement-and-command.md), "## Scale
requirements": "movement and collision for 1,000 units in under 3 ms per
tick, 10,000 in under 30 ms ... measured at the 10 ticks/s rate the sim
drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the
1,000-unit figure at 20 ticks/s."

E-13's own test_scale_E13.py measures the 10,000-unit case sparse (24,000 wu
canvas grid, ~240 wu apart, per that file's header) and idle after the
initial group move settles into its per-tick steady state. E-11's dense case
(test_e11_10000_units_dense_targeting_and_damage_per_tick) showed all-pairs
cost grows with local density, not just unit count, packing the same 10,000
units into a 1,500 wu box (~10-15 wu apart). This file combines both: the
E-11 dense box layout, both factions, and E-13's own moving scene (every
unit under a real group move order, so movement+collision has actual work
every tick, not just idle steady-state) -- R-099-03's 30 ms budget checked
under density AND motion together, which neither existing file does alone.
"""
import ctypes

from ._scale_helpers import assert_budget, assert_control_violates_budget, median_ns, raw_world, spawn_grid

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 3_000_000  # 3 ms
BUDGET_LARGE_NS = 30_000_000  # 30 ms
SEED = 2026091413
DENSE_BOX = 1500.0


def _build_dense_moving(lib, n, seed, box):
    w = raw_world(lib, 1, seed, features=[])
    half = n // 2
    ids = spawn_grid(lib, w, half, 0, RAIDER, canvas=box)
    ids += spawn_grid(lib, w, n - half, 1, RAIDER, canvas=box)
    selection = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, selection, len(ids), box, box)
    return w, ids


def _moved_fraction(lib, w, ids, med_op):
    starts = [lib.om_unit_get_pos(w, uid) for uid in ids]
    med = med_op()
    ends = [lib.om_unit_get_pos(w, uid) for uid in ids]
    moved = sum(1 for (x0, y0), (x1, y1) in zip(starts, ends) if x0 != x1 or y0 != y1)
    return med, moved


def test_e13_10000_units_dense_moving_movement_and_collision_per_tick(lib):
    """Expected red today: measured ~55 ms on branch push/B12-9 (sim lane,
    2026-09-24), well over the 30 ms budget even scaled by
    OM_SCALE_CPU_FACTOR -- this is the spec for that piece's dense-moving
    path, not a proposed number. Moved-fraction assertion below guards
    against a stationary scene passing on a stale/settled group move."""
    w, ids = _build_dense_moving(lib, N_LARGE, SEED, DENSE_BOX)
    med, moved = _moved_fraction(lib, w, ids, lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    assert moved >= 0.9 * len(ids), (
        f"only {moved}/{len(ids)} units moved -- group move order did not take, "
        "budget would be measured against a stationary scene"
    )
    assert_budget(med, BUDGET_LARGE_NS, f"E-13 {N_LARGE} units dense+moving (1500 wu box), om_tactical_step")
    assert_control_violates_budget(med, BUDGET_LARGE_NS, f"E-13 control, {N_LARGE} units dense+moving (budget/100)")


def test_e13_1000_units_dense_moving_movement_and_collision_per_tick(lib):
    """Positive control: the same dense+moving scene at 1,000 units, R-099-03's
    20 ticks/s budget -- must pass comfortably, proving the clock and the
    moved-fraction check are live and not the reason the 10,000-unit case
    above fails."""
    w, ids = _build_dense_moving(lib, N_SMALL, SEED, DENSE_BOX)
    med, moved = _moved_fraction(lib, w, ids, lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    assert moved >= 0.9 * len(ids), (
        f"only {moved}/{len(ids)} units moved -- group move order did not take"
    )
    assert_budget(med, BUDGET_SMALL_NS, f"E-13 {N_SMALL} units dense+moving (1500 wu box), om_tactical_step")
