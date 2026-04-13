import json
import config
from unit import FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_LAYER, FIELD_ABILITY_ACTIVE


def config_snapshot():
    return {
        "UNIT_COLLISION_RADIUS": config.UNIT_COLLISION_RADIUS,
        "STEERING_SEPARATION_RADIUS": config.STEERING_SEPARATION_RADIUS,
        "HARD_COLLISION_ENABLED": config.HARD_COLLISION_ENABLED,
        "COLLISION_RESOLUTION_ITERATIONS": config.COLLISION_RESOLUTION_ITERATIONS,
    }


class SimLogger:
    def __init__(self, path, scenario_name, tactical_map, factions, cfg_snapshot):
        self._f = open(path, "w")
        header = {
            "type": "header",
            "version": 1,
            "scenario": scenario_name,
            "map": {
                "width": tactical_map.width,
                "height": tactical_map.height,
                "name": getattr(tactical_map, "name", "unknown"),
            },
            "factions": {str(fid): {"name": info[0], "color": info[1]} for fid, info in factions.items()},
            "tick_duration_seconds": config.TACTICAL_TICK_DURATION,
            "config": cfg_snapshot,
        }
        self._f.write(json.dumps(header) + "\n")

    def log_tick(self, tick, store, deaths, subsystem_ms):
        units = []
        for uid in range(store.count):
            if not store.alive[uid]:
                continue
            units.append({
                "uid": uid,
                "faction": int(store.faction[uid]),
                "type": store.unit_type[uid],
                "x": float(store.data[uid, FIELD_X]),
                "y": float(store.data[uid, FIELD_Y]),
                "vx": 0.0,
                "vy": 0.0,
                "hp": int(store.data[uid, FIELD_HP]),
                "max_hp": int(store.data[uid, FIELD_MAX_HP]),
                "target_uid": int(store.auto_engage_target[uid]),
                "ability_state": int(store.data[uid, FIELD_ABILITY_ACTIVE]),
                "layer": int(store.data[uid, FIELD_LAYER]),
            })
        line = {
            "type": "tick",
            "tick": tick,
            "units": units,
            "deaths_this_tick": [int(uid) for uid in deaths],
            "subsystem_ms": {k: round(v * 1000.0, 3) for k, v in subsystem_ms.items()},
        }
        self._f.write(json.dumps(line) + "\n")

    def close(self):
        self._f.flush()
        self._f.close()
