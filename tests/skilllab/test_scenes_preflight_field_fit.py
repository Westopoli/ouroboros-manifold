# spec: LAB-REV2-L6 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, the L6 row: scenes.py; decision 7, preflight order no_fit first)
"""scenes.preflight answers "no_fit" for a WALKING mover placed on ground the generated field (Terrain.field_seed) says is not walkable,
read through terrain_walkable_at, and "ok" for the same Setup on walkable ground. LAB-REV2-FIX (Architect, decision 20 as rewritten): only
walking movers read terrain_walkable_at; flyers and guards are checked against blocks only (tests/skilllab/test_drift_fix_nofit.py).
So the mover here is a walking type with a move order; it was an idle built-in Vanguard (a flyer), which no longer reads the field
(TD-LAB-REV2-FIX-nofit).
Seed 11, 12000 canvas: (3500, 4000) is unwalkable band 1 ground, (2000, 2000) is walkable band 1 ground (measured 2026-10-14)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, scenes  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Terrain  # noqa: E402

UNWALKABLE, WALKABLE, FOE = (3500.0, 4000.0), (2000.0, 2000.0), (2100.0, 2000.0)


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


WALKER = {"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}


def _setup(at, seed=11):
    def group(side, unit, p, order, goal=None):
        return Group(side=side, unit=unit, count=1, formation="points", x=p[0], y=p[1], facing_deg=0.0, layer=0, order=order, goal=goal,
                     params={"points": [p]})
    return Setup(groups=(group(0, "Walker", at, "move", FOE), group(1, "Vanguard", FOE, "idle")), unit_types=dict(WALKER),
                 terrain=Terrain(canvas=(12000.0, 12000.0), field_seed=seed))


def test_control_the_two_places_are_what_the_comments_say(lib):
    w = lib.new_world(0)
    try:
        lib.set_canvas(w, 12000.0, 12000.0)
        assert lib.terrain_generate(w, 11, 12000.0) == 0
        assert not lib.terrain_walkable_at(w, *UNWALKABLE)
        assert lib.terrain_walkable_at(w, *WALKABLE) and lib.terrain_walkable_at(w, *FOE)
    finally:
        lib.free_world(w)


def test_a_unit_placed_on_unwalkable_field_ground_is_no_fit(lib):
    assert scenes.preflight(_setup(UNWALKABLE), lib) == "no_fit"


def test_the_same_setup_on_walkable_field_ground_is_ok(lib):
    assert scenes.preflight(_setup(WALKABLE), lib) == "ok"


def test_no_fit_needs_no_engine_argument():
    """preflight builds an engine itself when None is passed (its docstring); the field read must not need the caller's."""
    assert scenes.preflight(_setup(UNWALKABLE), None) == "no_fit"
    assert scenes.preflight(_setup(WALKABLE), None) == "ok"


def test_a_setup_without_a_field_is_not_asked_about_the_field():
    """A hand-built terrain (field_seed None) keeps its blocks-only rule: the same place is not a no_fit there."""
    s = _setup(UNWALKABLE, seed=None)
    assert scenes.preflight(s, None) == "ok"
