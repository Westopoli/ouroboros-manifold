# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-14
"""Leaf-04: cell and scan, driven through fight_fn with scripted margins."""
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup, WIN_MARGIN  # noqa: E402
from scripts.skilllab.scan import cell, scan  # noqa: E402


def _result(margin, outcome="side0"):
    return FightResult(outcome=outcome, margin=margin, strength_left=(1.0, 0.0), survivors=(1, 0),
                       heads=(1, 1), ticks=10, first_contact_tick=0, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _build(enemy_heads, swap):
    # The setup carries the build arguments so a fight_fn can read what cell passed in.
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap})


class Recorder:
    """fight_fn that logs (enemy, seed, swap) and answers margin_of(enemy, seed, swap)."""

    def __init__(self, margin_of, outcome_of=None):
        self.margin_of = margin_of
        self.outcome_of = outcome_of or (lambda e, s, w: "side0")
        self.calls = []
        self.setups = []
        self.results = []

    def __call__(self, setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        assert setup.unit_types["swap"] == swap  # cell passes build(enemy, swap)'s own swap
        self.calls.append((enemy, seed, swap))
        self.setups.append(setup)
        r = _result(self.margin_of(enemy, seed, swap), self.outcome_of(enemy, seed, swap))
        self.results.append(r)
        return r


def test_cell_call_order_is_swap_outer_seed_inner():
    """AC-13: swap False then True outer, seeds 0..replicates-1 inner, exactly 2*replicates calls."""
    rec = Recorder(lambda e, s, w: 0.5)
    cell(_build, 12, 3, fight_fn=rec)
    assert rec.calls == [(12, 0, False), (12, 1, False), (12, 2, False),
                         (12, 0, True), (12, 1, True), (12, 2, True)]


def test_cell_returns_every_fight_in_call_order_and_plain_mean():
    """AC-13: fights holds every FightResult in call order; mean_margin is the plain mean."""
    margins = {(0, False): 0.5, (1, False): 0.25, (0, True): -0.25, (1, True): 0.75}
    rec = Recorder(lambda e, s, w: margins[(s, w)])
    res = cell(_build, 9, 2, fight_fn=rec)
    assert isinstance(res, CellResult)
    assert res.enemy_heads == 9
    assert len(res.fights) == 4
    assert all(a is b for a, b in zip(res.fights, rec.results))
    assert res.mean_margin == pytest.approx(0.3125, abs=1e-12)


def test_cell_passes_the_built_setup_to_fight_fn():
    """AC-13/14: fight_fn(setup, seed, swap) gets the setup that build(enemy_heads, swap) returned."""
    built = []

    def build(enemy_heads, swap):
        s = _build(enemy_heads, swap)
        built.append(s)
        return s

    rec = Recorder(lambda e, s, w: 0.0)
    cell(build, 7, 2, fight_fn=rec)
    assert len(built) == 4
    assert all(any(b is s for b in built) for s in rec.setups)


def test_cell_won_is_strictly_greater_than_win_margin():
    """AC-13 (L32 'greater than'): mean exactly at the win margin is lost; just above is won."""
    at = cell(_build, 8, 2, win_margin=0.5, fight_fn=Recorder(lambda e, s, w: 0.5))
    above = cell(_build, 8, 2, win_margin=0.5, fight_fn=Recorder(lambda e, s, w: 0.5 + 2 ** -10))
    assert at.mean_margin == 0.5 and at.won is False
    assert above.won is True


def test_cell_win_margin_default_and_parameter():
    """AC-13: default win margin is WIN_MARGIN (0.05); the parameter replaces it."""
    assert WIN_MARGIN == 0.05
    assert cell(_build, 8, 2, fight_fn=Recorder(lambda e, s, w: 0.06)).won is True
    assert cell(_build, 8, 2, fight_fn=Recorder(lambda e, s, w: 0.04)).won is False
    assert cell(_build, 8, 2, win_margin=0.2, fight_fn=Recorder(lambda e, s, w: 0.1)).won is False
    assert cell(_build, 8, 2, win_margin=0.01, fight_fn=Recorder(lambda e, s, w: 0.1)).won is True


def test_cell_won_follows_the_mean_not_the_majority():
    """AC-13: one big win among three small losses still averages above the win margin."""
    rec = Recorder(lambda e, s, w: 0.9 if (s, w) == (0, False) else -0.1)
    res = cell(_build, 8, 2, fight_fn=rec)
    assert res.mean_margin == pytest.approx(0.15, abs=1e-12)
    assert res.won is True


def test_cell_averages_over_both_spawn_orders():
    """AC-13: a first-mover edge (+0.5 unswapped, -0.5 swapped) cancels to a lost cell."""
    res = cell(_build, 8, 3, fight_fn=Recorder(lambda e, s, w: -0.5 if w else 0.5))
    assert res.mean_margin == pytest.approx(0.0, abs=1e-12)
    assert res.won is False


def test_cell_stalemate_and_cap_margins_are_averaged():
    """AC-15: a stalemate or cap fight adds its margin to the mean like any other fight."""
    outcomes = {(0, False): "side0", (1, False): "stalemate", (0, True): "side0", (1, True): "cap"}
    margins = {(0, False): 0.8, (1, False): 0.2, (0, True): 0.6, (1, True): -0.2}
    rec = Recorder(lambda e, s, w: margins[(s, w)], lambda e, s, w: outcomes[(s, w)])
    res = cell(_build, 8, 2, fight_fn=rec)
    assert [f.outcome for f in res.fights] == ["side0", "stalemate", "side0", "cap"]
    assert res.mean_margin == pytest.approx(0.35, abs=1e-12)
    assert res.won is False  # AC-15: stalemate/cap present, so not won even though the mean is above 0.05


def test_cell_one_replicate_makes_two_calls():
    """AC-13 (Cardinality one): replicates=1 is one seed (0) per spawn order."""
    rec = Recorder(lambda e, s, w: 0.3)
    cell(_build, 8, 1, fight_fn=rec)
    assert rec.calls == [(8, 0, False), (8, 0, True)]


def test_cell_default_fight_fn_is_fight_module_fight(monkeypatch):
    """AC-14: with no fight_fn the cell calls scripts.skilllab.fight.fight(setup, seed, swap)."""
    import scripts.skilllab.fight as fight_module
    seen = []

    def fake(setup, seed, swap):
        seen.append((setup.unit_types["enemy"], seed, swap))
        return _result(0.4)

    monkeypatch.setattr(fight_module, "fight", fake)
    res = cell(_build, 10, 2)
    assert seen == [(10, 0, False), (10, 1, False), (10, 0, True), (10, 1, True)]
    assert res.mean_margin == pytest.approx(0.4, abs=1e-12)


def test_cell_calls_scale_linearly_in_replicates():
    """AC-13 scale: the fight_fn call count of a cell is exactly 2 * replicates (fresh input per size)."""
    rng = random.Random(41)
    counts = {}
    for reps in (5, 10, 20):
        table = {}
        rec = Recorder(lambda e, s, w, t=table: t.setdefault((s, w), rng.uniform(-1, 1)))
        cell(_build, 13, reps, fight_fn=rec)
        counts[reps] = len(rec.calls)
        assert sorted(set(rec.calls)) == sorted((13, s, w) for s in range(reps) for w in (False, True))
    assert counts == {5: 10, 10: 20, 20: 40}
    assert counts[20] / counts[10] == 2.0


def _series(won_up_to):
    """Margin series: won (+0.5) for enemy <= won_up_to, lost (-0.5) above it."""
    return lambda e, s, w: 0.5 if e <= won_up_to else -0.5


@pytest.mark.parametrize("won_up_to", [8, 9, 12, 23])
def test_scan_beats_is_last_won_before_the_change(won_up_to):
    """AC-14/27: a known won-to-lost change gives beats = last won, loses_to = beats + 1."""
    res = scan(_build, 16, 8, 24, replicates=2, fight_fn=Recorder(_series(won_up_to)))
    assert isinstance(res, ScanResult)
    assert res.beats == won_up_to
    assert res.loses_to == won_up_to + 1


def test_scan_change_at_last_cell_still_found():
    """AC-14 boundary: only the final cell lost -> beats is the second-to-last headcount."""
    res = scan(_build, 16, 8, 12, replicates=1, fight_fn=Recorder(_series(11)))
    assert (res.beats, res.loses_to) == (11, 12)


@pytest.mark.parametrize("name,margin_of", [
    ("all_won", lambda e, s, w: 0.5),
    ("all_lost", lambda e, s, w: -0.5),
    ("flat_zero", lambda e, s, w: 0.0),
    ("flat_small_positive_under_margin", lambda e, s, w: 0.04),
])
def test_scan_flat_series_gives_none_none(name, margin_of):
    """AC-14/27: no won-to-lost change (all won, all lost, flat) -> beats and loses_to are None."""
    res = scan(_build, 16, 8, 24, replicates=2, fight_fn=Recorder(margin_of))
    assert res.beats is None and res.loses_to is None


def test_scan_single_cell_has_no_change():
    """AC-14 (Cardinality one): one cell cannot change from won to lost."""
    for margin in (0.5, -0.5):
        res = scan(_build, 16, 10, 10, replicates=2, fight_fn=Recorder(lambda e, s, w, m=margin: m))
        assert len(res.cells) == 1
        assert res.beats is None and res.loses_to is None


def test_scan_uses_first_won_to_lost_change_scanning_upward():
    """AC-14 (L33 'first won-to-lost change'): won 8-10, lost 11, won 12, lost 13+ -> beats 10."""
    won = {8, 9, 10, 12}
    res = scan(_build, 16, 8, 16, replicates=2, fight_fn=Recorder(lambda e, s, w: 0.5 if e in won else -0.5))
    assert (res.beats, res.loses_to) == (10, 11)


def test_scan_lost_to_won_change_is_not_a_break_even():
    """AC-14: starting lost, turning won, then lost: beats is the last won before the first won-to-lost."""
    won = {10, 11}
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Recorder(lambda e, s, w: 0.5 if e in won else -0.5))
    assert (res.beats, res.loses_to) == (11, 12)


def test_scan_lost_then_won_only_has_no_break_even():
    """AC-14: a lost-to-won change alone leaves beats and loses_to None."""
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Recorder(lambda e, s, w: 0.5 if e >= 11 else -0.5))
    assert res.beats is None and res.loses_to is None


def test_scan_win_margin_boundary_decides_the_change():
    """AC-14/13: a cell whose mean margin equals the win margin counts as lost."""
    res = scan(_build, 16, 8, 14, replicates=2, win_margin=0.5,
               fight_fn=Recorder(lambda e, s, w: 1.0 if e <= 10 else 0.5))
    assert res.win_margin == 0.5
    assert [c.won for c in res.cells] == [True, True, True, False, False, False, False]
    assert (res.beats, res.loses_to) == (10, 11)


def test_scan_default_win_margin_recorded():
    """AC-14: ScanResult.win_margin is WIN_MARGIN when not given."""
    res = scan(_build, 16, 8, 9, replicates=1, fight_fn=Recorder(lambda e, s, w: 0.0))
    assert res.win_margin == WIN_MARGIN


def test_scan_cells_in_increasing_order_inclusive_of_both_ends():
    """AC-14: one cell per headcount enemy_from..enemy_to inclusive, increasing; size recorded."""
    res = scan(_build, 16, 12, 17, replicates=1, fight_fn=Recorder(lambda e, s, w: 0.0))
    assert res.size == 16
    assert [c.enemy_heads for c in res.cells] == [12, 13, 14, 15, 16, 17]
    assert all(isinstance(c, CellResult) for c in res.cells)


def test_scan_runs_cells_in_order_with_cells_times_two_times_replicates_calls():
    """AC-14: a plain loop of cells, exactly cells * 2 * replicates fight_fn calls."""
    rec = Recorder(lambda e, s, w: 0.0)
    scan(_build, 16, 10, 13, replicates=3, fight_fn=rec)
    assert len(rec.calls) == 4 * 2 * 3
    assert [c[0] for c in rec.calls] == [e for e in (10, 11, 12, 13) for _ in range(6)]
    assert rec.calls[:6] == [(10, 0, False), (10, 1, False), (10, 2, False),
                             (10, 0, True), (10, 1, True), (10, 2, True)]


def test_scan_default_replicates_is_ten():
    """AC-14: replicates defaults to 10 (20 calls per cell)."""
    rec = Recorder(lambda e, s, w: 0.0)
    scan(_build, 16, 8, 9, fight_fn=rec)
    assert len(rec.calls) == 2 * 2 * 10


def test_scan_cells_hold_the_recorded_fights():
    """AC-14 composition scan->cell: each ScanResult cell carries that cell's own fights and mean."""
    rec = Recorder(lambda e, s, w: e / 100.0)
    res = scan(_build, 16, 8, 10, replicates=2, fight_fn=rec)
    for c in res.cells:
        assert len(c.fights) == 4
        assert c.mean_margin == pytest.approx(c.enemy_heads / 100.0, abs=1e-12)
    assert [f for c in res.cells for f in c.fights] == rec.results


def test_scan_fight_calls_scale_with_the_number_of_cells():
    """AC-14 scale: fight_fn calls grow exactly by the cell ratio (5 cells vs 10 cells, fresh content)."""
    rng = random.Random(7)

    def calls_for(enemy_from, enemy_to):
        series = {}
        rec = Recorder(lambda e, s, w: series.setdefault((e, s, w), rng.uniform(-1, 1)))
        scan(_build, 16, enemy_from, enemy_to, replicates=4, fight_fn=rec)
        return len(rec.calls)

    five = calls_for(10, 14)
    ten = calls_for(20, 29)
    assert five == 5 * 2 * 4
    assert ten == 10 * 2 * 4
    assert ten / five == 2.0
    twenty = calls_for(30, 49)
    assert twenty / ten == 2.0


def test_scan_does_not_call_fight_fn_twice_for_one_cell_fight():
    """AC-14 scale (anti-gaming): no fight is repeated; every (enemy, seed, swap) occurs exactly once."""
    rec = Recorder(lambda e, s, w: 0.1)
    scan(_build, 16, 8, 14, replicates=3, fight_fn=rec)
    assert len(rec.calls) == len(set(rec.calls)) == 7 * 2 * 3


@pytest.mark.parametrize("bad", [0, -1, -10])
def test_cell_replicates_below_one_raises_value_error(bad):
    """AC-13 Reading: replicates < 1 raises ValueError and runs no fight."""
    rec = Recorder(lambda e, s, w: 0.5)
    with pytest.raises(ValueError):
        cell(_build, 8, bad, fight_fn=rec)
    assert rec.calls == []


@pytest.mark.parametrize("bad", [0, -3])
def test_scan_replicates_below_one_raises_value_error(bad):
    """AC-13 Reading through scan: replicates < 1 raises ValueError."""
    with pytest.raises(ValueError):
        scan(_build, 16, 8, 10, replicates=bad, fight_fn=Recorder(lambda e, s, w: 0.5))


@pytest.mark.parametrize("lo,hi", [(9, 8), (24, 8), (1, 0)])
def test_scan_enemy_from_above_enemy_to_raises_value_error(lo, hi):
    """AC-15 Reading: enemy_from > enemy_to raises ValueError and runs no fight."""
    rec = Recorder(lambda e, s, w: 0.5)
    with pytest.raises(ValueError):
        scan(_build, 16, lo, hi, replicates=2, fight_fn=rec)
    assert rec.calls == []


@pytest.mark.parametrize("bad_outcome", ["stalemate", "cap"])
def test_cell_with_a_stalemate_or_cap_fight_is_not_won_despite_a_high_mean(bad_outcome):
    """AC-15 Reading: mean margin 0.5 > 0.05 but one fight ended stalemate/cap -> won False; margin still averaged."""
    rec = Recorder(lambda e, s, w: 0.5, lambda e, s, w: bad_outcome if (s, w) == (1, True) else "side0")
    res = cell(_build, 8, 2, fight_fn=rec)
    assert res.mean_margin == pytest.approx(0.5, abs=1e-12)
    assert res.mean_margin > WIN_MARGIN
    assert res.won is False


@pytest.mark.parametrize("bad_outcome", ["stalemate", "cap"])
def test_cell_of_only_stalemate_or_cap_fights_is_not_won(bad_outcome):
    """AC-15 Reading: every fight stalemate/cap with a high mean margin -> not won, margin averaged."""
    res = cell(_build, 8, 3, fight_fn=Recorder(lambda e, s, w: 0.9, lambda e, s, w: bad_outcome))
    assert res.mean_margin == pytest.approx(0.9, abs=1e-12)
    assert res.won is False


def test_cell_without_stalemate_or_cap_and_high_mean_is_still_won():
    """AC-15 Reading (control): the same margins with all fights decided are won."""
    res = cell(_build, 8, 2, fight_fn=Recorder(lambda e, s, w: 0.5, lambda e, s, w: "side0"))
    assert res.won is True


def test_scan_treats_a_stalemate_cell_as_lost_when_finding_the_break_even():
    """AC-15/14 composition: cell 11 has one cap fight; its mean is high but it is lost, so beats is 10."""
    outcome = lambda e, s, w: "cap" if (e, s, w) == (11, 0, True) else "side0"
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Recorder(lambda e, s, w: 0.5, outcome))
    assert [c.won for c in res.cells] == [True, True, True, False, True, True, True]
    assert res.cells[3].mean_margin == pytest.approx(0.5, abs=1e-12)
    assert (res.beats, res.loses_to) == (10, 11)
