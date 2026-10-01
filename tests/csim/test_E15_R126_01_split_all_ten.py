"""R-126-01: the owner split per mission archetype, pinned for all ten archetypes.

The bible splits {player, enemy, neutral} by archetype (E-15 R-126-01). The expected
counts here are computed from the rule's percentages with exact integer arithmetic,
never by calling the code under test, so a wrong row in the code's split table fails.
Rounding per the rule's implementation note: player = round-half-up(total * p%),
enemy = round-half-up(total * e%), enemy trimmed if the sum exceeds total, neutral the
remainder, player at least 1 (taken from neutral first, then enemy).
Driven through the public om_structure_assign_owners (the function om_mission_setup calls).
"""
import ctypes

import pytest

# archetype index (mission archetype ids, csrc/mission.c) -> (player%, enemy%, neutral%)
RULE_SPLIT = {
    0: ("defensive stand", (50, 25, 25)),
    1: ("siege breaking", (33, 33, 34)),
    2: ("reconquest", (25, 50, 25)),
    3: ("assault", (25, 50, 25)),
    4: ("suppression", (40, 30, 30)),
    5: ("multi-front defense", (40, 35, 25)),
    6: ("interception", (33, 34, 33)),
    7: ("evacuation", (50, 25, 25)),
    8: ("containment", (33, 34, 33)),
    9: ("counterinsurgency", (40, 30, 30)),
}
TOTALS = (4, 6, 8, 10, 100)  # 100 resolves every percentage exactly (not a placed count)


def _half_up(total, pct):
    return (total * pct * 2 + 100) // 200


def expected(split, total):
    pp, ep, _ = split
    p = _half_up(total, pp)
    e = _half_up(total, ep)
    if p + e > total:
        e = total - p
    n = total - p - e
    if p < 1 and total >= 1:
        p = 1
        if n >= 1:
            n -= 1
        elif e >= 1:
            e -= 1
    return p, e, n


def code_split(lib, archetype, total):
    p, e, n = ctypes.c_uint32(), ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_structure_assign_owners(archetype, total, ctypes.byref(p), ctypes.byref(e), ctypes.byref(n))
    return p.value, e.value, n.value


def test_oracle_arithmetic_pinned():
    """The oracle itself: hand-computed rows so a bug in expected() cannot hide."""
    assert expected((50, 25, 25), 8) == (4, 2, 2)
    assert expected((33, 33, 34), 10) == (3, 3, 4)
    assert expected((25, 50, 25), 4) == (1, 2, 1)
    assert expected((40, 35, 25), 10) == (4, 4, 2)
    assert expected((33, 34, 33), 6) == (2, 2, 2)


@pytest.mark.parametrize("total", TOTALS)
@pytest.mark.parametrize("archetype", sorted(RULE_SPLIT))
def test_R_126_01_split_matches_rule_for_every_archetype(lib, archetype, total):
    name, split = RULE_SPLIT[archetype]
    got = code_split(lib, archetype, total)
    want = expected(split, total)
    assert got == want, (
        f"R-126-01: {name} at {total} structures: code (player, enemy, neutral) {got}, "
        f"rule {split} gives {want}"
    )
    assert sum(got) == total and got[0] >= 1


def test_control_altered_row_disagrees_with_code(lib):
    """Positive control: the oracle with siege altered to 34/33/33 must disagree with the code
    at some pinned total, proving the comparison can detect a wrong table row."""
    altered = dict(RULE_SPLIT)
    altered[1] = ("siege breaking (altered)", (34, 33, 33))
    disagreements = [
        (a, t)
        for a, (_, split) in altered.items()
        for t in TOTALS
        if code_split(lib, a, t) != expected(split, t)
    ]
    assert disagreements, "altered siege row 34/33/33 produced no disagreement at totals 4/6/8/10/100"
    assert all(a == 1 for a, _ in disagreements)
