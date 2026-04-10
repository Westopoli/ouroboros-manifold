import numpy as np
import config


MAX_UNITS = 512

FIELD_X = 0
FIELD_Y = 1
FIELD_LAYER = 2
FIELD_HP = 3
FIELD_MAX_HP = 4
FIELD_BASE_DAMAGE = 5
FIELD_ATTACK_INTERVAL = 6
FIELD_ATTACK_RANGE = 7
FIELD_SENSOR_RADIUS = 8
FIELD_SPEED = 9
FIELD_LAYER_TRANSITION_TIME = 10
FIELD_AOE_RADIUS = 11
FIELD_ATTACK_TIMER = 12
FIELD_ABILITY_COOLDOWN = 13
FIELD_ABILITY_ACTIVE = 14
FIELD_ABILITY_DURATION = 15
NUM_FIELDS = 16

CATEGORY_STRIKE = 0
CATEGORY_LINE = 1
CATEGORY_SIEGE = 2
CATEGORY_MAP = {"Strike": CATEGORY_STRIKE, "Line": CATEGORY_LINE, "Siege": CATEGORY_SIEGE}
CATEGORY_NAMES = {v: k for k, v in CATEGORY_MAP.items()}


class UnitStore:
    def __init__(self):
        self.data = np.zeros((MAX_UNITS, NUM_FIELDS), dtype=np.float64)
        self.faction = np.full(MAX_UNITS, -1, dtype=np.int32)
        self.category = np.full(MAX_UNITS, -1, dtype=np.int8)
        self.alive = np.zeros(MAX_UNITS, dtype=np.bool_)
        self.unit_type = [""] * MAX_UNITS
        self.count = 0

        self.target_x = np.zeros(MAX_UNITS, dtype=np.float64)
        self.target_y = np.zeros(MAX_UNITS, dtype=np.float64)
        self.has_move_target = np.zeros(MAX_UNITS, dtype=np.bool_)
        self.effective_speed = np.zeros(MAX_UNITS, dtype=np.float64)
        self.auto_engage_target = np.full(MAX_UNITS, -1, dtype=np.int32)
        self.ability_target_x = np.zeros(MAX_UNITS, dtype=np.float64)
        self.ability_target_y = np.zeros(MAX_UNITS, dtype=np.float64)
        self.waypoints = {}
        self.pulse_remaining = np.zeros(MAX_UNITS, dtype=np.int32)
        self.pulse_cooldown = np.zeros(MAX_UNITS, dtype=np.int32)

        self.attack_moving = np.zeros(MAX_UNITS, dtype=np.bool_)
        self.engage_anchor_x = np.zeros(MAX_UNITS, dtype=np.float64)
        self.engage_anchor_y = np.zeros(MAX_UNITS, dtype=np.float64)
        self.engage_anchor_set = np.zeros(MAX_UNITS, dtype=np.bool_)

    def spawn(self, unit_type, faction_id, x, y, layer=0, stats=None):
        if self.count >= MAX_UNITS:
            return -1
        uid = self.count
        self.count += 1

        if stats is None:
            stats = config.UNIT_STATS[unit_type]

        self.data[uid, FIELD_X] = x
        self.data[uid, FIELD_Y] = y
        self.data[uid, FIELD_LAYER] = layer
        self.data[uid, FIELD_HP] = stats["hp"]
        self.data[uid, FIELD_MAX_HP] = stats["hp"]
        self.data[uid, FIELD_BASE_DAMAGE] = stats["base_damage"]
        self.data[uid, FIELD_ATTACK_INTERVAL] = stats["attack_interval"]
        self.data[uid, FIELD_ATTACK_RANGE] = stats["attack_range"]
        self.data[uid, FIELD_SENSOR_RADIUS] = stats["sensor_radius"]
        self.data[uid, FIELD_SPEED] = stats["speed"]
        self.data[uid, FIELD_LAYER_TRANSITION_TIME] = stats["layer_transition_time"]
        self.data[uid, FIELD_AOE_RADIUS] = stats.get("aoe_radius", 0)
        self.data[uid, FIELD_ATTACK_TIMER] = 0.0
        self.data[uid, FIELD_ABILITY_COOLDOWN] = 0.0
        self.data[uid, FIELD_ABILITY_ACTIVE] = 0.0
        self.data[uid, FIELD_ABILITY_DURATION] = 0.0

        self.faction[uid] = faction_id
        self.category[uid] = CATEGORY_MAP[stats["category"]]
        self.alive[uid] = True
        self.unit_type[uid] = unit_type
        self.has_move_target[uid] = False

        return uid

    def kill(self, uid):
        self.alive[uid] = False

    def get_position(self, uid):
        return (self.data[uid, FIELD_X], self.data[uid, FIELD_Y])

    def get_positions_dict(self):
        result = {}
        for uid in range(self.count):
            if self.alive[uid]:
                result[uid] = (self.data[uid, FIELD_X], self.data[uid, FIELD_Y])
        return result

    def set_move_target(self, uid, tx, ty):
        self.target_x[uid] = tx
        self.target_y[uid] = ty
        self.has_move_target[uid] = True
        self.waypoints.pop(uid, None)

    def clear_move_target(self, uid):
        self.has_move_target[uid] = False

    def set_effective_speed(self, uid, speed):
        self.effective_speed[uid] = speed

    def clear_effective_speed(self, uid):
        self.effective_speed[uid] = 0.0

    def active_ids(self):
        return [uid for uid in range(self.count) if self.alive[uid]]

    def active_ids_for_faction(self, faction_id):
        return [uid for uid in range(self.count) if self.alive[uid] and self.faction[uid] == faction_id]
