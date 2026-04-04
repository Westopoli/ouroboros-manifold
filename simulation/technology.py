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


def apply_convergence(faction, registry: dict, stances: dict) -> dict | None:
    if not stances:
        return None
    from diplomacy import get_stance
    best_partner = None
    best_tech = faction.tech_level
    for other_fid, other_fac in registry.items():
        if other_fid == faction.id:
            continue
        if get_stance(stances, faction.id, other_fid) != "cooperative":
            continue
        if other_fac.tech_level > best_tech:
            best_tech = other_fac.tech_level
            best_partner = other_fac
    if best_partner is None:
        return None
    gap = best_partner.tech_level - faction.tech_level
    bonus = config.TECH_CONVERGENCE_RATE * max(0.0, gap) / 100.0
    if bonus <= 0:
        return None
    tech_before = faction.tech_level
    faction.tech_level = min(100.0, faction.tech_level + bonus)
    return {
        "faction_id": faction.id,
        "convergence_bonus": round(bonus, 6),
        "best_partner": best_partner.id,
        "best_partner_tech": round(best_partner.tech_level, 4),
        "tech_before": round(tech_before, 6),
        "tech_after": round(faction.tech_level, 6),
    }
