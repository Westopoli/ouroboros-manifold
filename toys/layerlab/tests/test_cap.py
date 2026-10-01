"""Rung CAP tests (SPEC.md section 16: unit cap 4096, ABI version 4; numerics and determinism 5.12 and 9).

Fixture choice for the big fights: the default 80 x 40 arena of 50 unit cells cannot hold 1000 a side at
the 50 unit rank spacing, so the fight scenario widens the arena to the loader's grid limit with a larger
cell: 128 x 64 cells of 100 (12800 x 6400 world units; the grid limit is SPEC 6 / ffi.MAX_GRID_W, _H, not
a cap under test). Each side is ONE `box` group at spacing 50 (rank and file 50 apart; the default spawn
jitter of 10 stays on), `cols` 40 for 1000 units (25 ranks, 2000 wide, 1250 deep) and 64 for 2048 units
(32 ranks, 3200 wide, 1600 deep). Side A stands at x 4800 facing +x, side B at x 8000 facing -x, both at
y 3200, layer 3, raiders, attack-moving at each other over a flat map with the base rules. The run is
limited to 2000 ticks so the trace buffer (ticks x units x 20 bytes) stays near 80 MB; a fight that hits
the tick cap still counts as run to completion (the result is a WIN_CAP outcome, not an error).

Legacy equivalence (test 4): digests stored in tests/data/cap_digests.json were made by
tests/make_cap_digests.py against the ABI 3 library before the cap change.
"""
import ctypes as C
import json
import threading
import time
from pathlib import Path

import numpy as np
import pytest

import make_cap_digests as mk
from layerlab import ffi, scenario
from layerlab.run import run

DATA = Path(__file__).resolve().parent / "data" / "cap_digests.json"
_OUTCOMES = (ffi.WIN_A, ffi.WIN_B, ffi.WIN_STALEMATE, ffi.WIN_CAP, ffi.WIN_MUTUAL)


def _fight(per_side_a, per_side_b, cols, max_ticks=2000):
    """Flat-map raider fight, one box per side (see the module docstring)."""
    scn = scenario.load(str(Path(__file__).resolve().parent.parent / "scenarios" / "base.toml"))
    scn["terrain"].update({"preset": "flat", "w_cells": 128, "h_cells": 64, "cell": 100.0})
    scn["run"]["max_ticks"] = max_ticks
    box = {"type": "raider", "formation": "box", "cols": cols, "spacing": 50.0, "y": 3200.0,
           "layer": 3, "order": "attack_move"}
    scn["groups"] = [
        {**box, "side": "A", "count": per_side_a, "x": 4800.0, "facing": 0.0, "goal": [8000.0, 3200.0]},
        {**box, "side": "B", "count": per_side_b, "x": 8000.0, "facing": 180.0, "goal": [4800.0, 3200.0]},
    ]
    return scn


def _big():
    return _fight(1000, 1000, cols=40)


def _timed_run(lib):
    t0 = time.perf_counter()
    res = run(_big(), seed=0, trace=True, lib=lib)
    wall = time.perf_counter() - t0
    print("CAP 1000v1000 lib=%s ticks=%d wall=%.1fs" % (lib, res.ticks, wall))
    return res


@pytest.fixture(scope="module")
def fight_o2():
    return _timed_run("O2")


@pytest.fixture(scope="module")
def fight_o0():
    return _timed_run("O0")


def _trace_bytes(res):
    assert res.trace is not None
    return np.ascontiguousarray(res.trace).tobytes()


# ---------------------------------------------------------------- 1. the constants

def test_cap_constants_and_library_abi():
    """SPEC 16: ffi.MAX_UNITS is 4096, ffi.ABI_VERSION is 4, and both built libraries report ABI 4."""
    assert ffi.MAX_UNITS == 4096
    assert ffi.ABI_VERSION == 4
    for lib in ("O0", "O2"):
        dll = C.CDLL(str(ffi.lib_path(lib).resolve()))
        dll.ll_abi_version.restype = C.c_uint32
        assert dll.ll_abi_version() == 4, "%s: ll_abi_version is %d" % (lib, dll.ll_abi_version())


# ---------------------------------------------------------------- 2. the 1000 v 1000 fight

def test_big_fight_completes_and_o0_equals_o2(fight_o0, fight_o2):
    """SPEC 16 and 9 (determinism contract): 1000 v 1000 raiders on a flat map (fixture in the module
    docstring) run to completion with no error, with every unit reported, and O0 and O2 give identical
    ll_result bytes and an identical trace digest. Wall time is printed (run with -s), no pass mark."""
    for res in (fight_o0, fight_o2):
        assert res.winner in _OUTCOMES
        assert res.ticks > 0
        assert len(res.unit) == 2000
        assert res.trace.shape == (res.ticks, 2000)
        assert res.survivors[0] + res.survivors[1] <= 2000
        assert res.shots[0] + res.shots[1] > 0, "nobody fired: the fixture does not fight"
    assert fight_o0.raw == fight_o2.raw, "ll_result bytes differ O0 vs O2"
    assert fight_o0.unit == fight_o2.unit
    assert _trace_bytes(fight_o0) == _trace_bytes(fight_o2), "trace differs O0 vs O2"


# ---------------------------------------------------------------- 3. the loader

def test_loader_accepts_4096_units():
    """SPEC 16: a scenario of 4096 units in total (2048 a side) loads, every spawn filled."""
    sc = scenario.to_c(_fight(2048, 2048, cols=64))
    assert sc.n_spawns == 4096
    assert sc.spawns[0].side == 0
    assert sc.spawns[2047].side == 0
    assert sc.spawns[2048].side == 1
    assert sc.spawns[4095].side == 1


def test_loader_refuses_4097_units():
    """SPEC 16: 4097 units raise ValueError naming the cap, 'LL_MAX_UNITS 4096' (positive control: 4096 loads)."""
    with pytest.raises(ValueError) as exc:
        scenario.to_c(_fight(2048, 2049, cols=64))
    assert "LL_MAX_UNITS 4096" in str(exc.value)


# ---------------------------------------------------------------- 4. legacy equivalence

def _stored():
    with open(DATA) as fh:
        return json.load(fh)


def test_digest_file_is_the_pinned_set():
    """SPEC 16 (legacy equivalence): the stored ABI 3 digest file holds exactly six scenarios at seeds 0 and 1,
    and the fixture scenarios stay at 128 units or fewer (positive control for the pin below)."""
    scns = mk.build_scenarios()
    assert len(scns) == 6
    assert sorted(_stored()) == sorted(mk.key(n, s) for n in scns for s in mk.SEEDS)
    for name, scn in scns.items():
        assert 0 < scenario.to_c(scn).n_spawns <= 128, name


@pytest.mark.parametrize("lib", ["O0", "O2"])
@pytest.mark.parametrize("seed", mk.SEEDS)
@pytest.mark.parametrize("name", list(mk.build_scenarios()))
def test_legacy_results_byte_identical_to_abi3(name, seed, lib):
    """SPEC 16: for a scenario of at most 128 units the traced result (scalar fields, unit rows, trace
    bytes) is byte-identical to the ABI 3 build: its sha256 equals the one stored before the change."""
    got = mk.digest(mk.build_scenarios()[name], seed, lib)
    assert got == _stored()[mk.key(name, seed)], "%s seed %d lib %s drifted from ABI 3" % (name, seed, lib)


# ---------------------------------------------------------------- 5. stack safety

def test_big_fight_in_default_stack_thread(fight_o2):
    """SPEC 16: the engine state is heap allocated, so the 1000 v 1000 fight completes inside a Python
    thread with the default stack size (no threading.stack_size call) and matches the main-thread run."""
    out = {}

    def work():
        try:
            out["res"] = run(_big(), seed=0, trace=False, lib="O2")
        except BaseException as e:  # noqa: BLE001 - reported through the assert below
            out["err"] = e

    t = threading.Thread(target=work)
    t.start()
    t.join()
    assert "err" not in out, repr(out.get("err"))
    assert out["res"].winner in _OUTCOMES
    assert out["res"].raw == fight_o2.raw
