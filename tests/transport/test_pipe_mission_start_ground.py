"""Terrain stage 3, piece 3b (spec 2026-10-06-terrain-stage3-spec.md rev 3): mission_start on generated ground.

Proves, through the pipe only:
  - era_kind 1 generates the mission's terrain, so terrain_dump answers cells_w x cells_h bands with every band 1..5
    present (spec 3b: "mission_start with era_kind 1 then terrain_dump answers cells_w x cells_h bands with every band
    present"); on the base the handler only calls om_set_era_kind, so terrain_dump answers error "no terrain".
  - a ground mission followed by a space mission on one world leaves no terrain ("a ground then a space mission answers
    the no-terrain error"; om_terrain_clear, "What the audit changed" row 3).
  - the same seed gives the same dump across processes (determinism, the mission seed mix in mission.c).
  - movement_kinds is a FLAT list [type_id, kind, ...] ("What the pre-flight changed" row 1), kind 0 flying / 1 walking,
    parsed with get_int_array; an odd length or a kind other than 0 or 1 answers error reason "bad movement_kinds" and
    changes nothing (docs/architecture.md mission_start).
  - a walking type's unit does not spawn on steep (unwalkable) ground (spec 3b; om_unit_spawn_internal refuses it).
Type ids are the sim's OM_UT_* (raider 0, interceptor 1, vanguard 2, warden 3, bombard 4, bastion 5; csrc/unit.c:69-76).
The generate-failure error (-1 answers error "terrain generate failed") cannot be induced through the pipe: every
archetype canvas is inside TG_MAX_CANVAS_WU and a dry cell always exists; it is reported, not tested here.
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

FEATURES = [1, 2, 3, 4, 5, 6, 7]
ALL_WALKING = [0, 1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 1]
SEEDS = [1, 2, 3]


def _world(seed=1):
    pp = Pipe()
    pp.cmd("set_seed", seed=seed, n_regions=80, features=FEATURES, new_campaign=False)
    return pp


@pytest.fixture
def pp():
    p = _world()
    yield p
    p.close()


def _ground(p, **extra):
    m = p.send("mission_start", faction=0, era_kind=1, **extra)
    assert m["type"] == "mission", m
    return m


def _dump(p):
    d = p.send("terrain_dump")
    assert d["type"] == "terrain", "ground mission_start did not generate terrain: %r" % (d,)
    return d


def test_ground_start_then_dump_has_every_band(pp):
    """Spec 3b: era_kind 1 then terrain_dump answers cells_w x cells_h bands, every band present."""
    _ground(pp)
    d = _dump(pp)
    w, h = d["cells_w"], d["cells_h"]
    assert w >= 80 and h >= 80, d
    bands = bytes.fromhex(d["bands"])
    assert len(bands) == w * h
    assert set(bands) == {1, 2, 3, 4, 5}, sorted(set(bands))
    assert len(bytes.fromhex(d["walkable"])) == w * h


def test_dump_still_present_after_mission_begin(pp):
    """Spec 3c reads one dump after mission_begin: the terrain must survive Begin."""
    _ground(pp)
    assert pp.send("mission_begin")["type"] == "tactical"
    _dump(pp)


def test_space_start_has_no_terrain(pp):
    """Positive control, green today and after: a space mission (era_kind 0 or absent) has no terrain."""
    assert pp.send("mission_start", faction=0)["type"] == "mission"
    r = pp.send("terrain_dump")
    assert r["type"] == "error" and r["name"] == "terrain_dump" and r["reason"] == "no terrain", r


def test_ground_then_space_mission_leaves_no_terrain(pp):
    """Spec 3b: a ground then a space mission on one world answers the no-terrain error (om_terrain_clear)."""
    _ground(pp)
    _dump(pp)  # precondition: the ground mission really had terrain
    assert pp.send("mission_end")["type"] == "debrief"
    assert pp.read_more()["type"] == "snapshot"
    m = pp.send("mission_start", faction=0, era_kind=0)
    assert m["type"] == "mission", m
    r = pp.send("terrain_dump")
    assert r["type"] == "error" and r["reason"] == "no terrain", r


def test_same_seed_two_processes_identical_ground_dumps():
    dumps = []
    for _ in range(2):
        p = _world()
        try:
            _ground(p)
            dumps.append(_dump(p))
        finally:
            p.close()
    assert dumps[0] == dumps[1]


@pytest.mark.parametrize("bad", [[0], [0, 1, 2], [0, 2], [0, -1], [-1, 1]])
def test_bad_movement_kinds_answers_error_and_changes_nothing(pp, bad):
    """Odd length or kind outside {0,1}: error reason "bad movement_kinds"; the next valid start works."""
    r = pp.send("mission_start", faction=0, era_kind=1, movement_kinds=bad)
    assert r == {"type": "error", "name": "mission_start", "reason": "bad movement_kinds"}, r
    assert pp.send("mission_start", faction=0)["type"] == "mission"


def test_flat_movement_kinds_accepted_and_empty_default(pp):
    """Flat list of 6 pairs and an empty list both start the mission (default empty)."""
    assert pp.send("mission_start", faction=0, era_kind=1, movement_kinds=ALL_WALKING)["type"] == "mission"
    # the flat form is the contract; a list of pairs is not (get_int_array reads integers only)
    r = pp.send("mission_start", faction=0, era_kind=1, movement_kinds=[[0, 1], [1, 0]])
    assert r["type"] == "error" and r["reason"] == "bad movement_kinds", r


@pytest.mark.parametrize("seed", SEEDS)
def test_walking_units_do_not_spawn_on_steep_ground(seed):
    """Spec 3b: with every type walking, no unit of the mission sits on an unwalkable cell (terrain_probe walkable)."""
    p = _world(seed)
    try:
        _ground(p, movement_kinds=ALL_WALKING)
        d = _dump(p)
        assert 0 in bytes.fromhex(d["walkable"]), "positive control: the terrain has unwalkable (steep) cells"
        t = p.send("mission_begin")
        assert t["type"] == "tactical", t
        units = t["units"]
        assert len(units) > 0
        bad = []
        for u in units:
            pr = p.send("terrain_probe", x=u["x"], y=u["y"], layer=0)
            assert pr["type"] == "terrain_probe", pr
            if pr["walkable"] != 1:
                bad.append((u["id"], u["type"], u["x"], u["y"], pr["band"]))
        assert not bad, "walking units spawned on unwalkable ground: %r" % bad[:5]
    finally:
        p.close()
