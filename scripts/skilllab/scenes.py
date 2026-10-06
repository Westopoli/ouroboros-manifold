"""Hand-built scenes in canvas coordinates."""
import dataclasses
import math

from scripts.skilllab.contract import Block, Group, Setup, Terrain

_CANVAS = (3000.0, 1600.0)
_WALL = (1500, 1600)
_GAP = (700, 900)


def phase_b_choke(defenders=8):
    """The Phase B choke: a wall with a gap, defenders in a line behind it, attackers in a blob in front."""
    def build(enemy_heads, swap):
        if defenders < 1 or enemy_heads < 1:
            raise ValueError("defenders and enemy_heads must be >= 1")
        terrain = Terrain(canvas=_CANVAS, blocks=(Block(_WALL[0], 0, _WALL[1], _GAP[0], 0, 4),
                                                  Block(_WALL[0], _GAP[1], _WALL[1], _CANVAS[1], 0, 4)))
        return Setup(groups=(
            Group(side=0, unit="Vanguard", count=defenders, formation="line", x=1700.0, y=800.0, facing_deg=180.0,
                  layer=0, order="attack_move", params={"spacing": 30}),
            Group(side=1, unit="Vanguard", count=enemy_heads, formation="blob", x=800.0, y=800.0, facing_deg=0.0,
                  layer=0, order="attack_move", params={"radius": 80 + 12 * math.sqrt(enemy_heads)})),
            unit_types={}, terrain=terrain)
    build.labels = {"play_side0": "defenders line", "play_side1": "attackers blob",
                    "status_side0": "naive", "status_side1": "naive"}
    return build


def guard_defenders(build):
    """Side 1 of the built setup holds the guard order (R-096-08)."""
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        groups = tuple(dataclasses.replace(g, order="guard") if g.side == 1 else g for g in setup.groups)
        return dataclasses.replace(setup, groups=groups)
    return wrapped
