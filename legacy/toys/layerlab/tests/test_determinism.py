"""Rung R0 test 1 (SPEC.md section 10): determinism gate (SPEC.md section 9)."""
import numpy as np
import pytest

from layerlab import scenario
from layerlab.run import run


@pytest.fixture(scope="module")
def scn(scenarios_dir):
    return scenario.load(str(scenarios_dir / "r0_raiders_10v5.toml"))


def _trace_bytes(res):
    assert res.trace is not None, "run(..., trace=True) must return a trace array"
    return np.ascontiguousarray(res.trace).tobytes()


def test_same_seed_twice_identical(scn):
    """Mirrors E-01 R-004-05 (determinism is a contract): same scenario and seed twice
    give identical ll_result bytes and identical trace bytes."""
    a = run(scn, seed=7, trace=True, lib="O2")
    b = run(scn, seed=7, trace=True, lib="O2")
    assert a.raw == b.raw
    assert len(a.trace) > 0
    assert _trace_bytes(a) == _trace_bytes(b)


def test_o0_vs_o2_identical(scn):
    """Mirrors E-01 R-004-05 (determinism across builds): the O0 and O2 libraries give
    identical result bytes and identical trace bytes for the same seed."""
    for seed in (0, 1, 7):
        a = run(scn, seed=seed, trace=True, lib="O0")
        b = run(scn, seed=seed, trace=True, lib="O2")
        assert a.raw == b.raw, "raw differs O0 vs O2 at seed %d" % seed
        assert _trace_bytes(a) == _trace_bytes(b), "trace differs O0 vs O2 at seed %d" % seed


def test_different_seeds_differ(scn):
    """Mirrors E-01 R-004-05 (the seed is the only source of variation: jitter and cooldown
    draws, SPEC 5.13): seeds 0 and 1 must not give the same result bytes or trace."""
    a = run(scn, seed=0, trace=True, lib="O2")
    b = run(scn, seed=1, trace=True, lib="O2")
    differs = (
        a.raw != b.raw
        or a.ticks != b.ticks
        or a.hp_ratio != b.hp_ratio
        or _trace_bytes(a) != _trace_bytes(b)
    )
    assert differs, "seeds 0 and 1 gave identical output: the seed draws are dead"
