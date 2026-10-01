"""B6: the chapter lifecycle over the pipe (R-055-06, R-057-09, R-055-04, R-062-01).

Rulings: docs/northstar/plans/2026-10-01-architect-rulings-2.md section 1.
docs/architecture.md: the snapshot frame carries `chapter` (uint, the opening jump belongs
to chapter 1, it advances once at the end of each jump that follows a mission, played or
refused) and `commander` (character id of the selector's latest pick); the chronicle
frame's `jump` object carries `chapter_end_reason` (0 normal, 1 commander death, 2 faction
collapsed).

What runs at the end of which jump (ruling 1.2): the opening jump runs the generator and the
selector (no collapse check, no advance); a jump after a mission, played or refused, runs the
collapse check, the generator, the selector and the advance; a retry jump runs the generator
only. So after `set_seed` the selector has already seated the first commander (R-057-09: a
forced rotation whose unrelated pool creates the first character and lineage), and these tests
rely on that and never seed a character.

Fixtures, not thresholds: seed 156 with 1000-tick jumps loses every player region at the end of
its second post-mission jump while holding 3 at the end of the first. Found by scanning seeds 1 to
400 on the B6 reference build (the generator moved into the jump, so the old seed 389 no longer
collapses); see COLLAPSE_SEED. Seeds 152 and 281 also qualify.

A15 (Addendum 6): when the collapse check fires, the player faction is reassigned in the same
jump (the snapshot's `player_faction` carries it). When no faction survives the jump takes the
terminal path (om_campaign_trigger_terminal_restart); the wire has no field for that, so it is
core-only (tests/csim/test_core_chapter_lifecycle.py) and an open item for the client.

Not reachable over the pipe today: the commander-death end reason (the commander fate is never
`killed` until B7 lands the assignment path in play), so it is core-only
(tests/csim/test_core_chapter_lifecycle.py, where collapse-wins-over-death is also proven).

Every field assertion is red on a pipe that does not send the field (a missing key counts as
red); the controls pin the case the new field must not change.
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
REFUSE = {"type": "cmd", "name": "mission_refuse"}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
QUIT = {"type": "cmd", "name": "quit"}
COLLAPSE_SEED = 156
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


def _commander(snapshot):
    assert "commander" in snapshot, "snapshot frame has no `commander` field: %s" % sorted(snapshot)
    return snapshot["commander"]


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


def test_R_057_09_set_seed_leaves_the_first_commander_seated():
    frames = _run([SET_SEED, SNAPSHOT])
    commander = _commander(_of_type(frames, "snapshot")[0])
    assert isinstance(commander, int) and commander > 0, "the opening jump must seat a commander"


def test_R_057_09_control_a_world_set_up_without_the_opening_jump_has_no_commander():
    frames = _run([dict(SET_SEED, new_campaign=False), SNAPSHOT])
    assert _commander(_of_type(frames, "snapshot")[0]) == 0


def test_R_055_06_a_retry_jump_runs_no_selector_so_the_commander_stays():
    frames = _run([SET_SEED, SNAPSHOT, _jump(), _jump()])
    commanders = [_commander(s) for s in _of_type(frames, "snapshot")]
    assert len(commanders) == 3 and commanders[0] > 0
    assert commanders == [commanders[0]] * 3


def test_R_055_04_the_post_mission_jump_runs_the_selector():
    """The selector runs in the jump that follows a mission and always leaves a commander
    seated (a stay, or a rotation to a new one)."""
    frames = _run([SET_SEED] + _mission_jump())
    after_jump = _of_type(frames, "snapshot")[-1]
    assert _commander(after_jump) > 0


def test_R_055_06_a_refused_mission_arms_the_chapter_advance_like_a_played_one():
    frames = _run([SET_SEED, START, REFUSE, _jump(), _jump()])
    assert [_chapter(s) for s in _of_type(frames, "snapshot")] == [1, 2, 2]
    chronicles = _of_type(frames, "chronicle")
    assert [_reason(c) for c in chronicles] == [REASON_NORMAL, REASON_NORMAL]


def test_R_072_07_a_world_with_no_generator_result_retries_through_jumps_without_a_selector():
    """With no opening jump the generator has never run, so mission_start finds no candidate
    and takes the A3 retry path: each retry is a jump (the tick moves) that re-runs the
    generator and never the selector (the commander stays 0)."""
    frames = _run([dict(SET_SEED, new_campaign=False), START, SNAPSHOT])
    missions = _of_type(frames, "mission")
    assert len(missions) == 1, frames
    snap = _of_type(frames, "snapshot")[0]
    assert snap["tick"] >= 20, "no retry jump ran"
    assert _commander(snap) == 0


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


def test_R_062_02_the_collapse_jump_reassigns_the_player_faction_on_the_wire():
    frames = _collapse_run()
    snaps = _of_type(frames, "snapshot")
    assert snaps[1]["player_faction"] == PLAYER, "control: the first jump keeps faction 0"
    final = snaps[-1]
    assert _owned_by_player(final) == 0
    assert final["player_faction"] not in (PLAYER, -1), "the collapse jump did not reassign the player faction"
    held = sum(1 for r in final["regions"] if r["owner"] == final["player_faction"])
    assert held > 0, "reassigned to a faction that holds no region"
