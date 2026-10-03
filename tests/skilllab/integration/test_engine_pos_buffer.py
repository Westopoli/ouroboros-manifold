# spec: Architect speed brief, change 2 (unit_pos reuses one buffer, returns fresh tuples)
"""Real library: unit_pos never aliases between calls and matches the two-c_double reference."""
import ctypes
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def reference_pos(library, w, u):
    x, y = ctypes.c_double(), ctypes.c_double()
    library._lib.om_unit_get_pos(w, int(u), ctypes.byref(x), ctypes.byref(y))
    return (float(x.value), float(y.value))


def test_fresh_tuples_of_floats_and_no_aliasing(library):
    w = library.new_world(0)
    try:
        t = library.type_id("Vanguard")
        a = library.spawn(w, t, 0, 100.0, 200.0, 0)
        b = library.spawn(w, t, 1, -300.0, 50.0, 0)
        p1 = library.unit_pos(w, a)
        p2 = library.unit_pos(w, b)
        p3 = library.unit_pos(w, a)
        assert p1 != p2 and p1 == p3 and p1 is not p3
        for p in (p1, p2, p3):
            assert type(p) is tuple and len(p) == 2 and all(type(v) is float for v in p)
        assert p1 == (100.0, 200.0) and p2 == (-300.0, 50.0)
    finally:
        library.free_world(w)


def test_positions_match_the_two_c_double_reference_over_five_ticks(library):
    w = library.new_world(0)
    try:
        t = library.type_id("Vanguard")
        a = library.spawn(w, t, 0, 0.0, 0.0, 0)
        b = library.spawn(w, t, 1, 500.0, 0.0, 0)
        library.order_move(w, [a], 400.0, 100.0)
        moved = set()
        for _ in range(5):
            library.step(w)
            for u in (a, b):
                assert library.unit_pos(w, u) == reference_pos(library, w, u)
            moved.add(library.unit_pos(w, a))
        assert len(moved) > 1, "the unit never moved, so the comparison proved nothing"
    finally:
        library.free_world(w)
