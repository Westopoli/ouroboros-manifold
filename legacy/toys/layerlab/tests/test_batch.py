"""Tests for layerlab/batch.py and the `batch` CLI command (SPEC.md section 8: batch.py, CLI).

Red until layerlab/batch.py exists and __main__.py knows `batch`. Fights are small and fast
(x0_mirror and r0_raiders_10v5 as they are, spawn_jitter untouched). Two cheap job shapes make
cost differ without a long fight: a `cap` job (run.max_ticks = 5, no shot ever fired) and a
`stalemate` job (both sides hold on layers 5 and 1, SPEC section 10 test 3).
"""
import csv
import json
import subprocess
import sys

import pytest

from layerlab import analysis, ffi, scenario
from layerlab.batch import read_rows, run_rows, write_rows
from layerlab.ffi import WIN_A, WIN_B, WIN_CAP, WIN_MUTUAL, WIN_STALEMATE
from layerlab.run import run

FIELDS = [
    "job", "seed", "error", "winner", "winner_name", "survivors_A", "survivors_B", "hp_ratio_A",
    "hp_ratio_B", "ticks", "first_shot_tick", "first_contact_tick", "shots_A", "shots_B", "damage_A",
    "damage_B", "cost_lost_A", "cost_lost_B", "unanswered_A", "unanswered_B", "transitions",
    "firing_ticks_A", "firing_ticks_B", "alive_ticks_A", "alive_ticks_B", "firing_share_A", "early_f_A",
    "early_f_B", "early_pred", "early_agree", "ex_agree_fraction", "ex_firing_ratio", "ex_damage_ratio",
]
NAMES = {WIN_A: "A", WIN_B: "B", WIN_STALEMATE: "stalemate", WIN_CAP: "cap", WIN_MUTUAL: "mutual"}
COUNT = "groups[0].count"
JITTER = "rules.spawn_jitter"


@pytest.fixture(scope="module")
def mirror(scenarios_dir):
    return scenario.load(str(scenarios_dir / "x0_mirror.toml"))


@pytest.fixture(scope="module")
def raiders(scenarios_dir):
    return scenario.load(str(scenarios_dir / "r0_raiders_10v5.toml"))


def _apply(scn, settings):
    for path, value in settings.items():
        scn = scenario.set_path(scn, path, value)
    return scn


def _job(scn, seed, settings=None):
    settings = dict(settings or {})
    return {"scenario": _apply(scn, settings), "seed": seed, "settings": settings}


def _cap(scn):
    """No shot is ever fired: the run ends at tick 5 as a cap."""
    return scenario.set_path(scn, "run.max_ticks", 5)


def _stalemate(scn):
    return _apply(scn, {"groups[0].layer": 5, "groups[1].layer": 1,
                        "groups[0].order": "hold", "groups[1].order": "hold"})


def _small_jobs(mirror, raiders, n=6):
    return [_job(mirror if i % 2 == 0 else raiders, seed=i, settings={COUNT: 10}) for i in range(n)]


def _set_cols(rows):
    return sorted({k for r in rows for k in r if k.startswith("set:")})


# --------------------------------------------------------------------------- (1) row schema


def test_row_fields_exact_and_in_order_then_sorted_set_columns(mirror):
    """SPEC 8 batch.py: a row has exactly the listed fields in order, then one `set:` column per
    settings key sorted by name, whatever order the settings were given in."""
    jobs = [_job(mirror, s, {JITTER: 10.0, COUNT: 10}) for s in range(3)]
    rows = run_rows(jobs, processes=0)
    assert len(rows) == 3
    for r in rows:
        assert list(r) == FIELDS + ["set:" + COUNT, "set:" + JITTER], list(r)
        assert r["set:" + COUNT] == 10 and r["set:" + JITTER] == 10.0


def test_row_without_settings_has_no_set_columns(mirror):
    """SPEC 8 (negative twin of the set: columns): a job with empty settings gets the plain fields only."""
    rows = run_rows([_job(mirror, 0)], processes=0)
    assert list(rows[0]) == FIELDS


def test_row_measures_match_a_direct_run(mirror, raiders):
    """SPEC 8: every measure is the corresponding Result value; job and seed are the job index and seed."""
    jobs = [_job(mirror, 3), _job(raiders, 7)]
    rows = run_rows(jobs, processes=0)
    for i, (job, row) in enumerate(zip(jobs, rows)):
        res = run(job["scenario"], seed=job["seed"])
        assert row["job"] == i and row["seed"] == job["seed"] and row["error"] is None
        assert row["winner"] == res.winner and row["winner_name"] == NAMES[res.winner]
        assert (row["survivors_A"], row["survivors_B"]) == res.survivors
        assert (row["hp_ratio_A"], row["hp_ratio_B"]) == res.hp_ratio
        assert row["ticks"] == res.ticks
        assert row["first_shot_tick"] == res.first_shot_tick
        assert row["first_contact_tick"] == res.first_contact_tick
        assert (row["shots_A"], row["shots_B"]) == res.shots
        assert (row["damage_A"], row["damage_B"]) == res.damage_dealt
        assert (row["cost_lost_A"], row["cost_lost_B"]) == res.cost_lost
        assert (row["unanswered_A"], row["unanswered_B"]) == res.unanswered_ticks
        assert row["transitions"] == res.transitions
        assert (row["firing_ticks_A"], row["firing_ticks_B"]) == res.firing_ticks
        assert (row["alive_ticks_A"], row["alive_ticks_B"]) == res.alive_ticks


def test_winner_name_matches_winner_for_every_outcome(mirror, raiders):
    """SPEC 8: winner_name is A, B, stalemate or cap for WIN_A, WIN_B, WIN_STALEMATE, WIN_CAP.
    The jobs below produce all four, so each mapping is exercised (not just the common one)."""
    jobs = [_job(raiders, 0), _job(mirror, 1), _job(mirror, 2), _job(mirror, 3),
            {"scenario": _stalemate(mirror), "seed": 0, "settings": {}},
            {"scenario": _cap(mirror), "seed": 0, "settings": {}}]
    rows = run_rows(jobs, processes=0)
    for r in rows:
        assert r["winner_name"] == NAMES[r["winner"]], r
    seen = {r["winner_name"] for r in rows}
    assert {"stalemate", "cap"} <= seen and seen & {"A", "B"}, seen


def test_firing_share_a_computed_from_firing_ticks(mirror, raiders):
    """SPEC 8: firing_share_A = firing_ticks_A / (firing_ticks_A + firing_ticks_B)."""
    for scn, seed in ((raiders, 0), (mirror, 4)):
        row = run_rows([_job(scn, seed)], processes=0)[0]
        res = run(scn, seed=seed)
        a, b = res.firing_ticks
        assert a + b > 0
        assert row["firing_share_A"] == pytest.approx(a / (a + b), rel=1e-12, abs=0)


def test_firing_share_a_none_when_both_zero(mirror):
    """SPEC 8 (negative twin): no one fires (a cap at tick 5, and the layer-5 v layer-1 stalemate)
    -> firing_share_A is None, not 0 and not an exception."""
    rows = run_rows([{"scenario": _cap(mirror), "seed": 0, "settings": {}},
                     {"scenario": _stalemate(mirror), "seed": 0, "settings": {}}], processes=0)
    for r in rows:
        assert (r["firing_ticks_A"], r["firing_ticks_B"]) == (0, 0)
        assert r["firing_share_A"] is None and r["error"] is None


@pytest.mark.parametrize("setting, message_part", [
    ("count", "LL_MAX_UNITS"),
    ("x", "not open"),
])
def test_error_rows_instead_of_exceptions(mirror, setting, message_part):
    """SPEC 8: a ValueError from the scenario (a group over the unit limit, a spawn off the arena)
    gives a row with `error` set to the message and every measure None; no exception, neighbours
    unharmed. Serial and pooled."""
    bad = {"count": {COUNT: ffi.MAX_UNITS + 1}, "x": {"groups[1].x": -5000.0}}[setting]
    jobs = [_job(mirror, 0), _job(mirror, 1, bad), _job(mirror, 2)]
    for procs in (0, 2):
        rows = run_rows(jobs, processes=procs)
        assert [r["job"] for r in rows] == [0, 1, 2]
        err = rows[1]
        assert isinstance(err["error"], str) and message_part in err["error"], err["error"]
        assert err["seed"] == 1
        for k in FIELDS:
            if k not in ("job", "seed", "error"):
                assert err[k] is None, (k, err[k])
        for k, v in bad.items():
            assert err["set:" + k] == v
        for good in (rows[0], rows[2]):
            assert good["error"] is None and good["winner_name"] in ("A", "B")


# --------------------------------------------------------------------------- (2) job order


@pytest.mark.parametrize("long_first", [True, False])
def test_job_order_preserved_with_pool_when_costs_differ(mirror, long_first):
    """SPEC 8: rows come back in JOB ORDER whatever order workers finish. One full fight (~1000
    ticks) among five 5-tick caps; seeds are distinct so a shuffle shows."""
    full = _job(mirror, 100)
    shorts = [{"scenario": _cap(mirror), "seed": 200 + i, "settings": {}} for i in range(5)]
    jobs = [full] + shorts if long_first else shorts + [full]
    rows = run_rows(jobs, processes=2)
    assert [r["job"] for r in rows] == list(range(6))
    assert [r["seed"] for r in rows] == [j["seed"] for j in jobs]
    for job, row in zip(jobs, rows):
        if job in shorts:
            assert row["winner_name"] == "cap" and row["ticks"] == 5
    assert rows[0 if long_first else 5]["winner_name"] in ("A", "B")


# --------------------------------------------------------------------------- (3) pooled == serial


def _mixed_jobs(mirror, raiders):
    jobs = [_job(mirror, s, {COUNT: 10}) for s in range(5)]
    jobs += [_job(raiders, s, {COUNT: 8 + s}) for s in range(5)]
    jobs.append(_job(mirror, 9, {COUNT: ffi.MAX_UNITS + 1}))                       # an error row in the mix
    jobs.append({"scenario": _cap(mirror), "seed": 1, "settings": {COUNT: 10}})
    return jobs


def test_pooled_rows_equal_serial_rows_and_csv_bytes_identical(mirror, raiders, tmp_path):
    """SPEC 8: the pooled run gives rows equal to the serial run's, and write_rows writes
    byte-identical files (floats via repr). 12 jobs, with an error row and a cap row among them."""
    jobs = _mixed_jobs(mirror, raiders)
    assert len(jobs) == 12
    serial = run_rows(jobs, processes=0)
    pooled = run_rows(jobs, processes=2)
    assert pooled == serial
    write_rows(serial, tmp_path / "serial.csv")
    write_rows(pooled, tmp_path / "pooled.csv")
    assert (tmp_path / "serial.csv").read_bytes() == (tmp_path / "pooled.csv").read_bytes()


def test_serial_vs_pooled_equality_is_not_vacuous(mirror, raiders, tmp_path):
    """Negative control for the test above: rows from different seeds are unequal, and so are their files."""
    a = run_rows([_job(mirror, s) for s in range(6)], processes=0)
    b = run_rows([_job(mirror, s + 50) for s in range(6)], processes=0)
    assert a != b
    write_rows(a, tmp_path / "a.csv")
    write_rows(b, tmp_path / "b.csv")
    assert (tmp_path / "a.csv").read_bytes() != (tmp_path / "b.csv").read_bytes()


# --------------------------------------------------------------------------- (4) CSV round trip


def test_write_read_round_trip_types_and_set_union(mirror, raiders, tmp_path):
    """SPEC 8 write_rows/read_rows: the header is the fields then the UNION of set: columns over
    all rows (sorted); a row lacking a settings key has an empty cell, read back as None; empty
    -> None, numbers -> int or float (not str), strings stay strings; floats are written with repr;
    an error message holding commas survives quoting."""
    jobs = [_job(mirror, 0, {COUNT: 8}),
            _job(raiders, 1, {JITTER: 5.5}),
            _job(mirror, 2, {"groups[0].formation": "line", COUNT: 10}),
            _job(mirror, 3),
            _job(mirror, 4, {"groups[1].x": -5000.0})]            # error text has "(-5000, 1168.75)"
    rows = run_rows(jobs, processes=0)
    path = tmp_path / "rows.csv"
    write_rows(rows, path)

    union = sorted({"set:" + COUNT, "set:" + JITTER, "set:groups[0].formation", "set:groups[1].x"})
    with open(path, newline="") as fh:
        raw = list(csv.reader(fh))
    assert raw[0] == FIELDS + union
    assert len(raw) == 1 + len(rows)
    col = {name: i for i, name in enumerate(raw[0])}
    assert raw[1][col["set:" + JITTER]] == ""                    # job 0 has no jitter setting
    assert raw[2][col["set:" + JITTER]] == "5.5"
    assert raw[1][col["error"]] == ""
    assert raw[1][col["hp_ratio_A"]] == repr(rows[0]["hp_ratio_A"])
    assert raw[5][col["winner"]] == ""                           # error row: measures empty

    back = read_rows(path)
    assert len(back) == len(rows)
    for orig, got in zip(rows, back):
        assert list(got) == FIELDS + union
        for k in got:
            want = orig.get(k)
            assert got[k] == want and type(got[k]) is type(want), (k, got[k], want)
    assert back[0]["set:" + COUNT] == 8 and type(back[0]["set:" + COUNT]) is int
    assert back[1]["set:" + JITTER] == 5.5 and type(back[1]["set:" + JITTER]) is float
    assert back[2]["set:groups[0].formation"] == "line"
    assert back[3]["set:" + COUNT] is None and back[3]["set:groups[1].x"] is None
    assert type(back[0]["hp_ratio_A"]) is float and type(back[0]["ticks"]) is int
    assert back[4]["error"] == rows[4]["error"] and "," in back[4]["error"]
    assert back[4]["winner"] is None


def test_read_rows_keeps_none_for_firing_share_and_float_zero(mirror, tmp_path):
    """SPEC 8 (negative twin): None and 0.0 are different on disk: a cap row's firing_share_A
    (None) reads back None; its early_f_A (0.0, predict_early with no shot) reads back 0.0, not None."""
    rows = run_rows([{"scenario": _cap(mirror), "seed": 0, "settings": {}}], processes=0)
    assert rows[0]["firing_share_A"] is None and rows[0]["early_f_A"] == 0.0
    write_rows(rows, tmp_path / "r.csv")
    back = read_rows(tmp_path / "r.csv")[0]
    assert back["firing_share_A"] is None
    assert back["early_f_A"] == 0.0 and type(back["early_f_A"]) is float


# --------------------------------------------------------------------------- (5) early and exchange fields


def _expected_early(res, scn, window):
    p = analysis.predict_early(res, scn, window=window)
    actual = {WIN_A: "A", WIN_B: "B"}.get(res.winner)
    if p["predicted"] in ("tie", "none") or actual is None:
        agree = None
    else:
        agree = 1 if p["predicted"] == actual else 0
    return p, agree


@pytest.mark.parametrize("window", [40, 25])
def test_early_fields_match_predict_early(mirror, raiders, window):
    """SPEC 8: early_f_A, early_f_B, early_pred come from predict_early(trace run, window); early_agree is 1
    when it names the actual winner, 0 when the other side, None for tie/none/non-A-B winners.
    Mirror seeds 0..7 contain both an agree and a disagree (checked)."""
    jobs = [_job(mirror, s) for s in range(8)] + [_job(raiders, 0)]
    rows = run_rows(jobs, processes=0, window=window)
    agrees = set()
    for job, row in zip(jobs, rows):
        res = run(job["scenario"], seed=job["seed"], trace=True)
        p, agree = _expected_early(res, job["scenario"], window)
        assert row["early_pred"] == p["predicted"]
        assert row["early_f_A"] == pytest.approx(p["f_A"], rel=1e-12, abs=1e-15)
        assert row["early_f_B"] == pytest.approx(p["f_B"], rel=1e-12, abs=1e-15)
        assert row["early_agree"] == agree and type(row["early_agree"]) is type(agree)
        agrees.add(agree)
    assert {0, 1} <= agrees, "fixture lost its agree/disagree variety: %s" % agrees


def test_early_none_and_agree_none_when_no_shot(mirror):
    """SPEC 8 (negative twin): no shot fired -> early_pred "none", early_agree None (not 0), even
    though the winner (cap, stalemate) exists."""
    rows = run_rows([{"scenario": _cap(mirror), "seed": 0, "settings": {}},
                     {"scenario": _stalemate(mirror), "seed": 0, "settings": {}}], processes=0)
    for r in rows:
        assert r["early_pred"] == "none" and r["early_agree"] is None
        assert r["early_f_A"] == 0.0 and r["early_f_B"] == 0.0


@pytest.mark.parametrize("ex_window", [20, 8])
def test_exchange_fields_match_analysis_exchange(mirror, raiders, ex_window):
    """SPEC 8: ex_agree_fraction = n_agree / (n_agree + n_disagree), ex_firing_ratio, ex_damage_ratio
    from analysis.exchange(res, scn, window=ex_window). A cap run has no windows: all three None."""
    jobs = [_job(mirror, s) for s in range(4)] + [_job(raiders, 2),
                                                  {"scenario": _cap(mirror), "seed": 0, "settings": {}}]
    rows = run_rows(jobs, processes=0, ex_window=ex_window)
    for job, row in zip(jobs, rows):
        res = run(job["scenario"], seed=job["seed"], trace=True)
        t = analysis.exchange(res, job["scenario"], window=ex_window)
        decided = t.n_agree + t.n_disagree
        want = t.n_agree / decided if decided else None
        for key, expect in (("ex_agree_fraction", want), ("ex_firing_ratio", t.firing_ratio),
                            ("ex_damage_ratio", t.damage_ratio)):
            if expect is None:
                assert row[key] is None, (key, row[key])
            else:
                assert row[key] == pytest.approx(expect, rel=1e-12, abs=1e-15), key
    assert rows[-1]["ex_agree_fraction"] is None and rows[-1]["ex_firing_ratio"] is None
    assert rows[0]["ex_firing_ratio"] is not None


# --------------------------------------------------------------------------- (6) processes spellings


def test_processes_zero_one_none_all_serial_and_equal(mirror, raiders):
    """SPEC 8: processes None, 0 and 1 run serially in-process and give equal rows."""
    jobs = _small_jobs(mirror, raiders)
    ref = run_rows(jobs, processes=0)
    assert len(ref) == 6
    assert run_rows(jobs, processes=1) == ref
    assert run_rows(jobs, processes=None) == ref
    assert run_rows(jobs) == ref


def test_processes_equality_is_not_vacuous(mirror, raiders):
    """Negative control: with other seeds the rows differ."""
    jobs = _small_jobs(mirror, raiders)
    other = [dict(j, seed=j["seed"] + 20) for j in jobs]
    assert run_rows(other, processes=0) != run_rows(jobs, processes=0)


def test_empty_job_list_gives_empty_rows():
    """SPEC 8: no jobs, no rows, whatever the processes value."""
    assert run_rows([], processes=0) == []
    assert run_rows([], processes=2) == []


# --------------------------------------------------------------------------- (7) CLI


def _cli(lab_dir, *args, timeout=240):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=lab_dir,
                          capture_output=True, text=True, timeout=timeout)


DIMS = [{"path": COUNT, "kind": "int", "lo": 6, "hi": 14},
        {"path": JITTER, "kind": "float", "lo": 2.0, "hi": 10.0}]
MIRROR = "scenarios/x0_mirror.toml"


def _dims_file(tmp_path, dims=DIMS, name="dims.json"):
    p = tmp_path / name
    p.write_text(json.dumps(dims))
    return p


def test_cli_batch_random_writes_csv_with_twelve_rows(lab_dir, tmp_path):
    """SPEC 8 CLI: `batch <scenario> --dims f --n 6 --seeds 2 --procs 2 --out tmp.csv` exits 0 and
    the CSV has 6 samples x 2 seeds = 12 data rows, jobs 0..11, no errors, both set: columns."""
    out = tmp_path / "tmp.csv"
    p = _cli(lab_dir, "batch", MIRROR, "--dims", str(_dims_file(tmp_path)), "--n", "6", "--seeds", "2",
             "--procs", "2", "--out", str(out))
    assert p.returncode == 0, p.stderr
    rows = read_rows(out)
    assert len(rows) == 12
    assert [r["job"] for r in rows] == list(range(12))
    assert {r["seed"] for r in rows} == {0, 1}
    assert all(r["error"] is None and r["winner_name"] in ("A", "B", "stalemate", "cap", "mutual") for r in rows)
    assert set(_set_cols(rows)) == {"set:" + COUNT, "set:" + JITTER}
    assert all(6 <= r["set:" + COUNT] <= 14 and 2.0 <= r["set:" + JITTER] <= 10.0 for r in rows)
    assert len(out.read_text().splitlines()) == 13


def test_cli_batch_seed_controls_the_sampler(lab_dir, tmp_path):
    """SPEC 8 CLI: `--seed` seeds the sampler (default 0). Same seed twice -> byte-identical CSV (the
    pool included); a different seed -> different set: values."""
    dims = str(_dims_file(tmp_path))

    def go(name, *extra):
        out = tmp_path / name
        p = _cli(lab_dir, "batch", MIRROR, "--dims", dims, "--n", "4", "--seeds", "1", "--procs", "2",
                 "--out", str(out), *extra)
        assert p.returncode == 0, p.stderr
        return out.read_bytes(), read_rows(out)

    default, _ = go("d.csv")
    zero, _ = go("z.csv", "--seed", "0")
    again, _ = go("z2.csv", "--seed", "0")
    other_bytes, other_rows = go("o.csv", "--seed", "1")
    assert default == zero == again
    assert other_bytes != zero
    assert [r["set:" + JITTER] for r in other_rows] != [r["set:" + JITTER] for r in read_rows(tmp_path / "z.csv")]


def test_cli_batch_grid_row_count(lab_dir, tmp_path):
    """SPEC 8 CLI: `--grid K` is K points per dimension: 2 dims x 2 points x 2 seeds = 8 rows; the
    int dimension takes exactly its bounds 4 and 10 (grid includes lo and hi)."""
    dims = [{"path": COUNT, "kind": "int", "lo": 4, "hi": 10},
            {"path": JITTER, "kind": "float", "lo": 2.0, "hi": 10.0}]
    out = tmp_path / "g.csv"
    p = _cli(lab_dir, "batch", MIRROR, "--dims", str(_dims_file(tmp_path, dims)), "--grid", "2",
             "--seeds", "2", "--out", str(out))
    assert p.returncode == 0, p.stderr
    rows = read_rows(out)
    assert len(rows) == 8
    assert {r["set:" + COUNT] for r in rows} == {4, 10}
    assert {r["set:" + JITTER] for r in rows} == {2.0, 10.0}


@pytest.mark.parametrize("case", ["not json", "missing file", "unknown path", "missing scenario"])
def test_cli_batch_bad_arguments_exit_nonzero(lab_dir, tmp_path, case):
    """SPEC 8 CLI: bad arguments (a dims file that is not JSON or is absent, a dimension path the
    scenario cannot resolve, a missing scenario) exit nonzero with a message on stderr """
    out = tmp_path / "bad.csv"
    scn = MIRROR
    dims = _dims_file(tmp_path)
    if case == "not json":
        dims.write_text("{this is: not json")
    elif case == "missing file":
        dims = tmp_path / "nope.json"
    elif case == "unknown path":
        dims = _dims_file(tmp_path, [{"path": "groups[0].nonexistent", "kind": "int", "lo": 1, "hi": 3}])
    else:
        scn = "scenarios/nope.toml"
    p = _cli(lab_dir, "batch", scn, "--dims", str(dims), "--n", "2", "--seeds", "1", "--out", str(out))
    assert p.returncode != 0
    assert p.stderr.strip()
