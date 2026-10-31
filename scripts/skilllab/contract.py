"""Locked contract of the skill lab harness (spec: docs/northstar/plans/skilllab-harness-spec.md).

Dataclasses carry data between modules. The `def` stubs below are the cross-module call
signatures; each is implemented in the module named in its comment, and every body here is a
sentinel. Callers import the real function from its own module, never from this file.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

FROZEN_NAMES = ("inert_knob", "category", "survey", "checked", "seeds", "probed")      # names other code and the artifact match on; adding is fine, renaming or removing is a contract change


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
    max_ticks: int = 12000    # the cap: a bug detector only, a capped fight is a lab defect to trace (Q-LAB-03)
    sample_every: int = 5     # ticks between firing-count samples
    trace: bool = False       # True records FightResult.trace
    settings: dict = field(default_factory=dict)   # OM_TP_* name -> number, set on the world before tick 1
    timeline: tuple = ()      # Steps issuing later orders; listed order matters
    terrain: Optional[Terrain] = None   # canvas, blocked rectangles and cover, applied before any unit exists
    states: bool = False      # True records FightResult.states
    target_policy: Optional[tuple] = None   # (side 0, side 1), each None, 0 nearest or 1 most damaged; None sets nothing (A196)
    point: Optional[tuple] = None   # (x, y) the shared attack-move point; None: each group aims at the first anchor of the other side
    orders_per_unit: bool = True    # one order_attack_move call per unit at the opening; later timeline steps stay group-level (a flip of the default is conditional, decision 43 item 1)
    firing_arc_deg: float = 360.0   # set on the world through OM_TP_FIRING_ARC_DEG when below 360 and the library has the parameter
    cone: dict = field(default_factory=dict)   # type name -> (range, half-angle degrees, share), applied through Engine.set_cone


@dataclass
class FightResult:
    outcome: str              # "side0" | "side1" | "draw" (both sides die on one tick) | "cap" (max_ticks reached: a lab defect, never a result)
    margin: float
    strength_left: tuple
    survivors: tuple
    heads: tuple
    ticks: int
    first_contact_tick: int   # first sampled tick at which any unit's can_engage reads 0, -1 if none
    firing: list              # [(tick, able0, able1), ...]
    firing_unit_seconds: tuple
    winner: Optional[str] = None   # the surviving side ("side0" | "side1"); None for draw and cap
    trace: Optional[list] = None   # [(tick, unit, x, y, target, facing, alive, layer, unit_type), ...] when Setup.trace, else None
    steps_fired: tuple = ()   # ((step_index, tick), ...) in firing order
    weighted_unit_seconds: tuple = (0.0, 0.0)   # the type-weighted count, whole fight
    states: Optional[list] = field(default_factory=list)   # [(tick, unit, code), ...] at sample ticks when Setup.states, [] when off
    firing_window: tuple = (0.0, 0.0)       # unit-seconds over [first_contact_tick, first_contact_tick + OPENING_WINDOW_TICKS)
    weighted_window: tuple = (0.0, 0.0)
    predicted_count: str = "tie"            # "side0" | "side1" | "tie": the larger window total
    predicted_type: str = "tie"
    agreement: str = "n/a"    # "both_right" | "count_wrong_type_right" | "both_wrong" | "count_right_type_wrong" | "n/a"
    reengage: tuple = (0, 0)  # (side 0, side 1) re-engage events: a silent side with an idle attack-move unit and a visible enemy was ordered onto the enemy centroid
    blind_cap: bool = False   # outcome "cap" and, at the cap tick, neither side sees any living enemy: a finding (blind post), not a lab cap defect
    living: tuple = ({}, {})  # ({side 0 Group.unit: count}, {side 1 Group.unit: count}) alive at the end of the fight, zero counts omitted


def trim_series(result: "FightResult") -> "FightResult":
    """The result without its per-tick series; row values stay. A series that was on becomes [] so 'was recorded' still reads."""
    return dataclasses.replace(result, firing=[], trace=None if result.trace is None else [],
                               states=[])


@dataclass
class CellResult:
    enemy_heads: int
    fights: list              # [FightResult, ...]
    mean_margin: float
    won: bool                 # every fight is side0
    defect: bool = False      # a draw or a cap sits in the cell (a lab defect to trace, never a result)


@dataclass
class ScanResult:
    size: int
    cells: list               # [CellResult, ...] in increasing enemy_heads
    beats: Optional[int]
    loses_to: Optional[int]
    ceiling_hit: bool = False   # won at every scanned headcount: beats is the top of the range, loses_to None
    multi_flip: bool = False    # the won/lost sequence over the scanned cells changes more than once


@dataclass
class Batch:
    title: str
    scans: dict               # label -> ScanResult
    firing_example: dict      # label -> FightResult whose firing series is charted
    rows: list                # [dict, ...] one per fight, from fight_row


TICKS_PER_SECOND = 20
OPENING_WINDOW_TICKS = 40     # DRAFT-opening-window-ticks (Westley to confirm): the primary prediction window after first contact
REENGAGE_SILENCE_TICKS = 40   # DRAFT-reengage-silence-ticks (Westley's number, the R-099-05 window): silent ticks of a side before the lab re-engages it
REENGAGE_MOVED_WU = 1.0       # DRAFT-reengage-moved-wu (Westley's number): an idle-eligible unit (attack-move role, no destination) counts as moved when displaced by more than this from its position at the window start (the tick the silence counter was last zeroed); destination-holders are not tested
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
def count_able(engine: Any, w: Any, units0: list, units1: list, arc_deg: float) -> tuple:
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
def cell(build: BuildFn, enemy_heads: int, replicates: int, fight_fn: Any = None) -> CellResult:
    raise NotImplementedError


def scan(build: BuildFn, size: int, enemy_from: int, enemy_to: int, replicates: int = 10,
         fight_fn: Any = None, full_scan: bool = False) -> ScanResult:
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
