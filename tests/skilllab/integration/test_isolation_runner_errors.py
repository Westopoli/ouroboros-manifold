# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7 (LI1: "failures produce an error row (never silently skipped)"); section 1 precondition 8 (findings are never smoothed over)
"""LI1 failures: every run asked for yields a row; one that cannot run is an error row with the same keys, never a skip, never a zero, never an exception out of the matrix.

E1 an unbuildable sha (a real commit whose csrc does not compile) gives an error row, stage `build`, and the failed tree is not cached as built.   E2 a ref that is no commit gives an error row (stage `resolve` or `archive`).
E3 a layout the version's own lab refuses (SIT-0106 at `then`: "arc too small") gives an error row, stage `layout`, carrying the lab's reason; the matrix goes on to the next run.   E4 an unknown layout id is an error row, stage `layout`.
E5 an error row has every ROW_KEYS key; result, margin, units_firing, fight_path and fight_sha256 are null (never 0, never ""); the CLI exits 1 and still writes the row, exit 0 when every row is ok.
Error stages: resolve, archive, build, layout, fight."""
import subprocess
from pathlib import Path

import pytest

import isolation_fixtures as fx

STAGES = ("resolve", "archive", "build", "layout", "fight")


def _assert_error_row(row, stage_in, name, layout, why=None):
    assert set(row) == fx.ROW_KEYS
    assert row["version"] == name and row["layout"] == layout and row["seed"] == fx.SEED and row["arm"] == "W"
    assert isinstance(row["error"], dict) and set(row["error"]) == {"stage", "message"}
    assert row["error"]["stage"] in stage_in and row["error"]["message"]
    for key in ("result", "margin", "units_firing", "fight_path", "fight_sha256"):
        assert row[key] is None, key
    if why:
        assert why in row["error"]["message"]


@pytest.fixture(scope="module")
def broken_repo(tmp_path_factory):
    """A throwaway clone of this repo (its own .git, in the test's temp dir) with one more commit on top of `then` whose csrc/unit.c does not compile. Returns (clone path, broken sha)."""
    clone = tmp_path_factory.mktemp("broken") / "clone"
    subprocess.run(["git", "clone", "-q", "--local", "--no-checkout", str(fx.ROOT), str(clone)], check=True, capture_output=True)
    fx.git(clone, "-c", "advice.detachedHead=false", "checkout", "-q", fx.THEN_SHA)
    with open(clone / "csrc" / "unit.c", "a") as f:
        f.write("\n#error unbuildable_on_purpose_for_li1\n")
    fx.git(clone, "-c", "user.name=li1", "-c", "user.email=li1@example.invalid", "commit", "-q", "-am", "broken on purpose")
    return clone, fx.git(clone, "rev-parse", "HEAD")


def test_e1_unbuildable_sha_is_an_error_row(broken_repo, tmp_path):
    ir = fx.runner()
    clone, sha = broken_repo
    row = ir.run_one("fix", fx.LAYOUT, fx.SEED, tmp_path, ref=sha, repo=clone)
    _assert_error_row(row, ("build",), "fix", fx.LAYOUT)
    assert row["lab_sha"] == sha                              # the sha is known and in the key; only the build failed
    assert "unbuildable_on_purpose_for_li1" in row["error"]["message"] or "error" in row["error"]["message"].lower()
    with pytest.raises(ir.BuildError) as why:
        ir.build_version(ir.resolve_version("fix", ref=sha, repo=clone), tmp_path, repo=clone)   # still fails: a failed build is not cached as a good tree
    assert why.value.stage == "build"


def test_e2_a_ref_that_is_no_commit_is_an_error_row(tmp_path):
    ir = fx.runner()
    row = ir.run_one("fix", fx.LAYOUT, fx.SEED, tmp_path, ref="0" * 40, repo=fx.ROOT)
    _assert_error_row(row, ("resolve", "archive"), "fix", fx.LAYOUT)
    assert row["lab_sha"] is None or row["lab_sha"] == "0" * 40


def test_e3_a_layout_the_version_refuses_is_an_error_row_and_the_matrix_goes_on(iso_scratch, tmp_path):
    ir = fx.runner()
    rows_file = tmp_path / "rows.jsonl"
    rows = ir.run_matrix(["then"], [fx.SITUATION, fx.LAYOUT], [fx.SEED], iso_scratch, rows_file, repo=fx.ROOT, out_dir=tmp_path / "fights")
    assert len(rows) == 2 and len(ir.read_rows(rows_file)) == 2          # the refused one did not end the matrix
    _assert_error_row(rows[0], ("layout",), "then", fx.SITUATION, "arc too small")
    assert rows[0]["lab_sha"] == fx.THEN_SHA
    assert rows[1]["error"] is None and rows[1]["layout"] == fx.LAYOUT


def test_e4_an_unknown_layout_id_is_an_error_row(iso_scratch, tmp_path):
    row = fx.runner().run_one("then", "L-9999", fx.SEED, iso_scratch, repo=fx.ROOT, out_dir=tmp_path)
    _assert_error_row(row, ("layout",), "then", "L-9999")


def test_e5_cli_exit_codes_and_the_row_is_written(iso_scratch, tmp_path):
    ir = fx.runner()
    rows_file = tmp_path / "rows.jsonl"
    done = subprocess.run([fx.PY, "-m", "scripts.skilllab.arena.isolation_runner", "--version", "then", "--layout", fx.SITUATION, "--seed", str(fx.SEED),
                           "--scratch", str(iso_scratch), "--rows", str(rows_file), "--repo", str(fx.ROOT), "--out", str(tmp_path / "fights")],
                          cwd=str(fx.ROOT), capture_output=True, text=True)
    assert done.returncode == 1, done.stdout + done.stderr
    (row,) = ir.read_rows(rows_file)
    _assert_error_row(row, ("layout",), "then", fx.SITUATION, "arc too small")
