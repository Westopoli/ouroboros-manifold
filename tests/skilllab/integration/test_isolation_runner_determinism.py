# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7 (LI1: "deterministic"); section 2 ("All runs deterministic, same seeds, same layout files")
"""LI1 determinism: the same version, layout and seed give the same row and the same fight file, whatever directory the run wrote to and whichever scratch root built the tree.

D1 two matrix runs (two out dirs, one scratch) have equal rows, byte for byte, ignoring only `fight_path`.   D2 the two rows files are equal line for line once fight_path is dropped, and the fight files are equal bytes.
D3 a second scratch root (a fresh `git archive` and build of `then`) gives the same fight_sha256: no scratch path, clock or hash order gets into the fight file.   D4 a built version is cached by sha: the second build call
returns the same tree, rebuilds nothing, and the tree is the archive (no `.git`)."""
import os
from pathlib import Path

import isolation_fixtures as fx


def test_d1_two_runs_have_identical_rows(iso_scratch):
    m = fx.matrix(iso_scratch)
    assert [fx.sans_path(r) for r in m.first] == [fx.sans_path(r) for r in m.second]
    assert [r["fight_sha256"] for r in m.first] == [r["fight_sha256"] for r in m.second]


def test_d2_rows_files_and_fight_files_are_equal(iso_scratch):
    m = fx.matrix(iso_scratch)
    ir = fx.runner()
    assert [fx.sans_path(r) for r in ir.read_rows(m.file1)] == [fx.sans_path(r) for r in ir.read_rows(m.file2)]
    for a, b in zip(m.first, m.second):
        assert a["fight_path"] != b["fight_path"] and Path(a["fight_path"]).read_bytes() == Path(b["fight_path"]).read_bytes()
        assert Path(a["fight_path"]).is_relative_to(m.out1) and Path(b["fight_path"]).is_relative_to(m.out2)


def test_d3_a_fresh_scratch_root_gives_the_same_fight(iso_scratch, tmp_path):
    ir = fx.runner()
    row = ir.run_one("then", fx.LAYOUT, fx.SEED, tmp_path / "other-scratch", repo=fx.ROOT)
    assert row["error"] is None
    assert row["fight_sha256"] == fx.by_version(fx.matrix(iso_scratch).first, "then")["fight_sha256"]
    assert Path(row["fight_path"]).is_relative_to(tmp_path / "other-scratch")        # the default out dir lives in the scratch root


def test_d4_build_is_cached_by_sha(iso_scratch):
    ir = fx.runner()
    fx.matrix(iso_scratch)                                  # builds then and now
    version = ir.resolve_version("then", repo=fx.ROOT)
    tree = ir.build_version(version, iso_scratch, repo=fx.ROOT)
    lib = tree / "libouroboros.so"
    assert lib.is_file() and tree.parent == Path(iso_scratch) and fx.THEN_SHA in tree.name
    assert (tree / "csrc").is_dir() and (tree / "scripts" / "skilllab" / "arena" / "run.py").is_file() and not (tree / ".git").exists()
    before = os.stat(lib).st_mtime_ns
    again = ir.build_version(version, iso_scratch, repo=fx.ROOT)
    assert again == tree and os.stat(lib).st_mtime_ns == before
    other = ir.build_version(ir.resolve_version("fix", ref=fx.THEN_SHA, repo=fx.ROOT), iso_scratch, repo=fx.ROOT)
    assert other == tree, "the cache key is the sha, not the name"
