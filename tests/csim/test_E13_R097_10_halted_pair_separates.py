# Rule pins: R-097-10, R-097-05
"""E-13 R-097-10 and the collision Invariant, Round 6 piece E3 (docs/northstar/plans/engine-rules-2026-11-08/round6.md): two halted units do not stay overlapped.

Rule words (docs/bible/epics/E-13-movement-and-command.md, as rewritten 2026-11-18, DEC-draws-round6-2026-11-18):
  R-097-10  "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement, except that an idle unit ... takes the
            full displacement from a mover of its own side and none from an enemy mover, which takes all of it; given both are stationary, they split the displacement equally (until 2026-11-18 only when either
            had been displaced earlier in the tick, which left two halted units overlapped for as long as both stood ...)."
  Invariant "No two same-layer units ... within 30 wu after the collision pass"; "A stationary unit is never moved by a moving unit's collision; two stationary units that overlap separate."
Cause (round6.md E3): the gate "and either was displaced earlier in the tick" lets two stationary units that nothing has moved this tick stand 20 wu apart for as long as both stand (the stage 4 trap fights:
six pairs for 5 to 7 s). The built piece removes the gate.

Scenes (every tick, through om_tactical_step):
  ENGAGED  two own Vanguards that hold the same enemy Supply as their target and fire at it, 100 wu apart; one is then moved (om_unit_teleport) to 20 wu from the other, with both still engaged.
  IDLE     two own Vanguards, no enemy anywhere, placed 20 wu apart.
In both, from the tick after the placement: by tick SETTLE_TICKS (DRAFT-ramp-settle-ticks, 3, round6.md) the pair is 30 wu apart; on every later tick it is, and no unit moves; the midpoint of the pair is where it
was (each took half of the 10 wu: "split ... equally"). Controls green today: a stationary (engaged) unit beside an own mover moves 0 on every tick, and the pair is never closer than 30 wu after a tick (the mover
took the whole overlap); an idle own unit yields to an own mover (it is pushed along, the mover walks to its goal).

Configuration: as test_E13_R097_10_proof_idle_yield.py (the shipped one for a csim scene: 2000 x 2000 canvas, abilities off, ground era, Vanguard walking, reach 0 up 1 down). The Supply never fires.
Vanguard: 4 wu a tick, attack range 300, collision diameter 30 wu.

Detector bounds (not rules; Westley's to change): SETTLE_TICKS 3 (DRAFT-ramp-settle-ticks, round6.md's number), POS_TOL 0.05 wu (numeric slack of the C's cheap trig, as the PP files), HOLD_TICKS 20 (how long
"do not move after" is watched), LOCK_TICKS 20 (a run limit for the engaged pair to take its target).
"""
import ctypes
import math

from conftest import OMFeature
from test_PP_unit_support import SUPPLY, VANGUARD, dest, pos, spawn, step, target

WALKING = 1                         # OM_MOVE_WALKING
ERA_GROUND = 1
CANVAS = 2000.0
DIAMETER = 30.0                     # R-097-05: 2 x radius 15
SETTLE_TICKS = 3                    # DRAFT-ramp-settle-ticks (round6.md E3)
POS_TOL = 0.05                      # numeric slack, not a rule threshold
HOLD_TICKS = 20                     # detector bound
LOCK_TICKS = 20                     # run limit
BIG_HP = 1.0e6
A_XY = (500.0, 500.0)
B_FAR = (600.0, 500.0)
B_NEAR = (520.0, 500.0)             # 20 wu from A
SUPPLY_XY = (550.0, 700.0)          # about 206 wu from each Vanguard: inside the attack range 300 and the notice distance 330


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    lib.om_tactical_disable_abilities(w)
    assert lib.om_set_era_kind(w, ERA_GROUND) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, 0, 1) == 0
    return w


def _move(lib, w, uid, x, y):
    arr = (ctypes.c_uint32 * 1)(uid)
    assert lib.om_command_move.raw(w, arr, 1, float(x), float(y)) == 0


def _engaged_pair(lib, wf):
    """Two own Vanguards 100 wu apart that hold the Supply and fire at it for a few ticks; then B is put 20 wu from A. Returns (world, a, b, supply)."""
    w = _world(lib, wf)
    a = spawn(lib, w, VANGUARD, 0, *A_XY)
    b = spawn(lib, w, VANGUARD, 0, *B_FAR)
    s = spawn(lib, w, SUPPLY, 1, *SUPPLY_XY)
    lib.om_unit_set_hp(w, s, BIG_HP)
    for _ in range(LOCK_TICKS):
        step(lib, w)
        if target(lib, w, a) == s and target(lib, w, b) == s:
            break
    assert target(lib, w, a) == s and target(lib, w, b) == s, "scene broken: the Vanguards hold %s and %s, not the Supply %d" % (target(lib, w, a), target(lib, w, b), s)
    for _ in range(3):
        step(lib, w)
    assert lib.om_unit_get_hp(w, s) < BIG_HP, "scene broken: the Vanguards do not fire at the Supply"
    pa, pb = pos(lib, w, a), pos(lib, w, b)
    assert pa == A_XY and pb == B_FAR, "scene broken: the engaged Vanguards moved: %s %s" % (pa, pb)
    lib.om_unit_teleport(w, b, B_NEAR[0], B_NEAR[1], 0)
    return w, a, b, s


def _idle_pair(lib, wf):
    w = _world(lib, wf)
    a = spawn(lib, w, VANGUARD, 0, *A_XY)
    b = spawn(lib, w, VANGUARD, 0, *B_NEAR)
    return w, a, b, None


def _assert_pair_separates(lib, w, a, b, s, what):
    """Every tick from the placement: the pair is 30 wu apart by tick SETTLE_TICKS, stays so, does not move after it, and its midpoint is where it was."""
    pa0, pb0 = A_XY, B_NEAR
    mid0 = ((pa0[0] + pb0[0]) / 2.0, (pa0[1] + pb0[1]) / 2.0)
    rows = []
    for t in range(1, SETTLE_TICKS + HOLD_TICKS + 1):
        step(lib, w)
        rows.append((pos(lib, w, a), pos(lib, w, b)))
        if s is not None:
            assert target(lib, w, a) == s and target(lib, w, b) == s, "%s: tick %d: the pair is no longer engaged (targets %s, %s)" % (what, t, target(lib, w, a), target(lib, w, b))
        if t >= SETTLE_TICKS:
            d = _dist(*rows[-1])
            assert d >= DIAMETER - POS_TOL, "%s: tick %d: the halted pair stands %.2f wu apart (30 wu after %d ticks; they were placed %.0f apart)" % (what, t, d, SETTLE_TICKS, _dist(pa0, pb0))
    settled = rows[SETTLE_TICKS - 1]
    for t in range(SETTLE_TICKS, len(rows) + 1):
        pa, pb = rows[t - 1]
        assert _dist(pa, settled[0]) <= POS_TOL and _dist(pb, settled[1]) <= POS_TOL, "%s: tick %d: the pair moved after it was settled: %s %s, was %s" % (what, t, pa, pb, settled)
    mid = ((settled[0][0] + settled[1][0]) / 2.0, (settled[0][1] + settled[1][1]) / 2.0)
    assert _dist(mid, mid0) <= POS_TOL, "%s: the midpoint of the pair moved from %s to %s (two stationary units split the displacement equally)" % (what, mid0, mid)


def test_R_097_10_two_units_halted_by_engagement_20_wu_apart_are_30_wu_apart_within_3_ticks_and_stay(lib, world_factory):
    """R-097-10 'given both are stationary, they split the displacement equally' and the Invariant 'two stationary units that overlap separate': two own Vanguards that hold and fire at an enemy Supply, one
    placed 20 wu from the other. By tick 3 they are 30 wu apart, on every later tick they are and neither moves, and the midpoint of the pair is where it was. Red today: the gate 'either was displaced earlier
    in the tick' leaves them 20 wu apart."""
    w, a, b, s = _engaged_pair(lib, world_factory)
    _assert_pair_separates(lib, w, a, b, s, "engaged pair")


def test_R_097_10_two_idle_units_20_wu_apart_are_30_wu_apart_within_3_ticks_and_stay(lib, world_factory):
    """R-097-10 / the Invariant, the same for two idle own Vanguards (no move target, no enemy anywhere) placed 20 wu apart: 30 wu apart by tick 3, every later tick, no movement after, midpoint unchanged.
    Red today."""
    w, a, b, s = _idle_pair(lib, world_factory)
    _assert_pair_separates(lib, w, a, b, s, "idle pair")


def test_R_097_10_control_a_stationary_engaged_unit_beside_a_mover_moves_0(lib, world_factory):
    """R-097-10 'Given one unit of the pair is stationary ... it moves 0 and the other takes the full displacement' (control, green today, must stay): an own Vanguard that holds and fires at the Supply
    stands at (500,500); an own mover is ordered to that spot. On every tick for 100 ticks the stationary unit is where it was, bit for bit, and the pair is never closer than 30 wu."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, 300.0, 500.0)
    a = spawn(lib, w, VANGUARD, 0, *A_XY)
    s = spawn(lib, w, SUPPLY, 1, *SUPPLY_XY)
    lib.om_unit_set_hp(w, s, BIG_HP)
    for _ in range(LOCK_TICKS):
        step(lib, w)
        if target(lib, w, a) == s:
            break
    assert target(lib, w, a) == s, "scene broken: the stationary Vanguard holds %s, not the Supply %d" % (target(lib, w, a), s)
    _move(lib, w, m, *A_XY)
    closest = 1e9
    for t in range(1, 101):
        step(lib, w)
        assert pos(lib, w, a) == A_XY, "tick %d: the stationary unit moved to %s (it moves 0)" % (t, pos(lib, w, a))
        d = _dist(pos(lib, w, m), pos(lib, w, a))
        closest = min(closest, d)
        assert d >= DIAMETER - POS_TOL, "tick %d: the pair is %.2f wu apart after the push" % (t, d)
    assert closest <= DIAMETER + POS_TOL, "scene broken: the mover never reached the stationary unit (closest %.2f wu)" % closest


def test_R_097_10_control_an_idle_unit_yields_to_a_mover_of_its_own_side(lib, world_factory):
    """R-097-10 'an idle unit ... takes the full displacement from a mover of its own side' (control, green today, must stay): an idle own Vanguard at (500,500), an own mover ordered to (520,500), inside the
    idle unit's 30 wu. The idle unit is pushed away from where it stood and the mover reaches its goal (destination cleared within 5 wu)."""
    w = _world(lib, world_factory)
    m = spawn(lib, w, VANGUARD, 0, 300.0, 500.0)
    i = spawn(lib, w, VANGUARD, 0, *A_XY)
    _move(lib, w, m, *B_NEAR)
    for _ in range(100):
        step(lib, w)
    assert _dist(pos(lib, w, i), A_XY) >= 5.0, "the idle own unit was not pushed: at %s" % (pos(lib, w, i),)
    assert dest(lib, w, m)[0] == 0 and _dist(pos(lib, w, m), B_NEAR) <= 5.0, "the mover did not arrive: at %s" % (pos(lib, w, m),)
