# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-28
"""AC 28 speed gate: a scan of 16 units against 12 to 24 enemies, 10 replicates, both orders, under 30 s.

Wall-clock is the point of this apex test; it runs alone. The library build is excluded.
"""
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays, scan  # noqa: E402

LIMIT_SECONDS = 30.0


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def test_scan_16_against_12_to_24_finishes_under_30_seconds(library):
    """AC 28: perf_counter around scan only; the result must hold all the work, so a stub cannot pass."""
    build = plays.blob_play(16)
    start = time.perf_counter()
    result = scan.scan(build, 16, 12, 24, replicates=10)
    elapsed = time.perf_counter() - start
    assert [c.enemy_heads for c in result.cells] == list(range(12, 25))
    assert all(len(c.fights) == 20 for c in result.cells)
    # the fights really ran: a stub returning canned FightResult objects has no ticks, no firing series
    for c in result.cells:
        for f in c.fights:
            assert f.ticks > 0, (c.enemy_heads, f.ticks)
            assert f.heads == (16, c.enemy_heads), (c.enemy_heads, f.heads)
            assert len(f.firing) > 0, c.enemy_heads
    assert elapsed < LIMIT_SECONDS, "scan took %.1f s" % elapsed
