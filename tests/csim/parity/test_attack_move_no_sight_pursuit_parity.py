"""Parity: attack-move holds slot and route until shooting, not sight (R-087-04, R-096-02; ruling A199; the engine
twins are tests/csim/test_PP_attack_move_no_sight_pursuit.py and simulation/test_attack_move_no_sight_pursuit.py).
Rule marked for playtest review, A199.

Four Vanguards abreast (40 wu apart) attack-move together past an idle Raider 450 wu off their east flank (seen in
sensor 700, never inside attack range 300). Each unit's slot is the click plus its offset from the line's centroid
(R-095-02). Both engines must hold the line's shape (each unit's offset from the final centroid within 1.5 x collision radius 15 of its slot offset), end the centroid within 2 x collision radius of the click (TD-PP-A199-shape-measure; R-095-05) and
agree with each other within PARITY_TOLERANCE. RED until both engines carry A199 (each engine's own red test names
its half). The positive control puts the enemy on the route, where both engines halt short of the slots.
"""
import math

from . import parity_c
from . import parity_python
from .parity_scenes import Scene
from .parity_tolerance import PARITY_TOLERANCE

ARRIVAL = 1.5 * 15.0
CENTROID_ARRIVAL = 2.0 * 15.0   # looser of the engines' centroid radii (open flag, R-095-05)
XS = (1000.0, 1040.0, 1080.0, 1120.0)
CX = sum(XS) / len(XS)
# TD-PP-A199-parity-length / TD-PP-A199-parity-route: the click is due north of the line's centroid, so the route is a
# straight 2000 wu north and an enemy 450 wu east of the line's end is never in attack range (the old click (2000, 3000)
# sent the line on a diagonal that passed within range of that enemy, so both engines halted and fired mid-route).
CLICK = (CX, 3000.0)
# Ticks from the distance, not from a run: 2000 wu at the Vanguard's 80 wu/s on the 20 Hz tick (4 wu per tick) is 500
# ticks; a margin of 1.4 for turning, the slot approach and the arrival radius gives 700.
VAN_SPEED, TICK_HZ, ROUTE_WU, MARGIN = 80.0, 20, 2000.0, 1.4
TICKS = math.ceil(ROUTE_WU / (VAN_SPEED / TICK_HZ) * MARGIN)


def _scene(name, enemy_x, enemy_y):
    return Scene(name, TICKS, "open",
                 tuple(("Vanguard", 0, x, 1000.0) for x in XS) + (("Raider", 1, enemy_x, enemy_y),),
                 ((0, "attack_move", (0, 1, 2, 3), CLICK[0], CLICK[1]),),
                 "A199: hold slot and route until shooting; R-087-04")


FLANK = _scene("attack_move_no_sight_flank", XS[-1] + 450.0, 2000.0)
ON_ROUTE = _scene("attack_move_no_sight_on_route", CX, 2000.0)   # on the centroid's straight route to the click


def _shape_error(trace):
    """TD-PP-A199-shape-measure: largest gap, over every frame, between a unit's offset from the centroid and its slot's offset from
    the click (R-095-02): zero when the line's shape is intact."""
    worst = 0.0
    for fr in trace.frames:   # every tick: an enemy that dies lets the line re-form, so the end alone would not show it
        cx = sum(fr[i][1] for i in range(len(XS))) / len(XS)
        cy = sum(fr[i][2] for i in range(len(XS))) / len(XS)
        worst = max(worst, max(math.hypot((fr[i][1] - cx) - (XS[i] - CX), fr[i][2] - cy) for i in range(len(XS))))
    return worst


def _centroid_miss(trace):
    last = trace.frames[-1]
    return math.hypot(sum(last[i][1] for i in range(len(XS))) / len(XS) - CLICK[0], sum(last[i][2] for i in range(len(XS))) / len(XS) - CLICK[1])


def _misses(trace):
    last = trace.frames[-1]
    return [math.hypot(last[i][1] - (CLICK[0] + XS[i] - CX), last[i][2] - CLICK[1]) for i in range(len(XS))]


def test_A199_R087_04_c_and_python_both_end_at_the_slots_past_a_seen_enemy():
    """A199 / R-087-04: past an enemy that is seen but never in range, every unit of the line ends within the
    arrival radius of its slot in both engines, and the engines agree. RED now: both walk off to the enemy."""
    parity_c.build()
    py = parity_python.run_scene(FLANK)
    c = parity_c.run_scene(FLANK)
    for name, tr in (("python", py), ("c", c)):
        # TD-PP-A199-shape-measure: R-095-05 ends a group on its centroid arriving, so (1) the shape is held within the slot
        # radius and (2) the centroid is within 2 x collision radius of the click, the looser of the engines' two radii
        # (C 1.5 x, Python 2 x; open flag for Westley, R-095-05's text does not settle it).
        assert _shape_error(tr) <= ARRIVAL, "%s: shape broke, a unit is %.1f wu off its slot offset (slot radius %.1f)" % (name, _shape_error(tr), ARRIVAL)
        assert _centroid_miss(tr) <= CENTROID_ARRIVAL, "%s: centroid ended %.1f wu from the click (limit %.1f)" % (name, _centroid_miss(tr), CENTROID_ARRIVAL)
    dev = max(math.hypot(py.frames[-1][i][1] - c.frames[-1][i][1], py.frames[-1][i][2] - c.frames[-1][i][2]) for i in range(len(XS)))
    assert dev <= PARITY_TOLERANCE, "final positions differ between the engines by %.2f wu" % dev


def test_control_A199_the_slot_miss_reading_trips_when_the_enemy_is_on_the_route():
    """Positive control (green now and after): with the enemy on the route in range, both engines halt and fire
    short of the slots, so the measurement above reads a miss over the arrival radius."""
    parity_c.build()
    for name, tr in (("python", parity_python.run_scene(ON_ROUTE)), ("c", parity_c.run_scene(ON_ROUTE))):
        assert max(_misses(tr)) > ARRIVAL, "%s: control did not trip (miss %.1f)" % (name, max(_misses(tr)))
