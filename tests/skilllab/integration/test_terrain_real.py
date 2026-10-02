# spec: docs/northstar/plans/push/pp_contract.md::section 5 (om_map_set_canvas, om_map_block_rect, om_map_add_cover); plan Phase S item 5a
"""Terrain through the production library: a canvas, one block and one cover apply and the fight is repeatable.

The second test needs engine behaviour that is not built yet (block_rect is an inert stub).
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Block, Cover, Terrain  # noqa: E402
from scripts.skilllab.plays import blob_play  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402

CANVAS = (4000.0, 4000.0)
COVER = Cover(0.0, 600.0, 60.0, 1)
BLOCK = Block(-15.0, -400.0, 15.0, 400.0, 0, 4)     # across the line between the sides, in play coordinates


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def setup_for(terrain):
    s = with_terrain(blob_play(8), terrain)(8, False)
    return dataclasses.replace(s, max_ticks=600)


def test_a_fight_on_a_canvas_with_one_cover_and_one_block_applies_and_repeats(library):
    """Canvas 4000x4000 with a cover and a block: no exception, and two runs of the same seed are equal."""
    s = setup_for(Terrain(canvas=CANVAS, blocks=(BLOCK,), covers=(COVER,)))
    first, second = fight.fight(s, 1, False, engine=library), fight.fight(s, 1, False, engine=library)
    assert first.ticks > 0 and first == second


def test_a_block_across_the_line_between_the_sides_changes_the_fight(library):
    """EXPECTED RED until the engine map wave lands (A144: held, not landed).
    The same fight with and without the block gives a different firing series."""
    with_block = fight.fight(setup_for(Terrain(canvas=CANVAS, blocks=(BLOCK,), covers=(COVER,))), 1, False,
                             engine=library)
    without = fight.fight(setup_for(Terrain(canvas=CANVAS, covers=(COVER,))), 1, False, engine=library)
    assert with_block.firing != without.firing
