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
not (the spec does not ask for it). Edges are read back with `om_region_neighbors`
when a build exports it (E-03/worldgen.c), else with the O(N^2) `om_region_edge`
sweep the header itself names as the fallback.

By default (no `--populate`) no world generation and no fixture setter runs
either -- this mirrors the pipe's own "set_seed" + "step" script in
tests/transport/test_pipe_shapes.py, so a fresh, ungenerated world's regions
have no owner, tier EMPTY, and zeroed fields, and (with `om_region_neighbors`
unexported and no adjacency ever set) an empty edge list.

`--populate` builds a deterministic populated stand-in instead (see
`populate_world`'s docstring): 4 factions each owning a contiguous block of
regions, a ring plus periodic chords, and seed-derived, distinct per-region
fields -- so the fixture exercises owners/edges/tiers, not an all-zero galaxy.

`--generate` builds the world the way `pipe/ouroboros_pipe`'s `set_seed` now
must (docs/architecture.md "C transport v1"): `om_world_new(n_regions, seed)`,
the requested features, then `om_world_generate(w)`. It raises if
`om_world_generated(w)` comes back 0 (a pinned `n_regions` below the
generator's feasibility floor, csrc/worldgen.c) rather than silently writing
an empty-looking fixture -- the whole point of `--generate` is a fixture with
real generated owners/edges/tiers, not a fixture that only looks like one.
`--populate` and `--generate` are mutually exclusive.

Deterministic: same seed/regions/ticks/features/populate-or-generate flag,
byte-identical JSON, every run.
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

POPULATE_N_REGIONS = 60
POPULATE_FACTION_COUNT = 4
POPULATE_BLOCK_SIZE = 12   # contiguous regions owned per faction (4*12=48, 12 left unowned)
POPULATE_CHORD_STEP = 5    # a chord every 5 regions, connecting it to the next waypoint 5 on


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
    csim._bind_e03(handle)
    version = handle.om_abi_version()
    if version != csim.EXPECTED_ABI_VERSION:
        raise RuntimeError(
            f"om_abi_version()={version}, expected {csim.EXPECTED_ABI_VERSION}"
        )
    return handle


def parse_features(raw: str) -> list[int]:
    return [int(tok) for tok in raw.split(",") if tok.strip()]


def _edges(lib: ctypes.CDLL, w, region_count: int) -> list[tuple[int, int, int]]:
    """[(a, b, t)] with a<b: `om_region_neighbors` (O(degree)) paired with
    `om_region_edge` for the type when a build exports the former, else the
    O(N^2) `om_region_edge` sweep ouroboros_sim.h names as the alternative
    (faction.c, which implements om_region_neighbors, is not landed in
    every build; om_region_edge itself is E-05 and always present)."""
    pairs: list[tuple[int, int, int]] = []
    if hasattr(lib, "om_region_neighbors"):
        lib.om_region_neighbors.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
        ]
        lib.om_region_neighbors.restype = ctypes.c_uint32
        for i in range(region_count):
            buf = (ctypes.c_uint32 * region_count)()
            n = min(lib.om_region_neighbors(w, i, buf, region_count), region_count)
            for k in range(n):
                j = buf[k]
                if j <= i:
                    continue
                edge_type = ctypes.c_int()
                if lib.om_region_edge(w, i, j, ctypes.byref(edge_type)):
                    pairs.append((i, j, edge_type.value))
    else:
        for i in range(region_count):
            for j in range(i + 1, region_count):
                edge_type = ctypes.c_int()
                if lib.om_region_edge(w, i, j, ctypes.byref(edge_type)):
                    pairs.append((i, j, edge_type.value))
    pairs.sort()
    return pairs


class _Lcg:
    """Small 64-bit LCG (MMIX/Knuth constants), seeded from --seed, used only
    to spread `--populate`'s region fields so every region differs. Has
    nothing to do with the sim's own RNG (`w->rng_state` / `om_rng_force`)."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next_unit(self) -> float:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return (self.state >> 11) * (1.0 / (1 << 53))


def populate_world(lib: ctypes.CDLL, w, seed: int, n_regions: int) -> None:
    """Deterministic populated stand-in for the galaxy view (an all-zero,
    all-unowned world exercises none of the transport's owner/edge/tier
    shape): 4 factions, archetypes 0..3, each a contiguous
    POPULATE_BLOCK_SIZE-region block (the block's first region tier HOME,
    the rest FRONTIER); the remaining POPULATE_N_REGIONS - 4*POPULATE_BLOCK_SIZE
    regions are unowned, tier EMPTY. A ring edge 0-1-2-..-(n-1)-0 (type 2,
    BOTH) plus, every POPULATE_CHORD_STEP regions, a chord to the next
    waypoint POPULATE_CHORD_STEP steps around the ring (type 1, TRADE) --
    at n=60/step=5 that is 60 ring edges + 12 chords = 72, all distinct.
    Every region's four fields is drawn from a small seeded LCG so they
    differ; built entirely with the E-05 hard-fixture setters (om_region_set,
    om_faction_set, om_region_set_edge) -- no om_world_generate call."""
    if n_regions != POPULATE_N_REGIONS:
        raise ValueError(
            f"--populate is sized for exactly {POPULATE_N_REGIONS} regions "
            f"({POPULATE_FACTION_COUNT} factions x {POPULATE_BLOCK_SIZE}-region blocks "
            f"+ a {POPULATE_N_REGIONS - POPULATE_FACTION_COUNT * POPULATE_BLOCK_SIZE}-region "
            f"unowned tail), got --regions {n_regions}"
        )

    lcg = _Lcg(seed)
    owned = POPULATE_FACTION_COUNT * POPULATE_BLOCK_SIZE
    for i in range(n_regions):
        military = 10.0 + lcg.next_unit() * 50.0
        economy = 10.0 + lcg.next_unit() * 50.0
        tension = lcg.next_unit() * 40.0
        population = 10.0 + lcg.next_unit() * 70.0
        if i < owned:
            faction_id = i // POPULATE_BLOCK_SIZE
            tier = csim.OMTier.HOME if i % POPULATE_BLOCK_SIZE == 0 else csim.OMTier.FRONTIER
        else:
            faction_id = -1
            tier = csim.OMTier.EMPTY
        rc = lib.om_region_set(w, i, tier, military, economy, tension, population, 0.0, 0.0, faction_id)
        assert rc == 0, f"om_region_set failed for region {i}: rc={rc}"

    for fid in range(POPULATE_FACTION_COUNT):
        rc = lib.om_faction_set(w, fid, fid, 100.0 + fid * 10.0, 1.0 + fid * 0.1, 5.0)
        assert rc == 0, f"om_faction_set failed for faction {fid}: rc={rc}"

    for i in range(n_regions):
        lib.om_region_set_edge(w, i, (i + 1) % n_regions, csim.OMEdge.BOTH)
    for i in range(0, n_regions, POPULATE_CHORD_STEP):
        lib.om_region_set_edge(w, i, (i + POPULATE_CHORD_STEP) % n_regions, csim.OMEdge.TRADE)


def build_snapshot(seed: int, n_regions: int, n_ticks: int, features: list[int],
                    populate: bool = False, generate: bool = False) -> dict:
    if populate and generate:
        raise ValueError("--populate and --generate are mutually exclusive")
    lib = load_lib()
    w = lib.om_world_new(n_regions, seed)
    if not w:
        raise RuntimeError("om_world_new returned NULL")
    try:
        if populate:
            populate_world(lib, w, seed, n_regions)

        for f in features:
            lib.om_world_set_feature(w, f, 1)

        if generate:
            lib.om_world_generate(w)
            if not lib.om_world_generated(w):
                raise RuntimeError(
                    f"om_world_generate failed for seed={seed} n_regions={n_regions} "
                    "(n_regions is below the generator's feasibility floor for the "
                    "default faction count -- csrc/worldgen.c om_world_generate)"
                )

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

        edges = [{"a": a, "b": b, "t": t} for a, b, t in _edges(lib, w, region_count)]

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


def write_snapshot(out_path: Path, seed: int, n_regions: int, n_ticks: int, features: list[int],
                    populate: bool = False, generate: bool = False) -> dict:
    snapshot = build_snapshot(seed, n_regions, n_ticks, features, populate=populate, generate=generate)
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
    ap.add_argument("--populate", action="store_true",
                    help="deterministic populated world (4 factions, ring+chords) instead of an all-zero one")
    ap.add_argument("--generate", action="store_true",
                    help="build the world through om_world_generate, the way the pipe's set_seed now must")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.populate and args.generate:
        ap.error("--populate and --generate are mutually exclusive")

    write_snapshot(Path(args.out), args.seed, args.regions, args.ticks, parse_features(args.features),
                   populate=args.populate, generate=args.generate)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
