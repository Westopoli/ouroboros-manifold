"""T1-5: the tactical frame reads the real world (docs/architecture.md "tactical frame").

Before this piece the pipe sent placeholders: `map.canvas` from a hard-coded category 0
(8000 while the mission's canvas is 24000), `map.cover` always empty, `units` and
`visible` always empty. Each value is compared with a ctypes read of the same world built
through the same C calls (seed 1, 80 regions, strategic features 1..7, 10 steps,
mission_start faction 0, mission_begin, one tactical_step), so the test proves the frame
carries what the sim holds, not fixed numbers.

Positive control: the world must actually hold units and nodes (a ctypes read that
finds none would let an empty frame pass; cover is the one list that is empty in the current sim), and the canvas must differ from the category-0
value the pipe used to send.
"""
import ctypes
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
CHAPTER_PHASE_MISSION = 2  # csrc/generational.c GEN_PHASE_MISSION, not exported by the header

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


@pytest.fixture(scope="module")
def pipe_frames():
    frames = _run([SET_SEED, {"type": "cmd", "name": "step", "n": 10},
                   {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "mission_begin"},
                   {"type": "cmd", "name": "tactical_step", "n": 1}])
    mission = next(f for f in frames if f["type"] == "mission")
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert len(tactical) == 2, [f["type"] for f in frames]
    return mission, tactical[-1]


@pytest.fixture(scope="module")
def world(pipe_frames):
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim  # noqa: E402

    lib = csim.load_lib()
    csim._bind_e03(lib)
    w = lib.om_world_new(80, 1)
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    for _ in range(10):
        lib.om_world_step(w)
    lib.om_mission_start(w, 0)
    lib.om_mission_build_candidate_pool(w)
    idx = lib.om_mission_select(w)
    pool = (csim.OMMissionCandidate * 256)()
    n = lib.om_mission_candidates(w, pool, 256)
    region, archetype = (pool[idx].region_idx, pool[idx].archetype) if idx < n else (0, 0)
    mission, _ = pipe_frames
    assert (region, archetype) == (mission["region"], mission["archetype"]), (
        "the ctypes world diverged from the pipe's world before the tactical read: %r vs %r"
        % ((region, archetype), (mission["region"], mission["archetype"])))
    lib.om_mission_setup(w, region, archetype, 0)
    lib.om_mission_build_objectives(w, archetype)
    lib.om_chapter_set_phase(w, CHAPTER_PHASE_MISSION)
    lib.om_mission_begin(w)
    lib.om_tactical_step(w)
    return lib, w, archetype


def _units(lib, w):
    count = lib.om_unit_count(w)
    ids, i = [], 0
    while len(ids) < count and i < 1_000_000:
        uid = lib.om_unit_id_at(w, i)
        if uid:
            ids.append(uid)
        i += 1
    assert len(ids) == count
    return ids


def test_canvas_comes_from_the_missions_category(pipe_frames, world):
    _, tactical = pipe_frames
    lib, w, archetype = world
    want = lib.om_map_get_canvas_base_dimension(lib.om_map_archetype_canvas_category(archetype))
    assert want != lib.om_map_get_canvas_base_dimension(0), "control: this mission's canvas equals the category-0 value the pipe used to send"
    assert tactical["map"]["canvas"] == want


def test_nodes_match_the_world(pipe_frames, world):
    _, tactical = pipe_frames
    lib, w, _ = world
    n = lib.om_map_get_node_count(w)
    assert n >= 1, "control: the world has no map nodes"
    nodes = tactical["map"]["nodes"]
    assert len(nodes) == n
    for i, node in enumerate(nodes):
        assert node["kind"] == lib.om_map_get_node_type(w, i)


def test_cover_matches_the_world(pipe_frames, world):
    _, tactical = pipe_frames
    lib, w, _ = world
    # Sim-side gap when this was written: no mission on seeds 1..11 generates any cover
    # (om_map_cover_count is 0), so this can only prove the frame agrees with the count and
    # the accessor rows, not that a non-empty list is emitted correctly.
    n = lib.om_map_cover_count(w)
    cover = tactical["map"]["cover"]
    assert len(cover) == n
    x, y, r, h = (ctypes.c_double() for _ in range(4))
    for i, c in enumerate(cover):
        assert lib.om_map_cover_at(w, i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(r), ctypes.byref(h))
        assert (c["x"], c["y"], c["r"], c["h"]) == pytest.approx((x.value, y.value, r.value, h.value))


def test_units_match_the_world(pipe_frames, world):
    _, tactical = pipe_frames
    lib, w, _ = world
    ids = _units(lib, w)
    assert len(ids) >= 2, "control: the world has no units"
    units = tactical["units"]
    assert [u["id"] for u in units] == ids
    assert len({u["faction"] for u in units}) >= 2, "control: only one faction has units"
    x, y = ctypes.c_double(), ctypes.c_double()
    for u in units:
        uid = u["id"]
        assert u["faction"] == lib.om_unit_get_faction(w, uid)
        assert u["type"] == lib.om_unit_get_unit_type(w, uid)
        assert u["layer"] == lib.om_unit_get_layer(w, uid)
        assert u["hp"] == pytest.approx(lib.om_unit_get_hp(w, uid))
        assert u["facing"] == pytest.approx(lib.om_unit_get_facing(w, uid))
        assert u["target"] == lib.om_unit_target(w, uid)
        lib.om_unit_get_pos(w, uid, ctypes.byref(x), ctypes.byref(y))
        assert (u["x"], u["y"]) == pytest.approx((x.value, y.value))


def test_visible_matches_the_world(pipe_frames, world):
    _, tactical = pipe_frames
    lib, w, _ = world
    ids = _units(lib, w)
    factions = sorted({lib.om_unit_get_faction(w, uid) for uid in ids})
    visible = tactical["visible"]
    assert set(visible) == {str(f) for f in factions}
    for f in factions:
        want = [uid for uid in ids if lib.om_player_can_see_unit(w, f, uid)]
        assert visible[str(f)] == want
