"""B7 (Q-077-02, R-077-05, R-077-03; docs/architecture.md `assign_commander`,
mission frame `commander_unit`, debrief `commander_fate`).

`assign_commander {unit_id}` answers `{"type":"ack","name":"assign_commander","tick":N}`
or one of the documented errors; the debrief carries `commander_fate` as an
int (0 killed, 1 wounded, 2 survived), 2 when no commander was assigned.

Killing a unit through pipe play: seed 1, 80 regions, features 0-7, one
`mission_start` draws an Assault with a 410-unit player force (ids 1..410) and
449 enemy units. Ordering every player unit to attack-move onto the enemy
centroid and stepping 4150 ticks kills some player units from tick ~4066 on
(the deadline is 4406, so the mission is still running). The first run is a
probe that names the dead ids; later runs assign one of them as commander
before the clash. This relies on the pipe being deterministic for a seed and
a command stream, and on the fixture below staying an Assault; the probe test
asserts that at least one player unit dies so a drifting fixture fails loudly.
Dead units are not in a full frame (A7 delta contract: they are filtered out and
listed once in the next delta's `units_removed`), so the dead ids are the player
ids at mission_begin minus the player ids in the final full frame.

Not constructible, flagged to the architect: a non-zero `commander_unit` in a
`mission` frame. The only writer of a `mission` frame is `mission_start`
(csrc/pipe/om_pipe.c write_mission), which documents `commander_unit` 0, and
`assign_commander` writes only an ack; so the assigned id is never observable
in a mission frame, only through `commander_fate`. Only the 0 case is tested.
"""
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
END = {"type": "cmd", "name": "mission_end"}
QUIT = {"type": "cmd", "name": "quit"}
CLASH_STEPS = 4150
FATE_KILLED, FATE_WOUNDED, FATE_SURVIVED = 0, 1, 2

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds, timeout=170):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _assign(unit_id):
    return {"type": "cmd", "name": "assign_commander", "unit_id": unit_id}


def _answers(frames):
    return [f for f in frames if f.get("name") == "assign_commander"]


def _types(frames, t):
    return [f for f in frames if f["type"] == t]


@lru_cache(maxsize=None)
def _centroid_and_ids():
    frames = _run([SET_SEED, {"type": "cmd", "name": "step", "n": 10}, START, BEGIN,
                   {"type": "cmd", "name": "tactical_step", "n": 1, "full": True}])
    units = _types(frames, "tactical")[-1]["units"]
    player = [u["id"] for u in units if u["faction"] == 0]
    enemy = [u for u in units if u["faction"] != 0]
    ex = sum(u["x"] for u in enemy) / len(enemy)
    ey = sum(u["y"] for u in enemy) / len(enemy)
    return player, ex, ey


def _clash_cmds(commander=None, after=()):
    player, ex, ey = _centroid_and_ids()
    cmds = [SET_SEED, {"type": "cmd", "name": "step", "n": 10}, START]
    if commander is not None:
        cmds.append(_assign(commander))
    cmds += [BEGIN,
             {"type": "cmd", "name": "command", "verb": "attack_move", "units": player, "x": ex, "y": ey},
             {"type": "cmd", "name": "tactical_step", "n": CLASH_STEPS},
             {"type": "cmd", "name": "tactical_step", "n": 1, "full": True}]
    return cmds + list(after)


@lru_cache(maxsize=None)
def _dead_ids():
    frames = _run(_clash_cmds())
    last = _types(frames, "tactical")[-1]
    assert last["mission_over"] is False, "fixture drifted: the mission ended before the clash read"
    alive = {u["id"] for u in last["units"] if u["faction"] == 0}
    return tuple(sorted(set(_centroid_and_ids()[0]) - alive))


@lru_cache(maxsize=None)
def _killed_commander_run():
    dead = _dead_ids()
    live = next(i for i in _centroid_and_ids()[0] if i not in dead)
    return _run(_clash_cmds(commander=dead[0], after=[_assign(live), END]))


def _error_reason(frames):
    ans = _answers(frames)
    assert ans, frames
    a = ans[-1]
    assert a["type"] == "error", a
    return a["reason"]


# ---- the probe and its positive control ----

def test_R_077_03_probe_the_clash_kills_at_least_one_player_unit():
    dead = _dead_ids()
    assert len(dead) >= 1, "fixture drifted: the clash no longer kills player units, the killed-commander tests below cannot run"


# ---- command answers ----

def test_R_077_05_no_world_errors():
    frames = _run([_assign(1)])
    assert _error_reason(frames) == "no world"


def test_R_077_05_mission_not_started_errors():
    frames = _run([SET_SEED, _assign(1)])
    assert _error_reason(frames) == "mission not started"


def test_R_077_05_missing_unit_id_errors():
    frames = _run([SET_SEED, START, {"type": "cmd", "name": "assign_commander"}])
    assert _error_reason(frames) == "missing unit_id"


def test_R_077_05_unit_not_in_force_errors_for_unknown_and_enemy_ids():
    player, _, _ = _centroid_and_ids()
    enemy_id = max(player) + 1
    frames = _run([SET_SEED, START, _assign(999999), _assign(enemy_id)])
    ans = _answers(frames)
    assert [a["type"] for a in ans] == ["error", "error"], ans
    assert [a["reason"] for a in ans] == ["unit not in force", "unit not in force"]


def test_R_077_05_assign_in_recon_and_reassign_in_play_both_ack_with_a_tick():
    frames = _run([SET_SEED, START, _assign(1), BEGIN, _assign(2),
                   {"type": "cmd", "name": "tactical_step", "n": 3}, _assign(3)])
    ans = _answers(frames)
    assert [a["type"] for a in ans] == ["ack", "ack", "ack"], ans
    assert all(isinstance(a["tick"], int) for a in ans), ans


def test_R_077_05_a_failed_assign_changes_nothing_and_writes_one_frame():
    frames = _run([SET_SEED, START, _assign(1), _assign(999999)])
    ans = _answers(frames)
    assert [a["type"] for a in ans] == ["ack", "error"], ans
    assert len(_types(frames, "mission")) == 1, "assign_commander must write no mission frame"


def test_R_077_05_mission_ended_errors():
    frames = _run([SET_SEED, START, BEGIN, END, _assign(1)])
    assert _error_reason(frames) == "mission ended"


def test_R_077_05_unit_dead_errors_when_no_live_commander_blocks_it():
    dead = _dead_ids()
    assert dead, "probe found no dead unit"
    frames = _run(_clash_cmds(after=[_assign(dead[0])]))
    assert _error_reason(frames) == "unit dead"


def test_R_077_05_commander_dead_blocks_reassignment():
    frames = _killed_commander_run()
    ans = _answers(frames)
    assert ans[0]["type"] == "ack", ans
    assert ans[-1]["type"] == "error" and ans[-1]["reason"] == "commander dead", ans


# ---- mission frame ----

def test_R_077_05_mission_frame_commander_unit_is_zero_with_none_assigned():
    frames = _run([SET_SEED, START])
    mission = _types(frames, "mission")[0]
    assert mission["commander_unit"] == 0 and type(mission["commander_unit"]) is int


# ---- debrief ----

def test_R_077_03_debrief_commander_fate_is_an_int_survived_with_none_assigned():
    frames = _run([SET_SEED, START, BEGIN, END])
    debrief = _types(frames, "debrief")[0]
    assert type(debrief["commander_fate"]) is int, debrief
    assert debrief["commander_fate"] == FATE_SURVIVED


def test_R_077_03_debrief_commander_fate_survived_for_an_assigned_live_unit():
    frames = _run([SET_SEED, START, _assign(1), BEGIN, END])
    assert _types(frames, "debrief")[0]["commander_fate"] == FATE_SURVIVED


def test_R_077_03_killed_commander_unit_shows_fate_zero_in_the_debrief():
    debrief = _types(_killed_commander_run(), "debrief")[0]
    assert debrief["commander_fate"] == FATE_KILLED, debrief


def test_R_077_03_control_a_living_commander_in_the_same_clash_does_not_show_killed():
    dead = _dead_ids()
    live = next(i for i in _centroid_and_ids()[0] if i not in dead)
    frames = _run(_clash_cmds(commander=live, after=[END]))
    assert _types(frames, "debrief")[0]["commander_fate"] in (FATE_WOUNDED, FATE_SURVIVED)


def test_R_077_03_refused_mission_debrief_omits_commander_fate():
    frames = _run([SET_SEED, START, {"type": "cmd", "name": "mission_refuse"}])
    debrief = _types(frames, "debrief")[0]
    assert "commander_fate" not in debrief, debrief
