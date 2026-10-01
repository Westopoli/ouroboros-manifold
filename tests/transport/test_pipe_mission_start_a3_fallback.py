"""A3 (Q-072-01 retry then Defensive Stand fallback) tests for handle_mission_start.
Split out of test_pipe_mission_start_context_and_fallback.py; red until A3 is built.
See that file's docstring for the fixture rationale. Rulings (Westley 2026-09-30):
R-072-07 weakest region = lowest ALG-09 stability composite (the snapshot's
`stability`), ties to the lowest region index; R-072-08 the fallback enemy has real
force floored at parity times the player's, and reaching the fallback sets
`quiet_world` in the mission frame (documented in docs/architecture.md).
"""
import ctypes
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
# R-074-03: parity is never below 0.75, so 0.75 is the lowest legal parity.
PARITY_FLOOR = 0.75
LIB = ROOT / "libouroboros.so"


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

    # R-072-07: weakest = lowest stability composite, ties to the lowest index,
    # judged on the world mission_start leaves behind.
    own = _player_regions(post)
    weakest = min(own, key=lambda r: (r["stability"], r["i"]))["i"]
    assert weakest != 0, "seed %d: fixture drift, weakest region must not be region 0" % seed

    assert mission is not None, "seed %d: no mission frame: %r" % (seed, frames)
    assert (mission["archetype"], mission["region"]) == (DEFENSIVE_STAND, weakest), (
        "seed %d: expected Defensive Stand on weakest player region %d, got archetype %r on region %r"
        % (seed, weakest, mission["archetype"], mission["region"]))
    assert mission.get("quiet_world") is True, (
        "seed %d: R-072-08 fallback must set quiet_world true: %r" % (seed, mission))


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
    assert mission.get("quiet_world") is False, (
        "seed %d: control, a pool-selected mission must carry quiet_world false (R-072-08): %r" % (seed, mission))


@pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built (om_unit_power)")
@pytest.mark.parametrize("seed", QUIET_SEEDS)
def test_fallback_mission_has_real_enemy_force_at_least_parity_times_the_players(seed):
    """A3, R-072-08: the fallback mission is never empty. The first tactical frame
    has enemy units (a faction other than the player and neutral), and their total
    power (om_unit_power per type, R-074 normalised formula) is at least parity
    times the player's. The mission frame carries no enemy power or faction, so both
    are read from the tactical frame's units. Parity is taken at its lowest legal
    value, 0.75 (R-074-03); the enemy's faction being the strongest adjacent
    non-player faction is not asserted: no fallback-reachable world borders one
    (see the A3 report).

    Red until A3 is built: today the fallback is the R-080-03 Siege on region 0.
    """
    lib = ctypes.CDLL(str(LIB))
    lib.om_unit_power.argtypes = [ctypes.c_uint32]
    lib.om_unit_power.restype = ctypes.c_double

    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": N_REGIONS,
         "features": [], "new_campaign": False},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1},
    ])
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, "seed %d: fallback mission refused: %r" % (seed, errors)
    mission = next((f for f in frames if f["type"] == "mission"), None)
    assert mission is not None and mission.get("quiet_world") is True, (
        "seed %d: R-072-08 fallback must set quiet_world true: %r" % (seed, mission))
    tactical = next((f for f in frames if f["type"] == "tactical"), None)
    assert tactical is not None, "seed %d: no tactical frame: %r" % (seed, frames)
    units = tactical["units"]
    mine = [u for u in units if u["faction"] == 0]
    theirs = [u for u in units if u["faction"] not in (0, -1)]
    assert mine, "seed %d: fallback mission has no player units" % seed
    assert theirs, "seed %d: fallback mission has no enemy units (R-072-08)" % seed
    power = lambda us: sum(lib.om_unit_power(u["type"]) for u in us)
    assert power(theirs) >= PARITY_FLOOR * power(mine), (
        "seed %d: enemy power %.1f below %.2f x player power %.1f (R-072-08)"
        % (seed, power(theirs), PARITY_FLOOR, power(mine)))
