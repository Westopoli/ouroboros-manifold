"""Enemy macro group orders through the pipe (B13-8/B9-13, R-120-02, R-124-02).

`om_macro_tick` used to only LOG the command type per force per 40-tick
evaluation; it never issued a group order, so enemy forces never moved (only
the per-unit AI auto-engaged whatever came into range). This drives a real
mission end to end through the binary pipe -- set_seed, step, mission_start,
mission_begin, tactical_step -- issuing no "command" verb at all, and checks
the non-player units' mean distance to the mission's objective node (map
node kind 0) falls over 600 tactical ticks.

seed 1 / n_regions 80 / step 10 is the smallest combination found (by trial)
that resolves to a mission with a non-empty enemy force for this seed; a
smaller world's candidate pool kept resolving to Defensive Stand with no
committed attack budget (0 enemy units), which would make this test vacuous.

RED on main (no group order issued: mean distance is bit-identical before
and after, 11754.142280596576 both times). GREEN after B13-8/B9-13.
"""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [1, 2, 3, 4, 5, 6, 7]
PLAYER_FAC = 0
OM_MISSION_SPINE_NODE_OBJECTIVE = 0

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=180)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def _objective(tactical_frame):
    return next(n for n in tactical_frame["map"]["nodes"] if n["kind"] == OM_MISSION_SPINE_NODE_OBJECTIVE)


def _mean_dist_to_objective(tactical_frame, obj):
    """Mean distance of every non-player unit to the objective node. None
    (not 0.0) when the scene has no enemy units, so a vacuous scene fails
    the setup assertion below instead of silently passing the real one."""
    enemies = [u for u in tactical_frame["units"] if u["faction"] != PLAYER_FAC]
    if not enemies:
        return None
    return sum(math.hypot(u["x"] - obj["x"], u["y"] - obj["y"]) for u in enemies) / len(enemies)


@pytest.fixture(scope="module")
def tactical_frames():
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 600, "full": True},
    ]
    frames = _run(cmds)
    tacticals = [f for f in frames if f["type"] == "tactical"]
    # A7: mission_begin writes one full frame (tick 0); a tactical_step with n > 1
    # runs all n steps and writes only the last frame, full here because it is requested.
    assert len(tacticals) == 2, "expected mission_begin's frame plus one frame for the 600-step call"
    assert all(f["full"] for f in tacticals), "the distance read needs full frames (map, units)"
    assert tacticals[-1]["tick"] == tacticals[0]["tick"] + 600, "the last frame is for step 600"
    return tacticals


def test_enemy_mean_distance_to_objective_decreases_with_no_commands(tactical_frames):
    """No 'command' pipe verb is ever sent in this scene -- only tactical_step.
    Before B13-8/B9-13 the macro layer never moved a force, so the enemy's
    mean distance to the objective is bit-identical before and after; after
    the fix, the registered force's group orders close the distance."""
    first, last = tactical_frames[0], tactical_frames[-1]
    obj = _objective(first)

    d0 = _mean_dist_to_objective(first, obj)
    d1 = _mean_dist_to_objective(last, obj)

    assert d0 is not None, (
        "setup check failed: no non-player units in the opening tactical frame "
        "(this seed/n_regions/step combination resolved to an empty enemy force)"
    )
    assert d1 is not None, "enemy force disappeared entirely over 600 ticks"
    assert d1 < d0, (
        f"R-120-02/B13-8: enemy mean distance to objective did not fall "
        f"(before={d0}, after={d1}) -- the macro layer issued no group order"
    )
