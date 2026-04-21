"""
Checkpoint F debug server — starts the socket server with a live test mission.
Run this before opening the debug_ws_test scene in Godot.

  python3 simulation/run_debug_server.py
"""

import sys
import os
import time
import json as _json
sys.path.insert(0, os.path.dirname(__file__))

from tactical_engine import TacticalEngine
from tactical_map import TacticalMap, SpineNode, GradientSource
from reinforcement import ReinforcementStructure
from command import Command
from socket_server import run
import socket_server            # for monkeypatching full_snapshot/delta
import snapshot_serializer
import perf_logger

UNIT_ROSTER = ["Vanguard", "Vanguard", "Vanguard", "Warden",
               "Raider", "Raider", "Interceptor", "Interceptor",
               "Bombard", "Bastion"]
UNITS_PER_SIDE = 200


# ── Perf instrumentation ────────────────────────────────────────────────────
# socket_server.py is protected; we patch it non-invasively by replacing its
# references to full_snapshot/delta (captured by `from X import Y`) at the
# socket_server module level. See simulation/perf_logger.py for the log format.

_perf = {"step_ms": 0.0, "logged_tick": -1}

_orig_full = snapshot_serializer.full_snapshot
_orig_delta = snapshot_serializer.delta


_tick_times = []

def _wrap_step(engine):
    orig = engine.step

    def timed_step():
        t0 = time.perf_counter()
        orig()
        elapsed = (time.perf_counter() - t0) * 1000.0
        _perf["step_ms"] = elapsed
        _tick_times.append(elapsed)
        if len(_tick_times) % 50 == 0:
            recent = _tick_times[-50:]
            avg = sum(recent) / len(recent)
            mx = max(recent)
            print(f"  tick {len(_tick_times):>4}  step_avg={avg:.1f}ms  step_max={mx:.1f}ms")

    engine.step = timed_step


def _wrapped_full_snapshot(engine):
    t0 = time.perf_counter()
    result = _orig_full(engine)
    ser_ms = (time.perf_counter() - t0) * 1000.0
    if engine.tick != _perf["logged_tick"]:
        perf_logger.log({
            "tick": engine.tick,
            "msg": "snapshot",
            "step_ms": round(_perf["step_ms"], 3),
            "ser_ms": round(ser_ms, 3),
            "units_total": len(result.get("units", [])),
        })
        _perf["logged_tick"] = engine.tick
    return result


def _wrapped_delta(engine, prev_state, dr_tracker=None):
    t0 = time.perf_counter()
    result = _orig_delta(engine, prev_state, dr_tracker)
    ser_ms = (time.perf_counter() - t0) * 1000.0
    if engine.tick != _perf["logged_tick"]:
        perf_logger.log({
            "tick": engine.tick,
            "msg": "delta",
            "step_ms": round(_perf["step_ms"], 3),
            "ser_ms": round(ser_ms, 3),
            "units_updated": len(result.get("units_updated", [])),
            "units_added": len(result.get("units_added", [])),
            "units_removed": len(result.get("units_removed", [])),
        })
        _perf["logged_tick"] = engine.tick
    return result


socket_server.full_snapshot = _wrapped_full_snapshot
socket_server.delta = _wrapped_delta


def make_engine():
    tmap = TacticalMap(
        width=4000, height=4000, layers=1,
        spine_nodes=[
            SpineNode(position=(1500.0, 1500.0),
                      node_type="reinforcement_structure", properties={}),
            SpineNode(position=(2500.0, 2500.0),
                      node_type="reinforcement_structure", properties={}),
        ],
        gradient_sources=[
            GradientSource(position=(1000.0, 2000.0), property_type="obstacle_density",
                           radius=600, intensity=0.7),
            GradientSource(position=(3000.0, 2000.0), property_type="obstacle_density",
                           radius=500, intensity=0.5),
        ],
    )
    engine = TacticalEngine(tmap, seed=42)
    engine.player_faction = 0

    cols = 20
    for i in range(UNITS_PER_SIDE):
        ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
        x = 200.0 + (i % cols) * 180.0
        y = 200.0 + (i // cols) * 120.0
        engine.store.spawn(ut, 0, x, y)
    for i in range(UNITS_PER_SIDE):
        ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
        x = 200.0 + (i % cols) * 180.0
        y = 3800.0 - (i // cols) * 120.0
        engine.store.spawn(ut, 1, x, y)

    a_ids = engine.store.active_ids_for_faction(0)
    engine.command_queue.add(Command(
        tick=0, type="attack_move", unit_ids=a_ids,
        params={"target_x": 2000.0, "target_y": 3500.0},
    ))
    b_ids = engine.store.active_ids_for_faction(1)
    engine.command_queue.add(Command(
        tick=0, type="attack_move", unit_ids=b_ids,
        params={"target_x": 2000.0, "target_y": 500.0},
    ))

    engine.reinforcement_structures = [
        ReinforcementStructure(
            structure_uid=9000, position=(1500.0, 1500.0), layer=0,
            hp=100.0, max_hp=100.0, owner_faction=0,
            capture_progress=0.0, production_timer_sec=0.0,
            production_target_unit_type="Vanguard", capture_radius=200.0,
        ),
        ReinforcementStructure(
            structure_uid=9001, position=(2500.0, 2500.0), layer=0,
            hp=75.0, max_hp=100.0, owner_faction=1,
            capture_progress=0.3, production_timer_sec=0.0,
            production_target_unit_type="Vanguard", capture_radius=200.0,
        ),
    ]
    _wrap_step(engine)
    return engine


if __name__ == "__main__":
    perf_logger.start("logs/sim_perf.jsonl")
    print("Starting debug server on 127.0.0.1:8765 — open debug_ws_test.tscn in Godot")
    print("Perf log → logs/sim_perf.jsonl")
    print("Ctrl-C to stop")
    try:
        run(engine_factory=make_engine)
    finally:
        perf_logger.close()
