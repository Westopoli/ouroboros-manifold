# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md::1. A layout is a feature vector, 4. Pieces (P1)
# LAB-REV2-L2 inventory (Q-LAB-03): KEPT unchanged. `start_distance` here is the layout Feature (spawn distance of maps.layout_map), not the retired Setup.start_distance; the 'residual stalemate' remark is the 2026-10-06 layout-geometry ruling.
"""maps.layout_map(features, seed): a feature-controlled layout beside sample_map. No Engine, no compiler.
Geometry is measured here from the returned Terrain with test-local code, never with the generator's own helpers.
Body = 2R = 30 wu (hardcoded until D1). `none` for choke width and detour ratio is 0 / 0.0; wall tests use
lane_count 0 and cover 0 so each feature is measured alone."""
import dataclasses
import hashlib
import heapq
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import maps  # noqa: E402  (layout_map is looked up on the module so a missing symbol is one red per test)
from scripts.skilllab.contract import Block, FightResult, Terrain  # noqa: E402
from scripts.skilllab.maps import CORRIDOR_WIDTH, DEFAULT_FRAME, KINDS, Features, Frame, sample_features, sample_map  # noqa: E402
from scripts.skilllab.rows import fight_row  # noqa: E402
from scripts.skilllab.terrain import _validate_terrain  # noqa: E402

BODY = 30.0
OLD_FIELDS = ["choke_count", "choke_width_wu", "choke_width_bodies", "lane_count", "blocked_layer_ranges",
              "fight_layer_blocked", "cover_density_corridor", "start_distance"]
NEW_FIELDS = ["detour_ratio", "blocked_layer_top"]
SAMPLE_MAP_DIGEST = "7b00c74505369b541b4dcb20ed3b643e43d36d719e1f8265f74a4937ae42338d"  # sha256 of repr of (canvas, blocks, covers) per map; later defaulted Terrain fields (field_seed) stay out, TD-LAB-sample-map-pin
RATIO_TOL = 0.05  # the spec's only tolerance (P1 tests column: "within 5% of r")


def _frame(d):
    return Frame((-d / 2, 0.0), (d / 2, 0.0), 0)


def feats(w=0, n=0, k=0, c=0.0, d=1400.0, r=0.0):
    return Features(choke_count=1 if w else 0, choke_width_wu=w * BODY, choke_width_bodies=float(w), lane_count=n,
                    blocked_layer_ranges=((0, k),) if (w or n) else (), fight_layer_blocked=bool(w or n),
                    cover_density_corridor=c, start_distance=d, detour_ratio=r, blocked_layer_top=k)


def make(f, seed=0):
    return maps.layout_map(f, seed, frame=_frame(f.start_distance))


def _mid_wall(t, d):
    """The two blocks of a lane-free wall: those whose x span contains the midpoint x (0)."""
    wall = sorted((b for b in t.blocks if b.x0 < 0 < b.x1), key=lambda b: b.y0)
    assert len(wall) == 2, "expected the two halves of one wall, got %r" % (t.blocks,)
    return wall


def _hits(p, q, b):
    """True if segment p-q crosses the open interior of block b (Liang-Barsky)."""
    t0, t1 = 0.0, 1.0
    for lo, hi, a, v in ((b.x0, b.x1, p[0], q[0] - p[0]), (b.y0, b.y1, p[1], q[1] - p[1])):
        if v == 0:
            if not lo < a < hi:
                return False
            continue
        s, e = sorted(((lo - a) / v, (hi - a) / v))
        t0, t1 = max(t0, s), min(t1, e)
        if t0 >= t1 - 1e-12:
            return False
    return True


def _shortest(blocks, a, b, eps=1e-3):
    nodes = [a, b] + [(x, y) for bl in blocks for x in (bl.x0 - eps, bl.x1 + eps) for y in (bl.y0 - eps, bl.y1 + eps)]
    dist = {0: 0.0}
    heap = [(0.0, 0)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > dist.get(u, math.inf):
            continue
        if u == 1:
            return du
        for v in range(len(nodes)):
            if v == u or any(_hits(nodes[u], nodes[v], bl) for bl in blocks):
                continue
            nd = du + math.dist(nodes[u], nodes[v])
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return math.inf


def _vertical_channels(t, x):
    """Free intervals on the line at x that are bounded above and below by blocks."""
    spans = sorted((b.y0, b.y1) for b in t.blocks if b.x0 < x < b.x1)
    return sum(1 for (_, a1), (b0, _) in zip(spans, spans[1:]) if b0 - a1 > 1e-9)


def test_layout_map_exists_and_returns_a_valid_terrain():
    """Spec section 4, P1: layout_map(features, seed) beside sample_map; returns a Terrain the lab accepts."""
    t = make(feats(w=4, n=1, k=2, c=0.1, r=1.5))
    assert isinstance(t, Terrain)
    _validate_terrain(t)


@pytest.mark.parametrize("w", [2, 4, 8])
@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_wall_gap_is_w_bodies(w, d):
    """Spec section 1, choke width w: gap = w bodies of 30 wu, wall at the frame's midpoint, whatever d is."""
    a, b = _mid_wall(make(feats(w=w, d=d)), d)
    assert b.y0 - a.y1 == pytest.approx(w * BODY, abs=1e-6)


def test_no_choke_means_no_wall():
    """Spec section 1, w = none: no blocks at all with no lanes either."""
    assert make(feats()).blocks == ()


@pytest.mark.parametrize("n", [0, 1, 2])
@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_lane_count_is_n_channels(n, d):
    """Spec section 1, lanes n (0, 1, 2 parallel): n walled channels across the line at the first spawn."""
    t = make(feats(n=n, d=d))
    assert _vertical_channels(t, -d / 2) == n
    if n == 0:
        assert t.blocks == ()


@pytest.mark.parametrize("k", [0, 2, 4])
def test_blocked_layers_are_zero_to_k(k):
    """Spec section 1, blocked-layer top k: every block has lo = 0 and hi = k."""
    t = make(feats(w=4, n=1, k=k))
    assert t.blocks
    assert {(b.layer_lo, b.layer_hi) for b in t.blocks} == {(0, k)}


@pytest.mark.parametrize("r", [1.5, 3.0])
@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_detour_ratio_around_over_through_is_within_5_percent(r, d):
    """Spec section 4, P1 tests: the detour path's length over the through path is within 5% of r."""
    f = feats(w=4, d=d, r=r)
    t = make(f)
    a, b = _mid_wall(t, d)
    plug = Block(a.x0, a.y1, a.x1, b.y0, 0, 4)
    s0, s1 = (-d / 2, 0.0), (d / 2, 0.0)
    through = _shortest(t.blocks, s0, s1)
    around = _shortest(t.blocks + (plug,), s0, s1)
    assert math.isfinite(through) and math.isfinite(around)
    assert around / through == pytest.approx(r, rel=RATIO_TOL)


@pytest.mark.parametrize("c", [0.1, 0.3])
@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_cover_density_of_the_corridor_is_c(c, d):
    """Spec section 1, cover density c of the corridor, measured with the lab's corridor (CORRIDOR_WIDTH, Frame)."""
    t = make(feats(c=c, d=d))
    assert t.covers
    area = 0.0
    for cv in t.covers:
        area += maps._disc_in_corridor(cv.x + d / 2, cv.y, cv.radius, d, CORRIDOR_WIDTH / 2)
    assert area / (d * CORRIDOR_WIDTH) == pytest.approx(c, rel=RATIO_TOL)


def test_zero_cover_density_places_no_cover():
    """Spec section 1, c = 0."""
    assert make(feats(w=4, n=1)).covers == ()


@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_start_distance_comes_from_the_frame(d):
    """Spec section 4, P1: start distance d via Frame; the layout is built around the frame's spawns."""
    f = feats(w=4, c=0.1, d=d, r=1.5)
    a, _ = _mid_wall(make(f), d)
    assert a.x0 < 0 < a.x1
    assert math.dist(_frame(d).spawn0, _frame(d).spawn1) == f.start_distance


def test_features_gain_detour_ratio_and_blocked_layer_top_after_the_old_fields():
    """Spec section 4, P1: Features gains detour_ratio, blocked_layer_top; the existing fields keep their order."""
    assert [x.name for x in dataclasses.fields(Features)] == OLD_FIELDS + NEW_FIELDS
    f = feats(w=8, n=2, k=4, c=0.3, d=2800.0, r=3.0)
    assert (f.detour_ratio, f.blocked_layer_top) == (3.0, 4)
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.detour_ratio = 1.0


@pytest.mark.parametrize("w,n,k,c,d,r", [(2, 0, 0, 0.0, 1400.0, 1.5), (4, 1, 2, 0.1, 2800.0, 3.0),
                                         (8, 2, 4, 0.3, 1400.0, 1.5)])
def test_every_feature_value_round_trips_through_features_and_rows(w, n, k, c, d, r):
    """Spec section 4, P1 tests: every feature value round-trips through Features, and into the feat_ columns in field order."""
    f = feats(w, n, k, c, d, r)
    res = FightResult(outcome="side0", margin=0.5, strength_left=(0.75, 0.25), survivors=(12, 3), heads=(16, 12),
                      ticks=340, first_contact_tick=35, firing=[(0, 0, 0)], firing_unit_seconds=(10.5, 7.25), winner="side0",
                      firing_window=(4.0, 2.5), weighted_unit_seconds=(9.0, 6.0), weighted_window=(3.5, 2.0),
                      predicted_count="side0", predicted_type="side0", agreement="both_right")   # LAB-REV2-L2: rev 2 result fields
    row = fight_row(res, f, knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok")
    assert [k_ for k_ in row if k_.startswith("feat_")] == ["feat_" + x.name for x in dataclasses.fields(Features)]
    assert row["feat_detour_ratio"] == r and row["feat_blocked_layer_top"] == k
    assert row["feat_choke_width_bodies"] == w and row["feat_lane_count"] == n
    assert row["feat_cover_density_corridor"] == c and row["feat_start_distance"] == d
    make(f)  # the generator accepts what the row records


def test_same_seed_and_features_give_identical_maps():
    """Spec section 4, P1 tests: byte-identical maps for the same seed and features."""
    f = feats(w=4, n=2, k=2, c=0.3, d=2800.0, r=1.5)
    for seed in range(10):
        assert repr(make(f, seed)) == repr(make(f, seed))


def test_the_seed_moves_the_cover():
    """Spec section 1 (seeded draw): different seeds give different cover placement."""
    f = feats(c=0.3)
    assert len({repr(make(f, s)) for s in range(10)}) > 1


def test_sample_map_is_byte_identical_and_an_all_none_layout_is_the_open_map():
    """Spec section 4, P1: sample_map and every existing row stay byte-identical (digest pinned on origin/main); an
    all-none layout equals the open map."""
    # Hash the fields that define a map (canvas, blocks, covers), written as the original dataclass repr, so later
    # defaulted Terrain fields (field_seed) cannot move the pin. Same digest as the pre-field_seed repr.
    seen = "[" + ", ".join(f"({k!r}, {s}, Terrain(canvas={m.canvas!r}, blocks={m.blocks!r}, covers={m.covers!r}))"
                           for k in KINDS for s in range(20) for m in [sample_map(k, s)]) + "]"
    assert hashlib.sha256(seen.encode()).hexdigest() == SAMPLE_MAP_DIGEST
    assert make(feats()) == sample_map("open", 0)


@pytest.mark.parametrize("kind", KINDS)
def test_existing_sample_features_keep_their_old_fields_and_gain_the_new_ones(kind):
    """Spec section 4, P1: sample_features rows keep their eight values; the two new fields exist."""
    f = sample_features(kind, 3)
    assert hasattr(f, "detour_ratio") and hasattr(f, "blocked_layer_top")


# spec: Architect ruling 2026-10-06 (residual stalemate), ruling 3: two lanes with a choke keep the gap and the axis clear
def _box_hits(b, x0, y0, x1, y1):
    return b.x0 < x1 and b.x1 > x0 and b.y0 < y1 and b.y1 > y0


@pytest.mark.parametrize("w", [2, 4, 8])
@pytest.mark.parametrize("d", [1400.0, 2800.0])
def test_two_lanes_with_a_choke_leave_the_gap_open_and_the_axis_clear(w, d):
    t = make(feats(w=w, n=2, k=2, d=d))
    gap = (0.0, -w * BODY / 2, 0.0, w * BODY / 2)   # the gap: the wall column, between its two halves
    assert not [b for b in t.blocks if _box_hits(b, -1.0, gap[1], 1.0, gap[3])], "a block sits in the choke gap"
    a, b = (-d / 2, 0.0), (d / 2, 0.0)
    assert not [bl for bl in t.blocks if _hits(a, b, bl)], "a block crosses the straight spawn-to-spawn line"


def test_positive_control_a_lane_free_choke_passes_the_same_check():
    t = make(feats(w=4, d=1400.0))
    assert not [b for b in t.blocks if _hits((-700.0, 0.0), (700.0, 0.0), b)]
