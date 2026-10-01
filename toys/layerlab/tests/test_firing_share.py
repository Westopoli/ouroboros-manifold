"""Firing share: SPEC 5.11a (the measurement), SPEC section 8 (`layerlab/analysis.py` and the `check`
CLI) and README 6.1 (docs/northstar/research/layer_dynamics/README.md, the firing-share hypothesis).

A unit CAN FIRE on a tick when it is alive, not winding, and acquisition (5.4) gave it a target. The
count does not depend on the cooldown. Per side the Result carries `alive_ticks`, `firing_ticks`
and `firing_weight`; the trace flag bit4 (16) marks each unit that can fire on a tick.

Conventions:
- `spawn_jitter` is 0 wherever distances matter; `stalemate_ticks` is huge and hp is huge in the
  duels, so nobody dies and every run lasts exactly `max_ticks` ticks.
- bit1 of the trace flags is "fired this tick" (a shot), bit4 is "can fire". They are different.
- The trace record of a tick is written after damage (step 6) and `alive` in it is the end-of-tick
  state, while `alive_ticks` is counted at step 4 (SPEC 5.11a). A unit killed on tick t therefore
  counts in `alive_ticks` for t and is dead in the trace record of t. See the identity tests.
- The analysis module is imported inside each test so that a missing module fails that test only.
"""
import math
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import LAB, add_type, grp, make_scenario, table9
from layerlab import scenario
from layerlab.ffi import WIN_A, WIN_B

TOUGH = 1.0e9
BIT4 = 16
SCEN = LAB / "scenarios"


def _analysis():
    import layerlab.analysis as analysis
    return analysis


def _load(name):
    return scenario.load(str(SCEN / name))


def _tough(scn, *names):
    for n in names:
        scn["types"][n]["hp"] = TOUGH
    return scn


def _duel(dist=150.0, type_a="raider", type_b="raider", layer_a=3, layer_b=3, rules=None, ticks=100,
          group_a=None, group_b=None, sensor=None):
    """1 v 1 on hold at y = 1000, A at x = 1900, B `dist` to the right. Jitter 0, huge hp, huge
    stalemate window, `ticks` ticks exactly."""
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    scn = make_scenario(
        [grp("A", type_a, 1900.0, 1000.0, layer_a, **(group_a or {})),
         grp("B", type_b, 1900.0 + dist, 1000.0, layer_b, facing=180.0, **(group_b or {}))],
        rules=r, run={"max_ticks": ticks, "stalemate_ticks": 10 ** 6})
    _tough(scn, type_a, type_b)
    if sensor is not None:
        for n in {type_a, type_b}:
            scn["types"][n]["sensor"] = sensor
    return scn


def _bit4(res, i):
    return (res.trace["flags"][:, i] & BIT4) != 0


# ---- 1. the definition (SPEC 5.11a) ------------------------------------------------------------

def test_can_fire_does_not_depend_on_the_cooldown():
    """SPEC 5.11a / README 6.1: 1 v 1 raiders on hold 150 apart (in range), same layer, 100 ticks,
    nobody dies: both can fire on every tick, so firing_ticks == alive_ticks == (100, 100), while
    the shot count is a few (cooldown 0.8 s = 16 ticks). The count is not the shot count."""
    res = runmod.run(_duel(150.0), seed=0)
    assert res.ticks == 100
    assert res.alive_ticks == (100, 100)
    assert res.firing_ticks == (100, 100)
    for s in (0, 1):
        assert 4 <= res.shots[s] <= 8, "shots %r: the control needs real shots at the cooldown rate" % (res.shots,)
        assert res.firing_ticks[s] > 10 * res.shots[s]


def test_out_of_range_pair_is_alive_but_cannot_fire():
    """SPEC 5.11a (negative twin of the definition test): the same pair 1000 apart with sensors
    long enough to see (so range is the only thing missing): alive_ticks == (100, 100) and
    firing_ticks == (0, 0). The sides do make contact, so the zero is the range test and not blindness."""
    res = runmod.run(_duel(1000.0, sensor=5000.0), seed=0)
    assert res.first_contact_tick >= 0
    assert res.shots == (0, 0)
    assert res.alive_ticks == (100, 100)
    assert res.firing_ticks == (0, 0)


# ---- 2. fire_requires_vision -------------------------------------------------------------------

BLIND_UP = {"vis_factor": table9(m2=0.2, m1=0.5, z=1.0, p2=0.2),   # X2: looking up one layer is 0
            "range_mult": table9(m1=1, z=1, p1=1),
            "dmg_mult": table9(m1=1, z=1, p1=1),
            "aoe_layer_mult": table9(m1=1, z=1, p1=1)}


def test_fire_requires_vision_unseen_target_does_not_count():
    """SPEC 5.11a / 5.4 / README 6.1: the X2 vision table on a 1 v 1 at 150 apart, A on layer 4 and B
    on layer 3: A sees B (0.5 x 800 = 400) and B cannot see A. With fire_requires_vision on,
    firing_ticks == (T, 0) over T = 100 ticks, both alive throughout."""
    res = runmod.run(_duel(150.0, layer_a=4, layer_b=3, rules={**BLIND_UP, "fire_requires_vision": 1}), seed=0)
    assert res.alive_ticks == (100, 100)
    assert res.firing_ticks == (100, 0)
    assert res.shots[0] > 0 and res.shots[1] == 0


def test_fire_requires_vision_off_both_can_fire():
    """SPEC 5.11a / 5.4 (positive twin): the same geometry and tables with fire_requires_vision off:
    the fire tables allow B to fire up at 150, so firing_ticks == (T, T). The vision gate is what
    held B back above."""
    res = runmod.run(_duel(150.0, layer_a=4, layer_b=3, rules={**BLIND_UP, "fire_requires_vision": 0}), seed=0)
    assert res.firing_ticks == (100, 100)
    assert res.shots[0] > 0 and res.shots[1] > 0


# ---- 3. an unarrived MOVE order -----------------------------------------------------------------

def _mover(order):
    """A raider 150 left of a holding B (in range from tick 0). A is ordered to point (1100, 1000),
    100 away, or holds. It arrives (within 1.5 x 15 = 22.5 of the goal) around tick 10."""
    scn = make_scenario(
        [grp("A", "raider", 1000.0, 1000.0, 3, order=order, goal=[1100.0, 1000.0]),
         grp("B", "raider", 1150.0, 1000.0, 3, facing=180.0)],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 60, "stalemate_ticks": 10 ** 6})
    return _tough(scn, "raider")


def test_unarrived_move_order_does_not_count_then_arrival_does():
    """SPEC 5.11a / 5.4 ("a unit under a MOVE order that has not arrived does not acquire or fire"):
    A under MOVE with a target already in range does not count until it arrives; from the arrival
    tick it does. First bit4 of A lies within one or two ticks of the arrival read off the trace, no
    bit4 before that, bit4 on every tick after, and firing_ticks[0] == ticks - first. B (hold) counts
    from tick 0."""
    res = runmod.run(_mover("move"), seed=0, trace=True)
    x, y = res.trace["x"][:, 0].astype(float), res.trace["y"][:, 0].astype(float)
    near = np.flatnonzero(np.hypot(x - 1100.0, y - 1000.0) <= 22.5 + 1e-3)
    assert len(near), "A never arrived: the scenario is broken"
    arrive = int(near[0])
    assert arrive >= 5, "A arrived at once: the control is too short to see a gap"
    bit = _bit4(res, 0)
    first = int(np.argmax(bit)) if bit.any() else None
    assert first is not None, "A never counted as able to fire, even after arriving"
    assert not bit[:max(0, arrive - 1)].any(), "A counted while still under an unarrived MOVE order"
    assert arrive - 1 <= first <= arrive + 2
    assert bit[first:].all()
    assert res.firing_ticks[0] == res.ticks - first
    assert res.firing_ticks[1] == res.ticks and _bit4(res, 1).all()


def test_hold_twin_of_the_move_test_counts_from_tick_zero():
    """SPEC 5.11a (positive twin of the MOVE test): the same A on hold counts from tick 0, so the
    gap above is the MOVE order and nothing else."""
    res = runmod.run(_mover("hold"), seed=0, trace=True)
    assert _bit4(res, 0)[0]
    assert res.firing_ticks == (res.ticks, res.ticks)


# ---- 4. the arc gate ---------------------------------------------------------------------------

def _arc(gate):
    scn = make_scenario(
        [grp("A", "gazer", 1000.0, 1000.0, 3, facing=180.0), grp("B", "dud", 1150.0, 1000.0, 3, facing=180.0)],
        rules={"spawn_jitter": 0.0, "facing_gates_fire": gate}, run={"max_ticks": 100, "stalemate_ticks": 10 ** 6})
    add_type(scn, "gazer", "raider", interval_s=0.05, arc_deg=60.0, turn_rate=6.0)
    add_type(scn, "dud", "raider", hp=1.0e6, dmg=0.0, interval_s=1.0e6)
    return scn


def test_arc_gate_on_counts_only_after_the_turn():
    """SPEC 5.11a / 5.4 / 5.12 (SPEC test 11 numbers): arc 60, facing 180, enemy at +x, turn_rate 6,
    gate on: bit4 clear on tick 0 and on every tick until the turn completes (about 9 ticks), then set
    on every tick after; firing_ticks[0] is the count of those later ticks."""
    res = runmod.run(_arc(1), seed=0, trace=True)
    bit = _bit4(res, 0)
    assert not bit[0], "counted as able to fire while facing away with the gate on"
    assert bit.any(), "never counted, even after turning"
    first = int(np.argmax(bit))
    need = math.ceil((math.pi - math.radians(30.0)) / (6.0 * 0.05))
    assert need - 1 <= first <= need + 3, "first able-to-fire tick %d, the turn needs about %d" % (first, need)
    assert not bit[:first].any() and bit[first:].all()
    assert res.firing_ticks[0] == res.ticks - first


def test_arc_gate_off_counts_from_tick_zero():
    """SPEC 5.11a / 5.4 (positive twin): the same unit facing away with the gate off counts from
    tick 0 and on every tick: firing_ticks[0] == 100."""
    res = runmod.run(_arc(0), seed=0, trace=True)
    assert _bit4(res, 0)[0]
    assert res.firing_ticks[0] == res.ticks == 100


# ---- 5. identities ------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["r0_raiders_10v5.toml", "x0_mirror.toml"])
@pytest.mark.parametrize("seed", range(5))
def test_trace_sums_match_result_counts(name, seed):
    """SPEC 5.11a / README 6.1: per side, the sum of trace bit4 == firing_ticks; alive_ticks is the
    sum of the trace alive flags plus one per unit that died (alive_ticks counts a unit on its death
    tick at step 4, the trace record of that tick is written after damage and shows it dead);
    firing_ticks <= alive_ticks; and a unit dead in the previous tick's record never counts."""
    scn = _load(name)
    res = runmod.run(scn, seed=seed, trace=True)
    n_start = (sum(g["count"] for g in scn["groups"] if g["side"] == "A"),
               sum(g["count"] for g in scn["groups"] if g["side"] == "B"))
    side, alive = res.trace["side"], res.trace["alive"].astype(int)
    can = (res.trace["flags"] & BIT4) != 0
    assert can.any(), "nothing ever counted as able to fire: the identities would be vacuous"
    for s in (0, 1):
        mine = side == s
        assert int(can[mine].sum()) == res.firing_ticks[s]
        deaths = n_start[s] - res.survivors[s]
        assert int(alive[mine].sum()) + deaths == res.alive_ticks[s]
        assert res.firing_ticks[s] <= res.alive_ticks[s]
    prev_dead = alive[:-1] == 0
    assert not (can[1:] & prev_dead).any(), "a dead unit counted as able to fire"


def test_identity_check_is_not_blind_to_deaths():
    """SPEC 5.11a (positive control for the alive identity): in the 10 v 5 control B is wiped out, so
    deaths are non-zero and the plain trace sum of alive flags is strictly below alive_ticks[1]."""
    res = runmod.run(_load("r0_raiders_10v5.toml"), seed=0, trace=True)
    assert res.survivors[1] == 0
    plain = int(res.trace["alive"][res.trace["side"] == 1].astype(int).sum())
    assert plain + 5 == res.alive_ticks[1] and plain < res.alive_ticks[1]


# ---- 6. firing_weight ---------------------------------------------------------------------------

def test_firing_weight_raider_against_bastion_uses_category_matrix():
    """SPEC 5.11a / 5.5: raider (Strike) and bastion (Siege) on hold 150 apart, in range both ways:
    each raider tick adds category_mult[Strike][Siege] = 1.5 and each bastion tick adds
    category_mult[Siege][Strike] = 0.2, so firing_weight == (1.5 x firing_ticks[0], 0.2 x firing_ticks[1])."""
    res = runmod.run(_duel(150.0, "raider", "bastion"), seed=0)
    assert res.firing_ticks == (100, 100)
    assert res.firing_weight[0] == pytest.approx(1.5 * res.firing_ticks[0], abs=1e-9)
    assert res.firing_weight[1] == pytest.approx(0.2 * res.firing_ticks[1], abs=1e-9)


def test_firing_weight_counts_only_ticks_that_can_fire():
    """SPEC 5.11a (twin with unequal counts): 500 apart, bastion sensor 1000, raider range 200: only
    the bastion (range 800, sees the raider) can fire. firing_ticks == (0, 100), so firing_weight
    == (0, 0.2 x 100): the weight is summed over ticks that can fire, not over ticks alive."""
    scn = _duel(500.0, "raider", "bastion")
    scn["types"]["bastion"]["sensor"] = 1000.0
    res = runmod.run(scn, seed=0)
    assert res.alive_ticks == (100, 100)
    assert res.firing_ticks == (0, 100)
    assert res.firing_weight[0] == 0.0
    assert res.firing_weight[1] == pytest.approx(0.2 * 100, abs=1e-9)


def test_firing_weight_raider_against_raider_equals_the_count():
    """SPEC 5.11a: Strike against Strike is category_mult 1.0, so firing_weight == firing_ticks
    (control for the matrix test: the weight is the count when the matrix entry is 1)."""
    res = runmod.run(_duel(150.0), seed=0)
    assert res.firing_weight[0] == pytest.approx(res.firing_ticks[0], abs=1e-9)
    assert res.firing_weight[1] == pytest.approx(res.firing_ticks[1], abs=1e-9)
    assert res.firing_ticks == (100, 100)


# ---- 7. the README 6.1 expectations on the X scenarios -------------------------------------------

def _firing(name, seed):
    return runmod.run(_load(name), seed=seed)


def _frac(res, s):
    return res.firing_ticks[s] / res.alive_ticks[s] if res.alive_ticks[s] else 0.0


@pytest.mark.parametrize("name", ["x2_high_ground_blind.toml", "x3_high_ground_no_return.toml"])
def test_b_never_fires_when_it_cannot_answer(name):
    """README 6.1 ("both predictions match in X2 and X3, B never fires") / SPEC 5.11a: B cannot see
    A (X2) or cannot hit A (X3), so firing_ticks[1] == 0 on every seed 0..9 while A fires."""
    for seed in range(10):
        res = _firing(name, seed)
        assert res.firing_ticks[1] == 0, "seed %d: B counted as able to fire" % seed
        assert res.firing_ticks[0] > 0, "seed %d: A never counted as able to fire" % seed


def test_b_does_fire_in_the_null_case_x4():
    """README 6.1 / SPEC 5.11a (positive twin of the X2 and X3 test): in X4 B can see and answer, so
    firing_ticks[1] > 0 on every seed 0..9. The zeros above are the rules, not a dead counter."""
    for seed in range(10):
        res = _firing("x4_high_ground_both_answer.toml", seed)
        assert res.firing_ticks[1] > 0 and res.firing_ticks[0] > 0, seed


@pytest.mark.parametrize("name", ["x0_mirror.toml", "x4_high_ground_both_answer.toml"])
def test_mirror_and_null_cases_have_matching_firing_fractions(name):
    """README 6.1 ("near a toss-up in X0 and X4") / SPEC 5.11a: over 20 seeds the mean firing
    fractions of A and B are within 0.1 of each other."""
    fa, fb = [], []
    for seed in range(20):
        res = _firing(name, seed)
        fa.append(_frac(res, 0))
        fb.append(_frac(res, 1))
    assert abs(np.mean(fa) - np.mean(fb)) <= 0.1, (np.mean(fa), np.mean(fb))
    assert np.mean(fa) > 0.1 and np.mean(fb) > 0.1, "the fractions are near zero: nothing was measured"


def test_unequal_case_x3_has_unequal_firing_fractions():
    """README 6.1 / SPEC 5.11a (negative twin of the mirror test): in X3 A fires and B never does, so
    the mean fractions over 20 seeds differ by more than 0.1: the comparison can fail."""
    fa = np.mean([_frac(_firing("x3_high_ground_no_return.toml", s), 0) for s in range(20)])
    fb = np.mean([_frac(_firing("x3_high_ground_no_return.toml", s), 1) for s in range(20)])
    assert fa - fb > 0.1, (fa, fb)


# ---- 8. analysis module (SPEC section 8, README 6.1) ---------------------------------------------

def _res(firing, alive, weight=None, winner=0):
    """Stand-in for a Result: 2-tuples indexed by side (0 = A, 1 = B)."""
    return SimpleNamespace(firing_ticks=tuple(firing), alive_ticks=tuple(alive),
                           firing_weight=tuple(float(w) for w in (weight if weight is not None else firing)),
                           winner=winner)


def test_firing_fraction_count_and_weighted():
    """SPEC section 8 / README 6.1: firing_fraction(result, side) == firing_ticks[side] /
    alive_ticks[side]; with weighted=True it is firing_weight[side] / alive_ticks[side]. The side is
    the index 0 (A) or 1 (B)."""
    a = _analysis()
    r = _res(firing=(30, 12), alive=(60, 48), weight=(45.0, 2.4))
    assert a.firing_fraction(r, 0) == pytest.approx(0.5, abs=1e-12)
    assert a.firing_fraction(r, 1) == pytest.approx(0.25, abs=1e-12)
    assert a.firing_fraction(r, 0, weighted=True) == pytest.approx(0.75, abs=1e-12)
    assert a.firing_fraction(r, 1, weighted=True) == pytest.approx(0.05, abs=1e-12)


def test_firing_fraction_is_zero_when_the_side_was_never_alive():
    """SPEC section 8: a side with alive_ticks 0 gives 0 (no division error), for both forms; a side
    with alive_ticks > 0 and no firing also gives 0 (control: the zero is not a default for everything)."""
    a = _analysis()
    r = _res(firing=(0, 5), alive=(0, 10), weight=(0.0, 7.5))
    assert a.firing_fraction(r, 0) == 0.0
    assert a.firing_fraction(r, 0, weighted=True) == 0.0
    assert a.firing_fraction(r, 1) == pytest.approx(0.5)
    assert a.firing_fraction(_res(firing=(0, 5), alive=(10, 10)), 0) == 0.0


def test_start_counts_from_the_ten_versus_five_scenario():
    """SPEC section 8: start_counts(scn) is (nA, nB) summed over the scenario's groups: (10, 5)."""
    assert _analysis().start_counts(_load("r0_raiders_10v5.toml")) == (10, 5)


def test_start_counts_follow_set_path_edits_and_sum_groups():
    """SPEC section 8 / 5 (negative twin): start_counts follows `groups[0].count` edits made with
    set_path, and adds up several groups of one side."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    assert a.start_counts(scenario.set_path(scn, "groups[0].count", 3)) == (3, 5)
    assert a.start_counts(scenario.set_path(scn, "groups[1].count", 8)) == (10, 8)
    more = scenario.set_path(scn, "groups[1].count", 5)
    more["groups"] = list(more["groups"]) + [{**more["groups"][1], "count": 2}]
    assert a.start_counts(more) == (10, 7)


def test_predict_strength_is_fraction_times_start_count_squared():
    """README 6.1 / SPEC section 8: strength = f x n0**2 per side; the larger strength is the
    predicted winner. 10 v 5: f_A 0.5 -> 50, f_B 0.8 -> 20: A."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    p = a.predict(_res(firing=(500, 400), alive=(1000, 500)), scn)
    assert p["f_A"] == pytest.approx(0.5) and p["f_B"] == pytest.approx(0.8)
    assert p["strength_A"] == pytest.approx(50.0) and p["strength_B"] == pytest.approx(20.0)
    assert p["predicted"] == "A"
    assert set(p) >= {"f_A", "f_B", "strength_A", "strength_B", "predicted"}


def test_predict_names_b_when_b_is_stronger_and_follows_the_counts():
    """README 6.1 / SPEC section 8 (negative twin): with the same fractions but start counts edited to
    (3, 5) the strengths are 4.5 and 20 and B is predicted: n0 comes from the scenario, squared."""
    a = _analysis()
    scn = scenario.set_path(_load("r0_raiders_10v5.toml"), "groups[0].count", 3)
    p = a.predict(_res(firing=(500, 400), alive=(1000, 500)), scn)
    assert p["strength_A"] == pytest.approx(0.5 * 9) and p["strength_B"] == pytest.approx(0.8 * 25)
    assert p["predicted"] == "B"


def test_predict_ties_within_one_billionth():
    """SPEC section 8: equal strengths within 1e-9 give "tie" (f_A 0.1 x 100 against f_B 0.4 x 25,
    both 10). Negative twin: strengths 10 and 10.25 are not a tie."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    assert a.predict(_res(firing=(10, 40), alive=(100, 100)), scn)["predicted"] == "tie"
    assert a.predict(_res(firing=(10, 41), alive=(100, 100)), scn)["predicted"] == "B"
    assert a.predict(_res(firing=(10, 39), alive=(100, 100)), scn)["predicted"] == "A"


def test_predict_weighted_uses_firing_weight_and_differs_from_count_only():
    """README 6.1 two predictions / SPEC section 8: hand-built numbers where the two forms disagree.
    alive (1000, 500), firing (500, 400), weight (100, 450), 10 v 5: count-only 50 against 20 -> A;
    weighted f_A 0.1 -> 10 against f_B 0.9 -> 22.5 -> B. The weighted form reads firing_weight."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    r = _res(firing=(500, 400), alive=(1000, 500), weight=(100.0, 450.0))
    plain = a.predict(r, scn)
    weighted = a.predict(r, scn, weighted=True)
    assert plain["predicted"] == "A" and weighted["predicted"] == "B"
    assert weighted["f_A"] == pytest.approx(0.1) and weighted["f_B"] == pytest.approx(0.9)
    assert weighted["strength_A"] == pytest.approx(10.0) and weighted["strength_B"] == pytest.approx(22.5)


def test_predict_forms_agree_when_weight_equals_count():
    """README 6.1 / SPEC section 8 (control for the differing-forms test): when firing_weight equals
    firing_ticks the two forms give the same numbers, so the difference above comes from the weight."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    r = _res(firing=(500, 400), alive=(1000, 500))
    assert a.predict(r, scn) == a.predict(r, scn, weighted=True)


def _expected_letter(winner):
    return {WIN_A: "A", WIN_B: "B"}.get(winner)


def test_check_counts_add_up_and_match_direct_runs():
    """SPEC section 8 / README 6.1: check(scn, seeds=range(5)) on the 10 v 5 control returns a
    CheckTable. Its attributes (named in this test, SPEC leaves the names open): wins_A, wins_B,
    other (outcomes that are neither), agree_count and agree_weighted (predictor named the actual
    winner), tied_count and tied_weighted (predictor said "tie"), mean_f_A and mean_f_B. Counts add
    up (wins_A + wins_B + other == 5; agreements and ties within the decided runs) and equal what
    direct runs and predict() give."""
    a = _analysis()
    scn = _load("r0_raiders_10v5.toml")
    t = a.check(scn, seeds=range(5))
    assert t.wins_A + t.wins_B + t.other == 5
    assert t.wins_A == 5 and t.wins_B == 0, "the 10 v 5 control: A wins every seed (SPEC test 2)"
    decided = t.wins_A + t.wins_B
    assert t.agree_count + t.tied_count <= decided
    assert t.agree_weighted + t.tied_weighted <= decided
    runs = [runmod.run(scn, seed=s) for s in range(5)]
    assert t.wins_A == sum(r.winner == WIN_A for r in runs)
    assert t.wins_B == sum(r.winner == WIN_B for r in runs)
    for weighted, agree, tied in ((False, t.agree_count, t.tied_count), (True, t.agree_weighted, t.tied_weighted)):
        preds = [a.predict(r, scn, weighted=weighted)["predicted"] for r in runs]
        assert agree == sum(p == _expected_letter(r.winner) for p, r in zip(preds, runs))
        assert tied == sum(p == "tie" for p in preds)
    assert t.mean_f_A == pytest.approx(np.mean([a.firing_fraction(r, 0) for r in runs]), abs=1e-12)
    assert t.mean_f_B == pytest.approx(np.mean([a.firing_fraction(r, 1) for r in runs]), abs=1e-12)


def test_check_table_text_is_fixed_width_and_names_both_predictors():
    """SPEC section 8: CheckTable.text is a multi-line string that names both predictors (count-only
    and type-weighted), one row each, the rows the same width (fixed-width table)."""
    t = _analysis().check(_load("r0_raiders_10v5.toml"), seeds=range(3))
    assert isinstance(t.text, str)
    lines = [ln for ln in t.text.splitlines() if ln.strip()]
    assert len(lines) >= 3
    low = [ln.lower() for ln in lines]
    rows = [ln for ln, lo in zip(lines, low) if "count" in lo or "weighted" in lo]
    assert any("count" in lo for lo in low) and any("weighted" in lo for lo in low), t.text
    assert len(rows) >= 2
    assert len({len(r) for r in rows}) == 1, "not fixed width:\n" + t.text


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=LAB, capture_output=True, text=True)


def test_cli_check_prints_the_table_and_exits_zero():
    """SPEC section 8: `python3 -m layerlab check scenarios/r0_raiders_10v5.toml --seeds 3` (seeds
    0..2) exits 0 and prints the CheckTable text."""
    proc = _cli("check", "scenarios/r0_raiders_10v5.toml", "--seeds", "3")
    assert proc.returncode == 0, proc.stderr
    expected = _analysis().check(_load("r0_raiders_10v5.toml"), seeds=range(3)).text
    assert expected.strip() in proc.stdout


def test_cli_check_bad_path_exits_nonzero_naming_the_path():
    """SPEC section 8 (negative twin): a missing scenario path exits nonzero and says which path, so
    this is the check command failing on the file and not the CLI refusing an unknown command."""
    proc = _cli("check", "scenarios/no_such_scenario.toml", "--seeds", "3")
    assert proc.returncode != 0
    assert "no_such_scenario" in proc.stderr
    assert "invalid choice" not in proc.stderr
