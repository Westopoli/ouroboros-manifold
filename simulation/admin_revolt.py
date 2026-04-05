import config
import events as _events


def check_admin_revolts(world, registry, pending_queue, rng, tick):
    if not config.ENABLE_ADMIN_REVOLTS:
        return []

    log = []
    for fid, fac in list(registry.items()):
        owned = world.regions_by_faction(fid)
        territory_count = len(owned)
        if territory_count == 0:
            continue

        excess = max(0, territory_count - config.ADMIN_REVOLT_INFLECTION_POINT)
        chance = config.ADMIN_REVOLT_BASE_RATE + config.ADMIN_REVOLT_SCALING_RATE * (excess ** 2)

        for region in owned:
            if rng.random() >= chance:
                continue

            chain_tag = _events._next_chain_tag()
            pending_queue.enqueue({
                "template_id": "evt_admin_separatist",
                "region_id":   region.id,
                "due_tick":    tick + 1,
                "probability": 1.0,
                "conditions":  {},
                "chain_tag":   chain_tag,
            })

            log.append({
                "type":       "admin_revolt_initiated",
                "tick":       tick,
                "faction_id": fid,
                "region_id":  region.id,
                "territory_count": territory_count,
                "chance":     round(chance, 6),
            })

    return log
