"""F5 window control for csrc/tactical_move.c (E-13, wave 2 card B12).

Rule (docs/bible/algorithms.md ALG-67 "Routing"): "Grid cells NAVMESH_CELL_SIZE
= 100 per layer; blocked where obstacle density > NAVMESH_OBSTACLE_THRESHOLD
= 0.7." om_navmesh_get_cell_size must read back exactly 100.0.

PLANT: under OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT, om_navmesh_get_cell_size
returns NAVMESH_CELL_SIZE scaled by NAVMESH_OBSTACLE_THRESHOLD instead of the
constant itself: 100.0 * 0.7 = 70.0.

Uses id 1101: 1100 (OM_BUG_MOVE_RUBBERBAND) is already spoken for by
tests/qa/t1/test_rts_detectors.py's own local enum (Q2), per the two-day-push
brief's decision 6.
"""
import pytest

from conftest import OMBugE13


def test_control_navmesh_cell_size_wrong_constant_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE13.NAVMESH_CELL_SIZE_WRONG_CONSTANT)

    cell_size = dbg.om_navmesh_get_cell_size(w)

    assert cell_size == pytest.approx(70.0, abs=1e-9), (
        "OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT injected but the cell size "
        "still reads the correct NAVMESH_CELL_SIZE (100.0) instead of the "
        "obstacle-threshold-scaled 70.0 -- the detector did not trip"
    )
