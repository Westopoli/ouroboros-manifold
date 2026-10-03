# spec: ruling A201: a draw is decided, margin 0.0; stalemate and cap are undecided
"""scan.cell_result / scan.cell / scan.scan with draws among the fights."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fight  # noqa: E402
from scripts.skilllab.contract import WIN_MARGIN, Setup  # noqa: E402
from scripts.skilllab.scan import cell, cell_result, scan  # noqa: E402


def F(outcome, margin):
    return dataclasses.replace(fight(outcome=outcome), margin=margin)


def test_cell_of_only_draws_is_decided_mean_zero_and_not_won():
    res = cell_result(8, [F("draw", 0.0)] * 4, WIN_MARGIN)
    assert res.mean_margin == 0.0 and res.won is False


def test_a_draw_does_not_make_a_winning_cell_undecided():
    """Margins 0.9, 0.9, 0.9, draw 0.0 -> mean 0.675 > 0.05 and decided, so won."""
    res = cell_result(8, [F("side0", 0.9)] * 3 + [F("draw", 0.0)], WIN_MARGIN)
    assert res.mean_margin == pytest.approx(0.675) and res.won is True


def test_a_draw_adds_nothing_to_the_mean():
    with_draw = cell_result(8, [F("side0", 0.4), F("side0", 0.4), F("draw", 0.0), F("draw", 0.0)], WIN_MARGIN)
    assert with_draw.mean_margin == pytest.approx(0.2)


def test_draws_pulling_the_mean_under_the_margin_lose_the_cell():
    res = cell_result(8, [F("side0", 0.1)] + [F("draw", 0.0)] * 3, WIN_MARGIN)
    assert res.mean_margin == pytest.approx(0.025) and res.won is False


@pytest.mark.parametrize("bad", ["stalemate", "cap"])
def test_stalemate_and_cap_still_make_a_cell_not_won(bad):
    res = cell_result(8, [F("side0", 0.9)] * 3 + [F(bad, 0.9)], WIN_MARGIN)
    assert res.mean_margin == pytest.approx(0.9) and res.won is False


@pytest.mark.parametrize("bad", ["stalemate", "cap"])
def test_positive_control_a_draw_in_the_same_place_is_won(bad):
    """Same cell as above with the bad fight turned into a margin-0.9 draw would be won: only the label differs."""
    assert cell_result(8, [F("side0", 0.9)] * 3 + [F("draw", 0.9)], WIN_MARGIN).won is True
    assert cell_result(8, [F("side0", 0.9)] * 3 + [F(bad, 0.9)], WIN_MARGIN).won is False


def _build(enemy, swap):
    return Setup(groups=(), unit_types={"enemy": enemy, "swap": swap})


class Scripted:
    def __init__(self, outcome_of, margin_of):
        self.outcome_of, self.margin_of = outcome_of, margin_of

    def __call__(self, setup, seed, swap):
        e = setup.unit_types["enemy"]
        return F(self.outcome_of(e, seed, swap), self.margin_of(e, seed, swap))


def test_cell_runs_fights_through_the_draw_rule():
    fn = Scripted(lambda e, s, w: "draw" if (s, w) == (0, False) else "side0", lambda e, s, w: 0.0 if (s, w) == (0, False) else 0.5)
    res = cell(_build, 8, 2, fight_fn=fn)
    assert res.mean_margin == pytest.approx(0.375) and res.won is True


def test_break_even_unchanged_by_draws_that_do_not_move_the_mean_below_the_margin():
    """Cells up to 10 win with one draw per cell (mean 0.375); from 11 every fight is a draw (mean 0.0): beats 10."""
    def outcome(e, s, w):
        return "draw" if e >= 11 or (s, w) == (0, False) else "side0"
    margin = lambda e, s, w: 0.0 if outcome(e, s, w) == "draw" else 0.5
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Scripted(outcome, margin))
    assert [c.won for c in res.cells] == [True, True, True, False, False, False, False]
    assert (res.beats, res.loses_to) == (10, 11)


def test_break_even_still_treats_a_cap_cell_as_lost():
    outcome = lambda e, s, w: "cap" if (e, s, w) == (11, 0, True) else "side0"
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Scripted(outcome, lambda e, s, w: 0.5))
    assert (res.beats, res.loses_to) == (10, 11)
