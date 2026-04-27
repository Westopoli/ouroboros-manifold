import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(__file__))

from tactical_engine import TacticalEngine
from tactical_map import TacticalMap, SpineNode
from reinforcement import ReinforcementStructure
from command import Command
from snapshot_serializer import full_snapshot, delta, delta_baseline, DeadReckoningTracker
import config

UNIT_ROSTER = ["Vanguard", "Vanguard", "Vanguard", "Warden",
               "Raider", "Raider", "Interceptor", "Interceptor",
               "Bombard", "Bastion"]
UNITS_PER_SIDE = 200
TICKS = 300
REPORT_EVERY = 50


def make_engine():
    tmap = TacticalMap(
        width=8000, height=8000, layers=1,
        spine_nodes=[
            SpineNode(position=(3000.0, 3000.0), node_type="reinforcement_structure", properties={}),
            SpineNode(position=(5000.0, 5000.0), node_type="reinforcement_structure", properties={}),
        ],
    )
    engine = TacticalEngine(tmap, seed=42)
    engine.player_faction = 0
    cols = 20
    for i in range(UNITS_PER_SIDE):
        ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
        x = 400.0 + (i % cols) * 180.0
        y = 400.0 + (i // cols) * 120.0
        engine.store.spawn(ut, 0, x, y)
    for i in range(UNITS_PER_SIDE):
        ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
        x = 400.0 + (i % cols) * 180.0
        y = 7600.0 - (i // cols) * 120.0
        engine.store.spawn(ut, 1, x, y)
    a_ids = engine.store.active_ids_for_faction(0)
    engine.command_queue.add(Command(tick=0, type="attack_move", unit_ids=a_ids,
                                     params={"target_x": 4000.0, "target_y": 7000.0}))
    b_ids = engine.store.active_ids_for_faction(1)
    engine.command_queue.add(Command(tick=0, type="attack_move", unit_ids=b_ids,
                                     params={"target_x": 4000.0, "target_y": 1000.0}))
    engine.reinforcement_structures = [
        ReinforcementStructure(structure_uid=9000, position=(3000.0, 3000.0), layer=0,
                               hp=100.0, max_hp=100.0, owner_faction=0,
                               capture_progress=0.0, production_timer_sec=0.0,
                               production_target_unit_type="Vanguard", capture_radius=200.0),
        ReinforcementStructure(structure_uid=9001, position=(5000.0, 5000.0), layer=0,
                               hp=75.0, max_hp=100.0, owner_faction=1,
                               capture_progress=0.3, production_timer_sec=0.0,
                               production_target_unit_type="Vanguard", capture_radius=200.0),
    ]
    return engine


engine = make_engine()
dr_tracker = DeadReckoningTracker()
prev = full_snapshot(engine)

t_step = []
t_ser = []
t_baseline = []
t_json_pkt = []
t_total = []

print(f"Running {TICKS} ticks with {UNITS_PER_SIDE}v{UNITS_PER_SIDE} units")
print(f"{'tick':>6}  {'step':>8}  {'ser':>8}  {'base':>8}  {'json':>8}  {'total':>8}  {'alive':>6}  note")
print(f"{'':>6}  {'(ms)':>8}  {'(ms)':>8}  {'(ms)':>8}  {'(ms)':>8}  {'(ms)':>8}")

for tick in range(TICKS):
    t0_total = time.perf_counter()

    t0 = time.perf_counter()
    engine.step()
    dt_step = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    is_snap = (tick > 0 and tick % 100 == 0)
    if is_snap:
        pkt = full_snapshot(engine)
        dr_tracker.reset()
    else:
        pkt = delta(engine, prev, dr_tracker)
    dt_ser = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    prev = delta_baseline(engine)
    dt_baseline = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    encoded = (json.dumps(pkt) + "\n").encode()
    dt_json = (time.perf_counter() - t0) * 1000

    dt_total = (time.perf_counter() - t0_total) * 1000

    t_step.append(dt_step)
    t_ser.append(dt_ser)
    t_baseline.append(dt_baseline)
    t_json_pkt.append(dt_json)
    t_total.append(dt_total)

    if (tick + 1) % REPORT_EVERY == 0:
        r = slice(-REPORT_EVERY, None)
        alive = sum(1 for uid in range(engine.store.count) if engine.store.alive[uid])
        note = ""
        if is_snap:
            note = "[snapshot]"
        print(f"{tick+1:>6}  "
              f"{sum(t_step[r])/REPORT_EVERY:>8.1f}  "
              f"{sum(t_ser[r])/REPORT_EVERY:>8.1f}  "
              f"{sum(t_baseline[r])/REPORT_EVERY:>8.1f}  "
              f"{sum(t_json_pkt[r])/REPORT_EVERY:>8.1f}  "
              f"{sum(t_total[r])/REPORT_EVERY:>8.1f}  "
              f"{alive:>6}  {note}")

print(f"\n--- OVERALL ({TICKS} ticks) ---")
print(f"  step:     avg={sum(t_step)/len(t_step):.1f}ms  max={max(t_step):.1f}ms")
print(f"  ser:      avg={sum(t_ser)/len(t_ser):.1f}ms  max={max(t_ser):.1f}ms")
print(f"  baseline: avg={sum(t_baseline)/len(t_baseline):.1f}ms  max={max(t_baseline):.1f}ms")
print(f"  json:     avg={sum(t_json_pkt)/len(t_json_pkt):.1f}ms  max={max(t_json_pkt):.1f}ms")
print(f"  total:    avg={sum(t_total)/len(t_total):.1f}ms  max={max(t_total):.1f}ms")
print(f"  overhead: {sum(t_total)/len(t_total) - sum(t_step)/len(t_step):.1f}ms avg (ser+base+json)")
print(f"  effective Hz: {1000.0 / (sum(t_total)/len(t_total)):.1f}")
json_bytes = len(encoded)
print(f"  last pkt size: {json_bytes} bytes")
