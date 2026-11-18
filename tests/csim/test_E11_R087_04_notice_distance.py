"""E-11 R-087-04 / E-13 R-096-02 (engine rule fixes, Round 5, G1; Westley 2026-11-17: "1: \"aquire within attack radius\" wins, modify the rule accordingly and
fix the conflict"): a unit acquires only within its notice distance, never the sensor radius.

Spec: docs/northstar/plans/engine-rules-2026-11-08/round5.md "G1". Rule pins: R-087-04, R-096-02, R-087-08, R-087-10.

Rule words proved, from docs/bible/epics/E-11-units-and-combat.md and E-13-movement-and-command.md on this branch:
  R-087-04  "Given an idle unit (no order, or an attack-move that has arrived) or an attack-moving unit with no target, When an enemy its side can see
            (E-12 R-093-02; reach across layers R-008-04) is within its notice distance, Then it acquires the nearest such enemy at its cohort turn
            (R-087-08), anchors where it stands (R-087-05), walks toward the target while it is beyond attack range, then halts and fires; an
            attack-mover leaves its slot and route to do so and resumes toward its point after the engagement (R-096-02); an idle unit holds where
            the engagement ends (R-087-06); the leash of R-087-05 bounds the walk. The notice distance is the unit's own attack range plus a margin of
            one tenth of that range (`DRAFT-notice-margin`, Westley's number to change: 30 wu on a range of 300 ...), measured as weapon reach is
            (R-087-10). It is never the sensor radius: an enemy the side sees beyond the notice distance is not acquired, and the unit stands or
            walks on (...). A plain-moving unit never acquires (R-096-01)."
  R-096-02  "Given an attack-move, When an enemy its side can see comes within the unit's notice distance (E-11 R-087-04), Then the unit closes to
            attack range, halts and fires; when the lock ends (...) it resumes toward the point."

Scenes: a 2000 x 2000 canvas, the shipped tactical parameters (targeting by sight on). The Vanguard has attack range 300, sensor 700, 4 wu a tick; its
notice distance is 300 x 1.1 = 330 wu. Enemies are Supplies (they never fire, so only the test changes what the unit does) or, where an enemy must walk,
a Raider that plain-moves (a plain mover never acquires and never fires). Every scene asserts that its side sees the enemy, so a red test is red for the
notice distance and not for sight.
Detector bounds (not rules): ACQUIRE_TICKS 12 (a cohort turn comes within OM_TARGETING_COHORT_COUNT ticks; measured 7), the run lengths, ARRIVE 30 wu.
"""
import ctypes

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, dest, hp, pos, set_param, spawn, step, target

NOTICE_MARGIN = 0.1       # DRAFT-notice-margin (round5.md G1): the engine will name it OM_NOTICE_MARGIN in an internal header; no test can read it
RANGE = 300.0             # Vanguard attack range
NOTICE = RANGE * (1.0 + NOTICE_MARGIN)
ACQUIRE_TICKS = 12
IDLE_TICKS = 200
ARRIVE = 30.0             # R-099-04: a unit that followed route waypoints has arrived within 30 wu of its point, and its destination is cleared
BIG_HP = 1.0e6
ENEMY_STEP = 7.5          # a Raider's wu a tick (speed 150)


def _none(t):
    """The wrapper reports no target as 0 or -1; a target id is positive."""
    return t is None or t <= 0


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    return w


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _idle_scene(lib, wf, gap):
    """An idle Vanguard at (500, 1000) and a tough Supply of the other side `gap` wu east of it, which the unit's side sees."""
    w = _world(lib, wf)
    u = spawn(lib, w, VANGUARD, 0, 500.0, 1000.0)
    e = spawn(lib, w, SUPPLY, 1, 500.0 + gap, 1000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    step(lib, w)
    assert lib.om_player_can_see(w, 0, e) == 1, "scene broken: the side does not see the enemy at %.0f wu" % gap
    return w, u, e


def _run_idle(lib, w, u, e, ticks):
    """Per tick after the step: (target, position, enemy hp)."""
    out = []
    for _ in range(ticks):
        step(lib, w)
        out.append((target(lib, w, u), pos(lib, w, u), hp(lib, w, e)))
    return out


# ------------------------------------------------------------------ the notice distance bounds acquisition

def test_R_087_04_an_idle_unit_never_acquires_an_enemy_its_side_sees_beyond_its_notice_distance(lib, world_factory):
    """R-087-04 "an enemy the side sees beyond the notice distance is not acquired, and the unit stands or walks on": an idle Vanguard (range 300,
    notice 330, sensor 700) with a seen Supply 340 wu away. On every tick of 200 it holds no target, stands where it was, and the Supply is
    unhurt. Red today: the unit acquires within the sensor radius, walks to 300 and fires."""
    w, u, e = _idle_scene(lib, world_factory, 340.0)
    start, full = pos(lib, w, u), hp(lib, w, e)
    for n, (t, p, h) in enumerate(_run_idle(lib, w, u, e, IDLE_TICKS), 1):
        assert _none(t), "tick %d: the unit holds target %s, an enemy 340 wu away beyond its notice distance %.0f" % (n, t, NOTICE)
        assert p == start, "tick %d: the unit moved from %s to %s toward an enemy beyond its notice distance" % (n, start, p)
        assert h == full, "tick %d: the enemy beyond the notice distance was hurt" % n


def test_R_087_04_control_an_enemy_at_320_is_acquired_walked_to_range_300_and_fired_on(lib, world_factory):
    """R-087-04 control (the setup one step inside the rule; the twin of the test above, 20 wu nearer): the Supply 320 wu away, inside the notice
    distance 330, is acquired at the next cohort turn, the unit walks to attack range 300 and halts, and the Supply loses hit points."""
    w, u, e = _idle_scene(lib, world_factory, 320.0)
    full = hp(lib, w, e)
    rows = _run_idle(lib, w, u, e, IDLE_TICKS)
    first = next((n for n, r in enumerate(rows, 1) if r[0] == e), None)
    assert first is not None and first <= ACQUIRE_TICKS, "the enemy at 320 wu was not acquired within %d ticks (first %s)" % (ACQUIRE_TICKS, first)
    gap = _d(rows[-1][1], (820.0, 1000.0))
    assert gap <= RANGE + 1.0, "the unit stands %.1f wu from the enemy, beyond attack range %.0f" % (gap, RANGE)
    assert rows[-1][2] < full, "the unit never fired on the enemy it acquired"
    still = rows[-30:]
    assert all(r[1] == still[0][1] for r in still), "the unit kept moving after it was in range"


def test_R_087_04_the_notice_distance_is_the_attack_range_plus_a_tenth_at_both_edges(lib, world_factory):
    """R-087-04 "attack range plus a margin of one tenth of that range": an enemy 1 wu inside the notice distance is acquired, 1 wu outside it is not,
    over 200 ticks on every tick. Red today (the outer half): the sensor radius is the acquisition radius."""
    w, u, e = _idle_scene(lib, world_factory, NOTICE - 1.0)
    first = next((n for n, r in enumerate(_run_idle(lib, w, u, e, IDLE_TICKS), 1) if r[0] == e), None)
    assert first is not None and first <= ACQUIRE_TICKS, "an enemy at %.0f wu, inside the notice distance %.0f, was not acquired (first %s)" % (NOTICE - 1.0, NOTICE, first)
    w, u, e = _idle_scene(lib, world_factory, NOTICE + 1.0)
    start = pos(lib, w, u)
    for n, (t, p, _) in enumerate(_run_idle(lib, w, u, e, IDLE_TICKS), 1):
        assert _none(t) and p == start, "tick %d: target %s, at %s, for an enemy at %.0f wu beyond the notice distance %.0f" % (n, t, p, NOTICE + 1.0, NOTICE)


def test_R_087_04_an_enemy_walking_in_is_acquired_only_once_it_is_inside_the_notice_distance(lib, world_factory):
    """R-087-04, every tick: a Raider plain-moves west toward an idle Vanguard from 500 wu to 250 wu away. On no tick does the Vanguard hold a target
    while the enemy was farther than the notice distance at the end of the tick before (less one step of the enemy's own), and it holds it within
    ACQUIRE_TICKS of the enemy first being inside. Red today: it acquires at the sensor radius, 200 wu out."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, 500.0, 1000.0)
    e = spawn(lib, w, RAIDER, 1, 1000.0, 1000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    arr = (ctypes.c_uint32 * 1)(e)
    assert lib.om_command_move.raw(w, arr, 1, 750.0, 1000.0) == 0
    inside_since = None
    acquired = None
    prev_gap = _d(pos(lib, w, u), pos(lib, w, e))
    for n in range(1, 200):
        step(lib, w)
        gap = _d(pos(lib, w, u), pos(lib, w, e))
        if inside_since is None and gap <= NOTICE:
            inside_since = n
        if target(lib, w, u) == e and acquired is None:
            acquired = n
            assert prev_gap <= NOTICE + ENEMY_STEP + 1e-6, "tick %d: acquired the enemy when it stood %.1f wu away at the tick's start, beyond the notice distance %.0f" % (n, prev_gap, NOTICE)
        prev_gap = gap
    assert inside_since is not None, "scene broken: the enemy never came inside the notice distance"
    assert acquired is not None and acquired - inside_since <= ACQUIRE_TICKS, "enemy inside the notice distance since tick %s, acquired at %s" % (inside_since, acquired)


# ------------------------------------------------------------------ reach is the weapon's reach to that enemy

def _cross_layer_scene(lib, wf, gap):
    """A Vanguard on layer 1 at (500, 1000) with the range multiplier one layer down set to 0.5 (its reach to layer 0 is 150 wu, its notice distance
    there 165), and a tough Supply on layer 0 `gap` wu east that the side sees."""
    w = _world(lib, wf)
    assert lib.om_roster_set_reach(w, VANGUARD, 1, 1) == 0
    assert set_param(lib, w, "OM_TP_RANGE_DOWN_1", 0.5) == 0
    u = spawn(lib, w, VANGUARD, 0, 500.0, 1000.0, 1)
    e = spawn(lib, w, SUPPLY, 1, 500.0 + gap, 1000.0, 0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    step(lib, w)
    assert lib.om_player_can_see(w, 0, e) == 1, "scene broken: the side does not see the enemy one layer down at %.0f wu" % gap
    return w, u, e


def test_R_087_04_the_notice_distance_follows_the_reach_to_the_enemys_layer(lib, world_factory):
    """R-087-04 "measured as weapon reach is (R-087-10)", the reach table's multiplier for the target's layer: with the range multiplier one layer down
    set to 0.5 a Vanguard on layer 1 reaches 150 wu to a unit on layer 0 and notices it at 165. A seen Supply on layer 0, 160 wu away (inside 165,
    outside the reach 150), is acquired within ACQUIRE_TICKS, the unit walks to 150 wu and the Supply loses hit points. Red today: a unit acquires
    across layers only within its reach, so it stands where it is."""
    w, u, e = _cross_layer_scene(lib, world_factory, 160.0)
    full = hp(lib, w, e)
    rows = _run_idle(lib, w, u, e, IDLE_TICKS)
    first = next((n for n, r in enumerate(rows, 1) if r[0] == e), None)
    assert first is not None and first <= ACQUIRE_TICKS, "the enemy at 160 wu was not acquired within %d ticks (first %s)" % (ACQUIRE_TICKS, first)
    assert _d(rows[-1][1], (660.0, 1000.0)) <= 151.0, "the unit stands %.1f wu from the enemy, beyond the cross-layer reach 150" % _d(rows[-1][1], (660.0, 1000.0))
    assert rows[-1][2] < full, "the unit never fired"


def test_R_087_04_control_a_cross_layer_enemy_beyond_the_reach_notice_distance_is_never_acquired(lib, world_factory):
    """R-087-04 control for the test above (the setup 40 wu outside the rule; green today and after): the same Supply 200 wu away, inside the side's
    sight and inside 330 (the notice distance with no multiplier), outside 165. On every tick of 200 the unit holds no target, stands still and
    the Supply is unhurt."""
    w, u, e = _cross_layer_scene(lib, world_factory, 200.0)
    start, full = pos(lib, w, u), hp(lib, w, e)
    for n, (t, p, h) in enumerate(_run_idle(lib, w, u, e, IDLE_TICKS), 1):
        assert _none(t) and p == start and h == full, "tick %d: target %s, at %s, enemy hp %s: an enemy 200 wu away beyond the cross-layer notice distance 165" % (n, t, p, h)


# ------------------------------------------------------------------ an attack-mover and a plain mover

def _march(lib, wf, off, plain=False):
    """A Vanguard at (1000, 200) ordered to (1000, 1800); a tough Supply `off` wu east of the route at (1000 + off, 1000)."""
    w = _world(lib, wf)
    u = spawn(lib, w, VANGUARD, 0, 1000.0, 200.0)
    lib.om_unit_set_hp(w, u, 5000.0)
    e = spawn(lib, w, SUPPLY, 1, 1000.0 + off, 1000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    if plain:
        arr = (ctypes.c_uint32 * 1)(u)
        assert lib.om_command_move.raw(w, arr, 1, 1000.0, 1800.0) == 0
    else:
        attack_move(lib, w, [u], 1000.0, 1800.0)
    return w, u, e


def test_R_096_02_an_attack_mover_passing_an_enemy_at_340_walks_on(lib, world_factory):
    """R-096-02 "When an enemy its side can see comes within the unit's notice distance, Then the unit closes": an enemy 340 wu off the route is never
    within 330. The attack-mover marches 1600 wu: on every tick it holds no target, its goal is its ordered point, it keeps to the route (within 5 wu
    of x 1000) and the enemy is unhurt; it arrives (within 30 wu, its destination cleared from then on, R-099-04). Red today: it leaves the route at the sensor radius."""
    w, u, e = _march(lib, world_factory, 340.0)
    full = hp(lib, w, e)
    for n in range(1, 481):
        step(lib, w)
        assert _none(target(lib, w, u)), "tick %d: the marching unit took target %s from 340 wu, beyond its notice distance" % (n, target(lib, w, u))
        assert abs(pos(lib, w, u)[0] - 1000.0) <= 5.0, "tick %d: the unit left its route (at %s)" % (n, pos(lib, w, u))
        has, gx, gy = dest(lib, w, u)
        if has == 0:    # R-099-04: the destination is cleared on arrival, and only then
            assert _d(pos(lib, w, u), (1000.0, 1800.0)) <= ARRIVE, "tick %d: the unit's goal is gone %.1f wu from its ordered point (at %s)" % (n, _d(pos(lib, w, u), (1000.0, 1800.0)), pos(lib, w, u))
        else:
            assert abs(gx - 1000.0) <= 1e-6 and abs(gy - 1800.0) <= 1e-6, "tick %d: the unit's goal is %s, not its ordered point" % (n, (has, gx, gy))
    assert hp(lib, w, e) == full, "the enemy beyond the notice distance was hurt"
    assert _d(pos(lib, w, u), (1000.0, 1800.0)) <= ARRIVE, "the unit did not arrive: at %s" % (pos(lib, w, u),)
    assert dest(lib, w, u)[0] == 0, "the unit arrived and its destination is still set: %s" % (dest(lib, w, u),)


def test_R_096_02_control_an_attack_mover_passing_an_enemy_at_320_closes_and_fires(lib, world_factory):
    """R-096-02 control, the twin of the test above with the enemy 320 wu off the route (inside the notice distance): the attack-mover acquires it
    on the march, leaves the route to the east and the enemy loses hit points."""
    w, u, e = _march(lib, world_factory, 320.0)
    full = hp(lib, w, e)
    taken, left = None, False
    for n in range(1, 481):
        step(lib, w)
        if taken is None and target(lib, w, u) == e:
            taken = n
        left = left or pos(lib, w, u)[0] > 1000.0 + 5.0
    assert taken is not None, "the attack-mover never acquired an enemy 320 wu off its route"
    assert left, "it acquired the enemy but never left its route toward it"
    assert hp(lib, w, e) < full, "it never fired"


def test_R_096_01_a_plain_mover_inside_the_notice_distance_never_acquires(lib, world_factory):
    """R-087-04 / R-096-01 "A plain-moving unit never acquires": the march of the control above, as a plain move past the enemy 320 wu off the route
    (inside the notice distance): on every tick no target, the unit keeps to the route, the enemy is unhurt. Green today and after (the control that
    the notice distance is not what stops the unit in the tests above)."""
    w, u, e = _march(lib, world_factory, 320.0, plain=True)
    full = hp(lib, w, e)
    for n in range(1, 441):
        step(lib, w)
        assert _none(target(lib, w, u)), "tick %d: a plain-moving unit took target %s" % (n, target(lib, w, u))
        assert abs(pos(lib, w, u)[0] - 1000.0) <= 5.0, "tick %d: the plain mover left its route (at %s)" % (n, pos(lib, w, u))
    assert hp(lib, w, e) == full
