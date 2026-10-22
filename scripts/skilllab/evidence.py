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


BASES = ("whole", "window")
DEFAULT_BASIS = "window"
AGREEMENTS = ("both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a")


def check_basis(basis) -> str:
    if basis not in BASES:
        raise ValueError("unknown basis %r: one of %s" % (basis, ", ".join(BASES)))
    return basis


def firing_advantage(result, basis=DEFAULT_BASIS) -> float:
    f0, f1 = result.firing_window if check_basis(basis) == "window" else result.firing_unit_seconds
    return (f0 - f1) / (f0 + f1) if f0 + f1 else 0.0


def points(scan_result, heads=None, basis=DEFAULT_BASIS) -> list:
    return [FightPoint(firing_advantage(f, basis), f.margin, f.ticks)
            for c in scan_result.cells if heads is None or c.enemy_heads == heads for f in c.fights]


def agreement_counts(agreements) -> dict:
    out = dict.fromkeys(AGREEMENTS, 0)
    for a in agreements:
        if a not in out:
            raise ValueError("unknown agreement word %r: one of %s" % (a, ", ".join(AGREEMENTS)))
        out[a] += 1
    return out


def agreement_word(outcome, predicted_count, predicted_type) -> str:
    """The agreement of fight._agreement (See also: scripts/skilllab/fight.py), for rows that carry the totals and not the words."""
    if outcome not in ("side0", "side1") or "tie" in (predicted_count, predicted_type):
        return "n/a"
    count_ok, type_ok = predicted_count == outcome, predicted_type == outcome
    if count_ok and type_ok:
        return "both_right"
    if type_ok:
        return "count_wrong_type_right"
    return "count_right_type_wrong" if count_ok else "both_wrong"


def _larger(pair) -> str:
    return "tie" if pair[0] == pair[1] else "side0" if pair[0] > pair[1] else "side1"


def row_agreement(row, basis=DEFAULT_BASIS) -> str:
    """A CSV row's agreement word on a basis. window: the row's own column. whole (decision 35 item 2): the count is the larger side of
    firing_unit_seconds, the type the larger side of weighted_unit_seconds, the outcome as the row has it."""
    if check_basis(basis) == "window":
        return row["agreement"]
    return agreement_word(row["outcome"], _larger((row["firing_unit_seconds_0"], row["firing_unit_seconds_1"])),
                          _larger((row["weighted_unit_seconds_0"], row["weighted_unit_seconds_1"])))
