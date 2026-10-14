# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md ruling 6 (contact architecture), rulings 1 and 5, piece LAB-REV2-L2; Q-LAB-03
"""Contact through the production library: the stall scene eliminates, an assault onto the holder's centre of mass eliminates,
and the pre-flight refuses a cell that cannot be fought (`no_fit`, `unroutable`, `no_reach`) before any tick.

The spec names the three refusals and the CSV column `prefight` but no function that computes them. Fixed here, and flagged to the
overseer (the builder must match, or the test writer is told):
    scenes.preflight(setup, engine) -> "ok" | "no_fit" | "unroutable" | "no_reach"
It reads the Setup as built (placed unit positions, terrain, layers, orders, `point`, the registered types' reach) against the
engine, runs no tick, and does not shift anything. `placed_scene` records the same value in build.labels["prefight"] (see
test_placed_by_feature.py). Every use of the name is in `_preflight` below.

Per-unit orders (`Setup.orders_per_unit`, default True) are what makes the stall scene end today: on the engine as it is on main a
group attack-move ends after the group's first engagement (R-096-02, rewritten 2026-10-13; LAB-REV2-E1), a single unit's does not.
Needs LAB-REV2-L1's firing.py as well as L2 for the fights to run: fight() reads the counts through the L1/L2 seam."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, scenes  # noqa: E402
from scripts.skilllab.contract import Block, Group, Setup, Terrain  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

ELIMINATED = ("side0", "side1", "draw")
RAIDER_REACH = {"RaiderR": {"base": "Raider", "reach": (1, 1)}}      # Raider: reach one up, one down (spec roster mix M1)


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _preflight(setup, library):
    return scenes.preflight(setup, library)


def _blob(side, unit, count, x, y, order="attack_move", layer=0, goal=None):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=0.0 if side == 0 else 180.0,
                 layer=layer, order=order, goal=goal, params={"radius": 80 + 12 * math.sqrt(count)})


def _centroid(groups):
    pts = [p for g in groups for p in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def stall_scene(**over):
    """8 Vanguards and 8 Raiders per side, the two blobs 600 wu apart, both sides attack-moved to the midpoint (2026-10-13)."""
    groups = tuple(_blob(side, unit, 8, -300.0 if side == 0 else 300.0, y)
                   for side in (0, 1) for unit, y in (("Vanguard", -70.0), ("Raider", 70.0)))
    return Setup(groups=groups, unit_types={}, point=(0.0, 0.0), **over)


def assault_scene(attackers=16, holders=8):
    """The attacker attack-moved onto the holder's centre of mass (the mean of the holder's placed positions) while the holder guards."""
    holder = _blob(1, "Vanguard", holders, 700.0, 0.0, order="guard")
    centroid = _centroid([holder])
    return Setup(groups=(_blob(0, "Vanguard", attackers, -700.0, 0.0), holder), unit_types={}, point=centroid)


# ---------------------------------------------------------------- the fights

def test_the_stall_scene_eliminates_under_per_unit_orders(library):
    """Ruling 6 / E1 stall scene: 16 v 16, blobs 600 apart, both attack-moved to the midpoint, one order per unit: the fight ends
    by elimination. Red on main: Setup has no `point` or `orders_per_unit`; and the group order stalled at 303 to 336 wu."""
    setup = stall_scene(orders_per_unit=True)
    r = fight(setup, 0, False, engine=library)
    assert r.outcome in ELIMINATED, (r.outcome, r.ticks)
    assert r.first_contact_tick > 0 and r.ticks < setup.max_ticks


def test_the_stall_scene_eliminates_whichever_side_spawns_first(library):
    """Control for the symmetry of the result path: the swapped spawn order also ends by elimination."""
    r = fight(stall_scene(orders_per_unit=True), 1, True, engine=library)
    assert r.outcome in ELIMINATED, (r.outcome, r.ticks)


def test_the_stall_scene_scores_its_prediction_against_the_survivor(library):
    """Ruling 5: an eliminated fight carries a winner (None for a draw), both predictions and an agreement label."""
    r = fight(stall_scene(orders_per_unit=True), 0, False, engine=library)
    assert r.agreement in ("both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a")
    assert r.predicted_count in ("side0", "side1", "tie") and r.predicted_type in ("side0", "side1", "tie")
    assert r.winner == (r.outcome if r.outcome in ("side0", "side1") else None)
    assert (r.agreement == "n/a") == (r.outcome == "draw" or "tie" in (r.predicted_count, r.predicted_type))


def test_a_holder_on_guard_with_the_attacker_aimed_at_its_centroid_eliminates(library):
    """Ruling 6: an assault: the holder guards (never steps), the attacker is attack-moved onto the holder's centre of mass and
    resumes after every engagement, so the fight ends by elimination."""
    setup = assault_scene()
    r = fight(setup, 0, False, engine=library)
    assert r.outcome in ELIMINATED, (r.outcome, r.ticks)
    assert r.first_contact_tick > 0 and r.ticks < setup.max_ticks


# ---------------------------------------------------------------- the pre-flight refusals

def test_a_fitting_same_layer_scene_is_ok_control(library):
    """Control: the stall scene and the assault scene, both fitting, same layer, open ground: 'ok'."""
    assert _preflight(stall_scene(), library) == "ok"
    assert _preflight(assault_scene(), library) == "ok"


def _into_canvas(setup, terrain):
    """The assault scene moved by (1500, 800) so that it lies inside a 3000 x 1600 canvas, with `terrain`."""
    groups = tuple(Group(**{**g.__dict__, "x": g.x + 1500.0, "y": g.y + 800.0}) for g in setup.groups)
    return Setup(groups=groups, unit_types=dict(setup.unit_types), point=(setup.point[0] + 1500.0, setup.point[1] + 800.0),
                 terrain=terrain)


CANVAS = (3000.0, 1600.0)


def test_a_formation_on_a_blocked_cell_is_refused_no_fit(library):
    """Spec L2: a placed point inside a blocked cell: 'no_fit', and no shifting. The holder blob (radius about 114 about
    (2200, 800)) has a block over its centre; the same scene without the block is 'ok'."""
    holder_block = Block(2150.0, 740.0, 2250.0, 860.0, 0, 4)
    assert _preflight(_into_canvas(assault_scene(), Terrain(canvas=CANVAS, blocks=(holder_block,))), library) == "no_fit"
    assert _preflight(_into_canvas(assault_scene(), Terrain(canvas=CANVAS)), library) == "ok"


def test_no_fit_applies_to_the_attacker_too(library):
    """The attacker blob (about (800, 800), radius about 128) with a 200 wu block over its middle is refused as well."""
    attacker_block = Block(700.0, 700.0, 900.0, 900.0, 0, 4)
    assert _preflight(_into_canvas(assault_scene(), Terrain(canvas=CANVAS, blocks=(attacker_block,))), library) == "no_fit"


def test_a_block_on_other_layers_is_not_a_misfit(library):
    """Control: the block over the holder covers layers 2 to 4 only; the holder stands on layer 0: 'ok'."""
    other_layers = Block(2150.0, 740.0, 2250.0, 860.0, 2, 4)
    assert _preflight(_into_canvas(assault_scene(), Terrain(canvas=CANVAS, blocks=(other_layers,))), library) == "ok"


def _cross_layer(attacker_unit, holder_layer, types=None):
    """A guard holder on `holder_layer`, an attacker blob on layer 0 attack-moved to the holder's centre of mass."""
    holder = _blob(1, "Vanguard", 8, 700.0, 0.0, order="guard", layer=holder_layer)
    attackers = (_blob(0, attacker_unit, 8, -700.0, 0.0),) if isinstance(attacker_unit, str) else \
        tuple(_blob(0, u, 4, -700.0, y) for u, y in zip(attacker_unit, (-80.0, 80.0)))
    return Setup(groups=attackers + (holder,), unit_types=dict(types or {}), point=_centroid([holder]))


def test_a_cross_layer_scene_whose_types_cannot_fire_at_the_offset_is_refused_no_reach(library):
    """Spec L2: no attacker type's reach covers the holder's offset. Vanguards have reach (0, 0): the holder two layers up is out
    of reach; so is a Raider with reach (1, 1) against a holder two layers up."""
    assert _preflight(_cross_layer("Vanguard", 2), library) == "no_reach"
    assert _preflight(_cross_layer("RaiderR", 2, RAIDER_REACH), library) == "no_reach"
    assert _preflight(_cross_layer("RaiderR", 3, RAIDER_REACH), library) == "no_reach"


def test_one_attacker_type_that_reaches_is_enough_so_the_scene_is_ok(library):
    """Control: 'no attacker type's reach covers' means every type fails. A mix of Vanguards (cannot) and Raiders with reach one up
    (can) against a holder one layer up is ok; a Raider against a holder one layer DOWN is ok too (reach one down)."""
    assert _preflight(_cross_layer(("Vanguard", "RaiderR"), 1, RAIDER_REACH), library) == "ok"
    assert _preflight(_cross_layer("RaiderR", 1, RAIDER_REACH), library) == "ok"


def test_the_offset_is_relative_to_the_attackers_layer(library):
    """Reach is up and down from the attacker: a Raider (1, 1) on layer 2 reaches a holder on layer 3 and one on layer 1."""
    for holder_layer in (1, 3):
        holder = _blob(1, "Vanguard", 8, 700.0, 0.0, order="guard", layer=holder_layer)
        setup = Setup(groups=(_blob(0, "RaiderR", 8, -700.0, 0.0, layer=2), holder), unit_types=dict(RAIDER_REACH),
                      point=_centroid([holder]))
        assert _preflight(setup, library) == "ok", holder_layer
    far = Setup(groups=(_blob(0, "RaiderR", 8, -700.0, 0.0, layer=2),
                        _blob(1, "Vanguard", 8, 700.0, 0.0, order="guard", layer=0)), unit_types=dict(RAIDER_REACH), point=(700.0, 0.0))
    assert _preflight(far, library) == "no_reach"


def _wall_scene(blocks):
    """Attackers at x = 300 and the point at x = 2700, both on y = 800; a wall at x = 1400..1600 between them."""
    holder = _blob(1, "Vanguard", 8, 2700.0, 800.0, order="guard")
    return Setup(groups=(_blob(0, "Vanguard", 8, 300.0, 800.0), holder), unit_types={}, point=_centroid([holder]),
                 terrain=Terrain(canvas=(3000.0, 1600.0), blocks=tuple(blocks)))


def test_an_unroutable_scene_is_refused_unroutable(library):
    """Spec L2: no path from the attackers to the point on their layer: a wall across the whole canvas, every layer."""
    assert _preflight(_wall_scene([Block(1400.0, 0.0, 1600.0, 1600.0, 0, 4)]), library) == "unroutable"


def test_a_wall_with_a_gap_on_the_line_is_routable_control(library):
    """Control: the same wall with a 200 wu gap at y = 700..900 (the phase B choke), on the straight line between the attackers
    and the point: 'ok'."""
    gap = [Block(1400.0, 0.0, 1600.0, 700.0, 0, 4), Block(1400.0, 900.0, 1600.0, 1600.0, 0, 4)]
    assert _preflight(_wall_scene(gap), library) == "ok"


def test_a_wall_on_other_layers_does_not_stop_a_scene_on_layer_zero(library):
    """Control: the wall blocks layers 2 to 4 only; the attackers and the point are on layer 0: 'ok' (routes are per layer)."""
    assert _preflight(_wall_scene([Block(1400.0, 0.0, 1600.0, 1600.0, 2, 4)]), library) == "ok"


def test_the_preflight_runs_no_tick_and_does_not_move_a_unit(library):
    """The pre-flight is a read of the Setup: calling it twice gives the same answer and leaves the Setup equal to a copy."""
    setup = _wall_scene([Block(1400.0, 0.0, 1600.0, 1600.0, 0, 4)])
    again = _wall_scene([Block(1400.0, 0.0, 1600.0, 1600.0, 0, 4)])
    assert _preflight(setup, library) == _preflight(setup, library) == "unroutable"
    assert setup == again
