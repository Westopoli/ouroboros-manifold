"""C6-1: debrief frame values from the pipe match om_mission_get_debrief via ctypes.

The pipe serialises om_debrief as:
  band              -> "band"
  objective_score   -> "achieved"
  retention         -> "brought_home"
(csrc/pipe/om_pipe.c write_debrief; docs/architecture.md "debrief frame").

Known gap: "region_delta" is always zeros in the pipe frame (no accessor
returns applied deltas; see csrc/pipe/om_pipe.c file-header comment, line 35).
Owner: csrc/pipe/om_pipe.c (missing om_mission_apply_consequences return path).
Pinned by test_debrief_region_delta_military_is_zero.
"""
import ctypes
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "libouroboros.so"
PIPE = ROOT / "pipe/ouroboros_pipe"
# DEFAULT_FEATURES matches c_bridge.gd DEFAULT_FEATURES = [0,1,2,3,4,5,6,7].
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SEED = 1
N_REGIONS = 80

pytestmark = pytest.mark.skipif(
    not PIPE.exists() or not LIB.exists(),
    reason="libouroboros.so or pipe/ouroboros_pipe not built",
)


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


class OMDebrief(ctypes.Structure):
    _fields_ = [
        ("band", ctypes.c_int32),
        ("objective_score", ctypes.c_double),
        ("retention", ctypes.c_double),
        ("commander_fate", ctypes.c_int32),
        ("text", ctypes.c_char * 2048),
    ]


@pytest.fixture(scope="module")
def pipe_debrief():
    """Run the pipe for seed=1, faction=0, and return the debrief frame dict."""
    script = b"".join(_frame(c) for c in [
        {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": N_REGIONS, "features": FEATURES},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_end"},
        {"type": "cmd", "name": "quit"},
    ])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=30)
    frames = _read_frames(proc.stdout)
    debrief = [f for f in frames if f.get("type") == "debrief"]
    assert len(debrief) == 1, "expected one debrief frame from pipe: %r" % frames
    return debrief[0]


@pytest.fixture(scope="module")
def ctypes_debrief():
    """Run the same mission sequence via ctypes and return om_mission_get_debrief."""
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim
    lib = csim.load_lib()
    csim._bind_e10(lib)
    w = lib.om_world_new(ctypes.c_uint32(N_REGIONS), ctypes.c_uint64(SEED))
    assert w, "om_world_new returned NULL"
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    lib.om_mission_start(w, 0)
    lib.om_mission_end(w)
    d = OMDebrief()
    lib.om_mission_get_debrief(w, ctypes.byref(d))
    lib.om_world_free(w)
    return d


def test_debrief_band_matches_pipe(pipe_debrief, ctypes_debrief):
    """S-077 R-077-01/02: pipe band int matches ctypes band for the same world."""
    assert int(pipe_debrief["band"]) == int(ctypes_debrief.band), \
        "pipe band=%r ctypes band=%r (seed=%d faction=0)" % (
            pipe_debrief["band"], ctypes_debrief.band, SEED)


def test_debrief_achieved_matches_pipe(pipe_debrief, ctypes_debrief):
    """S-077: pipe achieved maps om_debrief.objective_score for the same world."""
    assert float(pipe_debrief["achieved"]) == pytest.approx(float(ctypes_debrief.objective_score), abs=1e-6), \
        "pipe achieved=%r ctypes objective_score=%r" % (
            pipe_debrief["achieved"], ctypes_debrief.objective_score)


def test_debrief_brought_home_matches_pipe(pipe_debrief, ctypes_debrief):
    """S-077: pipe brought_home maps om_debrief.retention for the same world."""
    assert float(pipe_debrief["brought_home"]) == pytest.approx(float(ctypes_debrief.retention), abs=1e-6), \
        "pipe brought_home=%r ctypes retention=%r" % (
            pipe_debrief["brought_home"], ctypes_debrief.retention)


def test_debrief_region_delta_military_is_zero(pipe_debrief):
    """Known gap: om_debrief has no region_delta fields; pipe always emits zeros.
    This test pins the shape so a future non-zero value triggers a review.
    Owner: csrc/pipe/om_pipe.c (write_debrief, no return path from
    om_mission_apply_consequences)."""
    assert float(pipe_debrief.get("region_delta", {}).get("military", -1.0)) == pytest.approx(0.0), \
        "pipe region_delta.military is not zero: %r" % pipe_debrief.get("region_delta")
