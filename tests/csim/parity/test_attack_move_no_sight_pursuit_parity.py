"""Parity: attack-move holds slot and route until shooting, not sight (R-087-04, R-096-02; ruling A199; the engine
twins are tests/csim/test_PP_attack_move_no_sight_pursuit.py and simulation/test_attack_move_no_sight_pursuit.py).
Rule marked for playtest review, A199.

Four Vanguards abreast (40 wu apart) attack-move together past an idle Raider 450 wu off their east flank (seen in
sensor 700, never inside attack range 300). Each unit's slot is the click plus its offset from the line's centroid
(R-095-02). Both engines must end every unit within the arrival radius of its slot (1.5 x collision radius 15) and
agree with each other within PARITY_TOLERANCE. RED until both engines carry A199 (each engine's own red test names
its half). The positive control puts the enemy on the route, where both engines halt short of the slots.
"""
import math

from . import parity_c
from . import parity_python
from .parity_scenes import Scene
from .parity_tolerance import PARITY_TOLERANCE

ARRIVAL = 1.5 * 15.0
XS = (1000.0, 1040.0, 1080.0, 1120.0)
CX = sum(XS) / len(XS)
CLICK = (2000.0, 3000.0)


def _scene(name, enemy_x, enemy_y):
    return Scene(name, 700, "open",
                 tuple(("Vanguard", 0, x, 1000.0) for x in XS) + (("Raider", 1, enemy_x, enemy_y),),
                 ((0, "attack_move", (0, 1, 2, 3), CLICK[0], CLICK[1]),),
                 "A199: hold slot and route until shooting; R-087-04")


FLANK = _scene("attack_move_no_sight_flank", XS[-1] + 450.0, 2000.0)
ON_ROUTE = _scene("attack_move_no_sight_on_route", (CX + CLICK[0]) / 2, 2000.0)   # on the centroid's straight route to the click


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
        assert max(_misses(tr)) <= ARRIVAL, "%s: a unit ended %.1f wu from its slot (radius %.1f)" % (name, max(_misses(tr)), ARRIVAL)
    dev = max(math.hypot(py.frames[-1][i][1] - c.frames[-1][i][1], py.frames[-1][i][2] - c.frames[-1][i][2]) for i in range(len(XS)))
    assert dev <= PARITY_TOLERANCE, "final positions differ between the engines by %.2f wu" % dev


def test_control_A199_the_slot_miss_reading_trips_when_the_enemy_is_on_the_route():
    """Positive control (green now and after): with the enemy on the route in range, both engines halt and fire
    short of the slots, so the measurement above reads a miss over the arrival radius."""
    parity_c.build()
    for name, tr in (("python", parity_python.run_scene(ON_ROUTE)), ("c", parity_c.run_scene(ON_ROUTE))):
        assert max(_misses(tr)) > ARRIVAL, "%s: control did not trip (miss %.1f)" % (name, max(_misses(tr)))
