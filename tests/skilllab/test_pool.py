# spec: docs/northstar/research/layer_dynamics/README.md::9 (process-pool runner, skill lab harness item 4)
"""Unit tests of scripts/skilllab/pool.py and the map_fn threading through scan and breakeven.

Fake fight functions and fake multiprocessing contexts only: no compiler, no library, no spawn.
Red until pool.py exists and scan/breakeven accept map_fn.
"""
import dataclasses
import multiprocessing
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight as fight_module, plays  # noqa: E402
from scripts.skilllab import engine as engine_module  # noqa: E402
from scripts.skilllab import pool  # noqa: E402
from scripts.skilllab.breakeven import find_break_even, swap_control  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.scan import cell, scan  # noqa: E402


def _result(margin):
    return FightResult(outcome="side0" if margin > 0 else "side1", margin=margin,
                       strength_left=(1.0, 0.0), survivors=(1, 0), heads=(1, 1), ticks=10,
                       first_contact_tick=0, firing=[(0, 1, 1)], firing_unit_seconds=(0.25, 0.25))


def _build(enemy_heads, swap):
    # Setup carries the build arguments so a fake can read them. One group, so flip_sides changes it.
    group = Group(side=0, unit="Vanguard", count=1, formation="blob", x=0.0, y=0.0, facing_deg=0.0,
                  layer=0, order="idle")
    return Setup(groups=(group,), unit_types={"enemy": enemy_heads, "swap": swap})


def _margin(setup, seed, swap):
    # Wins up to 3 enemies, loses beyond; seed noise keeps fights distinct. Flipped sides read as negated.
    enemy = setup.unit_types["enemy"]
    base = 0.5 if enemy <= 3 else -0.5
    sign = 1 if setup.groups[0].side == 0 else -1
    return sign * base + 0.01 * seed + (0.001 if swap else 0.0)


class Serial:
    """fight_fn that logs (setup, seed, swap)."""

    def __init__(self):
        self.jobs = []

    def __call__(self, setup, seed, swap):
        self.jobs.append((setup, seed, swap))
        return _result(_margin(setup, seed, swap))


class Batched:
    """map_fn that logs each batch it is handed and answers like Serial."""

    def __init__(self):
        self.batches = []

    def __call__(self, jobs):
        jobs = list(jobs)
        self.batches.append(jobs)
        return [_result(_margin(*job)) for job in jobs]

    @property
    def jobs(self):
        return [job for batch in self.batches for job in batch]


# ---- FightPool ----

def test_workers_below_one_raise_value_error():
    """Negative control: 0 and -1 workers are refused."""
    for bad in (0, -1):
        with pytest.raises(ValueError):
            pool.FightPool(bad)


class _FakePool:
    def __init__(self):
        self.map_calls, self.closed = [], False

    def map(self, fn, iterable, chunksize=None):
        self.map_calls.append((fn, list(iterable), chunksize))
        return [fn(j) for j in self.map_calls[-1][1]]

    def close(self):
        self.closed = True

    def terminate(self):
        self.closed = True

    def join(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class _FakeContext:
    def __init__(self):
        self.pools, self.pool_args = [], []

    def Pool(self, *args, **kwargs):
        self.pool_args.append((args, kwargs))
        p = _FakePool()
        self.pools.append(p)
        return p


@pytest.fixture
def stub_fight(monkeypatch):
    """Replace Engine and fight.fight so run_job needs no library; returns the call log."""
    log = []

    class StubEngine:
        made = 0

        def __init__(self):
            StubEngine.made += 1

    def fake_fight(setup, seed=0, swap=False, engine=None):
        log.append((setup, seed, swap, engine))
        return _result(_margin(setup, seed, swap))

    monkeypatch.setattr(engine_module, "Engine", StubEngine)
    monkeypatch.setattr(fight_module, "fight", fake_fight)
    return log, StubEngine


def test_multi_worker_pool_uses_spawn_context_chunksize_one(monkeypatch, stub_fight):
    """README 9: workers > 1 asks get_context for "spawn" (never fork) and maps with chunksize 1, in order."""
    asked, ctx = [], _FakeContext()
    monkeypatch.setattr(multiprocessing, "get_context",
                        lambda *a, **k: (asked.append((a, k)), ctx)[1])
    jobs = [(_build(e, False), 0, False) for e in (1, 2, 3)]
    with pool.FightPool(2) as fp:
        out = fp.map(jobs)
    assert asked and all((a == ("spawn",) and not k) or (not a and k == {"method": "spawn"}) for a, k in asked)
    assert ctx.pools, "a process pool was created"
    args, kwargs = ctx.pool_args[0]
    assert 2 in args or kwargs.get("processes") == 2
    fn, mapped, chunksize = ctx.pools[0].map_calls[0]
    assert fn is pool.run_job and mapped == jobs and chunksize == 1
    assert out == [_result(_margin(*j)) for j in jobs]
    assert ctx.pools[0].closed


def test_single_worker_never_touches_multiprocessing(monkeypatch, stub_fight):
    """README 9: workers == 1 is the serial reference, in the calling process, in order."""
    def boom(*a, **k):
        raise AssertionError("multiprocessing touched")
    monkeypatch.setattr(multiprocessing, "get_context", boom)
    monkeypatch.setattr(multiprocessing, "Pool", boom)
    log, _ = stub_fight
    jobs = [(_build(e, s), seed, s) for e in (1, 5) for s in (False, True) for seed in (0, 1)]
    with pool.FightPool(1) as fp:
        out = fp.map(jobs)
    assert [(c[0], c[1], c[2]) for c in log] == jobs
    assert out == [_result(_margin(*j)) for j in jobs]


def test_map_after_close_raises_runtime_error(stub_fight):
    """Exit closes the pool; a later map is refused."""
    with pool.FightPool(1) as fp:
        pass
    with pytest.raises(RuntimeError):
        fp.map([(_build(1, False), 0, False)])


def test_failing_job_exception_propagates(monkeypatch, stub_fight):
    """Negative control: a job that raises surfaces its exception from map (workers 1)."""
    def bad(setup, seed=0, swap=False, engine=None):
        raise KeyError("boom")
    monkeypatch.setattr(fight_module, "fight", bad)
    with pool.FightPool(1) as fp:
        with pytest.raises(KeyError):
            fp.map([(_build(1, False), 0, False)])


def test_run_job_creates_one_engine_lazily_and_reuses_it(stub_fight):
    """README 9: one Engine per worker process, created on first job, kept in a module global."""
    log, engine_cls = stub_fight
    before = engine_cls.made
    first = pool.run_job((_build(1, False), 0, False))
    pool.run_job((_build(2, True), 1, True))
    assert engine_cls.made - before <= 1
    assert log[-1][3] is log[-2][3] and isinstance(log[-1][3], engine_cls)
    assert first == _result(_margin(_build(1, False), 0, False))
    assert [(c[1], c[2]) for c in log[-2:]] == [(0, False), (1, True)]


def test_plain_data_pickles():
    """README 9: a Setup from blob_play and a FightResult survive a pickle round trip equal."""
    setup = plays.blob_play(4)(3, True)
    assert pickle.loads(pickle.dumps(setup)) == setup
    res = dataclasses.replace(_result(0.25), trace=[(0, 1, 1.0, 2.0, 3, 0.5, True)], steps_fired=((0, 5),))
    assert pickle.loads(pickle.dumps(res)) == res


def test_import_has_no_side_effects():
    """README 9: importing pool in a fresh interpreter builds no library and starts no process."""
    code = ("import multiprocessing\n"
            "import scripts.skilllab.pool\n"
            "from scripts.skilllab import engine\n"
            "assert engine._lib_cache is None\n"
            "assert multiprocessing.active_children() == []\n"
            "print('clean')\n")
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "clean"


# ---- map_fn threading ----

def test_cell_map_fn_jobs_match_serial_order_and_result():
    """Jobs the map_fn gets equal the serial (setup, seed, swap) sequence; one call; same CellResult."""
    ser, bat = Serial(), Batched()
    expected = cell(_build, 4, 3, fight_fn=ser)
    got = cell(_build, 4, 3, map_fn=bat)
    assert len(bat.batches) == 1
    assert bat.jobs == ser.jobs
    assert got == expected


def test_full_scan_map_fn_is_one_call_with_all_cells_in_serial_order():
    """The linear sweep hands the map_fn ONE batch of every cell's jobs, in the serial order; same ScanResult."""
    ser, bat = Serial(), Batched()
    expected = scan(_build, 4, 2, 5, replicates=2, fight_fn=ser, full_scan=True)
    got = scan(_build, 4, 2, 5, replicates=2, map_fn=bat, full_scan=True)
    assert len(bat.batches) == 1
    assert bat.jobs == ser.jobs
    assert len(bat.batches[0]) == 4 * 2 * 2
    assert got == expected


def test_bisection_map_fn_batches_the_coarse_pass_then_one_call_per_step_in_the_serial_order():
    """LAB-REV2-L4: the default scan bisects. Through map_fn the first call carries the coarse cells together (that is what
    keeps 12 workers busy), each later call is one bisection step, and the jobs and the ScanResult equal the serial run's."""
    ser, bat = Serial(), Batched()
    expected = scan(_build, 4, 2, 5, replicates=2, fight_fn=ser)
    got = scan(_build, 4, 2, 5, replicates=2, map_fn=bat)
    assert got == expected and (got.beats, got.loses_to) == (3, 4)
    assert bat.jobs == ser.jobs
    assert len(bat.batches) >= 2 and all(bat.batches)
    first_heads = {job[0].unit_types["enemy"] for job in bat.batches[0]}
    assert {2, 5} <= first_heads and len(bat.batches[0]) >= 2 * 2 * 2


def test_find_break_even_map_fn_one_call_for_scan_then_one_per_refinement_round():
    """Initial scan is one call; the one round that adds fights is one call; same job order and BreakEven."""
    ser, bat = Serial(), Batched()
    kw = dict(replicates=2, near_replicates=4, max_rounds=2)
    expected = find_break_even(_build, 4, 2, 5, fight_fn=ser, **kw)
    got = find_break_even(_build, 4, 2, 5, map_fn=bat, **kw)
    assert expected.refined, "the fake margins must produce a flip so refinement runs"
    assert expected.rounds == 1
    assert len(bat.batches) == 1 + 1
    assert len(bat.batches[0]) == 4 * 2 * 2
    heads = [job[0].unit_types["enemy"] for job in bat.batches[1]]
    assert heads == sorted(heads) and set(heads) == {3, 4}
    assert bat.jobs == ser.jobs
    assert got == expected


def _moving_margin(setup, seed, swap):
    # Cell 10 flips to a loss only once refined (seeds 2, 3), so the break-even moves and round 2 fires.
    enemy = setup.unit_types["enemy"]
    if enemy == 10:
        return 0.5 if seed < 2 else -0.5
    return 0.5 if enemy <= 9 else -0.5


def test_find_break_even_map_fn_two_adding_rounds_make_three_calls():
    """Calls = 1 + rounds that added jobs; each round's batch is its near cells in increasing headcount."""
    ser, bat = Serial(), Batched()
    kw = dict(replicates=2, near_replicates=4, max_rounds=2)
    old = globals()["_margin"]
    globals()["_margin"] = _moving_margin
    try:
        expected = find_break_even(_build, 4, 8, 13, fight_fn=ser, **kw)
        got = find_break_even(_build, 4, 8, 13, map_fn=bat, **kw)
    finally:
        globals()["_margin"] = old
    assert expected.rounds == 2
    assert len(bat.batches) == 3
    assert len(bat.batches[0]) == 6 * 2 * 2
    for batch, cells in zip(bat.batches[1:], ({10, 11}, {9})):
        heads = [job[0].unit_types["enemy"] for job in batch]
        assert heads == sorted(heads) and set(heads) == cells
        assert len(batch) == len(cells) * 4
    assert bat.jobs == ser.jobs
    assert got == expected


def test_find_break_even_map_fn_round_adding_nothing_makes_no_call():
    """near_replicates == replicates: refinement adds no fights, so only the scan call happens."""
    ser, bat = Serial(), Batched()
    kw = dict(replicates=2, near_replicates=2, max_rounds=2)
    expected = find_break_even(_build, 4, 2, 5, fight_fn=ser, **kw)
    got = find_break_even(_build, 4, 2, 5, map_fn=bat, **kw)
    assert len(bat.batches) == 1
    assert bat.jobs == ser.jobs
    assert got == expected


def test_swap_control_map_fn_normal_set_first_then_flipped():
    """Whether one combined call or two (flipped and unflipped), normal jobs precede flipped, as serial."""
    ser, bat = Serial(), Batched()
    expected = swap_control(_build, 4, 2, fight_fn=ser)
    got = swap_control(_build, 4, 2, map_fn=bat)
    assert len(bat.batches) in (1, 2)
    assert bat.jobs == ser.jobs
    assert got == expected


def test_fight_pool_one_map_equals_serial_scan(stub_fight):
    """FightPool(1).map as map_fn gives results identical to the serial fight_fn path."""
    ser = Serial()
    expected = scan(_build, 4, 2, 5, replicates=2, fight_fn=ser)
    with pool.FightPool(1) as fp:
        got = scan(_build, 4, 2, 5, replicates=2, map_fn=fp.map)
    assert got == expected


@pytest.mark.parametrize("call", [
    lambda f, m: cell(_build, 3, 2, fight_fn=f, map_fn=m),
    lambda f, m: scan(_build, 4, 2, 3, replicates=2, fight_fn=f, map_fn=m),
    lambda f, m: find_break_even(_build, 4, 2, 3, replicates=2, near_replicates=2, fight_fn=f, map_fn=m),
    lambda f, m: swap_control(_build, 3, 2, fight_fn=f, map_fn=m),
])
def test_fight_fn_and_map_fn_together_raise(call):
    """Negative control: passing both is a ValueError."""
    with pytest.raises(ValueError):
        call(Serial(), Batched())


@pytest.mark.parametrize("delta", [-1, 1])
def test_map_fn_wrong_result_count_raises(delta):
    """Negative control: a map_fn returning too few or too many results is a ValueError."""
    def bad(jobs):
        jobs = list(jobs)
        return [_result(0.5) for _ in range(len(jobs) + delta)]
    with pytest.raises(ValueError):
        cell(_build, 3, 2, map_fn=bad)
    with pytest.raises(ValueError):
        swap_control(_build, 3, 2, map_fn=bad)
    with pytest.raises(ValueError):
        scan(_build, 4, 2, 3, replicates=2, map_fn=bad)
