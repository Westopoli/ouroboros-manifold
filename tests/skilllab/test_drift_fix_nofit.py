# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 20 as rewritten ("no_fit on field_seed terrain reads terrain_walkable_at for
# every walking mover"), LAB-REV2-FIX ruling 4 (Architect, decisions 41 and 42, 2026-10-19); R-001-07, R-004-01
"""scenes.preflight's no_fit: only WALKING movers read the generated field's walk mask.

Red on the integrated tree: scenes._no_fit reads terrain_walkable_at for EVERY placed unit, so a flyer hovering over unwalkable ground, and
a guard standing on it, read no_fit although the field's walk mask does not apply to them (a flyer's mask is the unblocked cells; a guard
does not move). Reading fixed here (decision 20, as rewritten):
  - a walking MOVER (unit_types[name]["movement"] == "walking", or the engine's own reading; order attack_move / move / group_move) on
    ground terrain_walkable_at refuses is "no_fit";
  - a flyer (the built-in types, whose unset movement reads flying) with a moving order, and a GUARD group of any type, walking included,
    are checked against blocks only: "ok" over unwalkable ground, "no_fit" inside a block on their layer;
  - hand-built blocks refuse every group, walker or not (unchanged).
Not pinned: an idle walker (neither a mover nor a guard; the ruling names movers, flyers and guards only).
Seed 11, 12000 canvas: (3500, 4000) is unwalkable band 1 ground, (2000, 2000) and (2100, 2000) are walkable (test_scenes_preflight_field_fit)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, scenes  # noqa: E402
from scripts.skilllab.contract import Block, Group, Setup, Terrain  # noqa: E402

UNWALKABLE, WALKABLE, FOE = (3500.0, 4000.0), (2000.0, 2000.0), (2100.0, 2000.0)
WALKER = {"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}
CANVAS = (12000.0, 12000.0)


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def _group(side, unit, p, order, goal=None, layer=0):
    return Group(side=side, unit=unit, count=1, formation="points", x=p[0], y=p[1], facing_deg=0.0, layer=layer, order=order, goal=goal,
                 params={"points": [p]})


def _setup(unit, at, order, blocks=(), extra=(), seed=11):
    """Side 0: one `unit` at `at` with `order` (a mover goes to FOE); side 1: an idle Vanguard on walkable ground at FOE."""
    mover = _group(0, unit, at, order, goal=FOE if order in ("move", "attack_move", "group_move") else None)
    return Setup(groups=(mover, _group(1, "Vanguard", FOE, "idle")) + tuple(extra), unit_types=dict(WALKER),
                 terrain=Terrain(canvas=CANVAS, blocks=tuple(blocks), field_seed=seed))


def test_control_the_two_places_are_what_the_comments_say(lib):
    w = lib.new_world(0)
    try:
        lib.set_canvas(w, *CANVAS)
        assert lib.terrain_generate(w, 11, CANVAS[0]) == 0
        assert not lib.terrain_walkable_at(w, *UNWALKABLE)
        assert lib.terrain_walkable_at(w, *WALKABLE) and lib.terrain_walkable_at(w, *FOE)
        assert lib.movement_kind(w, lib.type_id("Vanguard")) != 1           # the built-in type is a flyer
    finally:
        lib.free_world(w)


# ---- the walker keeps the rule (positive control for everything below) ---------------------------------------------------------------

@pytest.mark.parametrize("order", ["move", "attack_move", "group_move"])
def test_a_walking_mover_on_unwalkable_ground_is_no_fit(lib, order):
    assert scenes.preflight(_setup("Walker", UNWALKABLE, order), lib) == "no_fit"


def test_control_the_same_walker_on_walkable_ground_is_ok(lib):
    assert scenes.preflight(_setup("Walker", WALKABLE, "move"), lib) == "ok"


# ---- a flyer is checked against blocks only -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("order", ["move", "attack_move", "group_move"])
def test_a_flyer_over_unwalkable_ground_is_ok(lib, order):
    """Red before: terrain_walkable_at is read for the flyer too."""
    assert scenes.preflight(_setup("Vanguard", UNWALKABLE, order), lib) == "ok"


def test_a_flyer_inside_a_block_on_its_layer_is_no_fit(lib):
    """Positive control: blocks still refuse a flyer (they reach its layer)."""
    block = Block(x0=3400.0, y0=3900.0, x1=3600.0, y1=4100.0, layer_lo=0, layer_hi=4)
    assert scenes.preflight(_setup("Vanguard", UNWALKABLE, "move", blocks=(block,)), lib) == "no_fit"


def test_a_flyer_over_a_block_that_does_not_reach_its_layer_is_ok(lib):
    """The block stops below the flyer's layer (layer_hi 0, the flyer on layer 1): it passes, and the ground under it is not read."""
    block = Block(x0=3400.0, y0=3900.0, x1=3600.0, y1=4100.0, layer_lo=0, layer_hi=0)
    setup = _setup("Vanguard", UNWALKABLE, "move", blocks=(block,))
    flyer = _group(0, "Vanguard", UNWALKABLE, "move", goal=FOE, layer=1)
    setup = Setup(groups=(flyer, _group(1, "Vanguard", FOE, "idle", layer=1)), unit_types=setup.unit_types, terrain=setup.terrain)
    assert scenes.preflight(setup, lib) == "ok"


# ---- a guard is checked against blocks only ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("unit", ["Vanguard", "Walker"])
def test_a_guard_on_unwalkable_ground_is_ok_whatever_its_type(lib, unit):
    """Red before. A walking type on guard does not move, so the walk mask is not its business either."""
    assert scenes.preflight(_setup(unit, UNWALKABLE, "guard"), lib) == "ok"


@pytest.mark.parametrize("unit", ["Vanguard", "Walker"])
def test_a_guard_inside_a_block_on_its_layer_is_no_fit(lib, unit):
    block = Block(x0=3400.0, y0=3900.0, x1=3600.0, y1=4100.0, layer_lo=0, layer_hi=4)
    assert scenes.preflight(_setup(unit, UNWALKABLE, "guard", blocks=(block,)), lib) == "no_fit"


# ---- mixed sides: only the walking mover's ground is read ---------------------------------------------------------------------------

def test_a_guard_on_unwalkable_ground_beside_a_walker_on_walkable_ground_is_ok(lib):
    guard = _group(0, "Vanguard", UNWALKABLE, "guard")
    assert scenes.preflight(_setup("Walker", WALKABLE, "move", extra=(guard,)), lib) == "ok"


def test_control_a_walker_on_unwalkable_ground_beside_a_guard_on_walkable_ground_is_no_fit(lib):
    guard = _group(0, "Vanguard", WALKABLE, "guard")
    assert scenes.preflight(_setup("Walker", UNWALKABLE, "move", extra=(guard,)), lib) == "no_fit"


def test_the_flyer_rule_needs_no_engine_argument():
    assert scenes.preflight(_setup("Vanguard", UNWALKABLE, "move"), None) == "ok"
    assert scenes.preflight(_setup("Walker", UNWALKABLE, "move"), None) == "no_fit"
