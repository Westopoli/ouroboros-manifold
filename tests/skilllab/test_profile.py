# spec: docs/northstar/research/layer_dynamics/README.md section 4 (conditions C3 to C6, the 32-combination skill profile); every pass mark is Westley's and an input
# LAB-REV2-L2 inventory (Q-LAB-03): KEPT unchanged. 'undecided' means a scan whose break-even is None (no result), not the retired outcome `decided`.
"""profile.py (subsets, advantage, skill_profile, validate) and conditions C3, C4, C5, C6 over hand-built maps.
Every statistic is the harness writer's unconfirmed definition; every Verdict.detail says so.
Threshold values are placeholders for the tests only."""
import itertools
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.conditions import check_c3, check_c4, check_c5, check_c6  # noqa: E402
from scripts.skilllab.profile import PROFILE_SKILLS, advantage, beats, skill_profile, subsets, validate  # noqa: E402
from fakes_scans import EMPTY, FULL, S, by_size, make_map, thresholds  # noqa: E402

# draft, not confirmed by Westley; placeholder for the test
DRAFT_UNCONFIRMED_C3_STACK_GAIN = 1.0
DRAFT_UNCONFIRMED_C4_MAX_SHARE = 0.25
DRAFT_UNCONFIRMED_C5_MIN_LOSS = 0.2
DRAFT_UNCONFIRMED_C6_RETURN_SHARE = 0.5
DRAFT_UNCONFIRMED_MAP_SHARE = 0.5

C4_BASE = by_size(10, 20, 30, 40, 50, 50)    # single advantage 10, full advantage 40: ratio 0.25
C5_BASE = by_size(10, 20, 30, 40, 40, 50)    # full 50, each full-minus-one 40: loss 0.2


def _prefix(v):
    assert v.detail.startswith("unconfirmed definition:")


# ---------- profile ----------

def test_subsets_32_ordered_by_size_then_names():
    """32 subsets, empty first, full last, ordered by size then sorted names."""
    got = subsets()
    assert len(got) == 32 and got[0] == frozenset() and got[-1] == frozenset(PROFILE_SKILLS)
    assert got == [frozenset(c) for r in range(6) for c in itertools.combinations(PROFILE_SKILLS, r)]
    assert subsets() == got


def test_beats_and_advantage():
    """beats reads scan.beats; advantage is whole units over the naive control, None if either is undecided."""
    pm = make_map(over={S("S1"): 27, S("S2"): None})
    assert beats(pm.scans[S("S1")]) == 27 and beats(pm.scans[S("S2")]) is None
    assert advantage(pm, S("S1")) == 17 and advantage(pm, EMPTY) == 0
    assert advantage(pm, S("S2")) is None
    assert advantage(make_map(over={EMPTY: None}), S("S1")) is None


def test_skill_profile_rows_means_and_nones():
    """32 rows in subsets() order; undecided maps drop out of that row; no decided map gives None."""
    m1 = make_map("a", over={S("S1"): 20})                 # advantage of S1: 10
    m2 = make_map("b", over={S("S1"): 35, S("S2"): None})  # advantage of S1: 25, S2 undecided
    rows = skill_profile([m1, m2])
    assert [r["skills"] for r in rows] == [tuple(sorted(s)) for s in subsets()]
    by = {r["skills"]: r for r in rows}
    assert by[("S1",)] == {"skills": ("S1",), "maps": 2, "mean_advantage": 17.5}
    assert by[("S2",)]["maps"] == 1 and by[("S2",)]["mean_advantage"] == 10.0
    assert by[()]["maps"] == 2 and by[()]["mean_advantage"] == 0.0
    none_ctrl = skill_profile([make_map(over={EMPTY: None})])
    assert all(r["maps"] == 0 and r["mean_advantage"] is None for r in none_ctrl)
    assert all(r["maps"] == 0 and r["mean_advantage"] is None for r in skill_profile([]))


def test_validate_accepts_complete_map_and_rejects_each_defect():
    """validate returns None for a good map and raises ValueError for each listed defect."""
    assert validate(make_map(counters={"S1": 15})) is None
    pm = make_map()
    del pm.scans[S("S1", "S2")]
    with pytest.raises(ValueError):
        validate(pm)
    with pytest.raises(ValueError):
        validate(make_map(size=0))
    with pytest.raises(ValueError):
        validate(make_map(offers=("S1", "S9")))
    with pytest.raises(ValueError):
        validate(make_map(offers=("S1",), counters={"S2": 15}))


# ---------- C3 ----------

def _t3(**o):
    return thresholds(c3_stack_gain=DRAFT_UNCONFIRMED_C3_STACK_GAIN, c8_map_share=1.0, **o)


def test_c3_holds_exactly_at_the_gain_and_fails_past_it():
    """Doubling at every step holds at gain 1.0 exactly; a tiny bit above the gain fails; full 319 < 2*160 fails."""
    v = check_c3([make_map()], _t3())
    assert v.code == "C3" and v.holds is True and v.value == 1.0 and v.threshold == 1.0
    _prefix(v)
    assert check_c3([make_map()], _t3(**{})).holds is True
    assert check_c3([make_map()], thresholds(c3_stack_gain=1.01, c8_map_share=1.0)).holds is False
    assert check_c3([make_map(over={FULL: 319})], _t3()).holds is False


def test_c3_undecided_counts_against_and_is_reported():
    """A None beats makes the map not hold, and the detail mentions undecided maps."""
    v = check_c3([make_map(over={S("S1", "S2"): None})], _t3())
    assert v.holds is False and v.value == 0.0 and "undecided" in v.detail.lower()


def test_c3_share_uses_c8_map_share():
    """Two of four maps hold: share 0.5, holds at mark 0.5, fails at 0.75; C6's share mark is irrelevant."""
    maps = [make_map("a"), make_map("b"), make_map("c", over={FULL: 1}), make_map("d", over={FULL: 1})]
    v = check_c3(maps, thresholds(c3_stack_gain=1.0, c8_map_share=0.5, c6_map_share=1.0))
    assert v.holds is True and v.value == 0.5 and v.threshold == 0.5
    assert check_c3(maps, thresholds(c3_stack_gain=1.0, c8_map_share=0.75)).holds is False


# ---------- C4 ----------

def _t4(**o):
    return thresholds(c4_max_share=DRAFT_UNCONFIRMED_C4_MAX_SHARE, c8_map_share=1.0, **o)


def test_c4_boundary_and_threshold_flip():
    """Each single skill gives 10 of 40: ratio 0.25 holds at mark 0.25; one extra unit on S1 (0.275) fails."""
    v = check_c4([make_map(base=C4_BASE)], _t4())
    assert v.code == "C4" and v.holds is True and v.value == 1.0 and v.threshold == 1.0
    _prefix(v)
    assert check_c4([make_map(base=C4_BASE, over={S("S1"): 21})], _t4()).holds is False
    assert check_c4([make_map(base=C4_BASE)], thresholds(c4_max_share=0.24, c8_map_share=1.0)).holds is False


def test_c4_no_full_advantage_and_undecided_count_against():
    """Full advantage zero, negative or undecided: not held; a None single is undecided and not held."""
    v = check_c4([make_map(base=C4_BASE, over={FULL: 10})], _t4())
    assert v.holds is False and "no full-set advantage" in v.detail
    assert check_c4([make_map(base=C4_BASE, over={FULL: 5})], _t4()).holds is False
    assert check_c4([make_map(base=C4_BASE, over={FULL: None})], _t4()).holds is False
    v = check_c4([make_map(base=C4_BASE, over={S("S3"): None})], _t4())
    assert v.holds is False and "undecided" in v.detail.lower()


def test_c4_share_arithmetic_uses_c8_map_share():
    """One of three maps holds: share 1/3 against mark 1/3 holds, against 0.4 fails."""
    maps = [make_map("a", base=C4_BASE), make_map("b", base=C4_BASE, over={S("S1"): 21}),
            make_map("c", base=C4_BASE, over={FULL: 10})]
    v = check_c4(maps, thresholds(c4_max_share=0.25, c8_map_share=1 / 3))
    assert v.holds is True and v.value == 1 / 3
    assert check_c4(maps, thresholds(c4_max_share=0.25, c8_map_share=0.4)).holds is False


# ---------- C5 ----------

def _t5(**o):
    return thresholds(c5_min_loss=DRAFT_UNCONFIRMED_C5_MIN_LOSS, c8_map_share=1.0, **o)


def test_c5_boundary_and_threshold_flip():
    """Removing any skill costs 10 of 50 = 0.2: holds at mark 0.2; one removal costing 9 fails; mark 0.21 fails."""
    v = check_c5([make_map(base=C5_BASE)], _t5())
    assert v.code == "C5" and v.holds is True and v.value == 1.0
    _prefix(v)
    assert check_c5([make_map(base=C5_BASE, over={FULL - S("S2"): 41})], _t5()).holds is False
    assert check_c5([make_map(base=C5_BASE)], thresholds(c5_min_loss=0.21, c8_map_share=1.0)).holds is False


def test_c5_zero_or_undecided_full_and_undecided_removal_count_against():
    """beats(full) None or 0 does not hold; an undecided removal does not hold."""
    assert check_c5([make_map(base=C5_BASE, over={FULL: 0})], _t5()).holds is False
    assert check_c5([make_map(base=C5_BASE, over={FULL: None})], _t5()).holds is False
    v = check_c5([make_map(base=C5_BASE, over={FULL - S("S1"): None})], _t5())
    assert v.holds is False and "undecided" in v.detail.lower()


def test_c5_share_arithmetic():
    """Two of four maps hold: share 0.5; mark 0.5 holds, mark 0.6 fails."""
    maps = [make_map("a", base=C5_BASE), make_map("b", base=C5_BASE),
            make_map("c", base=C5_BASE, over={FULL: 41}), make_map("d", base=C5_BASE, over={FULL: None})]
    v = check_c5(maps, thresholds(c5_min_loss=0.2, c8_map_share=0.5))
    assert v.holds is True and v.value == 0.5
    assert check_c5(maps, thresholds(c5_min_loss=0.2, c8_map_share=0.6)).holds is False


# ---------- C6 ----------

def _t6(**o):
    return thresholds(c6_return_share=DRAFT_UNCONFIRMED_C6_RETURN_SHARE, c6_map_share=1.0, c8_map_share=0.0, **o)


def _m6(map_id="m", counter=15, **kw):
    return make_map(map_id, offers=("S1",), counters={"S1": counter}, **kw)


def test_c6_boundary_and_threshold_flip():
    """S1 gains 10; counter at 15 returns 5 of 10 = 0.5: holds at mark 0.5, counter 16 (0.4) fails, mark 0.6 fails."""
    v = check_c6([_m6()], _t6())
    assert v.code == "C6" and v.holds is True and v.value == 1.0 and v.threshold == 1.0
    _prefix(v)
    assert check_c6([_m6(counter=16)], _t6()).holds is False
    assert check_c6([_m6()], thresholds(c6_return_share=0.6, c6_map_share=1.0)).holds is False


def test_c6_missing_counter_counts_against():
    """An undecided or absent counter scan does not hold."""
    assert check_c6([_m6(counter=None)], _t6()).holds is False
    absent = make_map(offers=("S1",), counters={})
    v = check_c6([absent], _t6())
    assert v.holds is False and "undecided" in v.detail.lower()


def test_c6_not_applicable_maps_are_excluded():
    """No offered skill with a positive advantage: not applicable. Zero applicable maps gives None."""
    flat = by_size(10, 10, 10, 10, 10, 10)
    assert check_c6([_m6(base=flat)], _t6()).holds is None
    assert check_c6([_m6(over={S("S1"): None})], _t6()).holds is None
    maps = [_m6("a"), _m6("b", counter=16), _m6("c", base=flat)]
    v = check_c6(maps, thresholds(c6_return_share=0.5, c6_map_share=0.5, c8_map_share=1.0))
    assert v.holds is True and v.value == 0.5 and v.threshold == 0.5
    assert check_c6(maps, thresholds(c6_return_share=0.5, c6_map_share=0.51, c8_map_share=0.0)).holds is False


def test_c6_every_applicable_skill_must_hold_on_a_map():
    """A map with two offered skills holds only when both return enough."""
    ok = make_map(offers=("S1", "S2"), counters={"S1": 15, "S2": 15})
    bad = make_map(offers=("S1", "S2"), counters={"S1": 15, "S2": 16})
    assert check_c6([ok], _t6()).holds is True
    assert check_c6([bad], _t6()).holds is False
