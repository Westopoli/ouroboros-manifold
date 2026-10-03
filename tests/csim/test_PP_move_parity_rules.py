"""Parity-diagnosis C bugs, tests against RULED text (Addendum 63 / A176-A180, runs/2026-10-03_parity_diagnosis.md).

Proves E-13 R-100-02 (S-100, turn rate by category), R-099-04 (S-099, a route waypoint, the final one included,
counts as reached within 2 x collision radius = 30 wu), R-097-03 (S-097, the steering detour is held for 60 wu
moved, a new order does not clear it) and the targeting cohort (Phase B C1: the Python staggers by uid % 4 with
0-based uid; C ids are uid + 1, so the C must use (id - 1) % 4). Written before the fixes; each test is red today
for the reason in its docstring. Rates: simulation/config.py FACING_ROTATION_SPEED_* = 6.0 / 4.0 / 2.5 rad/s, one
tick is 1/20 s (OM_TACTICAL_TICK_RATE), so a capped turn is 0.3 / 0.2 / 0.125 rad per tick.
"""
import ctypes
import math

import pytest

from conftest import OMFeature

RAIDER = 0
FRIEND, ENEMY = 0, 1
TICKS_PER_SEC = 20.0
RATE_PER_TICK = {"strike": 6.0 / TICKS_PER_SEC, "line": 4.0 / TICKS_PER_SEC, "siege": 2.5 / TICKS_PER_SEC}
CATEGORY = {"strike": 0, "line": 1, "siege": 2}
ANGLE_TOL = 1e-6          # the cap is exact arithmetic on the facing value, no trig on the capped path
ANGLE_TOL_STEER = 0.01    # as test_PP_move_steer_face.py: absorbs the C's cheap trig on a displacement angle
RAIDER_STEP = 7.5         # 150 wu/s at 20 ticks/s
DETOUR_MIN_DIST = 60.0    # R-097-03
WAYPOINT_REACH = 30.0     # R-099-04: 2 x collision radius 15

# custom types: the category is what the rule names, the speed is picked to be the "wrong" band for it
T_STRIKE_SLOW, T_SIEGE_FAST, T_LINE_MID, T_DUMMY = 200, 201, 202, 203


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    return w


def _reg(lib, w, type_id, category, speed, attack_range=100.0, sensor=100.0):
    rc = lib.om_roster_register_custom_unit(w, type_id, category, b"parity", 500.0, 5.0, 1.0, attack_range,
                                            speed, sensor, 1.0, 0.0, 0)
    assert rc == 0, rc


def _angle_diff(a, b):
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


# ------------------------------------------------------------- R-100-02 turn rate by category

# (name, category, speed, per-tick cap). Strike at speed 30 (a Siege speed band), Siege at 200 (a Strike band):
# the category decides, never the speed.
TURN_CASES = [
    ("strike_slow", "strike", 30.0),
    ("line_fast", "line", 200.0),
    ("line_slow", "line", 30.0),
    ("line_mid", "line", 80.0),          # positive control: band and category agree today
    ("siege_fast", "siege", 200.0),
    ("strike_fast", "strike", 200.0),    # positive control: the speed band and the category agree today
    ("siege_slow", "siege", 30.0),       # positive control: likewise
]


@pytest.mark.parametrize("name,cat,speed", TURN_CASES, ids=[c[0] for c in TURN_CASES])
def test_R_100_02_turn_rate_is_set_by_category_not_speed(lib, tw, name, cat, speed):
    """A unit facing 0 ordered to a point due north (heading pi/2 = 1.5708 rad) turns by exactly the category's cap
    per tick for three ticks (0.3 / 0.2 / 0.125 rad), whatever its speed. Red today for strike_slow, line_fast, line_slow
    and siege_fast: tactical_move.c om_move_turn_rate_for picks the rate from native speed bands (>= 100 Strike,
    >= 60 Line, else Siege). The strike_fast, siege_slow and line_mid cases are the control that the detector passes when band and category agree."""
    _reg(lib, tw, T_STRIKE_SLOW, CATEGORY[cat], speed)
    u = lib.om_unit_spawn(tw, T_STRIKE_SLOW, FRIEND, 1000.0, 500.0, 0)
    assert u != 0
    f0 = lib.om_unit_get_facing(tw, u)
    assert abs(f0) < ANGLE_TOL, "spawn facing is expected to be 0"
    lib.om_command_move(tw, u, 1000.0, 1900.0)
    cap = RATE_PER_TICK[cat]
    for k in (1, 2, 3):
        lib.om_tactical_step(tw)
        got = lib.om_unit_get_facing(tw, u)
        assert abs(_angle_diff(got, k * cap)) < ANGLE_TOL, f"{name} tick {k}: facing {got:.6f}, want {k * cap:.6f}"


# ------------------------------------------------------------- R-099-04 waypoint reach

def _walk_to_rest(lib, w, u, limit=900, quiet=15):
    """Step until the unit has not moved for `quiet` ticks; return its position."""
    still = 0
    last = lib.om_unit_get_pos(w, u)
    for _ in range(limit):
        lib.om_tactical_step(w)
        p = lib.om_unit_get_pos(w, u)
        still = still + 1 if math.hypot(p[0] - last[0], p[1] - last[1]) < 1e-9 else 0
        last = p
        if still >= quiet:
            return p
    raise AssertionError("the unit never came to rest")


def test_R_099_04_one_waypoint_final_waypoint_reached_within_30_wu(lib, tw):
    """A routed move (a wall column across the line, so the path takes a waypoint before the destination): a Raider
    (7.5 wu per tick) ends within 30 wu of the destination, the final waypoint included, and not before it was within
    30 wu of the previous tick's start: [22.5, 30). The previous tick started at least 30 wu out, so it cannot have
    stopped earlier. Red today: tactical_move.c ~1936 uses OM_ARRIVAL_TOLERANCE_MULT x radius = 22.5."""
    # Test-defect, A163/A164: direct 300->800 move with no wall -> routed move around a wall (om_map_block_rect); cause: aligned targeting cohort (parity with the Python, Addendum 63): R-099-04's 30 wu applies to route waypoints, a direct move keeps 22.5 (see the control below).
    assert lib.om_map_block_rect(tw, 510.0, 10.0, 590.0, 790.0, 0, 4) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 850.0, 400.0)
    p = _walk_to_rest(lib, tw, u, limit=1200)
    d = math.hypot(850.0 - p[0], 400.0 - p[1])
    assert WAYPOINT_REACH - RAIDER_STEP <= d < WAYPOINT_REACH, f"stopped {d:.2f} wu short, want [22.5, 30)"


def test_control_R_099_04_direct_move_keeps_the_22_5_wu_arrival(lib, tw):
    """Positive control for the waypoint test (the old direct scene, open ground): a direct move is not a route
    waypoint, so it ends inside 1.5 x the 15 wu radius = 22.5 wu, the Python's arrival, not 30."""
    # Test-defect, A163/A164: new control, the former one-waypoint scene kept as the direct-move case; cause: aligned targeting cohort (parity with the Python, Addendum 63).
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 800.0, 400.0)
    p = _walk_to_rest(lib, tw, u)
    d = math.hypot(800.0 - p[0], 400.0 - p[1])
    assert d < WAYPOINT_REACH - RAIDER_STEP, f"stopped {d:.2f} wu short, want < 22.5"


def test_R_099_04_two_waypoint_route_ends_within_30_wu_and_not_earlier(lib, tw):
    """A wall (column 5, rows 0..7) forces a route with an intermediate waypoint before the destination. The final
    leg is a straight approach, so the unit stops in [30 - 7.5, 30) wu of the destination: within 30, not before it
    was within 30 of the previous tick's start. Red today for the same 22.5 vs 30 reason as the one-waypoint case."""
    assert lib.om_map_block_rect(tw, 510.0, 10.0, 590.0, 790.0, 0, 4) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    p = _walk_to_rest(lib, tw, u, limit=1200)
    d = math.hypot(900.0 - p[0], 400.0 - p[1])
    assert WAYPOINT_REACH - RAIDER_STEP <= d < WAYPOINT_REACH, f"stopped {d:.2f} wu short, want [22.5, 30)"


# ------------------------------------------------------------- R-097-03 detour survives a new order

def _detour_scene(lib, w):
    """A Raider at (0,0) ordered east, a friend standing at (40,0): the straight, +30 and -30 probes are held,
    +60 is the first clear one (SWEEP case "plus60_first_clear" of test_PP_move_steer_face.py)."""
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, 500.0, 500.0, 0)
    blocker = lib.om_unit_spawn(w, RAIDER, FRIEND, 540.0, 500.0, 0)
    assert u and blocker
    lib.om_command_move(w, u, 1500.0, 500.0)
    return u


def _step_angle(lib, w, u):
    x0, y0 = lib.om_unit_get_pos(w, u)
    lib.om_tactical_step(w)
    x1, y1 = lib.om_unit_get_pos(w, u)
    return math.atan2(y1 - y0, x1 - x0), math.hypot(x1 - x0, y1 - y0)


def test_R_097_03_control_detour_is_held_for_60_wu_of_movement(lib, tw):
    """Positive control, no new order: the first step takes the +60 degree detour and the unit then keeps that heading
    until 60 wu have been moved (8 steps of 7.5), re-probing and turning only after. Passes today."""
    u = _detour_scene(lib, tw)
    for k in range(8):
        ang, dist = _step_angle(lib, tw, u)
        assert abs(_angle_diff(ang, math.radians(60.0))) < ANGLE_TOL_STEER, f"step {k + 1}: heading {math.degrees(ang):.2f}"
        assert abs(dist - RAIDER_STEP) < 0.01


def test_R_097_03_a_new_move_order_does_not_clear_the_detour(lib, tw):
    """Westley's rule: the detour is held for 60 wu of distance moved. A new move order (here to the south-east, whose
    own probe would choose -75 degrees) given one step into the detour leaves the held +60 degree heading in place for
    the remaining steps up to 60 wu. Red today: tactical_move.c ~2516 (om_command_move) sets mu->deflecting = 0, so
    the next step re-probes and heads off the held +60 degrees."""
    u = _detour_scene(lib, tw)
    ang, _ = _step_angle(lib, tw, u)
    assert abs(_angle_diff(ang, math.radians(60.0))) < ANGLE_TOL_STEER      # the detour is active
    lib.om_command_move(tw, u, 1500.0, -500.0)
    for k in range(2, 9):
        ang, _ = _step_angle(lib, tw, u)
        assert abs(_angle_diff(ang, math.radians(60.0))) < ANGLE_TOL_STEER, \
            f"step {k}: heading {math.degrees(ang):.2f}, the order cleared the detour"


# ------------------------------------------------------------- targeting cohort (Phase B C1)

def test_PB_C1_targeting_cohort_follows_the_python_uid_not_the_c_id(lib, tw):
    """Python (simulation/damage.py update_targeting): the counter is bumped first, then a unit with 0-based uid u
    looks for a target when counter % 4 == u % 4. Measured with the parity harness on this very scene: uid 0 first
    has its target in frame 4, uid 1 in frame 1, uid 2 in frame 2, uid 3 in frame 3 (frame n = after n steps). The C
    ids are uid + 1, so the C must use (id - 1) % 4 (csrc/unit.c ~2053, om_unit_targeting_cohort ~2823). Red today:
    the C has them in frames 1, 2, 3, 4. The enemies are range-1, sensor-1 dummies that never acquire, so there is
    no return-fire or retaliation to confound the slot."""
    _reg(lib, tw, T_DUMMY, 1, 10.0, attack_range=1.0, sensor=1.0)
    ids = [lib.om_unit_spawn(tw, RAIDER, FRIEND, 500.0 + 300.0 * i, 500.0, 0) for i in range(4)]
    foes = [lib.om_unit_spawn(tw, T_DUMMY, ENEMY, 600.0 + 300.0 * i, 500.0, 0) for i in range(4)]
    assert all(ids) and all(foes)
    first = {}
    for frame in range(1, 9):
        lib.om_tactical_step(tw)
        for uid, cid in enumerate(ids):
            if uid not in first and lib.om_unit_get_target(tw, cid) != 0:
                first[uid] = frame
    expected = {uid: (uid % 4) or 4 for uid in range(4)}      # frame n = counter n: uid 0 waits for counter 4
    assert first == expected, f"first-target frame by 0-based uid: {first}, want {expected}"
    assert lib.om_unit_get_target(tw, ids[1]) == foes[1]      # control: each unit does acquire its own foe
