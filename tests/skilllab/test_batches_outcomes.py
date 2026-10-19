# spec: ruling A201 as superseded by Q-LAB-03 / LAB-REV2-L4: the run file result line counts caps, draws and defect cells
"""The result line over a scripted scan: caps, draws and defect cells (no stalled count: there is no stalemate)."""
import dataclasses
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fight, make_scan, stub_summary_write  # noqa: E402,F401
from scripts.skilllab import batches  # noqa: E402


class Cell:
    label = "blob@16"
    status = "naive"


def _scan(outcomes):
    sc = make_scan(16, 10, 10, 15)
    c = sc.cells[0]
    return dataclasses.replace(sc, cells=[dataclasses.replace(c, fights=[fight(outcome=o) for o in outcomes])])


def _line(outcomes):
    return batches._result_line(Cell(), "plain", _scan(outcomes))


def test_no_stalled_state_exists_any_more():
    """Q-LAB-03: there is no quiet stalemate; a fight ends by elimination or hits the cap."""
    assert not hasattr(batches, "_STALLED")
    line = _line(["cap", "cap", "draw", "draw", "draw", "side0", "side1"])
    assert "stalled" not in line and "stalemate" not in line


def test_result_line_carries_caps_draws_and_defect_cells_in_order():
    line = _line(["cap", "cap", "draw", "draw", "draw", "side0", "side1"])
    assert "caps 2; draws 3; defect cells 0" in line      # _scan() builds one cell whose own `defect` flag is the fake's default


def test_defect_cells_are_counted_from_the_scan_cells():
    sc = _scan(["cap", "side0"])
    sc = dataclasses.replace(sc, cells=[dataclasses.replace(sc.cells[0], defect=True)])
    assert "caps 1; draws 0; defect cells 1" in batches._result_line(Cell(), "plain", sc)


def test_positive_control_a_clean_scan_has_zero_of_each():
    line = _line(["side0", "side0", "side1"])
    assert re.search(r"caps 0; draws 0; defect cells 0", line)


def test_counts_sit_after_the_firing_text_and_before_any_pair_spread():
    line = _line(["draw", "side0"])
    assert line.index("mean firing unit-seconds") < line.index("caps ")


def test_weighted_text_is_always_present_now_that_the_count_is_always_recorded():
    """Setup.weighted is gone: weighted_unit_seconds is populated on every fight, so every result line carries its mean."""
    assert re.search(r"mean weighted firing unit.seconds 1\.50 side 0, 0\.75 side 1", _line(["side0", "side1"]))


def test_a_ceiling_hit_scan_line_says_so():
    sc = make_scan(16, 40, 48, None, ceiling=True)
    line = batches._result_line(Cell(), "plain", sc)
    assert "ceiling hit" in line and "no break-even in range" not in line and "lose to" not in line
    assert "beat all 48 enemy units" in line or "beat 48" in line
