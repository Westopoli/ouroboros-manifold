"""T1-7: units must move over the pipe after a move command (blocks real play).

Before this piece there was no transport test proving that a move command followed by
tactical steps actually changes a player unit's position in the pipe's tactical frame.
The ctypes E-13 tests (tests/csim/test_E13_*.py) proved movement in isolation (single
spawned units with clear paths); this test proves movement reaches the client through
the pipe in a real mission.

Setup (same seed/region/feature/step count as the other transport tests):
  set_seed 1, 80 regions, strategic features 1..7, step 10, mission_start faction 0,
  mission_begin.

Part 1 -- single edge unit (R-095-07):
  Unit 21 (id=21, the first-row Raider at the pocket edge, clear NE path) is commanded alone
  to (SPAWN_X+500, SPAWN_Y+500).  After 20 tactical_step frames the unit must have
  moved >= 75 wu toward the destination.

Part 2 -- group speed-sync (R-095-01):
  The client sends all selected units in ONE command frame; handle_command must call
  om_command_group_move (not per-unit om_command_move) so the slowest member caps
  the group's speed (R-095-01: "all units move at the speed of the slowest member
  until the group has spread further than the magic box").

  Unit 21 (Raider, type 0, ~147 wu/s) and unit 294 (Bastion, type 5, ~40 wu/s)
  are both at the edge of the spawn formation and can both move.  Commanded together
  with om_command_move (the unfixed pipe), unit 21 races at Raider speed while
  unit 294 moves at Bastion speed: ratio ~3.7x.  With om_command_group_move (fixed),
  both are capped at the Bastion's speed: ratio ~1.0x.

  Positive controls:
    - Unit 21 must move (sanity check on the begin frame position).
    - Unit 294 must move (confirms the slow unit also has a clear path).

Seed-stability: unit ids and spawn positions are deterministic for seed 1 / 80 regions /
features [1..7] / 10 strategic steps / faction 0.  If the world changes, the begin-frame
position checks will fail first, making the cause obvious.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES,
            "new_campaign": False}
STEP10 = {"type": "cmd", "name": "step", "n": 10}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}

# Unit 21 (seed 1, 80 regions, 10 strategic steps, faction 0): rightmost of the
# first spawn row.  It has a clear NE path unlike units 1..22 which are surrounded
# by neighbours on all ±90° probe headings.
UNIT_ID = 21  # TD-VG-D-7: was 23 (unit 23 is now enclosed in the D8 pocket formation and cannot move)
SPAWN_X = 12080.0  # TD-VG-D-7: was 12330
SPAWN_Y = 120.0  # TD-VG-D-7: was 15
# Destination: 500 wu NE of spawn (heading ~45°, clear path for this unit).
DEST_X = SPAWN_X + 500.0
DEST_Y = SPAWN_Y + 500.0

# R-095-07: Raider native speed 150 wu/s, OM_TACTICAL_TICK_RATE 20 tps.
# step_dist = 150 / 20 = 7.5 wu/tick. 20 ticks x 7.5 = 150 wu theoretical.
# Require at least 50% (75 wu) to tolerate steering and minor collision pushback.
MIN_DIST_WU = 75.0

# Part 2 -- speed-sync group: Raider + Bastion edge pair (R-095-01).
# Both units are at the right/top edge of the formation and have a clear NE path.
# Unit 21: type 0 (Raider), ~147 wu/s solo.  Unit 294: type 5 (Bastion), ~40 wu/s solo.
# When commanded together via om_command_group_move (the fix), both move at Bastion speed.
# When commanded via om_command_move (the defect), Raider races ahead at 3.7x Bastion speed.
FAST_ID = 21    # Raider at (12080, 120); TD-VG-D-7: was unit 23 at (12330, 15)
# TD-VG-E-34 (pin move, start-count pins move with the starting-force cut, E7, Architect 2026-10-19): the player spawns
# start_units of F, not F. Premise (this seed/region, archetype 8): F 490, p 1, e 1, n 2, share 0.5, frac 0.6, start 294.0,
# start_units 294, so the player's units are ids 1..294 and the last Bastion is unit 294 (was unit 490 of F 490, an enemy
# unit now), at (12080, 550) (was (12420, 450)). Unit 21's pin is unchanged.
SLOW_ID = 294   # Bastion at (12080, 550); TD-VG-E-34: was unit 490 at (12420, 450); TD-VG-D-7: was (11850, 645)
SLOW_SPAWN_X = 12080.0
SLOW_SPAWN_Y = 550.0
# Shared destination: 1000 wu NE of the midpoint between the two units.
GROUP_DEST_X = (SPAWN_X + SLOW_SPAWN_X) / 2.0 + 1000.0   
GROUP_DEST_Y = (SPAWN_Y + SLOW_SPAWN_Y) / 2.0 + 1000.0   
# After 20 steps at Bastion speed (~40 wu/s, 2 wu/tick) both units should move ~40 wu.
# The solo Raider speed is ~147 wu/s (7.35 wu/tick × 20 = 147 wu).
# Both must have moved, and their displacement ratio must be <= 1.5 (speed-capped group).
GROUP_N_STEPS = 20
MAX_SPEED_RATIO = 1.5

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
    """Single-unit edge command (Part 1): unit 21 commanded alone."""
    cmds = [SET_SEED, STEP10, START, BEGIN,
            {"type": "cmd", "name": "command", "verb": "move",
             "units": [UNIT_ID], "x": DEST_X, "y": DEST_Y}]
    for _ in range(N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    frames = _run(cmds)
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) == N_STEPS + 1, (
        "expected %d tactical frames (1 begin + %d steps), got %d: %r"
        % (N_STEPS + 1, N_STEPS, len(tactical), [f["type"] for f in frames]))
    return tactical[0], tactical[-1]


@pytest.fixture(scope="module")
def group_frames():
    """Group command (Part 2): Raider + Bastion commanded together to shared destination."""
    cmds = [SET_SEED, STEP10, START, BEGIN,
            {"type": "cmd", "name": "command", "verb": "move",
             "units": [FAST_ID, SLOW_ID], "x": GROUP_DEST_X, "y": GROUP_DEST_Y}]
    for _ in range(GROUP_N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    frames = _run(cmds)
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) == GROUP_N_STEPS + 1, (
        "expected %d tactical frames, got %d" % (GROUP_N_STEPS + 1, len(tactical)))
    return tactical[0], tactical[-1]


# ---------------------------------------------------------------------------
# Part 1 tests (single unit, R-095-07)
# ---------------------------------------------------------------------------

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
    disp_x = fu["x"] - bu["x"]
    disp_y = fu["y"] - bu["y"]
    toward_x = DEST_X - bu["x"]
    toward_y = DEST_Y - bu["y"]
    dot = disp_x * toward_x + disp_y * toward_y
    assert dot > 0.0, (
        "unit %d moved away from destination: spawn=(%.2f,%.2f) final=(%.2f,%.2f) "
        "dest=(%.2f,%.2f) dot=%.2f"
        % (UNIT_ID, bu["x"], bu["y"], fu["x"], fu["y"], DEST_X, DEST_Y, dot))


# ---------------------------------------------------------------------------
# Part 2 tests (group speed-sync, R-095-01)
# ---------------------------------------------------------------------------

def test_group_spawn_positions(group_frames):
    """Positive control: both units must start at their known spawn positions.
    If they diverge, the speed-ratio assertion would compare units at wrong positions."""
    begin, _ = group_frames
    units = {u["id"]: u for u in begin.get("units", [])}
    assert FAST_ID in units, "unit %d (Raider) absent from begin frame" % FAST_ID
    assert SLOW_ID in units, "unit %d (Bastion) absent from begin frame" % SLOW_ID
    fu = units[FAST_ID]
    su = units[SLOW_ID]
    assert fu["x"] == pytest.approx(SPAWN_X, abs=1.0), (
        "unit %d spawn x: %.2f != %.2f" % (FAST_ID, fu["x"], SPAWN_X))
    assert fu["y"] == pytest.approx(SPAWN_Y, abs=1.0), (
        "unit %d spawn y: %.2f != %.2f" % (FAST_ID, fu["y"], SPAWN_Y))
    assert su["x"] == pytest.approx(SLOW_SPAWN_X, abs=1.0), (
        "unit %d spawn x: %.2f != %.2f" % (SLOW_ID, su["x"], SLOW_SPAWN_X))
    assert su["y"] == pytest.approx(SLOW_SPAWN_Y, abs=1.0), (
        "unit %d spawn y: %.2f != %.2f" % (SLOW_ID, su["y"], SLOW_SPAWN_Y))


def test_group_both_units_moved(group_frames):
    """Both the Raider and the Bastion must move (confirms both have a clear
    path and the command reached the sim)."""
    begin, final = group_frames
    begin_units = {u["id"]: u for u in begin.get("units", [])}
    final_units = {u["id"]: u for u in final.get("units", [])}
    for uid in (FAST_ID, SLOW_ID):
        assert uid in begin_units and uid in final_units, (
            "unit %d missing from begin or final frame" % uid)
        bu = begin_units[uid]
        fu = final_units[uid]
        dist = ((fu["x"] - bu["x"]) ** 2 + (fu["y"] - bu["y"]) ** 2) ** 0.5
        assert dist >= 5.0, (
            "unit %d did not move after %d steps: spawn=(%.2f,%.2f) final=(%.2f,%.2f)"
            % (uid, GROUP_N_STEPS, bu["x"], bu["y"], fu["x"], fu["y"]))


def test_group_speed_sync(group_frames):
    """R-095-01: when both units are commanded together via a single move command,
    the pipe must issue a group order (om_command_group_move) so their speeds are
    capped at the slowest member.  The Raider's solo speed is ~147 wu/s and the
    Bastion's is ~40 wu/s (ratio 3.7x); with speed-capping both move at ~40 wu/s
    (ratio ~1.0x).  The assertion allows up to %.1fx to tolerate minor path
    differences between the two units' trajectories.""" % MAX_SPEED_RATIO
    begin, final = group_frames
    begin_units = {u["id"]: u for u in begin.get("units", [])}
    final_units = {u["id"]: u for u in final.get("units", [])}
    bu_fast = begin_units[FAST_ID]
    fu_fast = final_units[FAST_ID]
    bu_slow = begin_units[SLOW_ID]
    fu_slow = final_units[SLOW_ID]
    fast_dist = ((fu_fast["x"] - bu_fast["x"]) ** 2 + (fu_fast["y"] - bu_fast["y"]) ** 2) ** 0.5
    slow_dist = ((fu_slow["x"] - bu_slow["x"]) ** 2 + (fu_slow["y"] - bu_slow["y"]) ** 2) ** 0.5
    assert slow_dist > 0.0, "slow unit %d did not move (denominator)" % SLOW_ID
    ratio = fast_dist / slow_dist
    assert ratio <= MAX_SPEED_RATIO, (
        "speed-sync not enforced: Raider moved %.1f wu but Bastion moved %.1f wu "
        "(ratio %.2f > %.1f); pipe is issuing a per-unit order instead of a group order "
        "(handle_command must call om_command_group_move for multi-unit move commands)"
        % (fast_dist, slow_dist, ratio, MAX_SPEED_RATIO))
