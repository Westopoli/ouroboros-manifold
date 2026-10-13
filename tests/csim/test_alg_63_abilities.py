"""ALG-63 Abilities (docs/bible/algorithms.md; R-086-01..08, S-086) -- the six ability numbers and the Warden aura.

The expected values below are typed from the ALG-63 text, never read from csrc/om_constants.h:
Surge 60 ticks, speed x2.5, damage x2.0, cooldown 1500. Intercept: enemy Strike within 350, speed x1.8,
damage x1.5, cooldown 600. Brace: 40-tick windup immobile without bonus, then reduction 0.50 and damage x1.3,
cooldown 700 from activation, toggling off repeats the windup. Rally: instant 112 HP to every friendly within 400,
capped at max HP, cooldown 1500. Barrage: 30-tick telegraph, base x3.0 within radius 100 (ALG-61 cap 4 x the hit
base), cooldown 1800. Fortify: 400 ticks, reduction 0.20 within 350, Bastion speed x0.4, cooldown 1400. Warden
aura: friendlies within 300 regain 0.075 HP per tick. "Cooldowns tick down every tick; activation on cooldown is
rejected." Where the text does not say when a cooldown starts (all but Brace) both readings are accepted and the
ambiguity is SL-C3-01 (docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md).

Positive control per mechanism (test_control_*): the same measurement on a unit that never activated, or on a
perturbed input, gives a value different from the expectation, so a wrong expectation would fire the assertion.
"""
import ctypes

import pytest

from conftest import OMFeature

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = 0, 1, 2, 3, 4, 5
PLAYER, ENEMY = 0, 1
TICK_RATE = 20  # OM_TACTICAL_TICK_RATE: tactical ticks per second (ALG-60 timing note)


def _world(lib):
    w = lib.om_world_new(1, 1)
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _spawn(lib, w, utype, faction, x, y=0.0):
    uid = lib.om_unit_spawn(w, utype, faction, x, y, 0)
    assert uid
    return uid


def _activate(lib, w, uid, x=0.0, y=0.0):
    ids = (ctypes.c_uint32 * 1)(uid)
    return lib.om_command_activate_ability(w, ids, 1, x, y)


def _x(lib, w, uid):
    return lib.om_unit_get_pos(w, uid)[0]  # conftest wraps the out-pair as (x, y)


def _steps(lib, w, n):
    for _ in range(n):
        lib.om_world_step(w)


# ---- Surge ----------------------------------------------------------------------------------------------

def test_ALG_63_surge_speed_2_5_for_60_ticks_then_cooldown_1500(lib):
    """ALG-63 Surge: duration 60 ticks, speed x2.5, damage x2.0, cooldown 1500."""
    w = _world(lib)
    r = _spawn(lib, w, RAIDER, PLAYER, 0.0)
    base = lib.om_unit_profile_speed(w, RAIDER)
    assert _activate(lib, w, r) == 0
    assert lib.om_unit_effective_speed(w, r) == pytest.approx(base * 2.5)
    assert lib.om_unit_output_multiplier(w, r) == pytest.approx(2.0)
    lib.om_command_direct_move(w, r, 100000.0, 0.0)
    per_tick = base / TICK_RATE
    x0 = _x(lib, w, r)
    _steps(lib, w, 100)
    # 60 ticks at x2.5, then 40 at x1: the duration is exactly 60 ticks.
    assert _x(lib, w, r) - x0 == pytest.approx(60 * per_tick * 2.5 + 40 * per_tick)
    assert lib.om_unit_ability_active(w, r) == 0
    # ALG-63 says only "cooldown 1500" (Brace alone says "from activation"): counted from the end of the 60 ticks it is
    # 1500 - 39 after these 100 steps, counted from activation 1500 - 100. Either reading is accepted (SL-C3-01).
    assert lib.om_unit_ability_cooldown(w, r) in (pytest.approx(1500.0 - 39), pytest.approx(1500.0 - 100))
    assert _activate(lib, w, r) != 0  # activation on cooldown is rejected


def test_control_ALG_63_surge_a_unit_that_never_surged_moves_at_the_plain_pace(lib):
    w = _world(lib)
    r = _spawn(lib, w, RAIDER, PLAYER, 0.0)
    base = lib.om_unit_profile_speed(w, RAIDER)
    lib.om_command_direct_move(w, r, 100000.0, 0.0)
    _steps(lib, w, 100)
    assert _x(lib, w, r) == pytest.approx(100 * base / TICK_RATE)
    assert _x(lib, w, r) != pytest.approx(60 * base / TICK_RATE * 2.5 + 40 * base / TICK_RATE)


# ---- Intercept ------------------------------------------------------------------------------------------

def test_ALG_63_intercept_fires_on_enemy_strike_within_350_speed_1_8_damage_1_5_cooldown_600(lib):
    """ALG-63 Intercept: passive; cooldown 0 and an enemy Strike within 350 on the same layer -> speed x1.8, damage x1.5, cooldown 600."""
    w = _world(lib)
    i = _spawn(lib, w, INTERCEPTOR, PLAYER, 0.0)
    e = _spawn(lib, w, RAIDER, ENEMY, 340.0)  # Raider is a Strike unit, inside 350
    base = lib.om_unit_profile_speed(w, INTERCEPTOR)
    assert lib.om_unit_ability_active(w, i) == 0
    lib.om_world_step(w)
    assert lib.om_unit_ability_active(w, i) == 1
    assert lib.om_unit_effective_speed(w, i) == pytest.approx(base * 1.8)
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.5)
    lib.om_unit_set_hp(w, e, 0.0)  # the engagement ends
    lib.om_world_step(w)
    assert lib.om_unit_ability_active(w, i) == 0
    assert lib.om_unit_ability_cooldown(w, i) == pytest.approx(600.0)


@pytest.mark.parametrize("enemy_type,enemy_x", [(RAIDER, 360.0), (VANGUARD, 340.0)])
def test_control_ALG_63_intercept_stays_off_for_a_strike_beyond_350_or_a_non_strike_enemy(lib, enemy_type, enemy_x):
    w = _world(lib)
    i = _spawn(lib, w, INTERCEPTOR, PLAYER, 0.0)
    _spawn(lib, w, enemy_type, ENEMY, enemy_x)
    lib.om_world_step(w)
    assert lib.om_unit_ability_active(w, i) == 0
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.0)


# ---- Brace ----------------------------------------------------------------------------------------------

def test_ALG_63_brace_40_tick_windup_then_reduction_0_50_damage_1_3_cooldown_700_from_activation(lib):
    """ALG-63 Brace: windup 40 ticks immobile without bonus, then active with reduction 0.50 and damage x1.3; cooldown 700 from activation."""
    w = _world(lib)
    v = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    assert _activate(lib, w, v) == 0
    assert lib.om_unit_ability_cooldown(w, v) == pytest.approx(700.0)  # from activation
    assert lib.om_unit_effective_speed(w, v) == 0.0  # immobile in the windup
    assert lib.om_unit_output_multiplier(w, v) == pytest.approx(1.0)  # no bonus in the windup
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.0)
    _steps(lib, w, 40)
    assert lib.om_unit_output_multiplier(w, v) == pytest.approx(1.0)  # the 40th windup tick is still no bonus
    _steps(lib, w, 1)
    assert lib.om_unit_output_multiplier(w, v) == pytest.approx(1.3)
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.50)


def test_ALG_63_brace_toggling_off_repeats_the_windup(lib):
    """ALG-63 Brace: toggling off repeats the windup (40 ticks), after which the unit is plain again."""
    w = _world(lib)
    v = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    _activate(lib, w, v)
    _steps(lib, w, 41)
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.50)
    assert _activate(lib, w, v) == 0  # toggle off
    _steps(lib, w, 40)
    assert lib.om_unit_ability_active(w, v) == 1  # still winding down after 40 ticks
    _steps(lib, w, 1)
    assert lib.om_unit_ability_active(w, v) == 0
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.0)
    assert lib.om_unit_output_multiplier(w, v) == pytest.approx(1.0)
    assert lib.om_unit_effective_speed(w, v) == pytest.approx(lib.om_unit_profile_speed(w, VANGUARD))


def test_control_ALG_63_brace_an_unbraced_vanguard_has_no_reduction_and_no_bonus(lib):
    w = _world(lib)
    v = _spawn(lib, w, VANGUARD, PLAYER, 0.0)
    _steps(lib, w, 41)
    assert lib.om_unit_damage_reduction(w, v) != pytest.approx(0.50)
    assert lib.om_unit_output_multiplier(w, v) != pytest.approx(1.3)


# ---- Rally ----------------------------------------------------------------------------------------------

def test_ALG_63_rally_heals_112_to_every_friendly_within_400_capped_at_max_hp_cooldown_1500(lib):
    """ALG-63 Rally: instant 112 HP to every friendly within 400, capped at max HP; cooldown 1500."""
    w = _world(lib)
    wd = _spawn(lib, w, WARDEN, PLAYER, 0.0)
    near = _spawn(lib, w, RAIDER, PLAYER, 399.0)
    far = _spawn(lib, w, RAIDER, PLAYER, 401.0)
    foe = _spawn(lib, w, RAIDER, ENEMY, 100.0)
    nearly = _spawn(lib, w, RAIDER, PLAYER, 0.0, 100.0)
    max_hp = lib.om_unit_profile_max_hp(w, RAIDER)
    for u in (near, far, foe):
        lib.om_unit_set_hp(w, u, 100.0)
    lib.om_unit_set_hp(w, nearly, max_hp - 50.0)
    lib.om_unit_set_ability_cooldown(w, wd, 0.0)
    assert _activate(lib, w, wd) == 0
    assert lib.om_unit_hp(w, near) == pytest.approx(100.0 + 112.0)
    assert lib.om_unit_hp(w, far) == pytest.approx(100.0)  # outside 400
    assert lib.om_unit_hp(w, foe) == pytest.approx(100.0)  # an enemy is not a friendly
    assert lib.om_unit_hp(w, nearly) == pytest.approx(max_hp)  # capped
    assert lib.om_unit_ability_cooldown(w, wd) == pytest.approx(1500.0)
    assert _activate(lib, w, wd) != 0  # on cooldown


def test_control_ALG_63_rally_a_warden_that_never_rallied_heals_nobody(lib):
    w = _world(lib)
    _spawn(lib, w, WARDEN, PLAYER, 0.0)
    near = _spawn(lib, w, RAIDER, PLAYER, 100.0)
    lib.om_unit_set_hp(w, near, 100.0)
    assert lib.om_unit_hp(w, near) != pytest.approx(212.0)


# ---- Barrage --------------------------------------------------------------------------------------------

def test_ALG_63_barrage_30_tick_telegraph_then_3x_base_radius_100_capped_cooldown_1800(lib):
    """ALG-63 Barrage: 30-tick telegraph, then ALG-61 at the target with base x3.0 within radius 100; cooldown 1800."""
    w = _world(lib)
    b = _spawn(lib, w, BOMBARD, PLAYER, 0.0)
    t1 = _spawn(lib, w, VANGUARD, ENEMY, 1000.0)
    t2 = _spawn(lib, w, VANGUARD, ENEMY, 1050.0)
    t3 = _spawn(lib, w, VANGUARD, ENEMY, 1099.0)
    t4 = _spawn(lib, w, VANGUARD, ENEMY, 1101.0)  # 101 from the target: outside radius 100
    hp0 = lib.om_unit_profile_max_hp(w, VANGUARD)
    base = lib.om_unit_profile_base_damage(w, BOMBARD)
    assert _activate(lib, w, b, 1000.0, 0.0) == 0
    _steps(lib, w, 30)
    assert all(lib.om_unit_hp(w, t) == pytest.approx(hp0) for t in (t1, t2, t3, t4))  # telegraph: nothing yet
    _steps(lib, w, 1)
    hit = base * 3.0 * 1.5  # Siege vs Line category multiplier 1.5 (ALG-60)
    cap = base * 3.0 * 4.0  # ALG-61 AOE_DAMAGE_CAP_MULTIPLIER on the hit base
    assert lib.om_unit_hp(w, t1) == pytest.approx(hp0 - hit)
    assert lib.om_unit_hp(w, t2) == pytest.approx(hp0 - hit)
    assert lib.om_unit_hp(w, t3) == pytest.approx(hp0 - (cap - 2 * hit))  # the last hit is truncated to the cap
    assert lib.om_unit_hp(w, t4) == pytest.approx(hp0)
    # cooldown 1800 counted from the resolution (1800 now) or from the cast (1800 - 31 after these 31 steps): SL-C3-01
    assert lib.om_unit_ability_cooldown(w, b) in (pytest.approx(1800.0), pytest.approx(1800.0 - 31))


def test_control_ALG_63_barrage_without_a_cast_nothing_is_hurt(lib):
    w = _world(lib)
    _spawn(lib, w, BOMBARD, PLAYER, 0.0)
    t1 = _spawn(lib, w, VANGUARD, ENEMY, 5000.0)  # out of the Bombard's own range: no auto barrage either
    _steps(lib, w, 40)
    assert lib.om_unit_hp(w, t1) == pytest.approx(lib.om_unit_profile_max_hp(w, VANGUARD))


# ---- Fortify --------------------------------------------------------------------------------------------

def test_ALG_63_fortify_400_ticks_reduction_0_20_within_350_bastion_speed_0_4_cooldown_1400(lib):
    """ALG-63 Fortify: 400 ticks, reduction 0.20 within 350, Bastion speed x0.4; cooldown 1400."""
    w = _world(lib)
    b = _spawn(lib, w, BASTION, PLAYER, 0.0)
    inside = _spawn(lib, w, RAIDER, PLAYER, 349.0)
    outside = _spawn(lib, w, RAIDER, PLAYER, 351.0)
    base = lib.om_unit_profile_speed(w, BASTION)
    assert _activate(lib, w, b) == 0
    assert lib.om_unit_effective_speed(w, b) == pytest.approx(base * 0.4)
    assert lib.om_unit_damage_reduction(w, b) == pytest.approx(0.20)
    assert lib.om_unit_damage_reduction(w, inside) == pytest.approx(0.20)
    assert lib.om_unit_damage_reduction(w, outside) == pytest.approx(0.0)
    _steps(lib, w, 400)
    assert lib.om_unit_ability_active(w, b) == 1  # still up on the 400th tick
    _steps(lib, w, 1)
    assert lib.om_unit_ability_active(w, b) == 0
    assert lib.om_unit_effective_speed(w, b) == pytest.approx(base)
    assert lib.om_unit_damage_reduction(w, inside) == pytest.approx(0.0)
    # cooldown 1400 counted from activation (1400 - 401 now) or from the end of the 400 ticks (1400 now): SL-C3-01
    assert lib.om_unit_ability_cooldown(w, b) in (pytest.approx(1400.0 - 401), pytest.approx(1400.0))


def test_control_ALG_63_fortify_a_bastion_that_never_fortified_has_no_reduction(lib):
    w = _world(lib)
    b = _spawn(lib, w, BASTION, PLAYER, 0.0)
    assert lib.om_unit_damage_reduction(w, b) != pytest.approx(0.20)
    assert lib.om_unit_effective_speed(w, b) != pytest.approx(lib.om_unit_profile_speed(w, BASTION) * 0.4)


# ---- Warden aura ----------------------------------------------------------------------------------------

def test_ALG_63_warden_aura_friendlies_within_300_regain_0_075_hp_per_tick(lib):
    """ALG-63 Warden aura (passive): friendlies within 300 regain WARDEN_AURA_REPAIR_RATE = 0.075 HP per tick."""
    w = _world(lib)
    wd = _spawn(lib, w, WARDEN, PLAYER, 0.0)
    inside = _spawn(lib, w, RAIDER, PLAYER, 299.0)
    outside = _spawn(lib, w, RAIDER, PLAYER, 301.0)
    lib.om_unit_set_ability_cooldown(w, wd, 100000.0)  # keep Rally from auto-firing and muddying the HP
    lib.om_unit_set_hp(w, inside, 100.0)
    lib.om_unit_set_hp(w, outside, 100.0)
    _steps(lib, w, 40)
    assert lib.om_unit_hp(w, inside) == pytest.approx(100.0 + 40 * 0.075)
    assert lib.om_unit_hp(w, outside) == pytest.approx(100.0)


def test_control_ALG_63_warden_aura_no_warden_no_regain(lib):
    w = _world(lib)
    u = _spawn(lib, w, RAIDER, PLAYER, 0.0)
    lib.om_unit_set_hp(w, u, 100.0)
    _steps(lib, w, 40)
    assert lib.om_unit_hp(w, u) != pytest.approx(100.0 + 40 * 0.075)
