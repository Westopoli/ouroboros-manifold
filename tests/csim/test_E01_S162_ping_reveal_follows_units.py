"""E-01 S-162, rule change of Westley 2026-10-05 (R-162-01, R-162-03, R-162-05): the ping's reveal follows the units
it caught, and the pinged side is told nothing by default.

R-162-01: every enemy unit on the pinged layer inside the ping's radius AT THE CAST becomes visible to the caster's
side and stays visible for the reveal time wherever it moves; the reveal is the set of units caught, not a disc that
lives on. Default reveal 5 s = 100 tactical ticks (OM_TACTICAL_TICK_RATE 20). R-162-03: no alert by default; it is kept
behind OM_TP_PING_ALERT (0 off, the default; 1 on). R-162-05: after the reveal, with no other detection, the caught
units are hidden again. R-162-02: cooldown per casting unit, unchanged.

Fixture is test_PP_C_g67_ping.py's: caster engine layer 0 at the origin, enemies on engine layer 4 (bible layer 5),
four layers away so passive sight never shows them (R-005-05). Units are moved with om_unit_teleport (`place`), the
way the existing PP tests move units; enemies standing still are not moved by anything.

Red today (csrc/fog.c reveals whatever is inside a fixed disc while the disc lives, reveal default 40, alert always
on): tests 2, 3, 4, 6, 7, 8. Green today: 1, 5, 9 (guards)."""
import math

import pytest

from test_PP_C_g67_support import (PING_OK, PING_REASON_COOLDOWN, RAIDER, VANGUARD, alert, alert_count, place,
                                   set_param, set_ping_alert, side_sees, spawn, step)
from conftest import OMTacParam

HIGH = 4
COOLDOWN = 400
DEFAULT_REVEAL = 100   # 5 s at 20 ticks per second (R-162-01)
CAST_X = 1500.0        # disc centre (CAST_X, 0), radius 500, 1,500 from the caster (reach 2,000)


def _scene(lib, world_factory):
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    inside = spawn(lib, w, VANGUARD, 1, CAST_X + 100.0, 0.0, HIGH)
    return w, caster, inside


def _cast(lib, w, caster):
    assert lib.om_command_ping(w, caster, HIGH, CAST_X, 0.0) == PING_OK


def _steps_visible(lib, w, unit, n):
    return [i for i in range(1, n + 1) if (step(lib, w), side_sees(lib, w, 0, unit))[1]]


def test_R_162_01_a_unit_inside_the_radius_at_the_cast_is_visible_to_the_casters_side(lib, world_factory):
    """Test 1. Control inside: hidden before the cast."""
    w, caster, inside = _scene(lib, world_factory)
    assert side_sees(lib, w, 0, inside) == 0, "control: no passive sight across four layers"
    _cast(lib, w, caster)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1


def test_R_162_01_a_caught_unit_stays_visible_wherever_it_moves(lib, world_factory):
    """Test 2: the unit caught at (1600, 0) is moved to (5000, 4000), far outside the disc, partway through the reveal;
    it is still visible after every step of the reveal. Red today: outside the disc it is not revealed."""
    w, caster, inside = _scene(lib, world_factory)
    _cast(lib, w, caster)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1, "control: caught at the cast"
    place(lib, w, inside, 5000.0, 4000.0)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1, "the reveal did not follow the unit out of the disc"
    place(lib, w, inside, 9000.0, 9000.0)
    assert _steps_visible(lib, w, inside, 50) == list(range(1, 51))


def test_R_162_01_an_enemy_that_walks_into_the_disc_later_is_not_revealed(lib, world_factory):
    """Test 3: a second enemy 900 wu from the ping point at the cast (outside the 500 radius, control: not seen) walks
    into the old disc during the reveal; this ping never reveals it. Red today: the disc catches it."""
    w, caster, inside = _scene(lib, world_factory)
    late = spawn(lib, w, VANGUARD, 1, CAST_X + 900.0, 0.0, HIGH)
    _cast(lib, w, caster)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1, "control: the unit caught at the cast is revealed"
    assert side_sees(lib, w, 0, late) == 0, "control: outside the disc at the cast"
    place(lib, w, late, CAST_X + 50.0, 0.0)
    assert _steps_visible(lib, w, late, 30) == [], "a unit not caught at the cast was revealed by walking into the disc"


def test_R_162_05_after_the_reveal_time_the_caught_unit_is_hidden_again_wherever_it_is(lib, world_factory):
    """Test 4: reveal set to 10 ticks; the caught unit, moved out of the disc, is visible after steps 1 to 10 and hidden
    after step 11 (the existing PP tests' count: R-006-02). Red today: it is not visible outside the disc."""
    w, caster, inside = _scene(lib, world_factory)
    set_param(lib, w, "PING_REVEAL_TICKS", 10)
    _cast(lib, w, caster)
    place(lib, w, inside, 6000.0, -3000.0)
    assert _steps_visible(lib, w, inside, 30) == list(range(1, 11))


def test_R_162_05_with_the_default_reveal_a_moved_unit_is_visible_for_100_ticks_then_hidden(lib, world_factory):
    """Tests 4 and 6 together at default settings: visible after steps 1 to 100 and hidden from 101, moved out of the
    disc after the first step. Red today (40 ticks, fixed disc)."""
    w, caster, inside = _scene(lib, world_factory)
    _cast(lib, w, caster)
    step(lib, w, 1)
    place(lib, w, inside, 6000.0, -3000.0)
    seen = [1] + [i for i in range(2, DEFAULT_REVEAL + 21) if (step(lib, w), side_sees(lib, w, 0, inside))[1]]
    assert seen == list(range(1, DEFAULT_REVEAL + 1))


def test_R_162_01_a_unit_on_another_layer_inside_the_radius_is_not_revealed(lib, world_factory):
    """Test 5 (guard, passes today): an enemy on engine layer 3 inside the disc is not caught by a layer-4 ping, even if
    it later moves; control: the layer-4 enemy is."""
    w, caster, inside = _scene(lib, world_factory)
    other = spawn(lib, w, VANGUARD, 1, CAST_X, 100.0, 3)
    _cast(lib, w, caster)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1, "control"
    assert side_sees(lib, w, 0, other) == 0
    place(lib, w, other, CAST_X + 400.0, 0.0)
    assert _steps_visible(lib, w, other, 20) == []


def test_R_162_01_the_default_reveal_time_is_five_seconds_in_ticks(lib, world_factory):
    """Test 6: OM_TP_PING_REVEAL_TICKS reads 100 on a fresh world (5 s at 20 ticks per second). Red today: 40."""
    w, caster, inside = _scene(lib, world_factory)
    assert lib.om_tactical_get_param(w, OMTacParam.PING_REVEAL_TICKS) == DEFAULT_REVEAL


def test_R_162_03_by_default_a_ping_that_lands_on_enemy_units_writes_no_alert(lib, world_factory):
    """Test 7: default settings, a ping that catches an enemy (control: it is revealed, so the ping did land) leaves the
    pinged side with no alert. Red today: the alert is always written."""
    w, caster, inside = _scene(lib, world_factory)
    _cast(lib, w, caster)
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1, "control: the ping landed on the enemy"
    assert alert_count(lib, w, 1) == 0, "R-162-03: the pinged side is told nothing"


@pytest.mark.parametrize("theta", [10.0, 130.0, 250.0])
def test_R_162_03_with_the_alert_parameter_on_the_sector_contains_the_bearing_to_the_caster(lib, world_factory, theta):
    """Test 8: OM_TP_PING_ALERT 1 gives today's alert: one entry, its sector the 60-degree slice (0 to 5, counter-
    clockwise from +x) holding the bearing from the pinged unit to the caster. Red until the parameter exists."""
    w = world_factory(n_regions=1)
    set_ping_alert(lib, w, 1)
    ex, ey, r = 5000.0, 5000.0, 1500.0
    cx, cy = ex + r * math.cos(math.radians(theta)), ey + r * math.sin(math.radians(theta))
    caster = spawn(lib, w, RAIDER, 0, cx, cy, 0)
    spawn(lib, w, VANGUARD, 1, ex, ey, HIGH)
    assert alert_count(lib, w, 1) == 0, "control: none before the ping"
    assert lib.om_command_ping(w, caster, HIGH, ex, ey) == PING_OK
    assert alert_count(lib, w, 1) == 1
    rc, _, faction, sector = alert(lib, w, 1, 0)
    assert rc == 0 and faction == 1
    assert sector == int((math.degrees(math.atan2(cy - ey, cx - ex)) % 360.0) // 60.0)


def test_R_162_02_the_cooldown_is_per_casting_unit_and_unchanged(lib, world_factory):
    """Test 9 (guard, passes today): a second cast by the same unit inside the 400-tick cooldown is refused (reason 3);
    another unit casts at once; the first is accepted again after 400 ticks."""
    w, caster, inside = _scene(lib, world_factory)
    other = spawn(lib, w, RAIDER, 0, 0.0, 50.0, 0)
    _cast(lib, w, caster)
    assert lib.om_command_ping(w, caster, HIGH, CAST_X, 0.0) == PING_REASON_COOLDOWN
    assert lib.om_command_ping(w, other, HIGH, CAST_X, 50.0) == PING_OK
    step(lib, w, COOLDOWN)
    assert lib.om_command_ping(w, caster, HIGH, CAST_X, 0.0) == PING_OK
