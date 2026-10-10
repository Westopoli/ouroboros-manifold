"""Visible-game lane D, piece D7 (Architect, 2026-10-09, found by diagnosis). Fenced: builders never edit this file.

Proves S-246 / R-246-01 (the mission's field is the one the units were spawned on, D5-3: unit spawns are cleared to
open cells) and R-097-09 (the blocked-cell push-out never fires on a fresh mission: nothing moves without an order).
Bug: csrc/pipe/om_pipe.c handle_mission_start (era_kind 0) calls om_space_field_generate_nodes a second time with seed
ws ^ (ws >> 32), after om_mission_setup already generated the field (seed ws ^ region*0x9E3779B1 ^ archetype) and
spawned units on its cleared cells. The second generation overwrites the field and the blocked mask, so on seed 1
about 70 percent of the units start inside blocked layer cells and R-097-09 pushes every unit on tick 1.
RED on this base for that reason: test_no_unit_starts_in_a_blocked_cell fails on "units start blocked"; the
no-movement test fails because the push-out moves them. The controls pass by design.
The positive control for the push-out itself (a unit in a cell the test blocks) is in tests/csim/test_VG_D_d7.py:
no pipe verb places a unit or blocks a cell.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
N = 240
CELL = 100.0
pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")
QUIT = {"type": "cmd", "name": "quit"}
SEEDS = (1, 8)


def cmd(name, **kw):
    return {"type": "cmd", "name": name, **kw}


def run(cmds, timeout=240):
    script = b""
    for c in cmds + [QUIT]:
        body = json.dumps(c).encode()
        script += len(body).to_bytes(4, "big") + body
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def scenario(seed):
    """(units at tick 0 from the begin frame, masks, units after one tactical_step with no command)."""
    fr = run([cmd("set_seed", seed=seed, n_regions=80, features=list(range(8))),
              cmd("mission_start", faction=0, era_kind=0), cmd("mission_begin"),
              cmd("space_field_dump"), cmd("tactical_step", n=1, full=True)])
    tac = [f for f in fr if f["type"] == "tactical"]
    dump = [f for f in fr if f["type"] == "space_field"]
    assert tac and dump, [f["type"] for f in fr]
    return tac[0], [bytes.fromhex(m) for m in dump[0]["masks"]], tac[-1]


def blocked(masks, u):
    cx, cy = int(u["x"] // CELL), int(u["y"] // CELL)
    i = cy * N + cx
    return bool(masks[u.get("layer", 0)][i >> 3] >> (i & 7) & 1)


def units_in_blocked(frame, masks):
    return [u["id"] for u in frame["units"] if blocked(masks, u)]


def moved(a, b):
    pos = {u["id"]: (u["x"], u["y"]) for u in a["units"]}
    return [u["id"] for u in b["units"] if u["id"] in pos and pos[u["id"]] != (u["x"], u["y"])]


@pytest.mark.parametrize("seed", SEEDS)
def test_no_unit_starts_in_a_blocked_cell(seed):
    """D7, S-246 / R-246-01 (D5-3): at tick 0 of a space mission started through the pipe, no unit's cell is
    blocked in its own layer's dump mask. Red now: units start blocked ("units start blocked") because
    handle_mission_start regenerates the field after om_mission_setup spawned the units on the first one."""
    first, masks, _ = scenario(seed)
    assert first["units"], "no units in the begin frame"
    bad = units_in_blocked(first, masks)
    assert not bad, f"units start blocked: {len(bad)} of {len(first['units'])} (seed {seed})"


@pytest.mark.parametrize("seed", SEEDS)
def test_nothing_moves_on_the_first_step_without_a_command(seed):
    """D7, R-097-09: the push-out never fires on a fresh mission, so after one tactical_step with no command no
    unit has moved. Red now: units start in blocked cells and the push-out moves them on tick 1."""
    first, _, after = scenario(seed)
    m = moved(first, after)
    assert not m, f"{len(m)} of {len(first['units'])} units moved with no order (seed {seed})"


def test_control_detectors_reject_planted_frames():
    """Positive control for units_in_blocked and moved (pass by design)."""
    masks = [bytes(N * N // 8) for _ in range(5)]
    u = {"id": 1, "x": 150.0, "y": 250.0, "layer": 2}
    f = {"units": [u]}
    assert units_in_blocked(f, masks) == []
    i = 2 * N + 1
    bm = bytearray(masks[2])
    bm[i >> 3] |= 1 << (i & 7)
    masks[2] = bytes(bm)
    assert units_in_blocked(f, masks) == [1]
    assert units_in_blocked({"units": [dict(u, layer=1)]}, masks) == []
    assert moved(f, {"units": [dict(u, x=151.0)]}) == [1]
    assert moved(f, f) == []
