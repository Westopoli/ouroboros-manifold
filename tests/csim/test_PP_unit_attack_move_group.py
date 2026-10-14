"""PP-unit: attack-move as a group order (E-13 S-096, R-096-02; plan Phase A row P5, audit G11).

R-096-02: "Given an attack-move, When an enemy enters attack range on the unit's layer, Then the unit
halts and fires; when the target dies or leaves range it resumes toward the point. Two or more
units attack-moved together take formation slots as a move group does (R-095-02 to R-095-04); after
every fight the group resumes toward the point as a unit attack-moved alone does." (R-096-02 as
rewritten 2026-10-13, option (a); the text before it ended a group once every member had engaged,
superseded under TD-LAB-REV2-E1-2.)
Westley, on the lone unit: "It should resume its prior goal after the fight is completed", which now
holds for a group too.
Plan P5 also keeps the slowest-member speed cap (R-095-01: a group moves at its slowest member).

Today om_command_attack_move sends every unit to the one click point (no slots, no cap), and every
attack-mover, alone or in a group, resumes after any fight (om_tac_release). There is no getter for a unit's group id
(a missing observable; see the report), so "takes slots through om_command_group_move" is read off
each member's destination and speed, compared with what om_command_group_move itself gives an
identical formation.

Engaged = the member has held a target. Targets in the fight scenes are Supply units (never fire);
the test kills them by hand so the end of the fight is exact.
"""
import ctypes

import pytest

from test_PP_unit_support import (BASTION, RAIDER, SUPPLY, attack_move, dest, kill, pos, spawn, step,
                                  target)

FAR = 10000.0   # offset that keeps the control formation out of everything's reach

@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make



def _group_move(lib, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    gid = lib.om_command_group_move(w, arr, len(ids), float(x), float(y))
    assert gid != 0
    return gid


def _goal(lib, w, uid):
    has, x, y = dest(lib, w, uid)
    assert has == 1, f"unit {uid} has no goal"
    return (x, y)


LAYOUTS = {
    "pair_in_file": [(0.0, 0.0), (0.0, 100.0)],
    "three_abreast": [(0.0, 0.0), (0.0, 100.0), (0.0, 200.0)],
    "scattered_beyond_450": [(0.0, 0.0), (0.0, 1000.0)],      # scatter fallback: all to the click point
}


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_R_096_02_attack_moved_group_takes_move_group_slots(lib, world_factory, layout):
    """Units attack-moved together hold the slots a plain move group would give the same
    formation (offsets from the centroid; scatter fallback past 450 wu). The reference is
    om_command_group_move on an identical formation FAR away, so the comparison is made by the
    library itself, not by a formula in the test. Fails today for the two layouts that have slots:
    attack-move sends everyone to the click point."""
    w = world_factory(n_regions=1)
    mine = [spawn(lib, w, RAIDER, 0, x, y) for x, y in LAYOUTS[layout]]
    ref = [spawn(lib, w, RAIDER, 0, x, y + FAR) for x, y in LAYOUTS[layout]]

    attack_move(lib, w, mine, 1500.0, 40.0)
    _group_move(lib, w, ref, 1500.0, 40.0 + FAR)

    for m, r in zip(mine, ref):
        gx, gy = _goal(lib, w, m)
        rx, ry = _goal(lib, w, r)
        assert (gx, gy) == pytest.approx((rx, ry - FAR), abs=1e-6), (
            f"{layout}: member {m} goal ({gx}, {gy}) differs from the move-group slot ({rx}, {ry - FAR})")


def test_control_R_096_02_slots_differ_when_the_formation_has_room(lib, world_factory):
    """Positive control for the slot test (green today): in the pair layout the reference slots
    really are two different points, so 'both sent to the click point' is distinguishable from
    'took slots'."""
    w = world_factory(n_regions=1)
    ref = [spawn(lib, w, RAIDER, 0, x, y + FAR) for x, y in LAYOUTS["pair_in_file"]]
    _group_move(lib, w, ref, 1500.0, 40.0 + FAR)
    assert _goal(lib, w, ref[0]) != _goal(lib, w, ref[1])


def test_R_096_02_attack_moved_group_keeps_the_slowest_members_speed(lib, world_factory):
    """Plan P5 / R-095-01: attack-moved together, a Raider (150) and a Bastion (40) move at the
    slowest member's speed. Fails today: the Raider goes at its own speed."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    bastion = spawn(lib, w, BASTION, 0, 0.0, 100.0)
    slowest = min(lib.om_unit_effective_speed(w, raider), lib.om_unit_effective_speed(w, bastion))
    assert slowest == pytest.approx(40.0)

    attack_move(lib, w, [raider, bastion], 3000.0, 50.0)

    assert lib.om_unit_get_current_speed(w, raider) == pytest.approx(slowest, abs=1e-9)
    assert lib.om_unit_get_current_speed(w, bastion) == pytest.approx(slowest, abs=1e-9)


def test_control_R_096_02_move_group_cap_is_what_the_attack_move_test_measures(lib, world_factory):
    """Positive control (green today): the same pair under om_command_group_move reads the slowest
    member's speed through om_unit_get_current_speed, so that getter shows the cap."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, FAR)
    bastion = spawn(lib, w, BASTION, 0, 0.0, FAR + 100.0)
    _group_move(lib, w, [raider, bastion], 3000.0, FAR + 50.0)
    assert lib.om_unit_get_current_speed(w, raider) == pytest.approx(40.0, abs=1e-9)


# ---- the group resumes after every member has engaged, as a lone unit does ----

def _engage_pair(lib, w):
    """Two Raiders, each beside its own Supply target, attack-moved together toward (3000, 50).
    Returns (a, b, sa, sb) once both have held a target."""
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 100.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    sb = spawn(lib, w, SUPPLY, 1, 150.0, 100.0)
    attack_move(lib, w, [a, b], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa and target(lib, w, b) == sb:
            return a, b, sa, sb
    pytest.fail("fixture: both members should have engaged within 8 ticks")


def test_R_096_02_group_resumes_after_every_member_has_engaged(lib, world_factory):
    """Both members engage their own target, then both targets die: the group resumes the march
    (R-096-02 rewritten 2026-10-13; TD-LAB-REV2-E1-2 replaces the group-ends test). Both members
    move toward the point and keep a goal."""
    w = world_factory(n_regions=1)
    a, b, sa, sb = _engage_pair(lib, w)
    kill(lib, w, sa)
    kill(lib, w, sb)
    stopped = {a: pos(lib, w, a), b: pos(lib, w, b)}

    step(lib, w, 30)      # past the 10 tick backswing a first shot leaves, so a standstill is not a pause

    for u in (a, b):
        assert pos(lib, w, u)[0] > stopped[u][0], f"member {u} did not march on after every member had engaged"
        assert dest(lib, w, u)[0] == 1, f"member {u} lost its goal after the fight"


def test_control_R_096_02_group_goes_on_while_a_member_has_not_engaged(lib, world_factory):
    """Positive control (green before and after E1): the group marches on while one member (b, 2000 wu
    behind, out of everyone's sight) has not engaged, so the member that did (a) resumes toward the
    point when its target dies. Kept from the group-end days: a group never stopped for a member
    that had not engaged."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, -2000.0, 0.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [a, b], 3000.0, 0.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa:
            break
    assert target(lib, w, a) == sa, "fixture: a should have engaged"
    assert target(lib, w, b) == -1, "fixture: b must not have engaged"
    kill(lib, w, sa)
    x0 = pos(lib, w, a)[0]

    step(lib, w, 30)      # past the 10 tick backswing after a shot

    assert pos(lib, w, a)[0] > x0, "a should resume: its group is still marching"
    assert dest(lib, w, a)[0] == 1


def test_R_096_02_a_unit_attack_moved_alone_resumes_after_the_fight(lib, world_factory):
    """"A unit attack-moved alone is not a group: it resumes toward the point after every fight"
    (Westley: "It should resume its prior goal after the fight is completed"). The same fight as
    the group-resume test, with one Raider: when its target dies it marches on toward (3000, 50).
    Green before and after E1; kept so the group change cannot take the lone unit's march away."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [a], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa:
            break
    assert target(lib, w, a) == sa
    kill(lib, w, sa)
    x0 = pos(lib, w, a)[0]

    step(lib, w, 30)      # past the 10 tick backswing after a shot

    assert pos(lib, w, a)[0] > x0
    has, gx, gy = dest(lib, w, a)
    assert has == 1 and (gx, gy) == pytest.approx((3000.0, 50.0), abs=1e-6)
