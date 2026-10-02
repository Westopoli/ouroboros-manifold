"""Trace type and the comparator. Pure Python, no engine: both engines write the same Trace.

A Trace is one frame per tick (frame 0 = spawn state, frame k = after the k-th step), one row per
unit in uid order (C unit id = uid + 1): (alive, x, y, target, facing).
  target = uid of the unit it is engaged with, -1 for none or a dead target.
  facing = radians in [0, 2 pi).
"""
import math
from dataclasses import dataclass, field

TWO_PI = 2.0 * math.pi


@dataclass
class Trace:
    scene: str
    source: str                                   # "python:<variant>" or "c"
    frames: list = field(default_factory=list)    # frames[tick][uid] = (alive, x, y, target, facing)

    def n_ticks(self):
        return len(self.frames) - 1


def arc(a, b):
    """Shortest signed arc from a to b, in radians."""
    return (b - a + math.pi) % TWO_PI - math.pi


@dataclass
class Report:
    scene: str
    ticks: int
    max_pos: float = 0.0              # largest per-unit position deviation over every tick
    max_pos_at: tuple = (-1, -1)      # (tick, uid)
    max_facing: float = 0.0
    max_facing_at: tuple = (-1, -1)
    pos_dev: list = field(default_factory=list)       # per tick: max over units
    first_pos: tuple = None           # first (tick, uid, deviation) above pos_tol
    first_target: tuple = None        # first (tick, uid, a_target, b_target) where targets differ
    first_facing: tuple = None        # first (tick, uid, deviation) above facing_tol
    first_alive: tuple = None         # first (tick, uid) where alive differs
    shape_error: str = ""

    def first_divergence(self):
        """Earliest tick any channel left tolerance, as (tick, channel), or None."""
        found = [(c[0], name) for name, c in (("position", self.first_pos), ("target", self.first_target),
                                              ("facing", self.first_facing), ("alive", self.first_alive)) if c]
        return min(found) if found else None

    def passes(self):
        return not self.shape_error and self.first_divergence() is None


def compare(ref, got, pos_tol, facing_tol):
    """Compare two traces tick by tick. pos_tol in wu, facing_tol in radians; both come from
    parity_tolerance.py at the call site (this function holds no number of its own)."""
    rep = Report(ref.scene, ref.n_ticks())
    if len(ref.frames) != len(got.frames):
        rep.shape_error = "tick count %d != %d" % (ref.n_ticks(), got.n_ticks())
        return rep
    for t, (fa, fb) in enumerate(zip(ref.frames, got.frames)):
        if len(fa) != len(fb):
            rep.shape_error = "unit count %d != %d at tick %d" % (len(fa), len(fb), t)
            return rep
        tick_max = 0.0
        for uid, (ra, rb) in enumerate(zip(fa, fb)):
            alive_a, xa, ya, ta, ga = ra
            alive_b, xb, yb, tb, gb = rb
            if alive_a != alive_b and rep.first_alive is None:
                rep.first_alive = (t, uid)
            dev = math.hypot(xa - xb, ya - yb)
            tick_max = max(tick_max, dev)
            if dev > rep.max_pos:
                rep.max_pos, rep.max_pos_at = dev, (t, uid)
            if dev > pos_tol and rep.first_pos is None:
                rep.first_pos = (t, uid, dev)
            if ta != tb and rep.first_target is None:
                rep.first_target = (t, uid, ta, tb)
            fd = abs(arc(ga, gb))
            if fd > rep.max_facing:
                rep.max_facing, rep.max_facing_at = fd, (t, uid)
            if fd > facing_tol and rep.first_facing is None:
                rep.first_facing = (t, uid, fd)
        rep.pos_dev.append(tick_max)
    return rep
