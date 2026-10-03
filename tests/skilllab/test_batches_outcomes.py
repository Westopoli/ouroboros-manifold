# spec: ruling A201: the run file result line counts quiet stalemates, caps and draws separately
"""batches._STALLED and the result line over a scripted scan: 1 stalemate, 2 caps, 3 draws."""
import dataclasses
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fight, make_scan  # noqa: E402
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


def test_stalled_is_quiet_stalemate_only():
    assert batches._STALLED == ("stalemate",)


def test_result_line_carries_the_three_counts_in_order():
    line = _line(["stalemate", "cap", "cap", "draw", "draw", "draw", "side0", "side1"])
    assert "stalled fights 1 (quiet stalemates only); caps 2; draws 3" in line


def test_caps_and_draws_are_not_in_the_stalled_count():
    line = _line(["cap", "cap", "draw", "draw", "draw", "side0"])
    assert "stalled fights 0 (quiet stalemates only); caps 2; draws 3" in line


def test_positive_control_a_stalemate_is_counted_as_stalled():
    line = _line(["stalemate", "stalemate", "side0"])
    assert re.search(r"stalled fights 2 \(quiet stalemates only\); caps 0; draws 0", line)


def test_counts_sit_where_the_stalled_text_was():
    """After the firing text, before any pair spread."""
    line = _line(["draw", "side0"])
    assert line.index("mean firing unit-seconds") < line.index("stalled fights")
