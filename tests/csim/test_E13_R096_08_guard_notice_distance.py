"""E-13 R-096-08 / R-208-01 (engine rule fixes, Round 5, G3; Westley 2026-11-17, Q-096-02: "the unit only steps out when the enemy unit enters it's firing
radius, and it only runs after it for 200 leash"): a guard acquires within its notice distance as every unit does, follows no farther than GUARD_RADIUS from its
post, and returns to the post when its lock ends.

Spec: docs/northstar/plans/engine-rules-2026-11-08/round5.md "G3". Rule pins: R-096-08, R-208-01, R-087-03, R-087-04.

Rule words proved, from docs/bible/epics/E-13-movement-and-command.md on this branch:
  R-096-08  "Given a guard order, When issued to a selection, Then each unit takes its position as its post and acquires as every unit does, an enemy its
            side can see (E-12 R-093-02) within its notice distance (E-11 R-087-04), stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the
            post (...), firing whenever the target is in range, returning to the post when the lock ends (E-11 R-087-03) or when engaging the target would
            take the guard past the radius; it never crosses the radius and never marches; (...) a move, attack-move, attack-target or layer order ends
            the guard; return fire (R-087-06) is untouched."
  R-208-01  "Given selected units, When the player gives the guard order at a post, Then the units hold the post and engage what comes within their notice
            distance (E-11 R-087-04), following it no farther than `GUARD_RADIUS` from the post and returning to the post when the lock ends or the chase
            would pass the radius (R-096-08)."

Scene: a 2000 x 2000 canvas, one guard Vanguard (attack range 300, notice distance 330, sensor 700, 4 wu a tick, walking kind, as the lab sets it) whose post is
(1000, 1000), ordered with om_command_guard; enemies are Supplies (never fire) or a Bastion that plain-moves away at 2 wu a tick; targeting by sight on. Every
scene asserts that the guard's side sees the enemy. The lab twin is tests/skilllab/arena/test_engine_rules_f6_guard.py; the older radius geometry is
tests/csim/test_E13_R096_08_guard_steps_and_returns.py.
Detector bounds (not rules; Westley's to change): LEASH_SLACK 1 wu (DRAFT-guard-leash-slack), ARRIVE 5 wu (a step is 4 wu), REACH_SLACK 10 wu (how near the
radius a following guard must get), FIRE_CAP 100 ticks, RETURN_CAP 120 ticks, STAY 40 ticks.
"""
import ctypes

import pytest

from conftest import OMFeature, OMWorldP
from test_PP_unit_support import BASTION, SUPPLY, VANGUARD, hp, pos, spawn, step, target

POST = (1000.0, 1000.0)
GUARD_RADIUS = 200.0                # R-096-08 (DRAFT-guard-radius, Westley's)
RANGE = 300.0
NOTICE_MARGIN = 0.1                 # DRAFT-notice-margin (round5.md G1): the engine will name it OM_NOTICE_MARGIN; no test can read it
NOTICE = RANGE * (1.0 + NOTICE_MARGIN)
LEASH_SLACK = 1.0                   # DRAFT-guard-leash-slack, detector bound
ARRIVE = 5.0                        # detector bound
REACH_SLACK = 10.0                  # detector bound
FIRE_CAP = 100                      # detector bound
RETURN_CAP = 120                    # detector bound
STAY = 40                           # detector bound
WALKING = 1                         # OM_MOVE_WALKING
REACH_UP, REACH_DOWN = 0, 1         # scripts/skilllab/arena/run.py, stage 4
BIG_HP = 1.0e6


def _none(t):
    return t is None or t <= 0


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _guard(lib, w, ids):
    fn = getattr(lib.om_command_guard, "raw", lib.om_command_guard)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    fn.restype = ctypes.c_int
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return fn(w, arr, len(ids))


def _scene(lib, wf, dx, etype=SUPPLY, flee_to=None):
    """(world, guard, enemy): the guard at the post, ordered to guard; a tough enemy of the other side at (post.x + dx, post.y), plain-moving to `flee_to`."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, REACH_UP, REACH_DOWN) == 0
    g = spawn(lib, w, VANGUARD, 0, *POST)
    e = spawn(lib, w, etype, 1, POST[0] + dx, POST[1])
    lib.om_unit_set_hp(w, e, BIG_HP)
    assert _guard(lib, w, [g]) == 0
    if flee_to is not None:
        arr = (ctypes.c_uint32 * 1)(e)
        assert lib.om_command_move.raw(w, arr, 1, float(flee_to[0]), float(flee_to[1])) == 0
    step(lib, w)
    assert lib.om_player_can_see(w, 0, e) == 1, "scene broken: the guard's side does not see the enemy at +%.0f" % dx
    return w, g, e


def _run(lib, w, g, e, ticks):
    """Per tick after the step: (tick, guard position, distance from the post, enemy hp, guard target)."""
    out = []
    for n in range(1, ticks + 1):
        step(lib, w)
        p = pos(lib, w, g)
        out.append((n, p, _d(p, POST), hp(lib, w, e), target(lib, w, g)))
    return out


def _beyond(rows):
    """Every tick that ends farther than GUARD_RADIUS + LEASH_SLACK from the post."""
    return [(r[0], tuple(round(v, 1) for v in r[1]), round(r[2], 1)) for r in rows if r[2] > GUARD_RADIUS + LEASH_SLACK]


def _at_post_for_good(rows):
    """After RETURN_CAP ticks the guard stands within ARRIVE of the post on every remaining tick, and never crossed the radius."""
    assert not _beyond(rows), "the guard crossed the radius: %s" % _beyond(rows)[:3]
    late = [(r[0], round(r[2], 1)) for r in rows[RETURN_CAP - 1:] if r[2] > ARRIVE]
    assert not late, "the guard is not at its post %d ticks after its lock ended: %s" % (RETURN_CAP, late[:3])


# ------------------------------------------------------------------ the notice distance bounds the guard's acquisition

@pytest.mark.parametrize("dx", [340.0, 450.0])
def test_R_096_08_a_guard_leaves_a_seen_enemy_beyond_its_notice_distance_at_its_post(lib, world_factory, dx):
    """R-096-08 "acquires as every unit does, an enemy its side can see within its notice distance": the enemy seen at +340 and at +450 (notice distance
    330; the guard's sensor radius 700) is not engaged. On every tick of 200 the guard stands on its post, holds no target and the enemy is unhurt.
    Red today: the guard steps toward anything its side sees within the radius plus its range."""
    w, g, e = _scene(lib, world_factory, dx)
    full = hp(lib, w, e)
    for n, p, _, h, t in _run(lib, w, g, e, 200):
        assert p == POST, "tick %d: the guard left its post for an enemy %.0f wu away, beyond its notice distance (at %s)" % (n, dx, p)
        assert _none(t), "tick %d: the guard holds target %s, an enemy %.0f wu away" % (n, t, dx)
        assert h == full, "tick %d: the enemy beyond the notice distance was hurt" % n


def test_R_096_08_control_an_enemy_at_320_is_engaged_stepped_to_range_and_fired_on(lib, world_factory):
    """R-096-08 control (the setup 20 wu inside the rule; the twin of the test above): the enemy seen at +320 is acquired within a cohort turn, the guard steps
    to attack range 300 (20 wu out, inside the 200 wu radius) and the enemy loses hit points; the guard never ends a tick beyond the radius."""
    w, g, e = _scene(lib, world_factory, 320.0)
    full = hp(lib, w, e)
    rows = _run(lib, w, g, e, FIRE_CAP)
    assert any(r[4] > 0 for r in rows[:12]), "the guard never acquired an enemy 320 wu away"
    assert rows[-1][3] < full, "the guard never fired on the enemy at +320"
    assert _d(rows[-1][1], (POST[0] + 320.0, POST[1])) <= RANGE + 1.0, "the guard stands %.1f wu from the enemy, beyond attack range" % _d(rows[-1][1], (POST[0] + 320.0, POST[1]))
    assert not _beyond(rows), "beyond the radius: %s" % _beyond(rows)[:3]


# ------------------------------------------------------------------ it follows up to the radius, no farther, and returns when the lock ends

def test_R_096_08_a_guard_follows_a_retreating_enemy_to_200_wu_from_its_post_and_no_farther_and_returns(lib, world_factory):
    """R-096-08 "stepping toward it no farther than GUARD_RADIUS ... returning to the post when the lock ends or when engaging the target would take the
    guard past the radius; it never crosses the radius", every tick of 700: a Bastion at +320 (inside the notice distance) plain-moves east at 2 wu a
    tick, the guard 4. The guard fires on it, follows to within REACH_SLACK of 200 wu from the post, never ends a tick beyond 200 + LEASH_SLACK, and
    stands at its post for the last STAY ticks of the run, the Bastion having gone out of its notice distance."""
    w, g, e = _scene(lib, world_factory, 320.0, etype=BASTION, flee_to=(1900.0, 1000.0))
    full = hp(lib, w, e)
    rows = _run(lib, w, g, e, 700)
    assert rows[-1][3] < full, "the guard never fired on the retreating enemy"
    far = max(r[2] for r in rows)
    assert far >= GUARD_RADIUS - REACH_SLACK, "the guard followed only %.1f wu from its post (the radius is %.0f)" % (far, GUARD_RADIUS)
    assert not _beyond(rows), "%d ticks beyond %.0f wu from the post, first %s" % (len(_beyond(rows)), GUARD_RADIUS, _beyond(rows)[:3])
    assert all(r[2] <= ARRIVE for r in rows[-STAY:]), "the guard is not at its post at the end of the run (%.1f wu from it)" % rows[-1][2]


def test_R_208_01_a_guard_whose_target_leaves_its_notice_distance_returns_to_its_post(lib, world_factory):
    """R-208-01 "returning to the post when the lock ends" (E-11 R-087-03: the target leaves the notice distance): the guard has stepped 25 wu out to the enemy
    at +325; the enemy is put 345 wu east of the guard (370 from the post; beyond the notice distance, inside the radius plus the range, where the guard
    followed it before the ruling). Within RETURN_CAP ticks the guard is back within ARRIVE of the post and stays there; it holds no target; it never
    crosses the radius. Red today: the guard goes on after the enemy."""
    w, g, e = _scene(lib, world_factory, 325.0)
    rows = _run(lib, w, g, e, 40)
    assert any(r[4] > 0 for r in rows) and rows[-1][2] >= 20.0, "scene broken: the guard did not step out to the enemy (at %s)" % (rows[-1][1],)
    gx, gy = rows[-1][1]
    lib.om_unit_teleport(w, e, gx + NOTICE + 15.0, gy, 0)
    after = _run(lib, w, g, e, RETURN_CAP + STAY)
    _at_post_for_good(after)
    assert all(_none(r[4]) for r in after[RETURN_CAP - 1:]), "the guard holds a target again after its lock ended"
