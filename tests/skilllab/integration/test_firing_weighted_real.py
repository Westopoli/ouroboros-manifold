# spec: docs/northstar/plans/skilllab-plan.md::Phase S::item 8 (weighted firing count)
"""Weighted firing series against the real engine. Asserts only what holds without the side-sight engine rule."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.firing import unit_weight  # noqa: E402

UNIT = "Vanguard"


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


def _setup(weighted):
    g0 = Group(side=0, unit=UNIT, count=3, formation="line", x=300.0, y=400.0, facing_deg=0.0, layer=0,
               order="attack_move", params={"spacing": 30.0})
    g1 = Group(side=1, unit=UNIT, count=3, formation="line", x=480.0, y=400.0, facing_deg=180.0, layer=0,
               order="attack_move", params={"spacing": 30.0})
    return Setup(groups=(g0, g1), unit_types={}, max_ticks=60, sample_every=5, weighted=weighted)


def test_weighted_series_matches_firing_length_and_is_deterministic(real_engine):
    """Same sample ticks as firing; two runs of one seed are identical."""
    a = fight.fight(_setup(True), 0, False, engine=real_engine)
    b = fight.fight(_setup(True), 0, False, engine=real_engine)
    assert a.weighted is not None and len(a.weighted) == len(a.firing)
    assert [t for t, _, _ in a.weighted] == [t for t, _, _ in a.firing]
    assert a.weighted == b.weighted


def test_weighted_values_are_bounded_by_units_times_the_unit_weight(real_engine):
    """0 <= w_side <= headcount x weight of the (single) unit type; every sample, both sides."""
    r = fight.fight(_setup(True), 0, False, engine=real_engine)
    w = real_engine.new_world(0)
    try:
        cap = 3 * unit_weight(real_engine.type_stats(w, real_engine.type_id(UNIT)))
    finally:
        real_engine.free_world(w)
    for _, w0, w1 in r.weighted:
        assert 0.0 <= w0 <= cap + 1e-9 and 0.0 <= w1 <= cap + 1e-9


def test_off_by_default_records_nothing_and_leaves_the_rest_identical(real_engine):
    """weighted False: result.weighted is None and the firing series equals the weighted run's."""
    off = fight.fight(_setup(False), 0, False, engine=real_engine)
    on = fight.fight(_setup(True), 0, False, engine=real_engine)
    assert off.weighted is None and off.firing == on.firing and off.outcome == on.outcome


def test_profile_reach_reads_zero_zero_from_the_stub_library(real_engine):
    """Today's om_unit_profile_reach writes nothing; the binding returns (0, 0) for every built-in type."""
    w = real_engine.new_world(0)
    try:
        for name in ("Raider", "Vanguard", "Bastion"):
            assert real_engine.profile_reach(w, real_engine.type_id(name)) == (0, 0)
    finally:
        real_engine.free_world(w)
