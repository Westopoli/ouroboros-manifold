"""B6: the chapter lifecycle over the pipe (R-055-06, R-055-04, R-062-01).

docs/architecture.md (B6 contract): the snapshot frame carries `chapter` (uint, the
opening jump belongs to chapter 1, it advances once at the end of each jump that
follows a mission) and `commander` (character id, 0 when none); the chronicle frame's
`jump` object carries `chapter_end_reason` (0 normal, 1 commander death, 2 faction
collapsed).

Fixture limits, all measured on origin/push/B6-contract:
- A pipe campaign never has a lineage or a character (seeds 1 to 400, opening jump
  plus three jumps: om_character_count and om_lineage_count are 0 on every one), so
  a lineage cannot lose its last member through jumps and missions. The rotation path
  is proven by tests/csim/test_core_chapter_lifecycle.py. Here `commander` is only
  checked to be present and 0.
- The pipe has no verb that refuses a mission, so only the played-mission case is
  driven; the refused case is core-only.
- Faction collapse is reachable: seed 389 with 1000-tick jumps loses every player
  region at the end of its second post-mission jump (found by scanning seeds 1 to 400;
  see COLLAPSE_SEED).

Every field assertion is red on a pipe that does not send the field (a missing key
counts as red); the controls pin the case the new field must not change.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
END = {"type": "cmd", "name": "mission_end"}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
QUIT = {"type": "cmd", "name": "quit"}
COLLAPSE_SEED = 389
COLLAPSE_JUMP_TICKS = 1000
PLAYER = 0
REASON_NORMAL, REASON_FACTION_COLLAPSED = 0, 2

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _jump(ticks=50):
    return {"type": "cmd", "name": "jump", "ticks": ticks}


def _of_type(frames, kind):
    return [f for f in frames if f["type"] == kind]


def _chapter(snapshot):
    assert "chapter" in snapshot, "snapshot frame has no `chapter` field: %s" % sorted(snapshot)
    return snapshot["chapter"]


def _reason(chronicle):
    assert "chapter_end_reason" in chronicle["jump"], "chronicle jump has no chapter_end_reason: %r" % chronicle["jump"]
    return chronicle["jump"]["chapter_end_reason"]


def _mission_jump(ticks=50):
    return [START, END, _jump(ticks)]


def test_R_055_06_chapter_is_1_after_set_seed_and_the_opening_jump():
    frames = _run([SET_SEED, SNAPSHOT])
    assert _chapter(_of_type(frames, "snapshot")[0]) == 1


def test_R_055_06_a_jump_with_no_preceding_mission_leaves_the_chapter_unchanged():
    frames = _run([SET_SEED, _jump(), _jump()])
    assert [_chapter(s) for s in _of_type(frames, "snapshot")] == [1, 1]


def test_R_055_06_mission_then_jump_advances_the_chapter_by_one():
    frames = _run([SET_SEED] + _mission_jump())
    snaps = _of_type(frames, "snapshot")
    assert len(snaps) == 2, frames
    after_mission_end, after_jump = snaps
    assert _chapter(after_mission_end) == 1, "the mission's own end snapshot is still chapter 1"
    assert _chapter(after_jump) == 2


def test_R_055_06_a_retry_jump_after_the_post_mission_jump_does_not_advance_again():
    frames = _run([SET_SEED] + _mission_jump() + [_jump()])
    assert [_chapter(s) for s in _of_type(frames, "snapshot")] == [1, 2, 2]


def test_R_055_06_control_each_further_mission_advances_once_more():
    frames = _run([SET_SEED] + _mission_jump() + _mission_jump())
    assert [_chapter(s) for s in _of_type(frames, "snapshot")] == [1, 2, 2, 3]


def test_R_055_06_mission_start_reads_the_generator_result_it_does_not_select_again():
    """The generator runs once, at the end of the jump (ruling B6 item 3); a second
    mission_start in the same chapter reads that same result. Before B6, mission_start
    made its own weighted draw each time and the two picks could differ."""
    frames = _run([SET_SEED] + _mission_jump() + [START, END, START])
    missions = _of_type(frames, "mission")
    assert len(missions) == 3, frames
    first_in_chapter_2, second_in_chapter_2 = missions[1], missions[2]
    assert second_in_chapter_2["region"] == first_in_chapter_2["region"]
    assert second_in_chapter_2["archetype"] == first_in_chapter_2["archetype"]


def test_R_055_06_same_seed_and_commands_give_identical_frames():
    cmds = [SET_SEED] + _mission_jump() + _mission_jump()
    first, second = _run(cmds), _run(cmds)
    assert len(first) == len(second) > 0
    assert first == second


def test_R_055_04_the_snapshot_carries_a_commander_id():
    """A pipe campaign has no lineage (see the module note), so the id is 0, the
    documented `none selected`. The rotation itself is the core test."""
    frames = _run([SET_SEED, SNAPSHOT] + _mission_jump())
    snaps = _of_type(frames, "snapshot")
    for s in snaps:
        assert "commander" in s, "snapshot frame has no `commander` field: %s" % sorted(s)
        assert isinstance(s["commander"], int) and s["commander"] >= 0
    assert [s["commander"] for s in snaps] == [0] * len(snaps)


def test_R_062_01_chapter_end_reason_is_normal_on_an_ordinary_jump():
    frames = _run([SET_SEED, _jump()] + _mission_jump())
    chronicles = _of_type(frames, "chronicle")
    assert len(chronicles) == 2
    assert [_reason(c) for c in chronicles] == [REASON_NORMAL, REASON_NORMAL]


def _collapse_run():
    cmds = [dict(SET_SEED, seed=COLLAPSE_SEED)] + _mission_jump(COLLAPSE_JUMP_TICKS) + _mission_jump(COLLAPSE_JUMP_TICKS)
    return _run(cmds)


def _owned_by_player(snapshot):
    return sum(1 for r in snapshot["regions"] if r["owner"] == PLAYER)


def test_R_062_01_chapter_end_reason_is_faction_collapsed_when_the_player_loses_every_region():
    frames = _collapse_run()
    snaps, chronicles = _of_type(frames, "snapshot"), _of_type(frames, "chronicle")
    assert len(chronicles) == 2, frames
    final_snapshot = snaps[-1]
    assert _owned_by_player(final_snapshot) == 0, "fixture drifted: seed %d no longer collapses by its second jump" % COLLAPSE_SEED
    assert _reason(chronicles[0]) == REASON_NORMAL
    assert _reason(chronicles[1]) == REASON_FACTION_COLLAPSED
    assert _chapter(final_snapshot) == 3, "a collapse ends the chapter, it still advances"


def test_R_062_01_control_the_collapse_fixture_is_normal_before_the_collapse():
    frames = _collapse_run()
    first_jump_snapshot = _of_type(frames, "snapshot")[1]
    assert _owned_by_player(first_jump_snapshot) > 0
    assert _reason(_of_type(frames, "chronicle")[0]) == REASON_NORMAL
