# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 1 precondition 3 ("Flags are signals, never verdicts"), section 2 (a version that cannot run is said), section 7 (LI4: F and W through LI1's runner)
"""LI4-FW errors: nothing blocks. A run that cannot run is an error row (never an exception, never a skipped cell), and the comparison says `not measured`, never `same`.

E1 an unknown arm, or an arm of another piece's (M, V, R, P) is a ValueError before any run; `arms` default is ("F", "W").
E2 a `fix` ref that is no commit: every row of the matrix is an error row of stage `resolve`, lab_sha null, result/margin/units_firing/measures/invalid null, a non-empty message; the rows file has one line each.
E3 a layout the version's lab does not have (L-9999) is an error row of stage `layout` for both variants of both arms, at a version that builds (`then`); no exception.
E4 `cell()` of error rows: winner and every measure `not measured: <stage>: <message>`; `same_or_changed` of such a cell is not `same`."""
import json
from pathlib import Path

import pytest

import isolation_fixtures as fx
import isolation_fw_real as real


def test_e1_arms(iso_scratch):
    mod = real.fw()
    for bad in (("X",), ("M",), ("R",), ("F", "Q")):
        with pytest.raises(ValueError):
            mod.run_arms(["then"], iso_scratch, Path(iso_scratch) / "e1.jsonl", arms=bad, layouts=("L-0055",), seeds=(10,), repo=real.ROOT)
    import inspect
    assert inspect.signature(mod.run_arms).parameters["arms"].default == ("F", "W")
    assert inspect.signature(mod.run_arms).parameters["layouts"].default == real.STAGE3
    assert tuple(inspect.signature(mod.run_arms).parameters["seeds"].default) == (10, 1)


def test_e2_a_ref_that_is_no_commit_gives_error_rows_not_a_raise(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    rows = real.fw().run_arms(["fix"], tmp_path, rows_path, arms=("F", "W"), layouts=("L-0055", "L-0073"), seeds=(10, 1), refs={"fix": "no-such-ref-li4fw"}, repo=real.ROOT)
    assert len(rows) == 2 * 2 * 2 * 2          # arms x layouts x variants x seeds, one version
    for r in rows:
        assert set(r) == real.FW_KEYS and r["version"] == "fix"
        assert r["error"]["stage"] == "resolve" and r["error"]["message"] and r["lab_sha"] is None
        assert all(r[k] is None for k in ("result", "margin", "units_firing", "fight_path", "fight_sha256", "measures", "invalid"))
    assert [(r["arm"], r["layout"], r["variant"], r["seed"]) for r in rows[:4]] == [("F", "L-0055", "layout", 10), ("F", "L-0055", "layout", 1), ("F", "L-0055", "control", 10), ("F", "L-0055", "control", 1)]
    assert fx.runner().read_rows(rows_path) == rows and len(rows_path.read_text().splitlines()) == 16


def test_e3_a_layout_the_lab_does_not_have_is_an_error_row_at_a_version_that_builds(iso_scratch):
    rows = real.fw().run_arms(["then"], iso_scratch, Path(iso_scratch) / "e3.jsonl", arms=("W", "F"), layouts=("L-9999",), seeds=(10,), repo=real.ROOT)
    assert [(r["arm"], r["variant"]) for r in rows] == [("W", "layout"), ("W", "control"), ("F", "layout"), ("F", "control")]
    for r in rows:
        assert r["error"]["stage"] == "layout" and "L-9999" in r["error"]["message"] and r["lab_sha"] == fx.THEN_SHA
        assert r["measures"] is None and r["invalid"] is None and r["result"] is None


def test_e4_cells_and_comparison_of_failed_runs_say_not_measured(tmp_path):
    mod = real.fw()
    rows = mod.run_arms(["fix"], tmp_path, tmp_path / "rows.jsonl", arms=("W",), layouts=("L-0055",), seeds=(10, 1), refs={"fix": "no-such-ref-li4fw"}, repo=real.ROOT)
    cell = mod.cell([r for r in rows if r["variant"] == "layout"])
    assert cell["winner"].startswith("not measured") and "resolve" in cell["winner"]
    assert cell["error"]["stage"] == "resolve"
    for key in ("survivors", "last_tick", "end", "invalid", "units_firing"):
        assert isinstance(cell[key], str) and cell[key].startswith("not measured"), key
    assert all(str(v).startswith("not measured") for v in cell["predictions"].values())
    assert all(w.startswith("not measured") for _, w in cell["winners"])
    assert mod.same_or_changed(dict(cell["winners"]), {10: "A", 1: "A"})["verdict"].startswith("not measured")
