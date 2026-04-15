"""
test_obstacle_navigation.py

Verifies that a unit navigates around a wall of obstacles to reach a goal
that is unreachable in a straight line.

Layout (2000 wide × 1000 tall, navmesh cell=100):

  - Wall: 2 rows thick (cell rows 4 & 5, y-centers 450 & 550), spanning cols 3–18
    (x-centers 350–1850). Sources placed exactly at cell centers, radius=55
    (half-cell + 5), constant falloff — covers exactly one cell, zero bleed.
  - Left corridor: cols 0–2 (x 0–300), fully clear of any source.
  - Start: (1000, 75)  — north of wall, mid-map
  - Goal:  (1000, 925) — south of wall, mid-map
  - Straight line (800 units) passes through the wall.
  - Path must detour left through the open corridor (~2350 units).

Known gap: obstacle gradient avoidance in update_movement can cancel waypoint-
following direction when the probe point lands inside a constant-falloff source at
density=1.0. Avoided here by using cell-sized sources (radius=55 < cell=100) so
gradient density is zero everywhere outside the wall cells — no avoidance force
fires during corridor travel. The underlying pinning bug is tracked separately.
"""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from tactical_map import TacticalMap, GradientSource
from unit import UnitStore, FIELD_X, FIELD_Y
from movement import Navmesh, find_path, update_movement


CANVAS_W = 2000
CANVAS_H = 1000
CELL     = config.NAVMESH_CELL_SIZE   # 100

START_X, START_Y = 1000.0,  75.0
GOAL_X,  GOAL_Y  = 1000.0, 925.0

# Wall: rows 4–5 (cell y-centers 450, 550), cols 3–18 (x-centers 350..1850)
_WALL_COLS = list(range(3, 19))         # 16 columns
_WALL_ROWS = [4, 5]                     # 2 rows
SRC_RADIUS = CELL * 0.55               # 55 — covers exactly one cell, no bleed
SRC_INTENSITY = 1.0


def _cell_center(row, col):
    return ((col + 0.5) * CELL, (row + 0.5) * CELL)


def _build_wall_map():
    sources = []
    for row in _WALL_ROWS:
        for col in _WALL_COLS:
            cx, cy = _cell_center(row, col)
            sources.append(GradientSource(
                position=(cx, cy),
                property_type="obstacle_density",
                radius=SRC_RADIUS,
                intensity=SRC_INTENSITY,
                falloff="constant",
            ))
    return TacticalMap(width=CANVAS_W, height=CANVAS_H, gradient_sources=sources)


def test_navmesh_marks_wall():
    tmap = _build_wall_map()
    nm = Navmesh.from_tactical_map(tmap)

    assert nm.has_obstacles, "Expected wall cells to be marked as obstacles"

    # Every wall cell must be blocked
    blocked = 0
    total = len(_WALL_ROWS) * len(_WALL_COLS)
    for row in _WALL_ROWS:
        for col in _WALL_COLS:
            if not nm.is_walkable(row, col):
                blocked += 1
    assert blocked == total, f"Expected {total} wall cells blocked, got {blocked}"

    # Corridor cells (cols 0–2) at wall rows must be walkable
    for row in _WALL_ROWS:
        for col in range(3):
            assert nm.is_walkable(row, col), (
                f"Corridor cell (row={row}, col={col}) wrongly blocked"
            )

    print(f"  PASS navmesh_marks_wall: {blocked}/{total} wall cells blocked, corridor clear")


def test_path_exists_and_avoids_wall():
    tmap = _build_wall_map()
    nm = Navmesh.from_tactical_map(tmap)

    path, nodes = find_path(nm, START_X, START_Y, GOAL_X, GOAL_Y)

    assert path is not None, "find_path returned None — no path found around wall"

    # All waypoints must land in walkable cells
    bad = []
    for (wx, wy) in path:
        r, c = nm.cell(wx, wy)
        if not nm.is_walkable(r, c):
            bad.append((wx, wy))
    assert not bad, f"Path waypoints land in blocked cells: {bad}"

    # Path must be longer than the straight line (proves detour)
    straight = math.hypot(GOAL_X - START_X, GOAL_Y - START_Y)
    path_len = 0.0
    prev = (START_X, START_Y)
    for wp in path:
        path_len += math.hypot(wp[0] - prev[0], wp[1] - prev[1])
        prev = wp

    assert path_len > straight, (
        f"Path length {path_len:.1f} <= straight-line {straight:.1f} — "
        "unit did not detour around wall"
    )
    print(f"  PASS path_exists_and_avoids_wall: "
          f"path_len={path_len:.1f}  straight={straight:.1f}  "
          f"nodes_explored={nodes}  waypoints={len(path)}")


def test_unit_reaches_goal():
    tmap = _build_wall_map()
    store = UnitStore()
    uid = store.spawn("Vanguard", 0, START_X, START_Y)
    store.set_move_target(uid, GOAL_X, GOAL_Y)

    dt = 0.1
    ticks = 1500
    arrival_radius = config.UNIT_COLLISION_RADIUS * 2

    for _ in range(ticks):
        update_movement(store, tmap, dt)
        if not store.has_move_target[uid]:
            break

    x = store.data[uid, FIELD_X]
    y = store.data[uid, FIELD_Y]
    dist = math.hypot(x - GOAL_X, y - GOAL_Y)

    assert dist <= arrival_radius, (
        f"Unit did not reach goal after {ticks} ticks — "
        f"final position ({x:.1f}, {y:.1f}), dist to goal {dist:.1f}"
    )
    print(f"  PASS unit_reaches_goal: "
          f"final=({x:.1f}, {y:.1f})  dist_to_goal={dist:.1f}")


def test_unit_never_enters_wall():
    tmap = _build_wall_map()
    nm = Navmesh.from_tactical_map(tmap)
    store = UnitStore()
    uid = store.spawn("Vanguard", 0, START_X, START_Y)
    store.set_move_target(uid, GOAL_X, GOAL_Y)

    dt = 0.1
    ticks = 1500
    violations = []

    for t in range(ticks):
        update_movement(store, tmap, dt)
        x = store.data[uid, FIELD_X]
        y = store.data[uid, FIELD_Y]
        r, c = nm.cell(x, y)
        if not nm.is_walkable(r, c):
            violations.append((t, x, y))
        if not store.has_move_target[uid]:
            break

    assert not violations, (
        f"Unit entered blocked cell(s): {violations[:5]}"
    )
    print(f"  PASS unit_never_enters_wall: 0 wall violations")


def test_gradient_avoidance_fires_for_direct_move():
    """Gradient avoidance still fires for direct-move units (no waypoints).

    Source placed between cell centers so has_obstacles=False — no blocked
    cells, no A*-computed waypoints. Probe lands inside the source, density=1.0
    cancels the seek direction, unit freezes. This behavior is preserved by the
    `not has_waypoints` guard: the guard only exempts units already on a path.
    """
    src = GradientSource(
        position=(100.0, 400.0),
        property_type="obstacle_density",
        radius=45.0,
        intensity=1.0,
        falloff="constant",
    )
    tmap = TacticalMap(width=1000, height=1000, gradient_sources=[src])
    nm = Navmesh.from_tactical_map(tmap)
    assert not nm.has_obstacles, (
        "Source must not block any navmesh cell — recheck source placement"
    )

    store = UnitStore()
    uid = store.spawn("Vanguard", 0, 100.0, 350.0)
    store.set_move_target(uid, 100.0, 450.0)

    for _ in range(200):
        update_movement(store, tmap, 0.1)
        if not store.has_move_target[uid]:
            break

    y = store.data[uid, FIELD_Y]
    assert y < 440.0, (
        f"Direct-move unit should be frozen by gradient avoidance "
        f"— got y={y:.1f}, expected < 440"
    )
    print(f"  PASS gradient_avoidance_fires_for_direct_move: unit frozen at y={y:.1f}")


if __name__ == "__main__":
    print("Obstacle navigation tests")
    print("-" * 48)
    test_navmesh_marks_wall()
    test_path_exists_and_avoids_wall()
    test_unit_reaches_goal()
    test_unit_never_enters_wall()
    test_gradient_avoidance_fires_for_direct_move()
    print("-" * 48)
    print("All tests passed.")
