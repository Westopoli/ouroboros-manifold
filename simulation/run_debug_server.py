"""
Checkpoint F debug server — starts the socket server with a live test mission.
Run this before opening the debug_ws_test scene in Godot.

  python3 simulation/run_debug_server.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tactical_engine import TacticalEngine
from test_maps import open_field
from command import Command
from socket_server import run


def make_engine():
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=42)
    engine.player_faction = 0

    TYPES_A = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
               "Warden", "Bombard", "Bastion"]
    TYPES_B = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
               "Warden", "Bombard", "Bastion"]

    for i, ut in enumerate(TYPES_A):
        engine.store.spawn(ut, 0, 400.0 + i * 150.0, 500.0)
    for i, ut in enumerate(TYPES_B):
        engine.store.spawn(ut, 1, 400.0 + i * 150.0, 3500.0)

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
    return engine


if __name__ == "__main__":
    import os as _os
    print("Starting debug server on 127.0.0.1:8765 — open debug_ws_test.tscn in Godot")
    print("Ctrl-C to stop")
    try:
        run(engine_factory=make_engine)
        print("DEBUG: run() returned normally")
    except BaseException as e:
        print(f"DEBUG: run() raised {type(e).__name__}: {e}")
    finally:
        print("DEBUG: finally block reached — calling _exit")
        _os._exit(0)
