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
    """The opening window equals the whole-fight total here, so every test that does not speak of a basis reads the same on both
    (TD-LAB-REV2-L5-basis: the default basis is the window, decisions 29 item 2 and 31 C)."""
    return FightResult(outcome=outcome, margin=margin, strength_left=(0.0, 0.0), survivors=(0, 0),
                       heads=(0, 0), ticks=ticks, first_contact_tick=0, firing=[],
                       firing_unit_seconds=(f0, f1), firing_window=(f0, f1))


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


# =====================================================================================================================
# LAB-REV2-L5 additions. spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 ("C1 against both baselines; C2 per
# headcount cell and pooled, on the window and the whole fight; the agreement table"); ruling 5 (the opening window is the primary
# prediction form, whole-fight totals stay); ruling 3 (naive baselines, both ways); decisions 24, 25 (baseline roles).
#
# INTERFACE FIXED HERE (the builder reads it as the spec; QUESTIONs are readings for the Architect):
#   evidence.BASES = ("whole", "window");  evidence.DEFAULT_BASIS = "window"   (decision 29 item 2 for C2, decision 31 C for C1: the opening
#       window is the primary prediction form and the default; the whole fight is reported beside it)
#   evidence.firing_advantage(result, basis=DEFAULT_BASIS) -> float   (f0 - f1) / (f0 + f1), 0.0 when the sum is 0; "whole" reads
#       result.firing_unit_seconds, "window" reads result.firing_window; any other basis raises ValueError naming BASES
#   evidence.points(scan_result, heads=None, basis=DEFAULT_BASIS) -> list[FightPoint]   FightPoint.firing_adv on that basis
#   evidence.AGREEMENTS = ("both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a")
#   evidence.agreement_counts(agreements) -> dict   every word of AGREEMENTS as a key in that order, the count of each in the
#       iterable of str; a word outside AGREEMENTS raises ValueError
#   conditions.MapFiring gains `baselines: dict = {}` (LAST field, default empty dict): baseline role -> ScanResult of that naive
#       baseline at the same settings point (roles as the CSV baseline column: naive_attacker, naive_defender,
#       naive_defender_attacker_layer, naive_defender_play_layer)
#   conditions.check_c1(maps, skill, t, basis=DEFAULT_BASIS)    the MIRROR C1, kept (decision 31 B), now on the basis
#   conditions.check_c1_baselines(maps, skill, t, basis=DEFAULT_BASIS) -> list[Verdict]      one Verdict per baseline role present on
#       any map that offers the skill, roles sorted; code "C1@<role>"; the existing C1 formula with that role's scan in the place of
#       the mirror scan; a map without the role is not counted for it; no role anywhere -> []; detail starts "unconfirmed
#       definition:", names the role and the basis. The noise reference is the LARGEST |firing advantage| over that baseline's fights
#       at size (decision 31 C; not the mean, not the first), and the skilled mean must EXCEED it plus c1_min_firing_advantage
#       (strict >: equal is not enough). With no fights at size the reference is 0.0 (as check_c1 does for the mirror).
#   conditions.check_c2(scans, t, basis=DEFAULT_BASIS)           the detail names the basis
#   conditions.check_c8(maps, t, c1_skills=PROFILE_SKILLS, basis=DEFAULT_BASIS)   the C1 inside C8 reads that basis
#   conditions.c2_table(scans, t) -> list[dict]      keys scope ("pooled" | "cell"), enemy_heads (None for pooled), basis ("window" |
#       "whole"), fights (int), rho, off_trend_share (floats, the check_c2 statistics on that subset), holds (bool, rho >=
#       c2_rank_agreement AND off_trend_share <= c2_off_trend_share); order: basis window then whole; within a basis the pooled
#       row first, then one row per distinct enemy_heads ascending (a cell pools that headcount over all scans); [] without fights
# =====================================================================================================================
from scripts.skilllab import conditions, evidence  # noqa: E402   (module attributes: a missing L5 symbol fails the test, not the import)


def _wfight(w0, w1, f0=1.0, f1=1.0, margin=0.0, ticks=100):
    r = _fight(f0=f0, f1=f1, margin=margin, ticks=ticks)
    return dataclasses.replace(r, firing_window=(w0, w1))


def test_l5_bases_and_agreements_are_the_named_tuples():
    assert evidence.BASES == ("whole", "window") and evidence.DEFAULT_BASIS == "window"
    assert evidence.AGREEMENTS == ("both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a")


def test_l5_firing_advantage_reads_the_window_or_the_whole_fight():
    """Ruling 5, decision 29 item 2: the window is the primary form and the default, the whole-fight total is read beside it."""
    f = _wfight(w0=1.0, w1=3.0, f0=3.0, f1=1.0)          # whole +0.5, window -0.5
    assert firing_advantage(f) == -0.5 and firing_advantage(f, "window") == -0.5
    assert firing_advantage(f, "whole") == 0.5


def test_l5_firing_advantage_window_zero_total_is_zero_and_unknown_basis_raises():
    assert firing_advantage(_wfight(0.0, 0.0), "window") == 0.0          # positive control of the empty window: no division by zero
    with pytest.raises(ValueError) as e:
        firing_advantage(_wfight(1.0, 1.0), "weighted")
    assert "whole" in str(e.value) and "window" in str(e.value)


def test_l5_points_take_the_basis_through():
    sc = _scan(5, [_cell(5, [_wfight(1.0, 3.0, f0=3.0, f1=1.0, margin=0.25)])])
    assert [p.firing_adv for p in points(sc)] == [-0.5]                                    # the default basis is the window
    assert [p.firing_adv for p in points(sc, basis="whole")] == [0.5]
    assert [p.firing_adv for p in points(sc, basis="window")] == [-0.5]
    assert [p.firing_adv for p in points(sc, heads=5, basis="window")] == [-0.5] and points(sc, heads=9, basis="window") == []


def test_l5_agreement_counts_all_five_words_in_order_with_zeros():
    got = evidence.agreement_counts(["both_wrong", "both_right", "both_wrong", "n/a"])
    assert list(got) == list(evidence.AGREEMENTS)
    assert got == {"both_right": 1, "count_wrong_type_right": 0, "both_wrong": 2, "count_right_type_wrong": 0, "n/a": 1}
    assert sum(evidence.agreement_counts([]).values()) == 0           # empty input: all zeros, still five keys
    with pytest.raises(ValueError):
        evidence.agreement_counts(["both_right", "mostly_right"])      # negative control: an unknown word is a defect


# ---------- C1 against both baselines ----------

def _mapb(map_id, skilled_advs, baselines, size=5, skill="S2", mirror_adv=0.0):
    def fights(advs):
        return [_fight(f0=1 + a, f1=1 - a) for a in advs]
    mirror = _scan(size, [_cell(size, fights([mirror_adv]))])
    skilled = _scan(size, [_cell(size, fights(skilled_advs))])
    base = {role: _scan(size, [_cell(size, fights(advs))]) for role, advs in baselines.items()}
    return MapFiring(map_id, frozenset({skill}), mirror, skilled, size, base)


def test_l5_mapfiring_baselines_default_is_empty_and_last():
    mf = MapFiring("m", frozenset({"S2"}), _scan(5, []), _scan(5, []), 5)
    assert mf.baselines == {}
    assert dataclasses.fields(MapFiring)[-1].name == "baselines"


def test_l5_c1_against_both_baselines_positive_control_one_verdict_per_role_sorted():
    """Skilled 0.75 beats each baseline's noise (0.25) by more than 0.25: both verdicts hold."""
    m = _mapb("m", [0.75, 0.75], {"naive_defender": [0.25, -0.25], "naive_attacker": [0.25, -0.25]})
    vs = conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))
    assert [v.code for v in vs] == ["C1@naive_attacker", "C1@naive_defender"]
    assert [(v.holds, v.value) for v in vs] == [(True, 1.0), (True, 1.0)]
    assert all(v.detail.startswith("unconfirmed definition:") for v in vs)
    assert "naive_attacker" in vs[0].detail and "naive_defender" in vs[1].detail


def test_l5_c1_each_baseline_is_judged_on_its_own_negative_control():
    """The naive defender is a strong baseline (noise 0.625): the same skilled play holds against the attacker and not the defender."""
    m = _mapb("m", [0.75, 0.75], {"naive_attacker": [0.25], "naive_defender": [0.625]})
    vs = {v.code: v for v in conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))}
    assert vs["C1@naive_attacker"].holds is True and vs["C1@naive_defender"].holds is False
    assert vs["C1@naive_defender"].value == 0.0


def test_l5_c1_the_baseline_replaces_the_mirror_as_the_noise_reference():
    """QUESTION 1: a noisy mirror (0.9) does not matter when the baseline is quiet (0.0)."""
    m = _mapb("m", [0.75], {"naive_attacker": [0.0]}, mirror_adv=0.9)
    assert conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))[0].holds is True
    assert check_c1([m], "S2", _t(c1_map_share=1.0)).holds is False          # the unchanged mirror C1 still reads the mirror


def test_l5_c1_a_map_without_the_role_is_not_counted_for_it_and_only_offering_maps_count():
    a = _mapb("a", [0.75], {"naive_attacker": [0.0]})
    b = _mapb("b", [0.0], {})                                                  # no baselines: not counted for any role
    c = _mapb("c", [0.0], {"naive_attacker": [0.0]}, skill="S1")               # offers S1 only
    v = conditions.check_c1_baselines([a, b, c], "S2", _t(c1_map_share=1.0))[0]
    assert (v.code, v.value, v.holds) == ("C1@naive_attacker", 1.0, True)


def test_l5_c1_share_boundary_and_thresholds_come_from_the_input():
    maps = [_mapb("a", [0.75], {"naive_attacker": [0.0]}), _mapb("b", [0.0], {"naive_attacker": [0.0]})]
    assert conditions.check_c1_baselines(maps, "S2", _t(c1_map_share=0.5))[0].holds is True       # 1 of 2
    assert conditions.check_c1_baselines(maps, "S2", _t(c1_map_share=0.75))[0].holds is False
    assert conditions.check_c1_baselines(maps[:1], "S2", _t(c1_min_firing_advantage=0.9, c1_map_share=0.5))[0].holds is False


def test_l5_c1_no_baseline_on_any_map_gives_no_verdict_and_leaves_c1_alone():
    m = _map("m", {"S2"}, 0.25, [0.75])
    assert conditions.check_c1_baselines([m], "S2", _t()) == []
    assert check_c1([m], "S2", _t()).holds is True


# ---------- C2 on the window and the whole fight, per cell and pooled ----------

def _basis_scan():
    """Two cells (4 and 5), three fights each. Window advantage rises with the margin; the whole-fight advantage falls with it."""
    def fights(shift):
        out = []
        for w, m in ((-0.5, -0.5), (0.0, 0.0), (0.5, 0.5)):
            w0, w1 = 1 + w + shift, 1 - w - shift
            out.append(_wfight(w0, w1, f0=1 - w, f1=1 + w, margin=m))
        return out
    return _scan(5, [_cell(4, fights(0.0)), _cell(5, fights(0.0))])


def test_l5_check_c2_basis_window_and_whole_read_different_fights_of_the_same_scan():
    sc = _basis_scan()
    whole = check_c2([sc], _t(), basis="whole")
    window = check_c2([sc], _t(), basis="window")
    assert whole.value[0] < 0                                                             # falling with the margin
    assert window.value[0] > 0
    assert whole.holds is False and window.holds is True
    assert "whole" in whole.detail and "window" in window.detail
    assert check_c2([sc], _t()).value == window.value and check_c2([sc], _t()).holds is True       # the default basis is the window


def test_l5_check_c2_unknown_basis_raises():
    with pytest.raises(ValueError):
        check_c2([_basis_scan()], _t(), basis="weighted")


def test_l5_c2_table_has_pooled_then_cells_for_the_window_then_the_whole_fight():
    rows = conditions.c2_table([_basis_scan()], _t())
    assert [(r["basis"], r["scope"], r["enemy_heads"]) for r in rows] == [
        ("window", "pooled", None), ("window", "cell", 4), ("window", "cell", 5),
        ("whole", "pooled", None), ("whole", "cell", 4), ("whole", "cell", 5)]
    assert all(set(r) == {"scope", "enemy_heads", "basis", "fights", "rho", "off_trend_share", "holds"} for r in rows)
    assert [r["fights"] for r in rows] == [6, 3, 3, 6, 3, 3]


def test_l5_c2_table_cell_statistics_by_hand_and_holds_follows_the_thresholds():
    """Per cell the window rho is +1 (rank order equal) and the whole-fight rho is -1; holds uses the marks of the input."""
    rows = {(r["basis"], r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_basis_scan()], _t())}
    assert rows[("window", "cell", 4)]["rho"] == pytest.approx(1.0) and rows[("window", "cell", 4)]["holds"] is True
    assert rows[("whole", "cell", 4)]["rho"] == pytest.approx(-1.0) and rows[("whole", "cell", 4)]["holds"] is False
    strict = {(r["basis"], r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_basis_scan()], _t(c2_rank_agreement=1.5))}
    assert strict[("window", "cell", 4)]["holds"] is False


def test_l5_c2_table_pooled_row_equals_check_c2_on_the_same_basis():
    sc = _basis_scan()
    t = _t()
    rows = {(r["basis"], r["scope"]): r for r in conditions.c2_table([sc], t) if r["scope"] == "pooled"}
    for basis in ("window", "whole"):
        v = check_c2([sc], t, basis=basis)
        assert (rows[(basis, "pooled")]["rho"], rows[(basis, "pooled")]["off_trend_share"]) == pytest.approx(v.value)
        assert rows[(basis, "pooled")]["holds"] is v.holds


def test_l5_c2_table_pools_a_headcount_across_scans_and_is_empty_without_fights():
    a, b = _basis_scan(), _basis_scan()
    rows = {(r["basis"], r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([a, b], _t())}
    assert rows[("window", "cell", 4)]["fights"] == 6 and rows[("window", "pooled", None)]["fights"] == 12
    assert conditions.c2_table([], _t()) == [] and conditions.c2_table([_scan(5, [])], _t()) == []


def test_l5_c2_table_a_cell_under_three_fights_has_rho_zero_as_check_c2_does():
    sc = _scan(5, [_cell(4, [_wfight(1.5, 0.5, margin=0.5), _wfight(0.5, 1.5, margin=-0.5)])])
    r = [r for r in conditions.c2_table([sc], _t()) if r["scope"] == "cell" and r["basis"] == "window"][0]
    assert r["rho"] == 0.0 and r["fights"] == 2 and r["holds"] is False


def test_l5_c2_table_is_deterministic():
    assert conditions.c2_table([_basis_scan()], _t()) == conditions.c2_table([_basis_scan()], _t())


# ---------- decision 31 B and C: the mirror C1 is kept; C1 on the opening window, whole fight beside; the reference is the largest |advantage| ----------

def _wf(window_adv, whole_adv):
    """One fight whose opening-window advantage and whole-fight advantage are given (quarters and eighths: exact in binary)."""
    return _wfight(1 + window_adv, 1 - window_adv, f0=1 + whole_adv, f1=1 - whole_adv)


def _mapw(map_id, skilled, mirror, baselines, size=5, skill="S2"):
    """Each argument is a list of (window_adv, whole_adv) pairs, one fight each, all in the one cell at `size`."""
    scan = lambda pairs: _scan(size, [_cell(size, [_wf(*p) for p in pairs])])
    return MapFiring(map_id, frozenset({skill}), scan(mirror), scan(skilled), size, {r: scan(v) for r, v in baselines.items()})


def _same(*advs):
    return [(a, a) for a in advs]


@pytest.mark.parametrize("noise", [[0.9, 0.0], [0.0, 0.9], [-0.9, 0.0], [0.0, -0.9]])
def test_l5_c1_reference_is_the_largest_absolute_advantage_not_the_mean_the_first_or_the_last(noise):
    """Decision 31 C. Skilled mean 0.75, minimum 0.25. Baseline fights [0.9, 0.0] in either order and with either sign: the largest |adv|
    is 0.9 and 0.75 does not exceed 1.15. The mean (0.45), the first (0.9 or 0.0) or the last would let some of these pass."""
    m = _mapw("m", _same(0.75, 0.75), [(0.0, 0.0)], {"naive_defender": _same(*noise)})
    v = conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))[0]
    assert v.code == "C1@naive_defender" and v.holds is False and v.value == 0.0


def test_l5_c1_reference_positive_controls_a_quiet_baseline_holds():
    """Same skilled side, baseline [0.25, 0.0] (largest |adv| 0.25): 0.75 > 0.5 holds; [0.0, 0.0] holds."""
    for noise in ([0.25, 0.0], [0.0, 0.25], [0.0, 0.0]):
        m = _mapw("m", _same(0.75, 0.75), [(0.0, 0.0)], {"naive_defender": _same(*noise)})
        assert conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))[0].holds is True, noise


def test_l5_c1_the_comparison_is_strictly_greater_equal_does_not_hold():
    """Reference 0.5 + minimum 0.25 = 0.75: a skilled mean of exactly 0.75 does not exceed it; 0.8125 does. Mirror C1 and baseline C1 alike."""
    t = _t(c1_map_share=1.0)
    equal = _mapw("m", _same(0.75, 0.75), _same(0.5, 0.0), {"naive_attacker": _same(0.5, 0.0)})
    above = _mapw("m", _same(0.75, 0.875), _same(0.5, 0.0), {"naive_attacker": _same(0.5, 0.0)})
    assert conditions.check_c1_baselines([equal], "S2", t)[0].holds is False and check_c1([equal], "S2", t).holds is False
    assert conditions.check_c1_baselines([above], "S2", t)[0].holds is True and check_c1([above], "S2", t).holds is True


def test_l5_c1_with_no_fights_at_size_the_reference_is_zero_and_nothing_is_skilled():
    """A baseline scan without the cell at size has reference 0.0; a skilled scan without it cannot hold."""
    m = _mapw("m", _same(0.75), [(0.0, 0.0)], {"naive_attacker": []})
    m.baselines["naive_attacker"] = _scan(5, [])
    assert conditions.check_c1_baselines([m], "S2", _t(c1_map_share=1.0))[0].holds is True
    nobody = _mapw("m", [], [(0.0, 0.0)], {"naive_attacker": _same(0.0)})
    assert conditions.check_c1_baselines([nobody], "S2", _t(c1_map_share=1.0))[0].holds is False


def test_l5_c1_default_basis_is_the_opening_window_and_the_whole_fight_is_read_beside_it():
    """Skilled side: window advantage 0.75, whole-fight advantage 0.0, baseline quiet on both. The default (window) holds, basis "whole"
    does not; the mirror C1 and the baseline C1 agree on that."""
    m = _mapw("m", [(0.75, 0.0)], [(0.0, 0.0)], {"naive_attacker": [(0.0, 0.0)]})
    t = _t(c1_map_share=1.0)
    assert conditions.check_c1_baselines([m], "S2", t)[0].holds is True and check_c1([m], "S2", t).holds is True
    assert conditions.check_c1_baselines([m], "S2", t, basis="window")[0].holds is True
    assert conditions.check_c1_baselines([m], "S2", t, basis="whole")[0].holds is False and check_c1([m], "S2", t, basis="whole").holds is False


def test_l5_c1_whole_fight_can_hold_where_the_window_does_not():
    """The mirror image of the above: window 0.0, whole 0.75."""
    m = _mapw("m", [(0.0, 0.75)], [(0.0, 0.0)], {"naive_attacker": [(0.0, 0.0)]})
    t = _t(c1_map_share=1.0)
    assert conditions.check_c1_baselines([m], "S2", t)[0].holds is False and check_c1([m], "S2", t).holds is False
    assert conditions.check_c1_baselines([m], "S2", t, basis="whole")[0].holds is True and check_c1([m], "S2", t, basis="whole").holds is True


def test_l5_c1_the_noise_reference_is_read_on_the_same_basis_as_the_skilled_side():
    """Baseline fights are quiet in the whole fight (0.0) and loud in the window (0.9): the same skilled side (0.75 on both) fails on the
    window and holds on the whole fight, so the reference follows the basis."""
    m = _mapw("m", _same(0.75), [(0.9, 0.0)], {"naive_defender": [(0.9, 0.0)]})
    t = _t(c1_map_share=1.0)
    assert conditions.check_c1_baselines([m], "S2", t)[0].holds is False and check_c1([m], "S2", t).holds is False
    assert conditions.check_c1_baselines([m], "S2", t, basis="whole")[0].holds is True and check_c1([m], "S2", t, basis="whole").holds is True


def test_l5_c1_details_name_the_basis_and_an_unknown_basis_raises():
    m = _mapw("m", _same(0.75), [(0.0, 0.0)], {"naive_attacker": _same(0.0)})
    t = _t()
    assert "window" in conditions.check_c1_baselines([m], "S2", t)[0].detail
    assert "whole" in conditions.check_c1_baselines([m], "S2", t, basis="whole")[0].detail
    assert "window" in check_c1([m], "S2", t).detail
    with pytest.raises(ValueError):
        conditions.check_c1_baselines([m], "S2", t, basis="weighted")


def test_l5_the_mirror_c1_is_its_own_row_beside_the_baseline_rows_and_unchanged_by_them():
    """Decision 31 B: the mirror verdict keeps its code ("C1" from check_c1) and its formula; a baseline never replaces it."""
    m = _mapw("m", _same(0.75), _same(0.9, 0.0), {"naive_attacker": _same(0.0), "naive_defender": _same(0.0)})
    t = _t(c1_map_share=1.0)
    mirror = check_c1([m], "S2", t)
    baselines = conditions.check_c1_baselines([m], "S2", t)
    assert mirror.code == "C1" and mirror.holds is False                     # the loud mirror sinks it
    assert [v.code for v in baselines] == ["C1@naive_attacker", "C1@naive_defender"] and all(v.holds is True for v in baselines)


# ---------- decision 29 item 2: C2 default window; per-cell statistics; holds respects the off-trend share ----------

def _line_fights(xs, ys):
    """One fight per (x, y): window and whole-fight advantage x, margin y (x in halves and quarters, exact)."""
    return [_wfight(1 + x, 1 - x, f0=1 + x, f1=1 - x, margin=y) for x, y in zip(xs, ys)]


def _off_trend_oracle(xs, ys, margin):
    """The definition in check_c2's detail, independently: share of points farther than `margin` from the least-squares line."""
    from fractions import Fraction
    xs, ys = [Fraction(x) for x in xs], [Fraction(y) for y in ys]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else Fraction(0)
    return sum(1 for x, y in zip(xs, ys) if abs(y - (my + b * (x - mx))) > Fraction(margin)) / n


ON_X, ON_Y = [-0.5, 0.0, 0.5], [-0.5, 0.0, 0.5]                                     # a cell on its line: rank order equal, nothing off trend
OFF_X, OFF_Y = [-1.0, -0.5, 0.0, 0.5, 1.0], [-1.0, -0.99, -0.98, -0.97, 1.0]        # strictly increasing (rho 1) but bent: four of five off the line


def _cells_scan():
    return _scan(5, [_cell(4, _line_fights(ON_X, ON_Y)), _cell(5, _line_fights(OFF_X, OFF_Y))])


def test_l5_c2_table_off_trend_share_per_cell_and_pooled_are_the_check_c2_statistics():
    """The per-cell off_trend_share is asserted, not only rho: cell 4 is on its line (0.0), cell 5 has four of five points off (0.8), and
    the pooled row (eight points, one least-squares line) is a third number."""
    t = _t()
    rows = {(r["basis"], r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_cells_scan()], t)}
    margin = DRAFT_UNCONFIRMED_C2_OFF_TREND_MARGIN
    want4 = _off_trend_oracle(ON_X, ON_Y, margin)
    want5 = _off_trend_oracle(OFF_X, OFF_Y, margin)
    wantp = _off_trend_oracle(ON_X + OFF_X, ON_Y + OFF_Y, margin)
    assert (want4, want5) == (0.0, 0.8) and wantp not in (want4, want5)
    for basis in ("window", "whole"):
        assert rows[(basis, "cell", 4)]["off_trend_share"] == pytest.approx(want4)
        assert rows[(basis, "cell", 5)]["off_trend_share"] == pytest.approx(want5)
        assert rows[(basis, "pooled", None)]["off_trend_share"] == pytest.approx(wantp)
        assert rows[(basis, "pooled", None)]["off_trend_share"] == pytest.approx(check_c2([_cells_scan()], t, basis=basis).value[1])


def test_l5_c2_table_holds_needs_the_rank_agreement_and_the_off_trend_share_both():
    """Cell 5 has rho 1.0 (>= 0.8) and 80% of its points off trend (> the 25% mark): it does not hold. Cell 4 holds. Loosening only the
    off-trend mark makes cell 5 hold (positive control), tightening only the rank mark makes cell 4 fail (negative control)."""
    t = _t()
    rows = {(r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_cells_scan()], t) if r["basis"] == "window"}
    assert rows[("cell", 5)]["rho"] == pytest.approx(1.0) and rows[("cell", 5)]["holds"] is False
    assert rows[("cell", 4)]["holds"] is True
    loose = {(r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_cells_scan()], _t(c2_off_trend_share=0.9)) if r["basis"] == "window"}
    assert loose[("cell", 5)]["holds"] is True
    strict = {(r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([_cells_scan()], _t(c2_rank_agreement=1.5)) if r["basis"] == "window"}
    assert strict[("cell", 4)]["holds"] is False and strict[("cell", 5)]["holds"] is False


def test_l5_c2_table_a_pooled_verdict_can_differ_from_every_cell():
    """Per cell versus pooled: the two cells above give holds True and False; the pooled eight points give their own answer, the one
    check_c2 gives, and the table's pooled row says exactly that."""
    t = _t()
    sc = _cells_scan()
    rows = {(r["scope"], r["enemy_heads"]): r for r in conditions.c2_table([sc], t) if r["basis"] == "window"}
    pooled = check_c2([sc], t, basis="window")
    assert rows[("pooled", None)]["holds"] is pooled.holds
    assert rows[("pooled", None)]["off_trend_share"] != rows[("cell", 4)]["off_trend_share"] != rows[("cell", 5)]["off_trend_share"]
    assert rows[("pooled", None)]["fights"] == 8 and rows[("cell", 4)]["fights"] == 3 and rows[("cell", 5)]["fights"] == 5


def test_l5_check_c2_holds_respects_the_off_trend_share_on_the_default_basis():
    """A scan whose pooled rank agreement passes but whose off-trend share fails does not hold; the share mark alone decides."""
    sc = _scan(5, [_cell(5, _line_fights(OFF_X, OFF_Y))])
    assert check_c2([sc], _t()).holds is False and check_c2([sc], _t(c2_off_trend_share=0.9)).holds is True
