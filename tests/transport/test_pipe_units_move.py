"""T1-7: units must move over the pipe after a move command (blocks real play).

Before this piece there was no transport test proving that a move command followed by
tactical steps actually changes a player unit's position in the pipe's tactical frame.
The ctypes E-13 tests (tests/csim/test_E13_*.py) proved movement in isolation (single
spawned units with clear paths); this test proves movement reaches the client through
the pipe in a real mission.

Setup (same seed/region/feature/step count as the other transport tests):
  set_seed 1, 80 regions, strategic features 1..7, step 10, mission_start faction 0,
  mission_begin, then a move command on player unit 17 (id=17 in this world; the
  rightmost unit in the first spawn row, at the edge of the spawn cluster and the
  only one in its neighbourhood with a clear NE path), then 20 tactical_step frames.

Positive control: the begin frame must show unit 17 at its spawn position; if it
does not, the world diverged from the expected setup and the move-distance assertion
would be vacuously correct.

Acceptance: R-095-07 (a single unit moves at its own speed to the click point):
  - After 20 steps the unit's position must differ from spawn by at least the
    minimum step-distance times the step count (at 20 tps, Raider speed 150 wu/s,
    step_dist = 7.5 wu/tick; 20 ticks x 7.5 = 150 wu total; steering deflections
    and collision reduce this, so we require >= 50% of theoretical: 75 wu).
  - The displacement vector from spawn to final position must point toward the
    commanded destination (dot product with the destination direction > 0).
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
STEP10 = {"type": "cmd", "name": "step", "n": 10}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}

# Unit 17 (seed 1, 80 regions, 10 strategic steps, faction 0): rightmost of the
# first spawn row.  It has a clear NE path unlike units 1..16 which are surrounded
# by neighbours on all ±90° probe headings.
UNIT_ID = 17
SPAWN_X = 12240.0
SPAWN_Y = 15.0
# Destination: 500 wu NE of spawn (heading ~45°, clear path for this unit).
DEST_X = SPAWN_X + 500.0
DEST_Y = SPAWN_Y + 500.0

# R-095-07: Raider native speed 150 wu/s, OM_TACTICAL_TICK_RATE 20 tps.
# step_dist = 150 / 20 = 7.5 wu/tick. 20 ticks x 7.5 = 150 wu theoretical.
# Require at least 50% (75 wu) to tolerate steering and minor collision pushback.
MIN_DIST_WU = 75.0
N_STEPS = 20

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


@pytest.fixture(scope="module")
def movement_frames():
    cmds = [SET_SEED, STEP10, START, BEGIN,
            {"type": "cmd", "name": "command", "verb": "move",
             "units": [UNIT_ID], "x": DEST_X, "y": DEST_Y}]
    for _ in range(N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    frames = _run(cmds)
    tactical = [f for f in frames if f["type"] == "tactical"]
    # mission_begin writes one tactical frame; N_STEPS more follow.
    assert len(tactical) == N_STEPS + 1, (
        "expected %d tactical frames (1 begin + %d steps), got %d: %r"
        % (N_STEPS + 1, N_STEPS, len(tactical), [f["type"] for f in frames]))
    begin = tactical[0]
    final = tactical[-1]
    return begin, final


def test_unit_at_spawn_in_begin_frame(movement_frames):
    """Positive control: unit UNIT_ID must start at SPAWN_X, SPAWN_Y in the begin
    frame; if the world diverged the move-distance assertion below would be vacuous."""
    begin, _ = movement_frames
    units = {u["id"]: u for u in begin.get("units", [])}
    assert UNIT_ID in units, (
        "unit %d absent from mission_begin tactical frame (world may have changed)" % UNIT_ID)
    u = units[UNIT_ID]
    assert u["x"] == pytest.approx(SPAWN_X, abs=1.0), (
        "unit %d spawn x diverged: %.2f != %.2f" % (UNIT_ID, u["x"], SPAWN_X))
    assert u["y"] == pytest.approx(SPAWN_Y, abs=1.0), (
        "unit %d spawn y diverged: %.2f != %.2f" % (UNIT_ID, u["y"], SPAWN_Y))


def test_unit_moved_from_spawn(movement_frames):
    """After %d tactical steps the unit must have left its spawn by at least
    %.0f wu (50%% of theoretical step-distance at Raider speed).""" % (N_STEPS, MIN_DIST_WU)
    begin, final = movement_frames
    begin_units = {u["id"]: u for u in begin.get("units", [])}
    final_units = {u["id"]: u for u in final.get("units", [])}
    assert UNIT_ID in begin_units, "unit %d not in begin frame" % UNIT_ID
    assert UNIT_ID in final_units, "unit %d not in final frame after %d steps" % (UNIT_ID, N_STEPS)
    bu = begin_units[UNIT_ID]
    fu = final_units[UNIT_ID]
    dx = fu["x"] - bu["x"]
    dy = fu["y"] - bu["y"]
    dist = (dx * dx + dy * dy) ** 0.5
    assert dist >= MIN_DIST_WU, (
        "unit %d did not move: spawn=(%.2f,%.2f) final=(%.2f,%.2f) dist=%.2f < %.0f wu"
        % (UNIT_ID, bu["x"], bu["y"], fu["x"], fu["y"], dist, MIN_DIST_WU))


def test_unit_moved_toward_destination(movement_frames):
    """The displacement from spawn to final position must point toward the
    commanded destination (dot product with destination direction > 0)."""
    begin, final = movement_frames
    begin_units = {u["id"]: u for u in begin.get("units", [])}
    final_units = {u["id"]: u for u in final.get("units", [])}
    assert UNIT_ID in begin_units and UNIT_ID in final_units, (
        "unit %d missing from begin or final frame" % UNIT_ID)
    bu = begin_units[UNIT_ID]
    fu = final_units[UNIT_ID]
    # displacement vector
    disp_x = fu["x"] - bu["x"]
    disp_y = fu["y"] - bu["y"]
    # toward-destination direction
    toward_x = DEST_X - bu["x"]
    toward_y = DEST_Y - bu["y"]
    dot = disp_x * toward_x + disp_y * toward_y
    assert dot > 0.0, (
        "unit %d moved away from destination: spawn=(%.2f,%.2f) final=(%.2f,%.2f) "
        "dest=(%.2f,%.2f) dot=%.2f"
        % (UNIT_ID, bu["x"], bu["y"], fu["x"], fu["y"], DEST_X, DEST_Y, dot))
