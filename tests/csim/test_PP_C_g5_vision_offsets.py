"""Phase C step G5, the cross-layer vision factor per signed layer offset (E-01 R-005-02, R-005-04,
R-005-05; register Q-008-03 families; ruling A133 Q-C2).

A133 Q-C2: 'Vision per signed offset (VISION_UP_1..4, VISION_DOWN_1..4) replaces the two cone
parameters.' pp_contract.md section 3: 'the cross-layer vision factor (a fraction of sensor radius)
when the other unit is n layers above, or below, the observer.' Defaults 0.5, 0.2, 0.0, 0.0 each way
(om_constants OM_CONE_LAYER_1_FACTOR, _2_FACTOR; R-005-05: three layers or more apart is never seen).
Range 0 to 1 (refusal bounds, A133 Q-C9).

Observer: a Raider (sensor 800); the check is om_unit_can_see(observer, target). Vantage zones,
interference and cover are absent, so the radius is sensor x factor. Layers are engine layers 0 to 4
(A132).

Red today: om_unit_can_see reads the compile-time factors (fog.c om_unit_get_cross_layer_factor) and
never the settings, so any non-default setting is ignored. The defaults test is a green control by
design (engine defaults keep today's behaviour); every other test opens with a setting the engine
must honour.
"""
import pytest

from test_PP_C_g5_support import (
    EDGE, RAIDER, SUPPLY, VANGUARD, get_param, layers_for, set_param, set_reach, spawn,
)

SENSOR = 800.0  # OM_ROSTER_RAIDER_SENSOR
OFFSETS = [(d, n) for d in ("UP", "DOWN") for n in range(1, 5)]


def _sees(lib, world_factory, direction, n, dist, params=None, observer=RAIDER):
    """Whether an observer sees an enemy `dist` wu away n layers up or down from it, with the given
    settings, in a fresh world."""
    w = world_factory(n_regions=1)
    for name, value in (params or {}).items():
        assert set_param(lib, w, name, value) == 0
    a_layer, t_layer = layers_for(direction, n)
    o = spawn(lib, w, observer, 0, 0.0, 0.0, layer=a_layer)
    t = spawn(lib, w, SUPPLY, 1, float(dist), 0.0, layer=t_layer)
    return lib.om_unit_can_see(w, o, t) == 1


def test_R_005_05_default_vision_factors_are_half_a_fifth_then_none_both_ways(lib, world_factory):
    """Control, green today: with no setting touched the Raider sees one layer away to 400 wu
    (R-005-02, factor 0.50), two layers to 160 (R-005-04, 0.20), and three or four layers never,
    in both directions (R-005-05). Reading the settings back gives the same four numbers."""
    for direction in ("UP", "DOWN"):
        for n, factor in ((1, 0.5), (2, 0.2), (3, 0.0), (4, 0.0)):
            assert get_param(lib, world_factory(n_regions=1), f"OM_TP_VISION_{direction}_{n}") == factor
            if factor > 0.0:
                edge = SENSOR * factor
                assert _sees(lib, world_factory, direction, n, edge - EDGE), f"{direction} {n}: inside {edge}"
                assert not _sees(lib, world_factory, direction, n, edge + EDGE), f"{direction} {n}: beyond {edge}"
            else:
                assert not _sees(lib, world_factory, direction, n, 1.0), f"{direction} {n}: never"


@pytest.mark.parametrize("direction,n", OFFSETS)
def test_Q_C2_vision_setting_sets_the_cross_layer_radius_at_each_signed_offset(lib, world_factory, direction, n):
    """OM_TP_VISION_<dir>_<n> = 0.3 gives a radius of 800 x 0.3 = 240 wu at that offset: seen at 235,
    not seen at 245 (and, for offsets 3 and 4, seen at all, which defaults never allow). Today the
    setting is ignored: the default factor decides."""
    name = f"OM_TP_VISION_{direction}_{n}"
    edge = SENSOR * 0.3
    assert _sees(lib, world_factory, direction, n, edge - EDGE, {name: 0.3}), f"{name} 0.3: 235 wu is inside 240"
    assert not _sees(lib, world_factory, direction, n, edge + EDGE, {name: 0.3}), f"{name} 0.3: 245 wu is beyond 240"


@pytest.mark.parametrize("direction,n", OFFSETS)
def test_Q_C2_a_factor_of_one_sees_the_full_sensor_radius_and_zero_sees_nothing(lib, world_factory, direction, n):
    """Factor 1.0: the full 800 wu (seen at 795, not at 805). Factor 0: not even at 1 wu, though the
    same enemy at 1 wu is seen by default at offsets 1 and 2 (control inside the test where the
    default sees it)."""
    name = f"OM_TP_VISION_{direction}_{n}"
    assert _sees(lib, world_factory, direction, n, SENSOR - EDGE, {name: 1.0})
    assert not _sees(lib, world_factory, direction, n, SENSOR + EDGE, {name: 1.0})
    if n <= 2:
        assert _sees(lib, world_factory, direction, n, 1.0), "control: the default factor sees 1 wu away"
    assert not _sees(lib, world_factory, direction, n, 1.0, {name: 0.0})


def test_Q_C2_vision_is_per_direction(lib, world_factory):
    """Up and down are separate: UP_1 = 1.0 and DOWN_1 = 0.25 (a 200 wu radius) on a Raider in the
    middle layer: it sees an enemy one layer up at 600 and not one layer down at 600, nor one layer
    down at 210; it sees one layer down at 190. Then the other way round."""
    def sees(t_layer, dist, params):
        w = world_factory(n_regions=1)
        for k, v in params.items():
            assert set_param(lib, w, k, v) == 0
        o = spawn(lib, w, RAIDER, 0, 0.0, 0.0, layer=2)
        t = spawn(lib, w, SUPPLY, 1, float(dist), 0.0, layer=t_layer)
        return lib.om_unit_can_see(w, o, t) == 1
    asym = {"OM_TP_VISION_UP_1": 1.0, "OM_TP_VISION_DOWN_1": 0.25}
    assert sees(3, 600.0, asym), "up at 600 with factor 1.0"
    assert not sees(1, 600.0, asym)
    assert not sees(1, 210.0, asym)
    assert sees(1, 190.0, asym)
    flip = {"OM_TP_VISION_UP_1": 0.25, "OM_TP_VISION_DOWN_1": 1.0}
    assert sees(1, 600.0, flip), "down at 600 with factor 1.0"
    assert not sees(3, 600.0, flip)
    assert not sees(3, 210.0, flip)
    assert sees(3, 190.0, flip)


def test_Q_C2_vision_is_per_offset_not_per_direction_only(lib, world_factory):
    """UP_2 = 1.0 changes what is seen two layers up and nothing else: at 600 wu the enemy two layers
    up is seen, the one one layer up (default 400) and the one two layers down (default 160) are not."""
    p = {"OM_TP_VISION_UP_2": 1.0}
    assert _sees(lib, world_factory, "UP", 2, 600.0, p)
    assert not _sees(lib, world_factory, "UP", 1, 600.0, p)
    assert not _sees(lib, world_factory, "DOWN", 2, 600.0, p)


def test_Q_C2_a_units_reach_does_not_change_what_it_sees(lib, world_factory):
    """pp_contract section 3: 'Which offsets a unit may fire at at all is its type's reach, not
    these.' A Raider with reach (0, 0) and one with reach (4, 4) see the same: both see an enemy one
    layer up at 390 and not at 410. The sight half needs the setting honoured too: both then see
    to 700 with UP_1 = 0.9 (fails today, the setting is ignored), so the test is red for the vision
    reason and not for a reach one."""
    for reach in ((0, 0), (4, 4)):
        w = world_factory(n_regions=1)
        if reach != (0, 0):
            assert set_reach(lib, w, RAIDER, *reach) == 0
        assert set_param(lib, w, "OM_TP_VISION_UP_1", 0.9) == 0
        o = spawn(lib, w, RAIDER, 0, 0.0, 0.0, layer=1)
        near = spawn(lib, w, SUPPLY, 1, 700.0, 0.0, layer=2)
        assert lib.om_unit_can_see(w, o, near) == 1, f"reach {reach}: factor 0.9 sees 700 wu"
        far = spawn(lib, w, SUPPLY, 1, 730.0, 0.0, layer=2)
        assert lib.om_unit_can_see(w, o, far) == 0, f"reach {reach}: 730 wu is beyond 720"


def test_Q_C2_the_sensor_type_scales_the_signed_radius(lib, world_factory):
    """The factor is a fraction of the observer's own sensor radius: a Vanguard (sensor 700) at 0.3
    sees 210 wu one layer down, a Raider (800) 240."""
    p = {"OM_TP_VISION_DOWN_1": 0.3}
    assert _sees(lib, world_factory, "DOWN", 1, 700.0 * 0.3 - EDGE, p, observer=VANGUARD)
    assert not _sees(lib, world_factory, "DOWN", 1, 700.0 * 0.3 + EDGE, p, observer=VANGUARD)
