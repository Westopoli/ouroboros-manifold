# spec: docs/northstar/research/layer_dynamics/README.md section 4 (conditions C0, C1, C2); every pass mark is Westley's and an input
"""evidence + conditions part one: firing advantage, FightPoint extraction, Thresholds (no defaults),
check_c0, check_c1, check_c2. All scans are built by hand; no engine, no compiler.
Every statistic is the harness writer's "unconfirmed definition", not a ruling; every Verdict.detail says so.
Threshold values below are placeholders for the tests only."""
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.conditions import MapFiring, check_c0, check_c1, check_c2  # noqa: E402
from scripts.skilllab.contract import CellResult, FightResult, ScanResult  # noqa: E402
from scripts.skilllab.evidence import FightPoint, Thresholds, Verdict, firing_advantage, points  # noqa: E402

# draft, not confirmed by Westley; placeholder for the test
DRAFT_UNCONFIRMED_C0_TOLERANCE_UNITS = 1
DRAFT_UNCONFIRMED_C1_MIN_FIRING_ADVANTAGE = 0.25
DRAFT_UNCONFIRMED_C1_MAP_SHARE = 0.5
DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT = 0.8
DRAFT_UNCONFIRMED_C2_OFF_TREND_MARGIN = 0.12
DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE = 0.25


def _t(**over):
    base = dict(
        c0_tolerance_units=DRAFT_UNCONFIRMED_C0_TOLERANCE_UNITS,
        c1_min_firing_advantage=DRAFT_UNCONFIRMED_C1_MIN_FIRING_ADVANTAGE,
        c1_map_share=DRAFT_UNCONFIRMED_C1_MAP_SHARE,
        c2_rank_agreement=DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT,
        c2_off_trend_margin=DRAFT_UNCONFIRMED_C2_OFF_TREND_MARGIN,
        c2_off_trend_share=DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE,
        c3_stack_gain=0.0, c4_max_share=0.0, c5_min_loss=0.0, c6_return_share=0.0, c6_map_share=0.0,
        c8_map_share=0.0, c7_ceiling_targets=(0.0, 0.0), c9_length_bounds_ticks=(0, 0),
        guard_tolerance_units=0)
    base.update(over)
    return Thresholds(**base)


def _fight(f0=1.0, f1=1.0, margin=0.0, ticks=100, outcome="side0"):
    return FightResult(outcome=outcome, margin=margin, strength_left=(0.0, 0.0), survivors=(0, 0),
                       heads=(0, 0), ticks=ticks, first_contact_tick=0, firing=[],
                       firing_unit_seconds=(f0, f1))


def _cell(heads, fights, won=True):
    return CellResult(enemy_heads=heads, fights=list(fights),
                      mean_margin=sum(f.margin for f in fights) / len(fights) if fights else 0.0, won=won)


def _scan(size, cells, beats=None, loses_to=None):
    return ScanResult(size=size, cells=list(cells), beats=beats, loses_to=loses_to)


def _pts_scan(xs, ys, size=5):
    """One cell holding one fight per (firing_adv, margin) pair; firing seconds chosen so firing_adv == x exactly (x in quarters)."""
    fights = [_fight(f0=1 + x, f1=1 - x, margin=y) for x, y in zip(xs, ys)]
    return _scan(size, [_cell(size, fights)])


def _mirror(size, lo, hi, loses_to, won_fn=None):
    """Cells lo..hi, won below size unless won_fn says otherwise; loses_to is set directly (C0 reads both independently)."""
    won_fn = won_fn or (lambda h: h < size)
    cells = [_cell(h, [_fight()], won=won_fn(h)) for h in range(lo, hi + 1)]
    beats = loses_to - 1 if loses_to is not None else None
    return _scan(size, cells, beats=beats, loses_to=loses_to)


# ---------- evidence ----------

def test_thresholds_have_no_defaults_and_are_frozen():
    """Every Thresholds field is required (no default, no factory) and the record is frozen."""
    for f in dataclasses.fields(Thresholds):
        assert f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING, f.name
    with pytest.raises(dataclasses.FrozenInstanceError):
        _t().c0_tolerance_units = 5


@pytest.mark.parametrize("name", [f.name for f in dataclasses.fields(Thresholds)])
def test_omitting_any_threshold_is_a_type_error(name):
    """Dropping any single field from the constructor call raises TypeError."""
    kwargs = {f.name: 0 for f in dataclasses.fields(Thresholds)}
    del kwargs[name]
    with pytest.raises(TypeError):
        Thresholds(**kwargs)


def test_thresholds_field_set():
    """The field names are exactly the contract's."""
    assert [f.name for f in dataclasses.fields(Thresholds)] == [
        "c0_tolerance_units", "c1_min_firing_advantage", "c1_map_share", "c2_rank_agreement",
        "c2_off_trend_margin", "c2_off_trend_share", "c3_stack_gain", "c4_max_share", "c5_min_loss",
        "c6_return_share", "c6_map_share", "c8_map_share", "c7_ceiling_targets", "c9_length_bounds_ticks",
        "guard_tolerance_units"]


def test_verdict_and_fightpoint_fields():
    """Verdict(code, holds, value, threshold, detail) and FightPoint(firing_adv, margin, ticks) are frozen records."""
    v = Verdict("C0", None, 1, 2, "d")
    assert (v.code, v.holds, v.value, v.threshold, v.detail) == ("C0", None, 1, 2, "d")
    p = FightPoint(0.5, 0.25, 7)
    assert (p.firing_adv, p.margin, p.ticks) == (0.5, 0.25, 7)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.margin = 1.0


@pytest.mark.parametrize("f0,f1,expect", [(3.0, 1.0, 0.5), (1.0, 3.0, -0.5), (2.0, 2.0, 0.0),
                                          (5.0, 0.0, 1.0), (0.0, 5.0, -1.0), (0.0, 0.0, 0.0)])
def test_firing_advantage_values(f0, f1, expect):
    """(f0 - f1) / (f0 + f1), in [-1, 1], 0.0 when both are zero."""
    assert firing_advantage(_fight(f0, f1)) == expect


def test_firing_advantage_antisymmetric():
    """Swapping the sides negates the advantage (positive and negative control in one)."""
    assert firing_advantage(_fight(7.0, 2.0)) == -firing_advantage(_fight(2.0, 7.0)) != 0.0


def test_points_every_fight_in_cell_then_fight_order():
    """points() lists FightPoint(firing_adv, margin, ticks) for every fight of every cell, cell order then fight order."""
    s = _scan(4, [_cell(3, [_fight(3, 1, 0.5, 10), _fight(1, 1, 0.0, 20)]), _cell(4, [_fight(1, 3, -0.5, 30)])])
    assert points(s) == [FightPoint(0.5, 0.5, 10), FightPoint(0.0, 0.0, 20), FightPoint(-0.5, -0.5, 30)]


def test_points_heads_filter_and_empty():
    """heads= keeps only the cell at that enemy_heads; a missing cell gives []."""
    s = _scan(4, [_cell(3, [_fight(3, 1, 0.5, 10)]), _cell(4, [_fight(1, 3, -0.5, 30)])])
    assert points(s, heads=4) == [FightPoint(-0.5, -0.5, 30)]
    assert points(s, heads=9) == []


# ---------- C0 ----------

def test_c0_positive_control():
    """Larger force wins, smaller does not, break-even at equal numbers: holds."""
    v = check_c0(_mirror(5, 2, 8, loses_to=6), 5, _t())
    assert (v.code, v.holds, v.value, v.threshold) == ("C0", True, 6, DRAFT_UNCONFIRMED_C0_TOLERANCE_UNITS)
    assert v.detail.startswith("unconfirmed definition:")


def test_c0_loses_to_far_from_size_fails():
    """Negative control: break-even at 9 for size 5 is outside tolerance 1."""
    v = check_c0(_mirror(5, 2, 12, loses_to=9), 5, _t())
    assert v.holds is False and v.value == 9


def test_c0_tolerance_boundary():
    """abs(loses_to - size) == tolerance holds; one more does not."""
    m = _mirror(5, 2, 12, loses_to=7)
    assert check_c0(m, 5, _t(c0_tolerance_units=2)).holds is True
    assert check_c0(m, 5, _t(c0_tolerance_units=1)).holds is False


def test_c0_tolerance_is_read_from_input():
    """A huge tolerance rescues a far break-even; zero tolerance fails an off-by-one."""
    assert check_c0(_mirror(5, 2, 12, loses_to=11), 5, _t(c0_tolerance_units=100)).holds is True
    assert check_c0(_mirror(5, 2, 12, loses_to=6), 5, _t(c0_tolerance_units=0)).holds is False


def test_c0_smaller_enemy_not_won_fails():
    """A cell below size that is not won fails C0 even when the break-even is at size."""
    m = _mirror(5, 2, 8, loses_to=6, won_fn=lambda h: h < 6 and h != 3)
    assert check_c0(m, 5, _t()).holds is False


def test_c0_larger_enemy_won_fails():
    """A cell above size that is won fails C0."""
    m = _mirror(5, 2, 8, loses_to=6, won_fn=lambda h: h < 6 or h == 8)
    assert check_c0(m, 5, _t()).holds is False


def test_c0_cell_at_size_is_unconstrained():
    """The cell at enemy_heads == size may be won or not."""
    for won in (True, False):
        m = _mirror(5, 2, 8, loses_to=5, won_fn=lambda h, w=won: (h < 5) or (h == 5 and w))
        assert check_c0(m, 5, _t(c0_tolerance_units=1)).holds is True


def test_c0_no_break_even_fails():
    """loses_to None means no break-even was found: holds False."""
    m = _scan(5, [_cell(h, [_fight()], won=h < 5) for h in range(2, 8)] , beats=None, loses_to=None)
    assert check_c0(m, 5, _t()).holds is False


def test_c0_scan_must_cover_size():
    """A scan that never reaches size gives holds False and a detail that says so."""
    v = check_c0(_mirror(5, 6, 9, loses_to=7, won_fn=lambda h: False), 5, _t())
    assert v.holds is False and "size" in v.detail and v.detail.startswith("unconfirmed definition:")


# ---------- C1 ----------

def _map(map_id, offers, noise_adv, skilled_advs, size=5, skill="S2"):
    """Mirror with fights at +-noise_adv (quarters); skilled fights with the given firing advantages."""
    def fights(advs):
        return [_fight(f0=1 + a, f1=1 - a) for a in advs]
    mirror = _scan(size, [_cell(size, fights([noise_adv, -noise_adv]))])
    skilled = _scan(size, [_cell(size, fights(skilled_advs))])
    return MapFiring(map_id, frozenset(offers), mirror, skilled, size)


def test_c1_positive_control():
    """Skilled mean advantage 0.75 beats noise 0.25 + 0.25: holds on the only offering map."""
    v = check_c1([_map("m1", {"S2"}, 0.25, [0.75, 0.75])], "S2", _t())
    assert (v.code, v.holds, v.value, v.threshold) == ("C1", True, 1.0, DRAFT_UNCONFIRMED_C1_MAP_SHARE)
    assert v.detail.startswith("unconfirmed definition:")


def test_c1_negative_control_equal_to_noise():
    """Skilled mean equals the mirror's noise: not above it, so the map does not hold."""
    v = check_c1([_map("m1", {"S2"}, 0.5, [0.5, 0.5])], "S2", _t())
    assert v.holds is False and v.value == 0.0


def test_c1_strict_boundary():
    """mean == noise + min is not enough (strict); a hair more is."""
    t = _t(c1_min_firing_advantage=0.25)
    assert check_c1([_map("m", {"S2"}, 0.5, [0.75])], "S2", t).value == 0.0
    assert check_c1([_map("m", {"S2"}, 0.5, [0.75, 0.875])], "S2", t).value == 1.0


def test_c1_uses_mean_of_skilled_fights():
    """One strong and one weak skilled fight average to 0.625: above 0.5 + 0.0, below 0.5 + 0.25."""
    m = [_map("m", {"S2"}, 0.5, [0.75, 0.5])]
    assert check_c1(m, "S2", _t(c1_min_firing_advantage=0.0)).value == 1.0
    assert check_c1(m, "S2", _t(c1_min_firing_advantage=0.25)).value == 0.0


def test_c1_noise_is_max_absolute_advantage_of_mirror():
    """Noise takes the largest |firing_adv| of the mirror fights, from either sign."""
    s = _scan(5, [_cell(5, [_fight(f0=1.25, f1=0.75), _fight(f0=0.5, f1=1.5)])])  # 0.25 and -0.5
    sk = _scan(5, [_cell(5, [_fight(f0=1.75, f1=0.25)])])  # 0.75
    mf = MapFiring("m", frozenset({"S2"}), s, sk, 5)
    assert check_c1([mf], "S2", _t(c1_min_firing_advantage=0.125)).holds is True   # 0.75 > 0.5 + 0.125
    assert check_c1([mf], "S2", _t(c1_min_firing_advantage=0.25)).holds is False   # 0.75 == 0.5 + 0.25, not >


def test_c1_noise_cell_is_the_one_at_size_and_missing_means_zero():
    """Only the mirror cell at enemy_heads == size counts; with no such cell noise is 0.0."""
    mirror = _scan(5, [_cell(4, [_fight(f0=2.0, f1=0.0)])])      # a wild cell elsewhere, ignored
    sk = _scan(5, [_cell(5, [_fight(f0=1.5, f1=0.5)])])           # 0.5
    mf = MapFiring("m", frozenset({"S2"}), mirror, sk, 5)
    assert check_c1([mf], "S2", _t(c1_min_firing_advantage=0.25)).holds is True


def test_c1_skilled_cell_is_the_one_at_size():
    """The skilled mean is taken at enemy_heads == size only."""
    mirror = _scan(5, [_cell(5, [_fight(f0=1.0, f1=1.0)])])
    sk = _scan(5, [_cell(4, [_fight(f0=2.0, f1=0.0)]), _cell(5, [_fight(f0=1.0, f1=1.0)])])
    assert check_c1([MapFiring("m", frozenset({"S2"}), mirror, sk, 5)], "S2", _t()).holds is False


def test_c1_only_offering_maps_count():
    """Maps whose offers lack the skill are ignored: 1 of 1 offering maps holds."""
    maps = [_map("a", {"S2"}, 0.25, [0.75]), _map("b", {"S1"}, 0.25, [0.0]), _map("c", set(), 0.25, [0.0])]
    v = check_c1(maps, "S2", _t(c1_map_share=1.0))
    assert v.value == 1.0 and v.holds is True


def test_c1_map_share_boundary():
    """2 of 4 offering maps hold: share 0.5 holds at c1_map_share 0.5, not at 0.75."""
    maps = [_map("a", {"S2"}, 0.25, [0.75]), _map("b", {"S2"}, 0.25, [0.75]),
            _map("c", {"S2"}, 0.25, [0.0]), _map("d", {"S2"}, 0.25, [0.0])]
    v = check_c1(maps, "S2", _t(c1_map_share=0.5))
    assert (v.value, v.holds) == (0.5, True)
    assert check_c1(maps, "S2", _t(c1_map_share=0.75)).holds is False


def test_c1_no_offering_map_is_reported_not_judged():
    """No map offers the play: holds None and the detail says so."""
    v = check_c1([_map("a", {"S1"}, 0.25, [0.75])], "S2", _t())
    assert v.holds is None and "no map offers the play" in v.detail
    assert check_c1([], "S2", _t()).holds is None


def test_c1_thresholds_come_from_the_input():
    """Changing c1_min_firing_advantage flips the verdict on identical data."""
    m = [_map("m", {"S2"}, 0.25, [0.75])]
    assert check_c1(m, "S2", _t(c1_min_firing_advantage=0.0)).holds is True
    assert check_c1(m, "S2", _t(c1_min_firing_advantage=0.5)).holds is False


# ---------- C2 ----------

def _c2(xs, ys, **over):
    return check_c2([_pts_scan(xs, ys)], _t(**over))


def test_c2_perfect_monotone_rho_one():
    """Strictly increasing margin with firing advantage: rho 1.0, no fight off trend, holds."""
    v = _c2([-0.5, -0.25, 0.25, 0.5], [-0.5, -0.25, 0.25, 0.5])
    assert v.code == "C2" and v.value == (pytest.approx(1.0), 0.0) and v.holds is True
    assert v.threshold == (DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT, DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE)
    assert v.detail.startswith("unconfirmed definition:")


def test_c2_reversed_rho_minus_one():
    """Negative control: margin falls as firing advantage rises: rho -1.0, does not hold."""
    v = _c2([-0.5, -0.25, 0.25, 0.5], [1.0, 0.5, 0.0, -0.5])
    assert v.value[0] == pytest.approx(-1.0) and v.holds is False


def test_c2_hand_computed_small_example():
    """x = 0, .125, .25, .375 with y = 0, .25, .125, .5: rho 0.8 (sum d^2 = 2); residuals .0125 .1 .1625 .075."""
    xs, ys = [0.0, 0.125, 0.25, 0.375], [0.0, 0.25, 0.125, 0.5]
    v = _c2(xs, ys, c2_off_trend_margin=0.15)
    assert v.value[0] == pytest.approx(0.8)
    assert v.value[1] == pytest.approx(0.25)   # only the residual 0.1625 exceeds 0.15


def test_c2_line_fit_by_hand():
    """Fitted line y = 0.0125 + 1.1 x, residuals .0125 .1 .1625 .075 (absolute); off-trend share follows the margin."""
    xs, ys = [0.0, 0.125, 0.25, 0.375], [0.0, 0.25, 0.125, 0.5]
    shares = {}
    for margin in (0.005, 0.0875, 0.125, 0.2):
        shares[margin] = _c2(xs, ys, c2_off_trend_margin=margin).value[1]
    assert shares == pytest.approx({0.005: 1.0, 0.0875: 0.5, 0.125: 0.25, 0.2: 0.0})


def test_c2_ties_use_average_ranks():
    """x = 0,0,.5,.5 against y = 0,.25,.5,.75: average ranks give rho 4 / sqrt(20)."""
    v = _c2([-0.5, -0.5, 0.5, 0.5], [0.0, 0.25, 0.5, 0.75])
    assert v.value[0] == pytest.approx(4 / math.sqrt(20))


def test_c2_ties_fit_through_group_means():
    """With two distinct x values the fitted line passes the group means: residuals are +-0.125."""
    xs, ys = [-0.5, -0.5, 0.5, 0.5], [0.0, 0.25, 0.5, 0.75]
    assert _c2(xs, ys, c2_off_trend_margin=0.1).value[1] == 1.0
    assert _c2(xs, ys, c2_off_trend_margin=0.15).value[1] == 0.0


def test_c2_fewer_than_three_points_rho_zero():
    """Two points, however monotone, give rho 0.0; so do none."""
    assert _c2([0.0, 0.5], [0.0, 0.5]).value[0] == 0.0
    assert check_c2([_scan(5, [_cell(5, [_fight()])])], _t()).value[0] == 0.0


def test_c2_constant_margin_column_rho_zero():
    """A constant margin column gives rho 0.0 and holds False at a positive agreement mark."""
    v = _c2([-0.5, 0.0, 0.5], [0.25, 0.25, 0.25])
    assert v.value[0] == 0.0 and v.holds is False


def test_c2_constant_firing_column_rho_zero_and_flat_fit():
    """Constant firing advantage: rho 0.0 and slope 0, so residuals are margin minus mean margin."""
    ys = [0.0, 0.25, 0.5, 0.75, 1.0]   # mean .5, residuals .5 .25 0 .25 .5
    v = _c2([0.25] * 5, ys, c2_off_trend_margin=0.3)
    assert v.value == (0.0, pytest.approx(0.4))


def test_c2_rank_agreement_boundary():
    """rho exactly at the mark holds (>=); just above the mark does not. Perfect rank agreement must compare as exactly 1.0, not 0.9999999999999999."""
    xs, ys = [-0.5, -0.25, 0.25, 0.5], [-0.5, -0.25, 0.25, 0.5]
    assert _c2(xs, ys, c2_rank_agreement=1.0).holds is True
    pert = [0.0, 0.25, 0.125, 0.5]
    xs2 = [0.0, 0.125, 0.25, 0.375]
    assert _c2(xs2, pert, c2_rank_agreement=0.79, c2_off_trend_margin=9.0).holds is True
    assert _c2(xs2, pert, c2_rank_agreement=0.81, c2_off_trend_margin=9.0).holds is False


def test_c2_off_share_boundary():
    """off_share == mark holds (<=); under the mark fails. Hand example has one of four fights off trend."""
    xs, ys = [0.0, 0.125, 0.25, 0.375], [0.0, 0.25, 0.125, 0.5]
    kw = dict(c2_rank_agreement=-1.0, c2_off_trend_margin=0.15)
    assert _c2(xs, ys, c2_off_trend_share=0.25, **kw).holds is True
    assert _c2(xs, ys, c2_off_trend_share=0.24, **kw).holds is False


def test_c2_both_conditions_needed():
    """Good rho with too many off-trend fights fails; good off-share with poor rho fails."""
    xs, ys = [-0.5, -0.25, 0.25, 0.5], [-0.5, -0.25, 0.25, 0.5]
    assert _c2(xs, ys, c2_off_trend_margin=0.01, c2_off_trend_share=0.0, c2_rank_agreement=0.5).holds is True
    xs2, ys2 = [0.0, 0.125, 0.25, 0.375], [0.0, 0.25, 0.125, 0.5]
    assert _c2(xs2, ys2, c2_off_trend_margin=0.001, c2_rank_agreement=0.5, c2_off_trend_share=0.5).holds is False
    assert _c2(xs2, ys2, c2_off_trend_margin=9.0, c2_rank_agreement=0.95, c2_off_trend_share=0.5).holds is False


def test_c2_pools_all_scans():
    """Points of every scan are pooled: two scans of two points each behave as one of four."""
    a = _pts_scan([-0.5, -0.25], [-0.5, -0.25])
    b = _pts_scan([0.25, 0.5], [0.25, 0.5], size=6)
    pooled = check_c2([a, b], _t())
    assert pooled.value == _c2([-0.5, -0.25, 0.25, 0.5], [-0.5, -0.25, 0.25, 0.5]).value
    assert check_c2([a], _t()).value[0] == 0.0   # two points alone: below three


def test_c2_deterministic():
    """Same input, same verdict."""
    xs, ys = [0.0, 0.125, 0.25, 0.375], [0.0, 0.25, 0.125, 0.5]
    assert _c2(xs, ys) == _c2(xs, ys)
