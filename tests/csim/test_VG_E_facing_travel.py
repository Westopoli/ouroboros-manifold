# Rule pins: R-100-01@3b6c41, R-100-02@91e007
"""VG-E-facing-travel (sim): a moving unit faces the way it travels (R-100-01, S-100; DEC-facing-travel-2026-10-22).

Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "VG-E-facing-travel". Fenced: builders never edit this file.
Westley 2026-10-22: "The arrow points backwards relative to movement." Finding FINDING-sim-facing-goal-not-travel: the face pass
(csrc/tactical_move.c, om_move_face_pass) turns toward the final destination, not the direction of travel; 45-50 degrees off on a
bending route. The face pass priority becomes: engaged target, then the one-tick displacement heading (at least
DRAFT-facing-travel-min-disp 0.5 wu per tick), then the destination heading when has_dest, else keep the last facing.

Drafts used (ledger, Architect 2026-10-22/23; Westley may veto):
  DRAFT-facing-travel-tol  10 degrees: facing within this of the unit's 5-tick displacement heading while it moves.
  DRAFT-facing-travel-min-disp 0.5 wu per tick (the sanity floor the walker test asserts so the heading is not read off noise).

UNSTATED INTERFACE CHOICES (the paragraph names none of these; the test writer chose them, 2026-10-23):
  * The bending route: terrain seed 1 (om_terrain_generate(w, 1, 12000, 12000)), movement kind WALKING for the Raider, layer 0.
    The paragraph says "ordered 2000 wu along +y round a ridge" and does not give a start. Cells (114, 82) and (46, 14) were found by
    scanning the walk mask for starts with a straight +2000 wu goal whose om_walk_route bends; on main both read 45-57 degrees off
    (the paragraph's "45-50"). The start is the cell centre ((cx + 0.5) * 100, (cy + 0.5) * 100); the goal is the same x, y + 2000.
  * "5-tick displacement heading" = atan2 of (pos at tick t) - (pos at tick t - 5). The design text and DEC-facing-travel rev 2
    (2026-10-23) say the code reads one tick (prev_x/prev_y); the test text says 5 ticks. The 10-degree tolerance is asserted
    against the 5-tick heading as the paragraph's Tests first writes it; on the flipped throwaway build all six walker cases pass.
  * Facing is read with om_unit_get_facing after om_tactical_step; the tick numbers 10, 30, 60 count steps after om_command_move.
  * "Ordered and not yet moved faces its goal": asserted as the first tick's turn (facing leaves its planted value toward the goal,
    inside the turn cap) and as the facing after 10 ticks on an open map; the engaged-target and wall-stop branches are not asserted
    (the wall-stop needs a blocker scenario owned by VG-E-move-through-idle-own's files; see the report).
  * Kiting guard: the unit is a Vanguard with om_command_attack_target_kiting, the pattern of tests/csim/test_E13_S100_facing.py.

Not written (they need pieces that have not landed): anything reading the unit-position batch (LAB-CONTRACT-unit-pos-batch) or the
VG-T-EMIT-WIRE emissions. None of the paragraph's tests needs them; the walker is read through om_unit_get_pos.
"""
import ctypes
import math

import pytest

from conftest import OMFeature

RAIDER, VANGUARD = 0, 2
FRIEND, ENEMY = 0, 1
OM_MOVE_WALKING = 1
SEED = 1
CANVAS = 12000.0
LAYER = 0
CELL = 100.0
ORDER_WU = 2000.0              # the paragraph: ordered 2000 wu along +y
TOL_DEG = 10.0                 # DRAFT-facing-travel-tol
MIN_DISP = 0.5                 # DRAFT-facing-travel-min-disp, wu per tick
HEADING_TICKS = 5              # the window of the displacement heading
STRIKE_TURN_CAP = 0.3          # rad per tick, R-100-02 (6.0 rad/s at 20 ticks/s)

BEND_STARTS = [(114, 82), (46, 14)]   # see UNSTATED INTERFACE CHOICES


def _diff_deg(a, b):
    return (math.degrees(a - b) + 180.0) % 360.0 - 180.0


def _bend_world(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_WALKING) == 0
    return w


@pytest.mark.parametrize("start", BEND_STARTS)
@pytest.mark.parametrize("tick", [10, 30, 60])
def test_R_100_01_a_walker_on_a_bending_route_faces_its_travel_heading(lib, world_factory, start, tick):
    """R-100-01 (S-100): ordered 2000 wu along +y on terrain seed 1, the walker's facing is within 10 degrees of its 5-tick
    displacement heading at ticks 10, 30, 60. Red on main (a): the face pass points it at the final goal, 45-50 degrees off."""
    w = _bend_world(lib, world_factory)
    sx, sy = (start[0] + 0.5) * CELL, (start[1] + 0.5) * CELL
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, sx, sy, LAYER)
    assert u
    lib.om_command_move(w, [u], 1, sx, sy + ORDER_WU)
    pos = [lib.om_unit_get_pos(w, u)]
    for _ in range(tick):
        lib.om_tactical_step(w)
        pos.append(lib.om_unit_get_pos(w, u))
    a, b = pos[tick - HEADING_TICKS], pos[tick]
    moved = math.hypot(b[0] - a[0], b[1] - a[1])
    assert moved > HEADING_TICKS * MIN_DISP, f"setup: the walker moved only {moved:.2f} wu in {HEADING_TICKS} ticks at tick {tick}"
    heading = math.atan2(b[1] - a[1], b[0] - a[0])
    off = _diff_deg(lib.om_unit_get_facing(w, u), heading)
    assert abs(off) <= TOL_DEG, (f"tick {tick}: facing {math.degrees(lib.om_unit_get_facing(w, u)):.1f} deg, "
                                 f"5-tick displacement heading {math.degrees(heading):.1f} deg, {off:.1f} deg off (limit {TOL_DEG})")


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def test_R_100_01_a_unit_ordered_and_not_yet_moved_faces_its_goal(lib, tw):
    """R-100-01: on an open map a Raider facing -x, ordered to a point on +y, turns toward it on the first tick (inside the strike
    turn cap) and faces it by tick 10. Unchanged-behaviour guard; green on main."""
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    lib.om_unit_set_facing(tw, u, math.pi)
    lib.om_command_move(tw, [u], 1, 0.0, 2000.0)
    lib.om_tactical_step(tw)
    f1 = lib.om_unit_get_facing(tw, u)
    assert math.pi - STRIKE_TURN_CAP - 1e-6 <= f1 < math.pi - 0.01, f"first-tick facing {f1}: expected a capped turn from pi toward pi/2"
    for _ in range(9):
        lib.om_tactical_step(tw)
    assert abs(_diff_deg(lib.om_unit_get_facing(tw, u), math.pi / 2.0)) <= TOL_DEG


def test_R_100_01_a_kiting_unit_faces_its_kite_target(lib, tw):
    """R-100-01: a unit kiting (retreating under attack-target) faces its target, not its travel; the face pass skips kiting units.
    Unchanged-behaviour guard (tests/csim/test_E13_S100_facing.py pattern); green on main and must stay green."""
    u = lib.om_unit_spawn(tw, VANGUARD, FRIEND, 100.0, 0.0, 0)
    pursuer = lib.om_unit_spawn(tw, RAIDER, ENEMY, 200.0, 0.0, 0)
    lib.om_unit_set_facing(tw, u, math.pi)
    lib.om_command_attack_target_kiting(tw, u, pursuer, 0.0, 0.0)
    for t in range(3):
        lib.om_tactical_step(tw)
        assert abs(_diff_deg(lib.om_unit_get_facing(tw, u), 0.0)) <= TOL_DEG, f"tick {t + 1}: a kiting unit must face its target (+x)"


def test_R_100_01_positive_control_the_straight_run_reads_zero(lib, tw):
    """R-100-01: the straight +x run still reads 0. Positive control of the heading detector: the same displacement-heading
    measure as the bending test returns 0 degrees here and the facing agrees. Green on main (the control passes on the old
    behaviour, so a heading that reads 0 here and 45-57 on the bend is the bend's defect, not the detector's)."""
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    lib.om_unit_set_facing(tw, u, math.pi / 2.0)
    lib.om_command_move(tw, [u], 1, 2000.0, 0.0)
    pos = [lib.om_unit_get_pos(tw, u)]
    for _ in range(30):
        lib.om_tactical_step(tw)
        pos.append(lib.om_unit_get_pos(tw, u))
    a, b = pos[25], pos[30]
    heading = math.atan2(b[1] - a[1], b[0] - a[0])
    assert abs(math.degrees(heading)) < 1.0, "setup: the straight run's own heading is not 0"
    assert abs(_diff_deg(lib.om_unit_get_facing(tw, u), 0.0)) <= 1.0
