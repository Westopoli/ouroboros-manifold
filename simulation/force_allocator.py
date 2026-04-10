import math
import config
from power_rating import compute_power_rating
from mission_contracts import ForceUnit, ForceComposition, ReinforcementSpec


BUDGET_ARCHETYPES = {"defensive_stand", "multi_front_defense", "interception"}
INSURGENT_ARCHETYPES = {"counterinsurgency", "suppression"}


def _roll_insurgent_military(region, rng):
    pop = region.fields.get("population", 50) if hasattr(region, 'fields') else 50
    lo_thresh = config.INSURGENT_POP_LOW_THRESHOLD
    hi_thresh = config.INSURGENT_POP_HIGH_THRESHOLD
    t = max(0.0, min(1.0, (pop - lo_thresh) / (hi_thresh - lo_thresh)))
    lo_range = config.INSURGENT_MIL_LOW_POP_RANGE
    hi_range = config.INSURGENT_MIL_HIGH_POP_RANGE
    range_lo = lo_range[0] + t * (hi_range[0] - lo_range[0])
    range_hi = lo_range[1] + t * (hi_range[1] - lo_range[1])
    return rng.uniform(range_lo, range_hi)


def _lerp_parity(capacity):
    bps = config.PARITY_BREAKPOINTS
    if capacity <= bps[0][0]:
        return bps[0][1]
    if capacity >= bps[-1][0]:
        return bps[-1][1]
    for i in range(len(bps) - 1):
        x0, y0 = bps[i]
        x1, y1 = bps[i + 1]
        if x0 <= capacity <= x1:
            t = (capacity - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return bps[-1][1]


def compute_parity_ratio(capacity, difficulty):
    base = _lerp_parity(capacity)
    if difficulty == "easy":
        parity = max(base, config.PARITY_EASY_FLOOR)
    elif difficulty == "hard":
        parity = min(base, config.PARITY_HARD_CEILING)
    else:
        parity = base
    return max(parity, config.PARITY_FLOOR)


def determine_enemy_power(archetype, trigger_context, region, rng=None):
    if archetype in BUDGET_ARCHETYPES:
        budget = trigger_context.get("budget_committed", 0)
        return budget * config.BUDGET_TO_POWER_SCALE, {}
    elif archetype in INSURGENT_ARCHETYPES:
        # Use pre-rolled value from trigger context if available, otherwise roll now
        insurgent_mil = trigger_context.get("insurgent_military")
        if insurgent_mil is None:
            insurgent_mil = _roll_insurgent_military(region, rng)
        return insurgent_mil * config.MILITARY_TO_POWER_SCALE, {
            "insurgent_military": insurgent_mil,
        }
    else:
        mil = region.fields.get("military", 50) if hasattr(region, 'fields') else 50
        return mil * config.MILITARY_TO_POWER_SCALE, {}


def _get_unit_roster():
    roster = {}
    for unit_type, stats in config.UNIT_STATS.items():
        s = dict(stats)
        s["unit_type"] = unit_type
        pr = compute_power_rating(s)
        roster[unit_type] = {"stats": s, "power_rating": pr, "category": stats["category"]}
    return roster


def _fill_force(power_budget, asset_profile, roster, faction_id, rng):
    units = []
    remaining = power_budget
    profile_sorted = sorted(asset_profile.items(), key=lambda x: -x[1])

    for unit_type, ratio in profile_sorted:
        if unit_type not in roster:
            continue
        target_power = power_budget * ratio
        allocated = 0.0
        unit_info = roster[unit_type]
        while allocated < target_power and remaining > 0:
            pr = unit_info["power_rating"]
            if pr > remaining * 1.15:
                break
            units.append(ForceUnit(
                unit_type=unit_type,
                category=unit_info["category"],
                stats=unit_info["stats"],
                power_rating=pr,
                faction_id=faction_id,
                name=f"{unit_type}-{len(units)+1}",
            ))
            allocated += pr
            remaining -= pr

    total_power = sum(u.power_rating for u in units)
    return ForceComposition(units=units, total_power=total_power, faction_id=faction_id)


def apply_shortfall(force, capacity, rng):
    if capacity >= config.CAPACITY_SHORTFALL_THRESHOLD:
        return force, []
    reduction = config.CAPACITY_SHORTFALL_REDUCTION
    target_count = max(1, int(len(force.units) * (1.0 - reduction)))
    if target_count >= len(force.units):
        return force, []

    from collections import Counter
    type_counts = Counter(u.unit_type for u in force.units)
    to_remove = len(force.units) - target_count

    removed_types = []
    removed = 0
    types_by_count = sorted(type_counts.keys(), key=lambda t: -type_counts[t])
    idx = 0
    while removed < to_remove and any(type_counts[t] > 0 for t in types_by_count):
        ut = types_by_count[idx % len(types_by_count)]
        if type_counts[ut] > 0:
            type_counts[ut] -= 1
            removed += 1
            removed_types.append(ut)
        idx += 1

    kept = []
    remove_counts = Counter(removed_types)
    skip_counts = {}
    for u in reversed(force.units):
        skip_key = u.unit_type
        already_skipped = skip_counts.get(skip_key, 0)
        if already_skipped < remove_counts.get(skip_key, 0):
            skip_counts[skip_key] = already_skipped + 1
        else:
            kept.append(u)
    kept.reverse()

    total_power = sum(u.power_rating for u in kept)
    new_force = ForceComposition(units=kept, total_power=total_power, faction_id=force.faction_id)
    return new_force, removed_types


def compute_reinforcement_spec(archetype, region_military):
    canvas_size = config.ARCHETYPE_BASE_CANVAS.get(archetype, "medium")
    raw_count = int(region_military * config.MILITARY_TO_STRUCTURES_SCALE)
    lo, hi = config.STRUCTURE_COUNT_RANGE[canvas_size]
    count = max(lo, min(hi, raw_count))

    p_frac, e_frac, n_frac = config.ARCHETYPE_STRUCTURE_SPLIT.get(
        archetype, (0.33, 0.34, 0.33))
    player_s = max(1, round(count * p_frac))
    enemy_s = max(0, round(count * e_frac))
    neutral_s = max(0, count - player_s - enemy_s)

    enemy_target_ratio = config.ASSET_PROFILES.get(archetype, {})

    return ReinforcementSpec(
        structure_count=count,
        player_structures=player_s,
        enemy_structures=enemy_s,
        neutral_structures=neutral_s,
        production_rate=config.STRUCTURE_PRODUCTION_RATE,
        enemy_target_ratio=enemy_target_ratio,
    )


def allocate_forces(archetype, trigger_context, region, capacity,
                    difficulty, player_faction_id, enemy_faction_id, rng):
    roster = _get_unit_roster()
    asset_profile = config.ASSET_PROFILES.get(archetype, {})

    enemy_power, extra_ctx = determine_enemy_power(archetype, trigger_context, region, rng)
    enemy_force = _fill_force(enemy_power, asset_profile, roster, enemy_faction_id, rng)

    parity = compute_parity_ratio(capacity, difficulty)
    player_budget = enemy_force.total_power * parity

    player_force = _fill_force(player_budget, asset_profile, roster, player_faction_id, rng)

    shortfall_types = []
    if capacity < config.CAPACITY_SHORTFALL_THRESHOLD:
        player_force, shortfall_types = apply_shortfall(player_force, capacity, rng)

    if enemy_force.total_power > 0:
        actual_parity = player_force.total_power / enemy_force.total_power
        if actual_parity < config.PARITY_FLOOR:
            cheapest = min(roster.values(), key=lambda r: r["power_rating"])
            units = list(player_force.units)
            total = player_force.total_power
            while total / enemy_force.total_power < config.PARITY_FLOOR:
                units.append(ForceUnit(
                    unit_type=cheapest["stats"]["unit_type"],
                    category=cheapest["category"],
                    stats=cheapest["stats"],
                    power_rating=cheapest["power_rating"],
                    faction_id=player_faction_id,
                    name=f"{cheapest['stats']['unit_type']}-floor-{len(units)+1}",
                ))
                total += cheapest["power_rating"]
            player_force = ForceComposition(units=units, total_power=total,
                                            faction_id=player_faction_id)

    region_mil = region.fields.get("military", 50) if hasattr(region, 'fields') else 50
    reinforcements = compute_reinforcement_spec(archetype, region_mil)

    return {
        "enemy_force": enemy_force,
        "player_force": player_force,
        "enemy_power_total": enemy_power,
        "parity_ratio": parity,
        "player_budget": player_budget,
        "shortfall_types": shortfall_types,
        "reinforcements": reinforcements,
        **extra_ctx,
    }
