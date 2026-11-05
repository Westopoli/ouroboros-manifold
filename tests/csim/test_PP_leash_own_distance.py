# Rule pins: R-087-05@a79833, R-096-03@16d0c4
"""PP-move: the attack-move leash measures the PURSUER, never the target (E-11 R-087-05, E-13 R-096-03;
ruling A188, docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 64/65).

Old rule (csrc/unit.c, both leash sites): a target more than OM_ATTACK_MOVE_LEASH_DIST (200 wu) from the
unit's anchor is dropped, so a Vanguard (range 300) that acquires at 294 wu drops the target on the next
AI tick and walks on to about 188 wu (tick 49 to 76 on the 16 v 16 line). New rule: the unit's OWN distance
from its anchor is tested; a unit holding and firing from its anchor never drops a target for the leash.

Scenes (Vanguard: range 300, sensor 700, march goal (0, -3000); Supply: 100 hp, never fires). The
positive controls (target far from the anchor AND the unit itself far from it) are green on the old rule
and must stay green after it. Each runs with OM_TP_LEASH_BEFORE_DAMAGE 0 (default) and 1.
"""
import pytest

from test_PP_unit_support import (BOMBARD, SUPPLY, VANGUARD, RAIDER, attack_move, dest, hp, pos, set_param, spawn,
                                  step, target)

LEASH = "OM_TP_LEASH_BEFORE_DAMAGE"
SWITCHES = pytest.mark.parametrize("switch", [0, 1], ids=["leash_after_damage_0", "leash_before_damage_1"])
GOAL = (0.0, -3000.0)


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _acquire(lib, w, switch, enemy_y, enemy_hp=None, utype=VANGUARD):
    """Unit at (0,0) attack-moving to GOAL, a Supply at (0, enemy_y). Runs until the unit holds it
    (a cohort cycle is under 25 ticks). Returns (unit, enemy, unit position at acquisition)."""
    assert set_param(lib, w, LEASH, switch) == 0
    u = spawn(lib, w, utype, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 0.0, enemy_y)
    if enemy_hp is not None:
        lib.om_unit_set_hp(w, enemy, enemy_hp)
    attack_move(lib, w, [u], *GOAL)
    for _ in range(40):
        step(lib, w)
        if target(lib, w, u) == enemy:
            return u, enemy, pos(lib, w, u)
    pytest.fail("fixture: the unit never acquired the target at %s wu" % enemy_y)


@SWITCHES
def test_R_087_05_A188_bombard_acquiring_at_1150_holds_and_fires_until_the_target_dies(lib, world_factory, switch):
    """R-087-05 / R-096-03 / A188, redesigned for H-057 (DEC-leash-param-2026-11-01: the leash is max(sensor, range) per type,
    so a Vanguard's range never exceeds it): a Bombard (range 1200, sensor 300) holds a Supply 1150 wu ahead (acquired at 150 wu,
    then stood at 1150 from its anchor: beyond every pre-ruling leash, 200 and 800, inside its range). Standing at its anchor it never drops the target for the leash: every tick from
    acquisition to the kill the target is held, the unit does not move, and the target dies.
    RED on the old rule: the target (294 wu from the anchor) is dropped on the next AI tick and the unit walks on."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, "OM_TP_TARGET_BY_SIGHT", 0) == 0   # sight is untouched by H-057: a Bombard with sight on and no spotter does not fire beyond 300
    u, enemy, anchor = _acquire(lib, w, switch, -150.0, enemy_hp=100.0, utype=BOMBARD)
    lib.om_unit_set_hp(w, enemy, 5.0)   # low hp: a Bombard does about 3.5 per 60 ticks, so it can die inside the loop
    lib.om_unit_teleport(w, enemy, anchor[0], anchor[1] - 1150.0, 0)   # 1150 wu from the anchor and from the unit
    assert _dist(anchor, pos(lib, w, enemy)) > 800.0, "fixture: the target must be beyond the leash from the anchor"
    held, moved = 0, 0.0
    for _ in range(300):
        if hp(lib, w, enemy) <= 0.0:
            break
        assert target(lib, w, u) == enemy, "target dropped for the leash while holding at the anchor (held %d ticks)" % held
        held += 1
        step(lib, w)
        moved = max(moved, _dist(anchor, pos(lib, w, u)))
    assert hp(lib, w, enemy) <= 0.0, "the held target was never killed"
    assert held >= 2, "fixture: the unit should hold over several ticks"
    assert moved <= 1.0, "the unit left its anchor (%.1f wu) while holding a target in range" % moved


def _held_scene(lib, w, switch, unit_off, target_off):
    """Acquire a target 150 wu ahead (inside the old leash), then place the unit `unit_off` wu from its anchor
    and the target `target_off` wu from the anchor, all on the line of march (y negative = ahead).
    Returns (unit, enemy, anchor)."""
    u, enemy, anchor = _acquire(lib, w, switch, -150.0, enemy_hp=100.0)
    ax, ay = anchor
    lib.om_unit_set_hp(w, enemy, 100.0)
    lib.om_unit_teleport(w, u, ax, ay - unit_off, 0)
    lib.om_unit_teleport(w, enemy, ax, ay - target_off, 0)
    return u, enemy, anchor


def _watch(lib, w, u, n):
    seen = []
    for _ in range(n):
        step(lib, w)
        seen.append(target(lib, w, u))
    return seen


@SWITCHES
def test_R_087_05_A188_unit_over_200_from_its_anchor_drops_its_target_and_resumes(lib, world_factory, switch):
    """R-096-03 / A188 positive control for the hold tests (green on the old rule, must stay green): the
    unit stands 201 wu from its anchor, its target 350 wu from the anchor (in range, 149 wu away). The unit
    itself is past the leash, so it drops the target within one cohort cycle and its goal is the march
    goal (it resumes the attack-move). Proves the detector reads 'dropped'."""
    w = world_factory(n_regions=1)
    u, enemy, anchor = _held_scene(lib, w, switch, 701.0, 850.0)
    seen = _watch(lib, w, u, 3)
    assert -1 in seen, "a unit 701 wu from its anchor kept its target: %s" % seen
    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(GOAL, abs=1e-6), "unit did not resume its attack-move"


@SWITCHES
def test_R_087_05_A188_unit_inside_200_of_its_anchor_keeps_a_target_far_from_the_anchor(lib, world_factory, switch):
    """R-087-05 / A188 boundary: the same scene with the unit 699 wu from its anchor (target still 850 wu from
    it, 151 wu from the unit, in range). The unit is inside its leash, so it keeps the target on every tick.
    RED on the old rule (the target is 350 wu from the anchor and is dropped)."""
    w = world_factory(n_regions=1)
    u, enemy, anchor = _held_scene(lib, w, switch, 699.0, 850.0)
    seen = _watch(lib, w, u, 3)
    assert seen == [enemy] * 3, "a unit 699 wu from its anchor dropped its target for the leash: %s" % seen


@SWITCHES
def test_R_087_05_A188_range_at_most_200_behaves_as_before(lib, world_factory, switch):
    """Guard (green before and after): a Raider (range 200) acquires a Supply 150 wu ahead and holds it every
    tick without moving; the target never leaves the 200 wu ring, so the old and new rules agree."""
    w = world_factory(n_regions=1)
    u, enemy, anchor = _acquire(lib, w, switch, -150.0, enemy_hp=100.0, utype=RAIDER)
    seen = _watch(lib, w, u, 3)
    assert seen[0] == enemy and all(t in (enemy, -1) for t in seen)
    if hp(lib, w, enemy) > 0.0:
        assert seen == [enemy] * 3, seen
    assert _dist(anchor, pos(lib, w, u)) <= 1.0


@SWITCHES
def test_R_087_05_A188_range_at_most_200_unit_past_its_leash_drops_as_before(lib, world_factory, switch):
    """Guard (green before and after): a Raider 801 wu from its anchor (leash = its sensor radius 800, H-057) with the target in its range drops it
    (target 850 wu from the anchor, 49 wu from the unit); same outcome under the old and new rule."""
    w = world_factory(n_regions=1)
    u, enemy, anchor = _acquire(lib, w, switch, -150.0, enemy_hp=100.0, utype=RAIDER)
    ax, ay = anchor
    lib.om_unit_teleport(w, u, ax, ay - 801.0, 0)      # H-057: a Raider's leash is its sensor radius 800
    lib.om_unit_teleport(w, enemy, ax, ay - 850.0, 0)
    assert -1 in _watch(lib, w, u, 3)


@SWITCHES
def test_R_087_05_A188_the_anchor_is_where_the_unit_stood_at_acquisition(lib, world_factory, switch):
    """Existing rule kept (R-087-05, contract item 16): the anchor is the unit's position at acquisition
    (om_unit_get_leash_anchor), not the order start (0, 0) and not the target. Green before and after."""
    import ctypes
    from conftest import OMWorldP
    w = world_factory(n_regions=1)
    u, enemy, acq = _acquire(lib, w, switch, -150.0, enemy_hp=100.0)
    ax, ay = ctypes.c_double(), ctypes.c_double()
    fn = lib.om_unit_get_leash_anchor.raw if hasattr(lib.om_unit_get_leash_anchor, "raw") else lib.om_unit_get_leash_anchor
    fn.argtypes = [OMWorldP, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    assert fn(w, u, ctypes.byref(ax), ctypes.byref(ay)) == 1
    assert _dist((ax.value, ay.value), acq) <= 8.0, "anchor %s is not the acquisition position %s" % ((ax.value, ay.value), acq)
    assert ay.value < -5.0, "anchor is the order start, not the acquisition spot"
