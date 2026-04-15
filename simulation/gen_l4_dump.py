"""Generate viewer dump for L4: Strike flank vs Line, seed 1."""
import math
import random
from sim_logger import SimLogger, config_snapshot
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_ATTACK_RANGE
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import chokepoint

DUMP_PATH = "/tmp/l4_strike_flank_vs_line.jsonl"
FACTION_A, FACTION_B = 0, 1
SEED = 1

rng = random.Random(SEED)
tmap = chokepoint()
store = UnitStore()

def spawn_strike(store, faction, cx, cy, count, rng):
    uids = []
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids

def spawn_line(store, faction, cx, cy, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids

strike_uids = spawn_strike(store, FACTION_A, 2000.0, 1200.0, 10, rng)
line_uids   = spawn_line(store,   FACTION_B, 2000.0, 2500.0, 10, rng)

queue = CommandQueue()
queue.add(Command(tick=0,   type="attack_move", unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 1800.0}))
queue.add(Command(tick=150, type="move",        unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 3200.0}))
queue.add(Command(tick=300, type="attack_move", unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 2500.0}))
queue.add(Command(tick=0,   type="attack_move", unit_ids=line_uids,
                  params={"target_x": 2000.0, "target_y": 2000.0}))

factions = {FACTION_A: ("Strike", "#ef4444"), FACTION_B: ("Line", "#3b82f6")}
logger = SimLogger(DUMP_PATH, "l4_strike_flank_vs_line", tmap, factions, config_snapshot())

engine = TacticalEngine(tmap, store, seed=SEED)
engine.command_queue = queue

for _ in range(6000):
    logger.log_tick(engine.tick, engine.store, [], {})
    engine.step()
    if engine.is_terminal():
        break

logger.log_tick(engine.tick, engine.store, [], {})
logger.close()
print(f"Dump written: {DUMP_PATH}  ({engine.tick} ticks)")
print(f"View: python3 sim_viewer.py {DUMP_PATH}")
