# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Contract::Cell and scan (supersedes ruling A201: draw and cap are defects now)
"""scan.cell_result with draws and caps among the fights (LAB-REV2-L4). Ruling 1 / Q-LAB-03: a draw is the one tie the engine
can produce (both sides die on one tick); a cap is a bug detector. Neither is a result: the cell is `defect`, not won, and the scan
goes on. A200-era 'decided', 'undecided', 'stalemate' and the win margin no longer exist."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fight  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab.scan import cell, cell_result, scan  # noqa: E402


def F(outcome, margin):
    return dataclasses.replace(fight(outcome=outcome), margin=margin)


def test_cell_of_only_draws_is_a_defect_mean_zero_and_not_won():
    res = cell_result(8, [F("draw", 0.0)] * 4)
    assert res.mean_margin == 0.0 and res.won is False and res.defect is True


def test_one_draw_among_wins_makes_the_cell_a_defect_and_not_won():
    """Margins 0.9, 0.9, 0.9, draw 0.0: the mean is 0.675, but a cell is won only when every fight is side0."""
    res = cell_result(8, [F("side0", 0.9)] * 3 + [F("draw", 0.0)])
    assert res.mean_margin == pytest.approx(0.675) and res.won is False and res.defect is True


def test_a_draw_adds_its_zero_margin_to_the_mean():
    res = cell_result(8, [F("side0", 0.4), F("side0", 0.4), F("draw", 0.0), F("draw", 0.0)])
    assert res.mean_margin == pytest.approx(0.2)


@pytest.mark.parametrize("bad", ["draw", "cap"])
def test_positive_control_the_same_cell_with_a_clean_win_in_that_place_is_won(bad):
    assert cell_result(8, [F("side0", 0.9)] * 3 + [F("side0", 0.9)]) == dataclasses.replace(
        cell_result(8, [F("side0", 0.9)] * 4))
    clean = cell_result(8, [F("side0", 0.9)] * 4)
    dirty = cell_result(8, [F("side0", 0.9)] * 3 + [F(bad, 0.9)])
    assert (clean.won, clean.defect) == (True, False) and (dirty.won, dirty.defect) == (False, True)


def test_side1_wins_are_lost_but_not_defects():
    res = cell_result(8, [F("side0", 0.9)] * 3 + [F("side1", -0.9)])
    assert (res.won, res.defect) == (False, False)


def test_cell_result_takes_no_win_margin():
    with pytest.raises(TypeError):
        cell_result(8, [F("side0", 0.9)], 0.05)


def _build(enemy, swap):
    return Setup(groups=(), unit_types={"enemy": enemy, "swap": swap})


class Scripted:
    def __init__(self, outcome_of):
        self.outcome_of = outcome_of

    def __call__(self, setup, seed, swap):
        e = setup.unit_types["enemy"]
        o = self.outcome_of(e, seed, swap)
        return F(o, {"side0": 0.5, "side1": -0.5}.get(o, 0.0))


def test_cell_runs_fights_through_the_defect_rule():
    fn = Scripted(lambda e, s, w: "draw" if (s, w) == (0, False) else "side0")
    res = cell(_build, 8, 2, fight_fn=fn)
    assert res.mean_margin == pytest.approx(0.375) and res.won is False and res.defect is True


def test_a_draw_cell_inside_the_won_run_ends_the_run_there_for_the_break_even():
    """Cells up to 10 are clean wins; from 11 every fight is a draw: beats 10, loses_to 11, and those cells are defects."""
    outcome = lambda e, s, w: "draw" if e >= 11 else "side0"
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Scripted(outcome), full_scan=True)
    assert [c.won for c in res.cells] == [True, True, True, False, False, False, False]
    assert [c.defect for c in res.cells] == [False] * 3 + [True] * 4
    assert (res.beats, res.loses_to) == (10, 11)


def test_a_cap_in_one_cell_does_not_stop_the_scan():
    outcome = lambda e, s, w: "cap" if (e, s, w) == (11, 0, True) else "side0"
    rec = []

    def fn(setup, seed, swap):
        rec.append(setup.unit_types["enemy"])
        return Scripted(outcome)(setup, seed, swap)

    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=fn, full_scan=True)
    assert sorted(set(rec)) == list(range(8, 15)) and res.cells[3].defect is True
    assert (res.beats, res.loses_to) == (10, 11)
