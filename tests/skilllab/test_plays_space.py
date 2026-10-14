# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, piece LAB-REV2-L3 (plays); rulings 2 and 10; roster mixes M0 to M4
# (Q-LAB-03 / Westley 2026-10-13: "same units, same values, both sides, always"; no play sets a cross-layer vision factor)
"""Registered space-lab draft plays, rev 2: roster mixes instead of stat variants, the same mix on both sides, no vision factor,
every s3_* play puts a reach-capable type on another layer, a page that regenerates byte-identically and is in sync.
Reading: PlayDraft.setup_fn takes no arguments and returns a Setup whose side 0 fields 16 units. The mix, vision, variant, layer and sync
checks are helpers in this file, each with a positive control (a fake that must be flagged), so a green play proves the check can fail.
The lab has no integration marker; the engine tests are the only ones that load the library (like tests/skilllab/integration)."""
import collections
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, scenes, skills, timeline  # noqa: E402
from scripts.skilllab.contract import Block, Group, Setup, Terrain  # noqa: E402

SKILLED = ("s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_layer_above", "s3_types_by_reach",
           "s3_over_the_choke", "s3_dark_striker", "s3_ping_then_commit", "s4_bait", "s5_vulnerable_away")
COUNTERS = ("s2_mass_one_end", "s4_do_not_chase", "s1_outrange")
NAMES = SKILLED + COUNTERS
S3 = tuple(n for n in NAMES if n.startswith("s3_"))
STATUS = "unconfirmed draft, not measured"
UNITS = 16
TICKS = 50
HEADS = (8, 48)                      # the ends of the scan range (ruling 4)
VARIANT_NAMES = ("_HIGH", "_TOUGH", "_LONG", "_FRAIL", "_OUT")      # the retired stat variants (module-level dicts)
RETIRED_TYPES = ("VanguardTough", "VanguardLong", "VanguardHigh", "VanguardFrail", "VanguardOut")

# the reach table (batches.REACH_TABLE): (layers up, layers down) per roster type; Bombard and Bastion fire down two, Raider both ways one
ROSTER_REACH = {"Vanguard": (0, 0), "Raider": (1, 1), "Interceptor": (2, 1), "Bombard": (0, 2), "Bastion": (0, 2)}
V, R, I, B, A = "Vanguard", "Raider", "Interceptor", "Bombard", "Bastion"
M0 = {V: 16}
M1 = {V: 8, R: 8}
M2 = {V: 8, I: 8}
M3 = {V: 8, B: 8}
M4 = {V: 8, A: 8}
M3B = {V: 7, R: 1, B: 8}             # s3_over_the_choke (Architect ruling 2026-10-14): M3 with one Vanguard swapped for the Raider spotter, BOTH sides
# s3_over_the_choke scaled enemy side at 8 and 48 (largest-remainder rounding: 7, 1, 8 over 16 give 3.5, 0.5, 4 at 8 and exactly 21, 3, 24 at 48)
OVER_THE_CHOKE_SCALED = {8: {V: 3, R: 1, B: 4}, 48: {V: 21, R: 3, B: 24}}
# play -> mix of side 0 (the spec table). The six M0 plays are "controls, formation plays" (spec M0): flagged to the overseer as a reading.
# Plain M3 (8 Vanguard + 8 Bombard) stays for s2_screen; s3_over_the_choke is M3b.
PLAY_MIX = {"s1_hold_choke": M0, "s2_concave": M0, "s2_spread_line": M0, "s2_mass_one_end": M0, "s4_bait": M0, "s4_do_not_chase": M0,
            "s2_screen": M3, "s3_over_the_choke": M3B, "s3_layer_above": M1, "s3_types_by_reach": M2, "s3_dark_striker": M1, "s3_ping_then_commit": M1,
            "s5_vulnerable_away": M1, "s1_outrange": M4}


# ---------------------------------------------------------------- the checks (helpers, each with a control below)

def resolve(setup, g):
    """(roster base type, reach) of a group's unit: the unit_types entry's base and reach, else the built-in name with reach (0, 0)."""
    entry = setup.unit_types.get(g.unit)
    if entry is None:
        return g.unit, (0, 0)
    return entry.get("base", g.unit), tuple(entry.get("reach", (0, 0)))


def mix(setup, side):
    out = collections.Counter()
    for g in setup.groups:
        if g.side == side:
            out[resolve(setup, g)] += g.count
    return out


def mix_problems(setup, heads):
    """Empty when both sides field the same mix: side 0 has 16, side 1 has `heads`, and each (type, reach) count of side 1 is the
    side-0 count scaled by heads / 16 (exact where that is a whole number, within one otherwise)."""
    m0, m1 = mix(setup, 0), mix(setup, 1)
    out = []
    if sum(m0.values()) != UNITS:
        out.append("side 0 fields %d, not %d" % (sum(m0.values()), UNITS))
    if sum(m1.values()) != heads:
        out.append("side 1 fields %d, not %d" % (sum(m1.values()), heads))
    if set(m0) != set(m1):
        out.append("types differ: side 0 %s, side 1 %s" % (sorted(m0), sorted(m1)))
    for k in set(m0) & set(m1):
        want = m0[k] * heads / UNITS
        tol = 0 if want == int(want) else 1
        if abs(m1[k] - want) > tol:
            out.append("%s: side 1 has %d, scaled side 0 is %g" % (k, m1[k], want))
    return out


def vision_keys(setup):
    return sorted(k for k in setup.settings if k.startswith("OM_TP_VISION_"))


def variant_problems(setup):
    """Stat variants are retired: a unit_types entry carries a roster base and optionally a reach, nothing else."""
    out = []
    for name, entry in setup.unit_types.items():
        if set(entry) - {"base", "reach"}:
            out.append("%s sets %s" % (name, sorted(set(entry) - {"base", "reach"})))
        if entry.get("base") not in ROSTER_REACH:
            out.append("%s has base %r, not a roster type" % (name, entry.get("base")))
    return out


def reaches(reach, own_layer, target_layer):
    off = target_layer - own_layer
    return True if off == 0 else reach[0] >= off if off > 0 else reach[1] >= -off


def reach_on_another_layer(setup):
    """Some side-0 group stands on a layer other than the enemy's, with a type whose reach covers the enemy's layer."""
    enemy = {g.layer for g in setup.groups if g.side == 1}
    return any(g.side == 0 and g.layer not in enemy and all(reaches(resolve(setup, g)[1], g.layer, e) for e in enemy)
               for g in setup.groups)


def page_in_sync():
    return plays_space.PAGE.read_text() == plays_space.render_drafts_page()


def groups_of(setup, side, base):
    return [g for g in setup.groups if g.side == side and resolve(setup, g)[0] == base]


def _g(side, unit, count, layer=0, x=0.0, order="attack_move"):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=0.0, facing_deg=0.0, layer=layer, order=order,
                 params={"radius": 100})


def _fake(groups, unit_types=None, settings=None, timeline_=()):
    return Setup(groups=tuple(groups), unit_types=dict(unit_types or {}), settings=dict(settings or {}), timeline=tuple(timeline_))


RAIDER_REACH = {"Raider": {"base": "Raider", "reach": (1, 1)}}


# ---------------------------------------------------------------- positive controls (the checks can fail)

def test_control_unequal_mixes_are_rejected():
    """Control for the mix check: 8 Vanguards and 8 Raiders against 16 Vanguards is flagged; the same mix on both sides is not."""
    bad = _fake([_g(0, V, 8), _g(0, "Raider", 8), _g(1, V, 16)], RAIDER_REACH)
    assert any("types differ" in p for p in mix_problems(bad, 16)), mix_problems(bad, 16)
    good = _fake([_g(0, V, 8), _g(0, "Raider", 8), _g(1, V, 8), _g(1, "Raider", 8)], RAIDER_REACH)
    assert mix_problems(good, 16) == []


def test_control_the_mix_check_sees_a_wrong_scale_and_a_wrong_reach():
    """Control: 16 v 48 of the right types but 36 and 12 is flagged; the same type with another reach is another type."""
    skew = _fake([_g(0, V, 8), _g(0, "Raider", 8), _g(1, V, 36), _g(1, "Raider", 12)], RAIDER_REACH)
    assert mix_problems(skew, 48)
    other_reach = _fake([_g(0, "Raider", 16), _g(1, "RaiderFar", 16)], {**RAIDER_REACH, "RaiderFar": {"base": "Raider", "reach": (2, 2)}})
    assert mix_problems(other_reach, 16)
    even = _fake([_g(0, V, 8), _g(0, "Raider", 8), _g(1, V, 24), _g(1, "Raider", 24)], RAIDER_REACH)
    assert mix_problems(even, 48) == []


def test_control_a_vision_factor_is_flagged():
    """Control for the vision check: a play that sets a vision factor is flagged; one that sets another knob is not."""
    assert vision_keys(_fake([_g(0, V, 1)], settings={"OM_TP_VISION_UP_1": 0.5})) == ["OM_TP_VISION_UP_1"]
    assert vision_keys(_fake([_g(0, V, 1)], settings={"OM_TP_RANGE_DOWN_1": 1.0})) == []


def test_control_a_stat_variant_is_flagged():
    """Control for the variant check: a scaled Vanguard is flagged; a roster base with a reach is not."""
    variant = _fake([_g(0, "VanguardTough", 1)], {"VanguardTough": {"base": V, "scale": {"max_hp": 2.0}, "set": {}}})
    assert variant_problems(variant)
    assert variant_problems(_fake([_g(0, "Raider", 1)], RAIDER_REACH)) == []


def test_control_reach_on_another_layer_is_false_without_a_reach_or_a_layer():
    """Control: Raiders one layer up with no reach set cannot fire down; Raiders on the enemy's layer are not on another layer."""
    up_no_reach = _fake([_g(0, "Raider", 8, layer=1), _g(1, V, 8)])
    same_layer = _fake([_g(0, "Raider", 8, layer=0), _g(1, V, 8)], RAIDER_REACH)
    too_far = _fake([_g(0, "Raider", 8, layer=3), _g(1, V, 8)], RAIDER_REACH)
    for s in (up_no_reach, same_layer, too_far):
        assert not reach_on_another_layer(s)
    assert reach_on_another_layer(_fake([_g(0, "Raider", 8, layer=1), _g(1, V, 8)], RAIDER_REACH))


def test_control_the_sync_check_sees_a_stale_page(monkeypatch):
    """Control: with the page text altered the sync check fails."""
    monkeypatch.setattr(plays_space.Path, "read_text", lambda self, *a, **k: "stale")
    assert not page_in_sync()


# ---------------------------------------------------------------- the registry

def test_registry_holds_exactly_the_registered_plays():
    assert set(plays_space.PLAYS) == set(NAMES)


def test_the_stat_variants_are_gone():
    """Rev 2: the stat-scaled Vanguard variants and the _HIGH layer variant are retired (README section 4, ruling of 2026-10-13)."""
    assert [n for n in VARIANT_NAMES if hasattr(plays_space, n)] == []


@pytest.mark.parametrize("name", NAMES)
def test_play_builds_a_valid_setup_of_16_units(name):
    setup = plays_space.PLAYS[name].setup_fn()
    assert isinstance(setup, Setup)
    timeline.validate(setup)
    assert sum(g.count for g in setup.groups if g.side == 0) == UNITS
    assert sum(g.count for g in setup.groups if g.side == 1) >= 1


@pytest.mark.parametrize("name", NAMES)
def test_play_has_words_skill_status_and_a_named_number(name):
    p = plays_space.PLAYS[name]
    assert isinstance(p.words, str) and p.words.strip()
    assert p.skill in ("S1", "S2", "S3", "S4", "S5") and name.startswith(p.skill.lower() + "_")
    assert p.status.startswith(STATUS)
    assert isinstance(p.numbers, dict) and len(p.numbers) >= 1
    assert all(isinstance(k, str) and k and isinstance(v, (int, float)) for k, v in p.numbers.items())
    assert isinstance(p.timeline, tuple)


@pytest.mark.parametrize("name", NAMES)
def test_play_has_anchors(name):
    """scenes.placed_scene reads PLAYS[name].anchors: every play, new ones included, carries a role and two kinds."""
    a = plays_space.PLAYS[name].anchors
    assert isinstance(a, plays_space.Anchors) and a.role in ("defender", "attacker") and a.defender and a.attacker


def test_names_the_scene_builder_reads_still_exist():
    """scenes.py (LAB-REV2-L2's file, not L3's) reads these module names; L3 keeps them or STOPs (flagged: OUTRANGE_FACTOR and
    FRAIL_BACK belong to variants the spec retires, scenes.py still places by them)."""
    for n in ("UNITS", "SPREAD_SPACING", "SCREEN_AHEAD", "SCREEN_BEHIND", "FRAIL_BACK", "OUTRANGE_FACTOR", "Anchors", "COUNTER_USE", "scan_build"):
        assert hasattr(plays_space, n), n


# ---------------------------------------------------------------- the same mix on both sides (ruling 2)

@pytest.mark.parametrize("name", NAMES)
def test_every_play_fields_the_same_mix_on_both_sides_at_16_v_16(name):
    setup = plays_space.PLAYS[name].setup_fn()
    assert mix_problems(setup, UNITS) == []
    assert mix(setup, 0) == mix(setup, 1)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("heads", HEADS)
def test_every_play_builds_at_8_and_48_with_the_identical_mix(name, heads):
    """Counts scale by the ratio heads / 16 on the enemy side; side 0 stays 16. A mismatch of type, reach or ratio fails."""
    setup = plays_space.scan_build(name)(None, heads, False)
    timeline.validate(setup)
    assert mix_problems(setup, heads) == []


@pytest.mark.parametrize("name", NAMES)
def test_odd_headcounts_keep_the_mix_within_one_unit(name):
    """13 and 29 do not split evenly: the total is exact and each type is within one of the ratio."""
    for heads in (13, 29):
        assert mix_problems(plays_space.scan_build(name)(None, heads, False), heads) == [], heads


@pytest.mark.parametrize("name", sorted(PLAY_MIX))
def test_the_play_uses_its_roster_mix(name):
    """Spec roster mixes M0 to M4 (16 units, half each of the two types), by (type, reach)."""
    want = collections.Counter({(t, ROSTER_REACH[t]): n for t, n in PLAY_MIX[name].items()})
    assert mix(plays_space.PLAYS[name].setup_fn(), 0) == want


@pytest.mark.parametrize("name", NAMES)
def test_no_stat_variants_and_roster_reach_only(name):
    setup = plays_space.PLAYS[name].setup_fn()
    assert variant_problems(setup) == []
    assert not [t for t in RETIRED_TYPES if t in {g.unit for g in setup.groups}]
    for g in setup.groups:
        base, reach = resolve(setup, g)
        assert base in ROSTER_REACH and reach == ROSTER_REACH[base], (g.unit, base, reach)


@pytest.mark.parametrize("name", NAMES)
def test_the_naive_side_stands_on_one_layer(name):
    """The side-1 mix is fielded on a single layer (spec M0 to M4 note)."""
    for heads in (16,) + HEADS:
        setup = plays_space.scan_build(name)(None, heads, False)
        assert len({g.layer for g in setup.groups if g.side == 1}) == 1, heads


# ---------------------------------------------------------------- no vision factor (ruling 10)

@pytest.mark.parametrize("name", NAMES)
def test_no_play_sets_a_vision_factor(name):
    """Red on the lab branch: s3_types_by_reach sets OM_TP_VISION_DOWN_1 through its _HIGH variant."""
    for heads in (UNITS,) + HEADS:
        assert vision_keys(plays_space.scan_build(name)(None, heads, False)) == [], (name, heads)
    assert vision_keys(plays_space.PLAYS[name].setup_fn()) == []


# ---------------------------------------------------------------- every s3_* play: a reach-capable type on another layer

@pytest.mark.parametrize("name", S3)
@pytest.mark.parametrize("heads", HEADS)
def test_every_s3_play_puts_a_reach_capable_type_on_another_layer(name, heads):
    assert reach_on_another_layer(plays_space.scan_build(name)(None, heads, False)), name


# ---------------------------------------------------------------- the plays one by one

def test_layer_above_raiders_stand_one_layer_up_and_vanguards_level():
    s = plays_space.PLAYS["s3_layer_above"].setup_fn()
    assert {g.layer for g in groups_of(s, 0, R)} == {1}
    assert {g.layer for g in groups_of(s, 0, V)} == {0}
    assert {g.layer for g in s.groups if g.side == 1} == {0}


def test_types_by_reach_interceptors_up_vanguards_level():
    """Interceptor reach is (2 up, 1 down), so one layer up is the only layer from which they fire down at layer 0."""
    s = plays_space.PLAYS["s3_types_by_reach"].setup_fn()
    assert {g.layer for g in groups_of(s, 0, I)} == {1}
    assert {g.layer for g in groups_of(s, 0, V)} == {0}
    assert {g.layer for g in s.groups if g.side == 1} == {0}


def test_over_the_choke_bombards_above_the_wall_top():
    """Bombards (reach 0 up, 2 down) on a layer above every wall block's top and within two layers of the enemy's."""
    s = plays_space.PLAYS["s3_over_the_choke"].setup_fn()
    blocks = s.terrain.blocks
    assert blocks, "the choke is a wall"
    top = max(b.layer_hi for b in blocks)
    enemy_layer = {g.layer for g in s.groups if g.side == 1}
    assert len(enemy_layer) == 1
    bombards = groups_of(s, 0, B)
    assert bombards and all(g.layer > top and 0 < g.layer - next(iter(enemy_layer)) <= 2 for g in bombards), ([g.layer for g in bombards], top)
    assert groups_of(s, 0, V), "Vanguards stay in the mix"


def test_over_the_choke_bombards_stand_behind_the_wall_and_only_the_raider_spotter_stands_past_it():
    """Side 0 is on the left. The Bombards stand on the attacker's own side of the wall (mutant 'Bombards on the enemy's side' is red);
    the enemy is past the wall; the one side-0 group past the wall is the Raider spotter (Architect ruling 2026-10-14), and its reach
    covers the enemy's layer from its own, so it can see what the Bombards shoot at."""
    s = plays_space.PLAYS["s3_over_the_choke"].setup_fn()
    left, right = min(b.x0 for b in s.terrain.blocks), max(b.x1 for b in s.terrain.blocks)
    assert groups_of(s, 0, B) and all(g.x < left for g in groups_of(s, 0, B)), [(g.x, left) for g in groups_of(s, 0, B)]
    assert all(g.x > right for g in s.groups if g.side == 1), "the enemy stands past the wall"
    past = [g for g in s.groups if g.side == 0 and g.x > right]
    assert past and {resolve(s, g)[0] for g in past} == {R}, [(g.unit, g.x) for g in past]
    assert sum(g.count for g in past) == 1
    enemy_layer = {g.layer for g in s.groups if g.side == 1}.pop()
    assert all(reaches(resolve(s, g)[1], g.layer, enemy_layer) for g in past)


@pytest.mark.parametrize("heads", (UNITS,) + HEADS)
def test_over_the_choke_mix_is_m3b_on_both_sides_and_scales_exactly(heads):
    """16: 7 Vanguard + 1 Raider + 8 Bombard on both sides (side 0 stays 16 at every scan size); 8 and 48 give V3 R1 B4 and V21 R3 B24
    (the largest-remainder rounding; scan_build's plain rounding gives V4 R1 B3 at 8). Reach is the roster's for each type."""
    s = plays_space.scan_build("s3_over_the_choke")(None, heads, False)
    want = {t: n for t, n in (M3B if heads == UNITS else OVER_THE_CHOKE_SCALED[heads]).items()}
    side1 = collections.Counter()
    for g in s.groups:
        if g.side == 1:
            assert resolve(s, g)[1] == ROSTER_REACH[resolve(s, g)[0]], g.unit
            side1[resolve(s, g)[0]] += g.count
    assert dict(side1) == want
    assert mix(s, 0) == collections.Counter({(t, ROSTER_REACH[t]): n for t, n in M3B.items()})


def test_over_the_choke_wall_has_an_opening_and_a_top_below_the_top_layer():
    """The wall is a choke (a gap between two blocks) and not the full five-layer wall: the Bombards must be able to stand above it."""
    blocks = plays_space.PLAYS["s3_over_the_choke"].setup_fn().terrain.blocks
    ranked = sorted(blocks, key=lambda b: b.y0)
    assert len(ranked) >= 2 and any(a.y1 < b.y0 for a, b in zip(ranked, ranked[1:]))
    assert max(b.layer_hi for b in blocks) < 4


def test_dark_striker_side_0_goes_silent_at_tick_0_and_the_naive_side_does_not():
    """Skilled silent, naive emitting: every side-0 group has a set_emission step on=False at tick 0; no side-1 group is silenced."""
    s = plays_space.PLAYS["s3_dark_striker"].setup_fn()
    silent = {t.group for t in s.timeline if t.order == "set_emission" and t.on is False and t.when == ("tick", 0)}
    assert silent == {i for i, g in enumerate(s.groups) if g.side == 0}
    assert not [t for t in s.timeline if t.order == "set_emission" and s.groups[t.group].side == 1 and t.on is False]


@pytest.mark.parametrize("start_distance", (None, 2800))
def test_ping_then_commit_pings_the_enemys_layer_at_its_anchor_at_tick_0(start_distance):
    """The ping goal is the enemy's first anchor, also after start_distance moves the anchors (the shift is per side and a ping
    belongs to side 0's group index but aims at side 1)."""
    s = plays_space.scan_build("s3_ping_then_commit")(None, UNITS, False, start_distance)
    pings = [t for t in s.timeline if t.order == "ping"]
    assert len(pings) == 1 and pings[0].when == ("tick", 0)
    enemy = timeline.first_anchors(s)[1]
    assert tuple(pings[0].goal) == pytest.approx(enemy, abs=1e-6)
    assert pings[0].layer == {g.layer for g in s.groups if g.side == 1}.pop()
    assert pings[0].casters == "all"


def test_ping_then_commit_every_side_0_group_attack_moves_in_the_end():
    s = plays_space.PLAYS["s3_ping_then_commit"].setup_fn()
    for i, g in enumerate(s.groups):
        if g.side == 0:
            assert g.order == "attack_move" or any(t.group == i and t.order == "attack_move" for t in s.timeline), i


def test_screen_vanguards_stand_in_front_of_the_bombards():
    s = plays_space.PLAYS["s2_screen"].setup_fn()
    van, bom = groups_of(s, 0, V), groups_of(s, 0, B)
    assert van and bom and min(g.x for g in van) > max(g.x for g in bom)       # side 0 is on the left, the enemy on the right
    assert all(g.order == "attack_move" for g in van + bom)


def test_vulnerable_away_raiders_stand_behind_the_vanguards_by_at_least_frail_back():
    """Not just 'lower x': the frail type stands FRAIL_BACK (draft 400) or more behind the strong line (scenes.py places the far-side
    anchor FRAIL_BACK behind the choke and reads plays_space.FRAIL_BACK)."""
    s = plays_space.PLAYS["s5_vulnerable_away"].setup_fn()
    van, rai = groups_of(s, 0, V), groups_of(s, 0, R)
    assert van and rai
    assert min(g.x for g in van) - max(g.x for g in rai) >= plays_space.FRAIL_BACK, ([g.x for g in van], [g.x for g in rai])
    assert {g.layer for g in van + rai} == {0}


# The group order scenes._defender_positions (scenes.py, the placed path, L2's file) expects for each defender anchor kind: it places
# defender groups by index, so the order of the play's own side-0 groups is part of the play's contract. exit_screen: [front, behind];
# behind_cover: [long-reach type at the cover, short-reach type BEHIND_COVER in front]; far_side: [the strong line at the choke mouth,
# the vulnerable type FRAIL_BACK behind]. (lane_mouth, s4_bait: [bait, ambush] is already pinned by test_placed_by_feature.)
GROUP_ORDER = {"s2_screen": (V, B), "s3_layer_above": (R, V), "s3_types_by_reach": (I, V), "s5_vulnerable_away": (V, R)}


@pytest.mark.parametrize("name", sorted(GROUP_ORDER))
def test_side_0_groups_come_in_the_order_the_placed_path_expects(name):
    s = plays_space.PLAYS[name].setup_fn()
    assert tuple(resolve(s, g)[0] for g in s.groups if g.side == 0) == GROUP_ORDER[name]


@pytest.mark.parametrize("name", [n for n in NAMES if n not in ("s2_mass_one_end", "s4_do_not_chase", "s1_outrange")])
def test_the_attacking_side_is_a_blob(name):
    """Every play but the three counters has a blob attacker: anchors.attacker == 'blob' and every group of the attacking side (side 1
    for a defender play, side 0 for an attacker play) is a blob. Left out: s2_mass_one_end (a column) and s4_do_not_chase (a hold), and
    s1_outrange, whose own side 1 is the held line it attacks (registered as a defender play, so the placed path reuses that line as
    the attacker; its attacker kind is 'blob' by the existing anchor table but the play's own side 1 is a line: flagged in the report)."""
    a = plays_space.PLAYS[name].anchors
    assert a.attacker == "blob"
    attacking = 1 if a.role == "defender" else 0
    s = plays_space.PLAYS[name].setup_fn()
    assert {g.formation for g in s.groups if g.side == attacking} == {"blob"}


def test_mass_one_end_enemy_is_the_spread_line():
    """The counter to the spread line faces a line at SPREAD_SPACING (the naive side 'in a blob or a line')."""
    s = plays_space.PLAYS["s2_mass_one_end"].setup_fn()
    enemy = [g for g in s.groups if g.side == 1]
    assert {g.formation for g in enemy} == {"line"} and {g.params["spacing"] for g in enemy} == {plays_space.SPREAD_SPACING}
    assert {g.formation for g in s.groups if g.side == 0} == {"column"}


def test_outrange_bastions_attack_the_held_wall():
    s = plays_space.PLAYS["s1_outrange"].setup_fn()
    assert s.terrain.blocks
    assert groups_of(s, 0, A) and all(g.order == "attack_move" for g in s.groups if g.side == 0)
    assert {g.order for g in s.groups if g.side == 1} == {"guard"}


# ---------------------------------------------------------------- the real engine

@pytest.fixture(scope="module")
def library():
    from scripts.skilllab.engine import Engine
    return Engine()


@pytest.mark.parametrize("name", NAMES)
def test_play_runs_50_ticks_on_the_open_map_in_the_real_engine(name):
    from scripts.skilllab.fight import fight
    setup = plays_space.PLAYS[name].setup_fn()
    result = fight(dataclasses.replace(setup, max_ticks=TICKS, terrain=None), seed=0)
    assert result.ticks <= TICKS


@pytest.mark.parametrize("name", NAMES)
def test_play_setup_passes_the_preflight_at_16_v_16(name, library):
    """The play's own scene (the walls it names, the layers it stands on) is `ok` before any tick."""
    assert scenes.preflight(plays_space.PLAYS[name].setup_fn(), library) == "ok"


def test_control_the_preflight_can_refuse_a_play(library):
    """Control: the same play with a block laid over the enemy's blob is refused, so 'ok' above carries information."""
    s = plays_space.PLAYS["s2_concave"].setup_fn()
    enemy = next(g for g in s.groups if g.side == 1)
    walled = dataclasses.replace(s, terrain=Terrain(canvas=s.terrain.canvas, blocks=(Block(enemy.x - 300, enemy.y - 300, enemy.x + 300, enemy.y + 300, 0, 4),)))
    assert scenes.preflight(walled, library) == "no_fit"


# ---------------------------------------------------------------- the page

def test_page_renders_byte_identically_and_names_every_play():
    a, b = plays_space.render_drafts_page(), plays_space.render_drafts_page()
    assert isinstance(a, str) and a == b and a.encode() == b.encode()
    for name in NAMES:
        assert name in a
    assert STATUS in a


def test_page_names_no_retired_variant():
    page = plays_space.render_drafts_page()
    assert [t for t in RETIRED_TYPES if t in page] == []


def test_the_drafts_page_on_disk_is_in_sync_with_the_registry():
    """docs/.../plays_drafts.md is generated by `python -m scripts.skilllab.plays_space`; the builder regenerates it."""
    assert page_in_sync()
    text = plays_space.PAGE.read_text()
    assert all(("## %s (" % n) in text for n in NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_skills_registry_points_at_the_play_with_status_draft(name):
    p = plays_space.PLAYS[name]
    role = "counter" if name in COUNTERS else "skilled"
    entry = skills.get(p.skill, role)
    assert entry.status == "draft"
    assert entry.skill == p.skill and entry.role == role
