# Rule pins: R-164-01@511d57
# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R2, tests T6 and T1; defects D1, D2, D10); ledger FINDING-lab-d1, FINDING-lab-d2, FINDING-lab-d10; piece LAB-REV3-B
"""LAB-REV3-B, T6 and T1 (R2, R5, D1, D2, D10): plays on all five layers, plays that fire from below, and the swept set that covers the
game. Fast half: no fight (the real-fight half is integration/test_rev3_b_symmetry_real.py). The unit of the claim is the SWEPT set,
`sweep.PLAYS_BY_FAMILY` (plan T1: "a play nobody sweeps covers nothing"); each play's Setup is `plays_space.PLAYS[name].setup_fn()`.

What T6 pins here (every test below that is red today says why in its docstring):
  - layers 3 and 4 each carry a group of some swept play (the lab fields layers 0 and 1 only, D1);
  - plays that fire FROM BELOW exist, the two the plan names: a Raider group one layer below a group of the other side and an
    Interceptor group two layers below one (R2: "Interceptors two below, Raiders one below"). The play's own side 0 is the one below;
    the enemy's same-mix Raiders firing up at a side-0 Raider above them do not count. The shooter's reach (R-164-01: Raider one up,
    Interceptor two up) covers that offset, so the layer arrangement is a firing arrangement;
  - the enemy layer varies across the swept plays ("the enemy layer varies (0 to 4)", R2; T6: plays on layers 3 and 4): some swept play
    has its enemy on layer 3 and some on layer 4;
  - T1 plain: the coverage oracle of piece A's test_rev3_a_coverage.py finds nothing uncovered over the swept set (piece A ships that
    check as a strict expected failure; B turns it green by adding plays to PLAYS_BY_FAMILY and removes A's marker. This file holds the
    same check as an ordinary test so B's red is a plain failure with the uncovered items in its message).
  - baselines take the play's own layer pair (plan R2, Architect ruling 2026-10-20): ONE test over every play of plays_space.PLAYS (so
    the new plays once built) and over a fixture play whose enemy stands on layer 2 (the base has no such play).
  - Guards (green on the lab tip, they fail a builder who breaks a rev 2 ruling in a new swept play): both sides field the same mix at
    every headcount (ruling 2), no play sets a vision factor (ruling 10), the
    Setup validates and passes the pre-flight, the play has anchors, and no side fields more than 4 Wardens per 16 (D9; interim lab cap,
    see test_rev3_b_mirror.py).

NOT PINNED, with Westley (the brief lists them): which layer pairs and which enemy layers batch one fields ("layouts"; the plan's DRAFT
is every pair the reach table allows, and the tests ask for the examples the plan names, not for that exhaustive list); the cap number.
The names of the new plays are the builder's. Detector positive controls are the fixture tests at the top (green on the lab tip)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import plays_space, scenes, sweep, timeline  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from test_rev3_a_coverage import oracle  # noqa: E402

WARDEN_CAP = 4                                          # per 16: the interim lab cap of FINDING-lab-d9 (retires with FU-warden-no-stack)


def base_of(setup, g):
    entry = setup.unit_types.get(g.unit)
    return entry.get("base", g.unit) if entry else g.unit


def swept_names():
    return sorted({p for plays in sweep.PLAYS_BY_FAMILY.values() for p in plays})


def swept_setups():
    return [plays_space.PLAYS[n].setup_fn() for n in swept_names()]


def pairs(setup, shooter_side=None):
    """(shooter base type, offset) for every group of one side against every group of the other: offset = target layer - shooter layer.
    `shooter_side` limits the shooters to one side (None: both)."""
    for a in setup.groups:
        for b in setup.groups:
            if a.side != b.side and shooter_side in (None, a.side):
                yield base_of(setup, a), b.layer - a.layer


def has_pair(setups, base, offset):
    """Side 0, the play's own side, fires from below: its `base` group stands `offset` layers under a group of the enemy. The enemy
    fields the same mix (ruling 2), so its Raiders on the enemy layer fire UP at a side-0 Raider above them: that is the enemy's pairing
    and is not a play that fires from below (it is what T1 counts, both sides, and it is why this check reads side 0 only)."""
    return any(t == base and o == offset for s in setups for t, o in pairs(s, shooter_side=0))


def roster(setup, side):
    out = {}
    for g in setup.groups:
        if g.side == side:
            out[base_of(setup, g)] = out.get(base_of(setup, g), 0) + g.count
    return out


def mix_problems(setup, heads):
    """Empty when both sides field the same mix: side 0 has 16, side 1 has `heads`, each type of side 1 is the side-0 count scaled by
    heads / 16 (exact where whole, within one otherwise). Types are compared by roster base (reach is the roster's, rev 2 ruling 2)."""
    m0, m1 = roster(setup, 0), roster(setup, 1)
    out = []
    if sum(m0.values()) != 16 or sum(m1.values()) != heads:
        out.append("headcounts %d v %d, wanted 16 v %d" % (sum(m0.values()), sum(m1.values()), heads))
    if set(m0) != set(m1):
        out.append("types differ: side 0 %s, side 1 %s" % (sorted(m0), sorted(m1)))
    for k in set(m0) & set(m1):
        want = m0[k] * heads / 16
        if abs(m1[k] - want) > (0 if want == int(want) else 1):
            out.append("%s: side 1 has %d, the scaled side 0 is %g" % (k, m1[k], want))
    return out


def G(side, unit, layer, count=1):
    return Group(side=side, unit=unit, count=count, formation="blob", x=0.0, y=0.0, facing_deg=0.0, layer=layer, order="attack_move")


def S(*groups):
    return Setup(groups=tuple(groups), unit_types={})


# ---- the detectors' own positive controls (fixtures, green on the lab tip) --------------------------------------------------------

def test_control_a_raider_one_below_is_found_and_the_other_arrangements_are_not():
    below = S(G(0, "Raider", 0), G(1, "Vanguard", 1))
    assert has_pair([below], "Raider", 1)
    # the enemy's own Raiders on the enemy layer fire up at a side-0 Raider above them: not a side-0 play that fires from below
    assert not has_pair([S(G(0, "Raider", 1), G(1, "Raider", 0))], "Raider", 1)
    assert not has_pair([S(G(0, "Raider", 1), G(1, "Vanguard", 0))], "Raider", 1)       # Raider ABOVE the enemy: offset -1
    assert not has_pair([S(G(0, "Raider", 0), G(1, "Vanguard", 0))], "Raider", 1)       # same layer
    assert not has_pair([below], "Interceptor", 2)


def test_control_an_interceptor_two_below_is_found():
    assert has_pair([S(G(0, "Interceptor", 0), G(1, "Bombard", 2))], "Interceptor", 2)
    assert not has_pair([S(G(0, "Interceptor", 0), G(1, "Bombard", 1))], "Interceptor", 2)


def test_control_the_mix_check_flags_unequal_mixes_and_passes_equal_ones():
    bad = S(G(0, "Vanguard", 0, 8), G(0, "Raider", 0, 8), G(1, "Vanguard", 0, 16))
    assert mix_problems(bad, 16)
    assert mix_problems(S(G(0, "Vanguard", 0, 8), G(0, "Raider", 0, 8), G(1, "Vanguard", 0, 8), G(1, "Raider", 0, 8)), 16) == []


# ---- T6: layers 3 and 4, from below, the enemy layer ------------------------------------------------------------------------------

def test_t6_the_swept_plays_stand_on_layers_3_and_4():
    """T6 (R2, D1). Red today: the swept plays stand on layers {0, 1}."""
    layers = {g.layer for s in swept_setups() for g in s.groups}
    assert {3, 4} <= layers, "the swept plays stand on layers %s; layers 3 and 4 are missing" % sorted(layers)


def test_t6_a_swept_play_has_raiders_one_layer_below_the_enemy():
    """T6 (R2, D1): "plays that fire from below exist (Raiders one below)". Red today: every side-0 Raider stands level with or above
    the enemy."""
    assert has_pair(swept_setups(), "Raider", 1), "no swept play has a Raider group one layer below a group of the other side"


def test_t6_a_swept_play_has_interceptors_two_layers_below_the_enemy():
    """T6 (R2, D1): "plays that fire from below exist (Interceptors two below)". The Interceptor's reach up is 2 (R-164-01). Red today."""
    assert has_pair(swept_setups(), "Interceptor", 2), "no swept play has an Interceptor group two layers below a group of the other side"


def test_t6_the_enemy_layer_is_not_always_0_across_the_swept_plays():
    """T6 (R2: "the enemy layer varies (0 to 4)"; T6: "plays exist on layers 3 and 4"): some swept play has its enemy on layer 3 and
    some on layer 4 (strengthened from "more than one enemy layer" after the audit of c5bed6ac, which a play on layer 1 alone would
    satisfy). Which other enemy layers batch one fields is Westley's (layouts). Red today: every swept play has its enemy on layer 0."""
    enemy = {g.layer for s in swept_setups() for g in s.groups if g.side == 1}
    assert {3, 4} <= enemy, "the enemy stands on layers %s across the swept plays; layers 3 and 4 are missing" % sorted(enemy)


# ---- baselines take the play's own layer pair ---------------------------------------------------------------------------------------

FIXTURE_PLAY = "fixture_enemy_on_layer_2"


def fixture_setup():
    """A play whose pair is (3, 2): side 0 Raiders on layer 3, side 1 Raiders on layer 2, built by hand (the shape of
    plays.layer_symmetry_play(16, 2), without depending on the symmetry piece, so the red below is about the baselines)."""
    raider = {"Raider": {"base": "Raider", "reach": (1, 1)}}
    return Setup(groups=(Group(side=0, unit="Raider", count=16, formation="blob", x=-300.0, y=0.0, facing_deg=0.0, layer=3,
                               order="attack_move", params={"radius": 128.0}),
                         Group(side=1, unit="Raider", count=16, formation="blob", x=300.0, y=0.0, facing_deg=180.0, layer=2,
                               order="attack_move", params={"radius": 128.0})),
                 unit_types=raider, point=(0.0, 0.0))


@pytest.mark.parametrize("play", sorted(plays_space.PLAYS) + [FIXTURE_PLAY])
def test_r2_the_baselines_take_the_plays_own_layer_pair(play, monkeypatch):
    """R2 (Architect ruling 2026-10-20, plan R2 / T4 note): "a naive baseline takes the play's own layer pair: side 0 on the play's
    side-0 layer, side 1 on the play's enemy layer, naive orders", so every baseline compares like for like. Checked for the naive
    attacker and for the naive defender that keeps each type on the layer the play gave it (naive_defender_play_layer); the layers of
    each side are compared as sets (a play with side 0 on layers 0 and 1 gives a baseline on layers 0 and 1). The two other defender
    roles (naive_defender, naive_defender_attacker_layer) put side 0 on the enemy's layer by design (decisions 25 and 41) and are not
    pinned. Red today: the naive attacker is on layer 0 for every play (the five plays with side 0 above layer 0 and the fixture, whose
    pair is (3, 2)); the play-layer defender already keeps the play's layers (green)."""
    if play == FIXTURE_PLAY:
        monkeypatch.setitem(plays_space.PLAYS, FIXTURE_PLAY, plays_space.PlayDraft(
            setup_fn=fixture_setup, timeline=(), skill="S3", status="draft", numbers={}, words="fixture, not a swept play",
            anchors=plays_space.Anchors("attacker", "choke_mouth", "blob")))
    features = sweep.smoke_layouts()[sweep.SMOKE_LAYOUTS[0]]
    try:
        own = sweep.default_builds(play, "play", features)(16, False)
    except ValueError as err:
        if "disabled" in str(err):
            pytest.skip("the play's mix is disabled; it cannot be built")
        raise
    pair = ({g.layer for g in own.groups if g.side == 0}, {g.layer for g in own.groups if g.side == 1})
    for role in ("naive_attacker", "naive_defender_play_layer"):
        base = sweep.default_builds(play, role, features)(16, False)
        got = ({g.layer for g in base.groups if g.side == 0}, {g.layer for g in base.groups if g.side == 1})
        assert got == pair, "%s: the play's layers (side 0, side 1) are %s, the %s baseline's are %s" % (play, tuple(map(sorted, pair)), role, tuple(map(sorted, got)))


# ---- T1 plain ---------------------------------------------------------------------------------------------------------------------

def test_t1_nothing_is_uncovered_over_the_swept_plays():
    """T1 (R5, D1, D2, D10): the oracle of test_rev3_a_coverage.py over the swept set reports no category cell, no reach pairing and no
    layer left. Red today (five Siege cells, eleven pairings, layers 2 to 4)."""
    left = oracle(swept_setups())
    assert left == {"cells": [], "pairings": [], "layers": []}, "uncovered: %s" % left


# ---- guards: green on the lab tip, they hold a builder to the rev 2 rulings in every swept play ------------------------------------

SWEPT = swept_names()


@pytest.mark.parametrize("name", SWEPT)
def test_guard_every_swept_play_fields_the_same_mix_on_both_sides_at_every_headcount(name):
    for heads in (16, 8, 48, 13, 29):
        assert mix_problems(plays_space.scan_build(name)(None, heads, False), heads) == [], (name, heads)


@pytest.mark.parametrize("name", SWEPT)
def test_guard_no_swept_play_sets_a_vision_factor(name):
    assert not [k for k in plays_space.PLAYS[name].setup_fn().settings if k.startswith("OM_TP_VISION_")]


@pytest.mark.parametrize("name", SWEPT)
def test_guard_every_swept_play_validates_has_anchors_and_passes_the_preflight(name):
    from scripts.skilllab.engine import Engine
    setup = plays_space.PLAYS[name].setup_fn()
    timeline.validate(setup)
    a = plays_space.PLAYS[name].anchors
    assert isinstance(a, plays_space.Anchors) and a.role in ("defender", "attacker")
    assert scenes.preflight(setup, Engine()) == "ok"


@pytest.mark.parametrize("name", SWEPT)
def test_guard_no_swept_play_fields_more_than_4_wardens_per_16(name):
    """D9, the interim lab cap (see test_rev3_b_mirror.py): at most 4 Wardens in the 16 of side 0 and, scaled, in side 1."""
    for heads in (16, 48):
        setup = plays_space.scan_build(name)(None, heads, False)
        assert roster(setup, 0).get("Warden", 0) <= WARDEN_CAP
        assert roster(setup, 1).get("Warden", 0) * 16 <= WARDEN_CAP * heads + 16, (name, heads)      # +16: the rounding of one unit
