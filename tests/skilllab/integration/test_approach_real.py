# spec: Architect ruling A198 - hold-to-contact opening through the production library
"""Plays walk as move groups that keep their slots to a stop line (S = 0.95 x the smaller attack range), then switch
to attack_move on arrival. EXPECTED RED until Setup.approach, approach_setup and the play wiring land."""
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine, fight, plays  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402

VANGUARD_RANGE, RAIDER_RANGE = 300.0, 200.0


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _setup(build, enemy=32, **kw):
    s = build(enemy, False)
    return dataclasses.replace(s, trace=True, max_ticks=900, settings={**s.settings, **batches.BASE_SETTINGS}, **kw)


def _rows(result, tick):
    return [r for r in result.trace if r[0] == tick and r[6]]


def _spread(result, tick, ids):
    ys = [r[3] for r in _rows(result, tick) if r[1] in ids]
    return max(ys) - min(ys)


def _closest(result, tick, n0):
    rows = _rows(result, tick)
    a = [(r[2], r[3]) for r in rows if r[1] <= n0]
    b = [(r[2], r[3]) for r in rows if r[1] > n0]
    return min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in a for q in b)


def _first_step(result):
    assert result.steps_fired, "the approach fires no step"
    return min(t for _, t in result.steps_fired)


@pytest.fixture(scope="module")
def line_runs(library):
    on = fight.fight(_setup(plays.line_play(32)), 0, False, engine=library)
    off_setup = dataclasses.replace(_setup(plays.line_play(32)), approach=0.0)
    return on, fight.fight(off_setup, 0, False, engine=library)


def test_the_shape_is_held_until_contact(line_runs):
    on, off = line_runs
    ids = set(range(1, 33))
    t_on, t_off = on.first_contact_tick - 1, off.first_contact_tick - 1
    assert t_on >= 1 and t_off >= 1
    held = _spread(on, t_on, ids) / _spread(on, 0, ids)
    assert held >= 0.9
    # positive control: without the approach the line has already folded by its own first contact
    assert _spread(off, t_off, ids) / _spread(off, 0, ids) < held


def test_nobody_fires_during_the_approach(line_runs):
    on, _ = line_runs
    first = _first_step(on)
    assert on.first_contact_tick >= 1
    early = [row for row in on.firing if row[0] < first]
    assert early and all(a0 == 0 and a1 == 0 for _, a0, a1 in early)


def test_positive_control_the_unapproached_opening_fires_early(line_runs):
    _, off = line_runs
    assert off.steps_fired == ()
    assert off.first_contact_tick < 60


def test_the_fronts_stop_short_at_the_stop_distance(line_runs):
    on, _ = line_runs
    stop = 0.95 * VANGUARD_RANGE
    d = _closest(on, _first_step(on), 32)
    assert 0.8 * stop <= d <= 1.2 * stop


def test_a_mixed_raider_v_vanguard_play_uses_the_shorter_range(library):
    build = asym_play(8, Side("blob", mix=(("Raider", 1),)), Side("blob"))
    result = fight.fight(_setup(build, enemy=8), 0, False, engine=library)
    stop = 0.95 * RAIDER_RANGE
    d = _closest(result, _first_step(result), 8)
    assert 0.8 * stop <= d <= 1.2 * stop


def test_two_runs_are_identical(library):
    s = _setup(plays.line_play(8), enemy=8)
    assert fight.fight(s, 0, False, engine=library) == fight.fight(s, 0, False, engine=library)
