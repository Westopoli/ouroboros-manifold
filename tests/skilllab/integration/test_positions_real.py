# spec: batch runner spec addendum 3 (batch3_spec.md) - scripts/skilllab/positions.py (real engine)
"""Each position play at 4 units against 4, 400 ticks: its Steps fire at the stated ticks, and two runs are identical."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, positions  # noqa: E402

PLAYS = {"bait": positions.bait_play, "ambush": positions.ambush_play, "fall_back": positions.fall_back_play}


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _setup(name):
    return dataclasses.replace(PLAYS[name](4)(4, False), max_ticks=400)


@pytest.mark.parametrize("name", sorted(PLAYS))
def test_steps_fire_at_their_ticks(library, name):
    setup = _setup(name)
    result = fight.fight(setup, 0, False)
    want = tuple((i, s.when[1]) for i, s in enumerate(setup.timeline))
    assert want and result.steps_fired == want
    assert result.heads == (4, 4) and result.ticks > 0


def test_ambush_springs_at_its_tick(library):
    setup = _setup("ambush")
    result = fight.fight(setup, 0, False)
    assert setup.groups[0].order == "idle"
    assert result.steps_fired == ((0, 100),)


@pytest.mark.parametrize("name", sorted(PLAYS))
def test_two_runs_are_identical(library, name):
    assert fight.fight(_setup(name), 0, False) == fight.fight(_setup(name), 0, False)
