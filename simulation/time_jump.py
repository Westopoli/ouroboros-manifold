import config
import tick as _tick


def run_time_jump(world, n_ticks, registry, pending_queue, noise_offsets,
                  trigger_state, stances, pending_telegraphs, rng,
                  start_tick=0):
    n_ticks = max(config.TIME_JUMP_MIN_TICKS, min(config.TIME_JUMP_MAX_TICKS, n_ticks))

    start_ownership = {}
    start_fields = {}
    start_factions = set()
    for rid, r in world.regions.items():
        start_ownership[rid] = r.faction_id
        start_fields[rid] = dict(r.fields)
    for fid, fac in registry.items():
        if len(world.regions_by_faction(fid)) > 0:
            start_factions.add(fid)

    all_events = []
    territory_changes = []
    faction_births = []
    faction_deaths_detected = set()
    conquests = []
    colonizations = []
    admin_revolts = []
    revolts = []

    start_faction_ids = set(registry.keys())

    for i in range(n_ticks):
        t = start_tick + i + 1
        tick_log = _tick.run_tick(
            world, t,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            registry=registry,
            stances=stances,
            pending_telegraphs=pending_telegraphs,
        )

        for evt in tick_log.get("events", []):
            all_events.append({**evt, "tick": t})

        for c in tick_log.get("conquests", []):
            conquests.append({**c, "tick": t})

        for col in tick_log.get("colonizations", []):
            colonizations.append({**col, "tick": t})

        for ar in tick_log.get("admin_revolts", []):
            admin_revolts.append(ar)

        for rev in tick_log.get("revolts", []):
            revolts.append({**rev, "tick": t})

        new_ids = set(registry.keys()) - start_faction_ids
        for nid in new_ids:
            faction_births.append({"faction_id": nid, "tick": t})
            start_faction_ids.add(nid)

    end_ownership = {rid: r.faction_id for rid, r in world.regions.items()}
    for rid in start_ownership:
        if start_ownership[rid] != end_ownership.get(rid):
            territory_changes.append({
                "region_id": rid,
                "old_faction": start_ownership[rid],
                "new_faction": end_ownership.get(rid),
            })

    for fid in start_factions:
        if len(world.regions_by_faction(fid)) == 0:
            faction_deaths_detected.add(fid)

    field_deltas = {}
    for fid in registry:
        owned = world.regions_by_faction(fid)
        if not owned:
            continue
        end_avg = {}
        for f in ["military", "economy", "tension", "population"]:
            end_avg[f] = sum(r.fields[f] for r in owned) / len(owned)

        start_regions_for_fac = [rid for rid, ofid in start_ownership.items() if ofid == fid]
        if start_regions_for_fac:
            start_avg = {}
            for f in ["military", "economy", "tension", "population"]:
                vals = [start_fields[rid][f] for rid in start_regions_for_fac if rid in start_fields]
                start_avg[f] = sum(vals) / len(vals) if vals else 0.0
            field_deltas[fid] = {f: round(end_avg[f] - start_avg.get(f, 0.0), 2) for f in end_avg}

    return {
        "ticks_run":          n_ticks,
        "start_tick":         start_tick,
        "end_tick":           start_tick + n_ticks,
        "territory_changes":  territory_changes,
        "faction_births":     faction_births,
        "faction_deaths":     list(faction_deaths_detected),
        "conquests":          conquests,
        "colonizations":      colonizations,
        "admin_revolts":      admin_revolts,
        "revolts":            revolts,
        "events_total":       len(all_events),
        "field_deltas":       field_deltas,
    }
