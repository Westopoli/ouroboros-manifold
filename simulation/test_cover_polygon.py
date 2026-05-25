from tactical_map import CoverPolygon, TacticalMap


def _square(polygon_id, x0, y0, x1, y1):
    return CoverPolygon(polygon_id, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def test_cover_polygon_construction():
    p = CoverPolygon(7, [(0, 0), (10, 0), (10, 10), (0, 10)])
    assert p.polygon_id == 7
    assert len(p.vertices) == 4


def test_empty_tactical_map_has_no_cover():
    tm = TacticalMap(width=1000, height=1000)
    assert tm.cover_polygons == []
    assert tm.is_in_cover(5, 5) is False
    assert tm.cover_polygon_containing(5, 5) is None


def test_single_polygon_interior_point():
    tm = TacticalMap(width=1000, height=1000, cover_polygons=[_square(1, 0, 0, 100, 100)])
    assert tm.is_in_cover(50, 50) is True
    assert tm.cover_polygon_containing(50, 50) == 1


def test_point_outside_all_polygons():
    tm = TacticalMap(width=1000, height=1000, cover_polygons=[_square(1, 0, 0, 100, 100)])
    assert tm.is_in_cover(200, 200) is False
    assert tm.cover_polygon_containing(200, 200) is None


def test_two_disjoint_polygons_disambiguate_by_id():
    tm = TacticalMap(
        width=1000,
        height=1000,
        cover_polygons=[
            _square(1, 0, 0, 100, 100),
            _square(2, 200, 200, 300, 300),
        ],
    )
    assert tm.cover_polygon_containing(50, 50) == 1
    assert tm.cover_polygon_containing(250, 250) == 2
    assert tm.cover_polygon_containing(150, 150) is None


def test_point_on_edge_counts_as_inside():
    tm = TacticalMap(width=1000, height=1000, cover_polygons=[_square(1, 0, 0, 100, 100)])
    assert tm.is_in_cover(0, 50) is True
    assert tm.cover_polygon_containing(0, 50) == 1


def test_non_convex_l_shape():
    # L-shape: outer bounding (0,0)-(100,100); missing rect (50,50)-(100,100).
    # Vertices clockwise: (0,0) -> (100,0) -> (100,50) -> (50,50) -> (50,100) -> (0,100).
    l_shape = CoverPolygon(
        9,
        [(0, 0), (100, 0), (100, 50), (50, 50), (50, 100), (0, 100)],
    )
    tm = TacticalMap(width=1000, height=1000, cover_polygons=[l_shape])
    # Inner corner area of L (lower-left arm): inside.
    assert tm.is_in_cover(25, 75) is True
    assert tm.cover_polygon_containing(25, 75) == 9
    # "Missing" upper-right rectangle: outside.
    assert tm.is_in_cover(75, 75) is False
    assert tm.cover_polygon_containing(75, 75) is None
