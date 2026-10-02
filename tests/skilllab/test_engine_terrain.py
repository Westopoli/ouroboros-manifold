# spec: docs/northstar/plans/push/pp_contract.md::section 5 (om_map_set_canvas, om_map_block_rect, om_map_add_cover)
"""Engine.set_canvas, block_rect and add_cover against a fake ctypes library (no compiler, no real library).

The Engine is built without loading a library (Engine.__new__), its `_lib` replaced by a fake whose every
attribute is a recording function; `_bind()` then sets argtypes/restype on it, exactly as it would on the real one.
"""
import ctypes
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.engine import Engine  # noqa: E402

V, D, U32, I = ctypes.c_void_p, ctypes.c_double, ctypes.c_uint32, ctypes.c_int


class Fn:
    def __init__(self):
        self.argtypes = self.restype = None
        self.returns = 0
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.returns


class FakeLib:
    def __init__(self):
        self._fns = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._fns.setdefault(name, Fn())


@pytest.fixture
def eng():
    e = Engine.__new__(Engine)
    e._lib = FakeLib()
    e._bind()
    return e


W = ctypes.c_void_p(1234)


def test_the_three_terrain_symbols_are_bound_exactly_as_the_header_declares(eng):
    """argtypes and restype: canvas (V,d,d)->int, block_rect (V,d,d,d,d,u32,u32)->int, cover (V,d,d,d,d)->u32."""
    lib = eng._lib
    assert (lib.om_map_set_canvas.argtypes, lib.om_map_set_canvas.restype) == ([V, D, D], I)
    assert (lib.om_map_block_rect.argtypes, lib.om_map_block_rect.restype) == ([V, D, D, D, D, U32, U32], I)
    assert (lib.om_map_add_cover.argtypes, lib.om_map_add_cover.restype) == ([V, D, D, D, D], U32)


def test_set_canvas_passes_floats_and_accepts_zero(eng):
    """A 0 return is success: no raise, and the call carried the world and both sides as floats."""
    eng.set_canvas(W, 4000, 3000)
    (args,) = eng._lib.om_map_set_canvas.calls
    assert args == (W, 4000.0, 3000.0) and all(isinstance(a, float) for a in args[1:])


def test_block_rect_passes_floats_and_int_layers_and_accepts_zero(eng):
    """Coordinates go as floats, layers as ints, in header order."""
    eng.block_rect(W, 1, 2, 3, 4, 0, 4)
    (args,) = eng._lib.om_map_block_rect.calls
    assert args == (W, 1.0, 2.0, 3.0, 4.0, 0, 4)
    assert all(isinstance(a, float) for a in args[1:5]) and all(isinstance(a, int) for a in args[5:])


def test_add_cover_returns_the_engine_index_as_an_int(eng):
    """The 1-based index comes back as a Python int; the height goes to the library as a float."""
    eng._lib.om_map_add_cover.returns = 3
    got = eng.add_cover(W, 5, 6, 7, 2)
    (args,) = eng._lib.om_map_add_cover.calls
    assert got == 3 and isinstance(got, int) and args == (W, 5.0, 6.0, 7.0, 2.0)
    assert all(isinstance(a, float) for a in args[1:])


@pytest.mark.parametrize("name,call,symbol", [
    ("set_canvas", lambda e: e.set_canvas(W, -1.0, 10.0), "om_map_set_canvas"),
    ("block_rect", lambda e: e.block_rect(W, 0, 0, 1, 1, 0, 9), "om_map_block_rect"),
])
@pytest.mark.parametrize("rc", [-1, 1])
def test_a_nonzero_return_raises_valueerror_naming_the_call(eng, name, call, symbol, rc):
    """set_canvas and block_rect refuse with ValueError whose message names the call; any nonzero return counts."""
    getattr(eng._lib, symbol).returns = rc
    with pytest.raises(ValueError, match=name):
        call(eng)


def test_add_cover_returning_zero_raises_valueerror_naming_the_call(eng):
    """add_cover's refusal is a 0 index: ValueError naming add_cover. Control: index 1 does not raise."""
    eng._lib.om_map_add_cover.returns = 1
    assert eng.add_cover(W, 0, 0, 5, 1) == 1
    eng._lib.om_map_add_cover.returns = 0
    with pytest.raises(ValueError, match="add_cover"):
        eng.add_cover(W, 0, 0, 5, 9)


def test_the_binding_is_deterministic(eng):
    """The same calls on a fresh fake library give the same recorded arguments."""
    def run():
        e = Engine.__new__(Engine)
        e._lib = FakeLib()
        e._bind()
        e._lib.om_map_add_cover.returns = 1
        e.set_canvas(W, 10, 20)
        e.block_rect(W, 1, 2, 3, 4, 0, 1)
        e.add_cover(W, 1, 2, 3, 1)
        return [f.calls for f in (e._lib.om_map_set_canvas, e._lib.om_map_block_rect, e._lib.om_map_add_cover)]

    assert run() == run()
