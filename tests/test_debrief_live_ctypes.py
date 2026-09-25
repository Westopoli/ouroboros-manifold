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


@pytest.fixture(scope="module")
def ctypes_region_delta():
    """om_mission_get_region_delta for the same seed/faction/sequence as pipe_debrief.

    Replicates handle_mission_start in csrc/pipe/om_pipe.c (build_candidate_pool
    -> select -> setup -> build_objectives) so mission_set is true and
    om_mission_apply_consequences runs inside om_mission_end, setting
    consequence_seen.  om_mission_get_region_delta returns 0 and leaves out
    params untouched when consequence_seen is false.
    """
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim
    lib = csim.load_lib()
    # load_lib() already calls _bind_generated which includes _bind_e06/_bind_e10;
    # bind om_mission_get_region_delta directly (not emitted by specfactory yet).
    lib.om_mission_get_region_delta.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.om_mission_get_region_delta.restype = ctypes.c_int

    w = lib.om_world_new(ctypes.c_uint32(N_REGIONS), ctypes.c_uint64(SEED))
    assert w, "om_world_new returned NULL"
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)

    # Replicate pipe handle_mission_start: start -> build pool -> select ->
    # get candidates -> setup -> build objectives (sets mission_set = 1).
    lib.om_mission_start(w, ctypes.c_int32(0))
    lib.om_mission_build_candidate_pool(w)
    idx = lib.om_mission_select(w)
    pool = (csim.OMMissionCandidate * 256)()
    n = lib.om_mission_candidates(w, ctypes.cast(pool, ctypes.c_void_p),
                                   ctypes.c_uint32(256))
    region = ctypes.c_uint32(0)
    archetype = ctypes.c_uint32(0)
    if idx < n:
        region = ctypes.c_uint32(pool[idx].region_idx)
        archetype = ctypes.c_uint32(pool[idx].archetype)
    lib.om_mission_setup(w, region, archetype, ctypes.c_int(0))
    lib.om_mission_build_objectives(w, archetype)

    lib.om_mission_end(w)

    mil = ctypes.c_double()
    eco = ctypes.c_double()
    ten = ctypes.c_double()
    pop = ctypes.c_double()
    rc = lib.om_mission_get_region_delta(w, ctypes.byref(mil), ctypes.byref(eco),
                                          ctypes.byref(ten), ctypes.byref(pop))
    lib.om_world_free(w)
    assert rc == 1, "om_mission_get_region_delta returned %d (expected 1; consequence_seen not set)" % rc
    return {"military": mil.value, "economy": eco.value, "tension": ten.value,
            "population": pop.value}


def test_region_delta_matches_pipe(pipe_debrief, ctypes_region_delta):
    """C4-8: pipe region_delta matches om_mission_get_region_delta for all four
    fields (same seed, same faction, same world sequence)."""
    pipe_rd = pipe_debrief.get("region_delta", {})
    for field in ("military", "economy", "tension", "population"):
        assert float(pipe_rd.get(field, None)) == pytest.approx(
            float(ctypes_region_delta[field]), abs=1e-6), \
            "pipe region_delta.%s=%r ctypes=%r (seed=%d faction=0)" % (
                field, pipe_rd.get(field), ctypes_region_delta[field], SEED)


def test_debrief_region_delta_military_is_zero(pipe_debrief, ctypes_region_delta):
    """Gap closed by T1-12: pipe region_delta.military now equals the ctypes read.
    Updated from 'pin zero' to 'pin pipe == ctypes' (test defect: old assertion
    pinned the pre-T1-12 always-zero state; conftest comment updated accordingly).
    See test_region_delta_matches_pipe for all four fields."""
    pipe_val = float(pipe_debrief.get("region_delta", {}).get("military", None))
    assert pipe_val == pytest.approx(float(ctypes_region_delta["military"]), abs=1e-6), \
        "pipe region_delta.military=%r ctypes=%r (seed=%d faction=0)" % (
            pipe_val, ctypes_region_delta["military"], SEED)
