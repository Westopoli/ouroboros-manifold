# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S::first bullet (per-fight settings in Setup)
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase A::row 48 (OM_TP_* settings, G1)
"""Positive control of the settings binding: a setting moved off its default changes what a real fight does.

Separate from test_settings_real.py on purpose. Today's engine has no parameter at all, so there is nothing to
observe; after PP-contract alone the parameters exist and read back (test_settings_real.py goes green) but a
parameter only changes a fight once a rule piece (A2 tactical_move.c, A3 unit.c) reads it. Which parameters do
that when is not in the plan, so this test takes the six the plan names and requires that AT LEAST ONE, flipped
from its default, changes the fight's row or trace; it reports which ones moved. If it is still red after the
rules that consume the named switches have landed, the binding or a rule is dead.
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, rows  # noqa: E402

FLIPPED = {"OM_TP_PURSUE_BY_STEERING": 0.0, "OM_TP_ROUTE_AROUND_TERRAIN": 0.0, "OM_TP_TARGET_BY_SIGHT": 0.0,
           "OM_TP_ROUTE_ACROSS_LAYERS": 0.0, "OM_TP_LEASH_BEFORE_DAMAGE": 1.0, "OM_TP_TARGET_POLICY": 1.0}


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def observe(library, settings, seed):
    base = plays.blob_play(16)(16, False)
    setup = dataclasses.replace(base, trace=True, max_ticks=1500, settings=settings)
    r = fight.fight(setup, seed, False, engine=library)
    return rows.fight_row(r), repr(r.trace)


def test_at_least_one_named_setting_moves_a_real_fight(library):
    moved = []
    for name, value in sorted(FLIPPED.items()):
        for seed in (0, 1):
            if observe(library, {name: value}, seed) != observe(library, {}, seed):
                moved.append(name)
                break
    assert moved, "no named setting changed a fight at either seed: " + ", ".join(sorted(FLIPPED))
