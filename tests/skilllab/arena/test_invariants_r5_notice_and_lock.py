# Rule pins: R-087-03, R-087-04, R-087-06, R-087-08, R-096-08, R-208-01
"""Engine rules round 5, G7 (docs/northstar/plans/engine-rules-2026-11-08/round5.md): the lab checker's acquire, lock and guard predicates know the notice distance.
Pure predicates over planted frames (`scripts/skilllab/invariants.check`); the whole-run twins on the catalogue are G1 to G3's tests. The checker is the lab builder's: these
tests are red until it is built, each for the reason the test says.

Rule text as it reads on this branch (docs/bible/epics/E-11-units-and-combat.md, E-13-movement-and-command.md):
R-087-04: "When an enemy its side can see (E-12 R-093-02; reach across layers R-008-04) is within its notice distance, Then it acquires the nearest such enemy at its cohort turn
(R-087-08) ... The notice distance is the unit's own attack range plus a margin of one tenth of that range (`DRAFT-notice-margin`, Westley's number to change: 30 wu on a range of
300) , measured as weapon reach is (R-087-10). It is never the sensor radius: an enemy the side sees beyond the notice distance is not acquired".
R-087-03: "the unit keeps it, whatever else comes nearer, until the target dies, leaves its side's sight, leaves the unit's notice distance, or the player gives the unit a new order;
only then does it pick again, the nearest enemy its side can see within its notice distance ... A target taken by return fire (R-087-06) is not dropped for distance: the leash alone
bounds that chase (R-087-05)."
R-096-08: "each unit takes its position as its post and acquires as every unit does, an enemy its side can see within its notice distance (E-11 R-087-04), stepping toward it no farther than
`GUARD_RADIUS` = 200 wu from the post".

THE API THIS FILE PINS (the lab builder builds to it; everything not named here keeps the contract of tests/skilllab/test_invariants.py and test_invariants_nearest.py):

    NOTICE_MARGIN = 0.1       module constant, DRAFT-notice-margin: a unit's notice distance to an enemy is Rules.attack_range[unit] times Rules.range_mult(unit layer, enemy layer) times
                              (1 + NOTICE_MARGIN), measured as R-087-10 measures a shot (the spherical distance of `_spherical`, flat when either end flies). A unit with no attack_range entry
                              has no notice distance and is not judged by the three checks below (the pins of the earlier files stay green).
    acquire   (R-087-03)      the existing acquisition check, plus: a pick whose target stood beyond the notice distance in the previous frame is a violation, whether or not it is the nearest
                              seen enemy, unless return fire explains it (a hit by the target in the 4 frames up to the acquisition, as before). The same for a guard (Rules.guards): its pick is
                              judged from where it stands, no longer from its post and radius.
    lock end  (R-087-03)      a target change (old target alive and seen) is excused when the old target stood beyond the notice distance in the previous frame (the state the step decided on).
    lock kept (R-087-03)      a unit that holds a living, seen target that stands beyond the notice distance in each of more than COHORT_SLOTS (4) consecutive frames is reported once, in the
                              fifth of them; a lock taken by return fire (a hit by the target on the unit in the frame the lock began or the 3 before it) is never reported for it.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

NOTICE_MARGIN = 0.1          # DRAFT-notice-margin (round5.md G1), as the checker's constant
COHORT_PERIOD = 4            # R-087-08: "at its cohort turn on every 4th tick"
SLOT = 1                     # unit 1's cohort slot in every trace below: acquisitions land on ticks 1, 5, 9


@pytest.fixture(scope="module")
def inv():
    return _Module()


def keys(vs):
    return [(v["rule"], v["tick"], v["unit"]) for v in vs]


def notice(attack_range):
    return attack_range * (1 + NOTICE_MARGIN)


def pick(inv, attack_range, gap, at=5, hits=None, enemy_layer=0, my_layer=0, extra_rules=None, guard=False, nearer_unseen=None):
    """Unit 1 (side 0, at 100,100, attack range `attack_range`, no target before frame `at`) takes enemy 2 (side 1, `gap` wu east on a flat world) in frame `at`. Enemy 2 is
    the only enemy the side sees. Returns the R-087-03 violations."""
    kw = dict(cohort={1: SLOT}, attack_range={1: float(attack_range)}, sensor_radius={1: 5000.0})
    kw.update(extra_rules or {})
    if guard:
        kw["guards"] = {1: (100.0, 100.0)}
    frames = []
    for k in range(at + 1):
        units = {1: row(100, 100, layer=my_layer, target=2 if k >= at else 0), 2: row(100 + gap, 100, side=1, layer=enemy_layer)}
        if nearer_unseen:
            units[3] = row(100 + nearer_unseen, 100, side=1, layer=enemy_layer)
        frames.append(units)
    tr = trace(*frames)
    for fr in tr:
        fr["visible"] = {0: {2}, 1: {1}}
        fr["hits"] = list((hits or {}).get(fr["tick"], []))
    return inv.check(tr, rules(inv, **kw), only=["R-087-03"]).violations


def test_R_087_04_the_notice_margin_is_a_tenth_of_the_attack_range(inv):
    """R-087-04: "a margin of one tenth of that range (`DRAFT-notice-margin`)": the checker's constant is 0.1 (30 wu on a range of 300). Red today: no such constant."""
    assert inv.NOTICE_MARGIN == pytest.approx(0.1)


@pytest.mark.parametrize("attack_range", [200, 300, 600], ids=["raider-200", "vanguard-300", "bombard-600"])
def test_R_087_04_a_pick_beyond_the_notice_distance_is_flagged(inv, attack_range):
    """R-087-04: "an enemy the side sees beyond the notice distance is not acquired". Planted: the only enemy the side sees stands 10 wu beyond the notice distance (a tenth over the
    range) and the unit takes it on its cohort turn (tick 5, slot 1) with nothing hit it; it is the nearest seen enemy, so only the notice distance can flag it. Red today: the checker
    judges nearest alone, so the pick of an enemy at 340 wu with range 300 raises nothing."""
    assert keys(pick(inv, attack_range, notice(attack_range) + 10)) == [("R-087-03", 5, 1)]


@pytest.mark.parametrize("attack_range", [200, 300, 600], ids=["raider-200", "vanguard-300", "bombard-600"])
def test_R_087_04_control_a_pick_inside_the_notice_distance_is_silent(inv, attack_range):
    """R-087-04 control (green today and after): the same pick with the enemy 10 wu inside the notice distance (320 wu on a range of 300) is legal: the test above fails for the distance
    and for nothing else in the setup."""
    assert pick(inv, attack_range, notice(attack_range) - 10) == []


def test_R_087_06_control_a_pick_beyond_the_notice_distance_by_return_fire_is_silent(inv):
    """R-087-06 / R-087-03: "A target taken by return fire (R-087-06) is not dropped for distance". Planted: the same 340 wu pick, but the enemy hit the unit in the acquisition frame: legal."""
    assert pick(inv, 300, 340.0, hits={5: [(2, 1)]}) == []


def test_R_087_04_the_reach_table_multiplier_is_part_of_the_notice_distance(inv):
    """R-087-04 "measured as weapon reach is (R-087-10)", R-087-10 "reach table's multipliers": a unit on layer 1 with range 300 whose reach to layer 0 is 1.2 times (range_mult) has the notice
    distance 300 x 1.2 x 1.1 = 396: an enemy on layer 0 at 380 is legal; the same setup with the multiplier 1.0 (notice 330) flags the pick."""
    mult = {"range_mult": lambda la, lb: 1.2 if lb < la else 1.0, "layer_heights": [0.0, 0.0]}
    assert pick(inv, 300, 380.0, my_layer=1, enemy_layer=0, extra_rules=mult) == []
    assert keys(pick(inv, 300, 380.0, my_layer=1, enemy_layer=0, extra_rules={"layer_heights": [0.0, 0.0]})) == [("R-087-03", 5, 1)]


def test_R_087_10_the_notice_distance_is_spherical_across_layers(inv):
    """R-087-04 "measured as weapon reach is (R-087-10)": layer 1 stands 300 wu above layer 0 (layer_heights). Range 300 (notice 330): an enemy 100 wu away on the ground is 316 wu by
    slant, legal; one 250 wu away is 390 by slant, flagged."""
    h = {"layer_heights": [0.0, 300.0]}
    assert pick(inv, 300, 100.0, my_layer=1, enemy_layer=0, extra_rules=h) == []
    assert keys(pick(inv, 300, 250.0, my_layer=1, enemy_layer=0, extra_rules=h)) == [("R-087-03", 5, 1)]


def test_R_096_08_a_guards_pick_beyond_its_notice_distance_is_flagged(inv):
    """R-096-08 (current text): a guard "acquires as every unit does, an enemy its side can see within its notice distance". Planted: a guard with range 300 at its post takes the only
    enemy it sees, 400 wu away (inside the old reach of radius 200 + range 300, beyond notice 330). Red today: the guard's stage 2 takes anything within the radius plus range."""
    assert keys(pick(inv, 300, 400.0, guard=True)) == [("R-087-03", 5, 1)]


def test_R_096_08_control_a_guards_pick_inside_its_notice_distance_is_silent(inv):
    """R-096-08 control (green today and after): the same guard taking an enemy at 320 wu, inside the notice distance, is legal."""
    assert pick(inv, 300, 320.0, guard=True) == []


def hold(inv, attack_range, old_gap, new_target=4, swap_at=4, walking=None, hits=None, frames=None):
    """Unit 1 (range `attack_range`) holds enemy 2 from frame 0 (no acquisition is judged); in frame `swap_at` it takes enemy 4 (100 wu away, in notice). Enemy 2 stands `old_gap` wu east in every frame, or
    at `walking[k]` in frame k. Returns the R-087-03 violations."""
    out = []
    for k in range(swap_at + 1):
        gap = walking[k] if walking else old_gap
        out.append({1: row(100, 100, target=2 if k < swap_at else new_target), 2: row(100 + gap, 100, side=1), 4: row(100, 200, side=1)})
    tr = trace(*out)
    for fr in tr:
        fr["visible"] = {0: {2, 4}, 1: {1}}
        fr["hits"] = list((hits or {}).get(fr["tick"], []))
    return inv.check(tr, rules(inv, cohort={1: SLOT}, attack_range={1: float(attack_range)}, sensor_radius={1: 5000.0}), only=["R-087-03"]).violations


@pytest.mark.parametrize("attack_range", [200, 300, 600], ids=["raider-200", "vanguard-300", "bombard-600"])
def test_R_087_03_a_lock_dropped_because_the_target_left_the_notice_distance_is_not_a_swap(inv, attack_range):
    """R-087-03: the unit keeps the lock "until the target dies, leaves its side's sight, leaves the unit's notice distance, or the player gives the unit a new order; only then does it pick
    again". Planted: the target stands 10 wu beyond the notice distance in the frame the step decided on, and in the next frame the unit holds the nearer enemy 4: a legal end and a legal
    pick, silent. Red today: the swap check flags it (a live, seen target exchanged)."""
    assert hold(inv, attack_range, notice(attack_range) + 10) == []


@pytest.mark.parametrize("attack_range", [200, 300, 600], ids=["raider-200", "vanguard-300", "bombard-600"])
def test_R_087_03_control_a_lock_swapped_inside_the_notice_distance_is_flagged(inv, attack_range):
    """R-087-03 control (green today and after): the same swap with the old target 10 wu inside the notice distance nothing excuses: still a violation, so the test above is silent for the
    distance and not because swaps stopped being checked."""
    assert keys(hold(inv, attack_range, notice(attack_range) - 10)) == [("R-087-03", 4, 1)]


def test_R_087_03_a_target_walking_away_ends_the_lock_on_the_tick_after_it_passes_the_notice_distance(inv):
    """R-087-03, per tick: the target walks away: 300, 310, 320, 325, 340, 350 wu (notice 330). The swap in frame 5 follows the frame-4 state (340 wu, beyond): silent; the same swap one
    frame early, in frame 4 after the frame-3 state (325 wu, inside), is flagged."""
    walk = [300.0, 310.0, 320.0, 325.0, 340.0, 350.0]
    assert hold(inv, 300, 0, swap_at=5, walking=walk) == []
    assert keys(hold(inv, 300, 0, swap_at=4, walking=walk[:5])) == [("R-087-03", 4, 1)]


NEAR, FAR = 250.0, 400.0     # wu from the unit (range 300, notice 330): the target is inside, then beyond, the notice distance


def keep(inv, n, hits=None, back_at=None):
    """Unit 1 (range 300, side 0, at 100,100) takes enemy 2 in frame 1 (the enemy stands NEAR in frames 0 and 1, so the pick is legal) and holds it for `n` frames (frames 1 to n); the
    enemy stands FAR from frame 2 on, or NEAR again from frame `back_at`. The unit's target is 0 in frame n + 1. Returns the R-087-03 violations."""
    frames = []
    for k in range(n + 2):
        gap = NEAR if k <= 1 or (back_at is not None and k >= back_at) else FAR
        frames.append({1: row(100, 100, target=2 if 1 <= k <= n else 0), 2: row(100 + gap, 100, side=1)})
    tr = trace(*frames)
    for fr in tr:
        fr["visible"] = {0: {2}, 1: {1}}
        fr["hits"] = list((hits or {}).get(fr["tick"], []))
    return inv.check(tr, rules(inv, cohort={1: 1}, attack_range={1: 300.0}, sensor_radius={1: 5000.0}), only=["R-087-03"]).violations


def test_R_087_03_a_lock_kept_beyond_the_notice_distance_for_more_than_a_cohort_period_is_reported_once(inv):
    """R-087-03 (G7 lock): "a lock kept on a target beyond the notice distance for more than one cohort period is reported". "Beyond" is beyond in every reading of the tick (round5.md
    "Fourth pass": the unit and the target each at their position of frame N-1 or N). Planted: the unit takes an enemy at 250 wu (legal) in tick 1; the enemy stands at 400 (notice 330)
    from frame 2 on, so frame 2 has a reading at 250 (inside, frame 1's position) and the first frame beyond in every reading is 3; the unit still holds it in tick 12. Reported once, in the
    fifth such frame (tick 7), not every frame."""
    assert keys(keep(inv, 12)) == [("R-087-03", 7, 1)]
    assert keys(keep(inv, 7)) == [("R-087-03", 7, 1)]      # held through tick 7 (the fifth frame beyond in every reading) and dropped in tick 8: reported all the same


def test_R_087_03_control_a_lock_dropped_within_one_cohort_period_is_silent(inv):
    """R-087-03 control (green today, red if the allowance is dropped): the same enemy beyond the distance in every reading in ticks 3 to 6 (4 frames, one cohort period; tick 2 has a reading
    inside) and the lock dropped in tick 7 is silent; so is a lock dropped earlier."""
    assert keep(inv, 6) == []
    assert keep(inv, 5) == []


def test_R_087_03_control_a_target_that_comes_back_inside_the_notice_distance_is_silent(inv):
    """R-087-03 control: the target is beyond the notice distance for 3 frames only (ticks 2 to 4), then back at 250 for the rest of 12 frames: the count of consecutive frames beyond
    restarts when it is inside again, so nothing is reported."""
    assert keep(inv, 12, back_at=5) == []


def test_R_087_06_a_lock_taken_by_return_fire_is_never_reported_for_distance(inv):
    """R-087-06 / R-087-03: "A target taken by return fire (R-087-06) is not dropped for distance: the leash alone bounds that chase". Planted: the enemy hit the unit in the frame the
    lock began (tick 1) and then stood 400 wu away for 30 frames: silent. The same trace with no hit is reported (the first test of this group)."""
    assert keep(inv, 30, hits={1: [(2, 1)]}) == []


# ---------------------------------------------------------------------------------------------------------------- the test-side oracle (engine_rules_oracle.py)
# The same three questions asked of a hand-built fight record (the shape `oracle.Recorder` has: per tick `pre` and `post` rows, `fires`, `vis_pre`, `vis_post`), so that the oracle
# that judges the real fights of G1 to G3 is itself shown to report the planted case and to pass the legal one. Not the lab checker: it imports no scripts/skilllab/invariants.

def _oracle():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import engine_rules_oracle as oracle
    return oracle


def record(gaps, targets, hits=(), dead_before=None):
    """A fake Recorder of unit 1 (side 0, range 300, sensor radius 300, at the origin) and enemies 2 and 4 (side 1): `gaps[k]` is enemy 2's distance after tick k + 1 (and before tick
    k + 2), enemy 4 stands 100 wu away; `targets[k]` is unit 1's target after tick k + 1; `hits` the ticks in which enemy 2 fired at and hit unit 1 (each planted tick carries "fires" and "hits", as the Recorder's do)."""
    from types import SimpleNamespace

    def snap(k, tgt):
        gap = gaps[min(k, len(gaps) - 1)]
        return {1: {"alive": True, "x": 0.0, "y": 0.0, "layer": 0, "hp": 100.0, "tgt": tgt, "dest": (5000.0, 0.0)},
                2: {"alive": True, "x": gap, "y": 0.0, "layer": 0, "hp": 100.0, "tgt": 0, "dest": None},
                4: {"alive": True, "x": 0.0, "y": 100.0, "layer": 0, "hp": 100.0, "tgt": 0, "dest": None}}
    ticks, prev = [], 0
    for k, tgt in enumerate(targets):
        ticks.append({"n": k + 1, "pre": snap(k, prev), "post": snap(k + 1, tgt), "fires": [(2, 1)] if (k + 1) in hits else [],
                      "hits": [(2, 1)] if (k + 1) in hits else [],
                      "vis_pre": {(0, 2): True, (0, 4): True}, "vis_post": {(0, 2): True, (0, 4): True}})
        prev = tgt
    return SimpleNamespace(ticks=ticks, ids=[1, 2, 4], side={1: 0, 2: 1, 4: 1}, typ={1: 0, 2: 0, 4: 0}, stats={0: {"attack_range": 300.0, "sensor_radius": 300.0}}, heights=[],
                           mult_up=[1.0] * 5, mult_down=[1.0] * 5, flyers=set())


def test_R_087_04_the_oracle_reports_a_pick_beyond_the_notice_distance_and_passes_one_inside_it():
    """R-087-04 (oracle, round5.md "Fourth pass"): unit 1 takes enemy 2 in tick 2; the pick is reported only when enemy 2 is beyond the notice distance in every reading of the tick (the unit and
    the enemy each at their pre-step or post-step position). Enemy 2 at 340 wu (notice 330) before and after the step: reported with its distance and the notice distance; at 320: nothing; at 340 after
    enemy 2 hit the unit in tick 2 (return fire): nothing; at 320 before the step and 340 after it (a reading inside, which the engine may have taken): nothing, though the post-step state alone is beyond."""
    o = _oracle()
    assert [(t, u, tg) for t, u, tg, _, _ in o.picks_beyond_notice(record([340.0, 340.0, 340.0], [0, 2]))] == [(2, 1, 2)]
    assert o.picks_beyond_notice(record([320.0, 320.0, 320.0], [0, 2])) == []
    assert o.picks_beyond_notice(record([340.0, 340.0, 340.0], [0, 2], hits=(2,))) == []
    assert o.picks_beyond_notice(record([340.0, 340.0, 320.0], [0, 2])) == []
    assert o.picks_beyond_notice(record([320.0, 320.0, 340.0], [0, 2])) == []
    assert o.picks_beyond_notice(record([330.0, 330.0, 330.0], [0, 2])) == []      # exactly at the notice distance: inside it


def test_R_087_03_the_oracle_does_not_call_a_lock_dropped_for_the_notice_distance_a_swap():
    """R-087-03 (oracle, round5.md "Fourth pass"): unit 1 holds enemy 2 and in tick 3 holds enemy 4. Enemy 2 beyond 330 in some reading of that step (340 before, 320 after; or the reverse; or both): a legal
    end, no swap; at 320 in every reading (inside): a swap; at 340 after it hit the unit in tick 2 (return fire, exempt from the distance end): a swap."""
    o = _oracle()
    assert o.lock_swaps(record([340.0, 340.0, 340.0, 340.0], [2, 2, 4])) == []
    assert o.lock_swaps(record([340.0, 340.0, 340.0, 320.0], [2, 2, 4])) == []
    assert o.lock_swaps(record([320.0, 320.0, 320.0, 340.0], [2, 2, 4])) == []
    assert [(t, u) for t, u, _ in o.lock_swaps(record([320.0, 320.0, 320.0, 320.0], [2, 2, 4]))] == [(3, 1)]
    assert [(t, u) for t, u, _ in o.lock_swaps(record([340.0, 340.0, 340.0, 340.0], [2, 2, 4], hits=(2,)))] == [(3, 1)]


def test_R_087_03_the_oracle_reports_a_lock_kept_beyond_the_notice_distance_for_more_than_a_cohort_period():
    """R-087-03 (oracle, G7 lock, round5.md "Fourth pass"): enemy 2 locked from tick 1 stands at 250 after tick 1 and at 400 from tick 2; tick 2 has a reading at 250, so the first tick beyond in every
    reading is 3. The unit still holds it in tick 7, the fifth such tick: reported once; dropped in tick 7 (ticks 3 to 6, four ticks beyond): nothing; a lock taken by return fire (enemy 2 fired in tick 1):
    nothing."""
    o = _oracle()
    gaps = [250.0, 250.0] + [400.0] * 10
    assert [(t, u) for t, u, *_ in o.locks_beyond_notice(record(gaps, [2] * 10))] == [(7, 1)]
    assert o.locks_beyond_notice(record(gaps, [2] * 6 + [0] * 4)) == []
    assert o.locks_beyond_notice(record(gaps, [2] * 10, hits=(1,))) == []
