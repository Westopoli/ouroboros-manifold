# spec: break-even by scan with refinement, and the side-swap control (skill lab harness, item 3); LAB-REV2-L4
"""Break-even flips, refinement fights near a flip, and swap_control, driven through scripted fight_fn fakes.

LAB-REV2-L4: a cell is won when every fight is side0 (the fakes derive the outcome from the margin's sign: margin > 0 is side0),
there is no win margin, and find_break_even stays a LINEAR scan (it needs the neighbours of every flip, so it scans with
full_scan=True whatever scan()'s default is). A scan won all the way is a ceiling hit: BreakEven.ceiling_hit, beats = the top
headcount, no flips."""
import dataclasses
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import FightResult, Group, ScanResult, Setup  # noqa: E402
from scripts.skilllab.scan import scan  # noqa: E402
from scripts.skilllab.breakeven import (  # noqa: E402
    BreakEven, Flip, SwapControl, find_break_even, flip_sides, swap_control)

SIZE = 16
PLANTED_BIAS = 0.1   # placeholder planted by the biased fake; not a tolerance


def _result(margin, outcome=None):
    return FightResult(outcome=outcome or ("side0" if margin > 0 else "side1"), margin=margin, strength_left=(1.0, 0.0), survivors=(1, 0),
                       heads=(1, 1), ticks=10, first_contact_tick=0, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


def _build(enemy_heads, swap):
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap})


class Recorder:
    """fight_fn logging (enemy, seed, swap); answers margin_of(enemy, seed, swap)."""

    def __init__(self, margin_of, outcome_of=None):
        self.margin_of = margin_of
        self.outcome_of = outcome_of or (lambda e, s, w: "side0" if self.margin_of(e, s, w) > 0 else "side1")
        self.calls = []

    def __call__(self, setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        assert setup.unit_types["swap"] == swap
        self.calls.append((enemy, seed, swap))
        return _result(self.margin_of(enemy, seed, swap), self.outcome_of(enemy, seed, swap))


def _curve(won):
    """Won heads give +0.5, every other headcount -0.5."""
    won = set(won)
    return lambda e, s, w: 0.5 if e in won else -0.5


def _find(won, lo=8, hi=13, reps=2, near=4, rounds=2, rec=None, **kw):
    rec = rec or Recorder(_curve(won))
    res = find_break_even(_build, SIZE, lo, hi, replicates=reps, near_replicates=near,
                          max_rounds=rounds, fight_fn=rec, **kw)
    return res, rec


def _grid(heads, seeds):
    return {(e, s, w) for e in heads for s in seeds for w in (False, True)}


# ---- flips -------------------------------------------------------------------------------------

def test_single_win_to_loss_flip():
    """W W W L L L: one win_to_loss flip; beats/loses_to are its before/after."""
    res, _ = _find({8, 9, 10})
    assert isinstance(res, BreakEven) and isinstance(res.scan, ScanResult)
    assert res.flips == [Flip(before=10, after=11, direction="win_to_loss")]
    assert res.multi_flip is False
    assert (res.beats, res.loses_to) == (10, 11)


def test_single_flip_agrees_with_plain_scan():
    """beats/loses_to equal scan.scan's (full_scan) for a one-flip curve."""
    plain = scan(_build, SIZE, 8, 13, replicates=2, fight_fn=Recorder(_curve({8, 9, 10})), full_scan=True)
    res, _ = _find({8, 9, 10})
    assert (res.beats, res.loses_to) == (plain.beats, plain.loses_to) == (10, 11)


def test_loss_to_win_flip_has_no_beats():
    """L L W W: one loss_to_win flip; beats and loses_to are None."""
    res, _ = _find({10, 11}, lo=8, hi=11)
    assert res.flips == [Flip(before=9, after=10, direction="loss_to_win")]
    assert res.multi_flip is False
    assert res.beats is None and res.loses_to is None


def test_two_flips_set_multi_flip_and_beats_from_first_win_to_loss():
    """W W L L W W: two flips in increasing order; beats from the first win_to_loss."""
    res, _ = _find({8, 9, 12, 13})
    assert res.flips == [Flip(9, 10, "win_to_loss"), Flip(11, 12, "loss_to_win")]
    assert res.multi_flip is True
    assert (res.beats, res.loses_to) == (9, 10)


def test_beats_ignores_an_earlier_loss_to_win_flip():
    """L W W L: the loss_to_win comes first, beats still reads the win_to_loss."""
    res, _ = _find({9, 10}, lo=8, hi=11)
    assert [f.direction for f in res.flips] == ["loss_to_win", "win_to_loss"]
    assert (res.beats, res.loses_to) == (10, 11)


@pytest.mark.parametrize("won,ceiling", [({8, 9, 10, 11, 12, 13}, True), (set(), False)])
def test_all_won_and_all_lost_have_no_flips(won, ceiling):
    """No flip: empty flips, no refinement, rounds 0, and only the scan's fights ran. Won everywhere is a ceiling hit (beats = the
    top headcount, never 'no break-even'); lost everywhere is beats None."""
    res, rec = _find(won)
    assert res.flips == [] and res.multi_flip is False
    assert res.ceiling_hit is ceiling and (res.beats, res.loses_to) == ((13, None) if ceiling else (None, None))
    assert res.refined == [] and res.rounds == 0
    assert len(rec.calls) == 6 * 2 * 2


# ---- refinement --------------------------------------------------------------------------------

def test_refinement_adds_exactly_the_adjacent_cells_extra_fights():
    """Flip (10,11): cells 10 and 11 get seeds 2..3 both orders; nothing else; no repeats."""
    res, rec = _find({8, 9, 10})
    assert len(rec.calls) == len(set(rec.calls)) == 6 * 4 + 2 * 4
    assert set(rec.calls) == _grid(range(8, 14), range(2)) | _grid((10, 11), (2, 3))
    assert res.refined == [10, 11]
    assert res.rounds == 1


def test_refinement_extra_fights_use_swap_outer_seed_inner_after_the_scan():
    """The scan's 24 calls come first; each refined cell then runs swap-outer, seed-inner over the new seeds."""
    _, rec = _find({8, 9, 10})
    extra = rec.calls[24:]
    assert sorted(extra) == sorted(_grid((10, 11), (2, 3)))
    for heads in (10, 11):
        mine = [c for c in extra if c[0] == heads]
        assert mine == [(heads, 2, False), (heads, 3, False), (heads, 2, True), (heads, 3, True)]


def test_refined_cells_keep_old_fights_and_recompute_mean():
    """Refined cells hold old + new fights (old objects kept); mean_margin is the mean over all of them."""
    first = Recorder(_curve({8, 9, 10}))
    scanned = scan(_build, SIZE, 8, 13, replicates=2, fight_fn=first, full_scan=True)
    margins = lambda e, s, w: 0.5 if e in (8, 9, 10) else -0.5
    rec = Recorder(lambda e, s, w: margins(e, s, w) + (0.1 if (e, s) == (10, 3) and w else 0.0))
    res, _ = _find({8, 9, 10}, rec=rec)
    by = {c.enemy_heads: c for c in res.scan.cells}
    assert [c.enemy_heads for c in res.scan.cells] == [8, 9, 10, 11, 12, 13]
    assert [len(by[e].fights) for e in range(8, 14)] == [4, 4, 8, 8, 4, 4]
    assert by[10].mean_margin == pytest.approx((8 * 0.5 + 0.1) / 8, abs=1e-12)
    assert scanned.cells[0].mean_margin == by[8].mean_margin


def test_refinement_can_move_the_break_even():
    """Positive control: cell 10 looks won on seeds 0-1 but the extra seeds sink it; the flip moves to (9,10)."""
    def margin(e, s, w):
        if e == 10:
            return 0.5 if s < 2 else -0.5
        return 0.5 if e <= 9 else -0.5
    res, _ = _find(None, rec=Recorder(margin), rounds=1)
    assert res.flips == [Flip(9, 10, "win_to_loss")]
    assert (res.beats, res.loses_to) == (9, 10)
    assert [c.won for c in res.scan.cells][:4] == [True, True, False, False]
    assert res.refined == [10, 11] and res.rounds == 1


def test_second_round_fires_when_positions_changed_and_never_repeats_a_fight():
    """The flip moved in round 1, so round 2 refines only the newly adjacent cell 9 (10 is already at 4)."""
    def margin(e, s, w):
        if e == 10:
            return 0.5 if s < 2 else -0.5
        return 0.5 if e <= 9 else -0.5
    res, rec = _find(None, rec=Recorder(margin), rounds=2)
    assert res.rounds == 2
    assert res.refined == [9, 10, 11]
    assert len(rec.calls) == len(set(rec.calls)) == 6 * 4 + 3 * 4
    assert set(rec.calls) == _grid(range(8, 14), range(2)) | _grid((9, 10, 11), (2, 3))
    assert res.flips == [Flip(9, 10, "win_to_loss")]


def test_max_rounds_caps_the_second_round():
    """Same moving curve with max_rounds=1: cell 9 is never refined."""
    def margin(e, s, w):
        if e == 10:
            return 0.5 if s < 2 else -0.5
        return 0.5 if e <= 9 else -0.5
    res, rec = _find(None, rec=Recorder(margin), rounds=1)
    assert 9 not in res.refined
    assert len(rec.calls) == 6 * 4 + 2 * 4


def test_unchanged_positions_stop_after_one_round():
    """Nothing moves after refinement: exactly one round ran even with max_rounds 2."""
    res, _ = _find({8, 9, 10}, rounds=2)
    assert res.rounds == 1
    assert res.flips == [Flip(10, 11, "win_to_loss")]


def test_max_rounds_zero_means_no_refinement():
    """max_rounds=0: only the scan's fights, refined empty, rounds 0, flips still reported."""
    res, rec = _find({8, 9, 10}, rounds=0)
    assert len(rec.calls) == 6 * 2 * 2
    assert res.refined == [] and res.rounds == 0
    assert res.flips == [Flip(10, 11, "win_to_loss")]


def test_near_replicates_equal_replicates_adds_no_fights():
    """near_replicates == replicates: no extra fights and nothing listed as refined."""
    res, rec = _find({8, 9, 10}, near=2)
    assert len(rec.calls) == 6 * 2 * 2
    assert res.refined == []


def test_multi_flip_refines_every_adjacent_cell_once():
    """Two flips (9,10) and (11,12): cells 9..12 refined once each, increasing; 8 and 13 untouched."""
    res, rec = _find({8, 9, 12, 13})
    assert res.refined == [9, 10, 11, 12]
    assert len(rec.calls) == len(set(rec.calls)) == 6 * 4 + 4 * 4
    assert set(rec.calls) == _grid(range(8, 14), range(2)) | _grid((9, 10, 11, 12), (2, 3))


def test_refinement_recomputes_won_with_the_every_fight_side0_rule():
    """An extra fight ending in a cap makes the refined cell a defect and not won even with a high mean margin."""
    outcome = lambda e, s, w: "cap" if (e, s, w) == (10, 3, True) else ("side0" if e <= 10 else "side1")
    res, _ = _find(None, rec=Recorder(_curve({8, 9, 10}), outcome), rounds=1)
    cells = {c.enemy_heads: c for c in res.scan.cells}
    assert cells[10].won is False and cells[10].defect is True and cells[10].mean_margin == pytest.approx(0.5)
    assert res.beats == 9


def test_find_break_even_takes_no_win_margin():
    import inspect
    assert "win_margin" not in inspect.signature(find_break_even).parameters


def test_deterministic_same_inputs_same_output():
    """Two runs on the same fake give equal flips, refined, rounds and call lists."""
    a, ra = _find({8, 9, 12, 13})
    b, rb = _find({8, 9, 12, 13})
    assert (a.flips, a.refined, a.rounds, a.beats) == (b.flips, b.refined, b.rounds, b.beats)
    assert ra.calls == rb.calls
    assert [c.mean_margin for c in a.scan.cells] == [c.mean_margin for c in b.scan.cells]


def test_no_triple_is_fought_twice_on_a_busy_curve():
    """A flip at every step: every (heads, seed, swap) triple is still fought at most once."""
    res, rec = _find({8, 10, 12}, near=5, rounds=3)
    assert len(rec.calls) == len(set(rec.calls))
    assert res.multi_flip is True


@pytest.mark.parametrize("kw", [{"near": 1}, {"rounds": -1}])
def test_validation_errors_run_no_fight(kw):
    """near_replicates < replicates and max_rounds < 0 raise ValueError before any fight."""
    rec = Recorder(_curve({8, 9, 10}))
    with pytest.raises(ValueError):
        _find({8, 9, 10}, rec=rec, **kw)
    assert rec.calls == []


def test_default_fight_fn_imports_lazily_and_calls_fight(monkeypatch):
    """fight_fn=None resolves scripts.skilllab.fight.fight at call time; importing breakeven loads no engine."""
    monkeypatch.delitem(sys.modules, "scripts.skilllab.fight", raising=False)
    monkeypatch.delitem(sys.modules, "scripts.skilllab.breakeven", raising=False)
    importlib.import_module("scripts.skilllab.breakeven")
    assert "scripts.skilllab.fight" not in sys.modules
    import scripts.skilllab.fight as fight_module
    seen = []

    def fake(setup, seed, swap):
        seen.append((setup.unit_types["enemy"], seed, swap))
        return _result(0.5 if setup.unit_types["enemy"] <= 9 else -0.5)

    monkeypatch.setattr(fight_module, "fight", fake)
    fresh = sys.modules["scripts.skilllab.breakeven"]
    res = fresh.find_break_even(_build, SIZE, 8, 11, replicates=1, near_replicates=2, max_rounds=1)
    assert (res.beats, res.loses_to) == (9, 10)
    assert len(seen) == len(set(seen))


# ---- flip_sides --------------------------------------------------------------------------------

def _two_groups():
    return Setup(
        groups=(Group(side=0, unit="Vanguard", count=16, formation="blob", x=-50.0, y=1.0,
                      facing_deg=0.0, layer=0, order="move", goal=(10.0, 2.0), params={"radius": 90}),
                Group(side=1, unit="Raider", count=12, formation="line", x=50.0, y=-1.0,
                      facing_deg=180.0, layer=1, order="attack_move", goal=None, params={"spacing": 30})),
        unit_types={"X": {"base": "Vanguard", "scale": {}, "set": {}}}, abilities=True, max_ticks=100,
        sample_every=2, trace=True, settings={"OM_TP_A": 1.5})


def test_flip_sides_swaps_only_sides():
    """Every Group.side becomes 1 - side; every other field, order, goal and Setup field is equal."""
    orig = _two_groups()
    flipped = flip_sides(orig)
    assert isinstance(flipped, Setup)
    assert [g.side for g in flipped.groups] == [1, 0]
    for a, b in zip(orig.groups, flipped.groups):
        assert dataclasses.replace(b, side=a.side) == a
    assert flipped.groups[0].goal == (10.0, 2.0) and flipped.groups[0].order == "move"
    assert dataclasses.replace(flipped, groups=orig.groups) == orig


def test_flip_sides_is_an_involution_and_leaves_the_input_alone():
    """Flipping twice returns an equal Setup; the input keeps its sides."""
    orig = _two_groups()
    assert flip_sides(flip_sides(orig)) == orig
    assert [g.side for g in orig.groups] == [0, 1]


# ---- swap_control ------------------------------------------------------------------------------

def _sided_build(enemy_heads, swap):
    g0 = Group(side=0, unit="Vanguard", count=SIZE, formation="blob", x=-50.0, y=0.0,
               facing_deg=0.0, layer=0, order="attack_move")
    g1 = Group(side=1, unit="Vanguard", count=enemy_heads, formation="blob", x=50.0, y=0.0,
               facing_deg=180.0, layer=0, order="attack_move")
    return Setup(groups=(g0, g1), unit_types={"enemy": enemy_heads, "swap": swap})


class SidedFake:
    """Antisymmetric margin in (side-0 count - side-1 count) plus an optional planted per-fight bias."""

    def __init__(self, bias=0.0):
        self.bias = bias
        self.calls = []   # (enemy, seed, swap, flipped)

    def __call__(self, setup, seed, swap):
        c0 = sum(g.count for g in setup.groups if g.side == 0)
        c1 = sum(g.count for g in setup.groups if g.side == 1)
        flipped = setup.groups[0].side == 1
        self.calls.append((setup.unit_types["enemy"], seed, swap, flipped))
        scale = 1 + 0.1 * seed + (0.05 if swap else 0.0)
        return _result((c0 - c1) * scale / 100.0 + self.bias / 2)


def test_swap_control_side_blind_instrument_has_zero_bias():
    """A side-blind fake: margin_flipped == -margin, bias 0, margin is the mean of the normal fights."""
    fake = SidedFake()
    res = swap_control(_sided_build, 12, 3, fight_fn=fake)
    assert isinstance(res, SwapControl) and res.enemy_heads == 12
    expected = sum(4 * (1 + 0.1 * s + (0.05 if w else 0.0)) / 100 for w in (False, True) for s in range(3)) / 6
    assert res.margin == pytest.approx(expected, abs=1e-12)
    assert res.margin_flipped == pytest.approx(-expected, abs=1e-12)
    assert res.bias == pytest.approx(0.0, abs=1e-12)


def test_swap_control_reads_a_planted_bias():
    """Positive control: a fake adding PLANTED_BIAS to side 0 minus side 1 in every fight reads bias 0.1."""
    res = swap_control(_sided_build, 12, 3, fight_fn=SidedFake(bias=PLANTED_BIAS))
    assert res.bias == pytest.approx(PLANTED_BIAS, abs=1e-12)
    assert res.margin + res.margin_flipped == pytest.approx(res.bias, abs=1e-12)


def test_swap_control_runs_both_sets_swap_outer_seed_inner():
    """4*replicates calls; each of the flipped and unflipped sets runs swap-outer, seed-inner over 0..replicates-1."""
    fake = SidedFake()
    swap_control(_sided_build, 9, 2, fight_fn=fake)
    assert len(fake.calls) == 8
    order = [(9, 0, False), (9, 1, False), (9, 0, True), (9, 1, True)]
    assert [c[:3] for c in fake.calls if c[3]] == order
    assert [c[:3] for c in fake.calls if not c[3]] == order


def test_swap_control_has_no_pass_fail_field():
    """The control reports numbers only: exactly enemy_heads, margin, margin_flipped, bias."""
    assert [f.name for f in dataclasses.fields(SwapControl)] == ["enemy_heads", "margin", "margin_flipped", "bias"]


def test_swap_control_default_fight_fn_is_lazy(monkeypatch):
    """fight_fn=None resolves scripts.skilllab.fight.fight at call time."""
    import scripts.skilllab.fight as fight_module
    fake = SidedFake()
    monkeypatch.setattr(fight_module, "fight", fake)
    res = swap_control(_sided_build, 12, 1)
    assert len(fake.calls) == 4 and res.bias == pytest.approx(0.0, abs=1e-12)
