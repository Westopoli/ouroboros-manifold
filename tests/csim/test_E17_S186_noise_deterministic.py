"""E-17 S-186 / R-186-04: the terrain noise is a pure function of its inputs.

R-186-04: the terrain field comes from the seed alone (no world rng, no libm
transcendentals). These tests pin the fixed-point noise prototypes declared in
csrc/om_internal.h (om_tn_value2, om_tn_fbm2, om_tn_sin_q16, om_tn_cos_q16):
same inputs give the same outputs in two separate processes, value2 stays in
[-65536, 65536], different seeds differ, fbm2 with one octave is value2, the
sine table hits 0, 1, 0, -1 at the quarter turns, and the noise is continuous.

The symbols are internal (not in ouroboros_sim.h), so they are declared with
ctypes here. Terrain stage 1 spec 2026-10-05, "noise" lane.
"""
import ctypes
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = REPO_ROOT / "libouroboros.so"

Q16_ONE = 65536                    # 1.0 in Q16.16
Q16_QUARTER_TURN = Q16_ONE // 4    # turn fraction 1/4 in Q16
SEED_A = 0x5EED0001
SEED_B = 0x5EED0002
SAMPLE_COUNT = 100
SAMPLE_STRIDE_Q16 = 40503          # arbitrary odd stride, in Q16 units (about 0.62 lattice cells)
DIFF_SEED_MIN_FRACTION = 0.5       # "most" sample points must differ between seeds
CONTINUITY_STEP_Q16 = 256          # 1/256 of a lattice cell
# Value noise with smooth interpolation changes at most ~3.75 units per lattice
# unit (quintic, lattice values in [-1, 1]); 1/256 step -> ~960 Q16 plus rounding.
# provisional (2026-10-05)
CONTINUITY_BOUND_Q16 = 1024
FBM_OCTAVES = 4
FBM_GAIN_Q16 = Q16_ONE // 2

_SIGS = {
    "om_tn_value2": ([ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32], ctypes.c_int32),
    "om_tn_fbm2": ([ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int, ctypes.c_int32],
                   ctypes.c_int32),
    "om_tn_sin_q16": ([ctypes.c_uint32], ctypes.c_int32),
    "om_tn_cos_q16": ([ctypes.c_uint32], ctypes.c_int32),
}


def _declare(handle):
    for name, (args, res) in _SIGS.items():
        fn = getattr(handle, name)
        fn.argtypes = args
        fn.restype = res
    return handle


@pytest.fixture(scope="module")
def tn(lib):
    return _declare(lib)


def _points():
    return [((i * SAMPLE_STRIDE_Q16) - 20 * Q16_ONE, (i * 3 * SAMPLE_STRIDE_Q16 // 2) - 9 * Q16_ONE)
            for i in range(SAMPLE_COUNT)]


_CHILD = """
import ctypes, json, sys
lib = ctypes.CDLL(sys.argv[1])
for n, a, r in (("om_tn_value2", [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32], ctypes.c_int32),
                ("om_tn_fbm2", [ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int, ctypes.c_int32], ctypes.c_int32),
                ("om_tn_sin_q16", [ctypes.c_uint32], ctypes.c_int32)):
    f = getattr(lib, n); f.argtypes = a; f.restype = r
pts = json.loads(sys.argv[2]); seed = int(sys.argv[3]); oct_, gain = int(sys.argv[4]), int(sys.argv[5])
out = {"v": [lib.om_tn_value2(seed, x, y) for x, y in pts],
       "f": [lib.om_tn_fbm2(seed, x, y, oct_, gain) for x, y in pts],
       "s": [lib.om_tn_sin_q16(t) for t in range(0, 65536, 997)]}
print(json.dumps(out))
"""


def _run_child():
    res = subprocess.run(
        [sys.executable, "-c", _CHILD, str(LIB_PATH), json.dumps(_points()), str(SEED_A),
         str(FBM_OCTAVES), str(FBM_GAIN_Q16)],
        capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_same_inputs_same_outputs_across_two_processes(lib):
    first, second = _run_child(), _run_child()
    assert first == second
    # positive control: a stub returning 0 everywhere is not "deterministic noise"
    assert any(v != 0 for v in first["v"]), "value2 is constant zero (stub)"


def test_value2_bounded(tn):
    for seed in (SEED_A, SEED_B):
        for x, y in _points():
            v = tn.om_tn_value2(seed, x, y)
            assert -Q16_ONE <= v <= Q16_ONE, (seed, x, y, v)


def test_fbm2_bounded(tn):
    for x, y in _points():
        v = tn.om_tn_fbm2(SEED_A, x, y, FBM_OCTAVES, FBM_GAIN_Q16)
        assert -Q16_ONE <= v <= Q16_ONE, (x, y, v)


def test_different_seed_changes_most_points(tn):
    pts = _points()
    differ = sum(tn.om_tn_value2(SEED_A, x, y) != tn.om_tn_value2(SEED_B, x, y) for x, y in pts)
    assert differ >= DIFF_SEED_MIN_FRACTION * len(pts), f"only {differ} of {len(pts)} differ"


def test_fbm2_one_octave_equals_value2(tn):
    for x, y in _points():
        assert tn.om_tn_fbm2(SEED_A, x, y, 1, FBM_GAIN_Q16) == tn.om_tn_value2(SEED_A, x, y)


def test_sine_hits_quarter_points(tn):
    got = [tn.om_tn_sin_q16(k * Q16_QUARTER_TURN) for k in range(4)]
    assert got == [0, Q16_ONE, 0, -Q16_ONE], got


def test_cos_is_sin_shifted_by_a_quarter(tn):
    for t in range(0, Q16_ONE, 1013):
        assert tn.om_tn_cos_q16(t) == tn.om_tn_sin_q16((t + Q16_QUARTER_TURN) % Q16_ONE), t
    assert tn.om_tn_cos_q16(0) == Q16_ONE


def test_noise_is_continuous(tn):
    biggest = 0
    for x, y in _points():
        a = tn.om_tn_value2(SEED_A, x, y)
        for dx, dy in ((CONTINUITY_STEP_Q16, 0), (0, CONTINUITY_STEP_Q16)):
            biggest = max(biggest, abs(tn.om_tn_value2(SEED_A, x + dx, y + dy) - a))
    assert biggest < CONTINUITY_BOUND_Q16, biggest
    # positive control: the bound is not vacuous only if the noise actually varies
    assert any(tn.om_tn_value2(SEED_A, x, y) != 0 for x, y in _points())
