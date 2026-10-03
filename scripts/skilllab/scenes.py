"""Hand-built scenes in canvas coordinates."""
import dataclasses
import math

from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.contract import Block, Cover, Group, Setup, Terrain
from scripts.skilllab.terrain import with_terrain

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


def tall_cover_terrain(height=3):
    """The wall in play coordinates (centred); with_terrain shifts it to canvas centre."""
    if not (isinstance(height, int) or float(height).is_integer()) or not 0 <= height <= 5:
        raise ValueError("height must be a whole number 0..5, got %r" % (height,))
    covers = tuple(Cover(x=0.0, y=k * 150.0, radius=100.0, height=height) for k in range(-4, 5))
    return Terrain(canvas=(4000.0, 4000.0), covers=covers)


def tall_cover(height=3, counter=False):
    """Unconfirmed draft: nine Cover discs (radius 100, every 150 wu) between a blob and guarding defenders.

    counter=True puts the attackers on layer `height` as VanguardHigh, which reaches `height` layers down.
    """
    def builder(size):
        naive = asym_play(size, Side("blob"), Side("blob"))
        play = with_terrain(guard_defenders(naive), tall_cover_terrain(height))

        def build(enemy_heads, swap):
            setup = play(enemy_heads, swap)
            if not counter:
                return setup
            groups = tuple(dataclasses.replace(g, unit="VanguardHigh", layer=height) if g.side == 0 else g
                           for g in setup.groups)
            high = {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, height)}
            # draft numbers: range, damage and vision at full strength for every layer offset down to the cover height
            settings = {"OM_TP_%s_DOWN_%d" % (kind, n): 1.0 for kind in ("RANGE", "DAMAGE", "VISION")
                        for n in range(1, height + 1)}
            return dataclasses.replace(setup, groups=groups, unit_types={"VanguardHigh": high},
                                       settings={**setup.settings, **settings})
        build.labels = dict(naive.labels, status="unconfirmed draft")
        return build
    return builder
