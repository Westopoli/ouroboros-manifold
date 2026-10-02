# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-17
"""Leaf-05: fight_row and write_rows (write_rows ported from toys/layerlab/layerlab/batch.py)."""
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

FIXED = ["outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1",
         "heads_0", "heads_1", "ticks", "first_contact_tick", "firing_unit_seconds_0",
         "firing_unit_seconds_1"]


def _result(**over):
    base = dict(outcome="side0", margin=0.5, strength_left=(0.75, 0.25), survivors=(12, 3),
                heads=(16, 12), ticks=340, first_contact_tick=35,
                firing=[(0, 0, 0), (5, 2, 1)], firing_unit_seconds=(10.5, 7.25))
    base.update(over)
    return FightResult(**base)


def _read(path):
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


def test_fight_row_labels_first_then_fixed_keys_in_order():
    """AC-17: labels in the order given, then the 12 fixed keys in the spec order; nothing else."""
    row = fight_row(_result(), play="reach", enemy_heads=12)
    assert type(row) is dict
    assert list(row) == ["play", "enemy_heads"] + FIXED


def test_fight_row_values_flatten_the_result():
    """AC-17: tuple fields split into _0/_1 keys; values carried through unchanged."""
    row = fight_row(_result(), play="reach", enemy_heads=12)
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
    row = fight_row(_result(), zeta=1, alpha=2, mid=3)
    assert list(row)[:3] == ["zeta", "alpha", "mid"]
    assert list(row)[3:] == FIXED


def test_fight_row_without_labels_is_just_the_fixed_keys():
    """AC-17 (Existence, no labels): exactly the 12 fixed keys."""
    assert list(fight_row(_result())) == FIXED


def test_fight_row_carries_never_met_and_stalemate_values():
    """AC-17/11: first_contact_tick -1 and a stalemate outcome pass through as given."""
    row = fight_row(_result(outcome="stalemate", first_contact_tick=-1, margin=-0.125,
                            strength_left=(0.5, 0.625), survivors=(8, 10), ticks=6000), n=1)
    assert row["outcome"] == "stalemate" and row["first_contact_tick"] == -1
    assert row["margin"] == -0.125 and row["ticks"] == 6000


def test_fight_row_is_a_pure_function_of_its_inputs():
    """AC-17: the same result and labels give the same row twice; the result is not changed."""
    r = _result()
    before = copy.deepcopy(r)
    assert fight_row(r, play="p", enemy_heads=3) == fight_row(r, play="p", enemy_heads=3)
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
    rows = [fight_row(_result(), play="p", enemy_heads=8), fight_row(_result(margin=-0.25, ticks=99), play="p", enemy_heads=9)]
    p1, p2 = tmp_path / "one.csv", str(tmp_path / "two.csv")
    write_rows(rows, p1)
    write_rows(copy.deepcopy(rows), p2)
    assert p1.read_bytes() == Path(p2).read_bytes()
    assert p1.read_bytes() == (
        b"play,enemy_heads," + ",".join(FIXED).encode() + b"\n"
        b"p,8,side0,0.5,0.75,0.25,12,3,16,12,340,35,10.5,7.25\n"
        b"p,9,side0,-0.25,0.75,0.25,12,3,16,12,99,35,10.5,7.25\n")


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
    rows = [fight_row(_result(), play="reach", enemy_heads=n, replicate=n % 2) for n in (8, 9)]
    path = tmp_path / "r.csv"
    write_rows(rows, path)
    got = _read(path)
    assert got[0] == ["play", "enemy_heads", "replicate"] + FIXED
    assert got[1] == ["reach", "8", "0", "side0", "0.5", "0.75", "0.25", "12", "3", "16", "12", "340", "35", "10.5", "7.25"]
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


@pytest.mark.parametrize("key", FIXED)
def test_fight_row_label_named_like_a_fixed_key_raises_value_error(key):
    """AC-17 Reading: a label that collides with a fixed key raises ValueError."""
    with pytest.raises(ValueError):
        fight_row(_result(), **{key: "x"})


def test_fight_row_label_collision_amid_other_labels_raises():
    """AC-17 Reading: one colliding label among ordinary ones still raises."""
    with pytest.raises(ValueError):
        fight_row(_result(), play="reach", margin=3, enemy_heads=8)


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
