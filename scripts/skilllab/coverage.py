"""Coverage of the swept plays over the game (rev 3 plan R5, test T1; defects D1, D2, D10; ledger FINDING-lab-d1, -d2, -d10).

Three lists of what the plays named in sweep.PLAYS_BY_FAMILY do NOT exercise (a play nobody sweeps covers nothing):
  cells     (attacker category, target category) over ALG-60's Strike, Line, Siege: a unit of the first on one side, of the second on the other
  pairings  (type, offset): offset is the target layer minus the shooter layer, within the type's reach (up, down)
  layers    the engine's layers 0 to OM_LAYER_COUNT - 1
"""
from scripts.skilllab import plays_space, sweep

CATEGORY = {"Raider": "Strike", "Interceptor": "Strike", "Vanguard": "Line", "Warden": "Line", "Bombard": "Siege", "Bastion": "Siege"}
LAYER_COUNT = 5     # OM_LAYER_COUNT


def default_reach():
    return {**plays_space._REACH, "Warden": (0, 0)}


def uncovered(setups, reach=None):
    reach = default_reach() if reach is None else reach
    cells, pairings, layers = set(), set(), set()
    for setup in setups:
        for a in setup.groups:
            layers.add(a.layer)
            for b in setup.groups:
                if a.side == b.side:
                    continue
                cells.add((CATEGORY[a.unit], CATEGORY[b.unit]))
                up, down = reach[a.unit]
                if -down <= b.layer - a.layer <= up:
                    pairings.add((a.unit, b.layer - a.layer))
    categories = set(CATEGORY.values())
    want_cells = {(x, y) for x in categories for y in categories}
    want_pairings = {(t, d) for t in CATEGORY for d in range(-reach[t][1], reach[t][0] + 1)}
    return {"cells": sorted(want_cells - cells), "pairings": sorted(want_pairings - pairings),
            "layers": sorted(set(range(LAYER_COUNT)) - layers)}


def report():
    names = sorted({p for plays in sweep.PLAYS_BY_FAMILY.values() for p in plays})
    return uncovered([plays_space.PLAYS[n].setup_fn() for n in names])
