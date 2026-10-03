# spec: docs/northstar/plans/skilllab-plan.md::Phase S::item 8b (weighted count reads the engine's decision)
"""HELD, EXPECTED RED until the engine side-sight and reach land (Phase C); A144: not landed.

The weighted firing count must read what the engine decided (its visible set and reach), not recompute its own.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402
from scripts.skilllab.firing import count_able_weighted  # noqa: E402

BOMBARD_STAND_IN = 100
MAX_TICKS = 200
SETTLE = 10   # the engine scans for targets one unit per tick, so a unit acquires within a few ticks


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


def _scene(e, w, far, gap):
    """Side 0 = 3 units of the first type, side 1 = 3 Vanguard `gap` wu east; returns (ids0, ids1, ranges, weights)."""
    van = e.type_id("Vanguard")
    vstats = e.type_stats(w, van)
    t0 = van
    if far:
        stats = dict(vstats, role="Vanguard", ability_id=0, sensor_radius=300.0, attack_range=1000.0)
        e.register_unit_type(w, BOMBARD_STAND_IN, stats)
        t0 = BOMBARD_STAND_IN
    ids0 = [e.spawn(w, t0, 0, 300.0, 400.0 + 30.0 * i, 0) for i in range(3)]
    ids1 = [e.spawn(w, van, 1, 300.0 + gap, 400.0 + 30.0 * i, 0) for i in range(3)]
    e.disable_abilities(w)
    e.order_attack_move(w, ids0, 300.0 + gap, 400.0)
    e.order_attack_move(w, ids1, 300.0, 400.0)
    ranges = {u: e.type_stats(w, t0)["attack_range"] for u in ids0}
    ranges.update({u: vstats["attack_range"] for u in ids1})
    return ids0, ids1, ranges, {u: 1.0 for u in ids0 + ids1}


def _differences(e, far, gap):
    """[(tick, units that have acquired a target so far, harness able count)] once settled, where they differ."""
    w = e.new_world(0)
    try:
        ids0, ids1, ranges, weights = _scene(e, w, far, gap)
        diffs, ever = [], set()
        for tick in range(1, MAX_TICKS + 1):
            e.step(w)
            ever |= {u for u in ids0 if e.unit_alive(w, u) and e.unit_target(w, u) != 0}
            decided = len(ever)
            able0, _ = count_able_weighted(e, w, ids0, ids1, ranges, weights)
            if tick >= SETTLE and decided != int(able0):
                diffs.append((tick, decided, int(able0)))
        return diffs, bool(ever)
    finally:
        e.free_world(w)


def test_positive_control_inside_every_sensor_radius_engine_and_harness_agree(real_engine):
    """Both sides Vanguard 300 wu apart, no spotter needed: the acquired set (units that acquired a target so far) equals the harness's able set."""
    diffs, acquired = _differences(real_engine, far=False, gap=300.0)
    assert acquired, "control scene never acquired a target; the test harness is unsound"
    assert diffs == []


def test_weighted_count_reads_what_the_engine_decided_without_a_spotter(real_engine):
    """Requirement (Architect, 2026-10-02, ruling A144): when the engine's side-sight and reach land (Phase C) the
    weighted count must read the engine's visible set and reach. Long-range short-sensor units, no spotter, at 700 wu:
    the engine's acquired set and the harness's able set must agree at every tick. HELD, EXPECTED RED today."""
    diffs, acquired = _differences(real_engine, far=True, gap=700.0)
    assert acquired, "the engine never acquired a target in the unspotted scene"
    assert diffs == [], "(tick, engine acquired, harness able) differ: %r" % (diffs[:5],)
