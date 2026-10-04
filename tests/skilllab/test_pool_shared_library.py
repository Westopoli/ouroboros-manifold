# spec: parallel batches - FightPool builds the library once in the parent; workers load it via an initializer
"""FightPool(workers, library_path=None) and pool._init_worker. Fake contexts and fake Engine: no compiler, no spawn."""
import multiprocessing
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine as engine_module, fight as fight_module, pool  # noqa: E402

SENTINEL_PATH = Path("/nonexistent/libsentinel.so")


class _FakePool:
    def map(self, fn, iterable, chunksize=None):
        return [fn(j) for j in iterable]

    def close(self):
        pass

    def join(self):
        pass


class _FakeContext:
    def __init__(self):
        self.pool_args = []

    def Pool(self, *args, **kwargs):
        self.pool_args.append((args, kwargs))
        return _FakePool()


@pytest.fixture
def ctx(monkeypatch):
    c = _FakeContext()
    monkeypatch.setattr(multiprocessing, "get_context", lambda method=None: c)
    return c


@pytest.fixture
def built(monkeypatch):
    calls = []

    def fake_cached():
        calls.append(1)
        return SENTINEL_PATH

    monkeypatch.setattr(engine_module, "_cached_library", fake_cached)
    return calls


@pytest.fixture(autouse=True)
def fresh_engine(monkeypatch):
    monkeypatch.setattr(pool, "_engine", None, raising=False)


def _jobs(n=2):
    return [(object(), i, False) for i in range(n)]


@pytest.fixture
def stubs(monkeypatch):
    made, fights = [], []

    class RecEngine:
        def __init__(self, *args, **kwargs):
            made.append((args, kwargs))

    def fake_fight(setup, seed=0, swap=False, engine=None):
        fights.append(engine)
        return "r"

    monkeypatch.setattr(engine_module, "Engine", RecEngine)
    monkeypatch.setattr(fight_module, "fight", fake_fight)
    return made, fights


def test_multi_worker_uses_init_worker_with_library_path(ctx, built, stubs):
    with pool.FightPool(4) as fp:
        fp.map(_jobs())
    (args, kwargs), = ctx.pool_args
    assert (args[0] if args else kwargs.get("processes")) == 4
    assert kwargs["initializer"] is pool._init_worker
    assert tuple(kwargs["initargs"]) == (SENTINEL_PATH,)


def test_library_built_exactly_once_in_parent_for_many_workers(ctx, built, stubs):
    with pool.FightPool(4) as fp:
        fp.map(_jobs())
        fp.map(_jobs())
    assert len(built) == 1


def test_single_worker_builds_nothing_and_starts_nothing(ctx, built, stubs):
    with pool.FightPool(1) as fp:
        fp.map(_jobs())
    assert built == [] and ctx.pool_args == []


def test_explicit_library_path_is_used_and_nothing_built(ctx, built, stubs):
    explicit = Path("/nonexistent/explicit.so")
    with pool.FightPool(2, library_path=explicit) as fp:
        fp.map(_jobs())
    assert built == []
    (_, kwargs), = ctx.pool_args
    assert kwargs["initializer"] is pool._init_worker
    assert tuple(kwargs["initargs"]) == (explicit,)


def test_init_worker_makes_one_engine_from_path_and_run_job_reuses_it(stubs):
    made, fights = stubs
    pool._init_worker(SENTINEL_PATH)
    assert made == [((SENTINEL_PATH,), {})]
    pool.run_job((object(), 0, False))
    pool.run_job((object(), 1, False))
    assert len(made) == 1
    assert len(fights) == 2 and fights[0] is fights[1] and fights[0] is pool._engine


def test_run_job_without_initializer_builds_lazily_once(stubs):
    made, fights = stubs
    assert pool._engine is None
    pool.run_job((object(), 0, False))
    pool.run_job((object(), 1, False))
    assert made == [((), {})]
    assert fights[0] is fights[1]
