"""A4 (docs/northstar/plans/2026-10-01-architect-rulings.md section A4, E-10 S-079): the live
mission frame carries real briefing data, not the zeros T1-2 left behind.

Frame shape (docs/architecture.md mission frame, A4-frame-docs): `{archetype, region,
deadline_ticks, objectives[{i,kind,node,primary,radius,progress}], force:{types,tiers},
briefing:{situation,objective,assets}, parity, quiet_world}`. `force.types` is six counts in
unit-type-id order summing to the player's force size; `force.tiers` is the tier per type;
`briefing` carries all three non-empty texts (R-079-01); `parity` is a number > 0 (data for
tests and QA; the client never renders it, R-079-04); `quiet_world` is false for a
pool-selected mission (R-072-08); no frame carries `position_name` (the client derives names).

Red on main today: handle_mission_start emits radius 0.0 for every objective, force
{"types":[],"tiers":[]} and no briefing/parity/quiet_world; green once the HDR4-2-r accessors
land and handle_mission_start reads them. Rule text changed from the first draft of this file
(force.types was asserted as unit-type ids, now six counts): ledger row in
docs/northstar/plans/push_ledger_2026-09-22.md.

Tier source: no per-unit tier source exists in the sim, so only the shape of force.tiers is
asserted (six non-negative ints), never a value.

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
    assert len(force["types"]) == N_UNIT_TYPES, "force.types must be six counts, got %r" % force["types"]
    assert len(force["tiers"]) == N_UNIT_TYPES, "force.tiers must be six tiers, got %r" % force["tiers"]
    assert all(isinstance(t, int) and not isinstance(t, bool) and t >= 0 for t in force["types"]), force["types"]
    assert sum(force["types"]) > 0, "force.types sums to zero: no player roster shipped"
    assert all(isinstance(t, int) and not isinstance(t, bool) and t >= 0 for t in force["tiers"]), force["tiers"]
    b = m.get("briefing")
    assert isinstance(b, dict) and set(b) == {"situation", "objective", "assets"}, "briefing missing or wrong keys: %r" % b
    for k in ("situation", "objective", "assets"):
        assert isinstance(b[k], str) and b[k].strip(), "briefing.%s is empty (R-079-01)" % k
    p = m.get("parity")
    assert isinstance(p, (int, float)) and not isinstance(p, bool) and p > 0, "parity must be a number > 0, got %r" % (p,)
    assert m.get("quiet_world") is False, "quiet_world must be false for a pool-selected mission, got %r" % (m.get("quiet_world"),)
    assert "position_name" not in m, "frames carry no names (A4 ruling 2)"
    assert "position_name" not in primary[0], "frames carry no names (A4 ruling 2)"


def test_check_frame_rejects_todays_empty_frame():
    """Positive control for the detector: the frame main emits now must fail _check_frame."""
    today = {"objectives": [{"i": 0, "kind": 1, "node": 0, "primary": True, "radius": 0.0, "progress": 0.0}],
             "force": {"types": [], "tiers": []}}
    with pytest.raises(AssertionError):
        _check_frame(today)


DOCUMENTED = {"objectives": [{"i": 0, "kind": 1, "node": 3, "primary": True, "radius": 300.0, "progress": 0.0}],
              "force": {"types": [2, 2, 1, 0, 0, 0], "tiers": [2, 2, 1, 0, 0, 0]},
              "briefing": {"situation": "s", "objective": "o", "assets": "a"},
              "parity": 0.85, "quiet_world": False}


def test_check_frame_accepts_the_documented_example():
    _check_frame(DOCUMENTED)


@pytest.mark.parametrize("mutate", [
    lambda m: m["briefing"].update(assets=""),
    lambda m: m["briefing"].pop("situation"),
    lambda m: m.pop("briefing"),
    lambda m: m.update(parity=0),
    lambda m: m.pop("parity"),
    lambda m: m.update(quiet_world=True),
    lambda m: m.pop("quiet_world"),
    lambda m: m.update(position_name="Ridge Point"),
    lambda m: m["force"].update(types=[2, 2, 1]),
    lambda m: m["force"].update(types=[0, 0, 0, 0, 0, 0]),
])
def test_check_frame_rejects_each_defect(mutate):
    """Positive control: each ruled field, broken alone, fails the detector."""
    import copy
    m = copy.deepcopy(DOCUMENTED)
    mutate(m)
    with pytest.raises(AssertionError):
        _check_frame(m)


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


def test_S079_primary_objective_node_is_the_map_objective_node():
    """objectives[0].node (om_objective_get_node) is a spine node of the tactical map, and the
    primary objective is objectives[0]."""
    m, _ = _mission([SET_SEED, START])
    assert m["objectives"][0]["primary"] is True
    tactical = [f for f in _run([SET_SEED, START, BEGIN]) if f["type"] == "tactical"][0]
    nodes = {n["i"] for n in tactical["map"]["nodes"]}
    assert m["objectives"][0]["node"] in nodes
    _check_frame(m)


def test_R079_01_force_types_sum_to_the_player_force_in_the_tactical_frame():
    """force.types[t] counts the player's units of type t: it matches the faction-0 units the
    tactical frame lists after mission_begin (tally of om_mission_get_force_unit)."""
    m, _ = _mission([SET_SEED, START])
    _check_frame(m)
    tactical = [f for f in _run([SET_SEED, START, BEGIN]) if f["type"] == "tactical"][0]
    counts = [0] * N_UNIT_TYPES
    for u in tactical["units"]:
        if u["faction"] == 0:
            counts[u["type"]] += 1
    assert m["force"]["types"] == counts


def test_S079_mission_frame_is_deterministic():
    a, _ = _mission([SET_SEED, START])
    b, _ = _mission([SET_SEED, START])
    assert a == b
    _check_frame(a)


def test_R072_08_pool_selected_mission_is_not_quiet_world():
    m, _ = _mission([SET_SEED, START])
    assert m["quiet_world"] is False
    _check_frame(m)
