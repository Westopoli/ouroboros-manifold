# Rule pins: R-096-02@e8ae96, R-099-05@ea8d02
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md ruling 6 (contact architecture), rulings 1 and 5, piece LAB-REV2-L2; Q-LAB-03
"""Contact through the production library: the stall scene eliminates, an assault onto the holder's centre of mass eliminates,
and the pre-flight refuses a cell that cannot be fought (`no_fit`, `unroutable`, `no_reach`) before any tick.

The spec names the three refusals and the CSV column `prefight` but no function that computes them. Fixed here, and flagged to the
overseer (the builder must match, or the test writer is told):
    scenes.preflight(setup, engine) -> "ok" | "no_fit" | "unroutable" | "no_reach"
It reads the Setup as built (placed unit positions, terrain, layers, orders, `point`, the registered types' reach) against the
engine, runs no tick, and does not shift anything. `placed_scene` records the same value in build.labels["prefight"] (see
test_placed_by_feature.py). Every use of the name is in `_preflight` below.

Per-unit orders (`Setup.orders_per_unit`, default True) are what makes the stall scene end: after E1 (R-096-02, rewritten 2026-10-13) a
group attack-move resumes toward its point after every engagement, and a unit that gives up under R-099-05 ends where it stands.
Needs LAB-REV2-L1's firing.py as well as L2 for the fights to run: fight() reads the counts through the L1/L2 seam."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, maps, plays_space, scenes  # noqa: E402
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


# ---------------------------------------------------------------- audit fixes (D9): asymmetric reach, several groups, the label, precedence

PLAYS_PLACED = ["s1_hold_choke", "s1_outrange", "s2_concave", "s2_spread_line", "s2_screen", "s3_layer_above", "s3_types_by_reach",
                "s3_over_the_choke", "s3_dark_striker", "s3_ping_then_commit", "s4_bait", "s5_vulnerable_away", "s2_mass_one_end",
                "s4_do_not_chase", "naive"]       # as in test_placed_by_feature.py
UP_REACH = {"UpR": {"base": "Interceptor", "reach": (2, 0)}}       # reaches two layers up, none down
DOWN_REACH = {"DownR": {"base": "Bombard", "reach": (0, 2)}}       # reaches two layers down, none up (spec roster mix M3)


def _holder_at(layer, x=700.0, y=0.0):
    return _blob(1, "Vanguard", 8, x, y, order="guard", layer=layer)


def _reach_scene(unit, types, attacker_layer, holder_layer):
    holder = _holder_at(holder_layer)
    return Setup(groups=(_blob(0, unit, 8, -700.0, 0.0, layer=attacker_layer), holder), unit_types=dict(types), point=_centroid([holder]))


@pytest.mark.parametrize("holder_layer,expected", [(0, "ok"), (1, "ok"), (2, "ok"), (3, "no_reach"), (4, "no_reach")])
def test_an_attacker_that_reaches_two_down_covers_the_layers_below_it_and_not_above(library, holder_layer, expected):
    """Reach (up, down) is read in its own direction: a (0, 2) type on layer 2 reaches layers 2, 1 and 0 and not 3 or 4."""
    assert _preflight(_reach_scene("DownR", DOWN_REACH, 2, holder_layer), library) == expected


@pytest.mark.parametrize("holder_layer,expected", [(0, "no_reach"), (1, "no_reach"), (2, "ok"), (3, "ok"), (4, "ok")])
def test_an_attacker_that_reaches_two_up_covers_the_layers_above_it_and_not_below(library, holder_layer, expected):
    """The mirror: a (2, 0) type on layer 2 reaches layers 2, 3 and 4 and not 1 or 0 (so a swap of up and down is caught)."""
    assert _preflight(_reach_scene("UpR", UP_REACH, 2, holder_layer), library) == expected


def _pocket_walls(door):
    """A ring of walls 100 wu thick round the box x 150..450, y 650..950, every layer. `door` opens a 100 wu gap in the right wall."""
    right = [Block(450.0, 650.0, 550.0, 750.0, 0, 4), Block(450.0, 850.0, 550.0, 950.0, 0, 4)] if door else \
        [Block(450.0, 650.0, 550.0, 950.0, 0, 4)]
    return [Block(50.0, 550.0, 550.0, 650.0, 0, 4), Block(50.0, 950.0, 550.0, 1050.0, 0, 4), Block(50.0, 650.0, 150.0, 950.0, 0, 4)] + right


def _pocket_scene(sealed_first, door=False, with_pocket_group=True):
    """Two attacker groups and a guarding holder at (2700, 800): one attacker blob inside the walled box at (300, 800), one in the open
    at (300, 250). `sealed_first` puts the boxed group first or second in Setup.groups."""
    boxed = _blob(0, "Vanguard", 8, 300.0, 800.0)
    free = _blob(0, "Vanguard", 8, 300.0, 250.0)
    holder = _blob(1, "Vanguard", 8, 2700.0, 800.0, order="guard")
    attackers = ((boxed, free) if sealed_first else (free, boxed)) if with_pocket_group else (free,)
    return Setup(groups=attackers + (holder,), unit_types={}, point=_centroid([holder]),
                 terrain=Terrain(canvas=(3000.0, 1600.0), blocks=tuple(_pocket_walls(door))))


@pytest.mark.parametrize("sealed_first", [True, False])
def test_one_sealed_attacker_group_among_several_makes_the_scene_unroutable(library, sealed_first):
    """Spec L2: 'no path from EACH attacker': the boxed group cannot leave, whether it is listed first or last (a check of the first
    attacker group only, or of any one routable group, passes one of the two orders)."""
    assert _preflight(_pocket_scene(sealed_first), library) == "unroutable"


@pytest.mark.parametrize("sealed_first", [True, False])
def test_the_same_pocket_with_a_door_is_routable_control(library, sealed_first):
    assert _preflight(_pocket_scene(sealed_first, door=True), library) == "ok"


def test_the_walls_alone_do_not_make_a_scene_unroutable_control(library):
    """Control: the same walls with no group inside them (only the open attacker group) are 'ok'."""
    assert _preflight(_pocket_scene(True, with_pocket_group=False), library) == "ok"


def test_a_meeting_has_no_holder_so_it_is_never_no_reach(library):
    """Spec: no `no_reach` for a meeting (no group on guard). Side 0 on layer 0 and side 1 on layer 4, both attack-moved to a point
    on open ground, Vanguards (reach 0, 0): 'ok'. Control: the same sides with side 1 on guard are refused 'no_reach'."""
    meeting = Setup(groups=(_blob(0, "Vanguard", 8, -700.0, 0.0), _blob(1, "Vanguard", 8, 700.0, 0.0, layer=4)), unit_types={},
                    point=(0.0, 0.0))
    assert _preflight(meeting, library) == "ok"
    holder = _holder_at(4)
    assault = Setup(groups=(_blob(0, "Vanguard", 8, -700.0, 0.0), holder), unit_types={}, point=_centroid([holder]))
    assert _preflight(assault, library) == "no_reach"


def test_several_holders_one_reachable_holder_is_enough_so_the_scene_is_ok(library):
    """Reading of 'the holder is any group with order guard': the scene is `no_reach` only when no attacker type reaches ANY holder
    (the placed s3 scene stands a Vanguard-High group on layer 1 beside Vanguards on layer 0, against Vanguard attackers on layer 0,
    and is a fightable scene). Holders on layers 0 and 1 against Vanguards on layer 0: ok. Holders on layers 1 and 2: no_reach."""
    def two_holders(layers):
        holders = tuple(_blob(1, "Vanguard", 4, 700.0, y, order="guard", layer=l) for l, y in zip(layers, (-90.0, 90.0)))
        return Setup(groups=(_blob(0, "Vanguard", 8, -700.0, 0.0),) + holders, unit_types={}, point=_centroid(list(holders)))
    assert _preflight(two_holders((0, 1)), library) == "ok"
    assert _preflight(two_holders((1, 0)), library) == "ok"
    assert _preflight(two_holders((1, 2)), library) == "no_reach"


def _precedence_scene(wall, holder_block, holder_layer):
    """Vanguard attackers on layer 0 at x = 300, a guarding holder on `holder_layer` at x = 2700. `wall` closes the canvas between
    them on every layer; `holder_block` is a block over the holder's formation on every layer."""
    holder = _blob(1, "Vanguard", 8, 2700.0, 800.0, order="guard", layer=holder_layer)
    blocks = ([Block(1400.0, 0.0, 1600.0, 1600.0, 0, 4)] if wall else []) + ([Block(2650.0, 750.0, 2750.0, 850.0, 0, 4)] if holder_block else [])
    return Setup(groups=(_blob(0, "Vanguard", 8, 300.0, 800.0), holder), unit_types={}, point=_centroid([holder]),
                 terrain=Terrain(canvas=(3000.0, 1600.0), blocks=tuple(blocks)))


@pytest.mark.parametrize("wall,holder_block,holder_layer,expected", [
    # each refusal alone (controls: the scene builder produces each answer)
    (False, True, 0, "no_fit"), (True, False, 0, "unroutable"), (False, False, 2, "no_reach"), (False, False, 0, "ok"),
    # precedence: no_fit, then unroutable, then no_reach
    (True, True, 0, "no_fit"), (False, True, 2, "no_fit"), (True, False, 2, "unroutable"), (True, True, 2, "no_fit"),
])
def test_refusal_precedence_is_no_fit_then_unroutable_then_no_reach(library, wall, holder_block, holder_layer, expected):
    assert _preflight(_precedence_scene(wall, holder_block, holder_layer), library) == expected


def _features(choke=4, lane=1, cover=0.1, sd=1400.0):
    return maps.Features(choke_count=1 if choke else 0, choke_width_wu=choke * maps.LAYOUT_BODY_WU, choke_width_bodies=float(choke),
                         lane_count=lane, blocked_layer_ranges=(), fight_layer_blocked=False, cover_density_corridor=cover,
                         start_distance=sd, detour_ratio=0.0, blocked_layer_top=4)


def test_the_placed_scene_label_is_the_preflight_of_the_setup_it_built(library):
    """Decision: build.labels["prefight"] is set by placed_scene on every build, and is scenes.preflight of that Setup. Read for
    every play on an open layout, on a choke layout with a lane and on an open layout with a block laid over the hold; the blocked
    layout is also the control that the label is not always 'ok'."""
    import dataclasses
    seen = set()
    open_f = _features(choke=0, lane=0, cover=0.0)
    open_layout = maps.layout_map(open_f, 7)
    blocked = dataclasses.replace(open_layout, blocks=open_layout.blocks + (Block(-100.0, -100.0, 100.0, 100.0, 0, 4),))
    choke_f = _features()
    cases = [(open_layout, open_f), (blocked, open_f), (maps.layout_map(choke_f, 7), choke_f)]
    for layout, f in cases:
        for play in PLAYS_PLACED:
            build = scenes.placed_scene(layout, play, f.start_distance, f)
            setup = build(16, False)
            assert build.labels["prefight"] == _preflight(setup, library), play
            seen.add(build.labels["prefight"])
    assert {"ok", "no_fit"} <= seen


def test_the_label_follows_the_latest_build(library):
    """'On every build': the same build function called again with other arguments refreshes the label to that Setup's pre-flight."""
    f = _features(choke=0, lane=0, cover=0.0)
    build = scenes.placed_scene(maps.layout_map(f, 7), "s1_hold_choke", f.start_distance, f)
    for heads, swap in ((16, False), (8, True), (24, False)):
        setup = build(heads, swap)
        assert build.labels["prefight"] == _preflight(setup, library), (heads, swap)
