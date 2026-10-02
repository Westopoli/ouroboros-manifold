# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-21
"""AC 21 mirror control: identical sides, 16 v 16, both spawn orders, 10 replicates."""
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, scan  # noqa: E402

SIZE = 16
REPLICATES = 10
TOLERANCE = 0.05


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.fixture(scope="module")
def mirror_cell(library):
    return scan.cell(plays.blob_play(SIZE), SIZE, REPLICATES)


@pytest.fixture(scope="module")
def forced_no_swap_cell(library):
    def never_swap(setup, seed, swap):
        return fight.fight(setup, seed, False)

    return scan.cell(plays.blob_play(SIZE), SIZE, REPLICATES, fight_fn=never_swap)


def test_mirror_mean_margin_within_tolerance_of_zero(mirror_cell):
    """AC 21: both orders x 10 replicates, mean margin within 0.05 of zero."""
    assert len(mirror_cell.fights) == 2 * REPLICATES
    assert abs(mirror_cell.mean_margin) <= TOLERANCE, mirror_cell.mean_margin


def test_mirror_mean_margin_is_the_mean_of_the_fight_margins(mirror_cell):
    """AC 21: the cell's own mean_margin is recomputed from its fights, not trusted."""
    recomputed = statistics.fmean(f.margin for f in mirror_cell.fights)
    assert mirror_cell.mean_margin == pytest.approx(recomputed)
    assert abs(recomputed) <= TOLERANCE, recomputed


def test_mirror_fights_actually_happened(mirror_cell):
    """AC 21: a zero margin from fights that never met would be vacuous."""
    assert all(f.first_contact_tick >= 0 for f in mirror_cell.fights)
    assert all(f.heads == (SIZE, SIZE) for f in mirror_cell.fights)
    # a decided fight, not an all-cap or all-stalemate cell whose margin is near zero by absence
    assert all(f.outcome in ("side0", "side1") for f in mirror_cell.fights), \
        [f.outcome for f in mirror_cell.fights]


def test_mirror_positive_control_swap_forced_off_shows_first_spawner_ahead(forced_no_swap_cell):
    """AC 21 positive control: swap forced False everywhere, side 0 spawns first and leads by more than 0.05."""
    assert len(forced_no_swap_cell.fights) == 2 * REPLICATES
    assert forced_no_swap_cell.mean_margin > TOLERANCE, forced_no_swap_cell.mean_margin

