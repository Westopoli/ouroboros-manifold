"""Hard bodies at a slope mouth (SPEC.md 5.9 "Mounting is never blocked by bodies", 5.10 hard bodies).

Bug under test (found in E3): on the `ramp` preset several walkers waiting near the slope's bottom
edge centre block each other from mounting. One walker alone climbs; three or more stall at the
foot forever with zero layer changes (stalemate). SPEC 5.9: a walker that mounts is placed at the
edge centre even when that overlaps other units waiting on its layer, and the waiting units are
not pushed by it; the overlap clears as the mounted unit climbs away.

Geometry (ramp x1 40, sl 300, sw 200, g 1, h 1 on the default 80 x 40 grid of 50 unit cells):
the plateau starts at x = 2000; the slope's bottom edge centre is (1975, 1000), direction +x,
length 300 (top edge centre (2275, 1000), on the plateau, layer 2); a raider walks it in
300 / 7.5 = 40 ticks. The slope is 200 wide, so at most 6 bodies of 30 fit abreast (8 is the loose
bound used below) and 300 / 30 = 10 deep. Mounting radius is max(15, 25) = 25.

Conventions:
- Walkers are `raider` copies with movement_kind walk, speed 150, MOVE order to (3200, 1000)
  (layer 2: the goal cell is blocked on layer 1 by h = 1, so the goal layer is the nearest open
  layer, 2). Box of 5 columns, spacing 31 (all clear of each other), centred at (900, 1000), layer 1.
- `spawn_jitter` 0. One parked enemy flyer on layer 5 at (3900, 150) exists only so the run has
  both sides (a side with no units loses at once); same-layer-only fire (SPEC 3) keeps it inert.
- Overlap = same-effective-layer alive pairs (neither on a slope) closer than 29, as in
  test_bodies.py.

Expected today (hard bodies stall at the mouth): red are N >= 3 climbing (test 1), the occupancy and
finish test (2) and the plateau overlap test (3b), all because nobody mounts. Green today: N = 1,
the layer-1 hard-body guard (3a), the two-walker overlapped mount (4; two bodies do not stall, so it
is a guard, not a regression catcher), and the negative twins (5).

SPEC gaps filled here:
- The brief's "no enemies" cannot be literal: with no side B the run ends at tick 0 (5.11), so one
  far, inert enemy is parked as above.
- "Mounting at the same tick through each other forever" has no SPEC number; the bound asserted is
  the slope's footprint (200 wide, 300 long, bodies 30): at most 80 units on it, loosely.
- A MOVE goal cannot be satisfied by more than one body (arrival 22.5, bodies 30 wide); units
  standing blocked on the plateau behind each other is legal and the tests do not assert arrival.
"""
import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, grp, make_scenario, unit_trace

R = 15.0
OVERLAP_BELOW = 2 * R - 1.0           # 29
PLATEAU_GOAL = [3200.0, 1000.0]
RAMP = {"preset": "ramp", "x1": 40, "sl": 300.0, "sw": 200.0, "g": 1, "h": 1}
MAX_TICKS = 1500
SLOPE_CAPACITY = 80                   # loose upper bound on bodies on a 200 x 300 slope


# ---- helpers -----------------------------------------------------------------------------------

def _walker(scn):
    return add_type(scn, "walker", "raider", movement_kind="walk", speed=150.0)


def _scn(groups, rules=None):
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    scn = make_scenario(groups, terrain=RAMP, rules=r,
                        run={"max_ticks": MAX_TICKS, "stalemate_ticks": 3000})
    return _walker(scn)


def _enemy():
    return grp("B", "raider", 3900.0, 150.0, 5)


def _box(n, goal=PLATEAU_GOAL, order="move"):
    return grp("A", "walker", 900.0, 1000.0, 1, count=n, formation="box", cols=5, spacing=31.0,
               order=order, goal=list(goal))


def _run_box(n, **kw):
    scn = _scn([_box(n, **kw), _enemy()])
    return runmod.run(scn, seed=0, trace=True)


def _pairs(res, units):
    """(d, valid) over the given unit indices: d[t, i, j] xy distance; valid[t, i, j] for i < j,
    both alive, same effective layer, neither on a slope."""
    tr = res.trace[:, units]
    x, y = tr["x"].astype(np.float64), tr["y"].astype(np.float64)
    ok = tr["alive"].astype(bool) & ((tr["flags"] & 4) == 0)
    layer = tr["layer"].astype(int)
    d = np.hypot(x[:, :, None] - x[:, None, :], y[:, :, None] - y[:, None, :])
    valid = ok[:, :, None] & ok[:, None, :] & (layer[:, :, None] == layer[:, None, :])
    n = len(units)
    valid &= np.triu(np.ones((n, n), dtype=bool), k=1)[None, :, :]
    return d, valid


def _overlap_count(res, units, layer):
    """Per tick, pairs among `units` on effective `layer` closer than 29."""
    d, valid = _pairs(res, units)
    lay = res.trace[:, units]["layer"].astype(int)
    on_layer = (lay == layer)[:, :, None] & (lay == layer)[:, None, :]
    return ((d < OVERLAP_BELOW) & valid & on_layer).sum(axis=(1, 2))


def _overlap_count_outside(res, units, layer, centre, radius=40.0):
    """Like _overlap_count, but ignoring any pair in which either unit lies within `radius` of `centre`: SPEC
    5.10 lets bodies overlap inside the slope mouth (LL_MOUTH_RADIUS 40), so only overlap outside it is a bug."""
    d, valid = _pairs(res, units)
    lay = res.trace[:, units]["layer"].astype(int)
    on_layer = (lay == layer)[:, :, None] & (lay == layer)[:, None, :]
    x = res.trace[:, units]["x"].astype(float); y = res.trace[:, units]["y"].astype(float)
    near = np.hypot(x - centre[0], y - centre[1]) <= radius
    outside = ~(near[:, :, None] | near[:, None, :])
    return ((d < OVERLAP_BELOW) & valid & on_layer & outside).sum(axis=(1, 2))


def _first_mount(res, i):
    on = np.flatnonzero(unit_trace(res, i).on_slope)
    return int(on[0]) if len(on) else None


# ---- test 1: N walkers all climb ---------------------------------------------------------------

@pytest.mark.parametrize("n", [1, 3, 5, 10])
def test_n_walkers_in_a_box_all_climb_to_the_plateau(n):
    """SPEC 5.9 (positive; red today for N >= 3, N = 1 is the working control): N walkers ordered to
    the plateau all end alive on layer 2 within 1500 ticks, each with at least one layer change (the
    midline crossing). Today three or more stall at the foot with zero transitions."""
    res = _run_box(n)
    for i in range(n):
        u = res.unit[i]
        assert u["alive"], "walker %d died" % i
        assert u["layer"] == 2, "walker %d ended on layer %d (stuck at the foot?)" % (i, u["layer"])
        assert u["transitions"] >= 1, "walker %d never crossed the midline" % i


# ---- test 2: not all on the slope at once, finishing on time -----------------------------------

@pytest.mark.parametrize("n", [5, 10])
def test_slope_occupancy_is_bounded_and_the_group_finishes_in_time(n):
    """SPEC 5.9 (the overlap clears as the mounted unit climbs away; "forever" is the bug): the
    number of units on the slope (trace bit2) never exceeds what the footprint holds (<= 80), at
    least one unit mounts, every unit has mounted at some tick, and the last unit to dismount at the
    top (counted layer 2, off the slope) does so before the 1500-tick cap (the run does not end by
    cap or stalemate with units still at the foot)."""
    res = _run_box(n)
    on = np.stack([unit_trace(res, i).on_slope for i in range(n)])      # (n, ticks)
    assert on.sum(axis=0).max() <= SLOPE_CAPACITY
    assert on.any(axis=1).all(), "units that never mounted: %s" % np.flatnonzero(~on.any(axis=1))
    off_top = [int(np.flatnonzero(on[i])[-1]) + 1 for i in range(n)]
    assert max(off_top) < MAX_TICKS - 1, "last dismount at tick %d, run length %d" % (max(off_top), res.ticks)
    assert all(res.unit[i]["layer"] == 2 for i in range(n))


# ---- test 3: hard bodies still hold off the slope ----------------------------------------------

def _mounts(res, n):
    return [_first_mount(res, i) for i in range(n)]


@pytest.mark.parametrize("n", [5, 10])
def test_hard_bodies_hold_on_layer_one_away_from_the_slope(n):
    """SPEC 5.10 (guard, green today if bodies stay hard on the ground): on layer 1 no two walkers
    are closer than 29 after tick 20, counting only ticks before the first unit mounts (the
    placement at the edge centre, 5.9, is exempt from blocking and not counted). Not gated on the
    climb, so it proves the fix does not turn into general overlap."""
    res = _run_box(n)
    mounts = [m for m in _mounts(res, n) if m is not None]
    end = min(mounts) if mounts else len(res.trace)
    # Bodies may overlap inside the slope mouth (SPEC 5.10, LL_MOUTH_RADIUS 40 around the bottom edge centre
    # (1975, 1000)); only overlap OUTSIDE it counts. (The first version counted every overlap and failed at
    # ticks 139-140 for pairs 28 to 35 from the edge centre: a test defect once the mouth rule existed.)
    l1 = _overlap_count_outside(res, list(range(n)), 1, (1975.0, 1000.0))
    assert end > 21, "first mount at tick %d leaves no window" % end
    assert (l1[20:end] == 0).all(), "layer-1 overlap outside the mouth before the first mount, ticks %s" % (
        20 + np.flatnonzero(l1[20:end] > 0)[:5])


@pytest.mark.parametrize("n", [5, 10])
def test_hard_bodies_hold_on_the_plateau_after_the_climb(n):
    """SPEC 5.10 (red today, nobody climbs): on layer 2 (open plateau) no two off-slope units are
    closer than 29 from 30 ticks after the last unit dismounted. Mounting is exempt from blocking
    (5.9) but the climbers must not stay overlapped once on open ground. Fails first if some unit
    never mounted, so a no-climb run cannot pass it vacuously."""
    res = _run_box(n)
    mounts = _mounts(res, n)
    assert all(m is not None for m in mounts), "units that never mounted: %s" % [
        i for i, m in enumerate(mounts) if m is None]
    # Landing is exempt too (5.9: a dismounting unit may overlap what stands at the top and normal separation
    # resolves it), so the window starts 30 ticks after the LAST DISMOUNT (the last tick any unit is on the
    # slope, trace flag bit2), not after the last mount: the climb of a 300-long slope at speed 150 takes
    # 40 ticks. (The first version measured from the last mount, a test defect found by the slope-mouth
    # builder: overlaps of 26 to 29 at ticks 208 to 214 were the last three units landing.)
    on_slope = np.flatnonzero((res.trace["flags"][:, :n] & 4 > 0).any(axis=1))
    last = int(on_slope.max()) + 1
    l2 = _overlap_count(res, list(range(n)), 2)
    assert last + 30 < len(l2)
    assert (l2[last + 30:] == 0).all(), "layer-2 overlap after the climb, ticks %s" % (
        last + 30 + np.flatnonzero(l2[last + 30:] > 0)[:5])


# ---- test 4: mounting while overlapped ---------------------------------------------------------

def test_two_overlapping_walkers_at_the_bottom_edge_both_climb():
    """SPEC 5.9 (red or green is reported): two walkers 20 apart (x 1960 and 1990, y 1000; the
    bottom edge centre is x 1975, both inside the 25 mount radius) both ordered to the plateau.
    Neither may block the other's mount: both end on layer 2 having changed layer."""
    scn = _scn([grp("A", "walker", 1960.0, 1000.0, 1, order="move", goal=PLATEAU_GOAL),
                grp("A", "walker", 1990.0, 1000.0, 1, order="move", goal=PLATEAU_GOAL),
                _enemy()])
    res = runmod.run(scn, seed=0, trace=True)
    for i in (0, 1):
        assert res.unit[i]["layer"] == 2, "walker %d ended on layer %d" % (i, res.unit[i]["layer"])
        assert res.unit[i]["transitions"] >= 1
        assert _first_mount(res, i) is not None


# ---- test 5: negative twin, default combat rules ----------------------------------------------

def test_single_walker_with_an_enemy_and_default_fire_tables_still_climbs():
    """SPEC 5.9 positive control (works today): with an enemy present and fire tables as in the
    defaults (same-layer only), one walker on ATTACK_MOVE to the plateau mounts and ends on layer 2
    with a layer change. Proves the scenario helpers and the mount itself are sound, so the red
    tests above are about crowding."""
    scn = _scn([grp("A", "walker", 900.0, 1000.0, 1, order="attack_move", goal=PLATEAU_GOAL),
                _enemy()])
    res = runmod.run(scn, seed=0, trace=True)
    u = res.unit[0]
    assert u["alive"] and u["layer"] == 2 and u["transitions"] >= 1
    assert _first_mount(res, 0) is not None


@pytest.mark.parametrize("n", [1, 5])
def test_walkers_whose_goal_is_on_layer_one_never_mount(n):
    """SPEC 5.9 negative: mounting is never blocked by bodies, but nothing mounts a slope the route
    does not take. Walkers ordered to a ground point (1500, 1000), 475 short of the slope, stay on
    layer 1 with transitions 0 and are never on the slope (so the fix cannot be 'always mount')."""
    scn = _scn([_box(n, goal=[1500.0, 1000.0]), _enemy()])
    res = runmod.run(scn, seed=0, trace=True)
    for i in range(n):
        assert res.unit[i]["layer"] == 1 and res.unit[i]["transitions"] == 0
        assert _first_mount(res, i) is None
