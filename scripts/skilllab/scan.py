"""Cell and scan: fight both spawn orders over seeds, then sweep the enemy headcount."""
from __future__ import annotations

from typing import Any

from scripts.skilllab.contract import BuildFn, CellResult, ScanResult

COARSE_STEP = 8   # DRAFT-coarse-step (Westley's number): bisection scans these headcounts first, then halves the first won-to-lost bracket


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


def cell(build: BuildFn, enemy_heads: int, replicates: int, fight_fn: Any = None, map_fn: Any = None) -> CellResult:
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    fights = run_jobs(cell_jobs(build, enemy_heads, 0, replicates), fight_fn, map_fn)
    return cell_result(enemy_heads, fights)


def cell_jobs(build: BuildFn, enemy_heads: int, start: int, stop: int) -> list:
    return [(build(enemy_heads, swap), seed, swap) for swap in (False, True) for seed in range(start, stop)]


def cell_result(enemy_heads: int, fights: list) -> CellResult:
    """Won only when every fight is side0; a draw or a cap marks the cell a defect (Q-LAB-03)."""
    mean_margin = sum(f.margin for f in fights) / len(fights)
    return CellResult(enemy_heads=enemy_heads, fights=fights, mean_margin=mean_margin,
                      won=all(f.outcome == "side0" for f in fights),
                      defect=any(f.outcome in ("draw", "cap") for f in fights))


def pair_spread(c: CellResult) -> tuple:
    """Lowest and highest per-seed mean margin of the two side-swapped fights (fights[i] and fights[i + half])."""
    if len(c.fights) % 2:
        raise ValueError("a cell needs an even number of fights, got %d" % len(c.fights))
    half = len(c.fights) // 2
    pairs = [(c.fights[i].margin + c.fights[i + half].margin) / 2 for i in range(half)]
    return min(pairs), max(pairs)


def _crossing(cells: list) -> tuple:
    for prev, cur in zip(cells, cells[1:]):
        if prev.won and not cur.won:
            return prev.enemy_heads, cur.enemy_heads
    return None, None


def read_cells(cells: list) -> tuple:
    """(beats, loses_to, ceiling_hit, multi_flip) over the scanned cells in increasing enemy_heads."""
    beats, loses_to = _crossing(cells)
    flips = sum(a.won != b.won for a, b in zip(cells, cells[1:]))
    ceiling_hit = beats is None and bool(cells) and all(c.won for c in cells)
    if ceiling_hit:
        beats = cells[-1].enemy_heads
    return beats, loses_to, ceiling_hit, flips > 1


def _fight_cells(build: BuildFn, heads_list: list, replicates: int, fight_fn: Any, map_fn: Any) -> list:
    per_cell = [cell_jobs(build, heads, 0, replicates) for heads in heads_list]
    results = run_jobs([job for jobs in per_cell for job in jobs], fight_fn, map_fn)
    return [cell_result(heads, results[i * len(jobs):(i + 1) * len(jobs)])
            for i, (heads, jobs) in enumerate(zip(heads_list, per_cell))]


def _bisect(build: BuildFn, cells: dict, replicates: int, fight_fn: Any, map_fn: Any) -> None:
    """Halve the first won-to-lost bracket of the probed cells until its two headcounts are adjacent."""
    while True:
        ordered = [cells[h] for h in sorted(cells)]
        a, b = _crossing(ordered)
        if a is None or b - a <= 1:
            return
        mid = (a + b) // 2
        cells[mid] = _fight_cells(build, [mid], replicates, fight_fn, map_fn)[0]


def scan(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
         fight_fn: Any = None, map_fn: Any = None, refine_factor: int = 1, refine_band: int = 2,
         full_scan: bool = False) -> ScanResult:
    """Break-even over enemy_from..enemy_to. Default: a coarse pass every COARSE_STEP headcounts, then bisection of the
    first won-to-lost bracket. full_scan fights every headcount. Cells are returned in increasing enemy_heads."""
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    if refine_factor < 1:
        raise ValueError("refine_factor must be at least 1")
    if enemy_from > enemy_to:
        raise ValueError("enemy_from must not exceed enemy_to")
    if full_scan:
        first = list(range(enemy_from, enemy_to + 1))
    else:
        first = sorted(set(range(enemy_from, enemy_to + 1, COARSE_STEP)) | {enemy_to})
    cells = {c.enemy_heads: c for c in _fight_cells(build, first, replicates, fight_fn, map_fn)}
    if not full_scan:
        _bisect(build, cells, replicates, fight_fn, map_fn)
    beats, loses_to = _crossing([cells[h] for h in sorted(cells)])
    if refine_factor > 1 and beats is not None:
        total = replicates * refine_factor
        for heads in sorted(cells):
            if not beats - refine_band <= heads <= loses_to + refine_band:
                continue
            c = cells[heads]
            extra = run_jobs(cell_jobs(build, heads, replicates, total), fight_fn, map_fn)
            half, old_half = len(extra) // 2, len(c.fights) // 2
            cells[heads] = cell_result(heads, c.fights[:old_half] + extra[:half] + c.fights[old_half:] + extra[half:])
        if not full_scan:
            _bisect(build, cells, replicates, fight_fn, map_fn)
    ordered = [cells[h] for h in sorted(cells)]
    beats, loses_to, ceiling_hit, multi_flip = read_cells(ordered)
    return ScanResult(size=size, cells=ordered, beats=beats, loses_to=loses_to, ceiling_hit=ceiling_hit,
                      multi_flip=multi_flip)
