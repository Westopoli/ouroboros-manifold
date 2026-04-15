"""Generate viewer dump for L2: Siege vs Line, seed 1 (draws at 500s)."""
import random
from sim_logger import SimLogger, config_snapshot
from unit import UnitStore
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field

DUMP_PATH = "/tmp/l2_siege_vs_line.jsonl"
FACTION_A, FACTION_B = 0, 1
SEED = 1

rng = random.Random(SEED)
tmap = open_field()
store = UnitStore()

types = {"Siege": ["Bombard", "Bastion"], "Line": ["Vanguard", "Warden"]}

def spawn(store, cat, faction, cx, cy, count, rng):
    ut_list = types[cat]
    uids = []
    for i in range(count):
        ut = ut_list[i % len(ut_list)]
        x = cx + (i % 5) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // 5) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids

uids_a = spawn(store, "Siege", FACTION_A, 1700.0, 1850.0, 10, rng)
uids_b = spawn(store, "Line",  FACTION_B, 2100.0, 1850.0, 10, rng)

queue = CommandQueue()
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                  params={"target_x": 2000.0, "target_y": 2000.0}))
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                  params={"target_x": 2000.0, "target_y": 2000.0}))

factions = {FACTION_A: ("Siege", "#3b82f6"), FACTION_B: ("Line", "#ef4444")}
logger = SimLogger(DUMP_PATH, "l2_siege_vs_line", tmap, factions, config_snapshot())

engine = TacticalEngine(tmap, store, seed=SEED)
engine.command_queue = queue

for _ in range(10000):
    logger.log_tick(engine.tick, engine.store, [], {})
    engine.step()
    if engine.is_terminal():
        break

logger.log_tick(engine.tick, engine.store, [], {})
logger.close()
print(f"Dump written: {DUMP_PATH}  ({engine.tick} ticks)")
print(f"View: python3 sim_viewer.py {DUMP_PATH}")
