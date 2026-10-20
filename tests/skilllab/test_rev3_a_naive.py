# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T4; defect D4); ledger FINDING-lab-d4; piece LAB-REV3-A
"""LAB-REV3-A, T4 (R8, D4): the `naive_attacker` baseline fields the play's own mix. `scenes._groups_and_timeline` builds the naive
branch as 16 Vanguards against Vanguards whatever mix the play uses, so C1 ("against a naive attacker") compared an M1 or M2 play with
an M0 fight (analysis B, C3: on layout 81 `naive_attacker side0 {Vanguard: 16} side1 {Vanguard: 16}` against a play of 8 Raiders and
8 Vanguards). Fast half, no fight: the baseline is read from the build the sweep uses, `sweep.default_builds(play, "naive_attacker",
features)(16, False)`, against `sweep.default_builds(play, "play", features)(16, False)`, on the first smoke layout (the groups are
built whether or not the layout fits; only the unit names and counts are read).

BUILDER CONTRACT (behaviour only; no new name is pinned):
  - SIDE 0 of the naive_attacker build holds, per unit name, the same total count as side 0 of the play's build at the same headcount.
  - SIDE 1 of the naive_attacker build holds the same roster as side 1 of the play's build at the same headcount (rev 2 ruling 2,
    the same mix on both sides; the finding's own line lists both sides as Vanguard). This second clause is the test writer's reading
    of "the naive attacker fields the play's mix": it is a separate test, so the Architect can drop it alone.
  - A play that is all Vanguards keeps its baseline as it is (the positive control)."""
import collections
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, sweep  # noqa: E402

PLAYS = sorted(plays_space.PLAYS)
HEADS = 16


def roster(setup, side):
    out = collections.Counter()
    for g in setup.groups:
        if g.side == side:
            out[g.unit] += g.count
    return dict(out)


def builds(play):
    features = sweep.smoke_layouts()[sweep.SMOKE_LAYOUTS[0]]
    return (sweep.default_builds(play, "play", features)(HEADS, False),
            sweep.default_builds(play, "naive_attacker", features)(HEADS, False))


@pytest.mark.parametrize("play", [p for p in PLAYS if set(roster(plays_space.PLAYS[p].setup_fn(), 0)) == {"Vanguard"}])
def test_positive_control_an_all_vanguard_play_already_has_the_same_naive_attacker(play):
    """Green on the lab tip: the detector below does not fire where the roster already is the play's."""
    own, naive = builds(play)
    assert roster(naive, 0) == roster(own, 0) == {"Vanguard": 16}


@pytest.mark.parametrize("play", PLAYS)
def test_t4_the_naive_attacker_side_0_is_the_plays_roster(play):
    """T4 (D4): side 0 of the naive attacker is the play's side 0 roster. Red today for the eight plays with a mix: {'Vanguard': 16}."""
    own, naive = builds(play)
    assert roster(naive, 0) == roster(own, 0)


@pytest.mark.parametrize("play", PLAYS)
def test_t4_the_naive_attackers_enemy_is_the_plays_enemy_roster(play):
    """T4 (D4, ruling 2: the same mix both sides): side 1 of the naive_attacker build is the roster side 1 has in the play."""
    own, naive = builds(play)
    assert roster(naive, 1) == roster(own, 1)
