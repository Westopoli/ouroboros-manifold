"""B3 (mission-plays plan, R-096-05): the pipe `command` verb `activate_ability`
(docs/architecture.md "session commands", B3-verbs-docs) maps onto
om_command_activate_ability: `units` selection, optional `x`/`y` target (0.0 when
absent), `ack` when at least one unit activated, else
`{"type":"error","name":"command","reason":"command failed"}`; `not begun` in
recon, `no world` with no world; no frame beyond the ack. The effect is read from
later tactical frames (unit ids and positions).

Observable effect: a Raider's Surge (60 ticks, speed x2.5, R-086-01) makes the same
move order cover more ground than an identical run with no activation. A Vanguard's
Brace toggles (R-096-05), so a second activation is accepted where an unready
Surge is rejected. An Interceptor has no manual ability (R-086-02, passive only)
and is the "unit with no ability" control.

Positive control: on a pipe without the verb every case is red (`unknown verb`).
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
QUIT = {"type": "cmd", "name": "quit"}

RAIDER, INTERCEPTOR, VANGUARD = 0, 1, 2

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


def _ability(units, **extra):
    cmd = {"type": "cmd", "name": "command", "verb": "activate_ability", "units": list(units)}
    cmd.update(extra)
    return cmd


def _step(n=1):
    return {"type": "cmd", "name": "tactical_step", "n": n, "full": True}


def _first_unit(begin_frames, unit_type):
    tactical = next(f for f in begin_frames if f["type"] == "tactical")
    return next(u for u in tactical["units"] if u["faction"] == 0 and u["type"] == unit_type)


def _force_ids():
    """Ids of the player's first Raider, Interceptor and Vanguard (seed 1)."""
    frames = _run([SET_SEED, START, BEGIN])
    assert [f["type"] for f in frames] == ["mission", "tactical"], frames
    return tuple(_first_unit(frames, t)["id"] for t in (RAIDER, INTERCEPTOR, VANGUARD))


def _assert_ack(frame):
    assert frame["type"] == "ack" and frame["name"] == "command", frame


def _assert_failed(frame):
    assert frame["type"] == "error" and frame["name"] == "command", frame
    assert frame["reason"] == "command failed", frame


def test_activate_ability_on_a_ready_unit_answers_ack():
    raider, _, _ = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([raider])])
    assert [f["type"] for f in frames] == ["mission", "tactical", "ack"], frames
    _assert_ack(frames[2])


def test_activate_ability_target_point_is_optional_and_accepted():
    raider, _, vanguard = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([raider], x=100.0, y=200.0), _ability([vanguard])])
    _assert_ack(frames[2])
    _assert_ack(frames[3])


def test_activate_ability_writes_no_frame_beyond_the_ack():
    raider, _, _ = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([raider]), _step(1)])
    assert [f["type"] for f in frames] == ["mission", "tactical", "ack", "tactical"], frames


def test_unit_with_no_manual_ability_answers_command_failed():
    """Control: the Interceptor's ability is passive (R-086-02), so manual activation is
    rejected and an all-rejected command is an error (R-086-07)."""
    _, interceptor, _ = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([interceptor])])
    _assert_failed(frames[2])


def test_unknown_unit_id_answers_command_failed():
    frames = _run([SET_SEED, START, BEGIN, _ability([999999])])
    _assert_failed(frames[2])


def test_empty_selection_answers_command_failed():
    frames = _run([SET_SEED, START, BEGIN, _ability([])])
    _assert_failed(frames[2])


def test_mixed_selection_acks_when_at_least_one_unit_activates():
    raider, interceptor, _ = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([interceptor, 999999, raider])])
    _assert_ack(frames[2])


def test_unready_ability_is_rejected_on_the_second_activation():
    """Surge is active for 60 ticks, then on cooldown (R-086-01): not ready, so the repeat
    activation is skipped and the all-rejected command is an error."""
    raider, _, _ = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([raider]), _step(), _ability([raider])])
    _assert_ack(frames[2])
    assert frames[3]["type"] == "tactical", frames
    _assert_failed(frames[4])


def test_brace_toggles_instead_of_rejecting_the_repeat():
    """R-096-05: Brace toggles. Activating a braced Vanguard again cancels the brace and is
    accepted, where every other ability's repeat is rejected."""
    _, _, vanguard = _force_ids()
    frames = _run([SET_SEED, START, BEGIN, _ability([vanguard]), _step(), _ability([vanguard])])
    _assert_ack(frames[2])
    assert frames[3]["type"] == "tactical", frames
    _assert_ack(frames[4])


def _raider_displacement(activate):
    raider, _, _ = _force_ids()
    start = _first_unit(_run([SET_SEED, START, BEGIN]), RAIDER)
    target_y = start["y"] + 6000.0
    cmds = [SET_SEED, START, BEGIN]
    if activate:
        cmds.append(_ability([raider]))
    cmds += [{"type": "cmd", "name": "command", "verb": "move", "units": [raider],
              "x": start["x"], "y": target_y}, _step(20)]
    frames = _run(cmds)
    last = frames[-1]
    assert last["type"] == "tactical", frames[-3:]
    unit = next(u for u in last["units"] if u["id"] == raider)
    return ((unit["x"] - start["x"]) ** 2 + (unit["y"] - start["y"]) ** 2) ** 0.5


def test_activated_surge_is_visible_in_later_tactical_frames():
    """R-086-01 through the pipe: the Surge speed multiplier (x2.5) shows as a longer
    distance covered in the same number of steps for the identical move order."""
    plain = _raider_displacement(False)
    surged = _raider_displacement(True)
    assert plain > 0.0, "control run did not move: %r" % plain
    assert surged > plain * 1.5, "surge run covered %r vs %r unsurged" % (surged, plain)


def test_activate_ability_in_recon_answers_not_begun():
    frames = _run([SET_SEED, START, _ability([1])])
    assert frames[1]["type"] == "error" and frames[1]["name"] == "command", frames
    assert frames[1]["reason"] == "not begun", frames


def test_activate_ability_without_a_world_answers_no_world():
    frames = _run([_ability([1])])
    assert frames[0]["type"] == "error" and frames[0]["name"] == "command", frames
    assert frames[0]["reason"] == "no world", frames
