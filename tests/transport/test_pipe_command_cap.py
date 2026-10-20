"""T1-7-3: handle_command unit cap raised from 256 to OM_MAX_UNITS (10100).

A mission spawns 294 player units; with the old cap of 256 the last 38 unit
IDs in the sorted list are silently dropped by get_int_array, so a select-all
move command misses 38 units.

Red on unmodified code: unit 294 is at sorted position 294 (beyond old cap of
256) and receives no move command; after 20 tactical steps it stays at spawn.
Green after fix: unit 294 is included in the group move and must move >= 5 wu.

TD-VG-E-34 (pin move, start-count pins move with the starting-force cut, E7, Architect 2026-10-19): the mission composes
F 490 player units (it was all spawned: 490 and unit id 490), and the player spawns start_units of them. Premise (seed 1, 80
regions, region 66, archetype 8): F 490, p 1, e 1, n 2, share 0.5, frac 0.6, start 294.0, start_units 294. The player's units
are ids 1..294, so the last in ascending ID order is now 294, still beyond the old cap of 256.
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

# The mission spawns 294 player units (start_units of F 490, TD-VG-E-34) with these seed/region/step params.
EXPECTED_UNIT_COUNT = 294

# Unit 294: last in ascending ID order (was unit 490 when all of F 490 spawned).
# At sorted position 294 it falls beyond old cap=256 and is dropped.
# After the fix it receives the group move and must move >= MIN_DIST_WU.
CAP_PROOF_UNIT_ID = 294
CAP_PROOF_DEST_X = 13045.0
CAP_PROOF_DEST_Y = 1255.0
MIN_DIST_WU = 5.0
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


def _get_player_unit_ids(begin_frame, player_faction=0):
    return sorted(u["id"] for u in begin_frame.get("units", []) if u.get("faction") == player_faction)


@pytest.fixture(scope="module")
def cap_proof_frames():
    """Run mission with a select-all move command carrying all 294 unit IDs."""
    # First pass: discover unit IDs from the begin frame.
    discover = _run([SET_SEED, STEP10, START, BEGIN])
    tactical_begin = [f for f in discover if f["type"] == "tactical"]
    assert tactical_begin, "no tactical begin frame in discover pass"
    begin = tactical_begin[0]
    all_ids = _get_player_unit_ids(begin)

    # Second pass: issue the select-all move command.
    cmds = [SET_SEED, STEP10, START, BEGIN,
            {"type": "cmd", "name": "command", "verb": "move",
             "units": all_ids, "x": CAP_PROOF_DEST_X, "y": CAP_PROOF_DEST_Y}]
    for _ in range(N_STEPS):
        cmds.append({"type": "cmd", "name": "tactical_step", "n": 1})
    frames = _run(cmds)
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) == N_STEPS + 1, (
        "expected %d tactical frames (1 begin + %d steps), got %d"
        % (N_STEPS + 1, N_STEPS, len(tactical)))
    return begin, tactical[-1], all_ids


def test_player_unit_count(cap_proof_frames):
    """Mission must spawn exactly EXPECTED_UNIT_COUNT player units."""
    begin, _, all_ids = cap_proof_frames
    assert len(all_ids) == EXPECTED_UNIT_COUNT, (
        "expected %d player units, got %d; world may have changed"
        % (EXPECTED_UNIT_COUNT, len(all_ids)))


def test_cap_proof_unit_at_spawn(cap_proof_frames):
    """Positive control: CAP_PROOF_UNIT_ID must be present in the begin frame."""
    begin, _, _ = cap_proof_frames
    units = {u["id"]: u for u in begin.get("units", [])}
    assert CAP_PROOF_UNIT_ID in units, (
        "unit %d absent from begin frame (world diverged or unit count changed)"
        % CAP_PROOF_UNIT_ID)


def test_cap_proof_unit_moved(cap_proof_frames):
    """Unit beyond old cap=256 must move when all player IDs are in the command.

    With old cap=256: unit 490 is at sorted position 490 and is silently
    dropped; it stays at spawn.  After raising the cap to OM_MAX_UNITS (10100)
    unit 490 receives the group move and moves >= MIN_DIST_WU in N_STEPS ticks.
    """
    begin, final, _ = cap_proof_frames
    begin_units = {u["id"]: u for u in begin.get("units", [])}
    final_units = {u["id"]: u for u in final.get("units", [])}
    assert CAP_PROOF_UNIT_ID in begin_units, (
        "unit %d absent from begin frame" % CAP_PROOF_UNIT_ID)
    assert CAP_PROOF_UNIT_ID in final_units, (
        "unit %d absent from final frame after %d steps" % (CAP_PROOF_UNIT_ID, N_STEPS))
    bu = begin_units[CAP_PROOF_UNIT_ID]
    fu = final_units[CAP_PROOF_UNIT_ID]
    dist = ((fu["x"] - bu["x"]) ** 2 + (fu["y"] - bu["y"]) ** 2) ** 0.5
    assert dist >= MIN_DIST_WU, (
        "unit %d (beyond old cap=256) did not move: "
        "spawn=(%.2f,%.2f) final=(%.2f,%.2f) dist=%.2f < %.0f wu; "
        "unit was likely dropped by the old get_int_array cap"
        % (CAP_PROOF_UNIT_ID, bu["x"], bu["y"], fu["x"], fu["y"], dist, MIN_DIST_WU))
