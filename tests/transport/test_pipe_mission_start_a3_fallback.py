# Rule pins: R-072-07@d416e5, R-072-08@8db565, R-074-01@1c190d, R-074-02@c01ed7, R-074-03@93d2b7, R-074-04@10d3c7, R-074-05@22817d, R-080-03@92ae5a
"""A3 (Q-072-01 retry then Defensive Stand fallback) tests for handle_mission_start.
Split out of test_pipe_mission_start_context_and_fallback.py; red until A3 is built.
See that file's docstring for the fixture rationale. Rulings (Westley 2026-09-30):
R-072-07 weakest region = lowest ALG-09 stability composite (the snapshot's
`stability`), ties to the lowest region index; R-072-08 (architect rulings
2026-10-01, A3 items 1-3) the fallback enemy is the non-player faction nearest the
region by connection hops, ties to the highest total military then the lowest
faction id; its power P is its strongest region's military x 2000 (raised to one
unit of its cheapest profile if it would field nothing) and the player's budget is
P x parity (R-074-04); reaching the fallback sets `quiet_world` in the mission
frame only (documented in docs/architecture.md).
"""
import ctypes
import json
import subprocess
from collections import deque
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
# R-074-03: parity is never below 0.75 and base parity never above 1.0 (R-074-02),
# so legal parity is in [0.75, 1.0].
PARITY_MIN = 0.75
PARITY_MAX = 1.0
# R-074-05: capacity below 40 (the snapshot's 0..100 scale) removes 20 percent of
# the player's units; every QUIET_SEEDS fallback region is below it.
SHORTFALL_KEEP_MIN = 0.75
ENEMY_POWER_PER_MILITARY = 2000.0  # R-074-01 default form; R-072-08
N_TYPES = 6
SNAPSHOT_ROUNDING = 1e-3  # snapshot military is rounded to two decimals; relative slack on P
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


def _expected_enemy_faction(snap, region):
    """R-072-08: the non-player, non-neutral faction nearest `region` by connection
    hops (breadth-first over snapshot `edges`, any edge type; a faction's distance
    is its nearest region's), ties to the highest total military across its
    regions, then the lowest faction id. Returns (faction, strongest region military)."""
    adj = {}
    for e in snap["edges"]:
        adj.setdefault(e["a"], []).append(e["b"])
        adj.setdefault(e["b"], []).append(e["a"])
    dist, queue = {region: 0}, deque([region])
    while queue:
        x = queue.popleft()
        for y in adj.get(x, []):
            if y not in dist:
                dist[y] = dist[x] + 1
                queue.append(y)
    player = snap["player_faction"]
    stats = {}
    for r in snap["regions"]:
        f = r["owner"]
        if f in (-1, player) or r["i"] not in dist:
            continue
        d = stats.setdefault(f, {"hops": dist[r["i"]], "total": 0.0, "max": 0.0})
        d["hops"] = min(d["hops"], dist[r["i"]])
        d["total"] += r["military"]
        d["max"] = max(d["max"], r["military"])
    assert stats, "fixture drift: no non-player faction reachable from region %d" % region
    best = min(stats, key=lambda f: (stats[f]["hops"], -stats[f]["total"], f))
    return best, stats[best]["max"]


@pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built (om_unit_power)")
@pytest.mark.parametrize("seed", QUIET_SEEDS)
def test_fallback_enemy_is_nearest_faction_and_player_budget_follows_its_power(seed):
    """A3, R-072-08 (architect rulings 2026-10-01 items 1-3): the fallback mission's
    enemy is the non-player faction nearest the fallback region by connection hops
    (ties: highest total military, then lowest faction id), and the player's force
    is sized from that faction's P = strongest region military x 2000 times parity.

    Observable through the pipe: the enemy faction id on the first tactical frame's
    units, and each side's units. The mission frame carries no parity, budget or
    enemy field today (A4's `parity` frame field is not built), so the budget is
    asserted as a bracket: the player's total power (om_unit_power per unit, the
    R-074 normalised formula) lies between the fill the sim's own
    om_mission_fill_player_force gives at P x 0.75 (parity floor, times the 0.75
    R-074-05 shortfall allowance) and at P x 1.0 (parity ceiling), P read from the
    snapshot (rounded to two decimals, so +-0.1 percent slack).

    Red until A3 is built: today the fallback is the R-080-03 Siege on region 0
    against whoever owns it.
    """
    lib = ctypes.CDLL(str(LIB))
    lib.om_unit_power.argtypes = [ctypes.c_uint32]
    lib.om_unit_power.restype = ctypes.c_double
    lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    lib.om_world_new.restype = ctypes.c_void_p
    lib.om_world_generate.argtypes = [ctypes.c_void_p]
    lib.om_world_free.argtypes = [ctypes.c_void_p]
    lib.om_mission_load_launch_library.argtypes = [ctypes.c_void_p]
    lib.om_mission_setup.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]
    lib.om_mission_fill_player_force.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
    lib.om_mission_fill_player_force.restype = ctypes.c_double
    lib.om_mission_setup_fallback.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
    lib.om_mission_get_player_units.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]

    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": N_REGIONS,
         "features": [], "new_campaign": False},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1},
    ])
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, "seed %d: fallback mission refused: %r" % (seed, errors)
    mission = next((f for f in frames if f["type"] == "mission"), None)
    assert mission is not None and mission.get("quiet_world") is True, (
        "seed %d: R-072-08 fallback must set quiet_world true: %r" % (seed, mission))
    snap = next(f for f in frames if f["type"] == "snapshot")
    tactical = next((f for f in frames if f["type"] == "tactical"), None)
    assert tactical is not None, "seed %d: no tactical frame: %r" % (seed, frames)

    player = snap["player_faction"]
    expected_enemy, strongest = _expected_enemy_faction(snap, mission["region"])
    units = tactical["units"]
    mine = [u for u in units if u["faction"] == player]
    theirs = [u for u in units if u["faction"] not in (player, -1)]
    assert mine, "seed %d: fallback mission has no player units" % seed
    assert theirs, "seed %d: fallback mission has no enemy units (R-072-08)" % seed
    assert {u["faction"] for u in theirs} == {expected_enemy}, (
        "seed %d: enemy faction(s) %r on the field, expected the nearest-by-hops faction %d (R-072-08)"
        % (seed, sorted({u["faction"] for u in theirs}), expected_enemy))

    cheapest = min(lib.om_unit_power(t) for t in range(6))
    p = max(strongest * ENEMY_POWER_PER_MILITARY, cheapest)
    w = lib.om_world_new(N_REGIONS, seed)
    try:
        lib.om_world_generate(w)
        lib.om_mission_load_launch_library(w)
        lib.om_mission_setup(w, mission["region"], DEFENSIVE_STAND, 0)
        low = SHORTFALL_KEEP_MIN * lib.om_mission_fill_player_force(
            w, p * (1 - SNAPSHOT_ROUNDING), PARITY_MIN)
        high = lib.om_mission_fill_player_force(w, p * (1 + SNAPSHOT_ROUNDING), PARITY_MAX)
    finally:
        lib.om_world_free(w)
    assert low > 0, "seed %d: fixture drift, the oracle fill is empty for P=%.0f" % (seed, p)
    # TD-VG-E-34 (measures the composed F, Architect 2026-10-19): the band is a statement about the composed budget (P x
    # parity), and before E7 the spawned units were the whole composed force. The player now spawns start_units of F, so the
    # test sums the composed roster (om_mission_get_player_units of a world set up through the same
    # om_mission_setup_fallback the pipe calls) and keeps the band unchanged. Premise F, p, e, share, start, spawned is printed.
    wf = lib.om_world_new(N_REGIONS, seed)
    try:
        lib.om_world_generate(wf)
        lib.om_mission_load_launch_library(wf)
        lib.om_mission_setup_fallback(wf, mission["region"], expected_enemy)
        roster = (ctypes.c_uint32 * N_TYPES)()
        lib.om_mission_get_player_units(wf, player, roster, N_TYPES)
    finally:
        lib.om_world_free(wf)
    composed = list(roster)
    owners = [s["owner"] for s in tactical["structures"]]
    n_p, n_e = owners.count(player), owners.count(expected_enemy)
    share = n_p / (n_p + n_e) if n_p + n_e else None
    start = sum(composed) * ((0.2 + 1.2 * share if share <= 0.25 else 0.5 + 0.4 * (share - 0.25)) if share is not None else 1.0)
    print("PREMISE", "seed %d F %d p %d e %d share %s start %.2f start_units %d spawned %d composed %r"
          % (seed, sum(composed), n_p, n_e, share, start, int(start + 0.5), len(mine), composed))
    assert sum(composed) >= len(mine) > 0, "premise: the composed force F is at least what spawned"
    got = sum(lib.om_unit_power(t) * n for t, n in enumerate(composed))
    assert low <= got <= high, (
        "seed %d: composed player power %.1f outside [%.1f, %.1f] for enemy P=%.0f (strongest military %.2f of faction %d) times parity (R-072-08, R-074-04); F %d p %d e %d share %s start_units %d spawned %d"
        % (seed, got, low, high, p, strongest, expected_enemy, sum(composed), n_p, n_e, share, int(start + 0.5), len(mine)))
