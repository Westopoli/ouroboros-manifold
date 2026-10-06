"""R-001-07 / terrain stage 2 spec: `mission_start` carries an optional `era_kind` (0 space, 1 ground; default 0) and the
handler calls om_set_era_kind(w, era_kind) before om_mission_setup (Architect ruling 2026-10-06, pulled forward from the
stage 3 spec; the merge gate's reach lint rejects om_set_era_kind as unreachable from the pipe).

Observable: the ping (S-162 / R-005-09). In a ground era om_command_ping is refused with reason 5; in a space era it casts.
NOTE: csrc/pipe/om_pipe.c has no `ping` verb in handle_command today (verbs: move, attack_move, attack_target,
activate_ability, hold). The command frame assumed here is the move frame's shape with the ping's own fields:
{"type":"cmd","name":"command","verb":"ping","units":[caster],"layer":L,"x":X,"y":Y}; the ack is {"type":"ack",...} and a
ground refusal is an error frame named "command" whose reason is not "unknown verb" and names the ground refusal. The
builder adds the verb with the wiring; if the frame shape is chosen differently, the Architect fixes this file's PING helper.

Fixture: seed 1, 80 regions, features 1..7, mission_start faction 0, mission_begin; unit 23 is the player's rightmost
spawn-row unit (see test_pipe_units_move.py), ping 500 wu from the spawn point (inside reach).
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": [1, 2, 3, 4, 5, 6, 7],
            "new_campaign": False}
BEGIN = {"type": "cmd", "name": "mission_begin"}
QUIT = {"type": "cmd", "name": "quit"}
CASTER = 23
PING = {"type": "cmd", "name": "command", "verb": "ping", "units": [CASTER], "layer": 0, "x": 12830.0, "y": 515.0}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def _start(**extra):
    return dict({"type": "cmd", "name": "mission_start", "faction": 0}, **extra)


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def test_era_kind_1_makes_the_ping_refused_on_ground():
    """R-001-07 / S-162, ruling 2026-10-06: mission_start era_kind 1 puts the world in a ground era, so a ping is refused (reason 5)."""
    frames = _run([SET_SEED, _start(era_kind=1), BEGIN, PING])
    assert [f["type"] for f in frames[:2]] == ["mission", "tactical"], frames
    refusal = frames[2]
    assert refusal["type"] == "error" and refusal["name"] == "command", refusal
    assert refusal["reason"] != "unknown verb", "no ping verb in the pipe: %r" % refusal
    assert "ground" in refusal["reason"], refusal


def test_no_era_kind_field_keeps_the_space_era_and_the_ping_casts():
    """R-001-07, ruling 2026-10-06: without era_kind the default is 0 (space), as today; the same ping is accepted."""
    frames = _run([SET_SEED, _start(), BEGIN, PING])
    assert [f["type"] for f in frames[:2]] == ["mission", "tactical"], frames
    assert frames[2] == {"type": "ack", "name": "command"}, frames[2]


def test_bad_era_kind_answers_error_and_leaves_the_world_untouched():
    """R-001-07, ruling 2026-10-06: era_kind 2 answers error "bad era_kind"; a following mission_start without the field works."""
    frames = _run([SET_SEED, _start(era_kind=2), _start()])
    assert frames[0] == {"type": "error", "name": "mission_start", "reason": "bad era_kind"}, frames[0]
    assert frames[1]["type"] == "mission", frames[1]
