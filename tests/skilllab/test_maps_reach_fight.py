# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, situation sampler (maps must reach the fight)
"""Sampled maps must be able to change the fight (defect measured 2026-10-05: five sampled maps, every fight identical to open).

Reading of the sampler: all units fight on the layer the scene gives its groups (read from the built Setup, not hard-coded);
play coordinates are centred, so the spawns are the group anchors minus half the canvas. Wall: a rect line crossing the straight
segment between the spawns, with the gap placed anywhere along the wall (so not always on the segment). Lane: two rects bounding the
segment, one each side. Block: a rect that touches the segment. Cover field: a disc that touches the segment and is tall enough to
block the fight layer. No Engine, no compiler.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.maps import sample_map  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402

SEEDS = range(50)


def scene(terrain):
    """(spawn0, spawn1, fight_layer) in play coordinates for the landscape scene on this terrain."""
    s = with_terrain(asym_play(16, Side("blob"), Side("blob")), terrain)(16, False)
    dx, dy = terrain.canvas[0] / 2, terrain.canvas[1] / 2
    g0, g1 = (next(g for g in s.groups if g.side == k) for k in (0, 1))
    assert g0.layer == g1.layer
    return (g0.x - dx, g0.y - dy), (g1.x - dx, g1.y - dy), g0.layer


def seg_dist(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    t = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
    t = max(0.0, min(1.0, t))
    return ((px - ax - t * (bx - ax)) ** 2 + (py - ay - t * (by - ay)) ** 2) ** 0.5


def rect_hits_segment(b, a, c):
    """Segment a-c (horizontal in these scenes, y equal) against the rect, by sampling the segment finely."""
    return any(b.x0 <= a[0] + (c[0] - a[0]) * i / 200 <= b.x1 and b.y0 <= a[1] + (c[1] - a[1]) * i / 200 <= b.y1
               for i in range(201))


@pytest.mark.parametrize("kind", ["block", "wall", "lane"])
def test_every_block_includes_the_fight_layer(kind):
    """Every block of every sampled seed spans the layer the groups fight on (R: a block off that layer is invisible to movement)."""
    for seed in SEEDS:
        t = sample_map(kind, seed)
        _, _, layer = scene(t)
        for b in t.blocks:
            assert b.layer_lo <= layer <= b.layer_hi, "%s seed %d: %r misses fight layer %d" % (kind, seed, b, layer)


def test_a_block_touches_the_segment_between_the_spawns():
    for seed in SEEDS:
        t = sample_map("block", seed)
        a, c, _ = scene(t)
        assert any(rect_hits_segment(b, a, c) for b in t.blocks), "block seed %d: %r misses segment %r-%r" % (seed, t.blocks, a, c)


def test_a_wall_crosses_the_segment_and_the_gap_is_not_always_on_it():
    on_segment = 0
    for seed in SEEDS:
        t = sample_map("wall", seed)
        a, c, _ = scene(t)
        x0, x1 = t.blocks[0].x0, t.blocks[0].x1
        lo, hi = min(b.y0 for b in t.blocks), max(b.y1 for b in t.blocks)
        assert a[0] < x0 and x1 < c[0] and lo <= a[1] <= hi, "wall seed %d: x %r..%r y %r..%r does not cross %r-%r" % (seed, x0, x1, lo, hi, a, c)
        on_segment += not any(rect_hits_segment(b, a, c) for b in t.blocks)
    assert 0 < on_segment < len(SEEDS), "gap is on the segment for %d of %d seeds" % (on_segment, len(SEEDS))


def test_a_lane_has_one_wall_each_side_of_the_segment_both_along_it():
    for seed in SEEDS:
        t = sample_map("lane", seed)
        a, c, _ = scene(t)
        below, above = sorted(t.blocks, key=lambda b: b.y0)
        assert below.y1 <= a[1] <= above.y0, "lane seed %d: walls %r do not bound y=%r" % (seed, t.blocks, a[1])
        for b in (below, above):
            assert b.x0 <= a[0] and c[0] <= b.x1, "lane seed %d: %r does not run along %r-%r" % (seed, b, a, c)


def test_a_cover_field_has_a_tall_enough_disc_on_the_corridor():
    for seed in SEEDS:
        t = sample_map("cover_field", seed)
        a, c, layer = scene(t)
        assert any(d.height > layer and seg_dist(d.x, d.y, a, c) <= d.radius for d in t.covers), \
            "cover_field seed %d: no disc touches %r-%r: %r" % (seed, a, c, t.covers)
