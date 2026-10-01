"""Routing by travel time across layers (SPEC.md sections 5.10 and 6; E-01 R-001-05, R-001-07;
register Q-001-04 closed (b), Q-001-05 reading a).

Two sim changes are pinned here:
1. The flow field costs a step at distance / speed and a layer change at
   transition_s + forced_change_penalty * |dL| / speed seconds, so the shortest route by TIME wins
   across layers (default penalty 0; 100000 makes a detour always win; ties go to the same-layer
   route within 1e-6 s).
2. The goal layer is the layer the unit was ordered on (nearest open layer when the goal cell is
   blocked there), so a route that crosses another layer on the way returns to the ordered layer.

Geometry used throughout (all derived from SPEC 6 and 5.10):
- Arena 80 x 40 cells of 50 units; `wall` is 4 cells thick at x 1900..2100, blocked rows
  g .. 39 - g (g = end_gap, h = 2 blocks layers 1 and 2), so it spans y g*50 .. 2000 - g*50.
- The mover starts at (1025, 1025) (row 20) and is ordered to (3025, 1025) on its own layer, 2000
  units east, with a line of blocked cells between. Start and goal are cell centres.
- A route over the wall on a flat line costs 2000 / speed plus TWO layer changes (up to layer 3,
  and back down to the ordered layer 1, goal layer rule), i.e. 2 * transition_s extra seconds.
- The detour through an open end: the nearest open row is 20 - g rows away (up or down, the
  field picks the nearer end), so it takes 2 * (20 - g) diagonal steps on the 8-neighbour grid;
  each diagonal replaces a straight step of 50 by 50 * sqrt(2). Extra distance
  E(g) = 2 * (20 - g) * 50 * (sqrt(2) - 1)   (g = 9: 455.6, 10: 414.2, 11: 372.8, 12: 331.4,
  13: 289.9, 15: 207.1). The transfer wins when
  E > 2 * transition_s * speed + 4 * forced_change_penalty   (each change is |dL| = 2),
  and the detour wins when E is smaller. `_margin` below computes the signed gap and every
  test asserts it is at least 25 units, so no case sits on a knife edge by accident.
- Raider (transition_s 1.0, speed 150): the crossover is E = 300. Bastion (5.0, 40): E = 400.
  g = 11 (E = 372.8) therefore sends the raider over and the bastion around.
Spawn jitter is 0 throughout.
"""
import math

import pytest

import layerlab.run as runmod
from conftest import add_type, grp, make_scenario, unit_trace

CELL = 50.0
XS, XG, Y0 = 1025.0, 3025.0, 1025.0
STRIP_LO, STRIP_HI = 1910.0, 2090.0          # core of the 4-cell strip x 1900..2100 (edges excluded)
GOAL = (XG, Y0)
SQRT2 = math.sqrt(2.0)


def _extra(g):
    """E(g): extra distance of the open-end detour over the straight 2000 (see module docstring)."""
    return 2.0 * (20 - g) * CELL * (SQRT2 - 1.0)


def _margin(g, transition_s, speed, penalty=0.0):
    """Signed gap in world units: detour extra minus the cost of the two layer changes of a route
    over the wall. Positive: the transfer route is shorter by time; negative: the detour is."""
    transfer = 2.0 * transition_s * speed + 2.0 * penalty * 2.0
    return _extra(g) - transfer


def _wall(g):
    return {"preset": "wall", "h": 2, "end_gap": g}


def _band(g):
    """y range (core) of the wall's blocked rows."""
    return g * CELL + 10.0, 2000.0 - g * CELL - 10.0


def _in_core(ut, g):
    lo, hi = _band(g)
    return (ut.x >= STRIP_LO) & (ut.x <= STRIP_HI) & (ut.y >= lo) & (ut.y <= hi)


def _in_strip(ut):
    return (ut.x >= STRIP_LO) & (ut.x <= STRIP_HI)


def _scenario(terrain, movers, *, rules=None, max_ticks=800):
    """`movers`: list of (type, kind, x) flyers/walkers on layer 1 at (x, Y0) with a MOVE order to
    GOAL, in group order. A raider-class enemy is parked on layer 5 in a far corner so the run has
    both sides but nothing engages. Types named 'walker_*' are walking copies of raider."""
    groups = [grp("A", t, x, Y0, 1, order="move", goal=list(GOAL)) for t, _, x in movers]
    groups.append(grp("B", "raider", 3900.0, 150.0, 5))
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    scn = make_scenario(groups, terrain=terrain, rules=r, run={"max_ticks": max_ticks, "stalemate_ticks": 6000})
    for t, kind, _ in movers:
        if t.startswith("walker_"):
            add_type(scn, t, "raider", movement_kind="walk")
    return scn


def _go(g, mtype="raider", *, kind="fly", rules=None, max_ticks=800, start_x=XS):
    name = mtype if kind == "fly" else "walker_" + mtype
    scn = _scenario(_wall(g), [(name, kind, start_x)], rules=rules, max_ticks=max_ticks)
    res = runmod.run(scn, seed=0, trace=True)
    return res, unit_trace(res, 0)


def _took_transfer(res, ut, g):
    """True when the unit crossed the wall's blocked rows on a layer above 2."""
    over = _in_core(ut, g)
    if over.any():
        assert (ut.layer[over] >= 3).all(), "unit was inside the wall's blocked rows on layer 1 or 2"
        return True
    return False


def _assert_detour(res, ut, g):
    """Detour taken: stayed on layer 1 the whole run, never changed layer, and passed the strip only
    through an open end (y outside the blocked band)."""
    lo, hi = _band(g)
    assert res.unit[0]["transitions"] == 0
    assert not ut.changing.any()
    assert (ut.layer == 1).all()
    strip = _in_strip(ut)
    assert strip.any(), "unit never passed the strip"
    assert ((ut.y[strip] < lo) | (ut.y[strip] > hi)).all(), "unit crossed the strip inside the blocked band"
    assert abs(res.unit[0]["x"] - XG) <= 30.0 and abs(res.unit[0]["y"] - Y0) <= 30.0, "did not arrive"


# ---- A: the shortest route by time wins across layers (R-001-05, Q-001-04, Q-001-05 a1) ----------

def test_wall_with_a_long_detour_takes_the_transfer():
    """R-001-05 / Q-001-04 (b), Q-001-05 a1 (positive twin): a `wall` end_gap 10 (E = 414.2); a raider
    (two changes cost 2 * 1.0 s * 150 = 300 units of travel) crosses over the wall: layer 3 reached,
    inside the blocked rows only on a layer above 2, transitions >= 1, and no unit ever occupies
    a blocked cell (the in-core check)."""
    assert _margin(10, 1.0, 150.0) > 25.0
    res, ut = _go(10)
    assert _took_transfer(res, ut, 10), "raider took the detour although it is 114 units longer than the transfers"
    assert (ut.layer == 3).any()
    assert res.unit[0]["transitions"] > 0


def test_wall_with_a_short_detour_takes_the_detour():
    """R-001-05 / Q-001-04 (b), Q-001-05 a1 (negative twin): a `wall` end_gap 15 (E = 207.1, shorter
    than the 300 the two raider transfers cost): the shortest route by time is the detour. Stays on
    layer 1 for the whole run, transitions 0, passes the strip only through an open end. (Under the old
    reading with penalty 0 a free change always won, so this is red today.)"""
    assert _margin(15, 1.0, 150.0) < -25.0
    res, ut = _go(15)
    _assert_detour(res, ut, 15)


@pytest.mark.parametrize("mtype,crosses", [("raider", True), ("bastion", False)])
def test_the_same_wall_sends_a_raider_over_and_a_bastion_around(mtype, crosses):
    """R-001-05 / Q-001-05 a1 (type matters): `wall` end_gap 11, E = 372.8. A raider (a change costs
    1.0 s = 150 units of travel, two changes 300) crosses over the wall. A bastion (5.0 s at speed 40 =
    200 units per change, 400 for two) takes the detour: layer 1 throughout, no change, arrives."""
    spec = {"raider": (1.0, 150.0), "bastion": (5.0, 40.0)}[mtype]
    m = _margin(11, *spec)
    assert (m > 25.0) if crosses else (m < -25.0)
    res, ut = _go(11, mtype, max_ticks=1800)
    if crosses:
        assert _took_transfer(res, ut, 11) and (ut.layer == 3).any()
        assert res.unit[0]["transitions"] > 0
    else:
        _assert_detour(res, ut, 11)


@pytest.mark.parametrize("penalty,crosses", [(0.0, True), (10.0, True), (40.0, False), (100000.0, False)])
def test_forced_change_penalty_moves_the_crossover(penalty, crosses):
    """Q-001-04 (SPEC 5.10): the penalty is extra cost in world units per layer of change, divided
    by speed into seconds. `wall` end_gap 10 (E = 414.2), raider, goal layer 1: two changes of
    |dL| = 2, so the transfer route costs 300 + 4 * penalty. Penalty 0 (the default) and 10 (340)
    cross; 40 (460) and 100000 (the earlier reading: a detour always wins) go around."""
    m = _margin(10, 1.0, 150.0, penalty)
    assert (m > 25.0) if crosses else (m < -25.0)
    res, ut = _go(10, rules={"forced_change_penalty": penalty})
    if crosses:
        assert _took_transfer(res, ut, 10) and res.unit[0]["transitions"] > 0
    else:
        _assert_detour(res, ut, 10)


def test_default_forced_change_penalty_is_zero():
    """SPEC 3 / Q-001-04 closed: the lab default is forced_change_penalty 0 (the earlier value
    100000 made a detour always win). Read from the scenario the tests build, not assumed."""
    scn = make_scenario([])
    assert scn["rules"]["forced_change_penalty"] == 0


@pytest.mark.parametrize("eps,crosses", [(-0.05, True), (0.0, False), (0.05, False)])
def test_equal_cost_tie_goes_to_the_same_layer_route(eps, crosses):
    """SPEC 5.10 ties: a flyer (speed 100) whose two layer changes cost exactly the detour's extra
    time: transition_s = E(12) / (2 * speed) = 1.6569 s. At equality (within 1e-6 s) the same-layer
    detour wins (transitions 0). Knife-edge controls: 0.05 s shorter per change crosses (positive:
    the detector sees the other side of the edge), 0.05 s longer goes around."""
    speed = 100.0
    tie_s = _extra(12) / (2.0 * speed)
    scn = _scenario(_wall(12), [("tiefly", "fly", XS)], max_ticks=900)
    add_type(scn, "tiefly", "raider", speed=speed, transition_s=tie_s + eps)
    res = runmod.run(scn, seed=0, trace=True)
    ut = unit_trace(res, 0)
    if crosses:
        assert _took_transfer(res, ut, 12) and res.unit[0]["transitions"] > 0
    else:
        _assert_detour(res, ut, 12)


# ---- B: the unit ends on the layer it was ordered on (Q-001-05 a2, R-001-05) --------------------

def _barrier_run(goal, *, layer=1, rules=None, terrain=None, start=(XS, Y0), max_ticks=800, mtype="raider"):
    scn = make_scenario(
        [grp("A", mtype, start[0], start[1], layer, order="move", goal=list(goal)),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain=terrain or {"preset": "barrier", "h": 2},
        rules={"spawn_jitter": 0.0, **(rules or {})}, run={"max_ticks": max_ticks, "stalemate_ticks": 6000})
    res = runmod.run(scn, seed=0, trace=True)
    return res, unit_trace(res, 0)


def test_flyer_crosses_a_barrier_and_returns_to_its_ordered_layer():
    """Q-001-05 a2 / R-001-05: a `barrier` h = 2 (no way around), a flying raider on layer 1 ordered
    to a point beyond it on layer 1: it was on layer 3 in the strip (and mid-route), arrives on
    layer 1 (not 3), and counts exactly two changes (up, then back down)."""
    res, ut = _barrier_run(GOAL)
    u = res.unit[0]
    assert (ut.layer == 3).any(), "never reached layer 3"
    inside = _in_strip(ut)
    assert inside.any() and (ut.layer[inside] >= 3).all()
    assert u["layer"] == 1, "ended on layer %d, ordered on layer 1" % u["layer"]
    assert u["transitions"] == 2
    assert abs(u["x"] - XG) <= 30.0 and abs(u["y"] - Y0) <= 30.0


def test_goal_inside_the_barrier_footprint_ends_on_the_nearest_open_layer():
    """R-001-05 mountain case / SPEC 5.10 goal layer: the goal cell is blocked on layers 1 and 2 and
    open on 3 (a goal inside the barrier's footprint, h = 2): from layer 1 the goal layer is the
    nearest open layer, 3. The unit ends there, one change, at the goal."""
    goal = (2000.0, 1025.0)
    res, ut = _barrier_run(goal)
    u = res.unit[0]
    assert u["layer"] == 3 and u["transitions"] == 1
    assert abs(u["x"] - goal[0]) <= 30.0 and abs(u["y"] - goal[1]) <= 30.0


def test_goal_inside_the_footprint_on_an_open_ordered_layer_keeps_that_layer():
    """SPEC 5.10 goal layer (negative control for the test above): the same goal, but the unit was
    ordered on layer 4 where the goal cell is open: the ordered layer is the goal layer, so it
    ends on layer 4 with no change at all (it is not pulled down to the nearest layer 3)."""
    goal = (2000.0, 1025.0)
    res, ut = _barrier_run(goal, layer=4)
    u = res.unit[0]
    assert u["layer"] == 4 and u["transitions"] == 0 and not ut.changing.any()
    assert abs(u["x"] - goal[0]) <= 30.0 and abs(u["y"] - goal[1]) <= 30.0


@pytest.mark.parametrize("layer", [1, 3])
def test_goal_blocked_on_every_layer_stops_close_on_its_own_layer(layer):
    """R-001-05 second clause / SPEC 5.10: a `block` h = 5 (all layers blocked, x 1750..2250, y 750..1250)
    and an order to its centre: the unit stops outside the footprint on the layer it was ordered on,
    250 to 350 from the goal, with no layer change (the layer-3 case shows 'its layer', not 'layer
    1')."""
    goal = (2000.0, 1000.0)
    res, ut = _barrier_run(goal, layer=layer, terrain={"preset": "block", "h": 5}, start=(1000.0, 1000.0))
    u = res.unit[0]
    assert u["layer"] == layer and u["transitions"] == 0 and not ut.changing.any()
    outside = u["x"] < 1750.0 or u["x"] >= 2250.0 or u["y"] < 750.0 or u["y"] >= 1250.0
    assert outside
    assert 250.0 <= math.hypot(u["x"] - goal[0], u["y"] - goal[1]) <= 350.0


def test_without_auto_transition_the_unit_stops_at_the_edge_for_any_goal_layer():
    """R-001-05 control (auto_transition 0): no layer-change edges exist. A goal beyond the barrier
    and a goal inside it both leave the unit standing at the near edge on layer 1 (x just under
    1900), transitions 0, never changing."""
    for goal in (GOAL, (2000.0, 1025.0)):
        res, ut = _barrier_run(goal, rules={"auto_transition": 0})
        u = res.unit[0]
        assert u["layer"] == 1 and u["transitions"] == 0 and not ut.changing.any()
        assert 1850.0 <= u["x"] < 1900.0


def test_without_auto_transition_a_wall_is_always_a_detour():
    """R-001-05 / SPEC 5.10 (auto_transition 0): on the wall where the raider would otherwise cross
    (end_gap 10, margin +114), no change is offered: it goes around, transitions 0."""
    res, ut = _go(10, rules={"auto_transition": 0})
    _assert_detour(res, ut, 10)


# ---- C: walkers (R-001-07) ------------------------------------------------------------------------

@pytest.mark.parametrize("h", [1, 2])
def test_walker_with_a_plateau_goal_ends_on_the_plateau_layer(h):
    """R-001-07 / SPEC 5.9, 5.10: a `ramp` (h = 1 or 2), a walking raider ordered to a point on the
    plateau: it climbs the slope and ends on layer h + 1, at the goal, after h layer changes (the slope
    cross-overs). Goal layer rule: the plateau goal is blocked on the ordered layer 1, so the nearest
    open layer, h + 1, is the goal layer. (Slope traversal times are tested in test_layers.py.)"""
    scn = make_scenario(
        [grp("A", "climber", 1800.0, 1000.0, 1, order="move", goal=[3200.0, 1000.0]),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain={"preset": "ramp", "h": h, "sl": 600.0, "g": 1},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 900, "stalemate_ticks": 6000})
    add_type(scn, "climber", "raider", movement_kind="walk")
    res = runmod.run(scn, seed=0, trace=True)
    ut = unit_trace(res, 0)
    u = res.unit[0]
    assert ut.on_slope.any()
    assert u["layer"] == h + 1 and u["transitions"] == h
    assert abs(u["x"] - 3200.0) <= 30.0 and abs(u["y"] - 1000.0) <= 30.0


def test_walker_crosses_a_wall_only_by_the_detour_where_a_flyer_goes_over():
    """R-001-07: a walker never changes layer in place, so on `wall` end_gap 10 (where a raider flyer
    crosses, margin +114) the walking raider takes the open end: layer 1 throughout, transitions 0, arrives.
    Positive control: the flying raider of the same stats on the same wall crosses."""
    walk_res, walk = _go(10, kind="walk")
    _assert_detour(walk_res, walk, 10)
    fly_res, fly = _go(10, kind="fly")
    assert _took_transfer(fly_res, fly, 10) and fly_res.unit[0]["transitions"] > 0


# ---- D: the flow-field cache is per unit type and movement kind -----------------------------------

@pytest.mark.parametrize("order", [("raider", "bastion"), ("bastion", "raider")])
def test_two_types_ordered_to_one_goal_in_one_run_take_different_routes(order):
    """SPEC 5.10 cache key (goal cell, goal layer, movement kind, unit type, auto_transition): a raider and
    a bastion ordered to the same goal cell in the same run on `wall` end_gap 11 (E = 372.8): the raider
    crosses (layer 3 in the strip), the bastion goes around (layer 1 throughout, transitions 0), whichever
    group is listed (and so whichever builds the field) first."""
    xs = {"raider": XS, "bastion": XS + CELL}
    scn = _scenario(_wall(11), [(t, "fly", xs[t]) for t in order], max_ticks=1800)
    res = runmod.run(scn, seed=0, trace=True)
    ri, bi = order.index("raider"), order.index("bastion")
    r, b = unit_trace(res, ri), unit_trace(res, bi)
    assert _took_transfer(res, r, 11) and res.unit[ri]["transitions"] > 0
    assert res.unit[bi]["transitions"] == 0 and not b.changing.any() and (b.layer == 1).all()
    strip = _in_strip(b)
    lo, hi = _band(11)
    assert strip.any() and ((b.y[strip] < lo) | (b.y[strip] > hi)).all()


@pytest.mark.parametrize("order", [("fly", "walk"), ("walk", "fly")])
def test_a_flyer_and_a_walker_ordered_to_one_goal_take_different_routes(order):
    """SPEC 5.10 cache key (movement kind): a flying and a walking raider ordered to the same goal cell
    in one run on `wall` end_gap 10: the flyer crosses, the walker goes around, in either group order."""
    xs = {"fly": XS, "walk": XS + CELL}
    scn = _scenario(_wall(10), [("raider" if k == "fly" else "walker_raider", k, xs[k]) for k in order])
    res = runmod.run(scn, seed=0, trace=True)
    fi, wi = order.index("fly"), order.index("walk")
    f, w = unit_trace(res, fi), unit_trace(res, wi)
    assert _took_transfer(res, f, 10) and res.unit[fi]["transitions"] > 0
    assert res.unit[wi]["transitions"] == 0 and not w.changing.any() and (w.layer == 1).all()


# ---- E: determinism of the crossing runs (R-004-05, SPEC 9) ---------------------------------------

def _mixed_run(lib, seed=0):
    xs = {"raider": XS, "bastion": XS + CELL}
    scn = _scenario(_wall(11), [(t, "fly", xs[t]) for t in ("raider", "bastion")], max_ticks=1800)
    return runmod.run(scn, seed=seed, trace=True, lib=lib)


def test_crossing_run_twice_is_byte_identical():
    """SPEC 9 determinism gate on a run that exercises the new cost model (raider over, bastion around):
    the same scenario and seed twice give identical result bytes and identical trace bytes."""
    a, b = _mixed_run("O2"), _mixed_run("O2")
    assert a.raw == b.raw
    assert a.trace.tobytes() == b.trace.tobytes()
    assert a.unit[0]["transitions"] > 0, "the run did not cross: the identity above would be vacuous"


@pytest.mark.parametrize("seed", [0, 3])
def test_crossing_run_o0_and_o2_are_byte_identical(seed):
    """SPEC 9 / 5.12: the O0 and O2 builds give identical result and trace bytes on the same
    crossing run (Dijkstra sums in doubles must not depend on the optimiser)."""
    a, b = _mixed_run("O0", seed), _mixed_run("O2", seed)
    assert a.raw == b.raw
    assert a.trace.tobytes() == b.trace.tobytes()
