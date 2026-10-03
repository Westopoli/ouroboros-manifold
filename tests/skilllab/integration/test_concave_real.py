# spec: Architect ruling A187 follow-up - the concave's focus lands on the goal (scripts/skilllab/fight.py, real engine)
"""Through the real engine the skilled Vanguard arc's destinations ring the enemy's first anchor at the arc radius."""
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def test_concave_destinations_ring_the_enemy_anchor(library):
    setup = asym_play(16, Side("skilled"), Side("blob"))(16, False)
    enemy = [g for g in setup.groups if g.side == 1][0]
    t = (enemy.x, enemy.y)
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        library.set_param(w, library.param_id("OM_TP_PURSUE_BY_STEERING"), 1.0)
        types = fight._register_types(library, w, setup)
        rng, ids, ranges = random.Random(0), {}, {}
        for side in (0, 1):
            fight._spawn_side(library, w, setup, side, types, rng, ids, ranges)
        fight._issue_orders(library, w, setup, ids)
        dests = [library.unit_destination(w, u) for u in ids[0]]
    finally:
        library.free_world(w)
    radius = 150 + 12 * math.sqrt(16)
    assert len(dests) == 16 and all(d is not None for d in dests)
    for d in dests:
        assert abs(math.hypot(d[0] - t[0], d[1] - t[1]) - radius) <= 40
