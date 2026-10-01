"""B3 (mission-plays plan, R-078-05, R-079-02): `mission_refuse`, the briefing's Refuse
control (docs/architecture.md "session commands", B3-verbs-docs).

Valid only in recon (after `mission_start`, before `mission_begin`). It answers what
`mission_end` answers, a `debrief` frame then a `snapshot`: band 5 (refusal), `achieved`
and `brought_home` 0.0, `region_delta.tension` the applied change (8 percent of the
deficit, (100 - tension) * 0.08, clamped to [0, 100]), the other `region_delta` fields
0.0, and no `commander_fate` key. The mission ends, so the phase returns to strategic.
Errors, each `{"type":"error","name":"mission_refuse","reason":...}`: `no world`,
`no mission`, `already begun`.

The chronicle test (last) needs the B5 consequence entry as well as B3; it stays red
until both land.

Positive control: on a pipe without the verb every case is red (`unknown command`).
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
BEGIN = {"type": "cmd", "name": "mission_begin"}
END = {"type": "cmd", "name": "mission_end"}
REFUSE = {"type": "cmd", "name": "mission_refuse"}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
STEP = {"type": "cmd", "name": "step", "n": 1}
TACTICAL_STEP = {"type": "cmd", "name": "tactical_step", "n": 1}
JUMP = {"type": "cmd", "name": "jump", "ticks": 50}
QUIT = {"type": "cmd", "name": "quit"}

BAND_REFUSAL = 5
REFUSAL_PCT = 8.0
FIELD_MAX = 100.0

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


def _assert_error(frame, name, reason=None):
    assert frame["type"] == "error" and frame["name"] == name, frame
    assert frame["reason"] != "unknown command", "%s is not implemented: %r" % (name, frame)
    if reason is not None:
        assert frame["reason"] == reason, frame


def _refused():
    """frames of: set_seed, mission_start, snapshot (baseline), mission_refuse."""
    return _run([SET_SEED, START, SNAPSHOT, REFUSE])


def _split(frames):
    mission = next(f for f in frames if f["type"] == "mission")
    base = next(f for f in frames if f["type"] == "snapshot")
    after = frames[[i for i, f in enumerate(frames) if f["type"] == "snapshot"][0] + 1:]
    return mission, base, after


def test_refuse_in_recon_answers_debrief_then_snapshot():
    frames = _run([SET_SEED, START, REFUSE])
    assert [f["type"] for f in frames] == ["mission", "debrief", "snapshot"], frames


def test_refusal_debrief_carries_band_5_and_no_result():
    frames = _run([SET_SEED, START, REFUSE])
    assert frames[1]["type"] == "debrief", frames
    debrief = frames[1]
    assert debrief["band"] == BAND_REFUSAL, debrief
    assert debrief["achieved"] == 0.0 and debrief["brought_home"] == 0.0, debrief
    assert "commander_fate" not in debrief, debrief
    delta = debrief["region_delta"]
    for field in ("military", "economy", "population"):
        assert delta[field] == 0.0, debrief


def test_refusal_raises_tension_by_8_percent_of_the_deficit():
    frames = _refused()
    mission, base, after = _split(frames)
    assert [f["type"] for f in after] == ["debrief", "snapshot"], frames
    region = mission["region"]
    before = base["regions"][region]
    t0 = before["tension"]
    assert t0 < FIELD_MAX, "fixture needs tension below the cap: %r" % t0
    expected = min(FIELD_MAX, t0 + (FIELD_MAX - t0) * REFUSAL_PCT / FIELD_MAX)
    assert expected > t0
    debrief, snapshot = after
    assert debrief["region_delta"]["tension"] == pytest.approx(expected - t0, abs=1e-9), debrief
    assert snapshot["regions"][region]["tension"] == pytest.approx(expected, abs=1e-9), snapshot["regions"][region]


def test_refusal_changes_only_the_mission_regions_tension():
    frames = _refused()
    mission, base, after = _split(frames)
    assert [f["type"] for f in after] == ["debrief", "snapshot"], frames
    snapshot = after[1]
    region = mission["region"]
    for old, new in zip(base["regions"], snapshot["regions"]):
        for field in ("owner", "military", "economy", "population"):
            assert new[field] == old[field], (field, old, new)
        if old["i"] != region:
            assert new["tension"] == old["tension"], (old, new)


def test_refuse_without_a_world_answers_no_world():
    _assert_error(_run([REFUSE])[0], "mission_refuse", "no world")


def test_refuse_without_a_mission_answers_no_mission():
    _assert_error(_run([SET_SEED, REFUSE])[0], "mission_refuse", "no mission")


def test_refuse_twice_answers_no_mission_the_second_time():
    frames = _run([SET_SEED, START, REFUSE, REFUSE])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    _assert_error(frames[3], "mission_refuse", "no mission")


def test_refuse_after_mission_end_answers_no_mission():
    frames = _run([SET_SEED, START, END, REFUSE])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    _assert_error(frames[3], "mission_refuse", "no mission")


def test_refuse_after_begin_answers_already_begun_and_changes_nothing():
    frames = _run([SET_SEED, START, BEGIN, REFUSE, TACTICAL_STEP])
    assert [f["type"] for f in frames[:2]] == ["mission", "tactical"], frames
    _assert_error(frames[2], "mission_refuse", "already begun")
    assert frames[3]["type"] == "tactical", "the begun mission must keep running: %r" % frames[3:]


def test_refused_mission_is_over_for_the_tactical_commands():
    for later in (BEGIN, END, TACTICAL_STEP):
        frames = _run([SET_SEED, START, REFUSE, later])
        assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
        _assert_error(frames[3], later["name"])


def test_phase_returns_to_strategic_so_step_and_jump_work():
    frames = _run([SET_SEED, START, REFUSE, STEP, JUMP])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    rest = frames[3:]
    assert not [f for f in rest if f["type"] == "error"], rest
    types = [f["type"] for f in rest]
    assert types[-2:] == ["chronicle", "snapshot"], rest


def test_strategic_step_is_refused_during_recon_until_refusal_ends_the_mission():
    """Control: the same `step` is refused while the mission is still in recon, so the
    acceptance above comes from the refusal and not from a phase that never held."""
    frames = _run([SET_SEED, START, STEP])
    _assert_error(frames[1], "step")


def test_next_jump_carries_the_refusal_into_the_chronicle_as_a_failure_consequence():
    """E-09 R-065-02 maps band refusal to outcome failure; the consequence cluster is
    entry 1. cluster_type 0 is CONSEQUENCE, category 1 is outcome FAILURE
    (csrc/chronicle.c). Red until B5 (gen_time_jump adds the consequence entry) lands
    with B3."""
    frames = _run([SET_SEED, START, REFUSE, JUMP])
    chronicle = next((f for f in frames if f["type"] == "chronicle"), None)
    assert chronicle is not None, [f["type"] for f in frames]
    assert chronicle["entries"], "jump after a refusal wrote no chronicle entries: %r" % chronicle
    first = chronicle["entries"][0]
    assert first["cluster_type"] == 0, first
    assert first["category"] == 1, first
    assert first["refs"]["regions"] == [_run([SET_SEED, START])[0]["region"]], first
