# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 items 5 and 6, and decision 44 (Architect, 2026-10-19, implementation; Westley may
# veto; decision 44 is in the brief of this piece, not yet in the decisions file): a naive-defender post that cannot see the attackers' start is shifted, else refused
"""LAB-REV2-FIX round 3: blind naive-defender posts (shift, then refuse `blind_post`), and the artifact's line for every refused baseline.

DECISION 44 AS READ HERE
  BLIND: a naive-defender post is blind iff no clear sightline exists under R-098-02 between the post and the NEAREST point of the opposing side's
  start, RANGE IGNORED. A sightline is clear when no blocked 100 wu cell crosses the segment. A pure lab-side geometry probe on the Setup's blocks
  (scenes.py): no engine call, no spawned world.
  SHIFT: the baseline builder moves a blind post to the nearest FREE route-grid cell (50 wu cell, centre in no block reaching the layer) of the SAME
  REGION (decision 38) from which the start is visible, by increasing distance, within the guard radius 200 wu (DRAFT), and reports the distance in
  the build's `placement_shift` label. None within the radius: pre-flight says `blind_post` (5th word; precedence no_fit, unroutable, no_reach, blind_post).

INTERFACE FOR THE BUILDER (frozen here)
  scripts/skilllab/scenes.py
    SIGHT_CELL = 100.0            R-098-02's blocked-cell size (OM_NAVMESH_CELL_SIZE)
    GUARD_RADIUS = 200.0          the word DRAFT on its definition line (the artifact header already lists DRAFT-guard-radius; the number is the same one)
    sight_clear(terrain, a, la, b, lb) -> bool      a, b are (x, y) points on layers la, lb. True when no blocked 100 wu cell crosses the segment. The
                                                    cells a Block turns blocked are every cell it touches (floor of the low bound .. ceil of the high bound - 1,
                                                    as om_map_block_rect), on layers layer_lo..layer_hi; the cell tested for a pair is the LOWER layer of the
                                                    pair (csrc/fog.c om_fog_grid_blocks); the cells holding the two ends are exempt; a segment that only touches
                                                    a cell's corner does not cross it. Terrain None: clear.
    blind_post(terrain, layer, post, starts) -> bool      starts: iterable of (x, y, layer), the placed units of the opposing side. True iff there is a start and
                                                    sight_clear is False from the post to the start NEAREST the post (Euclid; range ignored). No starts: False.
    shifted_post(terrain, layer, post, starts, radius=GUARD_RADIUS) -> (x, y) | None      the post itself (equal values) when it is not blind; else the centre
                                                    of the nearest free, sighted route cell of the post's region within `radius` (inclusive); None when there is none.
                                                    The cell search is the lab's route grid (ROUTE_CELL 50, `_route_region`); the cell must be FREE (a cell standing
                                                    inside a Block is not a candidate even if its own sight cell is exempt as an end of the segment).
    preflight(setup, engine, naive_defender=False)      new keyword. With True, after no_fit, unroutable and no_reach: "blind_post" when some side-0 group on
                                                    guard has an anchor (g.x, g.y) that is a blind_post() to the placed units of side 1 (layer g.layer); else "ok".
                                                    With False the word is never blind_post (a skilled play's post is not refused here).
  scripts/skilllab/sweep.py   _naive_side (default_builds' naive_defender, _attacker_layer, _play_layer): for a build whose side 0 holds (guard order), each blob
                              anchor (the type's mean anchor, round-1 rule) that is blind is moved with shifted_post BEFORE the blob is skipped around blocks; when
                              any blind anchor has no shift NO anchor moves. build.labels["prefight"] = scenes.preflight(<its own Setup>, engine, naive_defender=True)
                              for such a build; build.labels["placement_shift"] = the distance moved (the largest of the anchors' distances when several moved),
                              0.0 when nothing moved or the build is refused. A non-holder (attack-move) side is never probed. The word `placement_shift` therefore
                              appears in sweep.py (TD-LAB-REV2-FIX-blind-post-retired-name).
  scripts/skilllab/report.py  artifact(): in <section id="findings">, AFTER the cut-scan list (when any), when at least one family entry of summary["order"] has
                              a non-empty `refused` list holding a naive baseline: ONE <ul class="refused-baselines">, the last element child of the section, one
                                  <li data-refused-baseline data-family data-play data-layout data-role data-reason>LINE ...</li>
                              per such entry, in summary["order"] family order and, inside a family, sorted by (play, layout, role) as strings. LINE (the test
                              writer's rule, questions Q-FIX3-1 and Q-FIX3-2):  "no naive " + R + ": " + W  with R = the role with its "naive_" prefix removed and
                              "_" turned into " ", W = the reason with "_" turned into " "; data-role and data-reason hold the codes. So (naive_defender,
                              blind_post) reads "no naive defender: blind post" (Architect's sentence). The li text STARTS with LINE (more words may follow).
                              Entries whose role does not start with "naive_" (a refused play) are not listed (not pinned). Nothing refused: no such <ul> and no
                              "no naive" text on the page.

Existing tests that encode what this retires (ledger rows TD-LAB-REV2-FIX-blind-post-*): tests/skilllab/test_sweep.py::test_sweep_module_names_no_retired_field_or_helper
(`placement_shift` may now appear in sweep.py); tests/skilllab/test_sweep_baselines.py::test_d_a_blob_on_a_blocked_anchor_cell_fills_the_region_of_the_nearest_open_cell
(4 cases) and ::test_d_a_free_point_inside_a_blocked_route_cell_is_not_used (2 cases), whose anchors were blind to the enemy and so are now shifted (the fixtures move
the enemy so the anchor keeps a clear line). No test pins placement_shift == 0.0 for a build that goes through sweep._naive_side (the pins in test_naive_blob_skip.py and
test_placed_by_feature.py are scenes.placed_scene's, which this piece does not touch). The real-layout label test (integration/test_baselines_real.py) stays green: the
plays it reads are shifted, not refused.
READINGS the test writer made (each one assertion that can be argued with): the cross-layer pair (lower layer of the pair), the exempt end cells, the
inclusive 200 wu bound, the largest-shift label, and the line text. Not pinned: ties by distance (any of the tied cells; the spiral order is the builder's), covers
(R-098-02 also blocks on cover discs; decision 44 names blocked cells only), the artifact line of a refused play, a duplicate across families."""
import dataclasses
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fakes_blind as fb  # noqa: E402
from fakes_blind import ENEMY, ENEMY_AT, WALL, base_build, blob, terrain  # noqa: E402
from fakes_baselines import positions  # noqa: E402
from fakes_scans import _fr  # noqa: E402
from scripts.skilllab import scenes, sweep  # noqa: E402
from scripts.skilllab.contract import Block, Setup  # noqa: E402

E = [(ENEMY_AT[0], ENEMY_AT[1], 0)]
POST = (975.0, 1010.0)               # west of WALL, blind to ENEMY_AT
CELL_150 = (1125.0, 1025.0)          # the pinned shift: the first free sighted cell past the wall's face, 150.75 wu away


# ---------------------------------------------------------------------------------------------------------- the constants

def test_the_guard_radius_is_200_and_marked_draft_on_its_definition_line():
    assert scenes.GUARD_RADIUS == 200.0 and scenes.SIGHT_CELL == 100.0
    line = next(l for l in (ROOT / "scripts/skilllab/scenes.py").read_text().splitlines() if l.startswith("GUARD_RADIUS"))
    assert "DRAFT" in line


# ---------------------------------------------------------------------------------------------------------- sight_clear

SEG = ((600.0, 1000.0), (1500.0, 1000.0))


def test_open_ground_has_a_clear_sightline():
    assert scenes.sight_clear(terrain(), *SEG[:1], 0, *SEG[1:], 0)


def test_a_blocked_cell_on_the_segment_blocks_it_either_way_round():
    t = terrain(Block(1000.0, 900.0, 1100.0, 1100.0))
    assert not scenes.sight_clear(t, SEG[0], 0, SEG[1], 0)
    assert not scenes.sight_clear(t, SEG[1], 0, SEG[0], 0)


def test_control_a_segment_beside_the_blocked_cell_is_clear():
    t = terrain(Block(1000.0, 900.0, 1100.0, 1100.0))
    assert scenes.sight_clear(t, (600.0, 1300.0), 0, (1500.0, 1300.0), 0)
    assert scenes.sight_clear(t, (600.0, 700.0), 0, (1500.0, 700.0), 0)


def test_the_blocked_thing_is_the_100_wu_cell_not_the_blocks_own_extent():
    """A block of 30 x 30 wu turns its whole 100 wu cell blocked (R-098-02 tests blocked cells): a segment through the cell and beside the block is blocked."""
    t = terrain(Block(1000.0, 1000.0, 1030.0, 1030.0))
    assert not scenes.sight_clear(t, (600.0, 1060.0), 0, (1500.0, 1060.0), 0)
    assert scenes.sight_clear(t, (600.0, 960.0), 0, (1500.0, 960.0), 0)             # the row below
    assert scenes.sight_clear(t, (600.0, 1160.0), 0, (1500.0, 1160.0), 0)           # the row above


def test_range_is_ignored_a_far_unblocked_post_is_not_blind():
    wide = (4000.0, 2000.0)
    assert not scenes.blind_post(terrain(canvas=wide), 0, (100.0, 1000.0), [(3900.0, 1000.0, 0)])       # 3800 wu, five sensor radii
    assert scenes.blind_post(terrain(Block(2000.0, 900.0, 2100.0, 1100.0), canvas=wide), 0, (100.0, 1000.0), [(3900.0, 1000.0, 0)])


@pytest.mark.parametrize("layer_lo,layer_hi,viewer,blocks", [
    (0, 1, 2, False),     # the block's top (1) is below the viewer's layer (2): no block
    (0, 1, 1, True),      # the block reaches the viewer's layer
    (0, 1, 0, True),
    (2, 4, 1, False),     # the block's bottom (2) is above the viewer's layer (1): no block
    (2, 4, 2, True),
])
def test_a_block_blocks_only_on_the_layers_it_reaches(layer_lo, layer_hi, viewer, blocks):
    """Both ends on the viewer's layer. The first row is the decision's own example: a block whose top is below the viewer's layer does not block."""
    t = terrain(Block(1000.0, 900.0, 1100.0, 1100.0, layer_lo, layer_hi))
    assert scenes.sight_clear(t, SEG[0], viewer, SEG[1], viewer) is (not blocks)


def test_reading_a_pair_on_two_layers_is_tested_on_the_lower_one():
    """READING (csrc/fog.c: the lower layer of the pair). Decision 44 words it 'a layer at or below the viewer's layer'; the engine's pair rule agrees on
    every same-layer case and differs only here, so it is pinned apart. Block on layer 0 only: a viewer on 2 looking at layer 0 is blocked; a block on 2 only
    does not block a pair whose lower layer is 0."""
    low = terrain(Block(1000.0, 900.0, 1100.0, 1100.0, 0, 0))
    high = terrain(Block(1000.0, 900.0, 1100.0, 1100.0, 2, 2))
    assert not scenes.sight_clear(low, SEG[0], 2, SEG[1], 0) and not scenes.sight_clear(low, SEG[0], 0, SEG[1], 2)
    assert scenes.sight_clear(high, SEG[0], 0, SEG[1], 2) and scenes.sight_clear(high, SEG[0], 2, SEG[1], 0)


def test_reading_the_cell_a_unit_stands_in_does_not_block_its_own_sight():
    """READING (csrc/fog.c exempts the cells holding the two ends, R-007-06's 'a unit standing inside is seen as normal'): a post standing in the wall's cell
    sees past it. The shift never relies on it (a candidate must be free), see test_the_shift_never_lands_inside_a_block."""
    t = terrain(WALL)
    assert scenes.sight_clear(t, (1050.0, 1000.0), 0, ENEMY_AT, 0)


def test_the_probe_agrees_with_the_exact_oracle_on_random_segments():
    """Positive control for the whole probe: 120 seeded segments over a terrain with blocks on several layers, against fakes_blind.clear (exact fractions,
    written from the words). Segments whose answer depends on how a corner touch is read are left out; both answers must occur."""
    t = terrain(Block(300.0, 200.0, 560.0, 900.0, 0, 2), Block(900.0, 400.0, 1030.0, 1700.0, 1, 3), Block(1300.0, 100.0, 1700.0, 330.0, 0, 4),
                Block(500.0, 1500.0, 1450.0, 1620.0, 0, 0))
    rnd = random.Random(44)
    seen = {True: 0, False: 0}
    for _ in range(120):
        a, b = [(rnd.uniform(5.0, 1995.0), rnd.uniform(5.0, 1995.0)) for _ in range(2)]
        la, lb = rnd.randint(0, 3), rnd.randint(0, 3)
        open_read, closed_read = fb.clear(t, a, la, b, lb), fb.clear(t, a, la, b, lb, closed=True)
        if open_read != closed_read:
            continue
        seen[open_read] += 1
        assert scenes.sight_clear(t, a, la, b, lb) is open_read, (a, la, b, lb)
    assert seen[True] >= 15 and seen[False] >= 15, seen


# ---------------------------------------------------------------------------------------------------------- blind_post

def test_a_post_behind_a_wall_is_blind_and_one_with_a_clear_line_is_not():
    t = terrain(WALL)
    assert scenes.blind_post(t, 0, POST, E)
    assert not scenes.blind_post(t, 0, (975.0, 300.0), E)                  # control: the wall's shadow does not reach it
    assert not scenes.blind_post(terrain(), 0, POST, E)                    # control: no wall


def test_only_the_nearest_start_counts():
    """'between the post and the NEAREST point': the nearest start is behind the wall and a farther one is in the open: blind. Swap them: not blind."""
    t = terrain(WALL)
    assert scenes.blind_post(t, 0, POST, [(1150.0, 1000.0, 0), (975.0, 200.0, 0)])
    assert not scenes.blind_post(t, 0, POST, [(975.0, 1300.0, 0), (1700.0, 1000.0, 0)])


def test_no_start_is_not_blind():
    assert not scenes.blind_post(terrain(WALL), 0, POST, [])


def test_a_block_below_the_posts_layer_does_not_make_it_blind():
    assert not scenes.blind_post(terrain(Block(1000.0, 600.0, 1100.0, 1400.0, 0, 1)), 2, POST, [(ENEMY_AT[0], ENEMY_AT[1], 2)])
    assert scenes.blind_post(terrain(Block(1000.0, 600.0, 1100.0, 1400.0, 0, 2)), 2, POST, [(ENEMY_AT[0], ENEMY_AT[1], 2)])


# ---------------------------------------------------------------------------------------------------------- shifted_post

def test_a_post_that_is_not_blind_stays_where_it_is():
    assert scenes.shifted_post(terrain(WALL), 0, (975.0, 300.0), E) == (975.0, 300.0)
    assert scenes.shifted_post(terrain(), 0, POST, E) == POST


def test_the_shift_lands_on_the_first_sighted_free_cell_past_the_wall():
    """Pinned cell. The wall is one sight cell thick (x 1000..1100, y 600..1400), the start at (1700, 1000). Nothing on the post's side within 200 wu is
    sighted (the shadow reaches 480 wu up and down); the first free sighted cell is the centre (1125, 1025) of the route cell past the east face, 150.75 wu
    away. The oracle (fakes_blind) is a separate scan and must say the same; its two readings of a corner touch agree."""
    t = terrain(WALL)
    got = scenes.shifted_post(t, 0, POST, E)
    assert got == CELL_150
    assert fb.expected_shift(t, 0, POST, E) == (CELL_150, pytest.approx(math.hypot(150.0, 15.0)))
    assert not scenes.blind_post(t, 0, got, E)


def test_the_shift_never_lands_inside_a_block():
    """Guard for the free-cell rule: the route cells whose centres stand in the wall (x 1025 and 1075) are nearer to the post and, because the cell a
    segment starts in is exempt, they read sighted. They are not free; the answer is the first cell past the face."""
    t = terrain(WALL)
    for inside in ((1025.0, 1025.0), (1075.0, 1025.0)):
        assert not scenes.blind_post(t, 0, inside, E), inside                       # fixture: a builder without the free-cell rule would pick one of these
        assert math.hypot(inside[0] - POST[0], inside[1] - POST[1]) < math.hypot(CELL_150[0] - POST[0], CELL_150[1] - POST[1])
    assert not any(b.x0 <= scenes_x <= b.x1 and b.y0 <= scenes_y <= b.y1 for b in t.blocks for scenes_x, scenes_y in [scenes.shifted_post(t, 0, POST, E)])


def test_a_tie_is_broken_among_the_tied_cells_and_always_the_same_way():
    """Post (975, 1000): (1125, 975) and (1125, 1025) are 151.97 wu away, a tie. Which one is the existing spiral order's and the builder's; either is accepted."""
    t = terrain(WALL)
    tied = fb.ties(t, 0, (975.0, 1000.0), E)
    assert sorted(tied) == [(1125.0, 975.0), (1125.0, 1025.0)]                       # fixture: really a tie
    first = scenes.shifted_post(t, 0, (975.0, 1000.0), E)
    assert first in tied and scenes.shifted_post(t, 0, (975.0, 1000.0), E) == first


def test_a_sighted_cell_in_another_region_is_not_used():
    """Same-region rule (decision 38). A wall the full height of the canvas: the start is west of it, the post east of it. Every cell within 200 wu on the
    west side is sighted (150 wu from the post) but belongs to the other region: no shift. Control: a gap at the top joins the regions, and the nearest
    sighted cell is across the wall."""
    sealed, joined = terrain(Block(1000.0, 0.0, 1100.0, 2000.0)), terrain(Block(1000.0, 0.0, 1100.0, 1900.0))
    west, post = [(500.0, 1000.0, 0)], (1150.0, 1010.0)
    assert scenes.blind_post(sealed, 0, post, west) and scenes.blind_post(joined, 0, post, west)
    assert fb.candidates(sealed, 0, post, west) == []                             # fixture: the oracle (region-aware) finds none
    assert scenes.shifted_post(sealed, 0, post, west) is None
    assert scenes.shifted_post(joined, 0, post, west) == (975.0, 1025.0) == fb.expected_shift(joined, 0, post, west)[0]


def test_the_search_stops_at_the_guard_radius():
    """Post (875, 1025): the first free sighted cell is 250 wu away. No shift. Control: post (975, 1010) finds its cell at 150.75."""
    t = terrain(WALL)
    assert scenes.blind_post(t, 0, (875.0, 1025.0), E)
    assert fb.candidates(t, 0, (875.0, 1025.0), E, radius=400.0)[0][0] == 250.0                  # fixture: the nearest is 250 wu away
    assert scenes.shifted_post(t, 0, (875.0, 1025.0), E) is None
    assert scenes.shifted_post(t, 0, POST, E) == CELL_150


def test_reading_the_radius_is_inclusive():
    """READING: 'within the guard radius' includes a cell exactly 200 wu away. Post (925, 1025): the cell (1125, 1025) is 200.0 wu away."""
    t = terrain(WALL)
    assert fb.candidates(t, 0, (925.0, 1025.0), E, radius=400.0)[0] == (200.0, (1125.0, 1025.0))
    assert scenes.shifted_post(t, 0, (925.0, 1025.0), E) == (1125.0, 1025.0)


def test_the_radius_argument_is_honoured():
    t = terrain(WALL)
    assert scenes.shifted_post(t, 0, POST, E, radius=100.0) is None
    assert scenes.shifted_post(t, 0, POST, E, radius=160.0) == CELL_150


def test_a_wall_on_another_layer_leaves_the_post_where_it_is():
    t = terrain(Block(1000.0, 600.0, 1100.0, 1400.0, 2, 3))
    assert scenes.shifted_post(t, 0, POST, E) == POST


# ---------------------------------------------------------------------------------------------------------- preflight: the fifth word

OWN = blob(0, "Vanguard", 1, *POST)


def scene(own, blocks, point=POST, enemy=ENEMY):
    return Setup(groups=tuple(own) + (enemy,), unit_types={k: dict(v) for k, v in fb.TYPES.items()}, terrain=terrain(*blocks), point=point)


def test_preflight_says_blind_post_for_a_naive_defender_only_when_asked():
    far_gap = Block(1000.0, 100.0, 1100.0, 1900.0)                                  # a wall the enemy can go round: routable, and a deep shadow
    setup = scene([blob(0, "Vanguard", 1, 900.0, 1000.0)], [far_gap], point=(900.0, 1000.0), enemy=blob(1, "Vanguard", 1, 1500.0, 1000.0, order="attack_move"))
    assert scenes.preflight(setup, None, naive_defender=True) == "blind_post"
    assert scenes.preflight(setup, None) == "ok" and scenes.preflight(setup, None, naive_defender=False) == "ok"


def test_preflight_control_a_clear_post_is_ok_with_the_flag():
    assert scenes.preflight(scene([blob(0, "Vanguard", 1, 975.0, 300.0)], [WALL], point=(975.0, 300.0)), None, naive_defender=True) == "ok"


def test_no_fit_comes_before_blind_post():
    """The post is blind; a second own unit stands inside the wall: no_fit. Control: without it, blind_post."""
    stuck = blob(0, "Raider", 1, 1050.0, 700.0)
    both = scene([OWN, stuck], [WALL])
    assert scenes.blind_post(terrain(WALL), 0, POST, E)
    assert scenes.preflight(both, None, naive_defender=True) == "no_fit"
    assert scenes.preflight(scene([OWN], [Block(1000.0, 100.0, 1100.0, 1900.0)], point=POST), None, naive_defender=True) in ("blind_post", "unroutable")


def test_unroutable_comes_before_blind_post():
    """A wall the full height of the canvas: the attacker cannot reach the post (unroutable) and the post is blind: unroutable. Control with a gap: blind_post."""
    sealed = scene([OWN], [Block(1000.0, 0.0, 1100.0, 2000.0)])
    assert scenes.blind_post(sealed.terrain, 0, POST, E)
    assert scenes.preflight(sealed, None, naive_defender=True) == "unroutable"
    gap = scene([OWN], [Block(1000.0, 0.0, 1100.0, 1900.0)])
    assert scenes.preflight(gap, None, naive_defender=True) == "blind_post"


def test_no_reach_comes_before_blind_post():
    """Holder on layer 0, attacker on layer 1 with reach (0, 0): no_reach, whatever the wall says. Control: reach (0, 1) (one layer down) is not no_reach."""
    from scripts.skilllab.engine import Engine
    engine = Engine()
    types = {"Vanguard": {"base": "Vanguard", "movement": "flying", "reach": (0, 0)}}
    layered = Setup(groups=(OWN, blob(1, "Vanguard", 1, *ENEMY_AT, layer=1, order="attack_move", facing=180.0)), unit_types=types,
                    terrain=terrain(Block(1000.0, 600.0, 1100.0, 1400.0, 0, 4)), point=POST)
    assert scenes.blind_post(layered.terrain, 0, POST, [(ENEMY_AT[0], ENEMY_AT[1], 1)])
    assert scenes.preflight(layered, engine, naive_defender=True) == "no_reach"
    reaching = dataclasses.replace(layered, unit_types={"Vanguard": {"base": "Vanguard", "movement": "flying", "reach": (0, 1)}})
    assert scenes.preflight(reaching, engine, naive_defender=True) != "no_reach"


# ---------------------------------------------------------------------------------------------------------- the baseline builder (sweep._naive_side)

FEATS = {"blocked_layer_top": 0, "choke_width_bodies": 0, "cover_density_corridor": 0, "detour_ratio": 0, "lane_count": 0, "start_distance": 1400}
HOLD = "naive_defender"


@pytest.fixture
def fake_scene(monkeypatch):
    def install(base):
        monkeypatch.setattr(sweep, "_layouts", {})
        monkeypatch.setattr(scenes, "placed_scene", lambda layout, play, start_distance, features, counter=False: base)
        return lambda role: sweep.default_builds("fake_play", role, FEATS)
    return install


def built(fake_scene, own, blocks, role=HOLD, enemy=ENEMY):
    build = fake_scene(base_build(list(own) + [enemy], blocks))(role)
    return build, build(8, False)


def own_of(setup):
    return [g for g in setup.groups if g.side == 0]


def test_a_blind_post_is_moved_to_the_pinned_cell_and_the_shift_is_reported(fake_scene):
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, *POST)], [WALL])
    assert [(g.x, g.y) for g in own_of(setup)] == [CELL_150]
    assert positions(own_of(setup)[0]) == [CELL_150] and setup.point == pytest.approx(CELL_150)
    assert build.labels["placement_shift"] == pytest.approx(math.hypot(150.0, 15.0))
    assert build.labels["prefight"] == "ok" == scenes.preflight(setup, None, naive_defender=True)
    assert setup.groups[-1] == ENEMY and setup.timeline == ()


def test_the_shifted_blob_keeps_its_units_and_its_order(fake_scene):
    _, setup = built(fake_scene, [blob(0, "Vanguard", 8, *POST)], [WALL])
    (g,) = own_of(setup)
    assert (g.unit, g.count, g.order, g.layer) == ("Vanguard", 8, "guard", 0) and (g.x, g.y) == CELL_150


def test_control_a_post_with_a_clear_line_is_not_moved(fake_scene):
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, 975.0, 300.0)], [WALL])
    assert [(g.x, g.y) for g in own_of(setup)] == [(975.0, 300.0)]
    assert build.labels.get("placement_shift", 0.0) == 0.0 and build.labels["prefight"] == "ok"


def test_control_open_ground_is_unchanged(fake_scene):
    """The golden hashes of the open-ground baselines rest on this: with no block the groups are exactly what they were."""
    build, setup = built(fake_scene, [blob(0, "Vanguard", 8, *POST)], [])
    (g,) = own_of(setup)
    assert (g.x, g.y, g.formation, g.params) == (POST[0], POST[1], "blob", {"radius": 80 + 12 * math.sqrt(8)})
    assert build.labels.get("placement_shift", 0.0) == 0.0 and build.labels["prefight"] == "ok"


def test_a_blind_post_with_no_cell_in_reach_is_refused_blind_post_and_nothing_moves(fake_scene):
    """A wall 1800 wu long with gaps at both ends: routable, shadow far deeper than 200 wu."""
    wall = Block(1000.0, 100.0, 1100.0, 1900.0)
    enemy = blob(1, "Vanguard", 1, 1500.0, 1000.0, order="attack_move", facing=180.0)
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, 900.0, 1000.0)], [wall], enemy=enemy)
    assert build.labels["prefight"] == "blind_post" == scenes.preflight(setup, None, naive_defender=True)
    assert [(g.x, g.y) for g in own_of(setup)] == [(900.0, 1000.0)] and build.labels["placement_shift"] == 0.0


def test_the_refusal_follows_the_precedence_in_the_build_label(fake_scene):
    """Sealed wall: the post is blind and the shift is impossible, but the attacker cannot route to it: the label says unroutable."""
    build, _ = built(fake_scene, [blob(0, "Vanguard", 1, *POST)], [Block(1000.0, 0.0, 1100.0, 2000.0)])
    assert build.labels["prefight"] == "unroutable"


def test_two_types_each_post_is_its_own_the_clear_one_stays(fake_scene):
    """Round-1 rule: one blob per unit type at that type's mean anchor. The Vanguard post is blind and moves; the Raider post has a clear line and stays;
    the label carries the distance the Vanguard moved."""
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, *POST), blob(0, "Raider", 1, 975.0, 300.0)], [WALL])
    anchors = {g.unit: (g.x, g.y) for g in own_of(setup)}
    assert anchors == {"Vanguard": CELL_150, "Raider": (975.0, 300.0)}
    assert build.labels["placement_shift"] == pytest.approx(math.hypot(150.0, 15.0)) and build.labels["prefight"] == "ok"


def test_one_unshiftable_post_refuses_the_build_and_no_post_moves(fake_scene):
    wall = Block(1000.0, 100.0, 1100.0, 1900.0)
    enemy = blob(1, "Vanguard", 1, 1500.0, 1000.0, order="attack_move", facing=180.0)
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, 900.0, 1000.0), blob(0, "Raider", 1, 900.0, 160.0)], [wall], enemy=enemy)
    assert build.labels["prefight"] == "blind_post"
    assert {g.unit: (g.x, g.y) for g in own_of(setup)} == {"Vanguard": (900.0, 1000.0), "Raider": (900.0, 160.0)}


def test_a_side_that_attacks_has_no_post_and_is_not_probed(fake_scene):
    """A meeting: side 0 attack-moves. The wall stands between the sides, nothing is shifted and nothing is refused."""
    attacker = blob(0, "Vanguard", 1, *POST, order="attack_move")
    build, setup = built(fake_scene, [attacker], [Block(1000.0, 100.0, 1100.0, 1900.0)])
    assert [(g.x, g.y) for g in own_of(setup)] == [POST] and build.labels.get("placement_shift", 0.0) == 0.0 and build.labels["prefight"] == "ok"


@pytest.mark.parametrize("role", ["naive_defender", "naive_defender_attacker_layer", "naive_defender_play_layer"])
def test_every_defender_variant_shifts_the_same_post(fake_scene, role):
    build, setup = built(fake_scene, [blob(0, "Vanguard", 1, *POST)], [WALL], role=role)
    assert [(g.x, g.y) for g in own_of(setup)] == [CELL_150] and build.labels["placement_shift"] > 0


def test_the_play_and_its_reach_zero_twin_are_not_shifted(fake_scene):
    """Only the naive defender baseline moves its post: the play's own scene keeps its placement."""
    install = fake_scene(base_build([blob(0, "Vanguard", 1, *POST), ENEMY], [WALL]))
    play = sweep.default_builds("fake_play", "play", FEATS)
    assert [(g.x, g.y) for g in own_of(play(8, False))] == [POST] and play.labels["placement_shift"] == 0.0
    assert [(g.x, g.y) for g in own_of(sweep.default_builds("fake_play", "reach_zero", FEATS)(8, False))] == [POST]
    assert install(HOLD)(8, False) is not None


def test_the_build_is_deterministic(fake_scene):
    first = built(fake_scene, [blob(0, "Vanguard", 8, *POST)], [WALL])[1]
    second = built(fake_scene, [blob(0, "Vanguard", 8, *POST)], [WALL])[1]
    assert first == second


# ---------------------------------------------------------------------------------------------------------- the sweep: a blind_post refusal is listed, the play runs on

LAYOUTS = {"A": FEATS}


class Wins:
    """fight_fn: side 0 wins while the enemy has at most 20 units; records the number of enemy units of every call."""

    def __init__(self):
        self.calls = []

    def __call__(self, setup, seed, swap):
        heads = sum(g.count for g in setup.groups if g.side == 1)
        self.calls.append(heads)
        return _fr("side0" if heads <= 20 else "side1", heads)


def run_family(tmp_path, family="range_up"):
    import csv
    entry = sweep.run_family(family, tmp_path, builds=sweep.default_builds, layouts=LAYOUTS, plays=("p_guard",), fight_fn=Wins(),
                             caps=sweep.Capabilities(arc=True, cone=True), replicates=1)
    with open(tmp_path / ("sweep_%s.csv" % family), newline="") as fh:
        return entry, list(csv.DictReader(fh))


def test_the_sweep_lists_a_blind_post_refusal_with_its_role_and_still_runs_the_rest(tmp_path, fake_scene):
    fake_scene(base_build([blob(0, "Vanguard", 1, 900.0, 1000.0)], [Block(1000.0, 100.0, 1100.0, 1900.0)], enemy_at=(1500.0, 1000.0)))
    entry, rows = run_family(tmp_path)
    assert {"family": "range_up", "play": "p_guard", "layout": "A", "role": "naive_defender", "reason": "blind_post"} in entry["refused"]
    baselines = {r["baseline"] for r in rows}
    assert "naive_defender" not in baselines and {"none", "naive_attacker"} <= baselines          # decision 32: the play and the other baselines run
    assert entry["baseline_no_fit"] == []                                                         # a blind post is not a no_fit cut


def test_control_a_shiftable_post_is_fought_and_not_refused(tmp_path, fake_scene):
    fake_scene(base_build([blob(0, "Vanguard", 1, *POST)], [WALL], enemy_at=ENEMY_AT))
    entry, rows = run_family(tmp_path)
    assert not [r for r in entry["refused"] if r["reason"] == "blind_post"]
    assert {r["baseline"] for r in rows} >= {"none", "naive_attacker", "naive_defender"}


def test_the_smoke_lists_the_blind_post_refusal_too(tmp_path, fake_scene):
    fake_scene(base_build([blob(0, "Vanguard", 1, 900.0, 1000.0)], [Block(1000.0, 100.0, 1100.0, 1900.0)], enemy_at=(1500.0, 1000.0)))
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    summary = sweep.run_smoke(tmp_path, workers=1, builds=sweep.default_builds, layouts=LAYOUTS, fight_fn=Wins(), control_builds=controls, replicates=1)
    got = [r for r in summary["refused"] if r["reason"] == "blind_post"]
    assert got and all(r["role"].startswith("naive_defender") and r["layout"] == "A" and "family" not in r for r in got)
