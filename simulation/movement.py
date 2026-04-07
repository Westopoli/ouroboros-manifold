import math
import numpy as np
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED,
    FIELD_ABILITY_ACTIVE, FIELD_LAYER,
)


def _distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def update_movement(store: UnitStore, tactical_map, dt: float):
    sep_radius = config.STEERING_SEPARATION_RADIUS
    sep_radius_sq = sep_radius * sep_radius
    obstacle_range = config.STEERING_OBSTACLE_AVOIDANCE_RANGE
    collision_radius = config.UNIT_COLLISION_RADIUS

    active = store.active_ids()
    positions = {}
    for uid in active:
        positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    for uid in active:
        if not store.has_move_target[uid]:
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]
        tx = store.target_x[uid]
        ty = store.target_y[uid]

        speed = store.data[uid, FIELD_SPEED]
        # Fortify speed reduction check (ability_active flag encodes ability-specific state)
        # Full ability integration happens in later checkpoints

        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx * dx + dy * dy)

        arrival_threshold = collision_radius
        if dist < arrival_threshold:
            store.has_move_target[uid] = False
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

        steer_x = seek_x + sep_x * 0.8 + obs_x * 1.0
        steer_y = seek_y + sep_y * 0.8 + obs_y * 1.0
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
