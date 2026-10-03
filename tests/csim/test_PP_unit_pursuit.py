"""PP-unit: pursuit through ordinary movement (E-11 S-087, R-087-04; plan Phase A row P1, audit G10).

R-087-04: "Given an attack-moving unit whose target is not within its attack range and a visible
enemy within sensor range, When evaluated, Then its move goal becomes the nearest visible enemy and
it walks there by its ordinary movement (R-097-03), steering around units in its way; it holds
position only while its own target is within its attack range, and pursues again when the target
leaves that range."
Plan P1 adds: chosen on the unit's cohort turn; the chase persists after arrival; a kept
out-of-range target survives between cohort turns; "visible" is the unit's OWN set in Phase A (the
side's set arrives in Phase C).

Observable used for "move goal": om_unit_get_destination (has_dest, x, y). Today the C walks a
pursuing unit by writing its position straight from unit.c (om_tac_step_toward) and leaves the
movement layer's goal on the march point, so the goal never becomes the enemy.

Scene unit: Raider (range 200, sensor 800, speed 150 = 7.5 wu per tick). Targets are Supply units
(never fire, so they cannot change what the attacker does); cohort turn = within 4 ticks.
"""
import pytest

from test_PP_unit_support import (RAIDER, INTERCEPTOR, SUPPLY, TICK_RATE, attack_move, dest, kill,
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
    """Attack-moving Raider marching to (0, -3000); two enemies in sensor range, none in attack
    range. After one cohort cycle its move goal is the NEAREST one, not the march point."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    near = spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    spawn(lib, w, SUPPLY, 1, 700.0, 300.0)            # 761 wu away: also in sensor range, not nearest
    attack_move(lib, w, [u], 0.0, -3000.0)

    step(lib, w, CYCLE)

    _assert_goal(lib, w, u, 500.0, 0.0, "R-087-04 nearest visible enemy")


def test_R_087_04_pursuit_is_ordinary_movement(lib, world_factory):
    """The pursuer walks by the movement layer, not by a position write from the AI: the movement
    layer reports it moving at its speed (today the AI marks it 'engaged', so the movement layer
    reports speed 0 while its position is written directly), and it closes on the enemy every tick."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 600.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, CYCLE)

    prev = _dist(pos(lib, w, u), pos(lib, w, enemy))   # before the getter: it syncs movement early
    assert lib.om_unit_get_current_speed(w, u) == pytest.approx(lib.om_unit_effective_speed(w, u), abs=1e-9), (
        "pursuing unit is not walking at its own speed through the movement layer")
    for _ in range(6):
        step(lib, w)
        now = _dist(pos(lib, w, u), pos(lib, w, enemy))
        assert now < prev, "pursuer did not close on the enemy this tick"
        prev = now


def test_R_087_04_holds_only_while_its_own_target_is_in_range(lib, world_factory):
    """Holds while its own target is in attack range (control: green today); once the target leaves
    that range it pursues again: the goal becomes the enemy's new place and the unit walks."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)       # in range 200
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, CYCLE)
    assert target(lib, w, u) == enemy
    held_at = pos(lib, w, u)
    step(lib, w, 8)
    assert pos(lib, w, u) == held_at, "unit moved while its target was in attack range"

    lib.om_unit_teleport(w, enemy, 600.0, 0.0, 0)      # out of range 200, inside sensor 800
    step(lib, w, CYCLE)
    _assert_goal(lib, w, u, 600.0, 0.0, "R-087-04 pursues again when the target leaves range")
    before = _dist(pos(lib, w, u), (600.0, 0.0))
    step(lib, w, 4)
    assert _dist(pos(lib, w, u), (600.0, 0.0)) < before


def test_R_087_04_chase_persists_after_arrival(lib, world_factory):
    """Plan P1: "the chase persists after arrival". A Raider attack-moves to (300, 0) and arrives
    with nothing around; an enemy then appears 600 wu on, inside sensor range. The unit, though it
    has arrived, goes after it (today it drops the order on arrival and sits idle)."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    attack_move(lib, w, [u], 300.0, 0.0)
    step(lib, w, 60)                                    # 300 wu at 7.5 per tick = 40 ticks
    # Arrived means within the arrival radius (R-099-04: 1.5 x collision radius 15 = 22.5 wu), not on the point.
    assert pos(lib, w, u) == pytest.approx((300.0, 0.0), abs=22.5), "fixture: unit should have arrived"

    enemy = spawn(lib, w, SUPPLY, 1, 900.0, 0.0)        # 600 wu from the arrived unit
    step(lib, w, CYCLE)
    _assert_goal(lib, w, u, 900.0, 0.0, "R-087-04 chase persists after arrival")
    x0 = pos(lib, w, u)[0]
    step(lib, w, 4)
    assert pos(lib, w, u)[0] > x0, "arrived unit did not walk after the visible enemy"


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
    """"a visible enemy within sensor range": a stealthed enemy in sensor range is not pursued
    (the unit goes on to its march point); the same enemy, no longer stealthed, is."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    lib.om_unit_set_stealth(w, enemy, 1)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, CYCLE)
    _assert_goal(lib, w, u, 0.0, -3000.0, "stealthed enemy must not be pursued")

    lib.om_unit_set_stealth(w, enemy, 0)
    step(lib, w, CYCLE)
    _assert_goal(lib, w, u, 500.0, 0.0, "visible enemy is pursued (positive control)")


def test_R_087_04_visible_means_the_sides_set(lib, world_factory):
    """R-087-04 / R-093-02 (Phase C, A185): "visible" is the pursuer's SIDE's set. A friendly Interceptor
    (sensor 1000) sees an enemy 600 wu from a Raider whose own sensing is blanked by an interference zone
    on it. Preconditions are asserted (the friend sees the enemy, the Raider does not); the Raider, whose
    side sees the enemy and which has it inside its sensor radius, then pursues it.
    TD-PP-C-r08704-sideset (A185): the Phase A text of this test (own set only, march goes on) is
    superseded; plan P1 / Phase C."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    spotter = spawn(lib, w, INTERCEPTOR, 0, 0.0, 700.0)
    enemy = spawn(lib, w, SUPPLY, 1, 600.0, 0.0)
    lib.om_map_add_interference_zone(w, 0.0, 0.0, 0, 1.0, 100.0)
    attack_move(lib, w, [u], -3000.0, 0.0)
    assert lib.om_unit_can_see(w, spotter, enemy) == 1, "fixture: the spotter should see the enemy"
    assert lib.om_unit_can_see(w, u, enemy) == 0, "fixture: the interference zone should blind the Raider"

    step(lib, w, CYCLE + 4)

    _assert_goal(lib, w, u, 600.0, 0.0, "R-087-04 the side's visible set (Phase C)")
    assert pos(lib, w, u)[0] > 0.0, "Raider did not walk toward an enemy its friend sees"
