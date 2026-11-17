# Rule pins: R-097-05, R-097-03, R-001-06, R-004-06, R-097-08
"""E-13 R-097-05 and R-097-03 (engine rules round 5, G5): two units that stand on the same slope collide whichever side of its midline each is on, and the steering probe
treats such a unit as a unit on its layer; units on different layers that are not on one slope still do not collide.

Rule words, as they read on this branch (docs/bible/epics/E-13-movement-and-command.md):
  R-097-05  "Given two units on the same layer within 30 wu (2 x radius 15), or two units within 30 wu that both stand on the same slope, whichever side of its midline each is on (E-01 R-001-06),
            When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick. The slope case is there because a walker that
            crosses a slope's midline changes layer (E-01 R-004-06) and would otherwise arrive inside units of its new layer (Westley, 2026-11-17, asked whether units on one slope collide across the
            layer line: "All the rest go with recommended", the recommendation being yes; ...)."
  R-097-03  "Given a moving unit, When it steps, Then it probes 40 wu ahead; if a unit on its layer, or on the same slope (R-097-05), blocks the probe (an idle unit of its own side does not block: idle
            means no move target and not engaged; an enemy always does) it tries +30, -30, +60, -60, +90 and -90 degrees from its heading, in that order, and takes the first clear one; if none is clear it
            continues straight."

Scene (the ramp of tests/csim/test_E01_R004_layer_change_is_continuous.py, the lab's hills.py ramp laid straight): canvas 4000, ground era, heights replaced by om_terrain_set_heights, low ground west of
x 1100, plateau east of x 1300, a ramp between; the layer flips at the midline, x about 1198 (R-004-06). A slope is whatever `om_terrain_slope_at` calls one: the premise of every on-slope test is read from
the live world (the two units' slope index is the same and not -1, their layers are what the test says), never typed in. Walking kinds, the shipped configuration (steering on).

Measure: the distance between the two units after each tick (the collision pass runs inside the tick), compared with 30 wu less POS_TOL 0.05 (the numeric slack of tests/csim/test_PP_move_collision.py, the
C's cheap trig is a step of 5e-5 wu short), on every tick the two stand on one slope; "pushed to 30 wu apart" is read as the distance after the pass being 30 within POS_TOL when two units alone overlap.

Every test below states whether it is red or green against the engine before Round 5 (the collision pass skips pairs whose start layers differ, csrc/tactical_move.c om_move_collide_pair, and the probe's
blocker gather filters on the same start layers): the on-slope tests are red for that reason; the controls (the same scene one step outside the rule) are green and show the measure can fail.
"""
import ctypes
import math

import pytest

from test_PP_unit_support import RAIDER, VANGUARD, pos, spawn, step
import test_E01_R004_layer_change_is_continuous as ramp

POS_TOL = 0.05                  # numeric slack, not a rule threshold
PAIR = 30.0                     # R-097-05: 2 x radius 15
TICKS = 60
ROW_Y = 2050.0           # a cell centre: a row on a cell edge (y 2050) makes the route planner lean 30 degrees off it
DUMMY = 40                      # a custom unit type that never fires (damage 0, range 1 wu) and barely moves: an enemy that only stands
DUMMY_HP = 5000.0
MIDLINE_X = 1198.0              # the ramp's layer flip, from the R004 file's docstring; the tests read the layers from the live world and assert them as premise


def _dummy(lib, w, kind):
    """Register the DUMMY type with movement kind `kind` (0 flying, 1 walking)."""
    assert lib.om_roster_register_custom_unit(w, DUMMY, 0, b"r5_dummy", DUMMY_HP, 0.0, 8.0, 1.0, 0.0, 100.0, 1.0, 0.0, 0) == 0
    assert lib.om_roster_set_movement_kind(w, DUMMY, kind) == 0


def _on_slope(lib, w, u):
    """The slope index the engine puts the unit on (om_terrain_slope_at), -1 when it is on none."""
    x, y = pos(lib, w, u)
    return lib.om_terrain_slope_at(w, x, y, None)


def _layer(lib, w, u):
    return lib.om_unit_get_layer(w, u)


def _dist(lib, w, a, b):
    pa, pb = pos(lib, w, a), pos(lib, w, b)
    return math.hypot(pa[0] - pb[0], pa[1] - pb[1])


def _move(lib, w, u, x, y):
    lib.om_command_move(w, [u], 1, float(x), float(y))


WARM = 4        # ticks the units stand before any order: the movement system files a unit's start layer on its first tick (a unit spawned and ordered at once is read as layer 0 for that tick)


def _warm(lib, w):
    for _ in range(WARM):
        step(lib, w)


def _meeting(lib, wf, terrain=True, la=0, lb=1, xa=1160.0, xb=1236.0, faction_b=0):
    """Two Vanguards walking toward each other along the row y 2050 (A east, B west), 76 wu apart; A on layer `la` below the midline, B on layer `lb` above it (the ramp's own layers)."""
    w = ramp._world(lib, wf, terrain=terrain)
    a = spawn(lib, w, VANGUARD, 0, xa, ROW_Y, la)
    b = spawn(lib, w, VANGUARD, faction_b, xb, ROW_Y, lb)
    _warm(lib, w)
    _move(lib, w, a, 1400.0, ROW_Y)
    _move(lib, w, b, 1000.0, ROW_Y)
    return w, a, b


def _meet_rows(lib, w, a, b, ticks=TICKS):
    """Per tick: (tick, distance, layer a, layer b, slope a, slope b)."""
    rows = []
    for t in range(1, ticks + 1):
        step(lib, w)
        rows.append((t, _dist(lib, w, a, b), _layer(lib, w, a), _layer(lib, w, b), _on_slope(lib, w, a), _on_slope(lib, w, b)))
    return rows


def _crossed(rows):
    """Ticks on which the two stand on one slope on different layers: the case R-097-05 adds."""
    return [r for r in rows if r[4] >= 0 and r[4] == r[5] and r[2] != r[3]]


# ------------------------------------------------------------------ R-097-05: two units on one slope, across the midline

def test_R_097_05_two_walkers_meeting_across_the_midline_are_never_closer_than_30_wu(lib, world_factory):
    """R-097-05: "two units within 30 wu that both stand on the same slope, whichever side of its midline each is on ... Then they are pushed apart along the line between them until 30 wu apart".
    Two Vanguards walk toward each other up the ramp, A from the lower side (layer 0), B from the upper (layer 1), and meet at the midline: on every one of 60 ticks on which they stand on one
    slope the distance between them, after the pass, is at least 30 wu less POS_TOL. Premise: they do meet (at least 5 ticks on one slope on different layers, and the gap falls to 31 wu or less).
    Red today: the pass skips a pair whose start layers differ, so they walk through each other (closest approach near 0 wu)."""
    w, a, b = _meeting(lib, world_factory)
    rows = _meet_rows(lib, w, a, b)
    crossed = _crossed(rows)
    assert len(crossed) >= 5, "premise: the two never stood on one slope on different layers (%d ticks); first rows %s" % (len(crossed), rows[:3])
    assert min(r[1] for r in crossed) <= PAIR + 1.0, "premise: the walkers never met on the slope (closest %.1f wu)" % min(r[1] for r in crossed)
    close = [(r[0], round(r[1], 2), r[2], r[3]) for r in rows if r[4] >= 0 and r[4] == r[5] and r[1] < PAIR - POS_TOL]
    assert not close, "%d ticks on one slope closer than 30 wu (tick, distance, layer a, layer b), first %s" % (len(close), close[:4])


def test_R_097_05_control_the_same_walkers_one_layer_apart_on_flat_ground_walk_through_each_other(lib, world_factory):
    """R-097-05 control (green today and after): the scene above on a world with no terrain (nothing is a slope): A on layer 0, B on layer 1, 76 wu apart and walking toward each other. 'Units on
    different layers that are not on one slope still do not collide': they pass through, the closest approach is under 30 wu, so the measure of the test above can fail and the rule's other clause holds."""
    w, a, b = _meeting(lib, world_factory, terrain=False, xa=1100.0, xb=1176.0)
    best = 1e9
    for _ in range(TICKS):
        step(lib, w)
        best = min(best, _dist(lib, w, a, b))
    assert _layer(lib, w, a) == 0 and _layer(lib, w, b) == 1, "premise: the layers changed (%d, %d)" % (_layer(lib, w, a), _layer(lib, w, b))
    assert _on_slope(lib, w, a) == -1, "premise: the flat world has a slope"
    assert best < PAIR - POS_TOL, "walkers on different layers off a slope collided: closest %.2f wu" % best


def _pair_pushed(lib, wf, xa, xb, la, lb, ticks=9):
    """Two Vanguards of one side on the ramp, 30 wu apart (A at xa, layer la; B at xb, layer lb), standing for WARM ticks; then A is ordered east, into B, which is idle. Returns the world, the pair and per
    tick (tick, gap) for `ticks` ticks. A idle own-side unit takes the push from a mover of its own side (R-097-10), so the pair is pushed on the line between them."""
    w = ramp._world(lib, wf)
    a = spawn(lib, w, VANGUARD, 0, xa, ROW_Y, la)
    b = spawn(lib, w, VANGUARD, 0, xb, ROW_Y, lb)
    _warm(lib, w)
    assert (_layer(lib, w, a), _layer(lib, w, b)) == (la, lb), "premise: layers %s, wanted %s" % ((_layer(lib, w, a), _layer(lib, w, b)), (la, lb))
    assert _on_slope(lib, w, a) >= 0 and _on_slope(lib, w, a) == _on_slope(lib, w, b), "premise: slopes %s" % ((_on_slope(lib, w, a), _on_slope(lib, w, b)),)
    _move(lib, w, a, 1400.0, ROW_Y)
    rows = []
    for t in range(1, ticks + 1):
        step(lib, w)
        rows.append((t, _dist(lib, w, a, b)))
    return w, a, b, rows


@pytest.mark.parametrize("name,xa,xb,la,lb", [("lower side", 1130.0, 1160.0, 0, 0), ("upper side", 1235.0, 1265.0, 1, 1)])
def test_R_097_05_control_two_units_on_one_side_of_the_midline_are_held_30_apart(lib, world_factory, name, xa, xb, la, lb):
    """R-097-05 control (green today and after; the same-layer case that is built): on the ramp, both on the lower side (layer 0) or both on the upper (layer 1), 30 wu apart, A walking at B (B idle, its
    own side: R-097-10, it takes the push): on each of the next 9 ticks the gap after the pass is 30 wu within POS_TOL. Proves the pair, the order, the warm-up and the measure of the straddling test below."""
    w, a, b, rows = _pair_pushed(lib, world_factory, xa, xb, la, lb)
    bad = [(t, round(g, 3)) for t, g in rows if abs(g - PAIR) > POS_TOL]
    assert not bad, "%s: gaps after the pass not 30 wu (tick, gap): %s" % (name, bad[:4])


def test_R_097_05_a_unit_on_each_side_of_the_midline_is_held_30_wu_apart(lib, world_factory):
    """R-097-05: "two units within 30 wu that both stand on the same slope, whichever side of its midline each is on ... Then they are pushed apart along the line between them until 30 wu apart": on the ramp,
    A on the lower side (layer 0, x 1170), B an idle unit of its own side on the upper (layer 1, x 1200), 30 wu apart; A walks at B. On each of the next 12 ticks the gap after the pass is 30 wu within
    POS_TOL, the same assertion as the control above for the straddling pair. Red today: the pass skips a pair whose start layers differ, A walks into B's place and the gap falls to about 16 wu."""
    w, a, b, rows = _pair_pushed(lib, world_factory, 1170.0, 1200.0, 0, 1)
    bad = [(t, round(g, 3)) for t, g in rows if abs(g - PAIR) > POS_TOL]
    assert not bad, "gaps after the pass not 30 wu across the midline (tick, gap): %s" % (bad[:5],)


def test_R_097_05_the_push_across_the_midline_is_along_the_line_between_the_two(lib, world_factory):
    """R-097-05: "pushed apart along the line between them": A (layer 0, x 1170) walks east into B (idle, layer 1, x 1200) on the row y 2050; A's steering may turn it off the row, so the test reads the
    line from the two positions: after the first tick B has left its place along the line from A's new position through B's old one, within POS_TOL of it (cross product of B's displacement and the
    line, over its length). Red today: B is not pushed at all (its displacement is 0, the test asserts B moved by at least 1 wu first)."""
    w = ramp._world(lib, world_factory)
    a = spawn(lib, w, VANGUARD, 0, 1170.0, ROW_Y, 0)
    b = spawn(lib, w, VANGUARD, 0, 1200.0, ROW_Y, 1)
    _warm(lib, w)
    assert (_layer(lib, w, a), _layer(lib, w, b)) == (0, 1), "premise: layers"
    b0 = pos(lib, w, b)
    _move(lib, w, a, 1400.0, ROW_Y)
    step(lib, w)
    a1, b1 = pos(lib, w, a), pos(lib, w, b)
    moved = math.hypot(b1[0] - b0[0], b1[1] - b0[1])
    assert moved >= 1.0, "B was not pushed: it moved %.3f wu" % moved
    line = math.hypot(b1[0] - a1[0], b1[1] - a1[1])
    cross = abs((b1[0] - b0[0]) * (b1[1] - a1[1]) - (b1[1] - b0[1]) * (b1[0] - a1[0])) / line
    assert cross <= POS_TOL, "B's push left the line between the two by %.3f wu (A %s, B %s -> %s)" % (cross, a1, b0, b1)


def test_R_097_05_enemies_across_the_midline_collide_too(lib, world_factory):
    """R-097-05 with R-097-08 ('enemy units ... collide like allies; nobody passes through anybody'): the meeting scene with B an enemy (faction 1, a plain move: it does not stop to fight): on every tick on
    which the two stand on one slope the gap is at least 30 wu less POS_TOL. Red today for the same reason as the allies' test."""
    w, a, b = _meeting(lib, world_factory, faction_b=1)
    rows = _meet_rows(lib, w, a, b)
    assert len(_crossed(rows)) >= 5, "premise: the two never stood on one slope on different layers"
    close = [(r[0], round(r[1], 2)) for r in rows if r[4] >= 0 and r[4] == r[5] and r[1] < PAIR - POS_TOL]
    assert not close, "%d ticks of enemies on one slope closer than 30 wu, first %s" % (len(close), close[:4])


# ------------------------------------------------------------------ R-097-05: different layers that are not on one slope

def _stacked(lib, w, x, upper_layer):
    """A walker (layer 0) at x - 80 heading east along the row, and a flying-kind dummy of the other side at x on `upper_layer`; returns (walker, other)."""
    _dummy(lib, w, 0)
    walker = spawn(lib, w, VANGUARD, 0, x - 80.0, ROW_Y, 0)
    other = spawn(lib, w, DUMMY, 1, x, ROW_Y, upper_layer)
    _warm(lib, w)
    _move(lib, w, walker, x + 300.0, ROW_Y)
    return walker, other


def _pass_under(lib, w, walker, other, ticks=70):
    """Per tick the walker's displacement along the row and its offset from it; returns (rows, closest approach)."""
    rows, best, prev = [], 1e9, pos(lib, w, walker)
    for t in range(1, ticks + 1):
        step(lib, w)
        p = pos(lib, w, walker)
        best = min(best, _dist(lib, w, walker, other))
        rows.append((t, p[0] - prev[0], p[1] - ROW_Y))
        prev = p
    return rows, best


def test_R_097_05_a_walker_on_flat_ground_under_a_flyer_is_not_pushed(lib, world_factory):
    """R-097-05: "Units on different layers that are not on one slope still do not collide" (round5.md G5: 'a walker on flat ground under a flyer is not pushed'): a world with no terrain, nothing is a
    slope; a walker (layer 0) walks east along the row through the place of an enemy flyer on layer 1: on every one of 70 ticks it moves forward and stays on the row (|y - 2050| under POS_TOL), and its
    closest approach to the flyer is under 30 wu (it did pass through). Green today and after (the case that is already right and must stay so)."""
    w = ramp._world(lib, world_factory, terrain=False)
    walker, flyer = _stacked(lib, w, 600.0, 1)
    assert (_layer(lib, w, walker), _layer(lib, w, flyer)) == (0, 1) and _on_slope(lib, w, walker) == -1, "premise: layers or a slope"
    rows, best = _pass_under(lib, w, walker, flyer)
    bad = [r for r in rows if r[2] > POS_TOL or r[2] < -POS_TOL or r[1] <= 0.0]
    assert not bad, "the walker was pushed or held (tick, dx, dy): %s" % (bad[:4],)
    assert best < PAIR - POS_TOL, "premise: the walker never passed the flyer (closest %.1f wu)" % best


def test_R_097_05_a_walker_on_the_low_ground_far_from_the_ramp_is_not_pushed_by_a_flyer(lib, world_factory):
    """R-097-05, the same clause in a world that has a ramp: the walker and the enemy flyer are on the low ground at x 600, 500 wu from the ramp's foot (x 1100). They are not on the slope in any reading
    of R-001-06 (a band of ground between a bottom edge and a top edge; the ramp is x 1100 to 1300); the walker is not pushed. NOTE: om_terrain_slope_at answers a slope index for this spot (the slope
    records of a hand-laid hill run the whole row, `findings` of this brief), so an implementation that tests slope membership by that call alone fails this test: the builder reports it, it is not a rule
    change. Green today (layers differ)."""
    w = ramp._world(lib, world_factory)
    walker, flyer = _stacked(lib, w, 600.0, 1)
    assert (_layer(lib, w, walker), _layer(lib, w, flyer)) == (0, 1), "premise: layers"
    rows, best = _pass_under(lib, w, walker, flyer)
    bad = [r for r in rows if r[2] > POS_TOL or r[2] < -POS_TOL or r[1] <= 0.0]
    assert not bad, "the walker was pushed or held (tick, dx, dy): %s" % (bad[:4],)
    assert best < PAIR - POS_TOL, "premise: the walker never passed the flyer (closest %.1f wu)" % best


def test_R_097_05_control_the_same_walker_and_a_unit_on_its_own_layer_are_pushed_apart(lib, world_factory):
    """R-097-05 control (green today and after): the no-terrain scene above with the second unit on layer 0 (a flying-kind dummy still, but on the walker's layer): the pass pushes the walker, so on some
    tick it is off the row or held back, and the two are never closer than 30 wu less POS_TOL. The test above is green because of the layers, not because the walker cannot be pushed."""
    w = ramp._world(lib, world_factory, terrain=False)
    walker, other = _stacked(lib, w, 600.0, 0)
    assert _layer(lib, w, walker) == _layer(lib, w, other) == 0, "premise: layers"
    rows, best = _pass_under(lib, w, walker, other)
    assert best >= PAIR - POS_TOL, "same-layer units closer than 30 wu: %.2f" % best
    assert any(abs(r[2]) > POS_TOL or r[1] <= 0.0 for r in rows), "the walker passed straight through a unit on its own layer"


# ------------------------------------------------------------------ R-097-03: the steering probe

def _probe_scene(lib, wf, blocker_x, blocker_layer, terrain=True, mover_x=1170.0):
    """A flying-kind Raider (the only movers that probe: a walker is routed and only collides, csrc/tactical_move.c om_move_walker_step) stands on the row at mover_x (layer 0, 4 ticks), then flies east along it; an enemy dummy (never fires, idle: an enemy always blocks) stands on the row at `blocker_x`, on `blocker_layer`,
    35 wu ahead of a mover at 1170 (inside the 40 wu probe, outside the 30 wu collision). Returns the world, the mover and the blocker."""
    w = ramp._world(lib, wf, terrain=terrain)
    _dummy(lib, w, 1)
    assert lib.om_roster_set_movement_kind(w, RAIDER, 0) == 0
    m = spawn(lib, w, RAIDER, 0, mover_x, ROW_Y, 0)
    s = spawn(lib, w, DUMMY, 1, blocker_x, ROW_Y, blocker_layer)
    _warm(lib, w)
    _move(lib, w, m, 1400.0, ROW_Y)
    return w, m, s


def _first_step(lib, w, m):
    """Where the mover stands after one tick, as the (dx, dy) it moved."""
    p0 = pos(lib, w, m)
    step(lib, w)
    p1 = pos(lib, w, m)
    return (p1[0] - p0[0], p1[1] - p0[1])


def _reacted(lib, wf, blocker_x, blocker_layer, terrain=True, mover_x=1170.0):
    """True when a blocker at `blocker_x` on `blocker_layer` changes the mover's first step from the step it takes with the blocker far away (x 1600): the probe saw it (the flyer turns to a clear heading,
    or waits when none is clear: either is not the straight step). Returns (reacted, straight step, step with the blocker)."""
    w, m, s = _probe_scene(lib, wf, 1600.0, 0, terrain=terrain, mover_x=mover_x)
    straight = _first_step(lib, w, m)
    assert straight[0] > 1.0 and abs(straight[1]) <= POS_TOL, "premise: the free flyer does not fly straight: %s" % (straight,)
    w, m, s = _probe_scene(lib, wf, blocker_x, blocker_layer, terrain=terrain, mover_x=mover_x)
    got = _first_step(lib, w, m)
    return math.hypot(got[0] - straight[0], got[1] - straight[1]) >= 1.0, straight, got


def test_R_097_03_the_probe_steers_around_an_enemy_on_the_same_slope_one_layer_up(lib, world_factory):
    """R-097-03: "it probes 40 wu ahead; if a unit on its layer, or on the same slope (R-097-05), blocks the probe (... an enemy always does) it tries +30, -30, ... degrees from its heading": a flyer
    over the ramp's lower side (layer 0, x 1170) heads east at an idle enemy on the upper side (layer 1, x 1205, 35 wu ahead, same slope). Its first step is not the step it takes with the enemy
    far away (it turns to a clear heading, or waits): the probe saw the enemy. Red today: the blocker is on another layer, the probe ignores it, the flyer flies straight."""
    w, m, s = _probe_scene(lib, world_factory, 1205.0, 1)
    assert (_layer(lib, w, m), _layer(lib, w, s)) == (0, 1), "premise: layers %s" % ((_layer(lib, w, m), _layer(lib, w, s)),)
    assert _on_slope(lib, w, m) >= 0 and _on_slope(lib, w, m) == _on_slope(lib, w, s), "premise: same slope"
    reacted, straight, got = _reacted(lib, world_factory, 1205.0, 1)
    assert reacted, "the flyer did not react to an enemy 35 wu ahead on the same slope: free step %s, step with the enemy %s" % (straight, got)


def test_R_097_03_control_the_probe_steers_around_an_enemy_on_its_own_layer(lib, world_factory):
    """R-097-03 control (green today and after): the same flyer and row, the enemy on the mover's own layer (layer 0, x 1185, 35 wu ahead of a start at 1150, inside the probe): its first step
    differs from the free step. Proves the measure of the test above reads a reaction of the probe."""
    reacted, straight, got = _reacted(lib, world_factory, 1185.0, 0, mover_x=1150.0)
    assert reacted, "the flyer did not react to an enemy on its own layer: free step %s, step with the enemy %s" % (straight, got)


def test_R_097_03_control_the_probe_ignores_an_enemy_on_another_layer_off_any_slope(lib, world_factory):
    """R-097-03 / R-097-05 control (green today and after; 'Units on different layers that are not on one slope' do not block): the flyer and the enemy as in the first probe test on a world with no
    terrain (nothing is a slope), the enemy on layer 1: the first step is the free step (the probe does not see the unit on another layer). Proves the probe test's reaction comes from the slope and
    not from the enemy's position alone."""
    w, m, s = _probe_scene(lib, world_factory, 1205.0, 1, terrain=False)
    assert _layer(lib, w, m) == 0 and _layer(lib, w, s) == 1 and _on_slope(lib, w, m) == -1, "premise"
    reacted, straight, got = _reacted(lib, world_factory, 1205.0, 1, terrain=False)
    assert not reacted, "the flyer reacted to a unit on another layer off any slope: free step %s, step with the enemy %s" % (straight, got)
