"""Generate a visualizer dump of the L4 flank scenario (Strike vs Line, seed 1)."""
import random
import sys
sys.path.insert(0, ".")

import config
from unit import UnitStore
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import chokepoint
from sim_logger import SimLogger, config_snapshot

FACTION_A = 0
FACTION_B = 1
DUMP_PATH = "/tmp/j_flank_seed1.jsonl"
MAX_TICKS = 6000

rng = random.Random(1)
tmap = chokepoint()
store = UnitStore()

line_uids = []
for i in range(10):
    ut = "Vanguard" if i % 3 != 2 else "Warden"
    x = 2000.0 + (i % 5) * 40.0 + rng.uniform(-15, 15)
    y = 2500.0 + (i // 5) * 40.0 + rng.uniform(-15, 15)
    line_uids.append(store.spawn(ut, FACTION_B, x, y))

strike_uids = []
for i in range(10):
    ut = "Raider" if i % 2 == 0 else "Interceptor"
    x = 2000.0 + (i % 5) * 40.0 + rng.uniform(-15, 15)
    y = 1200.0 + (i // 5) * 40.0 + rng.uniform(-15, 15)
    strike_uids.append(store.spawn(ut, FACTION_A, x, y))

queue = CommandQueue()
queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 1800.0}))
queue.add(Command(tick=150, type="fast_move", unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 3200.0}))
queue.add(Command(tick=300, type="group_move", unit_ids=strike_uids,
                  params={"target_x": 2000.0, "target_y": 2500.0}))

engine = TacticalEngine(tmap, store, seed=1)
engine.command_queue = queue

logger = SimLogger(
    DUMP_PATH, "L4_flank_seed1", tmap,
    {FACTION_A: ("Strike", "#3b82f6"), FACTION_B: ("Line", "#ef4444")},
    config_snapshot(),
)

for _ in range(MAX_TICKS):
    prev = len(engine.death_log)
    engine.step()
    deaths = [d["uid"] for d in engine.death_log[prev:]]
    logger.log_tick(engine.tick, engine.store, deaths, {
        "targeting": 0.0, "movement": 0.0, "abilities": 0.0,
        "damage": 0.0, "fog": 0.0, "commands": 0.0,
    })
    if engine.is_terminal():
        break

logger.close()
print(f"Written: {DUMP_PATH}")
print(f"View:    python3 sim_viewer.py {DUMP_PATH}")
