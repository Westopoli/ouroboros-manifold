"""PP-move rule tests, collision, arrival and map clamp.

Proves E-13 R-097-05, R-097-10 (the stationary-pair rule, renumbered from the second R-097-10 by A158), R-099-04
(S-097, S-099) and the P3 clamp part (plan Phase A row P3, `om_map_set_canvas`), as reworded by
Addendum 45 (docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md, rows "Collision" and P3).
The reference is simulation/movement.py 566-690 (collision) and 331-360 (arrival).

NOT tested, on purpose: two units on exactly the same spot (R-097-07). The Python throws them apart by a
thousand times the normal push; that case is Q-097-02, held for Westley. No scene below places two units
on one point.

The second sentence of R-097-10, "given both are stationary and either was displaced earlier in the tick, they
split the displacement equally", is read under the A153 rule (every unit, moving or stopped, starts pair checks):
see test_R_097_10_a_stopped_unit_starts_a_pair_check (test-defect, A155 to A159).

Scenes avoid the cheap-trig drift of the C (a step is 5e-5 wu short): positions are compared with
POS_TOL, which is numeric slack, not a rule threshold.
"""
import ctypes
import math

import pytest

from conftest import OMFeature

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = 0, 1, 2, 3, 4, 5
SUPPLY = 6  # never fires: an idle ENEMY of the mover that stays idle (R-097-10: only an enemy idle unit takes 0 from a mover)
FRIEND, ENEMY = 0, 1
POS_TOL = 0.05
COLLISION_DIAMETER = 30.0  # 2 x radius 15


@pytest.fixture
def tw(lib, world_factory):
    """A world with the tactical feature on. Files named test_PP_* get no epic isolation set."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _arr(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def _has_dest(lib, w, u):
    """1 when the unit still has a destination (the wrapped getter drops this flag; use the raw call)."""
    x, y = ctypes.c_double(), ctypes.c_double()
    return lib.om_unit_get_destination.raw(w, u, ctypes.byref(x), ctypes.byref(y))


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


# ---------------------------------------------------------------- pair pushes (R-097-05, R-097-10)

def test_R_097_05_two_moving_units_split_the_push_to_30_apart(lib, tw):
    """R-097-05 / R-097-10 (both moving): two same-layer units that overlap after the move are pushed apart along
    the line between them until 30 wu apart, half each. A (100,0) and B (100,20) both go +x: after the step both
    are at x 107.5, 20 apart, so each gives 5 wu along y: A (107.5,-5), B (107.5,25). Their straight probes are
    clear (44.7 from the other's start), so no steering enters. Green today; stays green."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 20.0, 0)
    lib.om_command_move(tw, a, 1000.0, 0.0)
    lib.om_command_move(tw, b, 1000.0, 20.0)
    lib.om_tactical_step(tw)
    pa, pb = lib.om_unit_get_pos(tw, a), lib.om_unit_get_pos(tw, b)
    assert _dist(pa, pb) == pytest.approx(COLLISION_DIAMETER, abs=POS_TOL)
    assert pa == pytest.approx((107.5, -5.0), abs=POS_TOL)
    assert pb == pytest.approx((107.5, 25.0), abs=POS_TOL)


def test_R_097_10_stationary_unit_takes_no_push_mover_takes_all(lib, tw):
    """R-097-10 (one stationary): "... Then it moves 0 and the other takes the full displacement, except that an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side and
    none from an enemy mover, which takes all of it". A unit with no move target takes 0 from an ENEMY mover, which takes the full displacement.
    M (id 1, the lower id so it starts the pair check) at (100,0) goes -x, 7.5 wu to (92.5,0), 17.5 from the idle ENEMY
    S (a Supply, which never fires) at (110,0); it is pushed back to 30 from S, i.e. to (80,0), and S has not moved at all.
    Test-defect (engine rules round 4, T10): S was a unit of M's own side, the reading R-097-10's rewrite replaced (an idle own unit now takes the push); the own-side twin is
    tests/csim/test_E13_R097_10_idle_own_units_yield.py."""
    m = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 0.0, 0)
    s = lib.om_unit_spawn(tw, SUPPLY, ENEMY, 110.0, 0.0, 0)
    lib.om_command_move(tw, m, -1000.0, 0.0)
    lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, s) == (110.0, 0.0), "a stationary unit was pushed"
    pm = lib.om_unit_get_pos(tw, m)
    assert pm == pytest.approx((80.0, 0.0), abs=POS_TOL)
    assert _dist(pm, (110.0, 0.0)) == pytest.approx(COLLISION_DIAMETER, abs=POS_TOL)


def test_R_097_10_a_stopped_unit_starts_a_pair_check(lib, tw):
    """R-097-10 (A153: every unit, moving or stopped, starts pair checks; was: only moved units did): two idle units
    20 wu apart, nobody moving this tick, are pushed apart equally (two stopped units split the push) to 30 wu:
    (95,0) and (125,0). Companion to the mover test above, which pushes the mover with the other unit idle."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 120.0, 0.0, 0)
    for _ in range(3):
        lib.om_tactical_step(tw)
    pa, pb = lib.om_unit_get_pos(tw, a), lib.om_unit_get_pos(tw, b)
    assert pa == pytest.approx((95.0, 0.0), abs=POS_TOL)
    assert pb == pytest.approx((125.0, 0.0), abs=POS_TOL)
    assert _dist(pa, pb) == pytest.approx(COLLISION_DIAMETER, abs=POS_TOL)


def test_R_097_05_other_layer_units_do_not_collide(lib, tw):
    """R-097-05: same-layer pairs only. M at (100,0) on layer 0 goes -x over an idle unit on layer 1 at (110,0):
    no push, M simply ends its step at (92.5,0). Control: the same scene with S on layer 0 is the stationary-pair
    test above, where M ends at (80,0)."""
    m = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 0.0, 0)
    s = lib.om_unit_spawn(tw, RAIDER, FRIEND, 110.0, 0.0, 1)
    lib.om_command_move(tw, m, -1000.0, 0.0)
    lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, m) == pytest.approx((92.5, 0.0), abs=POS_TOL)
    assert lib.om_unit_get_pos(tw, s) == (110.0, 0.0)


# ---------------------------------------------------------------- arrival (R-099-04)

def _two_unit_group(lib, w):
    """A at (0,0), B at (0,100), group-moved to click (1000,50): slots A (1000,0), B (1000,100)."""
    a = lib.om_unit_spawn(w, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(w, RAIDER, FRIEND, 0.0, 100.0, 0)
    assert lib.om_command_group_move(w, _arr([a, b]), 2, 1000.0, 50.0) != 0
    assert lib.om_unit_get_destination(w, a) == (1000.0, 0.0), "scene error: unexpected slot"
    return a, b


def test_R_099_04_within_slot_radius_arrives_where_it_stands(lib, tw):
    """R-099-04: a unit within its arrival radius (1.5 x collision radius = 22.5 wu for a formation slot) has arrived
    where it stands, without snapping to the point: its destination is cleared and it is stationary from then on.
    A is put 20 wu short of its slot (980,0); after a tick it is still at (980,0), has no destination, speed 0.
    (The C moves it on and snaps it to (1000,0).)"""
    a, _b = _two_unit_group(lib, tw)
    lib.om_unit_set_pos(tw, a, 980.0, 0.0)
    lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, a) == (980.0, 0.0), "arrived unit moved or snapped"
    assert _has_dest(lib, tw, a) == 0, "arrived unit kept its destination"
    assert lib.om_unit_get_current_speed(tw, a) == 0.0


def test_R_099_04_outside_slot_radius_keeps_approaching_control(lib, tw):
    """Positive control for the arrival test: A 25 wu short of its slot (975,0), outside 22.5, has not arrived: it
    keeps its destination and moves 7.5 wu closer. Green today and must stay green."""
    a, _b = _two_unit_group(lib, tw)
    lib.om_unit_set_pos(tw, a, 975.0, 0.0)
    lib.om_tactical_step(tw)
    assert _has_dest(lib, tw, a) == 1
    assert lib.om_unit_get_pos(tw, a)[0] == pytest.approx(982.5, abs=POS_TOL)


def test_R_099_04_displaced_after_arrival_does_not_re_approach(lib, tw):
    """R-099-04: any later displacement (collision or a direct position change) leaves an arrived unit at the new
    position with no re-approach. A arrives at (980,0), is then moved to (900,0): after more ticks it is still at
    (900,0) with no destination."""
    a, _b = _two_unit_group(lib, tw)
    lib.om_unit_set_pos(tw, a, 980.0, 0.0)
    lib.om_tactical_step(tw)
    assert _has_dest(lib, tw, a) == 0, "R-099-04: A within the slot radius did not arrive"
    lib.om_unit_set_pos(tw, a, 900.0, 0.0)
    for _ in range(4):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, a) == (900.0, 0.0), "arrived unit walked back to its slot"
    assert _has_dest(lib, tw, a) == 0


# ---------------------------------------------------------------- map clamp (P3, om_map_set_canvas)

CANVAS_W, CANVAS_H = 2000.0, 1000.0


def test_P3_set_canvas_contract(lib, tw):
    """Plan appendix: `int om_map_set_canvas(om_world *w, double width, double height)`: 0 ok; -1 on a non-positive
    size. Red until PP-contract lands the call."""
    assert lib.om_map_set_canvas(tw, 0.0, 100.0) == -1
    assert lib.om_map_set_canvas(tw, 100.0, -5.0) == -1
    assert lib.om_map_set_canvas(tw, CANVAS_W, CANVAS_H) == 0


@pytest.mark.parametrize("name,start,dest,axis,edge", [
    ("right_edge", (1995.0, 500.0), (3000.0, 500.0), 0, CANVAS_W),
    ("left_edge", (5.0, 500.0), (-1000.0, 500.0), 0, 0.0),
    ("top_edge", (500.0, 995.0), (500.0, 3000.0), 1, CANVAS_H),
    ("bottom_edge", (500.0, 5.0), (500.0, -1000.0), 1, 0.0),
])
def test_P3_positions_are_clamped_to_the_canvas(lib, tw, name, start, dest, axis, edge):
    """P3 clamp (Python movement.py 457-459): a unit ordered past the map edge stops at the edge; its position
    never leaves [0, width] x [0, height]. After 3 ticks (22.5 wu of travel, edge 5 wu away) the coordinate on
    the clamped axis equals the edge exactly."""
    assert lib.om_map_set_canvas(tw, CANVAS_W, CANVAS_H) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, start[0], start[1], 0)
    lib.om_command_move(tw, u, dest[0], dest[1])
    for _ in range(3):
        lib.om_tactical_step(tw)
        x, y = lib.om_unit_get_pos(tw, u)
        assert 0.0 <= x <= CANVAS_W and 0.0 <= y <= CANVAS_H, f"{name}: left the canvas at ({x}, {y})"
    assert lib.om_unit_get_pos(tw, u)[axis] == edge


def test_P3_clamp_positive_control_inside_the_canvas_is_untouched(lib, tw):
    """Positive control for the clamp detector: a unit well inside the canvas moves its full 7.5 wu per tick."""
    assert lib.om_map_set_canvas(tw, CANVAS_W, CANVAS_H) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 500.0, 500.0, 0)
    lib.om_command_move(tw, u, 1500.0, 500.0)
    for _ in range(3):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, u)[0] == pytest.approx(522.5, abs=POS_TOL)


def test_P3_collision_push_is_clamped_to_the_canvas(lib, tw):
    """P3 (Python _resolve_collisions, clamps new_ax/new_bx to the map): a push never carries a unit off the
    map. Idle ENEMY S (a Supply) at (510,15); M at (500,3) goes +x to (507.5,3), 12.3 from S, and is pushed along the line from S,
    mostly toward -y, which is off the map: it is clamped to y = 0 (without the clamp it ends near y = -14).
    Test-defect (engine rules round 4, T10): S was a unit of M's own side; R-097-10 now gives the push to an idle own unit, so the mover would not be pushed at all. An enemy idle unit takes none,
    as the scene needs."""
    assert lib.om_map_set_canvas(tw, CANVAS_W, CANVAS_H) == 0
    m = lib.om_unit_spawn(tw, RAIDER, FRIEND, 500.0, 3.0, 0)
    lib.om_unit_spawn(tw, SUPPLY, ENEMY, 510.0, 15.0, 0)
    lib.om_command_move(tw, m, 1000.0, 3.0)
    lib.om_tactical_step(tw)
    x, y = lib.om_unit_get_pos(tw, m)
    assert y == 0.0, f"pushed unit left the canvas or was not clamped: y = {y}"
    assert x > 0.0
