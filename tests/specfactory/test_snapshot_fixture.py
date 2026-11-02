# spec: docs/architecture.md "C transport v1"
"""Tests for scripts/specfactory/snapshot_fixture.py: the generator that
stands in for pipe/ouroboros_pipe (piece T1) until it exists, producing the
"snapshot" JSON docs/architecture.md's C transport v1 section specifies."""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TOOL = REPO / "scripts" / "specfactory" / "snapshot_fixture.py"
FIXTURE = REPO / "tests" / "transport" / "fixtures" / "snapshot_seed1_tick10.json"

REQUIRED_TOP_KEYS = {"type", "tick", "checksum", "regions", "factions", "edges", "telegraphs"}
REQUIRED_REGION_KEYS = {
    "i", "owner", "tier", "military", "economy", "tension", "population", "stability", "capacity",
}
REQUIRED_EDGE_KEYS = {"a", "b", "t"}


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True,
    )


def _generate(out_path: Path, *, seed: int, regions: int, ticks: int,
              populate: bool = False, generate: bool = False,
              features: str | None = None) -> subprocess.CompletedProcess:
    args = ["--seed", str(seed), "--regions", str(regions), "--ticks", str(ticks), "--out", str(out_path)]
    if populate:
        args.append("--populate")
    if generate:
        args.append("--generate")
    if features is not None:
        args += ["--features", features]
    return _run(*args)


def test_generator_runs_twice_byte_identical(tmp_path):
    out1 = tmp_path / "a.json"
    out2 = tmp_path / "b.json"
    p1 = _generate(out1, seed=2, regions=8, ticks=3)
    p2 = _generate(out2, seed=2, regions=8, ticks=3)
    assert p1.returncode == 0, p1.stdout + p1.stderr
    assert p2.returncode == 0, p2.stdout + p2.stderr
    assert out1.read_bytes() == out2.read_bytes()


def test_generator_schema_keys(tmp_path):
    out = tmp_path / "snap.json"
    proc = _generate(out, seed=2, regions=8, ticks=3)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    snap = json.loads(out.read_text())

    assert REQUIRED_TOP_KEYS <= set(snap)
    assert snap["type"] == "snapshot"
    assert snap["tick"] == 3
    assert len(snap["regions"]) == 8
    for r in snap["regions"]:
        assert REQUIRED_REGION_KEYS <= set(r)
        assert "name" not in r and "x" not in r and "y" not in r
    for e in snap["edges"]:
        assert REQUIRED_EDGE_KEYS <= set(e)
    for fac in snap["factions"]:
        assert {"id", "archetype", "budget", "tech", "stance"} <= set(fac)


def test_generator_seed_and_ticks_change_the_tick_field(tmp_path):
    out = tmp_path / "snap.json"
    proc = _generate(out, seed=5, regions=4, ticks=7)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    snap = json.loads(out.read_text())
    assert snap["tick"] == 7
    assert len(snap["regions"]) == 4


def test_checked_in_fixture_matches_current_generator_output(tmp_path):
    """tests/transport/fixtures/snapshot_seed1_tick10.json (seed 1, 80 regions,
    10 ticks, --generate) is exactly what the generator produces right now --
    not a stale snapshot from an earlier build. 80, not the doc examples' 60:
    60 is below om_world_generate's feasibility floor for the default
    15-faction generator on every seed (worst case needed is 15 * 4 + 15 = 75,
    csrc/worldgen.c); 80 clears it for any seed."""
    assert FIXTURE.exists()
    out = tmp_path / "regenerated.json"
    proc = _generate(out, seed=1, regions=80, ticks=10, generate=True,
                     features="6")  # fixture is the --features 6 output (c50ac4c9)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out.read_bytes() == FIXTURE.read_bytes()


# --------------------------------------------------------------------- --populate


def test_populate_runs_twice_byte_identical(tmp_path):
    out1 = tmp_path / "a.json"
    out2 = tmp_path / "b.json"
    p1 = _generate(out1, seed=1, regions=60, ticks=10, populate=True)
    p2 = _generate(out2, seed=1, regions=60, ticks=10, populate=True)
    assert p1.returncode == 0, p1.stdout + p1.stderr
    assert p2.returncode == 0, p2.stdout + p2.stderr
    assert out1.read_bytes() == out2.read_bytes()


def test_populate_gives_four_factions_seventytwo_edges_and_owned_regions(tmp_path):
    """--populate's ring (60 edges) + a chord every 5 regions (12 edges) =
    72; 4 factions each own a 12-region contiguous block (48 >= 40)."""
    out = tmp_path / "snap.json"
    proc = _generate(out, seed=1, regions=60, ticks=10, populate=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    snap = json.loads(out.read_text())

    assert len(snap["factions"]) == 4
    for fac in snap["factions"]:
        assert {"id", "archetype", "budget", "tech", "stance"} <= set(fac)
        assert len(fac["stance"]) == 4

    assert len(snap["edges"]) == 72
    for e in snap["edges"]:
        assert REQUIRED_EDGE_KEYS <= set(e)
        assert e["a"] < e["b"]

    owned = [r for r in snap["regions"] if r["owner"] != -1]
    assert len(owned) >= 40

    assert any(v != 0.0 for r in owned for v in
               (r["military"], r["economy"], r["tension"], r["population"]))


def test_populate_requires_sixty_regions(tmp_path):
    """The block/ring/chord layout is sized for exactly 60 regions; a
    mismatched --regions is a clear error, not a silently wrong layout."""
    out = tmp_path / "snap.json"
    proc = _generate(out, seed=1, regions=8, ticks=3, populate=True)
    assert proc.returncode != 0
    assert "60" in (proc.stdout + proc.stderr)
