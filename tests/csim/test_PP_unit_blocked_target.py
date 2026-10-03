"""PP-unit: a blocked target does not halt the march (Architect A171, Addendum 62; E-13 R-087-05 area, E-12 R-098-02).

Ruling A171: "a unit halts for a target only when it can shoot it. ... an attack-moving unit whose held target is
blocked (cover, wall, blocked cell) keeps walking its route; it fires when the line clears; a guard unit (A170)
stays put." The ruling's source is the Phase B choke page: the last attacker stands at (1499, 690), its target in
range by distance, the engine saying the shot is blocked, "and it stays", forever. The new rule text is written by the
builder (R-087-05, reworded); these tests name R-087-05 and pin the behaviour.

Observables: om_unit_get_pos (position per tick), om_unit_get_hp of the target (it never fires back: Supply), and
om_combat_can_shoot (the scene controls assert the line really is blocked, so a red test is red for the right reason).
Terrain is hand-placed (om_map_block_rect, om_map_add_cover); routing is switched on with OM_TP_ROUTE_AROUND_TERRAIN.

Scene unit: Raider (attack range 200, speed 7.5 wu per tick), target a Supply (never fires, so it cannot change what
the attacker does). The wall is the column x 500..600, built as in test_PP_move_route.py.

Bounds: "moves" is displacement over 20 ticks of at least half of 20 ticks at full speed, a detector bound that a
unit standing still (0 wu) fails and a unit walking its route (about 150 wu) passes; it is not a rule threshold. Loop
limits (200 ticks and the like) are generous run limits so that a broken build ends.

Guard half of A171 ("a guard unit stays put") is not tested here: om_command_guard is not in this branch's header
(A170, PP-contract); it belongs to the guard stance's own tests.
"""
import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, attack_move, hp, pos, set_param, spawn, step

FRIEND, ENEMY = 0, 1
WALK_TICKS = 20
MOVES = 0.5 * WALK_TICKS * 7.5          # half of 20 ticks at full speed (detector bound, see the docstring)
HOLDS = 5.0                             # a halted unit drifts less than this over 20 ticks (detector bound)
RUN_LIMIT = 200


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    set_param(lib, w, "OM_TP_ROUTE_AROUND_TERRAIN", 1.0)
    return w


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _scene(lib, w, atk_xy, tgt_xy, goal, layer=0):
    a = spawn(lib, w, RAIDER, FRIEND, atk_xy[0], atk_xy[1], layer)
    t = spawn(lib, w, SUPPLY, ENEMY, tgt_xy[0], tgt_xy[1], layer)
    attack_move(lib, w, [a], goal[0], goal[1])
    return a, t


def _in_range_but_blocked(lib, w, a, t):
    """Scene control: the target is within attack range by distance, and the engine says the shot is blocked."""
    assert _dist(pos(lib, w, a), pos(lib, w, t)) <= 200.0
    assert lib.om_combat_can_shoot(w, a, t) == 0, "scene broken: the line to the target is not blocked"


def _walks(lib, w, a, ticks=WALK_TICKS):
    start = pos(lib, w, a)
    step(lib, w, ticks)
    return _dist(start, pos(lib, w, a))


def _full_wall(lib, w):
    """Column 5, rows 0..7 (x 500..600, y 0..800), every layer."""
    assert lib.om_map_block_rect(w, 510.0, 10.0, 590.0, 790.0, 0, 4) == 0


# ------------------------------------------------------------ the ruled behaviour

def test_R_087_05_blocked_target_behind_a_wall_does_not_halt_an_attack_move(lib, tw):
    """A171 / R-087-05: attacker (440,400), Supply (620,400) 180 wu away behind a wall that fills the column to
    y = 800. The shot is blocked; the attack-moving unit keeps walking its route (round the wall's open end) and
    its position advances over 20 ticks. Red today: it stands still holding the blocked target."""
    _full_wall(lib, tw)
    a, t = _scene(lib, tw, (440.0, 400.0), (620.0, 400.0), (900.0, 400.0))
    _in_range_but_blocked(lib, tw, a, t)
    moved = _walks(lib, tw, a)
    assert moved >= MOVES, f"blocked target halted the march: moved {moved:.2f} wu in {WALK_TICKS} ticks"


def test_R_087_05_blocked_target_with_a_gap_the_route_passes_fires_once_the_line_clears(lib, tw):
    """A171 / R-087-05: the wall fills rows 0..3 only (x 500..600, y 0..400), so there is a gap above y = 400.
    Attacker (440,300), Supply (620,300) behind the wall, goal (900,300): the route passes through the gap. The
    unit walks (does not stand still while blocked) and, once its line to the target clears, fires: the target's
    hp falls within the run limit. Red today: it stands still, the target is never shot."""
    assert lib.om_map_block_rect(tw, 510.0, 10.0, 590.0, 390.0, 0, 4) == 0
    a, t = _scene(lib, tw, (440.0, 300.0), (620.0, 300.0), (900.0, 300.0))
    _in_range_but_blocked(lib, tw, a, t)
    assert _walks(lib, tw, a) >= MOVES, "blocked target halted the march"
    hp0 = hp(lib, tw, t)
    for _ in range(RUN_LIMIT):
        step(lib, tw)
        if hp(lib, tw, t) < hp0:
            return
    pytest.fail("the unit never fired at its target after the line cleared")


def test_R_087_05_the_corner_blocked_attacker_of_the_choke_page_walks_on_into_the_gap(lib, tw):
    """A171 / the Phase B choke page: the attacker stands at the wall's west face, (1499, 690), its defender in range
    by distance (151 wu) with the shot blocked by the wall (x 1500..1600, y 0..700), and 'stays' for ever. Ruled: it
    keeps walking its route. The gap is the open ground north of y = 700; the unit is attack-moving to (1800, 690).
    It leaves the corner, is never inside a blocked cell, and is east of the wall (x > 1600) inside the run limit.
    Red today: it stands at (1499, 690) for the whole run."""
    assert lib.om_map_block_rect(tw, 1510.0, 10.0, 1590.0, 690.0, 0, 4) == 0
    a, t = _scene(lib, tw, (1499.0, 690.0), (1650.0, 690.0), (1800.0, 690.0))
    _in_range_but_blocked(lib, tw, a, t)
    assert _walks(lib, tw, a) >= MOVES, "the corner-blocked attacker stood still"
    for _ in range(RUN_LIMIT):
        step(lib, tw)
        x, y = pos(lib, tw, a)
        assert not (1500.0 <= x < 1600.0 and y < 700.0), f"inside the wall at ({x:.1f}, {y:.1f})"
        if x > 1600.0:
            return
    pytest.fail("the attacker never got round the wall")


def test_R_087_05_cover_disc_blocks_fire_the_same_way_and_the_unit_walks_on(lib, tw):
    """A171 / R-098-02: a cover disc (tall, reaches the unit's layer) between attacker and target blocks the shot as a
    wall does; the attack-moving unit walks its route. Attacker (400,400) layer 1, disc r 20 at (500,400) height 5,
    Supply (580,400). Red today: stands still."""
    lib.om_map_add_cover(tw, 500.0, 400.0, 20.0, 5.0)
    a, t = _scene(lib, tw, (400.0, 400.0), (580.0, 400.0), (900.0, 700.0), layer=1)
    _in_range_but_blocked(lib, tw, a, t)
    assert _walks(lib, tw, a) >= MOVES, "a cover-blocked target halted the march"


# ------------------------------------------------------------ positive controls (today's behaviour, must stay)

def test_R_087_05_control_unblocked_target_in_range_still_halts_and_fires(lib, tw):
    """Control: no terrain. Attacker (400,400) attack-moving to (900,400), Supply (550,400) in range, line clear: the
    unit halts (stops advancing) and fires (hp falls). Green today and after."""
    a, t = _scene(lib, tw, (400.0, 400.0), (550.0, 400.0), (900.0, 400.0))
    hp0 = hp(lib, tw, t)
    assert lib.om_combat_can_shoot(tw, a, t) == 1
    step(lib, tw, 10)
    assert _walks(lib, tw, a) <= HOLDS, "an unblocked target in range did not halt the unit"
    assert hp(lib, tw, t) < hp0, "an unblocked target in range was not fired at"


def test_R_087_05_control_unit_standing_in_cover_is_shot_and_the_attacker_halts(lib, tw):
    """Control, the endpoint exemption (E-01 R-007-06): the Supply stands INSIDE the cover disc (r 20 at (500,400),
    target at (510,400)); the line is not blocked, the unit halts and fires as normal."""
    lib.om_map_add_cover(tw, 500.0, 400.0, 20.0, 5.0)
    a, t = _scene(lib, tw, (400.0, 400.0), (510.0, 400.0), (900.0, 700.0), layer=1)
    hp0 = hp(lib, tw, t)
    assert lib.om_combat_can_shoot(tw, a, t) == 1, "scene broken: endpoint exemption does not hold"
    step(lib, tw, 10)
    assert _walks(lib, tw, a) <= HOLDS, "a target standing in cover did not halt the unit"
    assert hp(lib, tw, t) < hp0, "a target standing in cover was not fired at"


def test_R_087_05_control_plain_move_is_unchanged_by_a_blocked_enemy(lib, world_factory):
    """Control: a plain-moving unit never halts for an enemy. The same walk, in two worlds, one with the blocked
    enemy and one without, gives the identical position trace tick for tick. Green today and after."""
    traces = []
    for with_enemy in (False, True):
        w = world_factory(n_regions=1)
        lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
        assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
        set_param(lib, w, "OM_TP_ROUTE_AROUND_TERRAIN", 1.0)
        _full_wall(lib, w)
        a = spawn(lib, w, RAIDER, FRIEND, 440.0, 400.0)
        if with_enemy:
            spawn(lib, w, SUPPLY, ENEMY, 620.0, 400.0)
        lib.om_command_move(w, a, 900.0, 400.0)
        trace = []
        for _ in range(WALK_TICKS):
            step(lib, w)
            trace.append(pos(lib, w, a))
        traces.append(trace)
    assert traces[0] == traces[1]
    assert _dist(traces[0][0], traces[0][-1]) >= MOVES, "control scene broken: the plain mover did not walk"
