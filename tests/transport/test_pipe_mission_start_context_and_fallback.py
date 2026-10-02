"""A2 (pipe half) and A3: handle_mission_start composes real selection context
and follows the answered Q-072-01 fallback (docs/northstar/plans/2026-09-30-mission-plays-plan.md).

R-072-02: urgency's conflict term reads recent attacks and the committed attack
budget on the region. om_mission_refresh_context (csrc/mission.c) computes them
from the pending telegraphs, but nothing on the pipe path calls it, so a region
with a telegraphed attack scores as if it were quiet.

Q-072-01 (answered A, Westley 2026-09-13): "Run another 20-tick jump and retry,
up to 5 times, then fall back to a Defensive Stand on the player's weakest
region."

There is no pipe command that declares an attack intent (`inject` only drives
om_debug_inject bugs). A pending telegraph is created the way play creates it:
the world steps and an agent declares one. The fixture seeds below were found
by scanning set_seed worlds whose snapshot lists a telegraph whose `target` is a
player-owned region (exactly one such region per seed), then taking the seeds
where a context-aware selection picks Defensive Stand (archetype 0) there.

"Weakest player region" is not defined by the bible. The A3 fixtures are seeds
where lowest stability, lowest military and highest mean deficit
(100 - military, 100 - economy, 100 - stability) all name the same region, so
the tests do not pick a definition; the precondition is asserted.

Quiet worlds for A3: `features: []` at tick 0 (`new_campaign: false`) is a world
where no archetype trigger fires through five 20-tick jumps.
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

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")

# seed -> the one player region under telegraph, pinned so a world change shows
# up as a clear failure. Only seeds 76 and 287 of 1-400 satisfy the test on both
# the pre-A81 and post-A81 worlds with the same target (TD-A89-3; the earlier
# seeds 20, 24, 26, 31, 33, 43 drifted when events began to reach regions 64+).
TELEGRAPH_SEEDS = {76: 68, 287: 66}
TRIGGERED_SEEDS = [1, 2, 8, 20, 24, 43]


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


@pytest.mark.parametrize("seed", sorted(TELEGRAPH_SEEDS))
def test_telegraphed_attack_on_player_region_selects_defensive_stand_there(seed):
    """A2, R-072-02 (conflict term: recent attacks + committed attack budget):
    a pending telegraph on one player region makes mission_start choose a
    Defensive Stand on exactly that region, through set_seed -> mission_start.

    Red on origin/push/A2: handle_mission_start never calls
    om_mission_refresh_context, so the region scores as quiet and a different
    candidate wins.
    """
    pre, post, mission, frames = _start(seed, FEATURES)
    own = {r["i"] for r in _player_regions(pre)}
    targets = sorted({t["target"] for t in pre["telegraphs"] if t["target"] in own})
    assert len(targets) == 1, "seed %d: fixture drift, player regions under telegraph = %r" % (seed, targets)
    assert targets[0] == TELEGRAPH_SEEDS[seed], "seed %d: telegraph target %d, pinned %d" % (
        seed, targets[0], TELEGRAPH_SEEDS[seed])
    assert mission is not None, "seed %d: no mission frame: %r" % (seed, frames)
    assert (mission["archetype"], mission["region"]) == (DEFENSIVE_STAND, targets[0]), (
        "seed %d: telegraph pending on player region %d but mission_start chose archetype %r on region %r"
        % (seed, targets[0], mission["archetype"], mission["region"]))
    assert post["tick"] == pre["tick"], "seed %d: a triggered world must not retry (tick %d -> %d)" % (
        seed, pre["tick"], post["tick"])


@pytest.mark.parametrize("seed", TRIGGERED_SEEDS)
def test_control_world_with_a_trigger_needs_zero_retries(seed):
    """Control for A3: after the opening jump a trigger already fires, so
    mission_start must not spend any ticks on retries (Q-072-01 retries only
    when nothing triggers). Green before and after; red if the retry loop
    jumps unconditionally.
    """
    pre, post, mission, frames = _start(seed, FEATURES)
    assert pre["tick"] >= RETRY_TICKS
    assert mission is not None, "seed %d: no mission frame: %r" % (seed, frames)
    assert post["tick"] == pre["tick"], "seed %d: triggered world retried (tick %d -> %d)" % (
        seed, pre["tick"], post["tick"])
