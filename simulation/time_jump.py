import config
import tick as _tick
from chronicle_distiller import distill
from chronicle_assembler import assemble_scroll


def run_time_jump(world, n_ticks, registry, pending_queue, noise_offsets,
                  trigger_state, stances, pending_telegraphs, rng,
                  start_tick=0, coherence_ledger=None, naming_system=None,
                  player_lineage_id=None, last_mission_region=None,
                  last_mission_outcome=None, mission_info=None):
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
    all_actions = []
    territory_changes = []
    faction_births = []
    faction_deaths_detected = set()
    conquests = []
    colonizations = []
    admin_revolts = []
    revolts = []

    start_faction_ids = set(registry.keys())
    ownership_timeline = []

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
            coherence_ledger=coherence_ledger,
        )

        for evt in tick_log.get("events", []):
            enriched = {**evt, "tick": t}
            enriched.setdefault("character_id", None)
            enriched.setdefault("chain_length", 0)
            enriched.setdefault("mission_consequence", False)
            all_events.append(enriched)

        for act in tick_log.get("faction_actions", []):
            all_actions.append({**act, "tick": t})

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

        if (i + 1) % config.OWNERSHIP_TIMELINE_STRIDE == 0 or i == n_ticks - 1:
            ownership_timeline.append({
                rid: r.faction_id for rid, r in world.regions.items()
            })

    # Coherence ledger: lineage growth + natural deaths
    if coherence_ledger and player_lineage_id:
        coherence_ledger.generate_lineage_members(
            player_lineage_id, n_ticks, world, start_tick + n_ticks, rng)
        coherence_ledger.process_natural_deaths(start_tick + n_ticks, rng, world=world)

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

    # Chronicle distiller
    scroll_entries = []
    chronicle_warnings = []
    if all_events:
        clusters = distill(
            all_events, coherence_ledger, player_lineage_id,
            last_mission_region, last_mission_outcome, world)
        scroll_entries, chronicle_warnings = assemble_scroll(
            clusters, coherence_ledger, player_lineage_id, world,
            mission_info, seed=start_tick, registry=registry)

    post_jump_factions = {}
    for fid, fac in registry.items():
        owned = world.regions_by_faction(fid)
        avg_fields = {}
        if owned:
            for f in ["military", "economy", "tension", "population"]:
                avg_fields[f] = sum(r.fields[f] for r in owned) / len(owned)
        post_jump_factions[fid] = {
            "owned_region_count": len(owned),
            "avg_fields": avg_fields,
            "name": getattr(fac, "name", fid),
        }
    post_jump_regions = {}
    region_populations = {}
    for rid, r in world.regions.items():
        post_jump_regions[rid] = {
            "faction_id": r.faction_id,
            "name": getattr(r, "name", rid),
        }
        region_populations[rid] = r.fields.get("population", 0.0)

    return {
        "ticks_run":          n_ticks,
        "start_tick":         start_tick,
        "end_tick":           start_tick + n_ticks,
        "start_ownership":    start_ownership,
        "territory_changes":  territory_changes,
        "faction_births":     faction_births,
        "faction_deaths":     list(faction_deaths_detected),
        "conquests":          conquests,
        "colonizations":      colonizations,
        "admin_revolts":      admin_revolts,
        "revolts":            revolts,
        "events":             all_events,
        "faction_actions":    all_actions,
        "events_total":       len(all_events),
        "field_deltas":       field_deltas,
        "scroll_entries":     scroll_entries,
        "chronicle_warnings": chronicle_warnings,
        "post_jump_snapshot": {
            "factions": post_jump_factions,
            "regions": post_jump_regions,
        },
        "region_populations": region_populations,
        "adjacency": world.adjacency,
        "edge_types": dict(world.edge_types),
        "ownership_timeline": ownership_timeline,
    }
