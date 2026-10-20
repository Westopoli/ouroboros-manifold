# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md Rev 4 (2026-10-07): feature-relative placement per play, roles
"""Rev 4 rule 1: scenes.placed_scene resolves each play's anchors against the layout's features.

Names the spec leaves open, fixed here (the builder must match, or the test-writer is told):
  - scenes.placed_scene(layout, play, start_distance, features) -> build(enemy_heads, swap); `layout` is the Terrain from
    maps.layout_map(features, seed), `features` the maps.Features it came from (the walls say where the choke is, the
    features say whether there is one); `play` is a plays_space.PLAYS name or "naive". Side 0 is always the skilled / counter /
    naive side as in the scans; the defender is side 0 when the play's role is "defender", side 1 when "attacker".
  - plays_space.PLAYS[name].anchors has attributes `.role` ("defender" | "attacker"), `.defender` and `.attacker` (kind strings,
    the KINDS table below).
  - The returned Setup: terrain = the layout (moved as a whole: the tests read geometry from setup.terrain, offset from the first
    block or cover) and, LAB-REV2-L2 (Q-LAB-03, ruling 6), `point` = the holder's centre of mass (the mean of the holder's placed
    unit positions, on the holder's layer). decided_by_survivors, defender_side and hold_anchor are retired with the hold rule.
  - build.labels["prefight"] (LAB-REV2-L2; the label name is this test writer's reading of "the pre-fight record", the spec names
    no symbol): "ok", or "no_fit" when a placed unit stands inside a blocked cell on its layer. Nothing is shifted any more
    (the placement_shift of Rev 4, FIT_STEP and FIT_LIMIT, is retired with it); a build that still sets the label may set 0.0.
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
    # LAB-REV2-L3 (the test writer's reading; the spec names no anchors for the four new plays): the Raiders and Interceptors are long-reach
    # types that stand behind the short ones (behind_cover); the choke play defends the choke; the dark and ping plays are attacker plays
    # that come at a defender holding an exit line.
    "s3_layer_above": ("defender", "behind_cover", "blob"),
    "s3_over_the_choke": ("defender", "choke_mouth", "blob"),
    "s3_dark_striker": ("attacker", "exit_line", "blob"),
    "s3_ping_then_commit": ("attacker", "exit_line", "blob"),
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
    elif play in ("s3_types_by_reach", "s3_layer_above"):
        gs = [g for g in gs if g.unit != "Vanguard"]
    elif play == "s5_vulnerable_away":
        gs = [g for g in gs if g.unit == "Raider"]       # LAB-REV2-L3: the frail variant is retired, the Raiders stand back
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
    """Rev 4 rule 1: the defender's formation (the group the anchor names) is within 150 wu of the anchor (LAB-REV2-L2: nothing
    is shifted to fit any more, so a recorded placement_shift, when the build still sets one, is 0.0)."""
    f = feats(sd=sd)
    layout, build, setup = scene(play, f)
    ds = dside_of(play)
    geo = Geo(setup, layout, f)
    got = centroid(anchor_units(play, setup, ds))
    ex = expected(play, geo, ds)
    shift = build.labels.get("placement_shift") or 0.0
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
        aim = g.goal if g.goal is not None else setup.point
        assert dist(aim, anchor) <= 300.0 or (play == "s2_mass_one_end" and abs(aim[0] - anchor[0]) <= 300.0)
    assert not any(hasattr(setup, name) for name in ("decided_by_survivors", "defender_side", "hold_anchor", "hold_ticks"))
    assert setup.orders_per_unit is True


@pytest.mark.parametrize("sd", [1400.0, 2800.0])
@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_ruling_6_the_point_is_the_holders_centre_of_mass(play, sd):
    """Ruling 6 (centroid rule): an assault is the attacker attack-moved onto the holder's centre of mass, the mean of the
    holder's placed positions (every holder group, on the holder's layer), while the holder guards. Setup.point is that mean."""
    f = feats(sd=sd)
    _l, _b, setup = scene(play, f)
    ds = dside_of(play)
    pts = units(setup, defender_groups(setup, ds))
    assert setup.point == pytest.approx(centroid(pts), abs=1e-6)


@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_ruling_6_the_holder_guards_and_every_naive_attacker_group_aims_at_the_point(play):
    """Control for the test above: with no goal of its own a mover is sent to Setup.point (the fight reads it)."""
    f = feats()
    _l, _b, setup = scene(play, f)
    ds = dside_of(play)
    movers = [g for g in setup.groups if g.side != ds and g.order == "attack_move" and g.goal is None]
    if play in ("naive", "s1_hold_choke", "s1_outrange", "s2_concave", "s2_spread_line", "s2_screen"):
        assert movers, play
    assert all(g.goal is None for g in movers)
    assert setup.point is not None


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


def test_a_formation_on_a_blocked_cell_is_refused_no_fit_and_is_not_shifted():
    """Ruling 6 / spec L2: no shifting; a placed point inside a blocked cell makes the pre-fight record 'no_fit'. The same layout
    without the extra block is 'ok', and the defender stands in the same place in both (red on the old code: it slid the
    formation 50 wu at a time along the corridor axis to find a fit). Open layout: the hold play stands at the layout centre (0, 0)."""
    import dataclasses
    f = feats(choke=0, lane=0, cover=0.0)
    base = maps.layout_map(f, SEED)
    blocked = dataclasses.replace(base, blocks=base.blocks + (Block(-100.0, -100.0, 100.0, 100.0, 0, 4),))
    s0 = scenes.placed_scene(base, "s1_hold_choke", 1400.0, f)
    s1 = scenes.placed_scene(blocked, "s1_hold_choke", 1400.0, f)
    a, b = s0(16, False), s1(16, False)
    assert s0.labels["prefight"] == "ok" and s1.labels["prefight"] == "no_fit"
    ca = centroid(units(a, defender_groups(a, 0)))
    cb = centroid(units(b, defender_groups(b, 0)))
    assert cb == pytest.approx(ca)
    assert any(not _walkable(b.terrain, *p) for p in units(b, defender_groups(b, 0)))
    assert (s1.labels.get("placement_shift") or 0.0) == 0.0


def test_a_formation_that_fits_is_ok_on_a_clear_layout():
    """Control: an open layout (no wall, no lane, no cover) places every play 'ok' and unshifted."""
    f = feats(choke=0, lane=0, cover=0.0)
    layout = maps.layout_map(f, SEED)
    for play in PLAYS_PLACED:
        build = scenes.placed_scene(layout, play, 1400.0, f)
        build(16, False)
        assert build.labels["prefight"] == "ok", play
        assert (build.labels.get("placement_shift") or 0.0) == 0.0, play


FIT_GRID = [(c, l, v) for c in (0, 2, 4, 8) for l in (0, 1, 2) for v in (0.0, 0.3)]


@pytest.mark.parametrize("choke,lane,cover", FIT_GRID)
@pytest.mark.parametrize("play", PLAYS_PLACED)
def test_the_prefight_record_follows_whether_any_unit_stands_in_a_block(play, choke, lane, cover):
    """Spec L2 (no_fit): a unit of either side placed inside a blocked cell on its layer makes the record 'no_fit'; with every
    unit at least 20 wu clear of every block (more than the replicate shift of 10) it is 'ok'. Between the two, nothing is
    asserted (the border). Replaces TD-LAB-fit-after-shift (the fit by shifting is retired)."""
    f = feats(choke=choke, lane=lane, cover=cover)
    _l, build, setup = scene(play, f)
    pts = [(g.layer, p) for g in setup.groups for p in units(setup, [g])]

    def within(margin):
        return any(b.layer_lo <= layer <= b.layer_hi and b.x0 - margin <= p[0] <= b.x1 + margin and b.y0 - margin <= p[1] <= b.y1 + margin
                   for layer, p in pts for b in setup.terrain.blocks)

    if within(0.0):
        assert build.labels["prefight"] == "no_fit"
    elif not within(20.0):
        assert build.labels["prefight"] == "ok"
    else:
        assert build.labels["prefight"] in ("ok", "no_fit")


# ---- (6) the declarations ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("play", list(KINDS))
def test_every_play_declares_anchors(play):
    """Rev 4 build impact: plays_space.PLAYS[name].anchors holds role, defender anchor kind and attacker kind."""
    a = plays_space.PLAYS[play].anchors
    assert (a.role, a.defender, a.attacker) == KINDS[play]


# ---- (7) existing scenes untouched -------------------------------------------------------------------------------

# Re-recorded for LAB-REV2-L3 (ledger TD-LAB-REV2-L3-hash): the rev 2 plays (stat variants retired, four new plays, M3b, scan rounding).
# Re-recorded for LAB-VISION-CONTROL (ledger TD-LAB-VISION-CONTROL-registry): the registered control fixture s3_vision_control is enumerated;
# the 14 earlier plays' per-play setup hashes are unchanged (the old value c5c0965e... is the hash of those 14 alone).
PLAYS_SPACE_HASH = "fd83eeae8e27c500ba98b02d16b125b451f5fe04e5f700b176abd41d0785926b"   # L3 build 6826dd09 plays plus s3_vision_control


def test_registered_space_plays_keep_their_setups():
    """Rev 4: adding anchors changes no registered setup (hash of groups, unit_types, timeline, settings, terrain of setup_fn() per play, recorded before the change).
    (The Rev 3 rows hash of the contact-distance plays is retired with test_decided_by_survivors.py, Q-LAB-03; the goldens of
    integration/test_cross_machine.py guard the rows now.)"""
    def key(n):
        s = plays_space.PLAYS[n].setup_fn()
        return (n, repr((s.groups, s.unit_types, s.timeline, s.settings, s.terrain)))
    h = hashlib.sha256(repr([key(n) for n in sorted(plays_space.PLAYS)]).encode())
    assert h.hexdigest() == PLAYS_SPACE_HASH
