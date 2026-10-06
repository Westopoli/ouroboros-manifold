# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, situation sampler (a sampled map must change the fight)
"""Real engine: the same fight on a sampled map differs from the open map in ticks, survivors or positions every 100 ticks.

Defect measured 2026-10-05: every sampled map gave a fight identical to the open map. The Phase B choke is the positive control."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.contract import Terrain  # noqa: E402
from scripts.skilllab.maps import sample_map  # noqa: E402
from scripts.skilllab.scenes import guard_defenders, phase_b_choke  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def run(setup, library):
    r = fight.fight(dataclasses.replace(setup, trace=True), 1, False, engine=library)
    return r.ticks, r.survivors, tuple(row[:4] for row in r.trace if row[0] % 100 == 0)


def landscape_setup(kind, seed):
    terrain = sample_map(kind, seed)
    return with_terrain(guard_defenders(asym_play(16, Side("blob"), Side("blob"))), terrain)(16, False)


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("kind", ["block", "wall", "lane", "cover_field"])
def test_a_sampled_map_changes_the_fight_against_open(library, kind, seed):
    got = run(landscape_setup(kind, seed), library)
    base = run(landscape_setup("open", seed), library)
    assert got != base, "%s seed %d: fight identical to open (ticks %d, survivors %r)" % (kind, seed, got[0], got[1])


def test_phase_b_choke_changes_the_fight_against_open(library):
    """Positive control, green today: the choke's walls are on layers 0 to 4."""
    setup = phase_b_choke(8)(16, False)
    open_setup = dataclasses.replace(setup, terrain=Terrain(canvas=setup.terrain.canvas))
    assert run(setup, library) != run(open_setup, library)
