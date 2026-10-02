"""Cell and scan: fight both spawn orders over seeds, then sweep the enemy headcount."""
from __future__ import annotations

from typing import Any

from scripts.skilllab.contract import BuildFn, CellResult, ScanResult, WIN_MARGIN


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


def cell(build: BuildFn, enemy_heads: int, replicates: int,
         win_margin: float = WIN_MARGIN, fight_fn: Any = None, map_fn: Any = None) -> CellResult:
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    fights = run_jobs([(build(enemy_heads, swap), seed, swap)
                       for swap in (False, True) for seed in range(replicates)], fight_fn, map_fn)
    mean_margin = sum(f.margin for f in fights) / len(fights)
    decided = all(f.outcome not in ("stalemate", "cap") for f in fights)
    return CellResult(enemy_heads=enemy_heads, fights=fights, mean_margin=mean_margin,
                      won=mean_margin > win_margin and decided)


def scan(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
         win_margin: float = WIN_MARGIN, fight_fn: Any = None, map_fn: Any = None) -> ScanResult:
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    if enemy_from > enemy_to:
        raise ValueError("enemy_from must not exceed enemy_to")
    cells = [cell(build, heads, replicates, win_margin, fight_fn, map_fn)
             for heads in range(enemy_from, enemy_to + 1)]
    beats = loses_to = None
    for prev, cur in zip(cells, cells[1:]):
        if prev.won and not cur.won:
            beats, loses_to = prev.enemy_heads, cur.enemy_heads
            break
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=loses_to, win_margin=win_margin)
