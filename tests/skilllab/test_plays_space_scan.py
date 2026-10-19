# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md, piece P3 (scannable space plays); rewritten for LAB-REV2-L3
# (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 1: mop-up, quiet-from-first-damage and the stall flags are retired, Q-LAB-03;
# ruling 2 and the roster mixes: the enemy side scales by ratio and keeps the side-0 mix; test_plays_space.py holds the mix checks)
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

NAMES = ("s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_layer_above", "s3_types_by_reach", "s3_over_the_choke",
         "s3_dark_striker", "s3_ping_then_commit", "s4_bait", "s5_vulnerable_away", "s2_mass_one_end", "s4_do_not_chase", "s1_outrange")
UNITS = 16


def _side(setup, side):
    return sum(g.count for g in setup.groups if g.side == side)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("heads", (8, 24, 48))
def test_each_play_builds_at_8_24_and_48_enemy_heads(name, heads):
    """Spec 'What the audit changed' row 1 + P3 tests column: each of the 14 plays builds at 8, 24 and 48 enemy heads; the skilled side stays 16."""
    setup = plays_space.scan_build(name)(None, heads, False)
    assert isinstance(setup, Setup)
    timeline.validate(setup)
    assert _side(setup, 0) == UNITS
    assert _side(setup, 1) == heads


@pytest.mark.parametrize("name", NAMES)
def test_16_v_16_build_is_the_plays_own_setup(name):
    """Ruling 1 (Q-LAB-03): no flags are added any more, so the 16 v 16 scan build IS fn() (red: it still replaces mopup / quiet fields)."""
    assert plays_space.scan_build(name)(None, UNITS, False) == plays_space.PLAYS[name].setup_fn()


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


# ---- stall fixes (Architect ruling 2026-10-06): one geometry for skilled plays, counters, naive scene; the flags are retired (Q-LAB-03) ----

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


RETIRED_FIELDS = ("mopup", "mopup_interval_ticks", "quiet_from_first_damage", "decided_by_survivors", "silence_ticks", "hold_anchor",
                  "hold_ticks", "defender_side", "approach", "stalemate_ticks", "objective", "start_distance")


@pytest.mark.parametrize("name", NAMES)
def test_scan_build_setup_carries_no_retired_stall_field(name):
    """Q-LAB-03: the retired fields are gone from the Setup the scan build returns, at 16 and at 24 heads."""
    for heads in (UNITS, 24):
        setup = plays_space.scan_build(name)(None, heads, False, D)
        assert [f for f in RETIRED_FIELDS if hasattr(setup, f)] == []


def test_control_the_retired_field_check_can_fail():
    """Control: a Setup-like object that still carries one of the fields is flagged by the same expression."""
    class Old:
        mopup = True
    assert [f for f in RETIRED_FIELDS if hasattr(Old, f)] == ["mopup"]


@pytest.mark.parametrize("name", NAMES)
def test_scan_build_keeps_the_play_timeline_and_settings_at_every_headcount(name):
    """The enemy count changes, nothing else: timeline, settings and unit types are the play's own (the ping and emission steps ride along)."""
    own = plays_space.PLAYS[name].setup_fn()
    for heads in (8, 48):
        setup = plays_space.scan_build(name)(None, heads, False)
        assert (setup.unit_types, setup.settings) == (own.unit_types, own.settings), heads
        assert [(t.order, t.when, t.on, t.layer) for t in setup.timeline] == [(t.order, t.when, t.on, t.layer) for t in own.timeline], heads
