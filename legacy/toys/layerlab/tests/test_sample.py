"""Tests for layerlab/sample.py (SPEC.md section 8: sample.py): grid, random_samples, make_jobs.

Red until layerlab/sample.py exists. grid and random_samples are pure, so their dimensions use
arbitrary dotted paths; make_jobs applies paths with scenario.set_path, so those tests use real paths
on scenarios/x0_mirror.toml. No fight is run here.
"""
import copy
import json
import math
import re
import statistics

import pytest

from layerlab import scenario
from layerlab.sample import grid, make_jobs, random_samples


@pytest.fixture(scope="module")
def mirror(scenarios_dir):
    return scenario.load(str(scenarios_dir / "x0_mirror.toml"))


def _f(path, lo, hi, **kw):
    return {"path": path, "kind": "float", "lo": lo, "hi": hi, **kw}


def _i(path, lo, hi, **kw):
    return {"path": path, "kind": "int", "lo": lo, "hi": hi, **kw}


def _c(path, values):
    return {"path": path, "kind": "choice", "values": values}


def _get(scn, path):
    """Read a dotted-index path with the same syntax as scenario.set_path."""
    node = scn
    for part in path.split("."):
        m = re.match(r"^([^\[\]]+)((?:\[\d+\])*)$", part)
        node = node[m.group(1)]
        for i in re.findall(r"\[(\d+)\]", m.group(2)):
            node = node[int(i)]
    return node


def _values(samples, path):
    return [s[path] for s in samples]


# --------------------------------------------------------------------------- (1) grid


def test_grid_cartesian_product_size_and_keys():
    """SPEC 8 grid: the cartesian product: 3 x 3 x 2 points, every point a dict path -> value over every path."""
    dims = [_f("a", 0.0, 1.0), _i("b", 1, 4), _c("c", ["x", "y"])]
    pts = grid(dims, 3)
    assert len(pts) == 3 * 3 * 2
    assert all(set(p) == {"a", "b", "c"} for p in pts)
    keys = {(p["a"], p["b"], p["c"]) for p in pts}
    assert len(keys) == 18                                       # all distinct: a true product


def test_grid_single_dimension_is_just_its_values():
    """SPEC 8 grid (negative twin of the product): one dimension -> one point per value, no extra keys."""
    pts = grid([_f("a", 0.0, 1.0)], 5)
    assert len(pts) == 5 and all(list(p) == ["a"] for p in pts)


def test_grid_float_evenly_spaced_lo_and_hi_included():
    """SPEC 8 grid: float dimensions take evenly spaced values, lo and hi included."""
    vals = sorted(_values(grid([_f("a", 2.0, 10.0)], 5), "a"))
    assert vals == pytest.approx([2.0, 4.0, 6.0, 8.0, 10.0], abs=1e-12)
    vals = sorted(_values(grid([_f("a", -1.0, 1.0)], 3), "a"))
    assert vals == pytest.approx([-1.0, 0.0, 1.0], abs=1e-12)
    assert all(isinstance(v, float) for v in vals)


def test_grid_int_rounded_and_deduplicated():
    """SPEC 8 grid: an int dimension rounds the evenly spaced values and drops duplicates:
    lo 1, hi 3, per_dim 5 -> [1, 2, 3] (five points, three distinct ints)."""
    pts = grid([_i("n", 1, 3)], 5)
    vals = _values(pts, "n")
    assert sorted(vals) == [1, 2, 3]
    assert len(vals) == 3
    assert all(type(v) is int for v in vals)


def test_grid_int_with_room_keeps_every_point():
    """SPEC 8 grid (negative twin of dedup): lo 0, hi 100, per_dim 5 -> 0, 25, 50, 75, 100, nothing dropped."""
    assert sorted(_values(grid([_i("n", 0, 100)], 5), "n")) == [0, 25, 50, 75, 100]


def test_grid_log_spacing():
    """SPEC 8 grid: `log` spaces geometrically: lo 1, hi 100, per_dim 3 -> 1, 10, 100 within 1e-9."""
    vals = sorted(_values(grid([_f("a", 1.0, 100.0, log=True)], 3), "a"))
    assert vals == pytest.approx([1.0, 10.0, 100.0], abs=1e-9)


def test_grid_linear_is_not_log():
    """Negative twin of the log test: without `log` the same bounds give 1, 50.5, 100."""
    vals = sorted(_values(grid([_f("a", 1.0, 100.0)], 3), "a"))
    assert vals == pytest.approx([1.0, 50.5, 100.0], abs=1e-9)
    vals = sorted(_values(grid([_f("a", 1.0, 100.0, log=False)], 3), "a"))
    assert vals == pytest.approx([1.0, 50.5, 100.0], abs=1e-9)


def test_grid_choice_takes_its_values_whatever_per_dim():
    """SPEC 8 grid: `choice` takes its values: all of them, once each, even with per_dim 2 or 7."""
    for per in (2, 7):
        vals = _values(grid([_c("c", [3, 4, 5])], per), "c")
        assert sorted(vals) == [3, 4, 5]
    vals = _values(grid([_c("c", ["line", "box"])], 5), "c")
    assert sorted(vals) == ["box", "line"]


def test_grid_per_dim_as_dict_gives_each_dimension_its_own_count():
    """SPEC 8 grid: per_dim may be a dict path -> count: 2 points on a, 4 on b -> 8 points."""
    dims = [_f("a", 0.0, 1.0), _f("b", 0.0, 3.0)]
    pts = grid(dims, {"a": 2, "b": 4})
    assert len(pts) == 8
    assert sorted({p["a"] for p in pts}) == pytest.approx([0.0, 1.0])
    assert sorted({p["b"] for p in pts}) == pytest.approx([0.0, 1.0, 2.0, 3.0])
    swapped = grid(dims, {"a": 4, "b": 2})
    assert len({p["a"] for p in swapped}) == 4 and len({p["b"] for p in swapped}) == 2


def test_grid_int_per_dim_applies_to_every_float_dimension():
    """SPEC 8 grid: an int per_dim is the count for every dimension: 3 and 3 -> 9 points."""
    assert len(grid([_f("a", 0.0, 1.0), _f("b", 5.0, 6.0)], 3)) == 9


# --------------------------------------------------------------------------- (2) random_samples


def test_random_samples_reproducible_and_seed_sensitive():
    """SPEC 8 random_samples: `random.Random(seed)`; same arguments -> the same list; another seed -> another list."""
    dims = [_f("a", 0.0, 1.0), _i("n", 1, 100), _c("c", ["x", "y", "z"])]
    a = random_samples(dims, 25, seed=7)
    assert len(a) == 25
    assert random_samples(dims, 25, seed=7) == a
    assert random_samples(dims, 25, 7) == a
    assert random_samples(dims, 25, seed=8) != a


def test_random_samples_n_respected_and_keys_are_the_dimension_paths():
    """SPEC 8: n points, each a dict over exactly the dimension paths."""
    for n in (1, 5, 40):
        pts = random_samples([_f("a", 0.0, 1.0), _i("n", 1, 5)], n, seed=0)
        assert len(pts) == n
        assert all(set(p) == {"a", "n"} for p in pts)


def test_random_samples_stay_inside_bounds_and_types():
    """SPEC 8: floats lie in [lo, hi] and are floats; ints are ints in [lo, hi]."""
    pts = random_samples([_f("a", -3.0, 7.5), _f("g", 0.5, 400.0, log=True), _i("n", 5, 9)], 500, seed=1)
    assert all(-3.0 <= p["a"] <= 7.5 and isinstance(p["a"], float) for p in pts)
    assert all(0.5 <= p["g"] <= 400.0 for p in pts)
    assert all(5 <= p["n"] <= 9 and type(p["n"]) is int for p in pts)
    assert len({p["a"] for p in pts}) > 400                       # actually continuous, not a few values


def test_random_ints_inclusive_at_both_ends():
    """SPEC 8: ints are inclusive: over many draws on 1..4 both 1 and 4 appear and nothing else does."""
    vals = _values(random_samples([_i("n", 1, 4)], 2000, seed=3), "n")
    assert set(vals) == {1, 2, 3, 4}
    counts = [vals.count(k) for k in (1, 2, 3, 4)]
    assert min(counts) > 300, counts                              # roughly uniform, ends not half-weighted


def test_random_choices_all_appear_and_only_them():
    """SPEC 8: choices are uniform: over 600 draws every value appears, no other value does."""
    vals = _values(random_samples([_c("c", ["x", "y", "z"])], 600, seed=5), "c")
    assert set(vals) == {"x", "y", "z"}
    assert all(vals.count(v) > 120 for v in ("x", "y", "z"))


def test_random_log_uniform_median_near_geometric_mean():
    """SPEC 8: `log` draws log-uniformly: lo 1, hi 10000 -> median near the geometric mean 100 (loose:
    30..300 over 2000 draws). Negative twin: uniform on the same bounds has its median near 5000."""
    logged = _values(random_samples([_f("a", 1.0, 10000.0, log=True)], 2000, seed=2), "a")
    flat = _values(random_samples([_f("a", 1.0, 10000.0)], 2000, seed=2), "a")
    assert 30.0 < statistics.median(logged) < 300.0
    assert 3500.0 < statistics.median(flat) < 6500.0
    assert math.isclose(statistics.mean(math.log10(v) for v in logged), 2.0, abs_tol=0.15)


# --------------------------------------------------------------------------- (3) make_jobs


SEEDS = [3, 4, 5]


def _samples(*counts, jitter=10.0):
    return [{"groups[0].count": c, "rules.spawn_jitter": jitter} for c in counts]


def _reason(entry):
    """skipped entries: a (sample, reason) pair or a dict with `sample` and `reason` (SPEC leaves the shape open)."""
    if isinstance(entry, dict):
        return entry["reason"]
    return entry[1]


def _skipped_sample(entry):
    if isinstance(entry, dict):
        return entry["sample"]
    return entry[0]


def test_make_jobs_count_and_job_shape(mirror):
    """SPEC 8 make_jobs: n_samples x n_seeds jobs, each {scenario, seed, settings}; no skips."""
    samples = _samples(6, 8, 10, 12)
    jobs, skipped = make_jobs(mirror, samples, SEEDS)
    assert len(jobs) == 4 * 3 and skipped == []
    assert all(set(j) == {"scenario", "seed", "settings"} for j in jobs)


def test_make_jobs_settings_verbatim_and_paths_applied(mirror):
    """SPEC 8 make_jobs: `settings` is the sample, verbatim; the job's scenario has every path
    applied (read back with the same path syntax); the base scenario is not mutated and jobs do not alias."""
    base_before = copy.deepcopy(mirror)
    samples = [{"groups[0].count": 6, "groups[1].count": 9, "rules.spawn_jitter": 4.5, "groups[1].layer": 2},
               {"groups[0].count": 7, "groups[1].count": 3, "rules.spawn_jitter": 0.0, "groups[1].layer": 4}]
    jobs, skipped = make_jobs(mirror, samples, [0, 1])
    assert skipped == [] and len(jobs) == 4
    for j in jobs:
        assert j["settings"] in samples
        for path, v in j["settings"].items():
            assert _get(j["scenario"], path) == v
    assert mirror == base_before
    jobs[0]["scenario"]["groups"][0]["count"] = 99
    assert all(_get(j["scenario"], "groups[0].count") != 99 for j in jobs[1:])
    assert mirror == base_before


def test_make_jobs_seeds_paired_across_samples(mirror):
    """SPEC 8 make_jobs: the same seeds are used for every sample: each sample appears with exactly SEEDS."""
    samples = _samples(6, 8, 10)
    jobs, _ = make_jobs(mirror, samples, SEEDS)
    for s in samples:
        got = sorted(j["seed"] for j in jobs if j["settings"] == s)
        assert got == sorted(SEEDS)
    assert {j["seed"] for j in jobs} == set(SEEDS)


def test_make_jobs_constraint_false_drops_to_skipped_with_reason(mirror):
    """SPEC 8 make_jobs: `constraint(scenario) -> bool`; False drops the sample into `skipped` with
    reason "constraint". The constraint sees the scenario with the sample applied (here it reads the count)."""
    samples = _samples(6, 8, 10, 12)
    seen = []

    def constraint(scn):
        seen.append(scn["groups"][0]["count"])
        return scn["groups"][0]["count"] <= 8

    jobs, skipped = make_jobs(mirror, samples, SEEDS, constraint=constraint)
    assert sorted({j["settings"]["groups[0].count"] for j in jobs}) == [6, 8]
    assert len(jobs) == 2 * 3
    assert len(skipped) == 2
    assert all(_reason(e) == "constraint" for e in skipped)
    assert sorted(_skipped_sample(e)["groups[0].count"] for e in skipped) == [10, 12]
    assert set(seen) == {6, 8, 10, 12}


def test_make_jobs_constraint_true_keeps_everything(mirror):
    """SPEC 8 (negative twin): a constraint that always holds drops nothing, and none given drops nothing."""
    samples = _samples(6, 8, 10)
    jobs, skipped = make_jobs(mirror, samples, SEEDS, constraint=lambda scn: True)
    assert len(jobs) == 9 and skipped == []
    jobs2, skipped2 = make_jobs(mirror, samples, SEEDS, constraint=None)
    assert len(jobs2) == 9 and skipped2 == []


@pytest.mark.parametrize("path, value", [
    ("groups[1].x", 1.0e7),                    # beyond the arena
    ("groups[1].x", -5000.0),                  # before the arena
    ("groups[0].count", 200),                  # more than LL_MAX_UNITS
])
def test_make_jobs_skips_layouts_that_do_not_fit_without_raising(mirror, path, value):
    """SPEC 8 make_jobs: a sample whose to_c raises ValueError is dropped with that message and make_jobs
    never raises; the sample beside it still makes its jobs."""
    bad = {path: value}
    good = {"groups[0].count": 8}
    expected = None
    try:
        scenario.to_c(scenario.set_path(mirror, path, value))
    except ValueError as e:
        expected = str(e)
    assert expected, "fixture error: this layout should not fit"
    jobs, skipped = make_jobs(mirror, [good, bad], SEEDS)
    assert all(j["settings"] == good for j in jobs)
    assert len(jobs) == 3
    assert len(skipped) == 1
    assert _reason(skipped[0]) == expected
    assert _skipped_sample(skipped[0]) == bad
    assert _reason(skipped[0]) != "constraint"


def test_make_jobs_constraint_and_layout_failure_each_keep_their_reason(mirror):
    """SPEC 8 make_jobs: both drop kinds in one call keep their own reason."""
    samples = [{"groups[0].count": 6}, {"groups[0].count": 10}, {"groups[0].count": 7, "groups[1].x": 1.0e7}]
    jobs, skipped = make_jobs(mirror, samples, [0], constraint=lambda s: s["groups"][0]["count"] != 10)
    assert [j["settings"] for j in jobs] == [{"groups[0].count": 6}]
    by_sample = {json.dumps(_skipped_sample(e), sort_keys=True): _reason(e) for e in skipped}
    assert by_sample[json.dumps({"groups[0].count": 10})] == "constraint"
    assert by_sample[json.dumps({"groups[0].count": 7, "groups[1].x": 1.0e7}, sort_keys=True)] != "constraint"
    assert len(skipped) == 2


# --------------------------------------------------------------------------- (4) dims json shape


def test_dims_json_shape_loads_and_drives_both_samplers(tmp_path):
    """SPEC 8 sample.py + CLI: a dims file is a JSON list of dimension dicts {path, kind, lo, hi, values, log};
    json.load output feeds grid and random_samples directly."""
    dims_in = [{"path": "groups[0].count", "kind": "int", "lo": 6, "hi": 14},
               {"path": "rules.spawn_jitter", "kind": "float", "lo": 1.0, "hi": 10.0, "log": True},
               {"path": "groups[0].layer", "kind": "choice", "values": [2, 3, 4]}]
    f = tmp_path / "dims.json"
    f.write_text(json.dumps(dims_in))
    dims = json.loads(f.read_text())
    assert dims == dims_in
    pts = grid(dims, 3)
    assert len(pts) == 3 * 3 * 3
    assert {p["groups[0].count"] for p in pts} == {6, 10, 14}
    assert sorted({p["rules.spawn_jitter"] for p in pts}) == pytest.approx([1.0, math.sqrt(10.0), 10.0], abs=1e-9)
    assert {p["groups[0].layer"] for p in pts} == {2, 3, 4}
    rnd = random_samples(dims, 20, seed=0)
    assert len(rnd) == 20
    assert all(6 <= p["groups[0].count"] <= 14 and 1.0 <= p["rules.spawn_jitter"] <= 10.0
               and p["groups[0].layer"] in (2, 3, 4) for p in rnd)


def test_dims_loaded_from_json_make_valid_jobs(mirror, tmp_path):
    """SPEC 8 (wiring): samples from a JSON-loaded dims list go through make_jobs with every path resolving."""
    f = tmp_path / "dims.json"
    f.write_text(json.dumps([{"path": "groups[0].count", "kind": "int", "lo": 6, "hi": 14},
                             {"path": "rules.spawn_jitter", "kind": "float", "lo": 2.0, "hi": 10.0}]))
    samples = random_samples(json.loads(f.read_text()), 6, seed=0)
    jobs, skipped = make_jobs(mirror, samples, [0, 1])
    assert len(jobs) == 12 and skipped == []
