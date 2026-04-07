import math
import config


def compute_power_rating(stats: dict) -> float:
    effective_hp = stats["hp"] / (1.0 - config.POWER_RATING_COVER_ASSUMPTION)
    dps = stats["base_damage"] / stats["attack_interval"]
    range_factor = math.log(stats["attack_range"] + 1) / math.log(config.RANGE_NORMALIZATION + 1)
    mobility_factor = stats["speed"] / config.SPEED_NORMALIZATION

    power = effective_hp * dps * range_factor * mobility_factor

    if stats.get("aoe_radius", 0) > 0:
        power *= config.AOE_POWER_MULTIPLIER

    unit_type = stats.get("unit_type")
    if unit_type and unit_type in config.ABILITY_POWER_BONUS:
        power *= (1.0 + config.ABILITY_POWER_BONUS[unit_type])

    return power


def compute_force_power(unit_list: list[dict]) -> float:
    return sum(compute_power_rating(s) for s in unit_list)
