"""A3 (Q-072-01 retry then Defensive Stand fallback) tests for handle_mission_start.
Split out of test_pipe_mission_start_context_and_fallback.py with no assertion edits;
red until A3 is built. See that file's docstring for the fixture rationale.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
N_REGIONS = 80
DEFENSIVE_STAND = 0
RETRY_TICKS = 20
MAX_RETRIES = 5

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")

QUIET_SEEDS = [3, 5, 13, 32]


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds)
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def _start(seed, features, new_campaign=True):
    set_seed = {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": N_REGIONS, "features": features}
    if not new_campaign:
        set_seed["new_campaign"] = False
    frames = _run([
        set_seed,
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "snapshot"},
    ])
    snaps = [f for f in frames if f["type"] == "snapshot"]
    assert len(snaps) == 2, "seed %d: expected pre and post snapshots: %r" % (seed, frames)
    mission = next((f for f in frames if f["type"] == "mission"), None)
    return snaps[0], snaps[1], mission, frames


def _player_regions(snap):
    return [r for r in snap["regions"] if r["owner"] == snap["player_faction"]]


@pytest.mark.parametrize("seed", QUIET_SEEDS)
def test_nothing_triggers_retries_five_jumps_then_defensive_stand_on_weakest(seed):
    """A3, Q-072-01 (a): no trigger fires, so mission_start runs five 20-tick
    jumps, then answers a Defensive Stand on the weakest player region (never
    the region-0 / archetype-0 default, never the Siege fallback of R-080-03).

    Red on origin/push/A2: mission_start never jumps (tick stays 0) and the
    R-080-03 fallback answers archetype 1 on region 0.
    """
    pre, post, mission, frames = _start(seed, [], new_campaign=False)
    assert pre["tick"] == 0
    own = _player_regions(pre)
    assert own, "seed %d: fixture drift, no player regions" % seed

    assert post["tick"] == pre["tick"] + MAX_RETRIES * RETRY_TICKS, (
        "seed %d: tick %d -> %d, expected %d retry jumps of %d ticks"
        % (seed, pre["tick"], post["tick"], MAX_RETRIES, RETRY_TICKS))

    # weakest, judged on the world mission_start leaves behind
    own = _player_regions(post)
    deficit = lambda r: (300 - r["military"] - r["economy"] - r["stability"]) / 3
    by_stability = min(own, key=lambda r: r["stability"])["i"]
    by_military = min(own, key=lambda r: r["military"])["i"]
    by_deficit = max(own, key=deficit)["i"]
    assert by_stability == by_military == by_deficit, (
        "seed %d: fixture drift, weakest region is ambiguous (stability %d, military %d, deficit %d)"
        % (seed, by_stability, by_military, by_deficit))
    assert by_stability != 0, "seed %d: fixture drift, weakest region must not be region 0" % seed

    assert mission is not None, "seed %d: no mission frame: %r" % (seed, frames)
    assert (mission["archetype"], mission["region"]) == (DEFENSIVE_STAND, by_stability), (
        "seed %d: expected Defensive Stand on weakest player region %d, got archetype %r on region %r"
        % (seed, by_stability, mission["archetype"], mission["region"]))


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_tick_zero_world_retries_one_jump_when_the_next_jump_triggers(seed):
    """A3, Q-072-01 (a): the retry stops at the first jump after which a
    trigger fires. At tick 0 nothing fires; after one 20-tick jump every
    full-feature seed has a trigger, so mission_start advances exactly 20 ticks.

    Red on origin/push/A2: tick stays 0.
    """
    pre, post, mission, frames = _start(seed, FEATURES, new_campaign=False)
    assert pre["tick"] == 0
    assert post["tick"] == RETRY_TICKS, "seed %d: tick %d -> %d, expected one %d-tick retry" % (
        seed, pre["tick"], post["tick"], RETRY_TICKS)
    assert mission is not None, "seed %d: no mission frame: %r" % (seed, frames)
