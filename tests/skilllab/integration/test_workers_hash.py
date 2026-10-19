# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Rulings in force::13 and Pieces::S; decisions 14 and 23
"""Rows hashed at 1 and 12 workers are byte-identical (ruling 13, LAB-REV2-S), real and fake, with planted nondeterminism controls.

INTERFACE (S builds nothing; "tests only". All of it exists on push/labrev2-lab at 4c638fc0):
  sweep.run_smoke(out_dir, workers=12, *, builds, control_builds, layouts, fight_fn, map_fn, full_scan, replicates) -> summary
    writes smoke.csv and smoke_summary.json ("rows_sha256" is the sha256 of smoke.csv); workers > 1 with no fight_fn and no map_fn
    fights through `pool.FightPool(workers, lean=True).map`, reached as the attribute `pool.FightPool` of scripts.skilllab.pool;
  sweep.run(families, out_dir, workers=1, full_scan=False, **kw) writes sweep_<family>.csv and sweep_summary.json
    (kw: builds, layouts, plays, replicates, fight_fn, map_fn, caps);
  fakes_scans.FakePool / ScriptedFight / fake_builds / _fr (tests/skilllab/fakes_scans.py).

Real cases (OM_LAB_SLOW=1, real engine, a spawned 12-worker pool): the smoke run, and one sweep family narrowed to one designated
play on one layout at one replicate (the whole damage_up family at three replicates is hours at one worker; narrowing it changes
how many rows there are, not whether worker count may change a byte). The smoke files test_sweep_real.py already holds one 1 v 12
smoke check inside a larger case about caps and defects; this file is the guard for the identity alone, so a cap finding does not
hide a hash finding.

Fast cases: the same two entry points through the fakes, always on. They fight in-process, with the real code path of sweep (pool
reached as `pool.FightPool`) replaced by a fake that stands in for the 12 workers.

FOR L4/L7 (after S lands): test_sweep_real.py::test_smoke_rows_are_the_same_bytes_at_1_and_12_workers_and_every_fight_ends_clean and
test_sweep.py::test_smoke_rows_are_the_same_bytes_at_one_and_twelve_workers carry hash lines that this file now guards on its own;
drop the duplicate hash lines there (keep the cap and defect assertions). Nothing here edits those files.

Controls (each proves the detector `assert_same_rows` fires, and each has a complement that proves it does not fire on honest runs):
  - order: a pool that returns results in completion order, not job order. The run's rows move to the wrong cells.
  - row permutation: the same set of rows written in reverse order on the 12-worker run (rows.write_rows patched). A detector that
    compared sorted lines, or only a count, would pass it; the control also asserts the sorted lines are equal, so the plant moves rows
    and changes nothing else.
  - worker identity: a pool whose results carry the index of the worker that ran the job (job index modulo the worker count). One
    worker and twelve workers then write different rows.
The planted controls assert that the plant really changed what it claims to (the pool says it reordered, the results differ), so a
control that stops planting goes red instead of vacuously passing.

Not pinned (Westley's): no number in this file is a threshold; the layout, play and replicate count of the real sweep case are the
test's own narrowing and are named below.
"""
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
HERE = str(Path(__file__).resolve().parents[1])
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from fakes_scans import FakePool, ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab import fight as fight_module, pool, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights, a 12-worker pool; set OM_LAB_SLOW=1")

REAL_SWEEP_FAMILY = "damage_up"
REAL_SWEEP_PLAY = "s3_types_by_reach"       # decisions 22: damage-up's designated fight
REAL_SWEEP_LAYOUT = "192"                    # the smoke layout where the vision plays place (the other two are refused)
REAL_SWEEP_REPLICATES = 1


# ---- the detector ------------------------------------------------------------------------------------------------------------------

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assert_same_rows(dir_a, dir_b, names):
    """THE detector: every named output file is the same bytes (and so the same sha256) in both directories."""
    for name in names:
        a, b = Path(dir_a) / name, Path(dir_b) / name
        assert a.exists() and b.exists(), name
        assert sha(a) == sha(b), "%s differs between %s and %s" % (name, dir_a, dir_b)
        assert a.read_bytes() == b.read_bytes(), name


SMOKE_FILES = ("smoke.csv", "smoke_summary.json")


def sweep_files(family):
    return ("sweep_%s.csv" % family, "sweep_summary.json")


# ---- real, gated ---------------------------------------------------------------------------------------------------------------------

@SLOW
def test_real_smoke_rows_hash_identically_at_1_and_12_workers(tmp_path):
    one = sweep.run_smoke(tmp_path / "w1", workers=1)
    twelve = sweep.run_smoke(tmp_path / "w12", workers=12)
    assert one["rows"] == twelve["rows"] and one["rows"] > 0
    assert one["rows_sha256"] == twelve["rows_sha256"] == sha(tmp_path / "w1" / "smoke.csv") == sha(tmp_path / "w12" / "smoke.csv")
    assert_same_rows(tmp_path / "w1", tmp_path / "w12", SMOKE_FILES)


@SLOW
def test_real_sweep_family_rows_are_the_same_bytes_at_1_and_12_workers(tmp_path):
    kw = dict(layouts={REAL_SWEEP_LAYOUT: sweep.smoke_layouts()[REAL_SWEEP_LAYOUT]}, plays=(REAL_SWEEP_PLAY,),
              replicates=REAL_SWEEP_REPLICATES)
    one = sweep.run([REAL_SWEEP_FAMILY], tmp_path / "w1", workers=1, **kw)
    sweep.run([REAL_SWEEP_FAMILY], tmp_path / "w12", workers=12, **kw)
    entry = one["families"][REAL_SWEEP_FAMILY]
    assert entry["skipped"] is None and entry["rows"] > 0 and entry["csv"] == "sweep_damage_up.csv"
    assert_same_rows(tmp_path / "w1", tmp_path / "w12", sweep_files(REAL_SWEEP_FAMILY))


# ---- fast, with fakes --------------------------------------------------------------------------------------------------------------------

def varied(setup, seed, swap):
    """A result that differs by cell, play, role, seed and swap, so a row that moves or a worker that leaks shows in the bytes."""
    u = setup.unit_types
    enemy, role, play = u["enemy"], u["_role"], u["_play"]
    margin = 0.5 + 0.001 * enemy + 0.01 * seed + (0.02 if swap else 0.0) + 0.003 * len(role) + 0.0007 * len(play)
    return _fr("side0" if enemy <= 16 else "side1", enemy, margin=margin if enemy <= 16 else -margin)


def world():
    return ScriptedFight(result_of=varied)


def control_builds():
    return {name: (lambda enemy_heads, swap, name=name: Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": name,
                                                                                    "_role": "play"}))
            for name in ("mirror", "numbers", "planted")}


class CompletionOrderPool(FakePool):
    """Planted worker-order nondeterminism: results come back in the order the jobs finish, not the order they went in. Job i
    finishes at time (n - i), so the last job finishes first: the list is reversed. `reordered` records that a map was reordered."""
    reordered = 0

    def map(self, jobs):
        jobs = list(jobs)
        finished = sorted(range(len(jobs)), key=lambda i: (len(jobs) - i, i))
        results = {i: self.fight_fn(*jobs[i]) for i in range(len(jobs))}
        out = [results[i] for i in finished]
        if len(jobs) > 1 and out != [results[i] for i in range(len(jobs))]:
            type(self).reordered += 1
        self.maps.append(len(jobs))
        return out


class WorkerIdentityPool(FakePool):
    """Planted nondeterminism of the other kind: the result carries which of the `workers` workers ran the job."""
    leaked = 0

    def map(self, jobs):
        jobs = list(jobs)
        self.maps.append(len(jobs))
        out = []
        for i, job in enumerate(jobs):
            r = self.fight_fn(*job)
            worker = i % self.workers
            type(self).leaked += worker > 0
            out.append(dataclasses.replace(r, margin=r.margin + 0.0001 * worker))
        return out


def _install(monkeypatch, cls):
    FakePool.instances.clear()
    FakePool.fight_fn = world()        # FakePool.__init__ reads the attribute on the base class
    monkeypatch.setattr(pool, "FightPool", cls)


def _one_worker(monkeypatch):
    """The 1-worker run takes the default in-process path: no fight_fn is passed, fight.fight is replaced by the stand-in (scan reaches
    it as the attribute `fight.fight`), and afterwards no pool was built, so a 1-worker run that slipped into a pool would show."""
    monkeypatch.setattr(fight_module, "fight", world())


def _no_pool_yet():
    assert FakePool.instances == [], "the 1-worker run built a pool"


def _smoke_pair(tmp_path, monkeypatch, cls, twelve_patch=None):
    """workers=1 in-process, workers=12 through the (fake) pool `cls`; `twelve_patch(monkeypatch)` plants something on the 12 only."""
    _install(monkeypatch, cls)
    with monkeypatch.context() as m:
        _one_worker(m)
        sweep.run_smoke(tmp_path / "w1", workers=1, builds=fake_builds(), control_builds=control_builds())
    _no_pool_yet()
    with monkeypatch.context() as m:
        if twelve_patch:
            twelve_patch(m)
        sweep.run_smoke(tmp_path / "w12", workers=12, builds=fake_builds(), control_builds=control_builds())
    assert FakePool.instances and FakePool.instances[-1].workers == 12 and FakePool.instances[-1].maps        # the pool was used


def _sweep_pair(tmp_path, monkeypatch, cls, twelve_patch=None):
    _install(monkeypatch, cls)
    kw = dict(builds=fake_builds(), layouts={"A": {}}, plays=("p2",))
    with monkeypatch.context() as m:
        _one_worker(m)
        sweep.run([REAL_SWEEP_FAMILY], tmp_path / "w1", workers=1, **kw)
    _no_pool_yet()
    with monkeypatch.context() as m:
        if twelve_patch:
            twelve_patch(m)
        sweep.run([REAL_SWEEP_FAMILY], tmp_path / "w12", workers=12, **kw)
    assert FakePool.instances and FakePool.instances[-1].workers == 12 and FakePool.instances[-1].maps


def reverse_row_order(m):
    """Planted pure permutation: write_rows writes the same rows, last first."""
    real = rows_mod.write_rows
    m.setattr(rows_mod, "write_rows", lambda rows, path: real(list(rows)[::-1], path))


def test_fake_smoke_rows_hash_identically_at_1_and_12_workers(tmp_path, monkeypatch):
    _smoke_pair(tmp_path, monkeypatch, FakePool)
    assert_same_rows(tmp_path / "w1", tmp_path / "w12", SMOKE_FILES)
    a = json.loads((tmp_path / "w1" / "smoke_summary.json").read_text())
    assert a["rows"] > 0 and a["rows_sha256"] == sha(tmp_path / "w12" / "smoke.csv")


def test_fake_sweep_family_rows_hash_identically_at_1_and_12_workers(tmp_path, monkeypatch):
    _sweep_pair(tmp_path, monkeypatch, FakePool)
    assert_same_rows(tmp_path / "w1", tmp_path / "w12", sweep_files(REAL_SWEEP_FAMILY))
    assert json.loads((tmp_path / "w1" / "sweep_summary.json").read_text())["families"][REAL_SWEEP_FAMILY]["rows"] > 0


def test_the_compared_files_include_the_summaries_not_only_the_csv():
    assert SMOKE_FILES == ("smoke.csv", "smoke_summary.json")
    assert sweep_files("damage_up") == ("sweep_damage_up.csv", "sweep_summary.json")


def test_the_fake_results_vary_by_cell_so_a_moved_row_would_show():
    """Positive control for the fixture: the stand-in fight does not return one value for everything."""
    w = world()
    a = w(fake_builds()("p", "play", {})(8, False), 0, False)
    b = w(fake_builds()("p", "play", {})(20, False), 0, False)
    c = w(fake_builds()("p", "play", {})(8, True), 1, True)
    assert len({(a.outcome, a.margin, a.heads), (b.outcome, b.margin, b.heads), (c.outcome, c.margin, c.heads)}) == 3


# ---- planted nondeterminism: the detector must fire --------------------------------------------------------------------------------------

def test_planted_completion_order_pool_is_caught_in_the_smoke_rows(tmp_path, monkeypatch):
    CompletionOrderPool.reordered = 0
    _smoke_pair(tmp_path, monkeypatch, CompletionOrderPool)
    assert CompletionOrderPool.reordered > 0          # the plant really reordered results
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", SMOKE_FILES)


def test_planted_completion_order_pool_is_caught_in_a_sweep_family(tmp_path, monkeypatch):
    CompletionOrderPool.reordered = 0
    _sweep_pair(tmp_path, monkeypatch, CompletionOrderPool)
    assert CompletionOrderPool.reordered > 0
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", sweep_files(REAL_SWEEP_FAMILY))


def _sorted_lines(path):
    return sorted(Path(path).read_text().splitlines())


def test_planted_row_permutation_is_caught_in_the_smoke_rows(tmp_path, monkeypatch):
    """The same rows in the reverse order: only the order differs, and the detector must still fire."""
    _smoke_pair(tmp_path, monkeypatch, FakePool, twelve_patch=reverse_row_order)
    assert _sorted_lines(tmp_path / "w1" / "smoke.csv") == _sorted_lines(tmp_path / "w12" / "smoke.csv")      # a pure permutation
    assert (tmp_path / "w1" / "smoke.csv").read_bytes() != (tmp_path / "w12" / "smoke.csv").read_bytes()
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", SMOKE_FILES)


def test_planted_row_permutation_is_caught_in_a_sweep_family(tmp_path, monkeypatch):
    _sweep_pair(tmp_path, monkeypatch, FakePool, twelve_patch=reverse_row_order)
    name = sweep_files(REAL_SWEEP_FAMILY)[0]
    assert _sorted_lines(tmp_path / "w1" / name) == _sorted_lines(tmp_path / "w12" / name)
    assert (tmp_path / "w1" / name).read_bytes() != (tmp_path / "w12" / name).read_bytes()
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", sweep_files(REAL_SWEEP_FAMILY))


def test_planted_worker_identity_in_the_results_is_caught_in_the_smoke_rows(tmp_path, monkeypatch):
    WorkerIdentityPool.leaked = 0
    _smoke_pair(tmp_path, monkeypatch, WorkerIdentityPool)
    assert WorkerIdentityPool.leaked > 0
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", SMOKE_FILES)


def test_planted_worker_identity_in_the_results_is_caught_in_a_sweep_family(tmp_path, monkeypatch):
    WorkerIdentityPool.leaked = 0
    _sweep_pair(tmp_path, monkeypatch, WorkerIdentityPool)
    assert WorkerIdentityPool.leaked > 0
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "w1", tmp_path / "w12", sweep_files(REAL_SWEEP_FAMILY))


def test_a_one_worker_run_that_went_through_a_pool_is_noticed(tmp_path, monkeypatch):
    """Control for the in-process check: a 1-worker run with a pool built (here forced by building one) trips _no_pool_yet."""
    _install(monkeypatch, FakePool)
    FakePool(1)
    with pytest.raises(AssertionError, match="built a pool"):
        _no_pool_yet()


def test_the_detector_reports_a_missing_file_and_passes_identical_directories(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "x.csv").write_text("1\n")
    (tmp_path / "b" / "x.csv").write_text("1\n")
    assert_same_rows(tmp_path / "a", tmp_path / "b", ("x.csv",))
    with pytest.raises(AssertionError):
        assert_same_rows(tmp_path / "a", tmp_path / "b", ("y.csv",))
    (tmp_path / "b" / "x.csv").write_text("2\n")
    with pytest.raises(AssertionError, match="differs between"):
        assert_same_rows(tmp_path / "a", tmp_path / "b", ("x.csv",))
