"""Phase C, step G3: pursuit and hold follow the side's sight (E-12 R-093-02 "acquires, pursues or fires";
E-11 R-087-04; brief G3: "An attack-moving unit steps toward the nearest visible enemy within sensor
radius (today it steps toward any enemy, through anything)" and "a unit never sits holding a target it
cannot fire at").

R-087-04 in Phase A reads "visible" as the unit's own set (plan P1); in Phase C it becomes the side's
(plan Phase C: 'P1's "visible" is the unit's own set in Phase A ... and becomes the side's here'). The
shared-sight test below is the one that tells the two apart.

RED TODAY, and why: csrc/unit.c's attack-move pursuit calls om_tac_nearest_hostile(sensor radius) and
om_tac_hostile_within(attack range) with no sight test, so a Raider steps toward (and holds against) an
enemy that a cover disc hides from its whole side. The controls (open ground; a friend that sees it; the
switch at 0) are green today on purpose.

Scene: a Raider (range 200, sensor 800, speed 150 = 7.5 wu per tick) at the origin attack-moving to
(-3000, 0), an inert enemy Supply to its east on the x axis, a cover disc (radius 20, height 5) on the axis
between them. The march goes straight away from the enemy along the very line the cover sits on, so a
Raider that ignores the enemy keeps the line blocked for as long as it marches (a march at an angle would
walk out from behind the disc within a few ticks and the enemy would honestly come into sight). A unit that
ignores the enemy has its distance to it grow; a pursuer's shrinks.
"""
from test_PP_C_g3_support import (BIG_HP, INTERCEPTOR, RAIDER, attack_move, can_see, cohort_cycle, dist, hp, inert,
                                  pos, set_param, spawn, step, target)

TICKS = 40  # 300 wu of free march at 7.5 wu per tick


def _scene(lib, w, enemy_x, cover_x=None):
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    enemy = inert(lib, w, 1, enemy_x, 0.0)
    if cover_x is not None:
        assert lib.om_map_add_cover(w, cover_x, 0.0, 20.0, 5.0) != 0, "fixture: cover not added"
    attack_move(lib, w, [raider], -3000.0, 0.0)
    return raider, enemy


def test_R_093_02_a_hidden_enemy_is_not_pursued(lib, world_factory):
    """R-093-02, brief G3: an enemy 700 wu away, inside sensor range 800 but behind a cover disc on the
    line, is not in the side's visible set: the attack-moving Raider keeps marching west and its
    distance to the enemy only grows. Red today: it walks east at the hidden enemy."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 700.0, cover_x=350.0)
    assert can_see(lib, w, raider, enemy) == 0, "fixture: the cover must hide the enemy"
    start = dist(pos(lib, w, raider), pos(lib, w, enemy))

    step(lib, w, TICKS)

    assert dist(pos(lib, w, raider), pos(lib, w, enemy)) > start, "pursued an enemy its side cannot see"
    assert target(lib, w, raider) != enemy


def test_R_093_02_a_visible_enemy_is_pursued_control(lib, world_factory):
    """Positive control for the test above, rewritten under A199 (TD-PP-A199-repin; R-087-04): no cover, same
    scene, the enemy in plain sight 700 wu away: an attack-mover does not walk toward an enemy it merely sees,
    so its distance grows just as for the hidden one. What sight buys is the shot: the same enemy brought into
    attack range is acquired and fired at (so the hidden test passes because of the cover, not on a unit that
    reacts to nothing)."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 700.0)
    assert can_see(lib, w, raider, enemy) == 1, "fixture: open ground must show the enemy"
    start = dist(pos(lib, w, raider), pos(lib, w, enemy))

    step(lib, w, TICKS)

    # Test-defect, H-057 (R-087-04 rev 2026-11-01): a seen enemy out of attack range is chased (was: A199, distance grows).
    assert dist(pos(lib, w, raider), pos(lib, w, enemy)) < start, "a seen enemy out of attack range is not chased"

    here = pos(lib, w, raider)
    lib.om_unit_teleport(w, enemy, here[0] + 150.0, here[1], 0)
    step(lib, w, cohort_cycle(lib, w))
    assert target(lib, w, raider) == enemy and hp(lib, w, enemy) < BIG_HP, "in attack range it is acquired and hit"


def test_R_089_02_a_friend_that_sees_the_enemy_lets_it_be_pursued(lib, world_factory):
    """R-089-02, R-093-02, plan Phase C (shared sight), rewritten under A199 (TD-PP-A199-repin): the same
    hidden enemy, but a friendly Interceptor 300 wu from it with a clear line sees it. The side's set no longer
    makes the Raider walk toward it (R-087-04): its distance still grows. What the side's set does give is the
    shot: with the enemy 150 wu away and the Raider's own sensing blanked by an interference zone on it (the
    friend sees it), the Raider acquires and fires at it."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 700.0, cover_x=350.0)
    friend = spawn(lib, w, INTERCEPTOR, 0, 700.0, 300.0)
    assert can_see(lib, w, raider, enemy) == 0 and can_see(lib, w, friend, enemy) == 1, "fixture: sight"
    start = dist(pos(lib, w, raider), pos(lib, w, enemy))

    step(lib, w, TICKS)

    # Test-defect, H-057 (R-087-04: "an enemy its side can see"): the friend's sight makes it chase (was: A199, distance grows).
    assert dist(pos(lib, w, raider), pos(lib, w, enemy)) < start, "a friend's sight does not make it chase"

    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 150.0)
    friend = spawn(lib, w, INTERCEPTOR, 0, 150.0, 300.0)
    lib.om_map_add_interference_zone(w, 0.0, 0.0, 0, 1.0, 100.0)
    assert can_see(lib, w, raider, enemy) == 0 and can_see(lib, w, friend, enemy) == 1, "fixture: sight"

    step(lib, w, cohort_cycle(lib, w))

    assert target(lib, w, raider) == enemy and hp(lib, w, enemy) < BIG_HP, "the side sees the enemy in range: it is fired at"




def test_R_093_02_beyond_sensor_radius_nothing_reacts(lib, world_factory):
    """Brief G3 test 'two forces separated by more than sensor radius do not react to each other': an
    enemy 900 wu away (sensor 800) on open ground: the Raider marches west, the distance grows. Green
    today; guards a fix that would make units chase beyond what anyone sees."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 900.0)
    assert can_see(lib, w, raider, enemy) == 0, "fixture: 900 wu is beyond sensor 800"
    start = dist(pos(lib, w, raider), pos(lib, w, enemy))

    step(lib, w, TICKS)

    assert dist(pos(lib, w, raider), pos(lib, w, enemy)) > start


def test_R_093_02_no_holding_against_a_hidden_enemy_in_range(lib, world_factory):
    """Brief G3 ('a unit never sits holding a target it cannot fire at'), R-093-02: an enemy 150 wu away,
    inside attack range 200, behind a cover disc 75 wu out: its side cannot see it. The attack-moving
    Raider does not hold against it: it keeps marching (its x decreases) and never takes it as a target
    or damages it. Red today: om_tac_hostile_within holds it in place for good."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 150.0, cover_x=75.0)
    assert can_see(lib, w, raider, enemy) == 0, "fixture: the cover must hide the enemy"

    step(lib, w, TICKS)

    assert pos(lib, w, raider)[0] < 0.0, "the Raider is holding against an enemy its side cannot see"
    assert target(lib, w, raider) != enemy and hp(lib, w, enemy) == BIG_HP


def test_R_093_02_holding_against_a_visible_enemy_in_range_control(lib, world_factory):
    """Positive control for the test above: no cover, same scene: the Raider holds position and hits the
    enemy. Green today and after."""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 150.0)
    assert can_see(lib, w, raider, enemy) == 1, "fixture: sight"

    step(lib, w, TICKS)

    assert target(lib, w, raider) == enemy and hp(lib, w, enemy) < BIG_HP, "a visible enemy in range is fought"


def test_R_093_02_a_target_that_goes_behind_cover_is_dropped(lib, world_factory):
    """Brief G3 ('a unit whose target moves behind a mass retargets'; 'a target that leaves the visible
    set ... is dropped at the next acquisition'): the Raider holds and fires at an enemy 150 wu away; a
    cover disc then appears on the line (the line of sight, not the unit, changes). Within one cohort
    cycle the Raider has dropped the target, no damage lands from then on, and it resumes its march west.
    Red today: it keeps holding the target. (Bible R-007-06: an endpoint inside a disc is exempt; both
    units here stand outside it.)"""
    w = world_factory(n_regions=1)
    raider, enemy = _scene(lib, w, 150.0)
    step(lib, w, TICKS)
    assert target(lib, w, raider) == enemy and hp(lib, w, enemy) < BIG_HP, "control: it was fighting"

    assert lib.om_map_add_cover(w, 75.0, 0.0, 20.0, 5.0) != 0
    assert can_see(lib, w, raider, enemy) == 0, "fixture: the new cover hides the enemy"
    cycle = cohort_cycle(lib, w)
    held_at_cycle = None
    frozen = None
    for tick in range(1, TICKS + 1):
        step(lib, w)
        if tick == cycle:
            held_at_cycle = target(lib, w, raider) == enemy
            frozen = hp(lib, w, enemy)
    assert held_at_cycle is False, f"still holding the hidden target {cycle} ticks after it was hidden"
    assert hp(lib, w, enemy) == frozen, "damage landed after the target was dropped"
    assert pos(lib, w, raider)[0] < 0.0, "a unit that dropped its target resumes its attack-move march"
