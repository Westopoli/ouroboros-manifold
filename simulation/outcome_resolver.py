import config
from mission_contracts import MissionResult


def compute_delta(current_value, form, pct):
    if form == "deficit":
        return (100 - current_value) * pct / 100.0
    elif form == "current":
        return current_value * pct / 100.0
    return 0.0


def _get_target_regions(target, mission_region_id, world, player_faction_id):
    if target == "mission":
        return [mission_region_id]
    elif target == "home":
        return [mission_region_id]
    elif target == "adjacent_player":
        neighbors = world.get_neighbors(mission_region_id)
        return [rid for rid in neighbors
                if world.regions[rid].faction_id == player_faction_id]
    elif target == "exposed":
        return [mission_region_id]
    return [mission_region_id]


def resolve_outcome(mission_result, archetype, mission_region_id,
                    world, player_faction_id, ledger=None, commander_id=None):
    table = config.CONSEQUENCE_TABLES.get(archetype, {})
    band_deltas = table.get(mission_result.outcome_band, [])

    applied_deltas = []
    for delta_spec in band_deltas:
        target_ids = _get_target_regions(
            delta_spec["target"], mission_region_id, world, player_faction_id)
        for rid in target_ids:
            region = world.regions[rid]
            field = delta_spec["field"]
            current = region.fields.get(field, 50)
            delta = compute_delta(current, delta_spec["form"], delta_spec["pct"])
            new_value = max(0.0, min(100.0, current + delta))
            applied_deltas.append({
                "region_id": rid,
                "field": field,
                "old_value": current,
                "delta": delta,
                "new_value": new_value,
                "form": delta_spec["form"],
                "pct": delta_spec["pct"],
                "target_type": delta_spec["target"],
            })
            region.fields[field] = new_value

    transfer = None
    transfer_outcomes = config.REGION_TRANSFER_OUTCOMES.get(archetype, set())
    if mission_result.outcome_band in transfer_outcomes:
        old_faction = world.regions[mission_region_id].faction_id
        world.regions[mission_region_id].faction_id = player_faction_id
        transfer = {
            "region_id": mission_region_id,
            "old_faction_id": old_faction,
            "new_faction_id": player_faction_id,
        }

    events = []
    if not mission_result.commander_survived:
        events.append({
            "event_id": config.COMMANDER_DEATH_EVENT_ID,
            "commander_id": commander_id,
            "region_id": mission_region_id,
            "archetype": archetype,
            "outcome_band": mission_result.outcome_band,
        })
        if ledger is not None and commander_id is not None:
            ledger.record_commander_death(commander_id, mission_region_id,
                                          mission_result.outcome_band)

    return {
        "applied_deltas": applied_deltas,
        "region_transfer": transfer,
        "events": events,
    }
