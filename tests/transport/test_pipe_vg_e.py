"""Visible-game programme lane E1, contract amendment K-e, pipe side (docs/northstar/plans/2026-10-07-visible-game-spec.md
rev 6, lane E1 section, piece E1a; contract text: docs/architecture.md "Visible-game economy fields"). Fenced: builders
never edit this file.

Pinned here (the shapes are K-e's, flagged in the contract text):
  full tactical frame   carries "strongpoints": [{id,x,y,owner,state}] (always present; [] on a fresh mission)
  delta tactical frame  carries "lots_changed": [[id,x,y,stage,building,owner],...] (always present; [] when none)
  every tactical frame  carries "economy": {"doctrine": int, "resources": {}} (doctrine 3 = balanced on a fresh world)
  lots_dump verb        {"type":"lots","lots":[[id,x,y,stage,building,owner],...]}; error "no world" with no world
  command place         {"verb":"place","units":[],"x","y","building"} -> ack; "command failed" for a missing field,
                        a negative building or non-empty units; "not begun" in recon; "no world" with no world
The refusals that depend on terrain (unwalkable, occupied) are E1e's and are not asserted here.
On main none of the new fields or verbs exist, so those tests fail on that; "(control)" tests pass on main.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
SEED = 8
pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

QUIT = {"type": "cmd", "name": "quit"}


def cmd(name, **kw):
    return {"type": "cmd", "name": name, **kw}


SET_SEED = cmd("set_seed", seed=SEED, n_regions=80, features=list(range(8)))
BEGUN = [SET_SEED, cmd("mission_start", faction=0, era_kind=0), cmd("mission_begin")]


def frames(cmds, timeout=240):
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


def tactical(cmds):
    return [f for f in frames(cmds) if f.get("type") == "tactical"]


def check_lot_row(r):
    assert isinstance(r, list) and len(r) == 6, r
    assert all(isinstance(v, int) for v in (r[0], r[3], r[4], r[5])), r
    assert all(isinstance(v, (int, float)) for v in (r[1], r[2])), r
    assert 0 <= r[3] <= 5, f"stage {r[3]} outside 0 rubble .. 5"


def check_economy(e):
    assert isinstance(e, dict) and isinstance(e.get("doctrine"), int) and 0 <= e["doctrine"] <= 3, e
    assert e.get("resources") == {}, e


def test_control_move_command_still_acks():
    """Control (passes on main): a move command with no units is still answered, not by the new place path."""
    f = frames(BEGUN + [cmd("command", verb="move", units=[], x=100.0, y=100.0)])[-1]
    assert f.get("type") in ("ack", "error"), f


def test_full_frame_carries_strongpoints_and_economy():
    """K-e: the mission_begin full frame has strongpoints [] shape-checked and economy {doctrine, resources}."""
    full = tactical(BEGUN)[-1]
    assert full.get("full") is True
    sp = full.get("strongpoints")
    assert isinstance(sp, list), "full frame has no strongpoints[]; K-e"
    for p in sp:
        assert set(p) >= {"id", "x", "y", "owner", "state"} and p["state"] in (0, 1, 2), p
    check_economy(full.get("economy"))
    assert full["economy"]["doctrine"] == 3, "a fresh world's doctrine is balanced (3)"


def test_delta_frame_carries_lots_changed_and_economy_not_strongpoints():
    """K-e: a delta has lots_changed (always present, [] when none) and economy; strongpoints are full-frame only."""
    ds = [f for f in tactical(BEGUN + [cmd("tactical_step", n=1)]) if f.get("full") is False]
    assert ds, "no delta frame"
    d = ds[-1]
    lc = d.get("lots_changed")
    assert isinstance(lc, list), "delta frame has no lots_changed; K-e"
    for r in lc:
        check_lot_row(r)
    check_economy(d.get("economy"))
    assert "strongpoints" not in d


def test_full_frame_has_no_lots_key():
    """K-e: lots reach the client by lots_dump once, not on full frames."""
    assert "lots_changed" not in tactical(BEGUN)[-1]


def test_lots_dump_shape():
    """K-e: lots_dump answers {type: lots, lots: [...]} (empty on a fresh mission) and twice is identical."""
    out = frames(BEGUN + [cmd("lots_dump"), cmd("lots_dump")])
    a, b = out[-2], out[-1]
    assert a.get("type") == "lots", a
    assert isinstance(a.get("lots"), list)
    for r in a["lots"]:
        check_lot_row(r)
    assert a == b


def test_lots_dump_no_world():
    f = frames([cmd("lots_dump")])[-1]
    assert f == {"type": "error", "name": "lots_dump", "reason": "no world"}, f


BEGUN_TERRAIN = [SET_SEED, cmd("mission_start", faction=0, era_kind=1), cmd("mission_begin")]  # era 1 generates terrain


def _place(x, y):
    return cmd("command", verb="place", units=[], x=x, y=y, building=3)


def _candidates():
    """Cell centres on the 100 wu grid, outward from the canvas centre (12000, 12000), the canvas being 24000 wide; first 64."""
    cells = sorted(((i, j) for i in range(-12, 13) for j in range(-12, 13)), key=lambda c: (c[0] ** 2 + c[1] ** 2, c))
    return [(12050.0 + 100.0 * i, 12050.0 + 100.0 * j) for i, j in cells[:64]]


def _is_ack(f):
    return f.get("type") == "ack" and f.get("name") == "command"


def test_place_accepted_on_the_command_path():
    """K-e/E1e (TD-VG-E-12): place (in an era-1 world, which has terrain) is acked at some walkable, unoccupied spot (E1e refuses unwalkable ground and
    overlap, so a fixed spot is not promised); the lots dump then lists a lot there."""
    cands = _candidates()
    out = frames(BEGUN_TERRAIN + [_place(x, y) for x, y in cands] + [cmd("lots_dump")])
    acks = [(c, f) for c, f in zip(cands, out[len(out) - 1 - len(cands):-1]) if _is_ack(f)]
    assert acks, "none of the first 64 candidate spots was accepted"
    lots = out[-1]
    assert lots.get("type") == "lots" and lots["lots"], lots
    (x, y), _ = acks[0]
    assert any(abs(r[1] - x) < 100 and abs(r[2] - y) < 100 for r in lots["lots"]), (x, y, lots)


def test_place_refused_off_canvas_returns_error_frame():
    """Control (TD-VG-E-12): a spot the sim refuses (far off the canvas, unwalkable) returns the error frame.
    Also: era 0 generates no terrain, so om_economy_place refuses every spot there (E1E_UNWALKABLE)."""
    g = frames(BEGUN + [_place(12050.0, 12050.0)])[-1]
    assert g == {"type": "error", "name": "command", "reason": "command failed"}, g
    f = frames(BEGUN_TERRAIN + [_place(-50000.0, -50000.0)])[-1]
    assert f == {"type": "error", "name": "command", "reason": "command failed"}, f


@pytest.mark.parametrize("kw", [
    dict(units=[], x=1200.0, y=800.0),                      # building missing
    dict(units=[], x=1200.0, y=800.0, building=-1),         # building negative
    dict(units=[], y=800.0, building=3),                    # x missing
    dict(units=[], x=1200.0, building=3),                   # y missing
    dict(units=[4], x=1200.0, y=800.0, building=3),         # units must be empty
])
def test_place_invalid_frames_refused(kw):
    f = frames(BEGUN + [cmd("command", verb="place", **kw)])[-1]
    assert f == {"type": "error", "name": "command", "reason": "command failed"}, f


def test_place_in_recon_is_not_begun():
    f = frames([SET_SEED, cmd("mission_start", faction=0, era_kind=0),
                cmd("command", verb="place", units=[], x=1200.0, y=800.0, building=3)])[-1]
    assert f == {"type": "error", "name": "command", "reason": "not begun"}, f


def test_place_no_world():
    f = frames([cmd("command", verb="place", units=[], x=1.0, y=1.0, building=0)])[-1]
    assert f == {"type": "error", "name": "command", "reason": "no world"}, f


def test_hello_abi_is_7():
    """K-e: the hello frame reported abi 6; K-e5 moved the pin to 7 (TD-VG-E-16)."""
    script = b""
    for c in [QUIT]:
        body = json.dumps(c).encode()
        script += len(body).to_bytes(4, "big") + body
    data = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60).stdout
    n = int.from_bytes(data[:4], "big")
    assert json.loads(data[4:4 + n])["abi"] == 7
