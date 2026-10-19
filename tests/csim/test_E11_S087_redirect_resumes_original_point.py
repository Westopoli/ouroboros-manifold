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
Group members are not covered: decision 28 rules the lone unit's redirect only (question for the Architect in the piece report).
"""
import math

import pytest

from test_PP_unit_support import BASTION, SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, spawn, step

P = (-1200.0, 0.0)                # the ordered point; behind the unit so a march to the attacker and a march to the point differ
ATTACKER_AT = (900.0, 0.0)        # beyond the Vanguard's range 300 and sensor 700 so only the hit, not sight, brings it into play
HIT = 10.0
KILL_TICK = 5                     # ticks of pursuit before the attacker dies in the 'early' scenes; the unit has moved about 20 wu
ARRIVAL = 22.5                    # R-095-05: 1.5 x the collision radius 15; the same radius the E1 tests use
MARCH_TICKS = 2000                # budget to pursue, kill and walk back 2100 wu at 4 wu a tick; fixture number, a bug detector only
PROMPT_TICKS = 60                 # ticks after the attacker's death by which the ordered point is the destination again; fixture number
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


def test_S087_R_087_06_the_ordered_point_is_the_destination_again_soon_after_the_attacker_dies(lib, world_factory):
    """Decision 28 point 1, 'when the attacker dies or leaves, the unit resumes toward its original point': PROMPT_TICKS after the
    attacker died (it has not yet reached the dead attacker's place, 880 wu away at 4 wu a tick) the unit's destination is P and it is
    marching away from the attacker's place. Red today: its destination is still the attacker's place until it gets there."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, ordered=True)
    attacker = _hit(lib, w, u)
    step(lib, w, KILL_TICK)
    kill(lib, w, attacker)
    x_dead = pos(lib, w, u)[0]

    step(lib, w, PROMPT_TICKS)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(P, abs=1e-6), (
        f"{PROMPT_TICKS} ticks after the attacker died the destination is not the ordered point {P}: {_idle_line(lib, w, u)}")
    assert pos(lib, w, u)[0] < x_dead, "the unit did not turn back toward its ordered point"


# ---- controls: green today and after ---------------------------------------------------------------------------------------------------

def test_control_S087_R_087_06_a_hit_attack_moving_unit_does_pursue_the_attacker(lib, world_factory):
    """Positive control (green today and after): the hit really sends the unit toward the attacker (x grows, it has a destination
    and no point-ward step), so the tests above start from a pursuit and a 'resumes' reading can be told from 'never left'."""
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
    assert where[0] > ARRIVAL, f"the idle unit did not stay out where the pursuit took it: {_idle_line(lib, w, u)}"
    step(lib, w, STAY_TICKS)
    assert pos(lib, w, u) == where, "a unit holding after its pursuit moved again"
