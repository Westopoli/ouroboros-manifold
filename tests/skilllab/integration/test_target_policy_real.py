# spec: ruling A196 (per-side target policy): fight.apply_target_policy(engine, w, setup), real library
"""Per-side target policy read back from the production library (needs push/pt-land merged)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, rows  # noqa: E402

P0, F1 = "OM_TP_TARGET_POLICY", "OM_TP_TARGET_POLICY_FACTION_1"


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def setup_with(pair, trace=False):
    base = plays.blob_play(8)(8, False)
    return dataclasses.replace(base, max_ticks=600, trace=trace, target_policy=pair)


def read(library, pair):
    w = library.new_world(0)
    try:
        fight.apply_target_policy(library, w, setup_with(pair))
        return library.get_param(w, library.param_id(P0)), library.get_param(w, library.param_id(F1))
    finally:
        library.free_world(w)


def test_0_1_reads_back_different_sides(library):
    assert read(library, (0, 1)) == (0.0, 1.0)


def test_1_0_reads_back_swapped(library):
    assert read(library, (1, 0)) == (1.0, 0.0)


def test_none_pair_leaves_faction_1_unset(library):
    assert read(library, None) == (0.0, -1.0)


def test_equal_pairs_read_back_equal(library):
    assert read(library, (0, 0)) == (0.0, 0.0)
    assert read(library, (1, 1)) == (1.0, 1.0)


def test_unset_entries_stay_default(library):
    assert read(library, (1, None)) == (1.0, -1.0)
    assert read(library, (None, 1)) == (0.0, 1.0)


def test_none_pair_fight_rows_equal_a_setup_without_the_field(library):
    plain = dataclasses.replace(plays.blob_play(8)(8, False), max_ticks=600, trace=True)
    a = fight.fight(plain, 3, False, engine=library)
    b = fight.fight(setup_with(None, trace=True), 3, False, engine=library)
    assert rows.fight_row(a) == rows.fight_row(b) and repr(a.trace) == repr(b.trace)
