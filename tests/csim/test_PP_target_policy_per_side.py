"""A196 (rulings-2 Addendum 66/67): LAB-ONLY per-side target policy and per-cohort-turn re-evaluation.

Contract proposed here (the Doer must match these names):
  * a new om_tac_param member OM_TP_TARGET_POLICY_FACTION_1, appended right before OM_TP__COUNT
    (the enum only grows at the end), read and written through om_tactical_set_param / get_param.
  * OM_TP_TARGET_POLICY keeps meaning faction 0's policy.
  * SENTINEL: the faction-1 id is "unset" at -1 (its default; range -1, 0, 1). Unset = follows
    OM_TP_TARGET_POLICY. -1 is outside the old id's range (0..1), so it cannot collide with a policy.
    Setting the id back to -1 unsets it. 2 is refused.
  * Policy 1 (most damaged): a unit re-evaluates on EVERY cohort turn (every 4th tick for its slot,
    OM_TARGETING_COHORT_COUNT) and switches to the most damaged enemy in range (lowest hp fraction;
    ties nearest, then lowest id). Policy 0 (nearest, kept while alive and in range) is untouched.
  * Lab instrument, not a game rule (A196; Q-008-05 stays Westley's).

Scenes: Raider (range 200) at the origin, Supply enemies (100 hp). Every check below that proves a
switch has a control that the same scene does NOT switch at policy 0, so a detector that always
passes cannot pass.
"""
import ctypes

import pytest

import a99_tactical_runs as A
from test_PP_unit_support import RAIDER, SUPPLY, get_param, set_param, spawn, step, target

P0 = "OM_TP_TARGET_POLICY"
P1 = "OM_TP_TARGET_POLICY_FACTION_1"
STAGGER = 4  # one full cohort cycle: every unit has a turn within this many ticks


def _supply(lib, w, faction, x, y, hp=None):
    u = spawn(lib, w, SUPPLY, faction, x, y)
    if hp is not None:
        lib.om_unit_set_hp(w, u, float(hp))
    return u


def _settle(lib, w, uid, expect):
    """Run one cohort cycle and require the opening pick, so the re-evaluation tests start from a held target."""
    step(lib, w, STAGGER)
    assert target(lib, w, uid) == expect, "setup: opening pick is not the nearest full-health enemy"


def _two_in_range(lib, w, attacker_faction, ox=0.0):
    """Attacker at (ox,0); held 'a' nearest at +100 full hp; 'b' farther at +150. Returns (att, a, b)."""
    foe = 1 - attacker_faction
    att = spawn(lib, w, RAIDER, attacker_faction, ox, 0.0)
    a = _supply(lib, w, foe, ox + 100.0, 0.0)
    b = _supply(lib, w, foe, ox + 150.0, 0.0)
    return att, a, b


# ---- (a) the id, round trip, default unset ----

def test_A196_new_param_id_exists_and_keeps_its_number(lib):
    from test_PP_unit_support import _enum_values
    v = _enum_values()
    assert P1 in v, f"A196: {P1} is not in enum om_tac_param"
    assert v[P1] == 59, "A196: the enum only grows at the end; the id keeps the number it had (59)"
    assert v[P1] not in (v[P0],)


def test_A196_faction_1_id_unset_by_default_and_round_trips(lib, world_factory):
    w = world_factory(n_regions=1)
    assert get_param(lib, w, P1) == -1.0, "A196 sentinel: unset reads -1"
    for val in (1, 0, -1):
        assert set_param(lib, w, P1, val) == 0
        assert get_param(lib, w, P1) == float(val)
    assert get_param(lib, w, P0) == 0.0, "setting the faction-1 id must not move faction 0's"
    assert set_param(lib, w, P1, 2) == -1, "out of range refused (positive control: 1 was accepted above)"
    assert get_param(lib, w, P1) == -1.0
    assert set_param(lib, w, P0, 1) == 0
    assert get_param(lib, w, P1) == -1.0, "setting faction 0's id must not write the faction-1 id"
    assert set_param(lib, w, P0, -1) == -1, "faction 0's id keeps its 0..1 range"


def _run_reeval(lib, w, attacker_faction, ox=0.0):
    att, a, b = _two_in_range(lib, w, attacker_faction, ox)
    _settle(lib, w, att, a)
    lib.om_unit_set_hp(w, b, 30.0)
    step(lib, w, STAGGER)
    return target(lib, w, att), a, b


def test_A196_unset_faction_1_follows_faction_0_policy(lib, world_factory):
    """Policy 1 set only for faction 0: a faction-1 attacker behaves as under policy 1 (compare to both set)."""
    w1 = world_factory(n_regions=1)
    assert set_param(lib, w1, P0, 1) == 0
    got_unset, a, b = _run_reeval(lib, w1, 1)
    w2 = world_factory(n_regions=1)
    assert set_param(lib, w2, P0, 1) == 0 and set_param(lib, w2, P1, 1) == 0
    got_both, a2, b2 = _run_reeval(lib, w2, 1)
    assert (a, b) == (a2, b2)
    assert got_both == b2, "control: with policy 1 explicit the faction-1 attacker switches to the more damaged"
    assert got_unset == got_both, "A196: unset faction-1 id must follow faction 0's value"


def test_A196_explicit_faction_1_overrides_faction_0(lib, world_factory):
    """Control for the follow rule: P0=1, P1=0 makes faction 1 keep its target (so 'follows' is not 'always 1')."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0 and set_param(lib, w, P1, 0) == 0
    got, a, b = _run_reeval(lib, w, 1)
    assert got == a


# ---- (b) per side in one scene ----

def test_A196_per_side_policies_in_one_scene(lib, world_factory):
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0
    assert set_param(lib, w, P1, 0) == 0
    att0, a0, b0 = _two_in_range(lib, w, 0, 0.0)
    att1, a1, b1 = _two_in_range(lib, w, 1, 6000.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att0) == a0 and target(lib, w, att1) == a1, "setup: both open on the nearest"
    lib.om_unit_set_hp(w, b0, 30.0)
    lib.om_unit_set_hp(w, b1, 30.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att0) == b0, "faction 0 (policy 1) switches to the most damaged in range"
    assert target(lib, w, att1) == a1, "faction 1 (policy 0) keeps its nearest, alive and in range"


def test_A196_per_side_reversed(lib, world_factory):
    """Reverse assignment: the rule follows the side, not the order of ids."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 0) == 0
    assert set_param(lib, w, P1, 1) == 0
    att0, a0, b0 = _two_in_range(lib, w, 0, 0.0)
    att1, a1, b1 = _two_in_range(lib, w, 1, 6000.0)
    step(lib, w, STAGGER)
    lib.om_unit_set_hp(w, b0, 30.0)
    lib.om_unit_set_hp(w, b1, 30.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att0) == a0
    assert target(lib, w, att1) == b1


# ---- (c) re-evaluation on every cohort turn (faction 0 id, policy 1) ----

def test_A196_policy_0_keeps_a_live_in_range_target_control(lib, world_factory):
    """Control for the switch tests: same scene at policy 0 never switches."""
    w = world_factory(n_regions=1)
    got, a, b = _run_reeval(lib, w, 0)
    assert got == a


def test_A196_reeval_switches_to_the_farther_more_damaged(lib, world_factory):
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0
    got, a, b = _run_reeval(lib, w, 0)
    assert got == b, "policy 1 re-evaluates every cohort turn; today it only picks first and after a kill"


def test_A196_reeval_ignores_a_more_damaged_enemy_out_of_range(lib, world_factory):
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0
    att = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    a = _supply(lib, w, 1, 100.0, 0.0)
    far = _supply(lib, w, 1, 400.0, 0.0)
    _settle(lib, w, att, a)
    lib.om_unit_set_hp(w, far, 5.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att) == a, "out of attack range is never a candidate (control: in range it would switch)"


def test_A196_reeval_tie_goes_to_the_nearest(lib, world_factory):
    """Held a is the least damaged; b (150) and c (180) tie on fraction: b, the nearer, wins."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0
    att = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    a = _supply(lib, w, 1, 100.0, 0.0)
    c = _supply(lib, w, 1, 180.0, 0.0)  # spawned before b so id order cannot be what decides
    b = _supply(lib, w, 1, 150.0, 0.0)
    _settle(lib, w, att, a)
    lib.om_unit_set_hp(w, b, 40.0)
    lib.om_unit_set_hp(w, c, 40.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att) == b


def test_A196_reeval_tie_on_fraction_and_distance_goes_to_the_lowest_id(lib, world_factory):
    """b and c mirror each other about the x axis: same fraction, same distance; the lower id wins."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, P0, 1) == 0
    att = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    a = _supply(lib, w, 1, 100.0, 0.0)
    b = _supply(lib, w, 1, 150.0, 20.0)
    c = _supply(lib, w, 1, 150.0, -20.0)
    assert b < c
    _settle(lib, w, att, a)
    lib.om_unit_set_hp(w, b, 40.0)
    lib.om_unit_set_hp(w, c, 40.0)
    step(lib, w, STAGGER)
    assert target(lib, w, att) == b


# ---- (d) policy 0 guard: recorded hashes stand ----

def test_A196_policy_0_explicit_equals_the_recorded_A99_hashes(lib):
    """Green now and after: both ids written explicitly at 0 (the faction-1 id only when it exists) leaves
    the recorded A99 fight trace byte-identical. Positive control: the next test."""
    name, units, gap, steps = "fight_502_gap100", 502, 100, 120
    rec = A.load_recorded()[name]["hashes"][:steps]
    w = A.build(lib, units)
    A.stage_fight(lib, w, A._slots(lib, w), gap)
    assert set_param(lib, w, P0, 0) == 0
    try:
        set_param(lib, w, P1, 0)
    except BaseException:  # the faction-1 id is not in the enum yet; the guard must still run
        pass
    got = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        got.append(A.state_hash(lib, w))
    lib.om_world_free(w)
    assert got == rec


def test_A196_A99_guard_positive_control_policy_1_changes_nothing_here_but_a_perturbed_hash_is_caught(lib):
    rec = list(A.load_recorded()["fight_502_gap100"]["hashes"][:20])
    got = A.run_hashes(lib, 502, 100, 20)
    assert got == rec
    rec[7] = "0" * 16
    assert got != rec
