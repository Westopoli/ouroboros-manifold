# spec: Architect ruling A187 item 2 (pair spread in result lines) - scripts/skilllab/batches.py _result_line
"""The run file result line ends with the pair spread of the cell at the break-even edge. No engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from scripts.skilllab.contract import CellResult, FightResult, ScanResult  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked, stub_summary_write  # noqa: E402,F401


def _f(margin):
    return FightResult(outcome="side0", margin=margin, strength_left=(0.5, 0.2), survivors=(8, 2), heads=(16, 16),
                       ticks=100, first_contact_tick=1, firing=[(0, 1, 1)], firing_unit_seconds=(0.5, 0.25))


def _cell(heads, margins, won):
    return CellResult(enemy_heads=heads, fights=[_f(m) for m in margins], mean_margin=sum(margins) / len(margins),
                      won=won)


def _scan(beats):
    """Cells 14, 15, 16; beats names the last won cell. Each cell has a different spread."""
    spec = {14: [0.1, 0.1, 0.1, 0.1], 15: [0.1, -0.3, 0.3, 0.5], 16: [-0.4, 0.2, -0.2, 0.6]}
    cells = [_cell(h, m, beats is not None and h <= beats) for h, m in spec.items()]
    return ScanResult(size=16, cells=cells, beats=beats, loses_to=None if beats is None else beats + 1)


def _cd():
    return batches.CellDef("x", 16, 14, 16, 2, None, "naive")


def test_line_with_a_crossing_ends_with_the_beats_cell_spread():
    line = batches._result_line(_cd(), "default", _scan(15))
    assert line.endswith(" | pair spread 0.10 to 0.20")


def test_spread_reads_the_beats_cell_not_another():
    assert batches._result_line(_cd(), "default", _scan(14)).endswith(" | pair spread 0.10 to 0.10")


def test_negative_values_use_two_decimals():
    sc = _scan(15)
    sc.cells[1] = _cell(15, [-0.4, 0.2, -0.2, 0.6], True)
    assert batches._result_line(_cd(), "default", sc).endswith(" | pair spread -0.30 to 0.40")


def test_no_crossing_has_no_spread_text():
    assert "pair spread" not in batches._result_line(_cd(), "default", _scan(None))


def test_run_file_result_lines_carry_the_spread(tmp_path):
    paths = batches.run(faked(batches.get("enemy_position")), tmp_path, scan_fn=FakeScan())
    text = Path(paths["run"]).read_text(encoding="utf-8")
    lines = [l for l in text.splitlines() if l.startswith("- blob") and "beat" in l]
    assert lines and all(l.endswith(" | pair spread 0.10 to 0.10") for l in lines)
