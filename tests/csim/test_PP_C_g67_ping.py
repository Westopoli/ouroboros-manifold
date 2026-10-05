"""PP-fog Phase C, brief G7 "The targeted ping": cast, radius, reveal, cooldown, reach, refusals, the alert with its
60-degree sector, and the ping as a spotter for the side's long-range fire (E-01 S-162 R-162-01 to R-162-03 and
R-162-05, R-008-04; E-12 R-093-02; brief section 5 G7 and section 6; contract pp_contract.md rows 12 to 14, section 4
rows OM_TP_PING_*, section 6 for the refusal reasons; rulings A132 for the layer range, A133).

Numbers (brief section 6, engine defaults, all settings; reveal now 100 ticks, R-162-01, Westley 2026-10-05, and the alert tests below set OM_TP_PING_ALERT 1 because the alert is off by default, R-162-03; the units caught are now followed, see test_E01_S162_ping_reveal_follows_units.py): radius 500, reveal 40 ticks, cooldown 400 ticks per unit,
reach 2,000 from the caster. The brief's G7 test list is followed: 'a ping on layer 5 from a unit on layer 1 reveals
an enemy there for exactly the reveal ticks and then not; an enemy on another layer inside the disc is not revealed; a
second ping inside the cooldown is refused; a ping beyond reach is refused; the pinged side's alert sector contains the
true bearing, and a caster moved 30 degrees within the same slice gives the same sector; the casting side gets no
alert.' Layers are engine layers 0 to 4 (A132): bible layer 5 is engine layer 4, bible layer 1 is engine layer 0.

Reading the tests pin where the documents leave a choice (said again in the report):
- The reveal covers the 40 ticks after the cast: the revealed enemy is in the side's visible set after each of steps
  1 to 40 and not after step 41 (R-006-02: 'a pulse that started 2.0 seconds ago, when the next tick runs, ...
  leave'). Whether it is also visible between the cast and the first step is not asserted.
- The cooldown opens when 400 ticks have passed since the cast: refused after 399 steps, accepted after 400
  (R-006-03: 'before tick T plus 20.0 seconds (400 ticks)'). Ticks are tactical ticks (om_tactical_tick), the only
  clock that runs in a tactical fight.
- The alert's `tick` is om_tactical_tick at the cast.

Today's inert stubs (csrc/fog.c): om_command_ping returns 0 for everything and does nothing, om_ping_alert_count
returns 0, om_ping_alert_get returns 0 and writes nothing. So the accepted-ping tests fail on 'enemy not revealed'
(or no alert), and every refusal test fails on the return value (0, where the contract gives a reason 1 to 4).
Controls that pass today: the not-visible-before-the-ping checks, the refusal-free calls, and the no-ping Bombard."""
import math

import pytest

from test_PP_C_g67_support import (BOMBARD, PING_OK, PING_REASON_CASTER, PING_REASON_COOLDOWN, PING_REASON_LAYER,
                                   PING_REASON_REACH, RAIDER, SUPPLY, VANGUARD, alert, alert_count, layer_count,
                                   ping, set_param, set_ping_alert, side_sees, spawn, step)

REACH = 2000.0
RADIUS = 500.0
REVEAL = 100   # R-162-01 (Westley 2026-10-05): 5 s at 20 ticks per second; was 40
COOLDOWN = 400
HIGH = 4   # bible layer 5


def _scene(lib, world_factory, ping_x=1500.0):
    """Caster (faction 0 Raider, engine layer 0, sensor 800) at the origin; an enemy faction 1 Vanguard on engine
    layer 4 100 wu from the ping point (ping_x, 0). The caster is four layers away from the enemy, so passive sight
    (factor 0.0 beyond two layers, R-005-05) never shows it."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    enemy = spawn(lib, w, VANGUARD, 1, ping_x + 100.0, 0.0, HIGH)
    return w, caster, enemy


def _visible_steps(lib, w, faction, unit, n):
    """The steps (1-based) after which the faction's visible set holds `unit`, over n steps."""
    seen = []
    for i in range(1, n + 1):
        step(lib, w)
        if side_sees(lib, w, faction, unit):
            seen.append(i)
    return seen


# ---- reveal: for exactly the reveal ticks, then hidden again (R-162-05, R-006-01/02 analogue) ----

def test_R_162_05_a_ping_reveals_an_enemy_on_the_named_layer_for_exactly_the_reveal_ticks(lib, world_factory):
    """Brief G7 test 1 (R-162-01, R-162-05): a ping on layer 5 (engine 4) from a unit on layer 1 (engine 0) reveals an
    enemy there for exactly the reveal ticks and then not. Control inside (passes today): not visible before."""
    w, caster, enemy = _scene(lib, world_factory)
    assert side_sees(lib, w, 0, enemy) == 0, "control: no passive sight across four layers"
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    assert _visible_steps(lib, w, 0, enemy, REVEAL + 20) == list(range(1, REVEAL + 1))


def test_R_162_05_the_reveal_length_is_the_setting(lib, world_factory):
    """OM_TP_PING_REVEAL_TICKS is what sets the length: at 10 the enemy is in the set after steps 1 to 10 only."""
    w, caster, enemy = _scene(lib, world_factory)
    set_param(lib, w, "PING_REVEAL_TICKS", 10)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    assert _visible_steps(lib, w, 0, enemy, 30) == list(range(1, 11))


def test_R_162_05_the_ping_reveals_to_the_casters_side_not_to_the_other(lib, world_factory):
    """The enemy side does not see the caster's side's units because of the ping (it gets an alert, not a view)."""
    w, caster, enemy = _scene(lib, world_factory)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 1)
    assert side_sees(lib, w, 0, enemy) == 1
    assert side_sees(lib, w, 1, caster) == 0, "the pinged side learns a sector, not the caster's position"


def test_R_162_05_a_second_unit_of_the_side_shares_the_reveal(lib, world_factory):
    """Visible set is per side (R-089-02): the revealed enemy is in faction 0's set, whichever of its units cast."""
    w, caster, enemy = _scene(lib, world_factory)
    other = spawn(lib, w, RAIDER, 0, 0.0, 300.0, 0)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 1)
    assert side_sees(lib, w, 0, enemy) == 1
    assert side_sees(lib, w, 0, other) == 1  # own unit: always in its own side's set (control)


# ---- the named layer only (brief G7 test 2) ----

@pytest.mark.parametrize("pinged,other", [(HIGH, 3), (3, HIGH), (0, 2)])
def test_R_162_01_an_enemy_on_another_layer_inside_the_disc_is_not_revealed(lib, world_factory, pinged, other):
    """Brief G7 test 2: an enemy on another layer inside the disc is not revealed. Two enemies share the disc, one on
    the pinged layer (control: it is revealed) and one on another layer (it is not). The caster is engine layer 0, so
    for pinged 0 the caster is on the named layer too and its 500-wu-radius disc is placed 1,500 away."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    on = spawn(lib, w, VANGUARD, 1, 1500.0, 100.0, pinged)
    off = spawn(lib, w, VANGUARD, 1, 1500.0, -100.0, other)
    assert ping(lib, w, caster, pinged, 1500.0, 0.0) == PING_OK
    step(lib, w, 1)
    assert side_sees(lib, w, 0, on) == 1, "control: the enemy on the named layer is revealed"
    assert side_sees(lib, w, 0, off) == 0, "an enemy on another layer is not"


# ---- radius (brief section 6: 500) ----

def test_R_162_01_the_disc_radius_is_500_and_measured_from_the_ping_point(lib, world_factory):
    """Every enemy unit on the named layer within OM_TP_PING_RADIUS (500) of the point: one at 480 is revealed (control
    inside), one at 520 is not. The caster is 1,500 away, so the disc is not centred on it."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    inside = spawn(lib, w, VANGUARD, 1, 1500.0, 480.0, HIGH)
    outside = spawn(lib, w, VANGUARD, 1, 1500.0, -520.0, HIGH)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1
    assert side_sees(lib, w, 0, outside) == 0


def test_R_162_01_the_disc_radius_is_the_setting(lib, world_factory):
    """OM_TP_PING_RADIUS 200: a unit 150 from the point is revealed, one 250 away (inside the default 500) is not."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    inside = spawn(lib, w, VANGUARD, 1, 1500.0, 150.0, HIGH)
    outside = spawn(lib, w, VANGUARD, 1, 1500.0, -250.0, HIGH)
    set_param(lib, w, "PING_RADIUS", 200.0)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 1)
    assert side_sees(lib, w, 0, inside) == 1
    assert side_sees(lib, w, 0, outside) == 0


def test_R_162_01_a_ping_costs_no_resource_and_moves_nothing(lib, world_factory):
    """R-162-02: no resource. The caster's hp is untouched and neither unit moves; the ping is not an order."""
    w, caster, enemy = _scene(lib, world_factory)
    hp = lib.om_unit_get_hp(w, caster)
    x, y = lib.om_unit_position_x(w, caster), lib.om_unit_position_y(w, caster)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 5)
    assert lib.om_unit_get_hp(w, caster) == hp
    assert (lib.om_unit_position_x(w, caster), lib.om_unit_position_y(w, caster)) == (x, y)


# ---- reach from the caster (brief section 6: 2,000) ----

@pytest.mark.parametrize("ping_x,expected", [(1990.0, PING_OK), (2010.0, PING_REASON_REACH)])
def test_R_162_01_reach_is_measured_from_the_caster(lib, world_factory, ping_x, expected):
    """Brief G7: 'the point within OM_TP_PING_REACH of it'. A point 1,990 away is cast (control), one 2,010 away is
    refused with reason 2 (contract section 6), and a refused ping reveals nothing: the enemy at the point stays
    hidden, an accepted one reveals it."""
    w, caster, enemy = _scene(lib, world_factory, ping_x=ping_x)
    assert ping(lib, w, caster, HIGH, ping_x, 0.0) == expected
    step(lib, w, 1)
    assert side_sees(lib, w, 0, enemy) == (1 if expected == PING_OK else 0)


def test_R_162_01_reach_is_the_setting(lib, world_factory):
    """OM_TP_PING_REACH 1000: 990 away is cast, 1,010 away is refused (it would be inside the default 2,000)."""
    w, caster, enemy = _scene(lib, world_factory)
    set_param(lib, w, "PING_REACH", 1000.0)
    assert ping(lib, w, caster, HIGH, 990.0, 0.0) == PING_OK
    other = spawn(lib, w, RAIDER, 0, 0.0, 50.0, 0)
    assert ping(lib, w, other, HIGH, 1010.0, 50.0) == PING_REASON_REACH


def test_R_162_01_reach_is_planar_the_layer_gap_does_not_count(lib, world_factory):
    """The reach test is distance from the caster to the point; the four-layer gap between the caster (engine 0) and
    the named layer (engine 4) adds nothing. A point 1,990 away on layer 4 is accepted, shown in
    test_R_162_01_reach_is_measured_from_the_caster; here the same point from a caster on layer 4 is accepted too."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, HIGH)
    assert ping(lib, w, caster, HIGH, 1990.0, 0.0) == PING_OK
    assert ping(lib, w, spawn(lib, w, RAIDER, 0, 0.0, 10.0, 0), HIGH, 2010.0, 10.0) == PING_REASON_REACH


# ---- cooldown per unit (brief section 6: 400 ticks) ----

def test_R_006_03_a_second_ping_inside_the_cooldown_is_refused_and_leaves_the_cooldown_alone(lib, world_factory):
    """Brief G7 test 3 and R-006-03 analogue: 'before tick T plus 400, the command is rejected and the cooldown is
    unchanged'. Cast at T; refused (reason 3) right away, after 399 steps; accepted after 400. The refusals at 0 and at
    399 do not restart the clock, or the 400-step ping would be refused."""
    w, caster, enemy = _scene(lib, world_factory)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_REASON_COOLDOWN
    step(lib, w, COOLDOWN - 1)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_REASON_COOLDOWN
    step(lib, w, 1)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK


def test_R_006_03_the_cooldown_is_per_unit(lib, world_factory):
    """Brief G7: 'each unit has its own cooldown'. A second caster of the same side pings at once while the first is on
    cooldown (control inside: the first IS refused, so a call that never refuses cannot pass)."""
    w, caster, enemy = _scene(lib, world_factory)
    second = spawn(lib, w, RAIDER, 0, 0.0, 50.0, 0)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_REASON_COOLDOWN
    assert ping(lib, w, second, HIGH, 1500.0, 50.0) == PING_OK


def test_R_006_03_the_cooldown_is_the_setting(lib, world_factory):
    """OM_TP_PING_COOLDOWN_TICKS 50: refused after 49 steps, accepted after 50."""
    w, caster, enemy = _scene(lib, world_factory)
    set_param(lib, w, "PING_COOLDOWN_TICKS", 50)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    step(lib, w, 49)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_REASON_COOLDOWN
    step(lib, w, 1)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK


def test_R_006_03_a_refused_ping_does_not_reveal(lib, world_factory):
    """A refused ping 'changes nothing': a second caster-less case, the cooled-down caster's ping at a different
    point reveals no enemy there (the enemy by the second point stays hidden). Control inside: the first ping's
    enemy is revealed."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    first = spawn(lib, w, VANGUARD, 1, 1500.0, 0.0, HIGH)
    second = spawn(lib, w, VANGUARD, 1, 0.0, 1500.0, HIGH)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK
    assert ping(lib, w, caster, HIGH, 0.0, 1500.0) == PING_REASON_COOLDOWN
    step(lib, w, 1)
    assert side_sees(lib, w, 0, first) == 1
    assert side_sees(lib, w, 0, second) == 0


# ---- refusals: dead or unknown caster, bad layer (A132: 0 to OM_LAYER_COUNT - 1) ----

def test_R_162_01_a_dead_caster_cannot_ping(lib, world_factory):
    """Brief G7: 'The caster must be alive'. Reason 1. Control inside: the same call from a live unit is cast."""
    w, caster, enemy = _scene(lib, world_factory)
    dead = spawn(lib, w, RAIDER, 0, 0.0, 20.0, 0)
    lib.om_unit_set_hp(w, dead, 0.0)
    assert ping(lib, w, dead, HIGH, 1500.0, 20.0) == PING_REASON_CASTER
    step(lib, w, 1)
    assert side_sees(lib, w, 0, enemy) == 0, "a refused ping reveals nothing"
    assert alert_count(lib, w, 1) == 0, "and alerts no one"
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_OK


@pytest.mark.parametrize("caster", [0, 999999])
def test_R_162_01_an_unknown_caster_cannot_ping(lib, world_factory, caster):
    """Contract section 6: 'caster unknown or dead' is reason 1 (0 is never a unit id; 999999 does not exist)."""
    w, live, enemy = _scene(lib, world_factory)
    assert ping(lib, w, caster, HIGH, 1500.0, 0.0) == PING_REASON_CASTER
    assert ping(lib, w, live, HIGH, 1500.0, 0.0) == PING_OK  # control


def test_R_162_01_a_layer_at_or_above_the_layer_count_is_refused(lib, world_factory):
    """A132: every call that takes a layer accepts 0 to OM_LAYER_COUNT - 1; contract section 6: reason 4 for a layer at
    or above OM_LAYER_COUNT. Layer 5 is the first refused (engine layers 0 to 4 are bible layers 1 to 5). The refused
    pings cost nothing: the live ping on layer 4 right after is not on cooldown."""
    n = layer_count()
    assert n == 5, "OM_LAYER_COUNT is five (A132)"
    w, caster, enemy = _scene(lib, world_factory)
    for bad in (n, n + 1, 100, 0xFFFFFFFF):
        assert ping(lib, w, caster, bad, 1500.0, 0.0) == PING_REASON_LAYER, f"layer {bad}"
    step(lib, w, 1)
    assert side_sees(lib, w, 0, enemy) == 0
    assert alert_count(lib, w, 1) == 0
    assert ping(lib, w, caster, n - 1, 1500.0, 0.0) == PING_OK, "layer OM_LAYER_COUNT - 1 is valid and not on cooldown"


@pytest.mark.parametrize("layer", range(5))
def test_control_R_162_01_every_valid_layer_is_accepted(lib, world_factory, layer):
    """Positive control for the layer check (passes today on the stub): layers 0 to 4 each cast from a fresh caster."""
    w = world_factory(n_regions=1)
    caster = spawn(lib, w, RAIDER, 0, 0.0, 0.0, 0)
    assert ping(lib, w, caster, layer, 100.0, 0.0) == PING_OK


# ---- the alert and its sector (R-162-03) ----

def _bearing_sector(from_x, from_y, to_x, to_y):
    """The oracle: 60-degree slice, 0 to 5, counter-clockwise from +x, of the bearing from (from) to (to)."""
    deg = math.degrees(math.atan2(to_y - from_y, to_x - from_x)) % 360.0
    return int(deg // 60.0)


def _alert_scene(lib, world_factory, theta_deg, r=1500.0, ex=5000.0, ey=5000.0):
    """Enemy (faction 1, engine layer 4) at E; caster (faction 0, engine layer 0) r wu from it at bearing theta
    (degrees counter-clockwise from +x, measured from the enemy to the caster). The alert is off by default
    (R-162-03, Westley 2026-10-05), so this scene switches it on (OM_TP_PING_ALERT 1)."""
    w = world_factory(n_regions=1)
    set_ping_alert(lib, w, 1)
    cx = ex + r * math.cos(math.radians(theta_deg))
    cy = ey + r * math.sin(math.radians(theta_deg))
    caster = spawn(lib, w, RAIDER, 0, cx, cy, 0)
    enemy = spawn(lib, w, VANGUARD, 1, ex, ey, HIGH)
    return w, caster, enemy, (ex, ey), (cx, cy)


@pytest.mark.parametrize("theta", [10.0, 70.0, 100.0, 130.0, 200.0, 250.0, 310.0, 350.0])
def test_R_162_03_the_pinged_side_gets_an_alert_whose_sector_contains_the_bearing_to_the_caster(
        lib, world_factory, theta):
    """R-162-03 and brief G7: the pinged side is alerted, with the tick and the 60-degree slice, numbered 0 to 5
    counter-clockwise from the +x axis, that contains the bearing from the centroid of its pinged units to the caster.
    The caster sits 1,500 wu from the single pinged unit at bearing theta, mid-slice or not near a slice edge."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, theta)
    expected = _bearing_sector(e[0], e[1], c[0], c[1])
    tick = lib.om_tactical_tick(w)
    assert alert_count(lib, w, 1) == 0, "control: no alert before the ping"
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 1
    rc, atick, afaction, sector = alert(lib, w, 1, 0)
    assert rc == 0
    assert (atick, afaction) == (tick, 1)
    assert sector == expected, f"bearing {theta} deg is in slice {expected}"


def test_R_162_03_a_caster_moved_thirty_degrees_inside_the_slice_gives_the_same_sector(lib, world_factory):
    """Brief G7 test: 'a caster moved 30 degrees within the same slice gives the same sector'. Bearings 70 and 100
    degrees are both in slice 1 (60 to 120), 30 degrees apart; a bearing of 130 (slice 2) differs, so the sector
    does change when the slice does (control)."""
    sectors = {}
    for theta in (70.0, 100.0, 130.0):
        w, caster, enemy, e, c = _alert_scene(lib, world_factory, theta)
        assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
        rc, _, _, sector = alert(lib, w, 1, 0)
        assert rc == 0
        sectors[theta] = sector
    assert sectors[70.0] == sectors[100.0] == 1
    assert sectors[130.0] == 2


def test_R_162_03_the_sector_is_taken_from_the_centroid_of_the_pinged_units(lib, world_factory):
    """Brief G7: the bearing 'from the centroid of that side's pinged units to the caster'. Two pinged units 300 wu to
    either side of E; the caster is at bearing 57 degrees from the centroid E, which is slice 0. The unit spawned
    first is on the far side, whose own bearing to the caster is in slice 1, so 'the first unit' gives the wrong
    answer. The premise is asserted before the ping."""
    theta, r, ex, ey = 57.0, 1500.0, 5000.0, 5000.0
    px, py = -math.sin(math.radians(theta)), math.cos(math.radians(theta))
    w = world_factory(n_regions=1)
    set_ping_alert(lib, w, 1)   # the alert is off by default (R-162-03, Westley 2026-10-05)
    cx, cy = ex + r * math.cos(math.radians(theta)), ey + r * math.sin(math.radians(theta))
    caster = spawn(lib, w, RAIDER, 0, cx, cy, 0)
    first = spawn(lib, w, VANGUARD, 1, ex - 300.0 * px, ey - 300.0 * py, HIGH)
    second = spawn(lib, w, VANGUARD, 1, ex + 300.0 * px, ey + 300.0 * py, HIGH)
    assert _bearing_sector(ex, ey, cx, cy) == 0
    assert _bearing_sector(ex - 300.0 * px, ey - 300.0 * py, cx, cy) == 1, "premise: the first unit alone says 1"
    assert _bearing_sector(ex + 300.0 * px, ey + 300.0 * py, cx, cy) == 0
    assert ping(lib, w, caster, HIGH, ex, ey) == PING_OK
    assert alert_count(lib, w, 1) == 1, "one alert per side, not one per unit"
    assert alert(lib, w, 1, 0)[3] == 0


def test_R_162_03_the_casting_side_gets_no_alert(lib, world_factory):
    """Brief G7: 'the casting side gets no alert', even with its own unit on the pinged layer inside the disc.
    Control inside: the pinged side does get one."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, 100.0)
    friendly = spawn(lib, w, VANGUARD, 0, e[0] + 50.0, e[1], HIGH)
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 1
    assert alert_count(lib, w, 0) == 0


def test_R_162_03_a_side_with_no_unit_in_the_disc_gets_no_alert(lib, world_factory):
    """Brief G7: 'every side with at least one unit inside the pinged disc gets an alert'. The enemy 600 from the ping
    point (outside the 500 disc) is not alerted. Control inside: a ping at its position alerts it."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, 100.0)
    assert ping(lib, w, caster, HIGH, e[0] + 600.0, e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 0
    other = spawn(lib, w, RAIDER, 0, c[0], c[1] + 10.0, 0)
    assert ping(lib, w, other, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 1


def test_R_162_03_a_refused_ping_alerts_no_one(lib, world_factory):
    """A refused ping changes nothing: no alert for a cooldown refusal, a reach refusal or a layer refusal. Control
    inside: the first ping alerts."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, 100.0)
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 1
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_REASON_COOLDOWN
    assert ping(lib, w, caster, layer_count(), e[0], e[1]) == PING_REASON_LAYER
    other = spawn(lib, w, RAIDER, 0, c[0], c[1] + 10.0, 0)
    assert ping(lib, w, other, HIGH, e[0] + 3000.0, e[1]) == PING_REASON_REACH
    assert alert_count(lib, w, 1) == 1


def test_R_162_03_alerts_accumulate_oldest_first_with_their_tick(lib, world_factory):
    """Contract section 6: 'alert `index` (0 oldest)'. Two pings 400 ticks apart (the cooldown): two alerts, ticks
    T and T + 400, in that order. `om_ping_alert_get` is 0 for a valid index, -1 for an index past the end and -1
    for a NULL out."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, 100.0)
    t0 = lib.om_tactical_tick(w)
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    step(lib, w, COOLDOWN)
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 2
    assert alert(lib, w, 1, 0)[:2] == (0, t0)
    assert alert(lib, w, 1, 1)[:2] == (0, t0 + COOLDOWN)
    assert alert(lib, w, 1, 2)[0] == -1
    assert lib.om_ping_alert_get(w, 1, 0, None) == -1


def test_R_162_03_an_unknown_faction_has_no_alerts(lib, world_factory):
    """Contract section 6: 'alerts held for faction; 0 for an unknown faction'. Control inside: the pinged faction 1
    holds one, so a count that is 0 for everything cannot pass."""
    w, caster, enemy, e, c = _alert_scene(lib, world_factory, 100.0)
    assert ping(lib, w, caster, HIGH, e[0], e[1]) == PING_OK
    assert alert_count(lib, w, 1) == 1
    assert alert_count(lib, w, 77) == 0
    assert alert_count(lib, w, -1) == 0


# ---- the ping lets the side's long-range units fire (G3 consumer; R-008-04, R-162-05) ----
#
# Why these are red today: the C acquires and fires at any enemy in range whatever the side sees (brief G3:
# "today it steps toward any enemy, through anything"), so a Bombard hits a target 1,000 wu away with no spotter
# and no ping. The "no ping, no fire" step of each test below fails today for that reason (G3 not built); the ping
# calls are inert stubs (om_command_ping returns 0, reveals nothing). Once G3 and the ping both land they pass.

def _bombard_scene(lib, world_factory, spotter_x=0.0, victim_x=1000.0):
    """Faction 0: a Bombard at the origin (sensor 300, range 1,200) and a Raider spotter at (spotter_x, 200) (sensor
    800). Faction 1: a Supply unit victim_x wu east of the Bombard, same layer (it never fires back). At 1,000 the
    target is beyond the Bombard's sensor and the spotter's (about 1,020 from it): the side does not see it. Reveal
    is set to 300 ticks so the Bombard's 3-second attack interval fits inside it."""
    w = world_factory(n_regions=1)
    bombard = spawn(lib, w, BOMBARD, 0, 0.0, 0.0, 0)
    spotter = spawn(lib, w, RAIDER, 0, spotter_x, 200.0, 0)
    victim = spawn(lib, w, SUPPLY, 1, victim_x, 0.0, 0)
    set_param(lib, w, "PING_REVEAL_TICKS", 300)
    return w, bombard, spotter, victim


def test_control_R_008_04_a_seen_target_is_fired_at_by_the_bombard(lib, world_factory):
    """Positive control for the tests below (passes today): the same Bombard and Supply victim, victim 250 wu away
    (inside the Bombard's own sensor 300), takes damage within 200 ticks. So 'hp unchanged' below means the Bombard
    was held back, not that this fixture cannot fire."""
    w, bombard, spotter, victim = _bombard_scene(lib, world_factory, victim_x=250.0)
    hp0 = lib.om_unit_get_hp(w, victim)
    step(lib, w, 200)
    assert lib.om_unit_get_hp(w, victim) < hp0


def test_R_008_04_a_ping_lets_the_sides_long_range_unit_fire(lib, world_factory):
    """R-008-04: 'a unit never fires at a target its side cannot see ... a target seen by any friendly unit or
    revealed by a ping may be fired at'. Step 1: no ping, 100 ticks, the Bombard (range 1,200, sensor 300) does not
    hit the victim 1,000 wu away. Step 2: the spotter (1,020 from the victim, in reach) pings the victim's position;
    within the 300-tick reveal the Bombard fires, because its side now sees the target (R-093-02, shared sight)."""
    w, bombard, spotter, victim = _bombard_scene(lib, world_factory)
    hp0 = lib.om_unit_get_hp(w, victim)
    step(lib, w, 100)
    assert lib.om_unit_get_hp(w, victim) == hp0, "R-008-04: fired at a target the side cannot see"
    assert ping(lib, w, spotter, 0, 1000.0, 0.0) == PING_OK
    step(lib, w, 200)
    assert lib.om_unit_get_hp(w, victim) < hp0, "the Bombard never fired at the revealed target"


def test_R_162_05_when_the_reveal_ends_the_fire_stops(lib, world_factory):
    """R-162-05: 'when no passive detection applies, the units it revealed are hidden again', and brief G3: a target
    that leaves the visible set is dropped; a unit never holds a target it cannot fire at. After the reveal (300
    ticks) plus a few ticks for the next acquisition, the Bombard holds no target and the victim's hp stops falling.
    Control inside: it fell during the reveal."""
    w, bombard, spotter, victim = _bombard_scene(lib, world_factory)
    hp0 = lib.om_unit_get_hp(w, victim)
    assert ping(lib, w, spotter, 0, 1000.0, 0.0) == PING_OK
    step(lib, w, 300)
    assert lib.om_unit_get_hp(w, victim) < hp0, "control: it was hit during the reveal"
    step(lib, w, 20)
    hp_settled = lib.om_unit_get_hp(w, victim)
    assert lib.om_unit_target(w, bombard) == -1, "the Bombard still holds a target the side cannot see"
    step(lib, w, 200)
    assert lib.om_unit_get_hp(w, victim) == hp_settled


def test_R_162_01_a_refused_ping_does_not_let_the_side_fire(lib, world_factory):
    """A ping refused for reach reveals nothing: a spotter 2,500 wu from the point (reach 2,000) is refused with
    reason 2 and the Bombard, which cannot see the victim, does not fire in 200 ticks. Control: the test two above,
    with the spotter in reach, fires."""
    w, bombard, spotter, victim = _bombard_scene(lib, world_factory, spotter_x=-1500.0)
    hp0 = lib.om_unit_get_hp(w, victim)
    assert ping(lib, w, spotter, 0, 1000.0, 0.0) == PING_REASON_REACH
    step(lib, w, 200)
    assert lib.om_unit_get_hp(w, victim) == hp0
