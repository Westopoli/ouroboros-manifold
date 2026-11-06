"""A `vantage` feature as engine terrain (stage 4 fix F1; docs/reports/2026-11-06-stage4-fix-plan.md, DEC-stage4-vantage-terrain-2026-11-06).

Westley 2026-11-06: red sees and fires at a hill only once it is past the halfway point of the ramp, because it is then on the upper layer (R-001-06, R-004-06,
R-005-09). `heights` builds a disc of one band on a radial ramp of RAMP_WU, from the same formula the replay draws (scenes/proto/layout_shot/layout_shot.gd `_tier_at`: tier
0 at radius + RAMP_WU, tier 1 at radius), and `features.apply(exact=True)` hands it to `Engine.terrain_set_heights`. The engine bands a cell by its height over the global range
in five steps, so the heights run from LOW_CM to LOW_CM + 2 * STEP_CM - 1 over the ramp (the band boundary, LOW_CM + STEP_CM, falls at the ramp's middle, tier 0.5) and one
corner cell is raised to LOW_CM + 5 * STEP_CM, which sets the step of a band to STEP_CM. That cell is a wall of its own (unwalkable) in the map's corner. STEP_CM is the
steepest one-cell rise the engine's walk test accepts with room to spare (a ramp rises STEP_CM per 100 wu cell); the walker flips layer where the band changes along its row.
See also: scripts/skilllab/arena/features.py (the slope band built the same way), the drawing in layout_shot.gd."""
import math

RAMP_WU = 200.0    # DRAFT-shot-ramp-wu, as layout_shot.gd RAMP_WU: the slope that joins the rise to the ground
LOW_CM = 7000      # above the generator's dry level (6000 cm), so it is a band floor
STEP_CM = 6000     # one band; a ramp rises this much per 100 wu cell, which the walk test (OM_TP_TERRAIN_STEEP_DEG) accepts
BAND_DIV = 5       # TG_BAND_DIV in csrc/terrain.c
TERRAIN_CELL = 100.0


def vantages(layout):
    return [f for f in layout.get("features", []) if f.get("kind") == "vantage"]


def check_preset(preset):
    if preset["layers"] < 2:
        raise ValueError("a vantage needs a preset with two layers or more, got %d" % preset["layers"])


def heights(feats, cells_w, cells_h):
    """Row-major cell heights in cm for the vantage features `feats` on a cells_w x cells_h grid (sampled at the cell centres, as the replay's drawing samples them)."""
    for f in feats:
        if f.get("height_band", 1) != 1:
            raise ValueError("vantage feature %r: only height_band 1 is built" % (f,))
    cm = []
    for cy in range(cells_h):
        for cx in range(cells_w):
            t = 0.0
            for f in feats:
                d = math.hypot((cx + 0.5) * TERRAIN_CELL - f["x"], (cy + 0.5) * TERRAIN_CELL - f["y"])
                t = max(t, min(1.0, max(0.0, (f["radius"] + RAMP_WU - d) / RAMP_WU)))
            cm.append(LOW_CM + int(t * (2 * STEP_CM - 1)))
    if cm[0] != LOW_CM:
        raise ValueError("a vantage reaches the corner cell that holds the band-step marker")
    cm[0] = LOW_CM + BAND_DIV * STEP_CM
    return cm


def ground_layer(engine, w, x, y):
    """The layer the ground gives a unit placed at (x, y): the terrain band of its cell, less one."""
    return engine.terrain_band_at(w, x, y) - 1
