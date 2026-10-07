"""Locked contract of the skill lab harness (spec: docs/northstar/plans/skilllab-harness-spec.md).

Dataclasses carry data between modules. The `def` stubs below are the cross-module call
signatures; each is implemented in the module named in its comment, and every body here is a
sentinel. Callers import the real function from its own module, never from this file.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class Group:
    side: int                 # 0 or 1
    unit: str                 # a built-in type name or a key of Setup.unit_types
    count: int
    formation: str            # "line" | "blob" | "concave" | "column" | "points"
    x: float
    y: float                  # anchor
    facing_deg: float
    layer: int                # as the engine numbers layers
    order: str                # "attack_move" | "move" | "group_move" | "idle" | "guard"
    goal: Optional[tuple] = None
    params: dict = field(default_factory=dict)   # spacing, cols, arc_deg, radius, points


@dataclass(frozen=True)
class Step:
    group: int                # index into Setup.groups
    when: tuple               # ("tick", n) | ("arrive", radius) | ("seen",)
    order: str                # "attack_move" | "move" | "group_move" | "idle" | "guard" (idle clears the group's orders; guard holds and fires in range)
    goal: Optional[tuple] = None   # None means the first anchor of the other side, as for Group.goal; ignored for idle and guard
    layer: Optional[int] = None    # ping and set_layer: the layer
    on: Optional[bool] = None      # set_emission: the flag
    casters: str = "all"           # ping: every living unit pings once

    @classmethod
    def ping(cls, layer, x, y, casters="all", when=("tick", 0)):
        """Every living unit pings (x, y) on `layer`; group is 0 (no group name exists), only the 'all' casters are built."""
        if casters != "all":
            raise ValueError("ping casters must be 'all', got %r" % (casters,))
        return cls(0, when, "ping", (x, y), layer=layer, casters=casters)

    @classmethod
    def set_layer(cls, group, layer, when=("tick", 0)):
        return cls(group, when, "set_layer", layer=layer)

    @classmethod
    def set_emission(cls, group, on, when=("tick", 0)):
        return cls(group, when, "set_emission", on=bool(on))


@dataclass(frozen=True)
class Block:
    x0: float
    y0: float
    x1: float
    y1: float
    layer_lo: int = 0
    layer_hi: int = 4


@dataclass(frozen=True)
class Cover:
    x: float
    y: float
    radius: float
    height: int               # in layers, 0..5


@dataclass(frozen=True)
class Terrain:
    canvas: tuple             # (width, height)
    blocks: tuple = ()
    covers: tuple = ()
    field_seed: int = None    # set: the fight generates the ground field of this seed (era kind 1)


@dataclass(frozen=True)
class Setup:
    groups: tuple
    unit_types: dict          # name -> stats; see spec AC 5 (full stats, or base + scale/set)
    abilities: bool = False   # False calls om_tactical_disable_abilities
    max_ticks: int = 12000
    stalemate_ticks: int = 400
    sample_every: int = 5     # ticks between firing-count samples
    trace: bool = False       # True records FightResult.trace
    settings: dict = field(default_factory=dict)   # OM_TP_* name -> number, set on the world before tick 1
    timeline: tuple = ()      # Steps issuing later orders; listed order matters
    terrain: Optional[Terrain] = None   # canvas, blocked rectangles and cover, applied before any unit exists
    weighted: bool = False    # True records FightResult.weighted
    states: bool = False      # True records FightResult.states and .order_ends
    target_policy: Optional[tuple] = None   # (side 0, side 1), each None, 0 nearest or 1 most damaged; None sets nothing (A196)
    approach: float = 0.0     # stop factor of the hold-to-contact opening (approach.py); 0.0 = off
    mopup: bool = False       # lab rule, provisional (A199): re-issue a stopped side's attack-move at the enemies it sees (mopup.py)
    start_distance: Optional[float] = None   # anchor distance between the sides, set by the objective scene; None = the plays' own contact distance
    objective: Optional[tuple] = None        # (x, y) both groups attack-move to; None = no objective
    quiet_from_first_damage: bool = False   # True counts stalemate_ticks from the first hp change, not tick 0 (objective scene)
    mopup_interval_ticks: int = 200   # a side's mop-up is considered at multiples of this many ticks, so no more often
    decided_by_survivors: bool = False   # True: after first damage 400 blind ticks end the fight "decided" (winner by hp); stalemate_ticks and mop-up are not used
    silence_ticks: int = 0    # decided_by_survivors: after first damage this many ticks with no hp change end the fight "decided" (winner by hp); 0 = off
    hold_ticks: int = 1200    # decided_by_survivors with hold_anchor: from first damage this long, then the hold rule applies (draft, Westley's number)
    defender_side: int = 0    # the side whose units must stand at hold_anchor
    hold_anchor: Optional[tuple] = None   # (x, y); None = no hold rule. Half the defender's living units within 300 wu and no attacker ends the fight "held", defender the winner


@dataclass
class FightResult:
    outcome: str              # "side0" | "side1" | "draw" (both sides die on one tick) | "stalemate" (stalemate_ticks quiet) | "cap" (A201) | "decided" | "held" (decided_by_survivors)
    margin: float
    strength_left: tuple
    survivors: tuple
    heads: tuple
    ticks: int
    first_contact_tick: int
    firing: list              # [(tick, able0, able1), ...]
    firing_unit_seconds: tuple
    winner: Optional[str] = None   # "side0" | "side1" | "draw" for a decided fight (hp sums, within 5% is a draw), the defender's side for a held one, else None
    trace: Optional[list] = None   # [(tick, unit, x, y, target, facing, alive), ...] when Setup.trace, else None
    steps_fired: tuple = ()   # ((step_index, tick), ...) in firing order
    weighted: Optional[list] = None   # [(tick, w0, w1), ...] when Setup.weighted, else None
    weighted_unit_seconds: Optional[tuple] = None   # as firing_unit_seconds, over the weighted series
    states: Optional[list] = None   # [(tick, unit, state), ...] per living unit when Setup.states, else None
    order_ends: Optional[tuple] = None   # ((unit, tick), ...) first tick each unit's destination ended, by unit id
    mopup_orders: Optional[int] = None   # mop-up attack-moves issued by both sides in this fight; None when Setup.mopup is off


def trim_series(result: "FightResult") -> "FightResult":
    """The result without its per-tick series; row values stay. A series that was on becomes [] so 'was recorded' still reads."""
    return dataclasses.replace(result, firing=[], trace=None if result.trace is None else [],
                               weighted=None if result.weighted is None else [],
                               states=None if result.states is None else [])


@dataclass
class CellResult:
    enemy_heads: int
    fights: list              # [FightResult, ...]
    mean_margin: float
    won: bool


@dataclass
class ScanResult:
    size: int
    cells: list               # [CellResult, ...] in increasing enemy_heads
    beats: Optional[int]
    loses_to: Optional[int]
    win_margin: float


@dataclass
class Batch:
    title: str
    scans: dict               # label -> ScanResult
    firing_example: dict      # label -> FightResult whose firing series is charted
    rows: list                # [dict, ...] one per fight, from fight_row


WIN_MARGIN = 0.05
TICKS_PER_SECOND = 20
DRAW_BAND = 0.05              # decided fights: hp sums within this share of the larger are a draw
SILENCE_TICKS = 1200          # placed scenes set Setup.silence_ticks to this: no hp change for this long after first damage ends the fight "decided" (ruled 2026-10-07)
REISSUE_TICKS = 200           # decided_by_survivors with hold_anchor: every group of either side with an enemy in sight and no target attack-moves at the anchor this often (ruled 2026-10-07)
BLIND_TICKS = 400             # decided_by_survivors: ticks without sight, after first damage, that decide the fight
HOLD_RADIUS = 300.0           # wu from hold_anchor
SHIFT_MAX = 10.0              # replicate position shift, per axis, world units
BuildFn = Callable[[int, bool], "Setup"]


# engine.py
def build_library(scratch_dir: Any = None) -> Any:
    raise NotImplementedError


class Engine:
    """The ctypes wrapper of the production library; methods are listed in spec AC 3."""


# formations.py
def place(kind: str, n: int, x: float, y: float, facing_deg: float, params: dict) -> list:
    raise NotImplementedError


# firing.py
def count_able(engine: Any, w: Any, units0: list, units1: list, ranges: dict) -> tuple:
    raise NotImplementedError


# fight.py
def fight(setup: Setup, seed: int = 0, swap: bool = False, engine: Any = None) -> FightResult:
    raise NotImplementedError


# plays.py
def blob_play(size: int, unit: str = "Vanguard") -> BuildFn:
    raise NotImplementedError


def line_play(size: int, unit: str = "Vanguard") -> BuildFn:
    raise NotImplementedError


def reach_play(size: int, unit: str = "Vanguard", factor: float = 1.2) -> BuildFn:
    raise NotImplementedError


def damage_play(size: int, unit: str = "Vanguard", factor: float = 1.2) -> BuildFn:
    raise NotImplementedError


def unit_stats(name: str) -> dict:
    raise NotImplementedError


# scan.py
def cell(build: BuildFn, enemy_heads: int, replicates: int,
         win_margin: float = WIN_MARGIN, fight_fn: Any = None) -> CellResult:
    raise NotImplementedError


def scan(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
         win_margin: float = WIN_MARGIN, fight_fn: Any = None) -> ScanResult:
    raise NotImplementedError


# sample.py
def grid(dims: Any, per_dim: Any) -> list:
    raise NotImplementedError


def random_samples(dims: Any, n: int, seed: int = 0) -> list:
    raise NotImplementedError


# rows.py
def fight_row(result: FightResult, **labels: Any) -> dict:
    raise NotImplementedError


def write_rows(rows: list, path: Any) -> None:
    raise NotImplementedError


# report.py
def report(batch: Batch, out_dir: Any) -> str:
    raise NotImplementedError


# __main__.py
def main(argv: Optional[list] = None) -> int:
    raise NotImplementedError
