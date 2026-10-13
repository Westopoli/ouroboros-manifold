"""T1-15: place_structure debug verb (docs/architecture.md test-and-debug verbs).

place_structure places a production structure in the live tactical world and
replies {"type":"ok","structure":<id>}. Gated by OM_DEBUG_INJECT: the non-debug
pipe rejects it as an unknown command.

(a) debug pipe: verb returns ok with structure id; second call returns different id.
(b) bad args (missing key, kind out of range) return error frame.
(c) non-debug pipe rejects the verb like any other unknown command.
(d) no frame exposes structures: the tactical frame keys are type/tick/map/units/visible;
    the effect of a placed structure is observed through the units it produces (tested
    in tests/transport/test_pipe_structure_production.py).
(e) Red on base (main before T1-15): place_structure verb unknown in debug pipe.
    Green after T1-15: verb wired to place structure in the live world.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]

if not PIPE_DBG.exists():
    pytest.fail("pipe/ouroboros_pipe_dbg missing: run make pipe/ouroboros_pipe_dbg")
if not PIPE.exists():
    pytest.fail("pipe/ouroboros_pipe missing: run make pipe/ouroboros_pipe")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(pipe_bin, cmds):
    quit_cmd = {"type": "cmd", "name": "quit"}
    script = b"".join(_frame(c) for c in cmds + [quit_cmd])
    proc = subprocess.run([str(pipe_bin)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
            "features": FEATURES}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
PLACE = {"type": "cmd", "name": "place_structure", "kind": 0, "owner": 1,
         "x": 0.0, "y": 0.0}


# ---- (a) verb returns ok with a structure id ----

def test_place_structure_returns_ok_with_id():
    """After set_seed and mission_start, place_structure returns ok with a
    structure id. Two calls return different ids (0 then 1).

    Red on base: verb unknown -> error. Green after T1-15: verb wired.
    """
    frames = _run(PIPE_DBG, [SET_SEED, START, PLACE, PLACE])
    ok_frames = [f for f in frames if f.get("type") == "ok"]
    assert len(ok_frames) == 2, (
        "expected 2 ok frames from 2 place_structure calls; got: %r"
        % [f.get("type") for f in frames])
    id0 = ok_frames[0].get("structure")
    id1 = ok_frames[1].get("structure")
    assert isinstance(id0, int), "structure id must be int, got %r" % id0
    assert isinstance(id1, int), "structure id must be int, got %r" % id1
    assert id0 != id1, (
        "two calls must return different structure ids; both returned %d" % id0)
    assert id1 == id0 + 1, (
        "second call must return slot %d, got %d" % (id0 + 1, id1))


# ---- (b) bad args return error frame ----

def test_place_structure_missing_kind_returns_error():
    """missing 'kind' key -> error frame, no consumption of anything."""
    cmd = {"type": "cmd", "name": "place_structure", "owner": 1, "x": 0.0, "y": 0.0}
    frames = _run(PIPE_DBG, [SET_SEED, START, cmd])
    err = frames[-1]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "missing kind", err


def test_place_structure_kind_out_of_range_returns_error():
    """kind=6 (beyond builtin roster 0..5) -> error frame."""
    cmd = {"type": "cmd", "name": "place_structure", "kind": 6, "owner": 1,
           "x": 0.0, "y": 0.0}
    frames = _run(PIPE_DBG, [SET_SEED, START, cmd])
    err = frames[-1]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "kind out of range", err


def test_place_structure_kind_negative_returns_error():
    """kind=-1 -> error frame."""
    cmd = {"type": "cmd", "name": "place_structure", "kind": -1, "owner": 1,
           "x": 0.0, "y": 0.0}
    frames = _run(PIPE_DBG, [SET_SEED, START, cmd])
    err = frames[-1]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "kind out of range", err


def test_place_structure_missing_owner_returns_error():
    """missing 'owner' key -> error frame."""
    cmd = {"type": "cmd", "name": "place_structure", "kind": 0, "x": 0.0, "y": 0.0}
    frames = _run(PIPE_DBG, [SET_SEED, START, cmd])
    err = frames[-1]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "missing owner", err


def test_place_structure_no_world_returns_error():
    """no set_seed -> error frame before any structure is placed."""
    cmd = {"type": "cmd", "name": "place_structure", "kind": 0, "owner": 1,
           "x": 0.0, "y": 0.0}
    frames = _run(PIPE_DBG, [cmd])
    err = frames[0]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "no world", err


# ---- (c) non-debug pipe rejects it like an unknown verb ----

def test_place_structure_rejected_by_non_debug_pipe():
    """Non-debug pipe: verb absent (OM_DEBUG_INJECT not defined), falls through
    to 'unknown command'. Reply is {"type":"error","name":"place_structure",
    "reason":"unknown command"}.
    """
    frames = _run(PIPE, [SET_SEED, START, PLACE])
    err = frames[-1]
    assert err["type"] == "error" and err["name"] == "place_structure", err
    assert err["reason"] == "unknown command", (
        "non-debug pipe must reply 'unknown command', got %r" % err)


# ---- (d) tactical frame does not expose structures ----

def test_tactical_frame_has_no_structures_key():
    """Name kept for history (TD-VG-K-5): spec section 2 adds `structures` to full frames, so the first
    tactical frame after mission_begin (a full frame) carries `structures` as a list.
    """
    cmds = [SET_SEED, START, BEGIN, PLACE,
            {"type": "cmd", "name": "tactical_step", "n": 1}]
    frames = _run(PIPE_DBG, cmds)
    tacticals = [f for f in frames if f.get("type") == "tactical"]
    assert tacticals, "no tactical frame received"
    full = tacticals[0]
    assert "structures" in full, "full tactical frame must carry structures; got keys: %r" % list(full.keys())
    assert isinstance(full["structures"], list), type(full["structures"])
