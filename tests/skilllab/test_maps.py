# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, situation sampler (space maps, sampled and asymmetric)
"""maps.sample_map / sample_maps: deterministic space maps in play coordinates, the documented draw ranges,
wall and lane geometry, asymmetry, and acceptance by terrain.with_terrain. No Engine, no compiler.
The ranges are documented design numbers of the sampler, not pass marks."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym_mod  # noqa: E402
import scripts.skilllab.plays as plays_mod  # noqa: E402
from scripts.skilllab.contract import Block, Cover, Terrain  # noqa: E402
from scripts.skilllab.maps import KINDS, LANE_CENTRE, LANE_HALF, LANE_LENGTH_PAST, LANE_THICK, sample_map, sample_maps  # noqa: E402
from scripts.skilllab.plays import blob_play  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402

SEEDS = range(50)
NON_OPEN = ("block", "wall", "lane", "cover_field")
BIG = 1500.0
TOL = 1e-6


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    stats = {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
             "speed": 5.0, "sensor_radius": 700.0, "layer_transition_time": 0.0, "aoe_radius": 0.0}
    monkeypatch.setattr(plays_mod, "unit_stats", lambda name: dict(stats))
    monkeypatch.setattr(asym_mod, "unit_stats", lambda name: dict(stats))


def _in(v, lo, hi):
    return lo - TOL <= v <= hi + TOL


def _layers_ok(b):
    return isinstance(b.layer_lo, int) and isinstance(b.layer_hi, int) and 0 <= b.layer_lo <= 2 \
        and b.layer_lo <= b.layer_hi <= 4


def _overlap(a, b):
    return a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1


def _mirror(t, axis):
    """Terrain reflected about the x axis (y -> -y) or the y axis (x -> -x), as comparable sets."""
    if axis == "x":
        blocks = {(b.x0, -b.y1, b.x1, -b.y0, b.layer_lo, b.layer_hi) for b in t.blocks}
        covers = {(c.x, -c.y, c.radius, c.height) for c in t.covers}
    else:
        blocks = {(-b.x1, b.y0, -b.x0, b.y1, b.layer_lo, b.layer_hi) for b in t.blocks}
        covers = {(-c.x, c.y, c.radius, c.height) for c in t.covers}
    return blocks, covers


def _own(t):
    return ({(b.x0, b.y0, b.x1, b.y1, b.layer_lo, b.layer_hi) for b in t.blocks},
            {(c.x, c.y, c.radius, c.height) for c in t.covers})


def test_kinds_are_the_five_in_order():
    """KINDS lists open, block, wall, lane, cover_field in that order."""
    assert KINDS == ("open", "block", "wall", "lane", "cover_field")


@pytest.mark.parametrize("kind", KINDS)
def test_same_arguments_give_equal_terrain(kind):
    """Determinism: sample_map(kind, seed) twice is an equal Terrain, for several seeds."""
    for seed in range(8):
        assert sample_map(kind, seed) == sample_map(kind, seed)


@pytest.mark.parametrize("kind", NON_OPEN)
def test_different_seeds_differ(kind):
    """Neighbouring seeds give different terrain for every kind but open."""
    maps = [sample_map(kind, s) for s in range(8)]
    assert all(a != b for a, b in zip(maps, maps[1:]))
    assert len({repr(m) for m in maps}) == len(maps)


def test_open_is_empty_and_seed_independent():
    """open: a Terrain with the canvas and no blocks, no covers, for any seed."""
    for seed in range(5):
        assert sample_map("open", seed) == Terrain(canvas=(4000.0, 4000.0))


@pytest.mark.parametrize("kind", KINDS)
def test_canvas_passes_through_unchanged(kind):
    """The canvas argument is the Terrain canvas; the default is (4000.0, 4000.0)."""
    assert sample_map(kind, 0).canvas == (4000.0, 4000.0)
    assert sample_map(kind, 0, canvas=(5000.0, 3000.0)).canvas == (5000.0, 3000.0)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("canvas", [(0.0, 4000.0), (4000.0, -1.0), (28001.0, 4000.0), (float("nan"), 4000.0),
                                     (4000.0, float("inf"))])
def test_bad_canvas_is_refused_like_with_terrain(kind, canvas):
    """A canvas with a side outside (0, 28000] or not finite raises ValueError."""
    with pytest.raises(ValueError):
        sample_map(kind, 0, canvas=canvas)


def test_unknown_kind_raises():
    """sample_map and sample_maps refuse an unknown kind."""
    with pytest.raises(ValueError):
        sample_map("maze", 0)
    with pytest.raises(ValueError):
        sample_maps(("open", "maze"), 1)


@pytest.mark.parametrize("kind", KINDS)
def test_everything_lies_within_1500_of_the_origin(kind):
    """Every block corner and cover centre is within +-1500 on each axis, over 50 seeds."""
    for seed in SEEDS:
        t = sample_map(kind, seed)
        for b in t.blocks:
            assert all(abs(v) <= BIG + TOL for v in (b.x0, b.y0, b.x1, b.y1)), (seed, b)
        for c in t.covers:
            assert abs(c.x) <= BIG and abs(c.y) <= BIG, (seed, c)


@pytest.mark.parametrize("kind", KINDS)
def test_every_block_passes_the_engine_refusals(kind):
    """Non-zero area, ordered corners, 0 <= layer_lo <= layer_hi <= 4; covers have positive radius and int heights 0..5."""
    for seed in SEEDS:
        t = sample_map(kind, seed)
        for b in t.blocks:
            assert isinstance(b, Block) and b.x0 < b.x1 and b.y0 < b.y1, (seed, b)
            assert 0 <= b.layer_lo <= b.layer_hi <= 4 and isinstance(b.layer_lo, int) and isinstance(b.layer_hi, int)
        for c in t.covers:
            assert isinstance(c, Cover) and c.radius > 0 and isinstance(c.height, int) and 0 <= c.height <= 5


def test_block_ranges():
    """block: one Block, width and height in [200, 800], centre in [-600, 600], layer_lo 0..2, layer_hi lo..4."""
    for seed in SEEDS:
        t = sample_map("block", seed)
        assert len(t.blocks) == 1 and t.covers == ()
        b = t.blocks[0]
        assert _in(b.x1 - b.x0, 200, 800) and _in(b.y1 - b.y0, 200, 800), (seed, b)
        assert _in((b.x0 + b.x1) / 2, -600, 600) and _in((b.y0 + b.y1) / 2, -600, 600), (seed, b)
        assert _layers_ok(b), (seed, b)


def _wall_parts(t):
    lower, upper = sorted(t.blocks, key=lambda b: b.y0)
    return lower, upper


def test_wall_ranges_and_gap():
    """wall: two Blocks along y sharing x extent and layers; L in [1200, 2400], thickness in [60, 120],
    centre x in [-500, 500], centre y in [-300, 300], gap in [150, 400] strictly inside the wall."""
    for seed in SEEDS:
        t = sample_map("wall", seed)
        assert len(t.blocks) == 2 and t.covers == ()
        lower, upper = _wall_parts(t)
        assert lower.x0 == upper.x0 and lower.x1 == upper.x1, seed
        assert (lower.layer_lo, lower.layer_hi) == (upper.layer_lo, upper.layer_hi) and _layers_ok(lower)
        assert _in(lower.x1 - lower.x0, 60, 120), seed
        assert _in((lower.x0 + lower.x1) / 2, -500, 500), seed
        length = upper.y1 - lower.y0
        gap = upper.y0 - lower.y1
        assert _in(length, 1200, 2400) and _in(gap, 150, 400), (seed, length, gap)
        assert _in((upper.y1 + lower.y0) / 2, -300, 300), seed
        assert lower.y0 < lower.y1 < upper.y0 < upper.y1, seed


def test_wall_pieces_do_not_overlap_and_lengths_add_up():
    """The two wall pieces do not overlap and their combined length is L minus the gap."""
    for seed in SEEDS:
        lower, upper = _wall_parts(sample_map("wall", seed))
        assert not _overlap(lower, upper), seed
        length, gap = upper.y1 - lower.y0, upper.y0 - lower.y1
        assert (lower.y1 - lower.y0) + (upper.y1 - upper.y0) == pytest.approx(length - gap, abs=TOL, rel=0)


def _lane_walls(t):
    lower, upper = sorted(t.blocks, key=lambda b: b.y0)
    return lower, upper


def test_lane_ranges():
    """lane: two Blocks along x, one layer range; each wall spans both spawns (x = -445, 445 in the default
    frame) plus a drawn extra past each end in LANE_LENGTH_PAST; thickness in LANE_THICK; lane half-width in
    LANE_HALF; lane centre y within LANE_CENTRE of 0."""
    for seed in SEEDS:
        t = sample_map("lane", seed)
        assert len(t.blocks) == 2 and t.covers == ()
        lower, upper = _lane_walls(t)
        assert (lower.layer_lo, lower.layer_hi) == (upper.layer_lo, upper.layer_hi) and _layers_ok(lower)
        for w in (lower, upper):
            assert _in(-445 - w.x0, *LANE_LENGTH_PAST) and _in(w.x1 - 445, *LANE_LENGTH_PAST), (seed, w)
            assert _in(w.y1 - w.y0, *LANE_THICK), (seed, w)
        lane_lo, lane_hi = lower.y1, upper.y0
        assert _in((lane_hi - lane_lo) / 2, *LANE_HALF), seed
        assert _in((lane_lo + lane_hi) / 2, -LANE_CENTRE, LANE_CENTRE), seed


def test_lane_walls_do_not_overlap_the_lane_or_each_other():
    """The lower wall lies below the lane, the upper above it, and the walls do not overlap."""
    for seed in SEEDS:
        lower, upper = _lane_walls(sample_map("lane", seed))
        assert lower.y1 < upper.y0 and not _overlap(lower, upper), seed


def test_lane_walls_differ():
    """Asymmetric: the two lane walls are drawn independently, so they differ in extent, over 50 seeds."""
    for seed in SEEDS:
        lower, upper = _lane_walls(sample_map("lane", seed))
        assert (lower.x0, lower.x1) != (upper.x0, upper.x1), seed
        assert lower.y1 - lower.y0 != upper.y1 - upper.y0, seed


def test_cover_field_ranges():
    """cover_field: 3..8 Covers, no blocks, radius in [50, 150], int height 1..5, x in [-1200, 1200], y in [-1000, 1000]."""
    counts = set()
    for seed in SEEDS:
        t = sample_map("cover_field", seed)
        assert t.blocks == () and 3 <= len(t.covers) <= 8, seed
        counts.add(len(t.covers))
        for c in t.covers:
            assert _in(c.radius, 50, 150) and isinstance(c.height, int) and 1 <= c.height <= 5, (seed, c)
            assert _in(c.x, -1200, 1200) and _in(c.y, -1000, 1000), (seed, c)
    assert len(counts) > 1   # n is drawn, not fixed


@pytest.mark.parametrize("kind", NON_OPEN)
@pytest.mark.parametrize("axis", ("x", "y"))
def test_terrain_is_not_mirror_symmetric(kind, axis):
    """Arithmetic of the draws (block centre != 0, wall and lane pieces unequal, covers random): at least 45
    of 50 seeds give terrain that is not its own reflection about the x axis, and the same for the y axis."""
    asymmetric = sum(1 for s in SEEDS if _mirror(sample_map(kind, s), axis) != _own(sample_map(kind, s)))
    assert asymmetric >= 45


def test_mirror_helper_sees_a_symmetric_terrain():
    """Positive control: a hand-made symmetric terrain is recognised as symmetric, open included."""
    sym = Terrain(canvas=(4000.0, 4000.0), blocks=(Block(-100.0, -300.0, 100.0, -100.0), Block(-100.0, 100.0, 100.0, 300.0)))
    assert _mirror(sym, "x") == _own(sym) and _mirror(sym, "y") == _own(sym)
    assert _mirror(sample_map("open", 0), "x") == _own(sample_map("open", 0))


@pytest.mark.parametrize("kind", KINDS)
def test_with_terrain_accepts_every_sampled_map(kind):
    """with_terrain(blob_play(16), map) builds without error for 20 seeds."""
    for seed in range(20):
        setup = with_terrain(blob_play(16), sample_map(kind, seed))(16, False)
        assert setup.terrain is not None and len(setup.terrain.blocks) == len(sample_map(kind, seed).blocks)


def test_sample_maps_index_and_seed_arithmetic():
    """sample_maps: kinds in the order given, per_kind each, map_seed = seed * 1000 + running index."""
    out = sample_maps(("wall", "open", "block"), 2, seed=3)
    assert [(k, s) for k, s, _ in out] == [("wall", 3000), ("wall", 3001), ("open", 3002), ("open", 3003),
                                           ("block", 3004), ("block", 3005)]
    for kind, map_seed, terrain in out:
        assert terrain == sample_map(kind, map_seed)


def test_sample_maps_default_seed_is_zero_and_repeatable():
    """The default seed is 0 and two calls are equal."""
    out = sample_maps(KINDS, 1)
    assert [s for _, s, _ in out] == [0, 1, 2, 3, 4]
    assert out == sample_maps(KINDS, 1, seed=0)
    assert isinstance(out, list) and all(isinstance(r, tuple) and len(r) == 3 for r in out)


@pytest.mark.parametrize("per_kind", (0, -1))
def test_sample_maps_per_kind_below_one_raises(per_kind):
    """per_kind < 1 is a ValueError."""
    with pytest.raises(ValueError):
        sample_maps(("open",), per_kind)
