import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from tactical_map import SpineNode, CoverPolygon
from layout_instantiator import InstantiatedLayout
from gradient_placer import place_cover_polygons


def _make_inst(spine_nodes):
    return InstantiatedLayout(
        layout_id="test",
        canvas_size="medium",
        canvas_w=2000,
        canvas_h=2000,
        seed=0,
        spine_nodes=spine_nodes,
        node_id_map={},
        edges=[],
    )


def test_single_chokepoint_emits_one_polygon_12_vertices():
    node = SpineNode(position=(500.0, 500.0), node_type="chokepoint")
    inst = _make_inst([node])

    polys = place_cover_polygons(inst)

    assert len(polys) == 1
    assert isinstance(polys[0], CoverPolygon)
    assert polys[0].polygon_id == 0
    assert len(polys[0].vertices) == 12
    r = config.GRADIENT_CHOKEPOINT_COVER_RADIUS
    for (vx, vy) in polys[0].vertices:
        dx = vx - 500.0
        dy = vy - 500.0
        dist = math.sqrt(dx * dx + dy * dy)
        assert dist <= r * 1.001


def test_chokepoint_plus_objective_emits_two_polygons_with_sequential_ids():
    n1 = SpineNode(position=(300.0, 300.0), node_type="chokepoint")
    n2 = SpineNode(position=(1500.0, 1500.0), node_type="objective")
    inst = _make_inst([n1, n2])

    polys = place_cover_polygons(inst)

    assert len(polys) == 2
    ids = sorted(p.polygon_id for p in polys)
    assert ids == [0, 1]


def test_vantage_only_emits_no_polygons():
    node = SpineNode(position=(500.0, 500.0), node_type="vantage")
    inst = _make_inst([node])

    polys = place_cover_polygons(inst)

    assert polys == []


def test_all_vertices_within_radius_tolerance():
    node = SpineNode(position=(1000.0, 1000.0), node_type="objective")
    inst = _make_inst([node])

    polys = place_cover_polygons(inst)
    r = config.GRADIENT_OBJECTIVE_COVER_RADIUS
    for (vx, vy) in polys[0].vertices:
        dist = math.sqrt((vx - 1000.0) ** 2 + (vy - 1000.0) ** 2)
        assert dist <= r * 1.001


def test_vertices_is_list_of_tuples():
    node = SpineNode(position=(500.0, 500.0), node_type="staging")
    inst = _make_inst([node])

    polys = place_cover_polygons(inst)

    assert isinstance(polys[0].vertices, list)
    for v in polys[0].vertices:
        assert isinstance(v, tuple)
        assert len(v) == 2
        assert isinstance(v[0], float)
        assert isinstance(v[1], float)
