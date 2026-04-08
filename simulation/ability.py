import math
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_SPEED,
    FIELD_BASE_DAMAGE, FIELD_ATTACK_RANGE, FIELD_LAYER,
    FIELD_ABILITY_COOLDOWN, FIELD_ABILITY_ACTIVE, FIELD_ABILITY_DURATION,
    CATEGORY_STRIKE,
)

ABILITY_INACTIVE = 0.0
ABILITY_ACTIVE = 1.0
ABILITY_WINDUP = 2.0
ABILITY_TELEGRAPH = 3.0

ABILITY_MAP = {
    "Raider": "surge",
    "Interceptor": "intercept",
    "Vanguard": "brace",
    "Warden": "rally",
    "Bombard": "barrage",
    "Bastion": "fortify",
}


def activate_ability(store, uid):
    if not store.alive[uid]:
        return False
    if store.data[uid, FIELD_ABILITY_COOLDOWN] > 0:
        return False

    ut = store.unit_type[uid]
    ability = ABILITY_MAP.get(ut)
    if ability is None:
        return False

    if ability == "surge":
        return _activate_surge(store, uid)
    elif ability == "brace":
        return _activate_brace(store, uid)
    elif ability == "rally":
        return _activate_rally(store, uid)
    elif ability == "barrage":
        return _activate_barrage(store, uid)
    elif ability == "fortify":
        return _activate_fortify(store, uid)
    return False


def _activate_surge(store, uid):
    store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_ACTIVE
    store.data[uid, FIELD_ABILITY_DURATION] = config.SURGE_DURATION_TICKS
    store.data[uid, FIELD_ABILITY_COOLDOWN] = config.SURGE_COOLDOWN_TICKS
    return True


def _activate_brace(store, uid):
    if store.data[uid, FIELD_ABILITY_ACTIVE] == ABILITY_ACTIVE:
        store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_WINDUP
        store.data[uid, FIELD_ABILITY_DURATION] = config.BRACE_WINDUP_TICKS
        return True
    if store.data[uid, FIELD_ABILITY_ACTIVE] != ABILITY_INACTIVE:
        return False
    store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_WINDUP
    store.data[uid, FIELD_ABILITY_DURATION] = config.BRACE_WINDUP_TICKS
    store.data[uid, FIELD_ABILITY_COOLDOWN] = config.BRACE_COOLDOWN_TICKS
    return True


def _activate_rally(store, uid):
    rx, ry = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
    my_faction = store.faction[uid]
    r_sq = config.RALLY_RADIUS * config.RALLY_RADIUS

    for other in store.active_ids():
        if store.faction[other] != my_faction:
            continue
        dx = store.data[other, FIELD_X] - rx
        dy = store.data[other, FIELD_Y] - ry
        if dx * dx + dy * dy <= r_sq:
            store.data[other, FIELD_HP] = min(
                store.data[other, FIELD_HP] + config.RALLY_HEAL_AMOUNT,
                store.data[other, FIELD_MAX_HP],
            )

    store.data[uid, FIELD_ABILITY_COOLDOWN] = config.RALLY_COOLDOWN_TICKS
    return True


def _activate_barrage(store, uid):
    target = store.auto_engage_target[uid]
    if target < 0 or not store.alive[target]:
        return False
    store.ability_target_x[uid] = store.data[target, FIELD_X]
    store.ability_target_y[uid] = store.data[target, FIELD_Y]
    store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_TELEGRAPH
    store.data[uid, FIELD_ABILITY_DURATION] = config.BARRAGE_TELEGRAPH_TICKS
    store.data[uid, FIELD_ABILITY_COOLDOWN] = config.BARRAGE_COOLDOWN_TICKS
    return True


def _activate_fortify(store, uid):
    store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_ACTIVE
    store.data[uid, FIELD_ABILITY_DURATION] = config.FORTIFY_DURATION_TICKS
    store.data[uid, FIELD_ABILITY_COOLDOWN] = config.FORTIFY_COOLDOWN_TICKS
    return True


def update_abilities(store, dt):
    barrage_events = []

    for uid in store.active_ids():
        if store.data[uid, FIELD_ABILITY_COOLDOWN] > 0:
            store.data[uid, FIELD_ABILITY_COOLDOWN] -= 1

        state = store.data[uid, FIELD_ABILITY_ACTIVE]
        if state == ABILITY_INACTIVE:
            _check_intercept(store, uid)
            continue

        ut = store.unit_type[uid]
        ability = ABILITY_MAP.get(ut)

        if ability == "surge":
            store.data[uid, FIELD_ABILITY_DURATION] -= 1
            if store.data[uid, FIELD_ABILITY_DURATION] <= 0:
                store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_INACTIVE

        elif ability == "brace":
            if state == ABILITY_WINDUP:
                store.data[uid, FIELD_ABILITY_DURATION] -= 1
                if store.data[uid, FIELD_ABILITY_DURATION] <= 0:
                    if store.data[uid, FIELD_ABILITY_COOLDOWN] > 0:
                        store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_ACTIVE
                    else:
                        store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_INACTIVE

        elif ability == "barrage":
            if state == ABILITY_TELEGRAPH:
                store.data[uid, FIELD_ABILITY_DURATION] -= 1
                if store.data[uid, FIELD_ABILITY_DURATION] <= 0:
                    barrage_events.append(uid)
                    store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_INACTIVE

        elif ability == "fortify":
            store.data[uid, FIELD_ABILITY_DURATION] -= 1
            if store.data[uid, FIELD_ABILITY_DURATION] <= 0:
                store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_INACTIVE

        elif ability == "intercept":
            store.data[uid, FIELD_ABILITY_DURATION] -= 1
            if store.data[uid, FIELD_ABILITY_DURATION] <= 0:
                store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_INACTIVE

    _apply_warden_aura_healing(store)

    return barrage_events


def _check_intercept(store, uid):
    if store.unit_type[uid] != "Interceptor":
        return
    if store.data[uid, FIELD_ABILITY_COOLDOWN] > 0:
        return

    mx, my = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
    my_faction = store.faction[uid]
    my_layer = store.data[uid, FIELD_LAYER]
    detect_r_sq = config.INTERCEPT_DETECTION_RADIUS ** 2

    for other in store.active_ids():
        if store.faction[other] == my_faction:
            continue
        if store.data[other, FIELD_LAYER] != my_layer:
            continue
        if store.category[other] != CATEGORY_STRIKE:
            continue
        dx = store.data[other, FIELD_X] - mx
        dy = store.data[other, FIELD_Y] - my
        if dx * dx + dy * dy <= detect_r_sq:
            store.data[uid, FIELD_ABILITY_ACTIVE] = ABILITY_ACTIVE
            store.data[uid, FIELD_ABILITY_DURATION] = 1
            store.data[uid, FIELD_ABILITY_COOLDOWN] = config.INTERCEPT_COOLDOWN_TICKS
            store.auto_engage_target[uid] = other
            return


def _apply_warden_aura_healing(store):
    wardens = [uid for uid in store.active_ids() if store.unit_type[uid] == "Warden"]
    if not wardens:
        return

    aura_r_sq = config.WARDEN_AURA_RADIUS ** 2
    for uid in store.active_ids():
        for warden in wardens:
            if store.faction[warden] != store.faction[uid]:
                continue
            dx = store.data[uid, FIELD_X] - store.data[warden, FIELD_X]
            dy = store.data[uid, FIELD_Y] - store.data[warden, FIELD_Y]
            if dx * dx + dy * dy <= aura_r_sq:
                store.data[uid, FIELD_HP] = min(
                    store.data[uid, FIELD_HP] + config.WARDEN_AURA_REPAIR_RATE,
                    store.data[uid, FIELD_MAX_HP],
                )
                break


def resolve_barrage(store, barrage_events):
    from unit import CATEGORY_NAMES
    deaths = []
    kill_sources = {}

    for uid in barrage_events:
        if not store.alive[uid]:
            continue
        tx = store.ability_target_x[uid]
        ty = store.ability_target_y[uid]
        attacker_faction = store.faction[uid]
        attacker_layer = store.data[uid, FIELD_LAYER]
        attacker_cat = CATEGORY_NAMES[store.category[uid]]
        base_dmg = store.data[uid, FIELD_BASE_DAMAGE] * config.BARRAGE_DAMAGE_MULTIPLIER
        r_sq = config.BARRAGE_RADIUS ** 2

        for target in store.active_ids():
            if store.faction[target] == attacker_faction:
                continue
            if store.data[target, FIELD_LAYER] != attacker_layer:
                continue
            dx = store.data[target, FIELD_X] - tx
            dy = store.data[target, FIELD_Y] - ty
            if dx * dx + dy * dy <= r_sq:
                target_cat = CATEGORY_NAMES[store.category[target]]
                mult = config.CATEGORY_MULTIPLIER[attacker_cat][target_cat]
                dmg = base_dmg * mult
                store.data[target, FIELD_HP] -= dmg
                if store.data[target, FIELD_HP] <= 0 and store.alive[target]:
                    deaths.append(target)
                    kill_sources[target] = uid

    for dead_uid in deaths:
        store.kill(dead_uid)

    return deaths, kill_sources


def get_damage_output_multiplier(store, uid):
    ut = store.unit_type[uid]
    state = store.data[uid, FIELD_ABILITY_ACTIVE]

    if ut == "Raider" and state == ABILITY_ACTIVE:
        return config.SURGE_DAMAGE_MULTIPLIER

    if ut == "Interceptor" and state == ABILITY_ACTIVE:
        return config.INTERCEPT_DAMAGE_MULTIPLIER

    if ut == "Vanguard" and state == ABILITY_ACTIVE:
        return config.BRACE_DAMAGE_MULTIPLIER

    return 1.0


def get_damage_reduction(store, target_uid):
    reduction = 0.0

    if store.unit_type[target_uid] == "Vanguard":
        if store.data[target_uid, FIELD_ABILITY_ACTIVE] == ABILITY_ACTIVE:
            reduction += config.BRACE_DAMAGE_REDUCTION

    tx, ty = store.data[target_uid, FIELD_X], store.data[target_uid, FIELD_Y]
    my_faction = store.faction[target_uid]

    for uid in store.active_ids():
        if store.faction[uid] != my_faction:
            continue

        if store.unit_type[uid] == "Warden":
            dx = tx - store.data[uid, FIELD_X]
            dy = ty - store.data[uid, FIELD_Y]
            if dx * dx + dy * dy <= config.WARDEN_AURA_RADIUS ** 2:
                reduction += config.WARDEN_AURA_DAMAGE_REDUCTION
                break

    for uid in store.active_ids():
        if store.faction[uid] != my_faction:
            continue
        if store.unit_type[uid] != "Bastion":
            continue
        if store.data[uid, FIELD_ABILITY_ACTIVE] != ABILITY_ACTIVE:
            continue
        dx = tx - store.data[uid, FIELD_X]
        dy = ty - store.data[uid, FIELD_Y]
        if dx * dx + dy * dy <= config.FORTIFY_RADIUS ** 2:
            reduction += config.FORTIFY_DAMAGE_REDUCTION
            break

    return min(reduction, 0.90)


def get_speed_multiplier(store, uid):
    ut = store.unit_type[uid]
    state = store.data[uid, FIELD_ABILITY_ACTIVE]

    if ut == "Raider" and state == ABILITY_ACTIVE:
        return config.SURGE_SPEED_MULTIPLIER

    if ut == "Interceptor" and state == ABILITY_ACTIVE:
        return config.INTERCEPT_SPEED_MULTIPLIER

    if ut == "Bastion" and state == ABILITY_ACTIVE:
        return config.FORTIFY_SPEED_MULTIPLIER

    return 1.0


def is_immobile(store, uid):
    if store.unit_type[uid] != "Vanguard":
        return False
    state = store.data[uid, FIELD_ABILITY_ACTIVE]
    return state == ABILITY_ACTIVE or state == ABILITY_WINDUP
