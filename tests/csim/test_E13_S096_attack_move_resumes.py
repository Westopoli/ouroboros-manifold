# Rule pins: R-095-05@819fd3, R-096-02@e8ae96
"""LAB-REV2-E1 -- an attack-move group resumes toward its point after every engagement (E-13 S-096, R-096-02).

R-096-02 (rewritten 2026-10-13, Westley, option (a)): "after every fight the group resumes toward the
point as a unit attack-moved alone does ... an attack-move is not finished until the unit reaches its
point". The engine today ends a group once every living member has engaged and never resumes it
(csrc/unit.c, om_tac_am_group_done inside om_tac_release). Measured 2026-10-13: two groups attack-moved
to one point stalled 303 to 336 wu apart with range 300, while the same units ordered one by one fought
to elimination. Spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 6 and the E1 row.

What is here
  - the stall scene (8 Vanguards and 8 Raiders per side, the blobs 600 wu apart, both sides attack-moved
    to the midpoint as GROUP orders) ends by elimination (S-096 / R-096-02) -- red today;
  - the control (green today): the same scene, one attack-move per unit, ends by elimination;
  - an isolation test: a group member resumes toward its point after it kills its target -- red today;
  - an integration test: the whole scene, ticked to the end with a cap, one side wiped out and the run
    ending by elimination rather than by the stalemate break -- red today;
  - a second-engagement test: a group member kills target 1, resumes, meets target 2 further along, kills
    it, resumes again and reaches the point -- red today (the group ends at the first kill), with a lone-unit
    control, green today;
  - a negative guard test: a group attack-moved to a point with no enemy arrives, ends as one group (every
    member has a goal until the group ends, then none) and stays within the arrival radius for
    STAY_TICKS ticks -- GREEN today and after (a guard against E1 making a finished group march again),
    with a control that the same reading trips on a unit still marching.
The scene numbers (8 and 8, 600 wu, midpoint) are the ones the spec's E1 row names; the blob shape
and radius (the lab's objective scene, Vanguards and Raiders alternating along the spiral) are the scene's,
not a rule threshold. No tolerance is asserted. Measured on the unmodified tree: the group-ordered scene
stalls with both factions alive for each of three type orders tried (V then R, R then V, alternating); the
per-unit scene eliminates for all three. The alternating scene used here stalls with 2 and 6 survivors, the
nearest pair 301.7 wu apart (range 300), and every survivor without a goal.

Superseded by R-096-02 (2026-10-13) -- tests that encode the ruling "once every member of the group has
engaged, the group ends and its members do not resume the march" (the engine clause of the Architect,
A124 build). NOT edited here; the E1 landing clerk retires or rewrites them under a ledger row quoting
R-096-02:
  1. tests/csim/test_PP_move_group.py::test_R_096_02_group_ends_when_every_member_has_engaged_and_does_not_resume
  2. tests/csim/test_PP_unit_attack_move_group.py::test_R_096_02_group_ends_when_every_member_has_engaged
  3. tests/csim/test_PP_unit_attack_move_group.py::test_control_R_096_02_group_goes_on_while_a_member_has_not_engaged
     (the spec row says "and its control"; it is the control of test 2 and states the group-end ruling in
     its docstring. Its assertion, that the engaged member resumes while another has not engaged, stays
     true under the new ruling, so it should stay green; the clerk decides if it is kept or retired.)
  4. tests/csim/parity/test_attack_move_no_sight_pursuit_parity.py::test_control_A199_the_slot_miss_reading_trips_when_the_enemy_is_on_the_route
     (found by the audit: it turns red under a correct E1, 'c: control did not trip (miss 20.0)'. It encodes
     the old end state, "halt short of the slots once the enemy is in range, read the miss at the end of
     the run". Under R-096-02 the enemy dies, the group resumes and reaches its slots, so the final miss
     falls under ARRIVAL. It should become: read the miss at the first engagement (the tick the first
     member holds a target), not at the end of the run; the clerk rewrites it with the parity re-record.)
Docstrings that quote the old wording (no assertion depends on them): the module docstrings of
tests/csim/test_PP_move_group.py (its "A unit attack-moved alone is not a group" line stays true) and
tests/csim/test_PP_unit_attack_move_group.py ("once every member of the group has engaged, the group
ends"), the section comment "the group ends / the lone unit resumes" in the former, and the "# ---- the
group ends once every member has engaged" comment in the latter. The grep for am_group_done / group_ends /
"group ends" found no other test that names the old ruling, but the audit's trial run of a correct E1 found
test 4, which asserts the old end state without naming it; the list is therefore the four above plus
whatever the E1 landing's full csim and parity run turns red. tests/csim/parity/ baselines are not touched
here; the E1 landing re-records them under the ledger row.
"""
import math

import pytest

from test_PP_unit_support import BASTION, RAIDER, SUPPLY, VANGUARD, attack_move, dest, kill, pos, spawn, step, target

SEP = 600.0                       # blob separation named by the spec's E1 row
MID = (0.0, 0.0)                  # the shared attack-move point: the midpoint between the blob centres at +-300
PER_TYPE = 8
CAP_TICKS = 12000                 # the lab's max_ticks for a bug detector (spec: Setup.max_ticks); not a result
_GOLDEN_ANGLE = 2.399963229728653


def _blob_points(n, x, y, radius):
    """n points of the lab's blob formation (scripts/skilllab/formations.py, a Fermat spiral and its reflection),
    reproduced here so the test does not import the lab, which this piece does not own."""
    pairs = n // 2
    out = [(x, y)] if n % 2 else []
    for i in range(pairs):
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * _GOLDEN_ANGLE
        out.append((x + d * math.cos(a), y + d * math.sin(a)))
        out.append((x - d * math.cos(a), y - d * math.sin(a)))
    return out


def _blob(lib, w, faction, cx):
    """A blob of 8 Vanguards and 8 Raiders (alternating along the spiral) centred on (cx, 0). The radius 128 is the
    lab's objective-scene radius for 16 units, 80 + 12 * sqrt(16); it is the scene's, not a rule threshold."""
    pts = _blob_points(2 * PER_TYPE, cx, 0.0, 128.0)
    return [spawn(lib, w, (VANGUARD, RAIDER)[i % 2], faction, x, y) for i, (x, y) in enumerate(pts)]


def _scene(lib, w):
    """The 2026-10-13 stall scene: side 0 centred at x = -300, side 1 at x = +300, 600 wu apart."""
    return _blob(lib, w, 0, -SEP / 2.0), _blob(lib, w, 1, SEP / 2.0)


def _alive(lib, w, ids):
    return sum(1 for u in ids if lib.om_unit_get_hp(w, u) > 0.0)


def _order_as_groups(lib, w, west, east):
    attack_move(lib, w, west, *MID)
    attack_move(lib, w, east, *MID)


def _order_per_unit(lib, w, west, east):
    for u in west + east:
        attack_move(lib, w, [u], *MID)


def _eliminated(lib, w, west, east):
    return min(_alive(lib, w, west), _alive(lib, w, east)) == 0


def _both_alive_line(lib, w, west, east, ticks):
    return (f"om_tactical_run_until_eliminated returned after {ticks} ticks with both factions alive "
            f"(side 0: {_alive(lib, w, west)} of {len(west)}, side 1: {_alive(lib, w, east)} of {len(east)})")


def test_S096_R_096_02_two_attack_moved_groups_fight_to_elimination(lib, world_factory):
    """S-096 / R-096-02: two groups of 16 (8 Vanguards and 8 Raiders each), 600 wu apart, both attack-moved to
    the midpoint as GROUP orders, fight until one side is eliminated. Red today: each member engages once, the
    group ends, nobody resumes, and the sides stall just out of range with both factions alive."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_as_groups(lib, w, west, east)

    ticks = lib.om_tactical_run_until_eliminated(w)

    assert _eliminated(lib, w, west, east), _both_alive_line(lib, w, west, east, ticks)


def test_control_S096_R_096_02_one_attack_move_per_unit_fights_to_elimination(lib, world_factory):
    """Positive control (green today): the same scene with one attack-move per unit (each unit is its own
    group of one and resumes after every fight) ends by elimination. Shows the scene can be won and that the
    elimination check can tell a finished fight from a stall."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_per_unit(lib, w, west, east)

    ticks = lib.om_tactical_run_until_eliminated(w)

    assert _eliminated(lib, w, west, east), _both_alive_line(lib, w, west, east, ticks)


def _engage_pair(lib, w):
    """Two Raiders attack-moved together toward (3000, 50), each beside its own Supply target (a unit that never
    fires, so the end of the fight is exact). Returns (a, b, sa, sb) once both have held a target."""
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 100.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    sb = spawn(lib, w, SUPPLY, 1, 150.0, 100.0)
    attack_move(lib, w, [a, b], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa and target(lib, w, b) == sb:
            return a, b, sa, sb
    pytest.fail("fixture: both members should have engaged within 8 ticks")


def test_S096_R_096_02_a_group_member_resumes_toward_its_point_after_its_target_dies(lib, world_factory):
    """Isolation, S-096 / R-096-02: both members of an attack-move group have engaged and both targets die; each
    member marches on toward the group's point (it has a goal again and moves along +x) as a lone unit does.
    Red today: the group ends, positions stay put and no member has a goal."""
    w = world_factory(n_regions=1)
    a, b, sa, sb = _engage_pair(lib, w)
    kill(lib, w, sa)
    kill(lib, w, sb)
    x0 = {a: pos(lib, w, a)[0], b: pos(lib, w, b)[0]}

    step(lib, w, 30)      # past the 10 tick backswing a first shot leaves, so "not moving" is not a pause

    for u in (a, b):
        assert pos(lib, w, u)[0] > x0[u], f"member {u} did not resume toward the point after its target died"
        assert dest(lib, w, u)[0] == 1, f"member {u} has no goal after its target died: the group ended"


def test_control_S096_R_096_02_a_lone_unit_resumes_toward_its_point_after_its_target_dies(lib, world_factory):
    """Positive control for the isolation test (green today): the same fight with one Raider attack-moved alone;
    it resumes toward (3000, 50) after its target dies, so the isolation test's check can tell a march from a halt."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [a], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa:
            break
    assert target(lib, w, a) == sa, "fixture: the lone unit should have engaged"
    kill(lib, w, sa)
    x0 = pos(lib, w, a)[0]

    step(lib, w, 30)

    assert pos(lib, w, a)[0] > x0
    assert dest(lib, w, a)[0] == 1


def test_S096_R_096_02_integration_whole_scene_ticked_to_one_side_wiped_out(lib, world_factory):
    """Integration, S-096 / R-096-02: the whole stall scene as group orders, ticked one step at a time (not
    through om_tactical_run_until_eliminated, whose stalemate break could end the run early) until one side has
    no living unit or the 12000 tick cap passes. The cap is a bug detector only: reaching it is a failure.
    Red today: the sides stall out of range and the cap is reached with both factions alive."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_as_groups(lib, w, west, east)

    ticks = 0
    while ticks < CAP_TICKS and not _eliminated(lib, w, west, east):
        step(lib, w)
        ticks += 1

    assert _eliminated(lib, w, west, east), (
        f"the cap of {CAP_TICKS} ticks passed with both factions alive "
        f"(side 0: {_alive(lib, w, west)} of {len(west)}, side 1: {_alive(lib, w, east)} of {len(east)})")


# ---- second engagement: kill, resume, meet the next target, kill, resume, arrive

SECOND_X = 900.0                  # where the second targets stand, fixture numbers
POINT_X = 3000.0                  # the attack-move point's x (the one _engage_pair orders), past both target pairs
ARRIVAL = 22.5                    # R-095-05: 1.5 x the collision radius 15; the same radius the engine ends a move on
MARCH_TICKS = 1000                # ticks allowed for a leg of the march, fixture number (a Raider covers 4 wu a tick)
STAY_TICKS = 100                  # ticks a finished group is watched for, fixture number


def _step_until(lib, w, pred, limit):
    for _ in range(limit):
        if pred():
            return True
        step(lib, w)
    return pred()


def test_S096_R_096_02_a_group_kills_two_targets_in_turn_and_reaches_its_point(lib, world_factory):
    """Second engagement, S-096 / R-096-02: two Raiders attack-moved as a group; each kills target 1, resumes,
    meets target 2 further along, kills it, resumes again and ends within the arrival radius of its slot.
    Red today: the group ends at the first kill, so target 2 is never engaged and the members stop at x = 0."""
    w = world_factory(n_regions=1)
    a, b, sa, sb = _engage_pair(lib, w)
    sa2 = spawn(lib, w, SUPPLY, 1, SECOND_X, 0.0)
    sb2 = spawn(lib, w, SUPPLY, 1, SECOND_X, 100.0)
    kill(lib, w, sa)
    kill(lib, w, sb)

    met = _step_until(lib, w, lambda: target(lib, w, a) == sa2 and target(lib, w, b) == sb2, MARCH_TICKS)
    assert met, (f"after the first kills the members did not meet the second targets within {MARCH_TICKS} ticks "
                 f"(a at x = {pos(lib, w, a)[0]:.1f} holds {target(lib, w, a)}, b at x = {pos(lib, w, b)[0]:.1f} "
                 f"holds {target(lib, w, b)})")
    kill(lib, w, sa2)
    kill(lib, w, sb2)

    step(lib, w, MARCH_TICKS)

    for u, slot_y in ((a, 0.0), (b, 100.0)):
        x, y = pos(lib, w, u)
        miss = math.hypot(x - POINT_X, y - slot_y)
        assert miss <= ARRIVAL, f"member {u} ended {miss:.1f} wu from its slot after the second kill (limit {ARRIVAL})"


def test_control_S096_R_096_02_a_lone_unit_kills_two_targets_in_turn_and_reaches_its_point(lib, world_factory):
    """Positive control for the second-engagement test (green today): one Raider attack-moved alone does the same
    two kills in turn and ends within the arrival radius of the point, so the scene and the checks can be passed."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    sa2 = spawn(lib, w, SUPPLY, 1, SECOND_X, 0.0)
    attack_move(lib, w, [a], POINT_X, 0.0)
    assert _step_until(lib, w, lambda: target(lib, w, a) == sa, 8), "fixture: the first engagement"
    kill(lib, w, sa)
    assert _step_until(lib, w, lambda: target(lib, w, a) == sa2, MARCH_TICKS), "fixture: the second engagement"
    kill(lib, w, sa2)

    step(lib, w, MARCH_TICKS)

    x, y = pos(lib, w, a)
    assert math.hypot(x - POINT_X, y) <= ARRIVAL


# ---- negative guard: no enemy, the group arrives, ends as one group and stays put

def _marching_group(lib, w):
    """Three members of mixed types, 300 wu behind and 60 wu to the side of one another, attack-moved to
    (600, 0) with no enemy anywhere. Returns (ids, slots): a member's slot is the point plus its offset from
    the group's centroid, which is where a group move sends it (R-095-05)."""
    start = [(0.0, 0.0, RAIDER), (-300.0, 0.0, BASTION), (-300.0, 60.0, RAIDER)]
    ids = [spawn(lib, w, t, 0, x, y) for x, y, t in start]
    cx = sum(x for x, _, _ in start) / 3.0
    cy = sum(y for _, y, _ in start) / 3.0
    attack_move(lib, w, ids, 600.0, 0.0)
    return ids, [(600.0 + x - cx, 0.0 + y - cy) for x, y, _ in start]


def _pos_all(lib, w, ids):
    return {u: pos(lib, w, u) for u in ids}


def _goals(lib, w, ids):
    return [dest(lib, w, u)[0] for u in ids]


def test_guard_S096_R_096_02_a_group_with_no_enemy_ends_as_one_group_and_stays_put(lib, world_factory):
    """Negative guard, S-096 / R-096-02 (GREEN on the unmodified tree and after E1, not a red test): a group
    attack-moved to a point with no enemy anywhere has nothing to resume after, so (1) every tick either all
    members have a goal or none does: the group ends once all of them have arrived (a rigid march at the
    slowest member's speed, so none ends it alone by arriving first), (2) each member ends within the arrival
    radius of its slot, and (3) for STAY_TICKS further ticks nobody moves and nobody has a goal. Guards E1
    against resuming a finished group, or ending it on the first arrival."""
    w = world_factory(n_regions=1)
    ids, slots = _marching_group(lib, w)

    ended = None
    for t in range(MARCH_TICKS):
        step(lib, w)
        goals = _goals(lib, w, ids)
        assert len(set(goals)) == 1, f"tick {t + 1}: goals {goals}: part of the group ended while the rest marched"
        if not goals[0]:
            ended = t + 1
            break
    assert ended is not None, f"the group had not ended after {MARCH_TICKS} ticks"
    for u, (sx, sy) in zip(ids, slots):
        x, y = pos(lib, w, u)
        assert math.hypot(x - sx, y - sy) <= ARRIVAL, f"member {u} ended {math.hypot(x - sx, y - sy):.1f} wu from its slot"

    rest = {u: pos(lib, w, u) for u in ids}
    step(lib, w, STAY_TICKS)

    assert _pos_all(lib, w, ids) == rest, "a finished group moved again"
    assert _goals(lib, w, ids) == [0, 0, 0], "a finished group has a goal again"


def test_control_guard_S096_R_096_02_the_stay_reading_trips_on_a_group_still_marching(lib, world_factory):
    """Positive control for the guard (green today and after): 20 ticks into the same march the all-or-none goal
    reading shows goals, and positions differ from the start, so the 'nobody moves, nobody has a goal' check
    in the guard would fail on a group still marching."""
    w = world_factory(n_regions=1)
    ids, _ = _marching_group(lib, w)
    before = _pos_all(lib, w, ids)

    step(lib, w, 20)

    assert _pos_all(lib, w, ids) != before
    assert _goals(lib, w, ids) == [1, 1, 1]
