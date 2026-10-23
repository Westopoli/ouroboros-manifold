# spec: batch runner spec addendum 4 (batch4_spec.md) section 2 - phase_b_choke through the production library
"""Phase B choke, 8 defenders against 8 attackers, through fight.fight twice.

If om_map_block_rect is still an inert stub in this build the engine may ignore the walls, so this asserts only
determinism, spawn positions and that the fight runs.

LAB-REV2-L4 ruler (TD-LAB-REV2-L4-layers): test_layers_batch_has_the_choke_phase_b_cells is retired with the `layers` batch (tables
LA, LB and LC are deleted by L4)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402
from scripts.skilllab.scenes import phase_b_choke  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _setup():
    return dataclasses.replace(phase_b_choke(8)(8, False), max_ticks=300)


def test_phase_b_choke_fight_runs_twice_with_identical_results(library):
    s = _setup()
    first, second = fight.fight(s, 1, False, engine=library), fight.fight(s, 1, False, engine=library)
    assert first.ticks > 0 and first.heads == (8, 8)
    assert first == second


def test_spawn_positions_are_inside_the_canvas(library):
    s = _setup()
    w, h = s.terrain.canvas
    pts = [p for g in s.groups for p in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    assert len(pts) == 16
    assert all(0 <= x <= w and 0 <= y <= h for x, y in pts)


def test_a_replicate_with_swap_also_runs(library):
    r = fight.fight(_setup(), 2, True, engine=library)
    assert r.ticks > 0 and r.heads == (8, 8)

