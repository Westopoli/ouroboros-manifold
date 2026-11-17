"""E-11 R-087-03 (engine rule fixes, Round 5, G2; Westley 2026-11-17: "I approve these two situations as well"): a lock ends when the target leaves the
unit's notice distance, and not before.

Spec: docs/northstar/plans/engine-rules-2026-11-08/round5.md "G2". Rule pins: R-087-03, R-087-04, R-087-05, R-087-06, R-087-08, R-096-02.

Rule words proved, from docs/bible/epics/E-11-units-and-combat.md on this branch:
  R-087-03  "Given an idle or attack-moving unit with no target and one or more enemies that its side can see (...) within its notice distance
            (R-087-04), When it acquires, Then it targets the nearest such enemy, and the target is a lock: the unit keeps it, whatever else comes
            nearer, until the target dies, leaves its side's sight, leaves the unit's notice distance, or the player gives the unit a new order; only
            then does it pick again, the nearest enemy its side can see within its notice distance (...). A target taken by return fire (R-087-06) is
            not dropped for distance: the leash alone bounds that chase (R-087-05). The leash and the give-up of a blocked target (R-087-09) end a
            lock as before."
  R-087-04  "... an idle unit holds where the engagement ends (R-087-06) ..."; "an attack-mover ... resumes toward its point after the engagement
            (R-096-02)". round5.md G2: "After a drop for distance an idle unit holds where it stands and an attack-mover resumes toward its point;
            the leash return of DEC-leash-anchor-return-2026-11-01 applies to leash drops only."
  R-087-08  "each unit validates its lock every tick (R-087-03) and acquires only while it has no lock, at its cohort turn on every 4th tick".

Scenes: a 2000 x 2000 canvas, the shipped tactical parameters (targeting by sight on). The Vanguard U has attack range 300 (notice distance 330), sensor 700
(its leash, R-087-05) and walks 4 wu a tick. Enemies: a Raider that plain-moves away at 7.5 wu a tick (a plain mover never acquires and never returns
fire), a Bastion that plain-moves away at 2 wu a tick, Supplies, and a Warden (range 350, notice 385, sensor 800) as the attacker of the return-fire scene.
Detector bounds (not rules): ACQUIRE_TICKS 12 (a cohort turn comes within 4 ticks), HOLD_TICKS 100, STEP 4 (one tick's walk), ARRIVE 20 wu, EPS 0.5 wu.
"""
import ctypes

from conftest import OMFeature
from test_PP_unit_support import BASTION, RAIDER, SUPPLY, VANGUARD, WARDEN, attack_move, dest, hp, pos, spawn, step, target

NOTICE_MARGIN = 0.1       # DRAFT-notice-margin (round5.md G1): the engine will name it OM_NOTICE_MARGIN; no test can read it
RANGE = 300.0             # Vanguard attack range
NOTICE = RANGE * (1.0 + NOTICE_MARGIN)
LEASH = 700.0             # Vanguard sensor radius, the leash of R-087-05
ACQUIRE_TICKS = 12
HOLD_TICKS = 100
STEP = 4.0                # detector bound: a Vanguard's walk in one tick
ARRIVE = 20.0             # detector bound
EPS = 0.5                 # detector bound
BIG_HP = 1.0e6


def _none(t):
    return t is None or t <= 0


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    return w


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _move(lib, w, uid, x, y):
    arr = (ctypes.c_uint32 * 1)(uid)
    assert lib.om_command_move.raw(w, arr, 1, float(x), float(y)) == 0


def _lock(lib, w, u, e, limit=ACQUIRE_TICKS):
    for n in range(1, limit + 1):
        step(lib, w)
        if target(lib, w, u) == e:
            return n
    return None


def _runner_scene(lib, wf, march_to=None):
    """U (a Vanguard) at (200, 1000), idle or attack-moving to `march_to`; a tough Raider 200 wu east that plain-moves east to (1950, 1000) at 7.5 wu a
    tick, which is faster than U. Returns (world, U, Raider)."""
    w = _world(lib, wf)
    u = spawn(lib, w, VANGUARD, 0, 200.0, 1000.0)
    e = spawn(lib, w, RAIDER, 1, 400.0, 1000.0)
    lib.om_unit_set_hp(w, u, 5000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    _move(lib, w, e, 1950.0, 1000.0)
    if march_to is not None:
        attack_move(lib, w, [u], *march_to)
    return w, u, e


def _follow_until_dropped(lib, w, u, e, ticks):
    """Steps `ticks` ticks after the lock; per tick: the lock is held while the target stood inside the notice distance at the end of the tick before,
    and is gone on the tick after it stood beyond it. Returns the tick (counted from the lock) on which the lock was gone, or None."""
    gap = _d(pos(lib, w, u), pos(lib, w, e))
    dropped = None
    for n in range(1, ticks + 1):
        step(lib, w)
        t = target(lib, w, u)
        if dropped is None and gap > NOTICE + 1e-6:
            assert t != e, "tick %d after the lock: the unit still holds its target, which stood %.1f wu away at the end of the tick before (notice distance %.0f)" % (n, gap, NOTICE)
        if dropped is None and gap <= NOTICE - 0.5:
            assert t == e, "tick %d after the lock: the lock went while the target stood %.1f wu away, inside the notice distance %.0f (target now %s)" % (n, gap, NOTICE, t)
        if dropped is None and t != e:
            dropped = n
        gap = _d(pos(lib, w, u), pos(lib, w, e))
    return dropped


# ------------------------------------------------------------------ the lock ends at the notice distance

def test_R_087_03_a_locked_target_that_outruns_the_unit_is_dropped_the_tick_it_is_beyond_the_notice_distance_and_not_followed(lib, world_factory):
    """R-087-03 "keeps it ... until the target ... leaves the unit's notice distance": the idle Vanguard locks the Raider 200 wu away (in range, so it stands and fires); the Raider runs
    off at 7.5 wu a tick against the Vanguard's 4. On every tick the lock holds while the Raider was inside 330 at the end of the tick before and is gone
    the tick after it was beyond. R-087-04: an idle unit holds where it stands: from the second tick after the drop, for 100 ticks, no target and no
    step, not back toward its anchor. Red today: the unit keeps the lock and runs after the Raider to its leash."""
    w, u, e = _runner_scene(lib, world_factory)
    assert _lock(lib, w, u, e) is not None, "scene broken: the unit never locked the Raider"
    anchor = (200.0, 1000.0)
    dropped = _follow_until_dropped(lib, w, u, e, 150)
    assert dropped is not None, "the unit still held its target 150 ticks later, %.1f wu from it" % _d(pos(lib, w, u), pos(lib, w, e))
    step(lib, w)
    held = pos(lib, w, u)
    for n in range(1, HOLD_TICKS + 1):
        step(lib, w)
        assert _none(target(lib, w, u)), "%d ticks after the drop: the unit took target %s again" % (n, target(lib, w, u))
        assert _d(pos(lib, w, u), held) <= EPS, "%d ticks after the drop: the unit moved from %s to %s (anchor %s)" % (n, held, pos(lib, w, u), anchor)


def test_R_087_03_an_attack_mover_whose_target_outruns_it_resumes_toward_its_point(lib, world_factory):
    """R-087-03 / R-096-02: the same chase with the Vanguard attack-moving to (200, 1900), a point 900 wu south of it. On the tick the lock goes for
    distance it resumes: from the second tick after the drop, for 40 ticks, no target, its goal is its ordered point, and every tick it is nearer to it
    and no farther east than it was; it arrives. Red today: the lock is not dropped, the unit runs east after the Raider."""
    point = (200.0, 1900.0)
    w, u, e = _runner_scene(lib, world_factory, march_to=point)
    assert _lock(lib, w, u, e) is not None, "scene broken: the attack-mover never locked the Raider"
    dropped = _follow_until_dropped(lib, w, u, e, 150)
    assert dropped is not None, "the attack-mover still held its target 150 ticks later, %.1f wu from it" % _d(pos(lib, w, u), pos(lib, w, e))
    step(lib, w)
    last = pos(lib, w, u)
    for n in range(1, 41):
        step(lib, w)
        p = pos(lib, w, u)
        has, gx, gy = dest(lib, w, u)
        assert _none(target(lib, w, u)), "%d ticks after the drop: target %s" % (n, target(lib, w, u))
        assert has == 1 and _d((gx, gy), point) <= 1e-6, "%d ticks after the drop: the goal is %s, not the ordered point %s" % (n, (has, gx, gy), point)
        assert _d(p, point) < _d(last, point) - 1.0, "%d ticks after the drop: not nearer its point (%.1f from it, %.1f the tick before)" % (n, _d(p, point), _d(last, point))
        assert p[0] <= last[0] + EPS, "%d ticks after the drop: the unit moved east, toward the Raider (%s to %s)" % (n, last, p)
        last = p
    step(lib, w, 200)
    assert _d(pos(lib, w, u), point) <= ARRIVE, "the attack-mover did not arrive: at %s" % (pos(lib, w, u),)


def test_R_087_03_a_target_at_329_is_kept_and_a_target_at_331_is_dropped_and_held_against(lib, world_factory):
    """R-087-03 at the edge, by a target put 1 wu inside and 1 wu outside the notice distance: the idle U has acquired a Supply 325 wu east of it (inside
    330) and walked 25 wu to attack range 300. The Supply is put 329 wu east of U (out of range, inside the notice distance): on every tick of 30 U holds
    it. Then the Supply is put 331 wu east of U: the lock is gone after one tick, and for 100 ticks U holds no target and does not move (not back
    toward its anchor, 25 wu west). Red today: the lock is kept at 331."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, 500.0, 1000.0)
    e = spawn(lib, w, SUPPLY, 1, 825.0, 1000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    assert _lock(lib, w, u, e) is not None, "scene broken: no lock on the Supply at 325 wu"
    step(lib, w, 30)
    ux, uy = pos(lib, w, u)
    assert target(lib, w, u) == e and ux >= 500.0 + 20.0, "scene broken: the unit did not walk to attack range and keep its lock (at %s)" % ((ux, uy),)
    lib.om_unit_teleport(w, e, ux + NOTICE - 1.0, uy, 0)
    for n in range(1, 31):
        step(lib, w)
        assert target(lib, w, u) == e, "tick %d: the lock on a target %.0f wu away, inside the notice distance, went (target %s)" % (n, NOTICE - 1.0, target(lib, w, u))
    ux, uy = pos(lib, w, u)
    lib.om_unit_teleport(w, e, ux + NOTICE + 1.0, uy, 0)
    step(lib, w)
    assert _none(target(lib, w, u)), "the lock on a target %.0f wu away, beyond the notice distance, held the tick after (target %s)" % (NOTICE + 1.0, target(lib, w, u))
    held = pos(lib, w, u)
    for n in range(1, HOLD_TICKS + 1):
        step(lib, w)
        assert _none(target(lib, w, u)) and _d(pos(lib, w, u), held) <= EPS, "%d ticks after the drop: target %s, at %s (held at %s, anchor 500, 1000)" % (n, target(lib, w, u), pos(lib, w, u), held)


# ------------------------------------------------------------------ what the drop does not touch

def test_R_087_03_control_a_target_that_is_slower_than_the_unit_is_followed_until_the_leash(lib, world_factory):
    """R-087-03 control (the setup one step outside the rule, green today and after): a Bastion plain-moves away at 2 wu a tick from the attack-moving Vanguard,
    which walks 4; the gap stays inside the notice distance (the backswing lets it open to at most about 320). On every tick the lock holds while the unit is
    farther than 2 steps inside its leash from its anchor (the sensor radius 700, R-087-05); it ends by the leash, which is unchanged."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, 100.0, 1000.0)
    e = spawn(lib, w, BASTION, 1, 350.0, 1000.0)
    lib.om_unit_set_hp(w, u, 5000.0)
    lib.om_unit_set_hp(w, e, BIG_HP)
    _move(lib, w, e, 1950.0, 1000.0)
    attack_move(lib, w, [u], 100.0, 1900.0)    # an attack-mover: it walks after a locked target that leaves its range (an idle unit does not, see the report)
    assert _lock(lib, w, u, e) is not None, "scene broken: no lock on the Bastion"
    anchor = pos(lib, w, u)
    widest, ended = 0.0, None
    away = _d(pos(lib, w, u), anchor)
    for n in range(1, 701):
        step(lib, w)
        if ended is None:
            widest = max(widest, _d(pos(lib, w, u), pos(lib, w, e)))
        if ended is None and away <= LEASH - 2 * STEP:
            assert target(lib, w, u) == e, "tick %d: the lock on the slower Bastion went with the unit %.1f wu from its anchor (leash %.0f); gap %.1f" % (n, away, LEASH, widest)
        if ended is None and target(lib, w, u) != e:
            ended = n
        away = _d(pos(lib, w, u), anchor)
    assert ended is not None, "the lock was never ended: the leash did not bound the chase (the unit is %.1f wu from its anchor)" % away
    assert widest < NOTICE, "scene broken: the gap to the Bastion opened to %.1f wu, beyond the notice distance %.0f" % (widest, NOTICE)


def test_R_087_03_a_target_taken_by_return_fire_is_not_dropped_for_distance(lib, world_factory):
    """R-087-03 "A target taken by return fire (R-087-06) is not dropped for distance: the leash alone bounds that chase": an idle Warden (range 350,
    notice 385) 345 wu from an idle Vanguard (notice 330) fires on it; the Vanguard does not notice the Warden itself, it is hit and returns fire.
    From the tick it is first hit, on every tick it holds the Warden as its target until it is within attack range 300, though the Warden stands beyond
    its notice distance; then the Warden loses hit points. Green today, red against an engine that drops every lock at the notice distance."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, VANGUARD, 0, 500.0, 1000.0)
    a = spawn(lib, w, WARDEN, 1, 845.0, 1000.0)
    lib.om_unit_set_hp(w, u, 5000.0)
    lib.om_unit_set_hp(w, a, BIG_HP)
    step(lib, w)    # the engine clamps the scene's hit points to the type's maximum; the baseline is read after it has
    full_u, full_a = hp(lib, w, u), hp(lib, w, a)
    hit, first_gap = None, None
    for n in range(1, 400):
        gap = _d(pos(lib, w, u), pos(lib, w, a))
        step(lib, w)
        if hit is None and hp(lib, w, u) < full_u:
            hit, first_gap = n, gap
        if hit is not None and _d(pos(lib, w, u), pos(lib, w, a)) > RANGE + 1.0:
            assert target(lib, w, u) == a, "tick %d (hit at %d): the return-fire target went with the Warden %.1f wu away" % (n, hit, _d(pos(lib, w, u), pos(lib, w, a)))
    assert hit is not None, "scene broken: the Warden never hit the Vanguard"
    assert first_gap > NOTICE, "scene broken: the Vanguard was hit from %.1f wu, inside its notice distance %.0f" % (first_gap, NOTICE)
    assert _d(pos(lib, w, u), pos(lib, w, a)) <= RANGE + 1.0, "the Vanguard never closed to attack range: %.1f wu" % _d(pos(lib, w, u), pos(lib, w, a))
    assert hp(lib, w, a) < full_a, "the Vanguard never fired back"
