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
    """P3 tests column: the 16 v 16 build equals today's fn() exactly."""
    assert plays_space.scan_build(name)(None, UNITS, False) == plays_space.PLAYS[name].setup_fn()


@pytest.mark.parametrize("name", NAMES)
def test_build_takes_the_layouts_map(name):
    """Audit row 1: the wrapper 'takes the layout's map'; the built Setup's terrain is that map's blocks and covers."""
    terrain = maps.sample_map("lane", 3)
    setup = plays_space.scan_build(name)(terrain, 12, False)
    assert setup.terrain.blocks == terrain.blocks
    assert setup.terrain.covers == terrain.covers
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
