"""Plays: builders of the two-sided Setups the scans fight."""
import math

from scripts.skilllab.contract import Group, Setup

_ANCHOR = 600.0
_LINE_SPACING = 30


def _group(side, unit, count, kind):
    params = {"spacing": _LINE_SPACING} if kind == "line" else {"radius": 80 + 12 * math.sqrt(count)}
    return Group(side=side, unit=unit, count=count, formation=kind,
                 x=-_ANCHOR if side == 0 else _ANCHOR, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0,
                 order="attack_move", goal=None, params=params)


def _play(size, unit, kind, side0_unit=None, unit_types=None):
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        return Setup(groups=(_group(0, side0_unit or unit, size, kind), _group(1, unit, enemy_heads, kind)),
                     unit_types=dict(unit_types or {}))
    return build


def blob_play(size, unit="Vanguard"):
    return _play(size, unit, "blob")


def line_play(size, unit="Vanguard"):
    return _play(size, unit, "line")


def reach_play(size, unit="Vanguard", factor=1.2):
    if factor <= 0:
        raise ValueError("factor must be > 0")
    name = unit + "Long"
    types = {name: {"base": unit, "scale": {"attack_range": factor}, "set": {}}}
    return _play(size, unit, "blob", side0_unit=name, unit_types=types)
