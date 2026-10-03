# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, each map's naive-against-naive break-even
"""Real engine, tiny: structure and repeatability only. Red until scripts/skilllab/maps.py and mapreport.py exist."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402
from scripts.skilllab.mapreport import MapReport, naive_break_even  # noqa: E402
from scripts.skilllab.maps import sample_map  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def test_naive_break_even_on_the_open_map_covers_the_range_and_repeats(library):
    """Open map 0, blob 4 against 3..5: a MapReport whose scan cells cover 3..5, equal across two runs."""
    def run():
        return naive_break_even("open", 0, sample_map("open", 0), size=4, enemy_from=3, enemy_to=5,
                                replicates=2, near_replicates=2, max_rounds=0)

    first, second = run(), run()
    assert isinstance(first, MapReport)
    assert [c.enemy_heads for c in first.naive.scan.cells] == [3, 4, 5]
    assert first == second
