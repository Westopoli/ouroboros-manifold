"""C1 S6 / architect ruling A30 (2026-10-01 rulings round 2, addendum 13): the tactical frame
fields `tier` and `state` are reserved and always 0. This pins both so that filling either goes
through a contract piece (docs/architecture.md "tactical frame") rather than slipping in.

Checked on a live mission after a clash (units have orders), on every unit in `units` (full
frames, including `"full":true` ones) and in `units_changed` (delta frames, A7).
Fixture: seed 8, eight launch features; the opposing groups meet around tick 2300.
"""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
SEED = 8

SET_SEED = {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": 80, "features": list(range(8))}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=180)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _step(n=1, full=None):
    cmd = {"type": "cmd", "name": "tactical_step", "n": n}
    if full is not None:
        cmd["full"] = full
    return cmd


def _unit_violations(frame):
    """Every (list name, unit id, field, value) where `tier` or `state` is not 0."""
    bad = []
    for key in ("units", "units_changed"):
        for u in frame.get(key, []):
            for field in ("tier", "state"):
                if u.get(field) != 0:
                    bad.append((key, u.get("id"), field, u.get(field)))
    return bad


def _clash_script(first):
    mine = [u for u in first["units"] if u["faction"] == 0]
    enemy = [u for u in first["units"] if u["faction"] != 0]
    _, target = min(((a, b) for a in mine for b in enemy),
                    key=lambda p: math.hypot(p[0]["x"] - p[1]["x"], p[0]["y"] - p[1]["y"]))
    cmds = [{"type": "cmd", "name": "command", "verb": "attack_target",
             "units": [u["id"] for u in mine], "target": target["id"]}]
    cmds += [_step(100, full=True)] * 11   # full frames while the units march
    cmds += [_step(100)] * 11              # delta frames to tick 2200
    cmds += [_step(1)] * 150               # delta frames through the clash
    cmds += [_step(1, full=True)]
    return cmds


def test_tier_and_state_are_zero_on_every_unit_in_a_live_clash():
    first_frames = _run([SET_SEED, START, BEGIN])
    first = next(f for f in first_frames if f["type"] == "tactical")
    frames = _run([SET_SEED, START, BEGIN] + _clash_script(first))
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, errors
    tac = [f for f in frames if f["type"] == "tactical"]
    assert any(f.get("full") for f in tac[1:]) and any(not f.get("full") for f in tac), "need both full and delta frames"
    assert tac[-1]["tick"] >= 2300, "the clash was not reached: last tick %d" % tac[-1]["tick"]
    n_units = 0
    for f in tac:
        bad = _unit_violations(f)
        assert not bad, "tick %d: tier/state not reserved 0 (A30): %r" % (f["tick"], bad[:5])
        n_units += len(f.get("units", [])) + len(f.get("units_changed", []))
    assert n_units > 0


def test_positive_control_the_detector_rejects_nonzero_tier_or_state():
    ok = {"id": 1, "tier": 0, "state": 0}
    assert _unit_violations({"units": [ok], "units_changed": [ok]}) == []
    assert _unit_violations({"units": [dict(ok, tier=1)]}) == [("units", 1, "tier", 1)]
    assert _unit_violations({"units_changed": [dict(ok, state=1)]}) == [("units_changed", 1, "state", 1)]
    assert _unit_violations({"units_changed": [{"id": 2, "state": 0}]}) == [("units_changed", 2, "tier", None)]
