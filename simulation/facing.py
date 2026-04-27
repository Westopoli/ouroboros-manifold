import math
import numpy as np
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_FACING_RAD, FIELD_ATTACK_RANGE,
    CATEGORY_STRIKE, CATEGORY_LINE, CATEGORY_SIEGE, MAX_UNITS,
)

_ROTATION_SPEED = {
    CATEGORY_STRIKE: config.FACING_ROTATION_SPEED_STRIKE,
    CATEGORY_LINE: config.FACING_ROTATION_SPEED_LINE,
    CATEGORY_SIEGE: config.FACING_ROTATION_SPEED_SIEGE,
}

TWO_PI = 2.0 * math.pi
_VELOCITY_FACING_THRESHOLD_SQ = 1.0

_prev_x = np.zeros(MAX_UNITS, dtype=np.float64)
_prev_y = np.zeros(MAX_UNITS, dtype=np.float64)
_prev_initialized = False


def _wrap_angle(a):
    a = a % TWO_PI
    if a < 0:
        a += TWO_PI
    return a


def _shortest_arc(current, target):
    diff = target - current
    diff = (diff + math.pi) % TWO_PI - math.pi
    return diff


_facing_log_counter = 0

def update_facing(store: UnitStore, dt: float):
    global _facing_log_counter, _prev_initialized
    _facing_log_counter += 1
    log_this_tick = (_facing_log_counter % 60 == 0)

    if not _prev_initialized:
        _prev_x[:store.count] = store.data[:store.count, FIELD_X]
        _prev_y[:store.count] = store.data[:store.count, FIELD_Y]
        _prev_initialized = True

    for uid in range(store.count):
        if not store.alive[uid]:
            continue

        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]
        current = store.data[uid, FIELD_FACING_RAD]

        target_angle = None
        reason = "none"

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
                reason = f"engage tgt={tgt}"

        if target_angle is None and store.has_move_target[uid]:
            tx = store.target_x[uid]
            ty = store.target_y[uid]
            dx = tx - px
            dy = ty - py
            if dx * dx + dy * dy > 1.0:
                target_angle = math.atan2(dy, dx)
                reason = "move"

        if target_angle is None:
            dx = px - _prev_x[uid]
            dy = py - _prev_y[uid]
            if dx * dx + dy * dy > _VELOCITY_FACING_THRESHOLD_SQ:
                target_angle = math.atan2(dy, dx)
                reason = "velocity"

        if log_this_tick and uid < 4:
            print(f"[FACING] uid={uid} current={current:.3f} target={target_angle if target_angle is not None else 'None'} reason={reason} has_move={store.has_move_target[uid]} engage_tgt={store.auto_engage_target[uid]}")

        if target_angle is None:
            _prev_x[uid] = px
            _prev_y[uid] = py
            continue

        target_angle = _wrap_angle(target_angle)
        arc = _shortest_arc(current, target_angle)

        max_step = _ROTATION_SPEED.get(int(store.category[uid]), config.FACING_ROTATION_SPEED_LINE) * dt
        if abs(arc) <= max_step:
            store.data[uid, FIELD_FACING_RAD] = target_angle
        else:
            step = max_step if arc > 0 else -max_step
            store.data[uid, FIELD_FACING_RAD] = _wrap_angle(current + step)

        _prev_x[uid] = px
        _prev_y[uid] = py
