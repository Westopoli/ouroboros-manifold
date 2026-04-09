import config


def compute_friction(region, world, registry) -> dict | None:
    """Compute border friction for one region from all hostile neighbors.
    Returns a friction log dict, or None if no hostile edges."""
    if not region.fields or region.faction_id is None:
        return None

    faction = registry.get(region.faction_id)
    if faction is None:
        return None

    hostile_edges = []
    for nb_id in world.get_neighbors(region.id, edge_type="border"):
        nb = world.regions[nb_id]
        if nb.faction_id is None or nb.faction_id == region.faction_id:
            continue

        our_stance = faction.diplomatic_stance.get(nb.faction_id, "neutral")
        nb_faction = registry.get(nb.faction_id)
        their_stance = (nb_faction.diplomatic_stance.get(region.faction_id, "neutral")
                        if nb_faction else "neutral")

        if our_stance != "hostile" and their_stance != "hostile":
            continue

        nb_mil = nb.fields["military"]
        tension_f = config.BORDER_FRICTION_TENSION * (nb_mil / 100.0)
        economy_f = config.BORDER_FRICTION_ECONOMY * (nb_mil / 100.0)
        hostile_edges.append({
            "neighbor": nb_id,
            "neighbor_military": round(nb_mil, 2),
            "tension_friction": round(tension_f, 4),
            "economy_friction": round(economy_f, 4),
        })

    if not hostile_edges:
        return None

    total_tension = sum(e["tension_friction"] for e in hostile_edges)
    total_economy = sum(e["economy_friction"] for e in hostile_edges)
    return {
        "region_id": region.id,
        "hostile_edges": hostile_edges,
        "total_tension_friction": round(total_tension, 4),
        "total_economy_friction": round(total_economy, 4),
    }


def apply_friction(region, friction_log: dict) -> None:
    region.fields["tension"] = min(100.0,
        region.fields["tension"] + friction_log["total_tension_friction"])
    region.fields["economy"] = max(config.ECONOMY_FLOOR,
        region.fields["economy"] - friction_log["total_economy_friction"])
    region.recompute_composites()


def run_border_friction(world, registry) -> list:
    """Apply border friction to all regions. Returns list of friction log entries."""
    logs = []
    for region in world.regions.values():
        friction = compute_friction(region, world, registry)
        if friction is not None:
            apply_friction(region, friction)
            logs.append(friction)
    return logs
