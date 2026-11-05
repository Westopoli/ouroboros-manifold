# Rule pins: R-087-04@74cc9c, R-096-02@e8ae96
"""Parity: the A199 control scene (R-087-04, R-096-02; the engine twins are tests/csim/test_PP_attack_move_no_sight_pursuit.py
and simulation/test_attack_move_no_sight_pursuit.py).
The A199 parity test is retired (H-057): the Python reference keeps A199 while the engine follows R-087-04 rev
2026-11-01; parity lives in tests/csim/test_E11_S087_engage_on_sight.py. What stays is the positive control:
four Vanguards abreast attack-move with an enemy on the route, where both engines halt short of the slots.
"""
import math

from . import parity_c
from . import parity_python
from .parity_scenes import Scene

ARRIVAL = 1.5 * 15.0
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


ON_ROUTE = _scene("attack_move_no_sight_on_route", CX, 2000.0)   # on the centroid's straight route to the click


def _first_halt_tick(trace):
    """TD-LAB-REV2-E1-3: the first tick on which no unit of the line moves, that is the halt at the first engagement."""
    fr = trace.frames
    for k in range(1, len(fr)):
        if all(fr[k][i][1:3] == fr[k - 1][i][1:3] for i in range(len(XS))):
            return k
    return len(fr) - 1


def _misses(trace, tick=-1):
    last = trace.frames[tick]
    return [math.hypot(last[i][1] - (CLICK[0] + XS[i] - CX), last[i][2] - CLICK[1]) for i in range(len(XS))]


def test_control_A199_the_slot_miss_reading_trips_when_the_enemy_is_on_the_route():
    """Positive control (green now and after): with the enemy on the route in range, both engines halt and fire
    short of the slots, so the measurement above reads a miss over the arrival radius. The miss is read at the first
    halt, not at the end of the run: since E1 (R-096-02 rewritten 2026-10-13, TD-LAB-REV2-E1-3) the C group resumes
    after the fight and reaches its slots, so only the first engagement still shows the halt in both engines."""
    parity_c.build()
    for name, tr in (("python", parity_python.run_scene(ON_ROUTE)), ("c", parity_c.run_scene(ON_ROUTE))):
        miss = max(_misses(tr, _first_halt_tick(tr)))
        assert miss > ARRIVAL, "%s: control did not trip (miss %.1f at the first halt)" % (name, miss)
