# spec: Architect speed brief, change 1 (a hp-driven living set equals the engine's)
"""Real library: unit_alive == (unit_hp > 0) for every unit at every tick of a 16 v 12 blob fight."""
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


def test_unit_alive_equals_hp_positive_at_every_tick(library):
    setup = plays.blob_play(16)(12, False)
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        library.set_param(w, library.param_id("OM_TP_PURSUE_BY_STEERING"), 1.0)
        types = fight._register_types(library, w, setup)
        rng, ids, ranges = random.Random(0), {}, {}
        for side in (0, 1):
            fight._spawn_side(library, w, setup, side, types, rng, ids, ranges)
        fight._issue_orders(library, w, setup, ids)
        sides = [[u for gi, g in enumerate(setup.groups) if g.side == s for u in ids[gi]] for s in (0, 1)]
        everyone, deaths = sides[0] + sides[1], 0
        for _ in range(1000):
            for u in everyone:
                assert library.unit_alive(w, u) == (library.unit_hp(w, u) > 0), u
            deaths = sum(1 for u in everyone if not library.unit_alive(w, u))
            if any(all(library.unit_hp(w, u) <= 0 for u in side) for side in sides):
                break
            library.step(w)
        assert deaths > 0, "no unit died, so the dead half of the equality was never exercised"
    finally:
        library.free_world(w)
