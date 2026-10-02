# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-16
"""Leaf-05: grid and random_samples, ported from toys/layerlab/layerlab/sample.py.

Expected values are literals produced once by running the toy; the toy is not imported here.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.sample import grid, random_samples  # noqa: E402

A = {"path": "a", "kind": "float", "lo": 0.0, "hi": 1.0}
N = {"path": "n", "kind": "int", "lo": 1, "hi": 10}
C = {"path": "c", "kind": "choice", "values": ["x", "y"]}
DIMS = [A, N, C]


def test_grid_float_axis_five_points():
    """AC-16: a float axis of 5 points runs lo..hi evenly."""
    assert grid([A], 5) == [{"a": 0.0}, {"a": 0.25}, {"a": 0.5}, {"a": 0.75}, {"a": 1.0}]


def test_grid_per_dim_one_is_lo_and_two_is_the_ends():
    """AC-16 (Cardinality one/two): per_dim 1 gives [lo]; per_dim 2 gives [lo, hi]."""
    assert grid([A], 1) == [{"a": 0.0}]
    assert grid([A], 2) == [{"a": 0.0}, {"a": 1.0}]


def test_grid_mixed_dims_full_literal_and_size():
    """AC-16: three dims at per_dim 3 -> 3 * 3 * 2 points, first dim slowest, ported order."""
    got = grid(DIMS, 3)
    expected = []
    for a in (0.0, 0.5, 1.0):
        for n in (1, 6, 10):
            for c in ("x", "y"):
                expected.append({"a": a, "n": n, "c": c})
    assert got == expected
    assert len(got) == 18
    assert list(got[0]) == ["a", "n", "c"]


def test_grid_int_axis_rounds_and_drops_duplicates():
    """AC-16: an int axis rounds its points and keeps each integer once."""
    assert grid([{"path": "n", "kind": "int", "lo": 1, "hi": 3}], 10) == [{"n": 1}, {"n": 2}, {"n": 3}]
    assert grid([{"path": "n", "kind": "int", "lo": 4, "hi": 4}], 3) == [{"n": 4}]
    got = grid([N], 3)
    assert all(type(p["n"]) is int for p in got)


def test_grid_float_axis_from_int_bounds_gives_floats():
    """AC-16: lo/hi given as ints still yield float points."""
    got = grid([{"path": "a", "kind": "float", "lo": 0, "hi": 1}], 3)
    assert got == [{"a": 0.0}, {"a": 0.5}, {"a": 1.0}]
    assert all(type(p["a"]) is float for p in got)


def test_grid_log_axis_literal():
    """AC-16: a log axis is geometric between lo and hi, ends exact."""
    got = grid([{"path": "g", "kind": "float", "lo": 1.0, "hi": 100.0, "log": True}], 3)
    assert got == [{"g": 1.0}, {"g": 10.000000000000002}, {"g": 100.0}]


def test_grid_per_dim_mapping_and_choice_ignores_count():
    """AC-16: per_dim may be a path->count mapping; a choice axis always lists all its values."""
    assert grid([A, N], {"a": 2, "n": 3}) == [
        {"a": 0.0, "n": 1}, {"a": 0.0, "n": 6}, {"a": 0.0, "n": 10},
        {"a": 1.0, "n": 1}, {"a": 1.0, "n": 6}, {"a": 1.0, "n": 10}]
    assert grid([A, {"path": "c", "kind": "choice", "values": ["p", "q"]}], {"a": 2}) == [
        {"a": 0.0, "c": "p"}, {"a": 0.0, "c": "q"}, {"a": 1.0, "c": "p"}, {"a": 1.0, "c": "q"}]
    assert grid([{"path": "c", "kind": "choice", "values": ["p", "q", "r"]}], 7) == [
        {"c": "p"}, {"c": "q"}, {"c": "r"}]


def test_grid_lo_equals_hi_and_no_dims():
    """AC-16 (Range lo == hi; Existence no dims): ported results."""
    assert grid([{"path": "a", "kind": "float", "lo": 2.0, "hi": 2.0}], 3) == [{"a": 2.0}] * 3
    assert grid([], 3) == [{}]


def test_grid_same_inputs_same_outputs_and_inputs_not_mutated():
    """AC-16: same arguments give the same list, and the dims are left untouched."""
    dims = copy.deepcopy(DIMS)
    first = grid(dims, 4)
    second = grid(dims, 4)
    assert first == second
    assert dims == DIMS


@pytest.mark.parametrize("bad", [
    [{"kind": "float", "lo": 0, "hi": 1}],
    [{"path": "a", "kind": "bogus"}],
    [{"path": "a", "kind": "choice", "values": []}],
    [{"path": "a", "kind": "float", "lo": 2, "hi": 1}],
    [{"path": "a", "kind": "float", "lo": 0, "hi": 1, "log": True}],
    [{"path": "a", "kind": "float", "lo": 0}],
])
def test_bad_dimension_is_value_error_in_both_functions(bad):
    """AC-16 (Conformance, ported _check): a malformed dimension raises ValueError."""
    with pytest.raises(ValueError):
        grid(bad, 3)
    with pytest.raises(ValueError):
        random_samples(bad, 1)


def test_grid_bad_counts_are_value_errors():
    """AC-16 (Range, ported): per_dim below 1, or a mapping missing a path, raises ValueError."""
    with pytest.raises(ValueError):
        grid([A], 0)
    with pytest.raises(ValueError):
        grid([A], {"zz": 2})


def test_random_samples_literal_for_seed_7():
    """AC-16: seed 7 reproduces the toy's draws exactly."""
    assert random_samples(DIMS, 4, seed=7) == [
        {"a": 0.32383276483316237, "n": 3, "c": "y"},
        {"a": 0.6509344730398537, "n": 2, "c": "x"},
        {"a": 0.36568891691258554, "n": 1, "c": "x"},
        {"a": 0.03749565844198488, "n": 7, "c": "y"}]


def test_random_samples_literal_for_seed_8_differs_from_seed_7():
    """AC-16: determinism is by seed; another seed gives other draws (literal from the toy)."""
    got = random_samples(DIMS, 4, seed=8)
    assert got == [
        {"a": 0.2267058593810488, "n": 7, "c": "x"},
        {"a": 0.1931166477860281, "n": 1, "c": "x"},
        {"a": 0.13684301262677445, "n": 9, "c": "x"},
        {"a": 0.4007102373381587, "n": 1, "c": "y"}]
    assert got != random_samples(DIMS, 4, seed=7)


def test_random_samples_default_seed_is_zero():
    """AC-16: seed defaults to 0; float draw literal for a single float dim."""
    assert random_samples([A], 3) == random_samples([A], 3, seed=0)
    assert random_samples([A], 3) == [{"a": 0.8444218515250481}, {"a": 0.7579544029403025},
                                      {"a": 0.420571580830845}]


def test_random_samples_prefix_property():
    """AC-16: one rng stream, so n=3 is the first three of n=4 for the same seed."""
    assert random_samples(DIMS, 3, seed=7) == random_samples(DIMS, 4, seed=7)[:3]


def test_random_samples_int_and_choice_literals():
    """AC-16: int dim (randint) and choice dim literals."""
    assert random_samples([{"path": "n", "kind": "int", "lo": 1, "hi": 6}], 8, seed=5) == [
        {"n": 5}, {"n": 3}, {"n": 6}, {"n": 3}, {"n": 6}, {"n": 6}, {"n": 6}, {"n": 5}]
    assert random_samples([{"path": "c", "kind": "choice", "values": ["p", "q", "r"]}], 5, seed=11) == [
        {"c": "q"}, {"c": "r"}, {"c": "q"}, {"c": "q"}, {"c": "r"}]


def test_random_samples_log_dims_literal():
    """AC-16: log float and log int draws."""
    dims = [{"path": "g", "kind": "float", "lo": 1.0, "hi": 100.0, "log": True},
            {"path": "k", "kind": "int", "lo": 2, "hi": 5, "log": True}]
    assert random_samples(dims, 3, seed=1) == [
        {"g": 1.8566433578077874, "k": 4},
        {"g": 33.69374137129035, "k": 3},
        {"g": 9.791972253410975, "k": 3}]


def test_random_samples_bounds_respected():
    """AC-16 (Range): every draw lies in [lo, hi] (inclusive), ints are ints, choices come from values."""
    dims = [A, N, C,
            {"path": "g", "kind": "float", "lo": 0.5, "hi": 8.0, "log": True},
            {"path": "k", "kind": "int", "lo": 2, "hi": 5, "log": True}]
    for seed in (0, 1, 2):
        for s in random_samples(dims, 300, seed=seed):
            assert 0.0 <= s["a"] <= 1.0 and type(s["a"]) is float
            assert 1 <= s["n"] <= 10 and type(s["n"]) is int
            assert s["c"] in ("x", "y")
            assert 0.5 <= s["g"] <= 8.0
            assert 2 <= s["k"] <= 5 and type(s["k"]) is int


def test_random_samples_lo_equals_hi_and_zero_samples():
    """AC-16 (Range lo == hi; Existence n == 0 and no dims): ported results."""
    dims = [{"path": "n", "kind": "int", "lo": 4, "hi": 4}, {"path": "a", "kind": "float", "lo": 2.5, "hi": 2.5}]
    assert random_samples(dims, 2, seed=3) == [{"n": 4, "a": 2.5}, {"n": 4, "a": 2.5}]
    assert random_samples(DIMS, 0) == []
    assert random_samples([], 2) == [{}, {}]


def test_outputs_do_not_depend_on_hash_order():
    """AC-16: no hash-order input; two processes with different PYTHONHASHSEED agree on string choices."""
    code = (
        "import json;from scripts.skilllab.sample import grid, random_samples;"
        "d=[{'path':'c','kind':'choice','values':['p','q','r','s']},{'path':'a','kind':'float','lo':0,'hi':1}];"
        "print(json.dumps([grid(d,3), random_samples(d,6,seed=2)]))")
    outs = []
    for hs in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hs)
        proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-500:]
        outs.append(json.loads(proc.stdout))
    assert outs[0] == outs[1] == outs[2]
    assert len(outs[0][0]) == 12


@pytest.mark.parametrize("n", [-1, -5])
def test_random_samples_negative_n_returns_empty_list(n):
    """AC-16 Reading: n < 0 returns an empty list, as the toy does."""
    assert random_samples(DIMS, n, seed=3) == []
    assert random_samples([], n) == []
