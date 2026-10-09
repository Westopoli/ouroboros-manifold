"""K-c6 contract (docs/architecture.md terrain verbs): terrain_dump carries layer_floors_wu (5 floats, wu, the
om_terrain_band_heights values) and flyer_types (ascending type ids whose mission_start movement_kinds kind is 0,
FLYING). Red now: handle_terrain_dump (csrc/pipe/pipe_dumps.c) writes neither key, so the key asserts fail.
The no-terrain control passes today and after."""
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

# flat [type_id, kind, ...]; kind 0 flying, 1 walking. Flyers here: 1 and 4.
KINDS = [0, 1, 1, 0, 2, 1, 3, 1, 4, 0, 5, 1]
FLYERS = [1, 4]


@pytest.fixture
def pp():
    p = Pipe()
    p.cmd("set_seed", seed=1, n_regions=80, features=[1, 2, 3, 4, 5, 6, 7], new_campaign=False)
    yield p
    p.close()


def test_layer_floors_equal_terrain_ack_band_heights(pp):
    """K-c6: layer_floors_wu has length 5 and equals terrain_ack.band_heights of the same terrain (1e-6)."""
    a = pp.send("terrain_generate", seed=11, canvas=16000)
    assert a["code"] == 0 and len(a["band_heights"]) == 5, a
    d = pp.send("terrain_dump")
    assert d["type"] == "terrain", d
    assert "layer_floors_wu" in d, "terrain_dump lacks layer_floors_wu (K-c6)"
    f = d["layer_floors_wu"]
    assert len(f) == 5
    assert all(abs(x - y) <= 1e-6 for x, y in zip(f, a["band_heights"])), (f, a["band_heights"])


def test_flyer_types_are_the_kind_zero_types_ascending(pp):
    """K-c6: flyer_types == ascending types whose mission_start movement_kinds kind is 0."""
    m = pp.send("mission_start", faction=0, era_kind=1, movement_kinds=KINDS)
    assert m["type"] == "mission", m
    d = pp.send("terrain_dump")
    assert d["type"] == "terrain", d
    assert "flyer_types" in d, "terrain_dump lacks flyer_types (K-c6)"
    assert d["flyer_types"] == FLYERS


def test_second_dump_identical_arrays(pp):
    """K-c6: both arrays are identical in every terrain_dump of a mission."""
    assert pp.send("mission_start", faction=0, era_kind=1, movement_kinds=KINDS)["type"] == "mission"
    d1, d2 = pp.send("terrain_dump"), pp.send("terrain_dump")
    assert "layer_floors_wu" in d1 and "flyer_types" in d1, "keys absent (K-c6)"
    assert d1["layer_floors_wu"] == d2["layer_floors_wu"] and d1["flyer_types"] == d2["flyer_types"]


def test_no_terrain_error_carries_neither_key(pp):
    """Positive control (green today and after): no terrain gives the "no terrain" error and neither key."""
    r = pp.send("terrain_dump")
    assert r["type"] == "error" and r["reason"] == "no terrain", r
    assert "layer_floors_wu" not in r and "flyer_types" not in r
