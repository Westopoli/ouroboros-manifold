import math
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
    FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_AOE_RADIUS,
    FIELD_ATTACK_TIMER, FIELD_LAYER, CATEGORY_NAMES,
)
from ability import get_damage_output_multiplier, get_damage_reduction
from movement import has_combat_los, _ensure_navmesh


def resolve_damage(store: UnitStore, tactical_map, dt: float):
    active = store.active_ids()
    navmesh = _ensure_navmesh(tactical_map)
    pending = {}

    for uid in active:
        timer = store.data[uid, FIELD_ATTACK_TIMER] - dt
        if timer > 0:
            store.data[uid, FIELD_ATTACK_TIMER] = timer
            continue

        target = store.auto_engage_target[uid]
        if target < 0 or not store.alive[target]:
            continue

        ax, ay = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tx, ty = store.data[target, FIELD_X], store.data[target, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        attack_range = store.data[uid, FIELD_ATTACK_RANGE]

        if dist > attack_range:
            continue

        if navmesh is not None and navmesh.has_obstacles:
            if not has_combat_los(navmesh, ax, ay, tx, ty):
                continue

        store.data[uid, FIELD_ATTACK_TIMER] = store.data[uid, FIELD_ATTACK_INTERVAL]

        attacker_cat = CATEGORY_NAMES[store.category[uid]]
        base_dmg = store.data[uid, FIELD_BASE_DAMAGE]
        aoe_radius = store.data[uid, FIELD_AOE_RADIUS]

        if aoe_radius > 0:
            _accumulate_aoe(store, uid, target, base_dmg, attacker_cat, aoe_radius, tactical_map, pending)
        else:
            _accumulate_single(store, uid, target, base_dmg, attacker_cat, tactical_map, pending)

    deaths = []
    kill_sources = {}
    for target_uid, hits in pending.items():
        total_dmg = sum(dmg for _, dmg in hits)
        store.data[target_uid, FIELD_HP] -= total_dmg
        if store.data[target_uid, FIELD_HP] <= 0:
            deaths.append(target_uid)
            top_source = max(hits, key=lambda h: h[1])[0]
            kill_sources[target_uid] = top_source

    for dead_uid in deaths:
        store.kill(dead_uid)

    return deaths, kill_sources


def _accumulate_single(store, attacker, target, base_dmg, attacker_cat, tactical_map, pending):
    target_cat = CATEGORY_NAMES[store.category[target]]
    mult = config.CATEGORY_MULTIPLIER[attacker_cat][target_cat]

    cover = 0.0
    if tactical_map is not None:
        cover = tactical_map.cover_density(store.data[target, FIELD_X], store.data[target, FIELD_Y])

    dmg = base_dmg * mult * (1.0 - cover)
    dmg *= get_damage_output_multiplier(store, attacker)
    dmg *= (1.0 - get_damage_reduction(store, target))
    if target not in pending:
        pending[target] = []
    pending[target].append((attacker, dmg))


def _accumulate_aoe(store, attacker, primary_target, base_dmg, attacker_cat, aoe_radius, tactical_map, pending):
    tx = store.data[primary_target, FIELD_X]
    ty = store.data[primary_target, FIELD_Y]
    attacker_faction = store.faction[attacker]
    attacker_layer = store.data[attacker, FIELD_LAYER]
    aoe_r_sq = aoe_radius * aoe_radius
    max_total = base_dmg * config.AOE_DAMAGE_CAP_MULTIPLIER

    targets_in_aoe = []
    for uid in store.active_ids():
        if store.faction[uid] == attacker_faction:
            continue
        if store.data[uid, FIELD_LAYER] != attacker_layer:
            continue
        dx = store.data[uid, FIELD_X] - tx
        dy = store.data[uid, FIELD_Y] - ty
        if dx * dx + dy * dy <= aoe_r_sq:
            targets_in_aoe.append(uid)

    if not targets_in_aoe:
        return

    total_dealt = 0.0
    for target in targets_in_aoe:
        target_cat = CATEGORY_NAMES[store.category[target]]
        mult = config.CATEGORY_MULTIPLIER[attacker_cat][target_cat]

        cover = 0.0
        if tactical_map is not None:
            cover = tactical_map.cover_density(store.data[target, FIELD_X], store.data[target, FIELD_Y])

        dmg = base_dmg * mult * (1.0 - cover)
        dmg *= get_damage_output_multiplier(store, attacker)
        dmg *= (1.0 - get_damage_reduction(store, target))

        if total_dealt + dmg > max_total:
            dmg = max(0.0, max_total - total_dealt)

        if dmg <= 0:
            break

        if target not in pending:
            pending[target] = []
        pending[target].append((attacker, dmg))
        total_dealt += dmg


def update_targeting(store: UnitStore, rng=None):
    active = store.active_ids()
    for uid in active:
        current = store.auto_engage_target[uid]
        if current >= 0 and store.alive[current]:
            dx = store.data[uid, FIELD_X] - store.data[current, FIELD_X]
            dy = store.data[uid, FIELD_Y] - store.data[current, FIELD_Y]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= store.data[uid, FIELD_ATTACK_RANGE]:
                continue

        candidates = []
        my_faction = store.faction[uid]
        my_layer = store.data[uid, FIELD_LAYER]
        mx, my_ = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        engage_range = store.data[uid, FIELD_ATTACK_RANGE]

        for other in active:
            if store.faction[other] == my_faction:
                continue
            if store.data[other, FIELD_LAYER] != my_layer:
                continue
            dx = store.data[other, FIELD_X] - mx
            dy = store.data[other, FIELD_Y] - my_
            d = math.sqrt(dx * dx + dy * dy)
            if d <= engage_range:
                candidates.append((other, d))

        if not candidates:
            store.auto_engage_target[uid] = -1
            continue

        min_dist = min(d for _, d in candidates)
        tied = [c for c, d in candidates if d - min_dist < 1.0]

        if len(tied) == 1 or rng is None:
            store.auto_engage_target[uid] = tied[0]
        else:
            store.auto_engage_target[uid] = rng.choice(tied)
