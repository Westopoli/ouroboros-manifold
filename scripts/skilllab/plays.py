"""Plays: builders of the two-sided Setups the scans fight.
Each issues one attack-move per group. The hold-to-contact opening of approach.py (groups walk as a group move to a stop
line, then attack-move) is a lab setting, off by default (A199): pass approach=APPROACH_STOP to switch it on."""
import math

from scripts.skilllab.contract import Group, Setup

_LINE_SPACING = 30
APPROACH = 0.0          # default: off, one attack-move per group
MAX_TICKS_BIG = 12000   # A201: cells of 32 a side and above get the cap named here; same as the Setup default since 2026-10-06 (TD-LAB-tick-cap)
MOPUP = True            # lab rule, provisional (mopup.py): a stopped side re-issues its attack-move at what it sees
MOPUP_INTERVAL_TICKS = 200
APPROACH_STOP = 0.95    # the stop factor of the lab setting (A198)
_STATS = {}


def max_ticks_for(size, enemy_heads):
    """max_ticks of a play: MAX_TICKS_BIG when either side has 32 or more units, else the Setup default."""
    return MAX_TICKS_BIG if max(size, enemy_heads) >= 32 else Setup.__dataclass_fields__["max_ticks"].default


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


def _play(size, unit, kind, side0_unit=None, unit_types=None, approach=APPROACH, mopup=MOPUP):
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        gap = unit_stats(unit)["sensor_radius"] + 1 + _depth(size, kind) + _depth(enemy_heads, kind)
        return Setup(groups=(_group(0, side0_unit or unit, size, kind, -gap / 2),
                             _group(1, unit, enemy_heads, kind, gap / 2)),
                     unit_types=dict(unit_types or {}), approach=approach, mopup=mopup, mopup_interval_ticks=MOPUP_INTERVAL_TICKS,
                     max_ticks=max_ticks_for(size, enemy_heads))
    return build


def blob_play(size, unit="Vanguard", approach=APPROACH, mopup=MOPUP):
    return _play(size, unit, "blob", approach=approach, mopup=mopup)


def line_play(size, unit="Vanguard", approach=APPROACH, mopup=MOPUP):
    return _play(size, unit, "line", approach=approach, mopup=mopup)


def _derived_play(size, unit, factor, suffix, stat, approach=APPROACH, mopup=MOPUP):
    if factor <= 0:
        raise ValueError("factor must be > 0")
    name = unit + suffix
    types = {name: {"base": unit, "scale": {stat: factor}, "set": {}}}
    return _play(size, unit, "blob", side0_unit=name, unit_types=types, approach=approach, mopup=mopup)


def reach_play(size, unit="Vanguard", factor=1.2, approach=APPROACH, mopup=MOPUP):
    return _derived_play(size, unit, factor, "Long", "attack_range", approach)


def damage_play(size, unit="Vanguard", factor=1.2, approach=APPROACH, mopup=MOPUP):
    return _derived_play(size, unit, factor, "Strong", "base_damage", approach)
