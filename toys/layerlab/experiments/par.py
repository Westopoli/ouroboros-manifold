"""Ad hoc process pool for the experiment scripts (the proper runner is layerlab/batch.py, SPEC 8).
Processes, never threads: ll_sim.c keeps a static error buffer. Each job is (scenario dict, seed); the worker
returns the small tuple (winner, survivors A, survivors B, ticks). Results come back in job order."""
import os
from concurrent.futures import ProcessPoolExecutor

def _one(job):
    from layerlab.run import run
    scn, seed = job
    try:
        r = run(scn, seed=seed)
    except (ValueError, RuntimeError):
        return None
    return (r.winner, r.survivors[0], r.survivors[1], r.ticks)

def pmap_runs(jobs, procs=None):
    procs = procs or max(1, min(8, (os.cpu_count() or 2) - 1))
    with ProcessPoolExecutor(max_workers=procs) as ex:
        return list(ex.map(_one, jobs, chunksize=max(1, len(jobs) // (procs * 8) or 1)))

def win_rates(scns, seeds=range(100), procs=None):
    """win rate of side A for each scenario in `scns`, over the same seeds; one pool for everything."""
    seeds = list(seeds)
    jobs = [(s, k) for s in scns for k in seeds]
    out = pmap_runs(jobs, procs)
    rates = []
    for i in range(len(scns)):
        chunk = [o for o in out[i * len(seeds):(i + 1) * len(seeds)] if o is not None]
        rates.append((sum(o[0] == 1 for o in chunk) / len(chunk), sum(o[1] for o in chunk) / len(chunk)) if chunk else (float("nan"), float("nan")))
    return rates
