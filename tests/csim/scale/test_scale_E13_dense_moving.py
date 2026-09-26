"""E-13 (docs/bible/epics/E-13-movement-and-command.md), "## Scale
requirements": "movement and collision for 1,000 units in under 3 ms per
tick, 10,000 in under 30 ms ... measured at the 10 ticks/s rate the sim
drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the
1,000-unit figure at 20 ticks/s."

S-097, S-102, R-099-03: the 30 ms budget is checked under density AND motion
together in the five-engagement scene below.

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

scene per Westley 2026-09-25: ten groups, five engagements. Five engagements
(2000v2000, 1200v1200, 800v800, 500v500, 500v500) placed at 4 corners and
centre of a 24,000 wu canvas, 600 wu gap between near edges, 30 wu spawn
spacing. Variant B (control-group blocks ≤ OM_MAGIC_BOX_SPREAD_RADIUS=450 wu)
is the budgeted case. Variant A (one group_move per group) and the old
single-point pile are stress rows: measured, reported, never asserting on
time.
"""
import ctypes
import math

import pytest

from ._scale_helpers import (
    assert_budget,
    assert_control_violates_budget,
    median_ns,
    raw_world,
    spawn_grid,
)

RAIDER = 0
N_SMALL = 1000
N_LARGE = 10000
BUDGET_SMALL_NS = 3_000_000   # 3 ms
BUDGET_LARGE_NS = 30_000_000  # 30 ms
SEED = 2026091413
DENSE_BOX = 1500.0

# Five-engagement scene (Westley 2026-09-25)
# OM_MAGIC_BOX_SPREAD_RADIUS = 450  csrc/om_constants.h
# OM_UNIT_COLLISION_RADIUS   = 15   csrc/om_constants.h
MAGIC_BOX_SPREAD_RADIUS = 450.0
SPAWN_SPACING = 30.0
FORMATION_GAP = 600.0  # wu between near edges of opposing groups

# Engagements: (n_per_side, n_per_side, engagement_centre_x, engagement_centre_y)
# Ten groups total, 10,000 units. All engagement centres > 10,607 wu apart
# (minimum pair: E3-E5 and E4-E5, sqrt(7500^2+7500^2) = 10,607 wu),
# well above the 3,000 wu target. Map canvas 24,000 wu; no group exceeds
# x=20,850 or y=19,920.
ENGAGEMENTS = [
    (2000, 4500.0,  4000.0),   # NW: 2000 v 2000
    (1200, 19500.0, 4000.0),   # NE: 1200 v 1200
    (800,  4500.0,  19500.0),  # SW:  800 v  800
    (500,  19500.0, 19500.0),  # SE:  500 v  500
    (500,  12000.0, 12000.0),  # C :  500 v  500
]


def _engagement_offsets(n, cx, cy):
    """Spawn offsets and move destinations for an n-vs-n engagement at (cx, cy).

    Returns (off_ax, off_ay, off_bx, off_by, dest_cx_a, dest_cx_b, dest_cy, cols).
    Group A (faction 0) spawns left of the 600 wu gap; Group B (faction 1)
    spawns right. Each group's destination is the other group's centre.
    """
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)
    gw = cols * SPAWN_SPACING
    gh = rows * SPAWN_SPACING
    off_ax = cx - gw - FORMATION_GAP / 2
    off_bx = cx + FORMATION_GAP / 2
    off_ay = cy - gh / 2
    off_by = cy - gh / 2
    dest_cx_a = off_bx + gw / 2   # A moves toward B's centre
    dest_cx_b = off_ax + gw / 2   # B moves toward A's centre
    return off_ax, off_ay, off_bx, off_by, dest_cx_a, dest_cx_b, cy, cols


def _spawn_group(lib, w, n, faction_id, off_x, off_y):
    """Spawn n units in a sqrt(n)×sqrt(n) grid at (off_x, off_y), SPAWN_SPACING apart."""
    cols = max(1, math.ceil(math.sqrt(n)))
    ids = []
    for i in range(n):
        gx, gy = i % cols, i // cols
        x = off_x + SPAWN_SPACING * 0.5 + gx * SPAWN_SPACING
        y = off_y + SPAWN_SPACING * 0.5 + gy * SPAWN_SPACING
        ids.append(lib.om_unit_spawn(w, RAIDER, faction_id, x, y, 0))
    return ids


def _order_variant_a(lib, w, ids, dest_cx, dest_cy):
    """Variant A: single group_move for the whole group."""
    sel = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, sel, len(ids), dest_cx, dest_cy)


def _order_variant_b(lib, w, ids, n, off_x, dest_cx, dest_cy):
    """Variant B: split group into column-blocks ≤ MAGIC_BOX_SPREAD_RADIUS wide;
    each block's destination is offset from dest_cx by the block's lateral
    displacement from the group centre, preserving formation layout."""
    cols = max(1, math.ceil(math.sqrt(n)))
    max_blk_cols = max(1, int(MAGIC_BOX_SPREAD_RADIUS / SPAWN_SPACING))  # = 15
    group_cx = off_x + cols * SPAWN_SPACING / 2
    col = 0
    while col < cols:
        blk_end = min(col + max_blk_cols, cols)
        blk_ids = [ids[i] for i in range(n) if col <= (i % cols) < blk_end]
        if blk_ids:
            # block centre x = off_x + sp * (col + blk_end) / 2
            blk_cx = off_x + SPAWN_SPACING * (col + blk_end) / 2
            delta_x = blk_cx - group_cx
            blk = (ctypes.c_uint32 * len(blk_ids))(*blk_ids)
            lib.om_command_group_move(w, blk, len(blk_ids),
                                      dest_cx + delta_x, dest_cy)
        col = blk_end


def _build_five_engagements(lib, seed):
    """Build world with five engagements; return (w, all_ids, per_group_meta).

    per_group_meta entries: (ids, n, off_x, dest_cx, dest_cy) for each of the
    ten groups, in order faction-0-E1, faction-1-E1, faction-0-E2, ...
    """
    w = raw_world(lib, 1, seed, features=[])
    all_ids = []
    meta = []
    for n, cx, cy in ENGAGEMENTS:
        off_ax, off_ay, off_bx, off_by, dest_cx_a, dest_cx_b, dest_cy, _ = \
            _engagement_offsets(n, cx, cy)
        ids_a = _spawn_group(lib, w, n, 0, off_ax, off_ay)
        ids_b = _spawn_group(lib, w, n, 1, off_bx, off_by)
        meta.append((ids_a, n, off_ax, dest_cx_a, dest_cy))
        meta.append((ids_b, n, off_bx, dest_cx_b, dest_cy))
        all_ids.extend(ids_a)
        all_ids.extend(ids_b)
    return w, all_ids, meta


def _moved_count(lib, w, ids, med_op):
    """(median_ns, moved_count): run med_op() and count units that changed position."""
    starts = [lib.om_unit_get_pos(w, uid) for uid in ids]
    med = med_op()
    ends = [lib.om_unit_get_pos(w, uid) for uid in ids]
    moved = sum(1 for (x0, y0), (x1, y1) in zip(starts, ends) if x0 != x1 or y0 != y1)
    return med, moved


def _build_dense_moving(lib, n, seed, box):
    """Original pile builder: n units in a box, all ordered to (box, box)."""
    w = raw_world(lib, 1, seed, features=[])
    half = n // 2
    ids = spawn_grid(lib, w, half, 0, RAIDER, canvas=box)
    ids += spawn_grid(lib, w, n - half, 1, RAIDER, canvas=box)
    selection = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, selection, len(ids), box, box)
    return w, ids


# ---------------------------------------------------------------------------
# Budgeted test: variant B, five engagements
# ---------------------------------------------------------------------------

def test_e13_10000_five_engagements_variant_b_budgeted_per_tick(lib):
    """R-099-03 budget (30 ms raw / 22.2 ms scaled) under density + motion.
    Variant B: ten groups ordered in control-group blocks ≤ 450 wu wide,
    formation preserved. Five engagements, 10,000 units total.
    scene per Westley 2026-09-25."""
    w, all_ids, meta = _build_five_engagements(lib, SEED)
    for ids, n, off_x, dest_cx, dest_cy in meta:
        _order_variant_b(lib, w, ids, n, off_x, dest_cx, dest_cy)

    med, moved = _moved_count(lib, w, all_ids,
                               lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    assert moved >= 0.9 * len(all_ids), (
        f"only {moved}/{len(all_ids)} units moved in variant B "
        "(scene is stationary; scene is wrong, not the threshold)"
    )
    assert_budget(
        med, BUDGET_LARGE_NS,
        f"E-13 {N_LARGE} units five-engagements variant-B, om_tactical_step"
    )
    assert_control_violates_budget(
        med, BUDGET_LARGE_NS,
        f"E-13 control, {N_LARGE} units five-engagements variant-B (budget/100)"
    )


# ---------------------------------------------------------------------------
# Stress rows: reported, never asserting on time
# ---------------------------------------------------------------------------

@pytest.mark.stress
def test_e13_10000_five_engagements_variant_a_stress_per_tick(lib):
    """Variant A stress row: each of the ten groups gets one group_move order
    to the opposing group's centre. No budget assertion; median reported only.
    Moved-fraction is printed but not asserted (scene validity is proven by
    variant B's assertion above)."""
    w, all_ids, meta = _build_five_engagements(lib, SEED)
    for ids, n, off_x, dest_cx, dest_cy in meta:
        _order_variant_a(lib, w, ids, dest_cx, dest_cy)

    med, moved = _moved_count(lib, w, all_ids,
                               lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    frac = moved / len(all_ids)
    print(
        f"[scale-stress] E-13 {N_LARGE} units five-engagements variant-A: "
        f"raw_median={med / 1e6:.3f} ms  moved_fraction={frac:.3f}"
    )
    # No assert_budget -- this is a stress row.


@pytest.mark.stress
def test_e13_10000_dense_pile_stress_per_tick(lib):
    """Original single-point pile: 10,000 units in a 1,500 wu box, all ordered
    to (1500, 1500). Pathological case kept visible. No budget assertion.
    (Renamed from test_e13_10000_units_dense_moving_movement_and_collision_per_tick.)"""
    w, ids = _build_dense_moving(lib, N_LARGE, SEED, DENSE_BOX)
    med, moved = _moved_count(lib, w, ids,
                               lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    frac = moved / len(ids)
    print(
        f"[scale-stress] E-13 {N_LARGE} units dense pile (1500 wu box): "
        f"raw_median={med / 1e6:.3f} ms  moved_fraction={frac:.3f}"
    )
    # No assert_budget -- this is a stress row.


# ---------------------------------------------------------------------------
# 1,000-unit positive control: unchanged
# ---------------------------------------------------------------------------

def test_e13_1000_units_dense_moving_movement_and_collision_per_tick(lib):
    """Positive control: the same dense+moving scene at 1,000 units, R-099-03's
    20 ticks/s budget -- must pass comfortably, proving the clock and the
    moved-fraction check are live and not the reason the 10,000-unit case
    above fails."""
    w, ids = _build_dense_moving(lib, N_SMALL, SEED, DENSE_BOX)
    med, moved = _moved_count(lib, w, ids,
                               lambda: median_ns(lambda: lib.om_tactical_step(w)))
    lib.om_world_free(w)

    assert moved >= 0.9 * len(ids), (
        f"only {moved}/{len(ids)} units moved -- group move order did not take"
    )
    assert_budget(med, BUDGET_SMALL_NS, f"E-13 {N_SMALL} units dense+moving (1500 wu box), om_tactical_step")
