"""Visible-game programme lane D, contract amendment K-d, pipe side: the `space_field_dump` verb
(docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, "Contract gates" row K-d; S-246 / R-246-03: the
simulation sends the cell masks and the plate polygons once per mission; Q-166-06 b). Fenced: builders never edit.

Frame shape PINNED here (the spec says "shape and size" and gives neither; flagged for the K-d contract doc):
  {"type":"space_field","cells_w":240,"cells_h":240,"layers":5,
   "masks":[<5 hex strings>],            one per layer 0..4; each is the 57600 cells packed 8 per byte, cell index
                                          i = cy*cells_w + cx, bit (i & 7) of byte (i >> 3) (LSB first), 1 = blocked
                                          (the blocked_bits sense); 7200 bytes = 14400 hex chars
   "polys":[[layer, kind, [x0,y0,x1,y1,...]], ...]}   layer 0..4; kind 0 plate, 1 mass, 2 rubble (field_map_space.gd
                                          KIND_*); coordinates in wu, at least 3 points, inside [0, 24000]
Errors (the terrain_dump form): {"type":"error","name":"space_field_dump","reason":...}; no world or no field answers
reason "no space field" (the reason text is a pin mirroring "no terrain").
How a field exists in a pipe session: mission_start with era_kind 0 (a space mission) generates it (lane D's wiring
piece, after K-d); era_kind 1 (ground) holds none. The size of the frame is RECORDED (stdout and the junit property
space_field_dump_bytes), not bounded: no number was given.
On main the verb is unknown, so every test here fails on that.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
SEED = 8
CANVAS = 24000.0
CELLS = 240 * 240
PACKED_HEX = (CELLS // 8) * 2
pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

QUIT = {"type": "cmd", "name": "quit"}


def set_seed(seed=SEED):
    return {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": 80, "features": list(range(8))}


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
        out.append((n, json.loads(data[i + 4:i + 4 + n])))
        i += 4 + n
    return out[1:]  # drop hello


def frames(cmds):
    return [f for _, f in run(cmds)]


def space_dump(seed=SEED):
    """(frame, size_in_bytes) of the dump after a space mission_start + mission_begin."""
    out = run([set_seed(seed), cmd("mission_start", faction=0, era_kind=0), cmd("mission_begin"), cmd("space_field_dump")])
    n, f = out[-1]
    return f, n


def check_shape(f):
    """Raises AssertionError on a malformed space_field frame. Positive control below plants bad ones."""
    assert f.get("type") == "space_field", f.get("type")
    assert (f.get("cells_w"), f.get("cells_h"), f.get("layers")) == (240, 240, 5), f
    masks = f.get("masks")
    assert isinstance(masks, list) and len(masks) == 5, "masks is not a list of 5"
    for k, m in enumerate(masks):
        assert isinstance(m, str) and len(m) == PACKED_HEX, f"layer {k}: mask hex length {len(m) if isinstance(m, str) else m}"
        bytes.fromhex(m)
    polys = f.get("polys")
    assert isinstance(polys, list) and polys, "no polygons"
    seen = set()
    for p in polys:
        assert isinstance(p, list) and len(p) == 3, f"poly is not [layer, kind, coords]: {p!r:.80}"
        layer, kind, xy = p
        assert isinstance(layer, int) and 0 <= layer <= 4, f"poly layer {layer}"
        assert isinstance(kind, int) and kind in (0, 1, 2), f"poly kind {kind}"
        assert isinstance(xy, list) and len(xy) % 2 == 0 and len(xy) >= 6, f"poly coords count {len(xy)}"
        assert all(isinstance(v, (int, float)) and 0.0 <= v <= CANVAS for v in xy), "poly coordinate outside the canvas"
        seen.add(layer)
    assert seen == {0, 1, 2, 3, 4}, f"layers with polygons: {sorted(seen)}"


def test_dump_shape_and_size_recorded(record_property):
    """R-246-03: masks (packed hex) and plate polygons, once per mission; size recorded."""
    f, n = space_dump()
    assert f["type"] != "error", f
    check_shape(f)
    record_property("space_field_dump_bytes", n)
    print(f"space_field_dump frame: {n} bytes, {len(f['polys'])} polygons")


def test_every_layer_has_both_open_and_blocked_cells():
    f, _ = space_dump()
    for k, m in enumerate(f["masks"]):
        b = bytes.fromhex(m)
        assert any(b), f"layer {k}: no blocked cell"
        assert any(x != 0xFF for x in b), f"layer {k}: no open cell"


def test_dump_twice_in_one_mission_identical():
    out = frames([set_seed(), cmd("mission_start", faction=0, era_kind=0), cmd("mission_begin"),
                  cmd("space_field_dump"), cmd("space_field_dump")])
    assert out[-1] == out[-2] and out[-1]["type"] == "space_field"


def test_same_seed_two_processes_identical_dumps():
    a, _ = space_dump(SEED)
    b, _ = space_dump(SEED)
    assert a == b and a["type"] == "space_field"


def test_different_seed_changes_the_masks():
    a, _ = space_dump(SEED)
    b, _ = space_dump(SEED + 1)
    assert a["type"] == "space_field" and b["type"] == "space_field"
    assert a["masks"] != b["masks"]


def test_dump_before_any_mission_is_error():
    r = frames([set_seed(), cmd("space_field_dump")])[-1]
    assert r["type"] == "error" and r["name"] == "space_field_dump", r
    assert r["reason"] == "no space field", r  # the verb exists and refuses for want of a field


def test_ground_mission_holds_no_space_field():
    r = frames([set_seed(), cmd("terrain_generate", seed=11, canvas=16000), cmd("mission_start", faction=0, era_kind=1),
                cmd("mission_begin"), cmd("space_field_dump")])[-1]
    assert r["type"] == "error" and r["name"] == "space_field_dump" and r["reason"] == "no space field", r


def test_tactical_step_unchanged_beside_the_field():
    """Control for the wiring: a space mission with a field still steps."""
    out = frames([set_seed(), cmd("mission_start", faction=0, era_kind=0), cmd("mission_begin"),
                  cmd("space_field_dump"), cmd("tactical_step", n=1)])
    assert out[-2]["type"] == "space_field" and out[-1]["type"] == "tactical" and out[-1]["tick"] >= 1, out[-2:]


def test_control_check_shape_rejects_planted_frames():
    """Positive control: check_shape fails on each planted defect and passes a minimal good frame."""
    mask = "00" * (CELLS // 8)
    good = {"type": "space_field", "cells_w": 240, "cells_h": 240, "layers": 5, "masks": [mask] * 5,
            "polys": [[k, 0, [0, 0, 100, 0, 100, 100]] for k in range(5)]}
    check_shape(good)
    bad = [
        {**good, "masks": [mask] * 4},
        {**good, "masks": [mask[:-2]] + [mask] * 4},
        {**good, "polys": [[0, 0, [0, 0, 100, 0, 100]]] + good["polys"]},
        {**good, "polys": [[7, 0, [0, 0, 100, 0, 100, 100]]] + good["polys"]},
        {**good, "polys": [[0, 0, [0, 0, 100, 0, 100, 99999]]] + good["polys"]},
        {**good, "polys": good["polys"][:4]},
        {**good, "type": "terrain"},
    ]
    for i, b in enumerate(bad):
        with pytest.raises(AssertionError):
            check_shape(b)
