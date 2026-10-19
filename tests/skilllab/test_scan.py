# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Contract::Cell and scan; rulings 1 and 4; row L4 (bracketed bisection default, --full-scan linear)
"""LAB-REV2-L4: cell and scan, driven through fight_fn with scripted outcomes. No engine.

Rules under test (spec "Cell and scan", decisions 12):
- a cell is WON when every fight in it is `side0`; margins decide nothing. `WIN_MARGIN` and `DRAW_BAND` are deleted.
- a `draw` or `cap` fight marks the cell `defect` (CellResult.defect); the scan carries on past it.
- break-even is read over the scanned headcounts as before (the first won-to-lost change); a scan that is won all the way to
  `enemy_to` with no loss is `ceiling_hit = True`, with beats = enemy_to and loses_to = None (ruling 4: never "no gain").
- ScanResult.multi_flip is True when the won/lost sequence over the scanned cells changes more than once.
- scan() default is a bracketed bisection: a coarse pass over the range, then halving of the first won-to-lost bracket down to
  adjacent headcounts. full_scan=True is the linear sweep, one cell per headcount.
Contract fields these tests need (contract.py, which L4's builder must edit; see the report): CellResult.defect (default False),
ScanResult.ceiling_hit and ScanResult.multi_flip (default False), no ScanResult.win_margin.
"""
import ast
import dataclasses
import inspect
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import scan as scan_module  # noqa: E402
from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup  # noqa: E402
from scripts.skilllab.scan import cell, scan  # noqa: E402

MARGIN = {"side0": 0.5, "side1": -0.5, "draw": 0.0, "cap": 0.0}


def _result(outcome, margin=None):
    return FightResult(outcome=outcome, margin=MARGIN[outcome] if margin is None else margin, strength_left=(1.0, 0.0),
                       survivors=(1, 0), heads=(1, 1), ticks=10, first_contact_tick=0, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _build(enemy_heads, swap):
    # The setup carries the build arguments so a fight_fn can read what cell passed in.
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap})


class Recorder:
    """fight_fn that logs (enemy, seed, swap) and answers outcome_of(enemy, seed, swap); margin_of overrides the margin."""

    def __init__(self, outcome_of, margin_of=None):
        self.outcome_of = outcome_of
        self.margin_of = margin_of
        self.calls = []
        self.setups = []
        self.results = []

    def __call__(self, setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        assert setup.unit_types["swap"] == swap  # cell passes build(enemy, swap)'s own swap
        self.calls.append((enemy, seed, swap))
        self.setups.append(setup)
        outcome = self.outcome_of(enemy, seed, swap)
        r = _result(outcome, None if self.margin_of is None else self.margin_of(enemy, seed, swap))
        self.results.append(r)
        return r

    @property
    def heads(self):
        return sorted({c[0] for c in self.calls})


def won_up_to(edge):
    """side0 wins every fight at or below `edge` enemy heads, side1 above."""
    return lambda e, s, w: "side0" if e <= edge else "side1"


def won_set(heads):
    heads = set(heads)
    return lambda e, s, w: "side0" if e in heads else "side1"


# ---- cell -------------------------------------------------------------------------------------------------------------

def test_cell_call_order_is_swap_outer_seed_inner():
    rec = Recorder(won_up_to(99))
    cell(_build, 12, 3, fight_fn=rec)
    assert rec.calls == [(12, 0, False), (12, 1, False), (12, 2, False), (12, 0, True), (12, 1, True), (12, 2, True)]


def test_cell_returns_every_fight_in_call_order_and_plain_mean_margin():
    margins = {(0, False): 0.5, (1, False): 0.25, (0, True): -0.25, (1, True): 0.75}
    rec = Recorder(won_up_to(99), margin_of=lambda e, s, w: margins[(s, w)])
    res = cell(_build, 9, 2, fight_fn=rec)
    assert isinstance(res, CellResult) and res.enemy_heads == 9 and len(res.fights) == 4
    assert all(a is b for a, b in zip(res.fights, rec.results))
    assert res.mean_margin == pytest.approx(0.3125, abs=1e-12)


def test_cell_passes_the_built_setup_to_fight_fn():
    built = []

    def build(enemy_heads, swap):
        s = _build(enemy_heads, swap)
        built.append(s)
        return s

    rec = Recorder(won_up_to(99))
    cell(build, 7, 2, fight_fn=rec)
    assert len(built) == 4 and all(any(b is s for b in built) for s in rec.setups)


def test_cell_is_won_when_every_fight_is_side0_whatever_the_margins():
    """Ruling 1: who was left standing decides. A margin of 0.001 on every fight is still won (no win margin)."""
    res = cell(_build, 8, 2, fight_fn=Recorder(won_up_to(99), margin_of=lambda e, s, w: 0.001))
    assert res.won is True and res.defect is False


def test_cell_with_one_side1_fight_is_not_won_despite_a_high_mean_margin():
    outcome = lambda e, s, w: "side1" if (s, w) == (1, True) else "side0"
    res = cell(_build, 8, 2, fight_fn=Recorder(outcome, margin_of=lambda e, s, w: 0.9))
    assert res.mean_margin == pytest.approx(0.9, abs=1e-12)
    assert res.won is False and res.defect is False        # a plain loss is not a defect


def test_cell_of_only_side1_fights_is_lost_and_not_a_defect():
    res = cell(_build, 8, 2, fight_fn=Recorder(won_up_to(0)))
    assert res.won is False and res.defect is False


@pytest.mark.parametrize("bad", ["draw", "cap"])
def test_a_draw_or_cap_fight_marks_the_cell_defect_and_not_won(bad):
    outcome = lambda e, s, w: bad if (s, w) == (0, True) else "side0"
    res = cell(_build, 8, 2, fight_fn=Recorder(outcome))
    assert res.defect is True and res.won is False
    assert [f.outcome for f in res.fights] == ["side0", "side0", bad, "side0"]


@pytest.mark.parametrize("bad", ["draw", "cap"])
def test_positive_control_the_same_cell_without_the_bad_fight_is_won_and_clean(bad):
    clean = cell(_build, 8, 2, fight_fn=Recorder(won_up_to(99)))
    dirty = cell(_build, 8, 2, fight_fn=Recorder(lambda e, s, w: bad if (s, w) == (0, True) else "side0"))
    assert (clean.won, clean.defect) == (True, False) and (dirty.won, dirty.defect) == (False, True)


def test_cell_one_replicate_makes_two_calls():
    rec = Recorder(won_up_to(99))
    cell(_build, 8, 1, fight_fn=rec)
    assert rec.calls == [(8, 0, False), (8, 0, True)]


def test_cell_default_fight_fn_is_fight_module_fight(monkeypatch):
    import scripts.skilllab.fight as fight_module
    seen = []

    def fake(setup, seed, swap):
        seen.append((setup.unit_types["enemy"], seed, swap))
        return _result("side0")

    monkeypatch.setattr(fight_module, "fight", fake)
    res = cell(_build, 10, 2)
    assert seen == [(10, 0, False), (10, 1, False), (10, 0, True), (10, 1, True)] and res.won is True


@pytest.mark.parametrize("bad", [0, -1, -10])
def test_cell_replicates_below_one_raises_value_error(bad):
    rec = Recorder(won_up_to(99))
    with pytest.raises(ValueError):
        cell(_build, 8, bad, fight_fn=rec)
    assert rec.calls == []


def test_cell_calls_scale_linearly_in_replicates():
    for reps in (5, 10, 20):
        rec = Recorder(won_up_to(99))
        cell(_build, 13, reps, fight_fn=rec)
        assert sorted(set(rec.calls)) == sorted((13, s, w) for s in range(reps) for w in (False, True))
        assert len(rec.calls) == 2 * reps


# ---- retired names and contract fields ------------------------------------------------------------------------------

def _identifiers(path):
    """Every name a module uses or binds, by AST (comments and strings do not count)."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
        elif isinstance(node, (ast.ImportFrom, ast.Import)):
            found.update(a.name for a in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            found.add(node.name)
    return found


@pytest.mark.parametrize("name", ["WIN_MARGIN", "DRAW_BAND", "win_margin"])
@pytest.mark.parametrize("mod", ["scan", "breakeven", "batches", "depth", "sweep", "__main__"])
def test_win_margin_and_draw_band_are_gone_from_the_l4_modules(mod, name):
    """Spec: WIN_MARGIN and DRAW_BAND deleted. (contract.py's own copy goes in the same piece; the report says so.)
    The sweep module is new and must not bring them back."""
    path = ROOT / "scripts" / "skilllab" / (mod + ".py")
    assert path.exists() or mod == "sweep"
    if path.exists():
        assert name not in _identifiers(path), "%s still uses %s" % (mod, name)


@pytest.mark.parametrize("fn", [cell, scan])
def test_cell_and_scan_take_no_win_margin_argument(fn):
    assert "win_margin" not in inspect.signature(fn).parameters


def test_contract_carries_defect_ceiling_hit_and_multi_flip_and_no_win_margin():
    cell_fields = {f.name: f for f in dataclasses.fields(CellResult)}
    scan_fields = {f.name: f for f in dataclasses.fields(ScanResult)}
    assert cell_fields["defect"].default is False
    assert scan_fields["ceiling_hit"].default is False and scan_fields["multi_flip"].default is False
    assert "win_margin" not in scan_fields


def test_scan_signature_defaults_to_bisection_and_full_scan_is_off():
    params = inspect.signature(scan).parameters
    assert params["full_scan"].default is False and params["replicates"].default == 10


# ---- scan: full (linear) -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("edge", [8, 9, 12, 23, 24])
def test_full_scan_beats_is_last_won_before_the_change(edge):
    res = scan(_build, 16, 8, 25, replicates=2, fight_fn=Recorder(won_up_to(edge)), full_scan=True)
    assert isinstance(res, ScanResult)
    assert (res.beats, res.loses_to, res.ceiling_hit, res.multi_flip) == (edge, edge + 1, False, False)


def test_full_scan_runs_one_cell_per_headcount_in_increasing_order_inclusive():
    rec = Recorder(won_up_to(14))
    res = scan(_build, 16, 12, 17, replicates=1, fight_fn=rec, full_scan=True)
    assert res.size == 16 and [c.enemy_heads for c in res.cells] == [12, 13, 14, 15, 16, 17]
    assert [c[0] for c in rec.calls] == [e for e in range(12, 18) for _ in range(2)]


def test_full_scan_cells_hold_the_recorded_fights():
    rec = Recorder(won_up_to(9), margin_of=lambda e, s, w: e / 100.0)
    res = scan(_build, 16, 8, 10, replicates=2, fight_fn=rec, full_scan=True)
    for c in res.cells:
        assert len(c.fights) == 4 and c.mean_margin == pytest.approx(c.enemy_heads / 100.0, abs=1e-12)
    assert [f for c in res.cells for f in c.fights] == rec.results


def test_all_won_to_the_end_is_a_ceiling_hit_not_none():
    """Ruling 4 / spec: beats = enemy_to with no loss is ceiling_hit; it is never reported as 'no break-even'."""
    res = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(won_up_to(99)), full_scan=True)
    assert (res.beats, res.loses_to, res.ceiling_hit, res.multi_flip) == (48, None, True, False)


@pytest.mark.parametrize("name,outcome_of", [
    ("all_lost", won_up_to(0)),
    ("all_draws", lambda e, s, w: "draw"),
    ("all_caps", lambda e, s, w: "cap"),
])
def test_lost_everywhere_gives_none_and_no_ceiling_hit(name, outcome_of):
    res = scan(_build, 16, 8, 24, replicates=2, fight_fn=Recorder(outcome_of), full_scan=True)
    assert (res.beats, res.loses_to, res.ceiling_hit, res.multi_flip) == (None, None, False, False)


def test_single_cell_scan_won_is_a_ceiling_hit_and_lost_is_none():
    won = scan(_build, 16, 10, 10, replicates=2, fight_fn=Recorder(won_up_to(99)), full_scan=True)
    lost = scan(_build, 16, 10, 10, replicates=2, fight_fn=Recorder(won_up_to(0)), full_scan=True)
    assert len(won.cells) == 1 and (won.beats, won.loses_to, won.ceiling_hit) == (10, None, True)
    assert (lost.beats, lost.loses_to, lost.ceiling_hit) == (None, None, False)


def test_scan_uses_first_won_to_lost_change_and_reports_multi_flip():
    """Won 8-10, lost 11, won 12, lost 13+: three changes, beats from the first won-to-lost."""
    res = scan(_build, 16, 8, 16, replicates=2, fight_fn=Recorder(won_set({8, 9, 10, 12})), full_scan=True)
    assert (res.beats, res.loses_to, res.multi_flip, res.ceiling_hit) == (10, 11, True, False)


def test_lost_then_won_then_lost_reads_the_win_to_loss_and_is_multi_flip():
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Recorder(won_set({10, 11})), full_scan=True)
    assert (res.beats, res.loses_to, res.multi_flip) == (11, 12, True)


def test_lost_then_won_only_is_one_change_so_not_multi_flip():
    """A loss-to-win change alone is no win-to-loss, so no break-even is read from it; it is one change, not two."""
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=Recorder(lambda e, s, w: "side0" if e >= 11 else "side1"), full_scan=True)
    assert res.multi_flip is False and res.loses_to is None


def test_a_defect_cell_is_lost_and_the_scan_carries_on_past_it():
    """Won 8-10, cell 11 has a cap fight, won 12-14: the scan still fights 12-14; beats 10; two changes."""
    outcome = lambda e, s, w: "cap" if (e, s, w) == (11, 0, True) else "side0"
    rec = Recorder(outcome)
    res = scan(_build, 16, 8, 14, replicates=2, fight_fn=rec, full_scan=True)
    assert [c.won for c in res.cells] == [True, True, True, False, True, True, True]
    assert [c.defect for c in res.cells] == [False, False, False, True, False, False, False]
    assert (res.beats, res.loses_to, res.multi_flip) == (10, 11, True)
    assert rec.heads == list(range(8, 15))


def test_draw_cells_are_defects_too():
    outcome = lambda e, s, w: "draw" if e == 9 else "side0"
    res = scan(_build, 16, 8, 10, replicates=1, fight_fn=Recorder(outcome), full_scan=True)
    assert [(c.won, c.defect) for c in res.cells] == [(True, False), (False, True), (True, False)]


def test_full_scan_fight_calls_scale_with_the_number_of_cells_and_never_repeat():
    rng = random.Random(7)
    series = {}
    counts = []
    for lo, hi in ((10, 14), (20, 29), (30, 49)):
        rec = Recorder(lambda e, s, w: series.setdefault((e, s, w), rng.choice(["side0", "side1"])))
        scan(_build, 16, lo, hi, replicates=4, fight_fn=rec, full_scan=True)
        assert len(rec.calls) == len(set(rec.calls)) == (hi - lo + 1) * 2 * 4
        counts.append(len(rec.calls))
    assert counts[1] / counts[0] == 2.0 and counts[2] / counts[1] == 2.0


@pytest.mark.parametrize("bad", [0, -3])
def test_scan_replicates_below_one_raises_value_error(bad):
    with pytest.raises(ValueError):
        scan(_build, 16, 8, 10, replicates=bad, fight_fn=Recorder(won_up_to(99)))


@pytest.mark.parametrize("lo,hi", [(9, 8), (24, 8), (1, 0)])
@pytest.mark.parametrize("full", [False, True])
def test_scan_enemy_from_above_enemy_to_raises_value_error(lo, hi, full):
    rec = Recorder(won_up_to(99))
    with pytest.raises(ValueError):
        scan(_build, 16, lo, hi, replicates=2, fight_fn=rec, full_scan=full)
    assert rec.calls == []


# ---- scan: bracketed bisection (the default) -------------------------------------------------------------------------

def _probes(res):
    return [c.enemy_heads for c in res.cells]


@pytest.mark.parametrize("edge", list(range(8, 48)))
def test_bisection_finds_the_same_break_even_as_the_linear_sweep_on_one_flip(edge):
    """Spec test: on a fake with one flip, bisection and the linear sweep agree on beats, loses_to, ceiling_hit, multi_flip."""
    bis = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(won_up_to(edge)))
    lin = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(won_up_to(edge)), full_scan=True)
    assert (bis.beats, bis.loses_to, bis.ceiling_hit, bis.multi_flip) == (lin.beats, lin.loses_to, lin.ceiling_hit, lin.multi_flip)
    assert (bis.beats, bis.loses_to) == (edge, edge + 1)


@pytest.mark.parametrize("edge", [8, 15, 16, 27, 47])
def test_bisection_fights_far_fewer_cells_than_the_linear_sweep(edge):
    """The 90 s scan mark rests on this: at most 14 of the 41 headcounts, in increasing order, with both bracket cells present."""
    rec = Recorder(won_up_to(edge))
    res = scan(_build, 16, 8, 48, replicates=3, fight_fn=rec)
    heads = _probes(res)
    assert heads == sorted(set(heads)) and len(heads) <= 14
    assert edge in heads and edge + 1 in heads
    assert rec.heads == heads and len(rec.calls) == len(heads) * 2 * 3 == len(set(rec.calls))
    lin = Recorder(won_up_to(edge))
    scan(_build, 16, 8, 48, replicates=3, fight_fn=lin, full_scan=True)
    assert len(lin.calls) == 41 * 2 * 3 > 2 * len(rec.calls)


def test_bisection_ceiling_hit_when_won_everywhere():
    rec = Recorder(won_up_to(99))
    res = scan(_build, 16, 8, 48, replicates=1, fight_fn=rec)
    assert (res.beats, res.loses_to, res.ceiling_hit, res.multi_flip) == (48, None, True, False)
    assert len(_probes(res)) <= 14 and 48 in _probes(res)


def test_bisection_lost_everywhere_is_none_and_cheap():
    rec = Recorder(won_up_to(0))
    res = scan(_build, 16, 8, 48, replicates=1, fight_fn=rec)
    assert (res.beats, res.loses_to, res.ceiling_hit, res.multi_flip) == (None, None, False, False)
    assert len(_probes(res)) <= 14


def test_bisection_reports_multi_flip_on_two_wide_flips_and_reads_the_first_win_to_loss():
    """Won 8-20, lost 21-36, won 37-48: two changes, far enough apart that the coarse pass shows both. The linear sweep reads the
    same beats and the same flag. Not a ceiling hit: there is a loss in the range."""
    fn = won_set(set(range(8, 21)) | set(range(37, 49)))
    bis = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(fn))
    lin = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(fn), full_scan=True)
    for res in (bis, lin):
        assert (res.beats, res.loses_to, res.multi_flip, res.ceiling_hit) == (20, 21, True, False)


def test_bisection_one_flip_is_not_multi_flip_even_with_a_defect_cell_inside_the_lost_run():
    """Defect cells are lost cells; a clean win-to-loss with a capped cell in the lost run is still one change."""
    outcome = lambda e, s, w: "side0" if e <= 20 else ("cap" if e == 30 else "side1")
    res = scan(_build, 16, 8, 48, replicates=1, fight_fn=Recorder(outcome))
    assert (res.beats, res.loses_to, res.multi_flip) == (20, 21, False)


@pytest.mark.parametrize("lo,hi", [(8, 9), (8, 8), (10, 12)])
def test_bisection_handles_tiny_ranges(lo, hi):
    res = scan(_build, 16, lo, hi, replicates=1, fight_fn=Recorder(won_up_to(lo)))
    lin = scan(_build, 16, lo, hi, replicates=1, fight_fn=Recorder(won_up_to(lo)), full_scan=True)
    assert (res.beats, res.loses_to, res.ceiling_hit) == (lin.beats, lin.loses_to, lin.ceiling_hit)
    assert [c.enemy_heads for c in res.cells] == sorted({c.enemy_heads for c in res.cells})


def test_bisection_is_deterministic():
    a, b = Recorder(won_up_to(31)), Recorder(won_up_to(31))
    scan(_build, 16, 8, 48, replicates=2, fight_fn=a)
    scan(_build, 16, 8, 48, replicates=2, fight_fn=b)
    assert a.calls == b.calls


def test_map_fn_gets_the_jobs_and_fight_fn_together_is_refused():
    rec = Recorder(won_up_to(20))
    calls = []

    def map_fn(jobs):
        calls.append(len(jobs))
        return [rec(*job) for job in jobs]

    res = scan(_build, 16, 8, 48, replicates=1, map_fn=map_fn)
    assert (res.beats, res.loses_to) == (20, 21) and sum(calls) == len(rec.calls) and calls
    with pytest.raises(ValueError):
        scan(_build, 16, 8, 48, replicates=1, fight_fn=rec, map_fn=map_fn)
