"""Refusal is scoped to the refused mission (E-10 R-078-05: "the band is refusal, no
force is deployed, and the region's tension rises"), and the player is never left
without a mission (R-072-07: a still-empty pool falls back to a Defensive Stand).

Bug: after `mission_refuse`, `st->refused` stays set, so the zero-force guard in the
pipe's `mission_start` rejects every later mission with "no viable mission".

Cases (seeds 1740831577 from the failing QA session, and 7; 80 regions):
 1. mission_start, mission_refuse, mission_start answers a mission frame.
 2. the same with the post-mission `jump` between the refuse and the second start.
 3. the second mission deploys player units (begin, then a tactical frame).
 4. control: the refused mission itself deploys no force (begin after refuse errors,
    no tactical frame), so a fix cannot simply ignore refusal.
Cases 1 to 3 are red today with `reason: "no viable mission"`; case 4 is green.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SEEDS = [1740831577, 7]
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
REFUSE = {"type": "cmd", "name": "mission_refuse"}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
TACTICAL_STEP = {"type": "cmd", "name": "tactical_step", "n": 1}
JUMP = {"type": "cmd", "name": "jump", "ticks": 50}
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


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


def _set_seed(seed):
    return {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": 80, "features": FEATURES}


def _no_errors(frames):
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, errors


@pytest.mark.parametrize("seed", SEEDS)
def test_mission_start_after_refuse_answers_a_mission_frame(seed):
    frames = _run([_set_seed(seed), START, REFUSE, START])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    assert frames[3]["type"] == "mission", "second mission_start after a refusal: %r" % frames[3]


@pytest.mark.parametrize("seed", SEEDS)
def test_mission_start_after_refuse_and_jump_answers_a_mission_frame(seed):
    frames = _run([_set_seed(seed), START, REFUSE, JUMP, START])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    rest = frames[3:]
    assert rest[-1]["type"] == "mission", "mission_start after refuse and jump: %r" % rest[-1]
    assert not [f for f in rest if f["type"] == "error"], rest


@pytest.mark.parametrize("seed", SEEDS)
def test_second_mission_after_refuse_deploys_a_player_force(seed):
    frames = _run([_set_seed(seed), SNAPSHOT, START, REFUSE, START, BEGIN, TACTICAL_STEP])
    snap = frames[0]
    assert snap["type"] == "snapshot", frames
    _no_errors(frames)
    tactical = next((f for f in frames if f["type"] == "tactical"), None)
    assert tactical is not None, "no tactical frame: %r" % frames
    mine = [u for u in tactical["units"] if u["faction"] == snap["player_faction"]]
    assert mine, "second mission deployed no player units: %r" % tactical["units"]


@pytest.mark.parametrize("seed", SEEDS)
def test_control_refused_mission_itself_deploys_no_force(seed):
    """R-078-05 control: the refused mission is over and has no force to begin."""
    frames = _run([_set_seed(seed), START, REFUSE, BEGIN])
    assert [f["type"] for f in frames[:3]] == ["mission", "debrief", "snapshot"], frames
    assert frames[1]["band"] == 5, frames[1]
    assert frames[3]["type"] == "error" and frames[3]["name"] == "mission_begin", frames[3]
    assert not [f for f in frames if f["type"] == "tactical"], frames
