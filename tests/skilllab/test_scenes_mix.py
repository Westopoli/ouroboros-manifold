# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, piece LAB-REV2-L3 (plays) and Q-LAB-03 / Westley 2026-10-13
# ("same units, same values, both sides, always"); audit fix pass of LAB-REV2-L3 tests, Architect ruling 2026-10-14.
"""The placed path (scenes.placed_scene, L2's file, edited by L3) fields the play's own two sides, the same mix on both.
Red on the lab branch: scenes._groups_and_timeline rebuilds side 1 as a Vanguard blob for every defender play, so s2_screen,
s3_layer_above, s3_types_by_reach, s3_over_the_choke, s5_vulnerable_away and the non-counter s1_outrange field unequal mixes (ruling 2);
and the ping step of s3_ping_then_commit is re-placed by group index (a ping aims at the enemy anchor, not at a side-0 group).
Reading: the play's own side 1 is used = the placed groups equal scan_build's groups in order, unit, count, formation, layer and params
(only x, y, facing, order and goal differ: they are what placement sets). Names are the existing ones: scenes.placed_scene(layout, play,
start_distance, features, counter=False)(enemy_heads, swap) -> Setup, plays_space.scan_build(play)(None, heads, False)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import maps, plays_space, scenes, timeline  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from test_placed_by_feature import SEED, centroid, feats, units  # noqa: E402
from test_plays_space import B, I, R, V, groups_of, mix_problems, reaches, resolve  # noqa: E402

PLAYS = ("s1_hold_choke", "s1_outrange", "s2_concave", "s2_spread_line", "s2_screen", "s3_layer_above", "s3_types_by_reach",
         "s3_over_the_choke", "s3_dark_striker", "s3_ping_then_commit", "s4_bait", "s5_vulnerable_away", "s2_mass_one_end",
         "s4_do_not_chase")
CASES = [(p, False) for p in PLAYS] + [("s1_outrange", True)]       # s1_outrange is also placed as the counter (COUNTER_USE)
HEADS = (16, 8, 48, 13, 29)


def placed(play, heads=16, counter=False, sd=1400.0, features=None):
    f = features or feats(sd=sd)
    layout = maps.layout_map(f, SEED)
    return scenes.placed_scene(layout, play, f.start_distance, f, counter=counter)(heads, False)


def own_side_problems(placed_setup, own_setup):
    """Empty when the placed groups are the play's own, in order (what placement may change is x, y, facing, order and goal)."""
    out = []
    if len(placed_setup.groups) != len(own_setup.groups):
        return ["%d groups placed, %d in the play" % (len(placed_setup.groups), len(own_setup.groups))]
    for i, (a, b) in enumerate(zip(placed_setup.groups, own_setup.groups)):
        for field in ("side", "unit", "count", "formation", "layer", "params"):
            if getattr(a, field) != getattr(b, field):
                out.append("group %d %s: placed %r, play %r" % (i, field, getattr(a, field), getattr(b, field)))
    if placed_setup.unit_types != own_setup.unit_types:
        out.append("unit_types differ")
    if placed_setup.settings != own_setup.settings:
        out.append("settings differ")
    return out


def _g(side, unit, count):
    return Group(side=side, unit=unit, count=count, formation="blob", x=0.0, y=0.0, facing_deg=0.0, layer=0, order="attack_move", params={"radius": 100})


def test_control_a_vanguard_blob_for_a_mixed_side_is_flagged_by_both_checks():
    """Control (the scenes.py defect shape): side 0 is 8 Vanguard + 8 Bombard, side 1 is rebuilt as 16 Vanguards. The mix check and the
    own-side check both flag it; the same mix on both sides is clean."""
    own = Setup(groups=(_g(0, V, 8), _g(0, B, 8), _g(1, V, 8), _g(1, B, 8)), unit_types={B: {"base": B, "reach": (0, 2)}})
    rebuilt = dataclasses.replace(own, groups=(own.groups[0], own.groups[1], _g(1, V, 16)))
    assert mix_problems(rebuilt, 16) and own_side_problems(rebuilt, own)
    assert mix_problems(own, 16) == [] and own_side_problems(own, own) == []


@pytest.mark.parametrize("heads", HEADS)
@pytest.mark.parametrize("play,counter", CASES)
def test_the_placed_scene_fields_the_same_mix_on_both_sides(play, counter, heads):
    """Ruling 2 at the scenes level: 16 on side 0, `heads` on side 1, each (type, reach) of side 1 the side-0 count scaled by heads / 16."""
    setup = placed(play, heads, counter)
    assert mix_problems(setup, heads) == [], (play, counter, heads)


@pytest.mark.parametrize("heads", (16, 8, 48))
@pytest.mark.parametrize("play,counter", CASES)
def test_the_placed_scene_uses_the_plays_own_side_1(play, counter, heads):
    """The placed scene keeps the play's own groups: same order, side, unit, count, formation, layer and params as scan_build, and the
    same unit_types and settings. Placement only sets x, y, facing, order and goal."""
    own = plays_space.scan_build(play)(None, heads, False)
    assert own_side_problems(placed(play, heads, counter), own) == [], (play, counter, heads)


@pytest.mark.parametrize("play", ["naive", "naive_line"])
@pytest.mark.parametrize("heads", HEADS)
def test_the_naive_scenes_keep_one_vanguard_mix_on_both_sides(play, heads):
    """Control, green by design: the naive scenes field 16 Vanguards against `heads` Vanguards, so the mix check passes on them."""
    assert mix_problems(placed(play, heads), heads) == []


# ---------------------------------------------------------------- group order in the placed path (see test_plays_space.GROUP_ORDER)

def _centre(setup, base, side=0):
    gs = [g for g in setup.groups if g.side == side and resolve(setup, g)[0] == base]
    return centroid(units(setup, gs))


def test_placed_screen_vanguards_stand_in_front_of_the_bombards():
    """exit_screen: group 0 (Vanguards) in front, group 1 (Bombards) behind; the defender is side 0 on the left, so front means larger x."""
    s = placed("s2_screen")
    assert _centre(s, V)[0] > _centre(s, B)[0]


@pytest.mark.parametrize("play,long_type", [("s3_layer_above", R), ("s3_types_by_reach", I)])
def test_placed_behind_cover_vanguards_stand_in_front_of_the_long_type(play, long_type):
    """behind_cover: group 0 (the long-reach type) at the cover, group 1 (Vanguards) BEHIND_COVER in front toward the attacker."""
    s = placed(play)
    assert _centre(s, V)[0] > _centre(s, long_type)[0]
    assert {g.layer for g in groups_of(s, 0, long_type)} == {1} and {g.layer for g in groups_of(s, 0, V)} == {0}


def test_placed_far_side_raiders_stand_behind_the_vanguards():
    """far_side: group 0 (Vanguards) at the choke mouth, group 1 (Raiders) behind it (FRAIL_BACK from the choke centre)."""
    s = placed("s5_vulnerable_away")
    assert _centre(s, V)[0] > _centre(s, R)[0]


# ---------------------------------------------------------------- the ping step in the placed path

@pytest.mark.parametrize("sd", (1400.0, 2800.0))
@pytest.mark.parametrize("heads", (16, 8, 48))
def test_placed_ping_goal_is_the_enemy_anchor_on_the_enemys_layer_at_tick_0(sd, heads):
    """s3_ping_then_commit placed: the one ping step is at tick 0, on the enemy's layer, aimed at the enemy's first anchor in the built
    Setup's own coordinates (the placed groups are moved onto the layout, the goal must move with them) and cast by the pinging side
    (a side-0 group), not re-placed by group index like a move goal. Red on the lab branch: the step goal is the group-index re-placement."""
    s = placed("s3_ping_then_commit", heads, sd=sd)
    timeline.validate(s)
    pings = [t for t in s.timeline if t.order == "ping"]
    assert len(pings) == 1 and pings[0].when == ("tick", 0) and pings[0].casters == "all"
    assert tuple(pings[0].goal) == pytest.approx(timeline.first_anchors(s)[1], abs=1e-6), (pings[0].goal, timeline.first_anchors(s))
    assert pings[0].layer == {g.layer for g in s.groups if g.side == 1}.pop()
    assert s.groups[pings[0].group].side == 0
    assert all(g.order == "attack_move" for g in s.groups if g.side == 0)


def test_placed_dark_striker_keeps_its_silent_steps_on_side_0():
    """s3_dark_striker placed: the set_emission steps of the play survive placement unchanged (group, when, on) and silence only side 0."""
    own = plays_space.PLAYS["s3_dark_striker"].timeline
    s = placed("s3_dark_striker")
    assert [(t.group, t.when, t.order, t.on) for t in s.timeline] == [(t.group, t.when, t.order, t.on) for t in own]
    assert all(s.groups[t.group].side == 0 for t in s.timeline)


def test_counter_use_of_s1_outrange_attacks_the_held_choke():
    """counter=True places s1_outrange as the attacker (side 0 attack-moves, long-range mix) against side 1 holding on guard."""
    s = placed("s1_outrange", counter=True)
    assert {g.order for g in s.groups if g.side == 1} == {"guard"}
    assert {g.order for g in s.groups if g.side == 0} == {"attack_move"}
    assert {resolve(s, g)[0] for g in s.groups if g.side == 0} == {"Vanguard", "Bastion"}


@pytest.mark.parametrize("play", ["s1_outrange", "s2_screen", "s3_over_the_choke", "s5_vulnerable_away"])
def test_placed_defender_plays_have_the_attacker_attack_moving_and_the_defender_on_guard(play):
    """The play's own side 1 may be a holder (s1_outrange) or move on its own; placing it as the attacker sets it to attack-move, and the
    defender (the play's side 0) to guard. Red for s1_outrange once the placed path stops rebuilding side 1 and forgets the order."""
    s = placed(play)
    assert {g.order for g in s.groups if g.side == 0} == {"guard"}
    assert {g.order for g in s.groups if g.side == 1} == {"attack_move"}


@pytest.mark.parametrize("sd", (1400.0, 2800.0))
def test_placed_bait_retreat_goal_moves_with_the_placed_groups(sd):
    """Extra finding, same defect class as the ping goal (not asked for in the fix list; the ruler may drop it): a step goal is built from
    the placed group but not moved onto the layout with the groups, so the s4_bait retreat 'move' lands thousands of wu off the canvas.
    The retreat goal is BAIT_FALLBACK_X behind the bait group's final position (the defender is side 0, on the left), on the canvas."""
    s = placed("s4_bait", sd=sd)
    retreat = next(t for t in s.timeline if t.order == "move")
    bait = s.groups[retreat.group]
    assert tuple(retreat.goal) == pytest.approx((bait.x - abs(plays_space.BAIT_FALLBACK_X), bait.y), abs=1e-6), (retreat.goal, (bait.x, bait.y))
