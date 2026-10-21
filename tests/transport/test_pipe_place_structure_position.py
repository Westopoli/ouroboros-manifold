"""W-1e: place_structure x/y sets structure position via om_structure_set_position.

place_structure with a non-origin x/y places the structure at that position.
After enough tactical steps the produced unit appears near the given point
(at a spawn-lattice slot within half the capture radius = 150 wu, R-126-02 as rewritten, TD-VG-E-29), not near the origin.

Red on main (W-1e not applied): (void)x; (void)y discards the coordinates,
structure stays at (0,0), unit spawns within 150 wu of origin, not of (1000,0).
Green after W-1e: om_structure_set_position is called, unit spawns near (1000,0).
"""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"

pytestmark = pytest.mark.skipif(
    not PIPE_DBG.exists(), reason="pipe/ouroboros_pipe_dbg not built")

FEATURES = [1, 2, 3, 4, 5, 6, 7]
STRUCT_X = 1000.0
STRUCT_Y = 0.0
STRUCT_OWNER = 0
# Half capture radius: R-126-02 bound (150 wu inclusive, the spawn lattice's bound, TD-VG-E-29); unit spawns within this of the structure.
HALF_CAP_RADIUS = 150.0
# 1 wu tighter bound: unit must be closer to the given point than to origin.
CLOSER_BOUND = 1.0


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    quit_cmd = {"type": "cmd", "name": "quit"}
    script = b"".join(_frame(c) for c in cmds + [quit_cmd])
    proc = subprocess.run([str(PIPE_DBG)], input=script, capture_output=True,
                          timeout=120)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _dist(u, x, y):
    return math.sqrt((u["x"] - x) ** 2 + (u["y"] - y) ** 2)


def test_place_structure_position_applied():
    """place_structure at (1000, 0) must produce a unit within 150 wu of
    (1000, 0). On main (x/y discarded) the structure sits at (0,0) and the
    unit spawns near origin, failing this assertion.

    R-126-02: spawn at the first free lattice slot within half capture radius of structure position (TD-VG-E-29).
    W-1e: position is applied via om_structure_set_position.
    """
    setup = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
    ]
    frames_setup = _run(setup)
    begin_tactical = next(
        (f for f in frames_setup if f.get("type") == "tactical"), None)
    assert begin_tactical is not None, (
        "mission_begin must produce a tactical frame")
    initial_ids = {u["id"] for u in begin_tactical.get("units", [])}
    assert initial_ids, (
        "positive control: 10 strategic steps must place units; "
        "got 0 units after mission_begin")

    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        # Structure at (1000, 0). owner=0 = E-05 player faction.
        {"type": "cmd", "name": "place_structure", "kind": 0, "owner": STRUCT_OWNER,
         "x": STRUCT_X, "y": STRUCT_Y},
        # 600 steps > ~540-tick RAIDER interval (power ~90, 27 s * 20 t/s).
        {"type": "cmd", "name": "tactical_step", "n": 600},
    ]
    frames = _run(cmds)
    tacticals = [f for f in frames if f.get("type") == "tactical"]
    assert tacticals, "tactical_step n=600 must produce tactical frames"

    final_units = tacticals[-1].get("units", [])
    # Mission setup (R-126-01, B9-N) places its own structures that spawn units
    # too; only units of the placed structure's faction are attributed to it, and
    # the nearest one must be the unit it spawned.
    new_units = [u for u in final_units
                 if u["id"] not in initial_ids and u["faction"] == STRUCT_OWNER]
    assert new_units, (
        "R-126-02: player-owned structure at (%.0f,%.0f) must spawn at least "
        "one unit within 600 steps (RAIDER interval ~540 ticks); none found. "
        "Check W-1d (owner=0 is player faction) is on main." % (STRUCT_X, STRUCT_Y))

    # The spawned unit must be within half the capture radius of the structure.
    nearest = min(new_units, key=lambda u: _dist(u, STRUCT_X, STRUCT_Y))
    for u in [nearest]:
        d = _dist(u, STRUCT_X, STRUCT_Y)
        assert d <= HALF_CAP_RADIUS + 1e-6, (
            "R-126-02 / W-1e: spawned unit at (%.2f,%.2f) is %.2f wu from "
            "structure (%.0f,%.0f); must be within %.0f wu. "
            "On main (x/y discarded) structure is at (0,0) -> unit spawns "
            "near origin, not near (%.0f,%.0f)."
            % (u["x"], u["y"], d, STRUCT_X, STRUCT_Y,
               HALF_CAP_RADIUS, STRUCT_X, STRUCT_Y))
