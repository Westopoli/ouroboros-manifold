# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-23
"""AC 23 planted advantage: 16 units with 1.2x damage per shot beat a larger enemy than 16 identical units.

The control is damage, not reach: on today's engine more reach made a side worse (docs/northstar/research/
layer_dynamics/runs/2026-10-02_harness_check.md). `reach_play` stays as a knob to study; nothing here asserts
that a reach scan beats more.

LAB-REV2-L4 ruler (TD-LAB-REV2-L4-fullscan): bisection is the scan default now, so the four fixtures ask for the linear sweep (full_scan=True)
and the comparisons read the exact break-even of each play.
"""
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
    return scan.scan(plays.blob_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO, full_scan=True)


@pytest.fixture(scope="module")
def identical_scan_again(library):
    return scan.scan(plays.blob_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO, full_scan=True)


@pytest.fixture(scope="module")
def null_damage_scan(library):
    return scan.scan(plays.damage_play(SIZE, factor=1.0), SIZE, ENEMY_FROM, ENEMY_TO, full_scan=True)


@pytest.fixture(scope="module")
def damage_scan(library):
    return scan.scan(plays.damage_play(SIZE), SIZE, ENEMY_FROM, ENEMY_TO, full_scan=True)


def test_damage_beats_strictly_more_enemies_than_identical(damage_scan, identical_scan):
    """AC 23: damage.beats exceeds identical.beats by at least one."""
    assert identical_scan.beats is not None, "baseline scan found no break-even"
    assert damage_scan.beats is not None, "damage scan found no break-even"
    assert damage_scan.beats - identical_scan.beats >= 1, (damage_scan.beats, identical_scan.beats)


def test_planted_positive_control_identical_baseline_is_reproducible(identical_scan, identical_scan_again):
    """AC 23: the identical-sides scan, run twice, gives the same beats (the baseline does not wander)."""
    assert identical_scan.beats == identical_scan_again.beats
    assert identical_scan.loses_to == identical_scan_again.loses_to
    assert [c.enemy_heads for c in identical_scan.cells] == list(range(ENEMY_FROM, ENEMY_TO + 1))


def test_planted_null_control_damage_factor_one_equals_identical(null_damage_scan, identical_scan):
    """AC 23 null control (AC 12): damage_play with factor 1.0 uses the same blob formation as blob_play, so
    its scan must equal the identical scan in beats and loses_to. The custom-type path adds no advantage
    by itself; the gap in the test above is therefore the damage, not the path."""
    assert null_damage_scan.beats == identical_scan.beats
    assert null_damage_scan.loses_to == identical_scan.loses_to
    assert [c.enemy_heads for c in null_damage_scan.cells] == list(range(ENEMY_FROM, ENEMY_TO + 1))


def test_planted_both_beats_values_compared(damage_scan, identical_scan, null_damage_scan):
    """AC 23: all three beats values are present; the damage scan exceeds both baselines by at least one."""
    assert None not in (damage_scan.beats, identical_scan.beats, null_damage_scan.beats)
    assert damage_scan.beats - identical_scan.beats >= 1
    assert damage_scan.beats - null_damage_scan.beats >= 1
    assert damage_scan.loses_to == damage_scan.beats + 1
