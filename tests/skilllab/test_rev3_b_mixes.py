# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1; defects D2, D9; test T11 data side); docs/northstar/research/layer_dynamics/audits/mixes_2026-10-19/README.md (the arbitration Westley accepted 2026-10-19); ledger FINDING-lab-d2, FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, R1 (D2): the mixes M5 to M9 as rows of the MIXES table of plays_space.py (columns name, units, used_in, enabled). Fast half.

THE ROWS (the arbitration of 2026-10-19, accepted by Westley: "I agree with all of your arbitration logic"):
  M5 8 Raider + 8 Bombard   M6 8 Interceptor + 8 Bombard   M7 8 Raider + 8 Interceptor   M8 8 Bombard + 8 Bastion   M9 12 Vanguard + 4 Warden
The same mix on both sides (rev 2 ruling 2). All six types as one robustness mix is BATCH TWO, not this piece: no row, no test here.

BUILDER CONTRACT (the same shape as the five rows M1 to M4 and M3b, test_plays_space_mixes.py):
  - `plays_space.MIXES` holds five more rows with exactly the keys name, units, used_in, enabled: units a {type: count} dict (the
    order of the keys is the order of the side-1 groups, not pinned here), used_in a tuple of names of plays that exist in
    `plays_space.PLAYS`, enabled a bool. The row's definition line (the line holding `"name": "M5"`) carries `DRAFT-mix-M5`, likewise M6..M9.
  - A play is on one row at most (a name listed in two rows is a "two mixes" error of the existing builder). The plays of a row field the
    row's units on side 0 and, scaled by heads / 16, on side 1, nothing added and nothing missing (a data edit changes the play).
  - ENABLED and SWEPT agree. An enabled row names at least one play that some family of `sweep.PLAYS_BY_FAMILY` runs (a mix no family
    runs covers nothing, plan T1); a disabled row (rejected by the 30-fight pre-check of test_rev3_b_mirror.py) names none that is swept,
    because a play of a disabled mix cannot be built.
  - The header above the table no longer says that M5 to M9 wait for Westley's go (stale-doc tripwire: the rows are in). Westley accepted
    the arbitration; the go to RUN batch one with the known-gaps header is still his and is not this comment.
  - M9 holds exactly 4 Wardens and no enabled row holds more than 4 per 16 (D9's interim lab cap, retiring with FU-warden-no-stack;
    the refusal itself is test_rev3_b_mirror.py).

Red today: the rows do not exist. The guard tests at the end are green on the lab tip."""
import copy
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import plays_space, sweep  # noqa: E402

SOURCE = (ROOT / "scripts" / "skilllab" / "plays_space.py").read_text()
NEW = {
    "M5": {"Raider": 8, "Bombard": 8},
    "M6": {"Interceptor": 8, "Bombard": 8},
    "M7": {"Raider": 8, "Interceptor": 8},
    "M8": {"Bombard": 8, "Bastion": 8},
    "M9": {"Vanguard": 12, "Warden": 4},
}
OLD = ("M1", "M2", "M3", "M3b", "M4")
OLD_HEADER = "M5 to M9 are added here after Westley's go on the roster analysis"
WARDEN_CAP = 4


def rows():
    return {r["name"]: r for r in plays_space.MIXES}


def row(name):
    assert name in rows(), "MIXES has no row %s (rows: %s)" % (name, sorted(rows()))
    return rows()[name]


def base_of(setup, g):
    entry = setup.unit_types.get(g.unit)
    return entry.get("base", g.unit) if entry else g.unit


def roster(setup, side):
    out = {}
    for g in setup.groups:
        if g.side == side:
            out[base_of(setup, g)] = out.get(base_of(setup, g), 0) + g.count
    return out


def scaled_ok(units, got, heads):
    """`got` is `units` scaled to `heads`: exact where heads / 16 * n is whole, within one otherwise; same types."""
    if set(got) != set(units) or sum(got.values()) != heads:
        return False
    return all(abs(got[t] - n * heads / 16) <= (0 if n * heads / 16 == int(n * heads / 16) else 1) for t, n in units.items())


def swept():
    return {p for plays in sweep.PLAYS_BY_FAMILY.values() for p in plays}


@pytest.fixture
def table(monkeypatch):
    copied = copy.deepcopy(plays_space.MIXES)
    monkeypatch.setattr(plays_space, "MIXES", copied)
    return copied


# ---- the rows ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_the_row_exists_with_the_arbitrated_units(name):
    """R1. Red today: no row (the table holds M1, M2, M3, M3b, M4)."""
    assert dict(row(name)["units"]) == NEW[name]


@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_the_row_has_exactly_the_four_columns_with_the_right_types(name):
    r = row(name)
    assert set(r) == {"name", "units", "used_in", "enabled"}, r
    assert isinstance(r["units"], dict) and isinstance(r["used_in"], tuple) and isinstance(r["enabled"], bool), r
    assert sum(r["units"].values()) == 16


def test_r1_the_table_holds_the_old_rows_and_the_new_ones_and_nothing_else():
    assert sorted(rows()) == sorted(OLD + tuple(NEW))


@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_the_row_names_existing_plays_and_no_play_is_on_two_rows(name):
    r = row(name)
    assert r["used_in"], "%s names no play: a mix nobody plays covers nothing" % name
    assert set(r["used_in"]) <= set(plays_space.PLAYS), sorted(set(r["used_in"]) - set(plays_space.PLAYS))
    listed = [p for x in plays_space.MIXES for p in x["used_in"]]
    assert len(listed) == len(set(listed)), "a play is on two rows"


@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_the_rows_definition_line_carries_its_draft_name(name):
    pat = re.compile(r"""(["']name["']\s*:|\bname\s*=)\s*["']%s["']""" % re.escape(name))
    lines = [ln for ln in SOURCE.splitlines() if pat.search(ln)]
    assert len(lines) == 1, "%s: %d lines hold the row's name (want exactly one)" % (name, len(lines))
    assert re.search(r"DRAFT-mix-%s(?![\w-])" % re.escape(name), lines[0]), lines[0]


def test_r1_the_header_no_longer_says_m5_to_m9_wait_for_westleys_go():
    """Stale-doc tripwire: the rows are in. test_plays_space_mixes.py::test_the_header_says_m5_to_m9_wait_for_westleys_go pins the old
    sentence and is retired by the ruler under a TD row (assumption changed: the rows are added)."""
    assert OLD_HEADER not in " ".join(SOURCE.split())


# ---- the plays field the row ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_each_play_of_the_row_fields_the_units_on_both_sides(name):
    plays = row(name)["used_in"]
    assert plays
    if not row(name)["enabled"]:         # rejected by the pre-check: its plays refuse to build, which is the table's word
        for play in plays:
            with pytest.raises(ValueError, match="disabled"):
                plays_space.PLAYS[play].setup_fn()
        return
    for play in plays:
        s = plays_space.PLAYS[play].setup_fn()
        assert roster(s, 0) == NEW[name], (play, roster(s, 0))
        assert roster(s, 1) == NEW[name], (play, roster(s, 1))
        for heads in (8, 13, 48):
            assert scaled_ok(NEW[name], roster(plays_space.scan_build(play)(None, heads, False), 1), heads), (play, heads)


@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_editing_the_row_changes_the_plays_that_use_it(table, name):
    """Data-driven (the mechanism of test_plays_space_mixes.py, on the new rows): move one unit from the row's first type to its last."""
    r = next(x for x in table if x["name"] == name)
    plays = r["used_in"]
    assert plays
    if not r["enabled"]:
        return                           # nothing to build; the disabled word is checked by the test above
    before = {p: repr(plays_space.PLAYS[p].setup_fn().groups) for p in plays}
    types = list(r["units"])
    r["units"][types[0]] -= 1
    r["units"][types[-1]] += 1
    for p in plays:
        s = plays_space.PLAYS[p].setup_fn()
        assert repr(s.groups) != before[p], p
        assert roster(s, 0) == r["units"] and roster(s, 1) == r["units"], p


# ---- enabled and swept agree ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_an_enabled_row_is_swept_and_a_disabled_row_is_not(name):
    r = row(name)
    in_sweep = set(r["used_in"]) & swept()
    if r["enabled"]:
        assert in_sweep, "%s is enabled and none of %s is in any family of PLAYS_BY_FAMILY" % (name, list(r["used_in"]))
    else:
        assert not in_sweep, "%s is disabled and %s is swept: the play cannot be built" % (name, sorted(in_sweep))


@pytest.mark.parametrize("name", sorted(NEW))
def test_r1_the_swept_plays_of_an_enabled_row_build(name):
    r = row(name)
    for p in sorted(set(r["used_in"]) & swept()):
        plays_space.PLAYS[p].setup_fn()      # no ValueError "disabled" / "no mix" / "two mixes"


# ---- D9 data side -----------------------------------------------------------------------------------------------------------------

def test_t11_m9_holds_exactly_four_wardens_and_twelve_vanguards():
    """The arbitration: M9 12 Vanguard + 4 Warden, the most Wardens D9's interim lab cap allows in 16. Red today: no row M9."""
    assert dict(row("M9")["units"]) == {"Vanguard": 12, "Warden": 4}


def test_t1_m9_is_enabled():
    """Architect ruling 2026-10-20 (plan R1): M9's one cap in 30 (seed 6, unswapped) is the Warden stall of FINDING-lab-d9 (fix
    FU-warden-no-stack), a known cap that is listed, not fatal: M9 stays enabled and T1 goes green on it. test_rev3_b_mirror.py holds the
    pre-check side (ok True, reason known_cap:FINDING-lab-d9). Red today: no row M9."""
    assert row("M9")["enabled"] is True


def test_t11_no_enabled_row_holds_more_than_4_wardens_per_16():
    """Guard (green on the lab tip): the interim lab cap of FINDING-lab-d9, retiring with FU-warden-no-stack, holds in the table itself."""
    bad = [r["name"] for r in plays_space.MIXES if r["enabled"] and r["units"].get("Warden", 0) * 16 > WARDEN_CAP * sum(r["units"].values())]
    assert bad == [], bad


def test_control_the_warden_count_check_sees_a_row_of_eight():
    row8 = {"name": "MX", "units": {"Vanguard": 8, "Warden": 8}, "used_in": (), "enabled": True}
    assert row8["units"].get("Warden", 0) * 16 > WARDEN_CAP * sum(row8["units"].values())
    m9 = {"Vanguard": 12, "Warden": 4}
    assert not m9.get("Warden", 0) * 16 > WARDEN_CAP * sum(m9.values())


# ---- guards: the old rows are as they were (green on the lab tip) -----------------------------------------------------------------

@pytest.mark.parametrize("name", OLD)
def test_guard_the_old_rows_keep_their_units(name):
    expected = {"M1": {"Vanguard": 8, "Raider": 8}, "M2": {"Vanguard": 8, "Interceptor": 8}, "M3": {"Vanguard": 8, "Bombard": 8},
                "M3b": {"Vanguard": 7, "Raider": 1, "Bombard": 8}, "M4": {"Vanguard": 8, "Bastion": 8}}
    assert dict(row(name)["units"]) == expected[name]
