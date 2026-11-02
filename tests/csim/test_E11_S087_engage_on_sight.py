"""H-057 engage-on-sight (E-11 S-087, R-087-04 rewritten 2026-11-01; E-13 R-096-01/02/03; E-11 R-087-05/06/08).

Rule (docs/stories/H-057.md, "Rule"): "An idle unit (no order, or an attack-move that has arrived) or an
attack-moving unit with no target, when an enemy its side can see (E-12 R-093-02; reach across layers R-008-04) is
within its sensor radius, acquires the nearest such enemy at its cohort turn (R-087-08), anchors where it stands
(R-087-05), and walks toward it until the enemy is within attack range, then halts and fires (R-096-02). An
attack-mover leaves its slot and route to do so and resumes toward its point or slot after the engagement. An idle
unit holds where the engagement ends (R-087-06). The 200 wu leash (R-087-05, R-096-03) bounds the walk. A plain-moving
unit never acquires (R-096-01)."

Every scene runs sight off (OM_TP_TARGET_BY_SIGHT 0, the stage 1 setting): "sees" is within sensor radius.
Vanguard: range 300, sensor 700, speed 80, collision radius 15, one tick = 1/20 s. Raider: range 200, sensor 800, hp 250.
The slot-and-shape detector is imported from test_PP_attack_move_no_sight_pursuit.py (not edited).
Plain-march tick counts are 20 ticks per second at 80 wu/s, i.e. 4 wu per tick.
"""
import ctypes

from test_PP_attack_move_no_sight_pursuit import ARRIVAL, _centroid, _d, _shape_error
from test_PP_unit_support import (BOMBARD, RAIDER, VANGUARD, attack_move, dest, hp, pos, set_param, spawn, step, target)

SIGHT = "OM_TP_TARGET_BY_SIGHT"
PURSUE = "OM_TP_PURSUE_BY_STEERING"
LEASH = 200.0
STEP = 4.0            # wu a Vanguard walks in one tick (80 wu/s at 20 ticks/s); slack unit, not a rule number
MOVE_FIRST_TICKS = 375  # 1500 wu at 4 wu/tick, the plain march of tests 2 and 5


def _world(lib, world_factory, sight_off=True):
    w = world_factory(n_regions=1)
    if sight_off:
        assert set_param(lib, w, SIGHT, 0) == 0
    return w


def _holds(lib, w, u, enemy):
    return target(lib, w, u) == enemy


def _move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


# ---- 1. idle pair --------------------------------------------------------------------------------------------

def _idle_pair(lib, w, gap):
    a = spawn(lib, w, VANGUARD, 0, 2000.0, 1000.0)
    b = spawn(lib, w, VANGUARD, 1, 2000.0, 1000.0 + gap)
    return a, b


def test_R_087_04_two_idle_hostile_vanguards_400_apart_engage(lib, world_factory):
    """R-087-04 / S-087 / H-057: "An idle unit ... when an enemy its side can see ... is within its sensor radius,
    acquires the nearest such enemy ... and walks toward it until the enemy is within attack range, then halts and
    fires". Two idle hostile Vanguards 400 wu apart (sensor 700, range 300): within 200 ticks both hold a target,
    within 600 ticks one has taken damage. RED now: acquisition looks only within attack range 300."""
    w = _world(lib, world_factory)
    a, b = _idle_pair(lib, w, 400.0)
    full = hp(lib, w, a)
    both_by, hurt_by = None, None
    for t in range(1, 601):
        step(lib, w)
        if both_by is None and target(lib, w, a) == b and target(lib, w, b) == a:
            both_by = t
        if hurt_by is None and (hp(lib, w, a) < full or hp(lib, w, b) < full):
            hurt_by = t
    assert both_by is not None and both_by <= 200, "both did not hold a target within 200 ticks (got %s)" % both_by
    assert hurt_by is not None, "nobody took damage in 600 ticks"


def test_control_R_087_04_idle_pair_900_apart_stay_apart_and_unhurt(lib, world_factory):
    """Positive control (green now and after): 900 wu apart is outside sensor 700, so after 600 ticks neither holds a
    target and neither is damaged; the same detector (target/hp reads) is the one in the test above."""
    w = _world(lib, world_factory)
    a, b = _idle_pair(lib, w, 900.0)
    full = hp(lib, w, a)
    step(lib, w, 600)
    assert target(lib, w, a) in (-1, 0) and target(lib, w, b) in (-1, 0)
    assert hp(lib, w, a) == full and hp(lib, w, b) == full
    assert _d(pos(lib, w, a), pos(lib, w, b)) >= 899.0


# ---- 2. lone attack-mover ------------------------------------------------------------------------------------

def _lone_march(lib, w, plain=False, enemy_hp=20.0, enemy_faction=1, enemy_type=RAIDER):
    u = spawn(lib, w, VANGUARD, 0, 2000.0, 500.0)
    lib.om_unit_set_hp(w, u, 5000.0)    # the enemy may fight back once it too engages; the mover's life is not under test
    enemy = spawn(lib, w, enemy_type, enemy_faction, 2400.0, 1000.0)   # 400 wu off the x=2000 route
    lib.om_unit_set_hp(w, enemy, enemy_hp)
    if plain:
        _move(lib, w, [u], 2000.0, 2000.0)
    else:
        attack_move(lib, w, [u], 2000.0, 2000.0)
    return u, enemy


def test_R_087_04_lone_attack_mover_engages_an_enemy_400_off_its_path_then_resumes(lib, world_factory):
    """R-087-04 / R-096-02 / S-087 / H-057: "An attack-mover leaves its slot and route to do so and resumes toward
    its point ... after the engagement". A lone attack-mover marching 1500 wu passes an enemy 400 wu off its path: it
    acquires within 200 ticks, the enemy (low hp) dies, and the unit arrives within the plain march's ticks plus 400.
    RED now: 400 off the path is never inside attack range 300, so no target is ever taken."""
    w = _world(lib, world_factory)
    u, enemy = _lone_march(lib, w)
    acquired = None
    arrived = None
    for t in range(1, MOVE_FIRST_TICKS + 400 + 1):
        step(lib, w)
        if acquired is None and _holds(lib, w, u, enemy):
            acquired = t
        if arrived is None and _d(pos(lib, w, u), (2000.0, 2000.0)) <= ARRIVAL:
            arrived = t
    assert acquired is not None and acquired <= 200, "no target within 200 ticks (got %s)" % acquired
    assert hp(lib, w, enemy) <= 0.0, "the enemy never died"
    assert arrived is not None, "the unit never arrived: ended at %s" % (pos(lib, w, u),)


def test_control_R_096_02_lone_march_without_enemy_arrives_within_the_plain_ticks(lib, world_factory):
    """Positive control (green now and after): the same march with no enemy arrives inside the plain-march ticks, so the
    arrival read in the test above is a real arrival and the 375 + 400 bound is not slack on a broken scene."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, 2000.0, 500.0)
    attack_move(lib, w, [u], 2000.0, 2000.0)
    step(lib, w, MOVE_FIRST_TICKS + 40)
    assert _d(pos(lib, w, u), (2000.0, 2000.0)) <= ARRIVAL


# ---- 3. group of 8 -------------------------------------------------------------------------------------------

GROUP_N, GROUP_SPACING = 8, 40.0
GX0, GY = 1000.0, 1000.0


def _group(lib, w, enemy_xy=None):
    """8 attack-movers in a line, one group order to a click 2000 wu north of the line's centroid (the 280 wu span is
    inside R-095-03's 450 wu, so no chunking). Returns (ids, enemy, slots, [(ids, click)])."""
    ids = [spawn(lib, w, VANGUARD, 0, GX0 + i * GROUP_SPACING, GY) for i in range(GROUP_N)]
    for u in ids:
        lib.om_unit_set_hp(w, u, 5000.0)
    cx = GX0 + (GROUP_N - 1) * GROUP_SPACING / 2.0
    click = (cx, GY + 2000.0)
    enemy = None
    if enemy_xy is not None:
        enemy = spawn(lib, w, RAIDER, 1, *enemy_xy)
        lib.om_unit_set_hp(w, enemy, 30.0)
    attack_move(lib, w, ids, *click)
    slots = {}
    for u in ids:
        has, x, y = dest(lib, w, u)
        assert has == 1, "fixture: a group unit has no slot after the group attack-move"
        slots[u] = (x, y)
    assert len({(round(x), round(y)) for x, y in slots.values()}) == GROUP_N, "fixture: slots collapsed to the click"
    return ids, enemy, slots, [(ids, click)]


def test_R_087_04_a_group_of_8_attack_movers_engages_a_lone_enemy_400_off_the_line_then_reaches_its_slots(lib, world_factory):
    """R-087-04 / R-096-02 / S-087 / H-057: "An attack-mover leaves its slot and route to do so and resumes toward its
    point or slot after the engagement". 8 attack-movers with a lone (low hp) enemy 400 wu east of the line's east end:
    at least one member holds it as a target, the members that see it engage, it dies, and after that every member ends
    within the arrival radius of its own slot (the slot-and-shape detector of test_PP_attack_move_no_sight_pursuit.py).
    RED now: 400 wu off the route is outside attack range 300 for every member, so nobody ever engages."""
    w = _world(lib, world_factory)
    east = GX0 + (GROUP_N - 1) * GROUP_SPACING
    ids, enemy, slots, clicks = _group(lib, w, (east + 400.0, GY + 1000.0))
    engaged = set()
    for _ in range(1000):
        step(lib, w)
        for u in ids:
            if target(lib, w, u) == enemy:
                engaged.add(u)
    assert engaged, "no member of the group ever held the enemy as a target"
    assert hp(lib, w, enemy) <= 0.0, "the enemy never died"
    miss = max(_d(pos(lib, w, u), slots[u]) for u in ids)
    assert miss <= ARRIVAL, "after the fight a member ended %.1f wu from its slot (limit %.1f)" % (miss, ARRIVAL)


def test_control_R_096_02_group_of_8_without_an_enemy_reaches_its_slots_in_shape(lib, world_factory):
    """Positive control (green now and after): the same 8-unit group with no enemy ends at its slots with the shape
    intact, so the slot-miss and shape reads of the test above can come out clean on this scene."""
    w = _world(lib, world_factory)
    ids, _, slots, clicks = _group(lib, w)
    held = 0.0
    for _ in range(1000):
        step(lib, w)
        held = max(held, _shape_error(lambda u: pos(lib, w, u), slots, clicks))
    assert max(_d(pos(lib, w, u), slots[u]) for u in ids) <= ARRIVAL
    assert held <= ARRIVAL


# ---- 4. leash ------------------------------------------------------------------------------------------------

COLLISION_RADIUS = 15.0
RETURN_TOL = 1.5 * COLLISION_RADIUS   # OM_ARRIVAL_TOLERANCE_MULT x OM_UNIT_COLLISION_RADIUS


def _chase(lib, w, utype, speed, ticks, gap=400.0):
    """An idle `utype` at its post (2000, 500) and a same-type enemy `gap` wu north that plain-moves away at the same speed.
    Returns the per-tick (pursuer position, enemy position, pursuer target, enemy id)."""
    a = spawn(lib, w, utype, 0, 2000.0, 500.0)
    b = spawn(lib, w, utype, 1, 2000.0, 500.0 + gap)
    _move(lib, w, [b], 2000.0, 3900.0)
    trace = []
    for _ in range(ticks):
        step(lib, w)
        trace.append((pos(lib, w, a), pos(lib, w, b), target(lib, w, a)))
    return a, b, trace


def test_R_087_05_idle_pursuer_is_bounded_by_its_sensor_radius_returns_and_holds(lib, world_factory):
    """R-087-05 / R-096-03 / S-087 / H-057 + DEC-leash-anchor-return-2026-11-01: the leash is the type's own sensor
    radius, the anchor is set once on acquiring from rest and not reset while pursuing or returning, and after a drop an
    idle unit walks back to its anchor. An idle Vanguard (sensor 700) at its post sees an enemy 400 wu off that walks away at
    the same speed (80 wu/s, a plain move, so it never acquires): it acquires within 200 ticks, keeps the target past 200 wu
    from its anchor, its distance from the anchor never exceeds 700 plus one tick's step, after the drop it is back within
    1.5 collision radii of its anchor, and once the enemy is out of sensor range it holds no target and does not move for 100
    ticks. RED now: it never acquires and never moves."""
    w = _world(lib, world_factory)
    a, b, trace = _chase(lib, w, VANGUARD, 80.0, 700)
    anchor = (2000.0, 500.0)
    acquired = next((i + 1 for i, t in enumerate(trace) if t[2] == b), None)
    assert acquired is not None and acquired <= 200, "no target within 200 ticks (got %s)" % acquired
    held_far = max((_d(t[0], anchor) for t in trace if t[2] == b), default=0.0)
    assert held_far > 200.0 + STEP, "it dropped the target inside the old 200 wu leash (held out to %.1f wu)" % held_far
    far = max(_d(t[0], anchor) for t in trace)
    assert far <= 700.0 + STEP, "the pursuer went %.1f wu from its anchor (leash = sensor radius 700)" % far
    assert far >= 700.0 - 3 * STEP, "it stopped at %.1f wu: it did not walk its sensor radius out" % far
    peak = max(range(len(trace)), key=lambda i: _d(trace[i][0], anchor))
    back = next((i for i in range(peak, len(trace)) if _d(trace[i][0], anchor) <= RETURN_TOL), None)
    assert back is not None, "after the drop it never came back within %.1f wu of its anchor" % RETURN_TOL
    assert _d(trace[back][0], trace[back][1]) > 700.0, "fixture: the enemy was still inside sensor range when it got back"
    p = trace[back][0]
    for _ in range(100):
        step(lib, w)
        assert target(lib, w, a) in (-1, 0), "it took a target again with the enemy out of sensor range"
        assert _d(pos(lib, w, a), p) <= 0.5, "it moved after getting back to its anchor"


def test_R_087_05_the_leash_is_per_type_a_raider_drops_at_its_own_sensor_radius(lib, world_factory):
    """R-087-05 / S-087 / H-057 + DEC-leash-anchor-return-2026-11-01: "every read of OM_ATTACK_MOVE_LEASH_DIST becomes the
    unit's profile sensor_radius" (per type, not one number). A Raider (sensor 800, speed 150) chasing a Raider that walks
    away at its speed reaches 800 wu from its anchor, past the Vanguard's 700, and no further than 800 plus one tick's step.
    RED now: it never acquires. (No type has a smaller effective radius than the Vanguard's 700: Bastion and Bombard have
    sensor 300 but range 800 and 1200, see the writer's report.)"""
    w = _world(lib, world_factory)
    a, b, trace = _chase(lib, w, RAIDER, 150.0, 400)
    anchor = (2000.0, 500.0)
    step_wu = 150.0 / 20.0
    far = max(_d(t[0], anchor) for t in trace)
    assert any(t[2] == b for t in trace), "the Raider never acquired the enemy"
    assert far <= 800.0 + step_wu, "the Raider went %.1f wu from its anchor (its sensor radius is 800)" % far
    assert far > 700.0 + step_wu, "the Raider stopped at %.1f wu: bounded by the Vanguard's 700, not its own 800" % far


def test_R_087_04_idle_pursuer_reaches_and_shoots_a_standing_enemy_400_off(lib, world_factory):
    """R-087-04 / S-087 / H-057 (the leash test's control, story test 4): the enemy standing still at 400 wu is reached
    (inside attack range 300) and shot. RED now: an idle unit never walks on a sight-range enemy."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, VANGUARD, 0, 2000.0, 500.0)
    b = spawn(lib, w, VANGUARD, 1, 2000.0, 900.0)
    full = hp(lib, w, b)
    step(lib, w, 400)
    assert _d(pos(lib, w, a), pos(lib, w, b)) <= 300.0, "it did not close to attack range"
    assert hp(lib, w, b) < full, "it closed but never fired"


def test_control_R_096_03_walking_enemy_detector_the_plain_move_walks_at_the_pursuers_speed(lib, world_factory):
    """Positive control (green now and after): the plain-moving Vanguard of the leash test walks 80 wu/s (4 wu a tick)
    away from an idle neighbour 900 wu off that never reacts, so 'walks away at the same speed' holds in that scene."""
    w = _world(lib, world_factory)
    spawn(lib, w, VANGUARD, 0, 100.0, 100.0)
    b = spawn(lib, w, VANGUARD, 1, 2000.0, 900.0)
    _move(lib, w, [b], 2000.0, 3900.0)
    step(lib, w, 50)
    run = _d(pos(lib, w, b), (2000.0, 900.0))
    assert abs(run - 50 * STEP) <= 2 * STEP, "walked %.1f wu in 50 ticks" % run


def test_R_087_05_the_leash_is_the_max_of_sensor_and_range_a_bombard_keeps_a_target_to_1200(lib, world_factory):
    """R-087-05 / S-087 / H-057 + DEC-leash-param-2026-11-01: the leash is max(sensor_radius, attack_range) per type. A Bombard
    (sensor 300, range 1200, so 1200) attack-moving acquires a target 150 wu ahead, then stands 1150 wu from its anchor with the
    target 150 wu beside it, in range: it keeps the target on every tick (a leash of its sensor radius 300, or of any Vanguard
    or Raider number, would drop it). At 1250 wu from the anchor it drops it. Vanguard 700 and Raider 800 are the other two
    points (tests above). RED now: the leash is 200."""
    for off, kept in ((1150.0, True), (1250.0, False)):
        w = _world(lib, world_factory)
        u = spawn(lib, w, BOMBARD, 0, 0.0, 0.0)
        enemy = spawn(lib, w, VANGUARD, 1, 0.0, -150.0)
        lib.om_unit_set_hp(w, enemy, 5000.0)
        attack_move(lib, w, [u], 0.0, -3000.0)
        for _ in range(40):
            step(lib, w)
            if target(lib, w, u) == enemy:
                break
        assert target(lib, w, u) == enemy, "fixture: the Bombard never acquired"
        ax, ay = pos(lib, w, u)
        lib.om_unit_teleport(w, u, ax, ay - off, 0)
        lib.om_unit_teleport(w, enemy, ax + 150.0, ay - off, 0)
        seen = []
        for _ in range(3):
            step(lib, w)
            seen.append(target(lib, w, u))
        if kept:
            assert seen == [enemy] * 3, "a Bombard %.0f wu from its anchor dropped its target: %s" % (off, seen)
        else:
            assert -1 in seen, "a Bombard %.0f wu from its anchor kept its target: %s" % (off, seen)


# ---- 5. plain move -------------------------------------------------------------------------------------------

def test_control_R_096_01_a_plain_move_past_an_enemy_400_off_takes_no_target_and_arrives(lib, world_factory):
    """R-096-01 / S-087 / H-057 (green now and after): "A plain-moving unit never acquires". The unit of test 2 on a
    plain move past the enemy 400 wu off its path holds no target on any tick and arrives."""
    w = _world(lib, world_factory)
    u, enemy = _lone_march(lib, w, plain=True, enemy_hp=5000.0)
    for _ in range(MOVE_FIRST_TICKS + 400):
        step(lib, w)
        if _d(pos(lib, w, u), (2000.0, 2000.0)) <= ARRIVAL:
            break   # arrived: the idle unit may now engage under R-087-04 (H-057); the plain-move phase is over
        assert target(lib, w, u) in (-1, 0), "a plain-moving unit took a target"
    assert _d(pos(lib, w, u), (2000.0, 2000.0)) <= ARRIVAL


# ---- 6. the L-0054 shape in miniature ------------------------------------------------------------------------

BLOB = 16
KILL_TICK = 900


def _blobs(lib, w):
    """Two 16-unit blobs, each a file 40 wu apart along the line of advance (600 wu deep, as L-0054's 128-unit blobs are deep
    against attack range 300), A on the west, B on the east, both attack-moved to the same point."""
    a_ids, b_ids = [], []
    for i in range(BLOB):
        a_ids.append(spawn(lib, w, VANGUARD, 0, 1000.0 + i * 40.0, 2000.0))
        b_ids.append(spawn(lib, w, VANGUARD, 1, 7000.0 - i * 40.0, 2000.0))
    attack_move(lib, w, a_ids, 4000.0, 2000.0)
    attack_move(lib, w, b_ids, 4000.0, 2000.0)
    return a_ids, b_ids


def _alive(lib, w, ids):
    return [u for u in ids if hp(lib, w, u) > 0.0]


def _run_blobs(lib, w, ticks):
    a_ids, b_ids = _blobs(lib, w)
    for t in range(ticks):
        step(lib, w)
        if t + 1 == KILL_TICK:
            for ids in (a_ids, b_ids):
                for u in sorted(_alive(lib, w, ids), key=lambda u: abs(pos(lib, w, u)[0] - 4000.0))[:12]:
                    lib.om_unit_set_hp(w, u, 0.0)
        if not _alive(lib, w, a_ids) or not _alive(lib, w, b_ids):
            return a_ids, b_ids, t + 1
    return a_ids, b_ids, None


def test_R_087_04_two_16_unit_blobs_attack_moved_to_one_point_fight_to_elimination(lib, world_factory):
    """R-087-04 / R-096-02 / S-087 / H-057, the L-0054 stall in miniature: two 16-unit blobs attack-moved to the same
    point, the 12 units nearest the point of each removed by script at tick 900 (after first contact); the fight ends by
    elimination (one side wiped) within 6000 ticks, not by a standoff. RED now: the survivors stand at their slots outside
    attack range 300 and inside sensor 700, and nobody walks the last wu."""
    w = _world(lib, world_factory)
    a_ids, b_ids, done = _run_blobs(lib, w, 6000)
    assert done is not None, "standoff: %d vs %d survivors, %.0f wu apart at tick 6000" % (
        len(_alive(lib, w, a_ids)), len(_alive(lib, w, b_ids)),
        _d(_centroid([pos(lib, w, u) for u in _alive(lib, w, a_ids)]), _centroid([pos(lib, w, u) for u in _alive(lib, w, b_ids)])))


def test_control_R_087_04_miniature_scene_does_contact_and_script_kill_removes_12_a_side(lib, world_factory):
    """Positive control (green now and after): the scene reaches tick 900 with both blobs intact-or-damaged, and the
    scripted removal leaves at most 4 survivors a side; so the standoff above is the engine's, not an empty scene."""
    w = _world(lib, world_factory)
    a_ids, b_ids = _blobs(lib, w)
    step(lib, w, KILL_TICK - 1)
    assert len(_alive(lib, w, a_ids)) > 4 and len(_alive(lib, w, b_ids)) > 4, "fixture: a blob was already thinned"
    for ids in (a_ids, b_ids):
        for u in sorted(_alive(lib, w, ids), key=lambda u: abs(pos(lib, w, u)[0] - 4000.0))[:12]:
            lib.om_unit_set_hp(w, u, 0.0)
    assert len(_alive(lib, w, a_ids)) <= 4 and len(_alive(lib, w, b_ids)) <= 4


def test_PP_baseline_switch_0_blob_scene_runs(lib, world_factory):
    """Run-only (not asserted, per H-057 test 6): the same miniature under OM_TP_PURSUE_BY_STEERING 0, the baseline arm,
    runs to its end without error."""
    w = _world(lib, world_factory)
    assert set_param(lib, w, PURSUE, 0) == 0
    _run_blobs(lib, w, 1500)
