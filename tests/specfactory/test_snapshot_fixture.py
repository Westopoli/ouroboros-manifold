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


def _generate(out_path: Path, *, seed: int, regions: int, ticks: int) -> subprocess.CompletedProcess:
    return _run(
        "--seed", str(seed), "--regions", str(regions), "--ticks", str(ticks), "--out", str(out_path),
    )


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
    """tests/transport/fixtures/snapshot_seed1_tick10.json (seed 1, 60 regions,
    10 ticks) is exactly what the generator produces right now -- not a stale
    snapshot from an earlier build."""
    assert FIXTURE.exists()
    out = tmp_path / "regenerated.json"
    proc = _generate(out, seed=1, regions=60, ticks=10)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out.read_bytes() == FIXTURE.read_bytes()
