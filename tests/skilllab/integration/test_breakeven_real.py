# spec: break-even by scan with refinement, and the side-swap control (skill lab harness, item 3)
"""Real engine, tiny: structure only. Red until scripts/skilllab/breakeven.py exists."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays  # noqa: E402
from scripts.skilllab.breakeven import BreakEven, SwapControl, find_break_even, swap_control  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def test_find_break_even_real_structure(library):
    """Blob 4 against 2..6: a BreakEven whose scan cells cover 2..6, with consistent flips/refined/rounds."""
    res = find_break_even(plays.blob_play(4), 4, 2, 6, replicates=2, near_replicates=3, max_rounds=1)
    assert isinstance(res, BreakEven)
    assert [c.enemy_heads for c in res.scan.cells] == [2, 3, 4, 5, 6]
    assert res.multi_flip == (len(res.flips) > 1)
    assert res.refined == sorted(set(res.refined))
    assert res.rounds in (0, 1)
    assert all(len(c.fights) in (4, 6) for c in res.scan.cells)


def test_swap_control_real_bias_is_finite(library):
    """Sanity only, not a pass mark: at 4 against 4 the side-flip bias has abs below 1.0."""
    res = swap_control(plays.blob_play(4), 4, 2)
    assert isinstance(res, SwapControl) and res.enemy_heads == 4
    assert abs(res.bias) < 1.0
