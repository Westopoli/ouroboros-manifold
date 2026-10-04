"""PP-unit: no pursuit on sight (E-11 S-087, R-087-04, R-087-05; plan Phase A row P1, audit G10).

R-087-04 as rewritten by ruling A199 (2026-10-03): an attack-moving unit with no target within its attack range
keeps marching on its slot and route and does not walk toward an enemy it merely sees in sensor range; it halts
and fires when an enemy is within its attack range, and an acquired target that leaves that range is followed by
the march under the leash (R-087-05: the pursuer's own distance from its anchor, 200 wu).
TD-PP-A199-repin: the Phase A text of these scenes (move goal becomes the nearest visible enemy) is superseded;
each scene keeps its geometry and now asserts the opposite (the goal stays on the march, the distance to a seen
enemy grows) and then the half that survives (an enemy brought into attack range is acquired and fired at).
Plan P1 still holds for: the cohort turn, "a kept out-of-range target survives between cohort turns".

Observable used for "move goal": om_unit_get_destination (has_dest, x, y).

Scene unit: Raider (range 200, sensor 800, speed 150 = 7.5 wu per tick). Targets are Supply units
(never fire, so they cannot change what the attacker does); cohort turn = within 4 ticks.
"""
import pytest

from test_PP_unit_support import (RAIDER, INTERCEPTOR, SUPPLY, TICK_RATE, attack_move, dest, hp, kill,
                                  pos, spawn, step, target, watch_target)

CYCLE = 4  # one full cohort cycle: every unit has had its turn

@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make


@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make



def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _assert_goal(lib, w, uid, x, y, why):
    has, gx, gy = dest(lib, w, uid)
    assert has == 1, f"{why}: unit has no move goal"
    assert (gx, gy) == pytest.approx((x, y), abs=1e-6), f"{why}: goal is ({gx}, {gy}), want ({x}, {y})"


def test_R_087_04_move_goal_becomes_the_nearest_visible_enemy(lib, world_factory):
    """Attack-moving Raider marching to (0, -3000); two enemies in sensor range, none in attack range. A full
    cohort cycle on and for 40 ticks after, its move goal is still the march point and it is farther from both
    (R-087-04: no walking toward an enemy merely seen). Brought into attack range, the nearest is acquired and
    fired at."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    near = spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    far = spawn(lib, w, SUPPLY, 1, 700.0, 300.0)      # 761 wu away: also in sensor range, not nearest
    attack_move(lib, w, [u], 0.0, -3000.0)
    start = (_dist(pos(lib, w, u), pos(lib, w, near)), _dist(pos(lib, w, u), pos(lib, w, far)))

    step(lib, w, 40)

    _assert_goal(lib, w, u, 0.0, -3000.0, "R-087-04 a seen enemy is not walked toward")
    assert _dist(pos(lib, w, u), pos(lib, w, near)) > start[0] and _dist(pos(lib, w, u), pos(lib, w, far)) > start[1]
    assert target(lib, w, u) == -1

    here = pos(lib, w, u)
    lib.om_unit_teleport(w, near, here[0] + 150.0, here[1], 0)   # inside attack range 200
    hp0 = hp(lib, w, near)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == near, "the enemy in attack range is acquired (nearest)"
    assert hp(lib, w, near) < hp0, "and fired at"


def test_R_087_04_pursuit_is_ordinary_movement(lib, world_factory):
    """With a seen enemy out of range the unit walks its march by the movement layer, at its own speed, and its
    distance to the enemy grows every tick (it does not close on it)."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 600.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, CYCLE)

    prev = _dist(pos(lib, w, u), pos(lib, w, enemy))   # before the getter: it syncs movement early
    assert lib.om_unit_get_current_speed(w, u) == pytest.approx(lib.om_unit_effective_speed(w, u), abs=1e-9), (
        "marching unit is not walking at its own speed through the movement layer")
    for _ in range(6):
        step(lib, w)
        now = _dist(pos(lib, w, u), pos(lib, w, enemy))
        assert now > prev, "the unit closed on a seen enemy it has no reason to chase"
        prev = now


def test_R_087_04_holds_only_while_its_own_target_is_in_range(lib, world_factory):
    """Marching east to (3000, 0). Holds while its own target is in attack range (control); once the target
    leaves that range (350 wu, inside sensor 800) the march goes on toward it (R-087-04, goal stays the march
    point) and, 150 wu of walking being under the 200 wu leash (R-087-05), the unit halts again once the
    target is within attack range 200 and fires."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)       # in range 200
    attack_move(lib, w, [u], 3000.0, 0.0)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy
    held_at = pos(lib, w, u)
    step(lib, w, 8)
    assert pos(lib, w, u) == held_at, "unit moved while its target was in attack range"

    lib.om_unit_teleport(w, enemy, 350.0, 0.0, 0)      # out of range 200, inside sensor 800
    step(lib, w, 4)
    _assert_goal(lib, w, u, 3000.0, 0.0, "the goal stays the march point")
    before = _dist(pos(lib, w, u), (350.0, 0.0))
    step(lib, w, 4)
    assert _dist(pos(lib, w, u), (350.0, 0.0)) < before, "the march did not close on its target"

    step(lib, w, 40)                                   # 150 wu to walk is 20 ticks; a margin
    assert _dist(pos(lib, w, u), (350.0, 0.0)) <= 200.0 + 7.5, "the unit did not halt in attack range"
    halted = pos(lib, w, u)
    step(lib, w, 8)
    assert pos(lib, w, u) == halted and target(lib, w, u) == enemy, "it holds and keeps the target"


def test_R_087_04_chase_persists_after_arrival(lib, world_factory):
    """A Raider attack-moves to (300, 0) and arrives with nothing around; an enemy then appears 600 wu on,
    inside sensor range. The arrived unit does not go after it (R-087-04); once the enemy is brought into attack
    range it acquires it and fires."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    attack_move(lib, w, [u], 300.0, 0.0)
    step(lib, w, 60)                                    # 300 wu at 7.5 per tick = 40 ticks
    # Arrived means within the arrival radius (R-099-04: 1.5 x collision radius 15 = 22.5 wu), not on the point.
    assert pos(lib, w, u) == pytest.approx((300.0, 0.0), abs=22.5), "fixture: unit should have arrived"

    enemy = spawn(lib, w, SUPPLY, 1, 900.0, 0.0)        # 600 wu from the arrived unit
    here = pos(lib, w, u)
    step(lib, w, CYCLE * 4)
    assert pos(lib, w, u) == here, "arrived unit walked after a seen enemy"
    assert target(lib, w, u) == -1

    lib.om_unit_teleport(w, enemy, here[0] + 150.0, here[1], 0)
    hp0 = hp(lib, w, enemy)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy and hp(lib, w, enemy) < hp0, "an enemy in attack range is acquired and fired at"


def test_R_087_04_out_of_range_target_survives_between_cohort_turns(lib, world_factory):
    """Plan P1 / audit G10: "a kept out-of-range target survives between cohort turns" (the Python
    keeps an alive target that has left range until a cohort turn finds another; the C clears it the
    same tick). An idle Raider holds an in-range target, then the target is moved 300 wu out (range
    200). On every tick of the next full cohort cycle the unit still holds it. Idle, not attack-
    moving: an attack-mover's target that far from its anchor is dropped at once by the 200 wu leash
    (R-087-05; the Python does the same), which would hide what is measured here."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy

    lib.om_unit_teleport(w, enemy, 300.0, 0.0, 0)
    seen = watch_target(lib, w, u, CYCLE)

    assert seen == [enemy] * CYCLE, f"target dropped after leaving range: {seen}"


def test_control_R_087_04_dead_target_is_released(lib, world_factory):
    """Positive control for the survival test above (green today): the same measure sees a held
    target being released when it dies, so 'still held' is a real reading, not a stuck getter."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy

    kill(lib, w, enemy)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == -1


def test_R_087_04_only_a_visible_enemy_is_pursued(lib, world_factory):
    """A stealthed enemy inside attack range is not acquired (the unit goes on to its march point); the same
    enemy, no longer stealthed, is. A seen enemy outside attack range is walked toward in neither case."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    lib.om_unit_set_stealth(w, enemy, 1)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, CYCLE)
    _assert_goal(lib, w, u, 0.0, -3000.0, "stealthed enemy must not be acquired")
    assert target(lib, w, u) == -1

    lib.om_unit_set_stealth(w, enemy, 0)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy, "visible enemy in attack range is acquired (positive control)"


def test_R_087_04_visible_means_the_sides_set(lib, world_factory):
    """R-087-04 / R-093-02 (Phase C, A185): "visible" is the unit's SIDE's set. A friendly Interceptor
    (sensor 1000) sees an enemy 600 wu from a Raider whose own sensing is blanked by an interference zone
    on it. Preconditions are asserted (the friend sees the enemy, the Raider does not). The Raider does not
    walk toward the enemy its friend sees (A199); with the enemy brought into its attack range, the side's
    sight is enough to acquire it.
    TD-PP-C-r08704-sideset (A185) and TD-PP-A199-repin: the pursuit half is superseded."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    spotter = spawn(lib, w, INTERCEPTOR, 0, 0.0, 700.0)
    enemy = spawn(lib, w, SUPPLY, 1, 600.0, 0.0)
    lib.om_map_add_interference_zone(w, 0.0, 0.0, 0, 1.0, 100.0)
    attack_move(lib, w, [u], -3000.0, 0.0)
    assert lib.om_unit_can_see(w, spotter, enemy) == 1, "fixture: the spotter should see the enemy"
    assert lib.om_unit_can_see(w, u, enemy) == 0, "fixture: the interference zone should blind the Raider"

    step(lib, w, CYCLE + 4)

    _assert_goal(lib, w, u, -3000.0, 0.0, "R-087-04 the march goes on")
    assert pos(lib, w, u)[0] < 0.0, "Raider walked toward an enemy its friend sees"

    here = pos(lib, w, u)
    lib.om_unit_teleport(w, enemy, here[0] + 150.0, here[1], 0)
    assert lib.om_unit_can_see(w, spotter, enemy) == 1, "fixture: the spotter still sees the enemy"
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy, "the side sees the enemy in attack range: it is acquired"
