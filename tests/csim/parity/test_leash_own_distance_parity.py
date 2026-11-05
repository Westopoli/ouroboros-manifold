# Rule pins: R-087-04@74cc9c, R-087-05@a79833, R-096-03@16d0c4
"""Parity: the A188 leash control scene (R-087-05, R-096-03; the engine twins are tests/csim/test_PP_leash_own_distance.py
and simulation/test_leash_own_distance.py).
The A188 parity test is retired (H-057): the Python reference keeps A188 while the engine follows R-087-04 rev
2026-11-01; parity lives in tests/csim/test_E11_S087_engage_on_sight.py. What stays is the positive control:
the stop detector reads a unit that really walks (a lone mover never stops here).
"""
import math

from . import parity_c
from . import parity_python
from .parity_scenes import Scene

MARCH = Scene(
    "leash_own_distance_march", 150, "open",
    (("Vanguard", 0, 1000.0, 2000.0),),
    ((0, "attack_move", (0,), 3500.0, 2000.0),),
    "control: nothing to stop for")


def _first_stop(trace, uid=0, still=10):
    """(tick, x, y) of the first tick from which unit `uid` stays within 0.5 wu for `still` ticks after
    having moved at least 1 wu; None if it never stops."""
    xs = [(f[uid][1], f[uid][2]) for f in trace.frames]
    moved = False
    for t in range(1, len(xs) - still):
        if math.hypot(xs[t][0] - xs[0][0], xs[t][1] - xs[0][1]) >= 1.0:
            moved = True
        if moved and all(math.hypot(xs[t + k][0] - xs[t][0], xs[t + k][1] - xs[t][1]) <= 0.5 for k in range(1, still + 1)):
            return t, xs[t][0], xs[t][1]
    return None


def test_control_A188_the_stop_detector_sees_no_stop_for_a_unit_that_keeps_walking():
    """Positive control (green now and after): a lone attack-mover has nothing to stop for and never stops in
    150 ticks in either engine, so a stop reading in the test above is a real stop."""
    parity_c.build()
    assert _first_stop(parity_python.run_scene(MARCH)) is None
    assert _first_stop(parity_c.run_scene(MARCH)) is None
