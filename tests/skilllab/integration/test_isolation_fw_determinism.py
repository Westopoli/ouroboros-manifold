# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7 (determinism: same seed, byte-identical fight document; no wall clock or hash-order input; never the repository checkout), section 3 (arms F and W)
"""LI4-FW determinism and checkout safety, one real layout (L-0055 at `now`, both arms, both variants, seed 10: 4 fights) run twice, the second time from a fresh scratch root and out dir.

D1 equal rows ignoring only `fight_path`, equal fight files (byte for byte: sha256), whichever scratch root or out dir; the twin's file and the neutral layout's file carry no scratch path.
D2 the comparison rows of the two runs are equal and carry no scratch path.   D3 the run touched nothing outside its scratch root: the worktree and the live checkout are as found, no libouroboros.so appeared."""
import json
import os
from pathlib import Path

import isolation_fixtures as fx
import isolation_fw_real as real

LAYOUT = "L-0055"


def _run(scratch, tag):
    rows_path = Path(scratch) / ("rows-%s" % tag) / "rows.jsonl"
    return real.fw().run_arms(["now"], scratch, rows_path, arms=("F", "W"), layouts=(LAYOUT,), seeds=(10,), repo=real.ROOT, out_dir=Path(scratch) / ("fights-" + tag))


def _state(repo):
    return {"head": fx.git(repo, "rev-parse", "HEAD"), "refs": fx.git(repo, "for-each-ref", "--format=%(refname) %(objectname)"), "status": fx.git(repo, "status", "--porcelain", "--ignored=no"),
            "worktrees": fx.git(repo, "worktree", "list", "--porcelain")}


def test_d1_d2_d3_two_runs_two_scratch_roots(iso_scratch, tmp_path_factory):
    repos = [real.ROOT] + ([fx.CHECKOUT] if fx.CHECKOUT.is_dir() else [])
    before = {str(r): _state(r) for r in repos}
    listing = sorted(p.name for p in real.ROOT.iterdir())
    second_root = tmp_path_factory.mktemp("fw-second-root")
    one, two = _run(iso_scratch, "one"), _run(second_root, "two")
    assert len(one) == len(two) == 4 and [(r["arm"], r["variant"]) for r in one] == [("F", "layout"), ("F", "control"), ("W", "layout"), ("W", "control")]
    assert all(r["error"] is None for r in one + two), [r["error"] for r in one + two]
    assert [fx.sans_path(r) for r in one] == [fx.sans_path(r) for r in two], "equal runs give equal rows ignoring only fight_path"
    for a, b in zip(one, two):
        assert a["fight_sha256"] == b["fight_sha256"] == fx.sha256(a["fight_path"]) == fx.sha256(b["fight_path"]), "byte-identical fight files"
        text = Path(a["fight_path"]).read_text()
        assert str(iso_scratch) not in text and str(second_root) not in text, "no scratch path reaches a fight file"
        assert str(iso_scratch) in a["fight_path"] and str(second_root) in b["fight_path"]
    mod = real.fw()
    c1, c2 = mod.comparison_rows(one, repo=real.ROOT), mod.comparison_rows(two, repo=real.ROOT)
    assert c1 == c2 and json.dumps(c1, sort_keys=True) == json.dumps(c2, sort_keys=True)
    assert str(iso_scratch) not in json.dumps(c1) and str(second_root) not in json.dumps(c1)
    assert len(c1) == 1 and c1[0]["layout"] == LAYOUT and c1[0]["then"] == "not run", "a comparison of one version says so; it never invents the other column"
    assert {str(r): _state(r) for r in repos} == before
    assert sorted(p.name for p in real.ROOT.iterdir()) == listing and not (real.ROOT / "libouroboros.so").exists()
    for r in one + two:
        assert not Path(r["fight_path"]).resolve().is_relative_to(real.ROOT) and not Path(r["fight_path"]).resolve().is_relative_to(fx.CHECKOUT)
