import random
import time
import config
from unit import UnitStore
from tactical_engine import TacticalEngine
from test_maps import open_field_large
from movement import apply_group_move, update_movement
from damage import update_targeting, resolve_damage
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import process_commands
from sim_logger import SimLogger, config_snapshot

OUT = "/tmp/test_small.jsonl"
TICKS = 1500

rng = random.Random(1)
tmap = open_field_large()
store = UnitStore()

ratio = {"Vanguard": 0.3, "Warden": 0.2, "Raider": 0.2, "Interceptor": 0.1, "Bombard": 0.1, "Bastion": 0.1}
for faction, cx in [(0, 5000.0), (1, 7000.0)]:
    placed = 0
    for ut, frac in ratio.items():
        n = max(1, round(50 * frac))
        for i in range(n):
            x = cx + rng.uniform(-200, 200)
            y = 6000.0 + (placed - 25) * 60.0 + rng.uniform(-15, 15)
            store.spawn(ut, faction, x, y)
            placed += 1

uids_a = [u for u in range(store.count) if store.faction[u] == 0]
uids_b = [u for u in range(store.count) if store.faction[u] == 1]
apply_group_move(store, uids_a, 6000.0, 6000.0)
apply_group_move(store, uids_b, 6000.0, 6000.0)

engine = TacticalEngine(tmap, store, seed=1)
logger = SimLogger(OUT, "50v50_quick", tmap,
                   {0: ("A", "#3b82f6"), 1: ("B", "#ef4444")}, config_snapshot())

for _ in range(TICKS):
    process_commands(engine.command_queue, engine.store, engine.tick)
    t = time.perf_counter(); update_targeting(engine.store, engine.map, engine.rng); dt_tgt = time.perf_counter() - t
    t = time.perf_counter(); update_movement(engine.store, engine.map, engine.dt); dt_mov = time.perf_counter() - t
    deaths, _ = resolve_damage(engine.store, engine.map, engine.dt)
    t = time.perf_counter(); be = update_abilities(engine.store, engine.dt)
    if be:
        resolve_barrage(engine.store, be)
    dt_abl = time.perf_counter() - t
    update_fog_timers(engine.store)
    engine.tick += 1
    logger.log_tick(engine.tick, engine.store, deaths, {
        "targeting": dt_tgt, "movement": dt_mov, "abilities": dt_abl,
        "damage": 0.0, "fog": 0.0, "commands": 0.0,
    })
    if engine.is_terminal():
        break

logger.close()
print(f"Wrote {OUT}  —  {engine.tick} ticks  A={len(engine.get_survivors(0))} B={len(engine.get_survivors(1))}")
