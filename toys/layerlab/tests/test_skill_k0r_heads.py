"""Whole-head scan (SPEC.md section 14.5 item 9, design chat 2026-10-01).

Run from toys/layerlab/. Red until the builder implements item 9: today `rstar` has no `size` argument, points
carry no `heads`, `RStar` has no `last_win_heads` / `first_loss_heads`, `profile` and the controls do not pass a
size, and `experiments/small_batch.py` has no `summary_line`.

Layout: (1) the scan is over distinct whole head counts, (2) refinement bisects integers, (3) the bracket edges in
heads, (4) size=None keeps the old behaviour, (5) profile and the controls pass the size, (6) small_batch's
summary line.

Scripted tests reuse `Scripted` from test_skill_k0r.py (it replaces `layerlab.skill.rstar.run_fights` and builds
real scenario dicts with groups); the curves here are functions of the enemy HEAD count `int(ratio * size + 0.5)`.
Conventions these tests fix where item 9 is silent:
  * A point's `heads` is an int; the point's `ratio` is `heads / size` exactly (same float as the division).
  * `last_win_heads` / `first_loss_heads` are ints.
  * `summary_line(rs, size)` reads "<size> skilled heads beat <last_win_heads> and lose to <first_loss_heads>"
    when both bracket edges exist; otherwise a sentence containing "no break-even" (case-insensitive).
"""
import dataclasses
import importlib
import importlib.util
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from layerlab.skill.rstar import RATIOS, rstar
from test_skill_k0r import Scripted, line
from test_skill_k0r_b import _fake_fight
from test_skill_k2 import _sit

LAB = Path(__file__).resolve().parent.parent


def _n(ratio, size):
    return max(1, int(ratio * size + 0.5))


def _expected_heads(size, ratios=RATIOS):
    return sorted({_n(r, size) for r in ratios})


class Recording(Scripted):
    """Scripted that also records every ratio `build` is called with."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.build_ratios = []

    def build(self, ratio, swap):
        self.build_ratios.append(ratio)
        return super().build(ratio, swap)


def _step(size, last_win_heads):
    """Skilled margin +0.5 while the enemy has at most `last_win_heads` heads, -0.5 beyond."""
    return lambda r, seed, sw: 0.5 if _n(r, size) <= last_win_heads else -0.5


# =========================================================================== (1) distinct whole head counts


@pytest.mark.parametrize("size", (8, 2, 3))
def test_scan_points_are_distinct_whole_head_counts(monkeypatch, size):
    """SPEC 14.5 item 9: with size given, each scan ratio r becomes n = max(1, int(r * size + 0.5)); duplicates
    are dropped, so no two points share a head count; every point has `heads` n, ratio exactly n / size, sorted.
    Size 2 and 3 make several default RATIOS collapse to one head count (the old scan ran them as separate points)."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: 0.5)         # above the whole scan: no refinement
    res = sc.run(size=size)
    want = _expected_heads(size)
    got = [p["heads"] for p in res.points]
    assert got == want, (got, want)
    assert len(set(got)) == len(got)
    assert [p["ratio"] for p in res.points] == [n / size for n in want]
    assert all(isinstance(p["heads"], int) for p in res.points)
    # a duplicate is dropped, not merely hidden: one fight per label and seed per distinct head count
    assert len(sc.seen) == 2 * 2 * len(want)


def test_size_8_default_ratios_give_the_hand_computed_heads(monkeypatch):
    """SPEC 14.5 item 9: size 8 with RATIOS (0.5 .. 8.0): int(r * 8 + 0.5) is 4 6 7 8 10 11 14 16 19 23 28 34 40
    48 64 (1.4 gives 11, not 12: 11.2 rounds down)."""
    res = Scripted(monkeypatch, lambda r, seed, sw: 0.5).run(size=8)
    assert [p["heads"] for p in res.points] == [4, 6, 7, 8, 10, 11, 14, 16, 19, 23, 28, 34, 40, 48, 64]


# =========================================================================== (2) integer refinement


def test_refinement_uses_integer_midpoints_between_bracket_edges(monkeypatch):
    """SPEC 14.5 item 9: ratios (0.5, 1.0, 1.5) at size 8 are 4, 8, 12 heads; the skilled side wins up to 9 heads.
    Bracket (8, 12): midpoint (8 + 12) // 2 = 10 loses, so (8, 10); midpoint 9 wins, so (9, 10): adjacent, stop.
    The extra points are exactly the whole head counts 10 and 9, even with refine=4 left over."""
    sc = Recording(monkeypatch, _step(8, 9))
    res = sc.run(size=8, ratios=(0.5, 1.0, 1.5), refine=4)
    assert [p["heads"] for p in res.points] == [4, 8, 9, 10, 12]
    assert [p["ratio"] for p in res.points] == [4 / 8, 8 / 8, 9 / 8, 10 / 8, 12 / 8]
    assert (res.last_win_heads, res.first_loss_heads) == (9, 10)


def test_refinement_stops_when_the_bracket_edges_are_adjacent(monkeypatch):
    """SPEC 14.5 item 9: size 16, default RATIOS: 16 heads win, 19 lose (1.2 * 16 = 19.2); the skilled side wins up
    to 18. Midpoints 17 then 18 are run, then the edges 18 and 19 are adjacent and no third extra point appears
    although refine=4 allowed it."""
    sc = Recording(monkeypatch, _step(16, 18))
    res = sc.run(size=16, refine=4)
    scan = set(_expected_heads(16))
    extra = sorted(p["heads"] for p in res.points if p["heads"] not in scan)
    assert extra == [17, 18]
    assert all(16 < h < 19 for h in extra)


def test_refinement_budget_still_bounds_the_extra_points(monkeypatch):
    """SPEC 14.5 item 9: refine counts bisections: refine=1 on the 8 / 12 bracket adds one point, the head
    count 10."""
    sc = Recording(monkeypatch, _step(8, 9))
    res = sc.run(size=8, ratios=(0.5, 1.0, 1.5), refine=1)
    assert [p["heads"] for p in res.points] == [4, 8, 10, 12]
    assert (res.last_win_heads, res.first_loss_heads) == (8, 10)


def test_no_fractional_head_count_ever_reaches_build(monkeypatch):
    """SPEC 14.5 item 9: every ratio `build` is called with is a whole head count over size:
    int(ratio * size + 0.5) / size == ratio within 1e-9, scan and refinement alike (old code bisected the ratio
    itself, and a second midpoint such as 1.1875 is 9.5 heads, not whole)."""
    for size, curve_win, ratios in ((8, 9, (0.5, 1.0, 1.5)), (16, 18, RATIOS), (8, 11, (0.5, 1.0, 2.0))):
        sc = Recording(monkeypatch, _step(size, curve_win))
        sc.run(size=size, ratios=ratios, refine=6)
        assert sc.build_ratios
        for r in sc.build_ratios:
            assert abs(int(r * size + 0.5) / size - r) < 1e-9, (size, r)


# =========================================================================== (3) last_win_heads / first_loss_heads


def _check_literal_truth(res, size):
    """Every table row at or below last_win_heads is a win, every row at or above first_loss_heads is not."""
    for p in res.points:
        if p["heads"] <= res.last_win_heads:
            assert p["value"] > res.win_margin, p
        if p["heads"] >= res.first_loss_heads:
            assert p["value"] <= res.win_margin, p


@pytest.mark.parametrize("name,size,curve", [
    ("step 16", 16, _step(16, 18)),
    ("step 8", 8, _step(8, 9)),
    ("line 16", 16, lambda r, seed, sw: line(r)),
    ("line 8", 8, lambda r, seed, sw: line(r)),
])
def test_bracket_edges_in_heads_differ_by_one_and_match_the_ratios(monkeypatch, name, size, curve):
    """SPEC 14.5 item 9: on a clean monotone curve with a bracket, after refinement first_loss_heads is
    last_win_heads + 1; they equal last_win and first_loss times size; the table's rows obey them."""
    res = Scripted(monkeypatch, curve).run(size=size, refine=10)
    assert res.last_win is not None and res.first_loss is not None, name
    assert isinstance(res.last_win_heads, int) and isinstance(res.first_loss_heads, int)
    assert res.first_loss_heads - res.last_win_heads == 1, name
    assert res.last_win_heads == round(res.last_win * size)
    assert res.first_loss_heads == round(res.first_loss * size)
    _check_literal_truth(res, size)


def test_step_curve_edges_are_exactly_the_scripted_break(monkeypatch):
    """SPEC 14.5 item 9: the step curve wins up to 18 heads at size 16: 'beats 18 and loses to 19'."""
    res = Scripted(monkeypatch, _step(16, 18)).run(size=16, refine=4)
    assert (res.last_win_heads, res.first_loss_heads) == (18, 19)


def test_above_scan_has_a_last_win_and_no_first_loss(monkeypatch):
    """SPEC 14.5 item 9: the skilled side beats every run head count: last_win_heads is the largest scanned
    head count, first_loss_heads is None."""
    res = Scripted(monkeypatch, lambda r, seed, sw: 0.5).run(size=8)
    assert res.above_scan is True
    assert res.last_win_heads == 64 and res.first_loss_heads is None


def test_below_scan_has_a_first_loss_and_no_last_win(monkeypatch):
    """SPEC 14.5 item 9: the skilled side beats nothing: first_loss_heads is the smallest scanned head count
    (int(0.5 * 8 + 0.5) = 4), last_win_heads is None."""
    res = Scripted(monkeypatch, lambda r, seed, sw: -0.5).run(size=8)
    assert res.below_scan is True
    assert res.last_win_heads is None and res.first_loss_heads == 4


def test_win_margin_moves_the_head_bracket(monkeypatch):
    """SPEC 14.5 item 9 with item 2: a margin of 0.05 is a win at win_margin 0.02 and not at 0.2; the head
    bracket follows the threshold, not zero. Step: +0.05 up to 10 heads, -0.5 beyond (size 8)."""
    curve = lambda r, seed, sw: 0.05 if _n(r, 8) <= 10 else -0.5          # noqa: E731
    sc = Scripted(monkeypatch, curve)
    low = sc.run(size=8, refine=6, win_margin=0.02)
    assert (low.last_win_heads, low.first_loss_heads) == (10, 11)
    high = sc.run(size=8, refine=6, win_margin=0.2)
    assert high.last_win_heads is None and high.below_scan is True


# =========================================================================== (4) size=None is the old behaviour


def test_size_none_is_identical_to_not_passing_size(monkeypatch):
    """SPEC 14.5 item 9: size=None keeps the old fractional behaviour: the line fixture of test_skill_k0r.py
    (refine=4, zero crossing 4.1) gives the same RStar with size=None as without the argument, and the refinement
    points are fractional ratios (the old bisection)."""
    sc = Scripted(monkeypatch, lambda r, seed, sw: line(r))
    plain = sc.run(refine=4)
    explicit = sc.run(refine=4, size=None)
    assert explicit == plain
    assert explicit.value == pytest.approx(4.1, abs=1e-6)
    new = [p["ratio"] for p in explicit.points if p["ratio"] not in RATIOS]
    # test-defect fix 2026-10-01: at the default win_margin 0.02 the scan's last win is 3.5 and its first loss 4.2
    # (line(4.2) = 0.0067 is under the margin), so the old bisection runs inside (3.5, 4.2); 4.2 and 5.0 are the
    # win_margin = 0 numbers
    assert len(new) == 4 and all(3.5 < r < 4.2 for r in new)
    assert explicit.last_win == 3.5 and explicit.first_loss == 4.2


def test_size_none_leaves_the_head_fields_empty(monkeypatch):
    """SPEC 14.5 item 9: without a size there are no head counts: last_win_heads and first_loss_heads are None."""
    res = Scripted(monkeypatch, lambda r, seed, sw: line(r)).run(refine=4, size=None)
    assert res.last_win_heads is None and res.first_loss_heads is None


# =========================================================================== (5) profile and the controls


@pytest.mark.parametrize("which", ("mirror_control", "advantage_control"))
def test_controls_pass_size_and_scan_whole_heads(monkeypatch, which):
    """SPEC 14.5 item 9: mirror_control(8) and advantage_control(8) call rstar with size=8; the points all carry
    `heads`, with no duplicate head count, and ratio == heads / 8. (Fights are scripted: more heads win.)"""
    controls = importlib.import_module("layerlab.skill.controls")
    rstarmod = importlib.import_module("layerlab.skill.rstar")
    monkeypatch.setattr(rstarmod, "run_fights", lambda jobs, *a, **k: [_fake_fight(scn) for scn, _s in jobs])
    calls = []
    real = controls.rstar

    def spy(build, **kw):
        calls.append(kw)
        return real(build, **kw)

    monkeypatch.setattr(controls, "rstar", spy)
    res = getattr(controls, which)(8)
    assert len(calls) >= 1 and all(kw.get("size") == 8 for kw in calls), calls
    assert res.points and all("heads" in p for p in res.points)
    heads = [p["heads"] for p in res.points]
    assert len(set(heads)) == len(heads)
    assert all(p["ratio"] == p["heads"] / 8 for p in res.points)
    assert heads == _expected_heads(8)


class _Rec:
    """Wraps a built `build(ratio, swap)` callable; records the ratios and forwards attribute reads (`arc`)."""

    def __init__(self, inner, log):
        self._inner, self._log = inner, log

    def __call__(self, ratio, swap):
        self._log.append(ratio)
        return self._inner(ratio, swap)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def test_profile_scans_whole_head_counts(monkeypatch):
    """SPEC 14.5 item 9: profile on one tiny situation (flat, size 4, no skills, scripted fights) builds only whole
    head counts: every ratio given to `build` has int(ratio * 4 + 0.5) / 4 == ratio, and each distinct head count is
    built exactly twice (both labels), so the default ratios 0.7 and 0.85, which both round to 3 heads, are not
    two scan points."""
    rstarmod = importlib.import_module("layerlab.skill.rstar")
    plays = importlib.import_module("layerlab.skill.plays")
    monkeypatch.setattr(rstarmod, "run_fights", lambda jobs, *a, **k: [_fake_fight(scn) for scn, _s in jobs])
    for mod in (rstarmod, plays):                                     # windows run traced fights: not wanted here
        monkeypatch.setattr(mod, "rstar_windows", lambda *a, **k: [], raising=False)
    log = []
    real_build = plays.build_scenario
    monkeypatch.setattr(plays, "build_scenario", lambda *a, **k: _Rec(real_build(*a, **k), log))
    sit = dataclasses.replace(_sit("flat"), id=0)
    prof = plays.profile([sit], sizes=(4,), seeds=(0,), combos=[frozenset()], processes=0)
    assert len(prof.cells) == 1
    assert log
    for r in log:
        assert abs(int(r * 4 + 0.5) / 4 - r) < 1e-9, r
    counts = Counter(log)
    assert all(c == 2 for c in counts.values()), counts          # one build per label per distinct head count
    scan_heads = _expected_heads(4)
    assert {int(r * 4 + 0.5) for r in log} >= set(scan_heads)
    assert len([r for r in counts if int(r * 4 + 0.5) in scan_heads]) >= len(scan_heads)


# =========================================================================== (6) small_batch summary line


def _small_batch():
    spec = importlib.util.spec_from_file_location("small_batch_under_test", LAB / "experiments" / "small_batch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rs(**kw):
    base = dict(value=1.3, above_scan=False, below_scan=False, last_win=None, first_loss=None,
                last_win_heads=None, first_loss_heads=None, short_scan=False, valid=True, points=[])
    base.update(kw)
    return SimpleNamespace(**base)


def test_summary_line_reads_the_head_bracket_not_value_times_size():
    """SPEC 14.5 item 9: summary_line(rs, size) is '<size> skilled heads beat <last_win_heads> and lose to
    <first_loss_heads>', built from the bracket edges. The object's value (1.3, x 8 = 10.4) and ratios disagree
    on purpose: the line must say 9 and 10."""
    sb = _small_batch()
    rs = _rs(value=1.3, last_win=1.0, first_loss=1.5, last_win_heads=9, first_loss_heads=10)
    out = sb.summary_line(rs, 8)
    assert isinstance(out, str)
    assert "8 skilled heads beat 9 and lose to 10" in out
    assert "10.4" not in out and "10 and lose to 11" not in out


def test_summary_line_is_adjacent_numbers_for_a_refined_result():
    """SPEC 14.5 item 9: the two numbers in the line are adjacent whole numbers when the heads fields are."""
    sb = _small_batch()
    out = sb.summary_line(_rs(last_win_heads=18, first_loss_heads=19), 16)
    assert "16 skilled heads beat 18 and lose to 19" in out


@pytest.mark.parametrize("kw", [
    dict(above_scan=True, value=None, last_win_heads=64),                           # beat every run count
    dict(below_scan=True, value=None, first_loss_heads=4),                          # beat none
    dict(value=None),                                                               # neither edge
])
def test_summary_line_without_a_bracket_is_a_plain_no_break_even_sentence(kw):
    """SPEC 14.5 item 9: when either bracket edge is missing the line says there is no break-even and does not
    claim 'beat ... and lose to ...'."""
    sb = _small_batch()
    out = sb.summary_line(_rs(**kw), 8)
    assert isinstance(out, str) and out.strip()
    assert "no break-even" in out.lower()
    assert "lose to" not in out
