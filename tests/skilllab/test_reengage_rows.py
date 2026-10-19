# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md "CSV columns" (reengage_0/1) and decision 28 point 3
"""LAB-REV2-L8: the re-engage counts in FightResult and in the CSV row. Interface: see the header of test_reengage.py.

FightResult.reengage: tuple = (0, 0)   (side 0, side 1); fight_row adds the int columns reengage_0, reengage_1 straight after
prefight and before any feat_* column; trim_series keeps them; a label named like them is refused. A fight that never re-engages
writes the same row as before plus those two columns at 0, so every older column keeps its place and its bytes."""
import copy
import csv
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import maps, rows  # noqa: E402
from scripts.skilllab.contract import FightResult, trim_series  # noqa: E402
from scripts.skilllab.rows import fight_row, write_rows  # noqa: E402

# the 26 fixed columns as they stood before L8, written out here so no other test file's list can move them
BEFORE_L8 = ["outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1", "heads_0", "heads_1", "ticks",
             "first_contact_tick", "firing_unit_seconds_0", "firing_unit_seconds_1", "firing_window_0", "firing_window_1",
             "weighted_unit_seconds_0", "weighted_unit_seconds_1", "weighted_window_0", "weighted_window_1", "predicted_count",
             "predicted_type", "agreement", "knob", "knob_value", "baseline", "ceiling_hit", "prefight"]
REENGAGE = ["reengage_0", "reengage_1"]
PLAIN = dict(knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok")


def _result(**over):
    base = dict(outcome="side0", margin=0.5, strength_left=(0.75, 0.25), survivors=(12, 3), heads=(16, 12), ticks=340,
                first_contact_tick=35, firing=[(0, 0, 0), (5, 2, 1)], firing_unit_seconds=(10.5, 7.25), winner="side0",
                firing_window=(4.0, 2.5), weighted_unit_seconds=(9.0, 6.0), weighted_window=(3.5, 2.0),
                predicted_count="side0", predicted_type="side0", agreement="both_right")
    base.update(over)
    return FightResult(**base)


def test_a_result_built_without_the_field_counts_zero_zero():
    """Default (0, 0): every older FightResult(...) call site keeps working."""
    assert tuple(_result().reengage) == (0, 0)
    assert "reengage" in FightResult.__dataclass_fields__


def test_the_field_carries_what_it_is_given_and_trim_series_keeps_it():
    r = _result(reengage=(3, 1))
    assert tuple(r.reengage) == (3, 1)
    assert tuple(trim_series(r).reengage) == (3, 1)


def test_the_row_ends_its_fixed_columns_with_reengage_0_and_1():
    row = fight_row(_result(reengage=(3, 1)), play="reach", **PLAIN)
    assert list(row) == ["play"] + BEFORE_L8 + REENGAGE
    assert (row["reengage_0"], row["reengage_1"]) == (3, 1)
    assert type(row["reengage_0"]) is int and type(row["reengage_1"]) is int


def test_the_reengage_columns_sit_before_the_feature_columns():
    f = maps.Features(choke_count=1, choke_width_wu=100.0, choke_width_bodies=2.0, lane_count=1, blocked_layer_ranges=(),
                      fight_layer_blocked=False, cover_density_corridor=0.1, start_distance=1400.0, detour_ratio=0.0,
                      blocked_layer_top=4)
    keys = list(fight_row(_result(), features=f, **PLAIN))
    assert keys[:len(BEFORE_L8) + 2] == BEFORE_L8 + REENGAGE
    assert all(k.startswith("feat_") for k in keys[len(BEFORE_L8) + 2:]) and len(keys) > len(BEFORE_L8) + 2


def test_a_row_without_a_reengage_equals_the_old_row_plus_two_zero_columns():
    """Byte-identity control: dropping the two new keys leaves every old key, in its old place, with the old value."""
    old = fight_row(_result(), play="reach", enemy_heads=12, **PLAIN)
    base = {k: v for k, v in old.items() if k not in REENGAGE}
    assert list(base) == ["play", "enemy_heads"] + BEFORE_L8
    assert (old["reengage_0"], old["reengage_1"]) == (0, 0)
    assert base["margin"] == 0.5 and base["firing_unit_seconds_1"] == 7.25 and base["agreement"] == "both_right"


@pytest.mark.parametrize("name", REENGAGE)
def test_a_label_named_like_a_reengage_column_is_refused(name):
    with pytest.raises(ValueError):
        fight_row(_result(), **{name: 1}, **PLAIN)
    assert name in rows._FIXED


def test_the_csv_header_and_line_carry_the_counts_as_bare_ints(tmp_path):
    path = tmp_path / "r.csv"
    write_rows([fight_row(_result(reengage=(2, 0)), **PLAIN)], path)
    with open(path, newline="") as fh:
        header, line = list(csv.reader(fh))
    assert header == BEFORE_L8 + REENGAGE
    got = dict(zip(header, line))
    assert (got["reengage_0"], got["reengage_1"]) == ("2", "0")
    assert line[:len(BEFORE_L8)] == [("" if v is None else repr(v) if isinstance(v, float) else str(v))
                                     for v in (fight_row(_result(), **PLAIN)[k] for k in BEFORE_L8)]
