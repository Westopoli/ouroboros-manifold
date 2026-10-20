# spec: Architect ruling A187 item 1 (slots kept for wide shapes) - scripts/skilllab/fight.py (real engine)
"""A Vanguard line keeps distinct slot destinations through the real engine: before the fix all sat on one point."""
import dataclasses
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _destinations(library, n, per_unit=False):
    setup = plays.line_play(n)(n, False)
    setup = dataclasses.replace(setup, orders_per_unit=per_unit)      # spelled out: L4 flipped the Setup default to False
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        library.set_param(w, library.param_id("OM_TP_PURSUE_BY_STEERING"), 1.0)
        types = fight._register_types(library, w, setup)
        rng, ids, ranges = random.Random(0), {}, {}
        for side in (0, 1):
            fight._spawn_side(library, w, setup, side, types, rng, ids, ranges)
        fight._issue_orders(library, w, setup, ids)
        return [library.unit_destination(w, u) for u in ids[0]]
    finally:
        library.free_world(w)


@pytest.mark.parametrize("n,spread", [(32, 800), (16, 400)])
def test_line_destinations_are_distinct_and_spread(library, n, spread):
    dests = _destinations(library, n)   # LAB-REV2-L2: the group order (orders_per_unit False) is the one that keeps slots
    assert all(d is not None for d in dests)
    assert len(set(dests)) == n
    ys = [d[1] for d in dests]
    assert max(ys) - min(ys) > spread


@pytest.mark.parametrize("n", [16, 32])
def test_per_unit_orders_all_head_for_the_shared_point(library, n):
    """LAB-REV2-L2 (ruling 6, Q-LAB-03): with orders_per_unit=True it is one attack-move per unit to Setup.point, so every destination
    is that point (the control for the slot test above, which asks for the group order). LAB-REV2 flip ruler (TD-LAB-REV2-flip, decision 40): the
    default is now the group order, so this test asks for the per-unit order explicitly."""
    setup = plays.line_play(n)(n, False)
    assert setup.orders_per_unit is False and setup.point is not None
    dests = _destinations(library, n, per_unit=True)
    assert all(d is not None for d in dests)
    assert set(dests) == {tuple(float(v) for v in setup.point)}
