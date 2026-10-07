# spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md::features lane
"""maps.sample_features and the feat_<field> columns of rows.fight_row. No Engine, no compiler."""
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import FightResult  # noqa: E402
from scripts.skilllab.maps import DEFAULT_FRAME, KINDS, WALL_GAP, Features, Frame, sample_features, sample_map  # noqa: E402
from scripts.skilllab.rows import fight_row, write_rows  # noqa: E402

SEEDS = range(30)
FIELDS = ["choke_count", "choke_width_wu", "choke_width_bodies", "lane_count", "blocked_layer_ranges",
          "fight_layer_blocked", "cover_density_corridor", "start_distance", "detour_ratio", "blocked_layer_top"]
CANVAS = (4000.0, 4000.0)
DEFAULT_RADIUS = 15.0   # wu, the spec's value when no engine is given


def _result():
    return FightResult(outcome="side0", margin=0.5, strength_left=(0.75, 0.25), survivors=(12, 3), heads=(16, 12),
                       ticks=340, first_contact_tick=35, firing=[(0, 0, 0)], firing_unit_seconds=(10.5, 7.25))


def test_features_is_a_frozen_dataclass_with_the_spec_fields_in_order():
    """Spec: frozen dataclass; fields as listed."""
    assert dataclasses.is_dataclass(Features)
    assert [f.name for f in dataclasses.fields(Features)] == FIELDS
    f = sample_features("open", 0, CANVAS)
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.choke_count = 5


@pytest.mark.parametrize("kind", KINDS)
def test_sample_features_is_deterministic_per_seed(kind):
    """Spec: deterministic per seed."""
    for s in SEEDS:
        assert sample_features(kind, s, CANVAS) == sample_features(kind, s, CANVAS)


@pytest.mark.parametrize("kind", KINDS)
def test_field_types_match_the_spec(kind):
    """Spec: int / float / tuple of (int, int) / bool types."""
    f = sample_features(kind, 3, CANVAS)
    assert type(f.choke_count) is int and type(f.lane_count) is int
    assert type(f.choke_width_wu) is float and type(f.choke_width_bodies) is float
    assert type(f.cover_density_corridor) is float and type(f.start_distance) is float
    assert type(f.fight_layer_blocked) is bool
    assert type(f.blocked_layer_ranges) is tuple
    assert all(type(r) is tuple and len(r) == 2 and all(type(v) is int for v in r) for r in f.blocked_layer_ranges)


def test_bodies_equals_wu_over_two_radii_with_no_engine():
    """Spec: gap over two collision radii; 15 wu when no engine is given."""
    for s in SEEDS:
        f = sample_features("wall", s, CANVAS)
        assert f.choke_width_bodies == pytest.approx(f.choke_width_wu / (2 * DEFAULT_RADIUS))


def test_open_map_records_zeros_and_an_empty_tuple():
    """Spec: open records zeros and an empty tuple."""
    for s in SEEDS:
        f = sample_features("open", s, CANVAS)
        assert (f.choke_count, f.choke_width_wu, f.choke_width_bodies, f.lane_count) == (0, 0.0, 0.0, 0)
        assert f.blocked_layer_ranges == () and f.fight_layer_blocked is False
        assert f.cover_density_corridor == 0.0


def test_wall_gives_one_choke_with_a_width_inside_wall_gap():
    """Spec: wall gives choke_count 1, width inside WALL_GAP, no lane."""
    for s in SEEDS:
        f = sample_features("wall", s, CANVAS)
        assert f.choke_count == 1 and f.lane_count == 0
        assert WALL_GAP[0] - 1e-6 <= f.choke_width_wu <= WALL_GAP[1] + 1e-6


def test_wall_width_is_the_gap_between_the_two_wall_blocks():
    """Spec: choke_width_wu is the wall gap (cross-checked against sample_map)."""
    for s in SEEDS:
        a, b = sample_map("wall", s, CANVAS).blocks
        assert sample_features("wall", s, CANVAS).choke_width_wu == pytest.approx(b.y0 - a.y1)


def test_lane_gives_one_lane_and_no_choke():
    """Spec: lane gives lane_count 1."""
    for s in SEEDS:
        f = sample_features("lane", s, CANVAS)
        assert f.lane_count == 1 and f.choke_count == 0 and f.choke_width_wu == 0.0


def test_block_records_one_range_matching_the_map():
    """Spec: block records one range; fight_layer_blocked is whether it contains the fight layer."""
    for s in SEEDS:
        f = sample_features("block", s, CANVAS)
        b = sample_map("block", s, CANVAS).blocks[0]
        assert f.blocked_layer_ranges == ((b.layer_lo, b.layer_hi),)
        assert f.fight_layer_blocked == (b.layer_lo <= DEFAULT_FRAME.layer <= b.layer_hi)
        assert f.choke_count == 0 and f.lane_count == 0


def test_ranges_are_one_per_block_in_block_order():
    """Spec: one (lo, hi) per block, in block order."""
    for kind in ("block", "wall", "lane"):
        for s in SEEDS:
            blocks = sample_map(kind, s, CANVAS).blocks
            assert sample_features(kind, s, CANVAS).blocked_layer_ranges == tuple((b.layer_lo, b.layer_hi) for b in blocks)


def test_fight_layer_blocked_follows_the_frames_layer():
    """Spec: any block's range contains the frame's fight layer."""
    for s in SEEDS:
        for layer in range(5):
            frame = Frame(DEFAULT_FRAME.spawn0, DEFAULT_FRAME.spawn1, layer)
            f = sample_features("wall", s, CANVAS, frame)
            assert f.fight_layer_blocked == any(lo <= layer <= hi for lo, hi in f.blocked_layer_ranges)


def test_start_distance_is_the_spawn_distance():
    """Spec: distance between the frame's spawns."""
    assert sample_features("open", 0, CANVAS).start_distance == pytest.approx(890.0)
    frame = Frame((0.0, 0.0), (300.0, 400.0), 0)
    assert sample_features("open", 0, CANVAS, frame).start_distance == pytest.approx(500.0)


def test_cover_density_is_zero_without_cover_and_bounded_with_it():
    """Spec: 0.0 when none; otherwise disc area in the corridor over corridor area, so within [0, 1]."""
    for kind in ("block", "wall", "lane"):
        assert sample_features(kind, 1, CANVAS).cover_density_corridor == 0.0
    vals = [sample_features("cover_field", s, CANVAS).cover_density_corridor for s in SEEDS]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert any(v > 0.0 for v in vals)  # the first disc is drawn inside the corridor


def test_cover_density_matches_a_hand_computed_value_for_a_disc_fully_inside():
    """Spec: area of discs inside the 600 wu wide corridor over corridor area (frame spawns 890 apart)."""
    for s in SEEDS:
        covers = sample_map("cover_field", s, CANVAS).covers
        inside = [c for c in covers if abs(c.y) + c.radius <= 300.0 and abs(c.x) + c.radius <= 445.0]
        if len(inside) == len(covers) and covers:
            area = sum(math.pi * c.radius ** 2 for c in covers)
            assert sample_features("cover_field", s, CANVAS).cover_density_corridor == pytest.approx(area / (890.0 * 600.0), rel=1e-3)
            return
    pytest.skip("no seed had every disc inside the corridor")


def test_sample_map_is_unchanged_by_feature_sampling():
    """Spec: sample_map is not re-drawn or altered."""
    for kind in KINDS:
        before = sample_map(kind, 4, CANVAS)
        sample_features(kind, 4, CANVAS)
        assert sample_map(kind, 4, CANVAS) == before


def test_unknown_kind_raises_value_error():
    with pytest.raises(ValueError):
        sample_features("nope", 0, CANVAS)


def test_fight_row_without_features_is_byte_identical_to_before(tmp_path):
    """Spec: no features argument adds no column."""
    plain = fight_row(_result(), play="reach")
    assert list(plain) == ["play", "outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1",
                           "heads_0", "heads_1", "ticks", "first_contact_tick", "firing_unit_seconds_0", "firing_unit_seconds_1"]
    assert fight_row(_result(), None, play="reach") == plain
    write_rows([plain], tmp_path / "a.csv")
    assert b"feat_" not in (tmp_path / "a.csv").read_bytes()


def test_fight_row_with_features_adds_one_feat_column_per_field():
    """Spec: one column per field named feat_<field>, values carried."""
    f = sample_features("wall", 2, CANVAS)
    row = fight_row(_result(), f, play="reach")
    for name in FIELDS:
        assert row["feat_" + name] == getattr(f, name)
    assert [k for k in row if k.startswith("feat_")] == ["feat_" + n for n in FIELDS]
    base = fight_row(_result(), play="reach")
    assert {k: v for k, v in row.items() if not k.startswith("feat_")} == base


def test_fight_row_features_by_keyword_and_label_order_kept():
    f = sample_features("open", 0, CANVAS)
    row = fight_row(_result(), features=f, play="reach", n=1)
    assert list(row)[:2] == ["play", "n"]


def test_features_rows_pass_through_write_rows(tmp_path):
    """Spec: the feat_ columns are written like any other."""
    rows = [fight_row(_result(), sample_features(k, 1, CANVAS), play=k) for k in KINDS]
    write_rows(rows, tmp_path / "f.csv")
    head = (tmp_path / "f.csv").read_text().splitlines()[0].split(",")
    assert all("feat_" + n in head for n in FIELDS)
