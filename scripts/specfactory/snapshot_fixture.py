#!/usr/bin/env python3
"""Builds a C transport v1 "snapshot" JSON message (docs/architecture.md,
"C transport v1") straight off the sim library through ctypes, standing in
for pipe/ouroboros_pipe (piece T1) until it exists.

Loads libouroboros.so the same way tests/csim/conftest.py's `lib` fixture
does (building it first with `make -s libouroboros.so libouroboros_dbg.so`,
then checking `om_abi_version()`), creates a world with `om_world_new(n_regions,
seed)`, turns on the requested `om_feature` ids, steps it `n_ticks` times, and
serializes regions/factions/edges/telegraphs exactly as the spec's key set and
rounding say: the four `om_region_field` values and the two `om_region_composite`
values are rounded to two decimals; faction budget/tech and telegraph commit are
not (the spec does not ask for it). No world generation runs (om_world_generate
is not called) -- this mirrors the pipe's own "set_seed" + "step" script in
tests/transport/test_pipe_shapes.py, so a fresh, ungenerated world's regions
have no owner, tier EMPTY, and zeroed fields; `om_region_neighbors` is declared
in ouroboros_sim.h (E-03) but not yet exported by every build, and an
ungenerated world has no adjacency to report regardless, so a build lacking
the symbol reports an empty edge list rather than raising.

Deterministic: same seed/regions/ticks/features, byte-identical JSON, every run.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CSIM_DIR = REPO_ROOT / "tests" / "csim"
if str(CSIM_DIR) not in sys.path:
    sys.path.insert(0, str(CSIM_DIR))
import conftest as csim  # noqa: E402

DEFAULT_FEATURES = "1,2,3,6"  # FACTIONS, FRICTION, ADMIN_REVOLTS, DRIFT (0 EVENTS is a stub, left off)
MAX_TELEGRAPHS = 4096


def load_lib() -> ctypes.CDLL:
    """conftest.py's `lib` fixture, without pytest: build the release library,
    load it, wire up the E-02..E-05 bindings this fixture needs, and check the
    ABI version the fenced suite was written against."""
    csim._build_libs()
    if not csim.LIB_PATH.exists():
        raise RuntimeError(f"libouroboros.so failed to build: {csim.BUILD_ERROR}")
    handle = ctypes.CDLL(str(csim.LIB_PATH))
    csim._configure_common(handle)
    csim._bind_e05(handle)
    version = handle.om_abi_version()
    if version != csim.EXPECTED_ABI_VERSION:
        raise RuntimeError(
            f"om_abi_version()={version}, expected {csim.EXPECTED_ABI_VERSION}"
        )
    return handle


def parse_features(raw: str) -> list[int]:
    return [int(tok) for tok in raw.split(",") if tok.strip()]


def _region_neighbors(lib: ctypes.CDLL, w, idx: int, max_n: int) -> list[int]:
    if not hasattr(lib, "om_region_neighbors"):
        return []
    lib.om_region_neighbors.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
    ]
    lib.om_region_neighbors.restype = ctypes.c_uint32
    buf = (ctypes.c_uint32 * max_n)()
    n = min(lib.om_region_neighbors(w, idx, buf, max_n), max_n)
    return [buf[i] for i in range(n)]


def build_snapshot(seed: int, n_regions: int, n_ticks: int, features: list[int]) -> dict:
    lib = load_lib()
    w = lib.om_world_new(n_regions, seed)
    if not w:
        raise RuntimeError("om_world_new returned NULL")
    try:
        for f in features:
            lib.om_world_set_feature(w, f, 1)

        tick = 0
        for _ in range(n_ticks):
            tick = lib.om_world_step(w)

        region_count = lib.om_region_count(w)
        regions = []
        for i in range(region_count):
            regions.append({
                "i": i,
                "owner": lib.om_region_owner(w, i),
                "tier": lib.om_region_tier(w, i),
                "military": round(lib.om_region_field(w, i, csim.OMField.MILITARY), 2),
                "economy": round(lib.om_region_field(w, i, csim.OMField.ECONOMY), 2),
                "tension": round(lib.om_region_field(w, i, csim.OMField.TENSION), 2),
                "population": round(lib.om_region_field(w, i, csim.OMField.POPULATION), 2),
                "stability": round(lib.om_region_composite(w, i, csim.OMComposite.STABILITY), 2),
                "capacity": round(lib.om_region_composite(w, i, csim.OMComposite.CAPACITY), 2),
            })

        faction_count = lib.om_faction_count(w)
        factions = []
        for fid in range(faction_count):
            factions.append({
                "id": fid,
                "archetype": lib.om_faction_archetype(w, fid),
                "budget": lib.om_faction_budget(w, fid),
                "tech": lib.om_faction_tech(w, fid),
                "stance": [lib.om_faction_stance(w, fid, k) for k in range(faction_count)],
            })

        edges = []
        for i in range(region_count):
            for j in _region_neighbors(lib, w, i, region_count):
                if j <= i:
                    continue
                edge_type = ctypes.c_int()
                if lib.om_region_edge(w, i, j, ctypes.byref(edge_type)):
                    edges.append({"a": i, "b": j, "t": edge_type.value})
        edges.sort(key=lambda e: (e["a"], e["b"]))

        tel_buf = (csim.OmTelegraph * MAX_TELEGRAPHS)()
        n_tel = min(lib.om_pending_telegraphs(w, tel_buf, MAX_TELEGRAPHS), MAX_TELEGRAPHS)
        telegraphs = []
        for k in range(n_tel):
            t = tel_buf[k]
            telegraphs.append({
                "attacker": t.attacker,
                "target": t.target_idx,
                "commit": t.commit,
                "declared_tick": t.declared_tick,
            })

        return {
            "type": "snapshot",
            "tick": tick,
            "checksum": lib.om_world_get_state_checksum(w),
            "regions": regions,
            "factions": factions,
            "edges": edges,
            "telegraphs": telegraphs,
        }
    finally:
        lib.om_world_free(w)


def write_snapshot(out_path: Path, seed: int, n_regions: int, n_ticks: int, features: list[int]) -> dict:
    snapshot = build_snapshot(seed, n_regions, n_ticks, features)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")
    return snapshot


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--regions", type=int, required=True)
    ap.add_argument("--ticks", type=int, required=True)
    ap.add_argument("--features", default=DEFAULT_FEATURES,
                    help=f"comma-separated om_feature ids (default {DEFAULT_FEATURES})")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    write_snapshot(Path(args.out), args.seed, args.regions, args.ticks, parse_features(args.features))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
