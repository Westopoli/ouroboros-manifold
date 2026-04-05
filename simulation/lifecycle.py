import config


def classify_phase(faction_id, world, registry, recent_events=None):
    owned = world.regions_by_faction(faction_id)
    region_count = len(owned)
    if region_count == 0:
        return "equilibrium"

    total_regions = len([r for r in world.regions.values() if r.tier != "empty"])
    if total_regions == 0:
        return "equilibrium"

    recent_events = recent_events or []

    revolt_events = [e for e in recent_events
                     if e.get("template_id", "").startswith("evt_admin")
                     or e.get("type") in ("revolt", "reversion")]
    attack_events = [e for e in recent_events if e.get("action") == "attack"]

    window = max(len(recent_events), 1)

    revolt_rate = len(revolt_events) / window if window > 0 else 0
    if revolt_rate >= config.LIFECYCLE_FRAGMENTATION_REVOLT_RATE:
        return "fragmentation"

    total_economy = sum(r.fields["economy"] for r in owned)
    maintenance = region_count * config.REGION_MAINTENANCE_COST
    if total_economy > 0 and maintenance / total_economy > config.LIFECYCLE_OVEREXTENSION_DRAIN_RATIO:
        return "overextension"

    attack_rate = len(attack_events) / window if window > 0 else 0
    if attack_rate >= config.LIFECYCLE_CONFLICT_ATTACK_RATE:
        return "conflict"

    empty_neighbors = set()
    for r in owned:
        for nid in world.get_neighbors(r.id):
            nr = world.regions.get(nid)
            if nr and nr.tier == "empty":
                empty_neighbors.add(nid)

    accessible_empty_ratio = len(empty_neighbors) / total_regions if total_regions > 0 else 0
    if accessible_empty_ratio >= config.LIFECYCLE_EXPANSION_EMPTY_THRESHOLD:
        return "expansion"

    colonize_events = [e for e in recent_events if e.get("action") == "colonize"]
    if colonize_events and not attack_events:
        return "consolidation"

    return "equilibrium"
