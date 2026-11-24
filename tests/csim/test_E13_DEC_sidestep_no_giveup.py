# Rule pins: DEC-movement-sidestep-2026-11-24 (1), R-099-05 (removed), R-099-04, R-096-02
"""Movement-sidestep LS1 (a) and (d): an attack-moving or moving unit is never given up because it is blocked; its order ends only by arrival, a new order, death, or the pursuit and guard rules.

Rule words (docs/northstar/story_reviews/westley/decisions.md, DEC-movement-sidestep-2026-11-24, point 1): "an attack-moving unit never ends its order short
because it is blocked, so the give-up of R-099-05 (group and lone, with the progress count and its reset) is removed". Westley, 2026-11-24: "The problem isn't the notice,
it's the fact that an attack-move command was not followed through to completion". R-099-04 as it stands after the decision: "Given a unit within its arrival radius of its
destination (1.5 x collision radius for a formation slot ...), When the tick runs, Then it has arrived where it stands ... a flying unit ordered alone stops within 1.5 radii
of its point". R-096-02: "after every fight the group resumes toward the point as a unit attack-moved alone does ... an attack-move is not finished until the unit reaches its point".
Spec: docs/northstar/plans/movement-sidestep-2026-11-24/spec.md "The behaviour" 1 and "Tests" (a), (d).

Scenes. A GUARD friend G (an own Vanguard under om_command_guard: not idle, so it neither yields to a mate (R-097-10) nor is skipped by the probe) stands exactly on the
destination, the one place the mover can never reach (collision keeps them 30 wu apart, over the 22.5 wu arrival radius). The mover M sits inside the old give-up disc
(75 wu) for the rest of the run. Per tick for 3000 ticks (150 s; the old give-up took 40 ticks) M's order must stay active: has_dest 1 after every step.
  (a) a group attack-move of two Raiders to (1000, 1000); M1 (the one whose slot G stands on) is the subject; M2 walks to its own slot, 40 wu away, and arrives (control).
  (d) one Raider moved alone, and one attack-moved alone, to G's place.
Each runs for the default (flying) movement kind and for walkers (the game's units on a world with ground; the give-up pass ran for both).

Red today: R-099-05's pass ends the order on the 40th tick inside the disc without progress, for the group member and for the lone unit, in both kinds.
Controls green today: M2 (a free slot) arrives and its order ends; a lone unit sent to a free point arrives and its order ends (so a missing destination is observable here, and an
order that must end does end: no test below demands an order that never ends).
"""
import pytest

from sidestep_support import ARRIVE_SLOT, RAIDER, VANGUARD, attack_move, dest, dist, group_move, guard, move, pos, spawn, step, world

TICKS = 3000
KINDS = ["flying", "walking"]


def _w(lib, wf, kind):
    return world(lib, wf, walking=(RAIDER, VANGUARD) if kind == "walking" else ())


def _guard_on(lib, w, xy):
    g = spawn(lib, w, VANGUARD, 0, *xy)
    assert guard(lib, w, [g]) == 0
    return g


def _order_stays(lib, w, uid, ticks=TICKS):
    """The first tick after which uid has no destination, or None; also the tick count of the run."""
    for t in range(1, ticks + 1):
        step(lib, w)
        if dest(lib, w, uid)[0] != 1:
            return t
    return None


# ---------------------------------------------------------------- (a) a blocked group attack-mover

@pytest.mark.parametrize("kind", KINDS)
def test_DEC_movement_sidestep_a_blocked_group_attack_mover_keeps_its_order_for_3000_ticks(lib, world_factory, kind):
    """DEC-movement-sidestep-2026-11-24 (1), R-096-02 'an attack-move is not finished until the unit reaches its point': M1 and M2 attack-moved together to (1000, 1000) from
    (500, 1000) and (500, 1040); a guard friend G stands on M1's slot. On every one of 3000 ticks M1 still has its destination (it is nowhere near arrival: G keeps it 30 wu from its slot).
    Red today (flying and walking): the give-up ends M1's order about 40 ticks after it reaches the 75 wu disc."""
    w = _w(lib, world_factory, kind)
    m1 = spawn(lib, w, RAIDER, 0, 500.0, 1000.0)
    m2 = spawn(lib, w, RAIDER, 0, 500.0, 1040.0)
    assert attack_move(lib, w, [m1, m2], 1000.0, 1000.0) == 0
    h, sx, sy = dest(lib, w, m1)
    assert h == 1 and dist((sx, sy), (1000.0, 980.0)) < 1e-6, "premise: M1's slot is %s (wanted (1000, 980): a formation 40 wu apart about the click)" % ((sx, sy),)
    _guard_on(lib, w, (sx, sy))
    ended = _order_stays(lib, w, m1)
    assert ended is None, "M1's order ended on tick %d at %s, %.1f wu from its slot (the guard keeps it 30 wu away); R-099-05's give-up is removed" % (ended, pos(lib, w, m1), dist(pos(lib, w, m1), (sx, sy)))
    assert dist(pos(lib, w, m1), (sx, sy)) < 75.0, "premise: M1 spent the run inside the old 75 wu disc, at %s" % (pos(lib, w, m1),)


@pytest.mark.parametrize("kind", KINDS)
def test_DEC_movement_sidestep_control_the_other_group_member_reaches_its_free_slot_and_its_order_ends(lib, world_factory, kind):
    """Control (green today and after): in the scene above M2's slot is free; its order ends by arrival (R-099-04: within 22.5 wu of the slot) and it takes no further own step.
    Proves the group walked and that an ended order is visible to this harness: the red of the tests above is the missing feature, not a harness that cannot see an end."""
    w = _w(lib, world_factory, kind)
    m1 = spawn(lib, w, RAIDER, 0, 500.0, 1000.0)
    m2 = spawn(lib, w, RAIDER, 0, 500.0, 1040.0)
    attack_move(lib, w, [m1, m2], 1000.0, 1000.0)
    _, s1x, s1y = dest(lib, w, m1)
    _, s2x, s2y = dest(lib, w, m2)
    _guard_on(lib, w, (s1x, s1y))
    ended = _order_stays(lib, w, m2, 1500)
    assert ended is not None, "M2 never arrived in 1500 ticks: at %s, slot %s" % (pos(lib, w, m2), (s2x, s2y))
    assert dist(pos(lib, w, m2), (s2x, s2y)) <= ARRIVE_SLOT + 1.0, "M2's order ended %.1f wu from its slot, not by arrival" % dist(pos(lib, w, m2), (s2x, s2y))


# ---------------------------------------------------------------- (d) a lone unit

@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("order", ["move", "attack_move"])
def test_DEC_movement_sidestep_a_lone_unit_blocked_on_its_point_keeps_its_order_for_3000_ticks(lib, world_factory, kind, order):
    """DEC-movement-sidestep-2026-11-24 (1) 'the give-up of R-099-05 (group and lone ...) is removed': one Raider ordered alone (a move, and an attack-move) from (500, 1000)
    to (1000, 1000) with a guard friend on the point. On every one of 3000 ticks it still has its destination. Red today: the lone give-up (Round 6 E2) ends the order on the
    40th tick inside the 75 wu disc, for a flyer and for a walker."""
    w = _w(lib, world_factory, kind)
    m = spawn(lib, w, RAIDER, 0, 500.0, 1000.0)
    (move if order == "move" else attack_move)(lib, w, [m], 1000.0, 1000.0)
    _guard_on(lib, w, (1000.0, 1000.0))
    ended = _order_stays(lib, w, m)
    assert ended is None, "the lone unit's order ended on tick %d at %s, %.1f wu from its point (the guard keeps it 30 wu away)" % (ended, pos(lib, w, m), dist(pos(lib, w, m), (1000.0, 1000.0)))
    assert dist(pos(lib, w, m), (1000.0, 1000.0)) < 75.0, "premise: the unit spent the run inside the old 75 wu disc, at %s" % (pos(lib, w, m),)


@pytest.mark.parametrize("kind", KINDS)
def test_DEC_movement_sidestep_control_a_lone_unit_on_a_free_path_arrives_and_its_order_ends(lib, world_factory, kind):
    """Control (green today and after), R-099-04: the same lone move with nothing on the point: the order ends within 1 wu of the point for a walker and within 22.5 wu (1.5 radii)
    for a flyer, well inside 3000 ticks. The order that must end does end; nothing here demands one that never ends."""
    w = _w(lib, world_factory, kind)
    m = spawn(lib, w, RAIDER, 0, 500.0, 1000.0)
    move(lib, w, [m], 1000.0, 1000.0)
    ended = _order_stays(lib, w, m)
    assert ended is not None and ended < 1000, "the unit never arrived: tick %s, at %s" % (ended, pos(lib, w, m))
    assert dist(pos(lib, w, m), (1000.0, 1000.0)) <= (1.0 if kind == "walking" else ARRIVE_SLOT) + 0.01
