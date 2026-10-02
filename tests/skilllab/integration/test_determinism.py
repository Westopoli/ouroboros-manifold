# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-25
"""AC 25 determinism: the same setup and seed give byte-identical rows."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, rows  # noqa: E402

SIZE, ENEMIES = 16, 12


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _rows_bytes(tmp_path, name, seed, swap=False):
    setup = plays.blob_play(SIZE)(ENEMIES, swap)
    result = fight.fight(setup, seed, swap)
    # no seed label: a seed label would make different seeds differ trivially
    row = rows.fight_row(result, play="blob", enemy_heads=ENEMIES, swap=swap)
    path = tmp_path / name
    rows.write_rows([row], path)
    return Path(path).read_bytes()


def test_same_setup_and_seed_give_identical_row_bytes(library, tmp_path):
    """AC 25: two runs, two files, equal bytes."""
    first = _rows_bytes(tmp_path, "a.csv", seed=3)
    second = _rows_bytes(tmp_path, "b.csv", seed=3)
    assert len(first) > 0
    assert first == second


def test_same_setup_and_seed_identical_with_swap(library, tmp_path):
    """AC 25: the swapped spawn order is deterministic too."""
    assert _rows_bytes(tmp_path, "a.csv", 3, True) == _rows_bytes(tmp_path, "b.csv", 3, True)


def test_determinism_positive_control_other_seeds_can_differ(library, tmp_path):
    """AC 25 positive control: the byte comparison can see a difference. Seeds are the replicates,
    so across seeds 0..4 the rows must not all be equal."""
    outputs = {_rows_bytes(tmp_path, "s%d.csv" % s, seed=s) for s in range(5)}
    assert len(outputs) > 1
