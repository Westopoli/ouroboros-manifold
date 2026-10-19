# spec: Architect ruling A187 item 2 (more fights near a break-even) - scripts/skilllab/scan.py scan(refine_factor, refine_band); LAB-REV2-L4: linear cases pass full_scan=True, bisection cases at the end
"""Refinement: cells near the crossing are fought again with more seeds. Scripted fight functions; no engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import FightResult, Setup  # noqa: E402
from scripts.skilllab.scan import scan  # noqa: E402


def _result(margin, seed, swap):
    # ticks encodes (seed, swap) so a test can read which fight sits where in a cell; margin > 0 is a side0 win (LAB-REV2-L4:
    # a cell is won when every fight is side0)
    return FightResult(outcome="side0" if margin > 0 else "side1", margin=margin, strength_left=(1.0, 0.0), survivors=(1, 0), heads=(1, 1),
                       ticks=seed * 10 + int(swap), first_contact_tick=0, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _build(enemy_heads, swap):
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap})


class Fn:
    def __init__(self, margin_of):
        self.margin_of, self.calls = margin_of, []

    def __call__(self, setup, seed, swap):
        e = setup.unit_types["enemy"]
        self.calls.append((e, seed, swap))
        return _result(self.margin_of(e, seed, swap), seed, swap)


def _step(edge):
    """won (0.5) up to and including edge, lost (-0.5) above."""
    return lambda e, s, w: 0.5 if e <= edge else -0.5


def _scan(fn, lo=5, hi=15, replicates=2, **kw):
    kw.setdefault("full_scan", True)      # these cases read the neighbours of the crossing, which only the linear sweep fights
    return scan(_build, 10, lo, hi, replicates=replicates, fight_fn=fn, **kw)


def _decode(f):
    return divmod(f.ticks, 10)[0], bool(f.ticks % 10)


def test_call_counts_first_pass_plus_band_cells():
    fn = Fn(_step(9))
    r = _scan(fn, refine_factor=3)
    assert (r.beats, r.loses_to) == (9, 10)
    band = [e for e in range(5, 16) if 7 <= e <= 12]
    assert len(fn.calls) == 11 * 2 * 2 + len(band) * 2 * (6 - 2)
    for e in range(5, 16):
        n = sum(1 for c in fn.calls if c[0] == e)
        assert n == (2 * 6 if e in band else 2 * 2), e


def test_band_cells_are_exactly_beats_minus_2_to_loses_to_plus_2():
    fn = Fn(_step(9))
    r = _scan(fn, refine_factor=3)
    refined = [c.enemy_heads for c in r.cells if len(c.fights) == 12]
    assert refined == [7, 8, 9, 10, 11, 12]
    assert all(len(c.fights) == 4 for c in r.cells if c.enemy_heads not in refined)


def test_band_is_clipped_to_the_scanned_range():
    fn = Fn(_step(8))
    r = _scan(fn, lo=8, hi=20, refine_factor=3)
    assert (r.beats, r.loses_to) == (8, 9)
    assert [c.enemy_heads for c in r.cells if len(c.fights) == 12] == [8, 9, 10, 11]


def test_refine_band_argument_narrows_the_band():
    r = _scan(Fn(_step(9)), refine_factor=3, refine_band=0)
    assert [c.enemy_heads for c in r.cells if len(c.fights) == 12] == [9, 10]


def test_refined_fights_are_ordered_swap_false_then_true_by_seed_and_first_pass_kept():
    fn = Fn(_step(9))
    r = _scan(fn, refine_factor=3)
    cell = next(c for c in r.cells if c.enemy_heads == 9)
    assert [_decode(f) for f in cell.fights] == [(s, False) for s in range(6)] + [(s, True) for s in range(6)]
    assert sorted(c[1:] for c in fn.calls if c[0] == 9) == sorted(
        [(s, False) for s in range(6)] + [(s, True) for s in range(6)])
    outside = next(c for c in r.cells if c.enemy_heads == 5)
    assert [_decode(f) for f in outside.fights] == [(0, False), (1, False), (0, True), (1, True)]


def test_refined_cell_result_is_recomputed():
    r = _scan(Fn(_step(9)), refine_factor=3)
    cell = next(c for c in r.cells if c.enemy_heads == 9)
    assert cell.mean_margin == pytest.approx(0.5) and cell.won
    assert len(cell.fights) == 12


@pytest.mark.parametrize("margin_of,ceiling", [(lambda e, s, w: 0.5, True), (lambda e, s, w: -0.5, False)])
def test_no_crossing_refines_nothing(margin_of, ceiling):
    """Won everywhere is a ceiling hit (beats = the top headcount), lost everywhere is None; neither has a crossing to refine."""
    fn = Fn(margin_of)
    r = _scan(fn, refine_factor=3)
    assert r.ceiling_hit is ceiling and r.loses_to is None and len(fn.calls) == 11 * 2 * 2
    assert r.beats == (15 if ceiling else None)
    assert all(len(c.fights) == 4 for c in r.cells)


def test_refine_factor_one_equals_todays_result():
    margin = lambda e, s, w: 0.5 - 0.05 * e + 0.01 * s
    a = _scan(Fn(margin))
    b = _scan(Fn(margin), refine_factor=1)
    assert a == b


def test_crossing_can_move_after_refinement():
    # cell 10 wins on seeds 0 and 1 but loses on later seeds; the first pass sees a break-even at 10, the refined cell is lost
    margin = lambda e, s, w: (0.9 if s < 2 else -0.5) if e == 10 else (0.5 if e <= 9 else -0.5)
    first = _scan(Fn(margin))
    assert (first.beats, first.loses_to) == (10, 11)
    r = _scan(Fn(margin), refine_factor=3)
    assert (r.beats, r.loses_to) == (9, 10)
    cell = next(c for c in r.cells if c.enemy_heads == 10)
    assert not cell.won and len(cell.fights) == 12 and cell.mean_margin == pytest.approx((2 * 2 * 0.9 + 2 * 4 * -0.5) / 12)


@pytest.mark.parametrize("bad", [0, -1])
def test_refine_factor_below_one_raises(bad):
    with pytest.raises(ValueError):
        _scan(Fn(_step(9)), refine_factor=bad)


# ---- LAB-REV2-L4: refinement over the bisection (default) scan -------------------------------------------------------------

def test_bisection_refines_the_cells_it_fought_within_the_band_and_nothing_else():
    """Bisection fights only some headcounts; the ones within refine_band of the crossing get the extra seeds, the rest keep
    their first pass. The two bracket cells are always among them."""
    fn = Fn(_step(31))
    r = scan(_build, 10, 8, 48, replicates=2, fight_fn=fn, refine_factor=3)
    assert (r.beats, r.loses_to) == (31, 32)
    by = {c.enemy_heads: c for c in r.cells}
    assert len(by[31].fights) == len(by[32].fights) == 12
    for e, c in by.items():
        assert len(c.fights) == (12 if 29 <= e <= 34 else 4), e
    assert sorted(set(c[1:] for c in fn.calls if c[0] == 31)) == sorted([(s, False) for s in range(6)] + [(s, True) for s in range(6)])


def test_bisection_without_refinement_matches_refine_factor_one():
    margin = lambda e, s, w: 0.5 if e <= 20 else -0.5
    assert scan(_build, 10, 8, 48, replicates=2, fight_fn=Fn(margin)) == scan(_build, 10, 8, 48, replicates=2, fight_fn=Fn(margin),
                                                                             refine_factor=1)
