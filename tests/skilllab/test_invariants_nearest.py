# Rule pins: R-087-03, R-087-06, R-087-08
"""Engine rules round 2, T3, check 1: `R-087-03` nearest at acquisition. Pure predicates on planted frames; the real fight is
tests/skilllab/arena/test_invariants_round2_wiring.py. Extends the API of tests/skilllab/test_invariants.py.

R-087-03 (docs/bible/epics/E-11-units-and-combat.md): "Given an idle or attack-moving unit with no target and an enemy that its side can see
(E-12 R-093-02; reach across layers R-008-04), When it acquires, Then it targets the nearest such enemy, and the target is a lock ... only then
does it retarget the nearest enemy its side can see".
R-087-08: "acquires only while it has no lock, at its cohort turn on every 4th tick".
R-087-06: "taking damage, When hit, Then it targets the attacker (return fire)".

THE API THIS FILE PINS (the implementer builds to it; the existing swap check of R-087-03 stays as it is):

    Rules(..., cohort=None)       {unit id: slot 0..3}. An acquisition in frame k is ON the cohort turn when k % 4 == slot[unit]. A unit with no entry is
                                  not checked for acquisition (the Monitor passes om_unit_targeting_cohort of every unit).
    frame["visible"]              optional {side: set of enemy unit ids that side sees}; absent: every living enemy is visible. The set of the PREVIOUS
                                  frame is the one an acquisition in frame k was decided on (the state before the step; measured, see the report).
    frame["hits"]                 optional [(attacker, victim)]: every unit the step's shots damaged, direct and splash; absent: the frame's "fires".
    acquisition                   in frame k: the unit is alive, its target is a unit other than its previous one, and its previous target was 0 or was dead in
                                  the previous frame. Judged on the previous frame's positions (planar hypot, the engine's metric today).
    eligible                      a living enemy in the unit's side's visible set, within the unit's reach in layers (Rules.reach {unit: (up, down)}; no
                                  entry: any layer).
    violation                     {"rule": "R-087-03", "tick": k, "unit": acquirer}: the target is not within DRAFT-inv-nearest-tol 1.0 wu of the nearest
                                  eligible enemy, AND no (target, unit) pair is in the "hits" of frames k-4 .. k (R-087-06 return fire, the 4 ticks up to and
                                  including the acquisition tick); or the acquisition is off the cohort turn and has no such hit.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, cell5_4, of, row, rules, trace  # noqa: E402,F401

NEAREST_TOL = 1.0     # DRAFT-inv-nearest-tol (wu): "the nearest" within this much, as the engine's own ties and the measured fights need


@pytest.fixture(scope="module")
def inv():
    return _Module()


def acq(inv, at=5, chose=2, slot=1, one=None, enemies=None, visible=None, hits=None, reach=None, old=0, old_dead_from=None, extra_enemies=None):
    """Unit 1 (side 0, at 100,100, no target before frame `at`) takes target `chose` in frame `at`. Enemies: 2 at 200 wu, 4 at 600 wu, 3 at 50 wu (listed in
    `enemies`, default none). `hits` {frame: [(attacker, victim)]}. Returns the R-087-03 violations."""
    en = {2: row(300, 100, side=1), 4: row(700, 100, side=1)}
    en.update(enemies or {})
    vis = visible if visible is not None else {0: set(en), 1: {1}}
    frames = []
    for k in range(0, at + 1):
        units = {1: row(100, 100, target=chose if k >= at else old, **(one or {}))}
        units.update({u: dict(r) for u, r in en.items()})
        if old_dead_from is not None and k >= old_dead_from:
            units[old].update(alive=False, hp=0.0)
        frames.append(({u: r for u, r in units.items()}, list((hits or {}).get(k, []))))
    tr = trace(*frames)
    for fr in tr:
        fr["visible"] = {s: set(v) for s, v in vis.items()}
        fr["hits"] = list((hits or {}).get(fr["tick"], []))
    return inv.check(tr, rules(inv, cohort={1: slot}, reach=reach or {}, sensor_radius={1: 5000.0}), only=["R-087-03"]).violations


def keys(vs):
    return [(v["rule"], v["tick"], v["unit"]) for v in vs]


def test_R_087_03_control_a_trace_with_no_acquisition_is_silent(inv):
    """Control (green today): a quiet trace, nobody takes a target, reports nothing for R-087-03."""
    tr = trace(*[{1: row(100, 100), 2: row(300, 100, side=1)}] * 6)
    assert inv.check(tr, rules(inv), only=["R-087-03"]).violations == []


def test_R_087_03_a_farther_target_on_the_cohort_turn_is_flagged(inv):
    """R-087-03 'it targets the nearest such enemy': planted, unit 1 (cohort slot 1) takes enemy 4 (600 wu) at tick 5 (5 % 4 = 1) while enemy 2 (200 wu)
    is seen."""
    assert keys(acq(inv, chose=4)) == [("R-087-03", 5, 1)]


def test_R_087_03_the_nearest_target_on_the_cohort_turn_is_silent(inv):
    """R-087-03 control: the same acquisition of the nearest enemy (2) is silent."""
    assert acq(inv, chose=2) == []


@pytest.mark.parametrize("near_by,flagged", [(0.5, False), (2.0, True)], ids=["within-1-wu-tie", "2-wu-farther"])
def test_R_087_03_nearest_means_within_one_wu(inv, near_by, flagged):
    """R-087-03 (DRAFT-inv-nearest-tol 1 wu): enemy 3 stands 200 + `near_by` wu away; taking 3 while 2 (200 wu) is seen is a tie inside 1 wu, a violation at 2 wu."""
    assert bool(acq(inv, chose=3, enemies={3: row(300 + near_by, 100, side=1)})) == flagged


def test_R_087_03_an_acquisition_off_the_cohort_turn_without_return_fire_is_flagged(inv):
    """R-087-08 'at its cohort turn on every 4th tick': planted, the nearest enemy is taken at tick 6 (slot 1, 6 % 4 = 2) and nothing hit the unit."""
    assert keys(acq(inv, at=6, chose=2)) == [("R-087-03", 6, 1)]


def test_R_087_03_an_acquisition_off_the_cohort_turn_after_a_hit_by_the_target_is_return_fire(inv):
    """R-087-06 control: the same tick-6 acquisition of the FAR enemy 4 is silent when enemy 4 hit the unit in that tick (return fire is not the nearest)."""
    assert acq(inv, at=6, chose=4, hits={6: [(4, 1)]}) == []


def test_R_087_03_return_fire_also_excuses_a_farther_target_on_the_cohort_turn(inv):
    """R-087-06 control: on the cohort turn (tick 5) the far enemy 4 that hit the unit in tick 5 is a legal target."""
    assert acq(inv, at=5, chose=4, hits={5: [(4, 1)]}) == []


@pytest.mark.parametrize("hit_at,flagged", [(1, True), (0, True), (4, False), (2, False)], ids=["5-ticks-old", "6-ticks-old", "4-ticks-old", "3-ticks-old"])
def test_R_087_03_return_fire_counts_the_four_ticks_up_to_the_acquisition_tick(inv, hit_at, flagged):
    """R-087-06 (window measured: 4 ticks up to and including the acquisition tick; DRAFT-inv-return-fire-ticks 4): a hit by enemy 4 at tick `hit_at` explains an
    acquisition of 4 at tick 5 when 5 - hit_at <= 4."""
    assert bool(acq(inv, at=5, chose=4, hits={hit_at: [(4, 1)]})) == flagged


def test_R_087_03_a_hit_by_a_different_enemy_is_not_return_fire_on_the_target(inv):
    """R-087-06: the unit was hit by enemy 2, then takes the far enemy 4: not return fire on 4, a violation."""
    assert keys(acq(inv, at=5, chose=4, hits={5: [(2, 1)]})) == [("R-087-03", 5, 1)]


def test_R_087_03_an_enemy_its_side_cannot_see_is_not_the_nearest(inv):
    """R-087-03 'an enemy that its side can see': enemy 3 stands 50 wu away unseen; taking 2 is silent, taking 3 (unseen) is a violation."""
    en, vis = {3: row(150, 100, side=1)}, {0: {2, 4}, 1: {1}}
    assert (acq(inv, chose=2, enemies=en, visible=vis), keys(acq(inv, chose=3, enemies=en, visible=vis))) == ([], [("R-087-03", 5, 1)])


def test_R_087_03_a_dead_nearer_enemy_is_not_the_nearest(inv):
    """R-087-03: enemy 3 at 50 wu is dead; taking 2 is silent."""
    assert acq(inv, chose=2, enemies={3: row(150, 100, side=1, alive=False, hp=0.0)}) == []


def test_R_087_03_an_enemy_beyond_the_units_layer_reach_is_not_the_nearest(inv):
    """R-087-03 '(reach across layers R-008-04)': enemy 3 at 50 wu stands on layer 3, the unit reaches (0 up, 1 down); taking 2 is silent."""
    assert acq(inv, chose=2, enemies={3: row(150, 100, side=1, layer=3)}, reach={1: (0, 1)}) == []


def test_R_087_03_a_retarget_after_the_old_target_died_is_an_acquisition(inv):
    """R-087-03 'only then does it retarget the nearest enemy': the unit held enemy 2, which died in frame 3; in frame 5 (slot 1) it takes enemy 4 while 3
    (150 wu) is nearer: violation. Control: taking 3 is silent."""
    en = {3: row(250, 100, side=1)}
    bad = acq(inv, chose=4, old=2, old_dead_from=3, enemies=en)
    good = acq(inv, chose=3, old=2, old_dead_from=3, enemies=en)
    assert (keys(bad), good) == ([("R-087-03", 5, 1)], [])


# ------------------------------------------------------------------ Round 2, T8: nearest at acquisition and the give-up exclusion (R-087-09)
#
# R-087-09 (E-11): "... if it finds none within 1 s (20 ticks) it drops the target and acquires another". The engine (csrc/unit.c, OM_GIVEUP_EXCLUSION_TICKS) keeps a given-up target
# ineligible for that unit for 100 ticks or until its line clears (DRAFT-giveup-exclusion-ticks 100, Westley's to change), so the unit's next pick is the nearest OTHER enemy its
# side sees. The checker's `_acquire` does not know that. Measured 2026-11-11 on this tree, the cover close-up fixture (tests/skilllab/arena/test_closeup.py COVER: h088 cover
# layout, side A Raiders, hold:A, seed 1, sight on, 1086 ticks): tick 205 unit 15 target 4 -> 0 (given up: 20 unshootable ticks at 232.6 to 233.1 wu), tick 206 unit 15 target 0 -> 3
# (236.3 wu; the nearest seen enemy is the given-up 4 at 232.7). THE API IS UNCHANGED (frames, Rules); the checker has to remember a give-up it excused (R-087-09: the target
# unshootable and not closed in on for 20 frames, then dropped) and leave that target out of the "nearest" set for DRAFT-giveup-exclusion-ticks 100 frames.

GIVE_UP_STUCK = 20          # frames the target is held unshootable before the engine gives it up (R-087-09, 20 ticks)
EXCLUSION = 100             # DRAFT-giveup-exclusion-ticks


def after_give_up(inv, chose, at, stuck=GIVE_UP_STUCK):
    """Unit 1 (side 0, still at (100, 100), attack range 500, cohort slot at % 4) holds enemy 2 (the nearest seen enemy, 200 wu) in frames 0..stuck-1 with the line blocked
    (`shootable` False), drops it in frame stuck (target 0: the give-up) and takes `chose` in frame `at`. Enemies, all seen, all still: 2 at 200 wu, 4 at 230 wu, 5 at 300 wu.
    Returns the R-087-03 violations as (rule, tick, unit)."""
    en = {2: row(300, 100, side=1), 4: row(330, 100, side=1), 5: row(400, 100, side=1)}
    frames = []
    for k in range(0, at + 1):
        held = 2 if k < stuck else 0
        target = chose if k == at else held
        frames.append(({1: row(100, 100, target=target, shootable=not held), **{u: dict(r) for u, r in en.items()}}, []))
    return keys(inv.check(trace(*frames), rules(inv, cohort={1: at % 4}, attack_range={1: 500.0}, sensor_radius={1: 5000.0}), only=["R-087-03"]).violations)


def test_R_087_03_control_a_unit_that_never_gave_anything_up_takes_the_nearest_not_the_next_nearest(inv):
    """R-087-03 'it targets the nearest such enemy' control (green today and after): the same trace as the tests below with no give-up (enemy 2 never held), the unit takes enemy 4
    (230 wu) with enemy 2 (200 wu) seen and nothing excluded: a violation at its tick."""
    assert after_give_up(inv, chose=4, at=61, stuck=0) == [("R-087-03", 61, 1)]


@pytest.mark.parametrize("at", [22, 61, 117], ids=["next-cohort-turn", "41-ticks-after", "97-ticks-after"])
def test_R_087_03_after_a_give_up_the_next_nearest_other_enemy_is_a_legal_pick_inside_the_exclusion_window(inv, at):
    """R-087-03 with R-087-09 (DRAFT-giveup-exclusion-ticks 100): the unit gave enemy 2 up in frame 20 (20 unshootable frames, then target 0); in frame `at` (2, 41 and 97 frames
    later, on its cohort turn) it takes enemy 4, the nearest enemy other than the given-up 2: silent. Measured: cover close-up tick 206, unit 15. Red today: `_acquire` counts the given-up
    enemy 2 as the nearest (200 wu against 230)."""
    assert after_give_up(inv, chose=4, at=at) == []


@pytest.mark.parametrize("at", [22, 61])
def test_R_087_03_after_a_give_up_the_third_nearest_enemy_is_still_a_violation(inv, at):
    """R-087-03 control (green today and after): the same trace but the unit takes enemy 5 (300 wu), farther than the next-nearest other enemy 4 (230 wu): a violation. The exclusion
    removes only the given-up target from the set; it does not make every pick legal."""
    assert after_give_up(inv, chose=5, at=at) == [("R-087-03", at, 1)]


def test_R_087_03_after_the_exclusion_window_the_given_up_enemy_is_eligible_again(inv):
    """R-087-09 (DRAFT-giveup-exclusion-ticks 100): 109 frames after the give-up (frame 20; frame 129) the given-up enemy 2 is the nearest eligible enemy again: taking it is silent, and
    taking enemy 4 (230 wu, no longer the nearest) is a violation. Both green today; the second turns red for an exclusion that never ends."""
    assert (after_give_up(inv, chose=2, at=129), after_give_up(inv, chose=4, at=129)) == ([], [("R-087-03", 129, 1)])
