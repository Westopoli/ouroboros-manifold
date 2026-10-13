"""Ground scenes, parked (see ground/README.md): tall cover is a ground idea, not a space one."""
import dataclasses

from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.contract import Cover, Terrain
from scripts.skilllab.scenes import guard_defenders
from scripts.skilllab.terrain import with_terrain


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
