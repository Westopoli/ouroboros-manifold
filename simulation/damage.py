import math
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
    FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_AOE_RADIUS,
    FIELD_ATTACK_TIMER, FIELD_LAYER, FIELD_SENSOR_RADIUS, CATEGORY_NAMES,
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


def update_targeting(store: UnitStore, tmap, rng=None, tick=0):
    active = store.active_ids()

    tmap.spatial_hash.clear()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    for uid in active:
        if store.plain_moving[uid]:   # plain move is non-combat: skip targeting entirely
            continue

        my_faction = store.faction[uid]
        my_layer   = store.data[uid, FIELD_LAYER]
        mx         = store.data[uid, FIELD_X]
        my_        = store.data[uid, FIELD_Y]
        atk_range  = store.data[uid, FIELD_ATTACK_RANGE]
        atk_r_sq   = atk_range * atk_range

        # Early exit: keep current target if still alive and in range.
        current = store.auto_engage_target[uid]
        if current >= 0 and store.alive[current]:
            dx = store.data[current, FIELD_X] - mx
            dy = store.data[current, FIELD_Y] - my_
            if dx * dx + dy * dy <= atk_r_sq:
                continue

        # Re-targeting stagger: spread queries across multiple ticks.
        # Siege (range > 600) every 5 ticks; all others every 2 ticks.
        # Stagger by uid so units don't all skip the same ticks.
        stagger = 5 if atk_range > 600 else 2
        if tick % stagger != uid % stagger:
            continue

        # Single query at max(attack_range, sensor_radius) covers both buckets.
        # Attack-move pursuit: if the unit is attack_moving and found nothing in
        # attack range, walk toward the closest enemy in sensor range instead.
        # Fires during march and after slot arrival. See movement.py apply_group_move.
        sensor_r    = store.data[uid, FIELD_SENSOR_RADIUS] if store.attack_moving[uid] else 0.0
        query_r     = atk_range if sensor_r <= atk_range else sensor_r
        sensor_r_sq = sensor_r * sensor_r

        best_atk_d_sq    = float("inf")
        best_atk_uid     = -1
        best_sensor_d_sq = float("inf")
        best_sensor_uid  = -1

        for other in tmap.spatial_hash.query(mx, my_, query_r):
            if store.faction[other] == my_faction:
                continue
            if store.data[other, FIELD_LAYER] != my_layer:
                continue
            dx   = store.data[other, FIELD_X] - mx
            dy   = store.data[other, FIELD_Y] - my_
            d_sq = dx * dx + dy * dy
            if d_sq <= atk_r_sq:
                if d_sq < best_atk_d_sq:
                    best_atk_d_sq = d_sq
                    best_atk_uid  = other
            elif sensor_r > 0 and d_sq <= sensor_r_sq:
                if d_sq < best_sensor_d_sq:
                    best_sensor_d_sq = d_sq
                    best_sensor_uid  = other

        if best_atk_uid >= 0:
            store.auto_engage_target[uid] = best_atk_uid
        else:
            store.auto_engage_target[uid] = -1
            if best_sensor_uid >= 0:
                store.set_move_target(uid,
                                      store.data[best_sensor_uid, FIELD_X],
                                      store.data[best_sensor_uid, FIELD_Y])
