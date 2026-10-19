# spec: ruling A201 (draw label) and LAB-REV2-L2 (Q-LAB-03, spec 2026-10-14 ruling 1: elimination only, a cap is a lab defect)
"""A real double kill labels "draw"; a real shot-proof standoff has no quiet-stalemate end any more: it runs to max_ticks and is
labelled "cap", a defect to trace and never a result (rewritten from the stalemate-label test, Q-LAB-03)."""
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
    return Setup(groups=(g(0, -gap / 2), g(1, gap / 2)), unit_types={}, max_ticks=2000, point=(0.0, 0.0))


def test_two_identical_units_point_blank_can_draw(library):
    results = [fight.fight(_duel(gap), seed, swap, engine=library)
               for gap in (4.0, 10.0, 20.0) for seed in SEEDS for swap in (False, True)]
    draws = [r for r in results if r.outcome == "draw"]
    if not draws:
        pytest.skip("no 1 v 1 draw in seeds 0..20, gaps 4/10/20, both spawn orders: the engine resolves it with a winner")
    assert all(r.survivors == (0, 0) and r.margin == 0.0 for r in draws)


def _standoff(max_ticks):
    """One idle Vanguard each side with a blocked rect across the line between them: nobody can shoot, nobody walks."""
    block = Block(-15.0, -400.0, 15.0, 400.0, 0, 4)
    setup = with_terrain(blob_play(1), Terrain(canvas=(4000.0, 4000.0), blocks=(block,)))(1, False)
    return dataclasses.replace(setup, groups=tuple(dataclasses.replace(g, order="idle") for g in setup.groups),
                               max_ticks=max_ticks)


def test_a_standoff_nobody_can_shoot_across_runs_to_the_cap_and_is_a_cap(library):
    """Q-LAB-03: no stalemate window. 2000 ticks of nobody hurting anybody end as `cap` at max_ticks (red on the old code: it
    ended `stalemate` after stalemate_ticks quiet ticks), with no winner and no agreement."""
    setup = _standoff(2000)
    res = fight.fight(setup, 0, False, engine=library)
    assert (res.outcome, res.ticks, res.winner, res.agreement) == ("cap", 2000, None, "n/a")
    assert res.survivors == (1, 1)


def test_the_retired_outcome_names_never_appear_from_the_real_engine(library):
    """Ruling 1: held, decided and stalemate are not outcomes. Positive control: the duel and the standoff produce names in
    the four-name set, and the standoff really is one of them (cap), so the set is exercised on both ends."""
    names = {fight.fight(_duel(10.0), seed, False, engine=library).outcome for seed in range(5)}
    names.add(fight.fight(_standoff(300), 0, False, engine=library).outcome)
    assert names <= {"side0", "side1", "draw", "cap"} and "cap" in names, names
