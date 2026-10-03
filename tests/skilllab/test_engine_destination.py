# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S (trace states, order ends)
"""Engine.unit_destination against the real library: None without an order, a tuple after a move order."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.engine import Engine  # noqa: E402


@pytest.fixture(scope="module")
def engine():
    return Engine()


def test_destination_none_then_tuple_then_none_again(engine):
    w = engine.new_world(0)
    try:
        u = engine.spawn(w, engine.type_id("Vanguard"), 0, 100.0, 100.0, 0)
        assert engine.unit_destination(w, u) is None
        engine.order_move(w, [u], 400.0, 100.0)
        dest = engine.unit_destination(w, u)
        assert isinstance(dest, tuple) and len(dest) == 2
        assert dest == pytest.approx((400.0, 100.0), abs=1.0)
        engine.clear_orders(w, [u])
        assert engine.unit_destination(w, u) is None
    finally:
        engine.free_world(w)
