"""K0 revision, part B (SPEC.md 14.5 items 1, 5, 6, 7, 8): situations, plays, profile, report.

Run from toys/layerlab/. Expected red until the builders implement 14.5. Part A (cost, fight, rstar) is tested
elsewhere; here part A is used only through the names SPEC 14.5 gives it (counts_for_heads, rstar_windows).

Conventions these tests fix (SPEC gaps, reported):
- Item 1: `Situation.mix` shares are HEAD shares; the skilled side fields counts_for_heads(mix, size), the naive
  side counts_for_heads(mix, (int)(ratio * size + 0.5)). The SPEC rounding is half-up, not Python's round()
  (banker's): ratio 0.8125 at size 8 is 6.5 heads and must give 7.
- Item 6: with ratio below 1 the skilled side is the larger side and attacks (attack_move) even with S1 on a
  family where S1 normally holds; with ratio above 1 it is the smaller side and holds. Ratio 1.0 is not tested.
  The naive side attacks at every ratio (unchanged).
- Item 7: a hidden-layer spawn failure is a ValueError whose message contains "on that layer" (the loader's
  wording). `validate` words the new reason with "hidden" (case-insensitive).
- Item 8: the builder provides, in experiments/baseline_report.py:
    fit_loglog(points) -> {"slope", "intercept", "r2", "n"}: `points` is a list of (x, y) pairs of positive
        numbers (x = firing_adv_at_rstar, y = R*); ordinary least squares of ln y on ln x (natural log).
    off_line(points, fit, thresh=0.25) -> the input points (same objects, input order) whose absolute residual
        |ln y - (slope * ln x + intercept)| is greater than thresh.
    c1_share(cells, combo_key) -> share (float) of the cells with cell["combo"] == combo_key, valid True,
        map_set "space" whose firing_adv_equal is greater than 1.0; None when no such cell exists.
    plot_rule_set(cells, config, out_path, map_set="space") -> str: takes the valid cells of that config and
        map set with a value and a firing_adv_at_rstar, one point per cell (x firing_adv_at_rstar, y value,
        both log axes), writes the PNG to out_path and returns the printed text, which holds the slope and the
        r squared (at least two decimals) and the `sit` ids of the off-line points.
"""
import dataclasses
import importlib
import importlib.util
import math
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from layerlab import formations, scenario, terrain  # noqa: E402
from test_skill_k2 import FAMILIES, _m, _sit, _units  # noqa: E402

LAB = Path(__file__).resolve().parent.parent
SPACE = ("flat", "block", "wall", "lane", "cover")
LAND = ("barrier_ramp", "ramp_defense")
REFUSABLE = {"flat": True, "block": True, "wall": True, "cover": True, "barrier_ramp": True,
             "lane": False, "ramp_defense": False}


def _heads(scn, label):
    out = {}
    for g in scn["groups"]:
        if g["side"] == label:
            out[g["type"]] = out.get(g["type"], 0) + int(g["count"])
    return out


def _labels(swap):
    return ("B", "A") if swap else ("A", "B")       # (skilled label, naive label)


# ------------------------------------------------------------------ item 1: ratio and size by headcount

HEAD_MIX = {"raider": 0.5, "vanguard": 0.25, "bombard": 0.25}


@pytest.mark.parametrize("swap", (False, True))
@pytest.mark.parametrize("ratio,naive_heads", [(0.5, {"raider": 2, "vanguard": 1, "bombard": 1}),
                                               (1.0, {"raider": 4, "vanguard": 2, "bombard": 2}),
                                               (2.0, {"raider": 8, "vanguard": 4, "bombard": 4}),
                                               (3.5, {"raider": 14, "vanguard": 7, "bombard": 7})])
def test_item1_both_sides_field_heads_by_the_mix_shares(ratio, naive_heads, swap):
    """SPEC 14.5 item 1: skilled 8 heads (4/2/2), naive ratio * 8 heads with the same head shares; swap
    exchanges the labels only."""
    sit = _sit("flat", mix=HEAD_MIX)
    scn = _m("plays").build_scenario(sit, frozenset(), 8)(ratio, swap)
    skilled, naive = _labels(swap)
    assert _heads(scn, skilled) == {"raider": 4, "vanguard": 2, "bombard": 2}
    assert _heads(scn, naive) == naive_heads
    assert sum(_heads(scn, skilled).values()) == 8
    assert sum(_heads(scn, naive).values()) == round(ratio * 8)


@pytest.mark.parametrize("ratio", (0.5, 1.0, 2.0, 3.5))
def test_item1_counts_match_counts_for_heads_and_labels_swap(ratio):
    """SPEC 14.5 item 1: the counts are exactly counts_for_heads (part A name) and swap=True exchanges A and B."""
    counts_for_heads = _m("cost").counts_for_heads
    sit = _sit("flat", mix=HEAD_MIX)
    base = _m("situation").base_scenario(sit)
    build = _m("plays").build_scenario(sit, frozenset(), 8)
    plain, swapped = build(ratio, False), build(ratio, True)
    want_s, want_n = counts_for_heads(sit.mix, 8, base), counts_for_heads(sit.mix, int(ratio * 8 + 0.5), base)
    assert _heads(plain, "A") == want_s and _heads(plain, "B") == want_n
    assert _heads(swapped, "B") == want_s and _heads(swapped, "A") == want_n
    assert _heads(plain, "A") == _heads(swapped, "B") and _heads(plain, "B") == _heads(swapped, "A")


def test_item1_naive_heads_round_half_up():
    """SPEC 14.5 item 1: round(ratio * size) is (int)(x + 0.5): 6.5 heads is 7 (Python's round gives 6)."""
    sit = _sit("flat", mix={"raider": 0.5, "vanguard": 0.5})
    scn = _m("plays").build_scenario(sit, frozenset(), 8)(0.8125, False)
    assert sum(_heads(scn, "B").values()) == 7
    assert sum(_heads(scn, "A").values()) == 8


def test_item1_largest_remainder_ties_go_to_the_type_listed_first():
    """SPEC 14.5 item 1: 6 naive heads at 0.75 / 0.25 is 4.5 + 1.5: the spare head goes to the first type."""
    sit = _sit("flat", mix={"raider": 0.75, "warden": 0.25})
    scn = _m("plays").build_scenario(sit, frozenset(), 8)(0.75, False)
    assert _heads(scn, "A") == {"raider": 6, "warden": 2}
    assert _heads(scn, "B") == {"raider": 5, "warden": 1}


def test_item1_sampled_mixes_are_head_shares_in_quarters_and_proportions_stay_within_one_head():
    """SPEC 14.5 item 1: sampled shares are multiples of 0.25 summing to 1, read as head shares: each side's
    count per type is within one head of share * its own total, and ratio 1.0 gives equal sides."""
    counts_for_heads = _m("cost").counts_for_heads
    sits = _m("situation").sample_situations(14, 1)
    plays = _m("plays")
    for sit in sits:
        shares = list(sit.mix.values())
        assert all(abs(s * 4 - round(s * 4)) < 1e-9 and s > 0 for s in shares), sit.mix
        assert abs(sum(shares) - 1.0) < 1e-9
        base = _m("situation").base_scenario(sit)
        for ratio in (1.0, 2.0):
            scn = plays.build_scenario(sit, frozenset(), 8)(ratio, False)
            for label, n in (("A", 8), ("B", round(ratio * 8))):
                got = _heads(scn, label)
                assert got == counts_for_heads(sit.mix, n, base), (sit.family, label, got)
                assert sum(got.values()) == n
                for t, share in sit.mix.items():
                    assert abs(got.get(t, 0) - share * n) < 1.0, (sit.family, label, t)


# ------------------------------------------------------------------ item 5: map sets

def test_item5_map_set_table_is_exact():
    """SPEC 14.5 item 5."""
    assert _m("situation").MAP_SET == {"flat": "space", "block": "space", "wall": "space", "lane": "space",
                                       "cover": "space", "barrier_ramp": "land", "ramp_defense": "land"}


@pytest.mark.parametrize("family", FAMILIES)
def test_item5_situation_map_set_property_follows_the_family(family):
    """SPEC 14.5 item 5: Situation.map_set per family (a property, so a hand-set family changes it)."""
    sit = _sit(family)
    assert sit.map_set == ("land" if family in LAND else "space")
    other = dataclasses.replace(sit, family="barrier_ramp" if family in SPACE else "flat")
    assert other.map_set != sit.map_set


def test_item5_sampler_produces_both_sets():
    """SPEC 14.5 item 5: sample_situations(14, 1) holds a space and a land situation."""
    sets = {s.map_set for s in _m("situation").sample_situations(14, 1)}
    assert sets == {"space", "land"}


def _fake_cells():
    S1, S2 = frozenset({"S1"}), frozenset({"S2"})
    cell = lambda ms, combo, prem, valid=True: {"map_set": ms, "combo": combo, "premium": prem, "valid": valid,
                                                "value": 1.0, "size": 8, "situation": 0, "flags": []}
    return [cell("space", S1, 1.0), cell("space", S1, 2.0), cell("space", S1, 3.0), cell("space", S1, 9.0, False),
            cell("land", S1, 10.0), cell("land", S1, 20.0), cell("space", S2, 5.0), cell("land", S2, 7.0)]


def test_item5_aggregate_filters_by_map_set():
    """SPEC 14.5 item 5: Profile.aggregate(map_set=...) counts only that set's cells; None counts all."""
    prof = _m("plays").Profile(cells=_fake_cells())
    S1, S2 = frozenset({"S1"}), frozenset({"S2"})
    allc, space, land = prof.aggregate(), prof.aggregate(map_set="space"), prof.aggregate(map_set="land")
    assert allc[S1]["n_valid"] == 5 and allc[S1]["median_premium"] == 3.0          # 1,2,3,10,20
    assert space[S1]["n_valid"] == 3 and space[S1]["median_premium"] == 2.0 and space[S1]["n_invalid"] == 1
    assert land[S1]["n_valid"] == 2 and land[S1]["median_premium"] == 15.0 and land[S1]["n_invalid"] == 0
    assert space[S2]["n_valid"] == 1 and space[S2]["median_premium"] == 5.0
    assert land[S2]["n_valid"] == 1 and land[S2]["median_premium"] == 7.0
    assert prof.aggregate(map_set=None) == allc


# ------------------------------------------------------------------ item 6: refusability

@pytest.mark.parametrize("family", FAMILIES)
def test_item6_situation_refusable_and_reason(family):
    """SPEC 14.5 item 6: refusable True for flat, block, wall, cover, barrier_ramp; False for lane and
    ramp_defense; refusable_reason is a non-empty str."""
    sit = _sit(family)
    assert sit.refusable is REFUSABLE[family]
    assert isinstance(sit.refusable_reason, str) and sit.refusable_reason.strip()


def _fake_fight(scn, seed_unused=None):
    """A scripted fight: the side with more heads wins. Fields part A adds are filled when they exist."""
    fight = _m("fight")
    heads = (sum(int(g["count"]) for g in scn["groups"] if g["side"] == "A"),
             sum(int(g["count"]) for g in scn["groups"] if g["side"] == "B"))
    m = float((heads[0] > heads[1]) - (heads[0] < heads[1]))
    kw = dict(margin=m, raw_margin=m, outcome="win_A" if m > 0 else "win_B" if m < 0 else "stalemate",
              ticks=100, first_contact_tick=10, contact=True, survivors=(), alive_ticks=(100, 100),
              firing_ticks=(50, 50), heads=heads)
    names = {f.name for f in dataclasses.fields(fight.FightResult)}
    return fight.FightResult(**{k: v for k, v in kw.items() if k in names})


def test_item6_profile_cells_carry_map_set_and_refusable(monkeypatch):
    """SPEC 14.5 items 5 and 6: every profile cell carries map_set and refusable of its situation."""
    rstar_mod = importlib.import_module("layerlab.skill.rstar")
    plays = _m("plays")
    monkeypatch.setattr(rstar_mod, "run_fights", lambda jobs, *a, **k: [_fake_fight(scn) for scn, _s in jobs])
    for mod in (rstar_mod, plays):                      # windows run traced fights: not wanted here
        monkeypatch.setattr(mod, "rstar_windows", lambda *a, **k: [], raising=False)
    # test-defect fix 2026-10-01: _sit gives every situation id 0, so the id lookup below needs distinct ids
    sits = [dataclasses.replace(_sit(f), id=i) for i, f in enumerate(("lane", "barrier_ramp", "flat"))]
    prof = plays.profile(sits, sizes=(4,), ratios=(0.7, 1.4, 2.8), refine=1, seeds=(0,),
                         combos=[frozenset()], processes=0)
    assert len(prof.cells) == len(sits)
    by_id = {s.id: s for s in sits}
    for c in prof.cells:
        sit = by_id[c["situation"]]
        assert c["map_set"] == sit.map_set and c["refusable"] is sit.refusable
    assert {c["map_set"] for c in prof.cells} == {"space", "land"}
    assert {c["refusable"] for c in prof.cells} == {True, False}


@pytest.mark.parametrize("swap", (False, True))
@pytest.mark.parametrize("family", [f for f in FAMILIES if f != "flat"])
def test_item6_larger_skilled_side_attacks_smaller_one_holds(family, swap):
    """SPEC 14.5 item 6: with S1 (which holds on this family) the skilled side attacks when it has more heads
    (ratio 0.5) and holds when it has fewer (ratio 2.0); the decision is by headcount."""
    sit = _sit(family)
    build = _m("plays").build_scenario(sit, frozenset({"S1"}), 8)
    skilled, naive = _labels(swap)
    orders = lambda scn, label: {g["order"] for g in scn["groups"] if g["side"] == label}
    larger, smaller = build(0.5, swap), build(2.0, swap)
    assert orders(larger, skilled) == {"attack_move"}
    assert orders(smaller, skilled) == {"hold"}
    assert orders(larger, naive) == {"attack_move"} and orders(smaller, naive) == {"attack_move"}
    assert sum(_heads(larger, skilled).values()) == 8 and sum(_heads(larger, naive).values()) == 4


# ------------------------------------------------------------------ item 7: hidden-layer spawn

CROSS = (None, "LA", "LB", "LC")
COMBOS = (frozenset(), frozenset({"S3"}), frozenset({"S3", "S4"}))
SAMPLES = (("barrier_ramp", 3), ("all", 4))


def _sample(kind, seed):
    fams = ("barrier_ramp",) if kind == "barrier_ramp" else None
    return _m("situation").sample_situations(40, seed, families=fams)


def _open_on(built, x, y, layer):
    rc = terrain.cell_of(built.w_cells, built.h_cells, built.cell, x, y)
    return rc is not None and bool(built.open[rc[1] * built.w_cells + rc[0]] & (1 << (layer - 1)))


@pytest.mark.parametrize("config", CROSS, ids=str)
@pytest.mark.parametrize("kind,seed", SAMPLES)
def test_item7_every_sampled_situation_builds_with_the_naive_side_on_open_cells(kind, seed, config):
    """SPEC 14.5 item 7: no 'not open on that layer' ValueError for any family, combo or swap, and under a
    cross-layer config the naive side's spawn cells are open on the hidden layer."""
    plays = _m("plays")
    failures = []
    for sit in _sample(kind, seed):
        for combo in COMBOS:
            build = plays.build_scenario(sit, combo, 8, config=config)
            for swap in (False, True):
                try:
                    scn = build(1.0, swap)
                except ValueError as e:
                    if "on that layer" in str(e):
                        failures.append((sit.id, sit.family, sit.hidden["layer"], sorted(combo), swap, str(e)))
                    continue
                if config is None:
                    continue
                scenario.to_c(scn)                          # the loader's own spawn check
                built = terrain.build(scn["terrain"])
                naive = "A" if swap else "B"
                units = [u for u in _units(scn["groups"]) if u["side"] == naive]
                assert units and {u["layer"] for u in units} == {sit.hidden["layer"]}
                for u in units:
                    if not _open_on(built, u["x"], u["y"], sit.hidden["layer"]):
                        failures.append((sit.id, sit.family, "naive spawn closed", sorted(combo), swap))
                        break
    assert not failures, failures[:5]


@pytest.mark.parametrize("kind,seed", SAMPLES)
def test_item7_sampled_hidden_layer_is_open_at_both_anchors_and_validate_is_clean(kind, seed):
    """SPEC 14.5 item 7: sample_situations picks hidden.layer where both anchors are open; validate finds nothing."""
    situation = _m("situation")
    for sit in _sample(kind, seed):
        built = terrain.build({**{"w_cells": 80, "h_cells": 40, "cell": 50.0, "layer_spacing": 0.0}, **sit.terrain})
        for anchor in (sit.anchor_A, sit.anchor_B):
            assert _open_on(built, anchor[0], anchor[1], sit.hidden["layer"]), (sit.id, sit.family, anchor)
        assert situation.validate(sit) == [], sit.id


# A block of height 2 closes layers 1 and 2 over cells 7..12 x 17..22 (x 350..650, y 850..1150), around anchor A.
CLOSED_AT_ANCHOR = {"preset": "block", "bw": 6, "bh": 6, "h": 2, "cx": 10, "cy": 20, "layer_spacing": 0.0}


def _hand_sit(hidden_layer):
    return dataclasses.replace(_sit("block"), terrain=dict(CLOSED_AT_ANCHOR), anchor_A=(500.0, 1000.0),
                               anchor_B=(3500.0, 1000.0), facing_A=0.0, facing_B=180.0, layer=3,
                               approach_distance=3000.0, hidden={"route": 0, "layer": hidden_layer})


def test_item7_validate_reports_an_anchor_closed_on_the_hidden_layer():
    """SPEC 14.5 item 7 positive control: hidden layer 2 is closed at anchor A (layer 3 is open there)."""
    situation = _m("situation")
    sit = _hand_sit(2)
    built = terrain.build({**{"w_cells": 80, "h_cells": 40, "cell": 50.0}, **sit.terrain})
    assert _open_on(built, 500.0, 1000.0, 3) and not _open_on(built, 500.0, 1000.0, 2)     # the fixture is right
    reasons = situation.validate(sit)
    assert reasons and any("hidden" in r.lower() for r in reasons), reasons
    assert not any("not open on layer 3" in r for r in reasons)


def test_item7_validate_is_clean_when_the_hidden_layer_is_open_at_the_anchors():
    """SPEC 14.5 item 7 negative control: the same map with hidden layer 3 (open) reports nothing."""
    assert _m("situation").validate(_hand_sit(3)) == []


@pytest.mark.parametrize("kind,seed", SAMPLES)
def test_item7_sampling_is_reproducible(kind, seed):
    """SPEC 14.5 item 7: same seed, same situations, twice (the resample is deterministic: next draw)."""
    assert _sample(kind, seed) == _sample(kind, seed)


# ------------------------------------------------------------------ item 8: report functions

def _report():
    spec = importlib.util.spec_from_file_location("baseline_report_under_test", LAB / "experiments" / "baseline_report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXACT = [(x, 2.0 * x) for x in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)]            # y = 2 x, ln-ln slope 1


def test_item8_fit_loglog_exact_power_law():
    """SPEC 14.5 item 8: y = 2 x gives slope 1, intercept ln 2, r2 1, n 7."""
    fit = _report().fit_loglog(EXACT)
    assert fit["n"] == 7
    assert fit["slope"] == pytest.approx(1.0, abs=1e-9)
    assert fit["intercept"] == pytest.approx(math.log(2.0), abs=1e-9)
    assert fit["r2"] == pytest.approx(1.0, abs=1e-9)
    steeper = _report().fit_loglog([(x, 3.0 * x ** 1.5) for x in (1.0, 2.0, 4.0, 8.0)])
    assert steeper["slope"] == pytest.approx(1.5, abs=1e-9) and steeper["r2"] == pytest.approx(1.0, abs=1e-9)


NOISY = [(1.0, 2.1), (1.5, 2.5), (2.0, 4.6), (3.0, 5.2), (4.0, 9.5), (6.0, 10.4), (8.0, 19.0), (10.0, 17.0)]


def test_item8_fit_loglog_noisy_matches_least_squares():
    """SPEC 14.5 item 8: on noisy data the fit is ordinary least squares in ln-ln and r2 is below 1."""
    lx, ly = np.log([p[0] for p in NOISY]), np.log([p[1] for p in NOISY])
    slope, intercept = np.polyfit(lx, ly, 1)
    r2 = 1.0 - ((ly - (slope * lx + intercept)) ** 2).sum() / ((ly - ly.mean()) ** 2).sum()
    fit = _report().fit_loglog(NOISY)
    assert fit["n"] == len(NOISY)
    assert fit["slope"] == pytest.approx(slope, abs=1e-9)
    assert fit["intercept"] == pytest.approx(intercept, abs=1e-9)
    assert fit["r2"] == pytest.approx(r2, abs=1e-9) and fit["r2"] < 0.999


def test_item8_off_line_flags_a_planted_outlier():
    """SPEC 14.5 item 8 positive control: one point three times too high (residual ln 3) is the only one flagged."""
    rep = _report()
    outlier = (3.0, 2.0 * 3.0 * 3.0)
    pts = [p for p in EXACT if p[0] != 3.0] + [outlier]
    assert rep.off_line(pts, {"slope": 1.0, "intercept": math.log(2.0), "r2": 1.0, "n": len(pts)}) == [outlier]
    contaminated = rep.fit_loglog(pts)                     # the outlier drags the fit; it is still the one flagged
    assert rep.off_line(pts, contaminated) == [outlier]
    assert rep.off_line(pts, contaminated, thresh=5.0) == []


def test_item8_off_line_negative_control_and_threshold():
    """SPEC 14.5 item 8 negative control: points on the line are flagged by nobody; thresh is respected."""
    rep = _report()
    assert rep.off_line(EXACT, rep.fit_loglog(EXACT)) == []
    fit = {"slope": 1.0, "intercept": math.log(2.0), "r2": 1.0, "n": 1}
    near = (2.0, 4.0 * math.exp(0.2))                      # residual 0.2: inside the default 0.25
    far = (2.0, 4.0 * math.exp(0.3))                       # residual 0.3: outside it
    assert rep.off_line([near], fit) == [] and rep.off_line([far], fit) == [far]
    assert rep.off_line([near], fit, thresh=0.1) == [near]


def _cell(sit, combo="1", map_set="space", valid=True, config="base", equal=1.2, at=2.0, value=4.0, **over):
    c = {"sit": sit, "family": "flat" if map_set == "space" else "barrier_ramp", "size": 8, "config": config,
         "combo": combo, "value": value, "r0": 2.0, "premium": 1.5, "valid": valid, "flags": [],
         "map_set": map_set, "refusable": True, "value_cost": value, "firing_adv_at_rstar": at,
         "firing_adv_equal": equal, "win_margin": 0.02, "windows": []}
    c.update(over)
    return c


def test_item8_c1_share_counts_valid_space_cells_of_the_combo():
    """SPEC 14.5 item 8: share of valid space cells of the combo with firing_adv_equal above 1.0 (not equal to it)."""
    rep = _report()
    cells = [_cell(1, equal=1.5), _cell(2, equal=1.01), _cell(3, equal=0.9), _cell(4, equal=1.0),     # 2 of 4
             _cell(5, equal=9.0, valid=False), _cell(6, equal=9.0, map_set="land"),                  # not counted
             _cell(7, combo="2", equal=9.0), _cell(8, combo="12", equal=0.1)]                        # other combos
    assert rep.c1_share(cells, "1") == pytest.approx(0.5)
    assert rep.c1_share(cells, "2") == pytest.approx(1.0)
    assert rep.c1_share(cells, "12") == pytest.approx(0.0)
    assert rep.c1_share(cells, "345") is None


def _power_cells(n=8, config="base", map_set="space", start=1000):
    return [_cell(start + i, config=config, map_set=map_set, at=1.0 + i, value=2.0 * (1.0 + i) ** 1.5)
            for i in range(n)]


def test_item8_plot_rule_set_writes_a_png_and_returns_slope_and_r2(tmp_path):
    """SPEC 14.5 item 8: a non-empty PNG (log-log R* against firing_adv_at_rstar), the text holds slope 1.50 and
    r2 1.00; invalid, land and other-config cells do not enter the fit."""
    pytest.importorskip("matplotlib")
    rep = _report()
    cells = (_power_cells()
             + [_cell(2000, valid=False, at=5.0, value=0.5), _cell(2001, map_set="land", at=5.0, value=0.5),
                _cell(2002, config="LA", at=5.0, value=0.5), _cell(2003, at=None, value=3.0)])
    out = tmp_path / "base_space.png"
    text = rep.plot_rule_set(cells, "base", str(out))
    assert out.exists() and out.stat().st_size > 1000
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert isinstance(text, str) and "slope" in text.lower() and ("r2" in text.lower() or "r squared" in text.lower())
    assert "1.50" in text and "1.00" in text
    for stray in ("2000", "2001", "2002", "2003"):
        assert stray not in text


def test_item8_plot_rule_set_lists_the_off_line_points_and_does_a_land_plot(tmp_path):
    """SPEC 14.5 item 8: the printed text names the sit id of a planted outlier (and of no on-line point); a land
    plot is a second file from the same function."""
    pytest.importorskip("matplotlib")
    rep = _report()
    cells = _power_cells(10) + [_cell(4242, at=3.0, value=2.0 * 3.0 ** 1.5 * 3.0)]
    text = rep.plot_rule_set(cells, "base", str(tmp_path / "s.png"))
    assert "4242" in text
    assert not any(str(1000 + i) in text for i in range(10))
    land = _power_cells(map_set="land", start=3000)
    land_text = rep.plot_rule_set(cells + land, "base", str(tmp_path / "l.png"), map_set="land")
    assert (tmp_path / "l.png").stat().st_size > 1000 and "1.50" in land_text and "4242" not in land_text
