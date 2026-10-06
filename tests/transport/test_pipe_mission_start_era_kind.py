"""R-001-07 / terrain stage 2 spec: `mission_start` carries an optional `era_kind` (0 space, 1 ground; default 0) and the
handler calls om_set_era_kind(w, era_kind) before om_mission_setup (Architect ruling 2026-10-06, pulled forward from the
stage 3 spec; the merge gate's reach lint rejects om_set_era_kind as unreachable from the pipe).

Observable: the net checksum (docs/architecture.md net_checksum). fog.c folds era_kind into the `fog` section word, so a
ground world and a space world answer different words after the same mission_start / mission_begin / net_reset. Section
names come from the `names` array of the net_ack.

Fixture: seed 1, 80 regions, features 1..7, mission_start faction 0, mission_begin; each case runs on a fresh pipe process.
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
RESET = {"type": "cmd", "name": "net_reset"}
CHECKSUM = {"type": "cmd", "name": "net_checksum"}

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


def _checksum(**extra):
    frames = _run([SET_SEED, _start(**extra), BEGIN, RESET, CHECKSUM])
    ack = frames[-1]
    assert ack["type"] == "net_ack" and ack["name"] == "net_checksum", frames
    return ack


def test_era_kind_1_changes_the_fog_section_and_the_checksum():
    """R-001-07, ruling 2026-10-06: mission_start era_kind 1 reaches om_set_era_kind, so the fog section word and the full checksum differ from era_kind 0."""
    space, ground = _checksum(era_kind=0), _checksum(era_kind=1)
    fog = space["names"].index("fog")
    assert space["names"] == ground["names"]
    assert ground["sections"][fog] != space["sections"][fog], "era_kind ignored: fog section equal %r" % space["sections"][fog]
    assert ground["checksum"] != space["checksum"], "era_kind ignored: checksum equal"


def test_no_era_kind_field_equals_era_kind_0():
    """R-001-07, ruling 2026-10-06: the default is space. Positive control: green today (the field is ignored), must stay green after the wiring."""
    absent, zero = _checksum(), _checksum(era_kind=0)
    assert absent["checksum"] == zero["checksum"]
    assert absent["sections"] == zero["sections"]


def test_bad_era_kind_answers_error_and_leaves_the_world_untouched():
    """R-001-07, ruling 2026-10-06: era_kind 2 answers error "bad era_kind"; a following mission_start without the field works."""
    frames = _run([SET_SEED, _start(era_kind=2), _start()])
    assert frames[0] == {"type": "error", "name": "mission_start", "reason": "bad era_kind"}, frames[0]
    assert frames[1]["type"] == "mission", frames[1]
