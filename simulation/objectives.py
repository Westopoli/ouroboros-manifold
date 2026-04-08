import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP
from power_rating import compute_power_rating
from mission_contracts import MissionResult


class Objective:
    def __init__(self, obj_id, obj_type, weight, params, is_primary=False):
        self.id = obj_id
        self.type = obj_type
        self.weight = weight
        self.params = params
        self.is_primary = is_primary
        self.completion = 0.0
        self.failed = False
        self._hold_ticks = 0


def update_objectives(objectives, store, player_faction, tick):
    for obj in objectives:
        if obj.type == "hold_zone":
            _update_hold_zone(obj, store, player_faction)
        elif obj.type == "destroy_targets":
            _update_destroy_targets(obj, store)
        elif obj.type == "escort_to_extraction":
            _update_escort(obj, store)
        elif obj.type == "survive_duration":
            _update_survive(obj, store, player_faction, tick)
        elif obj.type == "eliminate_force":
            _update_eliminate(obj, store, player_faction)


def _update_hold_zone(obj, store, player_faction):
    cx = obj.params["zone_x"]
    cy = obj.params["zone_y"]
    radius = obj.params["zone_radius"]
    total_ticks = obj.params["hold_duration_ticks"]
    r_sq = radius * radius

    player_present = False
    enemy_present = False
    for uid in store.active_ids():
        dx = store.data[uid, FIELD_X] - cx
        dy = store.data[uid, FIELD_Y] - cy
        if dx * dx + dy * dy <= r_sq:
            if store.faction[uid] == player_faction:
                player_present = True
            else:
                enemy_present = True

    if player_present and not enemy_present:
        obj._hold_ticks += 1

    obj.completion = min(1.0, obj._hold_ticks / total_ticks) if total_ticks > 0 else 0.0


def _update_destroy_targets(obj, store):
    target_uids = obj.params["target_uids"]
    if not target_uids:
        obj.completion = 1.0
        return
    destroyed = sum(1 for uid in target_uids if not store.alive[uid])
    obj.completion = destroyed / len(target_uids)


def _update_escort(obj, store):
    escort_uids = obj.params["escort_uids"]
    ex = obj.params["extraction_x"]
    ey = obj.params["extraction_y"]
    radius = obj.params.get("extraction_radius", 100)
    r_sq = radius * radius

    if not escort_uids:
        obj.completion = 0.0
        return

    reached = 0
    for uid in escort_uids:
        if not store.alive[uid]:
            continue
        dx = store.data[uid, FIELD_X] - ex
        dy = store.data[uid, FIELD_Y] - ey
        if dx * dx + dy * dy <= r_sq:
            reached += 1

    obj.completion = reached / len(escort_uids)


def _update_survive(obj, store, player_faction, tick):
    duration_ticks = obj.params["duration_ticks"]
    alive = len(store.active_ids_for_faction(player_faction))

    if alive == 0:
        obj.failed = True
        return

    obj.completion = min(1.0, tick / duration_ticks) if duration_ticks > 0 else 0.0


def _update_eliminate(obj, store, player_faction):
    enemy_faction = obj.params["enemy_faction"]
    initial_hp = obj.params["initial_enemy_hp"]

    if initial_hp <= 0:
        obj.completion = 1.0
        return

    current_hp = 0.0
    for uid in store.active_ids_for_faction(enemy_faction):
        current_hp += store.data[uid, FIELD_HP]

    destroyed_hp = initial_hp - current_hp
    obj.completion = min(1.0, max(0.0, destroyed_hp / initial_hp))


def check_terminal(objectives, store, player_faction, tick, time_limit_ticks):
    all_primary_resolved = True
    for obj in objectives:
        if not obj.is_primary:
            continue
        if obj.completion >= 1.0 or obj.failed:
            continue
        all_primary_resolved = False

    if all_primary_resolved:
        has_primary = any(o.is_primary for o in objectives)
        if has_primary:
            return "objectives_resolved"

    if time_limit_ticks > 0 and tick >= time_limit_ticks:
        return "time_expired"

    if len(store.active_ids_for_faction(player_faction)) == 0:
        return "force_eliminated"

    return None


def compute_scores(objectives):
    objective_score = 0.0
    for obj in objectives:
        score = 0.0 if obj.failed else obj.completion
        objective_score += score * obj.weight
    return objective_score


def compute_retention(store, player_faction, initial_power):
    if initial_power <= 0:
        return 0.0
    current_power = 0.0
    for uid in store.active_ids_for_faction(player_faction):
        stats = config.UNIT_STATS.get(store.unit_type[uid])
        if stats:
            s = dict(stats)
            s["unit_type"] = store.unit_type[uid]
            hp_frac = store.data[uid, FIELD_HP] / store.data[uid, FIELD_MAX_HP]
            s["hp"] = stats["hp"] * hp_frac
            current_power += compute_power_rating(s)
    return min(1.0, current_power / initial_power)


def classify_outcome(final_score, archetype):
    thresholds = config.OUTCOME_THRESHOLDS.get(archetype, [0.20, 0.40, 0.60, 0.80])
    bands = ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]

    for i, t in enumerate(thresholds):
        if final_score < t:
            return bands[i]
    return bands[-1]


def build_mission_result(mission_id, objectives, store, player_faction,
                         initial_power, archetype, tick, commander_uid=None):
    objective_score = compute_scores(objectives)
    retention = compute_retention(store, player_faction, initial_power)

    final_score = (objective_score * config.OUTCOME_WEIGHT_OBJECTIVE +
                   retention * config.OUTCOME_WEIGHT_RETENTION)

    band = classify_outcome(final_score, archetype)

    per_objective = []
    for obj in objectives:
        per_objective.append({
            "id": obj.id,
            "type": obj.type,
            "completion": obj.completion,
            "weight": obj.weight,
            "is_primary": obj.is_primary,
            "failed": obj.failed,
        })

    commander_survived = True
    if commander_uid is not None:
        commander_survived = bool(store.alive[commander_uid])

    return MissionResult(
        mission_id=mission_id,
        outcome_band=band,
        objective_score=objective_score,
        force_retention=retention,
        per_objective=per_objective,
        commander_survived=commander_survived,
        ticks_elapsed=tick,
    )
