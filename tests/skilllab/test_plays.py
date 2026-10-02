# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-12
"""plays: shape of the Setup each play builds, the reach play's derived type, and the plays/formations hand-off."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402
from scripts.skilllab.plays import blob_play, line_play, reach_play  # noqa: E402

DEFAULTS = Setup(groups=(), unit_types={})
KIND_OF = {blob_play: "blob", line_play: "line", reach_play: "blob"}   # AC-12: reach_play uses blob like blob_play


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
def test_ac12_setup_shape_two_groups_facing_each_other(play):
    """AC-12 (Readings): side 0 of `size` at (-600,0) facing 0, side 1 of enemy_heads at (600,0) facing 180, layer 0."""
    s = play(16)(8, False)
    g0, g1 = s.groups
    assert isinstance(s, Setup) and isinstance(s.groups, tuple) and len(s.groups) == 2
    assert (g0.side, g0.count, g0.x, g0.y, g0.facing_deg) == (0, 16, -600.0, 0.0, 0.0)
    assert (g1.side, g1.count, g1.x, g1.y, g1.facing_deg) == (1, 8, 600.0, 0.0, 180.0)
    assert (g0.layer, g1.layer, g0.order, g1.order, g0.goal, g1.goal) == (0, 0, "attack_move", "attack_move", None, None)
    assert isinstance(g0, Group) and g0.formation == g1.formation == KIND_OF[play]


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
def test_ac12_setup_flags_default_to_contract_defaults(play):
    """AC-12: abilities off, max_ticks / stalemate_ticks / sample_every left at the Setup defaults."""
    s = play(4)(4, False)
    assert (s.abilities, s.max_ticks, s.stalemate_ticks, s.sample_every) == (
        False, DEFAULTS.max_ticks, DEFAULTS.stalemate_ticks, DEFAULTS.sample_every)


def test_ac12_blob_and_line_params_follow_the_brief():
    """AC-12 (Readings): blob radius = 80 + 12*sqrt(count) per side (blob_play and reach_play); line spacing = 30; the two kinds differ."""
    g0, g1 = blob_play(16)(9, False).groups
    assert g0.params["radius"] == pytest.approx(80 + 12 * math.sqrt(16))
    assert g1.params["radius"] == pytest.approx(80 + 12 * math.sqrt(9))
    r0, r1 = reach_play(16)(9, False).groups
    assert r0.params["radius"] == pytest.approx(80 + 12 * math.sqrt(16))
    assert r1.params["radius"] == pytest.approx(80 + 12 * math.sqrt(9))
    l0, l1 = line_play(16)(9, False).groups
    assert l0.params["spacing"] == l1.params["spacing"] == 30
    assert g0.formation != l0.formation


@pytest.mark.parametrize("play", [blob_play, line_play])
def test_ac12_plain_plays_use_the_same_plain_unit_both_sides_and_no_custom_types(play):
    """AC-12: side 1 uses side 0's unit and formation; naive plays register no types."""
    for unit in ("Vanguard", "Warden"):
        s = play(6, unit=unit)(5, False)
        assert (s.groups[0].unit, s.groups[1].unit, s.unit_types) == (unit, unit, {})
    assert play(6)(5, False).groups[0].unit == "Vanguard"


@pytest.mark.parametrize("heads", [4, 9, 16, 24])
def test_ac12_reach_and_blob_scans_differ_only_in_reach(heads):
    """AC-12: for equal size and enemy_heads, reach_play and blob_play build the same groups except side 0's unit (the reach advantage)."""
    plain = blob_play(16)(heads, False)
    reach = reach_play(16)(heads, False)
    for gp, gr in zip(plain.groups, reach.groups):
        assert (gp.side, gp.count, gp.formation, gp.params, gp.x, gp.y, gp.facing_deg, gp.layer, gp.order, gp.goal) == (
            gr.side, gr.count, gr.formation, gr.params, gr.x, gr.y, gr.facing_deg, gr.layer, gr.order, gr.goal)
    assert plain.groups[1].unit == reach.groups[1].unit and plain.groups[0].unit != reach.groups[0].unit
    assert (plain.abilities, plain.max_ticks, plain.stalemate_ticks, plain.sample_every) == (
        reach.abilities, reach.max_ticks, reach.stalemate_ticks, reach.sample_every)


def test_ac12_reach_play_derives_a_long_type_on_side_0_only():
    """AC-12: side 0 uses `<unit>Long` = base unit with attack_range scaled 1.2; side 1 stays plain."""
    s = reach_play(16)(8, False)
    entry = s.unit_types["VanguardLong"]
    assert list(s.unit_types) == ["VanguardLong"]
    assert entry["base"] == "Vanguard" and entry["scale"] == {"attack_range": pytest.approx(1.2)}
    assert not entry.get("set")
    assert (s.groups[0].unit, s.groups[1].unit) == ("VanguardLong", "Vanguard")


def test_ac12_reach_play_unit_and_factor_parameters_are_honoured():
    """AC-12: a non-default unit and factor change the type name, base and scale (no hard-coded Vanguard / 1.2)."""
    s = reach_play(10, unit="Warden", factor=1.5)(10, True)
    assert list(s.unit_types) == ["WardenLong"]
    assert s.unit_types["WardenLong"]["base"] == "Warden"
    assert s.unit_types["WardenLong"]["scale"] == {"attack_range": pytest.approx(1.5)}
    assert (s.groups[0].unit, s.groups[1].unit) == ("WardenLong", "Warden")


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
def test_ac12_swap_leaves_the_setup_unchanged(play):
    """AC-12: the spawn order is applied inside fight, so build(n, True) == build(n, False)."""
    build = play(7)
    assert build(5, True) == build(5, False)


@pytest.mark.parametrize("heads", [1, 24])
def test_ac12_counts_side_0_fixed_side_1_follows_enemy_heads(heads):
    """AC-12 (cardinality one / peak): side 0 stays `size`; side 1 is exactly enemy_heads."""
    s = reach_play(16)(heads, False)
    assert (s.groups[0].count, s.groups[1].count) == (16, heads)
    assert blob_play(1)(heads, False).groups[0].count == 1


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
def test_ac12_groups_are_placeable_by_formations_and_stay_on_their_own_half(play):
    """AC-12 interaction with formations.place: each group's kind/params yield `count` points; sides do not overlap."""
    s = play(16)(12, False)
    pts = [place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params) for g in s.groups]
    assert [len(p) for p in pts] == [16, 12]
    assert max(p[0] for p in pts[0]) < 0.0 < min(p[0] for p in pts[1])


def test_ac12_line_plays_place_units_abreast_across_the_facing():
    """AC-12 interaction: a line play's points share one x (perpendicular to facing 0 / 180) and span (n-1)*spacing in y."""
    g0, g1 = line_play(16)(10, False).groups
    for g in (g0, g1):
        pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
        xs = [p[0] for p in pts]
        ys = sorted(p[1] for p in pts)
        assert max(xs) - min(xs) < 1e-4
        assert ys[-1] - ys[0] == pytest.approx((g.count - 1) * 30.0, abs=1e-3)


def test_ac12_reach_play_blob_points_stay_within_the_blob_radius_of_each_anchor():
    """AC-12 interaction: reach_play's groups are blobs; every point lies within the group's radius of its anchor."""
    for g in reach_play(16)(10, False).groups:
        pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
        assert g.formation == "blob"
        assert max(math.hypot(p[0] - g.x, p[1] - g.y) for p in pts) <= g.params["radius"] + 1e-5


def test_ac12_build_is_callable_with_keywords_from_the_spec_signature():
    """AC-12: build(enemy_heads, swap) -> Setup, by name as the spec writes it."""
    assert isinstance(blob_play(3)(enemy_heads=4, swap=True), Setup)


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
@pytest.mark.parametrize("size,heads", [(0, 8), (-1, 8), (8, 0), (8, -3)])
def test_ac12_size_or_enemy_heads_below_one_raises_valueerror_when_build_is_called(play, size, heads):
    """AC-12 (Readings): size or enemy_heads < 1 raises ValueError by the time build(enemy_heads, swap) has been called."""
    with pytest.raises(ValueError):
        play(size)(heads, False)


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play])
def test_ac12_unknown_unit_name_does_not_fail_at_build_time(play):
    """AC-12 (Readings): an unknown unit name builds a Setup; the failure comes later, inside fight."""
    s = play(4, unit="Zebra")(4, False)
    assert s.groups[1].unit == "Zebra" and s.groups[0].unit in ("Zebra", "ZebraLong")


@pytest.mark.parametrize("factor", [0.0, -1.2])
def test_ac12_reach_factor_zero_or_negative_raises_valueerror(factor):
    """AC-12 (Readings): factor <= 0 raises ValueError (at play creation or at build)."""
    with pytest.raises(ValueError):
        reach_play(16, factor=factor)(8, False)


def test_ac12_reach_factor_exactly_one_is_allowed():
    """AC-12 (Readings): factor 1.0 is allowed and scales by 1.0."""
    s = reach_play(16, factor=1.0)(8, False)
    assert s.unit_types["VanguardLong"]["scale"] == {"attack_range": pytest.approx(1.0)}
