"""PP-unit: formation arrival gives up, never mills (E-13 S-099, new R-099-05; Architect A169).

R-099-05 (Addendum 62, A169): a unit under a GROUP MOVE whose own slot it cannot reach ends its order
where it stands once it has been within 75 wu of its slot for 40 ticks (2 s) without arriving; a unit
never paces with no end. R-099-04 (arrival radius 1.5 x collision radius = 22.5 wu for a Raider) is unchanged.

Counting (the boundary, pinned exactly): after every `om_tactical_step`, a tick is "near" when the unit's position
REPORTED BY THE PREVIOUS STEP is within 75 wu of its slot (the C's give-up pass runs at the top of the tick, on
the positions the last tick ended with: positions are reported one tick behind, commit b2effc96); `near` counts
consecutive near ticks. The order must still be active (`om_unit_get_destination` return value has_dest == 1, read
through `.raw`) after the step that makes near == 39, and ended (has_dest == 0) after the step that makes near == 40.
The unit then stays where it stands.
What shifted (Architect A182, PF-tests2; a defect of this test's counting, not of the rule): before C4 (shots land
after movement, A178) the pinned count read the position after the same step and ended at near == 40; C4 moved the
unit's last step so the same-step count reads one tick ahead (ended at near == 41). Counting the previous step's
position, as the code's note says, restores 39 active / 40 ended. Rule and both boundaries are unchanged.

Scenes: S101's own (20 Raiders, 4 x 5 at 35 wu, one group move to (1000, 70)); and a constructed pair
(two Raiders group-moved to (1000, 0); slots (1000, -20) and (1000, 20); a third, orderless unit parked on
the first unit's slot, which collision never moves, so the slot can never be reached).
"""
import ctypes
import math

from conftest import OMFeature

from test_PP_unit_support import RAIDER, dest, pos, spawn

GIVE_UP_RADIUS = 75.0     # A169
GIVE_UP_TICKS = 40        # A169
ARRIVAL_RADIUS = 22.5     # R-099-04: 1.5 x collision radius 15 (S101 scene uses the same number)
SCENE_TICKS = 600         # brief: a bounded number of ticks


def _world(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _group_move(lib, w, ids, x, y):
    lib.om_command_group_move(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), x, y)


def _paces(has_dest_by_tick):
    """Detector: True if the unit's order never ended in the whole trace."""
    return bool(has_dest_by_tick) and all(has_dest_by_tick)


def _blocked_pair(lib, w):
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 40.0)
    _group_move(lib, w, [a, b], 1000.0, 0.0)
    _, sx, sy = dest(lib, w, a)
    spawn(lib, w, RAIDER, 0, sx, sy)       # parked on a's slot, no orders, never pushed
    return a, (sx, sy)


# ---- (5) positive control for the detector ----

def test_R_099_05_control_detector_trips_on_pacing_and_not_on_an_ended_order():
    """Positive control for _paces: a trace whose order is active for all 600 ticks trips it; a trace
    that ends does not."""
    assert _paces([1] * SCENE_TICKS)
    assert not _paces([1] * 150 + [0] * (SCENE_TICKS - 150))
    assert not _paces([])


# ---- (1) the S101 scene ----

def test_R_099_05_s101_scene_every_order_ends_and_nobody_paces(lib, world_factory):
    """S-099 R-099-05: 20 Raiders, one group move; within 600 ticks every unit's order has ended
    (has_dest 0). Red today for exactly the old behaviour: two units (S101 units 1 and 4) mill within
    their slots' reach with the order active to the last tick."""
    w = _world(lib, world_factory)
    units = [spawn(lib, w, RAIDER, 0, r * 35.0, c * 35.0) for r in range(4) for c in range(5)]
    _group_move(lib, w, units, 1000.0, 70.0)
    trace = {u: [] for u in units}
    for _ in range(SCENE_TICKS):
        lib.om_tactical_step(w)
        for u in units:
            trace[u].append(dest(lib, w, u)[0])
    pacing = [i for i, u in enumerate(units) if _paces(trace[u])]
    assert not pacing, f"units {pacing} still have an active order after {SCENE_TICKS} ticks (milling)"


# ---- (2) a slot that cannot be reached: the boundary ----

def test_R_099_05_blocked_slot_gives_up_at_exactly_40_ticks_within_75(lib, world_factory):
    """S-099 R-099-05: slot occupied by a stopped neighbour; the unit mills near it. Active after the
    39th consecutive near tick, ended after the 40th, not arrived (still farther than 22.5 wu), and it
    stays where it stands afterwards."""
    w = _world(lib, world_factory)
    a, slot = _blocked_pair(lib, w)
    near = 0
    ended_at = None
    d_prev = math.inf          # distance reported by the previous step (positions are one tick behind)
    for t in range(SCENE_TICKS):
        lib.om_tactical_step(w)
        p = pos(lib, w, a)
        d = math.hypot(p[0] - slot[0], p[1] - slot[1])
        has = dest(lib, w, a)[0]
        near = near + 1 if d_prev <= GIVE_UP_RADIUS else 0
        d_prev = d
        if near == GIVE_UP_TICKS - 1:
            assert has == 1, "gave up before 40 ticks within 75 wu"
        if near == GIVE_UP_TICKS:
            assert has == 0, "still pacing after 40 consecutive ticks within 75 wu of its slot"
            assert d > ARRIVAL_RADIUS, "scene must be a give-up, not an arrival"
            ended_at = (t, p)
            break
        if not has:
            assert False, f"order ended with only {near} near ticks (d={d:.1f}): not the give-up boundary"
    assert ended_at is not None, "unit never accumulated 40 near ticks"
    t, p = ended_at
    for _ in range(20):
        lib.om_tactical_step(w)
    assert dest(lib, w, a)[0] == 0
    q = pos(lib, w, a)
    assert math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-6, "an ended order leaves the unit standing"


# ---- (3) normal arrival is unchanged ----

def test_R_099_05_normal_arrival_still_ends_by_the_arrival_rule(lib, world_factory):
    """R-099-04 unchanged: a free unit ends its order within 22.5 wu of its slot (arrival, not give-up)."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 40.0)
    _group_move(lib, w, [a, b], 1000.0, 0.0)
    _, sx, sy = dest(lib, w, a)
    for _ in range(SCENE_TICKS):
        lib.om_tactical_step(w)
        if not dest(lib, w, a)[0]:
            break
    assert dest(lib, w, a)[0] == 0
    p = pos(lib, w, a)
    assert math.hypot(p[0] - sx, p[1] - sy) <= ARRIVAL_RADIUS


# ---- (4) farther than 75 wu: no give-up ----

def test_R_099_05_a_unit_farther_than_75_from_its_slot_does_not_give_up(lib, world_factory):
    """R-099-05: the clock runs only within 75 wu. A unit walking 1000 wu keeps its order for as long as it
    is farther than 75 wu from its slot (well past 40 ticks)."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 40.0)
    _group_move(lib, w, [a, b], 1000.0, 0.0)
    _, sx, sy = dest(lib, w, a)
    far_ticks = 0
    for _ in range(100):
        lib.om_tactical_step(w)
        p = pos(lib, w, a)
        if math.hypot(p[0] - sx, p[1] - sy) > GIVE_UP_RADIUS:
            far_ticks += 1
            assert dest(lib, w, a)[0] == 1, "gave up while still farther than 75 wu from its slot"
    assert far_ticks > GIVE_UP_TICKS
