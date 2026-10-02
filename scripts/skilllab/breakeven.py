"""Break-even by scan with refinement near every flip, and the side-swap control."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Optional

from scripts.skilllab.contract import BuildFn, CellResult, ScanResult, Setup, WIN_MARGIN
from scripts.skilllab.scan import scan


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


@dataclass
class SwapControl:
    enemy_heads: int
    margin: float
    margin_flipped: float
    bias: float


def _resolve(fight_fn: Any) -> Any:
    if fight_fn is None:
        from scripts.skilllab import fight as fight_module
        return fight_module.fight
    return fight_fn


def _flips(cells: list) -> list:
    return [Flip(a.enemy_heads, b.enemy_heads, "win_to_loss" if a.won else "loss_to_win")
            for a, b in zip(cells, cells[1:]) if a.won != b.won]


def _extend(cell: CellResult, build: BuildFn, start: int, stop: int, win_margin: float,
            fight_fn: Any) -> CellResult:
    new = [fight_fn(build(cell.enemy_heads, swap), seed, swap)
           for swap in (False, True) for seed in range(start, stop)]
    fights = cell.fights + new
    mean_margin = sum(f.margin for f in fights) / len(fights)
    decided = all(f.outcome not in ("stalemate", "cap") for f in fights)
    return CellResult(enemy_heads=cell.enemy_heads, fights=fights, mean_margin=mean_margin,
                      won=mean_margin > win_margin and decided)


def find_break_even(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
                    near_replicates: int = 30, max_rounds: int = 2, win_margin: float = WIN_MARGIN,
                    fight_fn: Any = None) -> BreakEven:
    if near_replicates < replicates:
        raise ValueError("near_replicates must be at least replicates")
    if max_rounds < 0:
        raise ValueError("max_rounds must not be negative")
    fight_fn = _resolve(fight_fn)
    result = scan(build, size, enemy_from, enemy_to, replicates, win_margin, fight_fn)
    cells = result.cells
    flips = _flips(cells)
    refined: set = set()
    rounds = 0
    while flips and rounds < max_rounds:
        rounds += 1
        before = [(f.before, f.after) for f in flips]
        near = {h for pair in before for h in pair} - refined
        if near_replicates > replicates:
            for i, c in enumerate(cells):
                if c.enemy_heads in near:
                    cells[i] = _extend(c, build, replicates, near_replicates, win_margin, fight_fn)
            refined |= near
        flips = _flips(cells)
        if [(f.before, f.after) for f in flips] == before:
            break
    first = next((f for f in flips if f.direction == "win_to_loss"), None)
    beats = first.before if first else None
    loses_to = first.after if first else None
    final = dataclasses.replace(result, cells=cells, beats=beats, loses_to=loses_to)
    return BreakEven(scan=final, flips=flips, multi_flip=len(flips) > 1, beats=beats,
                     loses_to=loses_to, refined=sorted(refined), rounds=rounds)


def flip_sides(setup: Setup) -> Setup:
    return dataclasses.replace(
        setup, groups=tuple(dataclasses.replace(g, side=1 - g.side) for g in setup.groups))


def swap_control(build: BuildFn, enemy_heads: int, replicates: int, fight_fn: Any = None) -> SwapControl:
    """Mean margin of the normal fights and of the same fights with sides flipped.

    Margins are signed side0 minus side1, so margin_flipped is not negated: a side-blind
    instrument gives margin_flipped == -margin and bias == 0. Numbers only, no pass mark.
    """
    fight_fn = _resolve(fight_fn)
    normal, flipped = [], []
    for transform, out in ((lambda s: s, normal), (flip_sides, flipped)):
        for swap in (False, True):
            for seed in range(replicates):
                out.append(fight_fn(transform(build(enemy_heads, swap)), seed, swap).margin)
    margin = sum(normal) / len(normal)
    margin_flipped = sum(flipped) / len(flipped)
    return SwapControl(enemy_heads=enemy_heads, margin=margin, margin_flipped=margin_flipped,
                       bias=margin + margin_flipped)
