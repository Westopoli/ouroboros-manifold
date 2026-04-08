import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_SENSOR_RADIUS


def activate_pulse(store, uid):
    if store.pulse_cooldown[uid] > 0:
        return False
    store.pulse_remaining[uid] = config.PULSE_REVEAL_TICKS
    store.pulse_cooldown[uid] = config.PULSE_COOLDOWN_TICKS
    return True


def update_fog_timers(store):
    for uid in store.active_ids():
        if store.pulse_remaining[uid] > 0:
            store.pulse_remaining[uid] -= 1
        if store.pulse_cooldown[uid] > 0:
            store.pulse_cooldown[uid] -= 1


def _get_cone_factors(at_vantage):
    base = [1.0, config.CONE_LAYER_1_FACTOR, config.CONE_LAYER_2_FACTOR]
    if not at_vantage:
        return base

    factors = [min(f * config.VANTAGE_CONE_MULTIPLIER, 1.0) for f in base]
    last_nonzero = config.CONE_LAYER_2_FACTOR
    for _ in range(config.VANTAGE_EXTRA_LAYER):
        factors.append(min(last_nonzero * config.VANTAGE_CONE_MULTIPLIER, 1.0))
    return factors


def _is_at_vantage(x, y, tactical_map):
    if tactical_map is None:
        return False
    for node in tactical_map.get_spine_nodes_by_type("vantage_point"):
        vr = node.properties.get("radius", 100)
        dx = x - node.position[0]
        dy = y - node.position[1]
        if dx * dx + dy * dy <= vr * vr:
            return True
    return False


def compute_visibility(store, tactical_map):
    active = store.active_ids()
    vantage_nodes = []
    if tactical_map is not None:
        vantage_nodes = tactical_map.get_spine_nodes_by_type("vantage_point")

    visibility = {}

    for uid in active:
        visible = set()
        mx = store.data[uid, FIELD_X]
        my = store.data[uid, FIELD_Y]
        my_layer = int(store.data[uid, FIELD_LAYER])
        my_faction = store.faction[uid]
        base_radius = store.data[uid, FIELD_SENSOR_RADIUS]

        interference = 0.0
        if tactical_map is not None:
            interference = tactical_map.sensor_interference(mx, my)
        effective_radius = base_radius * (1.0 - interference)

        at_vantage = _is_at_vantage(mx, my, tactical_map)
        cone_factors = _get_cone_factors(at_vantage)

        pulse_active = store.pulse_remaining[uid] > 0

        for other in active:
            if store.faction[other] == my_faction:
                continue

            ox = store.data[other, FIELD_X]
            oy = store.data[other, FIELD_Y]
            dx = ox - mx
            dy = oy - my
            dist = math.sqrt(dx * dx + dy * dy)

            if pulse_active and dist <= config.PULSE_RADIUS:
                visible.add(other)
                continue

            other_layer = int(store.data[other, FIELD_LAYER])
            layer_diff = abs(other_layer - my_layer)

            if layer_diff < len(cone_factors):
                factor = cone_factors[layer_diff]
            else:
                factor = 0.0

            if factor <= 0.0:
                continue

            detection_radius = effective_radius * factor
            if dist <= detection_radius:
                visible.add(other)

        visibility[uid] = visible

    return visibility
