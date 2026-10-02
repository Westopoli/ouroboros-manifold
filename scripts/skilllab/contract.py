"""Locked contract of the skill lab harness (spec: docs/northstar/plans/skilllab-harness-spec.md).

Dataclasses carry data between modules. The `def` stubs below are the cross-module call
signatures; each is implemented in the module named in its comment, and every body here is a
sentinel. Callers import the real function from its own module, never from this file.
"""
from __future__ import annotations

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
    order: str                # "attack_move" | "move" | "idle"
    goal: Optional[tuple] = None
    params: dict = field(default_factory=dict)   # spacing, cols, arc_deg, radius, points


@dataclass(frozen=True)
class Setup:
    groups: tuple
    unit_types: dict          # name -> stats; see spec AC 5 (full stats, or base + scale/set)
    abilities: bool = False   # False calls om_tactical_disable_abilities
    max_ticks: int = 6000
    stalemate_ticks: int = 400
    sample_every: int = 5     # ticks between firing-count samples
    trace: bool = False       # True records FightResult.trace
    settings: dict = field(default_factory=dict)   # OM_TP_* name -> number, set on the world before tick 1


@dataclass
class FightResult:
    outcome: str              # "side0" | "side1" | "stalemate" | "cap"
    margin: float
    strength_left: tuple
    survivors: tuple
    heads: tuple
    ticks: int
    first_contact_tick: int
    firing: list              # [(tick, able0, able1), ...]
    firing_unit_seconds: tuple
    trace: Optional[list] = None   # [(tick, unit, x, y, target, facing, alive), ...] when Setup.trace, else None


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
