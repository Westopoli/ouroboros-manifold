"""PP-unit: two bugs against rules already ruled, fixed under their owners with a test first
(plan Phase A: "G04 (Intercept never expires, R-086-02); G15 (a second Warden must add 0.05, Q-084-01;
the C gives 0.09). ... not asked again"). Both are red against today's C.

G04 / R-086-02: "Given an Interceptor with Intercept ready and an enemy Strike unit within 350 wu on
its layer, When the check runs, Then it triggers automatically: speed x 1.8 and damage x 1.5 for the
first engagement, then cooldown 600 ticks (30 s); the player never activates it." Today the buff is
set on and nothing in the tick ever ends it or starts the cooldown (audit G04). The Python's buff
lasts one tick; the bible's is "the first engagement". The tests below hold on either reading: they
assert only that the buff is gone one tick after the engagement has ended (the Strike unit dead), that
the 600 tick cooldown then runs, and that it blocks a second trigger.

G15 / R-083-03, Q-084-01: "a second Warden in range adds 0.05 reduction, not 0.10, and healing stacks
per Warden": one Warden 0.10, two 0.15. Today the reduction is 1 - 0.9^n = 0.19 for two.
"""
import pytest

from test_PP_unit_support import INTERCEPTOR, RAIDER, VANGUARD, WARDEN, hp, kill, spawn, step

INTERCEPT_COOLDOWN_TICKS = 600  # R-086-02


def _interceptor_with_strike_unit(lib, w, strike_x=300.0):
    i = spawn(lib, w, INTERCEPTOR, 0, 0.0, 0.0)
    r = spawn(lib, w, RAIDER, 1, strike_x, 0.0)      # Raider is a Strike unit; 300 wu is inside 350, outside its own range 200
    return i, r


def test_control_R_086_02_intercept_triggers_on_a_strike_unit_inside_350(lib, world_factory):
    """Positive control for the G04 tests (green today): the trigger itself works. A Strike unit at
    300 wu turns the buff on (speed 130 x 1.8 = 234, damage x 1.5); one at 400 wu does not."""
    w = world_factory(n_regions=1)
    i, _ = _interceptor_with_strike_unit(lib, w, 300.0)
    far_i = spawn(lib, w, INTERCEPTOR, 0, 0.0, 5000.0)
    spawn(lib, w, RAIDER, 1, 400.0, 5000.0)

    step(lib, w)

    assert lib.om_unit_effective_speed(w, i) == pytest.approx(130.0 * 1.8, abs=1e-9)
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.5, abs=1e-9)
    assert lib.om_unit_effective_speed(w, far_i) == pytest.approx(130.0, abs=1e-9)
    assert lib.om_unit_output_multiplier(w, far_i) == pytest.approx(1.0, abs=1e-9)


def test_R_086_02_intercept_ends_when_the_engagement_ends(lib, world_factory):
    """R-086-02: the buff is for the first engagement. Triggered, then the Strike unit dies: one
    tick later the Interceptor is back to its own speed (130) and damage (x 1.0) and its ability is
    not active. Fails today: the buff stays on for the rest of the fight."""
    w = world_factory(n_regions=1)
    i, r = _interceptor_with_strike_unit(lib, w)
    step(lib, w, 3)
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.5, abs=1e-9), "fixture: should be triggered"
    kill(lib, w, r)

    step(lib, w)

    assert lib.om_unit_effective_speed(w, i) == pytest.approx(130.0, abs=1e-9)
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.0, abs=1e-9)
    assert lib.om_unit_ability_active(w, i) == 0


def test_R_086_02_cooldown_of_600_ticks_follows_the_engagement(lib, world_factory):
    """R-086-02: "then cooldown 600 ticks". After the buff has ended the ability is on cooldown, a
    positive number of ticks not over 600 (om_unit_ability_cooldown is in ticks). Fails today: it is
    never started (reads 0.0 with the buff still on)."""
    w = world_factory(n_regions=1)
    i, r = _interceptor_with_strike_unit(lib, w)
    step(lib, w, 3)
    kill(lib, w, r)
    step(lib, w)

    cd = lib.om_unit_ability_cooldown(w, i)
    assert 0.0 < cd <= INTERCEPT_COOLDOWN_TICKS, f"cooldown after the engagement is {cd}"


def test_R_086_02_cooldown_blocks_a_second_trigger_until_it_runs_out(lib, world_factory):
    """While the cooldown runs, a new Strike unit inside 350 wu does not trigger the buff again;
    clearing the cooldown by hand (om_unit_set_ability_cooldown 0) is the only thing that lets it
    (so the cooldown, not some other condition, is what held it back). Fails today at the first
    assertion: the buff never ended, so it reads active."""
    w = world_factory(n_regions=1)
    i, r = _interceptor_with_strike_unit(lib, w)
    step(lib, w, 3)
    kill(lib, w, r)
    step(lib, w)
    cd = lib.om_unit_ability_cooldown(w, i)
    assert cd > 10.0, "fixture: cooldown should be running"

    spawn(lib, w, RAIDER, 1, 300.0, 0.0)
    step(lib, w, 10)
    assert lib.om_unit_ability_active(w, i) == 0, "second trigger during the cooldown"
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.0, abs=1e-9)

    lib.om_unit_set_ability_cooldown(w, i, 0.0)
    step(lib, w)
    assert lib.om_unit_output_multiplier(w, i) == pytest.approx(1.5, abs=1e-9), (
        "with the cooldown cleared the Strike unit inside 350 should trigger it again")


# ---- G15: the Warden aura ----

def _line_with_wardens(lib, w, n_wardens):
    v = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    offsets = [(50.0, 0.0), (0.0, 50.0)]
    for k in range(n_wardens):
        spawn(lib, w, WARDEN, 0, *offsets[k])
    return v


def test_control_R_083_03_no_warden_no_reduction_one_warden_is_ten_percent(lib, world_factory):
    """Positive control for the aura tests (green today): none in range gives 0, one gives 0.10, so
    the getter reads the aura and the difference between one and two is the thing under test."""
    w = world_factory(n_regions=1)
    v = _line_with_wardens(lib, w, 0)
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.0, abs=1e-9)
    spawn(lib, w, WARDEN, 0, 50.0, 0.0)
    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.10, abs=1e-9)


def test_R_083_03_a_second_warden_adds_nothing(lib, world_factory):
    """R-083-03 / Q-084-01 (closed 2026-10-20, "no stacking"): a second Warden within 300 wu adds nothing: two Wardens give 0.10, as one does.
    Test-defect, F4 engine rule fixes 2026-11-08: was test_R_083_03_a_second_warden_adds_005_not_009, pinned 0.15 for two Wardens; cause: the
    bible says Wardens do not stack, the diminishing 0.10 + 0.05 pin was stale."""
    w = world_factory(n_regions=1)
    v = _line_with_wardens(lib, w, 2)

    assert lib.om_unit_damage_reduction(w, v) == pytest.approx(0.10, abs=1e-9)


def test_R_083_03_healing_does_not_stack_per_warden(lib, world_factory):
    """R-083-03: the aura regains 0.075 HP per tick and a second Warden adds nothing. A damaged Vanguard in reach of two Wardens regains 0.075 hp
    in one tick, as with one.
    Test-defect, F4 engine rule fixes 2026-11-08: was test_R_083_03_healing_stacks_per_warden, pinned 2 * 0.075; cause: R-083-03 and Q-084-01
    closed say no stacking."""
    w = world_factory(n_regions=1)
    v = _line_with_wardens(lib, w, 2)
    lib.om_unit_set_hp(w, v, 400.0)   # 80 percent: not 'badly damaged', so no Rally (R-086-08) muddies the reading

    step(lib, w)

    assert hp(lib, w, v) == pytest.approx(400.0 + 0.075, abs=1e-9)
