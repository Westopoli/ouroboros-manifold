"""T1-4: `mission_begin` is the player's Begin (docs/architecture.md "session commands
(v1.1)", E-12 S-092 R-092-02/03): mission_start leaves the mission in recon (clock not
started), mission_begin ends recon, moves the phase to tactical and answers a tactical
frame; outside a recon-phase mission it answers error.

Positive control: the begin-after-start case is red on a pipe whose mission_start already
began the mission (T1-2), and the refusal cases are red on a pipe that has no mission_begin.
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
STEP = {"type": "cmd", "name": "tactical_step", "n": 1}
QUIT = {"type": "cmd", "name": "quit"}

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


def _assert_refused(frame):
    assert frame["type"] == "error" and frame["name"] == "mission_begin", frame
    assert frame["reason"] != "unknown command", "mission_begin is not implemented: %r" % frame


def test_begin_after_start_answers_a_tactical_frame():
    frames = _run([SET_SEED, START, BEGIN])
    assert [f["type"] for f in frames] == ["mission", "tactical"], frames
    tactical = frames[1]
    assert isinstance(tactical["units"], list) and "map" in tactical and "tick" in tactical


def test_begin_then_tactical_steps_advance_from_the_begin_frame():
    frames = _run([SET_SEED, START, BEGIN, STEP])
    ticks = [f["tick"] for f in frames if f["type"] == "tactical"]
    assert len(ticks) == 2 and ticks[1] == ticks[0] + 1, frames


def test_begin_twice_answers_error_the_second_time():
    frames = _run([SET_SEED, START, BEGIN, BEGIN])
    assert frames[1]["type"] == "tactical", frames
    _assert_refused(frames[2])


def test_begin_without_a_world_answers_error():
    _assert_refused(_run([BEGIN])[0])


def test_begin_without_a_mission_answers_error():
    _assert_refused(_run([SET_SEED, BEGIN])[0])


def test_begin_after_the_mission_ended_answers_error():
    frames = _run([SET_SEED, START, END, BEGIN])
    types = [f["type"] for f in frames]
    assert types[:3] == ["mission", "debrief", "snapshot"], frames
    _assert_refused(frames[3])
