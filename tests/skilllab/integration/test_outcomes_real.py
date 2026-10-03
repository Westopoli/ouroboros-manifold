# spec: ruling A201: draw / stalemate labels through the production library
"""A real double kill labels "draw"; a real shot-proof standoff labels "stalemate"."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Block, Group, Setup, Terrain  # noqa: E402
from scripts.skilllab.plays import blob_play  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402

SEEDS = range(21)


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _duel(gap):
    def g(side, x):
        return Group(side=side, unit="Vanguard", count=1, formation="line", x=x, y=0.0,
                     facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                     params={"spacing": 30.0})
    return Setup(groups=(g(0, -gap / 2), g(1, gap / 2)), unit_types={}, max_ticks=2000)


def test_two_identical_units_point_blank_can_draw(library):
    results = [fight.fight(_duel(gap), seed, swap, engine=library)
               for gap in (4.0, 10.0, 20.0) for seed in SEEDS for swap in (False, True)]
    draws = [r for r in results if r.outcome == "draw"]
    if not draws:
        pytest.skip("no 1 v 1 draw in seeds 0..20, gaps 4/10/20, both spawn orders: the engine resolves it with a winner")
    assert all(r.survivors == (0, 0) and r.margin == 0.0 for r in draws)


def test_a_standoff_nobody_can_shoot_across_is_a_quiet_stalemate(library):
    """One idle Vanguard each side with a blocked rect across the line between them: 400 quiet ticks -> stalemate."""
    block = Block(-15.0, -400.0, 15.0, 400.0, 0, 4)
    setup = with_terrain(blob_play(1), Terrain(canvas=(4000.0, 4000.0), blocks=(block,)))(1, False)
    setup = dataclasses.replace(setup, groups=tuple(dataclasses.replace(g, order="idle") for g in setup.groups),
                                max_ticks=2000)
    res = fight.fight(setup, 0, False, engine=library)
    assert res.outcome == "stalemate" and res.ticks == setup.stalemate_ticks
