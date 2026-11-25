# Rule pins: DEC-movement-sidestep-2026-11-24 (2), R-097-03, ALG-68, R-097-10
"""Movement-sidestep LS1 (b): the steering probe is not blocked by a group mate or by an idle friend; an enemy, an engaged or moving friend and a guard still block it.

Rule words (docs/northstar/story_reviews/westley/decisions.md, DEC-movement-sidestep-2026-11-24, point 2): "the steering probe is not blocked by a group
mate or by an idle friend of the mover's own side (what ALG-68 already says; the code stopped doing it on 2026-10-02, `a47c9876c`), and is blocked by an enemy,
an engaged or moving friend". R-097-03: "it probes 40 wu ahead; if a unit on its layer ... blocks the probe (an idle unit of its own side does not block: idle
means no move target and not engaged; an enemy always does) it tries +30, -30, +60, -60, +90 and -90 degrees from its heading, in that order, and takes the
first clear one". Spec: docs/northstar/plans/movement-sidestep-2026-11-24/spec.md "The behaviour" 2 and "Tests" (b).

Scene: flyers (the probe is read by the steering step of non-walkers only; see sidestep_support.py). A mover M at (500, 1000) ordered to (3000, 1000); a candidate blocker X
40 wu ahead at (540, 1000), so X stands exactly on the probe's tip. M heads straight on its first ticks unless the probe was blocked, in which case the first clear
sweep angle (+30 and -30 are blocked by X too; +60) turns it to the left: its y rises at once. "Deflects" is therefore M's y leaving 1000 within the first 3 ticks.

Red today: the gather includes group mates and idle friends, so M deflects for both (the two `_skips_` tests). Green today (controls: the harness sees a deflection and
the five blockers the spec keeps blocking do deflect M): enemy, guard friend, engaged friend, moving friend of another group, and a group mate of ANOTHER group.
"""
import pytest

from sidestep_support import RAIDER, VANGUARD, dest, engaged_friend, group_move, guard, move, run_steps, spawn, step, supply, world

M0 = (500.0, 1000.0)
X0 = (540.0, 1000.0)
FAR = (3000.0, 1000.0)
TICKS = 3
DEFLECT_WU = 0.5           # y change that counts as a deflection: a +60 turn at about 2 wu a tick moves y by over 1 wu on the first tick


def _deflected(track):
    return max(abs(p[1] - M0[1]) for p in track) > DEFLECT_WU


WARM_UP = 5   # ticks with no order given: the idle flag of the collision pass (ms->idle) is written at the end of a tick, so a unit is read idle from the second tick of its life on (A also deflects on tick 1 for an idle friend), and the engaged friend has its target


WARM_UP = 2   # idle friend only: ms->idle is written by the collision pass at the end of a tick, so a unit is read idle from its second tick on (variant A also deflects on tick 1 for an idle friend). No other kind waits: an enemy in notice would hold M's attention (M would take a target and not step)


def _scene(lib, wf, kind):
    """Returns (w, mover id, blocker id) for `kind`: the idle friend stands WARM_UP ticks before the orders are given; every other kind is ordered on tick 0."""
    w = world(lib, wf)
    m = spawn(lib, w, RAIDER, 0, *M0)
    other = None
    if kind in ("group_mate", "idle_friend", "moving_friend", "other_group_mate"):
        x = spawn(lib, w, RAIDER, 0, *X0)
    elif kind == "enemy":
        x = supply(lib, w, 1, *X0)
    elif kind == "guard_friend":
        x = spawn(lib, w, VANGUARD, 0, *X0)
    elif kind == "engaged_friend":
        x, _ = engaged_friend(lib, w, X0)
    if kind == "guard_friend":
        guard(lib, w, [x])
    if kind == "other_group_mate":
        other = spawn(lib, w, RAIDER, 0, 540.0, 1400.0)
    if kind == "idle_friend":
        step(lib, w, WARM_UP)
    if kind == "group_mate":
        assert group_move(lib, w, [m, x], *FAR) != 0               # M and X take one group; both walk to slots 40 wu apart, X ahead
    else:
        if kind == "moving_friend":
            move(lib, w, [x], *FAR)                                # a friend with a move order of its own, no group
        if kind == "other_group_mate":
            group_move(lib, w, [x, other], *FAR)                   # X is in a group, M is not in it
        move(lib, w, [m], *FAR)
    return w, m, x


def _track(lib, wf, kind):
    w, m, _ = _scene(lib, wf, kind)
    return run_steps(lib, w, m, TICKS)


# ---------------------------------------------------------------- the skip (red today)

def test_DEC_movement_sidestep_a_group_mate_does_not_deflect_the_mover(lib, world_factory):
    """DEC-movement-sidestep-2026-11-24 (2): 'the steering probe is not blocked by a group mate'. M and X are group-moved together to (3000, 1000), X 40 wu ahead of M;
    X is a member of M's group (their slots keep the 40 wu), so the probe tip stands on a mate and must read clear: M's first ticks are straight, y stays 1000.
    Positive control: test_DEC_movement_sidestep_control_an_enemy_on_the_tip_deflects_the_mover (same scene, X an enemy). Red today: M turns left on tick 1."""
    track = _track(lib, world_factory, "group_mate")
    assert not _deflected(track), "M deflected for a group mate: y over %d ticks %s" % (TICKS, [round(p[1], 3) for p in track])


def test_DEC_movement_sidestep_an_idle_friend_does_not_deflect_the_mover(lib, world_factory):
    """DEC-movement-sidestep-2026-11-24 (2): 'the steering probe is not blocked by ... an idle friend of the mover's own side'; R-097-03 'an idle unit of its own side does not
    block'. X is an own Raider with no order, no target, no guard (idle) on the probe's tip; M, moved alone, goes straight. Red today: M turns left on tick 1."""
    track = _track(lib, world_factory, "idle_friend")
    assert not _deflected(track), "M deflected for an idle friend: y over %d ticks %s" % (TICKS, [round(p[1], 3) for p in track])


# ---------------------------------------------------------------- what still blocks (controls, green today)

def test_DEC_movement_sidestep_control_an_enemy_on_the_tip_deflects_the_mover(lib, world_factory):
    """Control (green today and after): 'is blocked by an enemy'; R-097-03 'an enemy always does'. Same scene with X an enemy Supply: M's y leaves 1000 within 3 ticks.
    This is the positive control of the two skip tests: it proves `_deflected` sees a turn in this harness (their red is the missing skip, not a blind detector)."""
    track = _track(lib, world_factory, "enemy")
    assert _deflected(track), "M did not deflect for an enemy: y %s" % ([round(p[1], 3) for p in track],)


@pytest.mark.parametrize("kind", ["guard_friend", "engaged_friend", "moving_friend", "other_group_mate"])
def test_DEC_movement_sidestep_control_a_friend_that_holds_fires_moves_or_is_in_another_group_still_deflects_the_mover(lib, world_factory, kind):
    """DEC-movement-sidestep-2026-11-24 (2): 'is blocked by an enemy, an engaged or moving friend'. A guard (not idle: it holds its post), a friend that holds a target and fires
    (engaged), a friend with a move order of its own, a member of a different group: each on the tip deflects M. Green today and must stay green: a skip written too wide
    (every friend) turns these red. They are the other half of the skip tests: removing the skip's conditions one by one must turn exactly one of them red."""
    track = _track(lib, world_factory, kind)
    assert _deflected(track), "M did not deflect for %s: y %s" % (kind, [round(p[1], 3) for p in track])


def test_DEC_movement_sidestep_control_the_skip_is_the_mover_s_own_group_only(lib, world_factory):
    """DEC-movement-sidestep-2026-11-24 (2) 'a group mate' is a unit with the mover's own non-zero group: premise check that the group scene really puts both in one group:
    after a group move of M and X, both report a destination (a slot), and M's slot is 40 wu behind X's (so X stays on M's tip as both walk)."""
    w, m, x = _scene(lib, world_factory, "group_mate")
    hm, sx, sy = dest(lib, w, m)
    hx, tx, ty = dest(lib, w, x)
    assert hm == 1 and hx == 1
    assert abs((tx - sx) - 40.0) < 1e-6 and abs(ty - sy) < 1e-6, "slots %s and %s: premise: X's slot is 40 wu ahead of M's" % ((sx, sy), (tx, ty))
