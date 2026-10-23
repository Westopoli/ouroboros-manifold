"""Part A of the K0 revision (SPEC.md section 14.5 items 1 to 4; README 4.2): headcount shares, win margin,
cost beside the headcount ratio, firing counts in every fight row, and the firing-count time series.

Red until the builders implement 14.5 (the old definition: ratio by cost, a win is margin > 0, has none of
these). Layout: (1) counts_for_heads, (2) FightResult firing fields, (3) win_margin, (4) cost_ratio and
value_cost, (5) firing columns on points, (6) rstar_windows, (7) the controls end to end.

Scripted tests replace `layerlab.skill.rstar.run_fights` (as test_skill_k0.py does), so no engine fights run;
sections (2), (6) and (7) run real tiny fights. Every symbol the revision adds is looked up inside the test
that needs it, so each test goes red on its own missing feature and not on an import.

Conventions these tests fix where SPEC 14.5 is silent (reported to the Architect):
  * `firing_adv` is `skilled_firing_per_head / naive_firing_per_head`, both being the means over seeds and
    both labels (a ratio of means, not a mean of per-fight ratios).
  * `cost_ratio` and `value_cost`: the naive force cost over the skilled force cost, the skilled side being
    label A when swap is False and label B when swap is True; interpolated linearly over ratio.
  * `rstar_windows` entries: `margin` is the SKILLED side's signed margin (positive: the skilled side won),
    `windows` has one dict per `window_ticks` ticks from tick 0 (the last one may be short, and its mean is over
    the ticks it has), `*_firing` is the mean over the window's ticks of the number of that side's units whose
    trace flag bit 4 (16) is set, `*_alive` the mean number alive. Entries are not ordered by the tests.
  * Firing is not bounded by the same window's alive mean (a unit's last shot is flagged on its death tick); it is
    bounded by the starting heads.
  * `last_win` and `first_loss` stay scanned ratios, taken against `win_margin`: a ratio is a win when its
    value is `> win_margin`, otherwise a loss.
"""
import importlib
import math
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from conftest import add_type, grp, make_scenario
from layerlab.run import run
from layerlab.skill.controls import advantage_build, advantage_control, mirror_control

costmod = importlib.import_module("layerlab.skill.cost")
fightmod = importlib.import_module("layerlab.skill.fight")
rstarmod = importlib.import_module("layerlab.skill.rstar")
fight, FightResult = fightmod.fight, fightmod.FightResult
RATIOS, rstar = rstarmod.RATIOS, rstarmod.rstar


# =========================================================================== (1) counts_for_heads


def _heads(shares, n, scn=None):
    return costmod.counts_for_heads(shares, n, scn if scn is not None else make_scenario())


def test_heads_half_quarter_quarter_of_eight():
    """SPEC 14.5 (1): shares raider .5, bastion .25, warden .25 at n = 8 heads give exactly 4 / 2 / 2."""
    out = _heads({"raider": 0.5, "bastion": 0.25, "warden": 0.25}, 8)
    assert out == {"raider": 4, "bastion": 2, "warden": 2}


def test_heads_largest_remainder_ties_go_to_the_type_listed_first():
    """SPEC 14.5 (1): n = 10 gives ideal 5 / 2.5 / 2.5, one head left over, equal remainders: the type listed
    first takes it; listing the two in the other order moves it."""
    assert _heads({"raider": 0.5, "bastion": 0.25, "warden": 0.25}, 10) == {"raider": 5, "bastion": 3, "warden": 2}
    assert _heads({"raider": 0.5, "warden": 0.25, "bastion": 0.25}, 10) == {"raider": 5, "warden": 3, "bastion": 2}
    four = {"raider": 0.25, "interceptor": 0.25, "vanguard": 0.25, "warden": 0.25}
    assert _heads(four, 10) == {"raider": 3, "interceptor": 3, "vanguard": 2, "warden": 2}


def test_heads_hand_computed_remainder():
    """SPEC 14.5 (1): .5 / .375 / .125 of 8 heads: ideal 4 / 3 / 1, exact, no rounding needed; of 10: ideal
    5 / 3.75 / 1.25, floors 5 / 3 / 1, the largest remainder (.75) takes the spare head: 5 / 4 / 1."""
    shares = {"raider": 0.5, "bastion": 0.375, "warden": 0.125}
    assert _heads(shares, 8) == {"raider": 4, "bastion": 3, "warden": 1}
    assert _heads(shares, 10) == {"raider": 5, "bastion": 4, "warden": 1}


def test_heads_do_not_depend_on_cost():
    """SPEC 14.5 (1): shares are shares of HEADS, whatever the types cost: half raider (90) and half bastion
    (131) of 10 heads is 5 and 5 (by cost it would not be)."""
    assert _heads({"raider": 0.5, "bastion": 0.5}, 10) == {"raider": 5, "bastion": 5}


def test_heads_positive_share_gets_at_least_one_when_n_covers_the_types():
    """SPEC 14.5 (1): a type with a positive share gets at least 1 head when n >= the number of such types
    (plain rounding would give the small shares 0), and the total stays n. Negative twin: a zero share gets none."""
    assert _heads({"raider": 0.97, "bastion": 0.03}, 8) == {"raider": 7, "bastion": 1}
    assert _heads({"raider": 0.8, "bastion": 0.1, "warden": 0.1}, 3) == {"raider": 1, "bastion": 1, "warden": 1}
    out = _heads({"raider": 1.0, "bastion": 0.0}, 5)
    assert out.get("bastion", 0) == 0 and out["raider"] == 5


def test_heads_fewer_heads_than_types_still_sum_to_n():
    """SPEC 14.5 (1): the at-least-one rule only applies when n >= the number of types; with 2 heads and 3
    types the total is still exactly 2."""
    out = _heads({"raider": 0.8, "bastion": 0.1, "warden": 0.1}, 2)
    assert sum(out.values()) == 2 and out.get("raider", 0) >= 1


def test_heads_empty_for_no_heads_or_no_shares():
    """SPEC 14.5 (1): n <= 0 or no shares give {}."""
    shares = {"raider": 0.5, "bastion": 0.5}
    assert _heads(shares, 0) == {} and _heads(shares, -3) == {}
    assert _heads({}, 8) == {} and _heads({}, 0) == {}


def test_heads_sum_to_n_and_are_deterministic():
    """SPEC 14.5 (1): for every n the counts sum to n; four equal shares stay within one head of each other
    (and each type has at least one head from n = 4); the same call twice gives the same dict."""
    four = {"raider": 0.25, "interceptor": 0.25, "vanguard": 0.25, "warden": 0.25}
    for n in range(1, 41):
        out = _heads(four, n)
        assert sum(out.values()) == n, (n, out)
        got = [out.get(t, 0) for t in four]
        assert max(got) - min(got) <= 1, (n, out)
        if n >= 4:
            assert min(got) >= 1, (n, out)
        assert _heads(four, n) == _heads(dict(four), n)


# =========================================================================== (2) FightResult firing fields


def _close(a=3, b=3):
    """A small fast fight: a raiders against b raiders, 800 apart, both attack-move at each other."""
    return make_scenario([
        grp("A", "raider", 1000, 1000, 3, count=a, order="attack_move", goal=[1800.0, 1000.0], spacing=50.0),
        grp("B", "raider", 1800, 1000, 3, count=b, order="attack_move", goal=[1000.0, 1000.0], spacing=50.0,
            facing=180.0),
    ])


def test_fight_result_carries_alive_firing_and_heads():
    """SPEC 14.5 (3): FightResult gains alive_ticks and firing_ticks (the result's own 2-tuples) and heads (the
    starting headcount per label); firing_per_head(label) = firing_ticks[label] / heads[label]."""
    scn = _close(3, 3)
    res = run(scn, seed=0)
    fr = fight(scn, 0)
    assert fr.heads == (3, 3)
    assert tuple(fr.alive_ticks) == tuple(res.alive_ticks) and len(fr.alive_ticks) == 2
    assert tuple(fr.firing_ticks) == tuple(res.firing_ticks) and len(fr.firing_ticks) == 2
    assert fr.firing_ticks[0] > 0 and fr.firing_ticks[1] > 0          # a real fight: both sides fired
    assert fr.firing_per_head(0) == fr.firing_ticks[0] / 3
    assert fr.firing_per_head(1) == fr.firing_ticks[1] / 3


def test_fight_heads_are_per_label_and_firing_per_head_divides_by_them():
    """SPEC 14.5 (3): unequal sides: heads (2, 4); each label's firing per head divides by its own heads."""
    scn = _close(2, 4)
    fr = fight(scn, 0)
    assert fr.heads == (2, 4)
    assert fr.firing_per_head(0) == fr.firing_ticks[0] / 2
    assert fr.firing_per_head(1) == fr.firing_ticks[1] / 4


def test_firing_per_head_is_zero_for_no_heads():
    """SPEC 14.5 (3): 0.0 for a label with no heads (no division by zero), whatever its firing_ticks hold."""
    fr = FightResult(margin=0.0, raw_margin=0.0, outcome="stalemate", ticks=10, first_contact_tick=-1,
                     contact=False, survivors=(0, 3), alive_ticks=(0, 30), firing_ticks=(5, 6), heads=(0, 3))
    assert fr.firing_per_head(0) == 0.0
    assert fr.firing_per_head(1) == 2.0


# =========================================================================== scripted runner for (3) to (5)


class FakeFight:
    """What a scripted run_fights returns: every field a FightResult carries, margin already effective."""

    def __init__(self, margin, outcome="win_A", contact=True, alive=(100, 100), firing=(50, 50), heads=(8, 8)):
        self.margin, self.raw_margin, self.outcome = margin, margin, outcome
        self.ticks, self.contact, self.survivors, self.error = 100, contact, (1, 1), None
        self.first_contact_tick = 50 if contact else -1
        self.alive_ticks, self.firing_ticks, self.heads = tuple(alive), tuple(firing), tuple(heads)

    def firing_per_head(self, label):
        return self.firing_ticks[label] / self.heads[label] if self.heads[label] else 0.0


class Scripted:
    """A scripted `run_fights` and a `build` that makes REAL scenario dicts with groups.

    skilled(ratio, seed, swap) -> the SKILLED side's signed margin (the fight's own A-minus-B margin is that on
    label A and its negative on label B). `outcome(ratio, seed, swap)` optional. `data(ratio, seed, swap)` returns
    a dict with `skilled_firing`, `skilled_alive`, `naive_firing`, `naive_alive`, `skilled_heads`, `naive_heads`;
    each is put on the label the skilled side holds. `naive_cost(ratio)` is the cost of the single naive unit;
    the skilled force is 4 raiders (cost 360)."""

    def __init__(self, monkeypatch, skilled, outcome=None, data=None, naive_cost=None):
        self.skilled, self.outcome, self.data = skilled, outcome, data
        self.naive_cost = naive_cost or (lambda ratio: 360.0 * ratio)
        self.built = {}                  # id(scenario) -> (scenario, ratio, swap)
        self.seen = []
        monkeypatch.setattr(rstarmod, "run_fights", self.run_fights)

    def build(self, ratio, swap):
        sk, nv = ("B", "A") if swap else ("A", "B")
        scn = make_scenario([grp(sk, "raider", 1000, 1000, 3, count=4), grp(nv, "naive", 3000, 1000, 3, count=1)])
        add_type(scn, "naive", "raider", cost=self.naive_cost(ratio))
        scn["groups"].sort(key=lambda g: g["side"])
        self.built[id(scn)] = (scn, ratio, swap)
        return scn

    def run_fights(self, jobs, *args, **kwargs):
        out = []
        for scn, seed in jobs:
            keep, r, sw = self.built[id(scn)]
            assert keep is scn
            self.seen.append((r, sw, seed))
            s = self.skilled(r, seed, sw)
            m = -s if sw else s
            oc = self.outcome(r, seed, sw) if self.outcome else ("win_A" if m > 0 else "win_B")
            eff = 0.0 if oc in ("stalemate", "cap", "mutual") else m
            kw = {}
            if self.data:
                d = self.data(r, seed, sw)
                pair = lambda s_, n_: (n_, s_) if sw else (s_, n_)   # noqa: E731  skilled side on its own label
                kw = {"alive": pair(d["skilled_alive"], d["naive_alive"]),
                      "firing": pair(d["skilled_firing"], d["naive_firing"]),
                      "heads": pair(d["skilled_heads"], d["naive_heads"])}
            out.append(FakeFight(eff, outcome=oc, **kw))
        return out

    def run(self, **kw):
        return rstar(self.build, **kw)


def line(r, lo=0.5, hi=-0.5):
    """A skilled-side margin falling linearly from +0.5 at ratio 0.5 to -0.5 at ratio 8: zero at 4.25."""
    return lo + (hi - lo) * (r - 0.5) / 7.5


def base(r):
    """Linear through 0 at ratio 2.5, clipped to +-0.8."""
    return max(-0.8, min(0.8, (2.5 - r) * 0.3))


# =========================================================================== (3) win_margin


def test_win_margin_moves_the_break_even_to_the_threshold_crossing(monkeypatch):
    """SPEC 14.5 (2): the break-even is where the fitted curve crosses +win_margin. On a line from +0.5 (0.5)
    to -0.5 (8): 0 at 4.25, 0.2 at 2.75, 0.02 at 4.1. win_margin=0.2 is strictly earlier than win_margin=0."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: line(r))
    zero = sc.run(refine=4, win_margin=0.0)
    two = sc.run(refine=4, win_margin=0.2)
    assert zero.value == pytest.approx(4.25, abs=1e-6)
    assert two.value == pytest.approx(2.75, abs=1e-6)
    assert two.value < zero.value
    assert two.valid is True and two.above_scan is False and two.below_scan is False


def test_win_margin_default_is_0_02(monkeypatch):
    """SPEC 14.5 (2): rstar(..., win_margin=0.02): the default crosses at 4.1 and equals an explicit 0.02."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: line(r))
    default = sc.run(refine=4)
    assert default.value == pytest.approx(4.1, abs=1e-6)
    assert default == sc.run(refine=4, win_margin=0.02)


def test_win_margin_sets_last_win_and_first_loss(monkeypatch):
    """SPEC 14.5 (2): last_win and first_loss follow `value > win_margin`: at win_margin 0.2 the curve is
    0.2467 at 2.4 (a win) and 0.18 at 2.9 (not a win), though still positive. At win_margin 0 they are 4.2 and 5.0."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: line(r))
    two = sc.run(refine=4, win_margin=0.2)
    assert (two.last_win, two.first_loss) == (2.4, 2.9)
    zero = sc.run(refine=4, win_margin=0.0)
    assert (zero.last_win, zero.first_loss) == (4.2, 5.0)


def test_win_margin_refines_inside_the_threshold_bracket(monkeypatch):
    """SPEC 14.5 (2): the refinement bracket uses the same threshold: at win_margin 0.2 the 4 extra points all
    lie strictly inside (2.4, 2.9), not around the zero crossing at 4.25."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: line(r))
    res = sc.run(refine=4, win_margin=0.2)
    new = [p["ratio"] for p in res.points if p["ratio"] not in RATIOS]
    assert len(new) == 4 and all(2.4 < r < 2.9 for r in new), new


def test_margin_between_zero_and_win_margin_is_below_scan(monkeypatch):
    """SPEC 14.5 (2): a skilled side that leads by 0.1 at every ratio, a 'win' with a margin under 0.2, never
    beats the force: below_scan, no value, no last_win. Negative twin: with win_margin 0 the same curve
    is above_scan, and with win_margin 0.05 too."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.1)
    res = sc.run(refine=4, win_margin=0.2)
    assert res.value is None and res.below_scan is True and res.above_scan is False
    assert res.last_win is None and res.first_loss == 0.5 and res.valid is True
    for wm in (0.0, 0.05):
        res = sc.run(refine=4, win_margin=wm)
        assert res.value is None and res.above_scan is True and res.below_scan is False, wm
        assert res.last_win == 8.0 and res.first_loss is None


def test_default_win_margin_rejects_a_sliver_of_a_win(monkeypatch):
    """SPEC 14.5 (2): +0.015 at every ratio is under the default 0.02: below_scan with no argument given,
    above_scan with win_margin=0.01."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.015)
    res = sc.run(refine=4)
    assert res.below_scan is True and res.above_scan is False and res.value is None
    assert sc.run(refine=4, win_margin=0.01).above_scan is True


def test_curve_above_win_margin_everywhere_is_above_scan(monkeypatch):
    """SPEC 14.5 (2): every ratio above the threshold: above_scan, value None, no refine points (positive
    twin of the previous test, at the 0.2 threshold)."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.5)
    res = sc.run(refine=4, win_margin=0.2)
    assert res.value is None and res.above_scan is True and res.below_scan is False
    assert [p["ratio"] for p in res.points] == list(RATIOS)


def test_stalemate_never_counts_as_a_win_even_for_win_margin_zero(monkeypatch):
    """SPEC 14.5 (2): a stalemate has margin 0 and `0 > 0` is false: a scan of nothing but stalemates is
    below_scan at win_margin 0 (value > win_margin is strict) and at the default."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.5, outcome=lambda r, seed, sw: "stalemate")
    for kw in ({"win_margin": 0.0}, {}):
        res = sc.run(refine=4, **kw)
        assert res.below_scan is True and res.above_scan is False and res.value is None, kw
        assert all(p["value"] == 0.0 and p["n_stalemate"] == 4 for p in res.points)


def test_stalemates_above_ratio_2_4_cap_the_curve_at_zero_for_win_margin_zero(monkeypatch):
    """SPEC 14.5 (2): from ratio 2.4 up every fight is a stalemate (margin 0): at win_margin=0 the crossing is
    the point where the curve reaches 0, 2.4, and no ratio from 2.4 up is a last win."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r) if r < 2.4 - 1e-9 else 0.0,
                  outcome=lambda r, seed, sw: "stalemate" if r >= 2.4 - 1e-9 else "win_A")
    res = sc.run(refine=4, win_margin=0.0)
    assert res.value == pytest.approx(2.4, abs=1e-6)
    assert res.above_scan is False and res.below_scan is False and res.last_win < 2.4


def test_mutual_elimination_is_zero_and_never_a_win(monkeypatch):
    """SPEC 14.5 (2): mutual elimination has margin 0: a scan of mutual eliminations has value 0.0 at every
    point and is below_scan at win_margin 0 and at the default."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.0, outcome=lambda r, seed, sw: "mutual")
    for kw in ({"win_margin": 0.0}, {}):
        res = sc.run(refine=4, **kw)
        assert res.below_scan is True and res.value is None, kw
        assert all(p["value"] == 0.0 for p in res.points)


def test_win_margin_is_an_argument_of_both_controls():
    """SPEC 14.5 (2): `win_margin` is also an argument of mirror_control and advantage_control (the
    signature carries it; a call with it works)."""
    import inspect
    for fn in (mirror_control, advantage_control):
        assert "win_margin" in inspect.signature(fn).parameters, fn.__name__


# =========================================================================== (4) cost_ratio and value_cost


def test_every_point_carries_the_cost_ratio_for_both_labels(monkeypatch):
    """SPEC 14.5 (1): each point carries cost_ratio = naive force cost / skilled force cost, whichever label
    the skilled side holds. The skilled force is 4 raiders (360); the naive unit costs 360 * ratio ** 2, so the
    cost ratio is ratio ** 2 (not the headcount ratio)."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), naive_cost=lambda r: 360.0 * r * r)
    res = sc.run(refine=4)
    assert {sw for _, sw, _ in sc.seen} == {False, True}
    for p in res.points:
        assert p["cost_ratio"] == pytest.approx(p["ratio"] ** 2, rel=1e-9), p


def test_value_cost_is_the_cost_ratio_interpolated_at_value(monkeypatch):
    """SPEC 14.5 (1): value_cost is the (linear) interpolation of cost_ratio over ratio at `value`. With
    cost_ratio = ratio ** 2 the interpolation between the neighbouring points is not ratio ** 2 exactly,
    so a solver that squared the value would miss it."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), naive_cost=lambda r: 360.0 * r * r)
    res = sc.run(refine=0)
    xs = [p["ratio"] for p in res.points]
    ys = [p["cost_ratio"] for p in res.points]
    assert res.value is not None
    assert res.value_cost == pytest.approx(float(np.interp(res.value, xs, ys)), rel=1e-9)
    assert res.value_cost != pytest.approx(res.value ** 2, rel=1e-6)


def test_value_cost_is_none_when_there_is_no_value(monkeypatch):
    """SPEC 14.5 (1): `None` when value is None (above the scan and below it), and the points still carry cost_ratio."""
    for skilled in (0.5, -0.5):
        sc = Scripted(monkeypatch, lambda r, seed, sw, s=skilled: s)
        res = sc.run(refine=4)
        assert res.value is None and res.value_cost is None
        assert all("cost_ratio" in p for p in res.points)


# =========================================================================== (5) firing columns on points


def _fire_data(r, seed, sw):
    """Distinct numbers per ratio, seed and label, so a wrong label, a wrong mean or a wrong per-head divisor shows."""
    return {"skilled_firing": 40.0 + 10.0 * r + 4.0 * seed + (7.0 if sw else 0.0),
            "skilled_alive": 100.0 + 5.0 * seed + (3.0 if sw else 0.0),
            "naive_firing": 30.0 + 3.0 * r + 6.0 * seed + (2.0 if sw else 0.0),
            "naive_alive": 80.0 - 2.0 * r + (1.0 if sw else 0.0),
            "skilled_heads": 8, "naive_heads": max(1, round(8 * r))}


def _expect(r, seeds=(0, 1)):
    """The test's own means over seeds and both labels."""
    runs = [_fire_data(r, s, sw) for s in seeds for sw in (False, True)]
    m = lambda f: sum(f(d) for d in runs) / len(runs)    # noqa: E731
    out = {"skilled_firing_per_head": m(lambda d: d["skilled_firing"] / d["skilled_heads"]),
           "naive_firing_per_head": m(lambda d: d["naive_firing"] / d["naive_heads"]),
           "skilled_alive_ticks": m(lambda d: d["skilled_alive"]),
           "naive_alive_ticks": m(lambda d: d["naive_alive"])}
    out["firing_adv"] = out["skilled_firing_per_head"] / out["naive_firing_per_head"]
    return out


def test_points_carry_firing_per_head_alive_ticks_and_firing_adv(monkeypatch):
    """SPEC 14.5 (3): every point has skilled_firing_per_head and naive_firing_per_head (means over seeds and
    both labels, the skilled side's number from whichever label it holds), skilled_alive_ticks and
    naive_alive_ticks (same means), and firing_adv, the ratio of the two firing means."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=_fire_data)
    res = sc.run(refine=4)
    for p in res.points:
        want = _expect(p["ratio"])
        for key, v in want.items():
            assert p[key] == pytest.approx(v, rel=1e-9), (p["ratio"], key)


def test_firing_adv_is_a_ratio_of_means_not_a_mean_of_ratios(monkeypatch):
    """SPEC 14.5 (3): 'the ratio of the two means'. With firing that varies by seed and label, the mean of the
    per-fight ratios differs from the ratio of the means; the point carries the latter."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=_fire_data)
    res = sc.run(refine=0)
    p = next(p for p in res.points if p["ratio"] == 1.0)
    runs = [_fire_data(1.0, s, sw) for s in (0, 1) for sw in (False, True)]
    mean_of_ratios = sum((d["skilled_firing"] / d["skilled_heads"]) / (d["naive_firing"] / d["naive_heads"])
                         for d in runs) / len(runs)
    assert p["firing_adv"] != pytest.approx(mean_of_ratios, rel=1e-6)
    assert p["firing_adv"] == pytest.approx(p["skilled_firing_per_head"] / p["naive_firing_per_head"], rel=1e-12)


def test_firing_columns_follow_the_skilled_side_not_the_label(monkeypatch):
    """SPEC 14.5 (3): negative twin of the label rule: when the skilled side fires 100 and the naive side 10
    per head, firing_adv is 10 whichever label holds the skilled side (a solver that read label A always
    would average 100 and 10 into the same number for both and give 1.0)."""
    flat = lambda r, seed, sw: {"skilled_firing": 800.0, "skilled_alive": 120.0, "naive_firing": 80.0,   # noqa: E731
                                "naive_alive": 90.0, "skilled_heads": 8, "naive_heads": 8}
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=flat)
    res = sc.run(refine=0)
    for p in res.points:
        assert p["skilled_firing_per_head"] == pytest.approx(100.0) and p["naive_firing_per_head"] == pytest.approx(10.0)
        assert p["skilled_alive_ticks"] == pytest.approx(120.0) and p["naive_alive_ticks"] == pytest.approx(90.0)
        assert p["firing_adv"] == pytest.approx(10.0)


def test_firing_adv_equal_is_the_ratio_one_point(monkeypatch):
    """SPEC 14.5 (3): firing_adv_equal is the firing_adv of the point at ratio 1.0 (always in the scan)."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=_fire_data)
    res = sc.run(refine=4)
    one = next(p for p in res.points if p["ratio"] == 1.0)
    assert res.firing_adv_equal == pytest.approx(one["firing_adv"], rel=1e-12)
    assert res.firing_adv_equal == pytest.approx(_expect(1.0)["firing_adv"], rel=1e-9)


def test_firing_adv_at_rstar_interpolates_over_ratio_at_value(monkeypatch):
    """SPEC 14.5 (3): firing_adv_at_rstar is the linear interpolation of firing_adv over ratio at `value`."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=_fire_data)
    res = sc.run(refine=0)
    xs = [p["ratio"] for p in res.points]
    ys = [p["firing_adv"] for p in res.points]
    assert res.value is not None
    assert res.firing_adv_at_rstar == pytest.approx(float(np.interp(res.value, xs, ys)), rel=1e-9)
    # it is a number between the neighbours' values, not the equal-ratio value
    assert res.firing_adv_at_rstar != pytest.approx(res.firing_adv_equal, rel=1e-6)


def test_firing_adv_is_none_when_the_naive_side_never_fires(monkeypatch):
    """SPEC 14.5 (3): a naive firing mean of 0 gives firing_adv None (no division by zero) at every point, and
    so firing_adv_equal and firing_adv_at_rstar are None; the other columns are still there."""
    dead = lambda r, seed, sw: {**_fire_data(r, seed, sw), "naive_firing": 0.0}   # noqa: E731
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=dead)
    res = sc.run(refine=4)
    assert all(p["firing_adv"] is None for p in res.points)
    assert all(p["naive_firing_per_head"] == 0.0 and p["skilled_firing_per_head"] > 0 for p in res.points)
    assert res.firing_adv_equal is None and res.firing_adv_at_rstar is None


def test_firing_adv_at_rstar_is_none_when_it_is_missing_at_the_crossing(monkeypatch):
    """SPEC 14.5 (3): `None` when firing_adv is missing at the value: the naive side fires only up to ratio 2.0,
    the crossing (about 2.43) lies beyond it. firing_adv_equal (ratio 1.0) is still a number."""
    part = lambda r, seed, sw: {**_fire_data(r, seed, sw), "naive_firing": 0.0 if r > 2.0 else 30.0}   # noqa: E731
    sc = Scripted(monkeypatch, lambda r, seed, sw: base(r), data=part)
    res = sc.run(refine=4)
    assert res.value is not None and res.value > 2.0
    assert res.firing_adv_at_rstar is None
    assert isinstance(res.firing_adv_equal, float)


def test_firing_adv_at_rstar_is_none_without_a_value(monkeypatch):
    """SPEC 14.5 (3): `None` when value is None (the skilled side beats the whole scan), though every point has firing_adv."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.5, data=_fire_data)
    res = sc.run(refine=4)
    assert res.value is None and res.firing_adv_at_rstar is None
    assert all(p["firing_adv"] is not None for p in res.points)
    assert res.firing_adv_equal is not None


# =========================================================================== (6) rstar_windows


@pytest.fixture(scope="module")
def tiny():
    """4 raiders (range 240) against ratio * 4 raiders (range 200), flat, attack-move: the skilled side wins at
    small ratios and loses at large ones (the planted-advantage build of the controls, at size 4)."""
    build = advantage_build(4)
    rs = rstar(build, seeds=(0,), refine=2)
    assert rs.value is not None and rs.last_win is not None and rs.first_loss is not None, rs
    return build, rs


def _windows(build, rs, **kw):
    return rstarmod.rstar_windows(build, rs, **kw)


def _expected_windows(scn, swap, seed, window_ticks):
    """The windows computed straight from a traced run: counts of units with flag bit 4 and of alive units on
    each side, averaged over each window's ticks."""
    res = run(scn, seed=seed, trace=True)
    tr = res.trace
    side = tr["side"][0]
    fire = (tr["flags"] & 16) != 0
    alive = tr["alive"] != 0
    sk, nv = (1, 0) if swap else (0, 1)
    out = []
    for start in range(0, len(tr), window_ticks):
        sl = slice(start, min(start + window_ticks, len(tr)))
        out.append({"skilled_firing": float(fire[sl][:, side == sk].sum(axis=1).mean()),
                    "naive_firing": float(fire[sl][:, side == nv].sum(axis=1).mean()),
                    "skilled_alive": float(alive[sl][:, side == sk].sum(axis=1).mean()),
                    "naive_alive": float(alive[sl][:, side == nv].sum(axis=1).mean())})
    return res, out


def test_windows_are_for_last_win_and_first_loss_both_labels(tiny):
    """SPEC 14.5 (4): one traced fight per label for last_win and for first_loss: four entries; each has
    ratio, swap, seed, margin and windows."""
    build, rs = tiny
    got = _windows(build, rs, seeds=(0,))
    assert len(got) == 4
    assert {(e["ratio"], e["swap"]) for e in got} == {(rs.last_win, False), (rs.last_win, True),
                                                     (rs.first_loss, False), (rs.first_loss, True)}
    for e in got:
        assert {"ratio", "swap", "seed", "margin", "windows"} <= set(e)
        assert e["seed"] == 0 and e["windows"]


def test_windows_defaults_are_seed_zero_100_ticks_and_the_o2_lib(tiny):
    """SPEC 14.5 (4): the signature rstar_windows(build, rs, seeds=(0,), window_ticks=100, lib='O2'): calling
    with only build and rs equals calling with the defaults spelled out."""
    build, rs = tiny
    assert _windows(build, rs) == _windows(build, rs, seeds=(0,), window_ticks=100, lib="O2")


def test_window_numbers_match_a_traced_run(tiny):
    """SPEC 14.5 (4): the window numbers are the per-window means of the trace: units with flag bit 4 set
    (able to fire) and units alive, per side, the skilled side being label A when swap is False and label B
    when True. Windows start at tick 0 and are 100 ticks long; the count is ceil(ticks / 100). `margin` is
    the skilled side's signed margin."""
    build, rs = tiny
    for e in _windows(build, rs, seeds=(0,), window_ticks=100):
        scn = build(e["ratio"], e["swap"])
        res, want = _expected_windows(scn, e["swap"], 0, 100)
        assert len(e["windows"]) == len(want) == math.ceil(res.ticks / 100), e["ratio"]
        for got, exp in zip(e["windows"], want):
            for key in ("skilled_firing", "naive_firing", "skilled_alive", "naive_alive"):
                assert got[key] == pytest.approx(exp[key], abs=1e-9), (e["ratio"], e["swap"], key)
        m = fight(scn, 0).margin
        assert e["margin"] == pytest.approx(-m if e["swap"] else m, abs=1e-12)


def test_firing_never_exceeds_the_starting_heads_in_any_window(tiny):
    """SPEC 14.5 (4): the units able to fire never outnumber the side's starting heads (4 skilled, round(ratio * 4)
    naive), are never negative, and the alive counts never exceed them either; the skilled side's first window
    has most of its heads alive. (Firing is NOT bounded by the same window's alive mean: a unit's last shot is
    flagged on the tick it dies, so a window can read 3.60 firing against 3.58 alive; the trace test pins it.)"""
    build, rs = tiny
    for e in _windows(build, rs, seeds=(0,), window_ticks=50):
        naive_heads = max(1, round(e["ratio"] * 4))
        for w in e["windows"]:
            assert 0 <= w["skilled_firing"] <= 4 + 1e-9 and 0 <= w["naive_firing"] <= naive_heads + 1e-9
            assert 0 <= w["skilled_alive"] <= 4 + 1e-9 and 0 <= w["naive_alive"] <= naive_heads + 1e-9
        assert 2 < e["windows"][0]["skilled_alive"] <= 4 + 1e-9


def test_a_smaller_window_gives_more_windows_covering_the_same_fight(tiny):
    """SPEC 14.5 (4): the windows cover the fight: window_ticks=50 gives ceil(ticks / 50) windows (so about
    twice as many as 100), the whole fight and no more."""
    build, rs = tiny
    for e in _windows(build, rs, seeds=(0,), window_ticks=50):
        ticks = run(build(e["ratio"], e["swap"]), seed=0).ticks
        assert len(e["windows"]) == math.ceil(ticks / 50)


def test_windows_use_the_seeds_argument(tiny):
    """SPEC 14.5 (4): seeds=(0, 3) runs both: 8 entries, four with seed 0 and four with seed 3 (each
    seed's fights traced under that seed)."""
    build, rs = tiny
    got = _windows(build, rs, seeds=(0, 3))
    assert len(got) == 8
    assert sorted(e["seed"] for e in got) == [0, 0, 0, 0, 3, 3, 3, 3]
    for e in got:
        if e["seed"] == 3:
            _, want = _expected_windows(build(e["ratio"], e["swap"]), e["swap"], 3, 100)
            assert len(e["windows"]) == len(want)


def test_windows_are_deterministic(tiny):
    """SPEC 14.5 (4) and SPEC 9: two calls give equal results."""
    build, rs = tiny
    assert _windows(build, rs) == _windows(build, rs)


def test_windows_without_a_value_use_whichever_bracket_ratios_exist(tiny):
    """SPEC 14.5 (4): when rs.value is None, entries come for whichever of last_win and first_loss exist (two
    labels each); with neither, the result is []."""
    build, rs = tiny
    only_win = replace(rs, value=None, first_loss=None)
    got = _windows(build, only_win)
    assert len(got) == 2 and {e["ratio"] for e in got} == {rs.last_win} and {e["swap"] for e in got} == {False, True}
    only_loss = replace(rs, value=None, last_win=None)
    got = _windows(build, only_loss)
    assert len(got) == 2 and {e["ratio"] for e in got} == {rs.first_loss}
    assert _windows(build, replace(rs, value=None, last_win=None, first_loss=None)) == []


# =========================================================================== (7) the controls, end to end


@pytest.fixture(scope="module")
def mirror8():
    return mirror_control(8)


@pytest.fixture(scope="module")
def advantage8():
    return advantage_control(8)


def test_mirror_control_8_under_headcount_and_margin(mirror8):
    """SPEC 14.5 (1, 2) with 14.1's pass criteria: identical raider forces, ratio by heads, a win needs the
    default 0.02 margin: still valid, abs(value - 1.0) <= 1/8."""
    assert mirror8.valid is True and mirror8.value is not None, mirror8
    assert abs(mirror8.value - 1.0) <= 1 / 8


def test_advantage_control_8_under_headcount_and_margin(advantage8):
    """SPEC 14.5 (1, 2) with 14.1's pass criteria: the planted range advantage clears 1 + 1/8 or is above_scan."""
    assert advantage8.above_scan or advantage8.value > 1.0 + 1 / 8, advantage8


def test_mirror_control_with_explicit_win_margin_zero_and_the_default_agree_within_a_raider():
    """SPEC 14.5 (2): the controls take win_margin; at 0 and at the default 0.02 the mirror is still within one
    raider-equivalent of 1.0 and valid (the margin must not break the control)."""
    for wm in (0.0, 0.02):
        res = mirror_control(8, win_margin=wm)
        assert res.valid is True and res.value is not None, (wm, res)
        assert abs(res.value - 1.0) <= 1 / 8, wm


def test_mirror_control_carries_cost_and_firing_columns(mirror8):
    """SPEC 14.5 (1, 3): raiders against raiders cost the same per head, so cost_ratio equals the headcount
    ratio (to within half a head of 8) and value_cost is about value; the points carry the
    firing columns and firing_adv_equal and firing_adv_at_rstar are numbers."""
    for p in mirror8.points:
        assert abs(p["cost_ratio"] - p["ratio"]) <= 0.5 / 8 + 1e-9, p["ratio"]      # heads are whole numbers
        for key in ("skilled_firing_per_head", "naive_firing_per_head", "skilled_alive_ticks", "naive_alive_ticks"):
            assert p[key] > 0, (p["ratio"], key)
    assert mirror8.value_cost == pytest.approx(mirror8.value, abs=1 / 8)
    assert mirror8.firing_adv_equal is not None and mirror8.firing_adv_equal > 0
    assert mirror8.firing_adv_at_rstar is not None and mirror8.firing_adv_at_rstar > 0


def test_larger_win_margin_never_raises_the_mirror_break_even(mirror8):
    """SPEC 14.5 (2): a stricter win needs the skilled side to be further ahead: win_margin 0.2 gives a
    break-even no larger than the default's, on the same fights (the curve is the same, the threshold higher)."""
    strict = mirror_control(8, win_margin=0.2)
    if strict.value is None:
        assert strict.below_scan is True
    else:
        assert strict.value <= mirror8.value + 0.05      # slack: the refine points differ
