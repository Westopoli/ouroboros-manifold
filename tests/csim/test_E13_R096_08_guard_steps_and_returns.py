"""E-13 R-096-08 / R-208-01 (engine rule fixes 2026-11-08, F6): a guard steps toward a target it sees, within 200 wu of its post, fires, and returns.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F6"; ruling DEC-guard-cross-layer-2026-11-08 (Westley, 2026-11-08: a guard engages a
cross-layer target "only if the enemy unit is within vision"). Bug fix, not a story. The engine's guard holds and never steps (A170 comment,
csrc/unit.c); tests/csim/test_PP_unit_guard.py pins that old behaviour (see the report: some of its tests contradict the rule below and need
`Test-defect:` rewrites when F6 lands). The whole-fight twin is tests/skilllab/arena/test_engine_rules_f6_guard.py.

Rule words proved, word for word:
  R-096-08  "Given a guard order, When issued to a selection, Then each unit takes its position as its post and engages any target its side can
            see (E-12 R-093-02), stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the post (DRAFT-guard-radius: the attack-move leash
            of R-087-05, Westley's number to change; the radius bounds the guard's own walk, measured post to the guard's centre, ruled 2026-10-14
            for E4), firing whenever the target is in range, returning to the post when the target dies or when engaging it would take the guard past
            the radius; it never crosses the radius and never marches; the walk is toward any target its side can see within vision, on its own
            layer or another, as far as the radius allows, and it fires when reach and range allow (...); a move, attack-move, attack-target or
            layer order ends the guard; return fire (R-087-06) is untouched."
  R-208-01  "Given selected units, When the player gives the guard order at a post, Then the units hold the post and engage what their side can see
            (E-12 R-093-02) within `GUARD_RADIUS` of it, returning to the post when the target dies or leaves the radius, never chasing past it
            (R-096-08)."
Rule pins: R-096-08, R-208-01, R-093-02, R-087-06.

Scene: a 2000 x 2000 canvas, one guard Vanguard (attack range 300, sensor 700, 4 wu per tick, walking kind, as the lab sets it) whose post is
(1000, 1000), guarded with om_command_guard; one enemy Supply (never fires, so only the test changes what the guard does) on the post's row to
the east; roster reach as the lab's stage 4 sets it (REACH_UP 0, REACH_DOWN 1: a unit fires down one layer, not up); targeting by sight on (the
default). No box in the scene: this file is the radius geometry on open ground (the lab file runs the layout with its hills). Sight, measured:
  same layer     the guard sees a Supply out to its sensor radius (700 wu): +480, +600, +690 are all seen
  layer 1 -> 0   the guard on layer 1 sees a Supply on layer 0 out to 350 wu (+350 seen, +360 not): +340 is seen, +380 is not
Detector bounds (not rules; Westley's to change): LEASH_SLACK 1 wu (DRAFT-guard-leash-slack: the end of a tick may sit this far past 200 wu; the
sweep's I26 allowed 5), ARRIVE 5 wu (a step is 4 wu), STEP_MIN 20 wu, STEP_CAP 40 ticks, FIRE_CAP 100 ticks, RETURN_CAP 120 ticks (200 wu is 50
ticks of walking plus a cohort turn), STAY 40 ticks.
Controls green today: a guard fires from its post at an enemy in range without moving; a cross-layer enemy out of vision is not engaged; a move
order from a guard walks to the point; an unguarded idle unit leaves its post for the same enemy (so the leash detector can read a breach).
"""
import ctypes

import pytest

from conftest import OMFeature, OMWorldP
from test_PP_unit_support import SUPPLY, VANGUARD, attack_move, hp, pos, spawn, step

POST = (1000.0, 1000.0)
GUARD_RADIUS = 200.0                # R-096-08 (DRAFT-guard-radius, Westley's)
RANGE = 300.0                       # Vanguard attack range
LEASH_SLACK = 1.0                   # DRAFT-guard-leash-slack, detector bound
ARRIVE = 5.0                        # detector bound
STEP_MIN = 20.0                     # detector bound
STEP_CAP = 40                       # detector bound
FIRE_CAP = 100                      # detector bound
RETURN_CAP = 120                    # detector bound
STAY = 40                           # detector bound
WALKING = 1                         # OM_MOVE_WALKING
REACH_UP, REACH_DOWN = 0, 1         # scripts/skilllab/arena/run.py, stage 4
BIG_HP = 1.0e6
FAR = (1900.0, 1900.0)              # a place no unit of the scene sees


def guard(lib, w, ids):
    fn = getattr(lib.om_command_guard, "raw", lib.om_command_guard)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    fn.restype = ctypes.c_int
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return fn(w, arr, len(ids))


def move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def remove(lib, w, uid):
    """The enemy dies (hp 0), as the other csim files make a unit die."""
    lib.om_unit_set_hp(w, uid, 0.0)


def _scene(lib, wf, dx, g_layer=0, e_layer=0, guarded=True):
    """(world, guard, enemy). Guard at the post on g_layer, ordered to guard; enemy at (post.x + dx, post.y) on e_layer."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, REACH_UP, REACH_DOWN) == 0
    g = spawn(lib, w, VANGUARD, 0, *POST, g_layer)
    e = spawn(lib, w, SUPPLY, 1, POST[0] + dx, POST[1], e_layer)
    lib.om_unit_set_hp(w, e, BIG_HP)
    if guarded:
        assert guard(lib, w, [g]) == 0
    return w, g, e


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _seen(lib, w, e):
    return bool(lib.om_player_can_see(w, 0, e))


def _run(lib, w, g, e, ticks):
    """Per tick after the step: (tick, guard position, distance from post, enemy hp)."""
    out = []
    for n in range(1, ticks + 1):
        step(lib, w)
        p = pos(lib, w, g)
        out.append((n, p, _d(p, POST), hp(lib, w, e)))
    return out


def _leash(rows):
    """Every tick that ends farther than GUARD_RADIUS + LEASH_SLACK from the post."""
    return [(n, tuple(round(v, 1) for v in p), round(d, 1)) for n, p, d, _ in rows if d > GUARD_RADIUS + LEASH_SLACK]


def _fired(rows):
    """First tick on which the enemy's hp is below what it was after the first tick (the engine clamps the 1e6 of the scene to the type's maximum)."""
    base = rows[0][3]
    return next((n for n, _, _, h in rows if h < base), None)


def _out(lib, w, g, dx_out):
    """Run until the guard stands at least dx_out wu from the post; returns the ticks run, or None."""
    for n in range(1, STEP_CAP * 3):
        step(lib, w)
        if _d(pos(lib, w, g), POST) >= dx_out:
            return n
    return None


def _stepped_out(lib, w, g, dx_out):
    assert _out(lib, w, g, dx_out) is not None, "the guard never stepped %.0f wu out of its post in %d ticks (at %s)" % (dx_out, STEP_CAP * 3, pos(lib, w, g))


# ------------------------------------------------------------------ controls: green today

def test_R_096_08_control_a_guard_fires_from_its_post_at_an_enemy_in_range(lib, world_factory):
    """Control (green today and after): the enemy 250 wu away is in range; the guard fires at it and does not leave the post. Proves the guard,
    the enemy and the hp read, so the red tests below are red for the walk's sake."""
    w, g, e = _scene(lib, world_factory, 250.0)
    rows = _run(lib, w, g, e, 60)
    assert _fired(rows) is not None, "scene broken: the guard never shot an enemy 250 wu away"
    assert all(p == POST for _, p, _, _ in rows), "the guard left its post to shoot an enemy already in range"


def test_R_096_08_control_a_cross_layer_enemy_out_of_vision_is_not_engaged(lib, world_factory):
    """R-096-08 (Westley, 2026-11-08: a guard engages a cross-layer target 'only if the enemy unit is within vision'): the guard on layer 1, the enemy on
    layer 0 at +380 wu, 30 wu beyond the 350 wu the guard sees down. For 100 ticks the guard stays at the post and the enemy is not hurt. Green
    today and after."""
    w, g, e = _scene(lib, world_factory, 380.0, g_layer=1, e_layer=0)
    step(lib, w)
    assert not _seen(lib, w, e), "scene broken: the enemy is seen at +380 down one layer"
    rows = _run(lib, w, g, e, 100)
    assert all(p == POST for _, p, _, _ in rows), "the guard walked toward an enemy it cannot see"
    assert _fired(rows) is None, "the guard hurt an enemy it cannot see"


def test_R_096_08_control_an_unguarded_idle_unit_leaves_its_post_for_the_same_enemy(lib, world_factory):
    """Control for the leash tests (green today): the same scene with no guard order, the enemy at +690 (seen, 390 wu beyond range): the idle unit
    walks out past 200 wu from the post (H-057, it pursues as an attack-mover). The detector that reads 'farther than 200 wu from the post' can
    read a breach."""
    w, g, e = _scene(lib, world_factory, 690.0, guarded=False)
    rows = _run(lib, w, g, e, 200)
    assert _leash(rows), "scene broken: the unguarded unit never went farther than %.0f wu from its post (max %.1f)" % (GUARD_RADIUS, max(r[2] for r in rows))


@pytest.mark.parametrize("kind", ["move", "attack_move"])
def test_R_096_08_control_a_guard_given_a_move_or_attack_move_order_walks_there_and_does_not_return(lib, world_factory, kind):
    """R-096-08 'a move, attack-move ... order ends the guard' (green today, the guard that has not stepped): 500 wu from the post, no enemy near;
    it arrives within ARRIVE wu, farther than 200 wu from the post, and stays there for STAY ticks."""
    w, g, e = _scene(lib, world_factory, FAR[0] - POST[0])
    goal = (POST[0], POST[1] + 500.0)
    (move if kind == "move" else attack_move)(lib, w, [g], *goal)
    rows = _run(lib, w, g, e, 200 + STAY)
    assert _d(rows[199][1], goal) <= ARRIVE, "scene broken: the guard did not reach its point (at %s)" % (rows[199][1],)
    assert all(_d(p, goal) <= ARRIVE for _, p, _, _ in rows[199:]), "the guard left its point: back toward the post"


# ------------------------------------------------------------------ red today: the guard steps, fires, returns

def test_R_096_08_a_guard_with_a_seen_enemy_beyond_range_steps_toward_it(lib, world_factory):
    """R-096-08: 'engages any target its side can see ... stepping toward it'. The enemy 480 wu east, seen, 180 wu out of range: within STEP_CAP ticks
    the guard is at least STEP_MIN wu closer to it. Red today: the guard holds the post for ever (0.0 wu)."""
    w, g, e = _scene(lib, world_factory, 480.0)
    step(lib, w)
    assert _seen(lib, w, e), "scene broken: the enemy at +480 is not seen"
    start = _d(pos(lib, w, g), pos(lib, w, e))
    rows = _run(lib, w, g, e, STEP_CAP)
    closest = min(_d(p, pos(lib, w, e)) for _, p, _, _ in rows)
    assert start - closest >= STEP_MIN, "the guard did not step toward the enemy: %.1f wu closer after %d ticks (at %s)" % (start - closest, STEP_CAP, rows[-1][1])


def test_R_096_08_a_stepping_guard_fires_when_reach_and_range_allow(lib, world_factory):
    """R-096-08: 'it fires when reach and range allow'. Enemy at +480 (180 wu out of range, inside the 200 wu radius): within FIRE_CAP ticks the
    enemy's hp has fallen, and on that tick the guard was within attack range of it. Red today: the guard never steps, the enemy is never hurt."""
    w, g, e = _scene(lib, world_factory, 480.0)
    rows = _run(lib, w, g, e, FIRE_CAP)
    n = _fired(rows)
    assert n is not None, "the enemy was never hurt in %d ticks (guard at %s)" % (FIRE_CAP, rows[-1][1])
    gap = _d(rows[n - 1][1], (POST[0] + 480.0, POST[1]))
    assert gap <= RANGE + 1.0, "the enemy was hurt at tick %d from %.1f wu, beyond the attack range %.0f" % (n, gap, RANGE)


@pytest.mark.parametrize("dx", [480.0, 600.0, 690.0])
def test_R_096_08_a_guard_never_ends_a_tick_more_than_200_wu_from_its_post(lib, world_factory, dx):
    """R-096-08: 'it never crosses the radius and never marches', every tick of 300. The enemy is seen at +480 (reachable from 180 wu out),
    +600 (needs 300 wu out of the post: beyond the radius) and +690 (seen, 390 wu out of range). For the last two the rule leaves open whether the
    guard walks to the radius and holds or stays at the post (see the report); both keep the leash. Green today (the guard holds still); it is the
    never rule, and it goes red against a guard that steps without the clamp (the break the report names)."""
    w, g, e = _scene(lib, world_factory, dx)
    step(lib, w)
    assert _seen(lib, w, e), "scene broken: the enemy at +%.0f is not seen" % dx
    rows = _run(lib, w, g, e, 300)
    bad = _leash(rows)
    assert not bad, "%d ticks beyond %.0f wu from the post, first %s" % (len(bad), GUARD_RADIUS, bad[:3])


def test_R_096_08_a_guard_that_stepped_out_never_follows_a_second_target_past_the_radius(lib, world_factory):
    """R-096-08 'never chasing past it': the guard has stepped 100 wu out toward the enemy at +480; that enemy dies and a second one stands at
    +690 (seen from the guard, 390 wu out of range): the guard does not follow past 200 wu. Every tick of 400. Red today at the first assertion
    (the guard never stepped out)."""
    w, g, e = _scene(lib, world_factory, 480.0)
    _stepped_out(lib, w, g, 100.0)
    remove(lib, w, e)
    far = spawn(lib, w, SUPPLY, 1, POST[0] + 690.0, POST[1])
    lib.om_unit_set_hp(w, far, BIG_HP)
    rows = _run(lib, w, g, far, 400)
    bad = _leash(rows)
    assert not bad, "%d ticks beyond %.0f wu from the post, first %s" % (len(bad), GUARD_RADIUS, bad[:3])


def _returns(rows_after):
    at = rows_after[RETURN_CAP - 1]
    assert at[2] <= ARRIVE, "the guard is %.1f wu from its post %d ticks after its target went (at %s)" % (at[2], RETURN_CAP, at[1])
    late = [(n, round(d, 1)) for n, _, d, _ in rows_after[RETURN_CAP - 1:] if d > ARRIVE]
    assert not late, "the guard left its post again with nothing to engage: %s" % late[:3]
    assert not _leash(rows_after), "the guard crossed the radius on its way back: %s" % _leash(rows_after)[:3]


def test_R_096_08_a_guard_returns_to_its_post_when_the_target_dies(lib, world_factory):
    """R-096-08 'returning to the post when the target dies': after the guard has stepped at least 100 wu out toward the enemy at +480, the enemy
    dies; within RETURN_CAP ticks the guard is back within ARRIVE wu of the post and stays there STAY ticks, never past the radius. Red today: it
    never stepped out (the first assertion)."""
    w, g, e = _scene(lib, world_factory, 480.0)
    _stepped_out(lib, w, g, 100.0)
    remove(lib, w, e)
    _returns(_run(lib, w, g, e, RETURN_CAP + STAY))


def test_R_208_01_a_guard_returns_to_its_post_when_the_target_leaves(lib, world_factory):
    """R-208-01 'returning to the post when the target dies or leaves the radius': after the guard has stepped 100 wu out, the enemy is moved to
    (1900, 1900), out of sight and far outside the radius; within RETURN_CAP ticks the guard is back at the post and stays. Red today: it never
    stepped out."""
    w, g, e = _scene(lib, world_factory, 480.0)
    _stepped_out(lib, w, g, 100.0)
    lib.om_unit_teleport(w, e, *FAR, 0)
    _returns(_run(lib, w, g, e, RETURN_CAP + STAY))


@pytest.mark.parametrize("kind", ["move", "attack_move"])
def test_R_096_08_a_move_or_attack_move_order_ends_a_guard_that_stepped_out(lib, world_factory, kind):
    """R-096-08 'a move, attack-move ... order ends the guard': a guard that has stepped out toward the enemy at +480 (which then dies) is ordered
    to a point 500 wu south of the post; it walks there, far past 200 wu, and stays. Red today: it never stepped out."""
    w, g, e = _scene(lib, world_factory, 480.0)
    _stepped_out(lib, w, g, 100.0)
    remove(lib, w, e)
    goal = (POST[0], POST[1] + 500.0)
    (move if kind == "move" else attack_move)(lib, w, [g], *goal)
    rows = _run(lib, w, g, e, 200 + STAY)
    assert _d(rows[-1][1], goal) <= ARRIVE, "the ordered guard is %.1f wu from its point after %d ticks (at %s)" % (_d(rows[-1][1], goal), len(rows), rows[-1][1])
    assert all(_d(p, goal) <= ARRIVE for _, p, _, _ in rows[-STAY:]), "the guard walked back toward its post after the order"


# ------------------------------------------------------------------ cross layer: the guard on layer 1, the enemy on layer 0 (reach down 1)

def test_R_096_08_a_guard_steps_toward_a_seen_cross_layer_enemy_and_fires(lib, world_factory):
    """R-096-08 (Westley, 2026-11-08): 'the walk is toward any target its side can see within vision, on its own layer or another ... and it fires
    when reach and range allow'. The guard on layer 1, the enemy on layer 0 at +340 (seen, 40 wu beyond range): within FIRE_CAP ticks the guard has
    stepped toward it, the enemy's hp has fallen, and the guard never ended a tick beyond 200 wu from the post. Red today: the guard holds."""
    w, g, e = _scene(lib, world_factory, 340.0, g_layer=1, e_layer=0)
    step(lib, w)
    assert _seen(lib, w, e), "scene broken: the enemy at +340 down one layer is not seen"
    rows = _run(lib, w, g, e, FIRE_CAP)
    stepped = max(p[0] - POST[0] for _, p, _, _ in rows)
    assert stepped >= STEP_MIN, "the guard did not step toward the cross-layer enemy: %.1f wu east after %d ticks" % (stepped, FIRE_CAP)
    assert _fired(rows) is not None, "the enemy on the layer below was never hurt (guard at %s)" % (rows[-1][1],)
    assert not _leash(rows), "beyond the radius: %s" % _leash(rows)[:3]


def test_R_096_08_a_guard_returns_when_its_cross_layer_target_dies(lib, world_factory):
    """R-096-08 / R-208-01: the cross-layer case of the return. The guard has stepped 30 wu out toward the layer-0 enemy at +340; the enemy dies; the
    guard is back at the post within RETURN_CAP ticks and stays. Red today: it never stepped out."""
    w, g, e = _scene(lib, world_factory, 340.0, g_layer=1, e_layer=0)
    _stepped_out(lib, w, g, 30.0)
    remove(lib, w, e)
    _returns(_run(lib, w, g, e, RETURN_CAP + STAY))
