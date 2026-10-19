"""Ground scenes (see ground/README.md): the slope-top scene s1_slope_top and its two variants on the generated field of seed 11,
and the parked tall-cover scene (a ground idea, not a space one)."""
import dataclasses
import math

from scripts.skilllab import plays
from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.contract import Cover, Group, Setup, Terrain
from scripts.skilllab.scenes import _placed_mean, guard_defenders, preflight
from scripts.skilllab.terrain import with_terrain

SCENE = "s1_slope_top"
SCENE_MARGINAL = "s1_slope_top_marginal"
SCENE_FLYER = "s1_slope_top_flyer"
SEED = 11
CANVAS = 12000.0        # seed 11 generates no slope at 4000 (measured 2026-10-14), six at 12000

ATTACK_LAYER, HOLD_LAYER = 1, 2     # bands 2 and 3 of the field; slope 2 of seed 11 joins them (foot (9350, 3150), top (8850, 3150))

# Sweep grids (spec L6 row; rulings 10 and 11). Each holds the engine default as its second point.
SLOPE_TOP_KNOBS = {
    "OM_TP_SIGHT_EYE_HEIGHT": (25, 50, 100, 200),
    "OM_TP_GROUND_FLYER_SEEN_MULT": (1.25, 1.5, 2, 3),
    "OM_TP_SLOPE_UP_DIV": (1.0, 1.1, 1.3, 2.0),      # DRAFT: the 0.25x band means nothing for a divisor near 1
}
EYE, MULT = "OM_TP_SIGHT_EYE_HEIGHT", "OM_TP_GROUND_FLYER_SEEN_MULT"
# Knobs that change nothing in the natural scene (measured 2026-10-14; making them live is a later design call for the Architect
# and Westley). The variants below carry their controls; INERT_KNOBS_BY_SCENE holds what each scene leaves inert.
INERT_KNOBS = {
    EYE: "every sight line from the top of slope 2 to its foot is clear at eye heights 25 to 200, so the holders see the whole attack from the first tick",
    MULT: "the flyer multiplier acts only on a flyer above the ground's layer, and the natural scene's Raiders walk",
}


def _holder_radius(n):
    return 30 + 3 * math.sqrt(n)        # small on purpose: the natural 80 + 12 sqrt(n) blob spills off the narrow ribbon of the slope


def _types(flyer_raider=False):
    """The reach table (Vanguard 0 up 0 down, Raider 1 up 1 down) on walking types; the flyer variant leaves the Raider flying."""
    walk = {"movement": "walking"}
    return {"Vanguard": {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, 0), **walk},
            "Raider": {"base": "Raider", "scale": {}, "set": {}, "reach": (1, 1), **({} if flyer_raider else walk)}}


def _blob_at(x, y, radius):
    return dict(formation="blob", x=float(x), y=float(y), facing=0.0, params=lambda n: {"radius": radius(n) if callable(radius) else radius})


def _line_at(x, y, spacing):
    """A line along x (facing 90): lays a group along a ribbon of ground too thin for a blob."""
    return dict(formation="line", x=float(x), y=float(y), facing=90.0, params=lambda n: {"spacing": spacing})


def _groups(side, n, layer, order, shapes):
    """M1 (Vanguard and Raider in equal halves) as one group per type; `shapes` = {type: shape or (shape, layer)}."""
    out = []
    for unit, count in (("Vanguard", (n + 1) // 2), ("Raider", n // 2)):
        shape = shapes[unit]
        shape, lay = shape if isinstance(shape, tuple) else (shape, layer)
        out.append(Group(side=side, unit=unit, count=count, formation=shape["formation"], x=shape["x"], y=shape["y"],
                         facing_deg=shape["facing"] + (0.0 if side == 0 else 180.0), layer=lay, order=order, params=shape["params"](count)))
    return out


def _scene(label, attackers, holders, size, flyer_raider=False):
    """build(enemy_heads, swap) for a slope-top scene: the holder guards on the top band, the attacker attack-moves to the holder's
    placed mean (ruling 6) from the foot of the slope. Nothing is shifted to fit (Q-LAB-03): labels['prefight'] is scenes.preflight."""
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        groups = tuple(_groups(0, size, ATTACK_LAYER, "attack_move", attackers) + _groups(1, enemy_heads, HOLD_LAYER, "guard", holders))
        setup = Setup(groups=groups, unit_types=_types(flyer_raider), point=_placed_mean([g for g in groups if g.side == 1]),
                      max_ticks=plays.max_ticks_for(size, enemy_heads), terrain=Terrain(canvas=(CANVAS, CANVAS), field_seed=SEED))
        build.labels["prefight"] = preflight(setup, None)
        return setup
    build.labels = {"scene": label, "prefight": None}
    return build


def _both(shape):
    return {"Vanguard": shape, "Raider": shape}


NATURAL_ATTACKERS = _both(_blob_at(9330.0, 3135.0, 20.0))      # the slope's foot, band 2
NATURAL_HOLDERS = _both(_blob_at(9050.0, 3180.0, _holder_radius))     # on the slope, past its midline, band 3


def slope_top(size=16):
    return _scene(SCENE, NATURAL_ATTACKERS, NATURAL_HOLDERS, size)


# s1_slope_top_marginal: the eye-height control. The attackers lie along the thin ribbon of band 2 north of the foot, where the holders'
# post at (8900, 3220) sees none of them at eye heights 25 and 50 and all of them at 100 and 200 (measured 2026-10-19). Lines, because
# a blob does not fit the ribbon (a unit shifts by up to contract.SHIFT_MAX per axis and must stay on walkable ground).
# See also: slope_top, whose attackers stand where eye height changes nothing (INERT_KNOBS).
MARGINAL_ATTACKERS = {"Vanguard": _line_at(9220.0, 2954.0, 12.0), "Raider": _line_at(9320.0, 2954.0, 12.0)}
MARGINAL_HOLDERS = _both(_blob_at(8900.0, 3220.0, _holder_radius))


def slope_top_marginal(size=16):
    return _scene(SCENE_MARGINAL, MARGINAL_ATTACKERS, MARGINAL_HOLDERS, size)


# s1_slope_top_flyer: the flyer-seen control (R-005-11). The Raider flies on both sides; the attacker Raiders hover on layer 2 over band 2
# ground 1900 wu from the holders, who see a flyer from the larger sensor radius (800) times OM_TP_GROUND_FLYER_SEEN_MULT: not at 1.25
# to 2 (1000 to 1600), at 3 (2400). The holder Raiders hover on layer 3 over band 3, so the multiplier applies to them as well.
# See also: scenes.preflight, which routes a flyer by a straight line, since a flyer over lower ground has no path on the walk mask.
FLYER_ATTACKERS = {"Vanguard": NATURAL_ATTACKERS["Vanguard"], "Raider": (_blob_at(10550.0, 4350.0, 8.0), ATTACK_LAYER + 1)}
FLYER_HOLDERS = {"Vanguard": NATURAL_HOLDERS["Vanguard"], "Raider": (NATURAL_HOLDERS["Raider"], HOLD_LAYER + 1)}


def slope_top_flyer(size=16):
    return _scene(SCENE_FLYER, FLYER_ATTACKERS, FLYER_HOLDERS, size, flyer_raider=True)


# What each scene leaves inert, read as the holders' first-sight reading (the variants' controls, tests/skilllab/ground/test_slope_top_variants.py).
# Measured 2026-10-19: in the variants the knob they carry changes who is seen first but not the FightResult (both sides attack-move or
# guard and meet anyway), so a batch on a variant reports first sight, not the result, for that knob.
INERT_KNOBS_BY_SCENE = {
    SCENE: INERT_KNOBS,
    SCENE_MARGINAL: {MULT: INERT_KNOBS[MULT]},
    SCENE_FLYER: {EYE: "the walking Vanguards start at the foot of the slope, where every sight line is clear at eye heights 25 to 200"},
}


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
