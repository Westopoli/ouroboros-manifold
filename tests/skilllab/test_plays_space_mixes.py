# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 45 ruling 5 (Architect, 2026-10-19): the roster mixes M1 to M4 and M3b become ONE data
# table in plays_space.py, marked DRAFT-mix-<name> on each row, and M5 to M9 are added to it only after Westley's go on the roster analysis
"""LAB-REV2-FIX round 5: the roster mixes as one data table (scripts/skilllab/plays_space.py). Ledger TD-LAB-REV2-FIX5-mixes.

INTERFACE FOR THE BUILDER (frozen here)
  plays_space.MIXES: a list of rows, each a dict {"name": str, "units": {unit type: count}, "used_in": (play name, ...), "enabled": bool}.
    - units: the existing numbers, no number changes. The dict order is the order of the side-1 groups (_enemy / the blobs follow it); side 0 keeps the order
      its setup places today (test_placed_by_feature.py's setup hashes pin the actual order of both sides, so keep them green).
    - Editing a row must also rewrite the hard-coded side-0 counts, the blob radii and the group counts: side 0 of s3_over_the_choke is V7, R1, B8 in the
      code today. The builder must make side-0 composition follow the table (the edit tests below fail if any side-0 number is still hard-coded).
    - The table holds exactly the five rows M1, M2, M3, M4 and M3b (M0, all Vanguard, is not a row). The module-level tuples M1..M4 and the inline
      M3b of _over_the_choke are gone: the table is the only place the numbers live.
    - A play reads its mix when its setup_fn is CALLED (module-global lookup of MIXES each call), not at import: a test that replaces plays_space.MIXES
      with an edited copy changes the next build. A play's mix is the one ENABLED row whose used_in names it; both sides field it (side 0 and the
      side-1 blob(s) at 16), exactly as today.
    - MIXES must be defined ABOVE PLAYS in plays_space.py: PLAYS builds its plays at import time, so the table has to exist by then (the lookup itself
      still happens at each setup_fn call, as above).
    - Two ENABLED rows naming the same play: building that play raises ValueError whose message holds the play name and the words "two mixes".
    - A play whose row is disabled: building it (setup_fn or scan_build(name)(...)) raises ValueError whose message holds the play name, the mix name and
      the word "disabled". A play that takes its mix from the table and is named by no row raises ValueError whose message holds the
      play name and the words "no mix". The six M0 plays (all Vanguard; s1_hold_choke, s2_concave, s2_spread_line, s2_mass_one_end, s4_bait, s4_do_not_chase)
      are named by no row and do NOT take a mix from the table: they build as before. Plays on other mixes build as before.
  Each row's definition line (the line holding `name` and the mix name as a string, written `"name": "M1"` or `name="M1"`) carries `DRAFT-mix-M1`
  (M2, M3, M4 likewise, and `DRAFT-mix-M3b` on M3b; `DRAFT-mix-M3` is not satisfied by the M3b line: each name is checked on its own row's line).
  The header (module docstring or a comment above the table) says exactly: M5 to M9 are added here after Westley's go on the roster analysis
  Unchanged and pinned elsewhere: every registered setup (test_placed_by_feature.py::test_registered_space_plays_keep_their_setups hash), the three
  controls' goldens (integration/test_cross_machine.py), test_plays_space.py::test_the_play_uses_its_roster_mix.
"""
import collections
import copy
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_plays_space import ROSTER_REACH, mix, mix_problems  # noqa: E402
from scripts.skilllab import plays_space  # noqa: E402

SOURCE = (ROOT / "scripts" / "skilllab" / "plays_space.py").read_text()
V, R, I, B, A = "Vanguard", "Raider", "Interceptor", "Bombard", "Bastion"

# the current numbers, read from plays_space.py on origin/push/labrev2-lab (c2d9bce8): the order of the pairs is the order of the groups
EXPECTED = {
    "M1": [(V, 8), (R, 8)],
    "M2": [(V, 8), (I, 8)],
    "M3": [(V, 8), (B, 8)],
    "M3b": [(V, 7), (R, 1), (B, 8)],
    "M4": [(V, 8), (A, 8)],
}
# which plays use which mix: test_plays_space.py PLAY_MIX, read off the plays' setup functions
USED_IN = {
    "M1": {"s3_layer_above", "s3_dark_striker", "s3_ping_then_commit", "s5_vulnerable_away"},
    "M2": {"s3_types_by_reach"},
    "M3": {"s2_screen"},
    "M3b": {"s3_over_the_choke"},
    "M4": {"s1_outrange"},
}
M0_PLAYS = {"s1_hold_choke", "s2_concave", "s2_spread_line", "s2_mass_one_end", "s4_bait", "s4_do_not_chase"}
HEADER = "M5 to M9 are added here after Westley's go on the roster analysis"


def rows():
    return {r["name"]: r for r in plays_space.MIXES}


def want(units):
    return collections.Counter({(t, ROSTER_REACH[t]): n for t, n in units.items()})


def key(name):
    s = plays_space.PLAYS[name].setup_fn()
    return repr((s.groups, s.unit_types, s.timeline, s.settings, s.terrain))


@pytest.fixture
def table(monkeypatch):
    """An editable deep copy of the table, already installed as plays_space.MIXES."""
    copied = copy.deepcopy(plays_space.MIXES)
    monkeypatch.setattr(plays_space, "MIXES", copied)
    return copied


# ---- the table itself -----------------------------------------------------------------------------------------------------------

def test_the_table_exists_with_exactly_the_five_rows_and_the_fields():
    assert isinstance(plays_space.MIXES, list)
    assert sorted(r["name"] for r in plays_space.MIXES) == sorted(EXPECTED)
    for r in plays_space.MIXES:
        assert set(r) == {"name", "units", "used_in", "enabled"}, r
        assert isinstance(r["units"], dict) and isinstance(r["used_in"], tuple) and r["enabled"] is True, r


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_the_current_mixes_are_byte_identical(name):
    """Types, counts and the ORDER of the types (the order is the order of the placed groups) as they stand on origin/push/labrev2-lab."""
    assert list(rows()[name]["units"].items()) == EXPECTED[name]


@pytest.mark.parametrize("name", sorted(USED_IN))
def test_each_mix_lists_exactly_the_plays_that_use_it(name):
    assert set(rows()[name]["used_in"]) == USED_IN[name] and len(rows()[name]["used_in"]) == len(USED_IN[name])


def test_no_play_is_listed_twice_and_every_listed_play_exists():
    listed = [p for r in plays_space.MIXES for p in r["used_in"]]
    assert len(listed) == len(set(listed)) and set(listed) <= set(plays_space.PLAYS)
    assert not set(listed) & M0_PLAYS                       # M0 (all Vanguard) is not a row: its plays stay out of the table


def test_the_old_module_level_mix_names_are_gone():
    """One table, not a table beside the old tuples (the numbers live in one place)."""
    assert not [n for n in ("M1", "M2", "M3", "M4", "M3B", "M3b") if hasattr(plays_space, n)]


# ---- the plays read the table ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(USED_IN))
def test_each_play_fields_its_mix_on_both_sides(name):
    """From the TABLE (not from the test's own PLAY_MIX): every play a row names fields that row's units on side 0 and, scaled, on side 1."""
    for play in sorted(rows()[name]["used_in"]):
        s = plays_space.PLAYS[play].setup_fn()
        assert mix(s, 0) == want(rows()[name]["units"]), play
        assert mix(s, 1) == want(rows()[name]["units"]), play


def edit_move_one(row):
    """Move one unit from the row's first type to its last: the total stays 16, a number changes (a data edit, no code)."""
    types = list(row["units"])
    row["units"][types[0]] -= 1
    row["units"][types[-1]] += 1


@pytest.mark.parametrize("name", sorted(USED_IN))
def test_editing_a_row_changes_the_composition_of_the_plays_that_use_it(table, name):
    before = {p: key(p) for p in USED_IN[name]}
    row = next(r for r in table if r["name"] == name)
    edit_move_one(row)
    assert list(row["units"].items()) != EXPECTED[name]            # the edit is a real one
    for play in sorted(USED_IN[name]):
        s = plays_space.PLAYS[play].setup_fn()
        assert key(play) != before[play], play
        assert mix(s, 0) == want(row["units"]) and mix(s, 1) == want(row["units"]), play
        for heads in (16, 48):
            assert mix_problems(plays_space.scan_build(play)(None, heads, False), heads) == [], (play, heads)


def test_control_editing_one_row_leaves_the_plays_of_the_other_rows_alone(table):
    others = sorted(set().union(*(USED_IN[n] for n in USED_IN if n != "M1")) | M0_PLAYS)
    before = {p: key(p) for p in others}
    edit_move_one(next(r for r in table if r["name"] == "M1"))
    assert {p: key(p) for p in others} == before


def test_control_the_unedited_copy_builds_what_the_table_builds():
    before = {p: key(p) for p in plays_space.PLAYS}
    saved = plays_space.MIXES
    try:
        plays_space.MIXES = copy.deepcopy(saved)
        assert {p: key(p) for p in plays_space.PLAYS} == before
    finally:
        plays_space.MIXES = saved


def test_a_new_row_added_to_the_table_changes_a_plays_composition_without_a_code_edit(table):
    """Data-driven: a new row MX takes s3_layer_above from M1 (a play is on one row); the new row's numbers are what the play fields, on both sides."""
    next(r for r in table if r["name"] == "M1")["used_in"] = tuple(sorted(USED_IN["M1"] - {"s3_layer_above"}))
    table.append({"name": "MX", "units": {V: 10, R: 6}, "used_in": ("s3_layer_above",), "enabled": True})
    s = plays_space.PLAYS["s3_layer_above"].setup_fn()
    assert mix(s, 0) == want({V: 10, R: 6}) and mix(s, 1) == want({V: 10, R: 6})
    assert mix_problems(plays_space.scan_build("s3_layer_above")(None, 48, False), 48) == []
    # the plays still on M1 keep M1
    assert mix(plays_space.PLAYS["s3_dark_striker"].setup_fn(), 0) == want(dict(EXPECTED["M1"]))


# ---- enabled=False ---------------------------------------------------------------------------------------------------------------

def test_a_disabled_mix_makes_its_plays_raise_a_clear_error(table):
    next(r for r in table if r["name"] == "M2")["enabled"] = False
    with pytest.raises(ValueError) as e:
        plays_space.PLAYS["s3_types_by_reach"].setup_fn()
    assert all(w in str(e.value) for w in ("s3_types_by_reach", "M2", "disabled")), str(e.value)
    with pytest.raises(ValueError) as e2:
        plays_space.scan_build("s3_types_by_reach")(None, 16, False)
    assert all(w in str(e2.value) for w in ("s3_types_by_reach", "M2", "disabled")), str(e2.value)


def test_a_disabled_mix_leaves_every_other_play_as_it_was(table):
    others = sorted(set(plays_space.PLAYS) - USED_IN["M3b"])
    before = {p: key(p) for p in others}
    next(r for r in table if r["name"] == "M3b")["enabled"] = False
    assert {p: key(p) for p in others} == before
    with pytest.raises(ValueError):
        plays_space.PLAYS["s3_over_the_choke"].setup_fn()


def test_control_the_same_play_builds_when_its_mix_is_enabled(table):
    assert next(r for r in table if r["name"] == "M2")["enabled"] is True
    plays_space.PLAYS["s3_types_by_reach"].setup_fn()                          # no raise


def test_a_play_named_by_no_row_raises_a_clear_error(table):
    table[:] = [r for r in table if r["name"] != "M2"]
    with pytest.raises(ValueError) as e:
        plays_space.PLAYS["s3_types_by_reach"].setup_fn()
    assert "s3_types_by_reach" in str(e.value) and "no mix" in str(e.value), str(e.value)


def test_two_enabled_rows_naming_one_play_raise_a_clear_error(table):
    next(r for r in table if r["name"] == "M2")["used_in"] = ("s3_types_by_reach", "s3_layer_above")   # s3_layer_above is already on M1
    with pytest.raises(ValueError) as e:
        plays_space.PLAYS["s3_layer_above"].setup_fn()
    assert "s3_layer_above" in str(e.value) and "two mixes" in str(e.value), str(e.value)
    with pytest.raises(ValueError) as e2:
        plays_space.scan_build("s3_layer_above")(None, 16, False)
    assert "two mixes" in str(e2.value), str(e2.value)


def test_control_the_m0_plays_build_with_the_table_present_and_in_no_row():
    for p in sorted(M0_PLAYS):
        plays_space.PLAYS[p].setup_fn()                                       # no raise: they take no mix from the table


def test_the_table_is_defined_above_the_plays():
    """PLAYS builds its plays at import time, so MIXES has to be assigned first (the first top-level `PLAYS = {` is line 202 today)."""
    mixes = re.search(r"^MIXES\b[^\n=]*=", SOURCE, re.M)
    plays = re.search(r"^PLAYS\b[^\n=]*=", SOURCE, re.M)
    assert mixes and plays and mixes.start() < plays.start()


# ---- the marks and the header (grep of the source, as test_drift_fix_drafts.py does) --------------------------------------------

def row_lines(name):
    pat = re.compile(r"""(["']name["']\s*:|\bname\s*=)\s*["']%s["']""" % re.escape(name))
    return [ln for ln in SOURCE.splitlines() if pat.search(ln)]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_each_row_definition_line_carries_its_draft_name(name):
    lines = row_lines(name)
    assert len(lines) == 1, "%s: %d lines hold the row's name (want exactly one)" % (name, len(lines))
    assert re.search(r"DRAFT-mix-%s(?![\w-])" % re.escape(name), lines[0]), lines[0]


def test_control_the_row_grep_tells_m3_from_m3b():
    """The grep keys on the whole name string: a row line for M3b is not a line for M3, and DRAFT-mix-M3 is not satisfied by DRAFT-mix-M3b."""
    m3b = '{"name": "M3b", "units": {}, "used_in": (), "enabled": True},   # DRAFT-mix-M3b'
    assert not re.search(r"""(["']name["']\s*:|\bname\s*=)\s*["']M3["']""", m3b)
    assert not re.search(r"DRAFT-mix-M3(?![\w-])", m3b)
    assert re.search(r"DRAFT-mix-M3b(?![\w-])", m3b)


def test_the_header_says_m5_to_m9_wait_for_westleys_go():
    assert HEADER in " ".join(SOURCE.split()), "plays_space.py does not say: " + HEADER
