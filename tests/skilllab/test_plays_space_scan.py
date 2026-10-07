# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md, piece P3 (scannable space plays)
"""P3: each registered space play gets a BuildFn taking (map_or_None, enemy_heads, swap); skills.py says which skills have a counter.
Names chosen by the test writer (the spec names none): plays_space.scan_build(name) -> f(map, enemy_heads, swap) -> Setup,
and skills.has_counter(skill) -> bool. Flagged in the report for the architect to confirm."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import maps, plays_space, skills, timeline  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab.terrain import shift_terrain  # noqa: E402

NAMES = ("s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_types_by_reach", "s4_bait",
         "s5_vulnerable_away", "s2_mass_one_end", "s4_do_not_chase", "s1_outrange")
UNITS = 16


def _side(setup, side):
    return sum(g.count for g in setup.groups if g.side == side)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("heads", (8, 24))
def test_each_play_builds_at_8_and_24_enemy_heads(name, heads):
    """Spec 'What the audit changed' row 1 + P3 tests column: each of the 10 plays builds at 8 and 24 enemy heads; the skilled side stays 16."""
    setup = plays_space.scan_build(name)(None, heads, False)
    assert isinstance(setup, Setup)
    timeline.validate(setup)
    assert _side(setup, 0) == UNITS
    assert _side(setup, 1) == heads


@pytest.mark.parametrize("name", NAMES)
def test_16_v_16_build_equals_todays_fn(name):
    """P3 tests column: the 16 v 16 build equals today's fn() once the three stall flags are applied (TD-LAB-scan-build-flags)."""
    import dataclasses
    from scripts.skilllab import plays
    flags = dict(mopup=plays.MOPUP, mopup_interval_ticks=plays.MOPUP_INTERVAL_TICKS, quiet_from_first_damage=True)
    assert plays_space.scan_build(name)(None, UNITS, False) == dataclasses.replace(plays_space.PLAYS[name].setup_fn(), **flags)


@pytest.mark.parametrize("name", NAMES)
def test_build_takes_the_layouts_map(name):
    """Audit row 1: the wrapper 'takes the layout's map'; the built Setup's terrain is that map's blocks and covers."""
    terrain = maps.sample_map("lane", 3)
    setup = plays_space.scan_build(name)(terrain, 12, False)
    first = {}
    for g in setup.groups:
        first.setdefault(g.side, g)
    mid = ((first[0].x + first[1].x) / 2, (first[0].y + first[1].y) / 2)
    assert setup.terrain == shift_terrain(terrain, *mid)  # TD-LAB-scan-build-flags: map is shifted to the sides' midpoint
    assert _side(setup, 0) == UNITS and _side(setup, 1) == 12


@pytest.mark.parametrize("name", NAMES)
def test_build_is_deterministic_and_swap_keeps_the_skilled_side_16(name):
    """Audit row 1 (BuildFn shape, as plays.py/asym.py): same arguments give the same Setup; swap is applied by fight(), so the Setup is unchanged."""
    build = plays_space.scan_build(name)
    assert build(None, 8, False) == build(None, 8, False)
    assert build(None, 8, True) == build(None, 8, False)


def test_enemy_heads_below_one_is_rejected():
    """Audit row 1: like plays.py's builders, enemy_heads < 1 raises ValueError."""
    with pytest.raises(ValueError):
        plays_space.scan_build("s2_concave")(None, 0, False)


def test_unknown_play_name_is_rejected():
    """Audit row 1: asking for a play that is not registered raises ValueError."""
    with pytest.raises(ValueError):
        plays_space.scan_build("s9_nothing")


@pytest.mark.parametrize("skill,expected", [("S1", True), ("S2", True), ("S4", True), ("S3", False), ("S5", False)])
def test_skills_marks_which_skills_have_a_counter(skill, expected):
    """Audit row 2: counters registered for S1, S2 (spread line) and S4 only; S3 and S5 are 'no counter registered'."""
    assert skills.has_counter(skill) is expected


def test_has_counter_follows_the_registry(strip):
    """Audit row 2 positive control: the flag is read from the registry, not a fixed table; stripping S4's counter flips it."""
    strip("S4")
    assert skills.has_counter("S4") is False


def _anchor_gap(setup):
    """Anchor of a side = x of its first group (the play's main group); gap = enemy anchor minus ours."""
    first = {}
    for g in setup.groups:
        first.setdefault(g.side, g.x)
    return first[1] - first[0]


@pytest.mark.parametrize("name", NAMES)
def test_start_distance_places_anchors_that_far_apart(name):
    """Layout-search P4 ruling (Architect 2026-10-06): start_distance=2800 puts the two anchors 2800 wu apart on x; unit counts unchanged."""
    build = plays_space.scan_build(name)
    base = build(None, 16, False)
    far = build(None, 16, False, start_distance=2800)
    assert abs(_anchor_gap(far) - 2800) <= 1
    assert [(g.side, g.count) for g in far.groups] == [(g.side, g.count) for g in base.groups]


@pytest.mark.parametrize("name", NAMES)
def test_start_distance_none_is_todays_build_byte_equal(name):
    """Ruling: start_distance=None keeps today's gap; the Setup is equal to the call without the argument."""
    build = plays_space.scan_build(name)
    assert build(None, 16, False, start_distance=None) == build(None, 16, False)


# ---- stall fixes (Architect ruling 2026-10-06): one geometry and the same flags for skilled plays, counters, naive scene ----

import dataclasses  # noqa: E402

from scripts.skilllab import plays  # noqa: E402

D = 2800


def _choke_map():
    w = 4
    f = maps.Features(choke_count=1, choke_width_wu=w * maps.LAYOUT_BODY_WU, choke_width_bodies=float(w), lane_count=0,
                      blocked_layer_ranges=((0, 4),), fight_layer_blocked=True, cover_density_corridor=0.0,
                      start_distance=float(D), detour_ratio=0.0, blocked_layer_top=4)
    return maps.layout_map(f, 16, frame=maps.Frame((-D / 2, 0.0), (D / 2, 0.0), 0))


def _anchor_mid(setup):
    anchor = {}
    for g in setup.groups:
        anchor.setdefault(g.side, g.x)
    return (anchor[0] + anchor[1]) / 2


@pytest.mark.parametrize("name", NAMES)
def test_scan_build_walls_sit_between_the_units_inside_the_canvas(name):
    """Defect 1: the layout map must be shifted by canvas/2 like the groups; walls centred between the anchors, all inside the canvas."""
    setup = plays_space.scan_build(name)(_choke_map(), UNITS, False, D)
    assert setup.terrain.blocks
    mid = _anchor_mid(setup)
    cw, ch = setup.terrain.canvas
    xs = [(b.x0 + b.x1) / 2 for b in setup.terrain.blocks]
    assert all(abs(x - mid) <= 50 for x in xs), (xs, mid)
    assert all(0 <= b.x0 and b.x1 <= cw and 0 <= b.y0 and b.y1 <= ch for b in setup.terrain.blocks)


@pytest.mark.parametrize("name", NAMES)
def test_scan_build_setup_has_mopup_and_quiet_from_first_damage(name):
    """Defect 2: the stalemate clock must not fire during the approach; mop-up on, as in the plays."""
    setup = plays_space.scan_build(name)(None, UNITS, False, D)
    assert setup.mopup == plays.MOPUP
    assert setup.mopup_interval_ticks == plays.MOPUP_INTERVAL_TICKS
    assert setup.quiet_from_first_damage is True


@pytest.mark.parametrize("name", NAMES)
def test_16_v_16_build_equals_todays_fn_apart_from_the_three_flags(name):
    """Defect 2: the flags are the only change to the 16 v 16 build."""
    flags = dict(mopup=plays.MOPUP, mopup_interval_ticks=plays.MOPUP_INTERVAL_TICKS, quiet_from_first_damage=True)
    assert plays_space.scan_build(name)(None, UNITS, False) == dataclasses.replace(plays_space.PLAYS[name].setup_fn(), **flags)


def test_control_flag_free_setup_is_what_fails_the_flag_test():
    """Positive control: today's fn() setup lacks the flags, so the flag assertions can fail."""
    s = plays_space.PLAYS[NAMES[0]].setup_fn()
    assert s.quiet_from_first_damage is not True and s.mopup_interval_ticks == 200
