import math
import config
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
    FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_AOE_RADIUS,
    FIELD_ATTACK_TIMER, FIELD_LAYER, FIELD_SENSOR_RADIUS, CATEGORY_NAMES,
)
from ability import get_damage_output_multiplier, get_damage_reduction
from movement import has_combat_los, _ensure_navmesh

_targeting_tick = 0

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
        store.attack_backswing[uid] = config.ATTACK_BACKSWING_SEC

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

    _apply_return_fire(store, pending)

    return deaths, kill_sources


_RETURN_FIRE_FLEE_DIST = 200.0  # mirrors _ATTACK_MOVE_LEASH_SQ leash radius in movement.py


def _apply_return_fire(store: UnitStore, pending: dict) -> None:
    for target_uid, hits in pending.items():
        if not store.alive[target_uid]:
            continue
        if store.plain_moving[target_uid]:
            continue
        if store.auto_engage_target[target_uid] >= 0:
            continue

        tx = store.data[target_uid, FIELD_X]
        ty = store.data[target_uid, FIELD_Y]
        my_layer = store.data[target_uid, FIELD_LAYER]
        atk_r_sq = store.data[target_uid, FIELD_ATTACK_RANGE] ** 2

        same_layer_uid = -1
        cross_layer_uid = -1
        cross_dx = cross_dy = 0.0

        for attacker_uid, _dmg in hits:
            if not store.alive[attacker_uid]:
                continue
            if store.data[attacker_uid, FIELD_LAYER] == my_layer:
                if same_layer_uid < 0:
                    same_layer_uid = attacker_uid
            else:
                if cross_layer_uid < 0:
                    cross_layer_uid = attacker_uid
                    cross_dx = tx - store.data[attacker_uid, FIELD_X]
                    cross_dy = ty - store.data[attacker_uid, FIELD_Y]

        if same_layer_uid >= 0:
            ax = store.data[same_layer_uid, FIELD_X]
            ay = store.data[same_layer_uid, FIELD_Y]
            dx = ax - tx
            dy = ay - ty
            if dx * dx + dy * dy <= atk_r_sq:
                store.auto_engage_target[target_uid] = same_layer_uid
            else:
                store.attack_moving[target_uid] = True
                store.engage_anchor_x[target_uid] = tx
                store.engage_anchor_y[target_uid] = ty
                store.engage_anchor_set[target_uid] = True
                store.auto_engage_target[target_uid] = same_layer_uid
                store.set_move_target(target_uid, ax, ay)
        elif cross_layer_uid >= 0:
            length = math.sqrt(cross_dx * cross_dx + cross_dy * cross_dy)
            if length > 1e-6:
                nx, ny = cross_dx / length, cross_dy / length
            else:
                nx, ny = 1.0, 0.0
            store.set_move_target(target_uid,
                                  tx + nx * _RETURN_FIRE_FLEE_DIST,
                                  ty + ny * _RETURN_FIRE_FLEE_DIST)


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


def update_targeting(store: UnitStore, tmap, rng=None):
    global _targeting_tick
    _targeting_tick += 1
    cohort_this_tick = _targeting_tick % config.TARGETING_COHORT_COUNT
    active = store.active_ids()

    # Rebuild both hashes each tick.
    # target_hash (small cells): attack-range ring search — fast early exit in dense combat.
    # spatial_hash (large cells): sensor-pursuit full query — cheap at long range in sparse march.
    tmap.target_hash.clear()
    tmap.spatial_hash.clear()
    for uid in active:
        x, y = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tmap.target_hash.insert(uid, x, y)
        tmap.spatial_hash.insert(uid, x, y)

    for uid in active:
        if store.plain_moving[uid]:   # plain move is non-combat: skip targeting entirely
            continue

        my_faction = store.faction[uid]
        my_layer   = store.data[uid, FIELD_LAYER]
        mx         = store.data[uid, FIELD_X]
        my_        = store.data[uid, FIELD_Y]
        atk_range  = store.data[uid, FIELD_ATTACK_RANGE]
        atk_r_sq   = atk_range * atk_range

        is_cohort_turn = uid % config.TARGETING_COHORT_COUNT == cohort_this_tick

        # Target loyalty: keep current target if still alive and in range.
        # Cohort re-acquisition only applies when there's no valid current target.
        current = store.auto_engage_target[uid]
        if current >= 0 and store.alive[current]:
            dx = store.data[current, FIELD_X] - mx
            dy = store.data[current, FIELD_Y] - my_
            if dx * dx + dy * dy <= atk_r_sq:
                continue

        if not is_cohort_turn:
            continue

        # Outward ring search in target_hash (small cells) — break on first valid hit.
        # Yields unit IDs in ring order with no per-ring allocations; callers just break.
        # See tactical_map.py query_outward for ring traversal order.
        found_atk = False
        best_atk_d_sq = float("inf")
        best_atk_uid = -1
        for other in tmap.target_hash.query(mx, my_, atk_range):
            if store.faction[other] == my_faction: continue
            if store.data[other, FIELD_LAYER] != my_layer: continue
            dx = store.data[other, FIELD_X] - mx
            dy = store.data[other, FIELD_Y] - my_
            d_sq = dx * dx + dy * dy
            if d_sq <= atk_r_sq and d_sq < best_atk_d_sq:
                best_atk_d_sq = d_sq
                best_atk_uid = other
        if best_atk_uid >= 0:
            store.auto_engage_target[uid] = best_atk_uid
            found_atk = True

        if not found_atk:
            store.auto_engage_target[uid] = -1
            # Attack-move pursuit: walk toward the nearest visible enemy if none in range.
            # Uses spatial_hash (large cells) — cheap at long sensor ranges during march.
            # See movement.py apply_group_move — attack_moving flag set by attack_move command.
            if store.attack_moving[uid]:
                sensor_r = store.data[uid, FIELD_SENSOR_RADIUS]
                if sensor_r > atk_range:
                    sensor_r_sq = sensor_r * sensor_r
                    best_d_sq = float("inf")
                    best_uid  = -1
                    for other in tmap.spatial_hash.query(mx, my_, sensor_r):
                        if store.faction[other] == my_faction: continue
                        if store.data[other, FIELD_LAYER] != my_layer: continue
                        dx = store.data[other, FIELD_X] - mx
                        dy = store.data[other, FIELD_Y] - my_
                        d_sq = dx * dx + dy * dy
                        if d_sq <= sensor_r_sq and d_sq < best_d_sq:
                            best_d_sq = d_sq
                            best_uid  = other
                    if best_uid >= 0:
                        store.set_move_target(uid,
                                              store.data[best_uid, FIELD_X],
                                              store.data[best_uid, FIELD_Y])
