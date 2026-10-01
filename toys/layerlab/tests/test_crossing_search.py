"""Tests for layerlab/crossing_search.py and the `crossings` CLI command (SPEC.md section 8: crossing_search.py).

Red until layerlab/crossing_search.py exists and __main__.py knows `crossings`. Rows are built by
hand: dicts with `winner_name` and `set:<path>` columns, nothing else (the SPEC says the module reads
only those). `var`, `by` and `where` keys are bare dotted paths ("x", "w"); the `set:` prefix is the
column name the module adds.
"""
import math
import subprocess
import sys

import pytest

from layerlab.crossing_search import crossing_shift, curve_diagnostics, win_curve

FIELDS = [
    "job", "seed", "error", "winner", "winner_name", "survivors_A", "survivors_B", "hp_ratio_A",
    "hp_ratio_B", "ticks", "first_shot_tick", "first_contact_tick", "shots_A", "shots_B", "damage_A",
    "damage_B", "cost_lost_A", "cost_lost_B", "unanswered_A", "unanswered_B", "transitions",
    "firing_ticks_A", "firing_ticks_B", "alive_ticks_A", "alive_ticks_B", "firing_share_A", "early_f_A",
    "early_f_B", "early_pred", "early_agree", "ex_agree_fraction", "ex_firing_ratio", "ex_damage_ratio",
]


# --------------------------------------------------------------------------- builders


def _row(winner, **settings):
    r = {"winner_name": winner}
    for path, v in settings.items():
        r["set:" + path] = v
    return r


def _point_rows(x, p, n, **extra):
    """n rows at var value x with round(p * n) wins for A, the rest for B."""
    k = int(round(p * n))
    return [_row("A" if i < k else "B", x=x, **extra) for i in range(n)]


def _sig(x, c, width=2.0):
    return 1.0 / (1.0 + math.exp(-(x - c) / width))


def _curve_rows(w, fn, xs=range(31), n=100, override=None):
    """Rows for one value of w: p = fn(x), n rows per x; `override` maps x -> (p, n)."""
    override = override or {}
    rows = []
    for x in xs:
        p, nn = override.get(x, (fn(x), n))
        rows += _point_rows(x, p, nn, w=w)
    return rows


def _curve(ps, n=100, xs=None):
    xs = list(range(len(ps))) if xs is None else xs
    return [(x, p, n) for x, p in zip(xs, ps)]


# --------------------------------------------------------------------------- (1) win_curve


def test_win_curve_groups_by_value_with_p_and_n():
    """SPEC 8 win_curve: groups by the set:<var> column; p = fraction won by `expect`, n = rows; sorted by x."""
    rows = (_point_rows(3, 0.75, 4) + _point_rows(1, 0.25, 8) + _point_rows(2, 1.0, 5))
    curve = win_curve(rows, "x", expect="A")
    assert [c[0] for c in curve] == [1, 2, 3]
    assert [c[2] for c in curve] == [8, 5, 4]
    assert [c[1] for c in curve] == pytest.approx([0.25, 1.0, 0.75])


def test_win_curve_expect_b_inverts_the_count():
    """SPEC 8 win_curve (negative twin): expect "B" counts B wins; p_A + p_B = 1 when every row is A or B."""
    rows = _point_rows(1, 0.25, 8) + _point_rows(2, 0.5, 4)
    a = win_curve(rows, "x", expect="A")
    b = win_curve(rows, "x", expect="B")
    assert [c[1] for c in b] == pytest.approx([0.75, 0.5])
    assert [x[1] + y[1] for x, y in zip(a, b)] == pytest.approx([1.0, 1.0])
    assert [c[2] for c in a] == [c[2] for c in b] == [8, 4]


def test_win_curve_stalemate_and_cap_count_in_n_not_as_wins():
    """SPEC 8 win_curve: stalemate and cap rows are in n and are not wins: 2 A, 1 B, 1 stalemate,
    1 cap at one x -> n = 5, p(A) = 0.4 and p(B) = 0.2 (a stalemate is not an A win and not a B win)."""
    rows = [_row("A", x=1), _row("A", x=1), _row("B", x=1), _row("stalemate", x=1), _row("cap", x=1)]
    assert win_curve(rows, "x", expect="A") == [(1, pytest.approx(0.4), 5)]
    assert win_curve(rows, "x", expect="B") == [(1, pytest.approx(0.2), 5)]


def test_win_curve_skips_error_rows():
    """SPEC 8 win_curve: `error` rows are skipped: they add nothing to n, and a value held only by error
    rows has no point at all."""
    rows = [_row("A", x=1), _row("B", x=1)]
    err = {"error": "groups[0]: 200 spawns exceed LL_MAX_UNITS 128", "winner_name": None, "set:x": 1}
    only_err = {"error": "boom", "winner_name": None, "set:x": 9}
    assert win_curve(rows + [err, dict(err), only_err], "x") == [(1, 0.5, 2)]
    assert win_curve(rows, "x") == [(1, 0.5, 2)]


def test_win_curve_where_filters_on_set_columns():
    """SPEC 8 win_curve: `where` is a dict of set: column filters: only matching rows count; several
    filters all apply."""
    rows = (_point_rows(1, 1.0, 4, w=0) + _point_rows(1, 0.0, 6, w=1) + _point_rows(2, 0.5, 4, w=1)
            + _point_rows(1, 0.5, 2, w=1, z=7))
    assert win_curve(rows, "x", where={"w": 0}) == [(1, 1.0, 4)]
    assert win_curve(rows, "x", where={"w": 1}) == [(1, pytest.approx(0.125), 8), (2, 0.5, 4)]
    c = win_curve(rows, "x", where={"w": 1, "z": 7})
    assert c == [(1, 0.5, 2)]
    assert win_curve(rows, "x", where={"w": 5}) == []


def test_win_curve_where_none_uses_every_row():
    """SPEC 8 win_curve (negative twin of where): no filter keeps all rows."""
    rows = _point_rows(1, 1.0, 4, w=0) + _point_rows(1, 0.0, 4, w=1)
    assert win_curve(rows, "x") == [(1, 0.5, 8)]
    assert win_curve(rows, "x", where={}) == [(1, 0.5, 8)]
    assert win_curve(rows, "x", where={"w": 0}) == [(1, 1.0, 4)]


# --------------------------------------------------------------------------- (2) curve_diagnostics


def test_diagnostics_clean_sigmoid_one_crossing_monotonic():
    """SPEC 8 curve_diagnostics (positive control): a clean sigmoid centred at 4.5, sampled symmetrically,
    has one crossing at 4.5 (within 1e-9), is monotonic, no reversals."""
    xs = list(range(10))
    d = curve_diagnostics([(x, _sig(x, 4.5, 1.0), 200) for x in xs])
    assert len(d["crossings"]) == 1 and abs(d["crossings"][0] - 4.5) < 1e-9
    assert d["non_monotonic"] is False
    assert d["reversals"] == []


def test_diagnostics_flat_curve_has_no_crossing():
    """SPEC 8 curve_diagnostics (negative control): a flat curve at 0.3 (and one at 0.7) has no crossing, no reversal."""
    for level in (0.3, 0.7):
        d = curve_diagnostics(_curve([level] * 6))
        assert d["crossings"] == [] and d["non_monotonic"] is False and d["reversals"] == []


def test_diagnostics_noise_inside_two_standard_errors_is_not_flagged():
    """SPEC 8: a wobble of 0.04 at n = 100 (se about 0.046) is within two standard errors: not flagged."""
    d = curve_diagnostics(_curve([0.30, 0.34, 0.28, 0.33, 0.29, 0.34]))
    assert d["non_monotonic"] is False and d["reversals"] == []


def test_diagnostics_dip_between_high_points_is_non_monotonic_with_reversal():
    """SPEC 8: 0.9, 0.2, 0.9 at n = 200 reverses by far more than two standard errors: non_monotonic is
    True and `reversals` lists (x_left, x_right, delta) entries between neighbouring points; two crossings."""
    curve = _curve([0.9, 0.2, 0.9], n=200)
    d = curve_diagnostics(curve)
    assert d["non_monotonic"] is True
    assert d["reversals"], "no reversal reported"
    pairs = {(0, 1): -0.7, (1, 2): 0.7}
    for xl, xr, delta in d["reversals"]:
        assert (xl, xr) in pairs, (xl, xr)
        assert delta == pytest.approx(pairs[(xl, xr)], abs=1e-9)
        assert abs(delta) > 2 * math.sqrt(0.9 * 0.1 / 200)
    assert len(d["crossings"]) == 2


def test_diagnostics_same_shape_flagged_at_large_n_but_not_tiny_n():
    """SPEC 8: the threshold is twice the larger standard error sqrt(p(1-p)/n), so the SAME shape
    0.6, 0.4, 0.6 is flagged with n = 500 (se 0.022) and not with n = 5 (se 0.22: 0.2 is inside two se)."""
    big = curve_diagnostics(_curve([0.6, 0.4, 0.6], n=500))
    tiny = curve_diagnostics(_curve([0.6, 0.4, 0.6], n=5))
    assert big["non_monotonic"] is True and big["reversals"]
    assert tiny["non_monotonic"] is False and tiny["reversals"] == []
    assert len(tiny["crossings"]) == 2 == len(big["crossings"])      # crossings do not depend on n


def test_diagnostics_two_crossings():
    """SPEC 8: a curve that rises through 0.5 and falls back through it has two crossings, in order."""
    d = curve_diagnostics(_curve([0.1, 0.9, 0.1]))
    assert d["crossings"] == pytest.approx([0.5, 1.5])
    d = curve_diagnostics(_curve([0.1, 0.9, 0.95, 0.1], n=1000))
    assert len(d["crossings"]) == 2 and d["crossings"][0] < d["crossings"][1]


# --------------------------------------------------------------------------- (3) crossing_shift


def _two_w(c0, c1, **kw):
    rows = _curve_rows(0, lambda x: _sig(x, c0)) + _curve_rows(1, lambda x: _sig(x, c1), **kw)
    return rows


def test_crossing_shift_moves_when_the_centre_moves():
    """SPEC 8 crossing_shift: sigmoid centred at 10 for w = 0 and at 20 for w = 1 -> the first crossings
    differ by 10 > default tol (one tenth of the range 0..30 = 3): moves True, gains_second False."""
    rep = crossing_shift(_two_w(10, 20), "x", "w")
    assert rep.crossings[0] == pytest.approx([10.0], abs=0.25)
    assert rep.crossings[1] == pytest.approx([20.0], abs=0.25)
    assert rep.moves is True
    assert rep.gains_second is False
    assert list(rep.non_monotonic_by) == []
    assert [c[0] for c in rep.curves[0]] == list(range(31))


def test_crossing_shift_negative_control_nothing_changes():
    """SPEC 8 crossing_shift (negative control): the same curve for w = 0 and w = 1 -> moves False,
    gains_second False, no non-monotonic value."""
    rep = crossing_shift(_two_w(10, 10), "x", "w")
    assert rep.crossings[0] == pytest.approx(rep.crossings[1])
    assert rep.moves is False and rep.gains_second is False
    assert list(rep.non_monotonic_by) == []


def test_crossing_shift_small_shift_is_inside_default_tol_but_not_inside_a_tight_tol():
    """SPEC 8: moves needs a difference above `tol` (default range/10 = 3): a shift of 1 does not move;
    with tol = 0.5 it does; and the 10-unit shift does not move under tol = 15."""
    small = _two_w(10, 11)
    assert crossing_shift(small, "x", "w").moves is False
    assert crossing_shift(small, "x", "w", tol=0.5).moves is True
    assert crossing_shift(_two_w(10, 20), "x", "w", tol=15).moves is False


def test_crossing_shift_gains_second_crossing():
    """SPEC 8: for w = 1 the win probability rises through 0.5 near 10 and falls back near 24 (two
    crossings) while w = 0 crosses once -> gains_second True. Positive twin of the negative controls above."""
    rows = (_curve_rows(0, lambda x: _sig(x, 10))
            + _curve_rows(1, lambda x: _sig(x, 10) * (1.0 - _sig(x, 24))))
    rep = crossing_shift(rows, "x", "w")
    assert len(rep.crossings[0]) == 1 and len(rep.crossings[1]) == 2
    assert rep.gains_second is True


def test_crossing_shift_one_crossing_each_does_not_gain_second():
    """SPEC 8 (negative twin): both curves cross once, one of them moved: gains_second stays False."""
    rep = crossing_shift(_two_w(10, 20), "x", "w")
    assert rep.moves is True and rep.gains_second is False


def test_crossing_shift_non_monotonic_by_lists_the_reversing_values():
    """SPEC 8: non_monotonic_by holds the by-values whose curve reverses (here w = 1 only; each needs a
    control, README 6 pass 3); with w = 0 and 2 reversing it holds those two and not w = 1."""
    def dipped(x):
        return 0.3 if x in (16, 17) else _sig(x, 10)

    rows = (_curve_rows(0, lambda x: _sig(x, 10)) + _curve_rows(1, dipped))
    rep = crossing_shift(rows, "x", "w")
    assert list(rep.non_monotonic_by) == [1]

    rows = _curve_rows(0, dipped) + _curve_rows(1, lambda x: _sig(x, 10)) + _curve_rows(2, dipped)
    rep = crossing_shift(rows, "x", "w")
    assert set(rep.non_monotonic_by) == {0, 2}
    assert len(rep.non_monotonic_by) == 2


def test_crossing_shift_skips_points_below_min_n():
    """SPEC 8: points with n < min_n are skipped. w = 1 has a 5-row point at x = 15 (all A wins, which would
    add two crossings): with the default min_n = 10 the point is absent and no second crossing appears;
    min_n = 5 keeps it (n < min_n is strict) and min_n = 1 too, and the extra crossings show."""
    rows = _curve_rows(0, lambda x: _sig(x, 20)) + _curve_rows(1, lambda x: _sig(x, 20), override={15: (1.0, 5)})
    rep = crossing_shift(rows, "x", "w")
    assert 15 not in [c[0] for c in rep.curves[1]] and 15 in [c[0] for c in rep.curves[0]]
    assert all(c[2] >= 10 for c in rep.curves[1])
    assert len(rep.crossings[1]) == 1 and rep.gains_second is False
    for m in (5, 1):
        keep = crossing_shift(rows, "x", "w", min_n=m)
        assert 15 in [c[0] for c in keep.curves[1]], m
        assert len(keep.crossings[1]) > len(keep.crossings[0])
        assert keep.gains_second is True


def test_crossing_shift_uses_continuous_by_values_as_they_are():
    """SPEC 8: continuous by-values are used as they are, one curve per distinct value: w = 0.25 and 0.5."""
    rows = _curve_rows(0.25, lambda x: _sig(x, 10)) + _curve_rows(0.5, lambda x: _sig(x, 20))
    rep = crossing_shift(rows, "x", "w")
    assert rep.crossings[0.25] == pytest.approx([10.0], abs=0.25)
    assert rep.crossings[0.5] == pytest.approx([20.0], abs=0.25)
    assert len(rep.curves) == 2 and rep.moves is True


def test_crossing_shift_text_is_a_fixed_width_table_naming_the_three_flags():
    """SPEC 8: `text` is a fixed-width table of crossings by `by` value with the three flags. Table lines
    (those starting with a by-value, here 0, 1 and 12.5, of different widths) all have the same width."""
    rows = (_curve_rows(0, lambda x: _sig(x, 10)) + _curve_rows(1, lambda x: _sig(x, 20))
            + _curve_rows(12.5, lambda x: _sig(x, 15)))
    rep = crossing_shift(rows, "x", "w")
    text = rep.text
    lines = [ln for ln in text.splitlines() if ln.strip()]
    table = []
    for ln in lines:
        tok = ln.split()[0]
        try:
            if float(tok) in (0.0, 1.0, 12.5):
                table.append(ln)
        except ValueError:
            pass
    assert len(table) == 3, text
    assert len({len(t) for t in table}) == 1, "table lines are not fixed width:\n" + text
    low = text.lower()
    assert "moves" in low and "gains_second" in low
    assert "non_monotonic" in low or "non-monotonic" in low


# --------------------------------------------------------------------------- (4) reads only winner_name and set:


def test_only_winner_name_and_set_columns_are_needed_or_read():
    """SPEC 8: the module reads only `winner_name` and `set:` columns. Rows with no other column work,
    and the same rows padded with contradicting junk in other columns (winner 2, firing_share_A, hp ratios,
    a full batch field set) give identical curves, diagnostics and report text."""
    minimal = _two_w(10, 20)
    junk = []
    for i, r in enumerate(minimal):
        j = dict(r)
        j.update({"winner": 2 if r["winner_name"] == "A" else 1, "firing_share_A": 0.0, "hp_ratio_A": -1.0,
                  "ticks": "junk", "early_pred": "B", "job": i})
        junk.append(j)
    assert win_curve(junk, "x", where={"w": 1}) == win_curve(minimal, "x", where={"w": 1})
    a, b = crossing_shift(minimal, "x", "w"), crossing_shift(junk, "x", "w")
    assert a.crossings == b.crossings and a.moves == b.moves and a.text == b.text
    assert a.moves is True                                  # the minimal rows really carry the signal


# --------------------------------------------------------------------------- (5) CLI


def _cli(lab_dir, *args, timeout=120):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=lab_dir,
                          capture_output=True, text=True, timeout=timeout)


def _csv(tmp_path):
    from layerlab.batch import write_rows

    rows = []
    for jitter, centre in ((5.0, 8.0), (10.0, 12.0)):
        for count in (4, 6, 8, 10, 12, 14, 16):
            p = _sig(count, centre, 1.5)
            k = int(round(p * 20))
            for i in range(20):
                row = dict.fromkeys(FIELDS)
                row.update({"job": len(rows), "seed": i, "winner_name": "A" if i < k else "B",
                            "set:groups[0].count": count, "set:rules.spawn_jitter": jitter})
                rows.append(row)
    path = tmp_path / "rows.csv"
    write_rows(rows, path)
    return path


def test_cli_crossings_prints_the_report(lab_dir, tmp_path):
    """SPEC 8 CLI: `crossings rows.csv --var groups[0].count --by rules.spawn_jitter --expect A` exits 0 and
    prints the report (a crossings table with the flags); the two curves cross at 8 and 12, so the shift is
    4 against a default tol of 1.2: moves."""
    path = _csv(tmp_path)
    p = _cli(lab_dir, "crossings", str(path), "--var", "groups[0].count", "--by", "rules.spawn_jitter",
             "--expect", "A")
    assert p.returncode == 0, p.stderr
    assert "moves" in p.stdout.lower()
    default = _cli(lab_dir, "crossings", str(path), "--var", "groups[0].count", "--by", "rules.spawn_jitter")
    assert default.returncode == 0 and default.stdout == p.stdout


@pytest.mark.parametrize("args", [
    ["--var", "groups[0].nope", "--by", "rules.spawn_jitter"],
    ["--var", "groups[0].count", "--by", "rules.nope"],
    ["--var", "groups[0].count", "--by", "rules.spawn_jitter", "--expect", "C"],
])
def test_cli_crossings_bad_arguments_exit_nonzero(lab_dir, tmp_path, args):
    """SPEC 8 CLI: a column the CSV lacks (--var or --by), or an --expect other than A or B, exits nonzero
    with a message on stderr; the missing column is named."""
    path = _csv(tmp_path)
    p = _cli(lab_dir, "crossings", str(path), *args)
    assert p.returncode != 0
    assert p.stderr.strip()
    if "nope" in " ".join(args):
        assert "nope" in p.stderr


def test_cli_crossings_missing_file_exits_nonzero(lab_dir, tmp_path):
    """SPEC 8 CLI: a CSV that is not there exits nonzero with a message."""
    p = _cli(lab_dir, "crossings", str(tmp_path / "none.csv"), "--var", "x", "--by", "w")
    assert p.returncode != 0 and p.stderr.strip()
