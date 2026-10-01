"""The light fight runner (SPEC.md sections 14.1 and 14.5): no trace, deterministic result fields only."""
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from ..run import run
from .cost import side_units
from .margin import effective_margin, margin


@dataclass
class FightResult:
    margin: float
    raw_margin: float
    outcome: str
    ticks: int
    first_contact_tick: int
    contact: bool
    survivors: tuple
    alive_ticks: tuple
    firing_ticks: tuple
    heads: tuple
    error: str = None

    def firing_per_head(self, label):
        return self.firing_ticks[label] / self.heads[label] if self.heads[label] else 0.0


def fight(scn, seed=0, lib="O2"):
    res = run(scn, seed=seed, trace=False, lib=lib)
    m, outcome = effective_margin(res, scn)
    sides = [u["side"] for u in side_units(scn)]
    return FightResult(
        margin=m, raw_margin=margin(res, scn), outcome=outcome, ticks=res.ticks,
        first_contact_tick=res.first_contact_tick, contact=res.first_contact_tick >= 0,
        survivors=tuple(res.survivors), alive_ticks=tuple(res.alive_ticks),
        firing_ticks=tuple(res.firing_ticks), heads=(sides.count(0), sides.count(1)),
    )


def _work(job):
    scn, seed, lib = job
    try:
        return fight(scn, seed, lib)
    except ValueError as e:
        return FightResult(margin=0.0, raw_margin=0.0, outcome="error", ticks=0, first_contact_tick=-1,
                           contact=False, survivors=(), alive_ticks=(0, 0), firing_ticks=(0, 0), heads=(0, 0),
                           error=str(e))


def run_fights(jobs, processes=None, lib="O2"):
    work = [(scn, seed, lib) for scn, seed in jobs]
    if not processes or processes <= 1 or len(work) <= 1:
        return [_work(w) for w in work]
    with ProcessPoolExecutor(max_workers=processes) as pool:
        return list(pool.map(_work, work, chunksize=max(1, len(work) // (processes * 4))))


def measure_rate(scn, seeds, processes, lib):
    jobs = [(scn, s) for s in seeds]
    t0 = time.perf_counter()
    run_fights(jobs, processes=processes, lib=lib)
    seconds = time.perf_counter() - t0
    return {"fights": len(jobs), "seconds": seconds, "fights_per_second": len(jobs) / seconds}
