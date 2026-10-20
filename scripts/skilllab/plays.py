"""Plays: builders of the two-sided Setups the scans fight.
A meeting (ruling 6): both sides are attack-moved to Setup.point, the midpoint of the two anchors, one order per group (orders_per_unit False; True is the per-unit opt-in)."""
import math

from scripts.skilllab.contract import Group, Setup

_LINE_SPACING = 30
_STATS = {}


def max_ticks_for(size, enemy_heads):
    """max_ticks of a play: the Setup default (12000) for every cell, big or small (A201 as changed 2026-10-06, TD-LAB-tick-cap)."""
    return Setup.__dataclass_fields__["max_ticks"].default


def unit_stats(name):
    if name not in _STATS:
        from scripts.skilllab.engine import Engine
        eng = Engine()
        w = eng.new_world(0)
        try:
            _STATS[name] = eng.type_stats(w, eng.type_id(name))
        finally:
            eng.free_world(w)
    return _STATS[name]


def _depth(count, kind):
    return 0.0 if kind == "line" else 80 + 12 * math.sqrt(count)


def _group(side, unit, count, kind, x):
    params = {"spacing": _LINE_SPACING} if kind == "line" else {"radius": _depth(count, kind)}
    return Group(side=side, unit=unit, count=count, formation=kind, x=x, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0,
                 order="attack_move", goal=None, params=params)


def _play(size, unit, kind, side0_unit=None, unit_types=None):
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        gap = unit_stats(unit)["sensor_radius"] + 1 + _depth(size, kind) + _depth(enemy_heads, kind)
        return Setup(groups=(_group(0, side0_unit or unit, size, kind, -gap / 2),
                             _group(1, unit, enemy_heads, kind, gap / 2)),
                     unit_types=dict(unit_types or {}), point=(0.0, 0.0), max_ticks=max_ticks_for(size, enemy_heads))
    return build


def blob_play(size, unit="Vanguard"):
    return _play(size, unit, "blob")


def line_play(size, unit="Vanguard"):
    return _play(size, unit, "line")


def _derived_play(size, unit, factor, suffix, stat):
    if factor <= 0:
        raise ValueError("factor must be > 0")
    name = unit + suffix
    types = {name: {"base": unit, "scale": {stat: factor}, "set": {}}}
    return _play(size, unit, "blob", side0_unit=name, unit_types=types)


def reach_play(size, unit="Vanguard", factor=1.2):
    return _derived_play(size, unit, factor, "Long", "attack_range")


def damage_play(size, unit="Vanguard", factor=1.2):
    return _derived_play(size, unit, factor, "Strong", "base_damage")
