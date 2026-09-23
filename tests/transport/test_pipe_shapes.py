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
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": [6]},
        {"type": "cmd", "name": "step", "n": 10},
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "quit"},
    ])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    frames = _read_frames(proc.stdout)
    kinds = [f["type"] for f in frames]
    assert kinds[0] == "hello" and frames[0]["abi"] == 2 and frames[0]["layout_ok"] is True
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
