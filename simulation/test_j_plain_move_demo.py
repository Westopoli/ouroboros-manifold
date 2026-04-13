"""
test_j_plain_move_demo.py — Verify the plain-move no-halt fix.

Setup: 10 Strike units start on the left. 10 Line units are stationary
in the center (no commands). Strike units are issued a plain "move"
command past the center to the right side of the map.

Expected (post-fix): Strike units pass through Line's engagement range
without stopping. They do not acquire targets, do not return fire, and
complete the crossing. Verification: count units that reach the far side.

Run: python3 test_j_plain_move_demo.py
View: python3 sim_viewer.py /tmp/j_plain_move_demo.jsonl
"""
import sys
import time
sys.path.insert(0, ".")

import config
from unit import UnitStore
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field
from sim_logger import SimLogger, config_snapshot

OUT       = "/tmp/j_plain_move_demo.jsonl"
DT        = config.TACTICAL_TICK_DURATION
MAX_TICKS = 3000  # 150 sec — plenty for units to cross

tmap  = open_field()
store = UnitStore()

# Strike force: left side of map, moving right
STRIKE_START_X = 400.0
STRIKE_DEST_X  = 3600.0
LINE_CENTER_X  = 2000.0
CENTER_Y       = 2000.0

strike_uids = []
for i in range(10):
    x = STRIKE_START_X + (i % 5) * 40.0
    y = CENTER_Y + (i // 5 - 0.5) * 80.0
    strike_uids.append(store.spawn("Raider", 0, x, y))

# Line force: stationary in center — no commands issued
line_uids = []
for i in range(10):
    x = LINE_CENTER_X + (i % 5) * 40.0
    y = CENTER_Y + (i // 5 - 0.5) * 80.0
    line_uids.append(store.spawn("Vanguard", 1, x, y))

# Issue plain "move" command for Strike to cross to the far side
queue = CommandQueue()
queue.add(Command(tick=0, type="move", unit_ids=strike_uids,
                  params={"target_x": STRIKE_DEST_X, "target_y": CENTER_Y}))

engine = TacticalEngine(tmap, store, seed=1)
engine.command_queue = queue

logger = SimLogger(OUT, "plain_move_demo", tmap,
                   {0: ("Strike", "#3b82f6"), 1: ("Line_stationary", "#ef4444")},
                   config_snapshot())

first_contact_tick = None
halt_count = 0
completed_crossing = 0

for t in range(MAX_TICKS):
    engine.step()
    logger.log_tick(engine.tick, engine.store, [], {
        "targeting": 0.0, "movement": 0.0, "abilities": 0.0,
        "damage": 0.0, "fog": 0.0, "commands": 0.0,
    })

    # Sample every 50 ticks for analysis
    if t % 50 == 0:
        for uid in strike_uids:
            if not store.alive[uid]:
                continue
            x = store.data[uid, 0]  # FIELD_X
            tgt = store.auto_engage_target[uid]
            # Count units that halted (have a target and stopped moving)
            if tgt >= 0 and store.alive[tgt] and not store.has_move_target[uid]:
                halt_count += 1
            if first_contact_tick is None:
                # Check if any Strike entered Line's engagement range
                for lid in line_uids:
                    if store.alive[lid]:
                        lx = store.data[lid, 0]
                        ly = store.data[lid, 1]
                        sx = store.data[uid, 0]
                        sy = store.data[uid, 1]
                        import math
                        engage_range = store.data[lid, 7]  # FIELD_ATTACK_RANGE
                        if math.sqrt((sx - lx)**2 + (sy - ly)**2) <= engage_range:
                            first_contact_tick = engine.tick

    # Check completion: how many Strike are past the center?
    if engine.tick == MAX_TICKS - 1 or all(
        not store.alive[uid] or store.data[uid, 0] >= STRIKE_DEST_X - 50
        for uid in strike_uids
    ):
        for uid in strike_uids:
            if store.alive[uid] and store.data[uid, 0] >= STRIKE_DEST_X - 50:
                completed_crossing += 1
        break

logger.close()

print(f"\n{'═'*60}")
print(f"  PLAIN MOVE NO-HALT DEMO")
print(f"{'═'*60}")
print(f"  Duration: {engine.tick} ticks ({engine.tick * DT:.1f}s)")
print(f"  First contact tick: {first_contact_tick} ({first_contact_tick * DT:.1f}s)" if first_contact_tick else "  No contact detected")
print(f"")
print(f"  Strike units:        {len(strike_uids)}")
print(f"  Completed crossing:  {completed_crossing}")
print(f"  Halt events (50-tick samples): {halt_count}")
print(f"")

alive_strike = sum(1 for u in strike_uids if store.alive[u])
alive_line   = sum(1 for u in line_uids   if store.alive[u])
strike_hp    = sum(store.data[u, 3] for u in strike_uids if store.alive[u])  # FIELD_HP
line_hp      = sum(store.data[u, 3] for u in line_uids   if store.alive[u])

print(f"  Strike alive: {alive_strike}  HP remaining: {strike_hp:.0f}")
print(f"  Line alive:   {alive_line}   HP remaining: {line_hp:.0f}")
print(f"")

if halt_count == 0 and completed_crossing > 0:
    print(f"  PASS — Strike passed through without halting")
elif halt_count > 0:
    print(f"  FAIL — {halt_count} halt events detected (plain_moving fix not working)")
else:
    print(f"  INCONCLUSIVE — no units completed crossing")

print(f"\n  View: python3 sim_viewer.py {OUT}")
print(f"{'═'*60}\n")
