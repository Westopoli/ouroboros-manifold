"""The two controls for R* (SPEC.md sections 14.1 and 14.5): a mirror (R* near 1) and a planted range advantage."""
import copy
from pathlib import Path

from .. import ffi, scenario
from .cost import unit_cost
from .rstar import rstar

_BASE = Path(__file__).resolve().parents[2] / "scenarios" / "base.toml"
_ANCHOR = {"A": (1000.0, 1000.0), "B": (3000.0, 1000.0)}
_FACING = {"A": 0.0, "B": 180.0}
_ACROSS, _SPACING = 20, 50.0
_LAYER = 3
_PLANTED_RANGE = 240.0


def _ranks(side, kind, n, goal):
    """`n` units in a line abreast in ranks: at most 20 across, further ranks 50 behind, away from the enemy."""
    ax, ay = _ANCHOR[side]
    back = -1.0 if side == "A" else 1.0
    groups = []
    for r in range((n + _ACROSS - 1) // _ACROSS):
        groups.append({
            "side": side, "type": kind, "count": min(_ACROSS, n - r * _ACROSS),
            "formation": "line", "x": ax + back * _SPACING * r, "y": ay, "facing": _FACING[side],
            "layer": _LAYER, "spacing": _SPACING, "order": "attack_move", "goal": list(goal),
            "target_policy": "nearest",
        })
    return groups


def _build(size, skilled_type):
    base = scenario.load(str(_BASE))
    base["run"] = {"max_ticks": 9000, "stalemate_ticks": 1500}
    base["types"]["raider_far"] = {**base["types"]["raider"], "range": _PLANTED_RANGE}
    base["types"]["raider_far"]["cost"] = unit_cost(base, "raider")

    def build(ratio, swap):
        other = max(1, int(ratio * size + 0.5))
        if size + other > ffi.MAX_UNITS:
            raise ValueError("%d + %d raiders exceed LL_MAX_UNITS %d" % (size, other, ffi.MAX_UNITS))
        skilled_side, other_side = ("B", "A") if swap else ("A", "B")
        scn = copy.deepcopy(base)
        scn["groups"] = (_ranks(skilled_side, skilled_type, size, _ANCHOR[other_side])
                         + _ranks(other_side, "raider", other, _ANCHOR[skilled_side]))
        return scn

    return build


def mirror_build(size):
    return _build(size, "raider")


def advantage_build(size):
    return _build(size, "raider_far")


def mirror_control(size, processes=None, win_margin=0.02):
    return rstar(mirror_build(size), processes=processes, win_margin=win_margin, size=size)


def advantage_control(size, processes=None, win_margin=0.02):
    return rstar(advantage_build(size), processes=processes, win_margin=win_margin, size=size)
