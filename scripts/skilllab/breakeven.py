"""Break-even by scan with refinement near every flip, and the side-swap control."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Optional

from scripts.skilllab.contract import BuildFn, CellResult, ScanResult, Setup
from scripts.skilllab.scan import cell_jobs, cell_result, read_cells, run_jobs, scan


@dataclass
class Flip:
    before: int
    after: int
    direction: str


@dataclass
class BreakEven:
    scan: ScanResult
    flips: list
    multi_flip: bool
    beats: Optional[int]
    loses_to: Optional[int]
    refined: list
    rounds: int
    ceiling_hit: bool = False


@dataclass
class SwapControl:
    enemy_heads: int
    margin: float
    margin_flipped: float
    bias: float


def _flips(cells: list) -> list:
    return [Flip(a.enemy_heads, b.enemy_heads, "win_to_loss" if a.won else "loss_to_win")
            for a, b in zip(cells, cells[1:]) if a.won != b.won]


def find_break_even(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
                    near_replicates: int = 30, max_rounds: int = 2,
                    fight_fn: Any = None, map_fn: Any = None) -> BreakEven:
    if near_replicates < replicates:
        raise ValueError("near_replicates must be at least replicates")
    if max_rounds < 0:
        raise ValueError("max_rounds must not be negative")
    if fight_fn is not None and map_fn is not None:
        raise ValueError("pass fight_fn or map_fn, not both")
    result = scan(build, size, enemy_from, enemy_to, replicates, fight_fn, map_fn, full_scan=True)  # the neighbours of every flip are needed
    cells = result.cells
    flips = _flips(cells)
    refined: set = set()
    rounds = 0
    while flips and rounds < max_rounds:
        rounds += 1
        before = [(f.before, f.after) for f in flips]
        near = {h for pair in before for h in pair} - refined
        if near_replicates > replicates:
            idx = [i for i, c in enumerate(cells) if c.enemy_heads in near]
            per_cell = [cell_jobs(build, cells[i].enemy_heads, replicates, near_replicates) for i in idx]
            if idx:
                results = run_jobs([j for jobs in per_cell for j in jobs], fight_fn, map_fn)
                pos = 0
                for i, jobs in zip(idx, per_cell):
                    cells[i] = cell_result(cells[i].enemy_heads, cells[i].fights + results[pos:pos + len(jobs)])
                    pos += len(jobs)
            refined |= near
        flips = _flips(cells)
        if [(f.before, f.after) for f in flips] == before:
            break
    beats, loses_to, ceiling_hit, multi_flip = read_cells(cells)
    final = dataclasses.replace(result, cells=cells, beats=beats, loses_to=loses_to, ceiling_hit=ceiling_hit,
                               multi_flip=multi_flip)
    return BreakEven(scan=final, flips=flips, multi_flip=multi_flip, beats=beats, loses_to=loses_to,
                     refined=sorted(refined), rounds=rounds, ceiling_hit=ceiling_hit)


def flip_sides(setup: Setup) -> Setup:
    return dataclasses.replace(
        setup, groups=tuple(dataclasses.replace(g, side=1 - g.side) for g in setup.groups))


def swap_control(build: BuildFn, enemy_heads: int, replicates: int, fight_fn: Any = None,
                 map_fn: Any = None) -> SwapControl:
    """Mean margin of the normal fights and of the same fights with sides flipped.

    Margins are signed side0 minus side1, so margin_flipped is not negated: a side-blind
    instrument gives margin_flipped == -margin and bias == 0. Numbers only, no pass mark.
    """
    jobs = [(transform(build(enemy_heads, swap)), seed, swap)
            for transform in (lambda s: s, flip_sides) for swap in (False, True)
            for seed in range(replicates)]
    margins = [r.margin for r in run_jobs(jobs, fight_fn, map_fn)]  # one combined call, normal set first
    normal, flipped = margins[:len(margins) // 2], margins[len(margins) // 2:]
    margin = sum(normal) / len(normal)
    margin_flipped = sum(flipped) / len(flipped)
    return SwapControl(enemy_heads=enemy_heads, margin=margin, margin_flipped=margin_flipped,
                       bias=margin + margin_flipped)
