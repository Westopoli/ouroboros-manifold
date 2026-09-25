"""T1-11: debrief frame region_delta has at least one non-zero value after a
decided DEFENSIVE_STAND + TOTAL_SUCCESS mission.

Setup: seed 1, 80 regions, features 0-7, no strategic steps.  With these
params the pipe auto-selects archetype 0 (DEFENSIVE_STAND) -- the only
archetype whose consequence table has entries (R-078-02/03).

The test drives objective 0 to completion=1.0 via objective_complete before
mission_end so the outcome band is TOTAL_SUCCESS (score >= 0.80), which is
the only band with consequence rows.

Uses pipe/ouroboros_pipe_dbg (debug build): objective_complete is a TEST AND
DEBUG VERB gated by OM_DEBUG_INJECT, same as inject (docs/architecture.md).

Red on base (T1-7-3): objective_complete verb unknown, region_delta stays zero.
Green after T1-11: verb wired, TOTAL_SUCCESS band, non-zero region_delta.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]

if not PIPE_DBG.exists():
    pytest.fail("pipe/ouroboros_pipe_dbg missing: run make pipe/ouroboros_pipe_dbg")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    quit_cmd = {"type": "cmd", "name": "quit"}
    script = b"".join(_frame(c) for c in cmds + [quit_cmd])
    proc = subprocess.run([str(PIPE_DBG)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def test_debrief_region_delta_has_at_least_one_nonzero_after_decided_mission():
    """After mission_start + objective_complete(0, 1.0) + mission_end the debrief
    region_delta carries non-zero consequences (R-078-02/03 defensive_stand
    total_success row).  At least one of military/economy/tension is non-zero.

    Red on base: objective_complete verb unknown -> error frame -> objective stays
    at 0.0 completion -> TOTAL_FAILURE band -> consequence table returns 0 rows ->
    region_delta all zeros.

    Green after: verb wired to om_mission_set_objective_completion -> objective
    score 1.0 -> final score 1.0 -> TOTAL_SUCCESS band (>= 0.80 threshold) ->
    consequence rows applied -> region_delta non-zero.
    """
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "objective_complete", "objective": 0, "completion": 1.0},
        {"type": "cmd", "name": "mission_end"},
    ]
    frames = _run(cmds)
    debrief = next((f for f in frames if f.get("type") == "debrief"), None)
    assert debrief is not None, (
        "no debrief frame; frames received: %r" % [f.get("type") for f in frames])
    rd = debrief.get("region_delta")
    assert rd is not None, "region_delta missing from debrief: %r" % debrief
    nonzero = [k for k in ("military", "economy", "tension", "population") if rd.get(k, 0) != 0]
    assert nonzero, (
        "region_delta all zeros -- objective_complete may not be wired or "
        "consequence band is not TOTAL_SUCCESS; band=%r region_delta=%r"
        % (debrief.get("band"), rd))
