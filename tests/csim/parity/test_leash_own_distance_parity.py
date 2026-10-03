"""Parity: the A188 leash scene (R-087-05, R-096-03; the engine twins are tests/csim/test_PP_leash_own_distance.py
and simulation/test_leash_own_distance.py).

A Vanguard attack-moves at an idle Vanguard 700 wu away (sensor 700, range 300). Under the old rule both engines
drop the target at the range edge (about 294 wu) and walk on to about 188 wu; under A188 (the leash tests the
unit's own distance from its anchor) the unit stops where it takes the target in range, about 294 wu out.
One test: C and Python stop at the same tick, at the same place (PARITY_TOLERANCE), and that place is still
outside 200 wu of the enemy. RED until both engines carry A188 (each engine's own red test names its half).
The positive control proves the stop detector reads a unit that really walks (a lone mover never stops here).
"""
import math

from . import parity_c
from . import parity_python
from .parity_scenes import Scene
from .parity_tolerance import PARITY_TOLERANCE

SCENE = Scene(
    "leash_own_distance_294", 150, "open",
    (("Vanguard", 0, 1000.0, 2000.0), ("Vanguard", 1, 1700.0, 2000.0)),
    ((0, "attack_move", (0,), 3500.0, 2000.0),),
    "A188: the leash measures the pursuer; R-087-05, R-096-03")
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


def test_A188_R087_05_c_and_python_stop_at_the_same_place_at_294_wu():
    """A188 / R-087-05 / R-096-03: first stop of the attack-mover agrees between the engines (same tick, same
    place within PARITY_TOLERANCE) and is outside 200 wu of the enemy, not the old 188 wu stand-off."""
    parity_c.build()
    py = _first_stop(parity_python.run_scene(SCENE))
    c = _first_stop(parity_c.run_scene(SCENE))
    assert py and c, "an engine never stopped: python %s, c %s" % (py, c)
    assert py[0] == c[0], "first stop differs in tick: python %s, c %s" % (py, c)
    assert math.hypot(py[1] - c[1], py[2] - c[2]) <= PARITY_TOLERANCE, "first stop differs in place: python %s, c %s" % (py, c)
    for name, s in (("python", py), ("c", c)):
        assert 1700.0 - s[1] > 200.0, "%s stopped %.1f wu from the enemy: the leash dropped a target it was firing at" % (name, 1700.0 - s[1])


def test_control_A188_the_stop_detector_sees_no_stop_for_a_unit_that_keeps_walking():
    """Positive control (green now and after): a lone attack-mover has nothing to stop for and never stops in
    150 ticks in either engine, so a stop reading in the test above is a real stop."""
    parity_c.build()
    assert _first_stop(parity_python.run_scene(MARCH)) is None
    assert _first_stop(parity_c.run_scene(MARCH)) is None
