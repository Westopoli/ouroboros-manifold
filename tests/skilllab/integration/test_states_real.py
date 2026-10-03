# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S (trace states, order ends)
"""Setup.states against the real library: a 3 v 3 Vanguard blob fight."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays  # noqa: E402

STATES = {"can fire", "blocked", "walking", "no target"}


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def run(library):
    setup = dataclasses.replace(plays.blob_play(3)(3, False), states=True, max_ticks=600)
    return fight.fight(setup, 1, False, engine=library)


def test_states_real_fight(library):
    r = run(library)
    assert r.states and all(len(row) == 3 and row[2] in STATES for row in r.states)
    assert r.states[0][0] == 0
    assert any(s == "can fire" for _, _, s in r.states)
    keys = [(t, u) for t, u, _ in r.states]
    assert keys == sorted(keys)
    assert isinstance(r.order_ends, tuple)


def test_states_are_deterministic(library):
    a, b = run(library), run(library)
    assert a.states == b.states and a.order_ends == b.order_ends
