"""C transport v1 shape tests (docs/architecture.md, "C transport v1"). Red until piece T1
lands pipe/ouroboros_pipe; the fixture half passes as soon as snapshot_fixture.py has run."""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "docs/northstar/spec_factory/transport"
FIXTURE = ROOT / "tests/transport/fixtures/snapshot_seed1_tick10.json"
PIPE = ROOT / "pipe/ouroboros_pipe"


def _validate(instance, schema):
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(instance, schema)


def _required_keys(schema):
    return set(schema["required"])


def test_fixture_matches_snapshot_schema():
    schema = json.load(open(SCHEMAS / "snapshot.schema.json"))
    snap = json.load(open(FIXTURE))
    assert _required_keys(schema) <= set(snap)
    _validate(snap, schema)
    assert snap["tick"] == 10 and len(snap["regions"]) == 80
    for r in snap["regions"]:
        assert set(r) >= {"i", "owner", "military", "economy", "tension", "population", "stability", "capacity"}
        assert "name" not in r and "x" not in r and "y" not in r


def test_removed_key_fails_schema():
    schema = json.load(open(SCHEMAS / "snapshot.schema.json"))
    snap = json.load(open(FIXTURE))
    del snap["regions"]
    with pytest.raises(Exception):
        _validate(snap, schema)


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _read_frames(data):
    out, i = [], 0
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_hello_snapshot_and_checksum_match_ctypes():
    import sys
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim  # noqa: E402

    # n_regions=80, not the doc examples' 60: 60 is below the feasible minimum
    # for the default 15-faction generator on every seed (worst case needed
    # is 15 * 4 + 15 = 75, the max per-faction template minimum times the
    # faction count plus one corridor slot per faction, csrc/worldgen.c
    # om_world_generate) -- confirmed empirically, 0/5000 seeds generate at
    # n_regions=60. 80 clears that floor for any seed. See M0's report.
    script = b"".join(_frame(c) for c in [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": [6],
         "new_campaign": False},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "quit"},
    ])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    frames = _read_frames(proc.stdout)
    kinds = [f["type"] for f in frames]
    assert kinds[0] == "hello" and frames[0]["abi"] == 8 and frames[0]["layout_ok"] is True
    snap = [f for f in frames if f["type"] == "snapshot"][-1]
    assert snap["tick"] == 10
    lib = csim.load_lib()
    w = lib.om_world_new(80, 1)
    lib.om_world_set_feature(w, 6, 1)
    lib.om_world_generate(w)
    csim._bind_e03(lib)
    assert lib.om_world_generated(w) == 1
    for _ in range(10):
        lib.om_world_step(w)
    assert snap["checksum"] == lib.om_world_get_state_checksum(w)
    assert all(f["type"] == "delta" for f in frames[1:11])
    assert any(r["owner"] != -1 for r in snap["regions"])
    assert len(snap["edges"]) >= 1


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_set_seed_generation_failure_is_an_error_frame():
    script = b"".join(_frame(c) for c in [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 30, "features": [6]},
        {"type": "cmd", "name": "quit"},
    ])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    frames = _read_frames(proc.stdout)
    kinds = [f["type"] for f in frames]
    assert kinds[0] == "hello"
    errors = [f for f in frames if f["type"] == "error" and f.get("name") == "set_seed"]
    assert len(errors) == 1, frames


# ---------------------------------------------------------------------
# session commands (docs/architecture.md, "C transport v1", "session
# commands (v1.1, 2026-09-24; T1-2 builds them test-first)"). Same
# seed/n_regions/features as the hello test above (80, not 60: below
# the feasible minimum, see that test's comment).
# ---------------------------------------------------------------------

SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": [6],
            "new_campaign": False}


def _run(cmds, timeout=60):
    script = b"".join(_frame(c) for c in cmds)
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    return _read_frames(proc.stdout)


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_mission_start_answers_mission_frame_with_documented_keys():
    """session commands: "mission_start calls om_mission_start(w, faction) and
    answers the mission frame (fields from om_mission_get_objectives and the
    force allocation; archetype, region, deadline_ticks from the mission
    accessors)"."""
    schema = json.load(open(SCHEMAS / "mission.schema.json"))
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "quit"}])
    mission = frames[1]
    assert mission["type"] == "mission", frames
    assert _required_keys(schema) <= set(mission)
    _validate(mission, schema)


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_step_and_run_to_refused_during_mission():
    """session commands: "while the mission phase holds, step and run_to are
    refused with error (R-055-02: the strategic sim is stopped)"."""
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "step", "n": 1},
                   {"type": "cmd", "name": "run_to", "tick": 5},
                   {"type": "cmd", "name": "quit"}])
    step_resp, run_to_resp = frames[2], frames[3]
    assert step_resp["type"] == "error" and step_resp["name"] == "step", frames
    assert run_to_resp["type"] == "error" and run_to_resp["name"] == "run_to", frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_tactical_step_tick_advances_by_one_per_call():
    """session commands: "tactical_step drives om_tactical_step and answers a
    tactical frame per call"."""
    schema = json.load(open(SCHEMAS / "tactical.schema.json"))
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "mission_begin"},
                   {"type": "cmd", "name": "tactical_step", "n": 1},
                   {"type": "cmd", "name": "tactical_step", "n": 1},
                   {"type": "cmd", "name": "quit"}])
    assert frames[2]["type"] == "tactical", "mission_begin answers the tactical frame: %r" % frames
    tac1, tac2 = frames[3], frames[4]
    assert tac1["type"] == "tactical" and tac2["type"] == "tactical", frames
    full = frames[2]
    assert full["full"] is True, "mission_begin writes a full frame (A7)"
    assert _required_keys(schema) <= set(full)
    _validate(full, schema)
    # A7: a tactical_step frame is a delta; it carries no map and no units (the delta schema
    # is the architecture.md "Delta frame" key list, tactical.schema.json describes full frames).
    delta_keys = {"type", "tick", "mission_over", "band", "full", "units_changed", "units_removed", "visible"}
    assert tac1["full"] is False, tac1
    assert delta_keys <= set(tac1), "delta frame lacks keys: %r" % (delta_keys - set(tac1))
    assert "map" not in tac1 and "units" not in tac1, tac1
    unit_schema = schema["properties"]["units"]
    _validate(tac1["units_changed"], unit_schema)
    assert all(isinstance(i, int) for i in tac1["units_removed"])
    assert tac2["tick"] == tac1["tick"] + 1, frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_command_move_acks_and_unknown_verb_errors():
    """session commands: "command maps verb onto om_command_move, ... and
    answers ack; an unknown unit id or verb answers error"."""
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "mission_begin"},
                   {"type": "cmd", "name": "command", "verb": "move", "units": [4, 5], "x": 100.0, "y": 200.0},
                   {"type": "cmd", "name": "command", "verb": "bogus_verb", "units": [4]},
                   {"type": "cmd", "name": "quit"}])
    assert frames[2]["type"] == "tactical", "mission_begin answers the tactical frame: %r" % frames
    move_resp, bogus_resp = frames[3], frames[4]
    assert move_resp["type"] == "ack" and move_resp["name"] == "command", frames
    assert bogus_resp["type"] == "error" and bogus_resp["name"] == "command", frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_mission_end_answers_debrief_then_snapshot():
    """session commands: "mission_end calls om_mission_end, answers the
    debrief frame (om_mission_get_debrief) and then a snapshot"."""
    schema = json.load(open(SCHEMAS / "debrief.schema.json"))
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "mission_end"},
                   {"type": "cmd", "name": "quit"}])
    assert len(frames) >= 4, frames
    debrief, snap = frames[2], frames[3]
    assert debrief["type"] == "debrief", frames
    assert _required_keys(schema) <= set(debrief)
    _validate(debrief, schema)
    assert snap["type"] == "snapshot", frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_jump_outside_mission_answers_chronicle_then_snapshot_and_advances_tick():
    """session commands: "jump calls om_time_jump_run(w, ticks, &report); ...
    success answers the chronicle frame (om_chronicle_entry_count entries,
    retained only) and then a snapshot"."""
    schema = json.load(open(SCHEMAS / "chronicle.schema.json"))
    frames = _run([SET_SEED, {"type": "cmd", "name": "jump", "ticks": 50},
                   {"type": "cmd", "name": "quit"}])
    assert len(frames) >= 3, frames
    chronicle, snap = frames[1], frames[2]
    assert chronicle["type"] == "chronicle", frames
    assert _required_keys(schema) <= set(chronicle)
    _validate(chronicle, schema)
    assert chronicle["jump"]["from_tick"] == 0 and chronicle["jump"]["to_tick"] == 50, frames
    assert snap["type"] == "snapshot" and snap["tick"] == 50, frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_jump_inside_mission_answers_error():
    """session commands: "a nonzero return (a mission is running) answers
    error"."""
    frames = _run([SET_SEED, {"type": "cmd", "name": "mission_start", "faction": 0},
                   {"type": "cmd", "name": "jump", "ticks": 10},
                   {"type": "cmd", "name": "quit"}])
    jump_resp = frames[2]
    assert jump_resp["type"] == "error" and jump_resp["name"] == "jump", frames


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_save_writes_sidecar_and_list_saves_lists_it(tmp_path):
    """session commands, "Save slots (T2g-2 rulings)": "save writes the state
    bytes to path and a sidecar path + '.json' with {"tick","chapter","phase",
    "seed","n_regions","format_version"} ... list_saves answers
    {"type":"saves","slots":[...]} from the sidecars in dir". The autosave
    timing rule (R-111-01: after mission/debrief/chronicle frames, never
    mid-mission -- R-111-04) is client-side (docs/architecture.md: "autosave
    ... is client-side"); this test proves the save/list_saves shape that
    rule depends on, not the client's trigger timing."""
    schema = json.load(open(SCHEMAS / "saves.schema.json"))
    save_path = str(tmp_path / "slot1.omsave")
    frames = _run([SET_SEED, {"type": "cmd", "name": "save", "path": save_path},
                   {"type": "cmd", "name": "list_saves", "dir": str(tmp_path)},
                   {"type": "cmd", "name": "quit"}])
    save_resp, saves_resp = frames[1], frames[2]
    assert save_resp["type"] == "ack" and save_resp["name"] == "save", frames
    assert os.path.exists(save_path), "save did not write the state file"
    sidecar_path = save_path + ".json"
    assert os.path.exists(sidecar_path), "save did not write the .json sidecar"
    sidecar = json.load(open(sidecar_path))
    assert {"tick", "chapter", "phase", "seed", "n_regions", "format_version"} <= set(sidecar)
    assert saves_resp["type"] == "saves", frames
    assert _required_keys(schema) <= set(saves_resp)
    _validate(saves_resp, schema)
    assert any(s["path"] == save_path for s in saves_resp["slots"]), saves_resp


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_pipe_load_corrupt_file_errors_and_leaves_checksum_unchanged(tmp_path):
    """Save slots (T2g-2 rulings): "load answers error with reason 'version
    mismatch' or 'corrupt' when om_load_state_read returns nonzero (R-111-03)
    and the world is left untouched". The C API's own bool return does not
    distinguish the two reasons (csrc/save.c om_load_state_read), so either
    string is accepted here -- the pipe is free to pick one consistently."""
    save_path = str(tmp_path / "slot2.omsave")
    frames = _run([SET_SEED, {"type": "cmd", "name": "step", "n": 5},
                   {"type": "cmd", "name": "save", "path": save_path},
                   {"type": "cmd", "name": "quit"}])
    assert frames[-1]["type"] == "ack" and frames[-1]["name"] == "save", frames

    raw = bytearray(open(save_path, "rb").read())
    raw[0:4] = bytes((b ^ 0xFF) for b in raw[0:4])
    corrupt_path = str(tmp_path / "slot2_corrupt.omsave")
    open(corrupt_path, "wb").write(bytes(raw))

    frames = _run([SET_SEED, {"type": "cmd", "name": "step", "n": 5},
                   {"type": "cmd", "name": "snapshot"},
                   {"type": "cmd", "name": "load", "path": corrupt_path},
                   {"type": "cmd", "name": "snapshot"},
                   {"type": "cmd", "name": "quit"}])
    snap1, load_resp, snap2 = frames[-3], frames[-2], frames[-1]
    assert snap1["type"] == "snapshot" and snap2["type"] == "snapshot", frames
    assert load_resp["type"] == "error" and load_resp["name"] == "load", frames
    assert load_resp["reason"] in ("version mismatch", "corrupt"), frames
    assert snap1["checksum"] == snap2["checksum"], "load must leave the world untouched on error"
