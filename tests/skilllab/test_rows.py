# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-17; 2026-10-14 skill lab rev 2 "CSV columns" (LAB-REV2-L2, Q-LAB-03)
"""Leaf-05: fight_row and write_rows (write_rows ported from toys/layerlab/layerlab/batch.py).

Rev 2 (LAB-REV2-L2): the twelve fixed columns are kept, the result adds firing_window_0/1, weighted_unit_seconds_0/1,
weighted_window_0/1, predicted_count, predicted_type and agreement (all from the FightResult, always present), and the row
ends with knob, knob_value, baseline, ceiling_hit and prefight, which the scan and the scene supply as keyword arguments
(the spec lists them last and gives no defaults, so the tests always pass all five). `mopup_orders` is not a column."""
import copy
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import FightResult  # noqa: E402
from scripts.skilllab.rows import fight_row, write_rows  # noqa: E402
from scripts.skilllab.sample import grid  # noqa: E402

OLD12 = ["outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1",
         "heads_0", "heads_1", "ticks", "first_contact_tick", "firing_unit_seconds_0",
         "firing_unit_seconds_1"]
FROM_RESULT = OLD12 + ["firing_window_0", "firing_window_1", "weighted_unit_seconds_0", "weighted_unit_seconds_1",
                       "weighted_window_0", "weighted_window_1", "predicted_count", "predicted_type", "agreement"]
SUPPLIED = ["knob", "knob_value", "baseline", "ceiling_hit", "prefight"]
REENGAGE = ["reengage_0", "reengage_1"]   # LAB-REV2-L8 (TD-LAB-REV2-L8-columns): the spec lists them after prefight
REV3C = ["verdict", "decided_tick", "paper_score_0", "paper_score_1", "predicted_paper"]   # LAB-REV3-C (TD-LAB-REV3-C-columns): after reengage_1
FIXED = FROM_RESULT + SUPPLIED + REENGAGE + REV3C
PLAIN = dict(knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok")


def _result(**over):
    base = dict(outcome="side0", margin=0.5, strength_left=(0.75, 0.25), survivors=(12, 3),
                heads=(16, 12), ticks=340, first_contact_tick=35,
                firing=[(0, 0, 0), (5, 2, 1)], firing_unit_seconds=(10.5, 7.25),
                winner="side0", firing_window=(4.0, 2.5), weighted_unit_seconds=(9.0, 6.0),
                weighted_window=(3.5, 2.0), predicted_count="side0", predicted_type="side0", agreement="both_right")
    base.update(over)
    return FightResult(**base)


def _row(result=None, **labels):
    """fight_row with the five supplied columns at their plain values unless overridden; labels come first."""
    kw = dict(PLAIN)
    kw.update({k: labels.pop(k) for k in list(labels) if k in PLAIN})
    return fight_row(result or _result(), **labels, **kw)


def _read(path):
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


def test_fight_row_labels_first_then_fixed_keys_in_order():
    """AC-17 / rev 2 contract: labels in the order given, then the fixed keys: the 12 old ones, the 9 new result columns, the 5 supplied; nothing else."""
    row = _row(play="reach", enemy_heads=12)
    assert type(row) is dict
    assert list(row) == ["play", "enemy_heads"] + FIXED


def test_fight_row_values_flatten_the_result():
    """AC-17: tuple fields split into _0/_1 keys; values carried through unchanged."""
    row = _row(play="reach", enemy_heads=12)
    assert row["play"] == "reach" and row["enemy_heads"] == 12
    assert row["outcome"] == "side0"
    assert row["margin"] == 0.5
    assert (row["strength_left_0"], row["strength_left_1"]) == (0.75, 0.25)
    assert (row["survivors_0"], row["survivors_1"]) == (12, 3)
    assert (row["heads_0"], row["heads_1"]) == (16, 12)
    assert row["ticks"] == 340 and row["first_contact_tick"] == 35
    assert (row["firing_unit_seconds_0"], row["firing_unit_seconds_1"]) == (10.5, 7.25)


def test_fight_row_label_order_is_call_order_not_alphabetical():
    """AC-17: labels keep keyword order."""
    row = _row(zeta=1, alpha=2, mid=3)
    assert list(row)[:3] == ["zeta", "alpha", "mid"]
    assert list(row)[3:] == FIXED


def test_fight_row_without_labels_is_just_the_fixed_keys():
    """AC-17 (Existence, no labels): exactly the fixed keys, in the contract order."""
    assert list(_row()) == FIXED
    assert list(fight_row(_result(), **PLAIN))[:len(FROM_RESULT)] == FROM_RESULT


def test_fight_row_carries_never_met_and_cap_values():
    """AC-17/11, Q-LAB-03: first_contact_tick -1 and a cap outcome pass through as given (cap is a defect row, not dropped)."""
    row = _row(_result(outcome="cap", first_contact_tick=-1, margin=-0.125, winner=None, agreement="n/a",
                       strength_left=(0.5, 0.625), survivors=(8, 10), ticks=12000), n=1)
    assert row["outcome"] == "cap" and row["first_contact_tick"] == -1
    assert row["margin"] == -0.125 and row["ticks"] == 12000 and row["agreement"] == "n/a"


def test_fight_row_is_a_pure_function_of_its_inputs():
    """AC-17: the same result and labels give the same row twice; the result is not changed."""
    r = _result()
    before = copy.deepcopy(r)
    assert _row(r, play="p", enemy_heads=3) == _row(r, play="p", enemy_heads=3)
    assert r == before


def test_write_rows_exact_bytes_for_a_small_table(tmp_path):
    """AC-17: header from first appearance; ints bare, floats in one fixed format, None blank; \\n ends."""
    rows = [{"a": 1, "b": 0.5, "c": "x"}, {"a": 2, "b": 0.25, "c": None}]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    assert path.read_bytes() == b"a,b,c\n1,0.5,x\n2,0.25,\n"


def test_write_rows_columns_in_order_of_first_appearance(tmp_path):
    """AC-17 (Ordering): columns follow first appearance across rows; absent keys are blank."""
    rows = [{"b": 1, "a": 2}, {"c": 3, "a": 4}, {"d": 5}]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    assert path.read_bytes() == b"b,a,c,d\n1,2,,\n,4,3,\n,,,5\n"


def test_write_rows_float_format_is_fixed_across_values(tmp_path):
    """AC-17: one numeric format; 1.0 stays '1.0', 1/3 keeps full digits, same float prints the same twice."""
    rows = [{"x": 1.0, "y": 1 / 3, "z": 1e-07}, {"x": 1, "y": 1 / 3, "z": 0.1}, {"x": -0.0625, "y": 2.5, "z": 1e-07}]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    assert path.read_bytes() == (b"x,y,z\n1.0,0.3333333333333333,1e-07\n"
                                 b"1,0.3333333333333333,0.1\n-0.0625,2.5,1e-07\n")


def test_write_rows_line_ends_are_lf_only(tmp_path):
    """AC-17: no carriage returns anywhere; the file ends with one \\n."""
    rows = [{"a": i, "b": "t%d" % i} for i in range(5)]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    data = path.read_bytes()
    assert b"\r" not in data
    assert data.endswith(b"\n") and not data.endswith(b"\n\n")
    assert data.count(b"\n") == 6


def test_write_rows_bytes_depend_only_on_rows(tmp_path):
    """AC-17: two calls (different paths, str and Path) give identical bytes; no timestamp."""
    rows = [_row(play="p", enemy_heads=8), _row(_result(margin=-0.25, ticks=99), play="p", enemy_heads=9)]
    p1, p2 = tmp_path / "one.csv", str(tmp_path / "two.csv")
    write_rows(rows, p1)
    write_rows(copy.deepcopy(rows), p2)
    assert p1.read_bytes() == Path(p2).read_bytes()
    assert p1.read_bytes() == (
        b"play,enemy_heads," + ",".join(FIXED).encode() + b"\n"
        b"p,8,side0,0.5,0.75,0.25,12,3,16,12,340,35,10.5,7.25,4.0,2.5,9.0,6.0,3.5,2.0,side0,side0,both_right,none,,none,0,ok,0,0,,,0.0,0.0,tie\n"
        b"p,9,side0,-0.25,0.75,0.25,12,3,16,12,99,35,10.5,7.25,4.0,2.5,9.0,6.0,3.5,2.0,side0,side0,both_right,none,,none,0,ok,0,0,,,0.0,0.0,tie\n")


def test_write_rows_overwrites_an_existing_file(tmp_path):
    """AC-17: the file holds exactly the rows of the last call."""
    path = tmp_path / "r.csv"
    write_rows([{"a": 1}, {"a": 2}, {"a": 3}], path)
    write_rows([{"b": 9}], path)
    assert path.read_bytes() == b"b\n9\n"


def test_write_rows_does_not_change_the_rows(tmp_path):
    """AC-17: rows are read, not edited."""
    rows = [{"a": 1}, {"b": 2.5, "a": 3}]
    before = copy.deepcopy(rows)
    write_rows(rows, tmp_path / "r.csv")
    assert rows == before


def test_write_rows_text_with_commas_and_quotes_reads_back(tmp_path):
    """AC-17 (Conformance, ported csv writer): awkward text survives a csv read-back."""
    rows = [{"label": 'a,b "c"', "n": 1}]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    assert _read(path) == [["label", "n"], ['a,b "c"', "1"]]


def test_fight_rows_pass_through_write_rows(tmp_path):
    """AC-17 composition: rows built by fight_row are written with the exact column order and values."""
    rows = [_row(play="reach", enemy_heads=n, replicate=n % 2) for n in (8, 9)]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    got = _read(path)
    assert got[0] == ["play", "enemy_heads", "replicate"] + FIXED
    assert got[1] == ["reach", "8", "0", "side0", "0.5", "0.75", "0.25", "12", "3", "16", "12", "340", "35", "10.5", "7.25",
                      "4.0", "2.5", "9.0", "6.0", "3.5", "2.0", "side0", "side0", "both_right", "none", "", "none", "0", "ok", "0", "0", "", "", "0.0", "0.0", "tie"]
    assert got[2][:3] == ["reach", "9", "1"]
    assert len(got) == 3


def test_sample_grid_rows_pass_through_write_rows(tmp_path):
    """AC-16/17 composition rows<->sample: grid points are rows; columns follow dims order."""
    dims = [{"path": "reach", "kind": "float", "lo": 1.0, "hi": 1.5},
            {"path": "size", "kind": "int", "lo": 8, "hi": 16}]
    points = grid(dims, 2)
    path = tmp_path / "g.csv"
    write_rows(points, path)
    assert path.read_bytes() == b"reach,size\n1.0,8\n1.0,16\n1.5,8\n1.5,16\n"


@pytest.mark.parametrize("key", FROM_RESULT)
def test_fight_row_label_named_like_a_result_column_raises_value_error(key):
    """AC-17 Reading: a label that collides with a column taken from the result raises ValueError (the new columns too)."""
    with pytest.raises(ValueError):
        _row(**{key: "x"})


def test_fight_row_label_collision_amid_other_labels_raises():
    """AC-17 Reading: one colliding label among ordinary ones still raises."""
    with pytest.raises(ValueError):
        _row(play="reach", margin=3, enemy_heads=8)


def test_write_rows_empty_rows_writes_a_zero_byte_file(tmp_path):
    """AC-17 Reading: an empty rows list writes a 0-byte file (created, even over an older one)."""
    path = tmp_path / "r.csv"
    write_rows([{"a": 1}], path)
    write_rows([], path)
    assert path.is_file() and path.stat().st_size == 0
    fresh = tmp_path / "fresh.csv"
    write_rows([], fresh)
    assert fresh.read_bytes() == b""


def test_write_rows_nan_and_inf_are_written_as_text(tmp_path):
    """AC-17 Reading: nan and inf cells are the text nan and inf."""
    path = tmp_path / "r.csv"
    write_rows([{"x": float("nan"), "y": float("inf"), "z": 1.5}], path)
    assert path.read_bytes() == b"x,y,z\nnan,inf,1.5\n"


def test_write_rows_creates_missing_parent_directories(tmp_path):
    """AC-17 Reading: a missing parent directory of path is created (parents included)."""
    path = tmp_path / "a" / "b" / "r.csv"
    write_rows([{"a": 1}], path)
    assert path.read_bytes() == b"a\n1\n"
    write_rows([{"a": 2}], str(tmp_path / "c" / "r.csv"))
    assert (tmp_path / "c" / "r.csv").read_bytes() == b"a\n2\n"


# ---------------------------------------------------------------- rev 2 columns (spec "CSV columns", ruling 5)

def test_the_retired_outcome_columns_are_not_in_the_row():
    """Q-LAB-03: no mop-up counter in the row (mopup_orders is retired with the mop-up)."""
    assert "mopup_orders" not in _row()


def test_new_result_columns_carry_the_result_values():
    row = _row(_result(firing_window=(4.0, 2.5), weighted_unit_seconds=(9.0, 6.0), weighted_window=(3.5, 2.0),
                       predicted_count="side1", predicted_type="tie", agreement="n/a"))
    assert (row["firing_window_0"], row["firing_window_1"]) == (4.0, 2.5)
    assert (row["weighted_unit_seconds_0"], row["weighted_unit_seconds_1"]) == (9.0, 6.0)
    assert (row["weighted_window_0"], row["weighted_window_1"]) == (3.5, 2.0)
    assert (row["predicted_count"], row["predicted_type"], row["agreement"]) == ("side1", "tie", "n/a")


@pytest.mark.parametrize("agreement", ["both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a"])
def test_every_agreement_value_passes_through(agreement):
    assert _row(_result(agreement=agreement))["agreement"] == agreement


@pytest.mark.parametrize("outcome", ["side0", "side1", "draw", "cap"])
def test_the_four_outcomes_pass_through(outcome):
    assert _row(_result(outcome=outcome))["outcome"] == outcome


def test_supplied_columns_carry_what_the_caller_gave():
    row = fight_row(_result(), knob="OM_TP_VISION_UP_1", knob_value=0.25, baseline="naive_defender_play_layer",
                    ceiling_hit=1, prefight="no_reach")
    assert (row["knob"], row["knob_value"], row["baseline"], row["ceiling_hit"], row["prefight"]) == \
        ("OM_TP_VISION_UP_1", 0.25, "naive_defender_play_layer", 1, "no_reach")
    assert list(row)[-12:-7] == SUPPLIED   # TD-LAB-REV2-L8-columns: reengage_0/1 follow prefight; TD-LAB-REV3-C-columns: the five REV3C columns follow them


@pytest.mark.parametrize("baseline", ["naive_attacker", "naive_defender", "naive_defender_attacker_layer",
                                      "naive_defender_play_layer", "none"])
@pytest.mark.parametrize("prefight", ["ok", "no_fit", "unroutable", "no_reach"])
def test_every_baseline_and_prefight_value_is_written_as_given(tmp_path, baseline, prefight):
    path = tmp_path / "r.csv"
    write_rows([_row(baseline=baseline, prefight=prefight)], path)
    header, line = _read(path)
    got = dict(zip(header, line))
    assert got["baseline"] == baseline and got["prefight"] == prefight


def test_an_empty_knob_value_is_a_blank_cell_and_a_float_keeps_the_fixed_format(tmp_path):
    path = tmp_path / "r.csv"
    write_rows([_row(knob="none", knob_value=None), _row(knob="OM_TP_FIRING_ARC_DEG", knob_value=120.0)], path)
    header, a, b = _read(path)
    col = header.index("knob_value")
    assert (a[col], b[col]) == ("", "120.0")


def test_a_row_written_for_a_defect_cap_fight_is_still_a_row(tmp_path):
    """Spec cell/scan: draw or cap marks the cell defect and the scan continues, so the row exists with its outcome."""
    path = tmp_path / "r.csv"
    write_rows([_row(_result(outcome="cap", winner=None, agreement="n/a"))], path)
    header, line = _read(path)
    assert dict(zip(header, line))["outcome"] == "cap"
