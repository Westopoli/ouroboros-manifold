import math
import time
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED
from movement import Navmesh, PathCache, find_path, update_movement
from test_maps import open_field, chokepoint, cover_heavy

DT = config.TACTICAL_TICK_DURATION


def path_length(start_x, start_y, waypoints):
    total = 0.0
    px, py = start_x, start_y
    for wx, wy in waypoints:
        total += math.sqrt((wx - px) ** 2 + (wy - py) ** 2)
        px, py = wx, wy
    return total


def test_navmesh_generation():
    print("=" * 70)
    print("  NAVMESH GENERATION TIME")
    print("=" * 70)

    maps = [("open_field", open_field()), ("chokepoint", chokepoint()), ("cover_heavy", cover_heavy())]
    all_pass = True

    print(f"  {'Map':<16} {'Cells':>8} {'Blocked':>8} {'Time (ms)':>10} {'Status':>8}")
    print(f"  {'-'*16} {'-'*8} {'-'*8} {'-'*10} {'-'*8}")

    for name, tmap in maps:
        t0 = time.perf_counter()
        nm = Navmesh.from_tactical_map(tmap)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        total_cells = nm.rows * nm.cols
        blocked = sum(1 for r in range(nm.rows) for c in range(nm.cols) if not nm.grid[r][c])
        ok = elapsed_ms < 500
        if not ok:
            all_pass = False
        print(f"  {name:<16} {total_cells:>8} {blocked:>8} {elapsed_ms:>9.1f} {'OK' if ok else 'FAIL':>8}")

    print(f"\n  Navmesh generation: {'PASS' if all_pass else 'FAIL'} (all <500ms)")
    return all_pass


def test_chokepoint_path():
    print(f"\n{'=' * 70}")
    print("  CHOKEPOINT PATHFINDING")
    print("=" * 70)

    tmap = chokepoint()
    nm = Navmesh.from_tactical_map(tmap)

    start_x, start_y = 1000.0, 1000.0
    goal_x, goal_y = 3000.0, 3000.0

    path, nodes_explored = find_path(nm, start_x, start_y, goal_x, goal_y)

    ok = path is not None
    print(f"  Path found: {ok}")
    print(f"  Nodes explored: {nodes_explored}")

    if path:
        total = path_length(start_x, start_y, path)
        straight = math.sqrt((goal_x - start_x) ** 2 + (goal_y - start_y) ** 2)
        print(f"  Waypoints: {len(path)}")
        print(f"  Path length: {total:.0f} wu")
        print(f"  Straight-line: {straight:.0f} wu")
        print(f"  Path/straight ratio: {total / straight:.2f}")
        print(f"\n  Waypoint sequence:")
        for i, (wx, wy) in enumerate(path):
            print(f"    WP {i}: ({wx:.0f}, {wy:.0f})")

        all_in_gap = True
        for wx, wy in path:
            r, c = nm.cell(wx, wy)
            if not nm.is_walkable(r, c):
                all_in_gap = False
                print(f"    WARNING: waypoint ({wx:.0f}, {wy:.0f}) is in blocked cell ({r}, {c})")
        print(f"\n  All waypoints in walkable cells: {all_in_gap}")
    else:
        print("  ERROR: no path found through chokepoint")

    print(f"\n  Chokepoint path: {'PASS' if ok else 'FAIL'}")
    return ok


def test_chokepoint_unit_movement():
    print(f"\n{'=' * 70}")
    print("  CHOKEPOINT UNIT MOVEMENT — 5 sampled positions")
    print("=" * 70)

    tmap = chokepoint()
    store = UnitStore()
    uid = store.spawn("Raider", 0, 1000.0, 1000.0)
    store.set_move_target(uid, 3000.0, 3000.0)

    sample_ticks = [0, 100, 200, 300, 400]
    max_tick = max(sample_ticks) + 1

    print(f"  {'Tick':>6} {'X':>8} {'Y':>8} {'Wall side':>12}")
    print(f"  {'-'*6} {'-'*8} {'-'*8} {'-'*12}")

    wall_crossed = False
    for tick in range(max_tick):
        if tick in sample_ticks:
            x = store.data[uid, FIELD_X]
            y = store.data[uid, FIELD_Y]
            side = "below" if y < 1700 else ("above" if y > 2300 else "in gap")
            if y > 2300:
                wall_crossed = True
            print(f"  {tick:>6} {x:>8.0f} {y:>8.0f} {side:>12}")
        update_movement(store, tmap, DT)

    x = store.data[uid, FIELD_X]
    y = store.data[uid, FIELD_Y]
    if y > 2300:
        wall_crossed = True

    nm = Navmesh.from_tactical_map(tmap)
    r, c = nm.cell(x, y)
    in_walkable = nm.is_walkable(r, c)

    print(f"\n  Final position: ({x:.0f}, {y:.0f})")
    print(f"  Wall crossed: {wall_crossed}")
    print(f"  In walkable cell: {in_walkable}")

    ok = wall_crossed and in_walkable
    print(f"\n  Chokepoint movement: {'PASS' if ok else 'FAIL'}")
    return ok


def test_open_field_path():
    print(f"\n{'=' * 70}")
    print("  OPEN FIELD PATH — near-straight line")
    print("=" * 70)

    tmap = open_field()
    nm = Navmesh.from_tactical_map(tmap)

    start_x, start_y = 500.0, 500.0
    goal_x, goal_y = 3500.0, 3500.0

    path, nodes_explored = find_path(nm, start_x, start_y, goal_x, goal_y)

    ok = False
    if path:
        total = path_length(start_x, start_y, path)
        straight = math.sqrt((goal_x - start_x) ** 2 + (goal_y - start_y) ** 2)
        ratio = total / straight
        ok = len(path) <= 3 and ratio < 1.05

        print(f"  Waypoints: {len(path)} (target: ≤3)")
        print(f"  Path length: {total:.0f} wu")
        print(f"  Straight-line: {straight:.0f} wu")
        print(f"  Ratio: {ratio:.4f} (target: <1.05)")
        print(f"  Nodes explored: {nodes_explored}")
        for i, (wx, wy) in enumerate(path):
            print(f"    WP {i}: ({wx:.0f}, {wy:.0f})")
    else:
        print("  ERROR: no path found on open field")

    print(f"\n  Open field path: {'PASS' if ok else 'FAIL'}")
    return ok


def test_path_caching():
    print(f"\n{'=' * 70}")
    print("  PATH CACHING — 10 units, same destination")
    print("=" * 70)

    tmap = chokepoint()
    nm = Navmesh.from_tactical_map(tmap)
    cache = PathCache()

    goal_x, goal_y = 3000.0, 3000.0
    for i in range(10):
        sx = 1000.0 + (i % 3) * 20.0
        sy = 1000.0 + (i // 3) * 20.0
        cache.get(nm, sx, sy, goal_x, goal_y)

    print(f"  Requests:    10")
    print(f"  Cache hits:  {cache.hits}")
    print(f"  Cache misses: {cache.misses}")

    ok = cache.hits > 0
    print(f"\n  Path caching: {'PASS' if ok else 'FAIL'} (hits > 0)")
    return ok


def run():
    print("=" * 70)
    print("CHECKPOINT 6F — Pathfinding and Navmesh")
    print("=" * 70)

    results = {}
    results["Navmesh gen"] = test_navmesh_generation()
    results["Chokepoint path"] = test_chokepoint_path()
    results["Chokepoint movement"] = test_chokepoint_unit_movement()
    results["Open field path"] = test_open_field_path()
    results["Path caching"] = test_path_caching()

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name:<24} {'PASS' if passed else 'FAIL'}")

    total_pass = sum(1 for v in results.values() if v)
    print(f"\n  {total_pass}/{len(results)} tests passed")
    print("\nCheckpoint 6F complete.")


if __name__ == "__main__":
    run()
