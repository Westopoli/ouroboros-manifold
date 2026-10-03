"""Evidence for the condition checker: pass marks (all Westley's, all required inputs), verdicts, fight points.
Every statistic here is the harness writer's unconfirmed definition, not a ruling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Thresholds:
    c0_tolerance_units: int
    c1_min_firing_advantage: float
    c1_map_share: float
    c2_rank_agreement: float
    c2_off_trend_margin: float
    c2_off_trend_share: float
    c3_stack_gain: float
    c4_max_share: float
    c5_min_loss: float
    c6_return_share: float
    c6_map_share: float
    c8_map_share: float
    c7_ceiling_targets: tuple
    c9_length_bounds_ticks: tuple
    guard_tolerance_units: int


@dataclass(frozen=True)
class Verdict:
    code: str
    holds: Optional[bool]   # None = reported, not judged
    value: object
    threshold: object
    detail: str


@dataclass(frozen=True)
class FightPoint:
    firing_adv: float
    margin: float
    ticks: int


def firing_advantage(result) -> float:
    f0, f1 = result.firing_unit_seconds
    return (f0 - f1) / (f0 + f1) if f0 + f1 else 0.0


def points(scan_result, heads=None) -> list:
    return [FightPoint(firing_advantage(f), f.margin, f.ticks)
            for c in scan_result.cells if heads is None or c.enemy_heads == heads for f in c.fights]
