"""E-13 R-097-10 (engine rules round 4, T10): an idle unit takes the push from a mover of its own side; a walker is not held for ever by an idle own unit in its way.

Rule words proved, word for word (docs/bible/epics/E-13-movement-and-command.md):
  R-097-10  "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement, except that an idle unit (no move
            target, not engaged) takes the full displacement from a mover of its own side and none from an enemy mover, which takes all of it; given both are stationary and either was displaced earlier in the
            tick, they split the displacement equally. Every unit starts pair checks, moving or stopped, so a unit that walks into a stopped one is pushed out; ..."
  R-097-03  "Given a moving unit, When it steps, Then it probes 40 wu ahead; if a unit on its layer blocks the probe (an idle unit of its own side does not block: idle means no move target and not engaged; an
            enemy always does) it tries +30, -30, +60, -60, +90 and -90 degrees from its heading, in that order, and takes the first clear one; if none is clear it continues straight."
  R-097-05  "Given two units on the same layer within 30 wu (2 x radius 15), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick."
  R-097-08  "Given enemy units, When colliding, Then they collide like allies; nobody passes through anybody."
  R-096-08  (the guard clause) "... a collision push never carries a guard past the radius (DRAFT readings, DEC-engine-rules-round2-2026-11-11, Westley may veto)."
Owner's words behind R-097-10 and R-097-03 (decisions.md, DEC-Q087-02-2026-10-22): "Idle own units are not walls: a moving unit passes through idle units of its own side, which step aside (soft collision), as in the
reference RTS; no order ever stalls silently". The reference model is StarCraft 2 (DEC-sc2-reference-model-2026-11-11).
Rule pins: R-097-10, R-097-03, R-097-05, R-097-08, R-096-08.

Trace (engine-rules-baseline/x3/findings.txt, section I29, main e2dcee93): in `om_move_collide_pair` (csrc/tactical_move.c) a pair with exactly one stationary unit gives the mover the whole overlap, whoever the
stationary unit is. A walker whose way or destination lies in a ring of arrived own units takes its 4 wu step and is pushed back to the same spot, every tick, for the rest of the fight; it never waits and no route
fails (the sweep's I29: L-0028 sight on 12,655 unit-ticks, sight off 10,833 all one unit, control 6,496; L-0045 control 9,280). The whole-fight twin is
tests/skilllab/arena/test_engine_rules_r4_idle_yield.py. tests/csim/test_PP_move_collision.py and test_PP_move_collision_a5.py pinned the old reading with own-side stopped units and now use an enemy one
(Test-defect, see their docstrings).

Configuration: the shipped one for a csim scene: walking units (the Vanguard is set to the walking kind, as the lab does), steering and route-around-terrain on (their defaults), targeting by sight on (the default),
a 2000 x 2000 canvas, no obstacles (the geometry is units only). Vanguard: 4 wu a tick, attack range 300, collision diameter 30 wu.

Scenes (side 0 is the mover's side; the enemy Supply never fires, so only the test changes what a unit does):
  YIELD   mover M at (300,500) ordered to GOAL; idle own Vanguard(s) in its way. Today: the mover swerves round a single idle unit (the probe blocks on it, R-097-03 unbuilt) and, when GOAL is inside the
          idle unit's 30 wu, stops at the edge of the circle with a destination for ever. Measured on this tree: GOAL 20 wu behind one idle unit: M at (530.0, 500.0) from tick 90 on, 10 wu from GOAL, destination
          kept, idle unit unmoved; a row of three across the path, GOAL (560,500): M at (473.5, 515.9) from tick 60, 87.9 wu from GOAL; a ring of four round GOAL: M at (530.0, 528.9), 41.6 wu away.
  HELD    the same with the unit in the way an enemy Supply, an engaged own Vanguard (it holds a target and fires), or a guard: M stops 30 wu away and stays; the unit in the way never moves. Green today.

Detector bounds (not rules; Westley's to change): BACKSLIDE 1.0 wu (DRAFT-yield-backslide: the most the mover's distance to GOAL may rise in one tick; a tick that pushes it back to where it was is a rise of the whole
step), PASS_FACTOR 1.5 and PASS_SLACK 10 ticks (DRAFT-yield-path-factor, DRAFT-yield-slack-ticks: the mover arrives within ceil(1.5 x straight distance / 4 wu) + 10 ticks; the lone mover walks a gentle arc, 70 ticks for
260 wu where straight is 65, and the swerve round a unit costs more), ARRIVE 5 wu (one step; DRAFT-yield-arrive), POS_TOL 0.05 wu (numeric slack of the C's cheap trig, as the PP files), CONTACT 0.5 wu (a pair within
30.5 wu has touched).
Controls green today: a lone mover walks to GOAL; two own movers are still pushed apart to 30 wu (R-097-05); an idle own unit left alone stays idle; the HELD scenes.
"""
import ctypes
import math

import pytest

from conftest import OMFeature, OMWorldP
from test_PP_unit_support import SUPPLY, VANGUARD, dest, pos, spawn, step

WALKING = 1                         # OM_MOVE_WALKING
CANVAS = 2000.0
DIAMETER = 30.0                     # R-097-05: 2 x radius 15
SPEED = 4.0                         # Vanguard wu per tick (roster)
POS_TOL = 0.05                      # numeric slack, not a rule threshold
CONTACT = 0.5                       # detector bound
BACKSLIDE = 1.0                     # DRAFT-yield-backslide
PASS_FACTOR = 1.5                   # DRAFT-yield-path-factor
PASS_SLACK = 10                     # DRAFT-yield-slack-ticks
ARRIVE = 5.0                        # DRAFT-yield-arrive
GUARD_RADIUS = 200.0                # R-096-08
START = (300.0, 500.0)
IDLE_XY = (500.0, 500.0)


def _budget(a, b):
    return math.ceil(PASS_FACTOR * math.hypot(a[0] - b[0], a[1] - b[1]) / SPEED) + PASS_SLACK


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    return w


def _move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def _guard(lib, w, ids):
    fn = getattr(lib.om_command_guard, "raw", lib.om_command_guard)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    fn.restype = ctypes.c_int
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return fn(w, arr, len(ids))


def _scene(lib, wf, others, goal, mover_first=True):
    """(world, mover, [other ids]). `others` is a list of (unit type, faction, x, y). Ids follow the spawn order, mover_first or not (the pair check runs from the lower id)."""
    w = _world(lib, wf)
    if mover_first:
        m = spawn(lib, w, VANGUARD, 0, *START)
    ids = [spawn(lib, w, t, f, x, y) for t, f, x, y in others]
    if not mover_first:
        m = spawn(lib, w, VANGUARD, 0, *START)
    assert _move(lib, w, [m], *goal) == 0
    return w, m, ids


def _trace(lib, w, m, others, ticks):
    """Per tick after the step: {"m": mover pos, "o": [other positions], "has": mover has a destination}."""
    out = []
    for _ in range(ticks):
        step(lib, w)
        out.append({"m": pos(lib, w, m), "o": [pos(lib, w, u) for u in others], "has": dest(lib, w, m)[0] == 1})
    return out


def _arrival_tick(tr, goal):
    """First 1-based tick at which the mover has no destination and stands within ARRIVE of the goal, or None."""
    for k, row in enumerate(tr, 1):
        if not row["has"] and _dist(row["m"], goal) <= ARRIVE:
            return k
    return None


def _worst_rise(tr, start, goal):
    """The largest one-tick rise of the mover's distance to the goal."""
    prev, worst = _dist(start, goal), 0.0
    for row in tr:
        d = _dist(row["m"], goal)
        worst = max(worst, d - prev)
        prev = d
    return worst


def _gets_through(lib, wf, others, goal, mover_first=True):
    """The YIELD asserts: the mover arrives within the budget, never loses more than BACKSLIDE in a tick, and the units in its way took the push (they stand 30 wu from it at the end and some of them moved)."""
    w, m, ids = _scene(lib, wf, others, goal, mover_first)
    n = _budget(START, goal)
    tr = _trace(lib, w, m, ids, n)
    got = _arrival_tick(tr, goal)
    last = tr[-1]
    assert got is not None, "the mover never arrived in %d ticks: at %s (%.1f wu from %s), destination kept %s" % (n, last["m"], _dist(last["m"], goal), goal, last["has"])
    assert _worst_rise(tr, START, goal) <= BACKSLIDE, "the mover was pushed back %.1f wu in one tick (bound %.1f)" % (_worst_rise(tr, START, goal), BACKSLIDE)
    end = tr[got - 1]
    assert all(_dist(end["m"], o) >= DIAMETER - POS_TOL for o in end["o"]), "the units in the way were left inside the mover's 30 wu: %s" % [round(_dist(end["m"], o), 1) for o in end["o"]]
    moved = [i for i, o in enumerate(end["o"]) if _dist(o, (others[i][2], others[i][3])) > POS_TOL]
    assert moved, "no idle unit took a push: the mover went round them or was stopped, the idle units stood still"
    return tr, got


# ------------------------------------------------------------------ the rule (red today)

@pytest.mark.parametrize("mover_first", [True, False], ids=["mover_lower_id", "idle_lower_id"])
def test_R_097_10_a_mover_ordered_through_an_idle_own_unit_arrives_and_the_idle_unit_takes_the_push(lib, world_factory, mover_first):
    """R-097-10: "... an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side ..." (R-097-03: an idle own unit does not block). M (side 0) is ordered to a point 20 wu
    behind an idle side 0 Vanguard at (500,500), GOAL (520,500), 220 wu away: the goal lies inside the idle unit's 30 wu, so the mover can arrive only if the idle unit steps aside. It arrives within the budget (93 ticks),
    its distance to GOAL never rises by more than BACKSLIDE in a tick, and the idle unit is displaced (30 wu from M at the end). Both id orders: the pair check runs from the lower id. Red today: M stands at
    (530.0, 500.0), 10 wu from GOAL, with its destination, from tick 90 on; the idle unit has not moved."""
    _gets_through(lib, world_factory, [(VANGUARD, 0, *IDLE_XY)], (520.0, 500.0), mover_first)


def test_R_097_10_the_mover_takes_none_of_the_push_it_walks_its_full_step_through_the_contact(lib, world_factory):
    """R-097-10: the idle own unit "takes the full displacement", so the mover takes none: on every tick on which the mover is touching the idle unit (within 30.5 wu) and has not arrived, its step is the full walking
    step of the roster, SPEED = 4 wu within 0.5 wu (the lone mover's step is 4.0). Same scene as the test above. Red today: the mover's contact ticks end with a step of 0 (pushed back)."""
    goal = (520.0, 500.0)
    w, m, ids = _scene(lib, world_factory, [(VANGUARD, 0, *IDLE_XY)], goal)
    tr = _trace(lib, w, m, ids, _budget(START, goal))
    prev, contact = START, []
    for k, row in enumerate(tr, 1):
        step_len = _dist(prev, row["m"])
        if row["has"] and _dist(row["m"], row["o"][0]) <= DIAMETER + CONTACT:
            contact.append((k, round(step_len, 2)))
        prev = row["m"]
    assert contact, "premise: the mover never touched the idle unit (it went round at 30+ wu)"
    short = [(k, s) for k, s in contact if s < SPEED - 0.5]
    assert not short, "ticks in contact on which the mover walked less than a full step (pushed back): %s" % short[:8]


@pytest.mark.parametrize("mover_first", [True, False], ids=["mover_lower_id", "idle_lower_id"])
def test_R_097_10_a_row_of_three_idle_own_units_across_the_path_lets_the_mover_through(lib, world_factory, mover_first):
    """R-097-10 / R-097-03: three idle side 0 Vanguards stand in a row across the way at (500,470), (500,500), (500,530) (30 wu apart, 90 wu of wall); M goes from (300,500) to (560,500), 260 wu, 60 wu behind
    the row. It arrives within the budget (ceil(1.5 x 260 / 4) + 10 = 108 ticks), is never pushed back more than BACKSLIDE in a tick, and at least one idle unit took the push. Red today: M stops at
    (473.5, 515.9) from tick 60 on, 87.9 wu from GOAL, with its destination, and the row has not moved."""
    row = [(VANGUARD, 0, 500.0, 470.0), (VANGUARD, 0, 500.0, 500.0), (VANGUARD, 0, 500.0, 530.0)]
    _gets_through(lib, world_factory, row, (560.0, 500.0), mover_first)


def test_R_097_10_a_destination_inside_a_ring_of_idle_own_units_is_reached(lib, world_factory):
    """R-097-10 (the I29 geometry: unit 18 of L-0028 sight off, its destination 92 wu away and three arrived own units 30 wu round the spot where it stood): four idle side 0 Vanguards at (540,500), (580,500),
    (560,470), (560,530), 40 wu round GOAL (560,500). M from (300,500) arrives within the budget, is never pushed back more than BACKSLIDE in a tick, and the units of the ring took the push. Red today: M stops at
    (530.0, 528.9), 41.6 wu from GOAL, destination kept."""
    ring = [(VANGUARD, 0, 540.0, 500.0), (VANGUARD, 0, 580.0, 500.0), (VANGUARD, 0, 560.0, 470.0), (VANGUARD, 0, 560.0, 530.0)]
    _gets_through(lib, world_factory, ring, (560.0, 500.0))


# ------------------------------------------------------------------ what must not yield (green today, stays green)

def test_R_097_10_an_idle_enemy_unit_takes_none_of_the_push_the_mover_goes_round_or_is_held(lib, world_factory):
    """R-097-10: "... none from an enemy mover, which takes all of it" (R-097-08: nobody passes through anybody). An idle enemy Supply stands at (500,500); M (side 0) is ordered to (520,500), a point inside the
    enemy's 30 wu. For 100 ticks the enemy never moves (exactly), M never comes closer than 30 wu to it, and M touched it (premise: a pair that never met proves nothing). M is held at the circle, with its
    destination: the unit that is not its own side's is a wall. Green today (the old rule gives the mover everything); red against a build that lets any idle unit step aside."""
    w, m, ids = _scene(lib, world_factory, [(SUPPLY, 1, *IDLE_XY)], (520.0, 500.0))
    tr = _trace(lib, w, m, ids, 100)
    ds = [_dist(r["m"], r["o"][0]) for r in tr]
    assert min(ds) <= DIAMETER + CONTACT, "premise: the mover never touched the enemy (closest %.1f)" % min(ds)
    assert all(r["o"][0] == IDLE_XY for r in tr), "the idle enemy was pushed by an enemy mover: first at tick %d" % (1 + next(k for k, r in enumerate(tr) if r["o"][0] != IDLE_XY))
    assert min(ds) >= DIAMETER - POS_TOL, "the mover came %.2f wu from the enemy (30 wu is the diameter)" % min(ds)
    assert tr[-1]["has"], "the mover lost its destination while held at the enemy"


def test_R_097_10_an_idle_enemy_in_the_way_is_gone_round_with_the_goal_behind_it(lib, world_factory):
    """R-097-10 / R-097-03 (an enemy always blocks the probe): the same enemy Supply with GOAL 60 wu behind it at (560,500): the mover goes round it, arrives within the budget (108 ticks), and on no tick
    is it nearer than 30 wu to the enemy, which never moved. Green today."""
    goal = (560.0, 500.0)
    w, m, ids = _scene(lib, world_factory, [(SUPPLY, 1, *IDLE_XY)], goal)
    tr = _trace(lib, w, m, ids, _budget(START, goal))
    assert _arrival_tick(tr, goal) is not None, "the mover never got round the enemy: at %s" % (tr[-1]["m"],)
    assert min(_dist(r["m"], r["o"][0]) for r in tr) >= DIAMETER - POS_TOL
    assert all(r["o"][0] == IDLE_XY for r in tr)


def test_R_097_10_a_unit_halted_by_engagement_is_not_idle_it_does_not_step_aside_for_its_own_side(lib, world_factory):
    """R-097-10 first clause: "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement"; the exception names the
    idle unit "(no move target, not engaged)". A side 0 Vanguard E at (500,500) holds a target and fires (an enemy Supply 200 wu south at (500,700) with 1e6 hp, in range 300 and in sight: premise, dumped: E's target
    is the Supply on tick 1 and the Supply loses hp). M (side 0) is ordered onto E's spot. For 100 ticks E never moves (exactly), M never comes within 30 wu of it, and M touched it. Green today; red against a build
    that treats an engaged unit as idle (E would step aside, a unit in a firefight shoved about by its own side)."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, *START)
    e = spawn(lib, w, VANGUARD, 0, *IDLE_XY)
    s = spawn(lib, w, SUPPLY, 1, 500.0, 700.0)
    lib.om_unit_set_hp(w, s, 1.0e6)
    assert _move(lib, w, [m], *IDLE_XY) == 0
    tr, held = [], []
    for _ in range(100):
        step(lib, w)
        tr.append({"m": pos(lib, w, m), "o": [pos(lib, w, e)], "has": dest(lib, w, m)[0] == 1})
        held.append(lib.om_unit_get_target(w, e))
    assert held[0] == s and lib.om_unit_get_hp(w, s) < 1.0e6, "premise: E holds the Supply as its target and fires (target %s, supply hp %s)" % (held[0], lib.om_unit_get_hp(w, s))
    ds = [_dist(r["m"], r["o"][0]) for r in tr]
    assert min(ds) <= DIAMETER + CONTACT, "premise: the mover never touched E (closest %.1f)" % min(ds)
    assert all(r["o"][0] == IDLE_XY for r in tr), "the engaged unit stepped aside for a mover of its own side: first at tick %d" % (1 + next(k for k, r in enumerate(tr) if r["o"][0] != IDLE_XY))
    assert min(ds) >= DIAMETER - POS_TOL


def test_R_097_10_a_guard_at_its_post_is_not_carried_out_of_its_radius_by_a_mover_of_its_own_side(lib, world_factory):
    """R-096-08: "... a collision push never carries a guard past the radius" (GUARD_RADIUS = 200 wu from the post) and R-097-10: a guard is on an order, so it is not "idle (no move target, not engaged)".
    READING (the rule text does not settle it; flagged to the Architect, Westley may veto): a guard is not idle. A side 0 guard at its post (500,500); M (side 0) is ordered onto the post. For 100 ticks the guard
    never moves (exactly, so it is trivially inside 200 wu) and M never comes within 30 wu of it, and M touched it. The assertion on the radius itself (never past 200 wu from the post on any tick) is the rule's
    own words and holds under the other reading too. Green today; red against a build that treats a guard as idle (the guard steps aside) or one that lets a push carry it."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, *START)
    g = spawn(lib, w, VANGUARD, 0, *IDLE_XY)
    assert _guard(lib, w, [g]) == 0
    assert _move(lib, w, [m], *IDLE_XY) == 0
    tr = _trace(lib, w, m, [g], 100)
    ds = [_dist(r["m"], r["o"][0]) for r in tr]
    assert min(ds) <= DIAMETER + CONTACT, "premise: the mover never touched the guard (closest %.1f)" % min(ds)
    assert max(_dist(r["o"][0], IDLE_XY) for r in tr) <= GUARD_RADIUS, "the guard was carried past its radius"
    assert all(r["o"][0] == IDLE_XY for r in tr), "the guard stepped aside for a mover of its own side (reading: a guard is not idle): first at tick %d" % (1 + next(k for k, r in enumerate(tr) if r["o"][0] != IDLE_XY))
    assert min(ds) >= DIAMETER - POS_TOL


# ------------------------------------------------------------------ controls (green today, stay green)

def test_control_a_lone_mover_walks_its_full_step_and_arrives(lib, world_factory):
    """Control (green today): M alone, (300,500) to (520,500): every tick but the last is a step of SPEED = 4 wu (within 0.5 wu) and it arrives within the budget. Proves the speed and the budget the red tests use are
    the engine's, not a harness fault."""
    goal = (520.0, 500.0)
    w, m, _ = _scene(lib, world_factory, [], goal)
    tr = _trace(lib, w, m, [], _budget(START, goal))
    got = _arrival_tick(tr, goal)
    assert got is not None
    prev = START
    for k, row in enumerate(tr[:got - 1], 1):
        assert abs(_dist(prev, row["m"]) - SPEED) <= 0.5, "tick %d: step %.2f" % (k, _dist(prev, row["m"]))
        prev = row["m"]


def test_control_an_idle_own_unit_left_alone_stays_idle(lib, world_factory):
    """Control (premise of the YIELD tests, green today): an idle side 0 Vanguard with nothing near it for 60 ticks has no destination, no target and has not moved by a hair."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, *IDLE_XY)
    for _ in range(60):
        step(lib, w)
    assert dest(lib, w, u)[0] == 0 and lib.om_unit_get_target(w, u) == 0 and pos(lib, w, u) == IDLE_XY


def test_control_R_097_05_two_own_movers_are_still_pushed_apart_to_30_wu_and_both_give(lib, world_factory):
    """R-097-05: "Given two units on the same layer within 30 wu (2 x radius 15), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart ..." and R-097-10 "both are
    moving" (neither is idle: each is a mover). Two side 0 Vanguards 20 wu apart, (400,500) and (400,520), both ordered +x: on every one of 30 ticks they are at least 30 wu apart (POS_TOL), at 30 wu on the first,
    and both have moved from where they started (neither takes the whole push). Green today (measured: 30.000 on the first tick, both give); must stay green."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, VANGUARD, 0, 400.0, 500.0)
    b = spawn(lib, w, VANGUARD, 0, 400.0, 520.0)
    assert _move(lib, w, [a], 1500.0, 500.0) == 0 and _move(lib, w, [b], 1500.0, 520.0) == 0
    dists = []
    for _ in range(30):
        step(lib, w)
        dists.append(_dist(pos(lib, w, a), pos(lib, w, b)))
    assert dists[0] == pytest.approx(DIAMETER, abs=POS_TOL)
    assert min(dists) >= DIAMETER - POS_TOL, "the movers overlapped: closest %.2f wu" % min(dists)
    pa, pb = pos(lib, w, a), pos(lib, w, b)
    assert _dist(pa, (400.0, 500.0)) > 50.0 and _dist(pb, (400.0, 520.0)) > 50.0, "one of the two movers was held while the other took the whole push: %s %s" % (pa, pb)
