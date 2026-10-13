"""SV-1: scripts/simviewer/pipe_session.py, the viewer's pipe client.

Piece SV-1 of docs/northstar/plans/2026-10-12-simviewer-spec.md, section
"Shared interfaces" (frozen API) and "Pre-flight corrections" 1 to 4.

Rules proved (spec, not game rules; the viewer is tooling):
  - framing is 4-byte big-endian length + JSON body, hello first (pre-flight 1);
  - frames per verb (pre-flight 2): step n -> n delta then one ack (ack last),
    snapshot -> 1, mission_end -> [debrief, snapshot], jump -> [chronicle,
    snapshot], set_seed -> [] on success; an error frame raises PipeError;
  - close() sends quit and the process exits; the context manager closes;
  - constants DEFAULT_FEATURES and JUMP_TICKS (pre-flight 4).

Part 1 uses a fake pipe script (no binary). Part 2 is the positive control for
the error detector. Part 3 drives the real pipe/ouroboros_pipe_dbg.

Red on the built tree: module scripts.simviewer.pipe_session does not exist
(ImportError). Green after SV-1 builds it.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.simviewer.pipe_session import (  # noqa: E402
    DEFAULT_FEATURES,
    JUMP_TICKS,
    TERMINAL,
    PipeError,
    PipeSession,
)

PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"

# A python script that speaks the pipe framing. argv[1] = marker file written
# when quit arrives (holds the process id), argv[2] = mode ("ok" or "errstep").
FAKE = r'''
import json, os, sys

marker, mode = sys.argv[1], sys.argv[2]
out, inp = sys.stdout.buffer, sys.stdin.buffer


def put(obj):
    body = json.dumps(obj).encode()
    out.write(len(body).to_bytes(4, "big") + body)
    out.flush()


def get():
    head = inp.read(4)
    if len(head) < 4:
        return None
    return json.loads(inp.read(int.from_bytes(head, "big")))


put({"type": "hello", "abi": 7, "layout_ok": True, "player_faction": -1})
tick = 0
while True:
    c = get()
    if c is None:
        break
    name = c["name"]
    if name == "quit":
        with open(marker, "w") as f:
            f.write(str(os.getpid()))
        break
    if name == "set_seed":
        continue  # silent on success
    if name == "step":
        if mode == "errstep":
            put({"type": "error", "name": "step", "reason": "no world"})
            continue
        for _ in range(c.get("n", 1)):
            tick += 1
            put({"type": "delta", "tick": tick, "checksum": 0, "regions": []})
        put({"type": "ack", "name": "step", "tick": tick})
    elif name == "snapshot":
        put({"type": "snapshot", "tick": tick, "regions": []})
    elif name == "mission_start":
        put({"type": "error", "name": "mission_start", "reason": "no world"})
    elif name == "mission_end":
        put({"type": "debrief", "band": 1})
        put({"type": "snapshot", "tick": tick, "regions": []})
    elif name == "jump":
        tick += c["ticks"]
        put({"type": "chronicle", "entries": []})
        put({"type": "snapshot", "tick": tick, "regions": []})
    else:
        put({"type": "error", "name": name, "reason": "unknown command"})
'''


def _fake(tmp_path, mode="ok"):
    script = tmp_path / "fake_pipe.py"
    script.write_text(FAKE)
    marker = tmp_path / "quit.marker"
    argv = [sys.executable, str(script), str(marker), mode]
    return argv, marker


def _types(frames):
    return [f["type"] for f in frames]


# ---------------------------------------------------------------- constants

def test_constants_pinned():
    """SV-1 / spec pre-flight 4: DEFAULT_FEATURES == [0..7] (autoload/c_bridge.gd:27)
    and JUMP_TICKS == 50 (autoload/c_bridge.gd:749)."""
    assert DEFAULT_FEATURES == [0, 1, 2, 3, 4, 5, 6, 7]
    assert JUMP_TICKS == 50


def test_terminal_table_pinned():
    """SV-1 / spec pre-flight 2: TERMINAL maps each verb to the frame types it
    answers, in order (architecture.md session commands)."""
    expected = {
        "snapshot": ["snapshot"],
        "mission_start": ["mission"],
        "objective_complete": ["ack"],
        "mission_end": ["debrief", "snapshot"],
        "mission_refuse": ["debrief", "snapshot"],
        "jump": ["chronicle", "snapshot"],
    }
    for verb, types in expected.items():
        assert verb in TERMINAL, "TERMINAL has no entry for %r" % verb
        assert list(TERMINAL[verb]) == types, (
            "TERMINAL[%r] = %r, expected %r" % (verb, TERMINAL[verb], types))


# ---------------------------------------------------------------- fake pipe

def test_fake_hello_stored(tmp_path):
    """SV-1 / pre-flight 1: the first frame the server writes is hello and
    PipeSession stores it as .hello."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        assert s.hello["type"] == "hello"
        assert s.hello["abi"] == 7


def test_fake_step_n3_returns_three_deltas_then_ack(tmp_path):
    """SV-1 / pre-flight 2: step n=3 returns 3 delta frames then the ack, ack last."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        frames = s.send("step", n=3)
        assert _types(frames) == ["delta", "delta", "delta", "ack"]
        assert [f["tick"] for f in frames[:3]] == [1, 2, 3]
        assert frames[-1] == {"type": "ack", "name": "step", "tick": 3}


def test_fake_step_default_n_is_one(tmp_path):
    """SV-1 / frozen API: step defaults to n=1 -> one delta then the ack."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        assert _types(s.send("step")) == ["delta", "ack"]


def test_fake_snapshot_returns_one(tmp_path):
    """SV-1 / pre-flight 2: snapshot answers exactly one snapshot frame."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        assert _types(s.send("snapshot")) == ["snapshot"]


def test_fake_mission_end_returns_debrief_then_snapshot(tmp_path):
    """SV-1 / pre-flight 2: mission_end answers [debrief, snapshot]."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        assert _types(s.send("mission_end")) == ["debrief", "snapshot"]


def test_fake_jump_returns_chronicle_then_snapshot(tmp_path):
    """SV-1 / pre-flight 2: jump answers [chronicle, snapshot]."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        frames = s.send("jump", ticks=JUMP_TICKS)
        assert _types(frames) == ["chronicle", "snapshot"]
        assert frames[1]["tick"] == JUMP_TICKS


def test_fake_set_seed_returns_empty_and_does_not_eat_next_frame(tmp_path):
    """SV-1 / pre-flight 2: set_seed answers no frame on success -> []. The next
    command must still get its own frame (no desync)."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        assert s.send("set_seed", seed=1, n_regions=80, features=DEFAULT_FEATURES) == []
        assert _types(s.send("snapshot")) == ["snapshot"]


def test_fake_error_frame_raises_pipe_error_with_frame(tmp_path):
    """SV-1 / pre-flight 2: an error frame raises PipeError and exposes it as .frame."""
    argv, _ = _fake(tmp_path)
    with PipeSession(argv=argv) as s:
        with pytest.raises(PipeError) as exc:
            s.send("mission_start", faction=0)
        assert exc.value.frame["type"] == "error"
        assert exc.value.frame["name"] == "mission_start"
        assert exc.value.frame["reason"] == "no world"


def test_fake_close_sends_quit_and_process_exits(tmp_path):
    """SV-1 / frozen API: close() sends quit and the process exits (the fake
    records its pid on quit; after close() that pid must be gone)."""
    argv, marker = _fake(tmp_path)
    s = PipeSession(argv=argv)
    assert not marker.exists()
    s.close()
    assert marker.exists(), "fake never received quit"
    with pytest.raises(ProcessLookupError):
        os.kill(int(marker.read_text()), 0)


def test_fake_context_manager_closes(tmp_path):
    """SV-1 / frozen API: leaving the with-block closes the session (quit sent)."""
    argv, marker = _fake(tmp_path)
    with PipeSession(argv=argv):
        assert not marker.exists()
    assert marker.exists(), "context manager exit did not send quit"


# ------------------------------------------------------------ positive control

def test_positive_control_error_frame_makes_send_raise(tmp_path):
    """SV-1 positive control: a fake that answers step with an error frame must
    make send raise PipeError; proves the error detector fires (if this passes
    only because send never raises, the other tests prove nothing)."""
    argv, _ = _fake(tmp_path, mode="errstep")
    with PipeSession(argv=argv) as s:
        with pytest.raises(PipeError) as exc:
            s.send("step", n=2)
        assert exc.value.frame["reason"] == "no world"


# ------------------------------------------------------------ real dbg pipe

needs_pipe = pytest.mark.skipif(
    not PIPE_DBG.exists(),
    reason="pipe/ouroboros_pipe_dbg not built: run make pipe/ouroboros_pipe_dbg")


@needs_pipe
def test_real_set_seed_then_snapshot_has_80_regions():
    """SV-1 / pre-flight 2: set_seed (seed 1, 80 regions; 60 is below the feasible
    minimum and fails generation) answers no frame; snapshot returns 80 regions."""
    with PipeSession() as s:
        assert s.send("set_seed", seed=1, n_regions=80, features=DEFAULT_FEATURES) == []
        frames = s.send("snapshot")
        assert _types(frames) == ["snapshot"]
        assert len(frames[0]["regions"]) == 80


@needs_pipe
def test_real_step_three_deltas_then_ack():
    """SV-1 / pre-flight 2: on the real pipe step n=3 is 3 delta frames then
    {"type":"ack","name":"step"} with the last delta's tick."""
    with PipeSession() as s:
        s.send("set_seed", seed=1, n_regions=80, features=DEFAULT_FEATURES)
        frames = s.send("step", n=3)
        assert _types(frames) == ["delta", "delta", "delta", "ack"]
        assert frames[-1]["name"] == "step"
        assert frames[-1]["tick"] == frames[2]["tick"]


@needs_pipe
def test_real_mission_cycle_start_complete_end():
    """SV-1 / pre-flight 2 and 3: mission_start answers a mission frame with an
    in-range region; objective_complete (debug verb) answers an ack; mission_end
    answers [debrief, snapshot] with band in 0..4. Setup copied from
    tests/transport/test_pipe_debrief_region_delta.py (seed 16, 80 regions,
    new_campaign False, faction 0)."""
    with PipeSession() as s:
        s.send("set_seed", seed=16, n_regions=80, features=DEFAULT_FEATURES,
               new_campaign=False)
        start = s.send("mission_start", faction=0)
        assert _types(start) == ["mission"]
        assert 0 <= start[0]["region"] < 80
        ack = s.send("objective_complete", objective=0, completion=1.0)
        assert _types(ack) == ["ack"]
        end = s.send("mission_end")
        assert _types(end) == ["debrief", "snapshot"]
        assert 0 <= end[0]["band"] <= 4


@needs_pipe
def test_real_jump_returns_chronicle_and_snapshot_with_later_tick():
    """SV-1 / pre-flight 2 and 4: jump ticks=JUMP_TICKS on a fresh strategic world
    answers [chronicle, snapshot]; the snapshot tick is greater than before."""
    with PipeSession() as s:
        s.send("set_seed", seed=1, n_regions=80, features=DEFAULT_FEATURES)
        before = s.send("snapshot")[0]["tick"]
        frames = s.send("jump", ticks=JUMP_TICKS)
        assert _types(frames) == ["chronicle", "snapshot"]
        assert frames[1]["tick"] > before


@needs_pipe
def test_real_error_frame_raises_pipe_error():
    """SV-1 positive control on the real pipe: step with no world answers an
    error frame, so send raises PipeError carrying it."""
    with PipeSession() as s:
        with pytest.raises(PipeError) as exc:
            s.send("step")
        assert exc.value.frame["type"] == "error"
