# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-22
"""AC 22 numbers control: 16 against 8 of the same type, side 0 wins every fight."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays, scan  # noqa: E402

REPLICATES = 10


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.fixture(scope="module")
def numbers_cell(library):
    return scan.cell(plays.blob_play(16), 8, REPLICATES)


@pytest.fixture(scope="module")
def reversed_cell(library):
    return scan.cell(plays.blob_play(8), 16, REPLICATES)


def test_sixteen_beat_eight_in_every_fight(numbers_cell):
    """AC 22: both orders x 10 seeds, outcome is side0 each time."""
    assert len(numbers_cell.fights) == 2 * REPLICATES
    outcomes = [f.outcome for f in numbers_cell.fights]
    assert outcomes == ["side0"] * (2 * REPLICATES), outcomes
    assert all(f.heads == (16, 8) for f in numbers_cell.fights)


def test_numbers_positive_control_eight_against_sixteen_never_reads_side0(reversed_cell):
    """AC 22 positive control: the same detector reads side1 when the numbers are reversed."""
    outcomes = [f.outcome for f in reversed_cell.fights]
    assert "side0" not in outcomes, outcomes
    assert outcomes == ["side1"] * (2 * REPLICATES), outcomes
