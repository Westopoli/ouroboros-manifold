"""B3 + B5 (mission-plays plan, R-065-02): the refusal reaches the chronicle.

Split out of test_pipe_mission_refuse.py: this needs the B5 consequence entry
(gen_time_jump) as well as B3 `mission_refuse`, so it is not landed until B5 lands.
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
REFUSE = {"type": "cmd", "name": "mission_refuse"}
JUMP = {"type": "cmd", "name": "jump", "ticks": 50}
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
