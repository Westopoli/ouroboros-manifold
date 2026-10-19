# spec: docs/northstar/research/layer_dynamics/README.md section 4 (conditions C7, C8, C9, evaluate_all); every pass mark is Westley's and an input
"""C7 and C9 (report only), C8 (joint per-map), evaluate_all (order, codes, purity) over hand-built maps.
Every statistic is the harness writer's unconfirmed definition; every Verdict.detail says so.
Threshold values are placeholders for the tests only."""
import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.conditions import (MapFiring, check_c1, check_c2, check_c3, check_c4, check_c5,  # noqa: E402
                                         check_c6, check_c7, check_c8, check_c9, evaluate_all)
from fakes_scans import EMPTY, FULL, S, make_map, thresholds  # noqa: E402

# draft, not confirmed by Westley; placeholder for the test
DRAFT_UNCONFIRMED_C7_CEILING_TARGETS = (1.0, 2.0)
DRAFT_UNCONFIRMED_C9_LENGTH_BOUNDS_TICKS = (150, 350)


def _prefix(v):
    assert v.detail.startswith("unconfirmed definition:")


# ---------- C7 ----------

def test_c7_top_three_largest_first_ties_by_map_id():
    """Ratio beats(full)/size; top three, ties broken by map_id; report only."""
    t = thresholds(c7_ceiling_targets=DRAFT_UNCONFIRMED_C7_CEILING_TARGETS)
    sp = {"a": 20, "c": 30, "b": 30, "d": 10, "e": 25}
    maps = [make_map(k, over={FULL: v}) for k, v in sp.items()]
    v = check_c7(maps, t)
    assert v.code == "C7" and v.holds is None
    assert list(v.value) == [("b", 3.0), ("c", 3.0), ("e", 2.5)]
    assert v.threshold == DRAFT_UNCONFIRMED_C7_CEILING_TARGETS
    _prefix(v)
    assert "b" in v.detail and "e" in v.detail


def test_c7_skips_undecided_and_handles_none_decided():
    """A None beats(full) is skipped; with none decided the value is an empty list and the detail says so."""
    t = thresholds()
    v = check_c7([make_map("a", over={FULL: None}), make_map("b", over={FULL: 20})], t)
    assert list(v.value) == [("b", 2.0)]
    v = check_c7([make_map("a", over={FULL: None})], t)
    assert v.holds is None and list(v.value) == [] and "no" in v.detail.lower()
    assert list(check_c7([], t).value) == []


# ---------- C9 ----------

def test_c9_median_odd_even_and_bounds_inclusive():
    """(min, median, max, n_outside) over the full-set fights only; bounds inclusive; even median is the mean."""
    t = thresholds(c9_length_bounds_ticks=DRAFT_UNCONFIRMED_C9_LENGTH_BOUNDS_TICKS)
    odd = [make_map("a", full_ticks=(100, 300), other_ticks=777777), make_map("b", full_ticks=(200,))]
    v = check_c9(odd, t)
    assert v.code == "C9" and v.holds is None and tuple(v.value) == (100, 200, 300, 1)
    assert v.threshold == DRAFT_UNCONFIRMED_C9_LENGTH_BOUNDS_TICKS
    _prefix(v)
    even = [make_map("a", full_ticks=(150, 350, 351, 149))]
    assert tuple(check_c9(even, t).value) == (149, 250.0, 351, 2)
    edge = [make_map("a", full_ticks=(150, 350))]
    assert tuple(check_c9(edge, t).value) == (150, 250.0, 350, 0)


def test_c9_no_fights_gives_none():
    """No full-set fights at all: value None."""
    assert check_c9([], thresholds()).value is None
    assert check_c9([make_map(full_ticks=())], thresholds()).value is None


# ---------- C8 ----------

def _t8(**o):
    base = dict(c1_min_firing_advantage=0.25, c3_stack_gain=0.0, c4_max_share=0.04, c5_min_loss=0.5,
                c6_return_share=0.5, c6_map_share=0.0, c8_map_share=1.0)
    base.update(o)
    return thresholds(**base)


def _good(map_id="g", **kw):
    kw.setdefault("counters", {s: 15 for s in kw.get("offers", ("S1", "S2", "S3", "S4", "S5"))})
    return make_map(map_id, **kw)


def test_c8_good_map_holds_and_names_included_conditions():
    """A map meeting C1, C3, C4, C5, C6 holds; the detail lists the conditions and omits C2."""
    v = check_c8([_good()], _t8())
    assert v.code == "C8" and v.holds is True and v.value == 1.0 and v.threshold == 1.0
    _prefix(v)
    for c in ("C1", "C3", "C4", "C5", "C6"):
        assert c in v.detail


@pytest.mark.parametrize("kw", [
    dict(skilled_adv=0.1),                                  # fails C1 only
    dict(over={S("S1", "S2"): 15}),                         # fails C3 only
    dict(over={S("S1"): 25}),                               # fails C4 only
    dict(over={FULL - S("S1"): 300}),                       # fails C5 only
    dict(counters={s: 16 for s in ("S1", "S2", "S3", "S4", "S5")}),  # fails C6 only
    dict(over={FULL: None}),                                # undecided counts against
])
def test_c8_a_map_failing_one_part_is_excluded(kw):
    """Each of C1, C3, C4, C5, C6 (and undecided data) alone keeps a map out of the joint."""
    v = check_c8([_good("a"), _good("b", **kw)], _t8(c8_map_share=0.5))
    assert v.holds is True and v.value == 0.5
    assert check_c8([_good("a"), _good("b", **kw)], _t8(c8_map_share=0.51)).holds is False


def test_c8_c1_mirror_noise_matters_and_c6_not_applicable_holds():
    """Mirror noise 0.4 pushes 0.5 under 0.4 + 0.25; a map where C6 is not applicable still holds that part."""
    assert check_c8([_good(mirror_adv=0.4)], _t8()).holds is False
    flat_single = _good(offers=("S1",), counters={}, over={S("S1"): 10})
    assert check_c6([flat_single], thresholds(c6_return_share=0.5)).holds is None
    assert check_c8([_good(offers=("S1",), counters={}, over={S("S1"): 10})], _t8(c1_min_firing_advantage=-1.0)).holds is True


def test_c8_c2_is_not_part_of_the_joint():
    """An impossible C2 mark changes nothing in C8."""
    assert check_c8([_good()], _t8(c2_rank_agreement=2.0, c2_off_trend_share=-1.0)).holds is True


def test_c8_c1_skills_restricts_which_skills_are_tested():
    """With c1_skills=("S1",) a weak S2 skilled side does not sink the map; by default it does."""
    weak = _good(skilled_adv={"S2": 0.1})
    assert check_c8([weak], _t8()).holds is False
    assert check_c8([weak], _t8(), c1_skills=("S1",)).holds is True


# ---------- evaluate_all ----------

def _maps():
    return [_good("a", offers=("S1", "S3")), _good("b", kind="arena", offers=("S3",))]


def test_evaluate_all_order_codes_and_contents():
    """Verdicts come as C0, C1:Sx per offered skill in order, C2 to C9; each equals its checker's result."""
    t = _t8(c8_map_share=1.0)
    maps = _maps()
    out = evaluate_all(maps, t)
    assert [v.code for v in out] == ["C0", "C1:S1", "C1:S3", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
    assert out[0].holds is True and out[0].code == "C0"
    for v, skill in ((out[1], "S1"), (out[2], "S3")):
        offering = [MapFiring(m.map_id, m.offers, m.scans[EMPTY], m.scans[S(skill)], m.size)
                    for m in maps if skill in m.offers]
        ref = check_c1(offering, skill, t)
        assert (v.holds, v.value, v.threshold) == (ref.holds, ref.value, ref.threshold)
    allscans = [sc for m in maps for sc in m.scans.values()] + [sc for m in maps for sc in m.counters.values()]
    ref2 = check_c2(allscans, t)
    assert (out[3].holds, out[3].value, out[3].threshold) == (ref2.holds, ref2.value, ref2.threshold)
    for v, fn in zip(out[4:], (check_c3, check_c4, check_c5, check_c6, check_c7, check_c8, check_c9)):
        assert v == fn(maps, t)


def test_evaluate_all_c0_only_over_open_maps():
    """No open map: C0 holds None and says so; an open map with a far break-even makes C0 False."""
    t = _t8()
    out = evaluate_all([_good("b", kind="arena")], t)
    assert out[0].code == "C0" and out[0].holds is None and "no" in out[0].detail.lower()
    far = _good("a", over={EMPTY: 30})
    assert evaluate_all([far], t)[0].holds is False


def test_evaluate_all_is_pure_and_validates():
    """Same input, same output, input unchanged; an invalid map raises ValueError."""
    t = _t8()
    maps = _maps()
    before = copy.deepcopy(maps)
    first = evaluate_all(maps, t)
    assert maps == before
    assert evaluate_all(maps, t) == first
    bad = _good("x")
    del bad.scans[S("S1")]
    with pytest.raises(ValueError):
        evaluate_all([bad], t)


# =====================================================================================================================
# LAB-REV2-L5 (decision 31 B, C; decision 29 item 2): the per-baseline C1 is wired into the profile, the mirror C1 stays its own row, and
# every verdict reads the opening window by default with the whole fight beside it.
#
# INTERFACE FIXED HERE:
#   profile.ProfileMap gains `baselines: dict = {}` (LAST field, default empty dict): baseline role -> ScanResult of that naive baseline on
#       the map (the same meaning as MapFiring.baselines). validate() does not require it.
#   conditions.evaluate_all(maps, t, basis=DEFAULT_BASIS): after each "C1:<skill>" row (the mirror C1, unchanged) come the rows
#       "C1@<role>:<skill>" of check_c1_baselines over the maps offering that skill (MapFiring.baselines = ProfileMap.baselines), roles
#       sorted; without baselines on any map the output is exactly what it was. `basis` goes to every C1, C2 and C8 inside.
#   conditions.evaluate_bases(maps, t) -> {"window": evaluate_all(maps, t, basis="window"), "whole": evaluate_all(maps, t, basis="whole")},
#       keys in that order: the whole-fight verdicts reported beside the window ones.
# =====================================================================================================================
import dataclasses  # noqa: E402

from scripts.skilllab import conditions, profile  # noqa: E402
from fakes_scans import cell, fight, scan_of  # noqa: E402


def _baseline_scan(m, adv):
    return scan_of(m.size, 20, [cell(m.size, [fight(adv), fight(-adv)])])


def _with_baselines(m, **advs):
    m.baselines = {role: _baseline_scan(m, adv) for role, adv in advs.items()}
    return m


def _window_blind(m):
    """The skilled scans keep their whole-fight advantage and lose their window advantage (window 1, 1)."""
    for s, sc in m.scans.items():
        if s == EMPTY:
            continue
        for c in sc.cells:
            c.fights[:] = [dataclasses.replace(f, firing_window=(1.0, 1.0)) for f in c.fights]
    return m


def test_l5_profilemap_baselines_field_is_last_defaults_to_empty_and_is_not_validated():
    pm = make_map("a")
    assert pm.baselines == {} and dataclasses.fields(profile.ProfileMap)[-1].name == "baselines"
    pm.baselines = {"naive_attacker": _baseline_scan(pm, 0.0), "some_new_role": _baseline_scan(pm, 0.0)}
    profile.validate(pm)                              # no exception: roles are the sweep's business


def test_l5_evaluate_all_without_baselines_is_unchanged():
    """Negative control of the wiring: the codes are exactly the old list."""
    out = evaluate_all(_maps(), _t8(c8_map_share=1.0))
    assert [v.code for v in out] == ["C0", "C1:S1", "C1:S3", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]


def test_l5_evaluate_all_puts_the_baseline_rows_after_the_mirror_row_of_each_skill():
    t = _t8(c8_map_share=1.0)
    maps = [_with_baselines(_good("a", offers=("S1", "S3")), naive_defender=0.9, naive_attacker=0.0),
            _with_baselines(_good("b", kind="arena", offers=("S3",)), naive_attacker=0.0)]
    out = evaluate_all(maps, t)
    assert [v.code for v in out] == ["C0", "C1:S1", "C1@naive_attacker:S1", "C1@naive_defender:S1",
                                     "C1:S3", "C1@naive_attacker:S3", "C1@naive_defender:S3", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
    by = {v.code: v for v in out}
    for skill in ("S1", "S3"):
        offering = [MapFiring(m.map_id, m.offers, m.scans[EMPTY], m.scans[S(skill)], m.size, m.baselines) for m in maps if skill in m.offers]
        for ref in conditions.check_c1_baselines(offering, skill, t):
            got = by["%s:%s" % (ref.code, skill)]
            assert (got.holds, got.value, got.threshold) == (ref.holds, ref.value, ref.threshold)
        assert (by["C1:" + skill].holds, by["C1:" + skill].value) == (check_c1(offering, skill, t).holds, check_c1(offering, skill, t).value)
    # the quiet attacker baseline holds, the loud defender baseline does not (0.5 > 0.9 + 0.25 is false), the mirror (quiet) holds
    assert by["C1@naive_attacker:S1"].holds is True and by["C1@naive_defender:S1"].holds is False and by["C1:S1"].holds is True
    assert by["C1@naive_defender:S3"].value == 0.0 and by["C1@naive_attacker:S3"].value == 1.0           # S3: maps a and b


def test_l5_evaluate_all_baseline_rows_exist_only_for_skills_a_map_with_the_role_offers():
    """A role on a map that does not offer S3 gives no S3 row; positive control: the same role on the S1 map gives its S1 row."""
    maps = [_with_baselines(_good("a", offers=("S1",)), naive_attacker=0.0), _good("b", offers=("S3",))]
    codes = [v.code for v in evaluate_all(maps, _t8(c8_map_share=1.0))]
    assert "C1@naive_attacker:S1" in codes and not [c for c in codes if c.endswith(":S3") and c.startswith("C1@")]


def test_l5_evaluate_all_stays_pure_with_baselines():
    t = _t8()
    maps = [_with_baselines(_good("a"), naive_attacker=0.0)]
    before = copy.deepcopy(maps)
    first = evaluate_all(maps, t)
    assert maps == before and evaluate_all(maps, t) == first


def test_l5_evaluate_all_default_basis_is_the_window_and_basis_whole_reads_the_whole_fight():
    """Skilled sides have whole-fight advantage 0.5 and window advantage 0.0: C1 (mirror and baseline) and C8 fail on the window default and
    hold on the whole fight."""
    maps = [_with_baselines(_window_blind(_good("a")), naive_attacker=0.0)]
    t = _t8(c8_map_share=1.0)
    window, whole = evaluate_all(maps, t), evaluate_all(maps, t, basis="whole")
    for code in ("C1:S1", "C1@naive_attacker:S1", "C8"):
        assert {v.code: v.holds for v in window}[code] is False, code
        assert {v.code: v.holds for v in whole}[code] is True, code
    assert evaluate_all(maps, t, basis="window") == window


def test_l5_check_c8_reads_the_basis_of_its_inner_c1():
    m = _window_blind(_good("a"))
    assert check_c8([m], _t8()).holds is False and check_c8([m], _t8(), basis="whole").holds is True
    assert check_c8([m], _t8(), basis="window").holds is False


def test_l5_evaluate_bases_reports_the_window_and_the_whole_fight_verdicts_side_by_side():
    maps = [_with_baselines(_window_blind(_good("a")), naive_attacker=0.0)]
    t = _t8(c8_map_share=1.0)
    both = conditions.evaluate_bases(maps, t)
    assert list(both) == ["window", "whole"]
    assert both["window"] == evaluate_all(maps, t, basis="window") and both["whole"] == evaluate_all(maps, t, basis="whole")
    assert [v.code for v in both["window"]] == [v.code for v in both["whole"]]
    differing = [w.code for w, h in zip(both["window"], both["whole"]) if w.holds != h.holds]
    assert "C1:S1" in differing and "C1@naive_attacker:S1" in differing and "C0" not in differing
