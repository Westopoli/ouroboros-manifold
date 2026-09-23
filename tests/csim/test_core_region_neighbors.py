import ctypes

from conftest import OMEdge, set_edge


def _bind_region_neighbors(lib):
    if getattr(lib, "_core_region_neighbors_bound", False):
        return
    lib.om_region_neighbors.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
    ]
    lib.om_region_neighbors.restype = ctypes.c_uint32
    lib._core_region_neighbors_bound = True


def _neighbors(lib, w, idx, max_records):
    _bind_region_neighbors(lib)
    buf = (ctypes.c_uint32 * max_records)(*([0xFFFFFFFF] * max_records))
    n = lib.om_region_neighbors(w, idx, buf, max_records)
    return n, buf


def test_neighbors_ascending_order_and_undirected_with_untouched_tail(lib, world_factory):
    w = world_factory(n_regions=12, seed=1)
    set_edge(lib, w, 5, 2, OMEdge.BORDER)
    set_edge(lib, w, 5, 9, OMEdge.BORDER)
    set_edge(lib, w, 0, 5, OMEdge.BORDER)

    n, buf = _neighbors(lib, w, 5, 8)
    assert n == 3
    assert list(buf[:3]) == [0, 2, 9]
    assert list(buf[3:]) == [0xFFFFFFFF] * 5

    n2, buf2 = _neighbors(lib, w, 2, 8)
    assert n2 == 1
    assert buf2[0] == 5


def test_neighbors_count_exceeds_max_buffer_still_reports_true_total(lib, world_factory):
    w = world_factory(n_regions=12, seed=2)
    set_edge(lib, w, 5, 2, OMEdge.BORDER)
    set_edge(lib, w, 5, 9, OMEdge.BORDER)
    set_edge(lib, w, 0, 5, OMEdge.BORDER)

    n, buf = _neighbors(lib, w, 5, 1)
    assert n == 3
    assert buf[0] == 0


def test_neighbors_out_of_range_idx_and_no_edges_region_return_zero(lib, world_factory):
    w = world_factory(n_regions=12, seed=3)
    set_edge(lib, w, 5, 2, OMEdge.BORDER)

    n, buf = _neighbors(lib, w, 5, 8)
    assert n == 1
    assert buf[0] == 2

    n2, buf2 = _neighbors(lib, w, 12, 4)
    assert n2 == 0
    assert list(buf2) == [0xFFFFFFFF] * 4

    n3, _ = _neighbors(lib, w, 999999, 4)
    assert n3 == 0

    n4, _ = _neighbors(lib, w, 7, 8)
    assert n4 == 0
