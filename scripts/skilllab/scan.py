"""Cell and scan: fight both spawn orders over seeds, then sweep the enemy headcount."""
from __future__ import annotations

from typing import Any

from scripts.skilllab.contract import BuildFn, CellResult, ScanResult


def run_jobs(jobs: list, fight_fn: Any = None, map_fn: Any = None) -> list:
    """Fight each (setup, seed, swap) job in order: one fight_fn call per job, or one map_fn call for all."""
    if fight_fn is not None and map_fn is not None:
        raise ValueError("pass fight_fn or map_fn, not both")
    if map_fn is not None:
        results = list(map_fn(jobs))
        if len(results) != len(jobs):
            raise ValueError("map_fn returned %d results for %d jobs" % (len(results), len(jobs)))
        return results
    if fight_fn is None:
        from scripts.skilllab import fight as fight_module
        fight_fn = fight_module.fight
    return [fight_fn(*job) for job in jobs]


COARSE_STEP = 8


def cell(build: BuildFn, enemy_heads: int, replicates: int, fight_fn: Any = None, map_fn: Any = None) -> CellResult:
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    fights = run_jobs(cell_jobs(build, enemy_heads, 0, replicates), fight_fn, map_fn)
    return cell_result(enemy_heads, fights)


def cell_jobs(build: BuildFn, enemy_heads: int, start: int, stop: int) -> list:
    return [(build(enemy_heads, swap), seed, swap) for swap in (False, True) for seed in range(start, stop)]


def cell_result(enemy_heads: int, fights: list) -> CellResult:
    mean_margin = sum(f.margin for f in fights) / len(fights)
    defect = any(f.outcome in ("draw", "cap") for f in fights)
    return CellResult(enemy_heads=enemy_heads, fights=fights, mean_margin=mean_margin,
                      won=all(f.outcome == "side0" for f in fights), defect=defect)


def pair_spread(c: CellResult) -> tuple:
    """Lowest and highest per-seed mean margin of the two side-swapped fights (fights[i] and fights[i + half])."""
    if len(c.fights) % 2:
        raise ValueError("a cell needs an even number of fights, got %d" % len(c.fights))
    half = len(c.fights) // 2
    pairs = [(c.fights[i].margin + c.fights[i + half].margin) / 2 for i in range(half)]
    return min(pairs), max(pairs)


def _changes(cells: list) -> list:
    return [(a.enemy_heads, b.enemy_heads) for a, b in zip(cells, cells[1:]) if a.won != b.won]


def _crossing(cells: list) -> tuple:
    for prev, cur in zip(cells, cells[1:]):
        if prev.won and not cur.won:
            return prev.enemy_heads, cur.enemy_heads
    return None, None


def scan(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
         fight_fn: Any = None, map_fn: Any = None, refine_factor: int = 1, refine_band: int = 2,
         full_scan: bool = False) -> ScanResult:
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    if refine_factor < 1:
        raise ValueError("refine_factor must be at least 1")
    if enemy_from > enemy_to:
        raise ValueError("enemy_from must not exceed enemy_to")
    if fight_fn is not None and map_fn is not None:
        raise ValueError("pass fight_fn or map_fn, not both")
    done = {}

    def probe(heads_list):
        todo = [h for h in heads_list if h not in done]
        per_cell = [cell_jobs(build, h, 0, replicates) for h in todo]
        results = run_jobs([j for jobs in per_cell for j in jobs], fight_fn, map_fn)
        for i, (h, jobs) in enumerate(zip(todo, per_cell)):
            done[h] = cell_result(h, results[i * len(jobs):(i + 1) * len(jobs)])

    if full_scan:
        probe(range(enemy_from, enemy_to + 1))
    else:
        probe(sorted({enemy_from, enemy_to} | set(range(enemy_from, enemy_to + 1, COARSE_STEP))))
        ordered = [done[h] for h in sorted(done)]
        lo, hi = _crossing(ordered)
        while lo is not None and hi - lo > 1:
            mid = (lo + hi) // 2
            probe([mid])
            lo, hi = (mid, hi) if done[mid].won else (lo, mid)
    cells = [done[h] for h in sorted(done)]
    beats, loses_to = _crossing(cells)
    if refine_factor > 1 and beats is not None:
        total = replicates * refine_factor
        for i, c in enumerate(cells):
            if not beats - refine_band <= c.enemy_heads <= loses_to + refine_band:
                continue
            extra = run_jobs(cell_jobs(build, c.enemy_heads, replicates, total), fight_fn, map_fn)
            half, old_half = len(extra) // 2, len(c.fights) // 2
            cells[i] = cell_result(c.enemy_heads, c.fights[:old_half] + extra[:half] + c.fights[old_half:] + extra[half:])
        beats, loses_to = _crossing(cells)
    ceiling = all(c.won for c in cells)
    if ceiling:
        beats = cells[-1].enemy_heads
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=loses_to, ceiling_hit=ceiling,
                      multi_flip=len(_changes(cells)) > 1)
