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


# ------------------------------------------------------------------ Round 3, T9 item 3: what an engine pick may skip (the checker's `_acquire` knows two legal skips too few)
#
# R-087-03 "it targets the nearest such enemy" is judged by the engine in two stages (csrc/unit.c om_tac_nearest_actable / om_tac_pick_across, and om_tac_guard_seen for a guard); the checker's
# "nearest" must skip what the engine may skip. The engine's eligibility, traced by an investigator (engine-rules-baseline/x2/log3.txt, repro3.py): a candidate is alive, not stealthed, hostile, not
# given up by this unit (R-087-09, tested above) and seen by the side. Then
#   stage 1   in range from where the unit stands: the same layer, planar distance within the attack range; another layer within the unit's reach, SLANT distance within the range (walkers only; a
#             flyer on either end is measured flat, R-087-10, DRAFT-slant-ground-only). The nearest by planar distance wins.
#   stage 2   guards only, and only when stage 1 finds nothing: any layer in reach, SLANT distance from the guard's POST at most GUARD_RADIUS 200 + the attack range (R-096-08, csrc/unit.c
#             om_tac_guard_engageable); the nearest to the unit by planar distance wins.
# Reported today as "not the nearest" although legal, on L-0084 seed 1 (the whole fight is tests/skilllab/arena/test_engine_rules_r3_checker_nearest.py): six guard cases (tick/unit 1083/16, 1086/15,
# 1556/25, 1557/26, 1558/27, 1559/24: the nearer enemy was over 500 wu from the post by slant) and two slant cases (1270/15, 1271/16: the nearer enemy, 95 wu away, was 327.6 and 330.0 wu away by slant
# against a range of 300, and a same-layer enemy in range was taken).
# Rule words: R-087-03 "Then it targets the nearest such enemy"; R-096-08 "stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the post"; R-087-10 "the distance is spherical: the
# horizontal distance and the height difference between the two units' layers ... taken together". The API is the one pinned above (frames, Rules); the Rules the checker needs here exist already
# (`guards`, `layer_heights`, `attack_range`, `range_mult`, `flyers`), the Monitor fills them.

GUARD_RADIUS = 200.0     # R-096-08 (DRAFT-guard-radius, Westley's)
RANGE = 300.0


def pick(inv, units, chose, *, at=5, slot=1, guard=None, heights=None, reach=None, flyers=(), unit=None):
    """Unit 1 (side 0, attack range 300, cohort slot `slot`) has no target until frame `at`, when it takes `chose`. `units` are the enemies {id: row}, all seen. `guard` is the post of unit 1, if a guard.
    `heights` the layer band floors, `reach` unit 1's (up, down). Returns the R-087-03 violations as (rule, tick, unit)."""
    frames = []
    for k in range(0, at + 1):
        ux, uy, ul = (unit or (100, 100)) + (() if unit and len(unit) > 2 else (0,))
        one = row(ux, uy, side=0, layer=ul, target=chose if k >= at else 0)
        frames.append(({1: one, **{u: dict(r) for u, r in units.items()}}, []))
    tr = trace(*frames)
    for fr in tr:
        fr["visible"] = {0: set(units), 1: {1}}
    kw = dict(cohort={1: slot}, attack_range={1: RANGE}, sensor_radius={1: 5000.0})
    if guard is not None:
        kw["guards"] = {1: guard}
    if heights is not None:
        kw["layer_heights"] = heights
    if reach is not None:
        kw["reach"] = {1: reach}
    if flyers:
        kw["flyers"] = set(flyers)
    return keys(inv.check(tr, rules(inv, **kw), only=["R-087-03"]).violations)


# -- guards: stage 2 measures from the post, not from where the guard stands

# The guard stands 150 wu east of its post (100, 100), at (250, 100). N: 420 wu from the guard, 570 wu from the post (limit 200 + 300 = 500): not engageable. F: 460 wu from the guard, 484 from the post:
# engageable. Nothing is within 300 wu of the guard, so stage 1 finds nothing and stage 2 picks the nearest engageable: F.
GUARD_AT, POST = (250, 100), (100, 100)
N_FAR_FROM_POST = {2: row(670, 100, side=1)}         # 420 from the guard, 570 from the post
F_ENGAGEABLE = {3: row(250, 560, side=1)}            # 460 from the guard, 484 from the post


def test_R_087_03_control_a_guard_taking_the_nearest_enemy_it_can_engage_from_its_post_is_silent(inv):
    """R-087-03 control (green today and after): the same guard with enemy E at 400 wu from it and 446 from the post (engageable) as well as F (460, 484): taking E, the nearest it can engage, is silent."""
    e = {4: row(250, 500, side=1)}                    # 400 from the guard, 446 from the post
    assert pick(inv, {**e, **F_ENGAGEABLE}, chose=4, guard=POST, unit=GUARD_AT) == []


def test_R_087_03_a_guard_may_skip_a_nearer_enemy_that_is_beyond_its_post_radius_plus_range(inv):
    """R-087-03 'it targets the nearest such enemy' + R-096-08 'no farther than GUARD_RADIUS = 200 wu from the post' (engine stage 2, om_tac_guard_seen): the guard at (250, 100), post (100, 100), range
    300, picks F (460 from it, 484 from the post) while N (420 from it) is 570 wu from the post, beyond 200 + 300 = 500: legal, silent. Measured on L-0084 seed 1: ticks 1083 (unit 16), 1086 (15), 1556
    (25), 1557 (26), 1558 (27), 1559 (24). Red today: `_acquire` counts N as the nearest (420 against 460)."""
    assert pick(inv, {**N_FAR_FROM_POST, **F_ENGAGEABLE}, chose=3, guard=POST, unit=GUARD_AT) == []


def test_R_087_03_a_guard_skipping_a_nearer_enemy_it_could_engage_from_its_post_is_still_a_violation(inv):
    """R-087-03 control (green today and after): the same guard, with a nearer enemy N2 at 420 from it and 446 from the post (inside the 500 wu): taking F (460) instead is a violation. The skip is for
    the enemy the guard may not reach from its post, not for every enemy the guard does not take."""
    n2 = {2: row(250, 520, side=1)}                   # 420 from the guard, 446 from the post
    assert pick(inv, {**n2, **F_ENGAGEABLE}, chose=3, guard=POST, unit=GUARD_AT) == [("R-087-03", 5, 1)]


def test_R_087_03_a_unit_that_is_not_a_guard_may_not_skip_an_enemy_beyond_a_post_radius(inv):
    """R-087-03 control (green today and after): the post radius is for guards (R-096-08). The same positions with no guard order: taking F while N (420) is nearer is a violation."""
    assert pick(inv, {**N_FAR_FROM_POST, **F_ENGAGEABLE}, chose=3, unit=GUARD_AT) == [("R-087-03", 5, 1)]


def test_R_087_03_a_guard_with_an_enemy_in_range_must_take_the_nearest_in_range_not_stage_two(inv):
    """R-087-03 control (green today and after): stage 2 runs only when stage 1 finds nothing. The guard at (250, 100) has enemy A in range (250 wu) and enemy B in range (280 wu); taking B is a
    violation although both are inside the post's 500 wu."""
    a, b = {2: row(500, 100, side=1)}, {3: row(250, 380, side=1)}       # 250 and 280 from the guard
    assert pick(inv, {**a, **b}, chose=3, guard=POST, unit=GUARD_AT) == [("R-087-03", 5, 1)]


# -- slant: another layer's enemy is in range by slant distance

# Layers 0 and 1, band floors 0 and 313.5 wu (R-087-10: the height difference counts). The unit stands on layer 1 at (100, 100), reach (0 up, 1 down). A is on layer 0, 95 wu away
# horizontally: 327.6 by slant, out of range 300. B is on layer 1, 250 wu away: in range.
HEIGHTS = [0.0, 313.5]
UNIT_L1 = (100, 100, 1)
A_OUT_OF_RANGE_BY_SLANT = {2: row(195, 100, side=1, layer=0)}        # 95 planar, 327.6 by slant
B_SAME_LAYER_IN_RANGE = {3: row(350, 100, side=1, layer=1)}          # 250 planar and by slant


def test_R_087_03_a_unit_may_skip_a_nearer_enemy_on_another_layer_that_is_out_of_range_by_slant(inv):
    """R-087-03 + R-087-10 'the distance is spherical' (engine stage 1, om_tac_pick_across): the unit on layer 1 takes B (250 wu, same layer, in range) while A (95 wu away horizontally, layer 0) is 327.6
    wu away by slant, outside its range 300: legal, silent. Measured on L-0084 seed 1: ticks 1270 (unit 15, nearer enemy 327.6 by slant against range 300) and 1271 (unit 16, 330.0). Red today:
    `_acquire` measures planar distance only and counts A as the nearest (95 against 250)."""
    assert pick(inv, {**A_OUT_OF_RANGE_BY_SLANT, **B_SAME_LAYER_IN_RANGE}, chose=3, unit=UNIT_L1, heights=HEIGHTS, reach=(0, 1)) == []


def test_R_087_03_a_unit_skipping_a_nearer_enemy_inside_range_by_slant_is_still_a_violation(inv):
    """R-087-03 control (green today and after): band floors 0 and 100 wu make A 138.0 wu away by slant, inside range 300: taking B (250) instead is a violation. The slant skip is for the enemy out of range
    by slant, not for every enemy on another layer."""
    assert pick(inv, {**A_OUT_OF_RANGE_BY_SLANT, **B_SAME_LAYER_IN_RANGE}, chose=3, unit=UNIT_L1, heights=[0.0, 100.0], reach=(0, 1)) == [("R-087-03", 5, 1)]


def test_R_087_03_a_flyer_measures_flat_so_a_nearer_enemy_on_another_layer_is_not_skipped(inv):
    """R-087-10 'DRAFT-slant-ground-only' (a flyer on either end is measured flat) control (green today and after): the same scene as the slant skip with unit 1 a flyer: A is 95 wu away flat, in range;
    taking B (250) instead is a violation."""
    assert pick(inv, {**A_OUT_OF_RANGE_BY_SLANT, **B_SAME_LAYER_IN_RANGE}, chose=3, unit=UNIT_L1, heights=HEIGHTS, reach=(0, 1), flyers=(1,)) == [("R-087-03", 5, 1)]


def test_R_087_03_a_nearer_enemy_on_a_layer_out_of_reach_is_not_eligible_by_slant_or_otherwise(inv):
    """R-087-03 control (green today and after, the existing reach skip): A on layer 3, the unit reaches 0 up, 1 down from layer 1: not eligible. Taking B is silent."""
    far_layer = {2: row(195, 100, side=1, layer=3)}
    assert pick(inv, {**far_layer, **B_SAME_LAYER_IN_RANGE}, chose=3, unit=UNIT_L1, heights=[0.0, 313.5, 600.0, 900.0], reach=(0, 1)) == []
