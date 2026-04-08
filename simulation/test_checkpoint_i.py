#!/usr/bin/env python3
import json
import os
import sys
import random

sys.path.insert(0, os.path.dirname(__file__))

import config
import world as world_mod
import faction as faction_mod
import events as _events
import tick as _tick
from naming_system import NamingSystem
from coherence_ledger import CoherenceLedger
from time_jump import run_time_jump

config.ENABLE_EVENTS = True
config.ENABLE_FACTIONS = True
config.ENABLE_BORDER_FRICTION = True
config.ENABLE_RECRUITMENT = True
config.ENABLE_ADJACENCY_BONUS = True
config.ENABLE_OSCILLATION = True
config.ENABLE_TECHNOLOGY = True
config.ENABLE_DIPLOMACY = True
config.ENABLE_ADMIN_REVOLTS = True
config.DIAGNOSTIC_PRINTS = False

SEED = 1
WARMUP_TICKS = 300
JUMP_TICKS = [300, 600, 900]
JUMP_DURATION = 100


def load_naming_system():
    ns = NamingSystem()
    names_path = os.path.join("library", "naming", "names.json")
    with open(names_path) as f:
        all_names = json.load(f)
    for fid, cats in all_names.items():
        for cat, names in cats.items():
            ns.load_pool(fid, cat, names)
    # Map faction IDs used by templates to naming pool IDs
    ns.load_pool("player_civilization", "people",
                 all_names.get("player", {}).get("people", []))
    ns.load_pool("player_civilization", "places",
                 all_names.get("player", {}).get("places", []))
    ns.load_pool("player_civilization", "factions",
                 all_names.get("player", {}).get("factions", []))
    return ns


def print_chronicle_report(jump_num, jump_tick, result):
    print(f"\n{'='*60}")
    print(f"CHRONICLE REVIEW — Jump {jump_num} at tick {jump_tick}")
    print(f"{'='*60}")

    print(f"\n  Ticks run: {result['ticks_run']} ({result['start_tick']} → {result['end_tick']})")
    print(f"  Events fired: {result['events_total']}")
    print(f"  Territory changes: {len(result['territory_changes'])}")
    print(f"  Conquests: {len(result['conquests'])}")
    print(f"  Faction births: {len(result['faction_births'])}")
    print(f"  Faction deaths: {len(result['faction_deaths'])}")

    # Top significance events
    events = result.get("events", [])
    if events:
        from chronicle_distiller import score_event
        scored = []
        for evt in events:
            s = score_event(evt, None, None, None)
            scored.append((evt, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        print(f"\n  Top 5 events by significance:")
        for evt, s in scored[:5]:
            print(f"    {s:5.2f}  {evt.get('name', '?'):25s} in {evt.get('region_id', '?'):12s} tick={evt.get('tick', '?')}")

    # Scroll entries
    entries = result.get("scroll_entries", [])
    warnings = result.get("chronicle_warnings", [])

    print(f"\n  Scroll entries: {len(entries)}")
    if warnings:
        print(f"  Warnings: {len(warnings)}")
        for w in warnings:
            print(f"    {w}")

    # Structural checks
    n = len(entries)
    k1 = 5 <= n <= 10
    has_lineage = any(e.cluster_type == "lineage" for e in entries)
    print(f"\n  K1 (5-10 entries): {n} — {'PASS' if k1 else 'FAIL'}")
    print(f"  K2 (lineage present): {'PASS' if has_lineage else 'FAIL (no lineage — may be expected if no lineage exists)'}")

    # K4: word counts
    import re
    k4_pass = True
    k5_pass = True
    for entry in entries:
        base_wc = len(entry.base_text.split())
        exp_wc = len(entry.expanded_text.split())
        if base_wc >= 90 or exp_wc >= 140:
            k4_pass = False

        unresolved = re.findall(r"\{[a-z_]+\}", entry.expanded_text)
        if unresolved:
            k5_pass = False
            print(f"    UNRESOLVED in {entry.category}: {unresolved}")

    print(f"  K4 (word limits): {'PASS' if k4_pass else 'WARNING'}")
    print(f"  K5 (all slots resolved): {'PASS' if k5_pass else 'FAIL'}")

    # Print each scroll entry
    print(f"\n  --- Scroll ---\n")
    for i, entry in enumerate(entries):
        print(f"  [{i+1}] {entry.cluster_type} / {entry.category}")
        print(f"      Region: {entry.region_id} | Ticks: {entry.tick_range}")
        print(f"      Fragments: {entry.fragment_ids}")
        base_wc = len(entry.base_text.split())
        exp_wc = len(entry.expanded_text.split())
        print(f"      Base ({base_wc}w):")
        print(f"        \"{entry.base_text}\"")
        print(f"      Expanded ({exp_wc}w):")
        print(f"        \"{entry.expanded_text}\"")
        print()


def main():
    print("=" * 60)
    print("CHECKPOINT I: Chronicle Distiller Integration")
    print(f"Seed: {SEED} | Warmup: {WARMUP_TICKS} | Jumps at: {JUMP_TICKS}")
    print("=" * 60)

    # Setup
    rng = random.Random(SEED)
    w = world_mod.generate("contested_border", seed=SEED)
    factions = faction_mod.generate_starting_factions("contested_border", rng=rng, world=w)
    registry = faction_mod.make_registry(*factions)

    naming = load_naming_system()
    ledger = CoherenceLedger(naming)

    # Assign faction display names from naming system
    for fid, fac in registry.items():
        fname = naming.get_name(fid, "factions", current_tick=0, rng=rng)
        if fname:
            fac.name = fname

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()
    pending_telegraphs = []

    # Create initial leaders + lineage
    player_fid = None
    for fid, fac in registry.items():
        leader = ledger.assign_faction_leader(fid, None, 0, rng)
        if leader is None:
            continue
        # Place leader in first owned region
        owned = w.regions_by_faction(fid)
        if owned:
            leader.region_id = owned[0].id
        if fac.archetype == "player_civilization":
            player_fid = fid
            lineage_id = ledger.create_lineage(leader.id)

    player_lineage_id = lineage_id if player_fid else None

    # Assign regional commanders
    for fid in registry:
        for region in w.regions_by_faction(fid):
            ledger.assign_regional_commander(fid, region.id, 0, rng)

    print(f"\nWorld: {len(w.regions)} regions")
    print(f"Factions: {', '.join(f'{fid} ({fac.archetype})' for fid, fac in registry.items())}")
    print(f"Player faction: {player_fid}")
    print(f"Player lineage: {player_lineage_id}")
    print(f"Initial characters: {ledger.active_character_count()}")

    # Warmup: run ticks up to first jump point
    print(f"\nRunning warmup ({WARMUP_TICKS} ticks)...")
    for t in range(1, WARMUP_TICKS + 1):
        _tick.run_tick(
            w, t,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            registry=registry,
            pending_telegraphs=pending_telegraphs,
            coherence_ledger=ledger,
        )
    print(f"  Warmup complete. Characters: {ledger.active_character_count()}")

    # Determine the player's home region for mission context
    player_regions = w.regions_by_faction(player_fid) if player_fid else []
    last_mission_region = player_regions[0].id if player_regions else None

    # Run time jumps
    current_tick = WARMUP_TICKS
    for jump_num, jump_tick in enumerate(JUMP_TICKS, 1):
        gap = jump_tick - current_tick
        if gap <= 0:
            continue

        print(f"\n--- Time Jump {jump_num}: tick {current_tick} → {current_tick + JUMP_DURATION} ---")

        result = run_time_jump(
            world=w,
            n_ticks=JUMP_DURATION,
            registry=registry,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            stances=None,
            pending_telegraphs=pending_telegraphs,
            rng=rng,
            start_tick=current_tick,
            coherence_ledger=ledger,
            naming_system=naming,
            player_lineage_id=player_lineage_id,
            last_mission_region=last_mission_region,
            last_mission_outcome="mixed",
            mission_info={
                "outcome": "a costly defense that preserved the border but exhausted the garrison",
                "archetype": "defensive_stand",
                "region": last_mission_region or "unknown",
            },
        )

        print_chronicle_report(jump_num, current_tick, result)
        current_tick += JUMP_DURATION

        # Update mission region for next jump
        player_regions = w.regions_by_faction(player_fid) if player_fid else []
        last_mission_region = player_regions[0].id if player_regions else last_mission_region

    print(f"\n{'='*60}")
    print("CHECKPOINT I COMPLETE")
    print(f"  Final characters: active={ledger.active_character_count()}, historical={ledger.historical_character_count()}")
    print(f"  Total event attachments: {ledger.total_event_attachments()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
