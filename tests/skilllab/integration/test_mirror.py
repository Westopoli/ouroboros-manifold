# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-21
"""AC 21 mirror control: identical sides, 16 v 16, both spawn orders, 10 replicates, mean margin within 0.10 of zero.

Positive control: 18 against 16 reads a mean margin above 0.10 (A190: after the leash fix 17 against 16 reads 0.068,
under the mark, which stays; the 17 reading is printed beside it as information). The first-spawner edge of the first draft
does not show once positions are shifted (docs/northstar/research/layer_dynamics/runs/2026-10-02_harness_check.md).
"""
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays, scan  # noqa: E402

SIZE = 16
REPLICATES = 10
TOLERANCE = 0.10   # Westley, 2026-10-02: one fight swings about 0.17 on the position shifts


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.fixture(scope="module")
def mirror_cell(library):
    return scan.cell(plays.blob_play(SIZE), SIZE, REPLICATES)


@pytest.fixture(scope="module")
def seventeen_cell(library):
    return scan.cell(plays.blob_play(SIZE + 1), SIZE, REPLICATES)


@pytest.fixture(scope="module")
def eighteen_cell(library):
    return scan.cell(plays.blob_play(SIZE + 2), SIZE, REPLICATES)


def test_mirror_mean_margin_within_tolerance_of_zero(mirror_cell):
    """AC 21: both orders x 10 replicates, mean margin within 0.10 of zero."""
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


def test_mirror_positive_control_eighteen_against_sixteen_reads_ahead(eighteen_cell):
    """AC 21 positive control (A190): the same cell with 18 against 16 reads a mean margin above 0.10."""
    assert len(eighteen_cell.fights) == 2 * REPLICATES
    assert all(f.heads == (SIZE + 2, SIZE) for f in eighteen_cell.fights)
    assert eighteen_cell.mean_margin > TOLERANCE, eighteen_cell.mean_margin


def test_seventeen_against_sixteen_reading_is_printed_for_information(seventeen_cell, eighteen_cell):
    """AC 21 (A190): information only, no mark. The 17 reading is printed beside the 18 control (run with -s)."""
    assert len(seventeen_cell.fights) == 2 * REPLICATES
    assert all(f.heads == (SIZE + 1, SIZE) for f in seventeen_cell.fights)
    print("\nmirror controls: 17 against 16 mean margin %.3f, 18 against 16 mean margin %.3f (mark %.2f on 18)"
          % (seventeen_cell.mean_margin, eighteen_cell.mean_margin, TOLERANCE))
