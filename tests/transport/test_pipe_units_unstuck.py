"""T1-7-2-r: stuck units in a dense spawn must move when group-moved together;
group-ordered unit blocked entirely by NON-group stationary units must stay put.

On unmodified main, interior units of the 276-unit faction-0 spawn are packed
at exactly 30 wu (2 x OM_UNIT_COLLISION_RADIUS = 2 x 15).  Every steering
probe for an interior unit is blocked by a touching neighbour so `found` stays
0 and the unit waits forever.

Fix (T1-7-2-r ruling): probe does NOT count a same-group mate as a blocker when
the group id is nonzero.  Non-group units (group_id 0 or different nonzero id)
still block normally.

Test 1 (positive): group-move all 256 player units together; after 60 tactical
frames at least 90 % must end > 1 wu from spawn, and centre units 137-141 must
each move.

Test 2 (determinism): same command stream twice -> byte-identical final positions.

Test 3 (negative): group-move ONLY unit 137 (alone in its group); all 275 other
units are stationary with group_id 0 and still surround it; unit 137 must NOT
have moved > 1 wu after 60 frames.

Setup (same seed/region/feature/step as the other transport tests):
  set_seed 1, 80 regions, strategic features 1..7, step 10,
  mission_start faction 0, mission_begin.
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

# pipe accepts at most 256 ids (csrc/pipe/om_pipe.c handle_command).
# Once push/T1-7-3 merges, change PLAYER_IDS to list(range(1, 277)).
PLAYER_IDS = list(range(1, 257))

# Destination: well north of the spawn box (spawn Y range 15-495).
DEST_X = 12000.0
DEST_Y = 1500.0

# Centre units (interior of the spawn grid, all within PLAYER_IDS):
# seed 1 / 80 regions / faction 0 / 10 strategic steps.  On unmodified main
# these 5 units move 0 of 5 checks in 60 steps (fully blocked).
CENTER_IDS = [137, 138, 139, 140, 141]

N_STEPS = 60
MIN_MOVE_WU = 1.0       # unit must be this far from spawn to count as "moved"
MIN_MOVE_FRAC = 0.90    # at least this fraction of commanded units must have moved


pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run_unstuck_cmds():
    """Build the command stream: begin + group-move all PLAYER_IDS + 60 steps."""
    move_cmd = {"type": "cmd", "name": "command", "verb": "move",
                "units": PLAYER_IDS, "x": DEST_X, "y": DEST_Y}
    cmds = [SET_SEED, STEP10, START, BEGIN, move_cmd]
    for _ in range(N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    return cmds


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
def unstuck_frames():
    """Run the unstuck scenario; return (begin_frame, final_frame)."""
    frames = _run(_run_unstuck_cmds())
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) == N_STEPS + 1, (
        "expected %d tactical frames (1 begin + %d steps), got %d"
        % (N_STEPS + 1, N_STEPS, len(tactical)))
    return tactical[0], tactical[-1]


# ---------------------------------------------------------------------------
# Positive control: begin-frame positions are as expected
# ---------------------------------------------------------------------------

def test_center_units_present_at_begin(unstuck_frames):
    """Centre units must be in the begin frame; if missing the scenario diverged."""
    begin, _ = unstuck_frames
    unit_map = {u["id"]: u for u in begin.get("units", [])}
    for uid in CENTER_IDS:
        assert uid in unit_map, (
            "centre unit %d absent from mission_begin tactical frame" % uid)


# ---------------------------------------------------------------------------
# Test 1: unstuck progress (90 percent of commanded units must move > 1 wu)
# ---------------------------------------------------------------------------

def test_unstuck_90_percent_move(unstuck_frames):
    """After %d tactical steps at least %.0f%% of commanded units must end "
    "> %.0f wu from their spawn position.  On unmodified main (stuck units) "
    "this fraction is <<90%% for interior units.""" % (N_STEPS, MIN_MOVE_FRAC * 100, MIN_MOVE_WU)
    begin, final = unstuck_frames
    begin_map = {u["id"]: u for u in begin.get("units", [])}
    final_map = {u["id"]: u for u in final.get("units", [])}
    moved, total = 0, 0
    for uid in PLAYER_IDS:
        if uid not in begin_map or uid not in final_map:
            continue
        total += 1
        bu, fu = begin_map[uid], final_map[uid]
        dist = ((fu["x"] - bu["x"]) ** 2 + (fu["y"] - bu["y"]) ** 2) ** 0.5
        if dist > MIN_MOVE_WU:
            moved += 1
    frac = moved / total if total else 0.0
    assert frac >= MIN_MOVE_FRAC, (
        "only %.1f%% (%d/%d) of commanded units moved > %.0f wu after %d steps; "
        "centre units are stuck (T1-7-2-r fix not yet applied)"
        % (frac * 100, moved, total, MIN_MOVE_WU, N_STEPS))


def test_center_units_moved(unstuck_frames):
    """Centre units (IDs 137-141) must each move > 1 wu; on unmodified main
    they are completely surrounded and stay at spawn forever."""
    begin, final = unstuck_frames
    begin_map = {u["id"]: u for u in begin.get("units", [])}
    final_map = {u["id"]: u for u in final.get("units", [])}
    for uid in CENTER_IDS:
        assert uid in begin_map, "centre unit %d not in begin frame" % uid
        assert uid in final_map, "centre unit %d not in final frame" % uid
        bu, fu = begin_map[uid], final_map[uid]
        dist = ((fu["x"] - bu["x"]) ** 2 + (fu["y"] - bu["y"]) ** 2) ** 0.5
        assert dist > MIN_MOVE_WU, (
            "centre unit %d did not move: spawn=(%.2f,%.2f) final=(%.2f,%.2f) dist=%.3f wu"
            % (uid, bu["x"], bu["y"], fu["x"], fu["y"], dist))


# ---------------------------------------------------------------------------
# Test 2: determinism (same command stream -> identical positions, two runs)
# ---------------------------------------------------------------------------

def test_unstuck_determinism():
    """Same seed + command stream must produce byte-identical unit positions
    on two independent runs.  Fails if any new randomness or wall-clock input
    was introduced by the T1-7-2-r change."""
    cmds = _run_unstuck_cmds()
    frames_a = _run(cmds)
    frames_b = _run(cmds)
    tactical_a = [f for f in frames_a if f["type"] == "tactical"]
    tactical_b = [f for f in frames_b if f["type"] == "tactical"]
    assert len(tactical_a) == len(tactical_b), (
        "run A produced %d tactical frames, run B produced %d"
        % (len(tactical_a), len(tactical_b)))
    final_a = {u["id"]: u for u in tactical_a[-1].get("units", [])}
    final_b = {u["id"]: u for u in tactical_b[-1].get("units", [])}
    mismatches = []
    for uid in PLAYER_IDS:
        if uid not in final_a or uid not in final_b:
            continue
        ua, ub = final_a[uid], final_b[uid]
        if ua["x"] != ub["x"] or ua["y"] != ub["y"]:
            mismatches.append(
                "id=%d A=(%.6f,%.6f) B=(%.6f,%.6f)"
                % (uid, ua["x"], ua["y"], ub["x"], ub["y"]))
    assert not mismatches, (
        "%d unit(s) had non-identical positions across two runs:\n%s"
        % (len(mismatches), "\n".join(mismatches[:10])))


# ---------------------------------------------------------------------------
# Test 3 (negative): unit blocked by NON-group stationary units still waits
# ---------------------------------------------------------------------------

def test_single_unit_group_still_blocked():
    """Group-move ONLY unit 20 to the destination.  Unit 20 (spawn 11775,45)
    has all four cardinal 30-wu neighbours (ids 2, 19, 21, 38); all have
    group_id 0 in this scenario (they were not included in the group command).

    The fix excludes only same-nonzero-group mates.  group_id-0 units are still
    blockers.  All 13 probe directions from unit 20 are blocked by its four
    stationary non-group neighbours, so unit 20 must NOT move > 1 wu after
    60 steps.

    Positive control for the exclusion being exact: if the fix incorrectly
    excluded all units (or all stationary units), unit 20 would escape here.
    """
    move_single = {"type": "cmd", "name": "command", "verb": "move",
                   "units": [20], "x": DEST_X, "y": DEST_Y}
    cmds = [SET_SEED, STEP10, START, BEGIN, move_single]
    for _ in range(N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    frames = _run(cmds)
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) >= 2, "expected begin frame + at least 1 step"
    begin_map = {u["id"]: u for u in tactical[0].get("units", [])}
    final_map = {u["id"]: u for u in tactical[-1].get("units", [])}
    assert 20 in begin_map, "unit 20 absent from begin frame"
    assert 20 in final_map, "unit 20 absent from final frame"
    bu, fu = begin_map[20], final_map[20]
    dist = ((fu["x"] - bu["x"]) ** 2 + (fu["y"] - bu["y"]) ** 2) ** 0.5
    assert dist <= MIN_MOVE_WU, (
        "unit 20 moved %.3f wu despite being surrounded by non-group stationary "
        "units; exclusion is too broad (spawn=(%.2f,%.2f) final=(%.2f,%.2f))"
        % (dist, bu["x"], bu["y"], fu["x"], fu["y"]))
