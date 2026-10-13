"""ALG-70 Layout selection and instantiation (docs/bible/algorithms.md; E-17 R-112-01..06, R-116-01..02, Q-118-01).

ALG-70: "Candidates = layouts whose tags satisfy any of the archetype's compatibility filters; one uniform draw. Zone
positions (percent of canvas) scale to the canvas, jittered by up to LAYOUT_JITTER_PERCENT = 0.03 of canvas per zone.
Canvas dimension is a uniform draw in CANVAS_SIZE_RANGES ... for the archetype's base category (see Q-118-01). Shipped
library on 2026-09-10: 8 layouts; per archetype: defensive_stand 3, assault 5, multi_front_defense 2, containment 2,
every other archetype 1 (see Q-112-01)."

Archetype ids follow the E-10 S-073 table row order: 0 defensive stand, 1 siege breaking, 2 reconquest, 3 assault,
4 suppression, 5 multi-front defense, 6 interception, 7 rear guard, 8 containment, 9 counterinsurgency.

The canvas sentence is read through Q-118-01 (closed (a), Westley 2026-09-12): base 8000 / 16000 / 24000 shifted by up
to 30 percent of the base by the region's field, direction per R-116-02; the uniform-range draw of the ALG text is the
superseded half (SL-C3-04). Findings for the red tests: SL-C3-05 (docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md).

Positive control: test_control_* uses the same entry point on the side of the rule that holds today.
"""
import ctypes
import math

import pytest

LAYOUT_JITTER_PERCENT = 0.03
DEFENSIVE_STAND, SIEGE, RECONQUEST, ASSAULT, SUPPRESSION, MULTI_FRONT, INTERCEPTION, REAR_GUARD, CONTAINMENT, CI = range(10)
CATEGORY = {DEFENSIVE_STAND: 1, SIEGE: 2, RECONQUEST: 1, ASSAULT: 2, SUPPRESSION: 0, MULTI_FRONT: 2,
            INTERCEPTION: 1, REAR_GUARD: 1, CONTAINMENT: 2, CI: 0}  # 0 small, 1 medium, 2 large (S-073 Canvas column)
BASE = {0: 8000.0, 1: 16000.0, 2: 24000.0}  # Q-118-01 (a)
SHIPPED_PER_ARCHETYPE = {DEFENSIVE_STAND: 3, ASSAULT: 5, MULTI_FRONT: 2, CONTAINMENT: 2}


class _Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


def test_ALG_70_the_shipped_library_holds_8_layouts(lib):
    assert lib.om_map_library_total_layouts() == 8


@pytest.mark.parametrize("archetype", range(10))
def test_ALG_70_compatible_layouts_per_archetype(lib, world_factory, archetype):
    w = world_factory(n_regions=1)
    expected = SHIPPED_PER_ARCHETYPE.get(archetype, 1)
    assert lib.om_map_get_compatible_layout_count(w, archetype) == expected


def test_ALG_70_one_uniform_draw_over_the_compatible_pool(lib):
    pool = 4
    seen = {lib.om_map_select_layout_uniform(seed, pool) for seed in range(400)}
    assert seen <= set(range(pool))
    assert seen == set(range(pool))  # 400 seeds over 4 layouts reach every layout


def test_control_ALG_70_a_pool_of_one_always_picks_that_layout(lib):
    assert {lib.om_map_select_layout_uniform(seed, 1) for seed in range(50)} == {0}


@pytest.mark.parametrize("seed", [1, 7, 12345, 2**40 + 3])
def test_ALG_70_zone_position_is_the_percent_of_canvas_jittered_by_at_most_3_percent(lib, seed):
    canvas = 10000.0
    out = _Vec2()
    lib.om_map_instantiate_zone_pos(0.50, 0.25, canvas, seed, ctypes.byref(out))
    assert abs(out.x - 0.50 * canvas) <= LAYOUT_JITTER_PERCENT * canvas
    assert abs(out.y - 0.25 * canvas) <= LAYOUT_JITTER_PERCENT * canvas


def test_ALG_70_zone_jitter_is_drawn_not_constant(lib):
    xs = set()
    for seed in range(20):
        out = _Vec2()
        lib.om_map_instantiate_zone_pos(0.50, 0.25, 10000.0, seed, ctypes.byref(out))
        xs.add(round(out.x, 6))
    assert len(xs) > 1


def test_control_ALG_70_an_out_of_band_position_is_detected(lib):
    # The band check itself: 4 percent of a 10000 canvas is outside the 3 percent jitter.
    assert abs(0.54 * 10000.0 - 0.50 * 10000.0) > LAYOUT_JITTER_PERCENT * 10000.0


@pytest.mark.parametrize("archetype", range(10))
def test_ALG_70_canvas_base_category_follows_the_S073_table(lib, archetype):
    assert lib.om_map_archetype_canvas_category(archetype) == CATEGORY[archetype]
    assert lib.om_map_compute_modified_canvas(archetype, 50.0, 50.0) == pytest.approx(BASE[CATEGORY[archetype]])


@pytest.mark.parametrize("archetype,economy,tension,direction_field", [
    (DEFENSIVE_STAND, 100.0, 50.0, +1.0),   # grows with wealth
    (DEFENSIVE_STAND, 0.0, 50.0, -1.0),
    (SUPPRESSION, 50.0, 100.0, -1.0),       # shrinks with tension
    (SUPPRESSION, 50.0, 0.0, +1.0),
    (CI, 50.0, 100.0, +1.0),                # grows with tension
    (CI, 50.0, 0.0, -1.0),
])
def test_ALG_70_canvas_shifts_30_percent_of_base_with_the_field(lib, archetype, economy, tension, direction_field):
    expected = BASE[CATEGORY[archetype]] * (1.0 + 0.30 * direction_field)
    assert lib.om_map_compute_modified_canvas(archetype, economy, tension) == pytest.approx(expected)


def test_control_ALG_70_canvas_midpoint_is_unmodified_and_the_extremes_differ(lib):
    mid = lib.om_map_compute_modified_canvas(DEFENSIVE_STAND, 50.0, 50.0)
    assert lib.om_map_compute_modified_canvas(DEFENSIVE_STAND, 100.0, 50.0) != pytest.approx(mid)
    assert math.isclose(mid, 16000.0)
