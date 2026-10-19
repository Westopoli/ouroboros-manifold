# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 26 (naive blob that does not fit); decision 25 for the baseline builds
"""LAB-REV2-BASE, part 1 of 3: a naive blob skips blocked cells (scenes.placed_scene(..., "naive") here; sweep._naive_side in
test_sweep_baselines.py). No fight, no engine (the pre-flight of a same-layer scene needs none).

THIS FILE FREEZES THE INTERFACE FOR THE BUILDER (the builder edits scripts/skilllab/scenes.py [L6-owned base], formations.py, sweep.py,
scan.py/contract.py as needed; it edits no test).

Decision 26: "where the blob's next cell is blocked, placement skips to the next free cell in its existing fill order, so the blob keeps
today's shape on open ground (golden hashes unchanged) and fits wherever the play's own units fit."

READINGS (the test writer's; each is one assertion that can be argued with, kept apart from the invariants):
  - A cell is blocked when the unit's position stands in a Block that reaches the group's layer (layer_lo <= layer <= layer_hi), bounds
    inclusive, the same reading as scenes.preflight's no_fit. A block that does not reach the group's layer does not block it.
  - The "existing fill order" is the Fermat-spiral order of formations._blob (anchor first when the count is odd, then the pairs
    p_i / reflection of p_i in order), CONTINUED without end: the cells after the last one of the open-ground blob are the next pairs of
    the same spiral (pairs count and radius unchanged, i = pairs, pairs + 1, ...). A blocked cell is skipped alone (its partner stays);
    the blob takes the first `count` free cells of that order. fakes_baselines.fill_order is that sequence. A count of 1 (pairs = 0) has no
    continuation; no test here uses it on a blocked cell (see the report: question).
  - The group keeps Group.x, Group.y as the blob anchor and the radius 80 + 12 * sqrt(count) (the tests rebuild the fill order from them);
    the units are read where fight() reads them: formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params). HOW the skip
    reaches place() (a "points" formation, a param on "blob", a new formation kind) is the builder's.
INTERFACE ADDED: none at this level. The scene's own words: build.labels["prefight"] stays scenes.preflight of the Setup it built, so a
blob that skipped its blocked cells reads "ok" (today it reads "no_fit").

Red before (built tree 2741d544): a block laid through the blob's cells leaves units in it, so the label reads "no_fit" and the positions
equal the open-ground ones. Green controls: open ground, a block on another layer, a block that misses the blob.
"""
import dataclasses
import hashlib
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import expected_skipping, in_block, keyed, positions, radius_of, slab_through  # noqa: E402
from scripts.skilllab import formations, maps, scenes  # noqa: E402
from scripts.skilllab.contract import Block  # noqa: E402

SEED = 7
SD = 1400.0
HEADS = (8, 16, 17, 48)
REF = Block(-1900.0, -1900.0, -1800.0, -1800.0, 0, 4)      # far from both blobs; only calibrates the layout-to-scene offset


def feats(cover=0.0):
    return maps.Features(choke_count=0, choke_width_wu=0.0, choke_width_bodies=0.0, lane_count=0, blocked_layer_ranges=(),
                         fight_layer_blocked=False, cover_density_corridor=cover, start_distance=SD, detour_ratio=0.0,
                         blocked_layer_top=4)


def build_of(layout, f=None):
    f = f or feats()
    return scenes.placed_scene(layout, "naive", f.start_distance, f)


def offset():
    """(dx, dy) the scene adds to layout coordinates, read from where a reference block lands."""
    layout = dataclasses.replace(maps.layout_map(feats(), SEED), blocks=(REF,))
    b = build_of(layout)(16, False).terrain.blocks[0]
    return b.x0 - REF.x0, b.y0 - REF.y0


def groups_of(setup):
    """{'attacker': side 0 blob, 'defender': side 1 blob} of the naive scene."""
    by_side = {g.side: g for g in setup.groups}
    assert len(setup.groups) == 2 and set(by_side) == {0, 1}, setup.groups
    return {"attacker": by_side[0], "defender": by_side[1]}


def scene_with(block_final, heads):
    """(open-ground setup, blocked setup, build) for heads units on the defender; block_final is a Block in scene coordinates."""
    dx, dy = offset()
    base = maps.layout_map(feats(), SEED)
    layout = dataclasses.replace(base, blocks=base.blocks + (Block(block_final.x0 - dx, block_final.y0 - dy, block_final.x1 - dx,
                                                                   block_final.y1 - dy, block_final.layer_lo, block_final.layer_hi),))
    build = build_of(layout)
    return build_of(base)(heads, False), build(heads, False), build


def open_setup(heads):
    return build_of(maps.layout_map(feats(), SEED))(heads, False)


def cut(setup, who, cutname, layer_lo=0, layer_hi=4):
    """The wall of a case, in scene coordinates, read off the open-ground group so it is sure to land on the blob."""
    g = groups_of(setup)[who]
    if cutname == "one cell":              # a 10 x 10 wu block on the open-ground blob's highest cell (clear of the line to the point)
        px, py = max(positions(g), key=lambda p: p[1])
        return Block(px - 5, py - 5, px + 5, py + 5, layer_lo, layer_hi)
    if cutname == "upper half":            # everything 60 wu or more above the anchor row, 800 wu wide
        return Block(g.x - 400.0, g.y + 60.0, g.x + 400.0, g.y + 400.0, layer_lo, layer_hi)
    if cutname == "anchor cell":           # a 10 x 10 wu block on the anchor itself (an odd count puts a unit there)
        return Block(g.x - 5.0, g.y - 5.0, g.x + 5.0, g.y + 5.0, layer_lo, layer_hi)
    raise ValueError(cutname)


# The naive scene's unit_types are empty, so the pre-flight reads its units as non-walkers and walks a straight line from the attacker
# to the point over blocked cells (decision 20): a wall over the anchor row, or over the anchor (the holder's point), is 'unroutable' by
# itself. The "one cell" and "upper half" walls keep clear of that line, so their label is 'ok'; the "anchor cell" wall cannot, and for
# it only label == scenes.preflight(setup) is asserted.
CASES = [(who, cutname, heads) for who in ("attacker", "defender") for cutname in ("one cell", "upper half") for heads in HEADS] + \
    [("defender", "anchor cell", 17)]


IDS = ["%s-%s-%d" % c for c in CASES]


@pytest.mark.parametrize("who,cutname,heads", CASES, ids=IDS)
def test_a_blocked_cell_in_the_fill_path_is_skipped_and_the_scene_fits(who, cutname, heads):
    """(a) A wall through the blob (the attacker's 16 or the defender's `heads`): no unit stands in it, the count is kept, the label is
    the pre-flight of the Setup and 'ok' where the wall is clear of the line to the point. Red before: the label is 'no_fit' and
    units stand in the wall."""
    plain = open_setup(heads)
    open_, setup, build = scene_with(cut(plain, who, cutname), heads)
    g0, g = groups_of(open_)[who], groups_of(setup)[who]
    # fixture guard: the wall really catches cells of the open-ground blob (else the case proves nothing)
    assert [p for p in positions(g0) if in_block(setup.terrain.blocks, g0.layer, p)], "the wall must catch an open-ground cell"
    assert len(positions(g)) == g.count == g0.count
    assert not [p for gr in setup.groups for p in positions(gr) if in_block(setup.terrain.blocks, gr.layer, p)]
    assert build.labels["prefight"] == scenes.preflight(setup, None)
    if cutname != "anchor cell":
        assert build.labels["prefight"] == "ok"


@pytest.mark.parametrize("who,cutname,heads", CASES, ids=IDS)
def test_the_cells_that_were_free_keep_their_places_and_nothing_stacks(who, cutname, heads):
    """(a) Every open-ground cell that is not blocked is still taken, the skipped ones are replaced by cells that were not in the
    open-ground blob, and no two units share a cell."""
    plain = open_setup(heads)
    open_, setup, _ = scene_with(cut(plain, who, cutname), heads)
    g0, g = groups_of(open_)[who], groups_of(setup)[who]
    blocks = setup.terrain.blocks
    old, new = positions(g0), positions(g)
    kept = [p for p in old if not in_block(blocks, g0.layer, p)]
    assert len(kept) < len(old)
    assert set(keyed(kept)) <= set(keyed(new))
    assert len(set(keyed(new))) == len(new)
    assert len([p for p in keyed(new) if p not in set(keyed(old))]) == len(old) - len(kept)


@pytest.mark.parametrize("who,cutname,heads", CASES, ids=IDS)
def test_the_skipped_units_take_the_next_cells_of_the_fill_order(who, cutname, heads):
    """(a) The READING in the header: the blob equals the first `count` free cells of the continued spiral (to 4 decimals)."""
    plain = open_setup(heads)
    open_, setup, _ = scene_with(cut(plain, who, cutname), heads)
    g, g0 = groups_of(setup)[who], groups_of(open_)[who]
    assert (g.x, g.y) == (g0.x, g0.y)
    assert keyed(positions(g)) == keyed(expected_skipping(g, setup.terrain.blocks))


def test_the_odd_blob_loses_its_anchor_cell_when_the_wall_is_on_it():
    """(a) 17 units, a block on the anchor: the open-ground blob has a unit there, the skipping blob has none."""
    plain = open_setup(17)
    open_, setup, _ = scene_with(cut(plain, "defender", "anchor cell"), 17)
    g0, g = groups_of(open_)["defender"], groups_of(setup)["defender"]
    assert (round(g0.x, 4), round(g0.y, 4)) in keyed(positions(g0))
    assert (round(g.x, 4), round(g.y, 4)) not in keyed(positions(g))


# ---- positive controls: the same wall that does not catch the blob changes nothing -------------------------------------------

@pytest.mark.parametrize("who", ["attacker", "defender"])
def test_control_a_wall_on_other_layers_does_not_block_a_layer_0_blob(who):
    """Green before and after: the wall stands through the blob but only on layers 1 to 4; the blob is on layer 0, so nothing is
    skipped and the label is 'ok'. Without this the tests above could pass for a builder that skips on every layer."""
    plain = open_setup(16)
    open_, setup, build = scene_with(cut(plain, who, "upper half", layer_lo=1, layer_hi=4), 16)
    for side in (0, 1):
        a, b = [next(g for g in s.groups if g.side == side) for s in (open_, setup)]
        assert positions(a) == positions(b)
    assert build.labels["prefight"] == "ok"


@pytest.mark.parametrize("who", ["attacker", "defender"])
def test_control_a_wall_that_misses_the_blob_changes_nothing(who):
    """Green before and after: a wall 600 wu to the side of the blob leaves both blobs exactly where open ground puts them."""
    plain = open_setup(16)
    g = groups_of(plain)[who]
    far = Block(g.x - 200.0, g.y + 600.0, g.x + 200.0, g.y + 700.0, 0, 4)
    open_, setup, build = scene_with(far, 16)
    for side in (0, 1):
        a, b = [next(gr for gr in s.groups if gr.side == side) for s in (open_, setup)]
        assert positions(a) == positions(b)
    assert build.labels["prefight"] == "ok"


# ---- (b) open ground: byte-identical to the output of the built tree ------------------------------------------------------------

# sha256 over repr((cover, heads, side, unit, layer, order, positions)) for the two naive groups, heads in HEADS0, on an open layout and
# on one with cover only (cover is not a block). Recorded on the built tree 2741d544 (placed_scene "naive" before decision 26).
OPEN_HEADS = (1, 2, 3, 8, 16, 17, 48)
OPEN_GROUND_HASH = "2f3d05ad043680e39e3deef1413c6ea9919ed6c5a470db3d05c89554555f990c"


def test_open_ground_blob_positions_are_byte_identical_to_the_built_tree():
    """(b) Decision 26: 'the blob keeps today's shape on open ground (golden hashes unchanged)'. The hash is of the positions the groups
    give through formations.place; red if the skip changes any open-ground cell."""
    h = hashlib.sha256()
    for cover in (0.0, 0.3):
        f = feats(cover)
        build = build_of(maps.layout_map(f, SEED), f)
        for n in OPEN_HEADS:
            for g in build(n, False).groups:
                h.update(repr((cover, n, g.side, g.unit, g.layer, g.order, positions(g))).encode())
    assert h.hexdigest() == OPEN_GROUND_HASH


@pytest.mark.parametrize("n", OPEN_HEADS)
def test_open_ground_blobs_equal_the_plain_spiral_formation(n):
    """(b) Independent of the hash: each naive group's cells equal formations.place('blob', ...) at its anchor with radius 80 + 12 sqrt(n),
    whatever formation name the group carries."""
    for g in open_setup(n).groups:
        assert positions(g) == formations.place("blob", g.count, g.x, g.y, g.facing_deg, {"radius": radius_of(g.count)})


def test_open_ground_label_is_ok_and_nothing_is_shifted():
    build = build_of(maps.layout_map(feats(), SEED))
    build(48, False)
    assert build.labels["prefight"] == "ok" and build.labels["placement_shift"] == 0.0
