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


def _compute_preferred_velocities(store, active, dt):
    preferred = {}
    for uid in active:
        if is_immobile(store, uid):
            preferred[uid] = (0.0, 0.0, 0.0)
            continue

        eff = store.effective_speed[uid]
        speed = (eff if eff > 0 else store.data[uid, FIELD_SPEED]) * get_speed_multiplier(store, uid)

        # attack_move: hold position and fight when a valid target is in range
        if store.attack_moving[uid]:
            tgt = store.auto_engage_target[uid]
            if tgt >= 0 and store.alive[tgt]:
                preferred[uid] = (0.0, 0.0, speed)
                continue

        if not store.has_move_target[uid]:
            preferred[uid] = (0.0, 0.0, 0.0)
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]

        if uid in store.waypoints and store.waypoints[uid]:
            tx, ty = store.waypoints[uid][0]
        else:
            tx = store.target_x[uid]
            ty = store.target_y[uid]

        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.001:
            preferred[uid] = (0.0, 0.0, speed)
            continue

        vx = (dx / dist) * min(speed, dist / dt)
        vy = (dy / dist) * min(speed, dist / dt)
        preferred[uid] = (vx, vy, speed)

    return preferred


def _compute_orca_line(pa_x, pa_y, pb_x, pb_y, va_x, va_y, vb_x, vb_y, combined_radius, time_horizon):
    rel_x = pb_x - pa_x
    rel_y = pb_y - pa_y
    rel_vel_x = va_x - vb_x
    rel_vel_y = va_y - vb_y
    dist_sq = rel_x * rel_x + rel_y * rel_y
    combined_r_sq = combined_radius * combined_radius

    if dist_sq > combined_r_sq:
        w_x = rel_vel_x - rel_x / time_horizon
        w_y = rel_vel_y - rel_y / time_horizon
        w_dot_rel = w_x * rel_x + w_y * rel_y
        w_len_sq = w_x * w_x + w_y * w_y

        leg_sq = dist_sq - combined_r_sq
        if w_dot_rel < 0.0 and w_dot_rel * w_dot_rel > combined_r_sq * w_len_sq:
            w_len = math.sqrt(w_len_sq) if w_len_sq > 0 else 0.001
            unit_w_x = w_x / w_len
            unit_w_y = w_y / w_len
            line_dir_x = unit_w_y
            line_dir_y = -unit_w_x
            u_x = (combined_radius / time_horizon - w_len) * unit_w_x
            u_y = (combined_radius / time_horizon - w_len) * unit_w_y
        else:
            leg = math.sqrt(max(leg_sq, 0.0))
            dist = math.sqrt(dist_sq)
            if dist < 0.001:
                return None

            if rel_x * rel_vel_y - rel_y * rel_vel_x >= 0.0:
                line_dir_x = (rel_x * leg - rel_y * combined_radius) / dist_sq
                line_dir_y = (rel_y * leg + rel_x * combined_radius) / dist_sq
            else:
                line_dir_x = -(rel_x * leg + rel_y * combined_radius) / dist_sq
                line_dir_y = -(rel_y * leg - rel_x * combined_radius) / dist_sq

            dot_rv_dir = rel_vel_x * line_dir_x + rel_vel_y * line_dir_y
            u_x = dot_rv_dir * line_dir_x - rel_vel_x
            u_y = dot_rv_dir * line_dir_y - rel_vel_y
    else:
        inv_dt = 1.0 / time_horizon
        w_x = rel_vel_x - rel_x * inv_dt
        w_y = rel_vel_y - rel_y * inv_dt
        w_len = math.sqrt(w_x * w_x + w_y * w_y)
        if w_len < 0.001:
            return None
        unit_w_x = w_x / w_len
        unit_w_y = w_y / w_len
        line_dir_x = unit_w_y
        line_dir_y = -unit_w_x
        u_x = (combined_radius * inv_dt - w_len) * unit_w_x
        u_y = (combined_radius * inv_dt - w_len) * unit_w_y

    pt_x = va_x + u_x * 0.5
    pt_y = va_y + u_y * 0.5
    return (pt_x, pt_y, line_dir_x, line_dir_y)


def _solve_lp_2d(lines, pref_vx, pref_vy, max_speed):
    result_x = pref_vx
    result_y = pref_vy

    for i, (pt_x, pt_y, dir_x, dir_y) in enumerate(lines):
        det = dir_x * (pt_y - result_y) - dir_y * (pt_x - result_x)
        if det >= 0.0:
            continue

        t_num = dir_x * (pt_y - pref_vy) - dir_y * (pt_x - pref_vx)
        t_min = -1e9
        t_max = 1e9

        for j in range(i):
            jpt_x, jpt_y, jdir_x, jdir_y = lines[j]
            denom = dir_x * jdir_y - dir_y * jdir_x
            numer = jdir_x * (pt_y - jpt_y) - jdir_y * (pt_x - jpt_x)

            if abs(denom) < 1e-10:
                if numer < 0.0:
                    return None
                continue

            t = numer / denom
            if denom > 0.0:
                t_min = max(t_min, t)
            else:
                t_max = min(t_max, t)

            if t_min > t_max:
                return None

        speed_denom = dir_x * dir_x + dir_y * dir_y
        if speed_denom < 1e-10:
            continue
        dp = (pref_vx - pt_x) * dir_x + (pref_vy - pt_y) * dir_y
        t_opt = dp / speed_denom

        disc = max_speed * max_speed * speed_denom - (dir_x * (pt_y) - dir_y * (pt_x)) ** 2
        if disc < 0.0:
            disc = 0.0
        sqrt_disc = math.sqrt(disc) / speed_denom
        speed_t_center = (dir_x * (-pt_x) + dir_y * (-pt_y)) / speed_denom
        t_speed_min = speed_t_center - sqrt_disc
        t_speed_max = speed_t_center + sqrt_disc
        t_min = max(t_min, t_speed_min)
        t_max = min(t_max, t_speed_max)

        if t_min > t_max:
            return None

        t = max(t_min, min(t_max, t_opt))
        result_x = pt_x + t * dir_x
        result_y = pt_y + t * dir_y

    mag_sq = result_x * result_x + result_y * result_y
    if mag_sq > max_speed * max_speed:
        mag = math.sqrt(mag_sq)
        result_x = result_x / mag * max_speed
        result_y = result_y / mag * max_speed

    return (result_x, result_y)


def _solve_lp_2d_safe(lines, pref_vx, pref_vy, max_speed):
    result = _solve_lp_2d(lines, pref_vx, pref_vy, max_speed)
    if result is not None:
        return result

    best_x = pref_vx
    best_y = pref_vy
    mag = math.sqrt(best_x * best_x + best_y * best_y)
    if mag > max_speed:
        best_x = best_x / mag * max_speed
        best_y = best_y / mag * max_speed

    min_penalty = float('inf')
    for pt_x, pt_y, dir_x, dir_y in lines:
        det = dir_x * (pt_y - best_y) - dir_y * (pt_x - best_x)
        if det < 0:
            penalty = -det
            if penalty < min_penalty:
                dp = (best_x - pt_x) * dir_x + (best_y - pt_y) * dir_y
                proj_x = pt_x + dp * dir_x
                proj_y = pt_y + dp * dir_y
                mag_p = math.sqrt(proj_x * proj_x + proj_y * proj_y)
                if mag_p > max_speed:
                    proj_x = proj_x / mag_p * max_speed
                    proj_y = proj_y / mag_p * max_speed
                best_x = proj_x
                best_y = proj_y
                min_penalty = penalty

    return (best_x, best_y)


def compute_rvo_velocities(store, active, dt, tmap):
    agent_radius = config.UNIT_COLLISION_RADIUS
    neighbor_dist = config.RVO_NEIGHBOR_DIST
    time_horizon = config.RVO_TIME_HORIZON
    max_neighbors = config.RVO_MAX_NEIGHBORS
    combined_radius = agent_radius * 2.0
    neighbor_dist_sq = neighbor_dist * neighbor_dist

    # Rebuild spatial hash for neighbor lookup (fresh per subsystem call).
    # sorted() on query results ensures deterministic tie-breaking at max_neighbors trim.
    tmap.spatial_hash.clear()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    preferred = _compute_preferred_velocities(store, active, dt)
    adjusted = {}

    current_vel = {}
    for uid in active:
        pv = preferred[uid]
        current_vel[uid] = (pv[0], pv[1])

    for uid in active:
        pref_vx, pref_vy, max_speed = preferred[uid]
        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]
        my_layer = store.data[uid, FIELD_LAYER]

        neighbors = []
        for other in sorted(tmap.spatial_hash.query(px, py, neighbor_dist)):
            if other == uid:
                continue
            if store.data[other, FIELD_LAYER] != my_layer:  # keep layer filter
                continue
            ox = store.data[other, FIELD_X]
            oy = store.data[other, FIELD_Y]
            dx = ox - px
            dy = oy - py
            d_sq = dx * dx + dy * dy
            if d_sq < neighbor_dist_sq:
                neighbors.append((other, d_sq))

        neighbors.sort(key=lambda x: x[1])
        if len(neighbors) > max_neighbors:
            neighbors = neighbors[:max_neighbors]

        if not neighbors:
            adjusted[uid] = (pref_vx, pref_vy)
            continue

        orca_lines = []
        va_x, va_y = current_vel[uid]
        for other, _ in neighbors:
            ob_x = store.data[other, FIELD_X]
            ob_y = store.data[other, FIELD_Y]
            vb_x, vb_y = current_vel[other]

            line = _compute_orca_line(px, py, ob_x, ob_y, va_x, va_y, vb_x, vb_y, combined_radius, time_horizon)
            if line is not None:
                orca_lines.append(line)

        if not orca_lines:
            adjusted[uid] = (pref_vx, pref_vy)
            continue

        result = _solve_lp_2d_safe(orca_lines, pref_vx, pref_vy, max_speed)
        adjusted[uid] = result

    return adjusted


def update_movement(store: UnitStore, tactical_map, dt: float):
    obstacle_range = config.STEERING_OBSTACLE_AVOIDANCE_RANGE
    collision_radius = config.UNIT_COLLISION_RADIUS

    navmesh = _ensure_navmesh(tactical_map)
    path_cache = _ensure_path_cache(tactical_map)

    active = store.active_ids()

    for uid in active:
        if not store.has_move_target[uid]:
            continue
        if is_immobile(store, uid):
            continue
        if navmesh is not None and navmesh.has_obstacles and uid not in store.waypoints:
            final_tx = store.target_x[uid]
            final_ty = store.target_y[uid]
            path = path_cache.get(navmesh, store.data[uid, FIELD_X], store.data[uid, FIELD_Y], final_tx, final_ty)
            if path:
                store.waypoints[uid] = path

    _update_attack_move_state(store, active)
    rvo_velocities = compute_rvo_velocities(store, active, dt, tactical_map)

    for uid in active:
        if is_immobile(store, uid):
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]

        # Destination-arrival check: only for units that are actually navigating
        # (has a move target and is not held by attack_move engagement)
        held = store.attack_moving[uid] and store.auto_engage_target[uid] >= 0 and store.alive[store.auto_engage_target[uid]]
        if not held and store.has_move_target[uid]:
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

        vx, vy = rvo_velocities.get(uid, (0.0, 0.0))

        if tactical_map is not None:
            dir_x = vx
            dir_y = vy
            mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
            if mag > 0.001:
                probe_x = px + (dir_x / mag) * obstacle_range
                probe_y = py + (dir_y / mag) * obstacle_range
                if tactical_map.in_bounds(probe_x, probe_y):
                    density = tactical_map.obstacle_density(probe_x, probe_y)
                    if density > 0.3:
                        vx -= (dir_x / mag) * density * mag
                        vy -= (dir_y / mag) * density * mag

        new_x = px + vx * dt
        new_y = py + vy * dt

        if tactical_map is not None:
            new_x = max(0.0, min(tactical_map.width, new_x))
            new_y = max(0.0, min(tactical_map.height, new_y))

        store.data[uid, FIELD_X] = new_x
        store.data[uid, FIELD_Y] = new_y


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
