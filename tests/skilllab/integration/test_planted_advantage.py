# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-23
"""AC 23 planted advantage: 16 units with 1.2x reach beat a larger enemy than 16 identical units."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays, scan  # noqa: E402

SIZE, ENEMY_FROM, ENEMY_TO = 16, 8, 24


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.fixture(scope="module")
def identical_scan(library):
    return scan.scan(plays.blob_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO)


@pytest.fixture(scope="module")
def identical_scan_again(library):
    return scan.scan(plays.blob_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO)


@pytest.fixture(scope="module")
def null_reach_scan(library):
    return scan.scan(plays.reach_play(SIZE, factor=1.0), SIZE, ENEMY_FROM, ENEMY_TO)


@pytest.fixture(scope="module")
def reach_scan(library):
    return scan.scan(plays.reach_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO)


def test_reach_beats_strictly_more_enemies_than_identical(reach_scan, identical_scan):
    """AC 23: reach.beats exceeds identical.beats by at least one."""
    assert identical_scan.beats is not None, "baseline scan found no break-even"
    assert reach_scan.beats is not None, "reach scan found no break-even"
    assert reach_scan.beats - identical_scan.beats >= 1, (reach_scan.beats, identical_scan.beats)


def test_planted_positive_control_identical_baseline_is_reproducible(identical_scan, identical_scan_again):
    """AC 23: the identical-sides scan, run twice, gives the same beats (the baseline does not wander)."""
    assert identical_scan.beats == identical_scan_again.beats
    assert identical_scan.loses_to == identical_scan_again.loses_to
    assert [c.enemy_heads for c in identical_scan.cells] == list(range(ENEMY_FROM, ENEMY_TO + 1))


def test_planted_null_control_reach_factor_one_equals_identical(null_reach_scan, identical_scan):
    """AC 23 null control (AC 12): reach_play with factor 1.0 uses the same blob formation as blob_play, so
    its scan must equal the identical scan in beats and loses_to. The custom-type path adds no advantage
    by itself; the gap in the test above is therefore the reach, not a buffed hp or damage."""
    assert null_reach_scan.beats == identical_scan.beats
    assert null_reach_scan.loses_to == identical_scan.loses_to
    assert [c.enemy_heads for c in null_reach_scan.cells] == list(range(ENEMY_FROM, ENEMY_TO + 1))


def test_planted_both_beats_values_compared(reach_scan, identical_scan, null_reach_scan):
    """AC 23: all three beats values are present; the reach scan exceeds both baselines by at least one."""
    assert None not in (reach_scan.beats, identical_scan.beats, null_reach_scan.beats)
    assert reach_scan.beats - identical_scan.beats >= 1
    assert reach_scan.beats - null_reach_scan.beats >= 1
    assert reach_scan.loses_to == reach_scan.beats + 1
