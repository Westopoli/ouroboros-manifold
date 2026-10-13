# spec: R-096-08 (guard), R-096-04 (layer reach) - the tall-cover scene through the production library
"""tall_cover at 16 v 12, with and without the counter: both finish, and two runs are equal."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine, fight  # noqa: E402
from scripts.skilllab.ground.scenes_ground import tall_cover  # noqa: E402

OUTCOMES = {"side0", "side1", "draw", "stalemate", "cap"}


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _setup(counter):
    s = tall_cover(counter=counter)(16)(12, False)
    return dataclasses.replace(s, settings={**s.settings, **batches.BASE_SETTINGS}, max_ticks=1500)


@pytest.mark.parametrize("counter", [False, True])
def test_fight_finishes_with_a_valid_outcome_and_is_deterministic(library, counter):
    a = fight.fight(_setup(counter), 1, False, engine=library)
    b = fight.fight(_setup(counter), 1, False, engine=library)
    assert a.outcome in OUTCOMES and a.heads == (16, 12) and a.ticks > 0
    assert a == b


def test_counter_run_damages_the_defenders(library):
    """The scene's draft reach settings let layer-3 attackers hit layer 0. first_contact_tick stays -1 by design:
    count_able needs the same layer, so contact is read from the defenders' strength instead."""
    r = fight.fight(_setup(True), 1, False, engine=library)
    assert r.strength_left[1] < 1.0


def test_layer_zero_run_reads_whatever_it_reads(library):
    r = fight.fight(_setup(False), 1, False, engine=library)
    assert r.outcome in OUTCOMES and r.first_contact_tick >= -1
