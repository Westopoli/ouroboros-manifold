"""LAB-REV2-E1b -- an attack-moving unit hit from out of range pursues the attacker as ONE engagement of its order and
then resumes toward its ORIGINAL ordered point (E-11 S-087, R-087-06 rewritten 2026-10-19; E-13 R-096-02).

Ruling (Architect, decisions 28 point 1, docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md): a hit unit that is out of
range pursues the attacker as one engagement of its attack-move order; when the attacker dies or leaves, the unit resumes toward
the point the order was issued with (the `last_attacker` branch of csrc/unit.c keeps the issued point; om_tac_release resumes to it).
Only an idle unit, which has no order and so no point, holds where the pursuit ends. R-099-05 give-up ends the order as an arrival
does, unchanged (tests/csim/test_PP_unit_giveup.py stays green and is not edited here).

Why: the lab's caps (decision 28) all end with an attack-moving unit idle, no destination, standing where its attacker once stood,
because the engine overwrote the ordered point with the attacker's position (order_x/y and issued_x/y in unit.c) and the unit
"arrived" at the dead attacker's place. Westley's 2026-10-13 ruling: an attack-move is not finished until the unit reaches its point.

What is here
  - isolation, the attacker killed early (tick 5), the unit ends within the arrival radius of its ORDERED point -- red today: it ends
    at the attacker's old place with no destination (the idle line is pasted in the failure message);
  - isolation, the unit's own fire kills the attacker, then the same -- red today;
  - the unit has its ordered point as its destination again some ticks after the attacker died, not only on arrival at the attacker's
    place -- red today (fixture number: see PROMPT_TICKS);
  - controls (green today and after): the hit unit really pursues (it moves toward the attacker); an attack-moving unit never hit
    reaches the same point inside the same tick budget; an IDLE unit hit the same way pursues and then holds where the pursuit ends,
    with no destination, and never walks back to a point it never had.
Decision 30 (Architect 2026-10-19) extends it, added in a second commit: (1) a group member's point of record is its slot, and it
resumes toward the slot -- group test, red today; (2) the pursuit ends three ways (death, the R-096-03 leash of 200 wu from the
acquisition anchor, the attacker no longer seen, R-087-08), one test per ending, the leash and sight endings resume toward the original
point like death -- two more red tests; (3) the resume is immediate, within the R-087-08 stagger of 4 ticks, with no walk to the
attacker's last spot first -- the 60 tick bound of the first commit narrowed to 4 (a rule number). The attacker now stands inside the
unit's sensor (430 wu, or 650 wu for the leash and sight scenes): decision 30 point 2 drops a pursuit of an unseen attacker, and the
first commit's 900 wu attacker was never seen. Controls added, green today and after: a marching group has distinct slots and an unhit
member reaches its own, and inside the leash with the attacker seen the unit is still pursuing.
No new number is pinned: the scene numbers are fixtures, the arrival radius is R-095-05's (1.5 x collision radius 15, as the E1 tests).

Existing tests that encode the superseded wording "dropping its earlier destination" (R-087-06 before 2026-10-19), NOT edited here;
the E1b landing clerk retires or rewrites them under ledger rows TD-LAB-REV2-E1b-* quoting decision 28:
  1. tests/csim/test_PP_unit_return_fire.py::test_R_087_06_out_of_range_attacker_becomes_the_new_goal[attack_move]
     (asserts the goal IS the attacker's place with the old destination dropped; the idle case stays true; it stays green on a
     build that keeps the attacker's place as the destination while pursuing -- a measured throwaway build did -- and goes red on
     one that keeps the ordered point as the destination, so the clerk decides it with the builder's design in hand)
  2. tests/csim/test_PP_unit_return_fire.py::test_R_087_06_lowest_id_same_layer_attacker_out_of_range[attack_move-low_first / -high_first]
     (same reading: the goal after the hit is the attacker's place; which attacker is picked stays true, only the goal reading changes)
  3. the module docstring of tests/csim/test_PP_unit_return_fire.py (quotes R-087-06's old text, "attack-moves to the attacker, dropping
     its earlier destination"; no assertion depends on the docstring alone)
  tests/csim/test_PP_C_g5_area_return_fire.py reads only IDLE victims ('goal' = an idle unit attack-moving to the attacker), which
  decision 28 leaves as it was: not affected. test_PP_unit_guard.py reads guards and idle units: not affected.
  Whatever else the E1b landing's full csim run turns red is listed by the clerk the same way. What the goal is in the first tick or
  two after the hit (the attacker's place while pursuing, or the ordered point with the pursuit kept elsewhere) is the builder's
  design and is not pinned here; only the point the unit ends up resuming toward after the attacker is gone is.
The group member is covered by decision 30 point 1 (tests below).
"""
import math

import pytest

from test_PP_unit_support import BASTION, SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, spawn, step

P = (-1200.0, 0.0)                # the ordered point; behind the unit so a march to the attacker and a march to the point differ
ATTACKER_AT = (430.0, 0.0)        # beyond the Vanguard's range 300, inside its sensor 700 (so its side SEES it, decision 30 point 2),
                                  # and 130 wu from range, inside the R-096-03 leash, so the unit can close and kill it
HIT = 10.0
KILL_TICK = 5                     # ticks of pursuit before the attacker dies in the 'early' scenes; the unit has moved about 20 wu
ARRIVAL = 22.5                    # R-095-05: 1.5 x the collision radius 15; the same radius the E1 tests use
MARCH_TICKS = 2000                # budget to pursue, kill and walk back 2100 wu at 4 wu a tick; fixture number, a bug detector only
LEASH = 200.0                     # R-096-03 / R-087-05: the leash from the acquisition anchor, in wu (a rule number)
STAGGER = 4                       # R-087-08: the cohort stagger, ticks; decision 30 point 3: the resume lands within it (a rule number)
FAR_ATTACKER_AT = (650.0, 0.0)    # seen (inside sensor 700) and 350 wu from range, so the unit cannot reach it inside the leash
STAY_TICKS = 100                  # ticks a finished unit is watched for; fixture number


def _victim(lib, w, ordered):
    """Vanguard at the origin, id 2 (id 1 a far-off friend), attack-moved to P when `ordered`, idle otherwise; asserts the first
    step after the hit is not its targeting-cohort turn, so a target it holds can only come from return fire (as the R-087-06 tests)."""
    spawn(lib, w, BASTION, 0, -9000.0, 0.0)
    step(lib, w)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    if ordered:
        attack_move(lib, w, [u], *P)
    assert (lib.om_tactical_tick(w) + 1) % 4 != lib.om_unit_targeting_cohort(w, u), "fixture: cohort turn"
    return u


def _hit(lib, w, victim):
    """A Supply attacker (it never fires, so the only hit is this one) at ATTACKER_AT, and one hit from it."""
    attacker = spawn(lib, w, SUPPLY, 1, *ATTACKER_AT)
    lib.om_unit_deal_damage(w, attacker, victim, HIT)
    return attacker


def _idle_line(lib, w, u):
    has, gx, gy = dest(lib, w, u)
    x, y = pos(lib, w, u)
    return f"unit at ({x:.1f}, {y:.1f}), destination {'(%.1f, %.1f)' % (gx, gy) if has else 'None'}"


def _miss(lib, w, u, point):
    x, y = pos(lib, w, u)
    return math.hypot(x - point[0], y - point[1])


# ---- isolation: the pursuit is one engagement; the unit resumes toward P ----------------------------------------------------------

def test_S087_R_087_06_attacker_dies_early_and_the_unit_resumes_toward_its_ordered_point(lib, world_factory):
    """R-087-06 (2026-10-19) / R-096-02: an attack-moving unit is hit from out of range, pursues for KILL_TICK ticks, the attacker
    dies, and the unit ends within the arrival radius of its ORDERED point P. Red today: it walks on to the attacker's old place
    (900, 0), arrives there, and idles with no destination (the idle line in the message)."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = _hit(lib, w, u)
    step(lib, w, KILL_TICK)
    kill(lib, w, attacker)

    step(lib, w, MARCH_TICKS)

    assert _miss(lib, w, u, P) <= ARRIVAL, (
        f"the unit did not resume toward its ordered point {P} after the attacker died: {_idle_line(lib, w, u)} "
        f"({_miss(lib, w, u, P):.1f} wu from P, limit {ARRIVAL}); it idles where the dead attacker stood")


def test_S087_R_087_06_the_unit_kills_the_attacker_itself_and_resumes_toward_its_ordered_point(lib, world_factory):
    """Same ruling, the natural case: the pursuit ends because the unit closes into range and kills the attacker. It then resumes
    toward P and ends within the arrival radius of it. Red today: it walks on to the dead attacker's place and idles there."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = _hit(lib, w, u)
    for _ in range(MARCH_TICKS):
        if hp(lib, w, attacker) <= 0.0:
            break
        step(lib, w)
    assert hp(lib, w, attacker) <= 0.0, "fixture: the unit should have killed the attacker within the budget"
    assert pos(lib, w, u)[0] > 0.0, "fixture: the kill happened out where the attacker stood, not at the start"

    step(lib, w, MARCH_TICKS)

    assert _miss(lib, w, u, P) <= ARRIVAL, (
        f"the unit did not resume toward its ordered point {P} after killing the attacker: {_idle_line(lib, w, u)} "
        f"({_miss(lib, w, u, P):.1f} wu from P, limit {ARRIVAL})")


def test_S087_R_087_06_the_ordered_point_is_the_destination_again_within_the_stagger_of_the_attacker_dying(lib, world_factory):
    """Decision 30 point 3 (R-087-08): STAGGER ticks after the attacker died the unit's destination is P, and it does not walk to
    the attacker's last spot first. Red today: its destination is the attacker's place until it gets there."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = _hit(lib, w, u)
    step(lib, w, KILL_TICK)
    kill(lib, w, attacker)
    x_dead = pos(lib, w, u)[0]

    step(lib, w, STAGGER)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(P, abs=1e-6), (
        f"{STAGGER} ticks after the attacker died the destination is not the ordered point {P}: {_idle_line(lib, w, u)}")
    step(lib, w, 30)
    assert pos(lib, w, u)[0] < x_dead, "the unit did not turn back toward its ordered point"


# ---- decision 30 point 2: the pursuit ends three ways; the leash and sight endings resume toward the original point like death ----------

def _ticks_until_past_leash(lib, w, u, limit):
    """Step until the unit is more than LEASH from the origin (its anchor: where it stood when hit); returns the ticks taken or None."""
    for t in range(1, limit + 1):
        step(lib, w)
        x, y = pos(lib, w, u)
        if math.hypot(x, y) > LEASH:
            return t
    return None


def test_S087_R_096_03_the_pursuit_ends_at_the_leash_and_the_unit_resumes_toward_its_ordered_point(lib, world_factory):
    """Decision 30 point 2 (R-096-03): the attacker stands 350 wu beyond the unit's range, so it cannot be reached inside the leash.
    The unit pursues, passes LEASH (200 wu from where it was hit), and within STAGGER ticks of that its destination is P again; it
    then reaches P. Red today: nothing leashes the redirect, the destination stays the attacker's place and the unit walks there."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = spawn(lib, w, SUPPLY, 1, *FAR_ATTACKER_AT)
    lib.om_unit_deal_damage(w, attacker, u, HIT)

    took = _ticks_until_past_leash(lib, w, u, MARCH_TICKS)
    assert took is not None, f"the unit never pursued out past the leash: {_idle_line(lib, w, u)}"
    step(lib, w, STAGGER)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(P, abs=1e-6), (
        f"{STAGGER} ticks after passing the {LEASH} wu leash the destination is not the ordered point {P}: {_idle_line(lib, w, u)}")
    step(lib, w, MARCH_TICKS)
    assert _miss(lib, w, u, P) <= ARRIVAL, f"the unit did not reach its ordered point after the leash: {_idle_line(lib, w, u)}"


def test_S087_R_087_08_the_pursuit_ends_when_the_attacker_is_no_longer_seen_and_the_unit_resumes_toward_its_ordered_point(
        lib, world_factory):
    """Decision 30 point 2 (R-087-08, 'a unit cannot chase what it cannot see'): 10 ticks into the pursuit the attacker, which is alive
    and still near, becomes unseen (stealth). Within STAGGER ticks the unit's destination is P again and it reaches P. Red today:
    nothing validates the redirect against sight; the unit keeps walking to the attacker's place."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = spawn(lib, w, SUPPLY, 1, *FAR_ATTACKER_AT)
    lib.om_unit_deal_damage(w, attacker, u, HIT)
    step(lib, w, 10)
    lib.om_unit_set_stealth(w, attacker, 1)

    step(lib, w, STAGGER)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(P, abs=1e-6), (
        f"{STAGGER} ticks after the attacker became unseen the destination is not the ordered point {P}: {_idle_line(lib, w, u)}")
    step(lib, w, MARCH_TICKS)
    assert _miss(lib, w, u, P) <= ARRIVAL, f"the unit did not reach its ordered point after losing sight: {_idle_line(lib, w, u)}"


# ---- decision 30 point 1: a group member keeps its slot as its point of record ---------------------------------------------------------

G = (-1200.0, 50.0)               # the group's attack-move point; the members' slots are this plus their formation offsets


def _group_scene(lib, w):
    """Two Vanguards 100 wu apart attack-moved together to G and marching for 10 ticks; returns (a, b, slot_a, slot_b) where a slot is
    the destination each member holds while the group marches (the point of record, R-095-05)."""
    spawn(lib, w, BASTION, 0, -9000.0, 0.0)
    a = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    b = spawn(lib, w, VANGUARD, 0, 0.0, 100.0)
    attack_move(lib, w, [a, b], *G)
    step(lib, w, 10)
    slots = []
    for m in (a, b):
        has, gx, gy = dest(lib, w, m)
        assert has == 1, "fixture: a marching member should have a destination"
        slots.append((gx, gy))
    return a, b, slots[0], slots[1]


def test_S087_R_087_06_a_group_member_hit_from_out_of_range_resumes_toward_its_slot(lib, world_factory):
    """Decision 30 point 1: a member of a group attack-move, hit from out of range, pursues like the lone unit; when the attacker dies
    its destination within STAGGER ticks is its slot again (not G, not the attacker's place), and it ends within the arrival radius of
    the slot. Red today: the member walks to the attacker's place and idles there."""
    w = world_factory(n_regions=1)
    a, b, slot_a, slot_b = _group_scene(lib, w)
    attacker = spawn(lib, w, SUPPLY, 1, *ATTACKER_AT)
    lib.om_unit_deal_damage(w, attacker, a, HIT)
    step(lib, w, KILL_TICK)
    kill(lib, w, attacker)

    step(lib, w, STAGGER)

    has, gx, gy = dest(lib, w, a)
    assert has == 1 and (gx, gy) == pytest.approx(slot_a, abs=1e-6), (
        f"{STAGGER} ticks after the attacker died the member's destination is not its slot {slot_a}: {_idle_line(lib, w, a)}")
    step(lib, w, MARCH_TICKS)
    assert _miss(lib, w, a, slot_a) <= ARRIVAL, f"the member did not reach its slot: {_idle_line(lib, w, a)}"


def test_control_S087_R_087_06_a_marching_group_has_distinct_slots_and_an_unhit_member_reaches_its_own(lib, world_factory):
    """Positive control for the group test (green today and after): the two members hold different slots, neither equals the bare
    point G for both, and with no attacker each member ends within the arrival radius of its own slot, so the slot reading can pass."""
    w = world_factory(n_regions=1)
    a, b, slot_a, slot_b = _group_scene(lib, w)
    assert slot_a != slot_b, "fixture: the two members should hold distinct slots"

    step(lib, w, MARCH_TICKS)

    assert _miss(lib, w, a, slot_a) <= ARRIVAL and _miss(lib, w, b, slot_b) <= ARRIVAL, (
        f"a {_idle_line(lib, w, a)}; b {_idle_line(lib, w, b)}")


# ---- controls: green today and after ---------------------------------------------------------------------------------------------------

def test_control_S087_R_087_06_a_hit_attack_moving_unit_does_pursue_the_attacker(lib, world_factory):
    """Positive control (green today and after): the hit really sends the unit toward the attacker (x grows and it has a destination), so the tests above start from a pursuit and a 'resumes' reading can be told from 'never left'."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    _hit(lib, w, u)

    step(lib, w, KILL_TICK)

    assert pos(lib, w, u)[0] > 0.0, f"the hit unit did not pursue: {_idle_line(lib, w, u)}"
    assert dest(lib, w, u)[0] == 1


def test_control_S087_R_087_06_an_attack_moving_unit_never_hit_reaches_the_same_point_in_the_same_budget(lib, world_factory):
    """Positive control for the arrival reading (green today and after): the same unit and order with no attacker ends within the
    arrival radius of P inside MARCH_TICKS, so the resume tests can be passed and P is reachable in their budget."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)

    step(lib, w, MARCH_TICKS)

    assert _miss(lib, w, u, P) <= ARRIVAL, _idle_line(lib, w, u)


def test_control_S087_R_087_06_an_idle_unit_pursues_and_holds_where_the_pursuit_ends(lib, world_factory):
    """Idle unit (no order, so no point), green today and after (decision 28: only an idle unit holds where the pursuit ends): hit
    from out of range it pursues, the attacker dies, and after the pursuit it has no destination, does not move again, and is out
    where the pursuit took it, not back at its start or anywhere near a point it never had."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=False)
    attacker = _hit(lib, w, u)
    step(lib, w, KILL_TICK)
    assert pos(lib, w, u)[0] > 0.0 and dest(lib, w, u)[0] == 1, "fixture: the idle unit should be pursuing"
    kill(lib, w, attacker)

    step(lib, w, MARCH_TICKS)

    where = pos(lib, w, u)
    assert dest(lib, w, u)[0] == 0, f"an idle unit still has a destination after the pursuit: {_idle_line(lib, w, u)}"
    assert where[0] > 0.0, f"the idle unit did not stay out where the pursuit took it: {_idle_line(lib, w, u)}"
    step(lib, w, STAY_TICKS)
    assert pos(lib, w, u) == where, "a unit holding after its pursuit moved again"


def test_control_S087_R_096_03_inside_the_leash_and_while_seen_the_unit_is_still_pursuing(lib, world_factory):
    """Positive control for the leash and sight tests (green today and after): with the attacker alive, seen and the unit still inside
    the leash, the unit keeps moving toward it (x keeps growing between tick 15 and tick 25), so a destination that returns to P in
    those tests is an ending, not a pursuit that never happened."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = spawn(lib, w, SUPPLY, 1, *FAR_ATTACKER_AT)
    lib.om_unit_deal_damage(w, attacker, u, HIT)
    step(lib, w, 15)
    x15 = pos(lib, w, u)[0]

    step(lib, w, 10)

    assert pos(lib, w, u)[0] > x15 > 0.0, f"the unit stopped pursuing a seen attacker inside the leash: {_idle_line(lib, w, u)}"
    assert hp(lib, w, attacker) > 0.0 and math.hypot(*pos(lib, w, u)) < LEASH
