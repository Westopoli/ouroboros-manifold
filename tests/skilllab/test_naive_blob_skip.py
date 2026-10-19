# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decisions 26 and 36 (naive blob that does not fit, its bounds), 32 item 5 (one unit), 25 for the baseline builds
"""LAB-REV2-BASE, part 1 of 3: a naive blob skips cells it cannot stand on (scenes.placed_scene(..., "naive") here; sweep._naive_side in
test_sweep_baselines.py). No fight, no engine of ours (the pre-flight of a same-layer scene builds the library lazily for the built-in
types' movement; the sweep file's `library` fixture is the shared one).

THIS FILE FREEZES THE INTERFACE FOR THE BUILDER (the builder edits scripts/skilllab/scenes.py [L6-owned base], formations.py, sweep.py,
scan.py/contract.py as needed; it edits no test).

Decision 26: "where the blob's next cell is blocked, placement skips to the next free cell in its existing fill order, so the blob keeps
today's shape on open ground (golden hashes unchanged) and fits wherever the play's own units fit."
Decision 36 (Architect 2026-10-19) bounds the continuation: a cell must lie inside the layout's canvas (outside counts as blocked) AND
in the ANCHOR cell's connected free region on the mover's route mask of decision 20 (the lab-side 50 wu breadth-first search, 4
neighbours, a cell open when its centre is in no block that reaches the layer); a wall separates regions, a cell reached through its
gap is in the region. "Cannot hold the count" = that region has no free cell left. Unit k takes the k-th free cell of the fill
sequence; the points are compared UNSORTED, in fill order. Decision 32 item 5: a blob of one unit follows the same rule, no special
case (the anchor is radius zero; if blocked, the nearest free cell by increasing radius).

READINGS (the test writer's; each is one assertion that can be argued with, kept apart from the invariants):
  - A cell is blocked when the unit's position stands in a Block that reaches the group's layer (layer_lo <= layer <= layer_hi), bounds
    inclusive, the same reading as scenes.preflight's no_fit. A block that does not reach the group's layer does not block it.
  - "Region" is read at the route grid's own resolution (fakes_baselines.route_region): a point is in the region when its 50 wu cell
    is reached from the anchor's cell over open cells. Every wall these tests build for the region rule has bounds on multiples of 50
    wu (fakes_baselines.aligned) so that a cell is wholly in a wall or wholly out of it and the cell and the point readings agree. QUESTION
    for the Architect (report): a free point in a cell whose centre is blocked (an unaligned wall) is "outside" at cell resolution and
    "inside" at point resolution; decision 36 does not say which. The anchor cell itself starts the search even when it is blocked.
  - The "existing fill order" is the Fermat-spiral order of formations._blob (anchor first when the count is odd, then the pairs
    p_i / reflection of p_i in order), CONTINUED without end (pairs count and radius unchanged, i = pairs, pairs + 1, ...). A blocked
    cell is skipped alone (its partner stays). fakes_baselines.fill_order is that sequence; expected_skipping applies canvas, block and
    region. A blob of ONE unit has no pairs to count: its cell after the anchor is checked by properties (free, inside the canvas, in
    the region, not nearer for a wider wall), not against a sequence.
  - The group keeps Group.x, Group.y as the blob anchor and the radius 80 + 12 * sqrt(count) (the tests rebuild the fill order from them);
    the units are read where fight() reads them: formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params). HOW the skip
    reaches place() (a "points" formation, a param on "blob", a new formation kind) is the builder's, but nothing else of the group
    changes: dataclasses.replace(open_ground_group, formation=g.formation, params=g.params) == g.
  - When the region cannot hold the count the build keeps its open-ground placement (units stand in the wall) and reads 'no_fit'
    (the label stays scenes.preflight of the Setup it built, decision 25); the sweep's baseline_no_fit is read from that label.
  - Only the NAIVE scene skips. A skilled play whose blob stands in a wall keeps its open-ground placement and reads 'no_fit'
    (placement_shift 0.0); nothing is shifted to fit (Q-LAB-03).
  - The attacker of the naive scene is always 16 units (plays_space.UNITS): its cases do not vary with `heads`, and an odd-count attacker
    cannot be built; the odd-count blobs are the defender's (17 and 1 here; 7 and 9 in test_sweep_baselines.py).
Superseded-by-ruling watch list (TD-LAB-REV2-BASE-1, tests of other files that a naive blob which skips can touch; none edited here):
test_placed_by_feature.py::test_the_prefight_record_follows_whether_any_unit_stands_in_a_block[naive-*], ::test_a_formation_that_fits_is_ok_on_a_clear_layout,
::test_ruling_6_the_point_is_the_holders_centre_of_mass[naive-*] (Setup.point must be the mean of the SKIPPED positions; pinned for the sweep's
builds in test_sweep_baselines.py), integration/test_contact_real.py::test_the_placed_scene_label_is_the_preflight_of_the_setup_it_built.
INTERFACE ADDED: none at this level. The scene's own words: build.labels["prefight"] stays scenes.preflight of the Setup it built, so a
blob that skipped its blocked cells reads "ok" (today it reads "no_fit") wherever the rest of the scene is routable.

Red before (built tree 2741d544): a block laid through the blob's cells leaves units in it, so the label reads "no_fit" and the positions
equal the open-ground ones. Green controls: open ground, a block on another layer, a block that misses the blob, a skilled play with a
wall through its blob.

Real layout 192 (smoke layout, choke 8 bodies, start distance 2800; integration/test_baselines_real.py): the naive attacker's defender
blob at 48 straddles the choke wall's gap (x 3105 to 3195, gap rows 1880 to 2120); the unit at x = 3277 is in the anchor's region (the
east side connects to the anchor through the gap rows and round the wall's ends), so it STAYS; the pinned outcome there is "every unit
of every baseline is in the region, in the canvas, in no block, the fill order equals the helper's, nothing is refused".
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

from fakes_baselines import aligned, expected_skipping, in_block, inside_canvas, keyed, positions, radius_of, rounded, route_region  # noqa: E402
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


def build_of(layout, f=None, play="naive"):
    f = f or feats()
    return scenes.placed_scene(layout, play, f.start_distance, f)


def offset(play="naive"):
    """(dx, dy) the scene adds to layout coordinates, read from where a reference block lands."""
    layout = dataclasses.replace(maps.layout_map(feats(), SEED), blocks=(REF,))
    b = build_of(layout, play=play)(16, False).terrain.blocks[0]
    return b.x0 - REF.x0, b.y0 - REF.y0


def groups_of(setup):
    """{'attacker': side 0 blob, 'defender': side 1 blob} of the naive scene (one group per side: exactly two groups)."""
    by_side = {g.side: g for g in setup.groups}
    assert len(setup.groups) == 2 and set(by_side) == {0, 1}, setup.groups
    return {"attacker": by_side[0], "defender": by_side[1]}


def scene_with(blocks_final, heads, play="naive"):
    """(open-ground setup, blocked setup, build) for heads units on the defender; blocks_final are Blocks in scene coordinates (one Block
    or a sequence)."""
    blocks_final = (blocks_final,) if isinstance(blocks_final, Block) else tuple(blocks_final)
    dx, dy = offset(play)
    base = maps.layout_map(feats(), SEED)
    extra = tuple(Block(b.x0 - dx, b.y0 - dy, b.x1 - dx, b.y1 - dy, b.layer_lo, b.layer_hi) for b in blocks_final)
    build = build_of(dataclasses.replace(base, blocks=base.blocks + extra), play=play)
    return build_of(base, play=play)(heads, False), build(heads, False), build


def open_setup(heads):
    return build_of(maps.layout_map(feats(), SEED))(heads, False)


def cut(setup, who, cutname, layer_lo=0, layer_hi=4):
    """The wall of a case, in scene coordinates, read off the open-ground group so it is sure to land on the blob. Bounds on multiples of
    50 wu (header: the region reading), except the anchor cell's 10 x 10 wu block, which keeps its cell's centre open."""
    g = groups_of(setup)[who]
    if cutname == "one cell":              # the 50 wu route cell holding the open-ground blob's highest unit
        px, py = max(positions(g), key=lambda p: p[1])
        return aligned(px, py, px + 1e-6, py + 1e-6, layer_lo, layer_hi)
    if cutname == "upper half":            # everything 60 wu or more above the anchor row, 800 wu wide
        return aligned(g.x - 400.0, g.y + 60.0, g.x + 400.0, g.y + 400.0, layer_lo, layer_hi)
    if cutname == "anchor cell":           # a 10 x 10 wu block on the anchor itself (an odd count puts a unit there)
        cx, cy = (g.x // 50 + 0.5) * 50, (g.y // 50 + 0.5) * 50
        assert not (abs(g.x - cx) <= 5 and abs(g.y - cy) <= 5), "fixture: the block must leave the anchor cell's centre open"
        return Block(g.x - 5.0, g.y - 5.0, g.x + 5.0, g.y + 5.0, layer_lo, layer_hi)
    raise ValueError(cutname)


# The attacker of the naive scene is always 16 units, so its cases do not vary with `heads` (one run per wall, `heads` = 16 for the
# defender's id only). The odd count is the defender's 17 (anchor cell case included).
CASES = [("attacker", cutname, 16) for cutname in ("one cell", "upper half")] + \
    [("defender", cutname, heads) for cutname in ("one cell", "upper half") for heads in HEADS] + \
    [("defender", "anchor cell", 17)]


IDS = ["%s-%s-%d" % c for c in CASES]


def terrain_of(setup):
    return setup.terrain


@pytest.mark.parametrize("who,cutname,heads", CASES, ids=IDS)
def test_a_blocked_cell_in_the_fill_path_is_skipped_and_the_scene_fits(who, cutname, heads):
    """(a) A wall through the blob (the attacker's 16 or the defender's `heads`): no unit stands in it, the count is kept, nothing else
    of the group changes, the label is the pre-flight of the Setup and 'ok' (a flyer routes round the wall; the anchor-cell wall is
    'ok' too since decisions 20 and 27). Red before: the label is 'no_fit' and units stand in the wall."""
    plain = open_setup(heads)
    open_, setup, build = scene_with(cut(plain, who, cutname), heads)
    g0, g = groups_of(open_)[who], groups_of(setup)[who]
    # fixture guard: the wall really catches cells of the open-ground blob (else the case proves nothing)
    assert [p for p in positions(g0) if in_block(setup.terrain.blocks, g0.layer, p)], "the wall must catch an open-ground cell"
    assert len(positions(g)) == g.count == g0.count
    assert not [p for gr in setup.groups for p in positions(gr) if in_block(setup.terrain.blocks, gr.layer, p)]
    assert dataclasses.replace(g0, formation=g.formation, params=g.params) == g       # facing, layer, order, unit, side, goal, count kept
    assert build.labels["prefight"] == scenes.preflight(setup, None) == "ok"
    # ruling 6: Setup.point is the holder's (the defender's, side 1) centre of mass of the PLACED positions, skipped ones included
    holder = groups_of(setup)["defender"]
    centre = (sum(p[0] for p in positions(holder)) / holder.count, sum(p[1] for p in positions(holder)) / holder.count)
    assert setup.point == pytest.approx(centre, abs=1e-6)
    if who == "defender":
        assert setup.point != open_.point


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
    """(a) The READING in the header: unit k takes the k-th free cell of the continued spiral (to 4 decimals), UNSORTED, in fill order
    (decision 36 item 3); the anchor stays the group's x, y."""
    plain = open_setup(heads)
    open_, setup, _ = scene_with(cut(plain, who, cutname), heads)
    g, g0 = groups_of(setup)[who], groups_of(open_)[who]
    assert (g.x, g.y) == (g0.x, g0.y)
    expected = expected_skipping(g, setup.terrain)
    assert expected is not None and rounded(positions(g)) == rounded(expected)


def test_the_odd_blob_loses_its_anchor_cell_when_the_wall_is_on_it():
    """(a) 17 units, a block on the anchor: the open-ground blob has a unit there, the skipping blob has none."""
    plain = open_setup(17)
    open_, setup, _ = scene_with(cut(plain, "defender", "anchor cell"), 17)
    g0, g = groups_of(open_)["defender"], groups_of(setup)["defender"]
    assert (round(g0.x, 4), round(g0.y, 4)) in keyed(positions(g0))
    assert (round(g.x, 4), round(g.y, 4)) not in keyed(positions(g))


# ---- decision 26 only skips the NAIVE scene: a skilled play whose blob stands in a wall is left as it is --------------------------

@pytest.mark.parametrize("play", ["s1_hold_choke", "s3_layer_above"])
def test_a_skilled_plays_blob_in_a_wall_is_not_skipped(play):
    """Control against a builder that skips on every play (placed_scene, not only 'naive'): a wall through the skilled play's attacking
    blob leaves the open-ground positions, the formation and the params as they were, the label 'no_fit' (units stand in the wall) and
    placement_shift 0.0. Green before; red for a skip applied to every play."""
    f = feats()
    base = maps.layout_map(f, SEED)
    plain = build_of(base, f, play)(16, False)
    blob = next(g for g in plain.groups if g.side == 1 and g.formation == "blob")
    wall = aligned(blob.x - 400.0, blob.y + 60.0, blob.x + 400.0, blob.y + 400.0)
    open_, setup, build = scene_with(wall, 16, play=play)
    gb = next(g for g in setup.groups if g.side == 1 and g.formation == "blob")
    assert [p for p in positions(gb) if in_block(setup.terrain.blocks, gb.layer, p)], "fixture: the wall catches the blob"
    assert setup.groups == open_.groups                                  # every group exactly as on open ground
    assert build.labels["prefight"] == scenes.preflight(setup, None) == "no_fit"
    assert build.labels["placement_shift"] == 0.0


# ---- decision 36: the continuation stays inside the canvas and the anchor's connected region ------------------------------------

def wall_across(g, canvas, gap=None):
    """A 50 wu thick wall (one route cell) 1 to 50 wu east of the open-ground group's anchor, from the bottom of the canvas to the top
    (aligned to 50 wu), with a gap of rows `gap` (y0, y1) when given. Returns the Blocks (scene coordinates)."""
    x0 = math.ceil((g.x + 1.0) / 50.0) * 50.0
    if gap is None:
        return [Block(x0, 0.0, x0 + 50.0, canvas[1], 0, 4)]
    return [Block(x0, 0.0, x0 + 50.0, gap[0], 0, 4), Block(x0, gap[1], x0 + 50.0, canvas[1], 0, 4)]


def across(setup, wall):
    """The defender's units strictly east of the wall (past its far face)."""
    far = max(b.x1 for b in wall)
    return [p for p in positions(groups_of(setup)["defender"]) if p[0] > far]


@pytest.mark.parametrize("heads", [17, 48])
def test_a_wall_across_the_canvas_keeps_the_blob_on_the_anchors_side(heads):
    """(b) negative: a closed wall (no gap, canvas edge to canvas edge, one route cell thick) just east of the anchor. The cells beyond it are not
    in the anchor's region and are never taken: the blob fills westward. Fixture guard: a builder that ignores the region would put
    units beyond the wall (expected_skipping(connected=False)). Red before and for 'region ignored'."""
    plain = open_setup(heads)
    g0 = groups_of(plain)["defender"]
    wall = wall_across(g0, plain.terrain.canvas)
    _, setup, _ = scene_with(wall, heads)
    g = groups_of(setup)["defender"]
    leaky = expected_skipping(g, setup.terrain, connected=False)
    assert leaky is not None and len([p for p in leaky if p[0] > wall[0].x1]) >= 2, "fixture: the wall must separate the rules"
    assert not across(setup, wall)
    expected = expected_skipping(g, setup.terrain)
    assert expected is not None and rounded(positions(g)) == rounded(expected)
    assert not [p for p in positions(g) if in_block(setup.terrain.blocks, g.layer, p)]


@pytest.mark.parametrize("heads", [17, 48])
def test_a_cell_reached_through_the_gap_of_the_wall_is_taken(heads):
    """(b) positive: the same wall with a 200 wu gap on the anchor's row. The far side is connected to the anchor through the gap, so
    cells beyond the wall are in the region and the blob takes them: positions equal the fill order over the whole connected region,
    and at least one unit stands beyond the wall (where the closed wall of the test above leaves none). Red for 'only the anchor's
    side of a wall'."""
    plain = open_setup(heads)
    g0 = groups_of(plain)["defender"]
    gap = (math.floor((g0.y - 100.0) / 50.0) * 50.0, math.ceil((g0.y + 100.0) / 50.0) * 50.0)
    wall = wall_across(g0, plain.terrain.canvas, gap)
    _, setup, _ = scene_with(wall, heads)
    g = groups_of(setup)["defender"]
    assert len(across(setup, wall)) >= 1
    expected = expected_skipping(g, setup.terrain)
    assert expected is not None and rounded(positions(g)) == rounded(expected)
    assert not [p for p in positions(g) if in_block(setup.terrain.blocks, g.layer, p)]


def test_a_blob_at_the_edge_of_the_canvas_stays_inside_it():
    """(c) The layout's canvas is 2020 wide, which puts the 16-unit naive attacker's anchor 60 wu from the left edge: the open-ground
    blob would put units at x < 0. Cells outside the canvas count as blocked, so the skip takes the next cells inside it (and the
    label is the pre-flight of the Setup). Fixture guard: the open-ground blob has units outside. Red before and for 'canvas ignored'."""
    f = feats()
    layout = maps.layout_map(f, SEED, canvas=(2020.0, 4000.0))
    build = build_of(layout, f)
    setup = build(16, False)
    g = groups_of(setup)["attacker"]
    assert setup.terrain.canvas == (2020.0, 4000.0) and abs(g.x - 60.0) < 1e-6
    open_pts = formations.place("blob", g.count, g.x, g.y, g.facing_deg, {"radius": radius_of(g.count)})
    assert len([p for p in open_pts if not inside_canvas(setup.terrain, p)]) >= 2, "fixture: the blob must stick out of the canvas"
    pts = positions(g)
    assert len(pts) == 16 and all(inside_canvas(setup.terrain, p) for p in pts)
    leaky = expected_skipping(g, setup.terrain, canvas=False)
    assert rounded(leaky) == rounded(open_pts) and rounded(pts) != rounded(open_pts)
    expected = expected_skipping(g, setup.terrain)
    assert expected is not None and rounded(pts) == rounded(expected)
    assert build.labels["prefight"] == scenes.preflight(setup, None)


def pocket(g, hx=200.0, hy=100.0):
    """A closed ring of 100 wu walls around a box hx, hy either side of the anchor (aligned to 50 wu), in scene coordinates."""
    return [aligned(g.x - hx - 100, g.y - hy - 100, g.x - hx, g.y + hy + 100), aligned(g.x + hx, g.y - hy - 100, g.x + hx + 100, g.y + hy + 100),
            aligned(g.x - hx, g.y - hy - 100, g.x + hx, g.y - hy), aligned(g.x - hx, g.y + hy, g.x + hx, g.y + hy + 100)]


def test_a_closed_pocket_smaller_than_the_count_reads_no_fit():
    """(a, decision 36) The defender's anchor sits in a closed 400 x 200 wu pocket. Where the region can hold the headcount (the helper's
    walk over the pocket's free cells) the blob is skipped into the pocket and nothing stands in a wall; where it cannot, the build
    reads 'no_fit' (units stand in the walls: the pre-flight of the Setup). Hand-built terrain, the real pre-flight, no fake label. The
    pocket's attackers are outside it, so a headcount that fits reads 'unroutable' (the point is walled in): only 'no_fit' is pinned.
    Fixture guard: some headcounts of 8 to 48 fit and some do not. Red before: 'no_fit' only where open-ground cells stand in a wall,
    never 'cannot hold'; and for 'region ignored'."""
    plain = open_setup(16)
    walls = pocket(groups_of(plain)["defender"])
    fit, no_fit = [], []
    for heads in range(8, 49):
        _, setup, build = scene_with(walls, heads)
        g = groups_of(setup)["defender"]
        expected = expected_skipping(g, setup.terrain)
        label = build.labels["prefight"]
        assert label == scenes.preflight(setup, None)
        if expected is None:
            no_fit.append(heads)
            assert label == "no_fit", heads
            assert len(positions(g)) == heads and [p for p in positions(g) if in_block(setup.terrain.blocks, g.layer, p)], heads
        else:
            fit.append(heads)
            assert label != "no_fit", heads
            assert rounded(positions(g)) == rounded(expected), heads
            assert not [p for p in positions(g) if in_block(setup.terrain.blocks, g.layer, p)], heads
    assert fit and no_fit and min(fit) == 8 and max(no_fit) > min(no_fit), (fit, no_fit)


# ---- decision 32 item 5: a blob of one unit follows the same rule --------------------------------------------------------------

def test_a_blob_of_one_unit_stands_on_its_anchor_when_the_anchor_is_free():
    """(a) Radius zero: one unit at the anchor, exactly (and the open-ground label 'ok')."""
    setup = open_setup(1)
    g = groups_of(setup)["defender"]
    assert positions(g) == [(g.x, g.y)]


def test_a_blob_of_one_unit_on_a_blocked_anchor_takes_the_nearest_free_cell_by_increasing_radius():
    """(a) Decision 32 item 5: the anchor is blocked, the unit takes the nearest free cell: free, inside the canvas, in the anchor's
    region, near the anchor, and never nearer for a wider wall (the order is by increasing radius). No sequence is pinned (header)."""
    plain = open_setup(1)
    g0 = groups_of(plain)["defender"]
    cx, cy = (g0.x // 50 + 0.5) * 50, (g0.y // 50 + 0.5) * 50
    got = []
    for half in (5.0, 15.0):
        assert abs(g0.x - cx) > half or abs(g0.y - cy) > half, "fixture: the block must leave the anchor cell's centre open"
        wall = Block(g0.x - half, g0.y - half, g0.x + half, g0.y + half, 0, 4)
        _, setup, build = scene_with(wall, 1)
        g = groups_of(setup)["defender"]
        (p,) = positions(g)
        seen, cell_of = route_region(setup.terrain, g.layer, (g.x, g.y))
        assert not in_block(setup.terrain.blocks, g.layer, p) and inside_canvas(setup.terrain, p) and cell_of(p) in seen
        assert p != (g.x, g.y)
        d = math.hypot(p[0] - g.x, p[1] - g.y)
        assert d > half and d < 150.0
        assert build.labels["prefight"] == scenes.preflight(setup, None) and (g.x, g.y) == (g0.x, g0.y)
        got.append(d)
    assert got[0] <= got[1]


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
    far = aligned(g.x - 200.0, g.y + 600.0, g.x + 200.0, g.y + 700.0)
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
