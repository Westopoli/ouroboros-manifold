"""F5 window control for csrc/fog.c (E-12, wave 2 card B11).

Rule (docs/bible/algorithms.md ALG-65 "Visibility"): `effective = sensor_radius
* (1 - interference(observer position))`. Sampled at the exact center of a
planted interference zone (distance 0, so no radial falloff shape is in
play), the sample must read back the zone's own configured intensity: a zone
planted with intensity=0.35 must sample as 0.35 at its center.

PLANT: under OM_BUG_INTERFERENCE_IGNORES_INTENSITY, om_zone_sample_interference
ignores the zone's configured intensity and reports full interference (1.0)
for any point inside any zone's radius.
"""
import pytest

from conftest import OMBugE12


def test_control_interference_ignores_intensity_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE12.INTERFERENCE_IGNORES_INTENSITY)

    dbg.om_map_add_interference_zone(w, 500.0, 500.0, 0, 0.35, 100.0)

    sampled = dbg.om_zone_sample_interference(w, 500.0, 500.0, 0)

    assert sampled == pytest.approx(1.0, abs=1e-9), (
        "OM_BUG_INTERFERENCE_IGNORES_INTENSITY injected but the sample at "
        "the zone's own center still reads its correct configured intensity "
        "(0.35) instead of the constant 1.0 -- the detector did not trip"
    )
