"""Rung K0 tests (SPEC.md section 14.1): layerlab/skill/ cost.py, margin.py, fight.py, rstar.py, controls.py.

Red until the package layerlab/skill/ exists (ModuleNotFoundError on the imports below).

Layout: (1) cost, (2) margin on hand-built stand-in results, (3) fight and the light runner,
(4) the pure solver pieces (isotonic fit, zero crossing), (5) the R* logic against a SCRIPTED runner
(`layerlab.skill.rstar.run_fights` is replaced, so no C fights), (6) the two controls (real fights;
a few seconds each: fights take about 4 ms, a scan is about 80 of them).

Conventions the tests fix where SPEC 14.1 is silent (reported to the Architect):
  * `group` in a `side_units` row is the index into `scn["groups"]`.
  * `isotonic_nonincreasing` is the unweighted least-squares fit (the xs only order the points).
  * `margin_A_label` and `margin_B_label` are the means of the fights' own A-minus-B margin on each
    label (so for a skilled side on label B the skilled margin is `-margin_B_label`), which is what
    makes `label_gap = max |margin_A_label + margin_B_label|` the side-label bias.
  * `first_loss` and `last_win` may be taken over all points (refined included) or the scanned ones;
    the tests only require that they bracket the crossing.

Revised for SPEC 14.5 (test-defect fix, Architect-approved): the scripted fixtures build real group scenarios
(one raider group per side, counts from the ratio, as test_skill_k0r.py does) because `rstar` now reports the
cost ratio from the scenarios, and the scripted fight results carry alive_ticks, firing_ticks and heads. The
default `win_margin` is 0.02 (14.5 item 2), which moves every planted crossing a little (2.5 becomes about
2.4333); these tests are about the solver's other behaviour, so the scripted `Script.run` passes
`win_margin=0.0` unless a test gives its own, which keeps the planted numbers. The win margin itself is
tested in test_skill_k0r.py.
"""
import copy
import dataclasses
import importlib
import itertools
from types import SimpleNamespace

import pytest

from conftest import add_type, grp, make_scenario
from layerlab import ffi, scenario
from layerlab.ffi import WIN_A, WIN_B, WIN_CAP, WIN_MUTUAL, WIN_STALEMATE
from layerlab.run import run
from layerlab.skill.controls import advantage_control, mirror_control
from layerlab.skill.cost import counts_for_cost, force_cost, side_units, unit_cost
from layerlab.skill.margin import effective_margin, margin

# The package attributes `fight` and `rstar` may be the functions, so take the modules explicitly.
fightmod = importlib.import_module("layerlab.skill.fight")
rstarmod = importlib.import_module("layerlab.skill.rstar")
fight, measure_rate, run_fights = fightmod.fight, fightmod.measure_rate, fightmod.run_fights
FightResult = fightmod.FightResult
RATIOS, rstar = rstarmod.RATIOS, rstarmod.rstar
isotonic_nonincreasing, zero_crossing = rstarmod.isotonic_nonincreasing, rstarmod.zero_crossing

BASTION = 1050.0 * 7.0 / 1.8 / 31.25      # 130.666..., the rule `hp * dmg / interval_s / 31.25`
RAIDER = 90.0                             # 250 * 9 / 0.8 / 31.25


# =========================================================================== (1) cost


def _mixed():
    """Five groups interleaving the sides: spawn order is A raider x2, B bastion, A bastion, B raider x2, B seer."""
    return make_scenario([
        grp("A", "raider", 500, 500, 3, count=2),
        grp("B", "bastion", 3000, 500, 3, count=1),
        grp("A", "bastion", 500, 1000, 3, count=1),
        grp("B", "raider", 3000, 1000, 3, count=2),
        grp("B", "seer", 3000, 1500, 3, count=1),
    ])


def test_unit_cost_base_types():
    """SPEC 14.1 cost.py: explicit `cost` wins; otherwise hp * dmg / interval_s / 31.25 (raider 90,
    bastion 130.7); seer 120 and caster 150 are explicit in base.toml."""
    scn = make_scenario()
    assert unit_cost(scn, "raider") == pytest.approx(RAIDER, abs=1e-9)
    assert unit_cost(scn, "bastion") == pytest.approx(BASTION, abs=1e-9)
    assert unit_cost(scn, "bastion") == pytest.approx(130.7, abs=0.05)
    assert unit_cost(scn, "seer") == 120.0
    assert unit_cost(scn, "caster") == 150.0


def test_unit_cost_rule_for_an_unlisted_type_and_explicit_override():
    """SPEC 14.1: a type with no cost follows the rule (interceptor 325 * 6 / 1.0 / 31.25 = 62.4);
    the same stats with an explicit cost return the explicit number (the formula is not applied)."""
    scn = make_scenario()
    assert unit_cost(scn, "interceptor") == pytest.approx(62.4, abs=1e-9)
    add_type(scn, "pricey", "interceptor", cost=777.0)
    assert unit_cost(scn, "pricey") == 777.0


def test_unit_cost_equals_the_loader_cost_for_every_type():
    """SPEC 14.1 ('already used by the loader'): unit_cost is the cost to_c puts in the C type table."""
    scn = make_scenario([grp("A", "raider", 500, 500, 3)])
    sc = scenario.to_c(scn)
    for i, name in enumerate(scn["types"]):
        assert unit_cost(scn, name) == pytest.approx(sc.types[i].cost, rel=1e-12), name


def test_side_units_order_and_fields_match_to_c():
    """SPEC 14.1: one row per spawned unit in the order of to_c (groups in order, units within a group in
    order); keys side, type, cost, hp0, group (group = index into scn['groups'])."""
    scn = _mixed()
    rows = side_units(scn)
    sc = scenario.to_c(scn)
    names = list(scn["types"])
    assert len(rows) == sc.n_spawns == 7
    assert [r["side"] for r in rows] == [sc.spawns[i].side for i in range(7)] == [0, 0, 1, 0, 1, 1, 1]
    assert [r["type"] for r in rows] == [names[sc.spawns[i].type] for i in range(7)]
    assert [r["type"] for r in rows] == ["raider", "raider", "bastion", "bastion", "raider", "raider", "seer"]
    assert [r["group"] for r in rows] == [0, 0, 1, 2, 3, 3, 4]
    assert [r["hp0"] for r in rows] == [250.0, 250.0, 1050.0, 1050.0, 250.0, 250.0, 80.0]
    want = [RAIDER, RAIDER, BASTION, BASTION, RAIDER, RAIDER, 120.0]
    assert [r["cost"] for r in rows] == pytest.approx(want, abs=1e-9)
    for r in rows:
        assert set(r) >= {"side", "type", "cost", "hp0", "group"}


def test_side_units_empty_scenario_is_empty():
    """SPEC 14.1 (negative twin): no groups, no rows."""
    assert side_units(make_scenario()) == []


def test_force_cost_sums_per_side():
    """SPEC 14.1: force_cost is the sum of cost over that side's units (A: 2 raiders + bastion;
    B: bastion + 2 raiders + seer); a side with no units costs 0."""
    scn = _mixed()
    assert force_cost(scn, 0) == pytest.approx(2 * RAIDER + BASTION, abs=1e-9)
    assert force_cost(scn, 1) == pytest.approx(BASTION + 2 * RAIDER + 120.0, abs=1e-9)
    only_a = make_scenario([grp("A", "raider", 500, 500, 3, count=3)])
    assert force_cost(only_a, 0) == pytest.approx(3 * RAIDER, abs=1e-9)
    assert force_cost(only_a, 1) == 0.0


def _flat_priced():
    """Types t1..t4, every one cost 100 exactly, so unit counts are cost shares times total / 100."""
    scn = make_scenario()
    for name in ("t1", "t2", "t3", "t4"):
        add_type(scn, name, "raider", cost=100.0)
    return scn


def test_counts_single_type_hits_cost_within_one_unit():
    """SPEC 14.1: one type: the cost is as close to total_cost as the unit size allows (1000 / 90 = 11.1:
    11 raiders, 990)."""
    scn = make_scenario()
    out = counts_for_cost({"raider": 1.0}, 1000.0, scn)
    assert out == {"raider": 11}
    assert abs(out["raider"] * RAIDER - 1000.0) <= RAIDER


def test_counts_shares_of_cost_are_respected_half_and_half():
    """SPEC 14.1: 50/50 raider/bastion for 1000: each type's cost is near 500 (within one of its units),
    total within one unit of 1000, both present."""
    scn = make_scenario()
    out = counts_for_cost({"raider": 0.5, "bastion": 0.5}, 1000.0, scn)
    assert set(out) == {"raider", "bastion"}
    c_r, c_b = out["raider"] * RAIDER, out["bastion"] * BASTION
    assert abs(c_r - 500.0) <= RAIDER and abs(c_b - 500.0) <= BASTION
    assert abs(c_r + c_b - 1000.0) <= BASTION


def test_counts_positive_share_gets_at_least_one_unit():
    """SPEC 14.1: every positive share gets at least 1 unit, even a tiny one (0.1% of 1000 is far below one
    bastion). Negative twin: a zero share gets no unit."""
    scn = make_scenario()
    for tiny in (0.01, 0.001):
        out = counts_for_cost({"raider": 1.0 - tiny, "bastion": tiny}, 1000.0, scn)
        assert out["bastion"] >= 1 and out["raider"] >= 1, out
    out = counts_for_cost({"raider": 1.0, "bastion": 0.0}, 1000.0, scn)
    assert out.get("bastion", 0) == 0 and out["raider"] >= 1


def test_counts_zero_total_or_empty_shares_give_empty():
    """SPEC 14.1: total_cost 0 or empty shares give {}."""
    scn = make_scenario()
    assert counts_for_cost({"raider": 1.0}, 0, scn) == {}
    assert counts_for_cost({"raider": 1.0}, 0.0, scn) == {}
    assert counts_for_cost({}, 1000.0, scn) == {}
    assert counts_for_cost({}, 0, scn) == {}


def test_counts_largest_remainder_by_hand():
    """SPEC 14.1 largest-remainder rounding on cost shares. All four types cost 100, total 1000:
    shares 0.5 / 0.375 / 0.125 -> ideal 5 / 3.75 / 1.25, floors 5 / 3 / 1 = 900, one unit left,
    the largest remainder (0.75, t2) takes it -> 5 / 4 / 1."""
    scn = _flat_priced()
    out = counts_for_cost({"t1": 0.5, "t2": 0.375, "t3": 0.125}, 1000.0, scn)
    assert out == {"t1": 5, "t2": 4, "t3": 1}
    # shares 0.5 / 0.25 / 0.25 of 1100 -> ideal 5.5 / 2.75 / 2.75, floors 5 / 2 / 2 = 900, two units left;
    # remainders 0.5 / 0.75 / 0.75: t2 and t3 take them -> 5 / 3 / 3 (t1 with the smaller remainder does not).
    out = counts_for_cost({"t1": 0.5, "t2": 0.25, "t3": 0.25}, 1100.0, scn)
    assert out == {"t1": 5, "t2": 3, "t3": 3}


def test_counts_ties_go_to_the_type_listed_first_and_are_deterministic():
    """SPEC 14.1: four equal shares of 1000 at cost 100 each: ideal 2.5 each, two units left, equal
    remainders, so the first two listed take them. Listing the types in the other order moves the extras;
    the same call twice gives the same answer."""
    scn = _flat_priced()
    fwd = {"t1": 0.25, "t2": 0.25, "t3": 0.25, "t4": 0.25}
    assert counts_for_cost(fwd, 1000.0, scn) == {"t1": 3, "t2": 3, "t3": 2, "t4": 2}
    assert counts_for_cost(fwd, 1000.0, scn) == counts_for_cost(dict(fwd), 1000.0, scn)
    rev = {"t4": 0.25, "t3": 0.25, "t2": 0.25, "t1": 0.25}
    assert counts_for_cost(rev, 1000.0, scn) == {"t1": 2, "t2": 2, "t3": 3, "t4": 3}


# =========================================================================== (2) margin


def _cd():
    """A: cheap (10), dear (30); B: cheap, dear. Spawn order A cheap, A dear, B cheap, B dear; hp0 250."""
    scn = make_scenario([
        grp("A", "cheap", 500, 500, 3), grp("A", "dear", 600, 500, 3),
        grp("B", "cheap", 3000, 500, 3), grp("B", "dear", 3100, 500, 3),
    ])
    add_type(scn, "cheap", "raider", cost=10.0)
    add_type(scn, "dear", "raider", cost=30.0)
    return scn


FULL, HALF, DEAD = (250.0, 1), (125.0, 1), (0.0, 0)


def _res(units, winner=WIN_A):
    """A stand-in for layerlab.run.Result: only `winner` and `unit` (hp, alive per spawn index)."""
    return SimpleNamespace(winner=winner, unit=[{"hp": hp, "alive": alive} for hp, alive in units])


def test_margin_extremes():
    """SPEC 14.1: a side fully alive has share 1, all dead 0: A full and B dead is +1, the reverse -1,
    both full or both dead 0."""
    scn = _cd()
    assert margin(_res([FULL, FULL, DEAD, DEAD]), scn) == 1.0
    assert margin(_res([DEAD, DEAD, FULL, FULL]), scn) == -1.0
    assert margin(_res([FULL, FULL, FULL, FULL]), scn) == 0.0
    assert margin(_res([DEAD, DEAD, DEAD, DEAD]), scn) == 0.0


def test_margin_is_share_a_minus_share_b_exactly():
    """SPEC 14.1: A lost its cheap unit: share_A = 30/40 = 0.75. B's cheap unit at half hp: share_B =
    (10 * 0.5 + 30) / 40 = 0.875. margin = -0.125."""
    scn = _cd()
    assert margin(_res([DEAD, FULL, HALF, FULL]), scn) == pytest.approx(-0.125, abs=1e-12)


def test_margin_weights_by_cost():
    """SPEC 14.1: cost weighting: A losing its cheap unit (B untouched) is -0.25, losing its dear unit
    -0.75; the two differ."""
    scn = _cd()
    lose_cheap = margin(_res([DEAD, FULL, FULL, FULL]), scn)
    lose_dear = margin(_res([FULL, DEAD, FULL, FULL]), scn)
    assert lose_cheap == pytest.approx(-0.25, abs=1e-12)
    assert lose_dear == pytest.approx(-0.75, abs=1e-12)
    assert lose_cheap != lose_dear


def test_margin_counts_only_units_alive_at_the_end():
    """SPEC 14.1: 'units alive at the end': a dead unit adds nothing even when its recorded hp is stale
    (negative twin of the hp term)."""
    scn = _cd()
    stale_dead = (250.0, 0)
    assert margin(_res([stale_dead, FULL, FULL, FULL]), scn) == pytest.approx(-0.25, abs=1e-12)


def test_margin_in_unit_interval_and_antisymmetric_in_a_symmetric_scenario():
    """SPEC 14.1: margin lies in [-1, 1] (all 81 hp states of four units); with equal forces, exchanging
    the sides' end states negates it."""
    scn = _cd()
    for a0, a1, b0, b1 in itertools.product((FULL, HALF, DEAD), repeat=4):
        m = margin(_res([a0, a1, b0, b1]), scn)
        assert -1.0 <= m <= 1.0
        assert margin(_res([b0, b1, a0, a1]), scn) == pytest.approx(-m, abs=1e-12)


def test_margin_side_with_no_units_has_share_zero():
    """SPEC 14.1: a side with no units has share 0 (not a division error): only A spawned, A full -> 1."""
    scn = make_scenario([grp("A", "raider", 500, 500, 3, count=2)])
    assert margin(_res([FULL, FULL]), scn) == pytest.approx(1.0, abs=1e-12)
    assert margin(_res([DEAD, DEAD]), scn) == 0.0


def test_effective_margin_win_a_win_b_mutual():
    """SPEC 14.1: for win_A, win_B and mutual the effective margin is the raw margin and the outcome maps
    from the winner code."""
    scn = _cd()
    ra = _res([FULL, HALF, DEAD, DEAD], WIN_A)
    rb = _res([DEAD, DEAD, HALF, FULL], WIN_B)
    rm = _res([DEAD, DEAD, DEAD, DEAD], WIN_MUTUAL)
    assert effective_margin(ra, scn) == (margin(ra, scn), "win_A") and margin(ra, scn) > 0
    assert effective_margin(rb, scn) == (margin(rb, scn), "win_B") and margin(rb, scn) < 0
    assert effective_margin(rm, scn) == (0.0, "mutual")


@pytest.mark.parametrize("code,name", [(WIN_STALEMATE, "stalemate"), (WIN_CAP, "cap")])
def test_effective_margin_stalemate_and_cap_are_zero_whatever_the_raw_margin(code, name):
    """SPEC 14.1: a stalemate or a cap gives (0.0, outcome) even when the raw margin is far from 0
    (a stalemate is not a win, README 4.2). Positive control: the raw margin of this state is not 0."""
    scn = _cd()
    res = _res([FULL, FULL, HALF, DEAD], code)
    assert margin(res, scn) != 0.0
    m, outcome = effective_margin(res, scn)
    assert (m, outcome) == (0.0, name)


# =========================================================================== (3) fight and the light runner


def _close(a=3, b=3, **kw):
    """A small fast fight: a raiders against b raiders, 800 apart, both attack-move at each other."""
    return make_scenario([
        grp("A", "raider", 1000, 1000, 3, count=a, order="attack_move", goal=[1800.0, 1000.0], spacing=50.0),
        grp("B", "raider", 1800, 1000, 3, count=b, order="attack_move", goal=[1000.0, 1000.0], spacing=50.0,
            facing=180.0),
    ], **kw)


def _bad():
    """A group far outside the 4000 x 2000 arena: the loader raises ValueError."""
    scn = _close()
    scn["groups"][0]["y"] = 5000.0
    return scn


def test_fight_equals_manual_run_plus_margin():
    """SPEC 14.1: fight(scn, seed) is the manual run with the margin and outcome filled in."""
    scn = _close()
    for seed in (0, 1, 2):
        res = run(scn, seed=seed)
        m, outcome = effective_margin(res, scn)
        fr = fight(scn, seed)
        assert fr.margin == m and fr.outcome == outcome
        assert fr.raw_margin == margin(res, scn)
        assert fr.ticks == res.ticks
        assert fr.first_contact_tick == res.first_contact_tick
        assert tuple(fr.survivors) == tuple(res.survivors)
        assert fr.contact is True and fr.first_contact_tick >= 0 and fr.error is None
    assert fight(scn, 0) == fight(scn, 0)


def test_fight_default_seed_is_zero():
    """SPEC 14.1: fight(scn, seed=0, lib='O2')."""
    scn = _close()
    assert fight(scn) == fight(scn, 0)


def test_fight_result_carries_only_deterministic_fields():
    """SPEC 14.1: FightResult fields; no wall-time field and no trace."""
    names = {f.name for f in dataclasses.fields(FightResult)}
    assert {"margin", "raw_margin", "outcome", "ticks", "first_contact_tick", "contact", "survivors",
            "error"} <= names
    assert not any("second" in n or "time" in n or n == "trace" for n in names), names


def test_fight_runs_with_trace_off(monkeypatch):
    """SPEC 14.1: fight runs with trace=False. run() only builds an ffi.ll_trace when trace=True, so a
    tripwire on that class fails the test if the light runner ever traces. Positive control first: with
    the tripwire in place a traced run does trip it."""
    def tripwire(*a, **k):
        raise AssertionError("a trace buffer was requested")

    monkeypatch.setattr(ffi, "ll_trace", tripwire)
    with pytest.raises(AssertionError, match="trace buffer"):
        run(_close(), seed=0, trace=True)
    fr = fight(_close(), 0)
    assert fr.contact is True


def test_fight_no_contact_and_cap_and_stalemate_outcomes():
    """SPEC 14.1: first_contact_tick is -1 and contact False when nobody sees anybody (layer 5 against
    layer 1, holding: a stalemate, margin 0); a cap likewise has margin 0.0."""
    scn = _close()
    for g, layer in zip(scn["groups"], (5, 1)):
        g["layer"], g["order"] = layer, "hold"
    fr = fight(scn, 0)
    assert (fr.outcome, fr.margin, fr.contact, fr.first_contact_tick) == ("stalemate", 0.0, False, -1)
    capped = fight(_close(run={"max_ticks": 5}), 0)
    assert (capped.outcome, capped.margin) == ("cap", 0.0)


def _jobs():
    return [(_close(3, 3), 0), (_close(2, 4), 1), (_close(4, 2), 2), (_close(3, 3), 3), (_bad(), 4)]


def test_run_fights_preserves_job_order():
    """SPEC 14.1: results in job order. The jobs differ (3v3, 2v4, 4v2), so a shuffled order shows."""
    jobs = _jobs()[:4]
    want = [fight(s, seed) for s, seed in jobs]
    assert len({fr.margin for fr in want}) >= 3, "premise: the jobs must give distinguishable results"
    assert run_fights(jobs) == want
    assert run_fights(jobs, processes=0) == want and run_fights(jobs, processes=1) == want


def test_run_fights_pooled_equals_serial():
    """SPEC 14.1: processes > 1 uses a process pool and gives the very same results (error job included)."""
    jobs = _jobs()
    serial = run_fights(jobs, processes=None)
    assert run_fights(jobs, processes=2) == serial
    assert len(serial) == len(jobs)


def test_run_fights_error_job_is_a_result_not_an_exception():
    """SPEC 14.1: a scenario that raises ValueError gives outcome 'error', margin 0.0, contact False and the
    message in `error` (the loader's own message); the other jobs are unaffected. Premise checked first."""
    with pytest.raises(ValueError) as exc:
        scenario.to_c(_bad())
    good = fight(_close(), 0)
    out = run_fights([(_close(), 0), (_bad(), 1), (_close(), 0)])
    assert out[0] == good and out[2] == good and out[0].error is None
    bad = out[1]
    assert bad.outcome == "error" and bad.margin == 0.0 and bad.contact is False
    assert bad.error == str(exc.value)


def test_measure_rate_reports_fights_seconds_and_rate():
    """SPEC 14.1: measure_rate returns fights, seconds, fights_per_second (> 0, consistent)."""
    out = measure_rate(_close(), (0, 1, 2), processes=0, lib="O2")
    assert out["fights"] == 3
    assert out["seconds"] > 0 and out["fights_per_second"] > 0
    assert out["fights_per_second"] == pytest.approx(out["fights"] / out["seconds"], rel=1e-6)


# =========================================================================== (4) pure solver pieces


def _brute_isotonic(ys):
    """Exhaustive least squares: the best non-increasing fit is a set of contiguous block means; try every
    split and keep the non-increasing one with the least squared error."""
    n, best = len(ys), None
    for mask in range(1 << (n - 1)):
        blocks, start = [], 0
        for i in range(n - 1):
            if mask >> i & 1:
                blocks.append(ys[start:i + 1])
                start = i + 1
        blocks.append(ys[start:])
        means = [sum(b) / len(b) for b in blocks]
        if any(means[i] < means[i + 1] for i in range(len(means) - 1)):
            continue
        fit = [m for b, m in zip(blocks, means) for _ in b]
        sse = sum((y - f) ** 2 for y, f in zip(ys, fit))
        if best is None or sse < best[0] - 1e-12:
            best = (sse, fit)
    return best[1]


def test_isotonic_leaves_a_nonincreasing_input_unchanged():
    """SPEC 14.1: pool-adjacent-violators leaves a non-increasing series alone (plateaus included)."""
    ys = [5.0, 4.0, 3.0, 3.0, 1.0, -2.0]
    out = isotonic_nonincreasing(list(range(len(ys))), ys)
    assert isinstance(out, list) and out == pytest.approx(ys, abs=1e-12)


def test_isotonic_one_violation_pools_to_the_mean():
    """SPEC 14.1: [4, 1, 3, 0]: the pair (1, 3) rises, pools to 2: [4, 2, 2, 0]."""
    out = isotonic_nonincreasing([1, 2, 3, 4], [4.0, 1.0, 3.0, 0.0])
    assert out == pytest.approx([4.0, 2.0, 2.0, 0.0], abs=1e-12)


def test_isotonic_cascading_pool_by_hand():
    """SPEC 14.1: [1, 3, 2, 2.5]: (1, 3) pools to 2; 2 does not rise over it; 2.5 does, so it pools with the
    2 (2.25), which now rises over the first block, so all four pool to the mean 2.125 (hand-computed PAV)."""
    out = isotonic_nonincreasing([0, 1, 2, 3], [1.0, 3.0, 2.0, 2.5])
    assert out == pytest.approx([2.125] * 4, abs=1e-12)


@pytest.mark.parametrize("ys", [
    [1.0, 3.0, 2.0, 2.5],
    [3.0, 1.0, 2.0, 0.0, 4.0, 1.0],
    [0.2, -0.1, 0.4, -0.3, -0.2],
    [0.0, 0.0, 1.0, 0.0],
])
def test_isotonic_matches_brute_force_least_squares(ys):
    """SPEC 14.1: the fit is THE least-squares non-increasing fit: equal to an exhaustive search over
    block partitions; output non-increasing, same length, idempotent. (xs only order the points; weights
    are equal: the xs here are deliberately uneven.)"""
    xs = [0.5 * (1.7 ** i) for i in range(len(ys))]
    out = isotonic_nonincreasing(xs, ys)
    assert len(out) == len(ys)
    assert all(out[i] >= out[i + 1] - 1e-12 for i in range(len(out) - 1))
    assert out == pytest.approx(_brute_isotonic(ys), abs=1e-9)
    assert isotonic_nonincreasing(xs, out) == pytest.approx(out, abs=1e-12)


def test_zero_crossing_linear_interpolation():
    """SPEC 14.1: where the fitted curve crosses 0 going down: (2, 0.2) to (3, -0.2) crosses at 2.5; with
    uneven xs (1, 0.25) to (2, -0.25) at 1.5."""
    assert zero_crossing([1.0, 2.0, 3.0], [0.4, 0.2, -0.2]) == pytest.approx(2.5, abs=1e-12)
    assert zero_crossing([0.5, 1.0, 2.0], [0.5, 0.25, -0.25]) == pytest.approx(1.5, abs=1e-12)


def test_zero_crossing_is_none_when_always_positive_or_never_positive():
    """SPEC 14.1: None when above 0 at every point (beats the whole scan) and None when at or below 0 at
    every point (including all zero)."""
    assert zero_crossing([1.0, 2.0, 3.0], [0.3, 0.2, 0.1]) is None
    assert zero_crossing([1.0, 2.0], [0.0, -0.1]) is None
    assert zero_crossing([1.0, 2.0], [-0.1, -0.2]) is None
    assert zero_crossing([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) is None


def test_zero_crossing_flat_zero_segment_crosses_where_the_curve_first_reaches_zero():
    """SPEC 14.1 (the 'at or below 0' end of the definition; documented choice): a curve that comes down
    to exactly 0 and stays crosses at the first x where it is 0: (1, 0.4) (2, 0) (3, 0) (4, -0.2) -> 2.0."""
    assert zero_crossing([1.0, 2.0, 3.0, 4.0], [0.4, 0.0, 0.0, -0.2]) == pytest.approx(2.0, abs=1e-12)


# =========================================================================== (5) R* logic with a scripted runner


def test_ratios_scan():
    """SPEC 14.1: the fixed scan: 15 ratios from 0.5 up to 8.0, strictly increasing."""
    assert RATIOS == (0.5, 0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0, 2.4, 2.9, 3.5, 4.2, 5.0, 6.0, 8.0)
    assert len(RATIOS) == 15 and RATIOS[0] == 0.5 and RATIOS[-1] == 8.0
    assert all(a < b for a, b in zip(RATIOS, RATIOS[1:]))


def base(r):
    """The planted skilled-side margin: linear through 0 at ratio 2.5, clipped to +-0.8."""
    return max(-0.8, min(0.8, (2.5 - r) * 0.3))


class FakeFight:
    """What a scripted run_fights returns: every field a FightResult carries (SPEC 14.5 item 3)."""

    def __init__(self, margin, raw_margin, outcome, contact, heads):
        self.margin, self.raw_margin, self.outcome = margin, raw_margin, outcome
        self.ticks, self.contact, self.survivors, self.error = 100, contact, (1, 1), None
        self.first_contact_tick = 50 if contact else -1
        self.alive_ticks, self.firing_ticks, self.heads = (100, 100), (50, 50), tuple(heads)

    def firing_per_head(self, label):
        return self.firing_ticks[label] / self.heads[label] if self.heads[label] else 0.0


class Script:
    """A scripted `run_fights` and a matching `build` that makes REAL scenario dicts with groups: 8 skilled
    raiders against round(8 * ratio) naive raiders, the skilled side on label B when swap is True.

    skilled(ratio, seed, swap) -> the SKILLED side's margin; the fight's own A-minus-B margin is that on
    label A (swap False) and its negative on label B (swap True). `outcome` and `contact` are optional
    functions of (ratio, seed, swap). `run` passes `win_margin=0.0` unless the test gives one (see the module
    docstring)."""

    def __init__(self, monkeypatch, skilled, outcome=None, contact=None):
        self.skilled, self.outcome, self.contact = skilled, outcome, contact
        self.seen = []            # (ratio, swap, seed) for every fight the solver asked for
        self.built = {}           # id(scenario) -> (scenario, snapshot, ratio, swap), to prove scenarios pass through untouched
        self.calls = 0
        monkeypatch.setattr(rstarmod, "run_fights", self.run_fights)

    def build(self, ratio, swap):
        sk, nv = ("B", "A") if swap else ("A", "B")
        scn = make_scenario([grp(sk, "raider", 1000, 1000, 3, count=8),
                             grp(nv, "raider", 3000, 1000, 3, count=max(1, round(8 * ratio)))])
        scn["groups"].sort(key=lambda g: g["side"])
        self.built[id(scn)] = (scn, copy.deepcopy(scn), ratio, swap)
        return scn

    def run_fights(self, jobs, *args, **kwargs):
        self.calls += 1
        out = []
        for scn, seed in jobs:
            keep, snapshot, r, sw = self.built[id(scn)]
            assert keep is scn and scn == snapshot, "scenario was altered"
            self.seen.append((r, sw, seed))
            s = self.skilled(r, seed, sw)
            m = -s if sw else s
            oc = self.outcome(r, seed, sw) if self.outcome else ("win_A" if m > 0 else "win_B")
            has_contact = self.contact(r, seed, sw) if self.contact else True
            raw = 0.5 if oc == "stalemate" else m          # a stalemate's raw margin is not 0: use `margin`
            n_nv = max(1, round(8 * r))
            out.append(FakeFight(0.0 if oc in ("stalemate", "cap") else m, raw, oc, has_contact,
                                 (n_nv, 8) if sw else (8, n_nv)))
        return out

    def run(self, **kw):
        kw.setdefault("win_margin", 0.0)
        return rstar(self.build, **kw)


def test_clean_decreasing_curve_finds_the_crossing(monkeypatch):
    """SPEC 14.1 (1): margin falling through 0 at ratio 2.5: value within 0.05, monotonic, valid, no
    re-run; first_loss and last_win bracket 2.5; 4 refine points lie strictly inside the original bracket
    (2.4, 2.9), points are sorted by ratio; fights are counted (2 labels x 2 seeds per point)."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r))
    res = sc.run(refine=4)
    assert res.value == pytest.approx(2.5, abs=0.05)
    assert res.monotonic is True and res.valid is True and res.rerun is False
    assert res.above_scan is False and res.below_scan is False
    assert res.violation == pytest.approx(0.0, abs=1e-12) and res.label_gap == pytest.approx(0.0, abs=1e-12)
    assert res.first_loss is not None and res.last_win is not None
    assert res.last_win <= 2.5 <= res.first_loss
    ratios = [p["ratio"] for p in res.points]
    assert ratios == sorted(ratios) and len(set(ratios)) == len(ratios)
    new = [r for r in ratios if r not in RATIOS]
    assert len(new) == 4 and all(2.4 < r < 2.9 for r in new), new
    assert set(RATIOS) <= set(ratios) and len(ratios) == 19
    assert res.fights == len(sc.seen) == 4 * 19
    assert max(seed for _, _, seed in sc.seen) < 1000
    for p in res.points:
        assert {"ratio", "value", "margin_A_label", "margin_B_label", "n_stalemate", "n_no_contact"} <= set(p)
        assert p["value"] == pytest.approx(base(p["ratio"]), abs=1e-9)
        assert p["margin_A_label"] == pytest.approx(base(p["ratio"]), abs=1e-9)
        assert p["margin_B_label"] == pytest.approx(-base(p["ratio"]), abs=1e-9)


@pytest.mark.parametrize("refine", [0, 2, 4])
def test_refine_count_sets_the_extra_points(monkeypatch, refine):
    """SPEC 14.1: `refine` bisection points are added inside the bracket (negative twin: refine=0 adds
    none, and the plain interpolation between 2.4 and 2.9 on this linear curve is exactly 2.5)."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r))
    res = sc.run(refine=refine)
    assert len(res.points) == 15 + refine
    assert res.fights == len(sc.seen) == 4 * (15 + refine)
    if refine == 0:
        assert res.value == pytest.approx(2.5, abs=1e-9)
    else:
        assert res.value == pytest.approx(2.5, abs=0.05)


def test_both_labels_run_at_every_point_and_label_gap_is_the_planted_bias(monkeypatch):
    """SPEC 14.1 (2): every ratio runs with swap False and True for every seed; with the A-label run reading
    +0.1 high and the B-label run 0.1 low for the same skilled margin, label_gap = 0.2 and the value is
    the mean over both labels (still 2.5; a solver that used one label would land at 2.17 or 2.83)."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r) + (-0.1 if sw else 0.1))
    res = sc.run(refine=4)
    assert res.label_gap == pytest.approx(0.2, abs=1e-9)
    assert res.value == pytest.approx(2.5, abs=0.05)
    seen = set(sc.seen)
    for p in res.points:
        for sw, seed in itertools.product((False, True), (0, 1)):
            assert (p["ratio"], sw, seed) in seen, (p["ratio"], sw, seed)
        assert p["margin_A_label"] == pytest.approx(base(p["ratio"]) + 0.1, abs=1e-9)
        assert p["margin_B_label"] == pytest.approx(-(base(p["ratio"]) - 0.1), abs=1e-9)
        assert p["value"] == pytest.approx(base(p["ratio"]), abs=1e-9)


def test_seeds_argument_is_used(monkeypatch):
    """SPEC 14.1 (negative twin of the default seeds): seeds=(7, 8, 9) runs exactly those, 3 per label."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r))
    res = sc.run(seeds=(7, 8, 9), refine=0)
    assert {s for _, _, s in sc.seen} == {7, 8, 9} and res.fights == 15 * 2 * 3


def _bump(rerun_clean):
    """+0.54 at ratio 5.0 only: the raw value rises from -0.51 (ratio 4.2) to -0.21, a violation of 0.3."""
    def skilled(r, seed, sw):
        bumped = abs(r - 5.0) < 1e-9 and (seed < 1000 or not rerun_clean)
        return base(r) + (0.54 if bumped else 0.0)
    return skilled


def test_rising_curve_is_flagged_and_rerun_with_shifted_seeds_and_stays_invalid(monkeypatch):
    """SPEC 14.1 (3): a rise of 0.3 (> viol_tol 0.15): monotonic False, violation about 0.3, rerun True,
    the runner is called again with seeds + 1000; the re-run still rises, so valid is False. The re-run
    happens once (only seeds 0, 1, 1000, 1001 appear)."""
    sc = Script(monkeypatch, _bump(rerun_clean=False))
    res = sc.run(refine=4)
    assert res.monotonic is False and res.violation == pytest.approx(0.3, abs=0.01)
    assert res.rerun is True and res.valid is False
    assert {1000, 1001} <= {s for _, _, s in sc.seen}
    assert {s for _, _, s in sc.seen} == {0, 1, 1000, 1001}


def test_rising_curve_with_a_clean_rerun_is_valid(monkeypatch):
    """SPEC 14.1 (3): the same rise on seeds 0, 1 only; the re-run on seeds 1000, 1001 is clean: valid True,
    rerun True, and the crossing is still where the planted curve crosses."""
    sc = Script(monkeypatch, _bump(rerun_clean=True))
    res = sc.run(refine=4)
    assert res.rerun is True and res.valid is True
    assert {1000, 1001} <= {s for _, _, s in sc.seen}
    assert res.value == pytest.approx(2.5, abs=0.05)


def test_viol_tol_decides_what_counts_as_non_monotonic(monkeypatch):
    """SPEC 14.1 (negative twin of the flag): the same 0.3 rise with viol_tol=0.4 is monotonic, no re-run,
    valid, and no fight uses a shifted seed."""
    sc = Script(monkeypatch, _bump(rerun_clean=False))
    res = sc.run(refine=4, viol_tol=0.4)
    assert res.monotonic is True and res.rerun is False and res.valid is True
    assert max(s for _, _, s in sc.seen) < 1000


def test_skilled_side_beating_the_whole_scan(monkeypatch):
    """SPEC 14.1 (4): positive margin at every ratio up to 8: value None, above_scan True, below_scan False,
    no refine points (no bracket), the scan reached 8.0."""
    sc = Script(monkeypatch, lambda r, seed, sw: 0.5)
    res = sc.run(refine=4)
    assert res.value is None and res.above_scan is True and res.below_scan is False
    assert [p["ratio"] for p in res.points] == list(RATIOS) and max(r for r, _, _ in sc.seen) == 8.0
    assert res.first_loss is None and res.last_win == 8.0
    assert res.fights == 60 and res.valid is True


def test_skilled_side_never_winning(monkeypatch):
    """SPEC 14.1 (4): negative margin at every ratio: value None, below_scan True, above_scan False."""
    sc = Script(monkeypatch, lambda r, seed, sw: -0.5)
    res = sc.run(refine=4)
    assert res.value is None and res.below_scan is True and res.above_scan is False
    assert res.first_loss == 0.5 and res.last_win is None and res.valid is True


def test_all_stalemates_is_never_winning(monkeypatch):
    """SPEC 14.1 (5): stalemates have margin 0 (not a win): a scan of nothing but stalemates is
    below_scan, with 4 stalemates at every point."""
    sc = Script(monkeypatch, lambda r, seed, sw: 0.0, outcome=lambda r, seed, sw: "stalemate")
    res = sc.run(refine=4)
    assert res.value is None and res.below_scan is True and res.above_scan is False
    assert all(p["n_stalemate"] == 4 and p["value"] == 0.0 for p in res.points)


def test_stalemate_margin_is_zero_and_counted(monkeypatch):
    """SPEC 14.1 (5): from ratio 2.4 up every fight is a stalemate whose raw margin is +0.5 (the scripted
    runner reports it, the solver must use the effective margin 0): those points have value 0.0 and
    n_stalemate 4, the others 0; the crossing is where the curve reaches 0 (2.4), not above the scan.
    Restated under SPEC 14.5 (2): a stalemate point (margin 0) is a LOSS (value <= win_margin), so first_loss is
    the first stalemate ratio 2.4 (it was None under the old `value < 0` rule). Run at win_margin 0.0 (see the
    module docstring), where the crossing stays 2.4."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r) if r < 2.4 - 1e-9 else 0.0,
                outcome=lambda r, seed, sw: "stalemate" if r >= 2.4 - 1e-9 else "win_A")
    res = sc.run(refine=4)
    for p in res.points:
        if p["ratio"] >= 2.4 - 1e-9:
            assert p["n_stalemate"] == 4 and p["value"] == 0.0, p
        else:
            assert p["n_stalemate"] == 0 and p["value"] > 0, p
    assert res.above_scan is False and res.below_scan is False and res.first_loss == 2.4
    assert res.last_win < 2.4
    assert res.value == pytest.approx(2.4, abs=1e-6)


def test_no_contact_fights_are_counted(monkeypatch):
    """SPEC 14.1: n_no_contact counts fights with no contact: here all four at ratio 0.5, none elsewhere."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r), contact=lambda r, seed, sw: r != 0.5)
    res = sc.run(refine=0)
    for p in res.points:
        assert p["n_no_contact"] == (4 if p["ratio"] == 0.5 else 0), p
        assert p["n_stalemate"] == 0


# =========================================================================== (6) the controls (real fights)
# These run real fights: about 80 per scan at about 4 ms each, so a few seconds in all.


@pytest.fixture(scope="module")
def mirror8():
    return mirror_control(8)


@pytest.fixture(scope="module")
def advantage8():
    return advantage_control(8)


def test_mirror_control_8_is_one_within_a_raider(mirror8):
    """SPEC 14.1 pass criteria: identical forces, same plays: R* within one raider-equivalent of 1.0
    (abs(value - 1.0) <= 1/8) and valid."""
    assert mirror8.valid is True and mirror8.value is not None, mirror8
    assert abs(mirror8.value - 1.0) <= 1 / 8


def test_mirror_control_16_is_one_within_a_raider():
    """SPEC 14.1 pass criteria at the second size: abs(value - 1.0) <= 1/16 and valid."""
    res = mirror_control(16)
    assert res.valid is True and res.value is not None, res
    assert abs(res.value - 1.0) <= 1 / 16


def test_advantage_control_beats_the_mirror(mirror8, advantage8):
    """SPEC 14.1 pass criteria: the planted range advantage (240 against 200) gives value > 1 + 1/8 or
    above_scan, and is strictly above the mirror's R* (above_scan counts as above)."""
    assert advantage8.above_scan or advantage8.value > 1.0 + 1 / 8, advantage8
    assert advantage8.above_scan or advantage8.value > mirror8.value


def test_controls_are_deterministic(mirror8, advantage8):
    """SPEC 9 (determinism) for the controls: the same call twice gives the identical RStar."""
    assert mirror_control(8) == mirror8
    assert advantage_control(8) == advantage8
