# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md Rev 4 (2026-10-07): feature-relative placement per play, roles
"""Rev 4 rule 1: scenes.placed_scene resolves each play's anchors against the layout's features.

Names the spec leaves open, fixed here (the builder must match, or the test-writer is told):
  - scenes.placed_scene(layout, play, start_distance, features) -> build(enemy_heads, swap); `layout` is the Terrain from
    maps.layout_map(features, seed), `features` the maps.Features it came from (the walls say where the choke is, the
    features say whether there is one); `play` is a plays_space.PLAYS name or "naive". Side 0 is always the skilled / counter /
    naive side as in the scans; the defender is side 0 when the play's role is "defender", side 1 when "attacker".
  - plays_space.PLAYS[name].anchors has attributes `.role` ("defender" | "attacker"), `.defender` and `.attacker` (kind strings,
    the KINDS table below).
  - The returned Setup: decided_by_survivors True, defender_side = the defender's side, hold_anchor = the defender's anchor,
    terrain = the layout (maybe moved as a whole: the tests read geometry from setup.terrain, offset from the first block or cover).
  - build.labels["placement_shift"]: signed wu along +x (the corridor axis) the defender's formation was moved from its
    nominal anchor to fit the walkable mask; 0.0 when it was not moved.
Anchors the spec table leaves ambiguous, chosen here:
  - "choke mouth" and "choke exit" are the same point: the defender-side opening of the gap, (C.x + side * wall_thickness / 2, C.y)
    with C the gap midpoint; with no choke, C is the corridor midpoint and mouth = exit = C.
  - s2_spread_line "at one reach" = one weapon reach beyond the exit, like s1_outrange (reach of the play's own unit).
  - s1_outrange is a defender play (table row 2); its "counter use" row is not tested (it would put the same play on both roles).
  - lane mouth = the defender-side end of the lane channel, on the corridor axis; far side (s5) = the frail group FRAIL_BACK
    behind the choke on the defender's side; behind cover = the defender side of the nearest cover disc to the exit, one radius out.
  - s4_do_not_chase attacker "holds": at least half its units on guard; the other attackers attack-move at the defender's anchor.
"""
import hashlib
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import formations, maps, plays, plays_space, scenes  # noqa: E402
from scripts.skilllab.contract import Block  # noqa: E402

TOL = 150.0
WALL_T = maps.LAYOUT_WALL_THICK
SEED = 7

# play -> (role, defender anchor kind, attacker kind)
KINDS = {
    "s1_hold_choke": ("defender", "choke_mouth", "blob"),
    "s1_outrange": ("defender", "reach_beyond_exit", "blob"),
    "s2_concave": ("defender", "exit_concave", "blob"),
    "s2_spread_line": ("defender", "exit_line", "blob"),
    "s2_screen": ("defender", "exit_screen", "blob"),
    "s3_types_by_reach": ("defender", "behind_cover", "blob"),
    "s4_bait": ("defender", "lane_mouth", "blob"),
    "s5_vulnerable_away": ("defender", "far_side", "blob"),
    "s2_mass_one_end": ("attacker", "exit_line", "mass_one_end"),
    "s4_do_not_chase": ("attacker", "lane_mouth", "hold"),
}
PLAYS_PLACED = list(KINDS) + ["naive"]


def feats(choke=4, lane=1, cover=0.1, sd=1400.0):
    return maps.Features(choke_count=1 if choke else 0, choke_width_wu=choke * maps.LAYOUT_BODY_WU,
                         choke_width_bodies=float(choke), lane_count=lane, blocked_layer_ranges=(),
                         fight_layer_blocked=False, cover_density_corridor=cover, start_distance=sd,
                         detour_ratio=0.0, blocked_layer_top=4)


def scene(play, f, role_hint=None):
    layout = maps.layout_map(f, SEED)
    build = scenes.placed_scene(layout, play, f.start_distance, f)
    return layout, build, build(16, False)


def units(setup, groups):
    out = []
    for g in groups:
        out += formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
    return out


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def dist(a, b):
    return math.dist(a, b)


class Geo:
    """Geometry read from the built setup's own terrain."""

    def __init__(self, setup, layout, f):
        t = setup.terrain
        ref_new, ref_old = ((t.blocks[0].x0, t.blocks[0].y0), (layout.blocks[0].x0, layout.blocks[0].y0)) if layout.blocks \
            else ((t.covers[0].x, t.covers[0].y), (layout.covers[0].x, layout.covers[0].y))
        self.off = (ref_new[0] - ref_old[0], ref_new[1] - ref_old[1])
        walls = sorted((b for b in t.blocks if abs((b.x1 - b.x0) - WALL_T) < 1e-6), key=lambda b: b.y0)
        lanes = [b for b in t.blocks if abs((b.x1 - b.x0) - WALL_T) >= 1e-6]
        if f.choke_width_bodies:
            a, b = walls[:2]
            self.C = ((a.x0 + a.x1) / 2, (a.y1 + b.y0) / 2)
            self.t = WALL_T
        else:
            self.C = (self.off[0], self.off[1])      # the corridor midpoint of maps.DEFAULT_FRAME is (0, 0)
            self.t = 0.0
        self.lane_x = (min(b.x0 for b in lanes), max(b.x1 for b in lanes)) if lanes else None
        self.covers = t.covers


def dside_of(play):
    return 0 if play != "naive" and KINDS[play][0] == "defender" else 1


def sgn(dside):
    return -1 if dside == 0 else 1


def reach_of(play):
    r = plays.unit_stats("Vanguard")["attack_range"]
    return r * plays_space.OUTRANGE_FACTOR if play == "s1_outrange" else r


def mouth(geo, ds):
    return (geo.C[0] + sgn(ds) * geo.t / 2, geo.C[1])


def lane_mouth(geo, ds):
    if geo.lane_x is None:
        return mouth(geo, ds)
    return (geo.lane_x[0] if ds == 0 else geo.lane_x[1], geo.C[1])


def nearest_cover(geo, ds):
    m = mouth(geo, ds)
    return min(geo.covers, key=lambda c: dist((c.x, c.y), m))


def defender_groups(setup, ds):
    return [g for g in setup.groups if g.side == ds]


def anchor_units(play, setup, ds):
    gs = defender_groups(setup, ds)
    if play == "s4_bait" or play == "s4_do_not_chase":
        gs = gs[:1]
    elif play == "s3_types_by_reach":
        gs = [g for g in gs if g.unit != "Vanguard"]
    elif play == "s5_vulnerable_away":
        gs = [g for g in gs if g.unit == "VanguardFrail"]
    return units(setup, gs)


def expected(play, geo, ds):
    s = sgn(ds)
    m = mouth(geo, ds)
    kind = "choke_mouth" if play == "naive" else KINDS[play][1]
    r = reach_of(play)
    if kind in ("choke_mouth", "exit_concave", "exit_screen"):
        return m
    if kind in ("reach_beyond_exit", "exit_line"):
        return (m[0] + s * (r if play != "s2_mass_one_end" else reach_of("s2_spread_line")), m[1])
    if kind == "lane_mouth":
        return lane_mouth(geo, ds)
    if kind == "far_side":
        return (geo.C[0] + s * plays_space.FRAIL_BACK, geo.C[1])
    c = nearest_cover(geo, ds)
    return (c.x + s * c.radius, c.y)


# ---- (1) the table, per play, at both start distances -------------------------------------------------------------

@pytest.mark.parametrize("sd", [1400.0, 2800.0])
@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_defender_stands_at_its_declared_anchor(play, sd):
    """Rev 4 rule 1: the defender's formation (the group the anchor names) is within 150 wu of the anchor plus the recorded
    placement_shift (TD-LAB-fit-after-shift: the whole-formation fit can move a line up to FIT_LIMIT along the corridor axis)."""
    f = feats(sd=sd)
    layout, build, setup = scene(play, f)
    ds = dside_of(play)
    geo = Geo(setup, layout, f)
    got = centroid(anchor_units(play, setup, ds))
    ex = expected(play, geo, ds)
    shift = build.labels["placement_shift"] or 0.0
    assert dist(got, (ex[0] + shift, ex[1])) <= TOL


@pytest.mark.parametrize("sd", [1400.0, 2800.0])
@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_attacker_stands_start_distance_from_the_choke_on_the_other_side(play, sd):
    """Rev 4 rule 1: the attacker's centroid is start_distance (+-150) from the choke, on the side away from the defender."""
    f = feats(sd=sd)
    layout, _b, setup = scene(play, f)
    ds = dside_of(play)
    geo = Geo(setup, layout, f)
    c = centroid(units(setup, [g for g in setup.groups if g.side != ds]))
    assert abs(dist(c, geo.C) - sd) <= TOL
    assert (c[0] - geo.C[0]) * sgn(ds) < 0


@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_defender_guards_attacker_attack_moves_toward_the_defender(play):
    """Rev 4 rule 1: the defender holds (guard) unless its timeline says otherwise; the attacker is the only side that approaches."""
    f = feats()
    layout, _b, setup = scene(play, f)
    ds = dside_of(play)
    dgs, ags = defender_groups(setup, ds), [g for g in setup.groups if g.side != ds]
    if play == "s4_bait":                     # the bait group is the one the timeline sends; the rest hold
        assert all(g.order == "guard" for g in dgs[1:]) and dgs[1:]
    else:
        assert all(g.order == "guard" for g in dgs)
    anchor = centroid(units(setup, dgs))
    if play == "s4_do_not_chase":
        assert sum(g.count for g in ags if g.order == "guard") * 2 >= sum(g.count for g in ags)
        movers = [g for g in ags if g.order != "guard"]
    else:
        movers = ags
    first = (dgs[0].x, dgs[0].y)
    for g in movers:
        assert g.order == "attack_move"
        aim = g.goal if g.goal is not None else first
        assert dist(aim, anchor) <= 300.0 or (play == "s2_mass_one_end" and abs(aim[0] - anchor[0]) <= 300.0)
    assert setup.decided_by_survivors is True
    assert setup.defender_side == ds
    assert dist(setup.hold_anchor, anchor) <= 300.0


@pytest.mark.parametrize("play", ["s4_bait", "s4_do_not_chase"])
def test_bait_timeline_is_kept(play):
    """Rev 4 table: 'bait play, timeline unchanged': the same steps (order) on the bait's own groups. The `when` of s4_bait is
    ruled to be first sight, see test_bait_timeline_fires_on_first_sight_not_on_fixed_ticks (TD-LAB-bait-sight)."""
    f = feats()
    _l, _b, setup = scene(play, f)
    want = [(s.when if play != "s4_bait" else None, s.order) for s in plays_space.PLAYS[play].timeline]
    assert want
    assert [(s.when if play != "s4_bait" else None, s.order) for s in setup.timeline] == want
    bait_side = dside_of(play)
    assert all(setup.groups[s.group].side == bait_side for s in setup.timeline)


@pytest.mark.parametrize("sd", [1400.0, 2800.0])
def test_bait_timeline_fires_on_first_sight_not_on_fixed_ticks(sd):
    """Ruled 2026-10-07: the bait's retreat and the main group's close are keyed to the first tick an attacker is within the
    bait group's sight ('seen'), not to fixed ticks: the fixed ticks 100/150 fire before an attacker 1,400+ wu away arrives
    (red now: the placed scene keeps the plays_space ('tick', n) steps)."""
    f = feats(sd=sd)
    _l, _b, setup = scene("s4_bait", f)
    assert len(setup.timeline) == 2
    retreat, close = sorted(setup.timeline, key=lambda t: t.order != "move")
    assert (retreat.order, close.order) == ("move", "attack_move")
    assert [t.when for t in setup.timeline] == [("seen",), ("seen",)], [t.when for t in setup.timeline]


def test_s3_shorts_stand_in_front_of_the_long_types_behind_cover():
    """Rev 4 table s3: long-reach types behind the nearest cover, short-reach in front (toward the attacker)."""
    f = feats()
    _l, _b, setup = scene("s3_types_by_reach", f)
    gs = defender_groups(setup, 0)
    longs = centroid(units(setup, [g for g in gs if g.unit != "Vanguard"]))
    shorts = centroid(units(setup, [g for g in gs if g.unit == "Vanguard"]))
    assert (shorts[0] - longs[0]) * sgn(0) < 0


def test_s4_ambush_stands_beside_the_bait():
    """Rev 4 table s4: the ambush group is behind cover beside the bait group at the lane mouth (within 300 wu of it)."""
    f = feats()
    _l, _b, setup = scene("s4_bait", f)
    gs = defender_groups(setup, 0)
    bait = centroid(units(setup, gs[:1]))
    assert all(dist(centroid(units(setup, [g])), bait) <= 300.0 for g in gs[1:])


# ---- (2) fallbacks -----------------------------------------------------------------------------------------------

def test_no_choke_the_hold_play_stands_at_the_corridor_midpoint():
    """Rev 4: no choke (width none) = the choke is the corridor midpoint; the attacker is start_distance from it."""
    f = feats(choke=0)
    layout, _b, setup = scene("s1_hold_choke", f)
    geo = Geo(setup, layout, f)
    assert dist(centroid(units(setup, defender_groups(setup, 0))), geo.C) <= TOL
    att = centroid(units(setup, defender_groups(setup, 1)))
    assert abs(dist(att, geo.C) - 1400.0) <= TOL


def test_no_lane_the_bait_mouth_is_the_choke_mouth():
    """Rev 4: no lane = the bait mouth is the choke mouth."""
    f = feats(lane=0)
    layout, _b, setup = scene("s4_bait", f)
    geo = Geo(setup, layout, f)
    assert dist(centroid(units(setup, defender_groups(setup, 0)[:1])), mouth(geo, 0)) <= TOL


def test_no_cover_the_long_types_stand_behind_the_formation():
    """Rev 4: no cover = 'behind cover' is 'behind the formation': the long types are behind the shorts, near the exit."""
    f = feats(cover=0.0)
    layout, _b, setup = scene("s3_types_by_reach", f)
    geo = Geo(setup, layout, f)
    gs = defender_groups(setup, 0)
    longs = centroid(units(setup, [g for g in gs if g.unit != "Vanguard"]))
    shorts = centroid(units(setup, [g for g in gs if g.unit == "Vanguard"]))
    assert (longs[0] - shorts[0]) * sgn(0) > 0
    assert dist(centroid(units(setup, gs)), mouth(geo, 0)) <= 250.0


# ---- (3) the shift rule ------------------------------------------------------------------------------------------

def _walkable(terrain, x, y):
    return not any(b.x0 <= x <= b.x1 and b.y0 <= y <= b.y1 and b.layer_lo <= 0 <= b.layer_hi for b in terrain.blocks)


def test_a_formation_that_does_not_fit_shifts_along_the_corridor_axis_and_the_row_records_it():
    """Rev 4: an anchor cell blocked on the play's layer shifts the formation along the corridor axis (y unchanged) until the
    whole formation is walkable, and build.labels['placement_shift'] records the signed x shift."""
    import dataclasses
    f = feats(lane=0, cover=0.0)
    base = maps.layout_map(f, SEED)
    blocked = dataclasses.replace(base, blocks=base.blocks + (Block(-420.0, -400.0, -40.0, 400.0, 0, 4),))
    s0 = scenes.placed_scene(base, "s1_hold_choke", 1400.0, f)
    s1 = scenes.placed_scene(blocked, "s1_hold_choke", 1400.0, f)
    a, b = s0(16, False), s1(16, False)
    ca = centroid(units(a, defender_groups(a, 0)))
    cb = centroid(units(b, defender_groups(b, 0)))
    assert all(_walkable(b.terrain, *p) for p in units(b, defender_groups(b, 0)))
    assert cb[0] < ca[0] - 100.0 and cb[1] == pytest.approx(ca[1])
    assert s1.labels["placement_shift"] - s0.labels["placement_shift"] == pytest.approx(cb[0] - ca[0])
    assert s1.labels["placement_shift"] < s0.labels["placement_shift"]


def test_a_formation_that_fits_records_zero_shift_on_a_clear_layout():
    """Rev 4: control for the shift: an open layout (no wall, no lane, no cover) places every play unshifted, label 0.0."""
    f = feats(choke=0, lane=0, cover=0.0)
    layout = maps.layout_map(f, SEED)
    for play in PLAYS_PLACED:
        build = scenes.placed_scene(layout, play, 1400.0, f)
        build(16, False)
        assert build.labels["placement_shift"] == 0.0, play


FIT_GRID = [(c, l, v) for c in (0, 2, 4, 8) for l in (0, 1, 2) for v in (0.0, 0.3)]


@pytest.mark.parametrize("choke,lane,cover", FIT_GRID)
@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_every_placed_defender_unit_stands_on_a_walkable_cell_of_its_layer(play, choke, lane, cover):
    """TD-LAB-fit-after-shift: the fit covers the whole formation, not the anchor cells only: no defender unit stands inside a
    block that covers its group's layer (red before: the builder checked each group's anchor point alone)."""
    f = feats(choke=choke, lane=lane, cover=cover)
    _l, build, setup = scene(play, f)
    ds = dside_of(play)
    if build.labels["placement_shift"] is None:
        pytest.skip("no fit found: the scene records None")
    bad = [(g.unit, p) for g in defender_groups(setup, ds) for p in units(setup, [g])
           if any(b.x0 <= p[0] <= b.x1 and b.y0 <= p[1] <= b.y1 and b.layer_lo <= g.layer <= b.layer_hi for b in setup.terrain.blocks)]
    assert not bad, bad[:3]


# ---- (6) the declarations ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("play", list(KINDS))
def test_every_play_declares_anchors(play):
    """Rev 4 build impact: plays_space.PLAYS[name].anchors holds role, defender anchor kind and attacker kind."""
    a = plays_space.PLAYS[play].anchors
    assert (a.role, a.defender, a.attacker) == KINDS[play]


# ---- (7) existing scenes untouched -------------------------------------------------------------------------------

PLAYS_SPACE_HASH = "1f357bfc6f827628405b3cf74d8f7f32d23cbf202a2980a4f1be82ed73997897"   # recorded on main f6dc9959


def test_registered_space_plays_keep_their_setups():
    """Rev 4: adding anchors changes no registered setup (hash of groups, unit_types, timeline, settings, terrain of setup_fn() per play, recorded before the change).
    The Rev 3 rows hash (existing contact-distance plays) is in test_decided_by_survivors.py."""
    def key(n):
        s = plays_space.PLAYS[n].setup_fn()
        return (n, repr((s.groups, s.unit_types, s.timeline, s.settings, s.terrain)))
    h = hashlib.sha256(repr([key(n) for n in sorted(plays_space.PLAYS)]).encode())
    assert h.hexdigest() == PLAYS_SPACE_HASH
