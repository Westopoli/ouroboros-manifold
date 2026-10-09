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


def test_place_accepted_on_the_command_path():
    """K-e: kind place, empty units, x, y, building -> ack (the K-e stub accepts; E1e adds terrain refusals)."""
    f = frames(BEGUN + [cmd("command", verb="place", units=[], x=1200.0, y=800.0, building=3)])[-1]
    assert f.get("type") == "ack" and f.get("name") == "command", f


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


def test_hello_abi_is_6():
    """K-e: the hello frame reports abi 6."""
    script = b""
    for c in [QUIT]:
        body = json.dumps(c).encode()
        script += len(body).to_bytes(4, "big") + body
    data = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60).stdout
    n = int.from_bytes(data[:4], "big")
    assert json.loads(data[4:4 + n])["abi"] == 6
