# spec: LAB-REV2-L6 / L2 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md; decisions 20 and 27 of 2026-10-14-skill-lab-rev2-decisions.md); R-001-07, R-004-01
"""scenes.preflight routes a flyer on the 50 wu grid like a walker; only the mask differs (decisions 20 and 27, Architect 2026-10-19).

Ruling (binding): every mover is breadth-first routed on the 50 wu grid from its start to the point. A flyer's mask is the cells not
blocked at its layer (a block whose blocked_layer_top, Block.layer_hi, reaches the flyer's layer blocks it; one below passes); the
terrain-walk mask does not apply to it (R-001-07, R-004-01). A walker's mask is the terrain-walkable cells that are not blocked. On a
space scene (no terrain) the two masks coincide, so a flyer goes round a wall through its gap exactly as a walker does. The earlier
straight-line cell walk is RETIRED (TD-LAB-REV2-L6-flyer). A flyer still gets no_fit and no_reach.

How a type is a walker (decision 27): Setup.unit_types[name]["movement"] == "walking" when the play gives it, else the engine's own
reading (Engine.movement_kind; an unset type reads flying). A built-in type, or a custom one with no "movement" key, is a flyer.

Geometry (seed 11, 12000 canvas, layer 0 = band 1, measured 2026-10-19): (10250, 2750) is walkable ground in an 81-cell pocket of
the layer 0 walk mask that is not connected to the main ground, where (2100, 2000) lies; a walker there cannot reach it. Hand-built
cases use a 4000 x 1000 canvas, movers at (500, 500) going to (3500, 500), and a wall across x 1800..2000."""
import collections
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, scenes  # noqa: E402
from scripts.skilllab.contract import Block, Group, Setup, Terrain  # noqa: E402

WALKER = {"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}
POCKET, MAIN = (10250.0, 2750.0), (2100.0, 2000.0)
FIELD = Terrain(canvas=(12000.0, 12000.0), field_seed=11)
START, GOAL = (500.0, 500.0), (3500.0, 500.0)
FLY_LAYER = 2


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def _setup(unit, start, goal, terrain, layer=0, unit_types=None, holder_order="idle", holder_layer=None):
    mover = Group(side=0, unit=unit, count=1, formation="points", x=start[0], y=start[1], facing_deg=0.0, layer=layer,
                  order="move", goal=goal, params={"points": [start]})
    other = Group(side=1, unit="Vanguard", count=1, formation="points", x=goal[0], y=goal[1], facing_deg=180.0,
                  layer=layer if holder_layer is None else holder_layer, order=holder_order, params={"points": [goal]})
    return Setup(groups=(mover, other), unit_types=unit_types or {}, terrain=terrain)


def _wall(layer_hi, y0=0.0, y1=1000.0):
    return Terrain(canvas=(4000.0, 1000.0), blocks=(Block(x0=1800.0, y0=y0, x1=2000.0, y1=y1, layer_lo=0, layer_hi=layer_hi),))


def _fly(terrain, **kw):
    return _setup("Vanguard", START, GOAL, terrain, layer=FLY_LAYER, **kw)


def _walk(terrain):
    return _setup("Walker", START, GOAL, terrain, layer=FLY_LAYER, unit_types=WALKER)


def _components_differ(lib):
    """Control: on layer 0 the pocket and the main ground are two connected pieces of the walk mask (100 wu cells, 4-connected)."""
    w = lib.new_world(0)
    try:
        lib.set_canvas(w, 12000.0, 12000.0)
        assert lib.terrain_generate(w, 11, 12000.0) == 0
        cols, rows, _bands = lib.terrain_dump_bands(w)
        mask = lib.terrain_walk_mask(w, 0)
        assert lib.terrain_walkable_at(w, *POCKET) and lib.terrain_walkable_at(w, *MAIN)
    finally:
        lib.free_world(w)
    start = (int(POCKET[0] // 100), int(POCKET[1] // 100))
    seen, queue = {start}, collections.deque([start])
    while queue:
        cx, cy = queue.popleft()
        for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and mask[n[1] * cols + n[0]]:
                seen.add(n)
                queue.append(n)
    return (int(MAIN[0] // 100), int(MAIN[1] // 100)) not in seen


def test_control_the_pocket_is_cut_off_from_the_main_ground(lib):
    assert _components_differ(lib)


# --- the terrain-walk mask does not apply to a flyer (case 1); the positive pair is the walker from the same pocket (case 4) ---

def test_a_flyer_whose_start_is_cut_off_on_the_ground_mask_is_ok(lib):
    """A non-walkable band cuts the pocket off on the walk mask; the flyer's mask is unblocked cells only, so it reads ok."""
    assert scenes.preflight(_setup("Vanguard", POCKET, MAIN, FIELD), lib) == "ok"


def test_control_a_walker_from_the_same_pocket_to_the_same_target_is_unroutable(lib):
    assert scenes.preflight(_setup("Walker", POCKET, MAIN, FIELD, unit_types=WALKER), lib) == "unroutable"


def test_a_walker_over_open_ground_on_the_same_field_is_ok(lib):
    """Positive control for the control above: the walker's refusal is the pocket, not the field or the type."""
    assert scenes.preflight(_setup("Walker", (2000.0, 2000.0), MAIN, FIELD, unit_types=WALKER), lib) == "ok"


# --- walls on the flyer's own layer (cases 2 and 3) ---

def test_a_flyer_against_a_wall_reaching_its_layer_is_unroutable(lib):
    assert scenes.preflight(_fly(_wall(layer_hi=FLY_LAYER)), lib) == "unroutable"


def test_a_flyer_against_a_taller_wall_is_unroutable(lib):
    assert scenes.preflight(_fly(_wall(layer_hi=4)), lib) == "unroutable"


def test_a_flyer_against_a_wall_that_stops_below_its_layer_is_ok(lib):
    assert scenes.preflight(_fly(_wall(layer_hi=FLY_LAYER - 1)), lib) == "ok"


def test_control_a_walker_on_the_same_layer_reads_the_same_walls(lib):
    assert scenes.preflight(_walk(_wall(layer_hi=FLY_LAYER)), lib) == "unroutable"
    assert scenes.preflight(_walk(_wall(layer_hi=FLY_LAYER - 1)), lib) == "ok"


# --- the flyer is routed on the grid, round a gap (decisions 20 and 27) ---

def test_a_flyer_is_routed_round_a_wall_through_its_gap(lib):
    """The wall spans y 0..700, so a gap at y 700..1000 exists at the flyer's layer: the grid search goes round it and reads ok. Red
    while the source walks a straight line from (500, 500) to (3500, 500) across the wall and answers "unroutable"."""
    assert scenes.preflight(_fly(_wall(FLY_LAYER, y0=0.0, y1=700.0)), lib) == "ok"


def test_a_flyer_with_no_gap_at_its_layer_is_unroutable(lib):
    """Positive control for the gap case: the same wall over the full height (no gap) at the flyer's layer refuses it."""
    assert scenes.preflight(_fly(_wall(FLY_LAYER, y0=0.0, y1=1000.0)), lib) == "unroutable"


def test_a_flyer_whose_gap_is_closed_by_a_second_block_at_its_layer_is_unroutable(lib):
    """Two blocks at the flyer's layer leave no gap: y 0..700 and y 700..1000 in the same wall column."""
    t = Terrain(canvas=(4000.0, 1000.0), blocks=(
        Block(x0=1800.0, y0=0.0, x1=2000.0, y1=700.0, layer_lo=0, layer_hi=FLY_LAYER),
        Block(x0=1800.0, y0=700.0, x1=2000.0, y1=1000.0, layer_lo=0, layer_hi=FLY_LAYER)))
    assert scenes.preflight(_fly(t), lib) == "unroutable"


def test_a_flyer_whose_gap_block_stops_below_its_layer_is_ok(lib):
    """The upper piece of the wall (y 700..1000) tops out below the flyer's layer, so it is a gap for the flyer."""
    t = Terrain(canvas=(4000.0, 1000.0), blocks=(
        Block(x0=1800.0, y0=0.0, x1=2000.0, y1=700.0, layer_lo=0, layer_hi=FLY_LAYER),
        Block(x0=1800.0, y0=700.0, x1=2000.0, y1=1000.0, layer_lo=0, layer_hi=FLY_LAYER - 1)))
    assert scenes.preflight(_fly(t), lib) == "ok"


def test_control_a_walker_is_routed_round_the_same_gap(lib):
    assert scenes.preflight(_walk(_wall(FLY_LAYER, y0=0.0, y1=700.0)), lib) == "ok"


def test_a_flyer_whose_route_misses_the_wall_is_ok(lib):
    """A wall at y 800..1000 reaches the flyer's layer but is off the way at y 500."""
    assert scenes.preflight(_fly(_wall(FLY_LAYER, y0=800.0, y1=1000.0)), lib) == "ok"


# --- no_fit and no_reach still apply to a flyer (case 5) ---

def test_a_flyer_placed_inside_a_block_on_its_layer_is_no_fit(lib):
    t = Terrain(canvas=(4000.0, 1000.0), blocks=(Block(x0=400.0, y0=400.0, x1=600.0, y1=600.0, layer_lo=0, layer_hi=FLY_LAYER),))
    assert scenes.preflight(_fly(t), lib) == "no_fit"


def test_a_flyer_placed_inside_a_block_below_its_layer_is_not_no_fit(lib):
    """Positive control for the case above: the same block spanning layers 0..1 does not hold a flyer on layer 2."""
    t = Terrain(canvas=(4000.0, 1000.0), blocks=(Block(x0=400.0, y0=400.0, x1=600.0, y1=600.0, layer_lo=0, layer_hi=FLY_LAYER - 1),))
    assert scenes.preflight(_fly(t), lib) == "ok"


def test_a_flyer_that_cannot_reach_a_holders_layer_is_no_reach_on_open_blank_ground(lib):
    t = Terrain(canvas=(4000.0, 1000.0))
    s = _setup("Vanguard", START, GOAL, t, layer=0, holder_order="guard", holder_layer=3)
    assert scenes.preflight(s, lib) == "no_reach"


def test_a_cut_off_flyer_that_cannot_reach_a_holders_layer_is_no_reach_not_unroutable(lib):
    """The flyer's mask must reach no_reach: the pocket flyer is not unroutable, so the answer is no_reach."""
    s = _setup("Vanguard", POCKET, MAIN, FIELD, layer=0, holder_order="guard", holder_layer=3)
    assert scenes.preflight(s, lib) == "no_reach"
