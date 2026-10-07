"""Terrain pipe verbs: terrain_generate and terrain_dump (make the om_terrain_* field reachable from play).

Proves: terrain_generate answers terrain_ack {code, cells_w, cells_h, band_heights[5]};
terrain_dump answers a terrain frame {cells_w, cells_h, bands hex, walkable hex, slopes[]};
dump with no terrain is an error (net verbs' form); a canvas of 32000 is refused with a
nonzero code; same seed gives byte-identical dumps across processes; and the existing
mission / tactical_step verbs are unchanged beside a generated terrain.
Interactive driver: tests/long/harness.py Pipe, same as test_pipe_net_verbs.py.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
_spec = importlib.util.spec_from_file_location("long_harness", ROOT / "tests/long/harness.py")
_h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_h)
Pipe = _h.Pipe

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

SEED, CANVAS = 11, 16000
SLOPE_KEYS = {"x0", "y0", "x1", "y1", "mx", "my", "length", "lower_band", "upper_band"}


def _world(seed=1):
    pp = Pipe()
    pp.cmd("set_seed", seed=seed, n_regions=_h.N_REGIONS, features=_h.FEATURES)
    return pp


@pytest.fixture
def pp():
    p = _world()
    yield p
    p.close()


def test_generate_acks_code_zero_160_cells_five_bands(pp):
    a = pp.send("terrain_generate", seed=SEED, canvas=CANVAS)
    assert a["type"] == "terrain_ack" and a["name"] == "terrain_generate", a
    assert a["code"] == 0, a
    assert a["cells_w"] == 160 and a["cells_h"] == 160, a
    bh = a["band_heights"]
    assert len(bh) == 5 and all(bh[i] < bh[i + 1] for i in range(4)), a


def test_dump_bands_walkable_slopes(pp):
    assert pp.send("terrain_generate", seed=SEED, canvas=CANVAS)["code"] == 0
    d = pp.send("terrain_dump")
    assert d["type"] == "terrain", d
    assert d["cells_w"] == 160 and d["cells_h"] == 160, d
    bands = bytes.fromhex(d["bands"])
    assert len(bands) == 25600
    assert set(bands) == {1, 2, 3, 4, 5}, sorted(set(bands))
    walk = bytes.fromhex(d["walkable"])
    assert len(walk) == 25600 and set(walk) <= {0, 1}
    assert isinstance(d["slopes"], list)
    for s in d["slopes"]:
        assert set(s) >= SLOPE_KEYS, s


def test_dump_before_generate_is_error(pp):
    r = pp.send("terrain_dump")
    assert r["type"] == "error" and r["name"] == "terrain_dump", r
    assert r["reason"] != "unknown command", r  # the verb must exist and refuse for want of terrain


def test_generate_canvas_32000_refused(pp):
    a = pp.send("terrain_generate", seed=SEED, canvas=32000)
    assert a["type"] == "terrain_ack" and a["code"] != 0, a


def test_same_seed_two_processes_identical_dumps():
    dumps = []
    for _ in range(2):
        p = _world()
        try:
            assert p.send("terrain_generate", seed=SEED, canvas=CANVAS)["code"] == 0
            dumps.append(p.send("terrain_dump"))
        finally:
            p.close()
    assert dumps[0] == dumps[1]


def test_terrain_then_mission_tactical_step_unchanged():
    p = _world()
    try:
        assert p.send("terrain_generate", seed=SEED, canvas=CANVAS)["code"] == 0
        p.cmd("snapshot")
        pf = p.read_more().get("player_faction", 0)
        m = p.send("mission_start", faction=pf, era_kind=1)  # TD-T3-terrain-clear: a space mission clears terrain
        assert m["type"] == "mission", m
        t = p.send("mission_begin")
        assert t["type"] == "tactical", t
        mine = [u["id"] for u in t["units"] if u["faction"] == pf]
        r = p.send("command", verb="move", units=mine[:5], x=12000.0, y=9000.0)
        assert r["type"] == "ack", r
        f = p.send("tactical_step", n=1)
        assert f["type"] == "tactical" and f["tick"] >= 1, f
        # the dump still answers beside the mission
        assert p.send("terrain_dump")["type"] == "terrain"
    finally:
        p.close()
