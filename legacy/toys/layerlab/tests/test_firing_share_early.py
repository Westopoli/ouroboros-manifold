"""Opening-window firing-share predictor: SPEC section 8 (the `analysis.py` bullet: `predict_early`,
`check(..., window=40)`, the CheckTable attributes, the `check --window` CLI option) and README 6.1 / 8
(docs/northstar/research/layer_dynamics/README.md, pass 1: why the whole-fight form is not enough).

The form (SPEC 8): `t0 = result.first_shot_tick`; the window is ticks [t0, t0 + window) clipped to the
trace length; per side f = (unit-ticks in the window with trace flag bit4 set) / (unit-ticks in the
window where the unit's alive flag is set OR its bit4 is set); strength = f x n0**2 (n0 from the
scenario); the larger strength is the prediction, "tie" within 1e-9, "none" when first_shot_tick == -1.
It reads only the trace, so it cannot leak the ending (README 8).

Conventions:
- Stand-in results are `types.SimpleNamespace` objects carrying a real-dtype trace of shape
  (ticks, units); only the fields SPEC 8 names for predict_early are filled with meaning.
- The analysis module is imported inside each test, so a missing function fails that test only.
- Scenario counts come from scenarios/r0_raiders_10v5.toml edited with set_path (n0 = 10 v 10 unless
  a test says otherwise).
- Real-run numbers (x2 10 of 10, x0 toss-up, x4 at d = 0.8) are the README 8 pass-1 numbers.
"""
import re
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import LAB
from layerlab import scenario
from layerlab.ffi import WIN_A, WIN_B

BIT4 = 16
SCEN = LAB / "scenarios"
_DTYPE = np.dtype([("x", "<f4"), ("y", "<f4"), ("hp", "<f4"), ("progress", "<f4"),
                   ("layer", "u1"), ("side", "u1"), ("alive", "u1"), ("flags", "u1")])


def _analysis():
    import layerlab.analysis as analysis
    return analysis


def _load(name):
    return scenario.load(str(SCEN / name))


def _counts(n_a, n_b):
    """The 10 v 5 scenario with start counts (n_a, n_b) (SPEC 8: n0 comes from the scenario)."""
    scn = scenario.set_path(_load("r0_raiders_10v5.toml"), "groups[0].count", n_a)
    return scenario.set_path(scn, "groups[1].count", n_b)


def _trace(sides, flags, alive):
    """A trace array (ticks, units). `sides` is a list of 0/1 per unit; `flags` and `alive` are
    (ticks, units) 0/1 arrays: flags -> bit4 (16) set where 1, alive -> the alive byte."""
    flags = np.asarray(flags, dtype=np.uint8)
    alive = np.asarray(alive, dtype=np.uint8)
    assert flags.shape == alive.shape
    ticks, units = flags.shape
    tr = np.zeros((ticks, units), dtype=_DTYPE)
    tr["side"] = np.asarray(sides, dtype=np.uint8)[None, :]
    tr["alive"] = alive
    tr["flags"] = flags * BIT4
    tr["hp"] = 100.0
    return tr


def _stand_in(trace, first_shot_tick, winner=WIN_A, firing=(1, 1), alive=(1, 1), weight=(1.0, 1.0)):
    return SimpleNamespace(trace=trace, first_shot_tick=first_shot_tick, winner=winner,
                           firing_ticks=tuple(firing), alive_ticks=tuple(alive),
                           firing_weight=tuple(weight))


def _grid(ticks, units, fire=(), dead_from=None):
    """Helper for 0/1 grids: all alive unless `dead_from` maps unit -> first dead tick; `fire` is a
    list of (unit, lo, hi) half-open tick ranges with bit4 set."""
    flags = np.zeros((ticks, units), dtype=np.uint8)
    alive = np.ones((ticks, units), dtype=np.uint8)
    for u, lo, hi in fire:
        flags[lo:hi, u] = 1
    for u, t in (dead_from or {}).items():
        alive[t:, u] = 0
    return flags, alive


# ---- 1. predict_early on stand-in results -------------------------------------------------------

def test_predict_early_fractions_and_strengths_by_hand():
    """SPEC 8 / README 8: side A has 4 units all firing (bit4) for the whole window, side B has 4 units
    with half of the unit-ticks firing: f_A = 1.0, f_B = 0.5; strength = f x n0**2 with n0 = (4, 4):
    16 against 8, so A is predicted. Window [10, 30) of a 60-tick trace, first_shot_tick 10."""
    flags, alive = _grid(60, 8, fire=[(0, 0, 60), (1, 0, 60), (2, 0, 60), (3, 0, 60), (4, 0, 60), (5, 0, 60)])
    sides = [0, 0, 0, 0, 1, 1, 1, 1]
    p = _analysis().predict_early(_stand_in(_trace(sides, flags, alive), 10), _counts(4, 4), window=20)
    assert p["f_A"] == pytest.approx(1.0, abs=1e-12) and p["f_B"] == pytest.approx(0.5, abs=1e-12)
    assert p["strength_A"] == pytest.approx(16.0) and p["strength_B"] == pytest.approx(8.0)
    assert p["predicted"] == "A"
    assert set(p) >= {"f_A", "f_B", "strength_A", "strength_B", "predicted", "start", "end"}
    assert p["start"] == 10 and p["end"] == 30


def test_predict_early_larger_start_count_can_overturn_the_fractions():
    """SPEC 8 (negative twin of the hand case): same trace (f_A 1.0, f_B 0.5), start counts edited to
    (4, 6): strengths 16 and 0.5 x 36 = 18, so B is predicted: n0 comes from the scenario, squared."""
    flags, alive = _grid(60, 8, fire=[(0, 0, 60), (1, 0, 60), (2, 0, 60), (3, 0, 60), (4, 0, 60), (5, 0, 60)])
    sides = [0, 0, 0, 0, 1, 1, 1, 1]
    p = _analysis().predict_early(_stand_in(_trace(sides, flags, alive), 10), _counts(4, 6), window=20)
    assert p["strength_A"] == pytest.approx(16.0) and p["strength_B"] == pytest.approx(18.0)
    assert p["predicted"] == "B"


def test_predict_early_equal_strengths_give_tie():
    """SPEC 8: equal strengths within 1e-9 give "tie". Side A: 4 live units firing plus 4 dead units
    (alive 0, no bit4: not counted), f_A = 1.0, n0 = 4 -> 16. Side B: 8 live units, 2 firing,
    f_B = 0.25, n0 = 8 -> 16."""
    flags, alive = _grid(40, 16, fire=[(0, 0, 40), (1, 0, 40), (2, 0, 40), (3, 0, 40), (12, 0, 40), (13, 0, 40)],
                         dead_from={4: 0, 5: 0, 6: 0, 7: 0})
    sides = [0] * 8 + [1] * 8
    p = _analysis().predict_early(_stand_in(_trace(sides, flags, alive), 0), _counts(4, 8), window=40)
    assert p["f_A"] == pytest.approx(1.0) and p["f_B"] == pytest.approx(0.25)
    assert p["predicted"] == "tie"


def test_predict_early_near_equal_strengths_are_not_a_tie():
    """SPEC 8 (negative twin of the tie): the same trace with n0 = (4, 9): strengths 16 against
    0.25 x 81 = 20.25, B, not a tie. Without this the tie test passes for any predictor that
    always says "tie"."""
    flags, alive = _grid(40, 16, fire=[(0, 0, 40), (1, 0, 40), (2, 0, 40), (3, 0, 40), (12, 0, 40), (13, 0, 40)],
                         dead_from={4: 0, 5: 0, 6: 0, 7: 0})
    sides = [0] * 8 + [1] * 8
    p = _analysis().predict_early(_stand_in(_trace(sides, flags, alive), 0), _counts(4, 9), window=40)
    assert p["predicted"] == "B"


def test_window_is_half_open_flags_outside_do_not_count():
    """SPEC 8: the window is [t0, t0 + window), t0 = first_shot_tick = 10, window 20 -> ticks 10..29.
    One unit per side, 60 ticks, both alive throughout, n0 = (10, 10). A has bit4 only on ticks 9 and
    30 (just outside: before t0, and at t0 + window), B has bit4 only on tick 10. So f_A = 0,
    f_B = 1/20, and B is predicted. The window is [10, 30), not (9, 30] or [10, 30]."""
    a_fire = [(0, 9, 10), (0, 30, 31)]
    flags, alive = _grid(60, 2, fire=a_fire + [(1, 10, 11)])
    p = _analysis().predict_early(_stand_in(_trace([0, 1], flags, alive), 10), _counts(10, 10), window=20)
    assert p["f_A"] == 0.0
    assert p["f_B"] == pytest.approx(1 / 20, abs=1e-12)
    assert p["predicted"] == "B"
    assert (p["start"], p["end"]) == (10, 30)


def test_window_edges_inside_do_count():
    """SPEC 8 (positive twin of the half-open test): A with bit4 on ticks 10 and 29 (the first and
    last window ticks) has f_A = 2/20 = 0.1 against B's 1/20 (tick 10 only): A is predicted. The edge
    ticks inside the window are counted."""
    flags, alive = _grid(60, 2, fire=[(0, 10, 11), (0, 29, 30), (1, 10, 11)])
    p = _analysis().predict_early(_stand_in(_trace([0, 1], flags, alive), 10), _counts(10, 10), window=20)
    assert p["f_A"] == pytest.approx(0.1, abs=1e-12) and p["f_B"] == pytest.approx(0.05, abs=1e-12)
    assert p["predicted"] == "A"


def test_the_window_argument_is_honoured():
    """SPEC 8 (`window`): A has bit4 on ticks 10..14, B on 15..29, both alive. Window 5 sees only
    A's burst: A (f_A = 1, f_B = 0). Window 20 sees both: f_A = 5/20, f_B = 15/20 -> B. The default is
    40 (its [10, 50) window sees the same as 20 here, B)."""
    a = _analysis()
    flags, alive = _grid(60, 2, fire=[(0, 10, 15), (1, 15, 30)])
    res = _stand_in(_trace([0, 1], flags, alive), 10)
    assert a.predict_early(res, _counts(10, 10), window=5)["predicted"] == "A"
    p = a.predict_early(res, _counts(10, 10), window=20)
    assert p["f_A"] == pytest.approx(0.25) and p["f_B"] == pytest.approx(0.75)
    assert p["predicted"] == "B"
    d = a.predict_early(res, _counts(10, 10))
    assert d["end"] == 50 and d["predicted"] == "B"


def test_window_is_clipped_to_the_trace_length():
    """SPEC 8 ("clipped to the trace length"): a 25-tick trace with t0 = 10 and the default 40 gives
    the window [10, 25): 15 ticks. A fires on all 15 (f_A = 1.0, not 15/40), B on 5 of them
    (f_B = 1/3). No error from running past the end."""
    flags, alive = _grid(25, 2, fire=[(0, 10, 25), (1, 10, 15)])
    p = _analysis().predict_early(_stand_in(_trace([0, 1], flags, alive), 10), _counts(10, 10))
    assert p["f_A"] == pytest.approx(1.0) and p["f_B"] == pytest.approx(1 / 3)
    assert p["end"] == 25 and p["start"] == 10
    assert p["predicted"] == "A"


def test_no_shot_gives_none_and_a_shot_does_not():
    """SPEC 8: first_shot_tick == -1 gives predicted "none", even though the trace shows A with
    bit4 set. Positive twin: the same trace with first_shot_tick 0 predicts a side."""
    a = _analysis()
    flags, alive = _grid(30, 2, fire=[(0, 0, 30)])
    tr = _trace([0, 1], flags, alive)
    assert a.predict_early(_stand_in(tr, -1), _counts(10, 10))["predicted"] == "none"
    assert a.predict_early(_stand_in(tr, 0), _counts(10, 10))["predicted"] == "A"


def test_missing_trace_raises_value_error_and_a_trace_does_not():
    """SPEC 8: result.trace is None raises ValueError (the run was made without trace=True).
    Positive twin: with a trace and the same other fields no error."""
    a = _analysis()
    flags, alive = _grid(30, 2, fire=[(0, 0, 30)])
    with pytest.raises(ValueError):
        a.predict_early(_stand_in(None, 5), _counts(10, 10))
    assert a.predict_early(_stand_in(_trace([0, 1], flags, alive), 5), _counts(10, 10))["predicted"] == "A"


def test_unit_that_died_this_tick_counts_and_a_dead_one_does_not():
    """SPEC 8 ("the trace is written after damage, so a unit that died on that tick still counts"):
    window [0, 4). Side A's unit is alive on ticks 0 to 2 and dead on tick 3 with bit4 still set
    there (it died on tick 3); bit4 on ticks 0 and 3: f_A = 2/4 = 0.5 (denominator counts the death
    tick; a denominator of 3 would give 2/3). Side B's unit is alive on ticks 0 and 1 with bit4 on
    both, then dead with bit4 clear on ticks 2 and 3: f_B = 2/2 = 1.0 (the dead ticks are not counted;
    counting them would give 0.5)."""
    flags = np.array([[1, 1], [0, 1], [0, 0], [1, 0]], dtype=np.uint8)
    alive = np.array([[1, 1], [1, 1], [1, 0], [0, 0]], dtype=np.uint8)
    p = _analysis().predict_early(_stand_in(_trace([0, 1], flags, alive), 0), _counts(10, 10), window=4)
    assert p["f_A"] == pytest.approx(0.5, abs=1e-12)
    assert p["f_B"] == pytest.approx(1.0, abs=1e-12)
    assert p["predicted"] == "B"


# ---- 2. it cannot leak the ending ---------------------------------------------------------------

def _leak_trace():
    """A (unit 0) fires on every tick of the window, B (unit 1) never."""
    flags, alive = _grid(60, 2, fire=[(0, 0, 60)])
    return _trace([0, 1], flags, alive)


def test_prediction_ignores_winner_and_whole_fight_totals():
    """README 8 pass 1 / SPEC 8 ("never reads the finished fight's totals"): the early window favours
    A (A fires, B does not), while the stand-in's winner, firing_ticks, alive_ticks and firing_weight
    all favour B. predict_early still says A. Positive control: the whole-fight predict() on the same
    stand-in says B, so the stand-in really does carry a B-favouring ending."""
    a = _analysis()
    scn = _counts(10, 10)
    res = _stand_in(_leak_trace(), 5, winner=WIN_B, firing=(10, 900), alive=(1000, 1000), weight=(10.0, 900.0))
    assert a.predict(res, scn)["predicted"] == "B"
    assert a.predict(res, scn, weighted=True)["predicted"] == "B"
    assert a.predict_early(res, scn)["predicted"] == "A"


def test_same_trace_with_different_totals_gives_the_same_prediction():
    """SPEC 8 (negative twin of the leak test): the same trace under a result that favours A in
    every whole-fight field, one that favours B, and one carrying nothing but `trace` and
    `first_shot_tick`, all give the same dict. A predictor that read any other field would differ
    or raise AttributeError."""
    a = _analysis()
    scn = _counts(10, 10)
    tr = _leak_trace()
    favour_a = _stand_in(tr, 5, winner=WIN_A, firing=(900, 10), alive=(1000, 1000), weight=(900.0, 10.0))
    favour_b = _stand_in(tr, 5, winner=WIN_B, firing=(10, 900), alive=(1000, 1000), weight=(10.0, 900.0))
    bare = SimpleNamespace(trace=tr, first_shot_tick=5)
    base = a.predict_early(favour_a, scn)
    assert a.predict_early(favour_b, scn) == base
    assert a.predict_early(bare, scn) == base
    assert base["predicted"] == "A"


# ---- 3. check with the early predictor on real runs ----------------------------------------------

def test_check_x2_early_predictor_is_right_on_every_seed():
    """README 8 / SPEC 8: X2 (B cannot see up, never fires), 10 seeds, default window 40: the
    opening-window predictor names A on every one: agree_early == 10, tied_early == 0,
    none_early == 0. A wins all 10 (control: the 10 are decided runs)."""
    t = _analysis().check(_load("x2_high_ground_blind.toml"), range(10))
    assert t.wins_A == 10 and t.wins_B == 0
    assert t.agree_early == 10
    assert t.tied_early == 0
    assert t.none_early == 0
    assert t.window == 40


def test_check_x0_mirror_early_predictor_is_a_toss_up_and_matches_direct_runs():
    """README 8 (X0 mirror: "a coin flip", about 50 of 90 decided agree) / SPEC 8: 60 seeds, default
    window. wins_A + wins_B == 60. agree_early lies in 20..40 inclusive: that is the bound a fair
    coin passes (n <= 60 decided, p = 0.5: mean <= 30, sd <= 3.9, so 20 and 40 are at least 2.5 sd
    out) and the whole-fight form (98 of 100) would not need to; it is deliberately loose. The
    counts equal a direct count with run(trace=True) + predict_early (agree, tied, none; the rest are
    disagreements), so agree + tied + disagree == 60 - none."""
    a = _analysis()
    scn = _load("x0_mirror.toml")
    t = a.check(scn, range(60))
    assert t.wins_A + t.wins_B == 60
    agree = tied = none = disagree = 0
    for seed in range(60):
        res = runmod.run(scn, seed=seed, trace=True)
        actual = {WIN_A: "A", WIN_B: "B"}.get(res.winner)
        who = a.predict_early(res, scn)["predicted"]
        if who == "none":
            none += 1
        elif who == "tie":
            tied += 1
        elif who == actual:
            agree += 1
        else:
            disagree += 1
    assert (t.agree_early, t.tied_early, t.none_early) == (agree, tied, none)
    assert t.agree_early + t.tied_early + disagree == 60 - t.none_early
    # Measured over 200 seeds: 0.65 (window 10) to 0.77 (window 80), 0.75 at the default 40. With hard bodies
    # and the sidestep the opening firing count genuinely predicts the mirror's winner (the side with more
    # units firing early tends to win), so this is no longer a coin flip; it must still be well short of
    # the whole-fight form (about 0.92). Bound: at most 80 percent of 60.
    assert 24 <= t.agree_early <= 48, "early predictor agreed %d of 60 in the mirror" % t.agree_early
    assert disagree > 0, "no disagreement at all in a mirror: the predictor is reading the ending"


@pytest.mark.parametrize("off", [None, 0])
def test_check_window_off_skips_the_early_predictor_and_keeps_the_rest(off):
    """SPEC 8: window=None or 0 skips the early predictor: agree_early == tied_early == none_early
    == 0, and the whole-fight attributes equal those of the same call with the default window
    (agree_count, agree_weighted, tied_count, tied_weighted, wins, mean_f)."""
    a = _analysis()
    scn = _load("x4_high_ground_both_answer.toml")
    on = a.check(scn, range(8))
    t = a.check(scn, range(8), window=off)
    assert (t.agree_early, t.tied_early, t.none_early) == (0, 0, 0)
    assert t.agree_count == on.agree_count and t.agree_weighted == on.agree_weighted
    assert t.tied_count == on.tied_count and t.tied_weighted == on.tied_weighted
    assert (t.wins_A, t.wins_B, t.other) == (on.wins_A, on.wins_B, on.other)
    assert t.mean_f_A == on.mean_f_A and t.mean_f_B == on.mean_f_B
    assert t.window in (None, 0)
    assert on.agree_early + on.tied_early + on.none_early > 0, "window on measured nothing: the twin is vacuous"


@pytest.mark.parametrize("bad", [-1, -40, 2.5, "40"])
def test_check_bad_window_raises_value_error(bad):
    """SPEC 8 (`window`: a non-negative int, None or 0 to skip): a negative or non-int window
    raises ValueError."""
    with pytest.raises(ValueError):
        _analysis().check(_load("r0_raiders_10v5.toml"), range(2), window=bad)


# ---- 4. the cell where the whole-fight form misleads ---------------------------------------------

def test_damage_decided_cell_neither_form_credits_firing_counts():
    """README 8 pass 1 and pass 3 (d = 0.8, equal counts): X4 with rules.dmg_mult[5] = 0.8 and 10 v 10.
    A wins about 94 of 100 on damage alone, with the firing counts level. Neither prediction should read
    that as "position decided": with hard bodies the whole-fight form agrees 42 of 100 and the opening
    window 56 of 100 (6 tied), both chance level. (With soft, overlapping bodies the whole-fight form
    agreed 20 of 20 here; that was an artifact of the old movement, see the mirror test below for the
    leak that remains.)"""
    a = _analysis()
    scn = scenario.set_path(_load("x4_high_ground_both_answer.toml"), "rules.dmg_mult[5]", 0.8)
    scn = scenario.set_path(scn, "groups[1].count", 10)
    t = a.check(scn, range(100))
    assert t.wins_A >= 85, "damage alone decides this cell: A wins most of 100 (measured 94)"
    assert t.agree_count <= 60, "whole-fight form must not read a damage-decided cell as firing-decided (measured 42)"
    assert t.agree_early <= 70, "opening window must not either (measured 56 of 100)"


def test_whole_fight_form_leaks_the_ending_in_a_mirror_the_early_form_does_not():
    """README 8 pass 1 (the leak) and pass 3: in the mirror (X0, no side has any edge) the whole-fight
    prediction agrees with the winner about 92 of 100 times, because the winner keeps more units alive and
    firing; the opening-window form agrees about 72 to 75 of 100 (it carries real information, since the
    side with more units firing early tends to win, but it cannot see the ending). 100 seeds: whole-fight
    >= 80 and early <= 82 with the gap between them at least 10."""
    a = _analysis()
    t = a.check(_load("x0_mirror.toml"), range(100))
    assert t.agree_count >= 80, "whole-fight form should leak the ending in the mirror (measured 92)"
    assert t.agree_early <= 82, "opening window must stay clearly below the whole-fight form (measured 72)"
    assert t.agree_count - t.agree_early >= 10


# ---- 5. CheckTable.text and the CLI --------------------------------------------------------------

_ROW = re.compile(r"\s\d+\s+\d+\s+\d+\s*$")


def _rows(text):
    """Predictor rows: lines ending in three integers (agree, of, tied)."""
    return [ln for ln in text.splitlines() if _ROW.search(ln)]


def test_text_has_a_third_row_for_the_opening_window_when_on():
    """SPEC 8 (`.text`: one row per predictor: count-only, type-weighted, and opening-window when
    `window` is on, all rows the same width): three rows, the third naming the opening window, the
    same width, and carrying agree_early and tied_early."""
    t = _analysis().check(_load("x2_high_ground_blind.toml"), range(3), window=40)
    rows = _rows(t.text)
    assert len(rows) == 3, t.text
    low = [r.lower() for r in rows]
    assert "count" in low[0] and "weighted" in low[1]
    assert any(w in low[2] for w in ("window", "opening", "early")), t.text
    assert len({len(r) for r in rows}) == 1, "not fixed width:\n" + t.text
    assert str(t.agree_early) in rows[2].split() and str(t.tied_early) in rows[2].split()


def test_text_has_no_window_row_when_off():
    """SPEC 8 (negative twin): with window=0 the table has the two whole-fight rows only, still the
    same width. (Passes before the feature exists; the positive twin above is what is red.)"""
    t = _analysis().check(_load("x2_high_ground_blind.toml"), range(3), window=0)
    rows = _rows(t.text)
    assert len(rows) == 2, t.text
    assert len({len(r) for r in rows}) == 1
    assert not any(w in r.lower() for r in rows for w in ("window", "opening", "early"))


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=LAB, capture_output=True, text=True)


def test_cli_check_window_40_prints_the_third_row():
    """SPEC 8 (`check --window W`): `check scenarios/x2_high_ground_blind.toml --seeds 3 --window 40`
    exits 0 and prints the CheckTable text for window 40: three predictor rows, the third being
    the opening-window row."""
    proc = _cli("check", "scenarios/x2_high_ground_blind.toml", "--seeds", "3", "--window", "40")
    assert proc.returncode == 0, proc.stderr
    expected = _analysis().check(_load("x2_high_ground_blind.toml"), range(3), window=40).text
    assert expected.strip() in proc.stdout
    assert len(_rows(proc.stdout)) == 3, proc.stdout


def test_cli_check_default_window_is_40():
    """SPEC 8 (default 40): without --window the CLI prints three predictor rows (positive twin of
    the --window 0 test)."""
    proc = _cli("check", "scenarios/x2_high_ground_blind.toml", "--seeds", "3")
    assert proc.returncode == 0, proc.stderr
    assert len(_rows(proc.stdout)) == 3, proc.stdout


def test_cli_check_window_zero_prints_two_rows():
    """SPEC 8 (`--window 0` turns the opening-window predictor off): exit 0 and two predictor rows."""
    proc = _cli("check", "scenarios/x2_high_ground_blind.toml", "--seeds", "3", "--window", "0")
    assert proc.returncode == 0, proc.stderr
    assert len(_rows(proc.stdout)) == 2, proc.stdout


def test_cli_check_negative_window_exits_nonzero():
    """SPEC 8 (negative twin): `--window -1` is a bad window and exits nonzero with a message, and
    it is not the CLI refusing an unknown command."""
    proc = _cli("check", "scenarios/x2_high_ground_blind.toml", "--seeds", "3", "--window=-1")
    assert proc.returncode != 0
    assert proc.stderr.strip()
    assert "invalid choice" not in proc.stderr
    assert "unrecognized arguments" not in proc.stderr, "the option does not exist yet"
