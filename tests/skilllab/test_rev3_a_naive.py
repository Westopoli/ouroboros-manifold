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
  - Side 1 scales with the headcount like the play's own side 1 (heads/16 of the mix, the play's own rounding): the roster tests run at
    heads 8, 16 and 48 (W7 of the audit); side 0 stays the 16-unit mix at every headcount.
  - SHAPE (W6 of the audit; green on the lab tip, they fail a fix that returns the skilled play wholesale): the naive attacker's
    timeline is empty; every side-0 group has order attack_move; side 1 stays the post holder (order guard); each side stands on the layers
    the play gives it (LAB-REV3-B narrowed "layer 0" to this: for a layer-0 play it is layer 0). (The play's own side 0 may be on guard, on layer 1 or 2, or carry steps: those must not leak in.)
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
HEADS = (8, 16, 48)


def roster(setup, side):
    out = collections.Counter()
    for g in setup.groups:
        if g.side == side:
            out[g.unit] += g.count
    return dict(out)


def builds(play, heads=16):
    features = sweep.smoke_layouts()[sweep.SMOKE_LAYOUTS[0]]
    return (sweep.default_builds(play, "play", features)(heads, False),
            sweep.default_builds(play, "naive_attacker", features)(heads, False))


@pytest.mark.parametrize("play", [p for p in PLAYS if set(roster(plays_space.PLAYS[p].setup_fn(), 0)) == {"Vanguard"}])
def test_positive_control_an_all_vanguard_play_already_has_the_same_naive_attacker(play):
    """Green on the lab tip: the detector below does not fire where the roster already is the play's."""
    own, naive = builds(play)
    assert roster(naive, 0) == roster(own, 0) == {"Vanguard": 16}


@pytest.mark.parametrize("play", PLAYS)
@pytest.mark.parametrize("heads", HEADS)
def test_t4_the_naive_attacker_side_0_is_the_plays_roster(play, heads):
    """T4 (D4): side 0 of the naive attacker is the play's side 0 roster at every headcount (side 0 does not scale). Red today for the
    eight plays with a mix: {'Vanguard': 16}."""
    own, naive = builds(play, heads)
    assert roster(naive, 0) == roster(own, 0)


@pytest.mark.parametrize("play", PLAYS)
@pytest.mark.parametrize("heads", HEADS)
def test_t4_the_naive_attackers_enemy_is_the_plays_enemy_roster(play, heads):
    """T4 (D4, ruling 2: the same mix both sides; W7: it scales with heads, at 8 and 48 as at 16): side 1 of the naive_attacker build is
    the roster side 1 has in the play at that headcount."""
    own, naive = builds(play, heads)
    assert roster(naive, 1) == roster(own, 1)


@pytest.mark.parametrize("play", PLAYS)
@pytest.mark.parametrize("heads", HEADS)
def test_the_naive_attackers_shape_is_a_naive_blob_attacking_a_post_not_the_skilled_play(play, heads):
    """W6 pin, narrowed by LAB-REV3-B (ledger TD-LAB-REV3-B-a-tests, Architect ruling 2026-10-20): no timeline, side 0 attack-moving, side 1
    holding (guard), each side on the layers the play itself gives it (the baseline takes the play's own layer pair, so a mix play on layers
    2 to 4 is fought where it stands). For a play whose own pair is layer 0 this is still layer 0 on both sides."""
    own, naive = builds(play, heads)
    own_layers = [{g.layer for g in own.groups if g.side == s} for s in (0, 1)]
    assert naive.timeline == ()
    assert {g.order for g in naive.groups if g.side == 0} == {"attack_move"}
    assert {g.order for g in naive.groups if g.side == 1} == {"guard"}
    assert [{g.layer for g in naive.groups if g.side == s} for s in (0, 1)] == own_layers
    if own_layers == [{0}, {0}]:
        assert {(g.order, g.layer) for g in naive.groups if g.side == 0} == {("attack_move", 0)}
        assert {(g.order, g.layer) for g in naive.groups if g.side == 1} == {("guard", 0)}


def test_the_layer_pin_is_still_layer_0_for_the_layer_0_plays_and_the_new_plays_stand_where_they_are():
    """Control for the narrowing: the plays on layer 0 on both sides are still pinned to layer 0, and the layer-stack plays are not (their own pair
    is not layer 0, so a layer-0 pin would have misplaced them)."""
    flat = [p for p in PLAYS if {g.layer for g in plays_space.PLAYS[p].setup_fn().groups} == {0}]
    assert {"s1_hold_choke", "s2_warden_line", "s5_vulnerable_away"} <= set(flat)
    for p in flat:
        assert {g.layer for g in builds(p)[1].groups} == {0}, p
    for p in ("s3_raider_bombard", "s3_bombard_bastion", "s3_bombard_bastion_level"):
        assert {g.layer for g in builds(p)[1].groups} - {0}, p


def test_the_shape_pin_can_tell_a_skilled_play_from_a_naive_one():
    """Positive control for the pin above (green): the skilled play itself breaks it for the plays it is meant to catch."""
    own, _ = builds("s3_layer_above")
    assert own.timeline != () or {(g.order, g.layer) for g in own.groups if g.side == 0} != {("attack_move", 0)}
    own, _ = builds("s4_bait")
    assert own.timeline != ()
