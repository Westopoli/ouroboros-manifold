"""Rung R1 tests 4 and 5 (SPEC.md section 10): can_see isolation on E-01 R-005 numbers, and cover.

Vision is read through `layerlab.run.probe_can_see(scn, observer, target)` (SPEC 8, 5.2). The
module attribute is looked up at call time so that, until R1 exists, every test here fails on
its own with AttributeError instead of breaking collection.

R-005 numbers are the rule's: effective radius = sensor * factor, with no elevation bonus.
SPEC 5.2 step 3 multiplies in `1 + sensor_elev_bonus_per_layer * (obs_layer - tgt_layer)`. The lab
default is 0 (production's 0.15 is per elevation tier, not per layer), so the R-005 numbers hold by
default; the R-005 cases still set it to 0 explicitly so they stay valid if the default moves.
At 0.15 R-005-04's two-layer-up radius would be 140, not 200; the bonus has its own test.
Spawn jitter is zero so distances are exact.
"""
import pytest

import layerlab.run as runmod
from conftest import grp, make_scenario

OBS_X, OBS_Y = 2000.0, 1000.0
NO_ELEV = {"spawn_jitter": 0.0, "sensor_elev_bonus_per_layer": 0.0}


def can_see(obs_layer, tgt_layer, dist, *, rules=None, terrain=None, obs_xy=(OBS_X, OBS_Y),
            tgt_xy=None, tgt_type="raider"):
    """Observer is an interceptor (sensor 1000) at obs_xy; target at distance `dist` along +x
    (or at tgt_xy). Returns probe_can_see(observer=0, target=1)."""
    r = dict(NO_ELEV)
    r.update(rules or {})
    if tgt_xy is None:
        tgt_xy = (obs_xy[0] + dist, obs_xy[1])
    scn = make_scenario(
        [grp("A", "interceptor", obs_xy[0], obs_xy[1], obs_layer),
         grp("B", tgt_type, tgt_xy[0], tgt_xy[1], tgt_layer)],
        rules=r, terrain=terrain)
    return bool(runmod.probe_can_see(scn, 0, 1))


# ---- test 4: can_see on R-005-01 .. R-005-07 -------------------------------------------------

@pytest.mark.parametrize("dist,expected", [(900.0, True), (1100.0, False)])
def test_same_layer_sensor_radius(dist, expected):
    """R-005-01: observer sensor 1000 on layer 3, enemy on layer 3 at 900 is visible; control
    (negative case) at 1100, just past the sensor radius, is not."""
    assert can_see(3, 3, dist) is expected


@pytest.mark.parametrize("dist,expected", [(400.0, True), (600.0, False)])
def test_adjacent_layer_factor_half(dist, expected):
    """R-005-02 and R-005-03: enemy on layer 4 (adjacent, factor 0.50, effective radius 500):
    visible at 400 (positive), not visible at 600 (negative)."""
    assert can_see(3, 4, dist) is expected


@pytest.mark.parametrize("dist,expected", [(150.0, True), (250.0, False)])
def test_two_layers_up_factor_point_two(dist, expected):
    """R-005-04: enemy on layer 5 (two layers up, factor 0.20, effective radius 200): visible
    at 150 (positive), not visible at 250 (negative)."""
    assert can_see(3, 5, dist) is expected


@pytest.mark.parametrize("dist,expected", [(150.0, True), (250.0, False)])
def test_two_layers_down_visible_under_symmetric_table(dist, expected):
    """R-005-05 under Q-005-02 reading (a), the default symmetric table (vis_factor[2] = 0.2,
    as production's absolute-offset factor): an enemy on layer 1, two below the observer on
    layer 3, is visible at 150 (positive) and not at 250 (negative, past radius 200)."""
    assert can_see(3, 1, dist) is expected


def test_two_layers_down_hidden_under_asymmetric_table():
    """R-005-05 under Q-005-02 reading (b): vis_factor offset index 2 (looking two layers down)
    set to 0, so an enemy on layer 1 is not visible at 150 (negative case). Positive control in
    the same table: the enemy two layers UP (index 6, still 0.2) at 150 is visible, so the table
    edit removed only the downward look."""
    asym = [0.0, 0.0, 0.0, 0.5, 1.0, 0.5, 0.2, 0.0, 0.0]
    assert can_see(3, 1, 150.0, rules={"vis_factor": asym}) is False
    assert can_see(3, 5, 150.0, rules={"vis_factor": asym}) is True


@pytest.mark.parametrize("obs_layer,tgt_layer", [(2, 5), (4, 1), (1, 5), (5, 1), (1, 4), (5, 2)])
def test_three_or_more_layers_never_visible_by_default(obs_layer, tgt_layer):
    """R-005-05 (three or more layers away, either direction) with the default tables: never
    visible, even at 10 units (negative). Positive control: two layers apart at 10 units IS
    visible, so the check is able to say yes."""
    assert can_see(obs_layer, tgt_layer, 10.0) is False
    two_apart = obs_layer + 2 if obs_layer <= 3 else obs_layer - 2
    assert can_see(obs_layer, two_apart, 10.0) is True


VANTAGE_ON_OBSERVER = {"vantage": [{"x": OBS_X, "y": OBS_Y, "r": 100.0}]}


@pytest.mark.parametrize("obs_layer,tgt_layer,dist,expected", [
    (3, 4, 900.0, True),    # adjacent 1.00 -> radius 1000
    (3, 4, 1100.0, False),
    (3, 5, 350.0, True),    # two-layer 0.40 -> radius 400
    (3, 5, 450.0, False),
    (2, 5, 150.0, True),    # three-layer 0.20 -> radius 200
    (2, 5, 250.0, False),
])
def test_vantage_disc_factors(obs_layer, tgt_layer, dist, expected):
    """R-005-06: an observer standing inside a vantage disc uses vantage_vis_factor: adjacent
    1.00 (radius 1000), two-layer 0.40 (400), three-layer 0.20 (200). Each pair has a case
    inside and one outside the radius (positive and negative)."""
    assert can_see(obs_layer, tgt_layer, dist, terrain=VANTAGE_ON_OBSERVER) is expected


@pytest.mark.parametrize("obs_layer,tgt_layer,dist", [(3, 4, 900.0), (3, 5, 350.0), (2, 5, 150.0)])
def test_without_vantage_the_same_pairs_are_hidden(obs_layer, tgt_layer, dist):
    """R-005-06 negative control: the same pairs with no vantage disc are not visible (default
    adjacent 0.5 -> 500, two-layer 0.2 -> 200, three-layer 0), so the vantage cases above prove
    the disc is what changed the answer."""
    assert can_see(obs_layer, tgt_layer, dist) is False


def test_vantage_disc_not_containing_observer_changes_nothing():
    """R-005-06 'standing at a vantage node': a disc elsewhere on the map (observer outside it)
    does not apply. Adjacent layer at 900 stays hidden (negative); with the disc on the observer
    it is visible (positive)."""
    far_disc = {"vantage": [{"x": 3500.0, "y": 500.0, "r": 100.0}]}
    assert can_see(3, 4, 900.0, terrain=far_disc) is False
    assert can_see(3, 4, 900.0, terrain=VANTAGE_ON_OBSERVER) is True


def test_interference_zone_halves_adjacent_radius():
    """R-005-07: observer inside an interference zone of intensity 0.5 (at the zone centre, on
    the zone's layer): the adjacent-layer radius is sensor * 0.50 * 0.50 = 250. Visible at 240
    (positive), not at 260 (negative). Control without the zone: 260 is visible (radius 500)."""
    zone = {"zone": [{"x": OBS_X, "y": OBS_Y, "r": 400.0, "intensity": 0.5, "layer": 3}]}
    assert can_see(3, 4, 240.0, terrain=zone) is True
    assert can_see(3, 4, 260.0, terrain=zone) is False
    assert can_see(3, 4, 260.0) is True


def test_interference_zone_applies_only_on_its_own_layer_and_inside_radius():
    """R-005-07 negative cases: a zone on another layer than the observer's (layer 4, observer
    on 3) does nothing; a zone whose radius the observer is outside of does nothing. Both leave
    the adjacent-layer target at 400 visible (radius 500)."""
    other_layer = {"zone": [{"x": OBS_X, "y": OBS_Y, "r": 400.0, "intensity": 0.5, "layer": 4}]}
    outside = {"zone": [{"x": 3300.0, "y": OBS_Y, "r": 300.0, "intensity": 0.5, "layer": 3}]}
    assert can_see(3, 4, 400.0, terrain=other_layer) is True
    assert can_see(3, 4, 400.0, terrain=outside) is True


def test_sensor_elevation_bonus_default_value():
    """SPEC 5.2 step 3 (sensor_elev_bonus_per_layer set to production's 0.15, factor
    1 + bonus * (observer layer - target layer), floored at 0). Observer on layer 3, sensor
    1000, default tables: adjacent layer 4 radius is 1000*0.5*0.85 = 425 (visible at 420, not
    at 430); layer 5 radius 1000*0.2*0.7 = 140 (visible at 130, not at 150: R-005-04's 150
    needs the bonus off, see module docstring); layer 1 radius 1000*0.2*1.3 = 260 (visible at
    250, not at 270)."""
    r = {"spawn_jitter": 0.0, "sensor_elev_bonus_per_layer": 0.15}
    cases = [(4, 420.0, True), (4, 430.0, False), (5, 130.0, True), (5, 150.0, False),
             (1, 250.0, True), (1, 270.0, False)]
    for tgt_layer, dist, expected in cases:
        assert can_see(3, tgt_layer, dist, rules=r) is expected, (tgt_layer, dist)


# ---- test 5: cover ---------------------------------------------------------------------------

COVER_X = 2000.0


def cover_disc(r=100.0, height=2, x=COVER_X, y=OBS_Y):
    return {"cover": [{"x": x, "y": y, "r": r, "height_layer": height}]}


def sees_across_cover(layer, *, terrain, cover_mode=1, obs_x=1700.0, tgt_x=2300.0, y=OBS_Y):
    """Observer (interceptor, sensor 1000) and target 600 apart on the same layer; the disc
    sits at x = 2000 by default so the segment passes through its centre."""
    scn = make_scenario(
        [grp("A", "interceptor", obs_x, y, layer), grp("B", "raider", tgt_x, y, layer)],
        rules={"spawn_jitter": 0.0, "cover_mode": cover_mode}, terrain=terrain)
    return bool(runmod.probe_can_see(scn, 0, 1))


def test_cover_hides_target_when_obstacle_reaches_the_layer():
    """R-007-01: an obstacle whose height reaches layer 2 between observer and target, both on
    layer 1: the target is not visible (negative case). Control (positive case): cover_mode 0,
    where the identical pair is visible."""
    assert sees_across_cover(1, terrain=cover_disc(height=2)) is False
    assert sees_across_cover(1, terrain=cover_disc(height=2), cover_mode=0) is True


def test_cover_does_not_hide_above_its_height():
    """R-007-02: the same obstacle with both units on layer 3: the target is visible (the
    obstacle does not reach layer 3). Negative control: layer 2, which the height-2 obstacle does
    reach (SPEC 5.3: blocks when the interpolated layer <= height_layer), is hidden."""
    assert sees_across_cover(3, terrain=cover_disc(height=2)) is True
    assert sees_across_cover(2, terrain=cover_disc(height=2)) is False


def test_cover_off_the_sight_line_hides_nothing():
    """R-007-01 negative control: a height-2 disc beside the line (centre 300 units off the
    segment, radius 100) does not hide a layer-1 target; the segment misses it."""
    assert sees_across_cover(1, terrain=cover_disc(y=OBS_Y + 300.0)) is True
    assert sees_across_cover(1, terrain=cover_disc()) is False


def test_cover_disc_containing_an_endpoint_does_not_hide_it():
    """R-007-01 / SPEC 5.3: a disc that contains an endpoint's xy does not hide it. Target at
    x = 2050 inside the disc (centre 2000, r 100): visible (positive). Observer at x = 1950
    inside the disc: visible. Control: both endpoints outside the same disc with the segment
    through its centre: hidden (negative)."""
    assert sees_across_cover(1, terrain=cover_disc(), obs_x=1700.0, tgt_x=2050.0) is True
    assert sees_across_cover(1, terrain=cover_disc(), obs_x=1950.0, tgt_x=2300.0) is True
    assert sees_across_cover(1, terrain=cover_disc(), obs_x=1700.0, tgt_x=2300.0) is False


def _duel(layer, terrain, cover_mode, *, pre_revealed_a=False):
    """A raider at x=1925 and a raider at x=2075, 150 apart (inside range 200), disc at x=2000
    r=40 between them; endpoints are 75 from the disc centre, outside it."""
    a_kw = {"pre_revealed": 1} if pre_revealed_a else {}
    scn = make_scenario(
        [grp("A", "raider", 1925.0, OBS_Y, layer, **a_kw), grp("B", "raider", 2075.0, OBS_Y, layer)],
        rules={"spawn_jitter": 0.0, "cover_mode": cover_mode}, terrain=terrain,
        run={"max_ticks": 40, "stalemate_ticks": 6000})
    return scn


def test_cover_never_changes_damage():
    """R-007-04 (cover is never a damage reduction): two raiders on layer 3 see each other past
    a height-2 disc (it does not reach layer 3). Same seed with cover_mode 0 and 1: identical
    damage_dealt and shots, and every hit is the unmodified 9.0 (positive: damage happens, so
    the equality is not vacuous)."""
    small = cover_disc(r=40.0, height=2)
    r0 = runmod.run(_duel(3, small, 0), seed=3)
    r1 = runmod.run(_duel(3, small, 1), seed=3)
    assert r0.shots[0] > 0 and r0.shots[1] > 0
    assert r0.damage_dealt == r1.damage_dealt
    assert r0.shots == r1.shots
    for side in (0, 1):
        assert r1.damage_dealt[side] == pytest.approx(9.0 * r1.shots[side])


def test_cover_detector_is_live_on_damage():
    """R-007-01 with R-007-04 (negative control for the test above): the same duel on layer 1,
    where the disc does reach, deals no damage at all with cover_mode 1 (neither side sees the
    other) and does with cover_mode 0, so cover is observable through damage."""
    small = cover_disc(r=40.0, height=2)
    hidden = runmod.run(_duel(1, small, 1), seed=3)
    open_ = runmod.run(_duel(1, small, 0), seed=3)
    assert hidden.damage_dealt == (0.0, 0.0) and hidden.shots == (0, 0)
    assert open_.damage_dealt[0] > 0 and open_.damage_dealt[1] > 0


def test_hidden_attacker_still_fires_at_an_observer_it_can_see():
    """R-007-03 (SPEC 5.3: cover is applied only inside can_see): A is pre_revealed, so B's side
    sees it; B stands behind the cover disc from A's view (layer 1, cover_mode 1), so A never
    sees B. B fires and lands (positive); A, unable to see B, deals nothing (negative); firing
    does not reveal B."""
    res = runmod.run(_duel(1, cover_disc(r=40.0, height=2), 1, pre_revealed_a=True), seed=3)
    assert res.damage_dealt[1] > 0
    assert res.damage_dealt[0] == 0.0
