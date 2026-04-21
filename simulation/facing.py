import math
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_FACING_RAD, FIELD_ATTACK_RANGE,
    CATEGORY_STRIKE, CATEGORY_LINE, CATEGORY_SIEGE,
)

_ROTATION_SPEED = {
    CATEGORY_STRIKE: config.FACING_ROTATION_SPEED_STRIKE,
    CATEGORY_LINE: config.FACING_ROTATION_SPEED_LINE,
    CATEGORY_SIEGE: config.FACING_ROTATION_SPEED_SIEGE,
}

TWO_PI = 2.0 * math.pi


def _wrap_angle(a):
    a = a % TWO_PI
    if a < 0:
        a += TWO_PI
    return a


def _shortest_arc(current, target):
    diff = target - current
    diff = (diff + math.pi) % TWO_PI - math.pi
    return diff


def update_facing(store: UnitStore, dt: float):
    for uid in range(store.count):
        if not store.alive[uid]:
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]
        current = store.data[uid, FIELD_FACING_RAD]

        target_angle = None

        tgt = store.auto_engage_target[uid]
        if tgt >= 0 and store.alive[tgt]:
            tx = store.data[tgt, FIELD_X]
            ty = store.data[tgt, FIELD_Y]
            dx = tx - px
            dy = ty - py
            dist_sq = dx * dx + dy * dy
            atk_range = store.data[uid, FIELD_ATTACK_RANGE]
            if dist_sq <= atk_range * atk_range * 1.5 * 1.5:
                target_angle = math.atan2(dy, dx)

        if target_angle is None and store.has_move_target[uid]:
            tx = store.target_x[uid]
            ty = store.target_y[uid]
            dx = tx - px
            dy = ty - py
            if dx * dx + dy * dy > 1.0:
                target_angle = math.atan2(dy, dx)

        if target_angle is None:
            continue

        target_angle = _wrap_angle(target_angle)
        arc = _shortest_arc(current, target_angle)

        max_step = _ROTATION_SPEED.get(int(store.category[uid]), config.FACING_ROTATION_SPEED_LINE) * dt
        if abs(arc) <= max_step:
            store.data[uid, FIELD_FACING_RAD] = target_angle
        else:
            step = max_step if arc > 0 else -max_step
            store.data[uid, FIELD_FACING_RAD] = _wrap_angle(current + step)
