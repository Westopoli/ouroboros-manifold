"""PX-4 runner: builds a real C-sim world through ctypes, enables the T1
trace (csrc/ouroboros_sim.h `om_trace_enable`/`om_trace_len`/`om_trace_read`),
steps a fixed number of ticks, reads the rows back, and runs
`detectors.py`'s `run_all()` over them. Used by `test_detectors.py`'s
positive/negative controls and standalone (`python run_trace.py --bug
<name>`) for the wall-time numbers PX-4's write-up reports.

Loads tests/csim/conftest.py directly (not through pytest fixtures, so this
also works as a standalone script) under a private module name -- same
technique tests/qa/t1/conftest.py already uses, for the same reason: this
directory's own conftest.py must not collide with tests/csim/conftest.py's
bare "conftest" name when both are on sys.path in the same pytest session.
"""
from __future__ import annotations

import argparse
import ctypes
import importlib.util
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detectors as det  # noqa: E402

_CSIM_CONFTEST = Path(__file__).resolve().parents[2] / "csim" / "conftest.py"
_spec = importlib.util.spec_from_file_location("_run_trace_csim_conftest", _CSIM_CONFTEST)
_csim = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _csim
_spec.loader.exec_module(_csim)

OMBug = _csim.OMBug
OMTier = _csim.OMTier
OmTraceRow = _csim.OmTraceRow
set_region = _csim.set_region

FIELD_GEN_SEED = 20260921
WORLD_SEED = 2026092100


def load_handle(debug: bool) -> ctypes.CDLL:
    path = _csim.DBG_LIB_PATH if debug else _csim.LIB_PATH
    handle = ctypes.CDLL(str(path))
    _csim._configure_common(handle)
    if debug:
        _csim._configure_debug(handle)
    return handle


def build_world(handle, n_regions: int, seed: int = WORLD_SEED, *,
                 field_seed: int = FIELD_GEN_SEED, empty_region: int | None = 0,
                 osc_region: int | None = 1):
    """`empty_region` (default region 0) is forced EMPTY, 0 on every field --
    R-012-07's fixture, OM_BUG_EMPTY_DRIFTS's positive control.
    `osc_region` (default region 1) is forced HOME with a live oscillator
    phase, mirroring tests/csim/controls/test_control_osc_as_level.py's own
    fixture -- OM_BUG_OSC_AS_LEVEL's positive control. The rest is a
    HOME/FRONTIER mix seeded like
    tests/csim/test_E02_gate_drift_trajectory.py's `_build_60_region_world`
    (same RNG-driven field ranges), so this fixture is the E-02 gate test's
    own shape plus the two fixed control regions those detectors need."""
    w = handle.om_world_new(ctypes.c_uint32(n_regions), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    rng = random.Random(field_seed)
    for idx in range(n_regions):
        if empty_region is not None and idx == empty_region:
            set_region(handle, w, idx, tier=OMTier.EMPTY, military=0.0, economy=0.0,
                       tension=0.0, population=0.0)
            continue
        if osc_region is not None and idx == osc_region:
            set_region(handle, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0,
                       tension=50.0, population=50.0, econ_phase=0.4, tension_phase=0.9)
            continue
        tier = OMTier.HOME if rng.random() < 0.5 else OMTier.FRONTIER
        set_region(
            handle, w, idx, tier=tier,
            military=rng.uniform(5.0, 90.0), economy=rng.uniform(10.0, 95.0),
            tension=rng.uniform(0.0, 80.0), population=rng.uniform(5.0, 95.0),
            econ_phase=rng.uniform(0.0, 2 * math.pi), tension_phase=rng.uniform(0.0, 2 * math.pi),
        )
    return w


def run_and_trace(handle, world, ticks: int) -> tuple[list, float]:
    """Returns (rows, wall_seconds) for the traced run alone (world build
    and region seeding are not included in the timed window -- the brief's
    budget is "under 2s per run" for the traced step, matching how the E-02
    gate test times its own untraced bulk run separately from setup)."""
    handle.om_trace_enable(world, 1)
    t0 = time.perf_counter()
    ran = handle.om_world_run(world, ctypes.c_uint64(ticks))
    wall = time.perf_counter() - t0
    assert ran == ticks, f"om_world_run returned {ran}, expected {ticks}"
    n = handle.om_trace_len(world)
    rows = (OmTraceRow * n)()
    got = handle.om_trace_read(world, ctypes.c_uint64(0), ctypes.c_uint64(n), rows)
    assert got == n, f"om_trace_read returned {got} rows, expected {n}"
    return list(rows), wall


def run_case(*, bug: str | None, n_regions: int, ticks: int) -> dict:
    """bug=None: release lib, no injection (the clean baseline -- avoids
    R11's debug-build default-bug entirely, since the release .so has no
    OM_DEBUG_INJECT code path at all to default). bug='empty_drifts' or
    'osc_as_level': debug lib, that bug explicitly injected via
    om_debug_inject (R11: csrc/region.c's `w->inject = 0` collides with
    OM_BUG_OSC_AS_LEVEL's id, so every debug world defaults to that bug
    active even with no injection call -- explicit injection here is
    correct either way, but this fact is why 'clean' must use the release
    lib, not an un-injected debug one)."""
    debug = bug is not None
    handle = load_handle(debug)
    world = build_world(handle, n_regions)
    if bug == "empty_drifts":
        handle.om_debug_inject(world, OMBug.EMPTY_DRIFTS)
    elif bug == "osc_as_level":
        handle.om_debug_inject(world, OMBug.OSC_AS_LEVEL)
    elif bug is not None:
        raise ValueError(f"unknown bug {bug!r}")

    empty_region_indices = (0,)  # matches build_world's default empty_region=0
    rows, wall = run_and_trace(handle, world, ticks)
    findings = det.run_all(rows, empty_region_indices)
    handle.om_world_free(world)
    return {
        "bug": bug or "clean", "n_regions": n_regions, "ticks": ticks,
        "wall_s": round(wall, 4), "n_rows": len(rows),
        "findings": {k: [(f.kind, f.region_idx, f.detail) for f in v] for k, v in findings.items()},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bug", choices=("empty_drifts", "osc_as_level"), default=None)
    ap.add_argument("--regions", type=int, default=60)
    ap.add_argument("--ticks", type=int, default=500)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    result = run_case(bug=args.bug, n_regions=args.regions, ticks=args.ticks)
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        n_findings = sum(len(v) for v in result["findings"].values())
        print(f"bug={result['bug']} regions={result['n_regions']} ticks={result['ticks']} "
              f"wall={result['wall_s']}s rows={result['n_rows']} findings={n_findings}")
        for kind, entries in result["findings"].items():
            for k, region, detail in entries:
                print(f"  {kind} region={region} {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
