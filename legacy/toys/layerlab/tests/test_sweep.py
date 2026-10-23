"""Rung R3 tests (SPEC.md sections 8, 10 tests 12 and 13): sweep driver, crossing detector, log.

Red until layerlab/sweep.py and layerlab/log.py exist. Every test names the SPEC section or the
README section 6 control it mirrors.
"""
import datetime
import inspect
import math
import os
import re
import time

import numpy as np
import pytest

from layerlab import log, scenario
from layerlab.ffi import WIN_A, WIN_B
from layerlab.run import run
from layerlab.sweep import SweepTable, find_crossings, sweep

COUNT = "groups[0].count"
METRICS = [
    "win_rate", "hp_ratio_A", "hp_ratio_B", "ticks",
    "unanswered_A", "unanswered_B", "cost_lost_A", "cost_lost_B",
]


@pytest.fixture(scope="module")
def scn(scenarios_dir):
    return scenario.load(str(scenarios_dir / "r0_raiders_10v5.toml"))


@pytest.fixture(scope="module")
def base(scenarios_dir):
    return scenario.load(str(scenarios_dir / "base.toml"))


@pytest.fixture(scope="module")
def equal(scn):
    """10 v 10 raiders: the README section 6 count-ratio fixture (B count edited to 10)."""
    return scenario.set_path(scn, "groups[1].count", 10)


def _stalemate_scn(scn):
    """SPEC section 10 test 3 geometry: A on layer 5, B on layer 1, both hold, cross-layer fire off."""
    s = scenario.set_path(scn, "groups[0].layer", 5)
    s = scenario.set_path(s, "groups[1].layer", 1)
    s = scenario.set_path(s, "groups[0].order", "hold")
    return scenario.set_path(s, "groups[1].order", "hold")


def _fmt_hits(x, text):
    """True when crossing x appears in the printed text at a plausible precision (2 to 4 decimals or %g)."""
    forms = {"%.2f" % x, "%.3f" % x, "%.4f" % x, "%g" % x}
    return any(f in text for f in forms)


# --------------------------------------------------------------------------- find_crossings


def test_find_crossings_sigmoid_known_crossing():
    """SPEC section 10 test 12 (positive control): a synthetic sigmoid centred on c, sampled
    symmetrically about c, crosses 0.5 at c; found within 1e-9."""
    c, h = 3.7, 0.5
    xs = [c + h * (k + 0.5) for k in range(-10, 10)]
    ys = [1.0 / (1.0 + math.exp(-(x - c) / 0.8)) for x in xs]
    got = find_crossings(xs, ys, level=0.5)
    assert len(got) == 1, got
    assert abs(got[0] - c) < 1e-9


def test_find_crossings_level_argument_and_numpy_input():
    """SPEC section 8 find_crossings(xs, ys, level): a non-default level on numpy input; linear
    interpolation: y = 2x crosses level 1 at x = 0.5."""
    xs = np.array([0.0, 1.0, 2.0])
    ys = np.array([0.0, 2.0, 4.0])
    got = find_crossings(xs, ys, level=1.0)
    assert len(got) == 1 and abs(got[0] - 0.5) < 1e-12
    # same series at the default level 0.5 crosses at 0.25: the level is really read
    got = find_crossings(xs, ys)
    assert len(got) == 1 and abs(got[0] - 0.25) < 1e-12


@pytest.mark.parametrize("series", [[0.1] * 6, [0.9] * 6, [0.0, 0.0, 0.0, 0.0]])
def test_find_crossings_flat_series_none(series):
    """SPEC section 10 test 12 (negative control): a flat series off the level returns no crossing."""
    assert list(find_crossings(list(range(len(series))), series, level=0.5)) == []


def test_find_crossings_two_crossings_in_order():
    """SPEC section 8: a series that crosses twice returns both, in x order."""
    got = find_crossings([0.0, 1.0, 2.0], [0.0, 1.0, 0.0], level=0.5)
    assert len(got) == 2
    assert got[0] == pytest.approx(0.5, abs=1e-12)
    assert got[1] == pytest.approx(1.5, abs=1e-12)
    got = find_crossings([0, 1, 2, 3, 4], [0.0, 1.0, 0.0, 1.0, 0.0], level=0.5)
    assert got == pytest.approx([0.5, 1.5, 2.5, 3.5])


def test_find_crossings_sample_exactly_at_level_counts_once():
    """SPEC section 8: 'a sample exactly at the level counts once' (rising through it)."""
    got = find_crossings([0.0, 1.0, 2.0], [0.0, 0.5, 1.0], level=0.5)
    assert len(got) == 1
    assert got[0] == pytest.approx(1.0, abs=1e-12)


def test_find_crossings_decreasing_series():
    """SPEC section 8: decreasing series cross too, interpolated and counted the same way."""
    got = find_crossings([0.0, 1.0, 2.0, 3.0], [1.0, 0.75, 0.25, 0.0], level=0.5)
    assert len(got) == 1 and got[0] == pytest.approx(1.5, abs=1e-12)
    # decreasing, sample exactly at level: once
    got = find_crossings([0.0, 1.0, 2.0], [1.0, 0.5, 0.0], level=0.5)
    assert len(got) == 1 and got[0] == pytest.approx(1.0, abs=1e-12)


def test_find_crossings_uneven_spacing_interpolates_in_x():
    """SPEC section 8 (linear interpolation between samples): uneven x spacing is honoured."""
    got = find_crossings([0.0, 4.0], [0.0, 1.0], level=0.5)
    assert got == pytest.approx([2.0], abs=1e-12)
    got = find_crossings([0.0, 1.0, 5.0], [0.0, 0.25, 0.75], level=0.5)
    assert got == pytest.approx([3.0], abs=1e-12)


# --------------------------------------------------------------------------- the real sweeps


def test_count_ratio_sweep_crosses_near_equal_forces(equal, tmp_path):
    """SPEC section 10 test 12 and README section 6 (positive control): A count 5..20 against a
    fixed 10 raiders, 10 seeds, win_rate for A: the win rate rises with A's count and crosses 0.5
    between 8.0 and 12.5 inclusive."""
    t = sweep(equal, COUNT, list(range(5, 21)), seeds=range(10), metric="win_rate",
              expect="A", out_dir=tmp_path, log=False)
    assert len(t.mean) == 16
    assert t.mean[-1] - t.mean[0] >= 0.8, t.mean
    assert t.mean[0] <= 0.2 and t.mean[-1] >= 0.8, t.mean
    drops = [t.mean[i] - t.mean[i + 1] for i in range(len(t.mean) - 1)]
    assert max(drops) <= 0.3, "win rate is not rising with A's count: %s" % t.mean
    assert len(t.crossings) >= 1, t.mean
    for x in t.crossings:
        assert 8.0 <= x <= 12.5, t.crossings
    assert list(t.crossings) == sorted(t.crossings)


def test_count_ratio_sweep_expect_b_is_mirror(equal, tmp_path):
    """SPEC section 8 `expect` (negative case for the count-ratio detector): the same sweep scored
    for B falls with A's count, so it never rises where A's win rate rises."""
    t = sweep(equal, COUNT, [5, 10, 20], seeds=range(5), metric="win_rate",
              expect="B", out_dir=tmp_path, log=False)
    assert t.expect == "B"
    assert t.mean[0] >= 0.8 and t.mean[-1] <= 0.2, t.mean


def test_no_crossing_when_one_side_always_wins(scn, tmp_path):
    """SPEC section 8 crossings (negative control): 10 v 5 for A counts 8 and 10 and 12 is always an
    A win, so the win-rate series is flat at 1.0 and the sweep reports no crossing."""
    t = sweep(scn, COUNT, [8, 10, 12], seeds=range(4), metric="win_rate",
              out_dir=tmp_path, log=False)
    assert list(t.mean) == [1.0, 1.0, 1.0]
    assert list(t.crossings) == []
    assert "cross" not in t.text.lower()


def test_speed_gate_20v20_25_values_5_seeds(scn, tmp_path):
    """SPEC section 10 test 13: 20 v 20 raiders, a 25-value sweep (A count 8..32) x 5 seeds
    completes in under 20 s; the time is printed."""
    big = scenario.set_path(scn, "groups[0].count", 20)
    big = scenario.set_path(big, "groups[1].count", 20)
    t0 = time.perf_counter()
    t = sweep(big, COUNT, list(range(8, 33)), seeds=range(5), metric="win_rate",
              out_dir=tmp_path, log=False)
    elapsed = time.perf_counter() - t0
    print("\n[speed gate] 25 values x 5 seeds, 20 v 20 raiders: %.2f s" % elapsed)
    assert len(t.mean) == 25
    assert t.per_seed.shape == (25, 5)
    assert elapsed < 20.0, "sweep took %.2f s" % elapsed


# --------------------------------------------------------------------------- SweepTable shape


def test_sweep_signature_exactly_as_spec():
    """SPEC section 8: sweep(scn, var, values, seeds=range(5), var2=None, values2=None,
    metric="win_rate", expect="A", out_dir=None, log=True, transfer_class=None, title=None, lib="O2")."""
    sig = inspect.signature(sweep)
    names = list(sig.parameters)
    assert names == ["scn", "var", "values", "seeds", "var2", "values2", "metric", "expect",
                     "out_dir", "log", "transfer_class", "title", "lib"], names
    p = sig.parameters
    assert list(p["seeds"].default) == [0, 1, 2, 3, 4]
    for name, default in [("var2", None), ("values2", None), ("metric", "win_rate"),
                          ("expect", "A"), ("out_dir", None), ("log", True),
                          ("transfer_class", None), ("title", None), ("lib", "O2")]:
        assert p[name].default == default, name
    assert p["scn"].default is inspect.Parameter.empty
    assert p["var"].default is inspect.Parameter.empty
    assert p["values"].default is inspect.Parameter.empty


def test_one_variable_table_attributes(scn, tmp_path):
    """SPEC section 8 SweepTable (one variable): var values var2 values2 metric expect seeds mean
    per_seed stalemates caps crossings png text; shapes as defined."""
    values = [5, 8, 10]
    t = sweep(scn, COUNT, values, seeds=range(4), metric="win_rate", expect="A",
              out_dir=tmp_path, log=False)
    assert isinstance(t, SweepTable)
    for attr in ["var", "values", "var2", "values2", "metric", "expect", "seeds", "mean",
                 "per_seed", "stalemates", "caps", "crossings", "png", "text"]:
        assert hasattr(t, attr), attr
    assert t.var == COUNT and t.metric == "win_rate" and t.expect == "A"
    assert list(t.values) == values
    assert t.var2 is None and t.values2 is None
    assert list(t.seeds) == [0, 1, 2, 3]
    assert len(t.mean) == 3 and all(isinstance(m, float) for m in t.mean)
    assert isinstance(t.per_seed, np.ndarray) and t.per_seed.shape == (3, 4)
    assert len(t.stalemates) == 3 and len(t.caps) == 3
    assert isinstance(t.png, str) and isinstance(t.text, str)
    # mean is the mean over seeds of per_seed; win_rate per seed is 0 or 1
    assert np.allclose(t.mean, t.per_seed.mean(axis=-1))
    assert set(np.unique(t.per_seed)) <= {0.0, 1.0}


def test_two_variable_shapes_and_orientation(scn, tmp_path):
    """SPEC section 8 two-variable sweep: mean[i][j] is values[i], values2[j]; per_seed shaped
    (len(values), len(values2), n_seeds). Lengths 3 and 2 so a transposed table fails; A 3 v B 16 is
    a loss for A and A 16 v B 3 a win."""
    values, values2 = [3, 10, 16], [3, 16]
    t = sweep(scn, COUNT, values, seeds=range(3), var2="groups[1].count", values2=values2,
              metric="win_rate", out_dir=tmp_path, log=False)
    assert t.var2 == "groups[1].count" and list(t.values2) == values2
    assert len(t.mean) == 3 and all(len(row) == 2 for row in t.mean)
    assert t.per_seed.shape == (3, 2, 3)
    assert np.allclose(np.array(t.mean), t.per_seed.mean(axis=-1))
    assert t.mean[0][1] == 0.0, "A 3 v B 16 should never win: %s" % (t.mean,)
    assert t.mean[2][0] == 1.0, "A 16 v B 3 should always win: %s" % (t.mean,)
    assert len(t.stalemates) == 3 and all(len(r) == 2 for r in t.stalemates)
    assert len(t.caps) == 3 and all(len(r) == 2 for r in t.caps)
    # crossings: one list per values2 entry
    assert len(t.crossings) == 2
    assert all(isinstance(c, list) for c in t.crossings)
    assert os.path.exists(t.png)


def test_two_variable_cell_matches_direct_run(scn, tmp_path):
    """SPEC section 8 (per_seed indexing): per_seed[i][j][k] is the metric of one direct run at
    values[i], values2[j], seed k."""
    values, values2 = [4, 12], [5, 9, 15]
    t = sweep(scn, COUNT, values, seeds=range(2), var2="groups[1].count", values2=values2,
              metric="hp_ratio_A", out_dir=tmp_path, log=False)
    for i, a in enumerate(values):
        for j, b in enumerate(values2):
            s = scenario.set_path(scenario.set_path(scn, COUNT, a), "groups[1].count", b)
            for k in range(2):
                assert t.per_seed[i][j][k] == pytest.approx(run(s, seed=k).hp_ratio[0])


_EXTRACT = {
    "win_rate": lambda r: float(r.winner == WIN_A),
    "hp_ratio_A": lambda r: r.hp_ratio[0],
    "hp_ratio_B": lambda r: r.hp_ratio[1],
    "ticks": lambda r: float(r.ticks),
    "unanswered_A": lambda r: float(r.unanswered_ticks[0]),
    "unanswered_B": lambda r: float(r.unanswered_ticks[1]),
    "cost_lost_A": lambda r: r.cost_lost[0],
    "cost_lost_B": lambda r: r.cost_lost[1],
}


@pytest.mark.parametrize("metric", METRICS)
def test_each_metric_runs_and_matches_direct_run(scn, tmp_path, metric):
    """SPEC section 8 metrics: every named metric runs, and each per-seed value equals the matching
    Result field of a direct run() at the same value and seed."""
    values = [4, 10]
    t = sweep(scn, COUNT, values, seeds=range(3), metric=metric, out_dir=tmp_path, log=False)
    assert t.metric == metric
    for i, v in enumerate(values):
        s = scenario.set_path(scn, COUNT, v)
        for k in range(3):
            want = _EXTRACT[metric](run(s, seed=k))
            assert t.per_seed[i][k] == pytest.approx(want), (metric, v, k)
        assert t.mean[i] == pytest.approx(float(np.mean(t.per_seed[i])))


def test_metric_orientation_a_wins_big(scn, tmp_path):
    """SPEC section 8 metrics (orientation control): at 10 v 5 B is wiped, so hp_ratio_B is 0,
    cost_lost_B is 5 raiders (5 x 90) and hp_ratio_A stays well above 0."""
    kw = dict(seeds=range(3), out_dir=tmp_path, log=False)
    assert sweep(scn, COUNT, [10, 12], metric="hp_ratio_B", **kw).mean == [0.0, 0.0]
    cl_b = sweep(scn, COUNT, [10, 12], metric="cost_lost_B", **kw).mean
    assert cl_b == pytest.approx([450.0, 450.0])
    assert all(m > 0.3 for m in sweep(scn, COUNT, [10, 12], metric="hp_ratio_A", **kw).mean)
    assert all(m < 450.0 for m in sweep(scn, COUNT, [10, 12], metric="cost_lost_A", **kw).mean)


def test_expect_b_scores_b_wins(scn, tmp_path):
    """SPEC section 8 `expect` (section 8 win definition): expect B scores winner == B; in 10 v 5
    B never wins at A counts 10 and 12, so the table is 0.0."""
    t = sweep(scn, COUNT, [10, 12], seeds=range(3), expect="B", out_dir=tmp_path, log=False)
    assert list(t.mean) == [0.0, 0.0]
    t2 = sweep(scenario.set_path(scn, COUNT, 1), "groups[1].count", [10], seeds=range(3),
               expect="B", out_dir=tmp_path, log=False)
    assert list(t2.mean) == [1.0]
    assert run(scenario.set_path(scenario.set_path(scn, COUNT, 1), "groups[1].count", 10)).winner == WIN_B


def test_stalemates_counted_and_not_wins(scn, tmp_path):
    """SPEC section 8 (stalemate and cap counts are reported separately, not wins) and section 10
    test 3 geometry: every seed stalemates, so stalemates == n_seeds, caps == 0, win rate 0."""
    s = _stalemate_scn(scn)
    t = sweep(s, COUNT, [3, 5], seeds=range(4), out_dir=tmp_path, log=False)
    assert list(t.stalemates) == [4, 4]
    assert list(t.caps) == [0, 0]
    assert list(t.mean) == [0.0, 0.0]


def test_caps_counted_and_not_wins(scn, tmp_path):
    """SPEC section 8 (cap count, positive control): max_ticks 20 ends every run at the cap before
    any contact, so caps == n_seeds and stalemates == 0."""
    s = scenario.set_path(scn, "run.max_ticks", 20)
    t = sweep(s, COUNT, [3, 5], seeds=range(4), out_dir=tmp_path, log=False)
    assert list(t.caps) == [4, 4]
    assert list(t.stalemates) == [0, 0]
    assert list(t.mean) == [0.0, 0.0]


def test_stalemates_and_caps_zero_on_decisive_fights(scn, tmp_path):
    """SPEC section 8 (negative control for the stalemate and cap counters): decisive 10 v 5 fights
    report zero of both."""
    t = sweep(scn, COUNT, [10, 12], seeds=range(4), out_dir=tmp_path, log=False)
    assert list(t.stalemates) == [0, 0] and list(t.caps) == [0, 0]


def test_unknown_metric_raises_value_error(scn, tmp_path):
    """SPEC section 8 metrics: an unknown metric name is a ValueError."""
    with pytest.raises(ValueError):
        sweep(scn, COUNT, [5, 10], seeds=range(2), metric="speed_of_light",
              out_dir=tmp_path, log=False)


def test_unresolvable_var_raises_key_error(scn, tmp_path):
    """SPEC section 4 and 8 (a path that does not resolve is an error, never ignored): bad var
    and bad var2 both raise KeyError."""
    with pytest.raises(KeyError):
        sweep(scn, "rules.no_such_knob", [1, 2], seeds=range(2), out_dir=tmp_path, log=False)
    with pytest.raises(KeyError):
        sweep(scn, "groups[9].count", [1, 2], seeds=range(2), out_dir=tmp_path, log=False)
    with pytest.raises(KeyError):
        sweep(scn, COUNT, [5, 10], seeds=range(2), var2="rules.no_such_knob", values2=[1, 2],
              out_dir=tmp_path, log=False)


def test_resolvable_var_does_not_raise(scn, tmp_path):
    """SPEC section 4 (negative case for the KeyError detector): a valid rules path sweeps fine."""
    t = sweep(scn, "rules.spawn_jitter", [0.0, 10.0], seeds=range(2), out_dir=tmp_path, log=False)
    assert len(t.mean) == 2


def test_png_written_one_and_two_variables(scn, tmp_path):
    """SPEC section 8: a matplotlib PNG is saved under out_dir (line plus scatter; heatmap for two
    variables); t.png is its path."""
    t1 = sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=False)
    t2 = sweep(scn, COUNT, [5, 10], seeds=range(2), var2="groups[1].count", values2=[3, 6],
               out_dir=tmp_path, log=False)
    for t in (t1, t2):
        assert os.path.exists(t.png), t.png
        assert os.path.dirname(os.path.abspath(t.png)) == str(tmp_path)
        assert t.png.endswith(".png")
        with open(t.png, "rb") as fh:
            assert fh.read(8) == b"\x89PNG\r\n\x1a\n"
    assert t1.png != t2.png, "two sweeps overwrote each other's PNG"


def test_text_fixed_width_table_has_values_and_crossings(equal, tmp_path, capsys):
    """SPEC section 8: `text` is the printed fixed-width table, one line per value, containing every
    value and the crossings when present; sweep prints it."""
    values = [6, 8, 10, 12, 14]
    t = sweep(equal, COUNT, values, seeds=range(6), out_dir=tmp_path, log=False)
    out = capsys.readouterr().out
    assert t.text.strip() in out, "sweep did not print its table"
    rows = [ln for ln in t.text.splitlines()
            if ln.split() and ln.split()[0] in {str(v) for v in values} | {"%g" % v for v in values}]
    assert len(rows) == len(values), t.text
    assert len({len(r) for r in rows}) == 1, "rows are not fixed width:\n" + t.text
    assert len(t.crossings) >= 1, t.mean
    for x in t.crossings:
        assert _fmt_hits(x, t.text), "crossing %r missing from table:\n%s" % (x, t.text)


def test_text_two_variable_matrix_has_every_value(scn, tmp_path):
    """SPEC section 8: the two-variable table is a matrix that still shows every value of both axes."""
    t = sweep(scn, COUNT, [3, 10, 16], seeds=range(2), var2="groups[1].count", values2=[4, 17],
              out_dir=tmp_path, log=False)
    tokens = re.findall(r"[0-9.]+", t.text)
    for v in [3, 10, 16, 4, 17]:
        assert str(v) in tokens or "%.1f" % v in tokens, (v, t.text)


# --------------------------------------------------------------------------- log wiring


def test_log_false_writes_nothing(scn, tmp_path, lab_dir):
    """SPEC section 8 (`log` False): no class needed, no log file written anywhere under out_dir,
    and results/log.md is left byte-identical."""
    real = lab_dir / "results" / "log.md"
    before = real.read_bytes() if real.exists() else None
    sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=False)
    after = real.read_bytes() if real.exists() else None
    assert before == after
    assert not list(tmp_path.glob("*.md"))


def test_log_path_missing_class_raises(scn, tmp_path):
    """SPEC section 8 (a transfer_class is required when log is not False): missing raises
    ValueError and nothing is logged."""
    path = tmp_path / "log.md"
    with pytest.raises(ValueError):
        sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=path)
    assert not path.exists() or path.read_text() == ""


@pytest.mark.parametrize("bad", ["T9", "T0", "", "T1,T2", "none"])
def test_log_path_invalid_class_raises(scn, tmp_path, bad):
    """SPEC section 8 and section 12 (T1, T2, T3 only): any other class is a ValueError."""
    path = tmp_path / "log.md"
    with pytest.raises(ValueError):
        sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=path, transfer_class=bad)
    assert not path.exists() or path.read_text() == ""


@pytest.mark.parametrize("good", ["T1", "T2", "T3"])
def test_log_path_valid_classes_accepted(scn, tmp_path, good):
    """SPEC section 12 (negative case for the class check): T1, T2 and T3 all log."""
    path = tmp_path / "log.md"
    sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=path, transfer_class=good)
    assert re.search(r"\b%s\b" % good, path.read_text())


def test_log_entry_content(scn, tmp_path, base):
    """SPEC section 8 log.py: one markdown subsection with the date, the command, the scenario diff
    against base.toml, the table text and the transfer class. A rule changed from base appears in
    the diff; a rule left at base does not."""
    s = scenario.set_path(scn, "rules.spawn_jitter", 5.0)
    path = tmp_path / "log.md"
    today = [datetime.date.today().isoformat()]
    t = sweep(s, COUNT, [8, 10], seeds=range(2), out_dir=tmp_path, log=path,
              transfer_class="T1", title="Entry content probe")
    today.append(datetime.date.today().isoformat())
    text = path.read_text()
    assert any(d in text for d in today), "no date in log entry"
    assert COUNT in text, "command or var not in log entry"
    assert "sweep" in text.lower()
    assert "rules.spawn_jitter" in text, "scenario diff against base missing"
    assert "rules.pulse_radius" not in text, "diff lists a key that equals base"
    assert t.text.strip() in text, "table text missing"
    assert re.search(r"\bT1\b", text)
    assert "Entry content probe" in text
    assert re.search(r"^#{2,}\s", text, re.M), "entry is not a markdown subsection"


def test_second_sweep_appends_without_rewriting(scn, tmp_path):
    """SPEC section 8 log.py (never rewrites earlier text): an existing file keeps its text, a second
    sweep lands after the first byte-for-byte."""
    path = tmp_path / "log.md"
    path.write_text("# Layer lab log\n\nhand-written preamble\n")
    sweep(scn, COUNT, [5, 10], seeds=range(2), out_dir=tmp_path, log=path,
          transfer_class="T1", title="first entry")
    first = path.read_text()
    assert first.startswith("# Layer lab log\n\nhand-written preamble\n")
    assert "first entry" in first
    sweep(scn, "groups[1].count", [3, 5], seeds=range(2), out_dir=tmp_path, log=path,
          transfer_class="T2", title="second entry")
    second = path.read_text()
    assert second.startswith(first), "first entry was rewritten"
    tail = second[len(first):]
    assert "second entry" in tail and re.search(r"\bT2\b", tail)
    assert "first entry" not in tail
    assert second.count("first entry") == 1


# --------------------------------------------------------------------------- log.append


def _entry(scn, base, **over):
    e = {
        "date": "2026-09-30",
        "command": "python3 -m layerlab sweep demo --var groups[0].count",
        "diff": scenario.scenario_diff(base, scenario.set_path(scn, "rules.spawn_jitter", 5.0)),
        "table": "ROW-ONE   0.10\nROW-TWO   0.90",
        "png": None,
        "transfer_class": "T2",
    }
    e.update(over)
    return e


def test_log_append_writes_every_field(scn, base, tmp_path):
    """SPEC section 8 log.py: append(entry, path) writes date, command, diff, table, transfer class,
    and the optional title and note, as markdown."""
    path = tmp_path / "log.md"
    log.append(_entry(scn, base, title="Probe title", note="probe note text",
                      png="results/probe.png"), path)
    text = path.read_text()
    for needle in ["2026-09-30", "python3 -m layerlab sweep demo", "rules.spawn_jitter",
                   "ROW-ONE   0.10", "ROW-TWO   0.90", "Probe title", "probe note text"]:
        assert needle in text, needle
    assert re.search(r"\bT2\b", text)
    assert "probe.png" in text


def test_log_append_optional_fields_may_be_absent(scn, base, tmp_path):
    """SPEC section 8 log.py (`title` and `note` optional, `png` may be None): the minimal entry works."""
    path = tmp_path / "log.md"
    log.append(_entry(scn, base), path)
    assert "ROW-ONE" in path.read_text()


@pytest.mark.parametrize("bad", ["T4", "T0", "", None, "T", "T12"])
def test_log_append_invalid_class_raises(scn, base, tmp_path, bad):
    """SPEC section 8 log.py: an invalid transfer_class raises ValueError and writes nothing."""
    path = tmp_path / "log.md"
    with pytest.raises(ValueError):
        log.append(_entry(scn, base, transfer_class=bad), path)
    assert not path.exists() or path.read_text() == ""


def test_log_append_missing_class_key_raises(scn, base, tmp_path):
    """SPEC section 8 log.py (no default): an entry without the transfer_class key is a ValueError."""
    path = tmp_path / "log.md"
    e = _entry(scn, base)
    del e["transfer_class"]
    with pytest.raises(ValueError):
        log.append(e, path)
    assert not path.exists() or path.read_text() == ""


@pytest.mark.parametrize("good", ["T1", "T2", "T3"])
def test_log_append_valid_classes(scn, base, tmp_path, good):
    """SPEC section 12 (negative case for the class check): T1, T2, T3 are accepted."""
    path = tmp_path / "log.md"
    log.append(_entry(scn, base, transfer_class=good), path)
    assert re.search(r"\b%s\b" % good, path.read_text())


def test_log_append_only_appends(scn, base, tmp_path):
    """SPEC section 8 log.py: appends one subsection and never rewrites earlier text; earlier content
    survives a later append byte-for-byte, and a rejected append changes nothing."""
    path = tmp_path / "log.md"
    path.write_text("# keep me\n")
    log.append(_entry(scn, base, title="entry one"), path)
    one = path.read_text()
    assert one.startswith("# keep me\n") and "entry one" in one
    log.append(_entry(scn, base, title="entry two", transfer_class="T3"), path)
    two = path.read_text()
    assert two.startswith(one) and "entry two" in two[len(one):]
    with pytest.raises(ValueError):
        log.append(_entry(scn, base, title="entry three", transfer_class="T7"), path)
    assert path.read_text() == two
