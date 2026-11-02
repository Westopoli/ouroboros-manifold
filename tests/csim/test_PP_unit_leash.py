# Rule pins: R-087-05@a79833, R-096-03@16d0c4
"""PP-unit: the 200 wu leash and the leash-before-damage switch (E-11 R-087-05, E-13 R-096-03;
plan Phase A "Decisions": "200 wu leash before damage: a switch; the lab runs both; he picks";
audit G03).

R-087-05 / R-096-03: an attack-moving unit anchors at its position when it acquires a target; if the
target moves more than 200 wu from the anchor it drops the target.
G03: in the Python the drop runs BEFORE damage in the same step, so an attack-moving unit whose range
exceeds 200 (Vanguard 300) never fires at a target more than 200 wu from its anchor, and goes on
walking. The C checks the drop on the NEXT tick, after the shot. `OM_TP_LEASH_BEFORE_DAMAGE`
(om_tactical_set_param; default 0 = today's order, 1 = the Python's) selects between them. The
contract call and the enum are new (PP-contract): until they land the switch tests fail naming the
missing symbol.

Scene: Vanguard (range 300, sensor 700, 4 wu per tick), attack-moving to (0, -3000), idles 30 ticks
so its attack timer is full, then a Supply target (100 hp, never fires) appears BESIDE its path at
(250, y): inside range, outside the 200 wu leash. Walking on for 36 ticks it stays inside range
(sqrt(250^2 + 144^2) = 288 < 300), so every acquisition is at 250 wu or more.
"""
import pytest

from test_PP_unit_support import (SUPPLY, VANGUARD, attack_move, dest, get_param, hp, pos, set_param,
                                  spawn, step, target, watch_target)

LEASH = "OM_TP_LEASH_BEFORE_DAMAGE"

@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make



def _scene(lib, w, enemy_dx, switch=None):
    """Vanguard marching to (0, -3000); enemy appears beside it, enemy_dx wu to the side."""
    if switch is not None:
        assert set_param(lib, w, LEASH, switch) == 0
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)          # outside sensor range while the timer charges
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 30)
    ux, uy = pos(lib, w, u)
    lib.om_unit_teleport(w, enemy, ux + enemy_dx, uy, 0)
    return u, enemy, (ux, uy)


# ---- the switch itself ----

def test_R_087_05_leash_switch_default_and_range(lib, world_factory):
    """OM_TP_LEASH_BEFORE_DAMAGE defaults to 0 (today's order), takes 1, reads back, and an
    out-of-range value is refused and changes nothing (PP-contract: "-1 unknown or out of range")."""
    w = world_factory(n_regions=1)
    assert get_param(lib, w, LEASH) == 0.0
    assert set_param(lib, w, LEASH, 1) == 0
    assert get_param(lib, w, LEASH) == 1.0
    assert set_param(lib, w, LEASH, 2) == -1
    assert get_param(lib, w, LEASH) == 1.0
    assert set_param(lib, w, LEASH, 0) == 0
    assert get_param(lib, w, LEASH) == 0.0


# ---- switch 0: today's order, shot then drop ----

def test_R_096_03_switch_0_fires_before_the_leash_drops_the_target(lib, world_factory):
    """Default (switch 0, today's order): a Vanguard that acquires a target 250 wu away (beyond the
    200 wu leash, inside its 300 wu range) with a full attack timer shoots it. Green today; guards
    the default while the switch is built."""
    w = world_factory(n_regions=1)
    _, enemy, _ = _scene(lib, w, 250.0)
    before = hp(lib, w, enemy)

    step(lib, w, 30)

    assert hp(lib, w, enemy) < before, "switch 0 must keep today's order: the shot lands before the drop"


def test_R_087_05_target_beyond_200_from_the_anchor_is_dropped(lib, world_factory):
    """R-087-05 / R-096-03 (default order), re-pinned to A188 (the leash tests the unit's OWN distance from
    its anchor, never the target's): the unit moves from 0 to 250 wu from its anchor (its target, 150 wu from
    the anchor, stays inside its 300 wu range) and drops the target. The drop shows within one cohort cycle
    (a unit re-acquiring on its own turn re-anchors, so one tick can look kept)."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 4)
    assert target(lib, w, u) == enemy, "fixture: unit should have acquired and anchored"

    # Test-defect, H-057 (DEC-leash-anchor-return-2026-11-01): the leash is the type's sensor radius, a Vanguard's 700 wu, so the
    # unit goes 750 wu from its anchor with the target moved along (150 wu from the unit, in range): the drop is the leash's.
    lib.om_unit_teleport(w, u, 0.0, -750.0, 0)
    lib.om_unit_teleport(w, enemy, 150.0, -750.0, 0)
    seen = watch_target(lib, w, u, 4)

    assert -1 in seen, f"a unit 750 wu from its anchor never dropped its target: {seen}"


def test_control_R_087_05_target_inside_200_of_the_anchor_is_kept(lib, world_factory):
    """Positive control for the drop test above (green today): the unit moved to 650 wu from its anchor, still
    inside the leash (a Vanguard's sensor radius 700, H-057) with the target 190 wu beside it, in range, the same
    measure reads 'kept' on every tick."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 4)
    assert target(lib, w, u) == enemy

    lib.om_unit_teleport(w, u, 0.0, -650.0, 0)
    lib.om_unit_teleport(w, enemy, 190.0, -650.0, 0)
    seen = watch_target(lib, w, u, 4)

    assert seen == [enemy] * 4, f"target inside the leash was dropped: {seen}"


# ---- switch 1: the Python's order, drop then (no) damage ----

def test_R_096_03_switch_1_drops_before_damage_and_the_unit_walks_on(lib, world_factory):
    """Switch 1, re-pinned to A188 (the leash tests the unit's OWN distance from its anchor): the unit
    acquires a target 150 wu beside it, is then moved 250 wu from its anchor (the target stays in its
    range), and on the next tick drops it with no damage taken and its goal is the march goal again
    (it resumes). A target 250 wu from the anchor with the unit still at the anchor is no longer dropped."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, LEASH, 1) == 0
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 4)
    assert target(lib, w, u) == enemy, "fixture: unit should have acquired and anchored"
    before = hp(lib, w, enemy)

    lib.om_unit_teleport(w, u, 0.0, -750.0, 0)      # H-057: past the Vanguard's sensor radius 700, the leash (was 250 past 200)
    lib.om_unit_teleport(w, enemy, 150.0, -750.0, 0)
    step(lib, w)

    assert target(lib, w, u) == -1, "switch 1: a unit past the leash must drop its target"
    assert hp(lib, w, enemy) == before, "switch 1: the drop must come before damage"
    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx((0.0, -3000.0), abs=1e-6)


def test_control_R_096_03_switch_1_still_fires_inside_the_leash(lib, world_factory):
    """Positive control for the switch 1 test: with switch 1, a target 150 wu away (inside the 200
    wu leash) is shot. The no-damage reading above is therefore the leash, not a unit that cannot
    fire under switch 1."""
    w = world_factory(n_regions=1)
    _, enemy, _ = _scene(lib, w, 150.0, switch=1)
    before = hp(lib, w, enemy)

    step(lib, w, 30)

    assert hp(lib, w, enemy) < before


def test_R_096_03_switch_back_to_0_restores_the_shot(lib, world_factory):
    """Both ways on one world: switch 1 then 0 gives today's order again (fires at 250 wu)."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, LEASH, 1) == 0
    assert set_param(lib, w, LEASH, 0) == 0
    _, enemy, _ = _scene(lib, w, 250.0)
    before = hp(lib, w, enemy)

    step(lib, w, 30)

    assert hp(lib, w, enemy) < before
