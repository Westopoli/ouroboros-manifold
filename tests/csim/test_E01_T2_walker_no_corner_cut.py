"""E-01 R-001-07 / R-004-07 (terrain stage 2): a walker route never cuts a corner.

Defect diagnosed 2026-10-06 on push/t2-wp 67957c10: om_walk_route (csrc/walk_route.c) allows a diagonal step between two
walkable cells while one or both orthogonal neighbours are blocked, so the straight line between the cell centres runs
through a blocked cell's corner and a unit samples off the walk mask (lab: unit 15 at (8195, 5597), layer 2, tick 100).
Ruling (Architect, 2026-10-06): no corner cutting; a diagonal step is allowed only when both orthogonal neighbours are
walkable on that band.
Lab twin: tests/skilllab/integration/test_ground_scene_real.py::test_a_walker_ordered_across_the_map_stays_on_masked_cells.

Tests 1-3 are red today; 4 (flyers unchanged) is green and pins the trace.
Numbers marked "provisional (2026-10-06)" are test drafts; Westley may tighten them.
"""
import math
from collections import deque

import pytest

import test_E01_T2_walker_waypoint_arrival as wp
import test_E13_R207_05_walker_routes as routes

LAYER = wp.LAYER
CELL = routes.CELL
FOLLOW_TICKS = 300             # provisional (2026-10-06)
BLOB_TICKS = 600
BLOB_MIN_MOVE = 300.0          # same bar as the lab twin
FLYER_TICKS = 200
FLYER_SECTIONS_200 = wp.FLYER_SECTIONS_200   # same scene as the waypoint test (TD-VG-E-17: units and movement sections)
MAX_DETOUR_CELLS = 20          # provisional (2026-10-06): the follow-the-route pair must be reachable within this


def _walk(m, cw, x, y):
    return 0 <= x < cw and 0 <= y < len(m) // cw and m[y * cw + x] != 0


def _legal_neighbours(m, cw, x, y):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if (dx or dy) and _walk(m, cw, x + dx, y + dy):
                if dx and dy and not (_walk(m, cw, x + dx, y) and _walk(m, cw, x, y + dy)):
                    continue                       # corner cut: not legal
                yield x + dx, y + dy


def _bfs_len(m, cw, a, b):
    seen, q = {a: 0}, deque([a])
    while q:
        c = q.popleft()
        if c == b:
            return seen[c]
        if seen[c] >= MAX_DETOUR_CELLS:
            continue
        for n in _legal_neighbours(m, cw, *c):
            if n not in seen:
                seen[n] = seen[c] + 1
                q.append(n)
    return None


def _diagonal_pairs(m, cw, ch):
    """Yields (a, b, blocked_orthogonals) for walkable diagonal neighbours, in cell-index order."""
    for y in range(ch - 1):
        for x in range(cw - 1):
            for dx, dy in ((1, 1), (1, -1)):
                nx, ny = x + dx, y + dy
                if not (_walk(m, cw, x, y) and _walk(m, cw, nx, ny)):
                    continue
                blocked = (0 if _walk(m, cw, nx, y) else 1) + (0 if _walk(m, cw, x, ny) else 1)
                yield (x, y), (nx, ny), blocked


def _cut_pair(lib, w, need_detour):
    cw, ch = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    for a, b, blocked in _diagonal_pairs(m, cw, ch):
        if blocked == 0:
            continue
        if need_detour and _bfs_len(m, cw, a, b) is None:
            continue
        return a, b, blocked
    raise AssertionError("no corner-cut diagonal pair on seed 11 layer 2")


def _open_pair(lib, w):
    cw, ch = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    for a, b, blocked in _diagonal_pairs(m, cw, ch):
        if blocked == 0:
            return a, b
    raise AssertionError("no open diagonal pair on seed 11 layer 2")


def _on_mask(m, cw, pos):
    x, y = int(pos[0] // CELL), int(pos[1] // CELL)
    return _walk(m, cw, x, y)


def _legal_route(m, cw, pts):
    cells = [(int(x // CELL), int(y // CELL)) for x, y in pts]
    bad = []
    for (a, b), (c, d) in zip(cells, cells[1:]):
        if a != c and b != d and not (_walk(m, cw, c, b) and _walk(m, cw, a, d)):
            bad.append(((a, b), (c, d)))
    return bad


def test_R_001_07_a_route_never_steps_diagonally_past_a_blocked_orthogonal(lib, world_factory):
    w = wp._world(lib, world_factory, wp.OM_MOVE_WALKING, routes.CANVAS)
    routes._declare(lib)
    cw, _ = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    a, b, blocked = _cut_pair(lib, w, need_detour=False)
    u = lib.om_unit_spawn(w, wp.RAIDER, 0, *routes._centre(*a), LAYER)
    assert u
    n, pts, _ = routes._route(lib, w, u, *routes._centre(*b))
    bad = _legal_route(m, cw, pts)
    assert not bad, "route from %s to %s (%d blocked orthogonal) cuts corner(s): %s" % (a, b, blocked, bad)
    # control: an open 2x2 block (both orthogonals walkable) still takes the one-step diagonal
    oa, ob = _open_pair(lib, w)
    u2 = lib.om_unit_spawn(w, wp.RAIDER, 0, *routes._centre(*oa), LAYER)
    assert u2
    n2, pts2, _ = routes._route(lib, w, u2, *routes._centre(*ob))
    assert n2 == 2, "control: open diagonal %s -> %s should be one step, got %d points" % (oa, ob, n2)


def test_R_001_07_a_walker_following_a_detour_never_samples_a_masked_out_cell(lib, world_factory):
    w = wp._world(lib, world_factory, wp.OM_MOVE_WALKING, routes.CANVAS)
    routes._declare(lib)
    cw, _ = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    a, b, blocked = _cut_pair(lib, w, need_detour=True)
    u = lib.om_unit_spawn(w, wp.RAIDER, 0, *routes._centre(*a), LAYER)
    assert u
    goal = routes._centre(*b)
    n, pts, _ = routes._route(lib, w, u, *goal)
    assert not _legal_route(m, cw, pts), "setup: route %s -> %s cuts a corner: %s" % (a, b, [(int(x // CELL), int(y // CELL)) for x, y in pts])
    lib.om_command_move(w, [u], 1, *goal)
    for t in range(1, FOLLOW_TICKS + 1):
        lib.om_tactical_step(w)
        pos = lib.om_unit_get_pos(w, u)
        assert _on_mask(m, cw, pos), "tick %d: unit at (%.0f, %.0f) is off the mask" % (t, pos[0], pos[1])


def test_R_001_07_a_16_walker_blob_stays_on_the_mask_for_the_whole_crossing(lib, world_factory):
    w = wp._lab_world(lib, world_factory, wp.OM_MOVE_WALKING)
    cw, _ = routes._grid(lib, w)
    m = routes._mask(lib, w, LAYER)
    ids = wp._blob(lib, w)
    c0 = wp._centroid(lib, w, ids)
    lib.om_command_move(w, ids, len(ids), 600.0, 600.0)
    for t in range(1, BLOB_TICKS + 1):
        lib.om_tactical_step(w)
        for u in ids:
            pos = lib.om_unit_get_pos(w, u)
            assert _on_mask(m, cw, pos), "tick %d unit %d at (%.0f, %.0f) is off the mask" % (t, u, pos[0], pos[1])
    moved = math.hypot(*(p - q for p, q in zip(c0, wp._centroid(lib, w, ids))))
    assert moved > BLOB_MIN_MOVE, "blob centroid moved only %.0f wu in %d ticks" % (moved, BLOB_TICKS)


def test_R_001_07_flyer_blob_trace_is_unchanged_by_the_corner_rule(lib, world_factory):
    """Guard: flyers take no part in walk routes. Positive control: the flyers do move."""
    w = wp._lab_world(lib, world_factory, wp.OM_MOVE_FLYING)
    ids = wp._blob(lib, w)
    c0 = wp._centroid(lib, w, ids)
    lib.om_command_move(w, ids, len(ids), 600.0, 600.0)
    for _ in range(FLYER_TICKS):
        lib.om_tactical_step(w)
    assert math.hypot(*(p - q for p, q in zip(c0, wp._centroid(lib, w, ids)))) > 50.0, "flyers did not move"
    assert wp._units_movement(lib, w) == FLYER_SECTIONS_200
