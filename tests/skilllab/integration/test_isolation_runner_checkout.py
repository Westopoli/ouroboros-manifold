# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7 (LI1: "never the repository checkout"; "Never checked out in the repository", section 2); CLAUDE.md Git
"""LI1 checkout safety: the runner reads git objects and writes only under its scratch root.

K1 a matrix run leaves the repo it archived from as it found it: HEAD, `git status`, and the files of the worktree (this one) are unchanged, and Westley's live checkout is unchanged.
K2 every path the rows name (fight_path), every tree it built, is under the scratch root and under neither this worktree nor the live checkout.   K3 the lab ran from the scratch tree, not from this one: the fight file names its
layout relative to the tree that ran it, and the built tree's own csrc built the library there.
Runs on the fixture's matrix (two versions, one fight each); no extra fight."""
import json
import os
from pathlib import Path

import isolation_fixtures as fx


def _state(repo):
    return {
        "head": fx.git(repo, "rev-parse", "HEAD"),
        "status": fx.git(repo, "status", "--porcelain", "--ignored=no"),
        "stash": fx.git(repo, "stash", "list"),
    }


def _mtimes(root, rels):
    return {rel: os.stat(Path(root) / rel).st_mtime_ns for rel in rels}


WATCH = ("Makefile", "csrc/unit.c", "scripts/skilllab/arena/run.py", "csrc/ouroboros_sim.h")


def test_k1_the_repositories_are_unchanged_by_a_run(tmp_path_factory):
    ir = fx.runner()
    scratch = tmp_path_factory.mktemp("k1-scratch")
    repos = [fx.ROOT] + ([fx.CHECKOUT] if fx.CHECKOUT.is_dir() else [])
    before = {str(r): _state(r) for r in repos}
    stamps = {str(r): _mtimes(r, WATCH) for r in repos}
    listing = sorted(p.name for p in fx.ROOT.iterdir())
    rows = ir.run_matrix(["then"], [fx.SITUATION], [fx.SEED], scratch, scratch / "rows.jsonl", repo=fx.ROOT)     # an error row still goes through every step up to the layout
    assert len(rows) == 1
    assert {str(r): _state(r) for r in repos} == before
    assert {str(r): _mtimes(r, WATCH) for r in repos} == stamps
    assert sorted(p.name for p in fx.ROOT.iterdir()) == listing, "no file or directory appeared at the worktree root (no libouroboros.so, no pipe/, no scratch)"


def test_k2_every_path_is_under_the_scratch_root(iso_scratch):
    scratch = Path(iso_scratch).resolve()
    ir = fx.runner()
    for r in fx.matrix(iso_scratch).first:
        path = Path(r["fight_path"]).resolve()
        assert path.is_relative_to(scratch)
        for repo in (fx.ROOT.resolve(), fx.CHECKOUT.resolve()):
            assert not path.is_relative_to(repo) or scratch.is_relative_to(repo), "the fight file is inside a repository; only the scratch root may be (and it is not)"
        tree = ir.build_version(ir.resolve_version(r["version"], repo=fx.ROOT), iso_scratch, repo=fx.ROOT).resolve()
        assert tree.is_relative_to(scratch) and (tree / "libouroboros.so").is_file()
    assert not scratch.is_relative_to(fx.ROOT.resolve()) and not scratch.is_relative_to(fx.CHECKOUT.resolve())


def test_k3_the_lab_that_ran_was_the_scratch_trees_own(iso_scratch):
    ir = fx.runner()
    then = fx.by_version(fx.matrix(iso_scratch).first, "then")
    doc = json.loads(Path(then["fight_path"]).read_text())
    assert doc["layout_path"] == "docs/northstar/research/layer_dynamics/catalogue/%s.toml" % fx.LAYOUT      # relative to the tree that ran it
    tree = ir.build_version(ir.resolve_version("then", repo=fx.ROOT), iso_scratch, repo=fx.ROOT)
    assert (tree / "scripts" / "skilllab" / "arena" / "run.py").read_text() != (fx.ROOT / "scripts" / "skilllab" / "arena" / "run.py").read_text()
    assert '"fired"' not in (tree / "scripts" / "skilllab" / "arena" / "run.py").read_text()
