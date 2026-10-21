# Rule pins: R-126-02@2361a1
"""W-1b pipe test: structure production adds player-faction unit within timer.

Uses pipe/ouroboros_pipe_dbg (debug build): place_structure is a TEST AND DEBUG
VERB gated by OM_DEBUG_INJECT, same as objective_complete (docs/architecture.md).

Setup: seed 1, 80 regions, strategic features 1..7, 10 strategic steps.
mission_start faction 0, mission_begin. The 10 strategic steps produce units in
the tactical world so om_tactical_step calls om_support_tick (tactical_step is
a no-op when n_units==0; om_support_tick drives production per base tick).
R-126-02 (as rewritten, TD-VG-E-29): the produced unit stands at the first free slot of the
structure's spawn lattice, drawing nothing; this test counts units only.

place_structure kind=0 (RAIDER), owner=0 (E-05 player faction id; with W-1d
neutral becomes -1, so owner=0 means player faction 0). Then step 600 ticks
(RAIDER production interval ~540 ticks at power~90/100); a new unit must appear.

Owner-convention note: on today's main the production driver guards s->owner==0
as neutral and skips production. With W-1d (neutral = -1), owner=0 is treated as
E-05 faction 0 (player), enabling production. This test is therefore:
  - RED on main (without W-1d): no production for owner=0 -> unit count unchanged.
  - GREEN after W-1d lands: owner=0 drives player spawn.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"

pytestmark = pytest.mark.skipif(
    not PIPE_DBG.exists(), reason="pipe/ouroboros_pipe_dbg not built")

FEATURES = [1, 2, 3, 4, 5, 6, 7]


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


def test_player_structure_adds_unit_within_timer():
    """A player-owned production structure adds a player-faction unit within
    its production interval, visible as a new unit in the tactical frame.

    place_structure kind=0 (RAIDER) owner=0 (E-05 player faction with faction=0
    mission). 600 tactical steps exceed the ~540-tick RAIDER production interval
    (power~90, 30s*0.9 = 27s, 27*20 ticks = 540). Unit count must increase.

    Red on main (without W-1d): owner=0 treated as neutral, no production.
    Green after W-1d: owner=0 is E-05 faction 0, production spawns player unit.
    """
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
    ]
    frames_setup = _run(cmds)
    begin_tactical = next(
        (f for f in frames_setup if f.get("type") == "tactical"), None)
    assert begin_tactical is not None, (
        "mission_begin must produce a tactical frame; got: %r"
        % [f.get("type") for f in frames_setup])
    initial_unit_count = len(begin_tactical.get("units", []))
    assert initial_unit_count > 0, (
        "positive control: 10 strategic steps must place units in the world; "
        "got 0 units after mission_begin (om_tactical_step no-op without units)")

    cmds2 = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        # owner=0 = E-05 faction 0 (player with mission_start faction=0).
        # W-1d required: on main owner=0 is neutral, no production.
        {"type": "cmd", "name": "place_structure", "kind": 0, "owner": 0,
         "x": 0.0, "y": 0.0},
        {"type": "cmd", "name": "tactical_step", "n": 600},
    ]
    frames = _run(cmds2)
    tacticals = [f for f in frames if f.get("type") == "tactical"]
    assert tacticals, "tactical_step n=600 must produce tactical frames"
    final_unit_count = len(tacticals[-1].get("units", []))
    assert final_unit_count > initial_unit_count, (
        "R-126-02: player-owned structure must spawn a unit within the production "
        "interval (600 steps > ~540-tick RAIDER interval); unit count must exceed "
        "initial %d, got %d. "
        "On main (without W-1d) owner=0 is neutral -> no production -> this fails."
        % (initial_unit_count, final_unit_count))
