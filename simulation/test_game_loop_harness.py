# Game loop harness — spawned by test_game_loop.py
# Sets up a small world + tactical engine, runs the full game loop via pipe_transport.
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
config.ENABLE_EVENTS = True
config.ENABLE_FACTIONS = True
config.ENABLE_BORDER_FRICTION = True
config.ENABLE_RECRUITMENT = True
config.ENABLE_ADJACENCY_BONUS = True
config.ENABLE_OSCILLATION = True
config.ENABLE_TECHNOLOGY = False
config.ENABLE_DIPLOMACY = False
config.DIAGNOSTIC_PRINTS = False
config.TIME_JUMP_TICKS_PER_CHAPTER = 30
config.TICK_HZ = 1000  # run ticks as fast as possible for test
config.SNAPSHOT_INTERVAL_SEC = 0.5

import world as world_mod
import faction as faction_mod
import events as _events
import naming_system as _naming_mod
import coherence_ledger as _ledger_mod
from generational import GenerationalState
from tactical_engine import TacticalEngine
from test_maps import open_field
from command import Command
import pipe_transport


def setup_sim_env(seed=42):
    w = world_mod.generate_random(seed=seed)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)

    ns = _naming_mod.NamingSystem()
    for fid in registry:
        for cat in ["people", "places", "factions"]:
            pool = [f"{cat}_{fid}_{i}" for i in range(400)]
            ns._pools.setdefault(fid, {})[cat] = {
                "available": list(pool), "used": [], "cooldown": [],
            }
    ledger = _ledger_mod.CoherenceLedger(ns)
    for fid, fac in registry.items():
        home_regions = [r for r in w.regions.values() if r.faction_id == fid]
        if home_regions:
            ledger.assign_faction_leader(fid, home_regions[0].id, 0, w.rng)

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()

    player_fid = None
    for fid, fac in registry.items():
        if fac.archetype == "player_civilization":
            player_fid = fid
            break
    if not player_fid:
        player_fid = list(registry.keys())[0]

    leader = ledger.get_faction_leader(player_fid)
    player_lineage_id = ledger.create_lineage(leader.id) if leader else None

    gen_state = GenerationalState(player_fid, start_tick=0)
    if leader and player_lineage_id:
        gen_state.current_chapter["character_id"] = leader.id
        ledger.increment_chapter(player_lineage_id)

    return {
        "world": w,
        "registry": registry,
        "ledger": ledger,
        "ns": ns,
        "noise_offsets": noise_offsets,
        "trigger_state": trigger_state,
        "pending_queue": pending_queue,
        "player_fid": player_fid,
        "player_lineage_id": player_lineage_id,
        "gen_state": gen_state,
        "stances": {},
        "pending_telegraphs": [],
        "current_tick": 0,
    }


def make_engine():
    """Create a small tactical engine that will terminate quickly (few units)."""
    tmap = open_field()
    eng = TacticalEngine(tmap, seed=42)
    eng.player_faction = 0
    eng.mission_id = "mission_test_001"
    eng.archetype = "assault"
    eng.initial_power = 100.0
    eng.objectives = []
    eng.region_fields = {"military": 60.0, "tension": 50.0, "economy": 50.0, "population": 50.0}

    eng.store.spawn("Vanguard", 0, 1000.0, 1800.0)
    eng.store.spawn("Vanguard", 1, 1000.0, 2200.0)

    # Both factions attack each other — close spawn = fast terminal
    a_ids = eng.store.active_ids_for_faction(0)
    eng.command_queue.add(Command(tick=0, type="attack_move", unit_ids=a_ids,
                                  params={"target_x": 1000.0, "target_y": 2200.0}))
    b_ids = eng.store.active_ids_for_faction(1)
    eng.command_queue.add(Command(tick=0, type="attack_move", unit_ids=b_ids,
                                  params={"target_x": 1000.0, "target_y": 1800.0}))
    return eng


if __name__ == "__main__":
    sim_env = setup_sim_env()
    pipe_transport.run(make_engine, sim_env=sim_env)
