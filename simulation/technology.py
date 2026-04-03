import config


def get_tech_multipliers(archetype: str, tech_level: float) -> dict:
    weights = config.ARCHETYPE_TECH_MULTIPLIERS.get(archetype, {"attack": 0.0, "defense": 0.0, "economy": 0.0})
    ratio = tech_level / 100.0
    return {
        "attack":  1.0 + ratio * weights["attack"],
        "defense": 1.0 + ratio * weights["defense"],
        "economy": 1.0 + ratio * weights["economy"],
    }


def grow_tech(faction, world) -> dict | None:
    owned = [r for r in world.regions.values() if r.faction_id == faction.id and r.fields]
    if not owned:
        return None
    avg_economy    = sum(r.fields["economy"]    for r in owned) / len(owned)
    avg_population = sum(r.fields["population"] for r in owned) / len(owned)
    pop_factor     = avg_population / 100.0
    pop_floor_applied = pop_factor < config.TECH_POPULATION_FLOOR
    pop_factor     = max(config.TECH_POPULATION_FLOOR, pop_factor)
    base_growth    = config.BASE_TECH_RATE * (avg_economy / 100.0) * pop_factor
    tech_before    = faction.tech_level
    faction.tech_level = min(100.0, faction.tech_level + base_growth)
    return {
        "faction_id":        faction.id,
        "tech_level_before": round(tech_before, 6),
        "tech_level_after":  round(faction.tech_level, 6),
        "base_growth":       round(base_growth, 6),
        "avg_economy":       round(avg_economy, 2),
        "avg_population":    round(avg_population, 2),
        "pop_floor_applied": pop_floor_applied,
    }
