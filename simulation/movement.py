import math
import heapq
import numpy as np
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED,
    FIELD_ABILITY_ACTIVE, FIELD_LAYER,
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
    for r, c in _bresenham(r1, c1, r2, c2):
        if not navmesh.is_walkable(r, c):
            return False
    return True


def _bresenham(r1, c1, r2, c2):
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


def _ensure_navmesh(tactical_map):
    if tactical_map is None:
        return None
    if not hasattr(tactical_map, "_navmesh"):
        tactical_map._navmesh = Navmesh.from_tactical_map(tactical_map)
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
    sep_radius = config.STEERING_SEPARATION_RADIUS
    sep_radius_sq = sep_radius * sep_radius
    obstacle_range = config.STEERING_OBSTACLE_AVOIDANCE_RANGE
    collision_radius = config.UNIT_COLLISION_RADIUS

    navmesh = _ensure_navmesh(tactical_map)
    path_cache = _ensure_path_cache(tactical_map)

    active = store.active_ids()
    positions = {}
    for uid in active:
        positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    _update_attack_move_state(store, active)

    for uid in active:
        if not store.has_move_target[uid]:
            continue
        if is_immobile(store, uid):
            continue
        # attack_move: hold position while engaged with a live target
        if store.auto_engage_target[uid] >= 0 and store.alive[store.auto_engage_target[uid]]:
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]

        eff = store.effective_speed[uid]
        speed = eff if eff > 0 else store.data[uid, FIELD_SPEED]
        speed *= get_speed_multiplier(store, uid)

        if navmesh is not None and navmesh.has_obstacles and uid not in store.waypoints:
            final_tx = store.target_x[uid]
            final_ty = store.target_y[uid]
            path = path_cache.get(navmesh, px, py, final_tx, final_ty)
            if path:
                store.waypoints[uid] = path

        if uid in store.waypoints and store.waypoints[uid]:
            tx, ty = store.waypoints[uid][0]
        else:
            tx = store.target_x[uid]
            ty = store.target_y[uid]

        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < collision_radius:
            if uid in store.waypoints:
                store.waypoints[uid].pop(0)
                if store.waypoints[uid]:
                    continue
                del store.waypoints[uid]
            store.has_move_target[uid] = False
            store.effective_speed[uid] = 0.0
            store.attack_moving[uid] = False
            continue

        seek_x = dx / dist
        seek_y = dy / dist

        sep_x = 0.0
        sep_y = 0.0
        for other_uid in active:
            if other_uid == uid:
                continue
            if store.data[other_uid, FIELD_LAYER] != store.data[uid, FIELD_LAYER]:
                continue
            ox = positions[other_uid][0]
            oy = positions[other_uid][1]
            sdx = px - ox
            sdy = py - oy
            d_sq = sdx * sdx + sdy * sdy
            if d_sq < sep_radius_sq and d_sq > 0.001:
                d = math.sqrt(d_sq)
                weight = 1.0 - (d / sep_radius)
                sep_x += (sdx / d) * weight
                sep_y += (sdy / d) * weight

        obs_x = 0.0
        obs_y = 0.0
        if tactical_map is not None:
            probe_x = px + seek_x * obstacle_range
            probe_y = py + seek_y * obstacle_range
            if tactical_map.in_bounds(probe_x, probe_y):
                density = tactical_map.obstacle_density(probe_x, probe_y)
                if density > 0.3:
                    obs_x = -seek_x * density
                    obs_y = -seek_y * density

        steer_x = seek_x + sep_x * 0.9 + obs_x * 1.0
        steer_y = seek_y + sep_y * 0.9 + obs_y * 1.0
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

    if config.HARD_COLLISION_ENABLED:
        _resolve_collisions(store, active, tactical_map, navmesh)


def _resolve_collisions(store, active, tactical_map, navmesh):
    radius = config.UNIT_COLLISION_RADIUS
    min_dist = 2.0 * radius
    min_dist_sq = min_dist * min_dist

    for _ in range(config.COLLISION_RESOLUTION_ITERATIONS):
        for i in range(len(active)):
            uid_a = active[i]
            ax = store.data[uid_a, FIELD_X]
            ay = store.data[uid_a, FIELD_Y]
            layer_a = store.data[uid_a, FIELD_LAYER]

            for j in range(i + 1, len(active)):
                uid_b = active[j]
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
                        new_ax, new_ay = ax, ay
                    rb, cb = navmesh.cell(new_bx, new_by)
                    if not navmesh.is_walkable(rb, cb):
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


def apply_group_move(store: UnitStore, unit_ids, tx, ty):
    min_speed = min(store.data[uid, FIELD_SPEED] for uid in unit_ids)
    for uid in unit_ids:
        store.set_move_target(uid, tx, ty)
        store.set_effective_speed(uid, min_speed)


def apply_fast_move(store: UnitStore, unit_ids, tx, ty):
    for uid in unit_ids:
        store.set_move_target(uid, tx, ty)
        store.clear_effective_speed(uid)
