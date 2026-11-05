# Rule pins: R-096-01@d86536, R-097-03@6f75ba, R-097-04@3756c3, R-099-02@9e76f5, R-100-01@3b6c41, R-100-02@91e007, R-102-02@c99d03
"""PP-move rule tests, steering sweep (P8) and facing (P7).

Proves E-13 R-097-03, R-097-04, R-102-02 (S-097, S-102) and R-100-01 (S-100), as
reworded by Addendum 45 (docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md,
Phase A rows P8 and P7). Written before the code; every test here is meant to be red
against the 13-angle, wait-when-blocked, group-mates-exempt, live-position C.

The Python reference is simulation/movement.py 234-250, 311-325, 413-431 and
simulation/facing.py 59-77. The scene arithmetic is worked out in each docstring: a probe
point is 40 wu ahead of the unit; a probe is blocked when a living same-layer unit's
start-of-tick position is closer than 30 wu (2 x radius 15) to it.

Numeric slack: ANGLE_TOL_RAD is not a rule threshold. The rule fixes the six angles;
neighbouring choices in a scene differ by at least 0.52 rad, so any slack well below that
tells them apart. It only absorbs the C's cheap trig on the seek heading. DIST_TOL does the same for
the step length (a full step against a waiting unit).
"""
import ctypes
import math
import pathlib
import re

import pytest

from conftest import OMFeature

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = 0, 1, 2, 3, 4, 5
FRIEND, ENEMY = 0, 1

ANGLE_TOL_RAD = 0.01
DIST_TOL = 0.01         # the C's cheap sin/cos leave a step 5e-5 wu short; this only tells "moved" from "waited"
RAIDER_STEP = 7.5       # 150 wu/s at 20 ticks/s (R-099-02)
VANGUARD_STEP = 4.0     # 80 wu/s at 20 ticks/s
DETOUR_MIN_DIST = 60.0  # R-097-04

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def tw(lib, world_factory):
    """A world with the tactical feature on. Files named test_PP_* get no epic isolation set."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _arr(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def _angle_diff(a, b):
    """Smallest signed difference a - b in radians."""
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def _step_once(lib, w, u):
    """One tactical tick; returns (displacement angle in rad, distance moved, new position)."""
    x0, y0 = lib.om_unit_get_pos(w, u)
    lib.om_tactical_step(w)
    x1, y1 = lib.om_unit_get_pos(w, u)
    return math.atan2(y1 - y0, x1 - x0), math.hypot(x1 - x0, y1 - y0), (x1, y1)


def _spawn_blockers(lib, w, points, layer=0):
    return [lib.om_unit_spawn(w, RAIDER, FRIEND, float(x), float(y), layer) for (x, y) in points]


# (case id, blocker positions around a Raider at (0,0) ordered to (1000, 0), expected first-step angle in degrees)
#
# Probe points: straight (40,0); +30 (34.64,20); -30 (34.64,-20); +60 (20,34.64); -60 (20,-34.64);
# +90 (0,40); -90 (0,-40). A blocker holds a probe when it is under 30 wu from the probe point.
SWEEP_CASES = [
    # nothing in the way: straight (positive control for the "straight" outcome)
    ("clear", [], 0.0),
    # (40,0) holds straight, +30 (20.7 away) and -30 (20.7); +60 is 40 away: first clear is +60
    ("plus60_first_clear", [(40, 0)], 60.0),
    # (60,0) holds straight (20) but +30 is 32.3 away and -30 the same: +30 comes before -30
    ("plus30_before_minus30", [(60, 0)], 30.0),
    # (45,20) holds straight (20.6) and +30 (10.4); -30 is 41 away: -30
    ("minus30_when_plus30_blocked", [(45, 20)], -30.0),
    # (40,0) as above and (35,40) holds +60 (15.9 away); -60 is 40 and 77 away: -60
    ("minus60_when_plus60_blocked", [(40, 0), (35, 40)], -60.0),
    # (35,-40) now holds -60 (15.9); +90 (0,40) is 35 from (35,40): +90
    ("plus90_when_both_60s_blocked", [(40, 0), (35, 40), (35, -40)], 90.0),
    # (0,45) holds +90 (5); -90 (0,-40) is 35 from (35,-40): -90
    ("minus90_when_plus90_blocked", [(40, 0), (35, 40), (35, -40), (0, 45)], -90.0),
    # (0,-45) holds -90 as well: none clear, the unit continues straight (does not wait)
    ("none_clear_continues_straight", [(40, 0), (35, 40), (35, -40), (0, 45), (0, -45)], 0.0),
]


@pytest.mark.parametrize("case_id,blockers,expect_deg", SWEEP_CASES, ids=[c[0] for c in SWEEP_CASES])
def test_R_097_03_sweep_order_first_clear_none_clear_straight(lib, tw, case_id, blockers, expect_deg):
    """R-097-03 (P8): the unit probes 40 wu ahead; if blocked it tries +30, -30, +60, -60, +90, -90
    degrees from its heading, in that order, and takes the first clear one; if none is clear it
    continues straight (it does not wait). The unit always moves its full 7.5 wu this tick.
    Control: case 'clear' (no blocker) and every case that expects 0 or a clear direction must not
    be mistaken for 'waiting' (zero distance)."""
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    _spawn_blockers(lib, tw, blockers)
    lib.om_command_move(tw, u, 1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, u)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL), f"{case_id}: unit did not move its full step (waited?)"
    assert abs(_angle_diff(ang, math.radians(expect_deg))) < ANGLE_TOL_RAD, \
        f"{case_id}: moved at {math.degrees(ang):.2f} deg, expected {expect_deg}"


def test_R_097_03_only_same_layer_blockers(lib, tw):
    """R-097-03 (P8): only units on the mover's layer block the probe. A blocker at (40,0) on layer 1
    does not stop a layer 0 mover (it goes straight); the same blocker on layer 0 does (positive
    control: the mover deflects +60)."""
    other = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    _spawn_blockers(lib, tw, [(40, 0)], layer=1)
    lib.om_command_move(tw, other, 1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, other)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
    assert abs(_angle_diff(ang, 0.0)) < ANGLE_TOL_RAD, "a blocker on another layer deflected the mover"


def test_R_097_03_same_layer_blocker_is_the_positive_control(lib, tw):
    """Positive control for the layer-filter tests: the same geometry with the blocker on the mover's own
    layer must deflect it (any turn away from straight; the exact angle is the sweep test's business), on
    layer 0 and on layer 1 alike. Green today and must stay green."""
    for layer in (0, 1):
        w = lib.om_world_new(1, 1)
        lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
        try:
            u = lib.om_unit_spawn(w, RAIDER, FRIEND, 0.0, 0.0, layer)
            _spawn_blockers(lib, w, [(40, 0)], layer=layer)
            lib.om_command_move(w, u, 1000.0, 0.0)
            ang, dist, _ = _step_once(lib, w, u)
            assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
            assert abs(_angle_diff(ang, 0.0)) > 0.1, f"layer {layer}: a same-layer blocker did not deflect"
        finally:
            lib.om_world_free(w)


def test_R_097_03_mover_on_upper_layer_ignores_lower_layer_blocker(lib, tw):
    """R-097-03 (P8): the layer filter works both ways: a layer 1 mover is not blocked by a layer 0 unit."""
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 1)
    _spawn_blockers(lib, tw, [(40, 0)], layer=0)
    lib.om_command_move(tw, u, 1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, u)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
    assert abs(_angle_diff(ang, 0.0)) < ANGLE_TOL_RAD


def test_R_097_03_group_mates_block(lib, tw):
    """R-097-03 (P8): a unit of the mover's own move group blocks the probe like any other unit (the C
    exempted group mates). A at (0,0) and B at (40,0) are group-moved to (1000,0); A's slot is (980,0), its
    straight probe point (40,0) is B's start-of-tick position, so A deflects +60 as in the single-blocker case."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 40.0, 0.0, 0)
    gid = lib.om_command_group_move(tw, _arr([a, b]), 2, 1000.0, 0.0)
    assert gid != 0
    ang, dist, _ = _step_once(lib, tw, a)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
    assert abs(_angle_diff(ang, math.radians(60.0))) < ANGLE_TOL_RAD, \
        f"group mate did not block: A moved at {math.degrees(ang):.2f} deg"


def test_R_097_03_probe_uses_start_of_tick_positions(lib, tw):
    """R-097-03 (P8): the probe tests every other unit where it stood at the start of the tick, not where
    an earlier unit of this tick has already moved it. A (id 1) at (0,0) goes +x and moves first to (7.5,0);
    B (id 2) at (77,0) goes -x, its straight probe point is (37,0). Start of tick: A is 37 away, clear, so B
    goes straight (180 deg). With A already at (7.5,0) it would be 29.5 away and B would deflect."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 77.0, 0.0, 0)
    lib.om_command_move(tw, a, 1000.0, 0.0)
    lib.om_command_move(tw, b, -1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, b)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
    assert abs(_angle_diff(ang, math.pi)) < ANGLE_TOL_RAD, \
        f"B probed against A's live position: moved at {math.degrees(ang):.2f} deg"


def test_R_097_03_start_of_tick_control_idle_unit_at_the_live_spot_blocks(lib, tw):
    """Positive control for the start-of-tick test: A idle at (7.5,0) (so its start-of-tick and live positions
    are the same) is 29.5 from B's probe point (37,0): B must deflect, whichever angle the sweep then picks
    (the sweep test owns the angle: +30 from heading 180 is 210 deg). Green today and must stay green."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 7.5, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 77.0, 0.0, 0)
    lib.om_command_move(tw, b, -1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, b)
    assert dist == pytest.approx(RAIDER_STEP, abs=DIST_TOL)
    assert abs(_angle_diff(ang, math.pi)) > 0.1, "an idle unit on the probe point did not deflect B"


@pytest.mark.parametrize("unit_type,step", [(RAIDER, RAIDER_STEP), (VANGUARD, VANGUARD_STEP)],
                         ids=["raider_7_5_per_tick", "vanguard_4_per_tick"])
def test_R_097_04_detour_held_for_60_wu_of_distance_moved(lib, tw, unit_type, step):
    """R-097-04 (P8): a deflected heading is held for 60 wu of distance moved, counted by distance (so a slower
    unit holds it for more ticks), then the unit re-aims at its destination. The blocker at (60,0) holds only the
    straight probe (20 wu) and leaves +30 clear, so the deflection is +30 whatever the rest of the sweep does;
    it is removed after the first tick (hp 0) so that the straight way is clear and only the detour hold keeps
    the heading. A Raider holds +30 deg for 8 ticks, a Vanguard for 15; the next tick heads at the destination."""
    ticks_held = int(round(DETOUR_MIN_DIST / step))
    u = lib.om_unit_spawn(tw, unit_type, FRIEND, 0.0, 0.0, 0)
    blocker = _spawn_blockers(lib, tw, [(60, 0)])[0]
    lib.om_command_move(tw, u, 1000.0, 0.0)
    ang, dist, _ = _step_once(lib, tw, u)
    assert abs(_angle_diff(ang, math.radians(30.0))) < ANGLE_TOL_RAD, "no +30 deflection on tick 1"
    lib.om_unit_set_hp(tw, blocker, 0.0)
    assert lib.om_unit_alive(tw, blocker) == 0
    for k in range(2, ticks_held + 1):
        ang, dist, _ = _step_once(lib, tw, u)
        assert dist == pytest.approx(step, abs=DIST_TOL)
        assert abs(_angle_diff(ang, math.radians(30.0))) < ANGLE_TOL_RAD, \
            f"detour dropped on tick {k} of {ticks_held}"
    x, y = lib.om_unit_get_pos(tw, u)
    ang, dist, _ = _step_once(lib, tw, u)
    want = math.atan2(0.0 - y, 1000.0 - x)
    assert abs(_angle_diff(ang, want)) < ANGLE_TOL_RAD, \
        f"detour held past {DETOUR_MIN_DIST} wu: moved at {math.degrees(ang):.2f}, wanted {math.degrees(want):.2f}"


def test_R_102_02_sweep_order_is_documented_in_algorithms_md():
    """R-102-02 (S-102, plan row P8): the steering sweep order is fixed and documented: ALG-68 in
    docs/bible/algorithms.md names the six angles in order, +30, -30, +60, -60, +90, -90 (the file the
    constants are generated from, scripts/specfactory/alg_constants.py). Red until written there."""
    text = (REPO_ROOT / "docs/bible/algorithms.md").read_text()
    m = re.search(r"\*\*ALG-68[^\n]*", text)
    assert m, "ALG-68 paragraph missing"
    para = m.group(0).replace("\u2212", "-").replace("\u00b0", "")
    assert re.search(r"\+\s*30\D+?-\s*30\D+?\+\s*60\D+?-\s*60\D+?\+\s*90\D+?-\s*90", para), \
        "ALG-68 does not list the sweep angles +30, -30, +60, -60, +90, -90 in order"


# ----------------------------------------------------------------------------------------------
# Facing (P7, R-100-01). Raider turn rate 6.0 rad/s = 0.3 rad per tick (R-100-02, already ruled).
# ----------------------------------------------------------------------------------------------

def _face_scene(lib, w, enemy_dx, enemy_dy):
    a = lib.om_unit_spawn(w, RAIDER, FRIEND, 1000.0, 1000.0, 0)
    e = lib.om_unit_spawn(w, RAIDER, ENEMY, 1000.0 + enemy_dx, 1000.0 + enemy_dy, 0)
    lib.om_unit_set_facing(w, a, 0.0)
    return a, e


def test_R_100_01_stationary_firing_unit_turns_to_its_target(lib, tw):
    """R-100-01 (P7): a unit attacking a target faces the target, also when it is standing still. Raider A
    idle at (1000,1000) facing +x, enemy Raider 150 wu away at +y (inside the 200 wu range): A acquires it and
    must turn to face +y (pi/2), at the capped rate (0.3 rad on the first tick, not a snap)."""
    a, e = _face_scene(lib, tw, 0.0, 150.0)
    # Test-defect, A163/A164: 1 step -> up to 4 steps, stopping on the tick A acquires (first acquisition moved by up to 3 ticks); the first-tick capped-turn check now reads that acquiring tick; cause: aligned targeting cohort (parity with the Python, Addendum 63).
    for _ in range(4):
        lib.om_tactical_step(tw)
        if lib.om_unit_get_target(tw, a) == e:
            break
    assert lib.om_unit_get_target(tw, a) == e, "scene error: A did not engage the enemy within 4 ticks"
    f1 = lib.om_unit_get_facing(tw, a)
    assert 0.0 < f1 <= 0.3 + 1e-6, f"first-tick facing {f1}: expected a capped turn toward the target"
    for _ in range(7):
        lib.om_tactical_step(tw)
    assert abs(_angle_diff(lib.om_unit_get_facing(tw, a), math.pi / 2.0)) < ANGLE_TOL_RAD


def test_R_100_01_no_target_and_idle_keeps_last_facing(lib, tw):
    """R-100-01: idle with no target, a unit keeps its last facing. Positive control for the stationary-turn test:
    the same scene with the enemy 350 wu away (beyond 1.5 x the 200 wu range, no target) must not turn A."""
    a, e = _face_scene(lib, tw, 0.0, 850.0)
    for _ in range(8):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_target(tw, a) == 0, "scene error: A engaged a far enemy"
    assert lib.om_unit_get_facing(tw, a) == pytest.approx(0.0, abs=1e-9)


def test_R_100_01_engaged_target_outranks_move_target(lib, tw):
    """R-100-01 (P7): the engaged target comes before the move target. An attack-moving Raider ordered along +x
    meets an enemy 150 wu away at +y: it halts and fires and must face the enemy (pi/2), not its move target (0)."""
    a, e = _face_scene(lib, tw, 0.0, 150.0)
    lib.om_command_attack_move(tw, a, 3000.0, 1000.0)
    # Test-defect, A163/A164: 10 steps -> 13 steps (first acquisition moved by up to 3 ticks); cause: aligned targeting cohort (parity with the Python, Addendum 63).
    for _ in range(13):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_target(tw, a) == e
    # Test-defect, A163/A164: expected facing pi/2 -> the bearing from A's actual position to E (A walks 7.5 wu along +x before it acquires, so the bearing is pi/2 + 0.05); cause: aligned targeting cohort (parity with the Python, Addendum 63).
    ax, ay = lib.om_unit_get_pos(tw, a)
    ex, ey = lib.om_unit_get_pos(tw, e)
    assert abs(_angle_diff(lib.om_unit_get_facing(tw, a), math.atan2(ey - ay, ex - ax))) < ANGLE_TOL_RAD


def test_R_100_01_plain_move_never_faces_an_enemy_control(lib, tw):
    """Positive control for the engaged-outranks-move test: the same scene under a plain move (R-096-01: no
    target is acquired) faces the move target (0), not the enemy. Green today and must stay green."""
    a, e = _face_scene(lib, tw, 0.0, 150.0)
    lib.om_command_move(tw, a, 3000.0, 1000.0)
    for _ in range(4):
        lib.om_tactical_step(tw)
    assert lib.om_unit_get_target(tw, a) == 0
    assert abs(_angle_diff(lib.om_unit_get_facing(tw, a), 0.0)) < ANGLE_TOL_RAD
