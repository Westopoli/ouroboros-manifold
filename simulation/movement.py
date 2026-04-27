import math
import heapq
import numpy as np
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED,
    FIELD_ABILITY_ACTIVE, FIELD_LAYER, FIELD_ATTACK_RANGE,
)
from ability import is_immobile, get_speed_multiplier


class Navmesh:
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.cols = int(math.ceil(width / cell_size))
        self.rows = int(math.ceil(height / cell_size))
        self.grid = [[True] * self.cols for _ in range(self.rows)]
        self.has_obstacles = False

    @classmethod
    def from_tactical_map(cls, tmap):
        nm = cls(tmap.width, tmap.height, config.NAVMESH_CELL_SIZE)
        threshold = config.NAVMESH_OBSTACLE_THRESHOLD
        for r in range(nm.rows):
            for c in range(nm.cols):
                cx = (c + 0.5) * nm.cell_size
                cy = (r + 0.5) * nm.cell_size
                if tmap.obstacle_density(cx, cy) >= threshold:
                    nm.grid[r][c] = False
                    nm.has_obstacles = True
        return nm

    def cell(self, x, y):
        c = max(0, min(self.cols - 1, int(x / self.cell_size)))
        r = max(0, min(self.rows - 1, int(y / self.cell_size)))
        return (r, c)

    def cell_center(self, r, c):
        return ((c + 0.5) * self.cell_size, (r + 0.5) * self.cell_size)

    def is_walkable(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c]

    def neighbors(self, r, c):
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1),
                        (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if not self.is_walkable(nr, nc):
                continue
            if dr != 0 and dc != 0:
                if not self.is_walkable(r + dr, c) or not self.is_walkable(r, c + dc):
                    continue
            result.append((nr, nc))
        return result


class PathCache:
    def __init__(self):
        self._cache = {}
        self.hits = 0
        self.misses = 0

    def get(self, navmesh, start_x, start_y, goal_x, goal_y):
        sr, sc = navmesh.cell(start_x, start_y)
        gr, gc = navmesh.cell(goal_x, goal_y)
        key = (sr, sc, gr, gc)
        if key in self._cache:
            self.hits += 1
            return list(self._cache[key])
        self.misses += 1
        result = find_path(navmesh, start_x, start_y, goal_x, goal_y)
        if result[0] is not None:
            self._cache[key] = result[0]
            return list(result[0])
        return None

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0


def find_path(navmesh, start_x, start_y, goal_x, goal_y):
    sr, sc = navmesh.cell(start_x, start_y)
    gr, gc = navmesh.cell(goal_x, goal_y)

    if (sr, sc) == (gr, gc):
        return [(goal_x, goal_y)], 0

    if not navmesh.is_walkable(gr, gc):
        return [(goal_x, goal_y)], 0

    SQRT2 = math.sqrt(2)

    def heuristic(r, c):
        dr = abs(r - gr)
        dc = abs(c - gc)
        return max(dr, dc) + (SQRT2 - 1) * min(dr, dc)

    open_set = [(heuristic(sr, sc), 0.0, sr, sc)]
    g_score = {(sr, sc): 0.0}
    came_from = {}
    nodes_explored = 0

    while open_set:
        f, g, r, c = heapq.heappop(open_set)
        nodes_explored += 1

        if (r, c) == (gr, gc):
            path = []
            current = (gr, gc)
            while current in came_from:
                path.append(navmesh.cell_center(*current))
                current = came_from[current]
            path.reverse()
            if path:
                path[-1] = (goal_x, goal_y)
            else:
                path = [(goal_x, goal_y)]
            path = _simplify_path(navmesh, start_x, start_y, path)
            return path, nodes_explored

        if g > g_score.get((r, c), float("inf")):
            continue

        for nr, nc in navmesh.neighbors(r, c):
            d = SQRT2 if (nr != r and nc != c) else 1.0
            new_g = g + d
            if new_g < g_score.get((nr, nc), float("inf")):
                g_score[(nr, nc)] = new_g
                came_from[(nr, nc)] = (r, c)
                heapq.heappush(open_set, (new_g + heuristic(nr, nc), new_g, nr, nc))

    return None, nodes_explored


def _simplify_path(navmesh, start_x, start_y, path):
    if len(path) <= 1:
        return path
    full = [(start_x, start_y)] + path
    simplified = []
    i = 0
    while i < len(full) - 1:
        furthest = i + 1
        for j in range(i + 2, len(full)):
            if _has_los(navmesh, full[i], full[j]):
                furthest = j
        simplified.append(full[furthest])
        i = furthest
    return simplified


def _has_los(navmesh, p1, p2):
    r1, c1 = navmesh.cell(*p1)
    r2, c2 = navmesh.cell(*p2)
    for r, c in _supercover(r1, c1, r2, c2):
        if not navmesh.is_walkable(r, c):
            return False
    return True


def _supercover(r1, c1, r2, c2):
    # Bresenham + diagonal neighbor check. On each diagonal step, also yields
    # both orthogonal neighbors so every cell the continuous segment passes
    # through is checked. Replaces _bresenham in _has_los to prevent
    # _simplify_path from approving segments that clip wall corners.
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        yield (r, c)
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        step_r = e2 > -dc
        step_c = e2 < dr
        if step_r and step_c:
            yield (r + sr, c)
            yield (r, c + sc)
        if step_r:
            err -= dc
            r += sr
        if step_c:
            err += dr
            c += sc


def _bresenham(r1, c1, r2, c2):
    # Retained for reference. Replaced by _supercover in _has_los.
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        yield (r, c)
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc


def _probe_is_blocked(probe_grid, probe_cell_size, uid, px, py, dx, dy, probe_dist, block_r_sq, store):
    ppx = px + dx * probe_dist
    ppy = py + dy * probe_dist
    my_layer = store.data[uid, FIELD_LAYER]
    cr = int(ppx / probe_cell_size)
    cc = int(ppy / probe_cell_size)
    for nr in range(cr - 1, cr + 2):
        for nc in range(cc - 1, cc + 2):
            neighbors = probe_grid.get((nr, nc))
            if neighbors is None:
                continue
            for other_uid, ox, oy in neighbors:
                if other_uid == uid:
                    continue
                if store.data[other_uid, FIELD_LAYER] != my_layer:
                    continue
                ddx = ox - ppx
                ddy = oy - ppy
                if ddx * ddx + ddy * ddy < block_r_sq:
                    return True
    return False


def _ensure_navmesh(tactical_map):
    # Navmesh build takes ~5s on large (24000x24000) maps. Called eagerly by
    # TacticalEngine.__init__() so the cost is paid during engine creation (before
    # first tick). Godot shows tactical_loading_overlay.gd during the wait.
    if tactical_map is None:
        return None
    if not hasattr(tactical_map, "_navmesh"):
        tactical_map._navmesh = Navmesh.from_tactical_map(tactical_map)
        tactical_map._navmesh_generation_count = (
            getattr(tactical_map, "_navmesh_generation_count", 0) + 1
        )
    return tactical_map._navmesh


def _ensure_path_cache(tactical_map):
    if tactical_map is None:
        return None
    if not hasattr(tactical_map, "_path_cache"):
        tactical_map._path_cache = PathCache()
    return tactical_map._path_cache


_ATTACK_MOVE_LEASH_SQ = 200.0 * 200.0


def _update_attack_move_state(store, active):
    # Called after update_targeting; sets anchor on first engagement and enforces leash.
    for uid in active:
        if not store.attack_moving[uid]:
            continue
        tgt = store.auto_engage_target[uid]
        if tgt >= 0 and store.alive[tgt]:
            if not store.engage_anchor_set[uid]:
                store.engage_anchor_x[uid] = store.data[uid, FIELD_X]
                store.engage_anchor_y[uid] = store.data[uid, FIELD_Y]
                store.engage_anchor_set[uid] = True
            dx = store.data[tgt, FIELD_X] - store.engage_anchor_x[uid]
            dy = store.data[tgt, FIELD_Y] - store.engage_anchor_y[uid]
            if dx * dx + dy * dy > _ATTACK_MOVE_LEASH_SQ:
                store.auto_engage_target[uid] = -1
                store.engage_anchor_set[uid] = False
        else:
            store.engage_anchor_set[uid] = False


def update_movement(store: UnitStore, tactical_map, dt: float):
    obstacle_range = config.STEERING_OBSTACLE_AVOIDANCE_RANGE
    collision_radius = config.UNIT_COLLISION_RADIUS

    navmesh = _ensure_navmesh(tactical_map)
    path_cache = _ensure_path_cache(tactical_map)

    active = store.active_ids()
    positions = {}
    for uid in active:
        positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    # Spatial grid for _probe_is_blocked — built once per tick, cell sized to
    # block_radius so only the 3×3 neighborhood around the probe point needs checking.
    # See _probe_is_blocked for query logic.
    probe_cell_size = float(config.UNIT_COLLISION_RADIUS * 2)
    probe_grid = {}
    for uid, (x, y) in positions.items():
        cr = int(x / probe_cell_size)
        cc = int(y / probe_cell_size)
        key = (cr, cc)
        if key not in probe_grid:
            probe_grid[key] = []
        probe_grid[key].append((uid, x, y))

    _update_attack_move_state(store, active)

    for uid in active:
        if store.attack_backswing[uid] > 0:
            store.attack_backswing[uid] = max(0.0, store.attack_backswing[uid] - dt)

    for uid in active:
        if not store.has_move_target[uid]:
            continue
        if is_immobile(store, uid):
            continue
        if store.attack_backswing[uid] > 0:  # post-attack movement lock (SC2-style backswing)
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]

        # Hold position only while target is actively within firing range.
        # When target drifts out of range, unit pursues rather than staying frozen.
        # See also: damage.py update_targeting — sensor pursuit updates target_x/y
        # each tick toward the nearest enemy for attack_moving units with large sensor radius.
        tgt = store.auto_engage_target[uid]
        if tgt >= 0 and store.alive[tgt]:
            atk_r = store.data[uid, FIELD_ATTACK_RANGE]
            dx_t = store.data[tgt, FIELD_X] - px
            dy_t = store.data[tgt, FIELD_Y] - py
            if dx_t * dx_t + dy_t * dy_t <= atk_r * atk_r:
                continue  # target in firing range — hold position

        eff = store.effective_speed[uid]
        speed = eff if eff > 0 else store.data[uid, FIELD_SPEED]
        speed *= get_speed_multiplier(store, uid)

        if navmesh is not None and navmesh.has_obstacles and uid not in store.waypoints:
            final_tx = store.target_x[uid]
            final_ty = store.target_y[uid]
            path = path_cache.get(navmesh, px, py, final_tx, final_ty)
            if path:
                store.waypoints[uid] = path

        has_waypoints = uid in store.waypoints and store.waypoints[uid]
        if has_waypoints:
            tx, ty = store.waypoints[uid][0]
            arrival_radius = collision_radius * 2.0
        else:
            tx = store.target_x[uid]
            ty = store.target_y[uid]
            # At the final slot, use a wider arrival radius so formation units
            # don't endlessly seek a point blocked by collision. Gated on the
            # formation flag so flag-off behavior is bit-identical.
            # See also: apply_group_move — assigns per-unit slot targets.
            if config.FORMATION_MOVE_ENABLED:
                arrival_radius = collision_radius * config.ARRIVAL_TOLERANCE_MULT
            else:
                arrival_radius = collision_radius

        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < arrival_radius:
            if uid in store.waypoints:
                store.waypoints[uid].pop(0)
                if store.waypoints[uid]:
                    continue
                del store.waypoints[uid]
            store.has_move_target[uid] = False
            store.effective_speed[uid] = 0.0
            # attack_moving is intentionally NOT cleared here — it is a command-
            # level flag that should persist until a new command (move,
            # attack_target, activate_ability) replaces it. Clearing it on
            # arrival left units unable to pursue enemies they could see but
            # not yet shoot after their move target was consumed.
            store.plain_moving[uid] = False
            store.detour_remaining[uid] = 0.0
            # Remove from formation group's moving set on slot arrival.
            # _update_move_groups (Step 4) uses this set for centroid-arrival check.
            gid = store.move_group_id[uid]
            if gid >= 0 and gid in store.move_groups:
                store.move_groups[gid]["moving"].discard(uid)
            store.move_group_id[uid] = -1
            continue

        seek_x = dx / dist
        seek_y = dy / dist

        probe_dist = config.STEERING_PROBE_DIST
        block_r_sq = (config.UNIT_COLLISION_RADIUS * 2) ** 2

        if store.detour_remaining[uid] > 0:
            steer_x, steer_y = store.detour_dx[uid], store.detour_dy[uid]
        elif _probe_is_blocked(probe_grid, probe_cell_size, uid, px, py, seek_x, seek_y, probe_dist, block_r_sq, store):
            steer_x, steer_y = seek_x, seek_y
            heading_angle = math.atan2(seek_y, seek_x)
            for deg in [30, -30, 60, -60, 90, -90]:
                a = heading_angle + math.radians(deg)
                ax, ay = math.cos(a), math.sin(a)
                if not _probe_is_blocked(probe_grid, probe_cell_size, uid, px, py, ax, ay, probe_dist, block_r_sq, store):
                    steer_x, steer_y = ax, ay
                    store.detour_dx[uid] = ax
                    store.detour_dy[uid] = ay
                    store.detour_remaining[uid] = config.STEERING_DETOUR_MIN_DIST
                    break
        else:
            steer_x, steer_y = seek_x, seek_y

        obs_x, obs_y = 0.0, 0.0
        if tactical_map is not None and not has_waypoints:
            probe_x = px + steer_x * obstacle_range
            probe_y = py + steer_y * obstacle_range
            if tactical_map.in_bounds(probe_x, probe_y):
                density = tactical_map.obstacle_density(probe_x, probe_y)
                if density > 0.3:
                    obs_x = -steer_x * density
                    obs_y = -steer_y * density

        steer_x += obs_x
        steer_y += obs_y
        mag = math.sqrt(steer_x * steer_x + steer_y * steer_y)
        if mag > 0.001:
            steer_x /= mag
            steer_y /= mag

        move_dist = speed * dt
        if move_dist > dist:
            move_dist = dist

        new_x = px + steer_x * move_dist
        new_y = py + steer_y * move_dist

        if tactical_map is not None:
            new_x = max(0.0, min(tactical_map.width, new_x))
            new_y = max(0.0, min(tactical_map.height, new_y))

        store.data[uid, FIELD_X] = new_x
        store.data[uid, FIELD_Y] = new_y
        if store.detour_remaining[uid] > 0:
            store.detour_remaining[uid] = max(0.0, store.detour_remaining[uid] - move_dist)

    if config.FORMATION_MOVE_ENABLED:
        _update_move_groups(store)

    if config.HARD_COLLISION_ENABLED:
        # Only units that actually moved this tick drive the outer collision loop.
        # Stationary engaged units still live in the grid so movers can push them,
        # but they never initiate pair checks — cutting ~90% of work in dense combat.
        moved = {uid for uid in active if (
            store.data[uid, FIELD_X] != positions[uid][0] or
            store.data[uid, FIELD_Y] != positions[uid][1]
        )}
        _resolve_collisions(store, active, moved, tactical_map, navmesh)


def _update_move_groups(store):
    """Terminate formation groups by centroid arrival or empty moving set.

    Called from update_movement after the per-unit loop. See apply_group_move
    for group creation, and unit.py kill/set_move_target for moving-set cleanup.
    """
    if not store.move_groups:
        return

    group_arrival_sq = config.GROUP_ARRIVAL_RADIUS ** 2
    completed = []

    for gid, group in store.move_groups.items():
        tx = group["target_x"]
        ty = group["target_y"]
        moving = group["moving"]

        cx = cy = 0.0
        count = 0
        for uid in list(moving):
            if not store.alive[uid]:
                moving.discard(uid)
                continue
            engaged = (store.auto_engage_target[uid] >= 0
                       and store.alive[store.auto_engage_target[uid]])
            if engaged or not store.has_move_target[uid]:
                moving.discard(uid)
                continue
            cx += store.data[uid, FIELD_X]
            cy += store.data[uid, FIELD_Y]
            count += 1

        if count == 0:
            completed.append(gid)
            continue

        cx /= count
        cy /= count
        if (cx - tx) ** 2 + (cy - ty) ** 2 <= group_arrival_sq:
            completed.append(gid)

    for gid in completed:
        group = store.move_groups.pop(gid)
        for uid in group["uids"]:
            if not store.alive[uid]:
                continue
            if store.move_group_id[uid] != gid:  # reassigned to a newer group
                continue
            store.has_move_target[uid] = False
            store.effective_speed[uid] = 0.0
            store.detour_remaining[uid] = 0.0
            store.waypoints.pop(uid, None)
            # Do NOT clear attack_moving — units that were attack-moving stay in
            # attack mode after the group dissolves so they can still acquire
            # targets.
            store.plain_moving[uid] = False
            store.move_group_id[uid] = -1


def _resolve_collisions(store, active, moved, tactical_map, navmesh):
    radius = config.UNIT_COLLISION_RADIUS
    min_dist = 2.0 * radius
    min_dist_sq = min_dist * min_dist
    cell_size = min_dist  # cell sized to min_dist so only adjacent cells can overlap

    for _ in range(config.COLLISION_RESOLUTION_ITERATIONS):
        # Build spatial grid: cell (cr, cc) → list of uids in that cell.
        # Rebuilt each iteration because positions change after each push pass.
        # All active units go in the grid so stationary units can still be pushed.
        grid = {}
        for uid in active:
            cr = int(store.data[uid, FIELD_X] / cell_size)
            cc = int(store.data[uid, FIELD_Y] / cell_size)
            if (cr, cc) not in grid:
                grid[(cr, cc)] = []
            grid[(cr, cc)].append(uid)

        # Only moved units drive the outer loop — stationary engaged units never
        # initiate pair checks, cutting ~90% of iterations during dense combat.
        for uid_a in moved:
            ax = store.data[uid_a, FIELD_X]
            ay = store.data[uid_a, FIELD_Y]
            layer_a = store.data[uid_a, FIELD_LAYER]
            cr = int(ax / cell_size)
            cc = int(ay / cell_size)

            # Only check units in the 3×3 neighborhood — units further away
            # cannot be within min_dist of uid_a given cell_size == min_dist.
            for nr in range(cr - 1, cr + 2):
                for nc in range(cc - 1, cc + 2):
                    neighbors = grid.get((nr, nc))
                    if neighbors is None:
                        continue
                    for uid_b in neighbors:
                        if uid_b <= uid_a:  # avoid double-counting and self
                            continue
                        if store.data[uid_b, FIELD_LAYER] != layer_a:
                            continue

                        bx = store.data[uid_b, FIELD_X]
                        by = store.data[uid_b, FIELD_Y]
                        dx = ax - bx
                        dy = ay - by
                        d_sq = dx * dx + dy * dy

                        if d_sq >= min_dist_sq:
                            continue

                        if d_sq < 0.001:
                            # Deterministic fallback: lower uid pushes left
                            dx = -1.0 if uid_a < uid_b else 1.0
                            dy = 0.0
                            d = 0.001
                        else:
                            d = math.sqrt(d_sq)

                        overlap = min_dist - d
                        nx = dx / d
                        ny = dy / d

                        moving_a = store.has_move_target[uid_a] and not (
                            store.auto_engage_target[uid_a] >= 0 and store.alive[store.auto_engage_target[uid_a]]
                        )
                        moving_b = store.has_move_target[uid_b] and not (
                            store.auto_engage_target[uid_b] >= 0 and store.alive[store.auto_engage_target[uid_b]]
                        )

                        if moving_a and moving_b:
                            push_a, push_b = overlap * 0.5, overlap * 0.5
                        elif moving_a:
                            push_a, push_b = overlap, 0.0
                        elif moving_b:
                            push_a, push_b = 0.0, overlap
                        else:
                            push_a, push_b = overlap * 0.5, overlap * 0.5

                        new_ax = ax + nx * push_a
                        new_ay = ay + ny * push_a
                        new_bx = bx - nx * push_b
                        new_by = by - ny * push_b

                        if tactical_map is not None:
                            new_ax = max(0.0, min(tactical_map.width, new_ax))
                            new_ay = max(0.0, min(tactical_map.height, new_ay))
                            new_bx = max(0.0, min(tactical_map.width, new_bx))
                            new_by = max(0.0, min(tactical_map.height, new_by))

                        if navmesh is not None:
                            ra, ca = navmesh.cell(new_ax, new_ay)
                            if not navmesh.is_walkable(ra, ca):
                                # Try sliding along each axis before full revert.
                                ra2, ca2 = navmesh.cell(new_ax, ay)
                                if navmesh.is_walkable(ra2, ca2):
                                    new_ay = ay
                                else:
                                    ra3, ca3 = navmesh.cell(ax, new_ay)
                                    if navmesh.is_walkable(ra3, ca3):
                                        new_ax = ax
                                    else:
                                        new_ax, new_ay = ax, ay
                            rb, cb = navmesh.cell(new_bx, new_by)
                            if not navmesh.is_walkable(rb, cb):
                                # Try sliding along each axis before full revert.
                                rb2, cb2 = navmesh.cell(new_bx, by)
                                if navmesh.is_walkable(rb2, cb2):
                                    new_by = by
                                else:
                                    rb3, cb3 = navmesh.cell(bx, new_by)
                                    if navmesh.is_walkable(rb3, cb3):
                                        new_bx = bx
                                    else:
                                        new_bx, new_by = bx, by

                        store.data[uid_a, FIELD_X] = new_ax
                        store.data[uid_a, FIELD_Y] = new_ay
                        ax = new_ax
                        ay = new_ay
                        store.data[uid_b, FIELD_X] = new_bx
                        store.data[uid_b, FIELD_Y] = new_by


def has_combat_los(navmesh, x1, y1, x2, y2):
    if navmesh is None:
        return True
    return _has_los(navmesh, (x1, y1), (x2, y2))


def apply_group_move(store, unit_ids, tx, ty, tactical_map=None):
    """Issue a move order for a group of units.

    When FORMATION_MOVE_ENABLED is True and len > 1, each unit gets a personal
    offset slot derived from the group's current centroid — UNLESS the group is
    scattered (any unit farther than MAGIC_BOX_SPREAD_RADIUS from the centroid),
    in which case all units converge on (tx, ty) directly. Group is always
    registered in store.move_groups so _update_move_groups can terminate it by
    centroid arrival. See command.py move/attack_move handlers.

    When flag is False (or single-unit), falls back to the old shared-target path
    so behavior is bit-identical to pre-formation code.
    """
    alive_ids = [uid for uid in unit_ids if store.alive[uid]]
    if not alive_ids:
        return

    if not config.FORMATION_MOVE_ENABLED or len(alive_ids) == 1:
        for uid in alive_ids:
            store.set_move_target(uid, tx, ty)
        return

    cx = sum(store.data[uid, FIELD_X] for uid in alive_ids) / len(alive_ids)
    cy = sum(store.data[uid, FIELD_Y] for uid in alive_ids) / len(alive_ids)

    spread_sq = config.MAGIC_BOX_SPREAD_RADIUS ** 2
    scattered = any(
        (store.data[uid, FIELD_X] - cx) ** 2 + (store.data[uid, FIELD_Y] - cy) ** 2
        > spread_sq
        for uid in alive_ids
    )

    navmesh = _ensure_navmesh(tactical_map) if tactical_map is not None else None

    gid = store._next_move_group_id
    store._next_move_group_id += 1

    offsets = {}
    moving_set = set()

    for uid in alive_ids:
        if scattered:
            slot_x, slot_y = tx, ty
        else:
            ox = store.data[uid, FIELD_X] - cx
            oy = store.data[uid, FIELD_Y] - cy
            slot_x = tx + ox
            slot_y = ty + oy

            if navmesh is not None:
                tr, tc = navmesh.cell(slot_x, slot_y)
                if not navmesh.is_walkable(tr, tc):
                    slot_x, slot_y = tx, ty

        offsets[uid] = (slot_x - tx, slot_y - ty)
        store.set_move_target(uid, slot_x, slot_y)
        store.move_group_id[uid] = gid
        moving_set.add(uid)

    store.move_groups[gid] = {
        "uids": list(alive_ids),
        "target_x": tx,
        "target_y": ty,
        "offsets": offsets,
        "moving": moving_set,
    }


