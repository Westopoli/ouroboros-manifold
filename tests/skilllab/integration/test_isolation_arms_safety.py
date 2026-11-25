# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7 ("never the repository checkout"; "determinism (same seed, byte-identical fight document; no wall clock or hash-order input)"; "one worktree under ~/Projects/om-wt/, no push, no merge by agents"),
# section 2 ("Never checked out in the repository"), section 1 precondition 7 (one click per side, "not from the runner, a layout or a test")
"""LI3 arm safety, whole runs on `now` in a fresh scratch root: one M cell (8 against 16, both orders) and one V cell (flat, 8 a side, holder A).

Z1 the repositories (this worktree and Westley's live checkout) are unchanged by the arms: HEAD, status, stash, the catalogue directory, a file watch; every layout the arms wrote is under the scratch root, none in a repository.
Z2 the lab is called as the arm's brief says: M with sight off (no `--sight on`, no `--control`), V with `--sight on --control sight`; one `--layout` and one `--seed` per call; nothing else that could be a second order.
Z3 deterministic: the same arm cell twice (two out dirs) gives equal rows ignoring only `fight_path`, and byte-identical fight files and layout files.   Z4 the CLI writes the same rows as the function."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import isolation_arms_fixtures as af
import isolation_fixtures as fx

WATCH = ("Makefile", "csrc/unit.c", "scripts/skilllab/arena/run.py", "scripts/skilllab/arena/isolation_runner.py", "csrc/ouroboros_sim.h")


def scrub(row):
    """The row as bytes ignoring every path (the row's fight_path and a twin's): equal runs are equal in these bytes."""
    row = json.loads(json.dumps(row))
    row.pop("fight_path", None)
    if isinstance(row.get("twin"), dict):
        row["twin"].pop("fight_path", None)
    return json.dumps(row, sort_keys=True)


def _state(repo):
    return {"head": fx.git(repo, "rev-parse", "HEAD"), "status": fx.git(repo, "status", "--porcelain", "--ignored=no"), "stash": fx.git(repo, "stash", "list"),
            "catalogue": sorted(p.name for p in (Path(repo) / af.LD / "catalogue").iterdir()), "mtimes": {rel: os.stat(Path(repo) / rel).st_mtime_ns for rel in WATCH if (Path(repo) / rel).exists()}}


@pytest.fixture(scope="module")
def cells(tmp_path_factory):
    """Run one M cell and one V cell in a fresh scratch root, recording the repositories before and after and the lab calls (the real runs still happen)."""
    scratch = tmp_path_factory.mktemp("arms-safety")
    repos = [fx.ROOT] + ([fx.CHECKOUT] if fx.CHECKOUT.is_dir() else [])
    before = {str(r): _state(r) for r in repos}
    calls, real = [], subprocess.run

    def spy(argv, *args, **kw):
        calls.append((list(map(str, argv)), str(kw.get("cwd"))))
        return real(argv, *args, **kw)

    a = af.arms()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(subprocess, "run", spy)
        m_row = a.run_m("now", 8, scratch, swap=False, seed=10, repo=fx.ROOT, out_dir=scratch / "o1")
        n_m = len(calls)
        v_row = a.run_v_flat("now", scratch, heads=8, holder="A", seed=10, repo=fx.ROOT, out_dir=scratch / "o1")
    after = {str(r): _state(r) for r in repos}
    return scratch, before, after, m_row, v_row, calls, n_m


def test_z1_no_repository_changed_and_every_layout_is_in_the_scratch_root(cells):
    scratch, before, after, m_row, v_row, _, _ = cells
    assert m_row["error"] is None and v_row["error"] is None
    assert after == before
    for row in (m_row, v_row):
        assert Path(row["fight_path"]).resolve().is_relative_to(scratch.resolve())
        tree = scratch / ("tree-" + row["lab_sha"])
        assert (tree / af.LD / "catalogue" / (row["layout"] + ".toml")).is_file()
        for repo in [fx.ROOT] + ([fx.CHECKOUT] if fx.CHECKOUT.is_dir() else []):
            assert not (Path(repo) / af.LD / "catalogue" / (row["layout"] + ".toml")).exists()


def test_z2_the_lab_is_called_with_the_flags_of_the_arm_and_nothing_else(cells):
    _, _, _, m_row, v_row, calls, n_m = cells
    labs = [c for c in af.fight_lab_calls([c[0] for c in calls])]
    assert len(labs) >= 2
    m_calls, v_calls = af.fight_lab_calls([c[0] for c in calls[:n_m]]), af.fight_lab_calls([c[0] for c in calls[n_m:]])
    assert len(m_calls) == 1 and len(v_calls) == 1, "one lab call per cell: no retry, no second order, no separate twin run"
    (m,), (v,) = m_calls, v_calls
    assert af.flag_value(m, "--sight") in (None, "off") and "--control" not in m and "--control-dir" not in m
    assert af.flag_value(v, "--sight") == "on" and af.flag_value(v, "--control") == "sight" and af.flag_value(v, "--control-dir")
    for argv, row in ((m, m_row), (v, v_row)):
        assert argv.count("--layout") == 1 and argv.count("--seed") == 1 and af.flag_value(argv, "--seed") == "10"
        assert Path(af.flag_value(argv, "--layout")).stem == row["layout"]
        allowed = {"-m", "scripts.skilllab.arena.run", "--layout", "--seed", "--out", "--sight", "--control", "--control-dir", "--allow-invalid", "on", "off", "sight"}
        assert {x for x in argv[1:] if x.startswith("-") or x in allowed} <= allowed, "no flag the brief does not name"


def test_z3_the_same_cell_twice_is_the_same_rows_and_the_same_bytes(cells, tmp_path):
    scratch, _, _, m_row, v_row, _, _ = cells
    a = af.arms()
    m2 = a.run_m("now", 8, scratch, swap=False, seed=10, repo=fx.ROOT, out_dir=tmp_path / "o2")
    v2 = a.run_v_flat("now", scratch, heads=8, holder="A", seed=10, repo=fx.ROOT, out_dir=tmp_path / "o2")
    for one, two in ((m_row, m2), (v_row, v2)):
        assert scrub(one) == scrub(two)
        assert one["fight_path"] != two["fight_path"] and Path(one["fight_path"]).read_bytes() == Path(two["fight_path"]).read_bytes()
        if isinstance(one.get("twin"), dict):
            assert Path(one["twin"]["fight_path"]).read_bytes() == Path(two["twin"]["fight_path"]).read_bytes()
        layout = Path(scratch) / ("tree-" + one["lab_sha"]) / af.LD / "catalogue" / (one["layout"] + ".toml")
        assert layout.read_text() == af.arms().layout_toml(af.arms().m_layout(16, 8, False) if one["arm"] == "M" else af.arms().v_layout(8, "A"))


def test_z4_the_cli_writes_the_rows_the_function_returns(cells, tmp_path):
    scratch, _, _, m_row, _, _, _ = cells
    rows_file = tmp_path / "rows.jsonl"
    done = subprocess.run([fx.PY, "-m", "scripts.skilllab.arena.isolation_arms", "--arm", "M", "--version", "now", "--heads", "8", "--seeds", "10", "--scratch", str(scratch), "--rows", str(rows_file),
                           "--out", str(tmp_path / "o3")], cwd=str(fx.ROOT), capture_output=True, text=True)
    assert done.returncode in (0, 1), done.stderr[-500:]
    rows = [json.loads(line) for line in rows_file.read_text().splitlines()]
    assert len(rows) == 2 and [r["swap"] for r in rows] == [False, True], "a cell is both spawn orders"
    assert scrub(rows[0]) == scrub(m_row)
    assert (done.returncode == 1) is any(r["error"] for r in rows)
