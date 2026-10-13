"""Process-pool runner for fights: plain data in (setup, seed, swap), FightResult out, one Engine per worker."""
from __future__ import annotations

import multiprocessing

from scripts.skilllab.contract import trim_series
from scripts.skilllab import engine as engine_module, fight as fight_module

_engine = None


_lean = False


def _init_worker(library_path, lean=False):
    """Pool initializer: load the library the parent built, so no worker compiles its own."""
    global _engine, _lean
    _lean = lean
    _engine = engine_module.Engine(library_path)


def run_job(job):
    global _engine
    if not isinstance(_engine, engine_module.Engine):
        _engine = engine_module.Engine()
    setup, seed, swap = job
    result = fight_module.fight(setup, seed, swap, _engine)
    # lean: drop the per-tick series here, so the parent never holds them; seed 0, unswapped is each cell's charted example
    return trim_series(result) if _lean and (seed != 0 or swap) else result


class FightPool:
    def __init__(self, workers: int, library_path=None, lean: bool = False):
        if workers < 1:
            raise ValueError("workers must be at least 1")
        self._workers = workers
        self._library_path = library_path
        self._lean = lean
        self._pool = None
        self._closed = False

    def map(self, jobs) -> list:
        if self._closed:
            raise RuntimeError("pool is closed")
        jobs = list(jobs)
        if self._workers == 1:
            return [run_job(job) for job in jobs]
        if self._pool is None:
            # spawn, never fork: a forked child would inherit the parent's loaded library and world state
            path = self._library_path if self._library_path is not None else engine_module._cached_library()
            self._pool = multiprocessing.get_context("spawn").Pool(
                self._workers, initializer=_init_worker, initargs=(path, True) if self._lean else (path,))
        return self._pool.map(run_job, jobs, chunksize=1)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._closed = True
        if self._pool is not None:
            self._pool.close()
            self._pool.join()
            self._pool = None
