"""ALG-62 Targeting (docs/bible/algorithms.md; S-087, R-087-03..06).

ALG-62: units under a plain move skip targeting. A unit keeps its current target if alive and within attack range.
Otherwise, on its cohort tick (`uid mod TARGETING_COHORT_COUNT = 4 == tick mod 4`) it acquires the nearest same-layer
enemy within attack range. Return fire: an idle unit with no target and no order that takes damage targets the
attacker. Flinch: a unit that cannot return fire moves `_RETURN_FIRE_FLEE_DIST = 200` wu away from the attacker.

Conventions the test relies on, each checked in the file: C unit ids start at 1 and the Python uid is 0-based, so the
rule's `uid` is `id - 1` (csrc/unit.c om_unit_cohort_slot, A163/A164) and `tick` is the 1-based step count.
The sensor-radius clause of ALG-62 (an attack-moving unit with sensor radius > attack range acquires the nearest
visible enemy and moves toward it) is NOT asserted as written: E-11 R-087-04 (Westley 2026-10-03, A199) rules the
opposite, and test_ALG_62_attack_move_does_not_walk_toward_an_enemy_seen_only_in_sensor_range pins that ruled
behaviour. The disagreement is finding SL-C3-02 in docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md.

Every test_control_* is the positive control for the test above it: the same measurement under a perturbed input gives
a value that differs from the expectation, so a wrong expectation would fire.
"""
import math

import pytest

from conftest import OMFeature

RAIDER, VANGUARD, SUPPLY = 0, 2, 6
PLAYER, ENEMY = 0, 1
COHORT_COUNT = 4          # ALG-62 TARGETING_COHORT_COUNT
FLEE_DIST = 200.0         # ALG-62 _RETURN_FIRE_FLEE_DIST
VANGUARD_RANGE = 300.0    # roster, S-082
VANGUARD_SENSOR = 700.0


def _world(lib):
    w = lib.om_world_new(1, 1)
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _spawn(lib, w, utype, faction, x, y=0.0, layer=0):
    uid = lib.om_unit_spawn(w, utype, faction, x, y, layer)
    assert uid
    return uid


def _steps(lib, w, n):
    for _ in range(n):
        lib.om_world_step(w)


def test_ALG_62_a_unit_acquires_only_on_its_cohort_tick(lib):
    """ALG-62: acquisition happens on the cohort tick, `uid mod 4 == tick mod 4` (uid = id - 1, tick = step count)."""
    w = _world(lib)
    attackers = [_spawn(lib, w, VANGUARD, PLAYER, k * 5000.0) for k in range(4)]  # ids 1..4
    victims = [_spawn(lib, w, SUPPLY, ENEMY, k * 5000.0 + 100.0) for k in range(4)]
    assert attackers == [1, 2, 3, 4]
    first = {}
    for step in range(1, 9):
        lib.om_world_step(w)
        for a, v in zip(attackers, victims):
            if a not in first and lib.om_unit_get_target(w, a) == v:
                first[a] = step
    for a in attackers:
        uid = a - 1
        assert first[a] % COHORT_COUNT == uid % COHORT_COUNT, f"id {a} acquired at tick {first[a]}"
        assert first[a] <= COHORT_COUNT  # and no later than one full cohort cycle


def test_control_ALG_62_cohort_ticks_differ_between_units_so_the_check_discriminates(lib):
    w = _world(lib)
    attackers = [_spawn(lib, w, VANGUARD, PLAYER, k * 5000.0) for k in range(4)]
    for k in range(4):
        _spawn(lib, w, SUPPLY, ENEMY, k * 5000.0 + 100.0)
    first = {}
    for step in range(1, 9):
        lib.om_world_step(w)
        for a in attackers:
            if a not in first and lib.om_unit_get_target(w, a) != 0:
                first[a] = step
    assert len(set(first.values())) == 4  # four different cohort ticks: a single shared tick would have failed above
    assert first[1] != first[2]


def test_ALG_62_acquires_the_nearest_same_layer_enemy_within_attack_range_and_keeps_it(lib):
    """ALG-62: nearest same-layer enemy within attack range; a target alive and in range is kept."""
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    far = _spawn(lib, w, SUPPLY, ENEMY, 250.0)
    near = _spawn(lib, w, SUPPLY, ENEMY, 100.0)
    nearest_other_layer = _spawn(lib, w, SUPPLY, ENEMY, 50.0, 0.0, layer=1)
    beyond_range = _spawn(lib, w, SUPPLY, ENEMY, VANGUARD_RANGE + 1.0)
    _steps(lib, w, COHORT_COUNT)
    assert lib.om_unit_get_target(w, a) == near  # not the other-layer one at 50, not the one at 250
    nearer = _spawn(lib, w, SUPPLY, ENEMY, 20.0)
    _steps(lib, w, 2 * COHORT_COUNT)
    assert lib.om_unit_get_target(w, a) == near  # kept: alive and within range though `nearer` arrived
    assert len({near, far, nearest_other_layer, beyond_range, nearer}) == 5  # distinct fixture ids


def test_control_ALG_62_with_the_near_one_removed_the_far_one_is_taken(lib):
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    far = _spawn(lib, w, SUPPLY, ENEMY, 250.0)
    _spawn(lib, w, SUPPLY, ENEMY, 50.0, 0.0, layer=1)
    _steps(lib, w, COHORT_COUNT)
    assert lib.om_unit_get_target(w, a) == far


def test_ALG_62_a_plain_move_skips_targeting(lib):
    """ALG-62: units under a plain move skip targeting."""
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    _spawn(lib, w, SUPPLY, ENEMY, 100.0)
    lib.om_command_move(w, a, -3000.0, 0.0)
    _steps(lib, w, 2 * COHORT_COUNT)
    assert lib.om_unit_get_target(w, a) == 0


def test_control_ALG_62_the_same_unit_without_the_move_order_does_acquire(lib):
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    _spawn(lib, w, SUPPLY, ENEMY, 100.0)
    _steps(lib, w, 2 * COHORT_COUNT)
    assert lib.om_unit_get_target(w, a) != 0


def test_ALG_62_attack_move_does_not_walk_toward_an_enemy_seen_only_in_sensor_range(lib):
    """ALG-62 sensor clause as ruled by R-087-04 / A199: an attack-moving unit with an enemy in sensor range but beyond
    attack range keeps marching its own route and takes no target. (ALG-62's text says it would acquire and walk
    toward the enemy; see SL-C3-02.)"""
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    _spawn(lib, w, SUPPLY, ENEMY, 500.0)  # 300 < 500 < 700: in sensor, out of attack range
    assert 300.0 < 500.0 < VANGUARD_SENSOR
    lib.om_command_attack_move(w, [a], 1, -3000.0, 0.0)
    _steps(lib, w, 16)
    assert lib.om_unit_get_target(w, a) == 0
    x, y = lib.om_unit_get_pos(w, a)
    assert x == pytest.approx(-16 * lib.om_unit_profile_speed(w, VANGUARD) / 20.0)  # marched straight away from it


def test_control_ALG_62_an_enemy_inside_attack_range_does_stop_the_march(lib):
    w = _world(lib)
    a = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    e = _spawn(lib, w, SUPPLY, ENEMY, 200.0)
    lib.om_command_attack_move(w, [a], 1, -3000.0, 0.0)
    _steps(lib, w, 16)
    assert lib.om_unit_get_target(w, a) == e


@pytest.fixture
def _victim_world(lib):
    """Vanguard victim with id 2 (id 1 is a far friendly); one idle step first so the next step is not the victim's
    cohort tick, so a target it holds afterwards came from return fire and not from ordinary acquisition."""
    w = _world(lib)
    _spawn(lib, w, SUPPLY, PLAYER, -9000.0)
    _steps(lib, w, 1)
    victim = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    assert victim == 2
    assert (lib.om_tactical_tick(w) + 1) % COHORT_COUNT != lib.om_unit_targeting_cohort(w, victim)
    return w, victim


def test_ALG_62_an_idle_unit_with_no_target_that_takes_damage_targets_the_attacker(lib, _victim_world):
    """ALG-62 return fire: an idle unit with no target and no order that takes damage targets the attacker."""
    w, victim = _victim_world
    _spawn(lib, w, SUPPLY, ENEMY, 100.0)  # nearer enemy that did not hit it
    attacker = _spawn(lib, w, SUPPLY, ENEMY, 280.0)
    lib.om_unit_deal_damage(w, attacker, victim, 10.0)
    lib.om_world_step(w)
    assert lib.om_unit_get_target(w, victim) == attacker


def test_control_ALG_62_without_the_hit_the_victim_takes_no_target_off_its_cohort_tick(lib, _victim_world):
    w, victim = _victim_world
    _spawn(lib, w, SUPPLY, ENEMY, 100.0)
    _spawn(lib, w, SUPPLY, ENEMY, 280.0)
    lib.om_world_step(w)
    assert lib.om_unit_get_target(w, victim) == 0


def test_ALG_62_a_unit_that_cannot_return_fire_flinches_200_wu_away_from_the_attacker(lib):
    """ALG-62 flinch: a unit that cannot return fire (its attacker is on a layer it cannot reach) moves 200 wu away
    from the attacker."""
    w = _world(lib)
    ux, uy = 300.0, 400.0
    unit = _spawn(lib, w, RAIDER, PLAYER, ux, uy)
    attacker = _spawn(lib, w, SUPPLY, ENEMY, ux + 30.0, uy + 40.0, layer=3)  # 50 wu away, direction (0.6, 0.8)
    lib.om_unit_deal_damage(w, attacker, unit, 20.0)
    _steps(lib, w, 40)  # Raider 150 wu/s = 7.5 wu/tick: 27 ticks to cover 200
    x, y = lib.om_unit_get_pos(w, unit)
    assert math.hypot(x - ux, y - uy) == pytest.approx(FLEE_DIST)
    assert (x - ux) / FLEE_DIST == pytest.approx(-0.6)  # directly away from the attacker
    assert (y - uy) / FLEE_DIST == pytest.approx(-0.8)


def test_control_ALG_62_a_unit_that_can_return_fire_does_not_flee(lib):
    w = _world(lib)
    ux, uy = 300.0, 400.0
    unit = _spawn(lib, w, RAIDER, PLAYER, ux, uy)
    attacker = _spawn(lib, w, SUPPLY, ENEMY, ux + 30.0, uy + 40.0, layer=0)
    lib.om_unit_deal_damage(w, attacker, unit, 20.0)
    _steps(lib, w, 40)
    x, y = lib.om_unit_get_pos(w, unit)
    assert math.hypot(x - ux, y - uy) != pytest.approx(FLEE_DIST)
    assert lib.om_unit_get_target(w, unit) == attacker
