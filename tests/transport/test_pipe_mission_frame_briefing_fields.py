"""A4 (docs/northstar/plans/2026-09-30-mission-plays-plan.md, E-10 S-079): the live mission
frame carries real briefing data, not the zeros T1-2 left behind.

Scope is the part of A4 that docs/architecture.md already documents: the worked example
`{"type":"mission",...,"objectives":[{"i","kind","node","primary","radius","progress"}],
"force":{"types":[...],"tiers":[...]}}` (chronicle frame, mission frame, debrief frame). The
A4 fields `position_name`, `parity`, `objective` text and a top-level `node`/`radius`/
`force[]` are NOT documented there, so they are not tested here; a contract docs piece must
land first (see the A4 test report).

Red on main today: handle_mission_start emits radius 0.0 for every objective and
force {"types":[],"tiers":[]} (header comment of csrc/pipe/om_pipe.c); green once
handle_mission_start reads the objective radius and the force allocation from the sim.

Positive control: _check_frame rejects the frame main emits today (test_check_frame_*).
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
JUMP = {"type": "cmd", "name": "jump", "ticks": 50}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
QUIT = {"type": "cmd", "name": "quit"}
OBJECTIVE_KEYS = {"i", "kind", "node", "primary", "radius", "progress"}
N_UNIT_TYPES = 6  # builtin roster ids 0..5 (docs/architecture.md place_structure `kind`)

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _mission(cmds):
    frames = _run(cmds)
    missions = [f for f in frames if f.get("type") == "mission"]
    assert len(missions) == 1, frames
    return missions[0], frames


def _check_frame(m):
    """The documented mission-frame shape with live (non-zero, non-empty) content."""
    objs = m["objectives"]
    assert objs, "mission frame has no objectives"
    for o in objs:
        assert OBJECTIVE_KEYS <= set(o), "objective missing documented keys %r" % (OBJECTIVE_KEYS - set(o))
    primary = [o for o in objs if o["primary"]]
    assert len(primary) == 1, "R-075-01: exactly one primary objective, got %r" % objs
    assert primary[0]["radius"] > 0, "primary objective radius is %r (T1-2 placeholder zero)" % primary[0]["radius"]
    force = m["force"]
    assert set(force) == {"types", "tiers"}, force
    assert len(force["types"]) > 0, "force.types is empty (T1-2 placeholder), no player roster shipped"
    assert len(force["types"]) == len(force["tiers"]), force
    assert all(isinstance(t, int) and 0 <= t < N_UNIT_TYPES for t in force["types"]), force["types"]
    assert all(isinstance(t, int) and t >= 0 for t in force["tiers"]), force["tiers"]


def test_check_frame_rejects_todays_empty_frame():
    """Positive control for the detector: the frame main emits now must fail _check_frame."""
    today = {"objectives": [{"i": 0, "kind": 1, "node": 0, "primary": True, "radius": 0.0, "progress": 0.0}],
             "force": {"types": [], "tiers": []}}
    with pytest.raises(AssertionError):
        _check_frame(today)


def test_check_frame_accepts_the_documented_example():
    documented = {"objectives": [{"i": 0, "kind": 1, "node": 3, "primary": True, "radius": 300.0, "progress": 0.0}],
                  "force": {"types": [2, 2, 1, 0, 0, 0], "tiers": [2, 2, 1, 0, 0, 0]}}
    _check_frame(documented)


def test_R075_S079_mission_frame_after_set_seed_and_start_is_live():
    """R-075-01/R-075-02 (objective radius), R-074-04 (player force filled), S-079: worked example."""
    m, _ = _mission([SET_SEED, START])
    _check_frame(m)


def test_S079_mission_frame_after_set_seed_jump_start_is_live():
    m, _ = _mission([SET_SEED, JUMP, START])
    _check_frame(m)


def test_S079_objective_node_indexes_a_tactical_map_node():
    """The frame's `node` is a tactical map index (docs/architecture.md): it must exist in the map."""
    m, _ = _mission([SET_SEED, START])
    tactical = [f for f in _run([SET_SEED, START, BEGIN]) if f["type"] == "tactical"][0]
    n_nodes = len(tactical["map"]["nodes"])
    for o in m["objectives"]:
        assert 0 <= o["node"] < n_nodes, "objective node %r not in map of %d nodes" % (o["node"], n_nodes)
    _check_frame(m)  # the index check alone passes on an all-zero frame; tie it to live content


def test_S079_mission_frame_is_deterministic():
    a, _ = _mission([SET_SEED, START])
    b, _ = _mission([SET_SEED, START])
    assert a == b
    _check_frame(a)
