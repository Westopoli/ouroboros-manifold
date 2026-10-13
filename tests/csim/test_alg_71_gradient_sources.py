"""ALG-71 Gradient sources (docs/bible/algorithms.md; E-17 R-114-01..04).

ALG-71: "Per instantiated node: chokepoint obstacle (0.85, 600), staging obstacle (0.60, 800), vantage elevation
(0.90, 700), hazard anchor interference (0.75, 500), flank obstacle (0.35, 450) and cover (0.40, 450), chokepoint cover
(0.55, 550), objective cover (0.50, 400), hazard cover (0.35, 400) (GRADIENT_*). Layer masks: for a zone with
layer_restrictions, one layer_block_N source per layer not listed, radius LAYER_MASK_RADIUS = 600, intensity 1.0;
accessibility at a point is open unless the sampled block value >= 0.5."

Pairs are (intensity, radius). Node ids follow the E-17 S-113 type list order (objective 0, staging 1, transit 2,
chokepoint 3, flank_route 4, vantage 5, hazard_anchor 6, spawn_point 7, extraction 8); gradient ids follow the
OMGradientProperties field order (obstacle 0, cover 1, interference 2, elevation 3), the order the existing
test_R_114_03 uses for 0, 2 and 3. The cover id 1 is the one inferred value (signatures.toml marks the pair "likely").

Every red test here is the E-17 map generator being a STUB (SL-C3-05 in
docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md); the control below is green today.

Positive control: a (node, gradient) pair that ALG-71 does not list has no source, so its intensity is 0.0 -- the reader
works today, and it separates "not listed" from "listed".
"""
import ctypes

import pytest

OBJECTIVE, STAGING, TRANSIT, CHOKEPOINT, FLANK_ROUTE, VANTAGE, HAZARD_ANCHOR = 0, 1, 2, 3, 4, 5, 6
OBSTACLE, COVER, INTERFERENCE, ELEVATION = 0, 1, 2, 3
LAYER_MASK_RADIUS = 600.0

TABLE = [
    (CHOKEPOINT, OBSTACLE, 0.85, 600.0),
    (STAGING, OBSTACLE, 0.60, 800.0),
    (VANTAGE, ELEVATION, 0.90, 700.0),
    (HAZARD_ANCHOR, INTERFERENCE, 0.75, 500.0),
    (FLANK_ROUTE, OBSTACLE, 0.35, 450.0),
    (FLANK_ROUTE, COVER, 0.40, 450.0),
    (CHOKEPOINT, COVER, 0.55, 550.0),
    (OBJECTIVE, COVER, 0.50, 400.0),
    (HAZARD_ANCHOR, COVER, 0.35, 400.0),
]


@pytest.mark.parametrize("node,gradient,intensity,radius", TABLE)
def test_ALG_71_anchor_intensity_and_radius(lib, node, gradient, intensity, radius):
    assert lib.om_gradient_get_anchor_intensity(node, gradient) == pytest.approx(intensity)
    assert lib.om_gradient_get_anchor_radius(node, gradient) == pytest.approx(radius)


def test_control_ALG_71_a_pair_that_is_not_listed_has_no_source(lib):
    listed = {(n, g) for n, g, _, _ in TABLE}
    for node in (TRANSIT, STAGING, VANTAGE):
        for gradient in (OBSTACLE, COVER, INTERFERENCE, ELEVATION):
            if (node, gradient) in listed:
                continue
            assert lib.om_gradient_get_anchor_intensity(node, gradient) == 0.0
            assert lib.om_gradient_get_anchor_radius(node, gradient) == 0.0


def test_ALG_71_layer_mask_blocks_every_layer_not_listed_within_600(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_map_add_layer_restriction_zone(w, 1000.0, 1000.0, 0)  # the zone lists layer 0 only
    assert lib.om_map_sample_layer_accessibility(w, 1000.0, 1000.0, 1) == 0  # intensity 1.0 >= 0.5 at the centre
    assert lib.om_map_sample_layer_accessibility(w, 1000.0, 1000.0, 0) == 1  # a listed layer stays open
    assert lib.om_map_sample_layer_accessibility(w, 1000.0 + LAYER_MASK_RADIUS + 1.0, 1000.0, 1) == 1  # beyond the radius


def test_control_ALG_71_with_no_zone_every_layer_is_open_at_the_same_point(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_sample_layer_accessibility(w, 1000.0, 1000.0, 1) == 1
