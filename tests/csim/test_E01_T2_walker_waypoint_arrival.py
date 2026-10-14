"""E-01 R-001-07 / R-004-07 (terrain stage 2): a walker takes its next waypoint inside the arrival radius.

Defect diagnosed 2026-10-06 on push/t2-colmask: om_move_walker_step (csrc/tactical_move.c) advances to the next
waypoint only when the unit reaches it exactly (`d == 0.0 || v * left >= d`), while the steering path uses the arrival
radius OM_WAYPOINT_ARRIVE_MULT * OM_UNIT_COLLISION_RADIUS (30 wu). In a 16-walker blob the push-apart leaves front
units 25-29 wu past their waypoint; they step back, are pushed forward again, and the group stalls (about 100 wu in
600 ticks through a one-cell neck of the band-3 mask). Ruling (Architect): walkers use the same arrival radius for
intermediate waypoints; the final leg keeps its exact finish.
Lab twin: tests/skilllab/integration/test_ground_scene_real.py::test_a_walker_ordered_across_the_map_stays_on_masked_cells.

Tests 1 (isolation) and 3 (blob) are red today; 2 (exact finish) and 4 (flyers unchanged) are green and pin the fix.
Numbers marked "provisional (2026-10-06)" are test drafts; Westley may tighten them.
"""
import ctypes
import math
import sys

import test_E13_R207_05_walker_routes as routes
from conftest import REPO_ROOT, OMFeature, OMTacParam

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.skilllab.formations import place  # noqa: E402  the lab's own blob shape

RAIDER = 0
VANGUARD = 2                   # the lab's blob units are Vanguard clones
OM_MOVE_FLYING, OM_MOVE_WALKING = 0, 1
SEED = 11
LAYER = 2                      # band 3
CELL = 100.0
OVERSHOOT = 20.0               # provisional (2026-10-06): inside the 30 wu arrival radius
ADVANCE_TICKS = 10             # provisional (2026-10-06)
FINISH_WU = 1.0                # provisional (2026-10-06)
# Lab scene (tests/skilllab/integration/test_ground_scene_real.py): 12000 wu canvas, HIGH group on band 3.
LAB_CANVAS = 12000.0
HIGH_AT = (8150.0, 6050.0)
BLOB_N = 16
BLOB_RADIUS = 60.0
BLOB_TICKS = 600
BLOB_MIN_MOVE = 300.0          # same bar as the lab twin
FLYER_TICKS = 200
# Recorded 2026-10-06 on push/t2-colmask bd169a90 (flyer blob, 16 Vanguards, lab scene, ordered to (600, 600), 200 ticks).
# Re-recorded 2026-10-09 (TD-VG-E-1): K-e folds the economy words into the factions section; old 14299308082090419322.
# TD-VG-E-17: K-e5 moved the whole word (TD-VG-E-9 value 2109990263532742758) via the economy block; the pin is now the
# (units, movement) sections.
# TD-VG-W-2: old 11290823588580758478, new 12903589747027128004 (movement word only; units word 1545777915625493498 unchanged):
# W2 stored routes add the route block to the movement section.
FLYER_SECTIONS_200 = (1545777915625493498, 12903589747027128004)   # re-recorded 2026-10-13 on the W2 tree (was recorded 2026-10-11 on the K-e5 tree 2747b283)


def _units_movement(lib, w):
    """TD-VG-E-17: the trace is the "units" and "movement" sections (3, 4) of om_world_checksum_full, not the whole word."""
    buf = (ctypes.c_uint64 * 9)()
    lib.om_world_checksum_full(w, buf, 9)
    return (buf[3], buf[4])


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _world(lib, world_factory, kind, canvas):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, canvas, canvas) == 0
    assert lib.om_terrain_generate(w, SEED, canvas, canvas) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, kind) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, kind) == 0
    return w


def _straight_run(lib, w, run=5):
    """(start cell, direction, goal cell): a straight run of `run` walkable cells on layer 2, in the largest component."""
    cw, ch = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    best, seen = set(), set()
    for i, v in enumerate(m):
        if v and i not in seen:
            c = routes._component_cells(m, cw, ch, i)
            seen |= c
            if len(c) > len(best):
                best = c
    for i in sorted(best):
        cx, cy = i % cw, i // cw
        for dx, dy in ((0, 1), (1, 0)):
            cells = [(cx + k * dx, cy + k * dy) for k in range(run)]
            if all(0 <= x < cw and 0 <= y < ch and m[y * cw + x] for x, y in cells):
                return cells
    raise AssertionError("no straight walkable run of %d cells on seed 11 layer 2" % run)


def test_R_001_07_a_walker_past_its_waypoint_inside_the_arrival_radius_advances(lib, world_factory):
    w = _world(lib, world_factory, OM_MOVE_WALKING, routes.CANVAS)
    routes._declare(lib)
    cells = _straight_run(lib, w)
    u = lib.om_unit_spawn(w, RAIDER, 0, *routes._centre(*cells[0]), LAYER)
    assert u
    goal = routes._centre(*cells[-1])
    n, pts, _ = routes._route(lib, w, u, *goal)
    assert n >= 4, "setup: need a route with 3+ waypoints, got %d points" % n
    wp1, wp2 = pts[1], pts[2]
    assert abs(_dist(wp1, wp2) - CELL) < 1.0
    ux, uy = (wp2[0] - wp1[0]) / CELL, (wp2[1] - wp1[1]) / CELL
    lib.om_command_move(w, [u], 1, *goal)
    lib.om_tactical_step(w)
    lib.om_unit_set_pos(w, u, wp1[0] + ux * OVERSHOOT, wp1[1] + uy * OVERSHOOT)    # 20 wu past waypoint 1, towards 2
    prev = _dist(lib.om_unit_get_pos(w, u), wp2)
    assert abs(prev - (CELL - OVERSHOOT)) < 1.0, "setup: displacement did not take (%.1f)" % prev
    for t in range(1, ADVANCE_TICKS + 1):
        lib.om_tactical_step(w)
        d = _dist(lib.om_unit_get_pos(w, u), wp2)
        assert d < prev, "tick %d: distance to waypoint 2 went %.2f -> %.2f; the walker is stepping back to waypoint 1" % (t, prev, d)
        prev = d


def test_R_001_07_the_final_leg_keeps_its_exact_finish(lib, world_factory):
    w = _world(lib, world_factory, OM_MOVE_WALKING, routes.CANVAS)
    routes._declare(lib)
    cells = _straight_run(lib, w)
    u = lib.om_unit_spawn(w, RAIDER, 0, *routes._centre(*cells[0]), LAYER)
    assert u
    goal = routes._centre(*cells[-1])
    lib.om_command_move(w, [u], 1, *goal)
    for _ in range(600):
        lib.om_tactical_step(w)
    d = _dist(lib.om_unit_get_pos(w, u), goal)
    assert d <= FINISH_WU, "walker stopped %.2f wu from the ordered point" % d


def _blob(lib, w):
    ids = []
    for x, y in place("blob", BLOB_N, HIGH_AT[0], HIGH_AT[1], 0.0, {"radius": BLOB_RADIUS}):
        u = lib.om_unit_spawn(w, VANGUARD, 0, x, y, LAYER)
        assert u, "blob spawn refused at (%.1f, %.1f)" % (x, y)
        ids.append(u)
    return ids


def _lab_world(lib, world_factory, kind):
    w = _world(lib, world_factory, kind, LAB_CANVAS)
    assert lib.om_tactical_set_param(w, OMTacParam.PURSUE_BY_STEERING, 1.0) == 0    # the lab's BASE_SETTINGS
    lib.om_tactical_disable_abilities(w)
    lib.om_set_era_kind(w, 1)
    return w


def _centroid(lib, w, ids):
    ps = [lib.om_unit_get_pos(w, u) for u in ids]
    return sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)


def test_R_001_07_a_16_walker_blob_ordered_across_the_map_does_not_stall(lib, world_factory):
    w = _lab_world(lib, world_factory, OM_MOVE_WALKING)
    ids = _blob(lib, w)
    c0 = _centroid(lib, w, ids)
    lib.om_command_move(w, ids, len(ids), 600.0, 600.0)
    for _ in range(BLOB_TICKS):
        lib.om_tactical_step(w)
    moved = _dist(c0, _centroid(lib, w, ids))
    assert moved > BLOB_MIN_MOVE, "blob centroid moved only %.0f wu in %d ticks" % (moved, BLOB_TICKS)


def test_R_001_07_flyer_blob_trace_is_unchanged_by_the_waypoint_fix(lib, world_factory):
    """Guard: flyers take no part in waypoint arrival. Positive control: the flyers do move."""
    w = _lab_world(lib, world_factory, OM_MOVE_FLYING)
    ids = _blob(lib, w)
    c0 = _centroid(lib, w, ids)
    lib.om_command_move(w, ids, len(ids), 600.0, 600.0)
    for _ in range(FLYER_TICKS):
        lib.om_tactical_step(w)
    assert _dist(c0, _centroid(lib, w, ids)) > 50.0, "flyers did not move"
    cs = _units_movement(lib, w)
    print("FLYER_SECTIONS_200", cs)
    assert cs == FLYER_SECTIONS_200
